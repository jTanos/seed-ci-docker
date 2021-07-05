"""Web Server Gateway Interface"""

from api.src.app import flask_app
import eventlet
from eventlet import wsgi
import signal
from os import kill, getpid
import constants
from api.handlers.loghandler import LogHandler
from api.helpers.utilshelper import UtilsHelper

cert = UtilsHelper.resourcePath('api\\cert.pem')
key = UtilsHelper.resourcePath('api\\key.pem')

#################
# FOR PRODUCTION
#################
def start_server(**kwargs):
    """
        .. important:: Starting server...
    """
    try:
        ip, port = constants.WEB_API_HOST.split(':')
        # RUN HTTP
        # wsgi.server(eventlet.listen((ip, int(port))), flask_app)
        # RUN HTTPS
        wsgi.server(eventlet.wrap_ssl(eventlet.listen((ip, int(port))),
                              certfile=cert,
                              keyfile=key,
                              server_side=True), flask_app)
    except Exception as e:
        LogHandler.getCurrentClassLogger().exception("Error start_server. %s", e)

def stop_server():
    """
        .. important:: Server is shutting down...
    """
    kill(getpid(), signal.SIGINT)

# if __name__ == "__main__":
#     #################
#     # FOR DEVELOPMENT
#     #################
#     ip, port = constants.WEB_API_HOST.split(':')
#     ssl_context=(cert, key)
#     flask_app.run(host=ip, port=int(port), debug=True, ssl_context=ssl_context)