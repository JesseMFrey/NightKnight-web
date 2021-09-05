#!/usr/bin/env python

import os.path
import asyncio
import tornado.escape
import tornado.ioloop
import tornado.locks
import tornado.web
import webcolors

from NightKnight_control import NightKnight

from tornado.options import define, options, parse_command_line

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=True, help="run in debug mode")
define("serial_debug", default=False, help="Debug serial communications")
define("serial", default='/dev/ttyUSB0', help="Serial port to use")

NK_pages=('home','pattern','ADC','nosecone','resets','settings','flight_pattern')

class MainHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket=rocket
    def get(self):
        self.render("home.html", pages=NK_pages,page='home')

class PatternHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket=rocket
    def get(self):
        #TODO : get pattern stuff here
        patterns,current_pat=self.rocket.get_patterns()
        val=self.rocket.get_value()
        brt,color=self.rocket.get_color()
        clists,currentlst=self.rocket.get_clists()
        nightlight = self.rocket.get_nightlight()
        self.render('pattern.html',pages=NK_pages,page='patterns',
                        patterns=patterns,
                        pat=current_pat,
                        value=val,
                        brightness=brt,
                        color=color,
                        clists=clists,
                        currentlst=currentlst,
                        nightlight = nightlight,
                    )

    def post(self):
        #self.set_header("Content-Type", "text/plain")
        #get color
        color=webcolors.hex_to_rgb(self.get_body_argument("color"))
        #get brightness
        brt=self.get_body_argument("brt")
        #set brigtness and color
        self.rocket.set_color(brt,color)
        #set value
        self.rocket.set_value(int(self.get_body_argument("val")))
        #set color list
        self.rocket.set_clist(self.get_body_argument("clist"))
        #set pattern
        self.rocket.set_pattern(self.get_body_argument("pattern"))

        self.redirect('pattern.html',True)


class ADCHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket=rocket
    def get(self):
        #TODO: get ADC readings
        adc_dat=self.rocket.read_ADC()
        self.render('ADC.html',pages=NK_pages,page='ADC',
                        adc_dat=adc_dat,
                   )

class NoseconeHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket=rocket
    def get(self):
        #TODO: get nosecone and chute values
        nc_info=self.rocket.get_NC()
        chute_info=self.rocket.get_chute()
        self.render('nosecone.html',pages=NK_pages,page='nosecone',
                        chute=chute_info,
                        nc=nc_info,
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
        self.rocket.set_NC(mode,val1,val2,t1,t2)

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
        self.rocket.set_chute(mode,val1,val2,t1,t2)

        self.redirect('nosecone.html')

class ResetsHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket=rocket
    def get(self):
        #TODO: get reset info
        self.render('resets.html',pages=NK_pages,page='resets',
                    rst_reason='Everything was wrong!',rst_num=1000)

class SettingsHandler(tornado.web.RequestHandler):
    def initialize(self, rocket):
        self.rocket=rocket
    def get(self):
        flash,ram=self.rocket.get_settings()
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
        patterns,current=self.rocket.get_flight_patterns()
        #get expected altitude
        altitude = self.rocket.get_altitude()

        self.render('flight_pattern.html',pages=NK_pages,page='flight_pattern',
                        patterns=patterns,
                        pat=current,
                        altitude = altitude,
                    )

    def post(self):
        #set pattern
        self.rocket.set_flight_pattern(self.get_body_argument("pattern"))

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
        self.rocket.set_altitude(float(altitude),units = units)

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
        self.rocket.set_nightlight(val)

        redir = self.get_body_argument("redirect", default = '')

        if redir:
            self.redirect(redir)


def main():
    parse_command_line()

    rocket=NightKnight(options.serial,debug=options.serial_debug)

    handlers=[ (r"/", MainHandler,{'rocket':rocket}),
               (r"/home\.html", MainHandler,{'rocket':rocket}),
               (r"/pattern\.html", PatternHandler,{'rocket':rocket}),
               (r"/ADC\.html", ADCHandler,{'rocket':rocket}),
               (r"/nosecone\.html", NoseconeHandler,{'rocket':rocket}),
               (r"/chute", ChuteHandler,{'rocket':rocket}),
               (r"/simulate", SimulationHandler,{'rocket':rocket}),
               (r"/altitude", AltitudeHandler,{'rocket':rocket}),
               (r"/resets\.html", ResetsHandler,{'rocket':rocket}),
               (r"/settings\.html", SettingsHandler,{'rocket':rocket}),
               (r"/flight_pattern\.html", FlightPatternHandler,{'rocket':rocket}),
               (r"/nightlight", NightlightHandler,{'rocket':rocket}),
               ]

    print(handlers)

    app = tornado.web.Application(
        handlers,
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        debug=options.debug,
    )
    app.listen(options.port)
    print(f'Starting server on port number {options.port}...')
    print(f'Open at http://127.0.0.1:{options.port}/index.html')
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
