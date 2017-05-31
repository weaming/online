from os import path
from tornado import ioloop, web

from socketHandler import EchoWebSocket


class MainHandler(web.RequestHandler):
    def get(self):
        self.render('index.html')


def make_app(deubg=False):
    return web.Application([
        (r"/", MainHandler),
        (r"/websocket", EchoWebSocket),
    ],
        debug=deubg,
        template_path=path.join(path.dirname(__file__), "template"),
        static_path=path.join(path.dirname(__file__), "static"),
    )


if __name__ == "__main__":
    app = make_app(deubg=True)
    port = 9999
    app.listen(port)
    print('http://localhost:%s' % port)
    ioloop.IOLoop.current().start()
