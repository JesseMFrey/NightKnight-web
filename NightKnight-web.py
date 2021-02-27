#!/usr/bin/env python

import asyncio
import tornado.escape
import tornado.ioloop
import tornado.locks
import tornado.web
import os.path

from tornado.options import define, options, parse_command_line

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=True, help="run in debug mode")

NK_pages=('home','pattern','ADC','nosecone','resets','settings','flight_pattern')

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("home.html", pages=NK_pages,page='home')

class PatternHandler(tornado.web.RequestHandler):
    def get(self):
        #TODO : get pattern stuff here
        self.render('pattern.html',pages=NK_pages,page='pattern')

class ADCHandler(tornado.web.RequestHandler):
    def get(self):
        #TODO: get ADC readings
        self.render('ADC.html',pages=NK_pages,page='ADC')

class NoseconeHandler(tornado.web.RequestHandler):
    def get(self):
        #TODO: get nosecone and chute values
        self.render('nosecone.html',pages=NK_pages,page='nosecone')

class ResetsHandler(tornado.web.RequestHandler):
    def get(self):
        #TODO: get reset info
        self.render('resets.html',pages=NK_pages,page='resets',
                    rst_reason='Everything was wrong!',rst_num=1000)

class SettingsHandler(tornado.web.RequestHandler):
    def get(self):
        #TODO: get settings info
        self.render('settings.html',pages=NK_pages,page='settings',
                    color='#FF0000',pat='pat',val=20,clist='list',fpat='pat')

class FlightPatternHandler(tornado.web.RequestHandler):
    def get(self):
        #TODO: get flight pattern info
        self.render('flight_pattern.html',pages=NK_pages,page='flight_pattern',
                    patterns=('pattern1','pattern2'))

def main():
    parse_command_line()

    handlers=[ (r"/", MainHandler),
               (r"/home\.html", MainHandler),
               (r"/pattern\.html", PatternHandler),
               (r"/ADC\.html", ADCHandler),
               (r"/nosecone\.html", NoseconeHandler),
               (r"/resets\.html", ResetsHandler),
               (r"/settings\.html", SettingsHandler),
               (r"/flight_pattern\.html", FlightPatternHandler),
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
