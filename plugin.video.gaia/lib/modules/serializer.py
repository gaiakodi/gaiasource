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

from lib.modules.tools import Tools, Converter, Logger

class Serializer(object):

	def __init__(self):
		self.mData = None

	def data(self):
		return self.mData

	def dataSet(self, data):
		self.mData = data

	def dataUpdate(self, data, lists = False, unique = True):
		Tools.update(self.mData, data, lists = lists, unique = unique)

	def dataExport(self):
		try:
			# Make a deep copy.
			# Some classes, like Metadata, change/serialize their internal data during dataExportBefore(), that is changing Python objects to JSON objects.
			# If this function is called in a separate thread (eg: during caching), while another thread accesses the data between when dataExportBefore() and dataExportAfter() is called, code might fail since expected Python objects might temporarily be JSON.
			# UPDATE: This was removed, since there is an infinite recursion while deep copying during scraping (probably with Stream.dataExport()).
			# With this, there is also an issue to start playback of any stream.
			# This problem cannot be replicated anymore.
			# It previously occured sporadically while loading show menus, with exceptions in metadata.py saying that company.name() and/or person.name() cannot be called on a dictionary.
			# This was because while calling those functions from within company() and person(), sometimes those nested metadata objects (company/person) where not a Python object at the time of calling, but instead a dictionary, while the data was exported.
			# This problem seems to be gone. Maybe it has something to do with the fix in cache.py -> _cacheUpdate() where we now copy the data before starting the thread to save the data to disk.
			# If this is ever used again, also check dataSerialize() where copying the instance was removed, since it would otherwise be copied twice.
			#instance = Tools.copy(self, deep = True)
			instance = self

			data = instance.dataExportBefore()
			result = instance.dataCopy()
			instance.dataExportAfter(data)

			return result
		except: Logger.error()
		return None

	# Pure Virtual
	def dataExportBefore(self):
		return None

	# Pure Virtual
	def dataExportAfter(self, data = None):
		pass

	def dataImport(self, data):
		try:
			if Tools.isString(data): data = Converter.jsonFrom(data)
			elif Tools.isInstance(data, Serializer): data = data.dataCopy()
			data = self.dataImportBefore(data = data)
			self.dataUpdate(data = data)
			self.dataImportAfter(data = data)
			return True
		except:
			Logger.error()
			return False

	# Virtual
	def dataImportBefore(self, data = None):
		return data

	# Virtual
	def dataImportAfter(self, data = None):
		pass

	def dataCopy(self, deep = True):
		return Tools.copy(self.mData, deep = deep)

	def dataJson(self):
		return Converter.jsonTo(self.dataExport())

	@classmethod
	def dataSerialize(self, instance):
		if Tools.isArray(instance) and len(instance) > 0 and Tools.isInstance(instance[0], Serializer):
			return [self.dataSerialize(i) for i in instance]
		elif Tools.isInstance(instance, Serializer):
			return {
				'__class__' : instance.__class__.__name__,
				'__module__' : Tools.getModule(instance),

				# This seems to not be necessary anymor, due to the deep copying added in cache.py -> _cacheUpdate().
				# Read the comments above under dataExport() if this needs to be reabled.
				#'__data__' : Tools.copy(instance, deep = True).dataExport(),
				'__data__' : instance.dataExport(),
			}
		return None

	@classmethod
	def dataUnserialize(self, data):
		try:
			if Tools.isArray(data):
				result = []
				for i in data:
					item = self.dataUnserialize(i)
					result.append(i if item is None else item)
				return result
			else:
				instance = Tools.getInstance(data['__module__'], data['__class__'])
				instance.dataImport(data['__data__'])
				return instance
		except: pass
		return None

	# Tools.update()
	def get(self, key, default = None):
		try: return self.mData[key]
		except: return default

	# Tools.update()
	def items(self):
		try: return self.mData.items()
		except: return None

	def update(self, data):
		try: self.mData, Tools.update(self.mData, data, lists = True, unique = True)
		except: pass

	# Called from tools.Converter.jsonTo().
	def __json__(self):
		return self.dataJson()

	def __str__(self):
		return self.dataJson()

	def __getitem__(self, key):
		try: return self.mData[key]
		except: return None

	def __setitem__(self, key, value):
		self.mData[key] = value

	def __contains__(self, key):
		return key in self.mData
