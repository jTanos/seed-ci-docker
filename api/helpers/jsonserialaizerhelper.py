import jsonpickle
import json


class JsonSerialaizerHelper(object):

	def __init__(self):
		if self.__class__ is JsonSerialaizerHelper:
			raise Exception('No se puede instanciar una clase abstracta.')

	@staticmethod
	def objToJson(obj, unpicklable=True):
		"""Serializer this instance. Return json string."""		
		return jsonpickle.encode(obj,  unpicklable=unpicklable)

	@staticmethod
	def jsonToObj(data):
		return jsonpickle.decode(data)

	@staticmethod
	def objToDictionary(objects):
		"""Deserializer this instance or list instances. Return Dictionary."""
		jsonData = JsonSerialaizerHelper.objToJson(objects,False)
		return json.loads(jsonData)
