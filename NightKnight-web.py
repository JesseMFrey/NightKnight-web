#!/usr/bin/env python

import asyncio
import humanize
import json
import os
import patterns
import platform
import psutil
import shutil
import tornado.escape
import tornado.ioloop
import tornado.locks
import tornado.template
import tornado.web
import webcolors

from NightKnight_control import NightKnight
from datetime import timedelta

from tornado.options import define, options, parse_command_line

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")
define("serial_debug", default=False, help="Debug serial communications")
define("serial", default='/dev/ttyS4', help="Serial port to use")

template_path=os.path.join(os.path.dirname(__file__), "templates")
static_path=os.path.join(os.path.dirname(__file__), "static")

NK_pages=('home','pattern','ADC','nosecone','resets','settings','flight_pattern','server')

class MainHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket=rocket
    def get(self):
        self.render("home.html", pages=NK_pages,page='home')

class PatternHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket=rocket
    def get(self):
        
        patterns = self.rocket.get('pattern_list')
        current_pat = self.rocket.get('pattern',force=True)
        val = self.rocket.get('value')
        color = self.rocket.get('color')
        brt = self.rocket.get('brightness')
        clists = self.rocket.get('clist_list')
        currentlst=self.rocket.get('color_list')
        nightlight = self.rocket.get('nightlight')
        #check if nosecone is in pattern mode
        NC_pat = self.rocket.get('NC_mode') == 'pattern'

        self.render('pattern.html',pages=NK_pages,page='patterns',
                        patterns=patterns,
                        set_nc=NC_pat,
                        pat=current_pat,
                        value=val,
                        brightness=brt,
                        color=color,
                        clists=clists,
                        currentlst=currentlst,
                        nightlight = nightlight,
                    )

    def post(self):
        #get color
        color=webcolors.hex_to_rgb(self.get_body_argument("color"))
        #get brightness
        brt=self.get_body_argument("brt")
        #set brigtness and color
        self.rocket.set('color', color)
        self.rocket.set('brightness', brt)
        #set value
        self.rocket.set('value',int(self.get_body_argument("val")))
        #set color list
        self.rocket.set('color_list', self.get_body_argument("clist"))
        #set pattern
        self.rocket.set('pattern', self.get_body_argument("pattern"))
        #get if we should set NC
        setNC = self.get_body_argument("setNC",'np')
        #get actual NC mode
        actual_NC = self.rocket.get("NC_mode")

        if actual_NC == 'pattern' and setNC == 'np':
            #turn off nosecone
            self.rocket.set('NC', 'static', 0, 0, 0, 0)
        elif actual_NC != 'pattern' and setNC == 'pattern':
            #set nosecone to pattern mode
            self.rocket.set('NC', 'pattern', 0, 0, 0, 0)
        #otherwise nosecone stays as is

        self.redirect('pattern.html',True)

class PatternDescHandler(tornado.web.RequestHandler):

    def get(self):

        self.render('pattern_descriptions.html',pages=NK_pages,page='pattern_descriptions',patterns=patterns.info)

class ADCHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket=rocket
    def get(self):
        adc_dat=self.rocket.read_ADC()

        #add some calculated readings
        adc_dat['Battery Power'] = (adc_dat['Battery Voltage'][0]*adc_dat['Battery Current'][0],'W')
        adc_dat['LED Power'] = (adc_dat['LED Voltage'][0]*adc_dat['LED Current'][0],'W')

        self.render('ADC.html',pages=NK_pages,page='ADC',
                        adc_dat=adc_dat,
                   )

class NoseconeHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket=rocket
    def get(self):
        info = {}
        #get values and stor in dict
        for key in self.rocket.get_keys():
            if key.startswith('NC_') or key.startswith('chute_'):
                #copy value
                info[key] = self.rocket.get(key)

        self.render('nosecone.html',pages=NK_pages,page='nosecone',
                        info = info,
                        chute_patterns=self.rocket.chute_modes,
                        nc_patterns=self.rocket.NC_modes,
                    )

    def post(self):
        #get values
        mode=self.get_body_argument("mode")
        val1=int(self.get_body_argument("val1"))
        val2=int(self.get_body_argument("val2"))
        t1  =int(self.get_body_argument("t1"))
        t2  =int(self.get_body_argument("t2"))
        #set chute
        self.rocket.set('NC', mode, val1, val2, t1, t2)

        self.redirect('nosecone.html')

class ChuteHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket=rocket
    def get(self):
        self.redirect('nosecone.html')

    def post(self):
        #get values
        mode=self.get_body_argument("mode")
        val1=int(self.get_body_argument("val1"))
        val2=int(self.get_body_argument("val2"))
        t1  =int(self.get_body_argument("t1"))
        t2  =int(self.get_body_argument("t2"))
        #set chute
        self.rocket.set('chute', mode, val1, val2, t1, t2)

        self.redirect('nosecone.html')

class ResetsHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket=rocket
    def get(self):

        num, reason = self.rocket.get_resets()
        current_pat = self.rocket.get('pattern',force=True)


        if 'panic' in current_pat:
            is_panicking = True
        else:
            is_panicking = False

        self.render('resets.html',pages=NK_pages,page='resets',
                    rst_reason=reason,rst_num=num,
                    panic=is_panicking, pat = current_pat)
    def post(self):
        #get reset type
        rtype = self.get_body_argument("reset_type")

        self.rocket.reset(rtype)

        self.redirect('resets.html')


class SettingsHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket=rocket
    def get(self):
        ram   = self.rocket.get('ram_set')
        flash = self.rocket.get('flash_set')
        self.render('settings.html',pages=NK_pages,page='settings',
                        flash_set=flash,
                        ram_set=ram,
                   )
    def post(self):
        #get action
        action = self.get_body_argument("action")

        if action == 'save':
            self.rocket.write_settings()
        elif action == 'clear':
            self.rocket.clear_settings()
        else:
            raise ValueError(f'Unknown action \'{action}\'')

        self.redirect('settings.html')

class FlightPatternHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket=rocket
    def get(self):
        #get flight pattern info
        patterns = self.rocket.get('flight_pattern_list')
        current = self.rocket.get('flight_pattern')
        #get expected altitude
        altitude = self.rocket.get('flight_altitude')

        self.render('flight_pattern.html',pages=NK_pages,page='flight_pattern',
                        patterns=patterns,
                        pat=current,
                        altitude = altitude,
                    )

    def post(self):
        #set pattern
        self.rocket.set('flight_pattern',self.get_body_argument("pattern"))

        self.redirect('flight_pattern.html')

class SimulationHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket=rocket
    def get(self):
        self.redirect('flight_pattern.html')

    def post(self):
        #start simulation
        self.rocket.simulate()

        self.redirect('flight_pattern.html')

class AltitudeHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket = rocket
        
    def get(self):
        self.redirect('flight_pattern.html')

    def post(self):
        #get altitude from post
        altitude = self.get_body_argument("altitude")
        #get units from post
        units = self.get_body_argument("units")
        #set altitude
        self.rocket.set('flight_altitude', float(altitude), units = units)

        self.redirect('flight_pattern.html')

class NightlightHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket = rocket
        
    def get(self):
        pass

    def post(self):
        #get value from post
        val = self.get_body_argument("value")
        #get units from post
        self.rocket.set('nightlight', val)

        redir = self.get_body_argument("redirect", default = '')

        if redir:
            self.redirect(redir)

class BrightnessHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket = rocket

    def get(self):
        pass

    def post(self):
        #get value from post
        val = self.get_body_argument("value")
        #get units from post
        self.rocket.set('brightness', val)

        redir = self.get_body_argument("redirect", default = '')

        if redir:
            self.redirect(redir)

class ParameterHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket = rocket

    def get(self):
        pass

    def post(self):
        #get key to set/get from post
        key = self.get_body_argument("key")
        #get opperation from post
        opp = self.get_body_argument("opp",'read')

        if opp == 'read':
            val = self.rocket.get(key)

            #create json response
            response = json.dumps({key:val})
            #send response
            self.write(response)
        elif opp == 'write':
            val = self.get_body_argument('val')

            self.rocket.set('key', val)

        redir = self.get_body_argument("redirect", default = '')

        if redir:
            self.redirect(redir)

