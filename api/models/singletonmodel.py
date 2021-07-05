#!/usr/bin/sudo python3
# -*- coding: utf-8 -*-

class SingletonModel(type):
	_instances = {}

	def __call__(cls, *args, **kwargs):
		if cls not in cls._instances:
			cls._instances[cls] = super(SingletonModel, cls).__call__(*args, **kwargs)
		return cls._instances[cls]