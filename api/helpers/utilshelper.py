#!/usr/bin/sudo python3
# -*- coding: utf-8 -*-

import fileinput
import sys
import os

class UtilsHelper(object):
    '''
    Static class para funcionalidades varias
    '''

    def __init__(self):
        if self.__class__ is UtilsHelper:
            raise Exception('No se puede instanciar una clase abstracta.')

    @staticmethod
    def getObjectToList(function, iterable):
        '''Function is expresion lambda : example "lambda x : x.key == value"
        \niterable is list.'''
        return next((x for x in iterable if function(x)), None)	

    @staticmethod	
    def getConfigToDictionary(listSearch, key, value):
        '''Retorna object en un diccionario.'''	
        if (any(x for x in listSearch if x[key] == value)):
            ret = [x for x in listSearch if x[key] == value][0]
        else:
            raise Exception("No se encontro el valor %s = %s en %s" %(key, str(value), listSearch))
        return ret

    @staticmethod
    def replaceTextInFile(file, searchExp, replaceExp):
        '''Remplaza el texto en el archivo indicado. Se usa para el de constantes.'''
        for line in fileinput.input(file, inplace=1):
            if searchExp in line.replace("\n", ""):
                line = line.replace(searchExp, replaceExp)
            sys.stdout.write(line)

    @staticmethod
    def isLinux():
        '''Retorna si la plataforma es linux.'''
        if 'linux' in sys.platform:
            return True
        return False

    @staticmethod
    def getBundleDir():
        '''Retorna la ruta donde se corre el ejecutable ya sea compilado o no.'''		
        if getattr(sys, 'frozen', False):
            # we are running in a bundle			
            bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))        	
            # bundle_dir = sys._MEIPASS
        else:
            # we are running in a normal Python environment
            #bundle_dir = os.path.dirname(os.path.abspath(__file__))		
            bundle_dir = os.getcwd()		
        return bundle_dir

    @staticmethod
    def resourcePath(relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        base_path = UtilsHelper.getBundleDir()
        return os.path.join(base_path, relative_path)

    @staticmethod
    def originalPath(relative_path):
        """Get absolute path to original"""
        base_path = os.getcwd()
        return os.path.join(base_path, relative_path)   

    @staticmethod
    def isBuildPyInstaller():
        '''Retorna si es compilacion con PyInstaller.'''		
        return getattr(sys, 'frozen', False)