def human_readable_size(size, decimal_places=2):
    for unit in ['B','kB','MB','GB','TB']:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"

def human_readable_frequency(freq):
    step = 1e3
    for unit in ['MHz','GHz','THz']:
        if freq < step:
            break
        freq /= step
    return f"{freq:.{0}f} {unit}"

class ServerHandler(tornado.web.RequestHandler):
    def initialize(self):
        pass

    def get(self):

        #get uptime from proc
        with open('/proc/uptime','r') as f:
            #read file and convert to float
            uptime_s = float(f.readline().split()[0])

        uptime_str = humanize.naturaltime(timedelta(seconds=uptime_s))

        uptime_str = uptime_str.removesuffix(' ago')

        mem_info = psutil.virtual_memory()

        disk_info = shutil.disk_usage('/')

        freq_info = psutil.cpu_freq()

        try:
            load_avg = os.getloadavg()
        except OSError:
            load_avg = [float('NaN')]*3

        self.render("server.html", pages=NK_pages,page='server',
                        uptime = uptime_str,
                        machine = platform.machine(),
                        system = platform.system(),
                        py_impl = platform.python_implementation(),
                        py_ver = platform.python_version(),
                        disk_size = human_readable_size(disk_info.total),
                        disk_used = human_readable_size(disk_info.used),
                        cpu_usage = psutil.cpu_percent(),
                        ram_size = human_readable_size(mem_info.total),
                        ram_used = human_readable_size(mem_info.used),
                        cpu_freq = human_readable_frequency(freq_info.current),
                        load_avg = [ f'{100*x:.1f}' for x in load_avg],
                   )

    def post(self):
        pass

def gen_pat_js():
    print('Loading js template')
    loader = tornado.template.Loader(template_path)

    pat_js = loader.load("patterns.js").generate(patterns=patterns.info)

    js_path = os.path.join(static_path, 'patterns.js')

    with open(js_path, 'w') as js_file:
        print(f'Writing "{js_path}"')
        js_file.write(pat_js.decode('utf-8'))
    


def main():
    parse_command_line()

    gen_pat_js()

    rocket=NightKnight(options.serial,debug=options.serial_debug)

    handlers=[ (r"/", MainHandler,{'rocket':rocket}),
               (r"/home\.html", MainHandler,{'rocket':rocket}),
               (r"/index\.html", MainHandler,{'rocket':rocket}),
               (r"/pattern\.html", PatternHandler,{'rocket':rocket}),
               (r"/pattern_descriptions\.html", PatternDescHandler),
               (r"/pattern-descriptions\.html", PatternDescHandler),
               (r"/pattern-descriptions", PatternDescHandler),
               (r"/ADC\.html", ADCHandler,{'rocket':rocket}),
               (r"/nosecone\.html", NoseconeHandler,{'rocket':rocket}),
               (r"/chute", ChuteHandler,{'rocket':rocket}),
               (r"/simulate", SimulationHandler,{'rocket':rocket}),
               (r"/altitude", AltitudeHandler,{'rocket':rocket}),
               (r"/resets\.html", ResetsHandler,{'rocket':rocket}),
               (r"/settings\.html", SettingsHandler,{'rocket':rocket}),
               (r"/flight_pattern\.html", FlightPatternHandler,{'rocket':rocket}),
               (r"/nightlight", NightlightHandler,{'rocket':rocket}),
               (r"/brightness", BrightnessHandler,{'rocket':rocket}),
               (r"/parameter", ParameterHandler,{'rocket':rocket}),
               (r"/server.html", ServerHandler),
               ]

    app = tornado.web.Application(
        handlers,
        template_path=template_path,
        static_path=static_path,
        debug=options.debug,
    )
    app.listen(options.port)
    print(f'Starting server on port number {options.port}...')
    print(f'Open at http://127.0.0.1:{options.port}/index.html')
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
