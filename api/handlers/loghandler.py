#!/usr/bin/sudo python3
# -*- coding: utf-8 -*-

import pymysql
import time
import logging
import constants
import os
from api.models.singletonmodel import SingletonModel

FORMAT = '%(levelname)s - %(name)s: %(asctime)-15s   \n-ProcessName: %(processName)s     \n-ThreadName: %(threadName)s   \n-Name: %(name)s   \n-Archivo: %(filename)s    \n-Function: %(funcName)s   \n-LineLogging: %(lineno)d     \n-Message: %(message)s\n'


class LogDBHandler(logging.Handler):
    '''
    Customized logging handler that puts logs to the database.
    pymssql required
    '''

    def __init__(self):
        logging.Handler.__init__(self)
        try:
            self.sql_conn = pymysql.connect(host=constants.HOST, port=constants.PORT, user=constants.USER, passwd=constants.PASS, db=constants.DBNAME)
            self.sql_cursor = self.sql_conn.cursor()
        except Exception as e:
            print(str(e))

    def emit(self, record):		
        if not constants.DEBUG and str(record.levelname) == 'DEBUG':
            return

        # tm = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.created))
        self.log_msg = record.message.strip() + '\n' + str(record.exc_text).replace('None', '').replace('NoneType', '')
        if str(record.levelname) != 'DEBUG':
            self.log_msg = self.log_msg + '\nProcesName: ' + record.processName + '\nThreadName: ' + record.threadName
        self.log_msg = self.log_msg.replace("'", '"')
        sql = """CALL logs_i(%s, %s, %s, %s)"""

        try:
            self.sql_cursor.execute(sql, (str(record.levelno), str(record.levelname), str(self.log_msg), str(record.name)))
            self.sql_conn.commit()
        except Exception as e:
            print(e)
            print(sql)
            print('CRITICAL DB ERROR! Logging to database not possible!')


# Python 3
class LogHandler(metaclass=SingletonModel):
    """Usar para loguear Exception, Info o Debug 'LogHandler.getCurrentClassLogger().debug(), LogHandler.getCurrentClassLogger().info(), LogHandler.getCurrentClassLogger().exception()'"""
    logger = None
    loggerPath = None

    def __init__(self, loggerPath=None):
        if loggerPath is None:
            self.loggerPath = os.getcwd() + "/logs"
        else:
            self.loggerPath = loggerPath

        if not os.path.exists(self.loggerPath):
            os.mkdir(self.loggerPath)

        # create logger with 'Raspberry'
        self.logger = logging.getLogger('App %s' % constants.HOST)
        # create formatter and add it to the handlers
        formatter = logging.Formatter(FORMAT)

        # Use "INFO set TRACE o DEBUG COMPLETE" alternative ERROR only ERRORES	
        self.logger.setLevel(logging.DEBUG)	

        # create file handler which logs even Exception messages
        self.fhe = logging.FileHandler(self.loggerPath + '/Exceptions-' + time.strftime("%Y-%m-%d", time.gmtime()) + '.log')
        self.fhe.setLevel(logging.ERROR)
        self.fhe.setFormatter(formatter)

        # create file handler which logs even debug messages		
        self.fhd = logging.FileHandler(self.loggerPath + '/Debugs-' + time.strftime("%Y-%m-%d", time.gmtime()) + '.log')
        self.fhd.setLevel(logging.DEBUG)
        self.fhd.setFormatter(formatter)

        # # create file handler which logs even traces messages
        # fhi = logging.FileHandler('logs/InfoTraces-' + time.strftime("%Y-%m-%d", time.gmtime()) + '.log')
        # fhi.setLevel(logging.INFO)
        # fhi.setFormatter(formatter)

        # create console handler with a higher log level
        self.ch = logging.StreamHandler()
        self.ch.setLevel(logging.DEBUG)
        self.ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        
        self.logger.addHandler(self.fhe)
        # self.logger.addHandler(fhi)

        self.logdb = None

        # add the handlers to the logger
        if constants.DEBUG:
            self.logger.addHandler(self.fhd)
        if constants.CONSOLE:
            self.logger.addHandler(self.ch)
        # LOGGING DATA BASE
        if constants.LOG_TO_DB:
            # create console handler with a higher log level
            self.logdb = LogDBHandler()
            self.logger.addHandler(self.logdb)
            
    def __changeHandlers(self):
        if constants.DEBUG:
            self.logger.addHandler(self.fhd)
        else:
            self.logger.removeHandler(self.fhd)

        if constants.CONSOLE:
            self.logger.addHandler(self.ch)
        else:
            self.logger.removeHandler(self.ch)
        
        if constants.LOG_TO_DB:
            if self.logdb is None:
                self.logdb = LogDBHandler()
            self.logger.addHandler(self.logdb)
        else:
            self.logger.removeHandler(self.logdb)

    @staticmethod
    def getCurrentClassLogger(loggerPath=None):
        return LogHandler(loggerPath).logger

    @staticmethod
    def resetCurrentClassLogger():		
        return LogHandler().__changeHandlers()
