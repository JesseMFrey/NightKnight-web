#!/usr/bin/env python

import appdirs
import asyncio
import configparser
import datetime
import glob
import humanize
import json
import os
import patterns
import platform
import psutil
import random
import shutil
import tempfile
import tornado.escape
import tornado.ioloop
import tornado.locks
import tornado.template
import tornado.web
import webcolors

from contextlib import nullcontext
from NightKnight_control import NightKnight,CommandError
from datetime import timedelta

from tornado.options import define, options, parse_command_line

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")
define("serial_debug", default=False, help="Debug serial communications")
define("serial", default='/dev/ttyS4', help="Serial port to use")

template_path=os.path.join(os.path.dirname(__file__), "templates")
static_path=os.path.join(os.path.dirname(__file__), "static")

NK_pages=('home','pattern','ADC','nosecone','resets','settings','flight_pattern','server','schedule','config')

panic_patterns = {
        'ppanic' : 'Settings caused power panic, try reducing brightness',
        'mpanic' : 'Altimiter mode panic',
        'rpanic' : 'Unexpected reset caused panic.',
        'ptpanic' : 'Invalid pattern number',
        }

appname = 'NightKnight-web'
appauthor = 'jesse'

config_dir = appdirs.user_config_dir(appname,appauthor)
config_file = os.path.join(config_dir, 'config.cfg')
pattern_dir = os.path.join(config_dir, 'patterns')

def get_panic_str(pattern):
    if pattern in panic_patterns:
        return  panic_patterns[pattern]
    else:
        return None

class MainHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket=rocket
    def get(self):
        self.render("home.html", pages=NK_pages,page='home')

class PatternHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket=rocket
    def get(self):
        
        #initialize with default values
        patterns = None
        current_pat = None
        val = None
        color = [0, 0, 0]
        brt = None
        clists = None
        currentlst=None
        nightlight = None
        NC_pat = None
        read_err = None

        #get error message if it exists
        err_msg  = self.get_argument('error', default=None)

        try:
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
        except (CommandError,IOError,OSError) as e:
            read_err = str(e)

        panic_str = get_panic_str(current_pat)

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
                        error=err_msg,
                        r_err=read_err,
                        panic=panic_str,
                    )

    def post(self):
        #get color
        color=webcolors.hex_to_rgb(self.get_body_argument("color"))
        #get brightness
        brt=self.get_body_argument("brt")
        #get if we should set NC
        setNC = self.get_body_argument("setNC",'np')

        try:
            #set brigtness and color
            self.rocket.set('color', color)
            self.rocket.set('brightness', brt)
            #set value
            self.rocket.set('value',int(self.get_body_argument("val")))
            #set color list
            self.rocket.set('color_list', self.get_body_argument("clist"))
            #set pattern
            self.rocket.set('pattern', self.get_body_argument("pattern"))
            #get actual NC mode
            actual_NC = self.rocket.get("NC_mode")

            if actual_NC == 'pattern' and setNC == 'np':
                #turn off nosecone
                self.rocket.set('NC', 'static', 0, 0, 0, 0)
            elif actual_NC != 'pattern' and setNC == 'pattern':
                #set nosecone to pattern mode
                self.rocket.set('NC', 'pattern', 0, 0, 0, 0)
            #otherwise nosecone stays as is
        except (CommandError,IOError,OSError) as e:
            self.redirect(f'pattern.html?error={e}')
            #we are done here
            return

        self.redirect('pattern.html')

class PatternDescHandler(tornado.web.RequestHandler):

    def get(self):

        self.render('pattern_descriptions.html',pages=NK_pages,page='pattern_descriptions',patterns=patterns.info)

class ADCHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket=rocket
    def get(self):
        self.render('ADC.html',pages=NK_pages,page='ADC')

class StatusHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket = rocket

    def set_default_headers(self):
        #status is retunded with json
        self.set_header("Content-Type", 'application/json')

    def get(self):
        stat_type = self.get_argument('type', default='adc')

        if stat_type == 'adc':
            adc_dat = {}
            err = ''
            try:
                adc_dat=self.rocket.read_ADC()
            except (CommandError,IOError,OSError) as e:
                err = str(e)

            adc_dat['error'] = err
            resp = json.dumps(adc_dat)

        else:
            raise ValueError(f'Unknown status type : "{stat_type}"')

        self.write(resp)

class NoseconeHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket=rocket
    def get(self):
        info = {}
        cp = None
        np = None
        read_err = None
        write_err  = self.get_argument('error', default=None)
        try:
            #get values and stor in dict
            for key in self.rocket.get_keys():
                if key.startswith('NC_') or key.startswith('chute_'):
                    #copy value
                    info[key] = self.rocket.get(key)
            cp = self.rocket.chute_modes
            np = self.rocket.NC_modes
        except (CommandError,IOError,OSError) as e:
            read_err = str(e)

        self.render('nosecone.html',pages=NK_pages,page='nosecone',
                        info = info,
                        chute_patterns=cp,
                        nc_patterns=np,
                        r_error=read_err,
                        w_error=write_err,
                    )

    def post(self):
        #get values
        try:
            mode=self.get_body_argument("mode")
            val1=int(self.get_body_argument("val1"))
            val2=int(self.get_body_argument("val2"))
            t1  =int(self.get_body_argument("t1"))
            t2  =int(self.get_body_argument("t2"))
        except tornado.web.MissingArgumentError as e:
            self.redirect(f'nosecone.html?error={e}')
            return
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
        try:
            mode=self.get_body_argument("mode")
            val1=int(self.get_body_argument("val1"))
            val2=int(self.get_body_argument("val2"))
            t1  =int(self.get_body_argument("t1"))
            t2  =int(self.get_body_argument("t2"))
        except tornado.web.MissingArgumentError as e:
            self.redirect(f'nosecone.html?error={e}')
            return
        #set chute
        self.rocket.set('chute', mode, val1, val2, t1, t2)

        self.redirect('nosecone.html')

class ResetsHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket=rocket
    def get(self):

        num = None
        reason = ''
        current_pat = ''
        err_str = None
        try:
            num, reason = self.rocket.get_resets()
            current_pat = self.rocket.get('pattern',force=True)
        except (CommandError,IOError,OSError) as e:
            err_str = str(e)

        err_arg = self.get_argument('error', None)

        panic_str = get_panic_str(current_pat)

        self.render('resets.html',pages=NK_pages,page='resets',
                    rst_reason=reason,rst_num=num,
                    panic=panic_str, pat = current_pat,
                    r_error=err_str,
                    w_error=err_arg,
                    )
    def post(self):
        #get reset type
        rtype = self.get_body_argument("reset_type")

        try:
            self.rocket.reset(rtype)
        except (CommandError,IOError,OSError) as e:
            self.redirect(f'resets.html?error={e}')
            return

        self.redirect('resets.html')


class SettingsHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket=rocket
    def get(self):
        err_str = None
        flash = {}
        ram = {}
        try:
            ram   = self.rocket.get('ram_set')
            flash = self.rocket.get('flash_set')
        except (CommandError,IOError,OSError) as e:
            err_str = str(e)

        err_arg = self.get_argument('error', None)

        self.render('settings.html',pages=NK_pages,page='settings',
                        flash_set=flash,
                        ram_set=ram,
                        r_error=err_str,
                        w_error=err_arg,
                   )

    def post(self):
        #get action
        action = self.get_body_argument("action")

        try:
            if action == 'save':
                self.rocket.write_settings()
            elif action == 'clear':
                self.rocket.clear_settings()
            else:
                raise ValueError(f'Unknown action \'{action}\'')
        except (ValueError,CommandError,IOError,OSError) as e:
            self.redirect(f'settings.html?error={e}')
            return

        self.redirect('settings.html')

class FlightPatternHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket=rocket
    def get(self):
        err_str = None
        patterns = []
        current = None
        altitude = None
        #get flight pattern info
        try:
            patterns = self.rocket.get('flight_pattern_list')
            current = self.rocket.get('flight_pattern')
            #get expected altitude
            altitude = self.rocket.get('flight_altitude')
        except (CommandError,IOError,OSError) as e:
            err_str = str(e)

        err_arg = self.get_argument('error',None)

        self.render('flight_pattern.html',pages=NK_pages,page='flight_pattern',
                        patterns=patterns,
                        pat=current,
                        altitude = altitude,
                        r_error=err_str,
                        w_error=err_arg,
                    )

    def post(self):
        #set pattern
        try:
            self.rocket.set('flight_pattern',self.get_body_argument("pattern"))
        except (CommandError,IOError,OSError,ValueError,tornado.web.MissingArgumentError) as e:
            self.redirect(f'flight_pattern.html?error={e}')
            return

        self.redirect('flight_pattern.html')

class SimulationHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket=rocket
    def get(self):
        self.redirect('flight_pattern.html')

    def post(self):
        #start simulation
        try:
            self.rocket.simulate()
        except (CommandError,IOError,OSError) as e:
            self.redirect(f'flight_pattern.html?error={e}')
            return

        self.redirect('flight_pattern.html')

class AltitudeHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket = rocket
        
    def get(self):
        self.redirect('flight_pattern.html')

    def post(self):
        try:
            #get altitude from post
            altitude = self.get_body_argument("altitude")
            #convert to float for calculations
            altitude = float(altitude)
            #get units from post
            units = self.get_body_argument("units")
        except (ValueError,tornado.web.MissingArgumentError) as e:
            self.redirect(f'flight_pattern.html?error=invalid request')
            return

        #set altitude
        try:
            self.rocket.set('flight_altitude', altitude, units = units)
        except (CommandError,IOError,OSError) as e:
            self.redirect(f'flight_pattern.html?error={e}')
            return

        self.redirect('flight_pattern.html')

class NightlightHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket = rocket
        
    def get(self):
        pass

    def post(self):
        #get value from post
        val = self.get_body_argument("value")
        err_str=''
        try:
            #get units from post
            self.rocket.set('nightlight', val)
        except (CommandError,IOError,OSError) as e:
            err_str = str(e)


        redir = self.get_body_argument("redirect", default = '')

        if err_str and redir:
            err_arg = f'error={err_str}'
            if '?' in redir:
               #arguments exist, add seperator
               redir += '&' + err_arg 
            else:
                #no arguments, add start of arguments
                redir += '?' + err_arg 

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

def config_to_string(section):
    section_dict = dict(section)
    return '\n'.join([ f'{k} = {v}' for k, v in section_dict.items()])

class ConfigHandler(tornado.web.RequestHandler):
    def initialize(self, scheduler):
        self.scheduler = scheduler

    def get(self):
        patterns = find_patterns()
        config_list = [ os.path.splitext(os.path.basename(c))[0] for c in patterns ]
        current_name = os.path.splitext(os.path.basename(self.scheduler.current_pattern))[0]

        edit_name = self.get_argument('edit', None)

        if edit_name :
            #get full path to file
            edit_config = os.path.join(pattern_dir, edit_name + '.pat')

            config = configparser.ConfigParser()

            config.read(edit_config)

            day_config = config_to_string(config['settings'])
            night_config = config_to_string(config['settings-night'])
            #set name the same as we loaded
            config_name = os.path.splitext(os.path.basename(edit_config))[0]
        else:
            #get config from current settings
            keys = self.scheduler.rocket.saved_settings
            skip_keys = ('nightlight', 'flight_pattern', 'flight_altitude')
            day_config = '\n'.join([f'{k} = {self.scheduler.rocket.get(k)}' for k in keys if k not in skip_keys])
            day_config += '\nnightlight = off'
            night_config = '\nnightlight = on'
            config_name = ""


        self.render('configuration.html', pages=NK_pages, page='config',
                        configs = config_list,
                        is_night = self.scheduler.schedule_settings['state'] == 'night',
                        current = current_name,
                        day_config=day_config,
                        night_config=night_config,
                        config_name=config_name,
                    )

    def post(self):
        config_name = self.get_body_argument('config')
        config = os.path.join(pattern_dir, config_name + '.pat')
        load_night = self.get_body_argument('night','Day') == 'Night'

        action = self.get_body_argument('action')
        if action == 'Load':
            self.scheduler.set_config(config, is_night=load_night)
        elif action == 'Edit':
            self.redirect(f'config.html?edit={config_name}')
            return

        self.redirect('config.html')

