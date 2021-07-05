#!/usr/bin/sudo python3
# -*- coding: utf-8 -*-

import time
import signal
from api.handlers.loghandler import LogHandler
from api import wsgi

if __name__ == '__main__':
    
    try:
        wsgi.start_server()	
    except Exception as e:
        LogHandler.getCurrentClassLogger().exception("Error Main. %s", e)
    finally:
        wsgi.stop_server()