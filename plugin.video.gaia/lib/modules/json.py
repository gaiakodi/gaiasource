# -*- coding: utf-8 -*-

'''
	Gaia Add-on
	Copyright (C) 2016 Gaia

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

'''
Below are the execution times for different libraries for large JSON objects (3000 iterations).

			json			simplejson			simplejson			orjson				ujson				rapidjson
			(native)		(python)			(c-speedup)
			ms		%		ms		%			ms		%			ms		%			ms		%			ms		%
	loads	167598	1.0		191292	1.1414		193372	1.1538		143532	0.8564		191381	1.1419		203671	1.2152
	dumps	214197	1.0		221338	1.0333		214384	1.0009		36516	0.1705		100182	0.4677		95501	0.4459

orjson:
	Is by far the fastest.
	When executing once, everything works correctly. When executing it again (with a new process and Python invoker) Kodi freezes and crashes.
	Hence, not a reliable. At least for the old orjson version for Python 3.6.
rapidjson:
	Is the 2nd fastest.
	However, some of the wheels, especially manylinux, can be 1.6MB.
	All the differnt versions make the Gaia zip 30MB larger, so nhot a good option.
ujson:
	only slightly slower than rapidjson.
	Considerably smaller wheels.
	Increases the Gaia zip by 3.3MB.
'''

import json
from lib.modules.external import Importer

class Json(object):

	Separators		= (',', ':')	# Otherwise unnecessary spaces are added between the key and the value, increasing the JSON string size.
	Ujson			= None

	##############################################################################
	# INTERNAL
	##############################################################################

	@classmethod
	def _serializeObject(self, object):
		try: return object.dataExport()
		except: return object.__dict__

	@classmethod
	def _serializeString(self, object):
		try: return object.dataJson()
		except:
			try: return object.__json__()
			except: return object.__dict__

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def decode(self, data, default = None):
		# Always decode with the native library, since it is faster.
		return self.nativeDecode(data = data, default = default)

	@classmethod
	def encode(self, data, default = None):
		try: return self._ujsonEncode(data = data)
		except AttributeError: return self.nativeEncode(data = data, default = default)
		except: return default

	##############################################################################
	# NATIVE
	##############################################################################

	@classmethod
	def nativeDecode(self, data, default = None):
		try: return json.loads(data)
		except: return default

	@classmethod
	def nativeEncode(self, data, default = None):
		# 'default' must return a non-encoded object that can be JSON encoded.
		try: return json.dumps(data, default = self._serializeObject, separators = Json.Separators)
		except: return default

	##############################################################################
	# UJSON
	##############################################################################

	@classmethod
	def _ujsonDecode(self, data):
		return self.ujson().loads(data)

	@classmethod
	def _ujsonEncode(self, data):
		# Does not have a 'separators' parameter.
		# Ujson first tries to call __json__() on the object. If the returned value is not a string, an exception is thrown.
		# 'default' must return an already encoded string.
		return self.ujson().dumps(data, default = self._serializeString)

	@classmethod
	def ujsonDecode(self, data, default = None):
		try: return self._ujsonDecode(data = data)
		except: return default

	@classmethod
	def ujsonEncode(self, data, default = None):
		try: return self._ujsonEncode(data = data)
		except: return default

	@classmethod
	def ujson(self):
		if Json.Ujson is None:
			module = Importer.moduleUjson()
			Json.Ujson = module if module else False
		return Json.Ujson