def write_pat_config(file, settings, settings_night):
    with open(file, 'w') if isinstance(file, str) else nullcontext(file) as f:
        f.write('[settings]\n')
        f.write(settings)
        f.write('\n\n[settings-night]\n')
        f.write(settings_night)

class ConfigSaveHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket = rocket
        self.set_header("Content-Type", 'application/json')

    def post(self):
        action = self.get_body_argument('action')

        settings = self.get_body_argument('settings')
        settings_night = self.get_body_argument('settings_night')
        force = self.get_body_argument('force', False)

        reason = ''

        if action == 'Save':
            filename = self.get_body_argument('filename')

            full_name = os.path.join(pattern_dir, filename + '.pat')

            if force or not os.path.exists(full_name):
                write_pat_config(full_name, settings, settings_night)
                success = True
            else:
                success = False
                reason = 'File exists'
        elif 'Preview' in action:
            #open a temporary directory to store the config to
            with tempfile.TemporaryDirectory() as td:
                fname = os.path.join(td, 'tmp.pat')
                with open(fname, 'w') as config:
                    #write temporary file
                    write_pat_config(config, settings, settings_night)

                #apply to rocket
                self.rocket.load_pattern_config(fname, is_night='Night' in action)

            success = True
        else:
            success = False
            reason = 'Invalid action'

        response = json.dumps({'Success': success, 'Reason': reason})
        self.write(response)

class ScheduleHandler(tornado.web.RequestHandler):
    def initialize(self, scheduler):
        self.scheduler = scheduler

    def get(self):
        self.render('schedule.html', pages=NK_pages, page='schedule',
                    d_start=self.scheduler.schedule_settings['day_start'].strftime('%H:%M'),
                    d_end=self.scheduler.schedule_settings['day_end'].strftime('%H:%M'),
                    )

    def post(self):
        day_start = self.get_body_argument('start')
        day_end   = self.get_body_argument('end')

        self.scheduler.schedule_settings['day_start'] = datetime.datetime.strptime(day_start, '%H:%M').time()
        self.scheduler.schedule_settings['day_end'] = datetime.datetime.strptime(day_end, '%H:%M').time()

        #force update with new times
        self.scheduler.schedule_update()

        self.scheduler.write_config(config_file)

        self.redirect('schedule.html')


def gen_pat_js():
    print('Loading js template')
    loader = tornado.template.Loader(template_path)

    pat_js = loader.load("patterns.js").generate(patterns=patterns.info)

    js_path = os.path.join(static_path, 'patterns.js')

    with open(js_path, 'w') as js_file:
        print(f'Writing "{js_path}"')
        js_file.write(pat_js.decode('utf-8'))
    

class LightScheduler:

    save_keys = ('day_start', 'day_end')

    def __init__(self,rocket):
        self.schedule_settings = {
                                'day_start' : datetime.time(hour=6, minute=30),
                                'day_end'   : datetime.time(hour=12+9, minute=30),
                                'state'     : 'unknown',
                            }
        self.schedule_timer = None
        self.rocket=rocket

        #get a list of pattern config files
        self.patterns = find_patterns()
        #initialize current pattern
        self.current_pattern = None

    def set_config(self, cfg, **kwargs):
        #load pattern file
        self.rocket.load_pattern_config(cfg, **kwargs)
        #set config var
        self.current_pattern = cfg


    def schedule_update(self):
        # get current time
        current = datetime.datetime.now().time()

        #check if it's day time
        is_day = ( current > self.schedule_settings['day_start'] and current < self.schedule_settings['day_end'])

        new_state = 'day' if is_day else 'night'

        if new_state != self.schedule_settings['state']:

            if is_day:
                print('It\'s day now!')

                #set random pattern
                self.set_config(random.choice(self.patterns))
            else:
                print('It\'s night now!')

                if self.current_pattern is not None:
                    #set pattern
                    self.set_config(self.current_pattern, is_night=True)
                else:
                    #no pattern chosen, just set nightlight mode
                    self.rocket.set('nightlight', 'on')


        #update state
        self.schedule_settings['state'] = new_state

    def write_config(self, file='settings.cfg'):
        config = configparser.ConfigParser()

        config['schedule'] = {}
        for k, v in self.schedule_settings.items():
            if k in self.save_keys:
                #check if this is a time
                if isinstance(v, datetime.time):
                    config['schedule'][k] = v.strftime('%H:%M')
                else:
                    config['schedule'][k] = str('%H:%M')


        with open(file, 'w') as configfile:
            config.write(configfile)

    def load_config(self, file='settings.cfg'):

        if os.path.exists(file):
            config = configparser.ConfigParser()

            config.read(file)

            vals = {}

            for k,v in config['schedule'].items():
                #check what type to convert it to
                if isinstance(self.schedule_settings[k], datetime.time):
                    vals[k] = datetime.datetime.strptime(v, '%H:%M').time()
                elif isinstance(self.schedule_settings[k], str):
                    vals[k] = v

            #update all values at once
            self.schedule_settings |= vals

def find_patterns():
    patterns = glob.glob(os.path.join(pattern_dir, '*.pat'))
    return patterns

def main():
    parse_command_line()

    gen_pat_js()

    #create configuration dir
    os.makedirs(config_dir, exist_ok=True)

    rocket=NightKnight(options.serial,debug=options.serial_debug)
    LED_schedule = LightScheduler(rocket)
    #load config if it exists
    LED_schedule.load_config(config_file)

    handlers=[ (r"/", MainHandler,{'rocket':rocket}),
               (r"/home(?:\.html)?$", MainHandler,{'rocket':rocket}),
               (r"/index(?:\.html)?$", MainHandler,{'rocket':rocket}),
               (r"/pattern(?:\.html)?$", PatternHandler,{'rocket':rocket}),
               (r"/pattern_descriptions(?:\.html)?$", PatternDescHandler),
               (r"/pattern-descriptions(?:\.html)?$", PatternDescHandler),
               (r"/pattern-descriptions", PatternDescHandler),
               (r"/ADC(?:\.html)?$", ADCHandler,{'rocket':rocket}),
               (r"/nosecone(?:\.html)?$", NoseconeHandler,{'rocket':rocket}),
               (r"/chute(?:\.html)?$", ChuteHandler,{'rocket':rocket}),
               (r"/simulate(?:\.html)?$", SimulationHandler,{'rocket':rocket}),
               (r"/status(?:\.html)?$", StatusHandler,{'rocket':rocket}),
               (r"/altitude(?:\.html)?$", AltitudeHandler,{'rocket':rocket}),
               (r"/resets(?:\.html)?$", ResetsHandler,{'rocket':rocket}),
               (r"/settings(?:\.html)?$", SettingsHandler,{'rocket':rocket}),
               (r"/flight_pattern(?:\.html)?$", FlightPatternHandler,{'rocket':rocket}),
               (r"/nightlight(?:\.html)?$", NightlightHandler,{'rocket':rocket}),
               (r"/brightness(?:\.html)?$", BrightnessHandler,{'rocket':rocket}),
               (r"/parameter(?:\.html)?$", ParameterHandler,{'rocket':rocket}),
               (r"/server(?:\.html)?$", ServerHandler),
               (r"/schedule(?:\.html)?$", ScheduleHandler,{'scheduler':LED_schedule}),
               (r"/config(?:\.html)?$", ConfigHandler,{'scheduler':LED_schedule}),
               (r"/config-save(?:\.html)?$", ConfigSaveHandler,{'rocket':rocket}),
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

    #we just started, force an update
    LED_schedule.schedule_update()

    loop = tornado.ioloop.IOLoop.current()
    LED_schedule.schedule_timer = tornado.ioloop.PeriodicCallback(LED_schedule.schedule_update, 60e3)
    LED_schedule.schedule_timer.start()
    loop.start()


if __name__ == "__main__":
    main()
