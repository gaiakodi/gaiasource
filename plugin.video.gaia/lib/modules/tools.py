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

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import xbmcvfs
import xbmcgui

import sys
import os
import re
import hashlib
import time
import datetime

from lib.modules.concurrency import Pool, Lock
from lib.modules.json import Json

# When calling datetime.strptime() it works the first time, but then Python changes the function to None and calling it a second time does not work.
# This has been an issue since older Kodis with Python 2.7, and newer Kodi 21+ with Python 3.x.
# https://forum.kodi.tv/showthread.php?tid=112916&page=2
# https://bugs.python.org/issue27400
# This causes issues in eg Time.datetime().
class DateProxy(datetime.datetime):
	@staticmethod
	def strptime(string, format):
		return datetime.datetime(*(time.strptime(string, format)[0:6]))
datetime.datetime = DateProxy

class Time(object):

	# Use time.clock() instead of time.time() for processing time.
	# NB: Do not use time.clock(). Gives the wrong answer in timestamp() AND runs very fast in Linux. Hence, in the stream finding dialog, for every real second, Linux progresses 5-6 seconds.
	# http://stackoverflow.com/questions/85451/python-time-clock-vs-time-time-accuracy
	# https://www.tutorialspoint.com/python/time_clock.htm

	ModeSystem = 0 # time.time(). The system-wide time. This does not take into account when threads/processes are asleep/idle/interleaved.
	ModeProcessor = 1 # time.process_time() - How long a process is activley executed on the CPU.
	ModePerformance = 2 # time.perf_counter() - How much real time has passed, irrespective of CPU activity. Similar to time.time()
	ModeThread = 3 # time.clock_gettime(time.CLOCK_THREAD_CPUTIME_ID)
	ModeProcess = 4 # time.clock_gettime(time.CLOCK_PROCESS_CPUTIME_ID)
	ModeMonotonic = 5 # time.clock_gettime(time.CLOCK_MONOTONIC)
	ModeDefault = ModeSystem

	ZoneUtc = 'utc'
	ZoneLocal = 'local'

	FormatTimestamp = None
	FormatDateTime = '%Y-%m-%d %H:%M:%S'
	FormatDate = '%Y-%m-%d'
	FormatDateKodi = '%d/%m/%Y' # Kodi date input dialog.
	FormatTime = '%H:%M:%S'
	FormatTimeShort = '%H:%M'

	Timestamp = None

	def __init__(self, start = False, mode = ModeDefault):
		self.mStart = None
		self.mMode = mode
		if start: self.start()

	@classmethod
	def reset(self, settings = True):
		Time.Timestamp = None

	def start(self):
		self.mStart = self.time(mode = self.mMode)
		return self.mStart

	def restart(self):
		self.mStart = None
		return self.start()

	def elapsed(self, milliseconds = False):
		if self.mStart is None: self.mStart = self.time(mode = self.mMode)
		result = (self.time(mode = self.mMode) - self.mStart)
		if milliseconds: result *= 1000
		return int(result)

	def expired(self, expiration):
		return self.elapsed() >= expiration

	@classmethod
	def sleep(self, seconds):
		# NB: Use the sleep() function of xbmc instead of Python's native time module.
		# Otherwise in player.py -> keepPlaybackAlive(), the sleep() in the loop causes Kodi's player events, like onPlayBackStopped(), not to fire/execute, and there are a bunch of other problems in the Player class.
		# Not sure why this is the case.
		#time.sleep(seconds)
		xbmc.sleep(int(seconds * 1000))

	@classmethod
	def sleepRandom(self, start, end):
		seconds = Math.random(start, end)
		self.sleep(seconds)

	@classmethod
	def integer(self, date = None):
		if date is None: date = self.format(format = Time.FormatDate)
		return int(Regex.remove(data = date, expression = '[^\d]', all = True))

	@classmethod
	def time(self, mode = ModeThread):
		try:
			if mode == Time.ModeSystem:
				return time.time()
			elif mode == Time.ModeProcessor:
				return time.process_time()
			elif mode == Time.ModePerformance:
				return time.perf_counter()
			elif mode == Time.ModeThread:
				try: return time.clock_gettime(time.CLOCK_THREAD_CPUTIME_ID) # Only available on Unix.
				except: time.process_time()
			elif mode == Time.ModeProcess:
				try: return time.clock_gettime(time.CLOCK_PROCESS_CPUTIME_ID) # Only available on Unix.
				except: time.process_time()
			elif mode == Time.ModeMonotonic:
				try: return time.clock_gettime(time.CLOCK_MONOTONIC) # Only available on Unix.
				except:
					try: time.monotonic()
					except: pass
		except: Logger.error()
		return time.time()

	# UTC timestamp
	# iso: Convert ISO to UTC timestamp.
	# utc=False: interpret the date string without a timezone (eg 2024-10-01) as a local date, which could cause a few hours offset from UTC. utc=True: interpret the date string as a UTC date.
	@classmethod
	def timestamp(self, fixedTime = None, format = None, iso = False, utc = False, milliseconds = False, cached = False):
		if cached:
			if Time.Timestamp is None: Time.Timestamp = self.timestamp(cached = False)
			return int(Time.Timestamp * 1000) if milliseconds else Time.Timestamp

		if iso:
			if not fixedTime: return 0

			delimiter = -1
			if not fixedTime.endswith('Z'):
				delimiter = fixedTime.rfind('+')
				if delimiter == -1: delimiter = fixedTime.rfind('-')

			if delimiter >= 0:
				stamp = fixedTime[:delimiter]
				sign = fixedTime[delimiter]
				zone = fixedTime[delimiter + 1:]
			else:
				stamp = fixedTime
				zone = None

			if stamp.find('.') > -1: stamp = stamp[:stamp.find('.')]
			try: date = datetime.datetime.strptime(stamp, '%Y-%m-%dT%H:%M:%S')
			except TypeError: date = datetime.datetime(*(time.strptime(stamp, '%Y-%m-%dT%H:%M:%S')[0:6]))

			difference = datetime.timedelta()
			if zone:
				hours, minutes = zone.split(':')
				hours = int(hours)
				minutes = int(minutes)
				if sign == '-':
					hours = -hours
					minutes = -minutes
				difference = datetime.timedelta(hours = hours, minutes = minutes)

			delta = date - difference - datetime.datetime.utcfromtimestamp(0)
			try: seconds = delta.total_seconds() # Works only on 2.7.
			except: seconds = delta.seconds + (delta.days * 86400) # Close enough.
			return (int(seconds) * 1000) if milliseconds else int(seconds)
		else:
			if fixedTime is None:
				# Do not use time.clock(), gives incorrect result for search.py
				return int(time.time() * 1000) if milliseconds else int(time.time())
			else:
				if format:
					fixedTime = self.datetime(fixedTime, format = format, utc = utc)
					if not fixedTime: return 0

				function1 = None
				function2 = None
				if utc:
					try:
						import calendar
						function1 = calendar.timegm
					except: pass
				try: function2 = time.mktime
				except: pass

				try: return int(function1(fixedTime.timetuple()) * 1000) if milliseconds else int(function1(fixedTime.timetuple()))
				except:
					try: return int(function2(fixedTime.timetuple()) * 1000) if milliseconds else int(function2(fixedTime.timetuple()))
					except:
						# Somtimes mktime fails (mktime argument out of range), which seems to be an issue with very large dates (eg 2120-02-03) on Android.
						try: return int(time.strftime('%s', fixedTime) * 1000) if milliseconds else int(time.strftime('%s', fixedTime))
						except: return 0

	@classmethod
	def format(self, timestamp = None, format = FormatDateTime, local = None):
		if timestamp is None: timestamp = self.timestamp()

		# Windows cannot handle negative timestamps.
		# https://github.com/arrow-py/arrow/issues/675
		if timestamp < 0: date = datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds = timestamp)
		else: date = datetime.datetime.utcfromtimestamp(timestamp)

		if local:
			from lib.modules.external import Importer
			pytz = Importer.modulePytz()
			date = pytz.utc.localize(date).astimezone(pytz.timezone(self.zone()))
		return date.strftime(format)

	# datetime object from string.
	# utc=False: interpret a date string without a timezone (eg 2024-10-01) as a local date. utc=True: interpret the date string as a UTC date.
	@classmethod
	def datetime(self, string, format = FormatDateTime, utc = False):
		# Python has had a bug for years, that changes the function datetime.datetime.strptime to None after it was called the first time.
		# http://forum.kodi.tv/showthread.php?tid=112916
		try:
			return datetime.datetime.strptime(string, format)
		except:
			try:
				# This should not happen anymore, due to the fix with DateProxy.
				# But still leave herte in case there are other issues, like the function notr exisiting in some older Python or Android versions.
				function1 = None
				function2 = None
				if utc:
					try:
						import calendar
						function1 = calendar.timegm
					except: pass
				try: function2 = time.mktime
				except: pass

				try: return datetime.datetime.fromtimestamp(function1(time.strptime(string, format)))
				except: return datetime.datetime.fromtimestamp(function2(time.strptime(string, format)))
			except:
				# Somtimes mktime fails (mktime argument out of range), which seems to be an issue with very large dates (eg 2120-02-03) on Android or dates before 1970 on Windows.
				return None

	@classmethod
	def delta(self, weeks = 0, days = 0, hours = 0, minutes = 0, seconds = 0, milliseconds = 0, microseconds = 0):
		return datetime.timedelta(weeks = weeks, days = days, hours = hours, minutes = minutes, seconds = seconds, milliseconds = milliseconds, microseconds = microseconds)

	@classmethod
	def year(self, timestamp = None):
		if timestamp is None: return datetime.datetime.now().year
		else: return datetime.datetime.utcfromtimestamp(timestamp).year

	@classmethod
	def month(self, timestamp = None):
		if timestamp is None: return datetime.datetime.now().month
		else: return datetime.datetime.utcfromtimestamp(timestamp).month

	@classmethod
	def past(self, seconds = 0, minutes = 0, hours = 0, days = 0, months = 0, years = 0, timestamp = None, format = FormatTimestamp, local = None, utc = False):
		if timestamp is None: timestamp = self.timestamp(utc = utc)
		result = timestamp - seconds - (minutes * 60) - (hours * 3600) - (days * 86400) - (months * 2592000) - (years * 31557600)
		if not format == self.FormatTimestamp: result = self.format(timestamp = result, format = format, local = local)
		return result

	@classmethod
	def future(self, seconds = 0, minutes = 0, hours = 0, days = 0, months = 0, years = 0, timestamp = None, format = FormatTimestamp, local = None, utc = False):
		if timestamp is None: timestamp = self.timestamp(utc = utc)
		result = timestamp + seconds + (minutes * 60) + (hours * 3600) + (days * 86400) + (months * 2592000) + (years * 31557600)
		if not format == self.FormatTimestamp: result = self.format(timestamp = result, format = format, local = local)
		return result

	@classmethod
	def zone(self, country = None, all = False):
		if country:
			from lib.modules.external import Importer
			pytz = Importer.modulePytz()
			zones = pytz.country_timezones(country)
			if zones:
				if not all: return zones[0]
				else: return zones
			return None
		else:
			if time.daylight: offsetHour = time.altzone / 3600
			else: offsetHour = time.timezone / 3600
			return 'Etc/GMT%+d' % offsetHour

	@classmethod
	def offset(self, zone = None, country = None, all = False):
		from lib.modules.external import Importer
		pytz = Importer.modulePytz()

		if not zone: zone = self.zone(country = country, all = False)
		if Tools.isArray(zone): return [datetime.datetime.now(pytz.timezone(i)).strftime('%z') for i in zone]
		else: return datetime.datetime.now(pytz.timezone(zone)).strftime('%z')

	@classmethod
	def convert(self, stringTime, stringDay = None, abbreviate = False, formatInput = FormatTimeShort, formatOutput = None, zoneFrom = ZoneUtc, zoneTo = ZoneLocal):
		from lib.modules.external import Importer
		pytz = Importer.modulePytz()

		result = ''
		try:
			# If only time is given, the date will be set to 1900-01-01 and there are conversion problems if this goes down to 1899.
			if formatInput == '%H:%M':
				# Use current datetime (now) in order to accomodate for daylight saving time.
				stringTime = '%s %s' % (datetime.datetime.now().strftime('%Y-%m-%d'), stringTime)
				formatNew = '%Y-%m-%d %H:%M'
			else:
				formatNew = formatInput

			if zoneFrom == Time.ZoneUtc: zoneFrom = pytz.timezone('UTC')
			elif zoneFrom == Time.ZoneLocal: zoneFrom = pytz.timezone(self.zone())
			else: zoneFrom = pytz.timezone(zoneFrom)

			if zoneTo == Time.ZoneUtc: zoneTo = pytz.timezone('UTC')
			elif zoneTo == Time.ZoneLocal: zoneTo = pytz.timezone(self.zone())
			else: zoneTo = pytz.timezone(zoneTo)

			timeobject = self.datetime(string = stringTime, format = formatNew)

			if stringDay:
				stringDay = stringDay.lower()
				if stringDay.startswith('mon'): weekday = 0
				elif stringDay.startswith('tue'): weekday = 1
				elif stringDay.startswith('wed'): weekday = 2
				elif stringDay.startswith('thu'): weekday = 3
				elif stringDay.startswith('fri'): weekday = 4
				elif stringDay.startswith('sat'): weekday = 5
				else: weekday = 6
				weekdayCurrent = datetime.datetime.now().weekday()
				timeobject += datetime.timedelta(days = weekday) - datetime.timedelta(days = weekdayCurrent)

			timeobject = zoneFrom.localize(timeobject)
			timeobject = timeobject.astimezone(zoneTo)

			if not formatOutput: formatOutput = formatInput

			stringTime = timeobject.strftime(formatOutput)
			if stringDay:
				import calendar
				if abbreviate: stringDay = calendar.day_abbr[timeobject.weekday()]
				else: stringDay = calendar.day_name[timeobject.weekday()]
				return (stringTime, stringDay)
			else:
				return stringTime
		except:
			Logger.error()
			return stringTime


class Copier(object):

	Dispatcher = None

	@classmethod
	def _copyList(self, data, dispatch):
	    result = data.copy()
	    for index, item in enumerate(result):
	        copy = dispatch.get(type(item))
	        if not copy is None: result[index] = copy(data = item, dispatch = dispatch)
	    return result

	@classmethod
	def _copyDict(self, data, dispatch):
	    result = data.copy()
	    for key, value in result.items():
	        copy = dispatch.get(type(value))
	        if not copy is None: result[key] = copy(data = value, dispatch = dispatch)
	    return result

	@classmethod
	def copy(self, data):
		if Copier.Dispatcher is None:
			Copier.Dispatcher = {
				list : self._copyList,
				dict : self._copyDict,
			}
		copy = Copier.Dispatcher.get(type(data))
		if copy is None: return data
		else: return copy(data = data, dispatch = Copier.Dispatcher)


class Tools(object):

	@classmethod
	def get(self, data, *args, **kwargs):
		try:
			for i in args: data = data[i]
			return data
		except:
			return kwargs.get('default')

	@classmethod
	def copy(self, instance, deep = True, fast = True):
		# Deep copy is slow in Python.
		# https://stackoverflow.com/questions/45858084/what-is-a-fast-pythonic-way-to-deepcopy-just-data-from-a-python-dict-or-list
		# When using "fast = True", the data must be primitive (no special objects that are not part of the standard Python data types), and cannot contain recursive structures.
		# UPDATE: The fast copy option does not seem to be that much faster. Disable by default.
		# UPDATE 2: The fast copy on 1000s of show metadata is 2-3 times faster. Enable by default.

		if deep and fast:
			return Copier.copy(data = instance)
		else:
			import copy
			return copy.deepcopy(instance) if deep else copy.copy(instance)

	# inverse=True: when merging lists, do structure2+structure1 instead of structure1+structure2.
	@classmethod
	def update(self, structure1, structure2, none = True, lists = False, unique = True, inverse = False):
		attribute = unique if Tools.isString(unique) or Tools.isArray(unique) else None
		if not structure1 is None and not structure2 is None:
			for key, value in structure2.items():
				if not none and key in structure1 and value is None: pass
				elif not key in structure1 or structure1[key] is None: structure1[key] = value
				elif Tools.isDictionary(value):
					structure1[key] = self.update(structure1 = structure1.get(key, {}), structure2 = value, none = none, lists = lists, unique = unique, inverse = inverse)
				elif lists and Tools.isArray(value):
					structure1[key] = (value + structure1.get(key, [])) if inverse else (structure1.get(key, []) + value)
					if unique: structure1[key] = self.listUnique(structure1[key], attribute = attribute, update = True, none = none, lists = lists, unique = unique)
				else: structure1[key] = value
		return structure1

	@classmethod
	def type(self, variable):
		return type(variable)

	@classmethod
	def id(self, variable):
		return id(variable)

	@classmethod
	def list(self, variable):
		return list(variable)

	@classmethod
	def replaceInsensitive(self, data, value, replacement = ''):
		index1 = 0
		while index1 < len(data):
			index2 = data.lower().find(value.lower(), index1)
			if index2 == -1: return data
			data = data[:index2] + replacement + data[index2 + len(value):]
			index1 = index2 + len(replacement)
		return data

	# Wether or not the instance object has a given attribute (either a variable or function).
	@classmethod
	def hasAttribute(self, instance, name):
		return hasattr(instance, name)

	# Wether or not the instance object has a given variable.
	@classmethod
	def hasVariable(self, instance, name):
		attribute = getattr(instance, name, None)
		return not attribute is None and not callable(attribute)

	# Wether or not the instance object has a given function.
	@classmethod
	def hasFunction(self, instance, name):
		attribute = getattr(instance, name, None)
		return not attribute is None and callable(attribute)

	@classmethod
	def getVariable(self, instance, name):
		return getattr(instance, name, None)

	# Returns the function pointer of an object.
	@classmethod
	def getFunction(self, instance, name):
		return getattr(instance, name, None)

	# Returns the pointer to a class.
	@classmethod
	def getClass(self, instance, name):
		return getattr(instance, name, None)

	# Either provide an instance
	@classmethod
	def getInstance(self, instance, name):
		try:
			if Tools.isString(instance):
				import importlib
				instance = importlib.import_module(instance)
			return self.getClass(instance = instance, name = name)()
		except: return None

	# Returns the module import string from a class or instance.
	@classmethod
	def getModule(self, instance):
		return instance.__module__

	@classmethod
	def getParameters(self, function, internal = False):
		result = list(function.__code__.co_varnames[:function.__code__.co_argcount])
		if not internal: result.remove('self')
		return result

	@classmethod
	def isFunction(self, function):
		return callable(function)

	# Executes a function of an object.
	@classmethod
	def executeFunction(self, instance, name, *args, **kwargs):
		return self.getFunction(instance = instance, name = name)(*args, **kwargs)

	# Remove special characters (non-alpha-numeric).
	# Do not use [^\w\d], since it removes unicode alpha characters.
	# \p is not supported in Python's re module.
	# Use Python's builtin function instead.
	@classmethod
	def replaceNotAlphaNumeric(self, data, replace = ''):
		try:
			for char in data:
				if not char.isalnum() and not char == replace:
					data = data.replace(char, replace)
		except: pass
		return data

	# Remove special characters (non-alpha).
	@classmethod
	def replaceNotAlpha(self, data, replace = ''):
		try:
			for char in data:
				if not char.isalpha() and not char == replace:
					data = data.replace(char, replace)
		except: pass
		return data

	@classmethod
	def dictionaryGet(self, dictionary, keys, merge = False, default = None):
		try:
			result = dictionary
			if Tools.isArray(keys):
				if merge:
					for key in keys:
						if Tools.isArray(result):
							items = []
							for item in result:
								if Tools.isArray(item[key]): items.extend(item[key])
								else: items.append(item[key])
							result = items
						else:
							result = result[key]
				else:
					for key in keys: result = result[key]
			else:
				if merge and Tools.isArray(result):
					items = []
					for item in result:
						if Tools.isArray(item[keys]): items.extend(item[keys])
						else: items.append(item[keys])
					result = items
				else:
					result = result[keys]
			return result
		except:
			return default

	@classmethod
	def dictionarySet(self, dictionary, keys, value):
		for key in keys[:-1]:
			 dictionary = dictionary.setdefault(key, {})
		dictionary[keys[-1]] = value

	@classmethod
	def dictionaryMerge(self, dictionary1, dictionary2, copy = True, none = True):
		if copy: result = self.copy(dictionary1)
		else: result = dictionary1
		if none: result.update((key, value) for key, value in dictionary2.items() if not value is None)
		else: result.update(dictionary2)
		return result

	@classmethod
	def dictionaryEqual(self, dictionary1, dictionary2, keys = None):
		if not keys: keys = self.listUnique(list(dictionary1.keys()) + list(dictionary2.keys()))
		equal = True
		for key in keys:
			if not dictionary1[key] == dictionary2[key]:
				equal = False
				break
		return equal

	@classmethod
	def listUnique(self, data, attribute = None, update = False, none = True, lists = False, unique = True):
		try:
			if attribute:
				result = []
				if update:
					seen = {}
					for i in range(len(data)):
						item = data[i]
						key = self.dictionaryGet(dictionary = item, keys = attribute)
						if key in seen:
							if self.isStructure(item):
								Tools.update(result[seen[key]], item, none = none, lists = lists, unique = unique)
							else:
								result[seen[key]] = item
						else:
							seen[key] = i
							result.append(item)
				else:
					seen = set()
					add = seen.add
					result = []
					for i in data:
						key = self.dictionaryGet(dictionary = i, keys = attribute)
						if not key in seen:
							result.append(i)
							add(key)
				return result
			elif len(data) > 0 and self.isDictionary(data[0]):
				result = []
				for i in data:
					if not i in result: result.append(i)
				return result
			elif len(data) > 0 and self.isList(data[0]):
				return [list(j) for j in set(tuple(i) for i in data)]
			else:
				seen = set()
				add = seen.add
				return [i for i in data if not (i in seen or add(i))]
		except:
			Logger.error()
			return data

	@classmethod
	def listFlatten(self, data, recursive = True):
		result = []
		for i in data:
			if self.isArray(i):
				if recursive: i = self.listFlatten(data = i, recursive = recursive)
				result.extend(i)
			else: result.append(i)
		return result

	@classmethod
	def listSort(self, data, key = None, reverse = False, inplace = False):
		if inplace:
			data.sort(key = key, reverse = reverse)
			return data
		else:
			return sorted(data, key = key, reverse = reverse)

	@classmethod
	def listReverse(self, data, inplace = False):
		if inplace:
			data.reverse()
			return data
		else:
			return list(reversed(data)) # reversed() returns an iterator.

	@classmethod
	def listSplit(self, data, size = 1):
		for i in range(0, len(data), size):
			yield data[i : i + size]

	@classmethod
	def listShuffle(self, data, copy = False):
		import random
		if copy: data = self.copy(data, deep = False)
		random.shuffle(data)
		return data

	@classmethod
	def listInterleave(self, *lists):
		from itertools import zip_longest
		return [y for x in zip_longest(*lists) for y in x if y is not None]

	@classmethod
	def listConsecutive(self, data):
		if not data: return None
		return data == list(range(min(data), max(data) + 1))

	@classmethod
	def listChunk(self, data, chunk = 10):
		return [data[i : i + chunk] for i in range(0, len(data), chunk)]

	# Randomly pick an item from a list.
	@classmethod
	def listPick(self, data, count = 1, remove = False, weights = None):
		import random
		if remove:
			# Not very efficient. This operation is O(n) or more specifically O(count*n).
			# https://stackoverflow.com/questions/10048069/what-is-the-most-pythonic-way-to-pop-a-random-element-from-a-list
			if count > 1:
				result = []
				for i in range(count):
					result.append(data.pop(random.randint(0, len(data) - 1)))
				return result
			else:
				return data.pop(random.randint(0, len(data) - 1))
		else:
			# If the weight total is 0, choices() throws an exception.
			# ValueError: Total of weights must be greater than zero.
			if not weights is None and sum(weights) == 0: return random.choices(data, k = count)

			if count > 1 or weights: return random.choices(data, k = count, weights = weights)
			else: return random.choice(data)

	# Pick the most frequent/common element in the list.
	@classmethod
	def listCommon(self, data, count = 1):
		from collections import Counter
		result = Counter(data).most_common(count)
		if result: result = [i[0] for i in result]
		if count == 1: return result[0] if result else None
		else: return result

	@classmethod
	def listCount(self, data, value):
		return data.count(value)

	# Get middle value from list.
	@classmethod
	def listMiddle(self, data, sort = False):
		if sort: data = self.listSort(data)
		index = int((len(data) - 1) / 2)
		return data[index]

	@classmethod
	def listMean(self, data):
		return float(sum(data)) / len(data)

	@classmethod
	def listIndex(self, data, value, default = -1):
		try: return data.index(value)
		except: return default

	@classmethod
	def stringSplit(self, value, length, join = None):
		result = [value[i : i + length] for i in range(0, len(value), length)]
		if not join is None: result = join.join(result)
		return result

	# Either provide alphabet or uppercase/lowercase/digits.
	@classmethod
	def stringRandom(self, length = 8, alphabet = None, uppercase = True, lowercase = True, digits = True, symbols = False):
		import random
		if not alphabet:
			import string
			alphabet = ''
			if uppercase: alphabet += string.ascii_uppercase
			if lowercase: alphabet += string.ascii_lowercase
			if digits: alphabet += string.digits
			if symbols: alphabet += string.punctuation
		return ''.join(random.choice(alphabet) for i in range(length))

	@classmethod
	def stringRemovePrefix(self, data, remove):
		# str.removeprefix() is only avilable in Python 3.9+
		if data.startswith(remove): data = data[len(remove):]
		return data

	@classmethod
	def stringRemoveSuffix(self, data, remove):
		# str.removesuffix() is only avilable in Python 3.9+
		if data.endswith(remove): data = data[:len(remove)]
		return data

	@classmethod
	def stringRemoveAffix(self, data, remove = None, prefix = None, suffix = None):
		if remove: data = self.stringRemoveSuffix(data = self.stringRemovePrefix(data = data, remove = remove), remove = remove)
		if prefix: data = self.stringRemovePrefix(data = data, remove = prefix)
		if suffix: data = self.stringRemoveSuffix(data = data, remove = suffix)
		return data

	@classmethod
	def stringAscii(self, data):
		try: data.encode('ascii')
		except UnicodeEncodeError: return False
		else: return True

	@classmethod
	def isClass(self, value):
		return isinstance(value, type)

	@classmethod
	def isInstance(self, value, type):
		return isinstance(value, type)

	@classmethod
	def isBoolean(self, value):
		return isinstance(value, bool)

	@classmethod
	def isBytes(self, value):
		return isinstance(value, bytes)

	@classmethod
	def isString(self, value):
		try: return isinstance(value, (str, bytes))
		except:
			try: return isinstance(value, (basestring, unicode))
			except: pass
		return False

	@classmethod
	def isInteger(self, value, bool = False):
		if not bool and self.isBoolean(value): return False
		return isinstance(value, int)

	@classmethod
	def isFloat(self, value):
		return isinstance(value, float)

	@classmethod
	def isNumber(self, value, bool = False):
		if not bool and self.isBoolean(value): return False
		return isinstance(value, (int, float))

	# Check if string is numeric.
	# Floats and negative numbers are not considered numeric if "full = False".
	@classmethod
	def isNumeric(self, value, full = False):
		if full:
			return Regex.match(data = value, expression = '^[\-\+]?\d+(?:\.\d*)?$', cache = True)
		else:
			try: return value.isnumeric()
			except: return False

	@classmethod
	def isNumericInteger(self, value, exact = False):
		return Regex.match(data = value, expression = '^[\-\+]?\d+$' if exact else '^[\-\+]?\d+(?:\.\d*)?$', cache = True)

	@classmethod
	def isNumericFloat(self, value, exact = False):
		return Regex.match(data = value, expression = '^[\-\+]?\d+(?:\.\d*)$' if exact else '^[\-\+]?\d+$', cache = True)

	# Check if string is alphabetic.
	@classmethod
	def isAlphabetic(self, value):
		try: return value.isalpha()
		except: return False

	# Check if string is alphabetic or numeric.
	@classmethod
	def isAlphabeticNumeric(self, value):
		try: return value.isalnum()
		except: return False

	@classmethod
	def isList(self, value):
		return isinstance(value, list)

	@classmethod
	def isTuple(self, value):
		return isinstance(value, tuple)

	@classmethod
	def isArray(self, value):
		return isinstance(value, (list, tuple))

	@classmethod
	def isDictionary(self, value):
		return isinstance(value, dict)

	@classmethod
	def isStructure(self, value):
		return isinstance(value, (dict, list, tuple))


class Regex(object):

	FlagNone			= 0
	FlagCaseInsensitive	= re.IGNORECASE
	FlagMultiLines		= re.MULTILINE
	FlagAllLines		= re.DOTALL

	FlagsDefault 		= FlagCaseInsensitive

	Symbol				= '[\-\–\!\$\%%\^\&\*\(\)\_\+\|\~\=\`\{\}\\\[\]\:\"\;\'\<\>\?\,\.\\\/]'
	Nonalpha			= '[\d\s\-\–\!\$\%%\^\&\*\(\)\_\+\|\~\=\`\{\}\\\[\]\:\"\;\'\<\>\?\,\.\\\/]'

	Cache				= {}

	@classmethod
	def expression(self, expression, flags = FlagsDefault, cache = False):
		if Tools.isString(expression):
			if cache:
				try:
					id = expression + '_' + str(flags)
					return Regex.Cache[id]
				except:
					compiled = re.compile(expression, flags = flags)
					Regex.Cache[id] = compiled
					return compiled
			else:
				return re.compile(expression, flags = flags)
		else:
			return expression # Already compiled expression.

	@classmethod
	def escape(self, data):
		return re.escape(data)

	@classmethod
	def match(self, data, expression, flags = FlagsDefault, cache = False):
		if cache: return bool(self.expression(expression = expression, flags = flags, cache = cache).search(data))
		else: return bool(re.search(expression, data, flags = flags))

	@classmethod
	def search(self, data, expression, all = False, flags = FlagsDefault, cache = False):
		try:
			if all:
				if cache: return self.expression(expression = expression, flags = flags, cache = cache).findall(data)
				else: return re.findall(expression, data, flags = flags)
			else:
				if cache: return self.expression(expression = expression, flags = flags, cache = cache).search(data)
				else: return re.search(expression, data, flags = flags)
		except: return None

	@classmethod
	def index(self, data, expression, group = None, all = False, flags = FlagsDefault, cache = False, start = True, end = False):
		indexStart = None
		indexEnd = None
		try:
			result = self.search(data = data, expression = expression, all = all, flags = flags, cache = cache)
			if group is None:
				indexStart = result.start()
				indexEnd = result.end()
			else:
				indexStart = result.start(group)
				indexEnd = result.end(group)
		except: pass
		if start and end: return (indexStart, indexEnd)
		elif start: return indexStart
		elif end: return indexEnd
		else: return None

	@classmethod
	def extract(self, data, expression, group = 1, all = False, flags = FlagsDefault, cache = False):
		try:
			if all:
				if cache: match = self.expression(expression = expression, flags = flags, cache = cache).findall(data)
				else: match = re.findall(expression, data, flags = flags)
				if group is None: return match
				else: return match[group]
			else:
				if cache: match = self.expression(expression = expression, flags = flags, cache = cache).search(data)
				else: match = re.search(expression, data, flags = flags)
				if group is None: return match.groups()
				else: return match.group(group)
		except: return None

	@classmethod
	def replace(self, data, expression, replacement, group = None, all = False, flags = FlagsDefault, cache = False):
		if group:
			if all:
				offset = 0
				if cache: iterator = self.expression(expression = expression, flags = flags, cache = cache).finditer(data)
				else: iterator = re.finditer(expression, data, flags = flags)
				for match in iterator:
					if match:
						start = match.start(group)
						end = match.end(group)
						data = data[:start + offset] + replacement + data[end + offset:]
						offset += len(replacement) - (end - start)
			else:
				match = self.search(data = data, expression = expression, flags = flags)
				if match: data = data[:match.start(group)] + replacement + data[match.end(group):]
			return data
		else:
			if all is True: return re.sub(expression, replacement, data, flags = flags)
			else: return re.sub(expression, replacement, data, count = all if Tools.isInteger(all, bool = False) else 1, flags = flags)

	@classmethod
	def remove(self, data, expression, group = None, all = False, flags = FlagsDefault, cache = False):
		return self.replace(data = data, expression = expression, replacement = '', group = group, all = all, flags = flags, cache = cache)

	@classmethod
	def split(self, data, expression, flags = FlagsDefault, cache = False):
		if cache: return self.expression(expression = expression, flags = flags, cache = cache).split(data)
		else: return re.split(expression, data, flags = flags)


class JavaScript(object):

	Lock = Lock()

	# variable: return the value of a specific variable. Otherwise return whatever the script returns.
	@classmethod
	def execute(self, code, variable = None):
		# When executing/parsing multiple code snippets from multiple threads at the same time using EvalJs, only one execution will succeed.
		# EvalJs probably uses an interal cache which gets overwritten but the code from multiple threads.
		# eval_js does not have this problem and can be executed in parallel. However, when using a lock, it is still about 50% faster than without a lock.
		try:
			JavaScript.Lock.acquire()
			if variable is None:
				from lib.modules.external import Importer
				evalJs = Importer.moduleJs2PyEval1()
				return evalJs(code)
			else:
				from lib.modules.external import Importer
				evalJs = Importer.moduleJs2PyEval2()
				context = evalJs()
				context.execute(code)
				return Tools.getVariable(context, variable)
		except:
			Logger.error()
			return None
		finally:
			JavaScript.Lock.release()


class Math(object):

	# Return a string of the number with a comma-separator for units of thousands (eg: 12,345).
	@classmethod
	def thousand(self, value):
		return '{:,}'.format(value)

	@classmethod
	def human(self, value):
		magnitude = 0
		while abs(value) >= 1000:
			magnitude += 1
			value /= 1000.0
		return '%.0f%s' % (value, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])

	@classmethod
	def absolute(self, value):
		return abs(value)

	@classmethod
	def scale(self, value, fromMinimum = 0, fromMaximum = 1, toMinimum = 0, toMaximum = 1):
		return toMinimum + (value - fromMinimum) * ((toMaximum - toMinimum) / float(fromMaximum - fromMinimum))

	# Returns the closest value from the list.
	@classmethod
	def closest(self, list, value):
		return list[min(range(len(list)), key = lambda i : abs(list[i] - value))]

	@classmethod
	def random(self, start = 0.0, end = 1.0):
		import random
		if Tools.isFloat(start) or Tools.isFloat(end): return random.uniform(start, end)
		else: return random.randint(start, end)

	@classmethod
	def randomProbability(self, probability):
		return self.random() <= probability

	@classmethod
	def round(self, value, places = 0):
		return round(value, places)

	# Round to closests eg 10.
	@classmethod
	def roundClosest(self, value, base = 10):
		return int(base * round(float(value) / base))

	@classmethod
	def roundUp(self, value):
		import math
		return math.ceil(value)

	@classmethod
	def roundUpClosest(self, value, base = 10):
		import math
		return int(base * math.ceil(float(value) / base))

	@classmethod
	def roundDown(self, value):
		import math
		return math.floor(value)

	@classmethod
	def roundDownClosest(self, value, base = 10):
		import math
		return int(base * math.floor(float(value) / base))

	@classmethod
	def log(self, value, base = None): # If base = None, 'e' is used.
		import math
		return math.log(value) if base is None else math.log(value, base)

	@classmethod
	def power(self, value, exponent):
		return pow(value, exponent)

	@classmethod
	def tanh(self, value):
		import math
		return math.tanh(value)

	# Checks if a number is negative.
	# Can be used to differentiate between 0.0 and -0.0, because "0.0 == +0.0 == -0.0".
	# https://stackoverflow.com/questions/4083401/negative-zero-in-python
	@classmethod
	def negative(self, value):
		if value is None: return False
		import math
		return math.copysign(1, value) < 0

	# Calculate mean.
	@classmethod
	def mean(self, values):
		if not values: return 0
		return sum(values) / len(values)

	# Calculate standard deviation.
	@classmethod
	def deviation(self, values, mean = None):
		if not values: return 0
		from math import sqrt
		if mean is None: mean = self.mean(values = values)
		return sqrt(sum(pow(i - mean, 2) for i in values) / len(values))

	# Remove outliers from list.
	# https://www.askpython.com/python/examples/how-to-determine-outliers
	# upper=True: remove highest outliers.
	# lower=True: remove lowest outliers.
	# middle=True: remove middle values between upper and lower outliers.
	@classmethod
	def outliers(self, values, threshold = 2, upper = True, lower = True, middle = False):
		result = []
		mean = self.mean(values = values)
		deviation = self.deviation(values = values, mean = mean)
		for i in values:
			value = ((i - mean) / deviation) if deviation else 0
			if value > threshold:
				if not upper: result.append(i)
			elif value < -threshold:
				if not lower: result.append(i)
			elif not middle:
				result.append(i)
		return result


class Matcher(object):

	# Native Python
	AlgorithmDifferenceSequence = 'differencesequence' # Python's difflib.SequenceMatcher

	# Edit Distance (how many characters have to be added/removed/modified to get from string 1 to string 2).
	AlgorithmLongestSequence = 'longestsequence' # Longest Common Subsequence Distance
	AlgorithmLevenshtein = 'levenshtein' # Levenshtein Distance
	AlgorithmDamerauLevenshtein = 'dameraulevenshtein' # Damerau-Levenshtein Distance
	AlgorithmHamming = 'hamming' # Hamming Distance
	AlgorithmJaro = 'jaro' # Jaro Distance
	AlgorithmJaroWinkler = 'jarowinkler' # Jaro-Winkler Distance

	# Vector Similarity (measure of similarity between two non-zero vectors of an inner product space).
	AlgorithmCosine = 'cosine' # Cosine Similarity
	AlgorithmJaccard = 'jaccard' # Jaccard Similarity
	AlgorithmSorensen = 'sorensen' # Sorensen Dice Similarity
	AlgorithmQgram = 'qgram' # Q-Gram Similarity

	@classmethod
	def _encode(self, string):
		try: return string.decode('utf-8')
		except: return string

	@classmethod
	def match(self, algorithm, string1, string2, ignoreCase = True, ignoreSpace = False, ignoreNumeric = False, ignoreSymbol = False):
		string1 = self._encode(string1)
		string2 = self._encode(string2)

		if algorithm == Matcher.AlgorithmDifferenceSequence: return self.differenceSequence(string1 = string1, string2 = string2, ignoreCase = ignoreCase)
		if algorithm == Matcher.AlgorithmLongestSequence: return self.longestSequence(string1 = string1, string2 = string2, ignoreCase = ignoreCase, ignoreSpace = ignoreSpace, ignoreNumeric = ignoreNumeric, ignoreSymbol = ignoreSymbol)
		elif algorithm == Matcher.AlgorithmLevenshtein: return self.levenshtein(string1 = string1, string2 = string2, ignoreCase = ignoreCase, ignoreSpace = ignoreSpace, ignoreNumeric = ignoreNumeric, ignoreSymbol = ignoreSymbol)
		elif algorithm == Matcher.AlgorithmDamerauLevenshtein: return self.damerauLevenshtein(string1 = string1, string2 = string2, ignoreCase = ignoreCase, ignoreSpace = ignoreSpace, ignoreNumeric = ignoreNumeric, ignoreSymbol = ignoreSymbol)
		elif algorithm == Matcher.AlgorithmHamming: return self.hamming(string1 = string1, string2 = string2, ignoreCase = ignoreCase, ignoreSpace = ignoreSpace, ignoreNumeric = ignoreNumeric, ignoreSymbol = ignoreSymbol)
		elif algorithm == Matcher.AlgorithmJaro: return self.jaro(string1 = string1, string2 = string2, ignoreCase = ignoreCase, ignoreSpace = ignoreSpace, ignoreNumeric = ignoreNumeric, ignoreSymbol = ignoreSymbol)
		elif algorithm == Matcher.AlgorithmJaroWinkler: return self.jaroWinkler(string1 = string1, string2 = string2, ignoreCase = ignoreCase, ignoreSpace = ignoreSpace, ignoreNumeric = ignoreNumeric, ignoreSymbol = ignoreSymbol)
		elif algorithm == Matcher.AlgorithmCosine: return self.cosine(string1 = string1, string2 = string2, ignoreCase = ignoreCase, ignoreSpace = ignoreSpace, ignoreNumeric = ignoreNumeric, ignoreSymbol = ignoreSymbol)
		elif algorithm == Matcher.AlgorithmJaccard: return self.jaccard(string1 = string1, string2 = string2, ignoreCase = ignoreCase, ignoreSpace = ignoreSpace, ignoreNumeric = ignoreNumeric, ignoreSymbol = ignoreSymbol)
		elif algorithm == Matcher.AlgorithmSorensen: return self.sorensen(string1 = string1, string2 = string2, ignoreCase = ignoreCase, ignoreSpace = ignoreSpace, ignoreNumeric = ignoreNumeric, ignoreSymbol = ignoreSymbol)
		elif algorithm == Matcher.AlgorithmQgram: return self.qgram(string1 = string1, string2 = string2, ignoreCase = ignoreCase, ignoreSpace = ignoreSpace, ignoreNumeric = ignoreNumeric, ignoreSymbol = ignoreSymbol)
		else: return 0

	@classmethod
	def differenceSequence(self, string1, string2, ignoreCase = False):
		from difflib import SequenceMatcher
		string1 = self._encode(string1)
		string2 = self._encode(string2)
		if ignoreCase:
			string1 = string1.lower()
			string2 = string2.lower()
		return SequenceMatcher(None, string1, string2).ratio()

	@classmethod
	def longestSequence(self, string1, string2, ignoreCase = True, ignoreSpace = False, ignoreNumeric = False, ignoreSymbol = False):
		from lib.modules.external import Importer
		return Importer.moduleTextDistLcs()(self._encode(string1), self._encode(string2), ignore_non_alnumspc = ignoreSymbol, ignore_space = ignoreSpace, ignore_numeric = ignoreNumeric, ignore_case = ignoreCase)

	@classmethod
	def levenshtein(self, string1, string2, ignoreCase = True, ignoreSpace = False, ignoreNumeric = False, ignoreSymbol = False):
		from lib.modules.external import Importer
		return Importer.moduleTextDistLevenshtein()(self._encode(string1), self._encode(string2), ignore_non_alnumspc = ignoreSymbol, ignore_space = ignoreSpace, ignore_numeric = ignoreNumeric, ignore_case = ignoreCase)

	@classmethod
	def damerauLevenshtein(self, string1, string2, ignoreCase = True, ignoreSpace = False, ignoreNumeric = False, ignoreSymbol = False):
		from lib.modules.external import Importer
		return Importer.moduleTextDistDamerauLevenshtein()(self._encode(string1), self._encode(string2), ignore_non_alnumspc = ignoreSymbol, ignore_space = ignoreSpace, ignore_numeric = ignoreNumeric, ignore_case = ignoreCase)

	@classmethod
	def hamming(self, string1, string2, ignoreCase = True, ignoreSpace = False, ignoreNumeric = False, ignoreSymbol = False):
		from lib.modules.external import Importer
		# Hamming distance requires both strings to be the same length.
		string1 = self._encode(string1)
		string2 = self._encode(string2)
		length1 = len(string1)
		length2 = len(string2)
		if length1 > length2: string2 = string2.ljust(length1, 'x')
		elif length2 > length1: string1 = string1.ljust(length2, 'x')
		return Importer.moduleTextDistHamming()(string1, string2, ignore_non_alnumspc = ignoreSymbol, ignore_space = ignoreSpace, ignore_numeric = ignoreNumeric, ignore_case = ignoreCase)

	@classmethod
	def jaro(self, string1, string2, ignoreCase = True, ignoreSpace = False, ignoreNumeric = False, ignoreSymbol = False):
		from lib.modules.external import Importer
		return Importer.moduleTextDistJaro()(self._encode(string1), self._encode(string2), ignore_non_alnumspc = ignoreSymbol, ignore_space = ignoreSpace, ignore_numeric = ignoreNumeric, ignore_case = ignoreCase)

	@classmethod
	def jaroWinkler(self, string1, string2, ignoreCase = True, ignoreSpace = False, ignoreNumeric = False, ignoreSymbol = False):
		from lib.modules.external import Importer
		return Importer.moduleTextDistJaroWinkler()(self._encode(string1), self._encode(string2), ignore_non_alnumspc = ignoreSymbol, ignore_space = ignoreSpace, ignore_numeric = ignoreNumeric, ignore_case = ignoreCase)

	@classmethod
	def cosine(self, string1, string2, ignoreCase = True, ignoreSpace = False, ignoreNumeric = False, ignoreSymbol = False):
		from lib.modules.external import Importer
		try: return Importer.moduleTextDistCosine()(self._encode(string1), self._encode(string2), ignore_non_alnumspc = ignoreSymbol, ignore_space = ignoreSpace, ignore_numeric = ignoreNumeric, ignore_case = ignoreCase)
		except: return 0 # Empty string throws exception.

	@classmethod
	def jaccard(self, string1, string2, ignoreCase = True, ignoreSpace = False, ignoreNumeric = False, ignoreSymbol = False):
		from lib.modules.external import Importer
		try: return Importer.moduleTextDistJaccard()(self._encode(string1), self._encode(string2), ignore_non_alnumspc = ignoreSymbol, ignore_space = ignoreSpace, ignore_numeric = ignoreNumeric, ignore_case = ignoreCase)
		except: return 0 # Empty string throws exception.

	@classmethod
	def sorensen(self, string1, string2, ignoreCase = True, ignoreSpace = False, ignoreNumeric = False, ignoreSymbol = False):
		from lib.modules.external import Importer
		try: return Importer.moduleTextDistSorensen()(self._encode(string1), self._encode(string2), ignore_non_alnumspc = ignoreSymbol, ignore_space = ignoreSpace, ignore_numeric = ignoreNumeric, ignore_case = ignoreCase)
		except: return 0 # Empty string throws exception.

	@classmethod
	def qgram(self, string1, string2, ignoreCase = True, ignoreSpace = False, ignoreNumeric = False, ignoreSymbol = False):
		from lib.modules.external import Importer
		try: return Importer.moduleTextDistQgram()(self._encode(string1), self._encode(string2), ignore_non_alnumspc = ignoreSymbol, ignore_space = ignoreSpace, ignore_numeric = ignoreNumeric, ignore_case = ignoreCase)
		except: return 0 # Empty string throws exception.

class Language(object):

	Code = 'code'
	Name = 'name'
	Original = 'original'
	Fallback = 'fallback'
	Country = 'country'
	Frequency = 'frequency'
	Search = 'search'

	# Types
	TypePrimary = 'primary'
	TypeSecondary = 'secondary'
	TypeTertiary = 'tertiary'
	TypeDefault = TypePrimary

	# Settings
	SettingBase = 'general.language.'
	SettingPrimary = SettingBase + TypePrimary
	SettingSecondary = SettingBase + TypeSecondary
	SettingTertiary = SettingBase + TypeTertiary

	# Api
	ApiTrakt = 'trakt'
	ApiTvdb = 'tvdb'

	# Cases
	CaseCapital = 0
	CaseUpper = 1
	CaseLower = 2

	# Codes
	CodePrimary = 0 # ISO-639-1
	CodeSecondary = 1 # ISO-639-2-B
	CodeTertiary = 2 # ISO-639-3 or ISO-639-2-T
	CodeStream = CodeSecondary # The code used by Kodi's player and OpenSubtitles.
	CodeDefault = CodePrimary

	# Code
	CodeUniversal = 'un'
	CodeAutomatic = 'xa'
	CodePlain = 'xp'
	CodeNone = 'xn'
	CodeUnknown = 'xu'
	CodeNative = 'xx'
	CodeEnglish = 'en'
	CodeFrench = 'fr'
	CodeSpanish = 'es'
	CodePortuguese = 'pt'
	CodeItalian = 'it'
	CodeGerman = 'de'
	CodeDutch = 'nl'
	CodeRussian = 'ru'
	CodeChinese = 'zh'
	CodeTurkish = 'tr'
	CodeIndian = ('hi', 'bn', 'mr', 'te', 'ta', 'gu', 'ur', 'kn', 'or', 'ml', 'pa', 'as', 'sa', 'mai', 'mni') # Must be a tuple to be used as a dict-key in MetaImdb.

	# Names
	NameUniversal = CodeUniversal
	NameEnglish = CodeEnglish
	NameFrench = CodeFrench
	NameSpanish = CodeSpanish
	NamePortuguese = CodePortuguese
	NameItalian = CodeItalian
	NameGerman = CodeGerman
	NameDutch = CodeDutch
	NameRussian = CodeRussian
	NameChinese = CodeChinese
	NameDefault = NameEnglish
	NameNative = CodeNative # Do not use None, since it gets converted to the string "null" during JSON-encoding if used as a dict-key. Eg: from subtitle.py.

	# Country
	CountryNone = None

	# Common
	FrequencyCommon = 3			# Very common language, spoken by 10s of millions.
	FrequencyOccasional = 2		# Less common language, spoken by a few millions or a major national language.
	FrequencyUncommon = 1		# Uncommon language, spoke by a few millions or less.
	FrequencyNone = 0			# Not an official language.

	Disabled = 'none'			# Do not use a language at all.
	Automatic = 'automatic'		# Use the language according to the settings specified by the user in the language settings under the General tab.
	Alternative = 'alternative'	# Use the first language, besides English, according to the settings sepcified by the user in the language settings under the General tab. Just like Automatic, but excludes English.

	UniversalName = 'Universal'
	UniversalCode = CodeUniversal
	UniversalCountry = CodeUniversal

	EnglishName = 'English'
	EnglishCode = CodeEnglish
	EnglishCountry = ['us', 'gb']

	# Sets
	Sets = {
		'providers' : [CodeFrench, CodeSpanish, CodePortuguese, CodeItalian, CodeGerman, CodeDutch, CodeRussian],	# The set of languages supported by providers. Used in scrape.query.keyword.language.
	}

	Replacements = {'gr' : 'el'}
	Settings = None
	Details = True # True: use detailed icon dialog for settings. False: use plain single line dialog.

	Languages = None
	Variations = None # Language variations used by OpenSubtitles.
	Flags = None

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		if settings:
			Language.Settings = None

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def _process(self, language):
		if type(language) is tuple: language = language[0]
		elif type(language) is dict: language = language['code'][Language.CodeDefault]
		language = language.lower().strip()
		try: language = Language.Replacements[language]
		except: pass
		try: language = Converter.unicode(language)
		except: pass
		return language

	@classmethod
	def _prepare(self):
		if Language.Languages is None:
			Language.Languages = (
				{ Language.Name : { Language.NameNative : Language.UniversalName, Language.NameEnglish : Language.UniversalName, Language.NameFrench : 'Universel', Language.NameSpanish : 'Universal', Language.NamePortuguese : 'Universal', Language.NameItalian : 'Universale', Language.NameGerman : 'Universal', Language.NameDutch : 'Universeel', Language.NameRussian : 'Универсальный' }, Language.Code : (Language.UniversalCode, Language.UniversalCode, Language.UniversalCode), Language.Country : Language.UniversalCountry, Language.Frequency : Language.FrequencyNone },
				{ Language.Name : { Language.NameNative : 'Aҧсуа бызшәа', Language.NameEnglish : 'Abkhaz', Language.NameFrench : 'Abkhaz', Language.NameSpanish : 'Abkhaz', Language.NamePortuguese : 'Abkhaz', Language.NameItalian : 'Abkhaz', Language.NameGerman : 'Abkhaz', Language.NameDutch : 'Abkhaz', Language.NameRussian : 'Абхаз' }, Language.Code : ('ab', 'abk', 'abk'), Language.Country : 'ge', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Qafár af', Language.NameEnglish : 'Afar', Language.NameFrench : 'Afar', Language.NameSpanish : 'Afar', Language.NamePortuguese : 'Afar', Language.NameItalian : 'Afar', Language.NameGerman : 'Afar', Language.NameDutch : 'Afar', Language.NameRussian : 'Afar' }, Language.Code : ('aa', 'aar', 'aar'), Language.Country : 'dj', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Afrikaans', Language.NameEnglish : 'Afrikaans', Language.NameFrench : 'Afrikaans', Language.NameSpanish : 'Africaans', Language.NamePortuguese : 'Afrikaans', Language.NameItalian : 'Afrikaans', Language.NameGerman : 'Afrikaans', Language.NameDutch : 'Afrikaans', Language.NameRussian : 'Африкаанс' }, Language.Code : ('af', 'afr', 'afr'), Language.Country : 'za', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Akan', Language.NameEnglish : 'Akan', Language.NameFrench : 'Akan', Language.NameSpanish : 'Akan', Language.NamePortuguese : 'Akan', Language.NameItalian : 'Akan', Language.NameGerman : 'Akan', Language.NameDutch : 'Akan', Language.NameRussian : 'Акан' }, Language.Code : ('ak', 'aka', 'aka'), Language.Country : 'gh', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Shqip', Language.NameEnglish : 'Albanian', Language.NameFrench : 'Albanais', Language.NameSpanish : 'Albanés', Language.NamePortuguese : 'Albanês', Language.NameItalian : 'Albanese', Language.NameGerman : 'Albanisch', Language.NameDutch : 'Albanees', Language.NameRussian : 'Албанский' }, Language.Code : ('sq', 'alb', 'sqi'), Language.Country : 'al', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'ኣማርኛ', Language.NameEnglish : 'Amharic', Language.NameFrench : 'Amharique', Language.NameSpanish : 'Amárico', Language.NamePortuguese : 'Amharic', Language.NameItalian : 'Amharic', Language.NameGerman : 'Amharisch', Language.NameDutch : 'Amharisch', Language.NameRussian : 'Amharic' }, Language.Code : ('am', 'amh', 'amh'), Language.Country : 'et', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'العربية', Language.NameEnglish : 'Arabic', Language.NameFrench : 'Arabe', Language.NameSpanish : 'Arábica', Language.NamePortuguese : 'Árabe', Language.NameItalian : 'Arabo', Language.NameGerman : 'Arabisch', Language.NameDutch : 'Arabisch', Language.NameRussian : 'Арабский' }, Language.Code : ('ar', 'ara', 'ara'), Language.Country : 'sa', Language.Frequency : Language.FrequencyCommon },
				{ Language.Name : { Language.NameNative : 'l\'Aragonés', Language.NameEnglish : 'Aragonese', Language.NameFrench : 'Aragonais', Language.NameSpanish : 'Aragonés', Language.NamePortuguese : 'Aragonês', Language.NameItalian : 'Aragonese', Language.NameGerman : 'Aragonesisch', Language.NameDutch : 'Aragonees', Language.NameRussian : 'Арагонский' }, Language.Code : ('an', 'arg', 'arg'), Language.Country : 'es', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Հայերեն', Language.NameEnglish : 'Armenian', Language.NameFrench : 'Arménien', Language.NameSpanish : 'Armenio', Language.NamePortuguese : 'Armênio', Language.NameItalian : 'Armeno', Language.NameGerman : 'Armenisch', Language.NameDutch : 'Armeens', Language.NameRussian : 'Армянский' }, Language.Code : ('hy', 'arm', 'hye'), Language.Country : 'am', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'অসমীয়া', Language.NameEnglish : 'Assamese', Language.NameFrench : 'Assamen', Language.NameSpanish : 'Assamese', Language.NamePortuguese : 'Assamese', Language.NameItalian : 'Assamese', Language.NameGerman : 'Assamese', Language.NameDutch : 'Assamese', Language.NameRussian : 'Ассамский' }, Language.Code : ('as', 'asm', 'asm'), Language.Country : 'in', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'МагIарул МацI', Language.NameEnglish : 'Avar', Language.NameFrench : 'Avari', Language.NameSpanish : 'Avar', Language.NamePortuguese : 'Avar', Language.NameItalian : 'Avar', Language.NameGerman : 'Avar', Language.NameDutch : 'Rapen', Language.NameRussian : 'Авар' }, Language.Code : ('av', 'ava', 'ava'), Language.Country : 'ru', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Avestan', Language.NameEnglish : 'Avestan', Language.NameFrench : 'Avestan', Language.NameSpanish : 'Avesta', Language.NamePortuguese : 'Avestan', Language.NameItalian : 'Avestan', Language.NameGerman : 'Avestan', Language.NameDutch : 'Avestan', Language.NameRussian : 'Авестан' }, Language.Code : ('ae', 'ave', 'ave'), Language.Country : 'ir', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Aymar Aru', Language.NameEnglish : 'Aymara', Language.NameFrench : 'Aymara', Language.NameSpanish : 'Aimara', Language.NamePortuguese : 'Aymara', Language.NameItalian : 'Aymara', Language.NameGerman : 'Aymara', Language.NameDutch : 'Aymara', Language.NameRussian : 'Аймара' }, Language.Code : ('ay', 'aym', 'aym'), Language.Country : 'bo', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Azərbaycanca', Language.NameEnglish : 'Azerbaijani', Language.NameFrench : 'Azerbaïdjanais', Language.NameSpanish : 'Azerbaiyano', Language.NamePortuguese : 'Azerbaijani', Language.NameItalian : 'Azerbaijani', Language.NameGerman : 'Aserbaidschani', Language.NameDutch : 'Azerbeidzjani', Language.NameRussian : 'Азербайджан' }, Language.Code : ('az', 'aze', 'aze'), Language.Country : 'az', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Bamanankan', Language.NameEnglish : 'Bambara', Language.NameFrench : 'Bambara', Language.NameSpanish : 'Bambara', Language.NamePortuguese : 'Bambara', Language.NameItalian : 'Bambara', Language.NameGerman : 'Bambara', Language.NameDutch : 'Bambara', Language.NameRussian : 'Бамбара' }, Language.Code : ('bm', 'bam', 'bam'), Language.Country : 'ml', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'башҡорт Теле', Language.NameEnglish : 'Bashkir', Language.NameFrench : 'Bashkir', Language.NameSpanish : 'Bashkir', Language.NamePortuguese : 'Bashkir', Language.NameItalian : 'Bashkir', Language.NameGerman : 'Baskir', Language.NameDutch : 'Bashkir', Language.NameRussian : 'Башкир' }, Language.Code : ('ba', 'bak', 'bak'), Language.Country : 'ru', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Euskara', Language.NameEnglish : 'Basque', Language.NameFrench : 'Basque', Language.NameSpanish : 'Vasco', Language.NamePortuguese : 'Basque', Language.NameItalian : 'Basco', Language.NameGerman : 'Baskisch', Language.NameDutch : 'Baskisch', Language.NameRussian : 'Баскский' }, Language.Code : ('eu', 'baq', 'eus'), Language.Country : 'es', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Беларуская', Language.NameEnglish : 'Belarusian', Language.NameFrench : 'Biélorusse', Language.NameSpanish : 'Bielorruso', Language.NamePortuguese : 'Bielorrusso', Language.NameItalian : 'Bielorusso', Language.NameGerman : 'Belarussisch', Language.NameDutch : 'Wit-Russisch', Language.NameRussian : 'Белорусский' }, Language.Code : ('be', 'bel', 'bel'), Language.Country : 'by', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'বাংলা', Language.NameEnglish : 'Bengali', Language.NameFrench : 'Bengali', Language.NameSpanish : 'Bengalí', Language.NamePortuguese : 'Bengali', Language.NameItalian : 'Bengalese', Language.NameGerman : 'Bengali', Language.NameDutch : 'Bengaals', Language.NameRussian : 'Бенгальский' }, Language.Code : ('bn', 'ben', 'ben'), Language.Country : 'bd', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Bihari', Language.NameEnglish : 'Bihari', Language.NameFrench : 'Bihari', Language.NameSpanish : 'Bihari', Language.NamePortuguese : 'Bihari', Language.NameItalian : 'Bihari', Language.NameGerman : 'Bihari', Language.NameDutch : 'Bihari', Language.NameRussian : 'Bihari' }, Language.Code : ('bh', 'bih', 'bih'), Language.Country : 'in', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Bislama', Language.NameEnglish : 'Bislama', Language.NameFrench : 'Bislama', Language.NameSpanish : 'Bislama', Language.NamePortuguese : 'Bislama', Language.NameItalian : 'Bislama', Language.NameGerman : 'Bislama', Language.NameDutch : 'Bislama', Language.NameRussian : 'Бислама' }, Language.Code : ('bi', 'bis', 'bis'), Language.Country : 'vu', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Босански', Language.NameEnglish : 'Bosnian', Language.NameFrench : 'Bosniaque', Language.NameSpanish : 'Bosnio', Language.NamePortuguese : 'Bósnio', Language.NameItalian : 'Bosniaco', Language.NameGerman : 'Bosnisch', Language.NameDutch : 'Bosnisch', Language.NameRussian : 'Боснийский' }, Language.Code : ('bs', 'bos', 'bos'), Language.Country : 'ba', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Bokmål', Language.NameEnglish : 'Bokmal', Language.NameFrench : 'Bokmal', Language.NameSpanish : 'Bokmal', Language.NamePortuguese : 'Bokmal', Language.NameItalian : 'Bokmal', Language.NameGerman : 'Bokmal', Language.NameDutch : 'Bokmal', Language.NameRussian : 'Боймал' }, Language.Code : ('nb', 'nob', 'nob'), Language.Country : 'no', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Brezhoneg', Language.NameEnglish : 'Breton', Language.NameFrench : 'Breton', Language.NameSpanish : 'Bretón', Language.NamePortuguese : 'Bretão', Language.NameItalian : 'Bretone', Language.NameGerman : 'Bretonisch', Language.NameDutch : 'Breton', Language.NameRussian : 'Бретон' }, Language.Code : ('br', 'bre', 'bre'), Language.Country : 'fr', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'български', Language.NameEnglish : 'Bulgarian', Language.NameFrench : 'Bulgare', Language.NameSpanish : 'Búlgaro', Language.NamePortuguese : 'Búlgaro', Language.NameItalian : 'Bulgaro', Language.NameGerman : 'Bulgarisch', Language.NameDutch : 'Bulgaars', Language.NameRussian : 'Болгарский' }, Language.Code : ('bg', 'bul', 'bul'), Language.Country : 'bg', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'မြန်မာစာ', Language.NameEnglish : 'Burmese', Language.NameFrench : 'Birman', Language.NameSpanish : 'Birmano', Language.NamePortuguese : 'Birmanês', Language.NameItalian : 'Birmano', Language.NameGerman : 'Birmanisch', Language.NameDutch : 'Birmaans', Language.NameRussian : 'Бирманский' }, Language.Code : ('my', 'bur', 'mya'), Language.Country : 'mm', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Català', Language.NameEnglish : 'Catalan', Language.NameFrench : 'Catalan', Language.NameSpanish : 'Catalán', Language.NamePortuguese : 'Catalão', Language.NameItalian : 'Catalano', Language.NameGerman : 'Katalanisch', Language.NameDutch : 'Catalaans', Language.NameRussian : 'Каталон' }, Language.Code : ('ca', 'cat', 'cat'), Language.Country : 'es', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Chamoru', Language.NameEnglish : 'Chamorro', Language.NameFrench : 'Chamorro', Language.NameSpanish : 'Chamorro', Language.NamePortuguese : 'Chamorro', Language.NameItalian : 'Chamorro', Language.NameGerman : 'Chamorro', Language.NameDutch : 'Chamorro', Language.NameRussian : 'Chamorro' }, Language.Code : ('ch', 'cha', 'cha'), Language.Country : 'gu', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Нохчийн Mотт', Language.NameEnglish : 'Chechen', Language.NameFrench : 'Tchétchène', Language.NameSpanish : 'Checheno', Language.NamePortuguese : 'Chechen', Language.NameItalian : 'Ceceno', Language.NameGerman : 'Tschetschenisch', Language.NameDutch : 'Tsjets', Language.NameRussian : 'Чеченский' }, Language.Code : ('ce', 'che', 'che'), Language.Country : 'ru', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Chicheŵa', Language.NameEnglish : 'Chichewa', Language.NameFrench : 'Chichewa', Language.NameSpanish : 'Chichewa', Language.NamePortuguese : 'Chichewa', Language.NameItalian : 'Chichewa', Language.NameGerman : 'Chichewa', Language.NameDutch : 'Chichewa', Language.NameRussian : 'Чичью' }, Language.Code : ('ny', 'nya', 'nya'), Language.Country : 'mw', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : '中文', Language.NameEnglish : 'Chinese', Language.NameFrench : 'Chinois', Language.NameSpanish : 'Chino', Language.NamePortuguese : 'Chinês', Language.NameItalian : 'Cinese', Language.NameGerman : 'Chinesisch', Language.NameDutch : 'Chinees', Language.NameRussian : 'Китайский' }, Language.Code : ('zh', 'chi', 'zho'), Language.Country : 'cn', Language.Frequency : Language.FrequencyCommon },
				{ Language.Name : { Language.NameNative : 'Чӑвашла', Language.NameEnglish : 'Chuvash', Language.NameFrench : 'Chuve', Language.NameSpanish : 'Chuvash', Language.NamePortuguese : 'Chuvash', Language.NameItalian : 'Chuvash', Language.NameGerman : 'Chuvash', Language.NameDutch : 'Chuvash', Language.NameRussian : 'Чуваш' }, Language.Code : ('cv', 'chv', 'chv'), Language.Country : 'ru', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Kernewek', Language.NameEnglish : 'Cornish', Language.NameFrench : 'Cornouaillais', Language.NameSpanish : 'Cornualles', Language.NamePortuguese : 'Cornish', Language.NameItalian : 'Cornicolo', Language.NameGerman : 'Kornisch', Language.NameDutch : 'Corner', Language.NameRussian : 'Корниш' }, Language.Code : ('kw', 'cor', 'cor'), Language.Country : 'gb', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Corsu', Language.NameEnglish : 'Corsican', Language.NameFrench : 'Corse', Language.NameSpanish : 'Corso', Language.NamePortuguese : 'Corsicana', Language.NameItalian : 'Corsican', Language.NameGerman : 'Korsikan', Language.NameDutch : 'Corsicaans', Language.NameRussian : 'Corsican' }, Language.Code : ('co', 'cos', 'cos'), Language.Country : 'fr', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'ᓀᐦᐃᔭᐍᐏᐣ', Language.NameEnglish : 'Cree', Language.NameFrench : 'Cree', Language.NameSpanish : 'Cree', Language.NamePortuguese : 'Cree', Language.NameItalian : 'Cree', Language.NameGerman : 'Cree', Language.NameDutch : 'Cree', Language.NameRussian : 'Cree' }, Language.Code : ('cr', 'cre', 'cre'), Language.Country : 'ca', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Hrvatski', Language.NameEnglish : 'Croatian', Language.NameFrench : 'Croate', Language.NameSpanish : 'Croata', Language.NamePortuguese : 'Croata', Language.NameItalian : 'Croato', Language.NameGerman : 'Kroatisch', Language.NameDutch : 'Kroatisch', Language.NameRussian : 'Хорватский' }, Language.Code : ('hr', 'hrv', 'hrv'), Language.Country : 'hr', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Čeština', Language.NameEnglish : 'Czech', Language.NameFrench : 'Tchèque', Language.NameSpanish : 'Checo', Language.NamePortuguese : 'Checo', Language.NameItalian : 'Ceco', Language.NameGerman : 'Tschechisch', Language.NameDutch : 'Tsjechisch', Language.NameRussian : 'Чешский' }, Language.Code : ('cs', 'cze', 'ces'), Language.Country : 'cz', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Dansk', Language.NameEnglish : 'Danish', Language.NameFrench : 'Danois', Language.NameSpanish : 'Danés', Language.NamePortuguese : 'Dinamarquês', Language.NameItalian : 'Danese', Language.NameGerman : 'Dänisch', Language.NameDutch : 'Deens', Language.NameRussian : 'Датский' }, Language.Code : ('da', 'dan', 'dan'), Language.Country : 'dk', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Nederlands', Language.NameEnglish : 'Dutch', Language.NameFrench : 'Néerlandais', Language.NameSpanish : 'Holandés', Language.NamePortuguese : 'Holandês', Language.NameItalian : 'Olandese', Language.NameGerman : 'Niederländisch', Language.NameDutch : 'Nederlands', Language.NameRussian : 'Голландский' }, Language.Code : ('nl', 'dut', 'nld'), Language.Country : 'nl', Language.Frequency : Language.FrequencyCommon },
				{ Language.Name : { Language.NameNative : 'རྫོང་ཁ་', Language.NameEnglish : 'Dzongkha', Language.NameFrench : 'Dzongkha', Language.NameSpanish : 'Dzongkha', Language.NamePortuguese : 'Dzongkha', Language.NameItalian : 'Dzongkha', Language.NameGerman : 'Dzongkha', Language.NameDutch : 'Dzongkha', Language.NameRussian : 'Дзунгха' }, Language.Code : ('dz', 'dzo', 'dzo'), Language.Country : 'bt', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'English', Language.NameEnglish : 'English', Language.NameFrench : 'Anglais', Language.NameSpanish : 'Inglés', Language.NamePortuguese : 'Inglês', Language.NameItalian : 'Inglese', Language.NameGerman : 'Englisch', Language.NameDutch : 'Engels', Language.NameRussian : 'Английский' }, Language.Code : ('en', 'eng', 'eng'), Language.Country : 'gb', Language.Frequency : Language.FrequencyCommon },
				{ Language.Name : { Language.NameNative : 'Esperantaj', Language.NameEnglish : 'Esperanto', Language.NameFrench : 'Espéranto', Language.NameSpanish : 'Esperanto', Language.NamePortuguese : 'Esperanto', Language.NameItalian : 'Esperanto', Language.NameGerman : 'Esperanto', Language.NameDutch : 'Esperanto', Language.NameRussian : 'Эсперанто' }, Language.Code : ('eo', 'epo', 'epo'), Language.Country : Language.CountryNone, Language.Frequency : Language.FrequencyNone },
				{ Language.Name : { Language.NameNative : 'Eesti', Language.NameEnglish : 'Estonian', Language.NameFrench : 'Estonien', Language.NameSpanish : 'Estonio', Language.NamePortuguese : 'Estoniano', Language.NameItalian : 'Estone', Language.NameGerman : 'Estnisch', Language.NameDutch : 'Estlands', Language.NameRussian : 'Эстонский' }, Language.Code : ('et', 'est', 'est'), Language.Country : 'ee', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Èʋegbe', Language.NameEnglish : 'Ewe', Language.NameFrench : 'Ewe', Language.NameSpanish : 'Ewe', Language.NamePortuguese : 'Ewe', Language.NameItalian : 'Ewe', Language.NameGerman : 'Ewe', Language.NameDutch : 'Ewe', Language.NameRussian : 'Ewe' }, Language.Code : ('ee', 'ewe', 'ewe'), Language.Country : 'gh', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Føroyskt', Language.NameEnglish : 'Faroese', Language.NameFrench : 'Farsee', Language.NameSpanish : 'Feroz', Language.NamePortuguese : 'Faroese', Language.NameItalian : 'Faroese', Language.NameGerman : 'Faroese', Language.NameDutch : 'Farroom', Language.NameRussian : 'Faroese' }, Language.Code : ('fo', 'fao', 'fao'), Language.Country : 'fo', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Vakaviti', Language.NameEnglish : 'Fijian', Language.NameFrench : 'Fidjien', Language.NameSpanish : 'Fiyian', Language.NamePortuguese : 'Fijiano', Language.NameItalian : 'Fijian', Language.NameGerman : 'Fidschi', Language.NameDutch : 'Fijian', Language.NameRussian : 'Фиджийский' }, Language.Code : ('fj', 'fij', 'fij'), Language.Country : 'fj', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Suomi', Language.NameEnglish : 'Finnish', Language.NameFrench : 'Finlandais', Language.NameSpanish : 'Finlandés', Language.NamePortuguese : 'Finlandês', Language.NameItalian : 'Finlandese', Language.NameGerman : 'Finnisch', Language.NameDutch : 'Fins', Language.NameRussian : 'Финский' }, Language.Code : ('fi', 'fin', 'fin'), Language.Country : 'fi', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Français', Language.NameEnglish : 'French', Language.NameFrench : 'Français', Language.NameSpanish : 'Francés', Language.NamePortuguese : 'Francês', Language.NameItalian : 'Francese', Language.NameGerman : 'Französisch', Language.NameDutch : 'Frans', Language.NameRussian : 'Французкий' }, Language.Code : ('fr', 'fre', 'fra'), Language.Country : 'fr', Language.Frequency : Language.FrequencyCommon },
				{ Language.Name : { Language.NameNative : 'Frysk', Language.NameEnglish : 'Frisian', Language.NameFrench : 'Frison', Language.NameSpanish : 'Frisio', Language.NamePortuguese : 'Frísio', Language.NameItalian : 'Frisone', Language.NameGerman : 'Friesisch', Language.NameDutch : 'Fries', Language.NameRussian : 'Фризский' }, Language.Code : ('fy', 'fry', 'fry'), Language.Country : 'nl', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Fulfulde', Language.NameEnglish : 'Fula', Language.NameFrench : 'Fulsed', Language.NameSpanish : 'Fulla', Language.NamePortuguese : 'Fula', Language.NameItalian : 'Fula', Language.NameGerman : 'Fula', Language.NameDutch : 'Fula', Language.NameRussian : 'Фула' }, Language.Code : ('ff', 'ful', 'ful'), Language.Country : 'bf', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Galego', Language.NameEnglish : 'Galician', Language.NameFrench : 'Galicien', Language.NameSpanish : 'Gallego', Language.NamePortuguese : 'Galego', Language.NameItalian : 'Galiziano', Language.NameGerman : 'Galizisch', Language.NameDutch : 'Galicisch', Language.NameRussian : 'Галицкий' }, Language.Code : ('gl', 'glg', 'glg'), Language.Country : 'es', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Oluganda', Language.NameEnglish : 'Ganda', Language.NameFrench : 'Ganda', Language.NameSpanish : 'Ganda', Language.NamePortuguese : 'Ganda', Language.NameItalian : 'Ganda', Language.NameGerman : 'Ganda', Language.NameDutch : 'Ganda', Language.NameRussian : 'Гэнда' }, Language.Code : ('lg', 'lug', 'lug'), Language.Country : 'ug', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'ქართული', Language.NameEnglish : 'Georgian', Language.NameFrench : 'Géorgien', Language.NameSpanish : 'Georgiano', Language.NamePortuguese : 'Georgiano', Language.NameItalian : 'Georgiano', Language.NameGerman : 'Georgisch', Language.NameDutch : 'Georgisch', Language.NameRussian : 'Грузин' }, Language.Code : ('ka', 'geo', 'kat'), Language.Country : 'ge', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Deutsch', Language.NameEnglish : 'German', Language.NameFrench : 'Allemand', Language.NameSpanish : 'Alemán', Language.NamePortuguese : 'Alemão', Language.NameItalian : 'Tedesco', Language.NameGerman : 'Deutsch', Language.NameDutch : 'Duits', Language.NameRussian : 'Немецкий' }, Language.Code : ('de', 'ger', 'deu'), Language.Country : 'de', Language.Frequency : Language.FrequencyCommon },
				{ Language.Name : { Language.NameNative : 'Ελληνικά', Language.NameEnglish : 'Greek', Language.NameFrench : 'Grec', Language.NameSpanish : 'Griego', Language.NamePortuguese : 'Grego', Language.NameItalian : 'Greco', Language.NameGerman : 'Griechisch', Language.NameDutch : 'Grieks', Language.NameRussian : 'Греческий' }, Language.Code : ('el', 'gre', 'ell'), Language.Country : 'gr', Language.Frequency : Language.FrequencyCommon },
				{ Language.Name : { Language.NameNative : 'Kalaallisut', Language.NameEnglish : 'Greenlandic', Language.NameFrench : 'Groenlandais', Language.NameSpanish : 'Groenlandés', Language.NamePortuguese : 'Greenlandic', Language.NameItalian : 'Greenlandia', Language.NameGerman : 'Grönländisch', Language.NameDutch : 'Groenlands', Language.NameRussian : 'Гренландия' }, Language.Code : ('kl', 'kal', 'kal'), Language.Country : 'gl', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Avañe\'ẽ', Language.NameEnglish : 'Guarani', Language.NameFrench : 'Guarani', Language.NameSpanish : 'Guaraní', Language.NamePortuguese : 'Guarani', Language.NameItalian : 'Guarani', Language.NameGerman : 'Guarani', Language.NameDutch : 'Guarani', Language.NameRussian : 'Гуарани' }, Language.Code : ('gn', 'grn', 'grn'), Language.Country : 'py', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'ગુજરાતી', Language.NameEnglish : 'Gujarati', Language.NameFrench : 'Gujarati', Language.NameSpanish : 'Gujarati', Language.NamePortuguese : 'Gujarati', Language.NameItalian : 'Gujarati', Language.NameGerman : 'Gujarati', Language.NameDutch : 'Gujarati', Language.NameRussian : 'Гуджарати' }, Language.Code : ('gu', 'guj', 'guj'), Language.Country : 'in', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Kreyòl Ayisyen', Language.NameEnglish : 'Haitian', Language.NameFrench : 'Haïtien', Language.NameSpanish : 'Haitiano', Language.NamePortuguese : 'Haitiano', Language.NameItalian : 'Haitiano', Language.NameGerman : 'Haitianisch', Language.NameDutch : 'Haïtiaans', Language.NameRussian : 'Гаитян' }, Language.Code : ('ht', 'hat', 'hat'), Language.Country : 'ht', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'حَوْسَ', Language.NameEnglish : 'Hausa', Language.NameFrench : 'Hausa', Language.NameSpanish : 'Hausa', Language.NamePortuguese : 'Hausa', Language.NameItalian : 'Hausa', Language.NameGerman : 'Hausa', Language.NameDutch : 'Hausa', Language.NameRussian : 'Hausa' }, Language.Code : ('ha', 'hau', 'hau'), Language.Country : 'ng', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'עברית', Language.NameEnglish : 'Hebrew', Language.NameFrench : 'Hébreu', Language.NameSpanish : 'Hebreo', Language.NamePortuguese : 'Hebraico', Language.NameItalian : 'Ebraico', Language.NameGerman : 'Hebräisch', Language.NameDutch : 'Hebreeuws', Language.NameRussian : 'Иврит' }, Language.Code : ('he', 'heb', 'heb'), Language.Country : 'il', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Otjiherero', Language.NameEnglish : 'Herero', Language.NameFrench : 'Hérero', Language.NameSpanish : 'Herero', Language.NamePortuguese : 'Herero', Language.NameItalian : 'Herero', Language.NameGerman : 'Herero', Language.NameDutch : 'Herero', Language.NameRussian : 'Гереро' }, Language.Code : ('hz', 'her', 'her'), Language.Country : 'na', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'हिन्दी', Language.NameEnglish : 'Hindi', Language.NameFrench : 'Hindi', Language.NameSpanish : 'Hindi', Language.NamePortuguese : 'Hindi', Language.NameItalian : 'Hindi', Language.NameGerman : 'Hindi', Language.NameDutch : 'Hindi', Language.NameRussian : 'Хинди' }, Language.Code : ('hi', 'hin', 'hin'), Language.Country : 'in', Language.Frequency : Language.FrequencyCommon },
				{ Language.Name : { Language.NameNative : 'Hiri Motu', Language.NameEnglish : 'Hiri Motu', Language.NameFrench : 'Hiri Motu', Language.NameSpanish : 'Hiri Motu', Language.NamePortuguese : 'Hiri Motu', Language.NameItalian : 'Hiri Motu', Language.NameGerman : 'Hiri Motu', Language.NameDutch : 'Hiri Motu', Language.NameRussian : 'Hiri Motu' }, Language.Code : ('ho', 'hmo', 'hmo'), Language.Country : 'pg', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Magyar', Language.NameEnglish : 'Hungarian', Language.NameFrench : 'Hongrois', Language.NameSpanish : 'Húngaro', Language.NamePortuguese : 'Húngaro', Language.NameItalian : 'Ungherese', Language.NameGerman : 'Ungarisch', Language.NameDutch : 'Hongaars', Language.NameRussian : 'Венгерский' }, Language.Code : ('hu', 'hun', 'hun'), Language.Country : 'hu', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Interlingua', Language.NameEnglish : 'Interlingua', Language.NameFrench : 'Interlingua', Language.NameSpanish : 'Interlingua', Language.NamePortuguese : 'Interlíngua', Language.NameItalian : 'Interlingua', Language.NameGerman : 'Interlingua', Language.NameDutch : 'Interlingua', Language.NameRussian : 'Interlingua' }, Language.Code : ('ia', 'ina', 'ina'), Language.Country : Language.CountryNone, Language.Frequency : Language.FrequencyNone },
				{ Language.Name : { Language.NameNative : 'Bahasa Indonesia', Language.NameEnglish : 'Indonesian', Language.NameFrench : 'Indonésien', Language.NameSpanish : 'Indonesio', Language.NamePortuguese : 'Indonésio', Language.NameItalian : 'Indonesiano', Language.NameGerman : 'Indonesisch', Language.NameDutch : 'Indonesisch', Language.NameRussian : 'Индонезийский' }, Language.Code : ('id', 'ind', 'ind'), Language.Country : 'id', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Interlingue', Language.NameEnglish : 'Interlingue', Language.NameFrench : 'Interlingue', Language.NameSpanish : 'Interlingue', Language.NamePortuguese : 'Interlingue', Language.NameItalian : 'Interlingue', Language.NameGerman : 'Interlingue', Language.NameDutch : 'Interlingue', Language.NameRussian : 'Interlingue' }, Language.Code : ('ie', 'ile', 'ile'), Language.Country : Language.CountryNone, Language.Frequency : Language.FrequencyNone },
				{ Language.Name : { Language.NameNative : 'Gaeilge', Language.NameEnglish : 'Irish', Language.NameFrench : 'Irlandais', Language.NameSpanish : 'Irlandesa', Language.NamePortuguese : 'Irlandês', Language.NameItalian : 'Irlandesi', Language.NameGerman : 'Irisch', Language.NameDutch : 'Iers', Language.NameRussian : 'Ирландский' }, Language.Code : ('ga', 'gle', 'gle'), Language.Country : 'ie', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Asụsụ Igbo', Language.NameEnglish : 'Igbo', Language.NameFrench : 'Igbo', Language.NameSpanish : 'Igbo', Language.NamePortuguese : 'Igbo', Language.NameItalian : 'Igbo', Language.NameGerman : 'Igbo', Language.NameDutch : 'Igbo', Language.NameRussian : 'Igbo' }, Language.Code : ('ig', 'ibo', 'ibo'), Language.Country : 'ng', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Inupiatun', Language.NameEnglish : 'Inupiaq', Language.NameFrench : 'Inupiaq', Language.NameSpanish : 'Inúpuloq', Language.NamePortuguese : 'Inupiaq', Language.NameItalian : 'Inupiaq', Language.NameGerman : 'Inupiaq', Language.NameDutch : 'Inpiaq', Language.NameRussian : 'Inupiaq' }, Language.Code : ('ik', 'ipk', 'ipk'), Language.Country : 'us', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Ido', Language.NameEnglish : 'Ido', Language.NameFrench : 'Ido', Language.NameSpanish : 'Ido', Language.NamePortuguese : 'Ido', Language.NameItalian : 'Ido', Language.NameGerman : 'Ido', Language.NameDutch : 'Ido', Language.NameRussian : 'Ido' }, Language.Code : ('io', 'ido', 'ido'), Language.Country : Language.CountryNone, Language.Frequency : Language.FrequencyNone },
				{ Language.Name : { Language.NameNative : 'Íslenska', Language.NameEnglish : 'Icelandic', Language.NameFrench : 'Islandais', Language.NameSpanish : 'Islandés', Language.NamePortuguese : 'Islandês', Language.NameItalian : 'Islandese', Language.NameGerman : 'Isländisch', Language.NameDutch : 'Ijslands', Language.NameRussian : 'Исландский' }, Language.Code : ('is', 'ice', 'isl'), Language.Country : 'is', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Italiano', Language.NameEnglish : 'Italian', Language.NameFrench : 'Italien', Language.NameSpanish : 'Italiano', Language.NamePortuguese : 'Italiano', Language.NameItalian : 'Italiano', Language.NameGerman : 'Italienisch', Language.NameDutch : 'Italiaans', Language.NameRussian : 'Итальянский' }, Language.Code : ('it', 'ita', 'ita'), Language.Country : 'it', Language.Frequency : Language.FrequencyCommon },
				{ Language.Name : { Language.NameNative : 'ᐃᓄᒃᑎᑐᑦ', Language.NameEnglish : 'Inuktitut', Language.NameFrench : 'Inuktitut', Language.NameSpanish : 'Inuktitut', Language.NamePortuguese : 'Inuktitut', Language.NameItalian : 'Inuktitut', Language.NameGerman : 'Inktitutisch', Language.NameDutch : 'Inuktitut', Language.NameRussian : 'Inuktitut' }, Language.Code : ('iu', 'iku', 'iku'), Language.Country : 'ca', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : '日本語', Language.NameEnglish : 'Japanese', Language.NameFrench : 'Japonais', Language.NameSpanish : 'Japonés', Language.NamePortuguese : 'Japonês', Language.NameItalian : 'Giapponese', Language.NameGerman : 'Japanisch', Language.NameDutch : 'Japans', Language.NameRussian : 'Японский' }, Language.Code : ('ja', 'jpn', 'jpn'), Language.Country : 'jp', Language.Frequency : Language.FrequencyCommon },
				{ Language.Name : { Language.NameNative : 'Baṣa Jawa', Language.NameEnglish : 'Javanese', Language.NameFrench : 'Javanais', Language.NameSpanish : 'Javanés', Language.NamePortuguese : 'Javanese', Language.NameItalian : 'Giavanese', Language.NameGerman : 'Javanesisch', Language.NameDutch : 'Javaans', Language.NameRussian : 'Javanese' }, Language.Code : ('jv', 'jav', 'jav'), Language.Country : 'id', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'ಕನ್ನಡ', Language.NameEnglish : 'Kannada', Language.NameFrench : 'Kannada', Language.NameSpanish : 'Kannada', Language.NamePortuguese : 'Kannada', Language.NameItalian : 'Kannada', Language.NameGerman : 'Kannada', Language.NameDutch : 'Kannada', Language.NameRussian : 'Канада' }, Language.Code : ('kn', 'kan', 'kan'), Language.Country : 'in', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Kanuri', Language.NameEnglish : 'Kanuri', Language.NameFrench : 'Kanuri', Language.NameSpanish : 'Kanuri', Language.NamePortuguese : 'Kanuri', Language.NameItalian : 'Kanuri', Language.NameGerman : 'Kanuri', Language.NameDutch : 'Kanuri', Language.NameRussian : 'Канури' }, Language.Code : ('kr', 'kau', 'kau'), Language.Country : 'ng', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'कॉशुर', Language.NameEnglish : 'Kashmiri', Language.NameFrench : 'Kashmiri', Language.NameSpanish : 'Kashmiri', Language.NamePortuguese : 'Cashmiri', Language.NameItalian : 'Kashmiri', Language.NameGerman : 'Kaschmiri', Language.NameDutch : 'Kashmiri', Language.NameRussian : 'Кашмири' }, Language.Code : ('ks', 'kas', 'kas'), Language.Country : 'in', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Қазақ Tілі', Language.NameEnglish : 'Kazakh', Language.NameFrench : 'Kazakh', Language.NameSpanish : 'Kazakh', Language.NamePortuguese : 'Cazaque', Language.NameItalian : 'Kazako', Language.NameGerman : 'Kasakh', Language.NameDutch : 'Kazachs', Language.NameRussian : 'Казахский' }, Language.Code : ('kk', 'kaz', 'kaz'), Language.Country : 'kz', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'ភាសាខ្មែរ', Language.NameEnglish : 'Khmer', Language.NameFrench : 'Khmer', Language.NameSpanish : 'Khmer', Language.NamePortuguese : 'Khmer', Language.NameItalian : 'Khmer', Language.NameGerman : 'Khmer', Language.NameDutch : 'Khmer', Language.NameRussian : 'Khmer' }, Language.Code : ('km', 'khm', 'khm'), Language.Country : 'kh', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Gĩkũyũ', Language.NameEnglish : 'Kikuyu', Language.NameFrench : 'Kikuyu', Language.NameSpanish : 'Kikuyu', Language.NamePortuguese : 'Kikuyu', Language.NameItalian : 'Kikuyu', Language.NameGerman : 'Kikuyu', Language.NameDutch : 'Kikuyu', Language.NameRussian : 'Кикую' }, Language.Code : ('ki', 'kik', 'kik'), Language.Country : 'ke', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Ikinyarwanda', Language.NameEnglish : 'Kinyarwanda', Language.NameFrench : 'Kinyarwanda', Language.NameSpanish : 'Kinyarwanda', Language.NamePortuguese : 'Kinyarwanda', Language.NameItalian : 'Kinyarwanda', Language.NameGerman : 'Kinyarwanda', Language.NameDutch : 'Kinyarwanda', Language.NameRussian : 'Киньярванда' }, Language.Code : ('rw', 'kin', 'kin'), Language.Country : 'rw', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'íkiRǔndi', Language.NameEnglish : 'Kirundi', Language.NameFrench : 'Kirundi', Language.NameSpanish : 'Kirundi', Language.NamePortuguese : 'Kirundi', Language.NameItalian : 'Kirundi', Language.NameGerman : 'Kirundi', Language.NameDutch : 'Kirundi', Language.NameRussian : 'Kirundi' }, Language.Code : ('rn', 'run', 'run'), Language.Country : 'bi', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Кыргызча', Language.NameEnglish : 'Kyrgyz', Language.NameFrench : 'Kirghize', Language.NameSpanish : 'Kirguisa', Language.NamePortuguese : 'Quirguistão', Language.NameItalian : 'Kirghiz', Language.NameGerman : 'Kirgisisch', Language.NameDutch : 'Kirgizië', Language.NameRussian : 'Кыргыз' }, Language.Code : ('ky', 'kir', 'kir'), Language.Country : 'kg', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Коми кыв', Language.NameEnglish : 'Komi', Language.NameFrench : 'Komi', Language.NameSpanish : 'Komi', Language.NamePortuguese : 'Komi', Language.NameItalian : 'Komi', Language.NameGerman : 'Komi', Language.NameDutch : 'Komi', Language.NameRussian : 'Komi' }, Language.Code : ('kv', 'kom', 'kom'), Language.Country : 'ru', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Kikongo', Language.NameEnglish : 'Kongo', Language.NameFrench : 'Kongo', Language.NameSpanish : 'Kongo', Language.NamePortuguese : 'Kongo', Language.NameItalian : 'Kongo', Language.NameGerman : 'Kongo', Language.NameDutch : 'Kongo', Language.NameRussian : 'Конто' }, Language.Code : ('kg', 'kon', 'kon'), Language.Country : 'cd', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : '한국어', Language.NameEnglish : 'Korean', Language.NameFrench : 'Coréen', Language.NameSpanish : 'Coreano', Language.NamePortuguese : 'Coreano', Language.NameItalian : 'Coreano', Language.NameGerman : 'Koreanisch', Language.NameDutch : 'Koreaans', Language.NameRussian : 'Корейский' }, Language.Code : ('ko', 'kor', 'kor'), Language.Country : 'kr', Language.Frequency : Language.FrequencyCommon },
				{ Language.Name : { Language.NameNative : 'Kurdí', Language.NameEnglish : 'Kurdish', Language.NameFrench : 'Kurde', Language.NameSpanish : 'Kurdo', Language.NamePortuguese : 'Curdo', Language.NameItalian : 'Kurdo', Language.NameGerman : 'Kurdisch', Language.NameDutch : 'Koerdisch', Language.NameRussian : 'Курдский' }, Language.Code : ('ku', 'kur', 'kur'), Language.Country : 'iq', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Oshikwanyama', Language.NameEnglish : 'Kwanyama', Language.NameFrench : 'Kwanyama', Language.NameSpanish : 'Kwanyama', Language.NamePortuguese : 'Kwanyama', Language.NameItalian : 'Kwanyama', Language.NameGerman : 'Kwanyama', Language.NameDutch : 'Kwanyama', Language.NameRussian : 'Kwanyama' }, Language.Code : ('kj', 'kua', 'kua'), Language.Country : 'ao', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Lingua Latina', Language.NameEnglish : 'Latin', Language.NameFrench : 'Latin', Language.NameSpanish : 'Latín', Language.NamePortuguese : 'Latina', Language.NameItalian : 'Latina', Language.NameGerman : 'Latein', Language.NameDutch : 'Latijns', Language.NameRussian : 'Латинский' }, Language.Code : ('la', 'lat', 'lat'), Language.Country : 'it', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Lëtzebuergesch', Language.NameEnglish : 'Luxembourgish', Language.NameFrench : 'Luxembourgeois', Language.NameSpanish : 'Luxemburgués', Language.NamePortuguese : 'Luxemburguês', Language.NameItalian : 'Lussemburghese', Language.NameGerman : 'Luxemburgisch', Language.NameDutch : 'Luxemburgs', Language.NameRussian : 'Люксембургиш' }, Language.Code : ('lb', 'ltz', 'ltz'), Language.Country : 'lu', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Lèmburgs', Language.NameEnglish : 'Limburgish', Language.NameFrench : 'Limburgish', Language.NameSpanish : 'Limbúrgico', Language.NamePortuguese : 'Limburgo', Language.NameItalian : 'Limbongshish', Language.NameGerman : 'Limburgisch', Language.NameDutch : 'Limburgs', Language.NameRussian : 'Лимбургский' }, Language.Code : ('li', 'lim', 'lim'), Language.Country : 'nl', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Lingála', Language.NameEnglish : 'Lingala', Language.NameFrench : 'Lingala', Language.NameSpanish : 'Lingala', Language.NamePortuguese : 'Lingala', Language.NameItalian : 'Lingala', Language.NameGerman : 'Lingala', Language.NameDutch : 'Lingala', Language.NameRussian : 'Лингла' }, Language.Code : ('ln', 'lin', 'lin'), Language.Country : 'cd', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'ພາສາລາວ', Language.NameEnglish : 'Lao', Language.NameFrench : 'Lao', Language.NameSpanish : 'Lao', Language.NamePortuguese : 'Lao', Language.NameItalian : 'Lao', Language.NameGerman : 'Lao', Language.NameDutch : 'Lao', Language.NameRussian : 'Лаос' }, Language.Code : ('lo', 'lao', 'lao'), Language.Country : 'la', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Lietuvių', Language.NameEnglish : 'Lithuanian', Language.NameFrench : 'Lituanien', Language.NameSpanish : 'Lituano', Language.NamePortuguese : 'Lituano', Language.NameItalian : 'Lituano', Language.NameGerman : 'Litauisch', Language.NameDutch : 'Litouws', Language.NameRussian : 'Литовский' }, Language.Code : ('lt', 'lit', 'lit'), Language.Country : 'lt', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Tshiluba', Language.NameEnglish : 'Luba-Kasai', Language.NameFrench : 'Luba-Kasaï', Language.NameSpanish : 'Luba-Kasai', Language.NamePortuguese : 'Luba-Kasai', Language.NameItalian : 'Luba-Kasai', Language.NameGerman : 'Luba-Kasai', Language.NameDutch : 'Luba-Kasai', Language.NameRussian : 'Luba-Kasai' }, Language.Code : ('lu', 'lub', 'lub'), Language.Country : 'cd', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Latviešu', Language.NameEnglish : 'Latvian', Language.NameFrench : 'Letton', Language.NameSpanish : 'Letón', Language.NamePortuguese : 'Letão', Language.NameItalian : 'Lettone', Language.NameGerman : 'Lettisch', Language.NameDutch : 'Letland', Language.NameRussian : 'Латышский' }, Language.Code : ('lv', 'lav', 'lav'), Language.Country : 'lv', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Gaelg', Language.NameEnglish : 'Manx', Language.NameFrench : 'Manx', Language.NameSpanish : 'Manx', Language.NamePortuguese : 'Manx', Language.NameItalian : 'Manx', Language.NameGerman : 'Manx', Language.NameDutch : 'Manx', Language.NameRussian : 'Манс' }, Language.Code : ('gv', 'glv', 'glv'), Language.Country : 'im', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Mакедонски', Language.NameEnglish : 'Macedonian', Language.NameFrench : 'Macédonien', Language.NameSpanish : 'Macedónio', Language.NamePortuguese : 'Macedônio', Language.NameItalian : 'Macedone', Language.NameGerman : 'Mazedonisch', Language.NameDutch : 'Macedonisch', Language.NameRussian : 'Македонский' }, Language.Code : ('mk', 'mac', 'mkd'), Language.Country : 'mk', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Malagasy', Language.NameEnglish : 'Malagasy', Language.NameFrench : 'Malgache', Language.NameSpanish : 'Madagascarí', Language.NamePortuguese : 'Malgaxe', Language.NameItalian : 'Malgascio', Language.NameGerman : 'Malagassisch', Language.NameDutch : 'Madagaskar', Language.NameRussian : 'Малагасия' }, Language.Code : ('mg', 'mlg', 'mlg'), Language.Country : 'mg', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Bahasa Melayu', Language.NameEnglish : 'Malay', Language.NameFrench : 'Malais', Language.NameSpanish : 'Malayo', Language.NamePortuguese : 'Malaio', Language.NameItalian : 'Malese', Language.NameGerman : 'Malaiisch', Language.NameDutch : 'Maleis', Language.NameRussian : 'Малайский' }, Language.Code : ('ms', 'may', 'msa'), Language.Country : 'my', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'മലയാളം', Language.NameEnglish : 'Malayalam', Language.NameFrench : 'Malayalam', Language.NameSpanish : 'Malayalam', Language.NamePortuguese : 'Malayalam', Language.NameItalian : 'Malayalam', Language.NameGerman : 'Malayalam', Language.NameDutch : 'Malayalam', Language.NameRussian : 'Малаялам' }, Language.Code : ('ml', 'mal', 'mal'), Language.Country : 'in', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'ދިވެހި', Language.NameEnglish : 'Maldivian', Language.NameFrench : 'Maldivien', Language.NameSpanish : 'Maldigiento', Language.NamePortuguese : 'Maldivian', Language.NameItalian : 'Maldiviano', Language.NameGerman : 'Maledivianer', Language.NameDutch : 'Maldivian', Language.NameRussian : 'Мальдивиан' }, Language.Code : ('dv', 'div', 'div'), Language.Country : 'mv', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Malti', Language.NameEnglish : 'Maltese', Language.NameFrench : 'Maltais', Language.NameSpanish : 'Maltés', Language.NamePortuguese : 'Maltês', Language.NameItalian : 'Maltese', Language.NameGerman : 'Maltesisch', Language.NameDutch : 'Maltees', Language.NameRussian : 'Мальтий' }, Language.Code : ('mt', 'mlt', 'mlt'), Language.Country : 'mt', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Te Reo Māori', Language.NameEnglish : 'Maori', Language.NameFrench : 'Maori', Language.NameSpanish : 'Maorí', Language.NamePortuguese : 'Maori', Language.NameItalian : 'Maori', Language.NameGerman : 'Maori', Language.NameDutch : 'Maori', Language.NameRussian : 'Маори' }, Language.Code : ('mi', 'mao', 'mri'), Language.Country : 'nz', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'मराठी', Language.NameEnglish : 'Marathi', Language.NameFrench : 'Marathi', Language.NameSpanish : 'Marathi', Language.NamePortuguese : 'Marathi', Language.NameItalian : 'Marathi', Language.NameGerman : 'Marathi', Language.NameDutch : 'Marathi', Language.NameRussian : 'Маратхи' }, Language.Code : ('mr', 'mar', 'mar'), Language.Country : 'in', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Kajin M̧ajeļ', Language.NameEnglish : 'Marshallese', Language.NameFrench : 'Marshallese', Language.NameSpanish : 'Marshallese', Language.NamePortuguese : 'Marshallese', Language.NameItalian : 'Marshalese', Language.NameGerman : 'Marshalsesee', Language.NameDutch : 'Marshallese', Language.NameRussian : 'Marshallese' }, Language.Code : ('mh', 'mah', 'mah'), Language.Country : 'mh', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'монгол', Language.NameEnglish : 'Mongolian', Language.NameFrench : 'Mongol', Language.NameSpanish : 'Mongol', Language.NamePortuguese : 'Mongol', Language.NameItalian : 'Mongolo', Language.NameGerman : 'Mongolisch', Language.NameDutch : 'Mongools', Language.NameRussian : 'Монгольский' }, Language.Code : ('mn', 'mon', 'mon'), Language.Country : 'mn', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Ekakairũ Naoero', Language.NameEnglish : 'Nauru', Language.NameFrench : 'Nauru', Language.NameSpanish : 'Nauru', Language.NamePortuguese : 'Nauru', Language.NameItalian : 'Naurlu', Language.NameGerman : 'Nauru', Language.NameDutch : 'Nauru', Language.NameRussian : 'Науру' }, Language.Code : ('na', 'nau', 'nau'), Language.Country : 'nr', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Diné Bizaad', Language.NameEnglish : 'Navajo', Language.NameFrench : 'Navajo', Language.NameSpanish : 'Navajo', Language.NamePortuguese : 'Navajo', Language.NameItalian : 'Navajo', Language.NameGerman : 'Navajo', Language.NameDutch : 'Navajo', Language.NameRussian : 'Навася' }, Language.Code : ('nv', 'nav', 'nav'), Language.Country : 'us', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Sindebele', Language.NameEnglish : 'North Ndebele', Language.NameFrench : 'North Ndebele', Language.NameSpanish : 'Norte Ndebele', Language.NamePortuguese : 'North Ndebele', Language.NameItalian : 'N. Ndebele', Language.NameGerman : 'Nordndebele', Language.NameDutch : 'North Ndebele', Language.NameRussian : 'Северная Ндебеле' }, Language.Code : ('nd', 'nde', 'nde'), Language.Country : 'zw', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'नेपाली', Language.NameEnglish : 'Nepali', Language.NameFrench : 'Népalais', Language.NameSpanish : 'Nepalí', Language.NamePortuguese : 'Nepali', Language.NameItalian : 'Nepalese', Language.NameGerman : 'Nepali', Language.NameDutch : 'Nepali', Language.NameRussian : 'Непальский' }, Language.Code : ('ne', 'nep', 'nep'), Language.Country : 'np', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Oshindonga', Language.NameEnglish : 'Ndonga', Language.NameFrench : 'Ndonga', Language.NameSpanish : 'Ndonga', Language.NamePortuguese : 'Ndonga', Language.NameItalian : 'Ndonga', Language.NameGerman : 'Ndonga', Language.NameDutch : 'Ndonga', Language.NameRussian : 'Ndonga' }, Language.Code : ('ng', 'ndo', 'ndo'), Language.Country : 'na', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Norsk', Language.NameEnglish : 'Norwegian', Language.NameFrench : 'Norvégien', Language.NameSpanish : 'Noruego', Language.NamePortuguese : 'Norueguês', Language.NameItalian : 'Norvegese', Language.NameGerman : 'Norwegisch', Language.NameDutch : 'Noors', Language.NameRussian : 'Норвежский' }, Language.Code : ('no', 'nor', 'nor'), Language.Country : 'no', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Nuosuhxop', Language.NameEnglish : 'Nuosu', Language.NameFrench : 'Nuosu', Language.NameSpanish : 'Nuosu', Language.NamePortuguese : 'Nuosu', Language.NameItalian : 'Nuosu', Language.NameGerman : 'Nuosu', Language.NameDutch : 'Nuosu', Language.NameRussian : 'Несущий' }, Language.Code : ('ii', 'iii', 'iii'), Language.Country : 'cn', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Nynorsk', Language.NameEnglish : 'Nynorsk', Language.NameFrench : 'Nynorsk', Language.NameSpanish : 'Nynorsk', Language.NamePortuguese : 'Nynorsk', Language.NameItalian : 'Nynorsk', Language.NameGerman : 'Nynorsk', Language.NameDutch : 'Nynorsk', Language.NameRussian : 'Nynorsk' }, Language.Code : ('nn', 'nno', 'nno'), Language.Country : 'no', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Occitan', Language.NameEnglish : 'Occitan', Language.NameFrench : 'Occitan', Language.NameSpanish : 'Occitano', Language.NamePortuguese : 'Occitano', Language.NameItalian : 'Occitano', Language.NameGerman : 'Okzitanisch', Language.NameDutch : 'Occitaan', Language.NameRussian : 'Заклинание' }, Language.Code : ('oc', 'oci', 'oci'), Language.Country : 'fr', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'ᐊᓂᔑᓈᐯᒧᐎᓐ', Language.NameEnglish : 'Ojibwe', Language.NameFrench : 'Ojibwe', Language.NameSpanish : 'Ojibwe', Language.NamePortuguese : 'Ojibwe', Language.NameItalian : 'Ojibwe', Language.NameGerman : 'Ojibwe', Language.NameDutch : 'Ojibwe', Language.NameRussian : 'Ojibwe' }, Language.Code : ('oj', 'oji', 'oji'), Language.Country : 'ca', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'словѣньскъ', Language.NameEnglish : 'Old Slavonic', Language.NameFrench : 'Vieux Slave', Language.NameSpanish : 'Viejo Eslavo', Language.NamePortuguese : 'Velho Eslavo', Language.NameItalian : 'Vecchio Slavo', Language.NameGerman : 'Altslawisch', Language.NameDutch : 'Oud Slavisch', Language.NameRussian : 'Старый Славян' }, Language.Code : ('cu', 'chu', 'chu'), Language.Country : 'sk', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Afaan Oromoo', Language.NameEnglish : 'Oromo', Language.NameFrench : 'Oromo', Language.NameSpanish : 'Oromo', Language.NamePortuguese : 'Oromo', Language.NameItalian : 'Oromo', Language.NameGerman : 'Oromo', Language.NameDutch : 'Oromo', Language.NameRussian : 'Oromo' }, Language.Code : ('om', 'orm', 'orm'), Language.Country : 'et', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'ଓଡ଼ିଆ', Language.NameEnglish : 'Oriya', Language.NameFrench : 'Oriya', Language.NameSpanish : 'Oriya', Language.NamePortuguese : 'Oriya', Language.NameItalian : 'Oriya', Language.NameGerman : 'Oriya', Language.NameDutch : 'Oriya', Language.NameRussian : 'Ория' }, Language.Code : ('or', 'ori', 'ori'), Language.Country : 'in', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'ирон æвзаг', Language.NameEnglish : 'Ossetian', Language.NameFrench : 'Ossète', Language.NameSpanish : 'Osetiano', Language.NamePortuguese : 'Ossetian', Language.NameItalian : 'Ossetian', Language.NameGerman : 'Ossetian', Language.NameDutch : 'Ossetisch', Language.NameRussian : 'Осетинский' }, Language.Code : ('os', 'oss', 'oss'), Language.Country : 'ru', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'ਪੰਜਾਬੀ', Language.NameEnglish : 'Punjabi', Language.NameFrench : 'Punjabi', Language.NameSpanish : 'Punjabi', Language.NamePortuguese : 'Punjabi', Language.NameItalian : 'Punjabi', Language.NameGerman : 'Punjabi', Language.NameDutch : 'Punjabi', Language.NameRussian : 'Пенджаби' }, Language.Code : ('pa', 'pan', 'pan'), Language.Country : 'pk', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'पालि', Language.NameEnglish : 'Pali', Language.NameFrench : 'Pali', Language.NameSpanish : 'Pali', Language.NamePortuguese : 'Pali', Language.NameItalian : 'Pali', Language.NameGerman : 'Pali', Language.NameDutch : 'Pali', Language.NameRussian : 'Пали' }, Language.Code : ('pi', 'pli', 'pli'), Language.Country : 'in', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'فارسی', Language.NameEnglish : 'Persian', Language.NameFrench : 'Persan', Language.NameSpanish : 'Persa', Language.NamePortuguese : 'Persa', Language.NameItalian : 'Persiano', Language.NameGerman : 'Persisch', Language.NameDutch : 'Perzisch', Language.NameRussian : 'Персидский' }, Language.Code : ('fa', 'per', 'fas'), Language.Country : 'ir', Language.Frequency : Language.FrequencyCommon },
				{ Language.Name : { Language.NameNative : 'Polski', Language.NameEnglish : 'Polish', Language.NameFrench : 'Polonais', Language.NameSpanish : 'Polaco', Language.NamePortuguese : 'Polonês', Language.NameItalian : 'Polacco', Language.NameGerman : 'Polieren', Language.NameDutch : 'Pools', Language.NameRussian : 'Польский' }, Language.Code : ('pl', 'pol', 'pol'), Language.Country : 'pl', Language.Frequency : Language.FrequencyCommon },
				{ Language.Name : { Language.NameNative : 'پښتو', Language.NameEnglish : 'Pashto', Language.NameFrench : 'Pashto', Language.NameSpanish : 'Pashto', Language.NamePortuguese : 'Pashto', Language.NameItalian : 'Pashto', Language.NameGerman : 'Pashto', Language.NameDutch : 'Pashto', Language.NameRussian : 'Пашто' }, Language.Code : ('ps', 'pus', 'pus'), Language.Country : 'af', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Português', Language.NameEnglish : 'Portuguese', Language.NameFrench : 'Portugais', Language.NameSpanish : 'Portugués', Language.NamePortuguese : 'Português', Language.NameItalian : 'Portoghese', Language.NameGerman : 'Portugiesisch', Language.NameDutch : 'Portugees', Language.NameRussian : 'Португальский' }, Language.Code : ('pt', 'por', 'por'), Language.Country : 'pt', Language.Frequency : Language.FrequencyCommon },
				{ Language.Name : { Language.NameNative : 'Qhichwa', Language.NameEnglish : 'Quechua', Language.NameFrench : 'Quechua', Language.NameSpanish : 'Quechua', Language.NamePortuguese : 'Quechua', Language.NameItalian : 'Quechua', Language.NameGerman : 'Quechua', Language.NameDutch : 'Quechua', Language.NameRussian : 'Кечуа' }, Language.Code : ('qu', 'que', 'que'), Language.Country : 'pe', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Rumantsch', Language.NameEnglish : 'Romansh', Language.NameFrench : 'Romansh', Language.NameSpanish : 'Romansh', Language.NamePortuguese : 'Romanês', Language.NameItalian : 'Romancio', Language.NameGerman : 'Romansh', Language.NameDutch : 'Romansh', Language.NameRussian : 'Romansh' }, Language.Code : ('rm', 'roh', 'roh'), Language.Country : 'ch', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Română', Language.NameEnglish : 'Romanian', Language.NameFrench : 'Roumain', Language.NameSpanish : 'Rumano', Language.NamePortuguese : 'Romena', Language.NameItalian : 'Rumeno', Language.NameGerman : 'Rumänisch', Language.NameDutch : 'Roemeense', Language.NameRussian : 'Румынский' }, Language.Code : ('ro', 'rum', 'ron'), Language.Country : 'ro', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Русский', Language.NameEnglish : 'Russian', Language.NameFrench : 'Russe', Language.NameSpanish : 'Ruso', Language.NamePortuguese : 'Russo', Language.NameItalian : 'Russo', Language.NameGerman : 'Russisch', Language.NameDutch : 'Russisch', Language.NameRussian : 'Русский' }, Language.Code : ('ru', 'rus', 'rus'), Language.Country : 'ru', Language.Frequency : Language.FrequencyCommon },
				{ Language.Name : { Language.NameNative : 'संस्कृतम्', Language.NameEnglish : 'Sanskrit', Language.NameFrench : 'Sanskrit', Language.NameSpanish : 'Sánscrito', Language.NamePortuguese : 'Sânscrito', Language.NameItalian : 'Sanscrito', Language.NameGerman : 'Sanskrit', Language.NameDutch : 'Sanskriet', Language.NameRussian : 'Санскрит' }, Language.Code : ('sa', 'san', 'san'), Language.Country : 'in', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Sardu', Language.NameEnglish : 'Sardinian', Language.NameFrench : 'Sarde', Language.NameSpanish : 'Sardo', Language.NamePortuguese : 'Sardenha', Language.NameItalian : 'Sardo', Language.NameGerman : 'Sardinier', Language.NameDutch : 'Sardisch', Language.NameRussian : 'Сардин' }, Language.Code : ('sc', 'srd', 'srd'), Language.Country : 'it', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'سنڌي', Language.NameEnglish : 'Sindhi', Language.NameFrench : 'Sindhi', Language.NameSpanish : 'Sindhi', Language.NamePortuguese : 'Sindi', Language.NameItalian : 'Sindhi', Language.NameGerman : 'Sindhi', Language.NameDutch : 'Sindhi', Language.NameRussian : 'Sindhi' }, Language.Code : ('sd', 'snd', 'snd'), Language.Country : 'in', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Sámi', Language.NameEnglish : 'Sami', Language.NameFrench : 'Sami', Language.NameSpanish : 'Sami', Language.NamePortuguese : 'Sami', Language.NameItalian : 'Sami', Language.NameGerman : 'Sami', Language.NameDutch : 'Sami', Language.NameRussian : 'Сами' }, Language.Code : ('se', 'smi', 'sme'), Language.Country : 'se', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Gagana Sāmoa', Language.NameEnglish : 'Samoan', Language.NameFrench : 'Samoan', Language.NameSpanish : 'Samoano', Language.NamePortuguese : 'Samoan', Language.NameItalian : 'Samoan', Language.NameGerman : 'Samoan', Language.NameDutch : 'Samoan', Language.NameRussian : 'Самоан' }, Language.Code : ('sm', 'smo', 'smo'), Language.Country : 'ws', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Yângâ tî Sängö', Language.NameEnglish : 'Sango', Language.NameFrench : 'Sango', Language.NameSpanish : 'Sango', Language.NamePortuguese : 'Sango', Language.NameItalian : 'Sango', Language.NameGerman : 'Sango', Language.NameDutch : 'Sango', Language.NameRussian : 'Санго' }, Language.Code : ('sg', 'sag', 'sag'), Language.Country : 'cf', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Српски', Language.NameEnglish : 'Serbian', Language.NameFrench : 'Serbe', Language.NameSpanish : 'Serbio', Language.NamePortuguese : 'Sérvio', Language.NameItalian : 'Serbo', Language.NameGerman : 'Serbisch', Language.NameDutch : 'Servisch', Language.NameRussian : 'Сербский' }, Language.Code : ('sr', 'srp', 'srp'), Language.Country : 'rs', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Gàidhlig', Language.NameEnglish : 'Gaelic', Language.NameFrench : 'Gaélique', Language.NameSpanish : 'Gaélico', Language.NamePortuguese : 'Gaélico', Language.NameItalian : 'Gaelico', Language.NameGerman : 'Gälisch', Language.NameDutch : 'Gaelisch', Language.NameRussian : 'Гаельский' }, Language.Code : ('gd', 'gla', 'gla'), Language.Country : 'gb', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Shona', Language.NameEnglish : 'Shona', Language.NameFrench : 'Shona', Language.NameSpanish : 'Shona', Language.NamePortuguese : 'Shona', Language.NameItalian : 'Shona', Language.NameGerman : 'Shona', Language.NameDutch : 'Shona', Language.NameRussian : 'Сюжета' }, Language.Code : ('sn', 'sna', 'sna'), Language.Country : 'zw', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'සිංහල', Language.NameEnglish : 'Sinhala', Language.NameFrench : 'Sinhala', Language.NameSpanish : 'Sinhala', Language.NamePortuguese : 'Sinhala', Language.NameItalian : 'Singala', Language.NameGerman : 'Sinhala', Language.NameDutch : 'Sinhala', Language.NameRussian : 'Синала' }, Language.Code : ('si', 'sin', 'sin'), Language.Country : 'lk', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Slovenčina', Language.NameEnglish : 'Slovak', Language.NameFrench : 'Slovaque', Language.NameSpanish : 'Eslovaco', Language.NamePortuguese : 'Eslovaco', Language.NameItalian : 'Slovacco', Language.NameGerman : 'Slowakisch', Language.NameDutch : 'Slowaaks', Language.NameRussian : 'Словацкий' }, Language.Code : ('sk', 'slo', 'slk'), Language.Country : 'sk', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Slovenščina', Language.NameEnglish : 'Slovene', Language.NameFrench : 'Slovène', Language.NameSpanish : 'Esloveno', Language.NamePortuguese : 'Esloveno', Language.NameItalian : 'Sloveno', Language.NameGerman : 'Slowenisch', Language.NameDutch : 'Sloveens', Language.NameRussian : 'Словен' }, Language.Code : ('sl', 'slv', 'slv'), Language.Country : 'si', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Af Soomaali', Language.NameEnglish : 'Somali', Language.NameFrench : 'Somali', Language.NameSpanish : 'Somalí', Language.NamePortuguese : 'Somali', Language.NameItalian : 'Somalo', Language.NameGerman : 'Somali', Language.NameDutch : 'Somalisch', Language.NameRussian : 'Сомалийский' }, Language.Code : ('so', 'som', 'som'), Language.Country : 'so', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Sesotho', Language.NameEnglish : 'Sotho', Language.NameFrench : 'Sotho', Language.NameSpanish : 'Soto', Language.NamePortuguese : 'Soto', Language.NameItalian : 'Sothe', Language.NameGerman : 'Sotho', Language.NameDutch : 'Sotho', Language.NameRussian : 'Сото' }, Language.Code : ('st', 'sot', 'sot'), Language.Country : 'za', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'isiNdebele', Language.NameEnglish : 'South Ndebele', Language.NameFrench : 'South Ndebele', Language.NameSpanish : 'South Ndebele', Language.NamePortuguese : 'Ndebele Sul', Language.NameItalian : 'South Ndebele', Language.NameGerman : 'Südndebele', Language.NameDutch : 'Zuid Ndebele', Language.NameRussian : 'Южный Ндебеле' }, Language.Code : ('nr', 'nbl', 'nbl'), Language.Country : 'za', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Español', Language.NameEnglish : 'Spanish', Language.NameFrench : 'Espagnol', Language.NameSpanish : 'Español', Language.NamePortuguese : 'Espanhol', Language.NameItalian : 'Spagnolo', Language.NameGerman : 'Spanisch', Language.NameDutch : 'Spaans', Language.NameRussian : 'Испанский' }, Language.Code : ('es', 'spa', 'spa'), Language.Country : 'es', Language.Frequency : Language.FrequencyCommon },
				{ Language.Name : { Language.NameNative : 'Basa Sunda', Language.NameEnglish : 'Sundanese', Language.NameFrench : 'Sundanais', Language.NameSpanish : 'Sundana', Language.NamePortuguese : 'Sundanese', Language.NameItalian : 'Sundanese', Language.NameGerman : 'Sundanesisch', Language.NameDutch : 'Sundanese', Language.NameRussian : 'Sundanese' }, Language.Code : ('su', 'sun', 'sun'), Language.Country : 'id', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Kiswahili', Language.NameEnglish : 'Swahili', Language.NameFrench : 'Swahili', Language.NameSpanish : 'Swahili', Language.NamePortuguese : 'Swahili', Language.NameItalian : 'Swahili', Language.NameGerman : 'Swahili', Language.NameDutch : 'Swahili', Language.NameRussian : 'Суахили' }, Language.Code : ('sw', 'swa', 'swa'), Language.Country : 'tz', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'siSwati', Language.NameEnglish : 'Swati', Language.NameFrench : 'Swati', Language.NameSpanish : 'Swati', Language.NamePortuguese : 'Swati', Language.NameItalian : 'Swati', Language.NameGerman : 'Swati', Language.NameDutch : 'Swati', Language.NameRussian : 'Свати' }, Language.Code : ('ss', 'ssw', 'ssw'), Language.Country : 'sz', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Svenska', Language.NameEnglish : 'Swedish', Language.NameFrench : 'Suédois', Language.NameSpanish : 'Sueco', Language.NamePortuguese : 'Sueco', Language.NameItalian : 'Svedese', Language.NameGerman : 'Schwedisch', Language.NameDutch : 'Zweeds', Language.NameRussian : 'Шведский' }, Language.Code : ('sv', 'swe', 'swe'), Language.Country : 'se', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'தமிழ்', Language.NameEnglish : 'Tamil', Language.NameFrench : 'Tamil', Language.NameSpanish : 'Tamil', Language.NamePortuguese : 'Tâmil', Language.NameItalian : 'Tamil', Language.NameGerman : 'Tamilisch', Language.NameDutch : 'Tamil', Language.NameRussian : 'Тамил' }, Language.Code : ('ta', 'tam', 'tam'), Language.Country : 'in', Language.Frequency : Language.FrequencyCommon },
				{ Language.Name : { Language.NameNative : 'తెలుగు', Language.NameEnglish : 'Telugu', Language.NameFrench : 'Telugu', Language.NameSpanish : 'Telugu', Language.NamePortuguese : 'Telugu', Language.NameItalian : 'Telugu', Language.NameGerman : 'Telugu', Language.NameDutch : 'Telugu', Language.NameRussian : 'Телугу' }, Language.Code : ('te', 'tel', 'tel'), Language.Country : 'in', Language.Frequency : Language.FrequencyCommon },
				{ Language.Name : { Language.NameNative : 'тоҷики', Language.NameEnglish : 'Tajik', Language.NameFrench : 'Tajik', Language.NameSpanish : 'Tajik', Language.NamePortuguese : 'Tajik', Language.NameItalian : 'Tajik', Language.NameGerman : 'Tadschik', Language.NameDutch : 'Tadjik', Language.NameRussian : 'Таджикский' }, Language.Code : ('tg', 'tgk', 'tgk'), Language.Country : 'tj', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'ภาษาไทย', Language.NameEnglish : 'Thai', Language.NameFrench : 'Thaïlandais', Language.NameSpanish : 'Tailandés', Language.NamePortuguese : 'Tailandês', Language.NameItalian : 'Tailandese', Language.NameGerman : 'Thailändisch', Language.NameDutch : 'Thais', Language.NameRussian : 'Тайский' }, Language.Code : ('th', 'tha', 'tha'), Language.Country : 'th', Language.Frequency : Language.FrequencyCommon },
				{ Language.Name : { Language.NameNative : 'ትግርኛ', Language.NameEnglish : 'Tigrinya', Language.NameFrench : 'Tigrinya', Language.NameSpanish : 'Tigrinosa', Language.NamePortuguese : 'Tigrya', Language.NameItalian : 'Tigrenya', Language.NameGerman : 'Tigrinya', Language.NameDutch : 'Tigrinya', Language.NameRussian : 'Тигранья' }, Language.Code : ('ti', 'tir', 'tir'), Language.Country : 'er', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'དབུས་སྐད', Language.NameEnglish : 'Tibetan', Language.NameFrench : 'Tibétain', Language.NameSpanish : 'Tibetano', Language.NamePortuguese : 'Tibetano', Language.NameItalian : 'Tibetano', Language.NameGerman : 'Tibetanisch', Language.NameDutch : 'Tibetaans', Language.NameRussian : 'Тибетский' }, Language.Code : ('bo', 'tib', 'bod'), Language.Country : 'cn', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Türkmençe', Language.NameEnglish : 'Turkmen', Language.NameFrench : 'Turkmène', Language.NameSpanish : 'Turkmen', Language.NamePortuguese : 'Turkmen', Language.NameItalian : 'Turkmen', Language.NameGerman : 'Turkmen', Language.NameDutch : 'Turkmen', Language.NameRussian : 'Туркменский' }, Language.Code : ('tk', 'tuk', 'tuk'), Language.Country : 'tm', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Tagalog', Language.NameEnglish : 'Tagalog', Language.NameFrench : 'Tagalog', Language.NameSpanish : 'Tagalo', Language.NamePortuguese : 'Tagalog', Language.NameItalian : 'Tagalog', Language.NameGerman : 'Tagalog', Language.NameDutch : 'Tagalog', Language.NameRussian : 'Тагалог' }, Language.Code : ('tl', 'tgl', 'tgl'), Language.Country : 'ph', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Setswana', Language.NameEnglish : 'Tswana', Language.NameFrench : 'Tswana', Language.NameSpanish : 'Tswana', Language.NamePortuguese : 'Tswana', Language.NameItalian : 'Tswana', Language.NameGerman : 'Tswana', Language.NameDutch : 'Tswana', Language.NameRussian : 'Твана' }, Language.Code : ('tn', 'tsn', 'tsn'), Language.Country : 'za', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Faka-Tonga', Language.NameEnglish : 'Tongan', Language.NameFrench : 'Tongan', Language.NameSpanish : 'Tongan', Language.NamePortuguese : 'Tongania', Language.NameItalian : 'Tongan', Language.NameGerman : 'Tanganer', Language.NameDutch : 'Tongan', Language.NameRussian : 'Тонган' }, Language.Code : ('to', 'ton', 'ton'), Language.Country : 'to', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Türkçe', Language.NameEnglish : 'Turkish', Language.NameFrench : 'Turc', Language.NameSpanish : 'Turco', Language.NamePortuguese : 'Turco', Language.NameItalian : 'Turco', Language.NameGerman : 'Türkisch', Language.NameDutch : 'Turks', Language.NameRussian : 'Турецкий' }, Language.Code : ('tr', 'tur', 'tur'), Language.Country : 'tr', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Xitsonga', Language.NameEnglish : 'Tsonga', Language.NameFrench : 'Tsonga', Language.NameSpanish : 'Tsonga', Language.NamePortuguese : 'Tsonga', Language.NameItalian : 'Tsonga', Language.NameGerman : 'Tsonga', Language.NameDutch : 'Tsonga', Language.NameRussian : 'Цонга' }, Language.Code : ('ts', 'tso', 'tso'), Language.Country : 'za', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'татарча', Language.NameEnglish : 'Tatar', Language.NameFrench : 'Tatar', Language.NameSpanish : 'Tártaro', Language.NamePortuguese : 'Tártaro', Language.NameItalian : 'Tatar', Language.NameGerman : 'Tatar', Language.NameDutch : 'Tatar', Language.NameRussian : 'Татар' }, Language.Code : ('tt', 'tat', 'tat'), Language.Country : 'ru', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Twi', Language.NameEnglish : 'Twi', Language.NameFrench : 'Twi', Language.NameSpanish : 'Twi', Language.NamePortuguese : 'Twi', Language.NameItalian : 'Twi', Language.NameGerman : 'Twi', Language.NameDutch : 'Twi', Language.NameRussian : 'Twi' }, Language.Code : ('tw', 'twi', 'twi'), Language.Country : 'gh', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Reo Tahiti', Language.NameEnglish : 'Tahitian', Language.NameFrench : 'Tahitian', Language.NameSpanish : 'Tahitiano', Language.NamePortuguese : 'Taitian', Language.NameItalian : 'Tahitiano', Language.NameGerman : 'Tahitianer', Language.NameDutch : 'Tahitian', Language.NameRussian : 'Таитян' }, Language.Code : ('ty', 'tah', 'tah'), Language.Country : 'pf', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Українська', Language.NameEnglish : 'Ukrainian', Language.NameFrench : 'Ukrainien', Language.NameSpanish : 'Ucranio', Language.NamePortuguese : 'Ucraniano', Language.NameItalian : 'Ucraino', Language.NameGerman : 'Ukrainisch', Language.NameDutch : 'Oekraïens', Language.NameRussian : 'Украинец' }, Language.Code : ('uk', 'ukr', 'ukr'), Language.Country : 'ua', Language.Frequency : Language.FrequencyCommon },
				{ Language.Name : { Language.NameNative : 'اُردُو', Language.NameEnglish : 'Urdu', Language.NameFrench : 'Ourdou', Language.NameSpanish : 'Urdu', Language.NamePortuguese : 'Urdu', Language.NameItalian : 'Urdu', Language.NameGerman : 'Urdu', Language.NameDutch : 'Urdu', Language.NameRussian : 'Урду' }, Language.Code : ('ur', 'urd', 'urd'), Language.Country : 'pk', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'ئۇيغۇر', Language.NameEnglish : 'Uyghur', Language.NameFrench : 'Uyghur', Language.NameSpanish : 'Uyghur', Language.NamePortuguese : 'Uyghur', Language.NameItalian : 'Uyghur', Language.NameGerman : 'Uyghur', Language.NameDutch : 'Uyghur', Language.NameRussian : 'Уйгур' }, Language.Code : ('ug', 'uig', 'uig'), Language.Country : 'cn', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'اوزبیک', Language.NameEnglish : 'Uzbek', Language.NameFrench : 'Uzbek', Language.NameSpanish : 'Uzbeko', Language.NamePortuguese : 'Uzbeque', Language.NameItalian : 'Uzbeko', Language.NameGerman : 'Usbekisch', Language.NameDutch : 'Oezbeek', Language.NameRussian : 'Узбек' }, Language.Code : ('uz', 'uzb', 'uzb'), Language.Country : 'uz', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'Tshivenḓa', Language.NameEnglish : 'Venda', Language.NameFrench : 'Vendange', Language.NameSpanish : 'Vendedura', Language.NamePortuguese : 'Venda', Language.NameItalian : 'Venda', Language.NameGerman : 'Venda', Language.NameDutch : 'Venda', Language.NameRussian : 'Ведущий' }, Language.Code : ('ve', 'ven', 'ven'), Language.Country : 'za', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Tiếng Việt', Language.NameEnglish : 'Vietnamese', Language.NameFrench : 'Vietnamien', Language.NameSpanish : 'Vietnamita', Language.NamePortuguese : 'Vietnamita', Language.NameItalian : 'Vietnamita', Language.NameGerman : 'Vietnamesisch', Language.NameDutch : 'Vietnamees', Language.NameRussian : 'Вьетнамский' }, Language.Code : ('vi', 'vie', 'vie'), Language.Country : 'vn', Language.Frequency : Language.FrequencyCommon },
				{ Language.Name : { Language.NameNative : 'Volapük', Language.NameEnglish : 'Volapuk', Language.NameFrench : 'Volapuk', Language.NameSpanish : 'Volápuk', Language.NamePortuguese : 'Volapuk', Language.NameItalian : 'Volapuk', Language.NameGerman : 'Volapk', Language.NameDutch : 'Volapuk', Language.NameRussian : 'Волапук' }, Language.Code : ('vo', 'vol', 'vol'), Language.Country : Language.CountryNone, Language.Frequency : Language.FrequencyNone },
				{ Language.Name : { Language.NameNative : 'Walloon', Language.NameEnglish : 'Walloon', Language.NameFrench : 'Wallon', Language.NameSpanish : 'Valón', Language.NamePortuguese : 'Valão', Language.NameItalian : 'Walloon', Language.NameGerman : 'Wallonisch', Language.NameDutch : 'Waals', Language.NameRussian : 'Валлонский' }, Language.Code : ('wa', 'wln', 'wln'), Language.Country : 'be', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Cymraeg', Language.NameEnglish : 'Welsh', Language.NameFrench : 'Gallois', Language.NameSpanish : 'Galés', Language.NamePortuguese : 'Galês', Language.NameItalian : 'Gallese', Language.NameGerman : 'Walisisch', Language.NameDutch : 'Welsh', Language.NameRussian : 'Валлийский' }, Language.Code : ('cy', 'wel', 'cym'), Language.Country : 'gb', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Wolof', Language.NameEnglish : 'Wolof', Language.NameFrench : 'Wolof', Language.NameSpanish : 'Wolof', Language.NamePortuguese : 'Wolof', Language.NameItalian : 'Wolof', Language.NameGerman : 'Wolof', Language.NameDutch : 'Wolof', Language.NameRussian : 'Wolof' }, Language.Code : ('wo', 'wol', 'wol'), Language.Country : 'sn', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'isiXhosa', Language.NameEnglish : 'Xhosa', Language.NameFrench : 'Xhosa', Language.NameSpanish : 'Xhosa', Language.NamePortuguese : 'Xhosa', Language.NameItalian : 'Xhosa', Language.NameGerman : 'Xhosa', Language.NameDutch : 'Xhosa', Language.NameRussian : 'Xhosa' }, Language.Code : ('xh', 'xho', 'xho'), Language.Country : 'za', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : 'ײִדיש', Language.NameEnglish : 'Yiddish', Language.NameFrench : 'Yiddish', Language.NameSpanish : 'Yídish', Language.NamePortuguese : 'Iídiche', Language.NameItalian : 'Yiddish', Language.NameGerman : 'Jiddisch', Language.NameDutch : 'Jiddisch', Language.NameRussian : 'Идиш' }, Language.Code : ('yi', 'yid', 'yid'), Language.Country : 'il', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'Èdè Yorùbá', Language.NameEnglish : 'Yoruba', Language.NameFrench : 'Yoruba', Language.NameSpanish : 'Yoruba', Language.NamePortuguese : 'Yoruba', Language.NameItalian : 'Yoruba', Language.NameGerman : 'Yoruba', Language.NameDutch : 'Yoruba', Language.NameRussian : 'Йоруба' }, Language.Code : ('yo', 'yor', 'yor'), Language.Country : 'ng', Language.Frequency : Language.FrequencyOccasional },
				{ Language.Name : { Language.NameNative : '話僮', Language.NameEnglish : 'Zhuang', Language.NameFrench : 'Zhuang', Language.NameSpanish : 'Zhuang', Language.NamePortuguese : 'Zhuang', Language.NameItalian : 'Zhuang', Language.NameGerman : 'Zhuang', Language.NameDutch : 'Zhuang', Language.NameRussian : 'Zhuang' }, Language.Code : ('za', 'zha', 'zha'), Language.Country : 'cn', Language.Frequency : Language.FrequencyUncommon },
				{ Language.Name : { Language.NameNative : 'isiZulu', Language.NameEnglish : 'Zulu', Language.NameFrench : 'Zoulou', Language.NameSpanish : 'Zulú', Language.NamePortuguese : 'Zulu', Language.NameItalian : 'Zuli', Language.NameGerman : 'Zulu', Language.NameDutch : 'Zulu', Language.NameRussian : 'Zulu' }, Language.Code : ('zu', 'zul', 'zul'), Language.Country : 'za', Language.Frequency : Language.FrequencyOccasional },
			)

			# Only add "fallback" codes if Kodi cannot interpret them.
			# Add the code to a subtitle SRT file and check if Kodi detects the language correctly in the player's subtitle dialog.
			Language.Variations = (
				{Language.Original : Language.CodeChinese,		Language.Name : {Language.NameNative: '简体中文', Language.NameEnglish : 'Chinese (Simplified)'},														Language.Code : ('zh', 'chi', 'zho'),								Language.Country : 'cn',					Language.Frequency : Language.FrequencyCommon},
				{Language.Original : Language.CodeChinese,		Language.Name : {Language.NameNative: '繁体中文', Language.NameEnglish : 'Chinese (Traditional)'},														Language.Code : ('zt', 'zht', 'zht'),	Language.Fallback : 'chi', 	Language.Country : 'tw',					Language.Frequency : Language.FrequencyCommon},
				{Language.Original : Language.CodeChinese,		Language.Name : {Language.NameNative: '双语中文', Language.NameEnglish : 'Chinese (Bilingual)'},														Language.Code : ('ze', 'zhe', 'zhe'),	Language.Fallback : 'chi', 	Language.Country : 'cn',					Language.Frequency : Language.FrequencyCommon},

				{Language.Original : Language.CodePortuguese,	Language.Name : {Language.NameNative: 'Português (Portugal)', Language.NameEnglish : 'Portuguese (Portugal)', Language.NameUniversal : 'Portuguese'},	Language.Code : ('pt', 'por', 'por'),								Language.Country : 'pt',					Language.Frequency : Language.FrequencyCommon},
				{Language.Original : Language.CodePortuguese,	Language.Name : {Language.NameNative: 'Português (Brasil)', Language.NameEnglish : 'Portuguese (Brazil)'},												Language.Code : ('pb', 'pob', 'pob'),								Language.Country : 'br',					Language.Frequency : Language.FrequencyCommon},
				{Language.Original : Language.CodePortuguese,	Language.Name : {Language.NameNative: 'Português (Moçambique)', Language.NameEnglish : 'Portuguese (Mozambique)'},										Language.Code : ('pm', 'pom', 'pom'),	Language.Fallback : 'por', 	Language.Country : 'mz',					Language.Frequency : Language.FrequencyUncommon},

				{Language.Original : Language.CodeSpanish,		Language.Name : {Language.NameNative: 'Español (España)', Language.NameEnglish : 'Spanish (Spain)', Language.NameUniversal : 'Spanish'},				Language.Code : ('es', 'spa', 'spa'), 								Language.Country : 'es',					Language.Frequency : Language.FrequencyCommon},
				{Language.Original : Language.CodeSpanish,		Language.Name : {Language.NameNative: 'Español (Europa)', Language.NameEnglish : 'Spanish (Europe)'},													Language.Code : ('sp', 'spn', 'spn'),	Language.Fallback : 'spa', 	Language.Country : 'es',					Language.Frequency : Language.FrequencyCommon},
				{Language.Original : Language.CodeSpanish,		Language.Name : {Language.NameNative: 'Español (Latina)', Language.NameEnglish : 'Spanish (Latin)'},													Language.Code : ('ea', 'spl', 'spl'),	Language.Fallback : 'spa', 	Language.Country : Language.CountryNone,	Language.Frequency : Language.FrequencyCommon},
				{Language.Original : Language.CodeSpanish,		Language.Name : {Language.NameNative: 'Español (Extremeño)', Language.NameEnglish : 'Spanish (Extremaduran)'},											Language.Code : ('ex', 'ext', 'ext'),	Language.Fallback : 'spa', 	Language.Country : 'es',					Language.Frequency : Language.FrequencyUncommon},
			)

			for data in [Language.Languages, Language.Variations]:
				for i in range(len(data)):
					data[i][Language.Search] = {}
					data[i][Language.Search][Language.Name] = {
						Language.TypePrimary : {data[i][Language.Name][Language.NameEnglish].lower() : True},
						Language.TypeSecondary : {data[i][Language.Name][Language.NameNative].lower() : True},
						Language.TypeTertiary : {name.lower() : True for code, name in data[i][Language.Name].items() if not code == Language.NameEnglish and not code == Language.NameNative},
					}
					data[i][Language.Search][Language.Code] = {
						Language.TypePrimary : {data[i][Language.Code][Language.CodePrimary] : True},
						Language.TypeSecondary : {code : True for code in data[i][Language.Code] if not code == Language.CodePrimary},
					}

			Language.Flags = {
				'af' : True,
				'ar' : True,
				'bn' : True,
				'de' : True,
				'ea' : True,
				'en' : True,
				'es' : True,
				'eu' : True,
				'fa' : True,
				'fr' : True,
				'ko' : True,
				'ms' : True,
				'nl' : True,
				'pt' : True,
				'ro' : True,
				'se' : True,
				'ss' : True,
				'st' : True,
				'ta' : True,
				'tn' : True,
				'ur' : True,
				'zh' : True,
			}

	@classmethod
	def isAutomatic(self, language):
		return language.lower() == Language.Automatic

	@classmethod
	def isAlternative(self, language):
		return language.lower() == Language.Alternative

	@classmethod
	def isUniversal(self, language):
		language = language.lower()
		return language == Language.UniversalCode or language == Language.UniversalName.lower()

	@classmethod
	def settings(self, single = False, raw = False):
		if raw:
			languages = [
				Settings.getString(Language.SettingPrimary),
				Settings.getString(Language.SettingSecondary),
				Settings.getString(Language.SettingTertiary),
			]
			languages = [None if i.lower() == Language.Disabled else self.language(i) for i in languages]
			if single: return languages[0]
			else: return languages
		elif Language.Settings is None:
			languages = []

			language = Settings.getString(Language.SettingPrimary)
			if not language.lower() == Language.Disabled:
				language = self.language(language)
				if language and not language in languages: languages.append(language)

			language = Settings.getString(Language.SettingSecondary)
			if not language.lower() == Language.Disabled:
				language = self.language(language)
				if language and not language in languages: languages.append(language)

			language = Settings.getString(Language.SettingTertiary)
			if not language.lower() == Language.Disabled:
				language = self.language(language)
				if language and not language in languages: languages.append(language)

			if len(languages) == 0: languages.append(self.language(Language.EnglishCode))
			Language.Settings = Tools.listUnique(languages)

		if single: return Language.Settings[0]
		else: return Language.Settings

	@classmethod
	def settingsCode(self, code = CodeDefault, single = False):
		languages = self.settings(single = False)
		languages = [language[Language.Code][code] for language in languages]
		if single: return languages[0]
		else: return languages

	@classmethod
	def settingsName(self, name = NameDefault, single = False):
		languages = self.settings(single = False)
		languages = [language[Language.Name][name] for language in languages]
		if single: return languages[0]
		else: return languages

	@classmethod
	def settingsCountry(self, variation = False, single = False):
		languages = self.settings(single = False)

		countries = []
		for language in languages:
			if language[Language.Code][Language.CodePrimary] == Language.EnglishCode: countries.extend(Language.EnglishCountry)
			else: countries.append(language[Language.Country])

		if variation:
			variations = self.variations()
			languages = [language[Language.Code][Language.CodePrimary] for language in languages]
			for i in range(len(languages)):
				for var in variations:
					if languages[i] == var[Language.Original]:
						countries.insert(i + 1, var[Language.Country])
			countries = Tools.listUnique(countries)

		if single: return countries[0]
		else: return countries

	# default can be set to Alternative. This allows to return another language besides English.
	# Eg: We are working with the English title. If we want titles besides the English one, and the user specified Automatic in the settings, then Automatic is converted to Alternative.
	@classmethod
	def settingsCustom(self, id = None, type = None, default = Automatic, code = CodeDefault, automatic = True):
		if id is None: id = Language.SettingBase + type
		elif id and type: id = id.strip('.') + '.' + type
		setting = Settings.getString(id)

		if self.isAutomatic(setting):
			if automatic:
				if default == Language.TypePrimary:
					setting = Settings.getString(Language.SettingPrimary)
					if setting.lower() == Language.Disabled: return None
				elif default == Language.TypeSecondary:
					setting = Settings.getString(Language.SettingSecondary)
					if setting.lower() == Language.Disabled: return None
				elif default == Language.TypeTertiary:
					setting = Settings.getString(Language.SettingTertiary)
					if setting.lower() == Language.Disabled: return None
				else:
					setting = default
			else:
				setting = None

		if code is None or code is False: return self.language(language = setting)
		else: return self.code(language = setting, code = code)

	@classmethod
	def settingsCustoms(self, id = None, default = Automatic, code = CodeDefault):
		settings = []
		for type in [Language.TypePrimary, Language.TypeSecondary, Language.TypeTertiary]:
			setting = self.settingsCustom(id = id, type = type, default = type, code = code)
			if setting: settings.append(setting)
		return Tools.listUnique(settings)

	@classmethod
	def settingsSelect(self, id = None, type = None, title = None, automatic = None, none = None, set = None, current = None, update = True, result = Name):
		from lib.modules.interface import Translation, Dialog, Directory, Skin, Icon, Format

		if id is None and type: id = Language.SettingBase + type
		if current is None: current = Settings.getString(id)
		languages = self.languages(universal = False)
		languages = Tools.listSort(data = languages, key = lambda i : i[Language.Name][Language.NameDefault])

		if set:
			if Tools.isString(set): set = Language.Sets[set]
			languages = [i for i in languages if any(j in set for j in i[Language.Code])]

		codes = [i[Language.Code][Language.CodePrimary] for i in languages]
		names = [i[Language.Name][Language.NameDefault] for i in languages]
		descriptions = [[i[Language.Code][Language.CodeSecondary].upper(), i[Language.Name][Language.NameNative]] for i in languages]
		countries = [i[Language.Country] for i in languages]
		if automatic:
			codes.insert(0, Language.CodeAutomatic)
			names.insert(0, Language.Automatic.capitalize())
			descriptions.insert(0, [Translation.string(36136)])
			countries.insert(0, Language.CodeAutomatic)
		if none:
			codes.insert(0, Language.CodeNone)
			names.insert(0, Language.Disabled.capitalize())
			descriptions.insert(0, [Translation.string(36137)])
			countries.insert(0, Language.CodeNone)

		if Language.Details:
			directory = Directory()
			supportBold = Skin.supportDialogDetailBold(default = True)
			supportIcon = Skin.supportDialogDetailIcon(default = True)
			items = []
			for i in range(len(names)):
				label = names[i]
				if supportBold: label = Format.fontBold(label)
				label2 = descriptions[i]
				if len(label2) > 1: label2[0] = Format.fontBold(label2[0])
				label2 = Format.iconJoin(label2)
				icon = self.flag(codes[i], quality = Icon.QualityLarge if supportIcon else Icon.QualitySmall)
				items.append(directory.item(label = label, label2 = label2, icon = icon))
			try: current = names.index(current)
			except:
				try: current = codes.index(current)
				except: current = None
			choice = Dialog.select(title = title if title else 33787, items = items, selection = current, details = True)
		else:
			choice = Dialog.select(title = title if title else 33787, items = names, selection = current)
		if choice < 0: return None

		choiceName = names[choice]
		choiceCode = codes[choice]

		if update:
			if id == Language.SettingPrimary and not choiceCode == Language.EnglishCode:
				if not Dialog.option(title = 32356, message = Translation.string(35285) % (choiceName, choiceName), labelConfirm = choiceName, labelDeny = Language.EnglishName):
					choiceName = Language.EnglishName
					choiceCode = Language.EnglishCode

			Settings.set(id, choiceCode if result == Language.Code else choiceName)
			Language.Settings = None # Reset so that new settings are read.

		if result == Language.Name: return choiceName
		elif result == Language.Code: return choiceCode
		else: return choiceValue

	@classmethod
	def settingsSelectPrimary(self, set = None):
		return self.settingsSelect(type = Language.TypePrimary, title = 32356, automatic = False, none = False, set = set)

	@classmethod
	def settingsSelectSecondary(self, set = None):
		return self.settingsSelect(type = Language.TypeSecondary, title = 32357, automatic = False, none = True, set = set)

	@classmethod
	def settingsSelectTertiary(self, set = None):
		return self.settingsSelect(type = Language.TypeTertiary, title = 35036, automatic = False, none = True, set = set)

	@classmethod
	def isUniversal(self, language):
		if language is None: return False
		language = self._process(language)
		return language == Language.UniversalCode or language == Language.UniversalName.lower()

	@classmethod
	def isEnglish(self, language):
		if language is None: return False
		language = self._process(language)
		return language == Language.EnglishCode or language == Language.EnglishName.lower()

	@classmethod
	def languages(self, universal = True, frequency = None, country = None):
		self._prepare()
		if universal: result = Language.Languages
		else: result = Language.Languages[1:]
		if not frequency is None:
			if frequency is True: frequency = [Language.FrequencyCommon, Language.FrequencyOccasional]
			elif frequency is False: frequency = [Language.FrequencyUncommon]
			if Tools.isArray(frequency): result = [i for i in result if i[Language.Frequency] in frequency]
			elif Tools.isInteger(frequency): result = [i for i in result if i[Language.Frequency] >= frequency]
		if not country is None: result = [i for i in result if i[Language.Country] == country]
		return result

	@classmethod
	def codes(self, code = CodeDefault, universal = True, frequency = None, country = None):
		result = self.languages(universal = universal, frequency = frequency, country = country)
		return [i[Language.Code][code] for i in result]

	@classmethod
	def variations(self):
		self._prepare()
		return Language.Variations

	@classmethod
	def universal(self):
		self._prepare()
		return Language.Languages[0]

	@classmethod
	def language(self, language, variation = False, extended = False):
		if language is None: return None

		self._prepare()
		language = self._process(language)
		length = len(language)

		# Automatic or Alternative
		if language == Language.Automatic:
			return self.settings(single = True)
		elif language == Language.Alternative:
			languages = self.settings()
			for i in languages:
				if not i[Language.Code][Language.CodePrimary] == Language.EnglishCode:
					return i
			return languages[0]

		# Code - ISO 639-1
		if length == 2:
			if variation:
				for i in Language.Variations:
					if language in i[Language.Search][Language.Code][Language.TypePrimary]:
						return i
			for i in Language.Languages:
				if language in i[Language.Search][Language.Code][Language.TypePrimary]:
					return i

		# Code - ISO 639-2 or ISO 639-3
		elif length == 3:
			if variation:
				for i in Language.Variations:
					if language in i[Language.Search][Language.Code][Language.TypeSecondary]:
						return i
			for i in Language.Languages:
				if language in i[Language.Search][Language.Code][Language.TypeSecondary]:
					return i

		# Name - Variation
		if variation:
			for i in Language.Variations:
				if language in i[Language.Search][Language.Name][Language.TypePrimary]:
					return i
			for i in Language.Variations:
				if language in i[Language.Search][Language.Name][Language.TypeSecondary]:
					return i
			if extended:
				for i in Language.Variations:
					if language in i[Language.Search][Language.Name][Language.TypeTertiary]:
						return i

		# Name
		for i in Language.Languages:
			if language in i[Language.Search][Language.Name][Language.TypePrimary]:
				return i
		for i in Language.Languages:
			if language in i[Language.Search][Language.Name][Language.TypeSecondary]:
				return i
		if extended:
			for i in Language.Languages:
				if language in i[Language.Search][Language.Name][Language.TypeTertiary]:
					return i

		return None

	@classmethod
	def name(self, language, name = NameDefault, variation = False, extended = False):
		if language == Language.CodeNone: return Language.Disabled.capitalize()
		elif language == Language.CodeAutomatic: return Language.Automatic.capitalize()

		result = self.language(language = language, variation = variation, extended = extended)
		if result: return result[Language.Name][name]
		return None

	@classmethod
	def code(self, language, code = CodeDefault, variation = False, extended = False):
		result = self.language(language = language, variation = variation, extended = extended)
		if result: return result[Language.Code][code]
		return None

	@classmethod
	def ununiversalize(self, languages, english = True):
		for i in range(len(languages)):
			if self.isUniversal(languages[i]):
				del languages[i]
				if english:
					has = False
					for j in range(len(languages)):
						if self.isEnglish(languages[j]):
							has = True
							break
					if not has: languages.append(self.language(Language.EnglishCode))
				break
		return languages

	@classmethod
	def clean(self, languages):
		current = []
		result = []
		for i in languages:
			if i and not i[Language.Name][Language.NameEnglish] in current:
				current.append(i[Language.Name][Language.NameEnglish])
				result.append(i)
		return result

	@classmethod
	def country(self, language, variation = False):
		if language is None: return None
		try: return self.language(language = language, variation = variation)[Language.Country]
		except: return Language.UniversalCountry

	@classmethod
	def countries(self, language, variation = False):
		if language is None: return None
		try:
			countries = []
			language = self.language(language = language, variation = variation)
			if language[Language.Code][Language.CodePrimary] == Language.EnglishCode: countries.extend(Language.EnglishCountry)
			else: countries.append(language[Language.Country])
			if variation:
				variations = self.variations()
				for var in variations:
					if language[Language.Code][Language.CodePrimary] == var[Language.Original]:
						countries.append(var[Language.Country])
				countries = Tools.listUnique(countries)
			return countries
		except: return [Language.UniversalCountry]

	@classmethod
	def flag(self, language, variation = True, quality = None, combined = True, subtitle = False, plain = False):
		from lib.modules.interface import Icon
		if language == Language.CodeNone or language == Language.CodeUniversal:
			code = Language.CodePlain if plain else language
			special = Icon.SpecialCountries
		else:
			if language == Language.CodeAutomatic or language == Language.CodeNone:
				country = code = language
			else:
				language = self.language(language = language, variation = variation)
				code = language[Language.Code][Language.CodePrimary]
				country = language[Language.Country]

			# Use different flag icons for some languages to accomodate OpenSubtitles language variations.
			#	Chinese (Simplified): China country flag.
			#	Chinese (Traditional): Taiwan country flag.
			#	Chinese (Bilingual): Chinese language flag.
			#	Portuguese (Portugal): Portugal country flag.
			#	Portuguese (Brasil): Brazil country flag.
			#	Portuguese (Mozambique): Mozambique country flag.
			#	Spanish (Spain): Spain country flag.
			#	Spanish (Europe): Spain country flag.
			#	Spanish (Latin): Latin-Spanish language flag (Mexico and Argentina).
			#	Spanish (Extremaduran): Spain country flag.
			allow = True
			if subtitle:
				if code in ['zh', 'zt', 'pt', 'es']: allow = False
				if code in ['ze']: code = 'zh'

			if allow and combined and code in Language.Flags:
				special = Icon.SpecialLanguages
			else:
				code = country
				if code == Language.CountryNone: code = Language.CodeUniversal
				special = Icon.SpecialCountries
		return Icon.path(code, special = special, quality = quality)


class Country(object):

	Code				= 'code'
	Name				= 'name'
	Frequency			= 'frequency'
	Language			= 'language'

	Disabled			= 'none'
	Automatic			= 'automatic'

	NamePrimary			= 0
	#NameSecondary		= 1
	NameDefault			= NamePrimary

	CodePrimary			= 0 # ISO Alpha-2
	CodeSecondary		= 1 # ISO Alpha-3
	CodeTertiary		= 2 # FIPS 10-4
	CodeQuaternary		= 3 # ISO Numeric
	CodeDefault			= CodePrimary

	CodeUnitedStates	= 'us'

	FrequencyCommon		= 3		# Big countries that are independent.
	FrequencyOccasional	= 2		# Smaller countries that are still independent.
	FrequencyUncommon	= 1		# Minor territories, islands, principalities, commonwealth, or other states that or not fully independent.
	FrequencyNone		= 0		# Not an official country or not a country anymore.

	LanguagePrimary		= 0
	LanguageSecondary	= 1
	LanguageTertiary	= 2
	LanguageQuaternary	= 3
	LanguageDefault		= LanguagePrimary
	LanguageAll			= None

	UniversalName		= 'Universal'
	UniversalCode		= 'un'
	UniversalLanguage	= 'un'
	UniversalNumber		= -1

	Countries			= (
		{ Name : [UniversalName],									Code : [UniversalCode, UniversalCode, UniversalCode, UniversalNumber], Language : [UniversalLanguage],	Frequency : FrequencyNone },
		{ Name : ['Andorra'],										Code : ['ad', 'and', 'an', 20],		Language : ['ca'],										Frequency : FrequencyOccasional },
		{ Name : ['United Arab Emirates'],							Code : ['ae', 'are', 'ae', 784],	Language : ['ar', 'fa', 'en', 'hi', 'ur'],				Frequency : FrequencyCommon },
		{ Name : ['Afghanistan'],									Code : ['af', 'afg', 'af', 4],		Language : ['fa', 'ps', 'uz', 'tk'],					Frequency : FrequencyCommon },
		{ Name : ['Antigua and Barbuda'],							Code : ['ag', 'atg', 'ac', 28],		Language : ['en'],										Frequency : FrequencyOccasional },
		{ Name : ['Anguilla'],										Code : ['ai', 'aia', 'av', 660],	Language : ['en'],										Frequency : FrequencyUncommon },
		{ Name : ['Albania'],										Code : ['al', 'alb', 'al', 8],		Language : ['sq', 'el'],								Frequency : FrequencyCommon },
		{ Name : ['Armenia'],										Code : ['am', 'arm', 'am', 51],		Language : ['hy'],										Frequency : FrequencyCommon },
		{ Name : ['Angola'],										Code : ['ao', 'ago', 'ao', 24],		Language : ['pt'],										Frequency : FrequencyCommon },
		{ Name : ['Argentina'],										Code : ['ar', 'arg', 'ar', 32],		Language : ['es', 'en', 'it', 'de', 'fr', 'gn'],		Frequency : FrequencyCommon },
		{ Name : ['American Samoa'],								Code : ['as', 'asm', 'aq', 16],		Language : ['en', 'sm', 'to'],							Frequency : FrequencyUncommon },
		{ Name : ['Austria'],										Code : ['at', 'aut', 'au', 40],		Language : ['de', 'hr', 'hu', 'sl'],					Frequency : FrequencyCommon },
		{ Name : ['Australia'],										Code : ['au', 'aus', 'as', 36],		Language : ['en'],										Frequency : FrequencyCommon },
		{ Name : ['Aruba'],											Code : ['aw', 'abw', 'aa', 533],	Language : ['nl', 'es', 'en'],							Frequency : FrequencyUncommon },
		{ Name : ['Aland Islands'],									Code : ['ax', 'ala', None, 248],	Language : ['sv'],										Frequency : FrequencyUncommon },
		{ Name : ['Azerbaijan'],									Code : ['az', 'aze', 'aj', 31],		Language : ['az', 'ru', 'hy'],							Frequency : FrequencyCommon },
		{ Name : ['Bosnia and Herzegovina'],						Code : ['ba', 'bih', 'bk', 70],		Language : ['bs', 'hr', 'sr'],							Frequency : FrequencyCommon },
		{ Name : ['Barbados'],										Code : ['bb', 'brb', 'bb', 52],		Language : ['en'],										Frequency : FrequencyOccasional },
		{ Name : ['Bangladesh'],									Code : ['bd', 'bgd', 'bg', 50],		Language : ['bn', 'en'],								Frequency : FrequencyCommon },
		{ Name : ['Belgium'],										Code : ['be', 'bel', 'be', 56],		Language : ['nl', 'fr', 'de'],							Frequency : FrequencyCommon },
		{ Name : ['Burkina Faso'],									Code : ['bf', 'bfa', 'uv', 854],	Language : ['fr'],										Frequency : FrequencyCommon },
		{ Name : ['Bulgaria'],										Code : ['bg', 'bgr', 'bu', 100],	Language : ['bg', 'tr'],								Frequency : FrequencyCommon },
		{ Name : ['Bahrain'],										Code : ['bh', 'bhr', 'ba', 48],		Language : ['ar', 'en', 'fa', 'ur'],					Frequency : FrequencyOccasional },
		{ Name : ['Burundi'],										Code : ['bi', 'bdi', 'by', 108],	Language : ['fr', 'rn'],								Frequency : FrequencyCommon },
		{ Name : ['Benin'],											Code : ['bj', 'ben', 'bn', 204],	Language : ['fr'],										Frequency : FrequencyCommon },
		{ Name : ['Saint Barthelemy'],								Code : ['bl', 'blm', 'tb', 652],	Language : ['fr'],										Frequency : FrequencyUncommon },
		{ Name : ['Bermuda'],										Code : ['bm', 'bmu', 'bd', 60],		Language : ['en', 'pt'],								Frequency : FrequencyUncommon },
		{ Name : ['Brunei'],										Code : ['bn', 'brn', 'bx', 96],		Language : ['ms', 'en'],								Frequency : FrequencyOccasional },
		{ Name : ['Bolivia'],										Code : ['bo', 'bol', 'bl', 68],		Language : ['es', 'qu', 'ay'],							Frequency : FrequencyCommon },
		{ Name : ['Caribbean Netherlands'],							Code : ['bq', 'bes', None, 535],	Language : ['nl', 'en'],								Frequency : FrequencyUncommon },
		{ Name : ['Brazil'],										Code : ['br', 'bra', 'br', 76],		Language : ['pt', 'es', 'en', 'fr'],					Frequency : FrequencyCommon },
		{ Name : ['Bahamas'],										Code : ['bs', 'bhs', 'bf', 44],		Language : ['en'],										Frequency : FrequencyCommon },
		{ Name : ['Bhutan'],										Code : ['bt', 'btn', 'bt', 64],		Language : ['dz'],										Frequency : FrequencyOccasional },
		{ Name : ['Bouvet Island'],									Code : ['bv', 'bvt', 'bv', 74],		Language : [],											Frequency : FrequencyUncommon },
		{ Name : ['Botswana'],										Code : ['bw', 'bwa', 'bc', 72],		Language : ['en', 'tn'],								Frequency : FrequencyCommon },
		{ Name : ['Belarus'],										Code : ['by', 'blr', 'bo', 112],	Language : ['be', 'ru'],								Frequency : FrequencyCommon },
		{ Name : ['Belize'],										Code : ['bz', 'blz', 'bh', 84],		Language : ['en', 'es'],								Frequency : FrequencyOccasional },
		{ Name : ['Canada'],										Code : ['ca', 'can', 'ca', 124],	Language : ['en', 'fr', 'iu'],							Frequency : FrequencyCommon },
		{ Name : ['Cocos Islands'],									Code : ['cc', 'cck', 'ck', 166],	Language : ['ms', 'en'],								Frequency : FrequencyUncommon },
		{ Name : ['Democratic Republic of the Congo'],				Code : ['cd', 'cod', 'cg', 180],	Language : ['fr', 'ln', 'kg'],							Frequency : FrequencyCommon },
		{ Name : ['Central African Republic'],						Code : ['cf', 'caf', 'ct', 140],	Language : ['fr', 'sg', 'ln', 'kg'],					Frequency : FrequencyCommon },
		{ Name : ['Republic of the Congo'],							Code : ['cg', 'cog', 'cf', 178],	Language : ['fr', 'kg', 'ln'],							Frequency : FrequencyCommon },
		{ Name : ['Switzerland'],									Code : ['ch', 'che', 'sz', 756],	Language : ['de', 'fr', 'it', 'rm'],					Frequency : FrequencyCommon },
		{ Name : ['Ivory Coast'],									Code : ['ci', 'civ', 'iv', 384],	Language : ['fr'],										Frequency : FrequencyCommon },
		{ Name : ['Cook Islands'],									Code : ['ck', 'cok', 'cw', 184],	Language : ['en', 'mi'],								Frequency : FrequencyUncommon },
		{ Name : ['Chile'],											Code : ['cl', 'chl', 'ci', 152],	Language : ['es'],										Frequency : FrequencyCommon },
		{ Name : ['Cameroon'],										Code : ['cm', 'cmr', 'cm', 120],	Language : ['en', 'fr'],								Frequency : FrequencyCommon },
		{ Name : ['China'],											Code : ['cn', 'chn', 'ch', 156],	Language : ['zh', 'ug', 'za'],							Frequency : FrequencyCommon },
		{ Name : ['Colombia'],										Code : ['co', 'col', 'co', 170],	Language : ['es'],										Frequency : FrequencyCommon },
		{ Name : ['Costa Rica'],									Code : ['cr', 'cri', 'cs', 188],	Language : ['es', 'en'],								Frequency : FrequencyCommon },
		{ Name : ['Cuba'],											Code : ['cu', 'cub', 'cu', 192],	Language : ['es'],										Frequency : FrequencyCommon },
		{ Name : ['Cape Verde'],									Code : ['cv', 'cpv', 'cv', 132],	Language : ['pt'],										Frequency : FrequencyOccasional },
		{ Name : ['Curacao'],										Code : ['cw', 'cuw', 'uc', 531],	Language : ['nl'],										Frequency : FrequencyUncommon },
		{ Name : ['Christmas Island'],								Code : ['cx', 'cxr', 'kt', 162],	Language : ['en', 'zh', 'ms'],							Frequency : FrequencyUncommon },
		{ Name : ['Cyprus'],										Code : ['cy', 'cyp', 'cy', 196],	Language : ['el', 'tr', 'en'],							Frequency : FrequencyCommon },
		{ Name : ['Czech Republic'],								Code : ['cz', 'cze', 'ez', 203],	Language : ['cs', 'sk'],								Frequency : FrequencyCommon },
		{ Name : ['Germany'],										Code : ['de', 'deu', 'gm', 276],	Language : ['de'],										Frequency : FrequencyCommon },
		{ Name : ['Djibouti'],										Code : ['dj', 'dji', 'dj', 262],	Language : ['fr', 'ar', 'so', 'aa'],					Frequency : FrequencyCommon },
		{ Name : ['Denmark'],										Code : ['dk', 'dnk', 'da', 208],	Language : ['da', 'en', 'fo', 'de'],					Frequency : FrequencyCommon },
		{ Name : ['Dominica'],										Code : ['dm', 'dma', 'do', 212],	Language : ['en'],										Frequency : FrequencyOccasional },
		{ Name : ['Dominican Republic'],							Code : ['do', 'dom', 'dr', 214],	Language : ['es'],										Frequency : FrequencyCommon },
		{ Name : ['Algeria'],										Code : ['dz', 'dza', 'ag', 12],		Language : ['ar'],										Frequency : FrequencyCommon },
		{ Name : ['Ecuador'],										Code : ['ec', 'ecu', 'ec', 218],	Language : ['es'],										Frequency : FrequencyCommon },
		{ Name : ['Estonia'],										Code : ['ee', 'est', 'en', 233],	Language : ['et', 'ru'],								Frequency : FrequencyCommon },
		{ Name : ['Egypt'],											Code : ['eg', 'egy', 'eg', 818],	Language : ['ar', 'en', 'fr'],							Frequency : FrequencyCommon },
		{ Name : ['Western Sahara'],								Code : ['eh', 'esh', 'wi', 732],	Language : ['ar'],										Frequency : FrequencyUncommon },
		{ Name : ['Eritrea'],										Code : ['er', 'eri', 'er', 232],	Language : ['aa', 'ar', 'ti'],							Frequency : FrequencyCommon },
		{ Name : ['Spain'],											Code : ['es', 'esp', 'sp', 724],	Language : ['es', 'ca', 'gl', 'eu', 'oc'],				Frequency : FrequencyCommon },
		{ Name : ['Ethiopia'],										Code : ['et', 'eth', 'et', 231],	Language : ['am', 'en', 'om', 'ti', 'so'],				Frequency : FrequencyCommon },
		{ Name : ['Finland'],										Code : ['fi', 'fin', 'fi', 246],	Language : ['fi', 'sv'],								Frequency : FrequencyCommon },
		{ Name : ['Fiji'],											Code : ['fj', 'fji', 'fj', 242],	Language : ['en', 'fj'],								Frequency : FrequencyOccasional },
		{ Name : ['Falkland Islands'],								Code : ['fk', 'flk', 'fk', 238],	Language : ['en'],										Frequency : FrequencyUncommon },
		{ Name : ['Faroe Islands'],									Code : ['fo', 'fro', 'fo', 234],	Language : ['fo', 'da'],								Frequency : FrequencyUncommon },
		{ Name : ['France'],										Code : ['fr', 'fra', 'fr', 250],	Language : ['fr', 'br', 'co', 'ca', 'eu', 'oc'],		Frequency : FrequencyCommon },
		{ Name : ['Gabon'],											Code : ['ga', 'gab', 'gb', 266],	Language : ['fr'],										Frequency : FrequencyCommon },
		{ Name : ['United Kingdom'],								Code : ['gb', 'gbr', 'uk', 826],	Language : ['en', 'cy', 'gd'],							Frequency : FrequencyCommon },
		{ Name : ['Grenada'],										Code : ['gd', 'grd', 'gj', 308],	Language : ['en'],										Frequency : FrequencyOccasional },
		{ Name : ['Georgia'],										Code : ['ge', 'geo', 'gg', 268],	Language : ['ka', 'ru', 'hy', 'az'],					Frequency : FrequencyCommon },
		{ Name : ['French Guiana'],									Code : ['gf', 'guf', 'fg', 254],	Language : ['fr'],										Frequency : FrequencyUncommon },
		{ Name : ['Guernsey'],										Code : ['gg', 'ggy', 'gk', 831],	Language : ['en', 'fr'],								Frequency : FrequencyUncommon },
		{ Name : ['Ghana'],											Code : ['gh', 'gha', 'gh', 288],	Language : ['en', 'ak', 'ee', 'tw'],					Frequency : FrequencyCommon },
		{ Name : ['Gibraltar'],										Code : ['gi', 'gib', 'gi', 292],	Language : ['en', 'es', 'it', 'pt'],					Frequency : FrequencyUncommon },
		{ Name : ['Greenland'],										Code : ['gl', 'grl', 'gl', 304],	Language : ['kl', 'da', 'en'],							Frequency : FrequencyCommon },
		{ Name : ['Gambia'],										Code : ['gm', 'gmb', 'ga', 270],	Language : ['en', 'wo', 'ff'],							Frequency : FrequencyCommon },
		{ Name : ['Guinea'],										Code : ['gn', 'gin', 'gv', 324],	Language : ['fr'],										Frequency : FrequencyCommon },
		{ Name : ['Guadeloupe'],									Code : ['gp', 'glp', 'gp', 312],	Language : ['fr'],										Frequency : FrequencyUncommon },
		{ Name : ['Equatorial Guinea'],								Code : ['gq', 'gnq', 'ek', 226],	Language : ['es', 'fr'],								Frequency : FrequencyCommon },
		{ Name : ['Greece'],										Code : ['gr', 'grc', 'gr', 300],	Language : ['el', 'en', 'fr'],							Frequency : FrequencyCommon },
		{ Name : ['South Georgia and the South Sandwich Islands'],	Code : ['gs', 'sgs', 'sx', 239],	Language : ['en'],										Frequency : FrequencyUncommon },
		{ Name : ['Guatemala'],										Code : ['gt', 'gtm', 'gt', 320],	Language : ['es'],										Frequency : FrequencyCommon },
		{ Name : ['Guam'],											Code : ['gu', 'gum', 'gq', 316],	Language : ['en', 'ch'],								Frequency : FrequencyUncommon },
		{ Name : ['Guinea-Bissau'],									Code : ['gw', 'gnb', 'pu', 624],	Language : ['pt'],										Frequency : FrequencyOccasional },
		{ Name : ['Guyana'],										Code : ['gy', 'guy', 'gy', 328],	Language : ['en'],										Frequency : FrequencyOccasional },
		{ Name : ['Hong Kong'],										Code : ['hk', 'hkg', 'hk', 344],	Language : ['zh', 'zh', 'en'],							Frequency : FrequencyUncommon },
		{ Name : ['Heard Island and McDonald Islands'],				Code : ['hm', 'hmd', 'hm', 334],	Language : [],											Frequency : FrequencyUncommon },
		{ Name : ['Honduras'],										Code : ['hn', 'hnd', 'ho', 340],	Language : ['es'],										Frequency : FrequencyCommon },
		{ Name : ['Croatia'],										Code : ['hr', 'hrv', 'hr', 191],	Language : ['hr', 'sr'],								Frequency : FrequencyCommon },
		{ Name : ['Haiti'],											Code : ['ht', 'hti', 'ha', 332],	Language : ['ht', 'fr'],								Frequency : FrequencyCommon },
		{ Name : ['Hungary'],										Code : ['hu', 'hun', 'hu', 348],	Language : ['hu'],										Frequency : FrequencyCommon },
		{ Name : ['Indonesia'],										Code : ['id', 'idn', 'id', 360],	Language : ['id', 'en', 'nl', 'jv'],					Frequency : FrequencyCommon },
		{ Name : ['Ireland'],										Code : ['ie', 'irl', 'ei', 372],	Language : ['en', 'ga'],								Frequency : FrequencyCommon },
		{ Name : ['Israel'],										Code : ['il', 'isr', 'is', 376],	Language : ['he', 'ar', 'en'],							Frequency : FrequencyCommon },
		{ Name : ['Isle of Man'],									Code : ['im', 'imn', 'im', 833],	Language : ['en', 'gv'],								Frequency : FrequencyUncommon },
		{ Name : ['India'],											Code : ['in', 'ind', 'in', 356],	Language : ['en', 'hi', 'bn', 'te', 'mr', 'ta', 'ur', 'gu', 'kn', 'ml', 'or', 'pa', 'as', 'bh', 'ks', 'ne', 'sd', 'sa'],	Frequency : FrequencyCommon },
		{ Name : ['British Indian Ocean Territory'],				Code : ['io', 'iot', 'io', 86],		Language : ['en'],										Frequency : FrequencyUncommon },
		{ Name : ['Iraq'],											Code : ['iq', 'irq', 'iz', 368],	Language : ['ar', 'ku', 'hy'],							Frequency : FrequencyCommon },
		{ Name : ['Iran'],											Code : ['ir', 'irn', 'ir', 364],	Language : ['fa', 'ku'],								Frequency : FrequencyCommon },
		{ Name : ['Iceland'],										Code : ['is', 'isl', 'ic', 352],	Language : ['is', 'en', 'de', 'da', 'sv', 'no'],		Frequency : FrequencyCommon },
		{ Name : ['Italy'],											Code : ['it', 'ita', 'it', 380],	Language : ['it', 'de', 'fr', 'sc', 'ca', 'co', 'sl'],	Frequency : FrequencyCommon },
		{ Name : ['Jersey'],										Code : ['je', 'jey', 'je', 832],	Language : ['en', 'pt'],								Frequency : FrequencyUncommon },
		{ Name : ['Jamaica'],										Code : ['jm', 'jam', 'jm', 388],	Language : ['en'],										Frequency : FrequencyCommon },
		{ Name : ['Jordan'],										Code : ['jo', 'jor', 'jo', 400],	Language : ['ar', 'en'],								Frequency : FrequencyCommon },
		{ Name : ['Japan'],											Code : ['jp', 'jpn', 'ja', 392],	Language : ['ja'],										Frequency : FrequencyCommon },
		{ Name : ['Kenya'],											Code : ['ke', 'ken', 'ke', 404],	Language : ['en', 'sw'],								Frequency : FrequencyCommon },
		{ Name : ['Kyrgyzstan'],									Code : ['kg', 'kgz', 'kg', 417],	Language : ['ky', 'uz', 'ru'],							Frequency : FrequencyCommon },
		{ Name : ['Cambodia'],										Code : ['kh', 'khm', 'cb', 116],	Language : ['km', 'fr', 'en'],							Frequency : FrequencyCommon },
		{ Name : ['Kiribati'],										Code : ['ki', 'kir', 'kr', 296],	Language : ['en'],										Frequency : FrequencyOccasional },
		{ Name : ['Comoros'],										Code : ['km', 'com', 'cn', 174],	Language : ['ar', 'fr'],								Frequency : FrequencyOccasional },
		{ Name : ['Saint Kitts and Nevis'],							Code : ['kn', 'kna', 'sc', 659],	Language : ['en'],										Frequency : FrequencyOccasional },
		{ Name : ['North Korea'],									Code : ['kp', 'prk', 'kn', 408],	Language : ['ko'],										Frequency : FrequencyCommon },
		{ Name : ['South Korea'],									Code : ['kr', 'kor', 'ks', 410],	Language : ['ko', 'en'],								Frequency : FrequencyCommon },
		{ Name : ['Kosovo'],										Code : ['xk', 'xkx', 'kv', 0],		Language : ['sq', 'sr'],								Frequency : FrequencyOccasional },
		{ Name : ['Kuwait'],										Code : ['kw', 'kwt', 'ku', 414],	Language : ['ar', 'en'],								Frequency : FrequencyCommon },
		{ Name : ['Cayman Islands'],								Code : ['ky', 'cym', 'cj', 136],	Language : ['en'],										Frequency : FrequencyUncommon },
		{ Name : ['Kazakhstan'],									Code : ['kz', 'kaz', 'kz', 398],	Language : ['kk', 'ru'],								Frequency : FrequencyCommon },
		{ Name : ['Laos'],											Code : ['la', 'lao', 'la', 418],	Language : ['lo', 'fr', 'en'],							Frequency : FrequencyCommon },
		{ Name : ['Lebanon'],										Code : ['lb', 'lbn', 'le', 422],	Language : ['ar', 'fr', 'en', 'hy'],					Frequency : FrequencyCommon },
		{ Name : ['Saint Lucia'],									Code : ['lc', 'lca', 'st', 662],	Language : ['en'],										Frequency : FrequencyOccasional },
		{ Name : ['Liechtenstein'],									Code : ['li', 'lie', 'ls', 438],	Language : ['de'],										Frequency : FrequencyOccasional },
		{ Name : ['Sri Lanka'],										Code : ['lk', 'lka', 'ce', 144],	Language : ['si', 'ta', 'en'],							Frequency : FrequencyCommon },
		{ Name : ['Liberia'],										Code : ['lr', 'lbr', 'li', 430],	Language : ['en'],										Frequency : FrequencyCommon },
		{ Name : ['Lesotho'],										Code : ['ls', 'lso', 'lt', 426],	Language : ['en', 'st', 'zu', 'xh'],					Frequency : FrequencyCommon },
		{ Name : ['Lithuania'],										Code : ['lt', 'ltu', 'lh', 440],	Language : ['lt', 'ru', 'pl'],							Frequency : FrequencyCommon },
		{ Name : ['Luxembourg'],									Code : ['lu', 'lux', 'lu', 442],	Language : ['lb', 'de', 'fr'],							Frequency : FrequencyCommon },
		{ Name : ['Latvia'],										Code : ['lv', 'lva', 'lg', 428],	Language : ['lv', 'ru', 'lt'],							Frequency : FrequencyCommon },
		{ Name : ['Libya'],											Code : ['ly', 'lby', 'ly', 434],	Language : ['ar', 'it', 'en'],							Frequency : FrequencyCommon },
		{ Name : ['Morocco'],										Code : ['ma', 'mar', 'mo', 504],	Language : ['ar', 'fr'],								Frequency : FrequencyCommon },
		{ Name : ['Monaco'],										Code : ['mc', 'mco', 'mn', 492],	Language : ['fr', 'en', 'it'],							Frequency : FrequencyOccasional },
		{ Name : ['Moldova'],										Code : ['md', 'mda', 'md', 498],	Language : ['ro', 'ru', 'tr'],							Frequency : FrequencyCommon },
		{ Name : ['Montenegro'],									Code : ['me', 'mne', 'mj', 499],	Language : ['sr', 'hu', 'bs', 'sq', 'hr'],				Frequency : FrequencyCommon },
		{ Name : ['Saint Martin'],									Code : ['mf', 'maf', 'rn', 663],	Language : ['fr'],										Frequency : FrequencyUncommon },
		{ Name : ['Madagascar'],									Code : ['mg', 'mdg', 'ma', 450],	Language : ['fr', 'mg'],								Frequency : FrequencyCommon },
		{ Name : ['Marshall Islands'],								Code : ['mh', 'mhl', 'rm', 584],	Language : ['mh', 'en'],								Frequency : FrequencyOccasional },
		{ Name : ['Macedonia'],										Code : ['mk', 'mkd', 'mk', 807],	Language : ['mk', 'sq', 'tr', 'sr'],					Frequency : FrequencyCommon },
		{ Name : ['Mali'],											Code : ['ml', 'mli', 'ml', 466],	Language : ['fr', 'bm'],								Frequency : FrequencyCommon },
		{ Name : ['Myanmar'],										Code : ['mm', 'mmr', 'bm', 104],	Language : ['my'],										Frequency : FrequencyCommon },
		{ Name : ['Mongolia'],										Code : ['mn', 'mng', 'mg', 496],	Language : ['mn', 'ru'],								Frequency : FrequencyCommon },
		{ Name : ['Macao'],											Code : ['mo', 'mac', 'mc', 446],	Language : ['zh', 'zh', 'pt'],							Frequency : FrequencyUncommon },
		{ Name : ['Northern Mariana Islands'],						Code : ['mp', 'mnp', 'cq', 580],	Language : ['tl', 'zh', 'ch', 'en'],					Frequency : FrequencyUncommon },
		{ Name : ['Martinique'],									Code : ['mq', 'mtq', 'mb', 474],	Language : ['fr'],										Frequency : FrequencyUncommon },
		{ Name : ['Mauritania'],									Code : ['mr', 'mrt', 'mr', 478],	Language : ['ar', 'fr', 'wo'],							Frequency : FrequencyCommon },
		{ Name : ['Montserrat'],									Code : ['ms', 'msr', 'mh', 500],	Language : ['en'],										Frequency : FrequencyUncommon },
		{ Name : ['Malta'],											Code : ['mt', 'mlt', 'mt', 470],	Language : ['mt', 'en'],								Frequency : FrequencyCommon },
		{ Name : ['Mauritius'],										Code : ['mu', 'mus', 'mp', 480],	Language : ['en', 'fr'],								Frequency : FrequencyOccasional },
		{ Name : ['Maldives'],										Code : ['mv', 'mdv', 'mv', 462],	Language : ['dv', 'en'],								Frequency : FrequencyOccasional },
		{ Name : ['Malawi'],										Code : ['mw', 'mwi', 'mi', 454],	Language : ['ny'],										Frequency : FrequencyCommon },
		{ Name : ['Mexico'],										Code : ['mx', 'mex', 'mx', 484],	Language : ['es'],										Frequency : FrequencyCommon },
		{ Name : ['Malaysia'],										Code : ['my', 'mys', 'my', 458],	Language : ['ms', 'en', 'zh', 'ta', 'te', 'ml', 'pa', 'th'],	Frequency : FrequencyCommon },
		{ Name : ['Micronesia'],									Code : ['fm', 'fsm', 'fm', 583],	Language : ['en'],										Frequency : FrequencyOccasional },
		{ Name : ['Mozambique'],									Code : ['mz', 'moz', 'mz', 508],	Language : ['pt'],										Frequency : FrequencyCommon },
		{ Name : ['Namibia'],										Code : ['na', 'nam', 'wa', 516],	Language : ['en', 'af', 'de', 'hz'],					Frequency : FrequencyCommon },
		{ Name : ['New Caledonia'],									Code : ['nc', 'ncl', 'nc', 540],	Language : ['fr'],										Frequency : FrequencyUncommon },
		{ Name : ['Niger'],											Code : ['ne', 'ner', 'ng', 562],	Language : ['fr', 'ha', 'kr'],							Frequency : FrequencyCommon },
		{ Name : ['Norfolk Island'],								Code : ['nf', 'nfk', 'nf', 574],	Language : ['en'],										Frequency : FrequencyUncommon },
		{ Name : ['Nigeria'],										Code : ['ng', 'nga', 'ni', 566],	Language : ['en', 'ha', 'yo', 'ig', 'ff'],				Frequency : FrequencyCommon },
		{ Name : ['Nicaragua'],										Code : ['ni', 'nic', 'nu', 558],	Language : ['es', 'en'],								Frequency : FrequencyCommon },
		{ Name : ['Netherlands'],									Code : ['nl', 'nld', 'nl', 528],	Language : ['nl', 'fy'],								Frequency : FrequencyCommon },
		{ Name : ['Norway'],										Code : ['no', 'nor', 'no', 578],	Language : ['no', 'nb', 'nn', 'se', 'fi'],				Frequency : FrequencyCommon },
		{ Name : ['Nepal'],											Code : ['np', 'npl', 'np', 524],	Language : ['ne', 'en'],								Frequency : FrequencyCommon },
		{ Name : ['Nauru'],											Code : ['nr', 'nru', 'nr', 520],	Language : ['na', 'en'],								Frequency : FrequencyOccasional },
		{ Name : ['Niue'],											Code : ['nu', 'niu', 'ne', 570],	Language : ['en'],										Frequency : FrequencyUncommon },
		{ Name : ['New Zealand'],									Code : ['nz', 'nzl', 'nz', 554],	Language : ['en', 'mi'],								Frequency : FrequencyCommon },
		{ Name : ['Oman'],											Code : ['om', 'omn', 'mu', 512],	Language : ['ar', 'en', 'ur'],							Frequency : FrequencyCommon },
		{ Name : ['Panama'],										Code : ['pa', 'pan', 'pm', 591],	Language : ['es', 'en'],								Frequency : FrequencyCommon },
		{ Name : ['Peru'],											Code : ['pe', 'per', 'pe', 604],	Language : ['es', 'qu', 'ay'],							Frequency : FrequencyCommon },
		{ Name : ['French Polynesia'],								Code : ['pf', 'pyf', 'fp', 258],	Language : ['fr', 'ty'],								Frequency : FrequencyUncommon },
		{ Name : ['Papua New Guinea'],								Code : ['pg', 'png', 'pp', 598],	Language : ['en', 'ho'],								Frequency : FrequencyOccasional },
		{ Name : ['Philippines'],									Code : ['ph', 'phl', 'rp', 608],	Language : ['tl', 'en'],								Frequency : FrequencyCommon },
		{ Name : ['Pakistan'],										Code : ['pk', 'pak', 'pk', 586],	Language : ['ur', 'en', 'pa', 'sd', 'ps'],				Frequency : FrequencyCommon },
		{ Name : ['Poland'],										Code : ['pl', 'pol', 'pl', 616],	Language : ['pl'],										Frequency : FrequencyCommon },
		{ Name : ['Saint Pierre and Miquelon'],						Code : ['pm', 'spm', 'sb', 666],	Language : ['fr'],										Frequency : FrequencyUncommon },
		{ Name : ['Pitcairn'],										Code : ['pn', 'pcn', 'pc', 612],	Language : ['en'],										Frequency : FrequencyUncommon },
		{ Name : ['Puerto Rico'],									Code : ['pr', 'pri', 'rq', 630],	Language : ['en', 'es'],								Frequency : FrequencyUncommon },
		{ Name : ['Portugal'],										Code : ['pt', 'prt', 'po', 620],	Language : ['pt'],										Frequency : FrequencyCommon },
		{ Name : ['Palau'],											Code : ['pw', 'plw', 'ps', 585],	Language : ['en', 'ja', 'zh'],							Frequency : FrequencyOccasional },
		{ Name : ['Paraguay'],										Code : ['py', 'pry', 'pa', 600],	Language : ['es', 'gn'],								Frequency : FrequencyCommon },
		{ Name : ['Qatar'],											Code : ['qa', 'qat', 'qa', 634],	Language : ['ar', 'es'],								Frequency : FrequencyCommon },
		{ Name : ['Reunion'],										Code : ['re', 'reu', 're', 638],	Language : ['fr'],										Frequency : FrequencyUncommon },
		{ Name : ['Romania'],										Code : ['ro', 'rou', 'ro', 642],	Language : ['ro', 'hu'],								Frequency : FrequencyCommon },
		{ Name : ['Serbia'],										Code : ['rs', 'srb', 'ri', 688],	Language : ['sr', 'hu', 'bs'],							Frequency : FrequencyCommon },
		{ Name : ['Russia'],										Code : ['ru', 'rus', 'rs', 643],	Language : ['ru', 'tt', 'kv', 'ce', 'cv', 'ba'],		Frequency : FrequencyCommon },
		{ Name : ['Rwanda'],										Code : ['rw', 'rwa', 'rw', 646],	Language : ['rw', 'en', 'fr', 'sw'],					Frequency : FrequencyCommon },
		{ Name : ['Saudi Arabia'],									Code : ['sa', 'sau', 'sa', 682],	Language : ['ar'],										Frequency : FrequencyCommon },
		{ Name : ['Solomon Islands'],								Code : ['sb', 'slb', 'bp', 90],		Language : ['en'],										Frequency : FrequencyOccasional },
		{ Name : ['Seychelles'],									Code : ['sc', 'syc', 'se', 690],	Language : ['en', 'fr'],								Frequency : FrequencyOccasional },
		{ Name : ['Sudan'],											Code : ['sd', 'sdn', 'su', 729],	Language : ['ar', 'en'],								Frequency : FrequencyCommon },
		{ Name : ['South Sudan'],									Code : ['ss', 'ssd', 'od', 728],	Language : ['en'],										Frequency : FrequencyCommon },
		{ Name : ['Sweden'],										Code : ['se', 'swe', 'sw', 752],	Language : ['sv', 'se', 'fi'],							Frequency : FrequencyCommon },
		{ Name : ['Singapore'],										Code : ['sg', 'sgp', 'sn', 702],	Language : ['en', 'ms', 'ta', 'zh'],					Frequency : FrequencyOccasional },
		{ Name : ['Saint Helena'],									Code : ['sh', 'shn', 'sh', 654],	Language : ['en'],										Frequency : FrequencyUncommon },
		{ Name : ['Slovenia'],										Code : ['si', 'svn', 'si', 705],	Language : ['sl', 'sh'],								Frequency : FrequencyCommon },
		{ Name : ['Svalbard and Jan Mayen'],						Code : ['sj', 'sjm', 'sv', 744],	Language : ['no', 'ru'],								Frequency : FrequencyUncommon },
		{ Name : ['Slovakia'],										Code : ['sk', 'svk', 'lo', 703],	Language : ['sk', 'hu'],								Frequency : FrequencyCommon },
		{ Name : ['Sierra Leone'],									Code : ['sl', 'sle', 'sl', 694],	Language : ['en'],										Frequency : FrequencyCommon },
		{ Name : ['San Marino'],									Code : ['sm', 'smr', 'sm', 674],	Language : ['it'],										Frequency : FrequencyOccasional },
		{ Name : ['Senegal'],										Code : ['sn', 'sen', 'sg', 686],	Language : ['fr', 'wo'],								Frequency : FrequencyCommon },
		{ Name : ['Somalia'],										Code : ['so', 'som', 'so', 706],	Language : ['so', 'ar', 'it', 'en'],					Frequency : FrequencyCommon },
		{ Name : ['Suriname'],										Code : ['sr', 'sur', 'ns', 740],	Language : ['nl', 'en', 'jv'],							Frequency : FrequencyOccasional },
		{ Name : ['Sao Tome and Principe'],							Code : ['st', 'stp', 'tp', 678],	Language : ['pt'],										Frequency : FrequencyOccasional },
		{ Name : ['El Salvador'],									Code : ['sv', 'slv', 'es', 222],	Language : ['es'],										Frequency : FrequencyCommon },
		{ Name : ['Sint Maarten'],									Code : ['sx', 'sxm', 'nn', 534],	Language : ['nl', 'en'],								Frequency : FrequencyUncommon },
		{ Name : ['Syria'],											Code : ['sy', 'syr', 'sy', 760],	Language : ['ar', 'ku', 'hy', 'fr', 'en'],				Frequency : FrequencyCommon },
		{ Name : ['Eswatini'],										Code : ['sz', 'swz', 'wz', 748],	Language : ['en', 'ss'],								Frequency : FrequencyCommon },
		{ Name : ['Turks and Caicos Islands'],						Code : ['tc', 'tca', 'tk', 796],	Language : ['en'],										Frequency : FrequencyUncommon },
		{ Name : ['Chad'],											Code : ['td', 'tcd', 'cd', 148],	Language : ['fr', 'ar'],								Frequency : FrequencyCommon },
		{ Name : ['French Southern Territories'],					Code : ['tf', 'atf', 'fs', 260],	Language : ['fr'],										Frequency : FrequencyUncommon },
		{ Name : ['Togo'],											Code : ['tg', 'tgo', 'to', 768],	Language : ['fr', 'ee', 'ha'],							Frequency : FrequencyCommon },
		{ Name : ['Thailand'],										Code : ['th', 'tha', 'th', 764],	Language : ['th', 'en'],								Frequency : FrequencyCommon },
		{ Name : ['Tajikistan'],									Code : ['tj', 'tjk', 'ti', 762],	Language : ['tg', 'ru'],								Frequency : FrequencyCommon },
		{ Name : ['Tokelau'],										Code : ['tk', 'tkl', 'tl', 772],	Language : ['en'],										Frequency : FrequencyUncommon },
		{ Name : ['East Timor'],									Code : ['tl', 'tls', 'tt', 626],	Language : ['pt', 'id', 'en'],							Frequency : FrequencyOccasional },
		{ Name : ['Turkmenistan'],									Code : ['tm', 'tkm', 'tx', 795],	Language : ['tk', 'ru', 'uz'],							Frequency : FrequencyCommon },
		{ Name : ['Tunisia'],										Code : ['tn', 'tun', 'ts', 788],	Language : ['ar', 'fr'],								Frequency : FrequencyCommon },
		{ Name : ['Tonga'],											Code : ['to', 'ton', 'tn', 776],	Language : ['to', 'en'],								Frequency : FrequencyOccasional },
		{ Name : ['Turkey'],										Code : ['tr', 'tur', 'tu', 792],	Language : ['tr', 'ku', 'az', 'av'],					Frequency : FrequencyCommon },
		{ Name : ['Trinidad and Tobago'],							Code : ['tt', 'tto', 'td', 780],	Language : ['en', 'fr', 'es', 'zh'],					Frequency : FrequencyOccasional },
		{ Name : ['Tuvalu'],										Code : ['tv', 'tuv', 'tv', 798],	Language : ['en', 'sm'],								Frequency : FrequencyOccasional },
		{ Name : ['Taiwan'],										Code : ['tw', 'twn', 'tw', 158],	Language : ['zh', 'zh'],								Frequency : FrequencyCommon },
		{ Name : ['Tanzania'],										Code : ['tz', 'tza', 'tz', 834],	Language : ['sw', 'en', 'ar'],							Frequency : FrequencyCommon },
		{ Name : ['Ukraine'],										Code : ['ua', 'ukr', 'up', 804],	Language : ['uk', 'ru', 'pl', 'hu'],					Frequency : FrequencyCommon },
		{ Name : ['Uganda'],										Code : ['ug', 'uga', 'ug', 800],	Language : ['en', 'lg', 'sw', 'ar'],					Frequency : FrequencyCommon },
		{ Name : ['United States Minor Outlying Islands'],			Code : ['um', 'umi', None, 581],	Language : ['en'],										Frequency : FrequencyUncommon },
		{ Name : ['United States'],									Code : ['us', 'usa', 'us', 840],	Language : ['en', 'es', 'fr'],							Frequency : FrequencyCommon },
		{ Name : ['Uruguay'],										Code : ['uy', 'ury', 'uy', 858],	Language : ['es'],										Frequency : FrequencyCommon },
		{ Name : ['Uzbekistan'],									Code : ['uz', 'uzb', 'uz', 860],	Language : ['uz', 'ru', 'tg'],							Frequency : FrequencyCommon },
		{ Name : ['Vatican'],										Code : ['va', 'vat', 'vt', 336],	Language : ['la', 'it', 'fr'],							Frequency : FrequencyOccasional },
		{ Name : ['Saint Vincent and the Grenadines'],				Code : ['vc', 'vct', 'vc', 670],	Language : ['en', 'fr'],								Frequency : FrequencyOccasional },
		{ Name : ['Venezuela'],										Code : ['ve', 'ven', 've', 862],	Language : ['es'],										Frequency : FrequencyCommon },
		{ Name : ['British Virgin Islands'],						Code : ['vg', 'vgb', 'vi', 92],		Language : ['en'],										Frequency : FrequencyUncommon },
		{ Name : ['United States Virgin Islands'],					Code : ['vi', 'vir', 'vq', 850],	Language : ['en'],										Frequency : FrequencyUncommon },
		{ Name : ['Vietnam'],										Code : ['vn', 'vnm', 'vm', 704],	Language : ['vi', 'en', 'fr', 'zh', 'km'],				Frequency : FrequencyCommon },
		{ Name : ['Vanuatu'],										Code : ['vu', 'vut', 'nh', 548],	Language : ['bi', 'en', 'fr'],							Frequency : FrequencyOccasional },
		{ Name : ['Wallis and Futuna'],								Code : ['wf', 'wlf', 'wf', 876],	Language : ['fr'],										Frequency : FrequencyUncommon },
		{ Name : ['Samoa'],											Code : ['ws', 'wsm', 'ws', 882],	Language : ['sm', 'en'],								Frequency : FrequencyOccasional },
		{ Name : ['Yemen'],											Code : ['ye', 'yem', 'ym', 887],	Language : ['ar'],										Frequency : FrequencyCommon },
		{ Name : ['Mayotte'],										Code : ['yt', 'myt', 'mf', 175],	Language : ['fr'],										Frequency : FrequencyUncommon },
		{ Name : ['South Africa'],									Code : ['za', 'zaf', 'sf', 710],	Language : ['zu', 'xh', 'af', 'en', 'tn', 'st', 'ts', 'ss', 've', 'nr'],	Frequency : FrequencyCommon },
		{ Name : ['Zambia'],										Code : ['zm', 'zmb', 'za', 894],	Language : ['en', 'ny'],								Frequency : FrequencyCommon },
		{ Name : ['Zimbabwe'],										Code : ['zw', 'zwe', 'zi', 716],	Language : ['en', 'sn', 'nr', 'nd'],					Frequency : FrequencyCommon },

		{ Name : ['Serbia and Montenegro'],							Code : ['cs', 'scg', 'yi', 891],	Language : ['cu', 'hu', 'sq', 'sr'],					Frequency : FrequencyNone },
		{ Name : ['Netherlands Antilles'],							Code : ['an', 'ant', 'nt', 530],	Language : ['nl', 'en', 'es'],							Frequency : FrequencyNone },
		{ Name : ['Palestinia'],									Code : ['ps', 'pse', 'we', 275],	Language : ['ar'],										Frequency : FrequencyNone },
		{ Name : ['Antarctica'],									Code : ['aq', 'ata', 'ay', 10],		Language : [],											Frequency : FrequencyNone },
	)

	@classmethod
	def countries(self, universal = True, frequency = None, sort = None):
		if universal: result = Country.Countries
		else: result = Country.Countries[1:]

		if not frequency is None:
			if frequency is True: frequency = [Country.FrequencyCommon, Country.FrequencyOccasional]
			elif frequency is False: frequency = [Country.FrequencyUncommon]

			if Tools.isArray(frequency): result = [i for i in result if i[Country.Frequency] in frequency]
			elif Tools.isInteger(frequency): result = [i for i in result if i[Country.Frequency] >= frequency]

		if sort:
			if sort is True: sort = Country.Name
			result = sorted(result, key = lambda i : i[sort][0])

		return result

	@classmethod
	def country(self, data):
		if not data is None:

			compare = None
			compareString = None
			if Tools.isNumber(data):
				compare = (Country.Code, (Country.CodeQuaternary,))
			else:
				data = data.lower().replace(' ', '')
				length = len(data)
				if length == 2: compare = (Country.Code, (Country.CodePrimary, Country.CodeTertiary))
				elif length == 3: compare = (Country.Code, (Country.CodeSecondary,))
				elif length > 3: compareString = (Country.Name, (Country.NamePrimary,))

			if compare:
				# NB: First iterate over compare[1] before iterating over the countries.
				# This will search all ISO codes BEFORE FIPS codes.
				# Otherwise searching for "gb" returns "Gabon" instead of "United Kingdom".
				for j in compare[1]:
					for i in Country.Countries:
						if data == i[compare[0]][j]:
							return i
			elif compareString:
				for i in Country.Countries:
					value = i[compareString[0]]
					for j in compareString[1]:
						if data == value[j].lower().replace(' ', ''):
							return i

		return None

	@classmethod
	def name(self, data, name = NameDefault):
		country = self.country(data = data)
		if country: return country[Country.Name][name]
		return None

	@classmethod
	def code(self, data, code = CodeDefault):
		country = self.country(data = data)
		if country: return country[Country.Code][code]
		return None

	@classmethod
	def language(self, data, language = LanguageAll):
		country = self.country(data = data)
		if country:
			result = country[Country.Language]
			if not language is Country.LanguageAll: result = result[language]
			return result
		return None

	@classmethod
	def zone(self, data, all = False):
		code = self.code(data = data, code = Country.CodePrimary)
		if code: return Time.zone(country = code, all = all)
		return None

	@classmethod
	def offset(self, data, all = False):
		code = self.code(data = data, code = Country.CodePrimary)
		if code: return Time.offset(country = code, all = all)
		return None

	@classmethod
	def settings(self, id = None, type = None, code = CodeDefault):
		setting = Settings.getString(id)
		if code is None or code is False: return self.country(data = setting)
		else: return self.code(data = setting, code = code)

	@classmethod
	def settingsSelect(self, id = None, type = None, title = None, automatic = None, none = None, frequency = None):
		from lib.modules.interface import Dialog

		current = Settings.getString(id)
		countries = self.countries(universal = False, frequency = frequency, sort = Country.Name)

		countries = [i[Country.Name][Country.NameDefault] for i in countries]
		if automatic: countries.insert(0, Country.Automatic.capitalize())
		if none: countries.insert(0, Country.Disabled.capitalize())

		choice = Dialog.select(title = title if title else 33855, items = countries, selection = current)
		if choice < 0: return None

		choice = countries[choice]
		Settings.set(id, choice)
		return choice


class Identifier(object):

	Base = 32
	Alphabet = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'

	@classmethod
	def generate(self, *parts):
		parts = list(parts)
		for i in range(len(parts)):
			try: parts[i] = Converter.unicode(parts[i])
			except: pass
		parts = '_'.join(parts)
		try: hash = hashlib.sha256(parts.encode('utf-8')).hexdigest()
		except: hash = hashlib.sha256(parts).hexdigest()
		hash = int(hash, 16) % (10 ** 48)
		return self.base(hash)

	@classmethod
	def base(self, value, base = Base):
		# https://stackoverflow.com/questions/2267362/how-to-convert-an-integer-to-a-string-in-any-base
		if value == 0: return Identifier.Alphabet[0]
		digits = []
		while value:
			digits.append(Identifier.Alphabet[int(value % base)])
			value //= base
		digits.reverse()
		return ''.join(digits)

class Hash(object):

	# Fast hashing algorithm used by Python's dictionary.
	# Returns integer.
	# NB: Note that this function has a RANDOM seed.
	# Every time a new Python invoker is initialized, it will use a different random seed.
	# This means that the hash will be the SAME during the same execution, but DIFFERENT between consecutive executions.
	# Do not use this if a persistent hash is needed (eg: ID in a database).
	# The only way to use a fixed seed, is to set the PYTHONHASHSEED environment variable.
	# This is not a reliable way of doing it, since it will set it globally (and other libs might use it) and might not always work.
	# https://gist.github.com/mkolod/853cda9950b898d056ac149abc45417a
	@classmethod
	def hash(self, data):
		# To get hex hash: hash(data).to_bytes(8, 'big').hex().upper()
		return hash(data)

	# A hash that is persistent between executions, as an alternative to the hash() function.
	# Using external libraries for a "faster" hash function, either has C/C++ code, or pure-python implementations are slower than hashlib.
	# Although MD5 is faster in Python 2, under Python 3 SHA1 is slightly faster than MD5.
	# About 2.5x slower than the internal hash() function.
	@classmethod
	def hashPersistent(self, data):
		try: return hashlib.sha1(data.encode('utf-8')).hexdigest()
		except: return hashlib.sha1(data).hexdigest()

	@classmethod
	def random(self):
		import uuid
		return str(uuid.uuid4().hex).upper()

	@classmethod
	def uuid(self):
		import uuid
		return str(uuid.uuid4())

	@classmethod
	def sha1(self, data):
		try: return hashlib.sha1(data.encode('utf-8')).hexdigest().upper()
		except: return hashlib.sha1(data).hexdigest().upper() # If data contains non-encodable characters, like YggTorrent containers.

	@classmethod
	def sha256(self, data):
		try: return hashlib.sha256(data.encode('utf-8')).hexdigest().upper()
		except: return hashlib.sha256(data).hexdigest().upper() # If data contains non-encodable characters, like YggTorrent containers.

	@classmethod
	def sha512(self, data):
		try: return hashlib.sha512(data.encode('utf-8')).hexdigest().upper()
		except: return hashlib.sha512(data).hexdigest().upper() # If data contains non-encodable characters, like YggTorrent containers.

	@classmethod
	def md5(self, data):
		try: return hashlib.md5(data.encode('utf-8')).hexdigest().upper()
		except: return hashlib.md5(data).hexdigest().upper() # If data contains non-encodable characters, like YggTorrent containers.

	@classmethod
	def file(self, path):
		return self.fileSha256(path)

	@classmethod
	def fileSha1(self, path):
		return self.sha1(File.readNow(path))

	@classmethod
	def fileSha256(self, path):
		return self.sha256(File.readNow(path))

	@classmethod
	def fileSha512(self, path):
		return self.sha512(File.readNow(path))

	@classmethod
	def fileMd5(self, path):
		return self.md5(File.readNow(path))

	@classmethod
	def valid(self, hash, length = 40):
		return hash and len(hash) == length and bool(re.match('^[a-fA-F0-9]+', hash))

class Video(object):

	# https://en.wikipedia.org/wiki/Video_file_format
	# https://dotwhat.net/type/video-movie-files

	Extensions = {
		'mp2' : True,
		'mp4' : True,
		'mpg' : True,
		'mpg2' : True,
		'mpg4' : True,
		'mpeg' : True,
		'mpeg2' : True,
		'mpeg4' : True,
		'mpe' : True,
		'mpv' : True,
		'm4v' : True,
		'm4p' : True,
		'm2v' : True,
		'm2p' : True,
		'ps' : True,
		'mkv' : True,
		'mk3d' : True,
		'webm' : True,
		'avi' : True,
		'avp' : True,
		'avs' : True,
		'amv' : True,
		'flv' : True,
		'f4v' : True,
		'swf' : True,
		'aaf' : True,
		'asf' : True,
		'asx' : True,
		'3gp' : True,
		'3gpp' : True,
		'3gp2' : True,
		'3g2' : True,
		'3mm' : True,
		'ogg' : True,
		'ogv' : True,
		'wmv' : True,
		'mov' : True,
		'hdmov' : True,
		'qt' : True,
		'vob' : True,
		'rm' : True,
		'rmvb' : True,
		'svi' : True,
		'avchd' : True,
		'divx' : True,
		'xvid' : True,
		'mxf' : True,
		'viv' : True,
		'ts' : True,
		'mts' : True,
		'm2t' : True,
		'm2ts' : True,
		'bup' : True,
		'edl' : True,
		'enc' : True,
		'nsv' : True,
		'264' : True,
		'265' : True,
		'266' : True,
		'vp6' : True,
		'vp7' : True,
		'vp8' : True,
		'vp9' : True,
		'vp10' : True,
	}

	@classmethod
	def extensions(self, list = False, dot = False):
		if list:
			result = [i for i in Video.Extensions.keys()] # Convert iterator to list, but we already use "list" as parameter so we cannot use the function list(...).
			if dot: result = ['.' + i for i in result]
			return result
		return Video.Extensions

	@classmethod
	def extensionValid(self, extension = None, path = None, unknown = False):
		if extension == None: extension = os.path.splitext(path)[1][1:]
		if not extension and unknown: return True
		return extension.lower() in Video.Extensions


class Sound(object):

	ModeLaunch		= 'launch'
	ModeScrape		= 'scrape'
	ModeStream		= 'stream'
	ModeRating		= 'rating'
	ModePower		= 'power'
	ModeNotify		= 'notify'

	TimeStart		= 'start'
	TimeFinish		= 'finish'

	TypeDisabled	= None
	TypeNative		= 'native'
	TypeCustom		= 'custom'
	TypeDefault		= 'default'

	CategoryAlert	= 'alert'
	CategoryDing	= 'ding'
	CategoryNotify	= 'notify'
	CategoryStartup	= 'startup'
	Categories		= [CategoryStartup, CategoryNotify, CategoryAlert, CategoryDing] # Order in which displayed.

	MoodSwirling	= 'swirling'	# Sound swirling going upward/downward in a circular fashion.
	MoodSwooshing	= 'swooshing'	# Sound swooshing from one side to the other, like a sword.
	MoodBouncing	= 'bouncing'	# Sound bouncing from one side to the other, almost like a ping-pong ball.
	MoodStepping	= 'stepping'	# Sound that increases/decreases notes like steps.
	MoodBleeping	= 'bleeping'	# Sound that is bleeping and cannot be considered bouncing.
	MoodResonating	= 'resonating'	# Sound that last long and fades out.
	MoodClinking 	= 'clinking'	# Sound with a single tone.
	MoodDelighted	= 'delighted'	# Sound that is happy or positive.

	StyleElectro	= 'electro'		# Sound that is digital, electronic, cyber, or robotic.
	StyleMetal		= 'metal'		# Sound with hard metalic noises.
	StyleBell		= 'bell'		# Sound with soft metalic noises, like a concierge's bell.
	StyleBeat		= 'beat'		# Sound with a beat.
	StyleRoll		= 'roll'		# Sound with drum rolls.
	StyleRing		= 'ring'		# Sound with some kind of short ring.
	StyleTone		= 'tone'		# Any other sound that is short.
	StyleMelody		= 'melody'		# Any other sound that is long.

	Delay			= 0.5
	Files			= None
	Extension		= '.wav'
	Settings		= 'general.sound.effects'

	@classmethod
	def play(self, path, cached = True, stop = False, delay = True):
		if delay: Pool.thread(target = self._play, kwargs = {'path' : path, 'cached' : cached, 'stop' : stop, 'delay' : delay}, start = True)
		else: self._play(path = path, cached = cached, stop = stop, delay = delay)
		return bool(path)

	@classmethod
	def _play(self, path, cached = True, stop = False, delay = True):
		if stop: self.stop()

		# The sound effect starts playing too early, while the windows have not been displayed yet.
		# Wait a little while to sync the sound with the window.
		if delay:
			if delay is True: delay = Sound.Delay
			if delay: Time.sleep(delay)

		if path: xbmc.playSFX(path, cached)

	@classmethod
	def stop(self):
		xbmc.stopSFX()

	@classmethod
	def execute(self, mode, time):
		try:
			path = self. file(mode = mode, time = time)
			if not path: return False
			self.play(path = path)
			return True
		except: Logger.error()
		return False

	@classmethod
	def executeLaunch(self, time):
		return self.execute(mode = Sound.ModeLaunch, time = time)

	@classmethod
	def executeLaunchStart(self):
		return self.executeLaunch(time = Sound.TimeStart)

	@classmethod
	def executeLaunchFinish(self):
		return self.executeLaunch(time = Sound.TimeFinish)

	@classmethod
	def executeScrape(self, time):
		return self.execute(mode = Sound.ModeScrape, time = time)

	@classmethod
	def executeScrapeStart(self):
		return self.executeScrape(time = Sound.TimeStart)

	@classmethod
	def executeScrapeFinish(self):
		return self.executeScrape(time = Sound.TimeFinish)

	@classmethod
	def executeStream(self, time):
		return self.execute(mode = Sound.ModeStream, time = time)

	@classmethod
	def executeStreamStart(self):
		return self.executeStream(time = Sound.TimeStart)

	@classmethod
	def executeStreamFinish(self):
		return self.executeStream(time = Sound.TimeFinish)

	@classmethod
	def executeRating(self, time):
		return self.execute(mode = Sound.ModeRating, time = time)

	@classmethod
	def executeRatingStart(self):
		return self.executeRating(time = Sound.TimeStart)

	@classmethod
	def executeRatingFinish(self):
		return self.executeRating(time = Sound.TimeFinish)

	@classmethod
	def executePower(self, time):
		return self.execute(mode = Sound.ModePower, time = time)

	@classmethod
	def executePowerStart(self):
		return self.executePower(time = Sound.TimeStart)

	@classmethod
	def executePowerFinish(self):
		return self.executePower(time = Sound.TimeFinish)

	@classmethod
	def executeNotify(self, time):
		return self.execute(mode = Sound.ModeNotify, time = time)

	@classmethod
	def executeNotifyStart(self):
		return self.executeNotify(time = Sound.TimeStart)

	@classmethod
	def executeNotifyFinish(self):
		return self.executeNotify(time = Sound.TimeFinish)

	@classmethod
	def enabled(self, mode, time):
		return bool(self.file(mode = mode, time = time))

	@classmethod
	def enabledLaunch(self, time):
		return self.enabled(mode = Sound.ModeLaunch, time = time)

	@classmethod
	def enabledLaunchStart(self):
		return self.enabledLaunch(time = Sound.TimeStart)

	@classmethod
	def enabledLaunchFinish(self):
		return self.enabledLaunch(time = Sound.TimeFinish)

	@classmethod
	def enabledScrape(self, time):
		return self.enabled(mode = Sound.ModeScrape, time = time)

	@classmethod
	def enabledScrapeStart(self):
		return self.enabledScrape(time = Sound.TimeStart)

	@classmethod
	def enabledScrapeFinish(self):
		return self.enabledScrape(time = Sound.TimeFinish)

	@classmethod
	def enabledStream(self, time):
		return self.enabled(mode = Sound.ModeStream, time = time)

	@classmethod
	def enabledStreamStart(self):
		return self.enabledStream(time = Sound.TimeStart)

	@classmethod
	def enabledStreamFinish(self):
		return self.enabledStream(time = Sound.TimeFinish)

	@classmethod
	def enabledRating(self, time):
		return self.enabled(mode = Sound.ModeRating, time = time)

	@classmethod
	def enabledRatingStart(self):
		return self.enabledRating(time = Sound.TimeStart)

	@classmethod
	def enabledRatingFinish(self):
		return self.enabledRating(time = Sound.TimeFinish)

	@classmethod
	def enabledPower(self, time):
		return self.enabled(mode = Sound.ModePower, time = time)

	@classmethod
	def enabledPowerStart(self):
		return self.enabledPower(time = Sound.TimeStart)

	@classmethod
	def enabledPowerFinish(self):
		return self.enabledPower(time = Sound.TimeFinish)

	@classmethod
	def enabledNotify(self, time):
		return self.enabled(mode = Sound.ModeNotify, time = time)

	@classmethod
	def enabledNotifyStart(self):
		return self.enabledNotify(time = Sound.TimeStart)

	@classmethod
	def enabledNotifyFinish(self):
		return self.enabledNotify(time = Sound.TimeFinish)

	@classmethod
	def native(self, mode, time):
		try: return self.settings()[mode][time] == Sound.TypeNative
		except: return False

	@classmethod
	def nativeNotify(self):
		return self.native(mode = Sound.ModeNotify, time = Sound.TimeStart)

	@classmethod
	def id(self, category = None, mood = None, style = None, name = None, id = None):
		if id:
			split = id.split('-')
			return {'category' : split[0], 'mood' : split[1], 'style' : split[2], 'name' : ('-'.join(split[1:])) + Sound.Extension}
		else:
			id = [category]
			if name: id.append(name.replace(Sound.Extension, ''))
			else: id.extend([mood, style])
			return '-'.join(id)

	@classmethod
	def path(self, id = None, category = None, name = None):
		path = File.joinPath(System.pathResources(), 'resources', 'media', 'sound')
		if id:
			value = self.id(id = id)
			category = value['category']
			name = value['name']
		if category: path = File.joinPath(path, category)
		if name: path = File.joinPath(path, name)
		return path

	@classmethod
	def files(self):
		if Sound.Files is None:
			files = []
			path = self.path()
			directories, _ = File.listDirectory(path = path, absolute = False)
			for category in directories:
				_, clips = File.listDirectory(path = File.joinPath(path, category), absolute = True)
				if clips:
					file = []
					for clip in clips:
						name = File.name(path = clip, extension = False)
						split = name.split('-')
						files.append({
							'id' : category + '-' + name,
							'category' : category,
							'mood' : split[0],
							'style' : split[1],
							'label' : ' '.join(split).title(),
							'path' : clip,
						})
			Sound.Files = files
		return Sound.Files

	@classmethod
	def file(self, mode, time):
		settings = self.settings()

		# If clips were deleted or renamed from a previous version, rather use the default values instead of none.
		try: clip = settings[mode][time]
		except: clip = self.settingsDefault()[mode][time]

		if clip is Sound.TypeDisabled: return None
		elif clip == Sound.TypeNative: return None
		elif File.pathIs(clip): path = clip
		else: path = self.path(id = clip)

		return path

	@classmethod
	def settings(self):
		return Settings.getData(id = Sound.Settings)

	@classmethod
	def settingsDefault(self):
		disabled = Sound.TypeDisabled
		launch = self.id(category = Sound.CategoryStartup, mood = Sound.MoodSwirling, style = Sound.StyleRing)
		scrape = self.id(category = Sound.CategoryStartup, mood = Sound.MoodStepping, style = Sound.StyleMelody)
		stream = self.id(category = Sound.CategoryAlert, mood = Sound.MoodSwooshing, style = Sound.StyleTone)
		rating = self.id(category = Sound.CategoryDing, mood = Sound.MoodSwooshing, style = Sound.StyleBell)
		power = self.id(category = Sound.CategoryAlert, mood = Sound.MoodBouncing, style = Sound.StyleMelody)
		notify = Sound.TypeNative

		return {
			Sound.ModeLaunch	: {'label' : 33256,	Sound.TimeStart : disabled,	Sound.TimeFinish : launch},
			Sound.ModeScrape	: {'label' : 35514,	Sound.TimeStart : stream,	Sound.TimeFinish : scrape},
			Sound.ModeStream	: {'label' : 33071,	Sound.TimeStart : stream,	Sound.TimeFinish : disabled},
			Sound.ModeRating	: {'label' : 35187,	Sound.TimeStart : disabled,	Sound.TimeFinish : rating},
			Sound.ModePower		: {'label' : 36419,	Sound.TimeStart : power,	Sound.TimeFinish : disabled},
			Sound.ModeNotify	: {'label' : 36513,	Sound.TimeStart : notify,	Sound.TimeFinish : notify},
		}

	@classmethod
	def settingsUpdate(self, settings = False):
		from lib.modules.interface import Dialog, Translation

		title = Translation.string(33423)
		start = Translation.string(33424)
		finish = Translation.string(33425)
		disabled = Translation.string(32302)
		native = Translation.string(35022)
		custom = Translation.string(35233)
		default = Translation.string(33564)

		self.tCanceled = False
		self.tApplied = False
		self.tSettings = self.settings()
		if not self.tSettings: self.tSettings = self.settingsDefault()
		self.tDefault = self.settingsDefault()
		self.tFiles = self.files()

		def _settingsHelp():
			Dialog.details(title = title, items = [
				{'type' : 'title', 'value' : 'Overview', 'break' : 2},
				{'type' : 'text', 'value' : 'Sound effects can be played in the background at various places in the addon to make it livelier. ', 'break' : 2},
				{'type' : 'title', 'value' : 'Processes', 'break' : 2},
				{'type' : 'text', 'value' : 'Sound can be added to the following processes:', 'break' : 2},
				{'type' : 'list', 'value' : [
					{'title' : 'Launch', 'value' : 'When the addon is launched and the intro window is showing.'},
					{'title' : 'Scrape', 'value' : 'When a new scrape is manually initiated.'},
					{'title' : 'Stream', 'value' : 'When a new stream is being played.'},
					{'title' : 'Rating', 'value' : 'When a rating is cast for a title.'},
					{'title' : 'Power', 'value' : 'When a power action is executed, like powering down the device.'},
					{'title' : 'Notify', 'value' : 'When a popup notification is shown.'},
				], 'number' : False},
				{'type' : 'text', 'value' : 'Note that depending on the duration of the sound effect, is does not always make sense to play both at the start and at the end. For instance, playing a sound at the end of the [I]Stream[/I]  process might interfere with the sound of the playback that has just started.', 'break' : 2},
				{'type' : 'title', 'value' : 'Time', 'break' : 2},
				{'type' : 'text', 'value' : 'For each of these processes, sound can be added at two places:', 'break' : 2},
				{'type' : 'list', 'value' : [
					{'title' : 'Started', 'value' : 'When the process has just started.'},
					{'title' : 'Finished', 'value' : 'When the process has just finished.'},
				], 'number' : False},
				{'type' : 'title', 'value' : 'Sound', 'break' : 2},
				{'type' : 'text', 'value' : 'The following options are available when selection a sound effect:', 'break' : 2},
				{'type' : 'list', 'value' : [
					{'title' : 'Disable', 'value' : 'Disables the sound for the given process.'},
					{'title' : 'Default', 'value' : 'Use the default sound for the given process.'},
					{'title' : 'Native', 'value' : 'Use a native Kodi sound for notifications.'},
					{'title' : 'Custom', 'value' : 'Select a custom file for the sound effects. Note that all files must be WAV and other compressed formats will not play.'},
					{'title' : 'Predefined', 'value' : 'Otherwise select from a range of built-in sound effects.'},
				], 'number' : False},
			])

		def _settingsSave():
			label = None
			if self.tSettings == self.tDefault: label = default
			elif _settingsDisabled(): label = disabled
			else: label = custom
			Settings.setData(id = Sound.Settings, value = self.tSettings, label = label)

		def _settingsDefault():
			self.tSettings = Tools.copy(self.tDefault)

		def _settingsDisable():
			for v in self.tSettings.values():
				for k in v.keys():
					v[k] = None

		def _settingsDisabled():
			if self.tSettings:
				for k, v in self.tSettings.items():
					for value in v.values():
						if value: return False
			return True

		def _settingsLabel(value):
			if value is Sound.TypeDisabled: return disabled
			elif value == Sound.TypeNative: return native
			elif value == Sound.TypeCustom or File.pathIs(value): return custom
			else: return ' '.join(value.split('-')[1:]).title()

		def _settingsUpdate(mode, time):
			choice = Dialog.information(title = title, refresh = lambda : _settingsClips(mode = mode, time = time), reselect = Dialog.ReselectYes)
			if choice == -1: self.tCanceled = True

		def _settingsNotification(message = None, sound = False):
			Dialog.notification(title = title, message = message if message else 33428, icon = Dialog.IconInformation, time = 5000, duplicates = True, wait = False, sound = sound)

		def _settingsSelect(mode = None, time = None, type = None, file = None):
			if not type is Sound.TypeDisabled or file:
				path = None
				function = None
				if type is Sound.TypeNative:
					function = lambda : _settingsNotification(message = 33426, sound = True)
				elif type is Sound.TypeDefault:
					path = self.path(id = self.tDefault[mode][time])
				elif type is Sound.TypeCustom:
					default = self.tSettings[mode][time] if File.exists(self.tSettings[mode][time], file = True) else None
					path = Dialog.browse(title = title, type = Dialog.BrowseFile, default = default, mask = Sound.Extension)
					if not path or not File.exists(path, file = True): return
				elif file:
					path = file['path']

				while True:
					if function:
						function()
					else:
						_settingsNotification()
						self.play(path = path, stop = True)
					choice = Dialog.options(title = title, message = 36512, labelConfirm = 35478, labelDeny = 33743, labelCustom = 35470, default = Dialog.ChoiceNo)
					if choice is None or choice < 0: return
					elif choice == Dialog.ChoiceYes: break
					elif choice == Dialog.ChoiceNo: return

			if file: self.tSettings[mode][time] = file['id']
			elif type is Sound.TypeDefault: self.tSettings[mode][time] = self.tDefault[mode][time]
			elif type is Sound.TypeCustom: self.tSettings[mode][time] = path
			else: self.tSettings[mode][time] = type

			self.tApplied = True

		def _settingsClips(mode, time):
			if self.tCanceled: return None
			if self.tApplied:
				self.tApplied = False
				return None

			current = self.tSettings[mode][time]
			items = [
				{'title' : Dialog.prefixBack(35374), 'close' : True},
				{'title' : Dialog.prefixNext(33239), 'action' : _settingsHelp},
				{'title' : 32310, 'items' : [
					{'title' : 33737, 'selection' : current is Sound.TypeDisabled, 'action' : _settingsSelect, 'parameters' : {'mode' : mode, 'time' : time, 'type' : Sound.TypeDisabled}},
					{'title' : default, 'selection' : current == Sound.TypeDefault, 'action' : _settingsSelect, 'parameters' : {'mode' : mode, 'time' : time, 'type' : Sound.TypeDefault}},
					{'title' : native, 'selection' : current == Sound.TypeNative, 'action' : _settingsSelect, 'parameters' : {'mode' : mode, 'time' : time, 'type' : Sound.TypeNative}} if mode == Sound.ModeNotify else None,
					{'title' : custom, 'selection' : File.pathIs(current), 'action' : _settingsSelect, 'parameters' : {'mode' : mode, 'time' : time, 'type' : Sound.TypeCustom}},
				]}
			]

			files = Tools.listSort(self.tFiles, key = lambda i : i['id'])
			files = Tools.listSort(files, key = lambda i : Sound.Categories.index(i['category']) if i['category'] in Sound.Categories else 999)
			categories = {}
			for file in files:
				if not file['category'] in categories: categories[file['category']] = []
				categories[file['category']].append(file)
			for category, files in categories.items():
				items.append({'title' : category.title(), 'items' : [{'title' : file['label'], 'selection' : current == file['id'], 'action' : _settingsSelect, 'parameters' : {'mode' : mode, 'time' : time, 'file' : file}} for file in files]})

			return items

		def _settingsItems():
			if self.tCanceled: return None

			items = [
				{'title' : Dialog.prefixBack(33486), 'close' : True},
				{'title' : Dialog.prefixNext(33239), 'action' : _settingsHelp},
				{'title' : Dialog.prefixNext(33564), 'action' : _settingsDefault},
				{'title' : Dialog.prefixNext(33737), 'action' : _settingsDisable},
			]

			for mode, value in self.tDefault.items():
				items.append({'title' : value['label'], 'items' : [
					{'title' : start, 'value' : _settingsLabel(self.tSettings[mode][Sound.TimeStart]), 'action' : _settingsUpdate, 'parameters' : {'mode' : mode, 'time' : Sound.TimeStart}},
					{'title' : finish, 'value' : _settingsLabel(self.tSettings[mode][Sound.TimeFinish]), 'action' : _settingsUpdate, 'parameters' : {'mode' : mode, 'time' : Sound.TimeFinish}},
				]})

			return items

		Dialog.information(title = title, refresh = _settingsItems, reselect = Dialog.ReselectYes)
		_settingsSave()
		if settings: Settings.launchData(id = Sound.Settings)

# Kodi's thumbnail cache
class Thumbnail(object):

	Directory = 'special://thumbnails'

	@classmethod
	def hash(self, path):
		try:
			path = path.lower()
			bs = bytearray(path.encode())
			crc = 0xffffffff
			for b in bs:
				crc = crc ^ (b << 24)
				for i in range(8):
					if crc & 0x80000000:
						crc = (crc << 1) ^ 0x04C11DB7
					else:
						crc = crc << 1
				crc = crc & 0xFFFFFFFF
			return '%08x' % crc
		except:
			return None

	@classmethod
	def delete(self, path):
		name = self.hash(path)
		if name == None:
			return None
		name += '.jpg'
		file = None
		directories, files = File.listDirectory(Thumbnail.Directory)
		for f in files:
			if f == name:
				file = os.path.join(Thumbnail.Directory, f)
				break
		for d in directories:
			dir = os.path.join(Thumbnail.Directory, d)
			directories2, files2 = File.listDirectory(dir)
			for f in files2:
				if f == name:
					file = os.path.join(dir, f)
					break
			if not file == None:
				break
		if not file == None:
			File.delete(file, force = True)


class Converter(object):

	@classmethod
	def roman(self, number):
		number = number.lower().replace(' ', '')
		if not number: return None
		numerals = {'i' : 1, 'v' : 5, 'x' : 10, 'l' : 50, 'c' : 100, 'd' : 500, 'm' : 1000}
		result = 0
		for i in range(len(number) - 1, -1, -1):
			i = number[i]
			if not i in numerals: return None
			i = numerals[i]
			if (3 * i) < result: result -= i
			else: result += i
		return result

	# Converts a string into a number representation.
	@classmethod
	def number(self, string, pad = True, inverse = False):
		numbers = [ord(char) for char in string]
		if inverse: numbers = [65536 - number for number in numbers]
		if pad: numbers = ['%05d' % number for number in numbers] # Unicode can go up to 65535.
		else: numbers = [str(number) for number in numbers]
		return ''.join(numbers)

	@classmethod
	def boolean(self, value, string = False, none = False, default = False):
		if none and value is None:
			return value
		elif string:
			return 'true' if value else 'false'
		else:
			if value is True or value is False:
				return value
			elif Tools.isInteger(value):
				return value > 0
			elif Tools.isString(value):
				lower = value.lower()
				if default:
					if lower == 'true' or lower == 'yes' or lower == 't' or lower == 'y' or lower == '1': return True
					elif lower == 'false' or lower == 'no' or lower == 'f' or lower == 'n' or lower == '0': return False
					else: return value
				else:
					return lower == 'true' or lower == 'yes' or lower == 't' or lower == 'y' or lower == '1'
			else:
				return value if default else False

	@classmethod
	def dictionary(self, jsonData):
		try:
			import json

			if jsonData == None: return None
			jsonData = json.loads(jsonData)

			# In case the quotes in the string were escaped, causing the first json.loads to return a unicode string.
			try: jsonData = json.loads(jsonData)
			except: pass

			return jsonData
		except:
			return jsonData

	# Detect encoding from string.
	@classmethod
	def encodingDetect(self, value, best = True):
		try:
			from lib.modules.external import Importer
			return Importer.moduleChardet().detect(value)['encoding']
		except:
			Logger.error()
			return None

	# Replaces all unicode characters with an ASCII-normalized characters closest to the uunicode characterself.
	# Always returns an ASCII string.
	# Eg: Amélie -> Amelie
	# Eg (Non-umlaut): Über -> Uber
	# Eg (Umlaut): Über -> Ueber
	@classmethod
	def unicodeNormalize(self, string, umlaut = False):
		try:
			if not string: return string
			try: string = string.decode('utf-8')
			except: pass

			if umlaut:
				try: string = string.replace(chr(196), 'Ae').replace(chr(203), 'Ee').replace(chr(207), 'Ie').replace(chr(214), 'Oe').replace(chr(220), 'Ue').replace(chr(228), 'ae').replace(chr(235), 'ee').replace(chr(239), 'ie').replace(chr(246), 'oe').replace(chr(252), 'ue')
				except: Logger.error(developer = True)

			# It seems unidecode does not work in Python 2, only in Python 3.
			# In Python 2 the letter is removed instead of being replaced with a non-accent ASCII letter.
			#from lib.modules.external import Importer
			#unidecode = Importer.moduleUnidecode()
			#return unidecode(string.decode('utf-8'))

			import unicodedata
			return unicodedata.normalize('NFKD', string).encode('ascii', 'ignore').decode('ascii')
		except:
			Logger.error(developer = True)
			return self.unicodeStrip(string = string)

	# Removes all unicode characters.
	# Always returns an ASCII string.
	# Eg: Amélie -> Amlie
	@classmethod
	def unicodeStrip(self, string):
		try: string = string.decode('utf-8')
		except: pass
		try: return string.encode('ascii', 'ignore').decode('ascii')
		except: return string

	# Decode double escaped hex characters.
	# Eg: "\\x26" (not the hex Python char "\x26", but the hex char as a string with double backslash - eg extracted from HTML).
	@classmethod
	def unicodeHex(self, string):
		try:
			import codecs
			return self.unicode(codecs.escape_decode(string, 'hex')[0])
		except:
			Logger.error()
			return string

	@classmethod
	def unicode(self, value, encoding = 'utf-8'):
		if Tools.isString(value):
			try: value = str(value, encoding)
			except: pass
		else:
			# Non-strings (None, boolean, etc) fail to convert to string if the encoding is set.
			return str(value)
		return value

	@classmethod
	def bytes(self, value, encoding = 'utf-8'):
		try: value = bytes(value, encoding)
		except: pass
		return value

	@classmethod
	def base16From(self, data):
		import base64
		return self.unicode(base64.b16decode(data))

	@classmethod
	def base16To(self, data):
		import base64
		return self.unicode(base64.b16encode(self.bytes(data)))

	@classmethod
	def base32From(self, data):
		import base64
		return self.unicode(base64.b32decode(data))

	@classmethod
	def base32To(self, data):
		import base64
		return self.unicode(base64.b32encode(self.bytes(data)))

	@classmethod
	def base64Hex(self, data):
		import base64
		return self.unicode(base64.b64decode(data).hex())

	@classmethod
	def base64From(self, data, url = False):
		import base64
		if url: data = base64.urlsafe_b64decode(data)
		else: data = base64.b64decode(data)
		return self.unicode(data)

	@classmethod
	def base64To(self, data):
		# Alternatively use pybase64 (similar to ujson or psutil).
		# NB: Note that the pybase64 "manylinux x64 cp36" has a problem, always outputting random data, even if the input is the same.
		# Using the "manylinux x32 cp36" version seems to work correctly.
		# Or use the "manylinux x64 cp37" version, which also works correctly and also works under Python 3.6.
		# Currently we do not use pybase64, since the performance improvement is almost non-exisiting.
		# Although pybase64 is 20+ times faster than base64 for very large objects, there is essentially no speed improvement for smaller objects.
		# Eg: if 1000 streams are loaded in WindowStreams, each encoding their command/URL with System.command(), pybase64 and base64 perform exactly the same.
		# So ignore pybase64 for now, due to the problem described above (which maybe also exisit for other architecture wheels), and it only increasing the addon size.

		import base64
		return self.unicode(base64.b64encode(self.bytes(data)))

	@classmethod
	def jsonFrom(self, data, default = None):
		return Json.decode(data = data, default = default)

	@classmethod
	def jsonTo(self, data, ascii = True, default = None):
		return Json.encode(data = data, ascii = ascii, default = default)

	@classmethod
	def jsonPrettify(self, data, ascii = True, default = None, indent = True):
		return Json.prettify(data = data, ascii = ascii, default = default, indent = indent)

	# Extract a JSON object/list from a larger non-JSON text body.
	@classmethod
	def jsonExtract(self, data, multiple = True, text = False, uncomment = False, bounds = None):
		return Json.extract(data = data, multiple = multiple, text = text, uncomment = uncomment, bounds = bounds)

	# Remove comments from JSON.
	@classmethod
	def jsonUncomment(self, data):
		return Json.uncomment(data = data)

	@classmethod
	def quoteFrom(self, data, default = None):
		try:
			from lib.modules.network import Networker
			return Networker.linkUnquote(data, plus = True)
		except: return default

	@classmethod
	def quoteTo(self, data, default = None):
		try:
			from lib.modules.network import Networker
			return Networker.linkQuote(data, plus = True)
		except: return default

	@classmethod
	def serialize(self, data):
		try:
			import pickle
			return pickle.dumps(data)
		except:
			return None

	@classmethod
	def unserialize(self, data):
		try:
			import pickle
			return pickle.loads(data)
		except:
			return None

	# Convert HTML entities to ASCII.
	@classmethod
	def htmlFrom(self, data):
		try:
			try: from HTMLParser import HTMLParser
			except: from html.parser import HTMLParser
			return str(HTMLParser().unescape(data))
		except:
			return data


class Csv(object):

	@classmethod
	def decode(self, data = None, path = None, structured = False, header = False, delimiterColumn = ',', delimiterRow = None, delimiterQuote = '"', convertBoolean = True, convertInteger = True, convertFloat = True, convertList = True):
		try:
			# Do not use the native Python csv module.
			# There are too many problems with IMDb exported lists:
			#	1. Cannot deal with spaces in a single column (treats it like a delimiter).
			#	2. IMDb only quotes a column if the data contains a comma itself. But a string with spaces that does not contain a comma, is not quoted.

			replaceComma = '[GAIACOMMA]'
			replaceQuote = '[GAIAQUOTE]'
			replaceBreak = '[GAIABREAK]'

			if path: data = File.readNow(path)

			# Columns that are inside quotes and contain commas, should not be split.
			# Eg: 2023,"Animation, Adventure, Comedy",90662,2023-05-27
			# NB: Do this BEFORE splitting into rows, since there might be multiline columns, containing newlines and commas.
			if delimiterQuote:
				# Quotes within a column that is quoted are represented as double quotes.
				# Also exclude if the double quotes are at the start/end of the column.
				# Eg: 1,Action,123,"He made a ""reboot""",987
				# Ignore internal BBcode brackets followed by quotes.
				# Eg: 2011 short film ""[link=/title/tt2049400/]Beau[/link],"" which inspi
				data = Regex.replace(data = data, expression = '(?<![^\]],)(%s%s)(?!,)' % (delimiterQuote, delimiterQuote), replacement = replaceQuote, group = None, all = True, cache = True)

				# Both FlagMultiLines and FlagAllLines
				# Eg: https://imdb.com/list/ls566661486/export
				entries = Regex.extract(data = data, expression = '(?:^|(?<=,))\s*(\".*?\")(?:$|(?<=\"),)' , group = None, all = True, flags = Regex.FlagCaseInsensitive | Regex.FlagMultiLines | Regex.FlagAllLines, cache = True)
				if entries:
					for entry in entries:
						data = data.replace(entry, entry.strip(delimiterQuote).replace(',', replaceComma).replace('\n', replaceBreak))

			rows = data.splitlines() if delimiterRow is None else data.splitlines(delimiterRow)
			rows = [row for row in rows if row] # Remove empty lines.
			rows = [row.split(delimiterColumn) for row in rows]

			multiline = set()
			for row in rows:
				for i in range(len(row)):
					if replaceBreak in row[i]: multiline.add(i)

			for row in rows:
				for i in range(len(row)):
					value = row[i].strip()
					if convertInteger and value.isnumeric():
						try: value = int(value)
						except: pass
					elif convertFloat and '.' in value and value.replace('.', '').isnumeric():
						try: value = float(value)
						except: pass
					elif replaceComma in value and not i in multiline: # Do not split multiline descriptions, which might also contain commas.
						if convertList: value = [j.strip() for j in value.split(replaceComma)]
						else: value = value.replace(replaceComma, ',')
					elif convertBoolean:
						try: value = Converter.boolean(value = value, string = False, none = False, default = True)
						except: pass
					if Tools.isString(value): value = value.replace(replaceComma, ',').replace(replaceQuote, delimiterQuote).replace(replaceBreak, '\n')
					row[i] = value

			if structured:
				if rows:
					if Tools.isList(header): headers = header
					else: headers = rows[0]
					rows = rows[1:]
					for i in range(len(rows)):
						entry = {}
						row = rows[i]
						for j in range(len(row)):
							entry[headers[j]] = row[j]
						rows[i] = entry
			elif header:
				rows = rows[1 if header is True else header:]

			return rows
		except: Logger.error()
		return None

class Logger(object):

	try: TypeInfo		= xbmc.LOGINFO
	except: TypeInfo	= xbmc.LOGNOTICE
	TypeDebug			= xbmc.LOGDEBUG
	TypeError			= xbmc.LOGERROR
	TypeFatal			= xbmc.LOGFATAL
	TypeDefault			= TypeInfo

	# Must correspond with settings.xml.
	LevelDisabled		= 0
	LevelEssential		= 1
	LevelStandard		= 2
	LevelExtended		= 3
	LevelDefault		= LevelStandard
	LevelForce			= LevelDisabled
	Level				= None

	@classmethod
	def _exit(self):
		Logger.Exited = True

	@classmethod
	def level(self):
		if Logger.Level is None: Logger.Level = Settings.getInteger('general.log.level')
		return Logger.Level

	@classmethod
	def levelAllow(self, level):
		return self.level() >= level

	@classmethod
	def log(self, message, message2 = None, message3 = None, message4 = None, message5 = None, name = True, parameters = None, type = TypeDefault, level = LevelDefault, prefix = False, developer = False):
		if developer and not System.developer(): return
		if not self.levelAllow(level): return

		divider = ' '
		message = str(message)
		if message2: message += divider + str(message2)
		if message3: message += divider + str(message3)
		if message4: message += divider + str(message4)
		if message5: message += divider + str(message5)

		if prefix and name is True:
			if prefix is True:
				if type == Logger.TypeInfo: name = 'INFO'
				elif type == Logger.TypeDebug: name = 'DEBUG'
				elif type == Logger.TypeError: name = 'ERROR'
				elif type == Logger.TypeFatal: name = 'FATAL'
			else:
				name = prefix

		if name:
			nameValue = System.name().upper() + ' ' + ('DEV' if System.versionDeveloper() else System.version())
			if not name is True: nameValue += ' (' + name + ')'
			if parameters:
				nameValue += ' ['
				if Tools.isString(parameters):
					nameValue += parameters
				else:
					nameValue += ', '.join([str(parameter) for parameter in parameters])
				nameValue += ']'
			nameValue += ': '
			message = nameValue + message

		xbmc.log(message, type)

	@classmethod
	def error(self, message = None, exception = True, level = LevelEssential, exit = False, developer = False):
		if developer and not System.developer(): return

		if exception:
			type, value, trace = sys.exc_info()
			try: filename = trace.tb_frame.f_code.co_filename
			except: filename = None
			try: linenumber = trace.tb_lineno
			except: linenumber = None
			try: name = trace.tb_frame.f_code.co_name
			except: name = None
			try: errortype = type.__name__
			except: errortype = None

			# If the user eg loads a menu and canceles it before it is finished, a lot of threads will throw a SystemExit error.
			# Do not log these.
			# Other errors (eg: TypeError and IndexError) might still be thrown.
			if not exit and errortype == 'SystemExit': return None

			try: errormessage = value.message
			except:
				try:
					import traceback
					errormessage = traceback.format_exception(type, value, trace)
				except: pass
			if message: message += ' -> '
			else: message = ''
			message += str(errortype) + ' -> ' + str(errormessage)
			parameters = [filename, linenumber, name]
		else:
			parameters = None
		self.log(message, parameters = parameters, type = Logger.TypeError, level = level, prefix = True)

	@classmethod
	def errorCustom(self, message, level = LevelDefault):
		self.log(message, type = Logger.TypeError, level = level, prefix = True)

	@classmethod
	def path(self):
		path = File.translatePath('special://logpath')
		if not path.endswith('.log'): path = File.joinPath(path, 'kodi.log')
		return path

	@classmethod
	def data(self):
		return File.readNow(self.path())

	# Values in items can be:
	#	String
	# 	Dictionary with these optional values:
	#		title: Adds an empty line and another line with the uppercase title.
	#		separator: Adds a empty line and a separator line
	#		empty: Adds an empty line. Can also be added to other entires (eg: title) to add an empty line afterwards.
	#		section: The same as separator + title + empty
	#		label: Adds a label followed by a colon. Typically added together with a value, although not required.
	#		value: Adds a value. Typically added together with a label, although not required.
	#		align: Makes the values line up undeneath each other after the label.
	#		items: Adds nested sub-items which can have the same format as the outer items as explained above.
	@classmethod
	def details(self, title, items, align = False, level = LevelDefault):
		try:
			if not self.levelAllow(level): return

			lines = []

			levelCurrent = self.level()
			lineEmpty = ''
			lineIndent = '   '
			lineSeparator = '#' * 125

			def _string(value):
				if value is None: return 'Unknown'
				return Converter.unicode(value)

			def _indent(indent = 1):
				return lineIndent * indent

			def _spacing(items, indent = 1):
				spacing = 0
				for item in items:
					if item:
						if 'label' in item: spacing = max(spacing, len(item['label']) + len(_indent(indent)))
						if 'items' in item: spacing = max(spacing, _spacing(items = item['items'], indent = indent + 1))
				spacing += 2 # Colon + space
				return spacing

			def _add(items, align = False, spacing = None, indent = 1):
				if spacing is None and align: spacing = _spacing(items = items, indent = indent)

				currentSection = False
				currentIndent = _indent(indent)
				currentSeparator = lineSeparator[:-len(currentIndent) * 2]

				for item in items:
					if item:
						if Tools.isString(item):
							lines.append(currentIndent + item)
						elif not 'level' in item or self.levelAllow(item['level']):
							if 'section' in item:
								if currentSection: lines.extend([lineEmpty, currentSeparator])
								currentSection = True
								lines.extend([lineEmpty, currentIndent + _string(item['section']).upper()])
							if 'title' in item: lines.extend([lineEmpty, currentIndent + _string(item['title']).upper()])
							if 'separator' in item: lines.extend([lineEmpty, currentSeparator])
							if 'empty' in item: lines.append(lineEmpty)

							line = ''
							if 'label' in item or 'value' in item: line += currentIndent
							if 'label' in item: line += (_string(item['label']) + ':').ljust(spacing - len(currentIndent))
							if 'value' in item: line += _string(item['value'])
							if line: lines.append(line)

							if 'items' in item: _add(items = item['items'], align = align or ('align' in item and item['align']), spacing = spacing, indent = indent + 1)

			lines.extend([lineSeparator, lineEmpty, _indent() + 'GAIA - %s' % title.upper(), lineEmpty, lineSeparator])
			_add(items = items, align = align)
			lines.extend([lineEmpty, lineSeparator])

			self.log('', name = False, level = level)
			[self.log('##' + line, name = False) for line in lines]
			self.log('', name = False, level = level)

			return '\n'.join(lines)
		except:
			self.error(message = 'Could not generate detailed information')

	@classmethod
	def system(self, full = False, level = LevelDefault):
		try:
			if not self.levelAllow(level): return

			from lib.modules.concurrency import Pool

			items = []

			platform = Platform.data(refresh = True)
			hardware = Hardware.data(full = full, refresh = True)
			concurrency = Pool.settingData()

			# Identifier
			items.append({
				'section' : 'Identifier',
				'items' : [
					{'label' : 'Id', 'value' : platform['identifier']},
				],
			})

			# Gaia
			items.append({
				'section' : 'Gaia',
				'items' : [
					{'label' : 'ID', 'value' : platform['addon']['id']},
					{'label' : 'Name', 'value' : platform['addon']['name']},
					{'label' : 'Version', 'value' : platform['addon']['version']},
					{'label' : 'Author', 'value' : platform['addon']['author']},
				],
			})

			# Kodi
			items.append({
				'section' : 'Kodi',
				'items' : [
					{'label' : 'Name', 'value' : platform['kodi']['name']},
					{'label' : 'Build', 'value' : platform['kodi']['build']},
					{'label' : 'Version', 'value' : platform['kodi']['version']['label']},
					{'label' : 'Release', 'value' : platform['kodi']['release']['label']},
					{'label' : 'Uptime', 'value' : platform['kodi']['uptime']},
				],
			})

			# Platform
			items.append({
				'section' : 'Platform',
				'items' : [
					{'label' : 'Family', 'value' : platform['family']['name']},
					{'label' : 'System', 'value' : platform['system']['name']},
					{'label' : 'Distribution', 'value' : platform['distribution']['name']},
					{'label' : 'Version', 'value' : platform['version']['label']},
					{'label' : 'Architecture', 'value' : platform['architecture']['label']},
					{'label' : 'Environment', 'value' : platform['environment']['label']},
				],
			})

			# Python
			items.append({
				'section' : 'Python',
				'items' : [
					{'label' : 'Build', 'value' : platform['python']['build']},
					{'label' : 'Implementation', 'value' : platform['python']['implementation']},
					{'label' : 'Version', 'value' : platform['python']['version']},
					{'label' : 'Release', 'value' : platform['python']['release']},
					{'label' : 'Concurrency', 'value' : platform['python']['concurrency']['label']},
					{'label' : 'Interpreter', 'value' : platform['python']['interpreter']['label']},
				],
			})

			# Modules
			items.append({
				'section' : 'Modules',
				'items' : [
					{'label' : 'CloudScraper', 'value' : platform['module']['cloudscraper']},
					{'label' : 'PSutil', 'value' : platform['module']['psutil']},
					{'label' : 'UltraJSON', 'value' : platform['module']['ujson']},
					{'label' : 'Image', 'value' : platform['module']['image']},
				],
			})

			# Compression
			subitems = [
				{'label' : 'Global', 'value' : platform['compression']['global']},
				{'label' : 'Database', 'value' : platform['compression']['database']},
			]
			if platform['compression']['algorithm']:
				 for algorithm in platform['compression']['algorithm']:
					 subitems.append({'label' : algorithm['label'], 'value' : algorithm['description']})
			items.append({
				'section' : 'Compression',
				'items' : subitems,
			})

			# Concurrency
			items.append({
				'section' : 'Concurrency',
				'items' : [
					{'label' : 'Level', 'value' : concurrency['label']},
					{'label' : 'Global', 'value' : concurrency['global']['label']},
					{'label' : 'Metadata', 'value' : concurrency['metadata']['label']},
					{'label' : 'Scrape', 'value' : concurrency['scrape']['label']},
					{'label' : 'Binge', 'value' : concurrency['binge']['label']},
					{'label' : 'Connection', 'value' : concurrency['connection']['label']},
					{'label' : 'Mode', 'value' : concurrency['mode']['label']},
				],
			})

			# Hardware
			items.append({
				'section' : 'Hardware',
				'items' : [
					{'label' : 'Processor', 'value' : hardware['processor']['label']},
					{'label' : 'Memory', 'value' : hardware['memory']['label']},
					{'label' : 'Storage', 'value' : hardware['storage']['label']} if full else None,
				],
			})

			# Usage
			items.append({
				'section' : 'Usage',
				'items' : [
					{'label' : 'Processor', 'value' : hardware['processor']['usage']['label']},
					{'label' : 'Memory', 'value' : hardware['memory']['usage']['label']},
					{'label' : 'Storage', 'value' : hardware['storage']['usage']['label']},
				],
			})

			return self.details(title = 'System Details', items = items, align = True)
		except:
			self.error(message = 'Could not generate system information', level = Logger.LevelForce)

	@classmethod
	def scrapePath(self, create = False):
		path = File.joinPath(System.profile(), 'Log')
		if create and not File.existsDirectory(path): File.makeDirectory(path)
		return File.joinPath(path, 'scrape.log')

	@classmethod
	def scrape(self, data):
		path = self.scrapePath(create = True)
		return File.writeNow(path, data)

	@classmethod
	def dialog(self, lines = 1000):
		from lib.modules.interface import Dialog
		data = self.data()
		data = data.split('\n')
		data = '\n'.join(data[-lines:])
		Dialog.text(data, mono = True)

	@classmethod
	def dialogScrape(self):
		from lib.modules.interface import Dialog
		data = File.readNow(self.scrapePath())
		Dialog.text(data, mono = True)

class File(object):

	PrefixSpecial = 'special://'
	PrefixSamba = 'smb://'

	DirectoryHome = PrefixSpecial + 'home'
	DirectoryTemporary = PrefixSpecial + 'temp'

	@classmethod
	def translate(self, path):
		if path.startswith(File.PrefixSpecial): path = xbmcvfs.translatePath(path)
		return path

	@classmethod
	def name(self, path, extension = False):
		name = os.path.basename(path if extension else os.path.splitext(path)[0])
		if not name: name = None
		return name

	@classmethod
	def separator(self):
		return os.path.sep

	@classmethod
	def makeDirectory(self, path, retry = True):
		xbmcvfs.mkdirs(path)
		if self.existsDirectory(path):
			return True
		elif retry:
			# When manually deleting a folder, and then recreating it from Python, xbmcvfs.mkdirs(path) returns True, but the directory is never actually created.
			# When executing the same Python code again, the directory creation suddenly works.
			# This is probably an internal caching issue in Kodi (eg: maybe Kodi does not create the directory, because it still thinks it exists).
			# Eg: Deletre the "Windows" directory in the profile folder. Try loading the Donations window, and it will fail.
			# Creating a different temp path, deleting it, and then creating the actual path, seems to work.
			pathTemp = path + '_'
			xbmcvfs.mkdirs(pathTemp)
			self.deleteDirectory(pathTemp, force = True, check = False) # Do not check before deleting, since Kodi still thinks the directory exists.
			xbmcvfs.mkdirs(path)
			return self.existsDirectory(path)
		else:
			return False

	@classmethod
	def translatePath(self, path):
		return xbmcvfs.translatePath(path)

	@classmethod
	def legalPath(self, path):
		return xbmcvfs.makeLegalFilename(path)

	@classmethod
	def joinPath(self, path, *paths):
		parts = []
		for p in paths:
			if Tools.isArray(p): parts.extend(p)
			else: parts.append(p)
		return os.path.join(path, *parts)

	@classmethod
	def pathHome(self):
		return File.DirectoryHome

	@classmethod
	def pathTemporary(self):
		return File.DirectoryTemporary

	@classmethod
	def pathCurrent(self, caller = True):
		if caller:
			import inspect
			path = inspect.stack()[1].filename
		else:
			path = __file__
		return os.path.abspath(os.path.realpath(path))

	@classmethod
	def pathSeparator(self):
		return os.sep

	@classmethod
	def pathIs(self, path):
		if not path: return False
		return self.pathSeparator() in path

	# Directory must end with slash
	@classmethod
	def exists(self, path, file = None):
		if path:
			# Do not use xbmcvfs.exists, since it returns true for http links.
			if path.startswith('http:') or path.startswith('https:') or path.startswith('ftp:') or path.startswith('ftps:'):
				return os.path.exists(path)
			else:
				if file and path.endswith(self.pathSeparator()): return False
				return xbmcvfs.exists(path)
		return False

	@classmethod
	def existsDirectory(self, path):
		if not path.endswith('/') and not path.endswith('\\'): path += '/'
		return xbmcvfs.exists(path)

	# If samba file or directory.
	@classmethod
	def samba(self, path):
		return path.startswith(File.PrefixSamba)

	# If network (samba or any other non-local supported Kodi path) file or directory.
	# Path must point to a valid file or directory.
	@classmethod
	def network(self, path):
		return self.samba(path) or (self.exists(path) and not os.path.exists(path))

	@classmethod
	def delete(self, path, force = True):
		try:
			# For samba paths
			try:
				if self.exists(path):
					xbmcvfs.delete(path)
			except: pass

			# All with force
			try:
				if self.exists(path):
					if force:
						try:
							import stat
							os.chmod(path, stat.S_IWRITE) # Remove read only.
						except: pass
					return os.remove(path) # xbmcvfs often has problems deleting files
			except: pass

			return not self.exists(path)
		except:
			return False

	@classmethod
	def directory(self, path):
		return os.path.dirname(path)

	@classmethod
	def directoryName(self, path):
		return os.path.basename(self.directory(path))

	@classmethod
	def directoryCurrent(self, caller = True):
		if caller:
			import inspect
			path = inspect.stack()[1].filename
		else:
			path = __file__
		return self.directory(path)

	@classmethod
	def deleteDirectory(self, path, force = True, check = True):
		try:
			valid = not check or self.existsDirectory(path)

			# For samba paths
			try:
				if valid:
					xbmcvfs.rmdir(path)
					if not self.existsDirectory(path): return True
			except: pass

			try:
				if valid:
					import shutil
					shutil.rmtree(path)
					if not self.existsDirectory(path): return True
			except: pass

			# All with force
			try:
				if valid:
					if force:
						import stat
						os.chmod(path, stat.S_IWRITE) # Remove read only.
					os.rmdir(path)
					if not self.existsDirectory(path): return True
			except: pass

			# Try individual delete
			try:
				if valid:
					directories, files = self.listDirectory(path)
					for i in files:
						self.delete(os.path.join(path, i), force = force)
					for i in directories:
						self.deleteDirectory(os.path.join(path, i), force = force)
					try: xbmcvfs.rmdir(path)
					except: pass
					try:
						import shutil
						shutil.rmtree(path)
					except: pass
					try: os.rmdir(path)
					except: pass
			except: pass

			return not self.existsDirectory(path)
		except:
			Logger.error()
			return False

	@classmethod
	def size(self, path):
		file = xbmcvfs.File(path)
		size = file.size()
		file.close()
		return size

	@classmethod
	def sizeDirectory(self, path, limit = None):
		total = 0
		directories, files = self.listDirectory(path, absolute = True)
		for directory in directories:
			total += self.sizeDirectory(directory)
			if limit and total > limit: return -1
		for file in files:
			total += self.size(file)
			if limit and total > limit: return -1
		return total

	@classmethod
	def timeCreated(self, path):
		return xbmcvfs.Stat(path).st_ctime()

	@classmethod
	def timeAccessed(self, path):
		return xbmcvfs.Stat(path).st_atime()

	@classmethod
	def timeUpdated(self, path):
		return xbmcvfs.Stat(path).st_mtime()

	@classmethod
	def create(self, path):
		return self.writeNow(path, '')

	@classmethod
	def readNow(self, path, bytes = False, native = False, exists = False):
		try:
			if not path:
				try:
					import inspect
					trace = inspect.stack()[1][3]
				except: trace = None
				Logger.log('Invalid file path: ' + str(trace))
				return None

			if exists and not self.exists(path = path): return None

			result = None
			if native:
				with open(path, 'rb' if bytes else 'r') as file:
					result = file.read()
			else:
				file = xbmcvfs.File(path)
				result = file.readBytes() if bytes else file.read()
				file.close()
			return result
		except:
			Logger.error()
			return None

	@classmethod
	def writeNow(self, path, value, bytes = False, native = False):
		try:
			if not path:
				try:
					import inspect
					trace = inspect.stack()[1][3]
				except: trace = None
				Logger.log('Invalid file path: ' + str(trace))
				return None

			if native:
				with open(path, 'wb' if bytes else 'w') as file:
					file.write(value)
			else:
				file = xbmcvfs.File(path, 'w')
				result = file.write(value)
				file.close()
				return result
		except:
			Logger.error()
			return None

	@classmethod
	def write(self, path, bytes = False, native = False):
		try:
			if not path:
				try:
					import inspect
					trace = inspect.stack()[1][3]
				except: trace = None
				Logger.log('Invalid file path: ' + str(trace))
				return None

			if native: return open(path, 'wb' if bytes else 'w')
			else: return xbmcvfs.File(path, 'w')
		except:
			Logger.error()
			return None

	# replaceNow(path, 'from', 'to')
	# replaceNow(path, [['from1', 'to1'], ['from2', 'to2']])
	@classmethod
	def replaceNow(self, path, valueFrom, valueTo = None):
		data = self.readNow(path)
		if not Tools.isArray(valueFrom):
			valueFrom = [[valueFrom, valueTo]]
		for replacement in valueFrom:
			data = data.replace(replacement[0], replacement[1])
		self.writeNow(path, data)

	# Returns: directories, files
	@classmethod
	def listDirectory(self, path, absolute = False):
		directories, files = xbmcvfs.listdir(path)
		if absolute:
			for i in range(len(files)):
				files[i] = File.joinPath(path, files[i])
			for i in range(len(directories)):
				directories[i] = File.joinPath(path, directories[i])
		return directories, files

	@classmethod
	def copy(self, pathFrom, pathTo, bytes = None, overwrite = False, sleep = True):
		if overwrite and xbmcvfs.exists(pathTo):
			try: self.delete(path = pathTo, force = True)
			except: pass
			# This is important, especailly for Windows.
			# When deleteing a file and immediatly replacing it, the old file might still exist and the file is never replaced.
			if sleep: Time.sleep(0.1 if sleep == True else sleep)
		if bytes == None:
			return xbmcvfs.copy(pathFrom, pathTo)
		else:
			try:
				fileFrom = xbmcvfs.File(pathFrom)
				fileTo = xbmcvfs.File(pathTo, 'w')
				chunk = min(bytes, 1048576) # 1 MB
				while bytes > 0:
					size = min(bytes, chunk)
					fileTo.write(fileFrom.read(size))
					bytes -= size
				fileFrom.close()
				fileTo.close()
				return True
			except:
				return False

	@classmethod
	def copyDirectory(self, pathFrom, pathTo, overwrite = True):
		if not pathFrom.endswith('/') and not pathFrom.endswith('\\'): pathFrom += '/'
		if not pathTo.endswith('/') and not pathTo.endswith('\\'): pathTo += '/'

		# NB: Always check if directory exists before copying it on Windows.
		# If the source directory does not exist, Windows will simply copy the entire C: drive.
		if self.existsDirectory(pathFrom):
			try:
				if overwrite: File.deleteDirectory(pathTo)
				import shutil
				shutil.copytree(pathFrom, pathTo)
				return True
			except:
				return False
		else:
			return False

	@classmethod
	def renameDirectory(self, pathFrom, pathTo):
		if not pathFrom.endswith('/') and not pathFrom.endswith('\\'):
			pathFrom += '/'
		if not pathTo.endswith('/') and not pathTo.endswith('\\'):
			pathTo += '/'
		os.rename(pathFrom, pathTo)

	# Not for samba paths
	@classmethod
	def move(self, pathFrom, pathTo, replace = True, sleep = True):
		if pathFrom == pathTo:
			return False
		if replace:
			try: self.delete(path = pathTo, force = True)
			except: pass
			# This is important, especially for Windows.
			# When deleting a file and immediatly replacing it, the old file might still exist and the file is never replaced.
			if sleep: Time.sleep(0.1 if sleep is True else sleep)
		try:
			import shutil
			shutil.move(pathFrom, pathTo)
			return True
		except:
			return False

class System(object):

	# https://kodi.wiki/view/List_of_Built_In_Controls
	ControlConfirmNo = 10
	ControlConfirmYes = 11

	PropertyObserve = 'GaiaObserve'
	PropertyLaunch = 'GaiaLaunch'
	PropertyVersion = 'GaiaVersion'
	PropertyUpdate = 'GaiaUpdate'
	PropertyInitial = 'GaiaInitial'
	PropertyRestart = 'GaiaRestart'
	PropertyLock = 'GaiaLock'

	StartupScript = 'special://masterprofile/autoexec.py'
	AdvancedSettings = 'special://userdata/advancedsettings.xml'

	PluginPrefix = 'plugin://'

	GaiaAddon = 'plugin.video.gaia'
	GaiaExternals = 'script.gaia.externals'
	GaiaBinaries = 'script.gaia.binaries'
	GaiaResources = 'script.gaia.resources'
	GaiaMetadata = 'script.gaia.metadata'
	GaiaIcons = 'script.gaia.icons'
	GaiaSkins = 'script.gaia.skins'

	GaiaRepositoryCore = 'repository.gaia.core'
	GaiaRepositoryFull = 'repository.gaia.full'
	GaiaRepositoryTest = 'repository.gaia.test'

	KodiVersion = None
	KodiVersionFull = None
	KodiVersionNew = None

	OriginGaia = 'gaia' # The call came from within the Gaia plugin.
	OriginPlaylist = 'playlist' # The call came from an item added to the playlist.
	OriginLibrary = 'library' # The call came from an item added to the Kodi library, using Gaia's local library feature.
	OriginGaia = 'gaia' # The call came from within the Gaia addon.
	OriginWidget = 'widget' # The call came from an external skin widget. This will only work if "&origin=widget" was manually added to the widget's command.
	OriginAddon = 'addon' # The call came from an external addon. This will only work if "&origin=addon" was manually added to the command by the external addon.
	OriginExternal = 'external' # The call came from some other external source. This will only work if "&origin=external" was manually added to the command by the external source.

	OriginsParameter = 'origin'
	OriginsAddon = False # Do not use None, since it can mean that the origin cannot be detected.
	OriginsFixed = False # Do not use None, since it can mean that the origin cannot be detected.
	OriginsGaia = None

	PowerPowerdown = 'powerdown'		# Power down the system.
	PowerShutdown = 'shutdown'			# Default shutdown action defined in system settings.
	PowerReboot = 'reboot'				# Cold reboot the system (power cycle).
	PowerReset = 'reset'				# Reset the system (same as reboot).
	PowerRestart = 'restart'			# Restart Kodi (only implemented under Windows and Linux).
	PowerSuspend = 'suspend'			# Suspend the system (S3/S1 depending on bios setting).
	PowerHibernate = 'hibernate'		# Hibernate the system (S4).
	PowerStandby = 'standby'			# Put playing device on standby via a CEC peripheral.
	PowerMinimize = 'minimize'			# Minimize Kodi.
	PowerQuit = 'quit'					# Quit Kodi.
	PowerScreensaver = 'screensaver'	# Start the screensaver.
	PowerReload = 'reload'				# Reload the Kodi user profile (reloads profile, addons, addon.xml, settings, and restarts services).
	PowerRefresh = 'refresh'			# Refresh the Kodi skin (reloads changes to the skin XML).
	PowerRelaunch = 'relaunch'			# Relaunch the Gaia addon.

	Navigation = []
	NavigationParameter = 'navigation'

	Monitor = None
	Arguments = None

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		System.OriginsAddon = False
		System.OriginsFixed = False
		System.OriginsGaia = None

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def arguments(self, index = None):
		if index is None: return System.Arguments
		else: return System.Arguments[index]

	@classmethod
	def argumentsInitialize(self):
		# Copy the args, since when using <reuselanguageinvoker>, the array might change.
		System.Arguments = Tools.copy(sys.argv)

	@classmethod
	def handle(self):
		# This will fail if Gaia is called externally, eg through a widget that opens the Gaia context menu.
		try: return int(self.arguments(1))
		except: return None

	@classmethod
	def handleValid(self):
		handle = self.handle()
		return not handle is None and handle > 0

	@classmethod
	def query(self, parse = False):
		try:
			result = self.arguments(2).lstrip('?')
			if parse:
				from lib.modules.network import Networker
				result = Networker.linkDecode(result)
			return result
		except: return None

	@classmethod
	def queryRedo(self, parameters = None, loader = False, wait = False):
		if loader:
			from lib.modules.interface import Loader
			Loader.show()
		query = self.query(parse = True)
		if parameters: query.update(parameters)
		return self.executePlugin(parameters = query, wait = False)

	# If the developers option is enabled.
	@classmethod
	def developer(self, code = True, version = True):
		return (code and self.developerCode() == Converter.base64From('b3BlbnNlc2FtZQ==')) or (version and self.developerVersion())

	@classmethod
	def developerCode(self):
		return Settings.getString('general.developer.code')

	@classmethod
	def developerVersion(self):
		return self.versionDeveloper()

	@classmethod
	def developersCode(self):
		return Converter.base64From('b3BlbnNlc2FtZQ==')

	@classmethod
	def obfuscate(self, data, iterations = 3, inverse = True):
		if inverse:
			for i in range(iterations):
				data = Converter.base64From(data)[::-1]
		else:
			for i in range(iterations):
				data = Converter.base64To(data[::-1])
		return Converter.unicode(data)

	# Simulated restart of the addon.
	@classmethod
	def restart(self, reset = False, sleep = True):
		from lib.modules.interface import Loader

		self.restartStart()
		Loader.hide() # Very important. Otherwise the ActivateWindow() calls do not work, since probably the loader window interferes somehow.

		self.quit(reset = reset)
		if sleep: Time.sleep(0.2)

		# RunAddon does not seem to reload the container (that will execute _launch()) if executed from Gaia's root menu.
		#System.execute('RunAddon(%s)' % System.GaiaAddon)
		System.execute('ActivateWindow(videos,%s)' % System.command(action = None, optimize = False))

	@classmethod
	def restartBusy(self):
		try: return int(self.windowPropertyGet(property = System.PropertyRestart))
		except: return False

	@classmethod
	def restartStart(self):
		self.windowPropertySet(property = System.PropertyRestart, value = 1)

	@classmethod
	def restartFinish(self):
		self.windowPropertySet(property = System.PropertyRestart, value = 0)

	@classmethod
	def quit(self, reset = False):
		if reset:
			self.launchDataClear(full = True)
			Settings.interpreterReset()
		System.execute('Continer.Update(invalid,replace)')
		self.home()
		System.execute('Continer.Update(invalid,replace)')

	@classmethod
	def exit(self, log = True):
		if log: Logger.log('Aborting the execution of the Gaia addon.', type = Logger.TypeFatal)
		Pool.join() # Wait for threads to finish.
		try: sys.exit()
		except: pass

	@classmethod
	def aborted(self):
		try:
			return System.Monitor.abortRequested()
		except:
			System.Monitor = xbmc.Monitor()
			return System.Monitor.abortRequested()

	@classmethod
	def abortWait(self, timeout = None, exit = True):
		try:
			aborted = System.Monitor.waitForAbort(timeout)
		except:
			System.Monitor = xbmc.Monitor()
			aborted = System.Monitor.waitForAbort(timeout)
		if aborted and exit: self.exit()
		return aborted

	# This function reloads the Kodi user profile, reloading addons, addon.xml, settings, and restarting services.
	@classmethod
	def reload(self, message = False, loader = None):
		reload = True

		interactive = bool(message)
		loader = loader is True or interactive
		if interactive:
			from lib.modules.interface import Dialog, Translation, Format
			if Tools.isNumber(message): message = Translation.string(message)
			if Tools.isString(message): message += Format.newline()
			else: message = ''
			message += Translation.string(33132)
			reload = not Dialog.options(title = 33131, message = message, labelConfirm = 35015, labelDeny = 33149)

		if reload:
			from lib.modules.interface import Loader
			if loader:
				Loader.show()
				Time.sleep(0.5) # Wait, otherwise Kodi freezes while reloading the profile before the Loader is visible.

			# Waiting does not work with self.execute().
			# When using the RPC, waiting is possible. But if the 'wait' parameter is passed to Profiles.LoadProfile, the call fails complaining about too many parameters in the call.
			self.execute('LoadProfile(%s)' % xbmc.getInfoLabel('system.profilename'))

	@classmethod
	def visible(self, item):
		return xbmc.getCondVisibility(item)

	@classmethod
	def redirect(self, parameters):
		# For Gaia Eminence.
		# Makes sure that when directly opening a submenu in Gaia from the home menu, and the user navigates back (hitting the back key, not clicking on the back list item), the home screen is shown again.
		redirect = parameters.get('redirect')
		if redirect:
			System.launch()
			try: del parameters['redirect']
			except: pass
			System.window(action = redirect, parameters = parameters, activate = True, update = False, refresh = False)
			return 'redirect' # Dummy action which prevents any of code in addon.py to execute.
		return None

	@classmethod
	def navigation(self, name = None, more = False):
		if name:
			# Ignore the "More" menu entry, but only if it is
			# Eg allow: Movies - Discover - Years - More
			# Eg disallow: Movies - Discover - Years - More - 1925
			if not more and System.Navigation and System.Navigation[-1] == self.addon().getLocalizedString(33432): del System.Navigation[-1]
			return System.Navigation + [name]
		return System.Navigation

	@classmethod
	def navigationParameter(self, navigation = None, name = None):
		return System.NavigationParameter + '=' + self.navigationEncode(navigation = navigation, name = name)

	@classmethod
	def navigationEncode(self, navigation = None, name = None, link = True):
		from lib.modules.network import Networker
		if navigation is None: navigation = self.navigation(name = name)
		navigation = ','.join(navigation)
		return Networker.linkQuote(navigation) if link else navigation

	@classmethod
	def navigationDecode(self, navigation):
		from lib.modules.network import Networker
		return Networker.linkUnquote(navigation).split(',')

	@classmethod
	def navigationDescription(self, name = None):
		from lib.modules.interface import Format
		return Format.iconJoin(self.navigation(name = name))

	@classmethod
	def navigationResolve(self, action = None, navigation = None, parameters = None, initialize = True):
		# If the context menu is launched, the handle is -1 and pluginPropertySet() does not work.
		# Attempt to use invalid handle -1
		handle = self.handle()
		if handle is None or handle < 0: return None

		# For Gaia Eminence.
		addon = self.addon()

		if navigation is None and parameters: navigation = parameters.get(System.NavigationParameter)

		# When the skin directly launches a submenu without opening the main menu first.
		if not navigation:
			from lib.meta.menu import MetaMenu

			if action == MetaMenu.ContentSearch:
				navigation = 32010
			elif action == MetaMenu.Action:
				content = parameters.get(MetaMenu.ParameterContent)
				if content:
					if content == MetaMenu.ContentSearch: navigation = 32010
					elif content == MetaMenu.ContentQuick: navigation = 35550
					elif content == MetaMenu.ContentProgress: navigation = 32037
					elif content == MetaMenu.ContentArrival: navigation = 33490
					elif content == MetaMenu.ContentFavorite: navigation = 33000

			if not navigation:
				media = parameters.get('media')
				if media:
					if Media.isFilm(media): navigation = 32001
					elif Media.isShow(media): navigation = 32002

			if not navigation: navigation = 35639
			navigation = [addon.getLocalizedString(navigation)]

		if navigation:
			if navigation and Tools.isString(navigation): navigation = self.navigationDecode(navigation = navigation)
			if navigation:
				if len(navigation) > 1 and navigation[0] == addon.getLocalizedString(35639): navigation.pop(0)
				self.pluginPropertySet(property = 'GaiaNavigationCategory', value = navigation[0])
				subnavigation = navigation[1:]
				self.pluginPropertySet(property = 'GaiaNavigationSubcategory', value = '  •  '.join(subnavigation) if subnavigation else addon.getLocalizedString(33102))
		elif action is None or action == 'home':
			self.pluginPropertySet(property = 'GaiaNavigationCategory', value = 'Gaia')
			self.pluginPropertySet(property = 'GaiaNavigationSubcategory', value = addon.getLocalizedString(33102))

		if navigation and self.originGaia():
			media = ''
			navigationType = navigation[0]
			if navigationType:
				if navigationType == addon.getLocalizedString(32001): media = Media.Movie
				elif navigationType == addon.getLocalizedString(32002): media = Media.Show
			self.windowPropertySet(property = 'GaiaNavigationType', value = media)

		if initialize: System.Navigation = navigation

		return navigation

	@classmethod
	def versionKodi(self, full = False):
		if full:
			if System.KodiVersionFull is None:
				System.KodiVersionFull = self.infoLabel('System.BuildVersion')
			return System.KodiVersionFull
		else:
			if System.KodiVersion is None:
				try: System.KodiVersion = float(re.search('^(\d+\.?\d+)', self.infoLabel('System.BuildVersion')).group(0))
				except: pass
			return System.KodiVersion

	@classmethod
	def versionKodiMinimum(self, version):
		return self.versionKodi(full = False) >= version

	@classmethod
	def versionKodiMaximum(self, version):
		return self.versionKodi(full = False) <= version

	@classmethod
	def home(self):
		System.execute('ActivateWindow(Home)')

	@classmethod
	def pluginPropertySet(self, property, value, handle = None):
		return xbmcplugin.setProperty(self.handle() if handle is None else handle, property, str(value))

	@classmethod
	def pluginResolvedSet(self, link = None, item = None, success = True, dummy = True, playable = True, handle = None):
		if item is None:
			if link is None:
				if dummy:
					link = self.command(action = 'dummy', parameters = {'time' : Time.timestamp()})
				else:
					try: link = self.arguments(0) + self.arguments(2)
					except: return False
			from lib.modules.interface import Directory
			item = Directory().item(path = link)
			item.setProperty('IsPlayable', 'true' if playable else 'false')

		if handle is None: handle = self.handle()
		if handle and handle >= 0:
			xbmcplugin.setResolvedUrl(handle, success, item)
			return True

		return False

	@classmethod
	def windowPropertyGet(self, property, id = 10000):
		return xbmcgui.Window(id).getProperty(property)

	@classmethod
	def windowPropertySet(self, property, value, id = 10000):
		return xbmcgui.Window(id).setProperty(property, str(value))

	@classmethod
	def windowPropertyClear(self, property, id = 10000):
		return xbmcgui.Window(id).clearProperty(property)

	@classmethod
	def globalLock(self, id = ''):
		self.windowPropertySet(property = System.PropertyLock + id, value = 1)

	@classmethod
	def globalUnlock(self, id = ''):
		self.windowPropertySet(property = System.PropertyLock + id, value = 0)

	@classmethod
	def globalLocked(self, id = ''):
		return self.windowPropertyGet(property = System.PropertyLock + id) == '1'

	@classmethod
	def path(self, id = GaiaAddon):
		try: addon = xbmcaddon.Addon(id)
		except: addon = None
		if addon is None: return None
		else: return File.translatePath(addon.getAddonInfo('path'))

	@classmethod
	def pathBinaries(self):
		return self.path(System.GaiaBinaries)

	@classmethod
	def pathExternals(self):
		return self.path(System.GaiaExternals)

	@classmethod
	def pathIcons(self):
		return self.path(System.GaiaIcons)

	@classmethod
	def pathResources(self):
		return self.path(System.GaiaResources)

	@classmethod
	def pathMetadata(self):
		return self.path(System.GaiaMetadata)

	@classmethod
	def pathSkins(self):
		return self.path(System.GaiaSkins)

	# OS user home directory
	@classmethod
	def pathHome(self):
		try: return os.path.expanduser('~')
		except: return None

	@classmethod
	def pathProviders(self, provider = None, translate = True):
		path = File.joinPath(self.profile(translate = translate), 'Providers')
		if provider: path = File.joinPath(path, provider)
		return path

	@classmethod
	def plugin(self, id = GaiaAddon):
		return System.PluginPrefix + str(id)

	# Detect the origin based on the container info.
	@classmethod
	def origin(self, extended = True, quick = True):
		try:
			# If called multiple times within a single execution, this can make things slower.
			# Detect once and reuse the value.
			if System.OriginsAddon is False:
				# When originGaia() is called from player.py, sometimes in sporadic cases, the info label returns "".
				# This makes the stream window not reload in a few cases.
				# Waiting and retying then typically return the addon path.

				# Set wait to a low number (percentage of the normal infoLabel() timeout).
				# Otherwise, this makes the addon take long to open if launched from Addons -> Video Addons -> Gaia, since there is no PluginName.
				# This was previously 2.5 secs each of the infoLabel() calls below (50 iterations of 0.05secs each).
				# If this new adaptation is too short for player.py, increase again.
				wait1 = 0.3 if quick else 1.0 # 0.45 secs and 1.5secs (wait1*30 iterations of 0.05secs each)
				wait2 = 0.3 # 0.45 secs (wait2*30 iterations of 0.05secs each)

				origin = self.infoLabel('Container.PluginName', empty = True, wait = wait1)

				# If Gaia is launched from the addon menu, PluginName is None.
				if not origin and extended:
					if not self.query() and self.infoLabel('Container.FolderPath', empty = True, wait = wait2) == 'addons://sources/video':
						origin = self.plugin()

				System.OriginsAddon = origin
		except: Logger.error()
		return System.OriginsAddon

	# Determine the origin based on the fixed parameters passed in.
	@classmethod
	def originFixed(self):
		try:
			if System.OriginsFixed is False:
				query = self.query(parse = True)
				System.OriginsFixed = query.get(System.OriginsParameter) if query else None
		except: Logger.error()
		return System.OriginsFixed

	@classmethod
	def originGaia(self, strict = True, quick = True):
		if strict:
			if System.OriginsGaia is None:
				if strict and self.originFixed() == System.OriginGaia: System.OriginsGaia = True
				if System.OriginsGaia is None: System.OriginsGaia = self.originIs(origin = self.origin(quick = quick), addon = System.GaiaAddon)
			return System.OriginsGaia
		else:
			return self.originIs(origin = self.origin(), addon = System.GaiaAddon)

	@classmethod
	def originAddon(self, strict = True, quick = True, gaia = True):
		if strict and self.originFixed() == System.OriginAddon: return True
		origin = self.origin(quick = quick)
		if not gaia and self.originIs(origin = origin, addon = System.GaiaAddon): return False
		else: return origin and Tools.stringRemovePrefix(origin, System.PluginPrefix).startswith('plugin.')

	@classmethod
	def originExternal(self, strict = True, quick = True):
		if strict and self.originFixed() == System.OriginExternal: return True
		origin = self.origin(quick = quick)
		if not origin: return True # Widgets return None.
		else: return not self.originIs(origin = origin, addon = System.GaiaAddon)

	@classmethod
	def originWidget(self, strict = True, quick = True):
		# Note that widgets (and other external addons) can use the URL created by Gaia, which already has an "origin" parameter.
		# So a wdiget might have "origin=gaia".
		# Only check if originFixed() is postivley matched. If it contains any other origin parameter, do not return False, but use other means of detection.
		if strict and self.originFixed() == System.OriginWidget: return True
		return not self.origin(quick = quick)

	@classmethod
	def originPlaylist(self):
		return self.originFixed() == System.OriginPlaylist

	@classmethod
	def originLibrary(self):
		return self.originFixed() == System.OriginLibrary

	@classmethod
	def originIs(self, origin, addon):
		if origin: return Tools.stringRemovePrefix(origin, System.PluginPrefix) == addon
		else: return origin == addon

	@classmethod
	def originSet(self, origin = True, command = None, parameters = None):
		if origin is True: origin = System.OriginGaia if self.originGaia() else None
		if parameters:
			if origin: parameters[System.OriginsParameter] = origin
			return parameters
		elif command:
			if origin: command += '&%s=%s' % (System.OriginsParameter, origin)
			return command

	@classmethod
	def originMenu(self):
		return System.visible('Window.IsActive(videos)')

	# The container ID that called the addon URL.
	# Might not always be available, but should be available from widgets.
	# Sometimes it does not return an ID if the container is still updating. Wait some time.
	@classmethod
	def originContainer(self, wait = True):
		try:
			id = System.infoLabel('System.CurrentControlID', empty = True, wait = wait)
			if id: id = int(id)
			return id
		except: return None

	# action: None = selection from dialog, Specific = execute a specific action.
	@classmethod
	def power(self, action = True, proper = True, level = 1, execute = True, warning = True, notification = True, sound = True, wait = False):
		from lib.modules.interface import Translation, Format, Dialog, Loader
		from lib.modules.convert import ConverterDuration
		from lib.modules.interface import Player
		from lib.modules.concurrency import Pool

		actions = [
			{'action' : System.PowerPowerdown,		'name' : 36404,	'label' : 36462,	'level' : 0,	'command' : 'Powerdown'},
			{'action' : System.PowerShutdown,		'name' : 36405,	'label' : 36463,	'level' : 1,	'command' : 'ShutDown'},
			{'action' : System.PowerReboot,			'name' : 36406,	'label' : 36464,	'level' : 0,	'command' : 'Reboot'},
			{'action' : System.PowerReset,			'name' : 35479,	'label' : 36465,	'level' : 3,	'command' : 'Reset'},
			{'action' : System.PowerSuspend,		'name' : 36407,	'label' : 36466,	'level' : 0,	'command' : 'Suspend'},
			{'action' : System.PowerHibernate,		'name' : 36408,	'label' : 36467,	'level' : 0,	'command' : 'Hibernate'},
			{'action' : System.PowerStandby,		'name' : 36460,	'label' : 36468,	'level' : 0,	'command' : 'CECStandby'},
			{'action' : System.PowerQuit,			'name' : 36410,	'label' : 36471,	'level' : 0,	'command' : 'Quit'},
			{'action' : System.PowerRestart,		'name' : 32501,	'label' : 36469,	'level' : 1,	'command' : 'RestartApp'},
			{'action' : System.PowerMinimize,		'name' : 36409,	'label' : 36470,	'level' : 0,	'command' : 'Minimize'},
			{'action' : System.PowerScreensaver,	'name' : 36411,	'label' : 36472,	'level' : 0,	'command' : 'ActivateScreensaver'},
			{'action' : System.PowerReload,			'name' : 33149,	'label' : 32067,	'level' : 2,	'command' : self.reload},
			{'action' : System.PowerRefresh,		'name' : 32072,	'label' : 32066,	'level' : 2,	'command' : 'ReloadSkin()'},
			{'action' : System.PowerRelaunch,		'name' : 32068,	'label' : 32069,	'level' : 2,	'command' : lambda : self.restart(reset = True)},
		]

		# Format label.
		for i in actions:
			format = Translation.string(i['label']).split(' ')
			i['format'] = Format.fontBold(' '.join(format[:-1])) + ' ' + format[-1]

		# Return only data without executing the action.
		if not execute: return [i for i in actions if i['level'] <= level]

		# Show a selection dialog.
		if not action:
			items = [i for i in actions if i['level'] <= level]
			choice = Dialog.select(title = 36419, items = [i['format'] for i in items])
			if choice is None or choice < 0: return False
			action = items[choice]['action']

		# Retrieve the action data.
		data = None
		for i in actions:
			if i['action'] == action:
				data = i
				break
		if not data: return False
		action = data

		def _exit(delay):
			# Stop playback and let Trakt history and progress sync first.
			player = Player()
			playback = player.isPlayback()
			if playback:
				player.stop()
				Time.sleep(delay)
			else:
				Time.sleep(delay / 4.0)

		def _power(action, warning, notification, sound):
			timeout = 10
			delay = 15
			choice = True
			thread = None
			label = action['label']

			thread = Pool.thread(target = _exit, kwargs = {'delay' : delay}, start = True)
			if warning:
				message = ConverterDuration(value = timeout, unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatWordOptimal)
				message = Regex.replace(data = message, expression = '(\d+)', replacement = r'[B]\1[/B]', group = None, all = True)
				message = Translation.string(36457) % (Format.fontBold(label), message)
				choice = not Dialog.option(title = 36419, message = message, labelConfirm = 33743, labelDeny = action['name'], default = Dialog.ChoiceYes, timeout = timeout * 1000)

			if choice:
				Loader.show()
				if sound: Sound.executePowerStart()
				if notification: Dialog.notification(title = 36419, message = Translation.string(36420) % Format.fontBold(label), icon = Dialog.IconWarning, time = delay * 1000, sound = False) # Play its own sound here.
				thread.join()
				Time.sleep(1)
				_execute(action = action, sound = sound, direct = False)

		def _execute(action, sound, direct):
			if sound:
				if direct and Sound.executePowerStart(): sound = False
				if sound and Sound.executePowerFinish(): Time.sleep(2)
			command = action['command']
			if Tools.isString(command): self.execute(command = command)
			else: command()
			Loader.show() # Closed by self.restart().
			Time.sleep(0.5)
			Dialog.closeNotification()
			Loader.hide()

		if not proper or action['action'] in [System.PowerMinimize, System.PowerScreensaver]: _execute(action = action, sound = sound, direct = True)
		else: Pool.thread(target = _power, kwargs = {'action' : action, 'warning' : warning, 'notification' : notification, 'sound' : sound}, start = True, join = wait)
		return action['action']

	@classmethod
	def command(self, action = None, parameters = None, encoded = None, query = None, id = GaiaAddon, origin = None, optimize = True):
		'''
			The URL encoding and quote functions in urllib are very slow.
			This is not an issue if we only have to encode a few small commands.
			But if we eg create the stream list whith 100s or 1000s of streams all containing metadata and stream data, it can take seconds to encode.
			There are no other pure Python libraries that are faster than urllib.
			There are libraries that claim to be a lot faster than urllib, but they rely on C or Rust code, and there are no precompiled Python wheels for ARM architectures.
				https://github.com/acg/python-percentcoding
				https://github.com/blue-yonder/urlquote
			Base64 is about 5 - 6 times faster than URL encoding, and actually has a slightly lower output string size.
		'''

		if query is None:
			# We do this to force an order of the parameters.
			# This is useful for a non-optimized/encoded URL, making it easier to read by users and utilize and manipulate in skin shortcuts.
			from lib.modules.external import Importer
			data = Importer.moduleOrderedDict()()
			if not action is None: data['action'] = action
			if parameters:
				if 'media' in parameters: data['media'] = parameters['media']
				if 'link' in parameters: data['link'] = parameters['link']
				data.update(parameters)
				if 'action' in parameters and not action is None: data['action'] = action # In case "action" was replaced by the value in parameters.
			parameters = data

			# This is to indicate wether or not the command is executed from within Gaia or from an external addon or widget.
			# When we add a Gaia list to an external widget, and then click an item in the widget (eg: Show Arrivals with submenus), calling System.originGaia() will always be true.
			# It seems the only way to make sure we can detect the origin correctly, is to add this parameter when we select the path of the widget from the Skin settings.
			# When selecting the list from the Skin settings, the origin is correctly None.
			# Used from addon.py -> episodesSubmenu.
			if origin is None: origin = False if parameters.get(System.OriginsParameter) else True
			if origin: parameters = self.originSet(origin = origin, parameters = parameters)

			# Just makes it easier to ready without the URL-encoded JSON brackets.
			if System.NavigationParameter in parameters and Tools.isArray(parameters[System.NavigationParameter]):
				parameters[System.NavigationParameter] = self.navigationEncode(navigation = parameters[System.NavigationParameter], link = False)

			# Make it even faster by encoding the entire parameters.
			# Besides being faster, we can also keep data types without having to convert them (eg bools or None).
			'''query = []
			for key, value in parameters.items():
				#CommandBase64 = 'base64:'
				if Tools.isStructure(value): value = System.CommandBase64 + Converter.base64To(Converter.jsonTo(value))
				else: value = Converter.quoteTo(str(value))
				if not value is None: query.append(str(key) + '=' + value)
			query = '&'.join(query)'''

			# Only do this with Gaia commands.
			# Otherwise call to eg ResolveUrl authentication fails if base64 encoded.
			if optimize and id == System.GaiaAddon:
				data = [self.commandEncode(parameters)]
				if encoded:
					if Tools.isArray(encoded): data.extend(encoded)
					else: data.append(encoded)
				parameters = {'data' : data}

			from lib.modules.network import Networker
			query = Networker.linkEncode(self.commandFormat(parameters))

		return '%s/?%s' % (self.plugin(id = id), query)

	@classmethod
	def commandEncode(self, parameters):
		return Converter.base64To(Converter.jsonTo(parameters))

	@classmethod
	def commandDecode(self, data):
		return Converter.jsonFrom(Converter.base64From(data))

	@classmethod
	def commandFormat(self, parameters):
		# NB: Encode arrays as JSON objects.
		# Kodi has problems with URL arrays ("val[]=1&val[]=2", or "val=1&val=2" for the Python version of URL arrays).
		# Kodi always just picks 1 of the parameters and does not interpret it as an array ("val=2").
		# This ONLY happens if the command URL is used in a Kodi menu/directory.
		# When the URL is called from System.executePlugin() or from a custom window, this does not happen.
		# This is also not a problem if we base64 encode the parameters in the URL, only if we use a raw unencoded URL.
		from lib.modules.network import Networker
		for key, value in parameters.items():
			if Tools.isBoolean(value): parameters[key] = Converter.boolean(value, string = True).lower()
			elif Tools.isStructure(value): parameters[key] = Converter.jsonTo(value)
		return parameters

	@classmethod
	def commandUnformat(self, parameters):
		for key, value in parameters.items():
			if value and Tools.isString(value):
				lower = value.lower()
				if lower == 'true' or lower == 'false': parameters[key] = Converter.boolean(value)
				elif lower.startswith('[') or lower.startswith('{'): parameters[key] = Converter.jsonFrom(value)
		return parameters

	@classmethod
	def commandResolve(self, command = None, initialize = False):
		if initialize: self.argumentsInitialize()

		from lib.modules.network import Networker
		if command is None: command = self.arguments(2)

		parameters = dict(Networker.linkDecode(command.replace(self.plugin() + '/', '').replace('?', '')))
		parameters = self.commandUnformat(parameters)

		if 'data' in parameters:
			if Tools.isArray(parameters['data']):
				data = {}
				for i in parameters['data']:
					data.update(self.commandDecode(i))
				parameters = data
			else:
				parameters = self.commandDecode(parameters['data'])

		return parameters

	@classmethod
	def commandPlugin(self, action = None, parameters = None, command = None, id = GaiaAddon, optimize = True, call = True):
		if id is None: id = System.GaiaAddon
		if command is None: command = self.command(action = action, parameters = parameters, id = id, optimize = optimize)
		if call: command = 'RunPlugin(%s)' % command
		return command

	@classmethod
	def commandContainer(self, action = None, parameters = None, command = None, id = GaiaAddon, optimize = True, call = True, replace = False):
		if id is None: id = System.GaiaAddon
		if command is None: command = self.command(action = action, parameters = parameters, id = id, optimize = optimize)
		if call: command = 'Container.Update(%s%s)' % (command, ',replace' if replace else '')
		return command

	@classmethod
	def commandWindow(self, action = None, parameters = None, command = None, id = GaiaAddon, optimize = True, call = True, parent = None):
		if id is None: id = System.GaiaAddon
		if command is None: command = self.command(action = action, parameters = parameters, id = id, optimize = optimize)
		if call: command = 'ActivateWindow(videos,%s%s)' % (command, (',' + parent) if parent else '')
		return command

	@classmethod
	def commandIsMenu(self):
		parameters = System.commandResolve()
		if not parameters: return False
		action = parameters.get('action')
		return action and (action.startswith('movie') or action.startswith('show') or action.startswith('season') or action.startswith('episode'))

	@classmethod
	def commandIsScrape(self):
		parameters = System.commandResolve()
		if not parameters: return False
		action = parameters.get('action')
		return action and 'scrape' in action

	@classmethod
	def addon(self, id = GaiaAddon):
		try: return xbmcaddon.Addon(id if id else System.GaiaAddon)
		except: return None # Not installed/enabled.

	@classmethod
	def info(self, value, id = GaiaAddon):
		return self.addon(id = id).getAddonInfo(Converter.unicode(value))

	@classmethod
	def id(self, id = GaiaAddon):
		return self.addon(id = id).getAddonInfo('id')

	@classmethod
	def name(self, id = GaiaAddon):
		return self.addon(id = id).getAddonInfo('name')

	@classmethod
	def author(self, id = GaiaAddon):
		return self.addon(id = id).getAddonInfo('author')

	@classmethod
	def profile(self, id = GaiaAddon, translate = True):
		profile = self.addon(id = id).getAddonInfo('profile')
		if translate: profile = File.translatePath(profile)
		return profile

	@classmethod
	def description(self, id = GaiaAddon):
		return self.addon(id = id).getAddonInfo('description')

	@classmethod
	def disclaimer(self, id = GaiaAddon):
		return self.addon(id = id).getAddonInfo('disclaimer')

	@classmethod
	def version(self, id = GaiaAddon):
		return self.addon(id = id).getAddonInfo('version')

	# Version Number:
	#	Format: AAABBBCCCR.XXX
	#		AAA: Major version
	#		BBB: Minor version
	#		CCC: Patch version
	#		R: Release version (1 = alpha, 2 = beta, 9 = stable)
	#		XXX: Alpha/beta version
	# EG: 6.54.32 -> 6054329.0
	# EG: 6.54.32~alpha -> 6054321.0
	# EG: 6.54.32~beta98 -> 6054322.098
	@classmethod
	def versionNumber(self, id = GaiaAddon, version = None):
		try:
			if version is None: version = self.version(id = id)

			try: subversion = version.split('~')[1]
			except: subversion = None

			try:
				try: version = version.split('~')[0]
				except: pass
				version = version.split('.')
			except: pass

			result = ['%03d' % int(i) for i in version]
			result = ''.join(result)

			if subversion:
				try: subresult = int(subversion.replace('alpha', '').replace('beta', ''))
				except: subresult = 0
				if 'alpha' in subversion: result += '1.'
				elif 'beta' in subversion: result += '2.'
				else: result += '3.'
				result += ('%03d' % subresult)
			else:
				result += '9.0'

			version = float(result)
		except: version = None
		return version if version else 0

	@classmethod
	def versionPrerelease(self, id = GaiaAddon, version = None):
		try:
			if version is None: version = self.version(id = id)
			for i in ['alpha', 'beta']:
				if i in version: return i
		except: pass
		return None

	@classmethod
	def versionMajor(self, id = GaiaAddon, version = None):
		try:
			if version is None: version = self.version(id = id)
			return int(str(version).split('.')[0])
		except: return 0

	@classmethod
	def versionMinor(self, id = GaiaAddon, version = None):
		try:
			if version is None: version = self.version(id = id)
			return int(str(version).split('.')[1])
		except: return 0

	@classmethod
	def versionPatch(self, id = GaiaAddon, version = None):
		try:
			if version is None: version = self.version(id = id)
			return int(str(version).split('.')[2])
		except: return 0

	@classmethod
	def versionDeveloper(self, id = GaiaAddon):
		return self.version(id = id) == '999.999.999'

	@classmethod
	def versionInfo(self, update = False):
		newFull = self.version()
		newNumber = self.versionNumber(version = newFull)
		newMajor = self.versionMajor(version = newFull)
		newMinor = self.versionMinor(version = newFull)
		newPatch = self.versionPatch(version = newFull)
		newPrerelease = self.versionPrerelease(version = newFull)

		oldFull = Settings.getString('internal.version')
		oldNumber = self.versionNumber(version = oldFull)
		oldMajor = self.versionMajor(version = oldFull)
		oldMinor = self.versionMinor(version = oldFull)
		oldPatch = self.versionPatch(version = oldFull)
		oldPrerelease = self.versionPrerelease(version = oldFull)

		change = (not newFull == oldFull)
		changeMajor = (not newMajor == oldMajor)
		changeMinor = (not newMinor == oldMinor) or changeMajor
		changePatch = (not newPatch == oldPatch) or changeMinor
		changePrerelease = (not newPrerelease == oldPrerelease)

		if update: Settings.set('internal.version', newFull)

		return {
			'new' : {
				'full' : newFull,
				'number' : newNumber,
				'major' : newMajor,
				'minor' : newMinor,
				'patch' : newPatch,
				'prerelease' : newPrerelease,
			},
			'old' : {
				'full' : oldFull,
				'number' : oldNumber,
				'major' : oldMajor,
				'minor' : oldMinor,
				'patch' : oldPatch,
				'prerelease' : oldPrerelease,
			},
			'change' : {
				'full' : change,
				'major' : changeMajor,
				'minor' : changeMinor,
				'patch' : changePatch,
				'prerelease' : changePrerelease,
			},
		}

	@classmethod
	def infoLabel(self, value, empty = False, wait = True):
		# Some values (eg: System.CpuUsage) will return "Busy" when called first. Wait for Kodi to load the value.
		if wait:
			counter = 0
			interations = 30 if empty else 100
			if Tools.isFloat(wait): interations = int(interations * wait)
			while True:
				result = xbmc.getInfoLabel(value)

				# NB: Some info labels can return an empty string.
				# Eg: Container.PluginName in origin() will return "" when the context menu is opened from a widget, causing the context menu to load very long.
				# Only wait if the label returns "busy", but not if the label is empty.
				#if result and not 'busy' in result.lower(): return result
				try:
					data = result.lower().strip()
					busy = data == 'busy'
					if not busy and empty: busy = data == ''
				except: busy = False
				if not busy: return result

				counter += 1
				if counter > interations: return None
				Time.sleep(0.05)
		else:
			return xbmc.getInfoLabel(value)

	@classmethod
	def infoLabelLoad(self, values = None):
		# Takes some time to retrieve.
		# If not, Kodi sometimes just returns "Busy" as the value.
		if values is None: values = ['System.CpuUsage', 'System.Memory(free)', 'System.Memory(total)', 'System.FreeSpace', 'System.TotalSpace', 'System.BuildVersion', 'System.BuildDate', 'System.Uptime']
		for value in values: self.infoLabel(value, wait = True)

	# Checks if an addon is installed.
	# deprecated: If False, ignore addons that are still installed from Kodi 18 or earlier, but are not supported in Kodi 19 anymore.
	# enabled: If True, the addon must be both installed and enabled.
	@classmethod
	def installed(self, id = GaiaAddon, native = False, deprecated = True, enabled = False):
		try:
			if native:
				return id == xbmcaddon.Addon(id).getAddonInfo('id')
			else:
				properties = ['installed']
				if not deprecated: properties.append('dependencies')
				if enabled: properties.append('enabled')
				result = System.executeJson(addon = id, method = 'Addons.GetAddonDetails', parameters = {'properties' : properties})['result']['addon']
				if result['installed'] and (not enabled or result['enabled']):
					if deprecated: return True
					oldPython = False
					for i in result['dependencies']:
						if i['addonid'] == 'xbmc.python':
							oldPython = int(i['minversion'].split('.')[0]) <= 2
							break
					return not oldPython
		except: pass
		return False

	@classmethod
	def addonDetails(self, id = GaiaAddon, properties = None):
		try:
			if not properties: properties = ['name', 'version', 'enabled', 'installed']
			return System.executeJson(addon = id, method = 'Addons.GetAddonDetails', parameters = {'properties' : properties})['result']['addon']
		except: pass
		return None

	# Checks if an addon is enabled.
	@classmethod
	def enabled(self, id = GaiaAddon, native = False):
		try:
			if native: return id == xbmcaddon.Addon(id).getAddonInfo('id')
			else: return System.executeJson(addon = id, method = 'Addons.GetAddonDetails', parameters = {'properties' : ['enabled']})['result']['addon']['enabled']
		except: pass
		return None

	@classmethod
	def execute(self, command, wait = False):
		return xbmc.executebuiltin(command, wait)

	@classmethod
	def executeScript(self, script, parameters = None, wait = False):
		command = 'RunScript(' + script
		if parameters:
			items = []
			if Tools.isDictionary(parameters):
				for key, value in parameters.items():
					items.append(str(key) + '=' + str(value))
			for item in items:
				command += ',' + str(item)
		command += ')'
		return self.execute(command = command, wait = wait)

	@classmethod
	def stopScript(self, script):
		return self.execute('StopScript(%s)' % script)

	@classmethod
	def executePlugin(self, action = None, parameters = None, command = None, id = GaiaAddon, optimize = True, wait = False):
		return self.execute(self.commandPlugin(id = id, action = action, parameters = parameters, command = command, optimize = optimize, call = True), wait = wait)

	@classmethod
	def executeContainer(self, action = None, parameters = None, command = None, replace = False, id = GaiaAddon, optimize = True, wait = False):
		return self.execute(self.commandContainer(id = id, action = action, parameters = parameters, command = command, replace = replace, optimize = optimize, call = True), wait = wait)

	@classmethod
	def executeWindow(self, action = None, parameters = None, command = None, parent = None, id = GaiaAddon, optimize = True, wait = False):
		return self.execute(self.commandWindow(id = id, action = action, parameters = parameters, command = command, parent = parent, optimize = optimize, call = True), wait = wait)

	# Either query OR all the other parameters.
	@classmethod
	def executeJson(self, query = None, method = None, parameters = None, version = '2.0', id = 1, addon = False, wait = None, decode = True):
		if query is None:
			if parameters is None: parameters = {}
			if addon is True: parameters['addonid'] = self.id()
			elif addon: parameters['addonid'] = addon
			if not wait is None: parameters['wait'] = wait
			query = {}
			query['jsonrpc'] = version
			query['id'] = id
			query['method'] = method
			query['params'] = parameters
			query = Converter.jsonTo(query)
		result = xbmc.executeJSONRPC(query)
		if decode: result = Converter.jsonFrom(result)
		return result

	@classmethod
	def executeClick(self, control, window = None):
		return self.execute('SendClick(%s%s)' % ((str(window) + ',') if window else '', str(control)))

	# sleep for n seconds. Sometimes causes the new window not to show (only in the background). Sleeping seems to solve the problem.
	@classmethod
	def window(self, action = None, parameters = {}, command = None, sleep = None, activate = True, update = True, refresh = False):
		result = True
		if command is None: command = self.command(action = action, parameters = parameters)
		if activate: result = System.execute('ActivateWindow(10025,%s,return)' % command) # When launched externally (eg: from shortcut widgets).
		if update: System.execute('Container.Update(%s)' % command)
		if refresh: System.execute('Container.Refresh')
		if sleep: Time.sleep(sleep)
		return result

	@classmethod
	def temporary(self, directory = None, file = None, gaia = True, make = True, clear = False):
		path = File.translatePath('special://temp/')
		if gaia: path = os.path.join(path, System.name().lower())
		if directory: path = os.path.join(path, directory)
		if clear: File.deleteDirectory(path, force = True)
		if make: File.makeDirectory(path)
		if file: path = os.path.join(path, file)
		return path

	@classmethod
	def temporaryRandom(self, directory = None, extension = 'dat', gaia = True, make = True, clear = False):
		if extension and not extension == '' and not extension.startswith('.'): extension = '.' + extension
		file = Hash.random() + extension
		path = self.temporary(directory = directory, file = file, gaia = gaia, make = make, clear = clear)
		while File.exists(path):
			file = Hash.random() + extension
			path = self.temporary(directory = directory, file = file, gaia = gaia, make = make, clear = clear)
		return path

	@classmethod
	def temporaryClear(self):
		return File.deleteDirectory(self.temporary(make = False))

	@classmethod
	def versionDataGet(self):
		try: return Converter.jsonFrom(self.windowPropertyGet(System.PropertyVersion))
		except: return None

	@classmethod
	def versionDataSet(self, data):
		self.windowPropertySet(System.PropertyVersion, Converter.jsonTo(data))

	@classmethod
	def versionDataClear(self):
		self.windowPropertyClear(System.PropertyVersion)

	@classmethod
	def _observe(self):
		xbmc.Monitor().waitForAbort()
		#os._exit(1)
		Syste.exit()

	@classmethod
	def observe(self):
		# Observes when Kodi closes and exits.
		# Reduces the chances the Kodi freezes on exit (might still take a few seconds).
		value = self.windowPropertyGet(System.PropertyObserve)
		if not value:
			self.windowPropertySet(System.PropertyObserve, str(Time.timestamp()))
			thread = Pool.thread(target = self._observe)
			thread.start()

	@classmethod
	def launchAddon(self, wait = True):
		from lib.modules.interface import Loader
		Loader.hide() # Must hide loader, otherwise for some weird reason RunAddon(...) does not work, at least from the widgets.

		id = self.id()
		System.execute('RunAddon(%s)' % id)
		if wait:
			for i in range(0, 150):
				if self.originGaia():
					try: items = int(self.infoLabel('Container.NumItems'))
					except: items = 0
					# Check NumItems, because the addon might have been launched, but the container/directory is still loading.
					# The container must be done loading, otherwise if a container update is executed right afterwards, the main menu items and the container update items might be mixed and displayed as the same list.
					if items > 0: break
				if id in str(self.infoLabel('Container.PluginName')): break
				Time.sleep(0.05)

	@classmethod
	def launchDataGet(self):
		try: return Converter.jsonFrom(self.windowPropertyGet(System.PropertyLaunch))
		except: return None

	@classmethod
	def launchDataSet(self, data):
		self.windowPropertySet(System.PropertyLaunch, Converter.jsonTo(data))

	@classmethod
	def launchDataClear(self, full = False):
		self.windowPropertyClear(System.PropertyLaunch)
		if full: self.windowPropertyClear(System.PropertyInitial)

	@classmethod
	def launchStatus(self, default = None):
		try: return int(self.windowPropertyGet(System.PropertyInitial))
		except: return default

	@classmethod
	def launchFinished(self, default = None, status = 3):
		return self.launchStatus(default = 0) >= status

	@classmethod
	def launch(self, hidden = None):
		if self.launchStatus(default = 0) >= 5: return False # More efficient than always calling self.launchDataGet().
		observe = False
		if hidden is None: hidden = not self.originGaia() # Do not show the launch window if requests come from widgets or any other addon that is not Gaia.

		data = self.launchDataGet()
		if not data and not hidden:
			Time.sleep(0.2) # Give some time for the hidden process to set self.launchDataSet() below.
			data = self.launchDataGet()

		if data:
			launched = self.launchStatus(default = 0)
			if launched == 3: self.windowPropertySet(System.PropertyInitial, '4')

			if self.originExternal():
				# If launched from an external plugin or widget, do not show the intro window if initialization was already completed.
				if launched: return False
			else:
				# This makes sure to always show the intro window when Gaia is opened for the first time, even if the initialization was already completed.
				if launched >= 5: return False
				elif launched >= 3: self.windowPropertySet(System.PropertyInitial, '5')
			observe = True
		else:
			# When using widgets, the call from the widget might execute before service.py has a chance to call this function.
			# In such a case, just return here, and give service.py (which does not have System.arguments()) a chance to finish.
			# Otherwise the entire initialization is executed twice (or even more times if there are more widgets).
			if hidden and System.arguments(): return False

			self.launchDataSet({'progress' : 0, 'status' : None})

		Pool.thread(target = self._launch, kwargs = {'hidden' : hidden, 'observe' : observe}, start = True)
		return True

	@classmethod
	def _launch(self, hidden = False, observe = False):
		if not hidden and self.launchStatus(default = 0) < 4: self.windowPropertySet(System.PropertyInitial, '1')

		# Sequential non-threaded and parallel threaded execution seems to take more or less the same time.
		# Sometimes sequential execution is actually faster.
		# Keep sequential execution for now, since it is probably more robust with less mututal exclusion problems.
		#self.tSequential = False
		self.tSequential = True

		self.tSplash = None
		self.tThreads = []
		self.tStatus = ['Initializing Gaia Launch']
		self.tProgress = 1
		self.tInitial = False
		self.tWizard = False

		def _launchObserve():
			if not hidden:
				try: self.tSplash.update(progress = 0, status = self.tStatus[0]) # Make sure to intialize to 0, otherwise (due to optimization), the progress is not initially updated in _launchObserve.
				except: pass
			while True:
				data = self.launchDataGet()
				if not data: break
				progress = data['progress']
				if not hidden:
					try: self.tSplash.update(progress = progress, status = data['status'])
					except:
						try: self.tSplash.update(progress = progress)
						except: pass
				if progress >= 98: break # 98, not 100.
				Time.sleep(0.5)
			_launchFinalize()

		def _launchProgress(increase = 0):
			if self.tSequential:
				try: status = self.tStatus[-1]
				except: pass
			else:
				index = 0
				for i in range(len(self.tThreads)):
					index = i
					if self.tThreads[i].is_alive(): break
				try: status = self.tStatus[index]
				except: status = self.tStatus[0]
			self.tProgress += increase
			self.launchDataSet({'progress' : self.tProgress, 'status' : status})
			if not hidden:
				try: self.tSplash.update(progress = self.tProgress, status = status)
				except:
					try: self.tSplash.update(progress = self.tProgress)
					except: pass

		def _launchExecute(_progress, _function, **kwargs):
			_launchProgress(_progress)
			if _function: _function(**kwargs)

		def _launchAdd(_progress, _status, _function, **kwargs):
			self.tStatus.append(_status)
			if self.tSequential:
				 _launchExecute(_progress, _function, **kwargs)
			else:
				thread = Pool.thread(target = _launchExecute, args = (_progress, _function), kwargs = kwargs)
				self.tThreads.append(thread)
				thread.start()

		def _launchFinalize():
			from lib.modules.interface import Splash, Loader

			if not hidden: Sound.executeLaunchFinish()

			version = self.versionDataGet()
			changed = False

			self.tProgress = max(99 if observe else 97, self.tProgress)
			self.tStatus = ['Launching Gaia']
			Settings.set('internal.initial.launch', True)
			if not hidden:
				try: self.tSplash.update(progress = self.tProgress, status = self.tStatus[0])
				except: pass
			if not hidden and self.launchStatus(default = 0) < 4: self.windowPropertySet(System.PropertyInitial, '2')

			Loader.enable()

			# Initial Launch
			if not hidden:
				from lib.modules.window import WindowWizard
				Time.sleep(1.5)
				if WindowWizard.show(initial = True, wait = True): changed = True

			self.tProgress = max(100 if observe else 98, self.tProgress)
			self.tStatus = ['Launching Gaia']
			if not hidden:
				try: self.tSplash.update(progress = self.tProgress, status = self.tStatus[0])
				except: pass

			_launchProgress() # Make sure 100% is written to the global variable for the observer.

			# System Details
			if not hidden: Pool.thread(target = Logger.system, kwargs = {'level' : Logger.LevelStandard}).start()

			# Updates
			Extension.versionCheck(wait = False)

			# Final
			if not hidden:
				Time.sleep(0.5) # Wait a little to not immediately pop up new dialogs.
				Splash.popupClose()

				Donations.popup(wait = True)

				# Announcement
				def _launchAnnouncement():
					Time.sleep(0.5)
					Announcements.show(wait = True, version = version['old']['number'] if (version['old']['number'] and not version['old']['number'] == version['new']['number']) else None)
					Announcements.storage(wait = True)
				Pool.thread(target = _launchAnnouncement).start()

			# Backup - Export
			if not hidden or changed:
				#gaiaremove - the if-statement check can be removed at a later stage. This is just to prevent backup imports between v6 and v7.
				if not(version['old']['number'] and version['old']['number'] < 70000000.0 and version['new']['number'] >= 70000000.0):
					if not self.tWizard:
						def _launchBackup():
							Time.sleep(2)
							Backup.automaticImport() # Check again, in case the initialization corrupted the settings.
							Backup.automaticExport()
						Pool.thread(target = _launchBackup, start = True)

			if self.launchStatus(default = 0) < 4: self.windowPropertySet(System.PropertyInitial, '3' if hidden else '5')

		self.tInitial = not Settings.getBoolean('internal.initial.launch')
		update = System.windowPropertyGet(System.PropertyUpdate)
		if update:
			update = bool(int(update))
		else:
			update = not Settings.getString('internal.version') == self.version()
			System.windowPropertySet(System.PropertyUpdate, str(int(update)))

		# Wizard
		from lib.modules.window import WindowWizard
		self.tWizard = Settings.getInteger(WindowWizard.PropertyInitial) == WindowWizard.StatusUncompleted

		# Splash
		from lib.modules.interface import Splash, Loader
		if not hidden:
			if not Splash.loader(): Loader.disable()
			self.tSplash = Splash.popup(time = None, wait = False, slogan = (self.tInitial or update), alternative = not(self.tInitial or update))
			Sound.executeLaunchStart()

		# Only observe progress if the actually code execution happens from service.py.
		if observe: return Pool.thread(target = _launchObserve, start = True)

		_launchProgress(2) # 2%

		if not self.tSequential:
			# For some reason when using threads that import the external Cloudflare library, the loading screen gets stuck.
			# Import before starting the threads.
			# Update: Is this still the case? Some other bugs in this function (that are fixed now) might have actually caused the problem.
			# Update 2: This was probably caused by the global XBMC window var that was set in the Cloudflare library for the user agents, which has now been removed.
			from lib.modules.cloudflare import Cloudflare
			Cloudflare.prepare()

		# Service
		self.tStatus = ['Initializing Launch Service']
		_launchProgress() # Update status label.
		from lib.modules.service import Service
		Service.launchGaia(process = True)
		_launchProgress(2) # 4%

		self.tStatus = ['Initializing Settings Cache']
		_launchProgress() # Update status label.
		Settings.cacheInitialize() # Load into cache in order to not get delays when calling functions below.
		_launchProgress(5) # 9%

		# Backup - Import
		self.tStatus = ['Initializing Settings Backup']
		_launchProgress() # Update status label.
		if Backup.automaticImport():
			Settings.cacheClear()
			Settings.cacheInitialize()
		_launchProgress(5) # 14%

		# Force Kodi to load the settings into memory.
		self.tStatus = ['Initializing Settings Cache']
		_launchProgress() # Update status label.
		Settings.set('internal.dummy', True)
		_launchProgress(5) # 19%

		# Version
		self.tStatus = ['Initializing Settings Version']
		_launchProgress() # Update status label.
		version = self.versionInfo(update = True)
		self.versionDataSet(version)
		_launchProgress(1) # 20%

		# Version changed.
		if not version['old']['number'] == version['new']['number']:
			Settings.interpreterSelect(notification = True, silent = True)

			# Clear the property for external libraries, to force redetecting them when a new version is installed.
			# The __gaia__ directories are gone after installing a new version, but the global properties still point to them.
			try:
				from lib.modules.external import Loader as ExternalLoader
				ExternalLoader.clear()
			except: Logger.error()

		# Do not do this if Gaia was installed from scratch without having and old version.
		if version['old']['number']:
			if version['old']['number'] < 70000000.0 and version['new']['number'] >= 70000000.0:
				# Clear everything between v6 and v7.
				#gaiaremove - this can be removed in a later version.
				directories, files = File.listDirectory(System.profile())
				for i in directories:
					if not 'download' in i.lower(): File.deleteDirectory(i)
				for i in files:
					File.delete(i)

		_launchProgress(4) # 25%

		self.tStatus = []

		# General Settings
		def _launchSettings():
			from lib.modules.view import View
			from lib.meta.tools import MetaTools
			try: Buffer.initialize()
			except: Logger.error()
			try: Timeout.initialize()
			except: Logger.error()
			try: Playlist.initialize()
			except: Logger.error()
			try: YouTube.qualityUpdate()
			except: Logger.error()
			try: View.settingsInitialize()
			except: Logger.error()
			try: MetaTools.settingsInitialize()
			except: Logger.error()
		_launchAdd(1, 'Initializing Settings Data', _launchSettings) # 26%

		# Compression
		def _launchCompression():
			# Wait up to 120 seconds for the benchmark to finish, otherwise just continue and let it finish in the background.
			# 120 seconds seems a lot, but this is only on the 1st run after a new installation. And the benchmarking has a sleep delay to wait for other CPU-intensive stuff to finish.
			# This allows the compression algorithm to be determined, before we might use them, like for metadata.db when we preload Arrivals/Progress menus.
			# The thread will wait for launch to finish before starting the benchmark.
			from lib.modules.compression import Compressor
			Pool.thread(target = Compressor.benchmark, kwargs = {'settings' : True, 'background' : True, 'wait' : 120, 'delay' : True}, start = True)
		_launchAdd(2, 'Initializing Compression Algorithms', _launchCompression) # 28%

		# Context Menu
		def _launchContext():
			from lib.modules.interface import Context
			Context.initialize()
		_launchAdd(3, 'Initializing Context Menu', _launchContext) # 31%

		# Promotions
		_launchAdd(1, 'Initializing New Promotions', Promotions.update, refresh = False) # 32%

		# Window
		if version['change']['full']:
			from lib.modules.window import Window
			_launchAdd(4, 'Initializing Custom Windows', Window.clean) # 36%
		else: _launchProgress(4)

		# Copy the select theme background as fanart to the root folder.
		# Ensures that the selected theme also shows outside the addon.
		# Requires first a Gaia restart (to replace the old fanart) and then a Kodi restart (to load the new fanart, since the old one was still in memory).
		def _launchImage():
			if not self.developerVersion():
				from lib.modules.theme import Theme
				fanartTo = File.joinPath(System.path(), 'resources', 'fanart.jpg')
				Thumbnail.delete(fanartTo) # Delete from cache.
				File.delete(fanartTo) # Delete old fanart.
				fanartFrom = Theme.fanart()
				if fanartFrom: File.copy(fanartFrom, fanartTo, overwrite = True)
		_launchAdd(1, 'Initializing Image Files', _launchImage) # 37%

		# Clear Temporary
		_launchAdd(1, 'Initializing Temporary Directory', System.temporaryClear) # 38%

		# Cache
		def _launchCache():
			from lib.modules.cache import Cache
			Cache.instance().expressionClean()
		_launchAdd(2, 'Initializing Expression Cache', _launchCache) # 40%

		# Externals
		def _launchExternals():
			from lib.modules.external import Importer, Psutil, Ujson

			# This occasionally removes semi-temporary directories for external libraries based on a probability.
			# These semi-temporary directories are too "permanent" to use the Kodi temp dir, since that one gets cleared every time Kodi is launched.
			# We need another directory that does not get cleared when Kodi is launched.
			# However, we still need to sometimes clear this semi-temporary directory, to remove possible problems, force re-retrieval of temp data, or remove code that might have changed with a Gaia update.
			Importer.update()

			threads = [
				Pool.thread(target = Psutil().moduleDetect, start = True),
				Pool.thread(target = Ujson().moduleDetect, start = True),
			]
			[thread.join() for thread in threads]
		_launchAdd(2, 'Initializing External Modules', _launchExternals) # 42%

		# Cloudflare
		def _launchCloudflare():
			from lib.modules.cloudflare import Cloudflare
			Cloudflare.initialize()
		_launchAdd(2, 'Initializing Cloudflare Bypasser', _launchCloudflare) # 44%

		# Elementum & Quasar
		_launchAdd(1, 'Initializing Elementum Handler', Elementum.connect, install = False, background = True, wait = False) # 45%
		_launchAdd(1, 'Initializing Quasar Handler', Quasar.connect, install = False, background = True, wait = False) # 46%

		# Premium
		from lib import debrid
		from lib.modules.orionoid import Orionoid
		_launchAdd(3, 'Initializing Orion Service', Orionoid().initialize) # 49%
		_launchAdd(1, 'Initializing Premiumize Service', debrid.premiumize.Core().initialize) # 50%
		_launchAdd(1, 'Initializing Premiumize Service', debrid.premiumize.Core().deleteLaunch) # 51%
		_launchAdd(1, 'Initializing OffCloud Service', debrid.offcloud.Core().deleteLaunch) # 52%
		_launchAdd(1, 'Initializing RealDebrid Service', debrid.realdebrid.Core().deleteLaunch) # 53%

		# External
		def _launchExternal():
			Resolver.authenticationCheck()
		_launchAdd(3, 'Initializing External Resolvers', _launchExternal) # 56%

		# Providers
		def _launchProviders():
			from lib.providers.core.manager import Manager
			Manager.check(progress = False, load = True, wait = True) # load = True: Load them here already. Should decrease the provider initializtion time on first scrape.
			if self.tInitial: Manager.optimizeInternal()
		_launchAdd(15, 'Initializing Provider Structure', _launchProviders) # 71%

		# Playback + Trakt
		def _launchPlayback():
			# This allows for faster navigation and updated metadata for Quick/Progress/Arrivals menus.
			# This does an internal Trakt refresh if necessary.
			# Do not do this the first time Gaia is launched after a fresh install. Do this at the end of the wizard.
			if not self.tWizard and not self.tInitial:
				from lib.modules.playback import Playback
				Playback.instance().launch(refresh = True, reload = True, delay = True, wait = None)
		_launchAdd(19, 'Initializing Playback History', _launchPlayback) # 90%

		# Clean Old Settings
		# Place this last, since it can take very long, and we do not want to show this status from the start until close to the end of the progress.
		# Do not do this here, but rather in service.py, since there is less file I/O interference than here.
		#_launchAdd(12, 'Cleaning Old Settings', Settings.clean) # 94%

		def _launchFinish():
			pass
		_launchAdd(1, 'Launching Gaia', _launchFinish) # 95%

		[thread.join() for thread in self.tThreads]
		_launchFinalize()

	@classmethod
	def launchAutomatic(self):
		self.execute('RunAddon(plugin.video.gaia)')

	@classmethod
	def _automaticIdentifier(self, identifier):
		identifier = identifier.upper()
		return ('#[%s]' % identifier, '#[/%s]' % identifier)

	# Checks if a command is in the Kodi startup script.
	@classmethod
	def automaticContains(self, identifier):
		if xbmcvfs.exists(System.StartupScript):
			identifiers = self._automaticIdentifier(identifier)
			file = xbmcvfs.File(System.StartupScript, 'r')
			data = file.read()
			file.close()
			if identifiers[0] in data and identifiers[1] in data:
				return True
		return False

	# Inserts a command into the Kodi startup script.
	@classmethod
	def automaticInsert(self, identifier, command):
		identifiers = self._automaticIdentifier(identifier)
		data = ''
		contains = False

		if xbmcvfs.exists(System.StartupScript):
			file = xbmcvfs.File(System.StartupScript, 'r')
			data = file.read()
			file.close()
			if identifiers[0] in data and identifiers[1] in data:
				contains = True

		if contains:
			return False
		else:
			id = self.id()
			module = identifier.lower() + 'xbmc'
			command = command.replace(System.PluginPrefix, '').replace(id, '')
			while command.startswith('/') or command.startswith('?'):
				command = command[1:]
			command = System.PluginPrefix + id + '/?' + command
			content = '%s\n%s\nimport xbmc as %s\nif %s.getCondVisibility("System.HasAddon(%s)") == 1: %s.executebuiltin("RunPlugin(%s)")\n%s' % (data, identifiers[0], module, module, id, module, command, identifiers[1])
			file = xbmcvfs.File(System.StartupScript, 'w')
			file.write(content)
			file.close()
			return True

	# Removes a command from the Kodi startup script.
	@classmethod
	def automaticRemove(self, identifier):
		identifiers = self._automaticIdentifier(identifier)
		data = ''
		contains = False
		indexStart = 0
		indexEnd = 0
		if xbmcvfs.exists(System.StartupScript):
			file = xbmcvfs.File(System.StartupScript, 'r')
			data = file.read()
			file.close()
			if data and not data == '':
				data += '\n'
				indexStart = data.find(identifiers[0])
				if indexStart >= 0:
					indexEnd = data.find(identifiers[1]) + len(identifiers[1])
					contains = True

		if contains:
			data = data[:indexStart] + data[indexEnd:]
			file = xbmcvfs.File(System.StartupScript, 'w')
			file.write(data)
			file.close()
			return True
		else:
			return False

	#	[
	#		['title' : 'Category 1', 'items' : [{'title' : 'Name 1', 'value' : 'Value 1', 'link' : True}, {'title' : 'Name 2', 'value' : 'Value 2'}]]
	#		['title' : 'Category 2', 'items' : [{'title' : 'Name 3', 'value' : 'Value 3', 'link' : False}, {'title' : 'Name 4', 'value' : 'Value 4'}]]
	#	]
	@classmethod
	def information(self, full = True):
		from lib.modules.interface import Dialog, Loader
		from lib.modules.concurrency import Pool
		Loader.show()

		items = []

		# Detect Hardware before Platform, since the Platform uses the hardware data.
		# Otherwise Hardware will use non-full cached data.
		hardware = Hardware.data(full = full, refresh = True)
		platform = Platform.data(refresh = True)
		concurrency = Pool.settingData()

		# Addon
		subitems = []
		if platform['addon']['id']: subitems.append({'title' : 'Id', 'value' : platform['addon']['id']})
		if platform['addon']['name']: subitems.append({'title' : 'Name', 'value' : platform['addon']['name']})
		if platform['addon']['author']: subitems.append({'title' : 'Author', 'value' : platform['addon']['author']})
		if platform['addon']['version']: subitems.append({'title' : 'Version', 'value' : platform['addon']['version']})
		items.append({'title' : 'Addon', 'items' : subitems})

		# Kodi
		subitems = []
		if platform['kodi']['name']: subitems.append({'title' : 'Name', 'value' : platform['kodi']['name']})
		if platform['kodi']['build']: subitems.append({'title' : 'Build', 'value' : platform['kodi']['build']})
		if platform['kodi']['version']['label']: subitems.append({'title' : 'Version', 'value' : platform['kodi']['version']['label']})
		if platform['kodi']['release']['label']: subitems.append({'title' : 'Release', 'value' : platform['kodi']['release']['label']})
		items.append({'title' : 'Kodi', 'items' : subitems})

		# Platform
		subitems = []
		if platform['family']['name']: subitems.append({'title' : 'Family', 'value' : platform['family']['name']})
		if platform['system']['name']: subitems.append({'title' : 'System', 'value' : platform['system']['name']})
		if platform['distribution']['name']: subitems.append({'title' : 'Distribution', 'value' : platform['distribution']['name']})
		if platform['version']['label']: subitems.append({'title' : 'Version', 'value' : platform['version']['label']})
		if platform['architecture']['label']: subitems.append({'title' : 'Architecture', 'value' : platform['architecture']['label']})
		if platform['environment']['label']: subitems.append({'title' : 'Environment', 'value' : platform['environment']['label']})
		items.append({'title' : 'Platform', 'items' : subitems})

		# Python
		subitems = []
		if platform['python']['version']: subitems.append({'title' : 'Version', 'value' : platform['python']['version']})
		if platform['python']['build']: subitems.append({'title' : 'Build', 'value' : platform['python']['build']})
		if platform['python']['implementation']: subitems.append({'title' : 'Implementation', 'value' : platform['python']['implementation']})
		if platform['python']['release']: subitems.append({'title' : 'Release', 'value' : platform['python']['release']})
		if platform['python']['concurrency']['label']: subitems.append({'title' : 'Concurrency', 'value' : platform['python']['concurrency']['label']})
		if platform['python']['interpreter']['label']: subitems.append({'title' : 'Interpreter', 'value' : platform['python']['interpreter']['label']})
		items.append({'title' : 'Python', 'items' : subitems})

		# Modules
		subitems = []
		if platform['module']['cloudscraper']: subitems.append({'title' : 'CloudScraper', 'value' : platform['module']['cloudscraper']})
		if platform['module']['psutil']: subitems.append({'title' : 'PSutil', 'value' : platform['module']['psutil']})
		if platform['module']['ujson']: subitems.append({'title' : 'UltraJSON', 'value' : platform['module']['ujson']})
		if platform['module']['image']: subitems.append({'title' : 'Image', 'value' : platform['module']['image']})
		items.append({'title' : 'Modules', 'items' : subitems})

		# Compression
		subitems = []
		if platform['compression']['global']: subitems.append({'title' : 'Global', 'value' : platform['compression']['global']})
		if platform['compression']['database']: subitems.append({'title' : 'Database', 'value' : platform['compression']['database']})
		if platform['compression']['algorithm']:
			 for algorithm in platform['compression']['algorithm']:
				 subitems.append({'title' : algorithm['label'], 'value' : algorithm['description']})
		items.append({'title' : 'Compression', 'items' : subitems})

		# Concurrency
		subitems = []
		if concurrency['label']: subitems.append({'title' : 'Level', 'value' : concurrency['label']})
		if concurrency['global']['label']: subitems.append({'title' : 'Global', 'value' : concurrency['global']['label']})
		if concurrency['metadata']['label']: subitems.append({'title' : 'Metadata', 'value' : concurrency['metadata']['label']})
		if concurrency['scrape']['label']: subitems.append({'title' : 'Scrape', 'value' : concurrency['scrape']['label']})
		if concurrency['binge']['label']: subitems.append({'title' : 'Binge', 'value' : concurrency['binge']['label']})
		if concurrency['connection']['label']: subitems.append({'title' : 'Connection', 'value' : concurrency['connection']['label']})
		if concurrency['mode']['label']: subitems.append({'title' : 'Mode', 'value' : concurrency['mode']['label']})
		items.append({'title' : 'Concurrency', 'items' : subitems})

		# Hardware
		subitems = []
		subitems.append({'title' : 'Processor', 'value' : hardware['processor']['label']})
		subitems.append({'title' : 'Memory', 'value' : hardware['memory']['label']})
		subitems.append({'title' : 'Storage', 'value' : hardware['storage']['label']})
		items.append({'title' : 'Hardware', 'items' : subitems})

		# Usage
		subitems = []
		subitems.append({'title' : 'Processor', 'value' : hardware['processor']['usage']['label']})
		subitems.append({'title' : 'Memory', 'value' : hardware['memory']['usage']['label']})
		subitems.append({'title' : 'Storage', 'value' : hardware['storage']['usage']['label']})
		items.append({'title' : 'Usage', 'items' : subitems})

		Loader.hide()
		return Dialog.information(title = 33467, items = items)

	@classmethod
	def manager(self):
		self.execute('ActivateWindow(systeminfo)')


class Eminence(object):

	PropertyWidget = 'GaiaWidgetReload'
	PropertyWidgetMovie = 'GaiaWidgetReloadMovie'
	PropertyWidgetShow = 'GaiaWidgetReloadShow'
	PropertyWidgetMixed = 'GaiaWidgetReloadMixed'

	@classmethod
	def widgetReload(self, media = None):
		# For Gaia Eminence skin.
		# Forces the widget in the Quick view to reload the list content.
		# Call this if the content in the list has changed (eg: item watched).

		time = str(Time.timestamp())
		properties = [Eminence.PropertyWidget]

		if media is None or Media.isFilm(media): properties.extend(Eminence.PropertyWidgetMovie)
		if media is None or Media.isSerie(media): properties.append(Eminence.PropertyWidgetShow)
		if media is None or Media.isMixed(media): properties.append(Eminence.PropertyWidgetMixed)

		for property in properties: System.windowPropertySet(property, time)

class Screen(object):

	Ratio4x3  =	'4x3'
	Ratio16x9 =	'16x9'
	Ratio20x9 =	'20x9'
	Ratios = (
		(Ratio4x3,  1.33333333),
		(Ratio16x9, 1.77777777),
		(Ratio20x9, 2.22222222),
	)

	@classmethod
	def dimension(self):
		return [self.width(), self.height()]

	@classmethod
	def width(self):
		try: return xbmcgui.getScreenWidth()
		except: return int(System.infoLabel('System.ScreenWidth')) # Older Kodi versions.

	@classmethod
	def height(self):
		try: return xbmcgui.getScreenHeight()
		except: return int(System.infoLabel('System.ScreenHeight')) # Older Kodi versions.

	@classmethod
	def ratio(self, closest = False):
		ratio = self.width() / float(self.height())
		if closest: ratio = Screen.Ratios[min(range(len(Screen.Ratios)), key = lambda i : abs(Screen.Ratios[i][1] - ratio))]
		return ratio

class Settings(object):

	Addon = None
	Database = 'settings'
	Lock = Lock()
	Busy = 0

	LevelBasic = 0
	LevelStandard = 1
	LevelAdvanced = 2
	LevelExpert = 3
	LevelInternal = 4

	InterpreterDisabled = 0
	InterpreterStandard = 1
	InterpreterExtreme = 2

	ParameterDefault = 'default'
	ParameterValue = 'value'

	PropertyCacheInitialized = 'GaiaSettingsCacheInitialized'
	PropertyCacheEnabled = 'GaiaSettingsCacheEnabled'
	PropertyCacheTimeUser = 'GaiaSettingsCacheTimeUser'
	PropertyCacheTimeMain = 'GaiaSettingsCacheTimeMain'
	PropertyCacheDataUser = 'GaiaSettingsCacheDataUser'
	PropertyCacheDataMain = 'GaiaSettingsCacheDataMain'

	CategoryGeneral = 'general'
	CategoryAccount = 'account'
	CategoryPremium = 'premium'
	CategoryProvider = 'provider'
	CategoryScrape = 'scrape'
	CategoryStream = 'stream'
	CategoryPlayback = 'playback'
	CategoryActivity = 'activity'
	CategoryMetadata = 'metadata'
	CategoryImage = 'image'
	CategoryMenu = 'menu'
	CategoryInterface = 'interface'
	CategoryTheme = 'theme'
	CategoryView = 'view'
	CategoryOracle = 'oracle'
	CategoryLibrary = 'library'
	CategoryDownload = 'download'
	CategoryNetwork = 'network'
	CategoryUtility = 'utility'

	UnitByte = 'b'
	UnitByteKilo = 'kb'
	UnitByteMega = 'mb'
	UnitByteGiga = 'gb'
	UnitByteTera = 'tb'

	UnitSecond = 'second'
	UnitMinute = 'minute'
	UnitHour = 'hour'
	UnitDay = 'day'
	UnitWeek = 'week'
	UnitMonth = 'month'
	UnitYear = 'year'

	SpecialDefault = 'default'
	SpecialAutomatic = 'automatic'
	SpecialUnlimited = 'unlimited'
	SpecialNone = 'none'
	SpecialNever = 'never'
	SpecialAlways = 'always'

	CustomNumber = 'number'
	CustomPercent = 'percent'
	CustomDuration = 'duration'
	CustomSize = 'size'
	CustomColor = 'color'
	CustomIcon = 'icon'

	# Specify the custom settings values here, so that the label can be correctly set if the setting value is updated programmatically.
	#	'id' : {
	#		'type' : <custom type>,
	#		'title' : <title string ID>,
	#		'value' : {
	#			'unit' : <optional unit type>,
	#			'default' : <optional default value>,
	#			'minimum' : <optional minimum value>,
	#			'maximum' : <optional maximum value>,
	#		},
	#		'label' : {
	#			'suffix' : <optional fixed label suffix>,
	#			'singular' : <optional singular label suffix>,
	#			'plural' : <optional plural label suffix>,
	#		},
	#		'special' : {
	#			'zero' : <optional special value for 0>,
	#			'none' : <optional special value for None>,
	#			'minimum' : <optional special value for those below the minimum value>,
	#			'minimum' : <optional special value for those above the maximum value>,
	#		},
	#	},
	Custom = {
		'theme.color.primary' : {
			'type' : CustomColor,
			'title' : 35486,
			'value' : {
				'default' : 'FFA0C12C',
			},
		},
		'theme.color.secondary' : {
			'type' : CustomColor,
			'title' : 35487,
			'value' : {
				'default' : 'FF3C7DBF',
			},
		},
		'theme.color.tertiary' : {
			'type' : CustomColor,
			'title' : 35334,
			'value' : {
				'default' : 'FF777777',
			},
		},
		'theme.color.rating' : {
			'type' : CustomColor,
			'title' : 35187,
			'value' : {
				'default' : 'FFD4AF37',
			},
		},
		'theme.color.main' : {
			'type' : CustomColor,
			'title' : 35397,
			'value' : {
				'default' : 'FF2396FF',
			},
		},
		'theme.color.alternative' : {
			'type' : CustomColor,
			'title' : 35239,
			'value' : {
				'default' : 'FF004F98',
			},
		},
		'theme.color.special' : {
			'type' : CustomColor,
			'title' : 33105,
			'value' : {
				'default' : 'FF6C3483',
			},
		},
		'theme.color.ultra' : {
			'type' : CustomColor,
			'title' : 35240,
			'value' : {
				'default' : 'FF00A177',
			},
		},
		'theme.color.excellent' : {
			'type' : CustomColor,
			'title' : 35241,
			'value' : {
				'default' : 'FF00A244',
			},
		},
		'theme.color.good' : {
			'type' : CustomColor,
			'title' : 35242,
			'value' : {
				'default' : 'FF668D2E',
			},
		},
		'theme.color.medium' : {
			'type' : CustomColor,
			'title' : 33999,
			'value' : {
				'default' : 'FFB7950B',
			},
		},
		'theme.color.poor' : {
			'type' : CustomColor,
			'title' : 35243,
			'value' : {
				'default' : 'FFBA4A00',
			},
		},
		'theme.color.bad' : {
			'type' : CustomColor,
			'title' : 35244,
			'value' : {
				'default' : 'FF922B21',
			},
		},
		'general.concurrency.global.limit' : {
			'type' : CustomNumber,
			'title' : 36620,
			'label' : {
				'suffix' : 35413,
			},
			'value' : {
				'default' : None,
				'minimum' : 50,
				'maximum' : 10000,
			},
			'special' : {
				'zero' : SpecialUnlimited,
				'none' : SpecialAutomatic,
			},
		},
		'general.concurrency.metadata.limit' : {
			'type' : CustomNumber,
			'title' : 36621,
			'label' : {
				'singular' : 36169,
				'plural' : 32012,
			},
			'value' : {
				'default' : None,
				'minimum' : 1,
				'maximum' : 100,
			},
			'special' : {
				'zero' : SpecialUnlimited,
				'none' : SpecialAutomatic,
			},
		},
		'general.concurrency.scrape.limit' : {
			'type' : CustomNumber,
			'title' : 36621,
			'label' : {
				'singular' : 36169,
				'plural' : 32012,
			},
			'value' : {
				'default' : None,
				'minimum' : 1,
				'maximum' : 100,
			},
			'special' : {
				'zero' : SpecialUnlimited,
				'none' : SpecialAutomatic,
			},
		},
		'general.concurrency.scrape.binge' : {
			'type' : CustomNumber,
			'title' : 36624,
			'label' : {
				'singular' : 36169,
				'plural' : 32012,
			},
			'value' : {
				'default' : None,
				'minimum' : 1,
				'maximum' : 100,
			},
			'special' : {
				'zero' : SpecialUnlimited,
				'none' : SpecialAutomatic,
			},
		},
		'general.concurrency.scrape.connection' : {
			'type' : CustomNumber,
			'title' : 32038,
			'label' : {
				'singular' : 33404,
				'plural' : 33413,
			},
			'value' : {
				'default' : 0,
				'minimum' : 50,
				'maximum' : 10000,
			},
			'special' : {
				'zero' : SpecialUnlimited,
				'none' : SpecialAutomatic,
			},
		},
		'provider.failure.detection.time' : {
			'type' : CustomDuration,
			'title' : 33671,
			'value' : {
				'unit' : UnitDay,
				'default' : 5,
				'minimum' : 1,
				'maximum' : 30,
			},
			'special' : {
				'zero' : SpecialNever,
				'none' : SpecialDefault,
			},
		},
		'scrape.limit.time' : {
			'type' : CustomDuration,
			'title' : 32312,
			'value' : {
				'unit' : UnitSecond,
				'default' : 180,
				'minimum' : 15,
				'maximum' : 900,
			},
			'special' : {
				'zero' : SpecialUnlimited,
				'none' : SpecialDefault,
			},
		},
		'scrape.limit.query' : {
			'type' : CustomNumber,
			'title' : 33329,
			'label' : {
				'singular' : 33328,
				'plural' : 32035,
			},
			'value' : {
				'default' : 10,
				'minimum' : 1,
				'maximum' : 50,
			},
			'special' : {
				'zero' : SpecialDefault,
				'none' : SpecialDefault,
			},
		},
		'scrape.limit.page' : {
			'type' : CustomNumber,
			'title' : 35307,
			'label' : {
				'singular' : 35809,
				'plural' : 35810,
			},
			'value' : {
				'default' : 10,
				'minimum' : 1,
				'maximum' : 100,
			},
			'special' : {
				'zero' : SpecialUnlimited,
				'none' : SpecialDefault,
			},
		},
		'scrape.limit.request' : {
			'type' : CustomNumber,
			'title' : 35806,
			'label' : {
				'singular' : 35807,
				'plural' : 35808,
			},
			'value' : {
				'default' : 0,
				'minimum' : 5,
				'maximum' : 10000,
			},
			'special' : {
				'zero' : SpecialUnlimited,
				'none' : SpecialDefault,
			},
		},
		'scrape.save.stream' : {
			'type' : CustomDuration,
			'title' : 33887,
			'value' : {
				'unit' : UnitHour,
				'default' : 360, # 15 days. We can keep more data, since the data is now compressed and will not take up too much extra space.
				'minimum' : 0,
				'maximum' : 2190,
			},
			'special' : {
				'zero' : SpecialNever,
				'none' : SpecialDefault,
			},
		},
		'scrape.save.cache' : {
			'type' : CustomDuration,
			'title' : 33888,
			'value' : {
				'unit' : UnitHour,
				'default' : 72,
				'minimum' : 0,
				'maximum' : 2190,
			},
			'special' : {
				'zero' : SpecialNever,
				'none' : SpecialDefault,
			},
		},
		'scrape.cache.inspection.time' : {
			'type' : CustomDuration,
			'title' : 32312,
			'value' : {
				'unit' : UnitSecond,
				'default' : 120, # 60 secs sometimes too little if there are a few 1000 streams.
				'minimum' : 10,
				'maximum' : 300,
			},
			'special' : {
				'zero' : SpecialUnlimited,
				'none' : SpecialDefault,
			},
		},
		'scrape.termination.unresponsive.time' : {
			'type' : CustomDuration,
			'title' : 32312,
			'value' : {
				'unit' : UnitSecond,
				'default' : 15,
				'minimum' : 1,
				'maximum' : 180,
			},
			'special' : {
				'zero' : SpecialDefault,
				'none' : SpecialDefault,
			},
		},
		'scrape.termination.unresponsive.limit' : {
			'type' : CustomNumber,
			'title' : 33330,
			'label' : {
				'singular' : 33681,
				'plural' : 32345,
			},
			'value' : {
				'default' : 1,
				'minimum' : 1,
				'maximum' : 10,
			},
			'special' : {
				'zero' : SpecialDefault,
				'none' : SpecialDefault,
			},
		},
		'activity.binge.scrape' : {
			'type' : CustomDuration,
			'title' : 36495,
			'value' : {
				'unit' : UnitMinute,
				'default' : 10,
				'minimum' : 1,
				'maximum' : 120,
			},
			'special' : {
				'zero' : SpecialDefault,
				'none' : SpecialDefault,
			},
		},
		'activity.binge.delay' : {
			'type' : CustomDuration,
			'title' : 35581,
			'value' : {
				'unit' : UnitSecond,
				'default' : 0,
				'minimum' : 5,
				'maximum' : 600,
			},
			'special' : {
				'zero' : SpecialDefault,
				'none' : SpecialDefault,
			},
		},
		'activity.binge.continue.timeout' : {
			'type' : CustomDuration,
			'title' : 36498,
			'value' : {
				'unit' : UnitSecond,
				'default' : 20,
				'minimum' : 5,
				'maximum' : 600,
			},
			'special' : {
				'zero' : SpecialNever,
				'none' : SpecialDefault,
			},
		},
		'activity.history.count.rewatch' : {
			'type' : CustomDuration,
			'title' : 35405,
			'value' : {
				'unit' : UnitDay,
				'default' : 60,
				'minimum' : 1,
				'maximum' : 3650,
			},
			'special' : {
				'zero' : SpecialAlways,
				'none' : SpecialDefault,
			},
		},
		'activity.rating.binge.timeout' : {
			'type' : CustomDuration,
			'title' : 33660,
			'value' : {
				'unit' : UnitSecond,
				'default' : 40, # 20 secs is too little.
				'minimum' : 5,
				'maximum' : 600,
			},
			'special' : {
				'zero' : SpecialNever,
				'none' : SpecialDefault,
			},
		},
		'activity.rating.timeout' : {
			'type' : CustomDuration,
			'title' : 36498,
			'value' : {
				'unit' : UnitSecond,
				'default' : 0,
				'minimum' : 5,
				'maximum' : 600,
			},
			'special' : {
				'zero' : SpecialNever,
				'none' : SpecialDefault,
			},
		},
		'activity.rating.rerate.movie' : {
			'type' : CustomDuration,
			'title' : 36378,
			'value' : {
				'unit' : UnitDay,
				'default' : 90,
				'minimum' : 1,
				'maximum' : 3650,
			},
			'special' : {
				'zero' : SpecialAlways,
				'none' : SpecialDefault,
				'maximum' : SpecialNever,
			},
		},
		'activity.rating.rerate.show' : {
			'type' : CustomDuration,
			'title' : 36379,
			'value' : {
				'unit' : UnitDay,
				'default' : 90,
				'minimum' : 1,
				'maximum' : 3650,
			},
			'special' : {
				'zero' : SpecialAlways,
				'none' : SpecialDefault,
				'maximum' : SpecialNever,
			},
		},
		'activity.rating.rerate.season' : {
			'type' : CustomDuration,
			'title' : 36380,
			'value' : {
				'unit' : UnitDay,
				'default' :180,
				'minimum' : 1,
				'maximum' : 3650,
			},
			'special' : {
				'zero' : SpecialAlways,
				'none' : SpecialDefault,
			},
		},
		'activity.rating.rerate.episode' : {
			'type' : CustomDuration,
			'title' : 36381,
			'value' : {
				'unit' : UnitDay,
				'default' : 365,
				'minimum' : 1,
				'maximum' : 3650,
			},
			'special' : {
				'zero' : SpecialAlways,
				'none' : SpecialDefault,
				'maximum' : SpecialNever,
			},
		},
		'playback.time.wait' : {
			'type' : CustomDuration,
			'title' : 35289,
			'value' : {
				'unit' : UnitSecond,
				'default' : 90,
				'minimum' : 10,
				'maximum' : 300,
			},
			'special' : {
				'zero' : SpecialUnlimited,
				'none' : SpecialDefault,
			},
		},
		'playback.buffer.monitor.delay' : {
			'type' : CustomDuration,
			'title' : 33020,
			'value' : {
				'unit' : UnitSecond,
				'default' : SpecialAutomatic,
				'minimum' : 15,
				'maximum' : 7200,
			},
			'special' : {
				'zero' : SpecialAutomatic,
				'none' : SpecialDefault,
			},
		},
		'interface.button.time' : {
			'type' : CustomDuration,
			'title' : 32312,
			'value' : {
				'unit' : UnitSecond,
				'default' : 25,
				'minimum' : 1,
				'maximum' : 180,
			},
			'special' : {
				'zero' : SpecialDefault,
				'none' : SpecialDefault,
			},
		},
		'network.vpn.monitor.interval' : {
			'type' : CustomDuration,
			'title' : 33804,
			'value' : {
				'unit' : UnitSecond,
				'default' : 420,
				'minimum' : 300,
				'maximum' : 86400,
			},
			'special' : {
				'zero' : SpecialNever,
				'none' : SpecialDefault,
			},
		},
		'network.vpn.monitor.interval.alternative' : {
			'type' : CustomDuration,
			'title' : 33804,
			'value' : {
				'unit' : UnitSecond,
				'default' : 120,
				'minimum' : 60,
				'maximum' : 86400,
			},
			'special' : {
				'zero' : SpecialNever,
				'none' : SpecialDefault,
			},
		},
		'network.vpn.kill.timeout' : {
			'type' : CustomDuration,
			'title' : 36164,
			'value' : {
				'unit' : UnitSecond,
				'default' : 120,
				'minimum' : 30,
				'maximum' : 600,
			},
			'special' : {
				'zero' : SpecialDefault,
				'none' : SpecialDefault,
			},
		},
		'utility.bluetooth.monitor.interval' : {
			'type' : CustomDuration,
			'title' : 33804,
			'value' : {
				'unit' : UnitSecond,
				'default' : 45,
				'minimum' : 10,
				'maximum' : 300,
			},
			'special' : {
				'zero' : SpecialDefault,
				'none' : SpecialDefault,
			},
		},
		'general.developer.precheck.link.time' : {
			'type' : CustomDuration,
			'title' : 32312,
			'value' : {
				'unit' : UnitSecond,
				'default' : 30,
				'minimum' : 10,
				'maximum' : 300,
			},
			'special' : {
				'zero' : SpecialDefault,
				'none' : SpecialDefault,
			},
		},
		'general.developer.precheck.metadata.time' : {
			'type' : CustomDuration,
			'title' : 32312,
			'value' : {
				'unit' : UnitSecond,
				'default' : 30,
				'minimum' : 10,
				'maximum' : 300,
			},
			'special' : {
				'zero' : SpecialDefault,
				'none' : SpecialDefault,
			},
		},
		'oracle.chatgpt.model.limit' : {
			'type' : CustomNumber,
			'title' : 33854,
			'label' : {
				'suffix' : 33680,
			},
			'value' : {
				'minimum' : 100,
				'maximum' : 32768,
			},
			'special' : {
				'zero' : SpecialUnlimited,
				'none' : SpecialAutomatic,
			},
		},
	}

	CacheInitialized = False
	CacheEnabled = False
	CacheTimeMain = None
	CacheDataMain = None
	CacheValuesMain = None
	CacheTimeUser = None
	CacheDataUser = None
	CacheValuesUser = None

	DataLabel = 'label'
	DataValue = 'value'

	# Also check downloader.py.
	PathDefault = 'Default'
	Paths = {
		'download.manual.location.combined' 		: 'special://userdata/addon_data/plugin.video.gaia/Downloads/Manual/',
		'download.manual.location.movie'			: 'special://userdata/addon_data/plugin.video.gaia/Downloads/Manual/Movies/',
		'download.manual.location.show'				: 'special://userdata/addon_data/plugin.video.gaia/Downloads/Manual/Shows/',
		'download.manual.location.other'			: 'special://userdata/addon_data/plugin.video.gaia/Downloads/Manual/Other/',

		'download.cache.location.combined'			: 'special://userdata/addon_data/plugin.video.gaia/Downloads/Cache/',
		'download.cache.location.movie'				: 'special://userdata/addon_data/plugin.video.gaia/Downloads/Cache/Movies/',
		'download.cache.location.show'				: 'special://userdata/addon_data/plugin.video.gaia/Downloads/Cache/Shows/',
		'download.cache.location.other'				: 'special://userdata/addon_data/plugin.video.gaia/Downloads/Cache/Other/',

		'library.location.combined'					: 'special://userdata/addon_data/plugin.video.gaia/Library/',
		'library.location.movie'					: 'special://userdata/addon_data/plugin.video.gaia/Library/Movies/',
		'library.location.show'						: 'special://userdata/addon_data/plugin.video.gaia/Library/Shows/',
	}

	@classmethod
	def _addon(self):
		if Settings.Addon is None: Settings.Addon = System.addon()
		return Settings.Addon

	@classmethod
	def _addonReset(self):
		Settings.Addon = None

	@classmethod
	def _database(self):
		from lib.modules.database import Database
		return Database.instance(name = Settings.Database, create = '''
			CREATE TABLE IF NOT EXISTS %s
			(
				id TEXT PRIMARY KEY,
				data TEXT
			);
			'''
		)

	@classmethod
	def interpreter(self, full = False, label = False):
		from lib.modules.interface import Translation

		check = True
		if full:
			data = File.readNow(File.joinPath(System.path(), 'addon.xml'))
			check = Regex.extract(data = data, expression = '<reuselanguageinvoker>(.*?)<\/reuselanguageinvoker>', group = 1) == 'true'

		interpreter = Settings.InterpreterStandard
		if check:
			setting = self.getString(id = 'general.performance.interpreter')
			# When default, returns "$ADDON[plugin.video.gaia 36091]".
			if setting:
				if '36091' in setting or Translation.string(36091) in setting: interpreter = Settings.InterpreterStandard
				elif '36170' in setting or Translation.string(36170) in setting: interpreter = Settings.InterpreterExtreme
				else: interpreter = Settings.InterpreterDisabled

		if label:
			if interpreter == Settings.InterpreterStandard: label = Translation.string(36091)
			elif interpreter == Settings.InterpreterExtreme: label = Translation.string(36170)
			else: label = Translation.string(32302)
			return interpreter, label
		return interpreter

	@classmethod
	def interpreterSelect(self, notification = False, silent = False, settings = False):
		from lib.modules.interface import Dialog, Translation, Format

		result = False
		id = 'general.performance.interpreter'
		items = [(Settings.InterpreterDisabled, 32302), (Settings.InterpreterStandard, 36091), (Settings.InterpreterExtreme, 36170)]

		if silent:
			choice = self.interpreter(full = False)
		else:
			Dialog.details(title = 33454, items = [
				{'type' : 'text', 'value' : 'A Python [I]Interpreter[/I]  or [I]Invoker[/I]  is the software that executes Python code. Every time you navigate trough the menus in Gaia, scrape sources, play videos, or carry out any action whatsoever, Kodi will use an interpreter to execute the required code in Gaia.', 'break' : 2},
				{'type' : 'text', 'value' : 'Traditionally Kodi initializes a new interpreter for every addon action. That means, just navigating from the main menu to a submenu in Gaia requires a new interpreter. Creating a new interpreter has a computational overhead and slows down the addon. That is why Kodi introduced a new feature for addons called [I]reuselanguageinvoker[/I], which tries to reuse existing interpreters as far as possible. Reusing interpreters has less computational overhead, since they do not have to be initialized from scratch each time and therefore improves the performance of the addon.', 'break' : 2},
				{'type' : 'text', 'value' : 'Gaia was not initially designed to reuse interpreters and some features might behave incorrectly under these conditions. In older versions of Kodi, reusing interpreters could crash Kodi or cause addons to hang. This is especially prevalent if an addon is used through widgets or other external addons or scripts. If you find any such behavior, disable reusing interpreters in Gaia\'s settings. If the problem is solved by disabling the setting, please report this on Gaia\'s ticket system, since it is probably a bug that can be fixed.', 'break' : 2},

				{'type' : 'text', 'value' : 'Interpreters can be used in the following ways:', 'break' : 2},
				{'type' : 'list', 'value' : [
					{'title' : 'Disabled', 'value' : 'Do not reuse interpreters at all and execute Gaia in the traditional manner. This is the most robust option, but will make Gaia slightly slower.'},
					{'title' : 'Standard', 'value' : 'Reuse interpreters to execute Gaia, but reset critical states and settings between executions. This is less robust and might cause some unexcepted behavior, but will make Gaia slightly faster.'},
					{'title' : 'Extreme', 'value' : 'Reuse interpreters to execute Gaia, reset critical states, but keep settings between executions. This can make Gaia even faster, since settings are kept in memory. This means that if you change any of Gaia\'s settings, they will not take effect, since Gaia will continue to use the old settings that are cached in memory. You will have to restart Kodi (or use Gaia -> Tools -> Utilities -> System -> Tools -> Reload Kodi) every time you change a setting in Gaia for the new values to be loaded. It is therefore recommended to disable the reuse of interpreters, fully configure Gaia\'s setting until you are happy with all preferences, and only then enable this Extreme option.'},
				]},
			])
			choice = Dialog.select(title = 33454, items = [Format.fontBold(i[1]) for i in items])

		if choice >= 0:
			interpreter = items[choice][0]
			enabled = not interpreter == Settings.InterpreterDisabled
			self.set(id = id, value = Translation.string(items[choice][1]))

			path = File.joinPath(System.path(), 'addon.xml')
			data = File.readNow(path)
			reuse = Regex.extract(data = data, expression = '<reuselanguageinvoker>(.*?)<\/reuselanguageinvoker>', group = 1) == 'true'

			if not reuse == enabled:
				result = True
				data = Regex.replace(data = data, expression = '<reuselanguageinvoker>(.*?)<\/reuselanguageinvoker>', replacement = 'true' if enabled else 'false', group = 1)
				File.writeNow(path, data)
				System.reload(message = False if silent and not notification else 33148)

		if settings: self.launch(id = id)
		return result

	@classmethod
	def interpreterReset(self):
		# This function clears/resets global or class variables that might interfere when Gaia's inner working if the Python invoker is reused.
		# Gaia was designed with the assumption that a new invoker is used every time, meaning any global/class variables are cleared by the garbage collector at the end of execution.
		# Any new execution assumes that all those variables are intiialized from scratch.

		interpreter = self.interpreter()
		if interpreter:
			settings = interpreter == Settings.InterpreterStandard

			from lib.meta.tools import MetaTools
			from lib.meta.menu import MetaMenu
			from lib.meta.pack import MetaPack
			from lib.meta.cache import MetaCache
			from lib.meta.image import MetaImage
			from lib.meta.manager import MetaManager
			from lib.meta.provider import MetaProvider
			from lib.meta.service import MetaService
			from lib.meta.providers.fanart import MetaFanart
			from lib.meta.services.tvdb import MetaTvdb
			from lib.providers.core.manager import Manager
			from lib.providers.core.base import ProviderBase
			from lib.providers.core.debrid import ProviderDebrid
			from lib.providers.core.external import ProviderExternal
			from lib.providers.core.web import ProviderWeb
			from lib.debrid.debrid import Debrid
			from lib.modules.stream import Stream
			from lib.modules.cache import Cache, Memory
			from lib.modules.concurrency import Pool
			from lib.modules.account import Account
			from lib.modules.cloudflare import Cloudflare
			from lib.modules.menu import Menu
			from lib.modules.core import Core
			from lib.modules.handler import Handler
			from lib.modules.playback import Playback
			from lib.modules.search import Search
			from lib.modules.shortcut import Shortcut
			from lib.modules.interface import Font, Icon, Format, Core as CoreDialog, Dialog, Context
			from lib.modules.player import Player, Streamer, Subtitle
			from lib.modules.window import Window
			from lib.modules.environment import Environment
			from lib.modules.external import Importer, Loader
			from lib.modules import trakt as Trakt

			classes = [
				MetaTools, MetaMenu, MetaPack, MetaCache, MetaImage, MetaManager, MetaProvider, MetaService, MetaTvdb, MetaFanart,
				Debrid, Stream,
				Manager, ProviderBase, ProviderDebrid, ProviderExternal, ProviderWeb,
				Account, Cloudflare, Search, Shortcut, Menu, Core, Handler, Playback, Window, Trakt,
				Font, Icon, Format, CoreDialog, Dialog, Context,
				Player, Streamer, Subtitle,
				Cache, Memory, Pool,
				Language, Title, Audience, System, Time, Environment,
				#Importer, Loader, # Do not reset these. They do not rely on any settings. And it is actually more efficient to not reset, so we can reuse imported modules between invokers, which typically take long to import.
			]
			for i in classes:
				try: i.reset(settings = settings)
				except: Logger.error()

			if settings: self.cacheClear(full = False)

	@classmethod
	def level(self, default = LevelBasic):
		try:
			path = File.joinPath('special://userdata', 'guisettings.xml')
			data = File.readNow(path)
			level = Regex.extract(data = data, expression = '<settinglevel>(.*?)<\/settinglevel>')
			level = int(level)
		except:
			level = default
			Logger.error('Cannot read the settings level')
		return level

	# NB: Kodi does not internally update this value if the file is written to, and the value is reset if Kodi restarts.
	# Do not use this function to permanently set the settings level through Python - it won't work.
	@classmethod
	def levelSet(self, level):
		try:
			path = File.joinPath('special://userdata', 'guisettings.xml')
			data = File.readNow(path)
			data = Regex.replace(data = data, expression = '<settinglevel>(.*?)<\/settinglevel>', replacement = str(level), group = 1)
			File.writeNow(path, data)
			return True
		except:
			Logger.error('Cannot write the settings level')
			return False

	# This function is not very reliable.
	# Sometimes when writing the updated settings to file, the file is unchanged.
	# This happens both with Kodi's file I/O and Python's native file I/O.
	# It might be caused because Kodi internally writes the settings to file, and then overwriting the data that was previously written from this function.
	# We try to write multiple times in a thread, sleeping in between, until the file size has changed or 2.5 seconds have passed.
	# Hence, if this function was not able to write to file during this time, the old settings will remain in the file. On the next launch this will be retried.
	@classmethod
	def clean(self, reload = False, retry = True, background = True):
		if background: Pool.thread(target = self._clean, kwargs = {'reload' : reload, 'retry' : retry, 'delay' : True}, start = True)
		else: self._clean(reload = reload, retry = retry)

	@classmethod
	def _clean(self, reload = False, retry = True, delay = False):
		# Important when called from service.py after Kodi is freshly booted.
		# Otherwise Koldi might not have loaded the addon settings yet, causing many "Resetting to default value" calls below.
		if delay: Time.sleep(3)

		dataMain = self.cacheDataMain()
		idsMain = Regex.extract(data = dataMain, expression = '<setting\s*id\s*=\s*"(.*?)"', group = None, all = True, flags = Regex.FlagCaseInsensitive | Regex.FlagMultiLines)

		# Reset data labels to default if they were removed from settings.db.
		# Eg: The user deletes settings.db or the DB gets corrupted. The labels still show in the settings dialog.
		# The user might be confused why all the accounts still show as authenticated in the settings dialog, although they do not work anymore.
		exceptions = [
			'dummy', # In the comment section.
		]
		for id in idsMain:
			if not id in exceptions and self.idDataLabel(id) in idsMain:
				if not self.defaultIs(id = self.idDataLabel(id)) and self._getDatabase(id = self.idDataValue(id)) is None: # Check defaultIs() on the label, not on "id".
					Logger.log('CLEAN SETTINGS - Resetting to default value (%s)' % id)
					self.defaultData(id = id)
					change = True

		# Only do this here, since some values might be reset to default above.
		self.cacheClear()
		dataUser = self.cacheDataUser()
		idsUser = Regex.extract(data = dataUser, expression = '(?:^|[\r\n]+)(.*?id\s*=\s*"(.*?)".*?(?:<\/setting>|\/>)(?:\r|\n|$))', group = None, all = True, flags = Regex.FlagCaseInsensitive | Regex.FlagMultiLines)

		# Remove old settings that do not exist anymore.
		change = False
		for id in idsUser:
			if not id[1] in idsMain:
				Logger.log('CLEAN SETTINGS - Removing old setting (%s)' % id[1])
				dataUser = dataUser.replace(id[0], '')
				change = True

		def _write(data, reload):
			path = self.pathProfile()
			size = File.size(path)
			for i in range(5):
				File.writeNow(path, data)
				Time.sleep(0.5)
				if not File.size(path) == size: break
			if reload: self.cacheClear()

		if change:
			# File does not change in Kodi 19 if writeNow() is used, probably due to caching.
			# Sometimes writeNow() seems to work? But just stick with writeNative() to be sure.
			if retry:
				_write(data = dataUser, reload = reload)
			else:
				File.writeNow(self.pathProfile(), dataUser)
				if reload: self.cacheClear()

	@classmethod
	def path(self, id):
		path = self.get(id)
		if path == Settings.PathDefault or not path or path.strip() == '': path = Settings.Paths[id]
		return path

	@classmethod
	def pathAddon(self):
		return File.joinPath(System.path(), 'resources', 'settings.xml')

	@classmethod
	def pathProfile(self):
		return File.joinPath(System.profile(), 'settings.xml')

	@classmethod
	def pathDatabase(self):
		return File.joinPath(System.profile(), 'settings.db')

	# Get a Kodi setting.
	# A list of setting IDs can be found in: .kodi/data/userdata/guisettings.xml
	@classmethod
	def kodi(self, id):
		try: return System.executeJson(method = 'Settings.GetSettingValue', parameters = {'setting' : id})['result']['value']
		except: Logger.error()
		return None

	# Set a Kodi setting.
	@classmethod
	def kodiSet(self, id, value):
		try: return System.executeJson(method = 'Settings.SetSettingValue', parameters = {'setting' : id, 'value' : value})['result']
		except: Logger.error()
		return False

	# Reset a Kodi setting to its default setting.
	@classmethod
	def kodiDefault(self, id):
		try: return System.executeJson(method = 'Settings.ResetSettingValue', parameters = {'setting' : id})['result']
		except: Logger.error()
		return False

	@classmethod
	def clear(self, initialize = False):
		File.delete(self.pathProfile())
		File.delete(self.pathDatabase())
		if initialize: # Recreate the files.
			self._database()
			self.set(id = 'internal.dummy', value = True)

	@classmethod
	def size(self):
		return File.size(self.pathProfile()) + File.size(self.pathDatabase())

	@classmethod
	def cache(self):
		# Ensures that the data always stays in memory.
		# Otherwise the "static variables" are deleted if there is no more reference to the Settings class.
		if not Settings.CacheInitialized:
			Settings.Lock.acquire()

			if not Settings.CacheInitialized:
				# These should be initialized before calling System.windowPropertySet() below.
				# Otherwise we sometimes get sporadic errors during Kodi boot when calling Service.settingAutomatic(), since Settings.cache() is still busy initializing while we try to read the settings.
				#	tools.py, cacheGet]: File "tools.py", in cacheGet\n    if id in values:, "TypeError: argument of type 'NoneType' is not iterable"
				Settings.CacheValuesMain = {}
				Settings.CacheValuesUser = {}

				try: cacheGlobal = int(System.windowPropertyGet(Settings.PropertyCacheInitialized))
				except: cacheGlobal = False

				if cacheGlobal:
					Settings.CacheInitialized = Converter.boolean(System.windowPropertyGet(Settings.PropertyCacheInitialized))
					Settings.CacheEnabled = Converter.boolean(System.windowPropertyGet(Settings.PropertyCacheEnabled))
				else:
					Settings.CacheInitialized = True

					# NB: Loading the settings through Kodi (self._addon().getSetting) takes more than 3x longer than manually reading the settings from file.
					#Settings.CacheEnabled = Converter.boolean(self._addon().getSetting('general.settings.cache'))
					cache = None
					try:
						Settings.Lock.release()
						data = self.cacheDataUser()
						Settings.Lock.acquire()
						cache = self.raw(id = 'general.settings.cache', parameter = Settings.ParameterValue, data = data)
						if not cache is None: cache = Converter.boolean(cache)
					except: pass
					if cache is None: cache = Converter.boolean(self._addon().getSetting('general.settings.cache'))
					Settings.CacheEnabled = cache

					System.windowPropertySet(Settings.PropertyCacheInitialized, int(Settings.CacheInitialized))
					System.windowPropertySet(Settings.PropertyCacheEnabled, int(Settings.CacheEnabled))

			Settings.Lock.release()

	@classmethod
	def cacheInitialize(self):
		self.cache()
		if Settings.CacheEnabled:
			self.cacheDataMain()
			self.cacheDataUser()

	@classmethod
	def cacheClear(self, full = True):
		# NB: Reset addon in order to clear Kodi's internal settings cache.
		Settings.Lock.acquire()

		self._addonReset()

		Settings.CacheInitialized = False
		Settings.CacheEnabled = False
		Settings.CacheTimeMain = None
		Settings.CacheDataMain = None
		Settings.CacheValuesMain = None
		Settings.CacheTimeUser = None
		Settings.CacheDataUser = None
		Settings.CacheValuesUser = None

		if full:
			System.windowPropertyClear(Settings.PropertyCacheInitialized)
			System.windowPropertyClear(Settings.PropertyCacheEnabled)
			System.windowPropertyClear(Settings.PropertyCacheTimeMain)
			System.windowPropertyClear(Settings.PropertyCacheDataMain)
			System.windowPropertyClear(Settings.PropertyCacheTimeUser)
			System.windowPropertyClear(Settings.PropertyCacheDataUser)

		Settings.Lock.release()

	@classmethod
	def cacheData(self, valueData, valueTime, propertyData, propertyTime, path, file = True):
		if valueData is None:
			Settings.Lock.acquire()

			if valueData is None:
				if valueTime is None: valueTime = File.timeUpdated(path())
				timeCurrent = valueTime
				timePrevious = System.windowPropertyGet(propertyTime)

				if timePrevious and timeCurrent == int(timePrevious):
					valueData = System.windowPropertyGet(propertyData)

				if not valueData and file:
					valueData = File.readNow(path())
					System.windowPropertySet(propertyTime, timeCurrent)
					System.windowPropertySet(propertyData, valueData)

			Settings.Lock.release()
		return valueData, valueTime

	@classmethod
	def cacheDataMain(self, file = True):
		Settings.CacheDataMain, Settings.CacheTimeMain = self.cacheData(valueData = Settings.CacheDataMain, valueTime = Settings.CacheTimeMain, propertyData = Settings.PropertyCacheDataMain, propertyTime = Settings.PropertyCacheTimeMain, path = self.pathAddon)
		return Settings.CacheDataMain

	@classmethod
	def cacheDataUser(self, file = True):
		Settings.CacheDataUser, Settings.CacheTimeUser = self.cacheData(valueData = Settings.CacheDataUser, valueTime = Settings.CacheTimeUser, propertyData = Settings.PropertyCacheDataUser, propertyTime = Settings.PropertyCacheTimeUser, path = self.pathProfile)
		return Settings.CacheDataUser

	@classmethod
	def cacheEnabled(self):
		self.cache()
		return Settings.CacheEnabled

	@classmethod
	def cacheGet(self, id, raw, database = False):
		try:
			self.cache()
			if raw:
				data = self.cacheDataMain()
				values = Settings.CacheValuesMain
				parameter = Settings.ParameterDefault
			else:
				data = self.cacheDataUser()
				values = Settings.CacheValuesUser
				parameter = Settings.ParameterValue

			if id in values: # Already looked-up previously.
				return values[id]
			elif database:
				result = self._getDatabase(id = id)
				values[id] = result
				return result
			else:
				result = self.raw(id = id, parameter = parameter, data = data)
				if result is None: result = self._addon().getSetting(Converter.unicode(id)) # Not in the userdata settings yet. Fallback to normal Kodi lookup.
				values[id] = result
				return result
		except:
			# When the settings cache is cleared (eg: in clean()), the global dictionaries/data might be set to None while this function is busy executing from another thread.
			Logger.error()

		return None

	@classmethod
	def cacheSet(self, id, value):
		try:
			self.cache()
			Settings.CacheValuesUser[id] = value
		except:
			# When the settings cache is cleared (eg: in clean()), the global dictionaries/data might be set to None while this function is busy executing from another thread.
			Logger.error()

	@classmethod
	def custom(self, id, settings = True):
		from lib.modules.interface import Dialog, Format

		type = self._customParameter(id, 'type')
		title = self._customParameter(id, 'title')
		if not title: title = 33011
		value = self.customGet(id = id)

		if type == Settings.CustomColor:
			color = Dialog.input(title = title, type = Dialog.InputAlphabetic, default = value)
			try: color = color.strip()
			except: pass
			if color and Format.colorIsHex(color):
				while len(color) < 8: color = 'F' + color
				if len(color) > 8: color = color[:8]
				value = color.upper()
			elif color:
				Dialog.notification(title = title, message = 35236, icon = Dialog.IconError)
			else:
				value = self._customParameter(id, 'value', 'default')
		elif type == Settings.CustomIcon:
			value = Dialog.input(title = title, type = Dialog.InputAlphabetic, default = value)
			if not value: value = self._customParameter(id, 'value', 'default')
		else:
			valueMinimum = self._customParameter(id, 'value', 'minimum')
			valueMaximum = self._customParameter(id, 'value', 'maximum')
			if type in [Settings.CustomNumber, Settings.CustomPercent, Settings.CustomDuration, Settings.CustomSize]:
				value = Dialog.input(type = Dialog.InputNumeric, title = title, default = self._customValue(id = id, value = value, inverse = True))
				special = self._customSpecial(id = id)
				if not special or not value in special:
					if not valueMinimum is None and value < valueMinimum:
						if False in special: value = False
						else: value = valueMinimum
					elif not valueMaximum is None and value > valueMaximum:
						if True in special: value = True
						else: value = valueMaximum
				value = self._customValue(id = id, value = value, inverse = False)

		self.customSet(id = id, value = value)
		if settings:
			if type in [Settings.CustomColor, Settings.CustomIcon]: Settings.launch(id = id)
			else: Settings.launchData(id = id)

	@classmethod
	def customGet(self, id, raw = False, cached = True, default = None):
		type = self._customParameter(id, 'type')
		if type in [Settings.CustomColor, Settings.CustomIcon]:
			value = self.get(id = id)
			if not value:
				try: value = self._customParameter(id, 'value', 'default')
				except: value = default
		else:
			try: value = self.getData(id = id, raw = raw, cached = cached, default = default)['value']
			except: value = default
		return self._customValue(id = id, value = value, inverse = False, convert = False)

	@classmethod
	def customSet(self, id, value, label = None, background = False):
		type = self._customParameter(id, 'type')
		if label is None: label = self.customLabel(id = id, value = value)
		if type in [Settings.CustomColor, Settings.CustomIcon]: self.set(id = id, value = label)
		else: self.setData(id = id, value = {'value' : value}, label = label, background = background)

	@classmethod
	def customLabel(self, id, value):
		from lib.modules.interface import Translation, Format

		label = None
		type = self._customParameter(id, 'type')

		if type == Settings.CustomColor:
			label = Format.fontColor(label = value, color = value)
		elif type == Settings.CustomIcon:
			label = value
		else:
			labelExtra = None
			labelSuffix = self._customParameter(id, 'label', 'suffix')
			labelSingular = self._customParameter(id, 'label', 'singular')
			labelPlural = self._customParameter(id, 'label', 'plural')
			special = self._customSpecial(id = id)

			if special and value in special: label = special[value]

			special = True
			if label == Settings.SpecialDefault: label = 33564
			elif label == Settings.SpecialAutomatic: label = 33800
			elif label == Settings.SpecialUnlimited: label = 35221
			elif label == Settings.SpecialNone: label = 33112
			elif label == Settings.SpecialNever: label = 36043
			elif label == Settings.SpecialAlways: label = 32017
			else: special = False

			label = Translation.string(label)

			if not special:
				if type == Settings.CustomNumber:
					if labelSingular and value == 1: labelSuffix = labelSingular
					elif labelPlural: labelSuffix = labelPlural
				elif type == Settings.CustomPercent:
					labelExtra = '%'
					value = int(value * 100.0)
					if labelSingular and value == 1: labelSuffix = labelSingular
					elif labelPlural: labelSuffix = labelPlural
				elif type == Settings.CustomSize:
					from lib.modules.convert import ConverterSize
					label = ConverterSize(value, unit = ConverterSize.Byte).stringOptimal()
				elif type == Settings.CustomDuration:
					from lib.modules.convert import ConverterDuration
					unit = self._customUnit(id = id)
					format = ConverterDuration.FormatWordMedium if unit in [ConverterDuration.UnitHour, ConverterDuration.UnitDay, ConverterDuration.UnitYear] else ConverterDuration.FormatAbbreviationShort
					label = ConverterDuration(value, unit = ConverterDuration.UnitSecond).string(format = format, capitalize = True)

				if Tools.isNumber(value): value = '{:,}'.format(value)
				if labelExtra or labelSuffix:
					label = str(value)
					if labelExtra: label = '%s%s' % (label, Translation.string(labelExtra))
					if labelSuffix: label = '%s %s' % (label, Translation.string(labelSuffix))

		return label

	@classmethod
	def _customParameter(self, id, *args):
		return Tools.dictionaryGet(Settings.Custom[id], keys = list(args))

	@classmethod
	def _customSpecial(self, id):
		special = self._customParameter(id, 'special')
		if not special: special = {}
		if 'zero' in special: special[0] = special['zero']
		if 'none' in special: special[None] = special['none']
		if 'minimum' in special: special[False] = special['minimum']
		if 'maximum' in special: special[True] = special['maximum']
		return special

	@classmethod
	def _customUnit(self, id):
		try:
			type = self._customParameter(id, 'type')
			unit = self._customParameter(id, 'value', 'unit')

			if type == Settings.CustomSize:
				from lib.modules.convert import ConverterSize
				return {
					Settings.UnitByte : ConverterSize.Byte,
					Settings.UnitByteKilo : ConverterSize.ByteKilo,
					Settings.UnitByteMega : ConverterSize.ByteMega,
					Settings.UnitByteGiga : ConverterSize.ByteGiga,
					Settings.UnitByteTera : ConverterSize.ByteTera,
				}[unit]
			elif type == Settings.CustomDuration:
				from lib.modules.convert import ConverterDuration
				return {
					Settings.UnitSecond : ConverterDuration.UnitSecond,
					Settings.UnitMinute : ConverterDuration.UnitMinute,
					Settings.UnitHour : ConverterDuration.UnitHour,
					Settings.UnitDay : ConverterDuration.UnitDay,
					Settings.UnitWeek : ConverterDuration.UnitWeek,
					Settings.UnitMonth : ConverterDuration.UnitMonth,
					Settings.UnitYear : ConverterDuration.UnitYear,
				}[unit]
		except: pass
		return None

	@classmethod
	def _customValue(self, id, value = None, inverse = False, convert = True):
		# Special below-minimum or above-maximum.
		if value is True or value is False: return None if inverse else value

		type = self._customParameter(id, 'type')
		if type == Settings.CustomColor:
			from lib.modules.interface import Format
			value = Format.colorExtract(value)
		elif type == Settings.CustomIcon:
			pass
		else:
			special = self._customSpecial(id = id)
			if value in special and special[value] == Settings.SpecialDefault:
				default = self._customParameter(id, 'value', 'default')
				if not default is None:
					value = default
					convert = True

			if value == Settings.SpecialAutomatic: value = None

			if convert and not value is None:
				type = self._customParameter(id, 'type')
				unit = self._customUnit(id = id)

				if type == Settings.CustomNumber:
					value = int(value)
				elif type == Settings.CustomPercent:
					if inverse: value = int(float(value) * 100.0)
					else: value = float(value) / 100.0
				elif type == Settings.CustomSize:
					from lib.modules.convert import ConverterSize
					base = ConverterSize.Byte
					if inverse: value = int(ConverterSize(value, unit = base).value(unit = unit))
					else: value = ConverterSize(value, unit = unit).value(unit = base)
				elif type == Settings.CustomDuration:
					from lib.modules.convert import ConverterDuration
					base = ConverterDuration.UnitSecond
					if inverse: value = int(ConverterDuration(value, unit = base).value(unit = unit))
					else: value = int(ConverterDuration(value, unit = unit).value(unit = base))

		return value

	# id: the ID of a category, group, or setting.
	# idOld: the ID of the old settings format. Used for external addons that have not upgraded. Might not always work correctly.
	@classmethod
	def launch(self, id = None, idOld = None, addon = None, category = None, wait = False, background = False):
		from lib.modules import interface

		gaia = System.id()
		if addon is None: addon = gaia
		gaiaIs = addon == gaia
		if background is None: background = not gaiaIs

		if background:
			# Kodi has a bug.
			# Sometimes when an external addon's settings dialog is launched from Gaia's settings dialog, labels are empty show up in the external settings.
			# Maybe this is due to Gaia's labels in memory are being used.
			# Launching in an external process might solve this.
			# Problem seems to be gone. But if it comes back, change the function parameter to: "background = None".
			interface.Loader.show()
			parameters = {}
			if not id is None: parameters['id'] = id
			if not addon is None: parameters['addon'] = addon
			if not category is None: parameters['category'] = category
			System.executePlugin(action = 'settingsBackground', parameters = parameters)
		else:
			interface.Loader.hide()
			System.execute('Addon.OpenSettings(%s)' % addon)

			if id:
				try:
					data = self.cacheDataMain()
					level = self.level()

					entry = None
					index = None
					for i in ['setting', 'group', 'category']:
						try:
							entry = '<%s id="%s"' % (i, id)
							index = data.index(entry)
							break
						except: pass
					data = data[:index + len(entry)]

					# Exclude categories that are hidden, because all their children are also hidden.
					index = 0
					values = Regex.extract(data = data, expression = '<category(.*?)<\/category>', group = None, all = True, flags = Regex.FlagAllLines)
					for value in values:
						for i in range(Settings.LevelBasic, level + 1):
							if value.count('<level>%d</level>' % i) > 0:
								index += 1
								break

					System.execute('Control.SetFocus(%d)' % (index - 100))

					if not type == 'category':
						entry = '<category id="'
						index = data.rindex(entry)
						sub = data[index + len(entry):]

						# Count the total number of elements with and ID attribute.
						index = sub.count('id="')

						# The groups are also included in Kodi's focus index.
						index -= sub.count('<group')

						# Exclude groups that are hidden, because all their children are also hidden.
						# Must add 2 and not just 1 to the index. Not sure why, maybe Kodi adds something internally.
						values = Regex.extract(data = sub, expression = '<group(.*?)<\/group>', group = None, all = True, flags = Regex.FlagAllLines)
						for value in values:
							for i in range(Settings.LevelBasic, level + 1):
								if value.count('<level>%d</level>' % i) > 0:
									index += 2
									break

						# Ignore entries with a level lower than the level mode set by the user.
						for i in range(Settings.LevelInternal, level, -1):
							index -= sub.count('<level>%d</level>' % i)

						# For group selection, go to the first entry in the group.
						if ('<group id="%s"' % id) in sub: index += 1

						System.execute('Control.SetFocus(%d)' % (index - 80))
				except:
					Logger.log('Setting ID not found: ' + id)
			elif category:
				System.execute('Control.SetFocus(%d)' % (int(category) - 100)) # Convert to int, when passed from addon.py.
				if not idOld is None: System.execute('Control.SetFocus(%d)' % (int(idOld) - 80))

		if wait: self.launchWait(all = not gaiaIs)

	@classmethod
	def launchWait(self, all = True):
		# Wait for all types of dialogs, an not just the addon settings dialog, since some settings might open other types of dialogs.
		from lib.modules import interface
		interface.Dialog.dialogWait()

		# Some settings dialogs of external addons have other kinds of dialogs that can be shown from the settings.
		# Eg: The PM/RD Oauth dialog when authenticating an account from ResolveURL.
		# Wait a few seconds to make sure that all of those sub-dialogs are also closed.
		if all:
			interface.Loader.show()
			count = 0
			while True:
				if interface.Dialog.dialogVisible(loader = False): # Do not check for the loader, since we show the loader from this code.
					interface.Loader.hide()
					count = 0
					Time.sleep(0.1)
				else:
					interface.Loader.show()
					count += 1
					if count > 15:
						break # 3 seconds. 2 seconds is not enough.
					Time.sleep(0.2)
			interface.Loader.hide()

	@classmethod
	def launchData(self, id = None, wait = False):
		self.launch(id = self.idDataLabel(id), wait = wait)

	@classmethod
	def wait(self):
		while Settings.Busy > 0: Time.sleep(0.3)

	@classmethod
	def idDataLabel(self, id):
		return id + '.' + Settings.DataLabel

	@classmethod
	def idDataValue(self, id):
		return id + '.' + Settings.DataValue

	@classmethod
	def set(self, id, value, cached = False, database = False, background = False):
		Settings.Busy += 1
		if Tools.isStructure(value) or database:
			base = self._database()
			base._insert('INSERT OR IGNORE INTO %s (id) VALUES(?);' % Settings.Database, parameters = (id,))
			base._update('UPDATE %s SET data = ? WHERE id = ?;' % Settings.Database, parameters = (Converter.jsonTo(value), id))
			if cached or self.cacheEnabled(): self.cacheSet(id = id, value = value)
			Settings.Busy -= 1
		else:
			if value is True or value is False: # Use is an not ==, because checks type as well. Otherwise int/float might also be true.
				value = Converter.boolean(value, string = True)
			elif value is None:
				value = ''
			else:
				value = str(value)

			# Updating the settings takes 700ms+.
			# Allow them to update in a background thread.
			def _set(id, value, cached):
				if cached or self.cacheEnabled(): self.cacheSet(id = id, value = value)
				Settings.Lock.acquire()
				self._addon().setSetting(id = Converter.unicode(id), value = value)
				Settings.Lock.release()
				Settings.Busy -= 1
			if background:
				thread = Pool.thread(target = _set, args = (id, value, cached))
				thread.start()
			else:
				_set(id = id, value = value, cached = cached)

	@classmethod
	def setData(self, id, value, label = None, background = False):
		if not label is None:
			if label is True and Tools.isArray(value): label = len(value)
			self.setLabel(id = id, value = label, background = background)
		self.set(id = id, value = True, background = background) # Set the value in the XML file.
		self.set(id = self.idDataValue(id), value = value, database = True, background = background)

	@classmethod
	def setLabel(self, id, value, background = False):
		from lib.modules import interface
		self.set(id = self.idDataLabel(id), value = interface.Translation.string(value), background = background)

	@classmethod
	def setCustom(self, id, value, label = None, background = False):
		return self.customSet(id = id, value = value, label = label, background = background)

	# wait : number of seconds to sleep after command, since it takes a while to send.
	@classmethod
	def external(self, values, wait = 0.1):
		System.executePlugin(action = 'settingsExternal', parameters = values)
		Time.sleep(wait)

	# values is a dictionary.
	@classmethod
	def externalSave(self, values):
		if 'action' in values: del values['action']
		for id, value in values.items():
			self.set(id = id, value = value, external = False)

	@classmethod
	def default(self, id, database = False):
		try:
			# This does not always work.
			# Sometimes when writing the truncated data to file, Kodi later replaces the content with its in-memory version.
			'''
			data = self.cacheDataUser()
			expression = '(?:^|[\r\n]+)(.*?id\s*=\s*"%s".*?(?:[\r\n]+|$))'
			if not Tools.isArray(id): id = [id]

			for i in id:
				data = Regex.remove(data = data, expression = expression % i, group = 1)
				try: del Settings.CacheValuesUser[i]
				except: pass

			File.writeNow(self.pathProfile(), data)
			System.windowPropertySet(Settings.PropertyCacheDataUser, data)
			'''

			data = self.cacheDataUser()
			expression = '(?:^|[\r\n]+)(.*?id\s*=\s*"%s".*?(?:[\r\n]+|$))'
			if not Tools.isArray(id): id = [id]

			for i in id:
				value = None if database else self.raw(id = i, parameter = Settings.ParameterDefault)
				self.set(id = i, value = value, database = database)

				data = Regex.remove(data = data, expression = expression % i, group = 1)
				try: del Settings.CacheValuesUser[i]
				except: pass

			System.windowPropertySet(Settings.PropertyCacheDataUser, data)
		except: logger.error()

	@classmethod
	def defaultIs(self, id):
		return self.getString(id = id) == self.raw(id = id, parameter = Settings.ParameterDefault)

	@classmethod
	def defaultData(self, id):
		self.default([id, self.idDataLabel(id)], database = False)
		self.default([self.idDataValue(id)], database = True)

	# Retrieve the values directly from the original settings instead of the saved user XML.
	# This is for internal values/settings that have a default value. If these values change, they are not propagate to the user XML, since the value was already set from a previous version.
	@classmethod
	def raw(self, id, parameter = ParameterDefault, data = None):
		try:
			if data is None: data = self.cacheDataMain()

			if parameter == Settings.ParameterValue: expression = 'id\s*=\s*"' + id + '"[^\/]*?>(.*?)<'
			else: expression = 'id\s*=\s*"' + id + '".*?<' + parameter + '[^\/]*?>(.*?)<'

			match = re.search(expression, data, re.IGNORECASE | re.DOTALL)
			if match: return match.group(1)
		except: pass
		return None

	@classmethod
	def _getDatabase(self, id):
		try: return Converter.jsonFrom(self._database()._selectValue('SELECT data FROM %s WHERE id = "%s";' % (Settings.Database, id)))
		except: return None

	# Kodi reads the settings file on every request, which is slow.
	# If the cached option is used, the settings XML is read manually once, and all requests are done from there, which is faster.
	@classmethod
	def get(self, id, raw = False, cached = True, database = False):
		if cached and self.cacheEnabled(): return self.cacheGet(id = id, raw = raw, database = database)
		elif raw: return self.raw(id)
		elif database: return self._getDatabase(id)
		else: return self._addon().getSetting(Converter.unicode(id))

	@classmethod
	def getString(self, id, raw = False, cached = True):
		return self.get(id = id, raw = raw, cached = cached)

	@classmethod
	def getBoolean(self, id, raw = False, cached = True):
		return Converter.boolean(self.get(id = id, raw = raw, cached = cached))

	@classmethod
	def getBool(self, id, raw = False, cached = True):
		return self.getBoolean(id = id, raw = raw, cached = cached)

	@classmethod
	def getNumber(self, id, raw = False, cached = True):
		return self.getDecimal(id = id, raw = raw, cached = cached)

	@classmethod
	def getDecimal(self, id, raw = False, cached = True):
		value = self.get(id = id, raw = raw, cached = cached)
		try: return float(value)
		except: return 0

	@classmethod
	def getFloat(self, id, raw = False, cached = True):
		return self.getDecimal(id = id, raw = raw, cached = cached)

	@classmethod
	def getInteger(self, id, raw = False, cached = True):
		value = self.get(id = id, raw = raw, cached = cached)
		try: return int(value)
		except: return 0

	@classmethod
	def getInt(self, id, raw = False, cached = True):
		return self.getInteger(id = id, raw = raw, cached = cached)

	@classmethod
	def getObject(self, id, raw = False, cached = True, default = None):
		result = self.get(id = id, raw = raw, cached = cached, database = True)
		return default if result is None else result

	@classmethod
	def getList(self, id, raw = False, cached = True, default = []):
		return self.getObject(id = id, raw = raw, cached = cached, default = default)

	@classmethod
	def getData(self, id, raw = False, cached = True, default = None, verify = True):
		if self.getBoolean(id) or not verify: return self.getObject(id = self.idDataValue(id), raw = raw, cached = cached, default = default)
		else: return default # Eg: The "Default" button used in the settings dialog will reset the value to False.

	@classmethod
	def getDataObject(self, id, raw = False, cached = True, default = None, verify = True):
		return self.getData(id = id, raw = raw, cached = cached, default = default, verify = verify)

	@classmethod
	def getDataList(self, id, raw = False, cached = True, default = [], verify = True):
		return self.getData(id = id, raw = raw, cached = cached, default = default, verify = verify)

	@classmethod
	def getDataLabel(self, id, raw = False, cached = True):
		return self.getString(self.idDataLabel(id), raw = raw, cached = cached)

	@classmethod
	def getCustom(self, id, raw = False, cached = True, default = None):
		return self.customGet(id = id, raw = raw, cached = cached, default = default)

	@classmethod
	def has(self, id, raw = False, cached = True):
		result = self.get(id = id, raw = raw, cached = cached, database = True)
		return bool(result)


###################################################################
# CLEANUP
###################################################################

class Cleanup(object):

	@classmethod
	def _size(self, size):
		if size is None:
			from lib.modules.interface import Translation
			return Translation.string(35320)
		else:
			from lib.modules.convert import ConverterSize
			return ConverterSize(size).stringOptimal(places = 1)

	@classmethod
	def _clean(self, function, message = None, confirm = None):
		from lib.modules.interface import Translation, Dialog, Loader
		Loader.hide()

		if message: message = Translation.string(message) + ' '
		else: message = ''
		message += Translation.string(33042)

		if Dialog.option(title = 33989, message = message):
			if not confirm or Dialog.option(title = 33989, message = confirm):
				Loader.show()
				function()
				Dialog.notification(title = 33989, message = 33043, icon = Dialog.IconSuccess, duplicates = True)

	@classmethod
	def _help(self):
		from lib.modules.interface import Dialog
		Dialog.text(title = 33989, message = 'The cleanup feature deletes various files generated by Gaia over time. Cleaning will free up disc space and can help fix some sporadic problems. Be careful when clearing data, since the data will be lost forever and might require you to reinitialize certain things.[CR][CR]Clearing certain data, like the [I]Cache[/I], [I]Metadata[/I], and [I]Providers[/I], might temporarily slow down specific features in Gaia the first time they are used. For instance, menus containing movies or shows will take longer to load the first time they are opened after clearing the [I]Cache[/I]  or [I]Metadata[/I] , since metadata for the menus has to be re-retrieved and re-processed from external sources.[CR][CR]Some categories, like the [I]Library[/I]  and [I]Downloads[/I], have both a database storing metadata for internal use, and separate files stored on disk. If only the database is cleared, the corresponding entries will not show up in Gaia anymore, but the files stored on disc will remain.')

	@classmethod
	def _items(self):
		from lib.modules.interface import Loader, Dialog
		Loader.show()

		items = [
			{'title' : Dialog.prefixBack(33486), 'close' : True},
			{'title' : Dialog.prefixNext(33239), 'action' : self._help},
		]

		# General
		subitems = []
		subitems.append({'title' : 33027, 'size' : self.addonSize, 'clean' : self.addonClean, 'message' : 33899, 'confirm' : 33900})
		subitems.append({'title' : 35324, 'size' : self.menuSize, 'clean' : self.menuClean, 'message' : 33901, 'confirm' : 33902})
		items.append({'title' : 32310, 'items' : subitems})

		# Database
		subitems = []
		subitems.append({'title' : 33029, 'size' : self.databaseSize, 'clean' : self.databaseClean, 'message' : 33903})
		subitems.append({'title' : 33016, 'size' : self.databaseCacheSize, 'clean' : self.databaseCacheClean, 'message' : 33904})
		subitems.append({'title' : 33015, 'size' : self.databaseMetadataSize, 'clean' : self.databaseMetadataClean, 'message' : 33905})
		subitems.append({'title' : 33481, 'size' : self.databaseStreamSize, 'clean' : self.databaseStreamClean, 'message' : 36427})
		subitems.append({'title' : 32036, 'size' : self.databaseHistorySize, 'clean' : self.databaseHistoryClean, 'message' : 33906})
		subitems.append({'title' : 33041, 'size' : self.databaseSearchSize, 'clean' : self.databaseSearchClean, 'message' : 33907})
		subitems.append({'title' : 32330, 'size' : self.databasePlaybackSize, 'clean' : self.databasePlaybackClean, 'message' : 33908})
		subitems.append({'title' : 35566, 'size' : self.databaseTrailerSize, 'clean' : self.databaseTrailerClean, 'message' : 33909})
		subitems.append({'title' : 35119, 'size' : self.databaseShortcutSize, 'clean' : self.databaseShortcutClean, 'message' : 33911})
		items.append({'title' : 33775, 'items' : subitems})

		# Settings
		subitems = []
		subitems.append({'title' : 33029, 'size' : self.settingSize, 'clean' : self.settingClean, 'message' : 33912, 'confirm' : 33913})
		subitems.append({'title' : 33021, 'size' : self.settingCurrentSize, 'clean' : self.settingCurrentClean, 'message' : 33914, 'confirm' : 33913})
		subitems.append({'title' : 33773, 'size' : self.settingBackupSize, 'clean' : self.settingBackupClean, 'message' : 33915})
		items.append({'title' : 33011, 'items' : subitems})

		# Providers
		subitems = []
		subitems.append({'title' : 33029, 'size' : self.providerSize, 'clean' : self.providerClean, 'message' : 33954})
		subitems.append({'title' : 33026, 'size' : self.providerDatabaseSize, 'clean' : self.providerDatabaseClean, 'message' : 33955})
		subitems.append({'title' : 33319, 'size' : self.providerFileSize, 'clean' : self.providerFileClean, 'message' : 33956})
		items.append({'title' : 32345, 'items' : subitems})

		# Library
		subitems = []
		subitems.append({'title' : 33029, 'size' : self.librarySize, 'clean' : self.libraryClean, 'message' : 33957})
		subitems.append({'title' : 33026, 'size' : self.libraryDatabaseSize, 'clean' : self.libraryDatabaseClean, 'message' : 33958})
		subitems.append({'title' : 33319, 'size' : self.libraryFileSize, 'clean' : self.libraryFileClean, 'message' : 33964})
		items.append({'title' : 35170, 'items' : subitems})

		# Downloads
		subitems = []
		subitems.append({'title' : 33029, 'size' : self.downloadSize, 'clean' : self.downloadClean, 'message' : 33965, 'confirm' : 33966})
		subitems.append({'title' : 33026, 'size' : self.downloadDatabaseSize, 'clean' : self.downloadDatabaseClean, 'message' : 33967})
		subitems.append({'title' : 33319, 'size' : self.downloadFileSize, 'clean' : self.downloadFileClean, 'message' : 33969, 'confirm' : 33966})
		items.append({'title' : 32347, 'items' : subitems})

		# Folders
		subitems = []
		subitems.append({'title' : 33029, 'size' : self.folderSize, 'clean' : self.folderClean, 'message' : 33970})
		subitems.append({'title' : 33466, 'size' : self.folderTemporarySize, 'clean' : self.folderTemporaryClean, 'message' : 33971})
		subitems.append({'title' : 33896, 'size' : self.folderWindowSize, 'clean' : self.folderWindowClean, 'message' : 33972})
		subitems.append({'title' : 33898, 'size' : self.folderQrSize, 'clean' : self.folderQrClean, 'message' : 33973})
		items.append({'title' : 33895, 'items' : subitems})

		for i in range(len(items)):
			if 'items' in items[i]:
				for j in range(len(items[i]['items'])):
					items[i]['items'][j]['value'] = self._size(items[i]['items'][j]['size']())
					if not 'message' in items[i]['items'][j]: items[i]['items'][j]['message'] = None
					if not 'confirm' in items[i]['items'][j]: items[i]['items'][j]['confirm'] = None
					# NB: Pass values in as lambda parameters and not in the call of self.clean(...) itself, otherwise the function will always execute with the last values set in this for-loop (aka QR code values).
					items[i]['items'][j]['action'] = lambda function = items[i]['items'][j]['clean'], message = items[i]['items'][j]['message'], confirm = items[i]['items'][j]['confirm']: self._clean(function = function, message = message, confirm = confirm)

		Loader.hide()
		return items

	@classmethod
	def clean(self, settings = False):
		from lib.modules.interface import Dialog
		Dialog.information(title = 33989, refresh = self._items, reselect = Dialog.ReselectYes)
		if settings: Settings.launch(id = 'general.database.clean')

	@classmethod
	def addonSize(self):
		return File.sizeDirectory(System.profile())

	@classmethod
	def addonClean(self):
		File.deleteDirectory(System.profile())

	@classmethod
	def menuSize(self):
		total = 0
		total += self.databaseCacheSize()
		total += self.databaseMetadataSize()
		return total

	@classmethod
	def menuClean(self):
		self.databaseCacheClean()
		self.databaseMetadataClean()

	@classmethod
	def databaseSize(self):
		total = 0
		total += self.databaseCacheSize()
		total += self.databaseMetadataSize()
		total += self.databaseStreamSize()
		total += self.databaseHistorySize()
		total += self.databaseSearchSize()
		total += self.databasePlaybackSize()
		total += self.databaseTrailerSize()
		total += self.databaseShortcutSize()
		return total

	@classmethod
	def databaseClean(self):
		self.databaseCacheClean()
		self.databaseMetadataClean()
		self.databaseStreamClean()
		self.databaseHistoryClean()
		self.databaseSearchClean()
		self.databasePlaybackClean()
		self.databaseTrailerClean()
		self.databaseShortcutClean()

	@classmethod
	def databaseCacheSize(self):
		from lib.modules.cache import Cache
		return Cache.instance()._size()

	@classmethod
	def databaseCacheClean(self):
		from lib.modules.cache import Cache
		Cache.instance().clear(confirm = False)

	@classmethod
	def databaseMetadataSize(self):
		from lib.meta.cache import MetaCache
		return MetaCache.instance()._size()

	@classmethod
	def databaseMetadataClean(self):
		from lib.meta.cache import MetaCache
		MetaCache.instance().clear(confirm = False)

	@classmethod
	def databaseStreamSize(self):
		from lib.providers.core.manager import Manager
		return Manager.streamsDatabaseSize()

	@classmethod
	def databaseStreamClean(self):
		from lib.providers.core.manager import Manager
		Manager.streamsDatabaseClear()

	@classmethod
	def databaseHistorySize(self):
		from lib.modules.history import History
		return History()._size()

	@classmethod
	def databaseHistoryClean(self):
		from lib.modules.history import History
		History().clear(confirm = False)

	@classmethod
	def databaseSearchSize(self):
		from lib.modules.search import Search
		return Search()._size()

	@classmethod
	def databaseSearchClean(self):
		from lib.modules.search import Search
		Search().clear(confirm = False)

	@classmethod
	def databasePlaybackSize(self):
		from lib.modules.playback import Playback
		return Playback()._size()

	@classmethod
	def databasePlaybackClean(self):
		from lib.modules.playback import Playback
		Playback().clear(confirm = False)

	@classmethod
	def databaseTrailerSize(self):
		from lib.modules.video import Trailer
		return Trailer()._size()

	@classmethod
	def databaseTrailerClean(self):
		from lib.modules.video import Trailer
		Trailer().clear(confirm = False)

	@classmethod
	def databaseShortcutSize(self):
		from lib.modules.shortcut import Shortcut
		return Shortcut.instance()._size()

	@classmethod
	def databaseShortcutClean(self):
		from lib.modules.shortcut import Shortcut
		Shortcut.instance().clear(confirm = False)

	@classmethod
	def settingSize(self):
		return self.settingCurrentSize() + self.settingBackupSize()

	@classmethod
	def settingClean(self):
		self.settingCurrentClean()
		self.settingBackupClean()

	@classmethod
	def settingCurrentSize(self):
		return Settings.size()

	@classmethod
	def settingCurrentClean(self):
		Settings.clear(initialize = True)

	@classmethod
	def settingBackupSize(self):
		return Backup.automaticSize()

	@classmethod
	def settingBackupClean(self):
		Backup.automaticClear()

	@classmethod
	def providerSize(self):
		return self.providerDatabaseSize() + self.providerFileSize()

	@classmethod
	def providerClean(self):
		self.providerDatabaseClean()
		self.providerFileClean()

	@classmethod
	def providerDatabaseSize(self):
		from lib.providers.core.manager import Manager
		return Manager.databaseSize(streams = False)

	@classmethod
	def providerDatabaseClean(self):
		from lib.providers.core.manager import Manager
		Manager.databaseClear(streams = False)

	@classmethod
	def providerFileSize(self):
		from lib.providers.core.manager import Manager
		return Manager.dataSize()

	@classmethod
	def providerFileClean(self):
		from lib.providers.core.manager import Manager
		Manager.dataClear()

	@classmethod
	def librarySize(self):
		size = self.libraryFileSize()
		return self.libraryDatabaseSize() + (size if size and size > 0 else 0)

	@classmethod
	def libraryClean(self):
		self.libraryDatabaseClean()
		self.libraryFileClean()

	@classmethod
	def libraryDatabaseSize(self):
		from lib.modules.library import Library
		return Library.sizeDatabase()

	@classmethod
	def libraryDatabaseClean(self):
		from lib.modules.library import Library
		Library.clearDatabase()

	@classmethod
	def libraryFileSize(self):
		from lib.modules.library import Library
		return Library.sizeFile()

	@classmethod
	def libraryFileClean(self):
		from lib.modules.library import Library
		Library.clearFile()

	@classmethod
	def downloadSize(self):
		size = self.downloadFileSize()
		return self.downloadDatabaseSize() + (size if size and size > 0 else 0)

	@classmethod
	def downloadClean(self):
		self.downloadDatabaseClean()
		self.downloadFileClean()

	@classmethod
	def downloadDatabaseSize(self):
		from lib.modules.downloader import Downloader
		return Downloader.sizeDatabase()

	@classmethod
	def downloadDatabaseClean(self):
		from lib.modules.downloader import Downloader
		Downloader.cleanDatabase()

	@classmethod
	def downloadFileSize(self):
		from lib.modules.downloader import Downloader
		return Downloader.sizeFile()

	@classmethod
	def downloadFileClean(self):
		from lib.modules.downloader import Downloader
		Downloader.cleanFile()

	@classmethod
	def folderSize(self):
		return self.folderTemporarySize() + self.folderWindowSize() + self.folderQrSize()

	@classmethod
	def folderClean(self):
		self.folderTemporaryClean()
		self.folderWindowClean()
		self.folderQrClean()

	@classmethod
	def folderTemporarySize(self):
		return File.sizeDirectory(System.temporary(make = False))

	@classmethod
	def folderTemporaryClean(self):
		System.temporaryClear()

	@classmethod
	def folderWindowSize(self):
		from lib.modules.window import Window
		return File.sizeDirectory(Window._pathWindow(kodi = False))

	@classmethod
	def folderWindowClean(self):
		from lib.modules.window import Window
		Window.clean()

	@classmethod
	def folderQrSize(self):
		from lib.modules.qr import Qr
		return Qr.size()

	@classmethod
	def folderQrClean(self):
		from lib.modules.qr import Qr
		Qr.clean()

###################################################################
# MEDIA
###################################################################

class Media(object):

	Unknown		= None

	# BASE TYPES
	# Default types also used by Kodi directly.
	Movie			= 'movie'
	Set				= 'set'
	Show			= 'show'
	Season			= 'season'
	Episode			= 'episode'
	Person			= 'person'
	Mixed			= 'mixed' 			# Mixture of movies and shows.
	Pack			= 'pack' 			# Show season/episode pack.

	# ADDITIONAL TYPES
	# Custom types not used by Kodi directly.
	Recap 			= 'recap'			# Season or set recaps.
	Extra			= 'extra'			# Extra season or set content.
	List			= 'list'			# List containing any of the other types.
	Company			= 'company'			# Studio, network, or other company.

	# DERIVED TYPES
	# A subtype to the base types.
	Feature			= 'feature'			# Feature full-length movies.
	Short			= 'short'			# Short films. IMDb: full support (through type) | TMDb: limited support (through keywords or duration) | TVDb: no support (cannot filter by duration) | Trakt: limited support (through genre or duration).
	Special			= 'special'			# Special films and TV specials. IMDb: full support (through type) | TMDb: limited support (through genre, although only TV movies) | TVDb: limited support (through genre, although only TV movies) | Trakt: limited support (through keywords, although not great).
	Multi			= 'multi'			# Series with mutiple seasons.
	Mini			= 'mini'			# Mini-series with a single season. IMDb: full support (through type) | TMDb: full support (through type) | TVDb: full support (through genre) | Trakt: no support (has a mini-series genre, but nothing labeled as such).

	# SERIE TYPES
	# Season and episode types.
	Standard		= 'standard'		# A standard season or episode.
	Exclusive		= 'exclusive'		# A special season (S0) or episode (E0). Do not use "special", since that is reserved for TV specials.
	Premiere		= 'premiere'		# A first season of a show or a first episode of a season.
	Finale			= 'finale'			# A last season of a show or a last episode of a season.
	Outer			= 'outer'			# A first or last episode of a show.
	Inner			= 'inner'			# A first or last episode of a season.
	Middle			= 'middle'			# A first or last episode in the middle of a season that is split into mutiple parts.

	# RELEASE TYPES
	# How the media was released.
	Cinema			= 'cinema'			# Released in theaters.
	Television		= 'television'		# Released for TV or home streaming. IMDb: full support (through type) | TMDb: full support (through genre) | TVDb: full support (through genre) | Trakt: limited support (through keywords, although not great).

	# TOPIC TYPES
	# Content of the media as a subtype to the base types, or genres.
	Anima			= 'anima'			# Animation of all types.
	Anime			= 'anime'			# Japanese anime. IMDb: limited support (through keywords, but very few) | TMDb: full support (through keywords) | TVDb: full support (through genre) | Trakt: full support (through genre).
	Donghua			= 'donghua'			# Chinese donghua. IMDb: limited support (through keywords, but very few) | TMDb: full support (through keywords) | TVDb: limited support (listed as Anime genre with China as the country/language) | Trakt: full support (through genre).
	Docu			= 'docu'			# Documentaries.
	Family			= 'family'			# Family and children genres.
	Music			= 'music'			# Music and musical genres.
	Sport			= 'sport'			# Sports and sporting events genres.
	Telly			= 'telly'			# Reality-TV, talk-shows, games-shows, award-shows, news, travel, food, and home-and-garden.
	Soap			= 'soap'			# Soap operas.

	# MOOD TYPES
	# Combination of genres.
	Loved 			= 'loved'			# Romance
	Relaxed			= 'relaxed'			# Drama, Family
	Cheerful 		= 'cheerful'		# Comedy
	Imaginary		= 'imaginary'		# Fantasy, Science-Fiction, Superhero
	Suspicious		= 'suspicious'		# Thriller, Mystery, Suspense
	Adventurous		= 'adventurous'		# Adventure, Action
	Aggressive		= 'aggressive'		# Action, Crime, War, Martial, Western, Eastern
	Frightened		= 'frightened'		# Horror, Disaster
	Curious			= 'curious'			# History, Documentary, Biography, Politics
	Energetic		= 'energetic'		# Sport, Sporting, Travel, Holiday, Music, Musical
	Indifferent		= 'indifferent'		# Reality, Soap, Talk, Game, Home, Food, Award
	Experimental	= 'experimental'	# Noir, Short, Indie, Special, Fan, Television

	# AGE TYPES
	Future			= 'future'			# Released in the future.
	Recent			= 'recent'			# Released over the past 2 years.
	Modern			= 'modern'			# Released between 2010 and now.
	Mature			= 'mature'			# Released between 1990 and 2010.
	Vintage			= 'vintage'			# Released between 1960 and 1990.
	Ancient			= 'ancient'			# Released before 1960.

	# QUALITY TYPES
	Great			= 'great'			# Rating above 8.0.
	Good			= 'good'			# Rating between 7.0 and 8.0.
	Fair			= 'fair'			# Rating between 6.0 and 7.0.
	Poor			= 'poor'			# Rating between 4.0 and 6.0.
	Bad				= 'bad'				# Rating below 4.0.

	# AUDIENCE TYPES
	Kid				= 'kid'				# Content for kids as specified by the age settings.
	Teen			= 'teen'			# Content for teens as specified by the age settings.
	Adult			= 'adult'			# Content for adults as specified by the age settings.

	# ENTERPRISE TYPES
	Studio			= 'studio'			# Studios only.
	Network			= 'network'			# Networks only.
	Vendor			= 'vendor'			# Vendors only.
	Producer		= 'producer'		# Studios only at the moment.
	Broadcaster		= 'broadcaster'		# Studios and networks.
	Distributor		= 'distributor'		# Studios, networks, and vendors.
	Original		= 'original'		# Studios and networks, excluding other major companies.

	# REGION TYPES
	# Content from a specific country or language.
	# Check MetaTools for which countries and languages are included.
	Local			= 'local'			# Local cinema according to the user's settings.
	American		= 'american'		# Hollywood, US, and Canadian cinema.
	Oceanic			= 'oceanic'			# Australian and New Zealand cinema.
	British			= 'british'			# British cinema.
	French			= 'french'			# French cinema. Might include other countries than France, like Canada.
	Germanic		= 'germanic'		# German cinema. Might include other countries than Germany, like Austria and Switzerland.
	Spanish			= 'spanish'			# Spanish cinema. Might include other countries than Spain, like latin american countries.
	Portuguese		= 'portuguese'		# Portuguese cinema. Might include other countries than Portugal, like latin american countries.
	Italian			= 'italian'			# Italian cinema.
	Russian			= 'russian'			# Russian cinema.
	Turkish			= 'turkish'			# Turkish cinema.
	Benelux			= 'benelux'			# Netherlands, Belgium, and Luxembourg cinema.
	Nordic 			= 'nordic'			# Scandinavia cinema.
	Slavic 			= 'slavic'			# Slavic cinema.
	Balkan 			= 'balkan'			# Balkan cinema.
	Baltic			= 'baltic'			# Baltic cinema.
	Mexican 		= 'mexican'			# Mexican cinema.
	Latin 			= 'latin'			# Latin american cinema.
	Indian			= 'indian'			# Bollywood and other Indian cinema. Might include other countries than India, like Sri Lanka.
	Chinese			= 'chinese'			# Chinese cinema. Might include other countries than China, like Taiwan and Hong Kong.
	Japanese		= 'japanese'		# Japanese cinema.
	Korean			= 'korean'			# Korean cinema. Mostly South Korean, but might also include North Korea.
	Eastern			= 'eastern'			# Southeast Asia cinema.
	Arabian			= 'arabian'			# Arabic cinema.
	African			= 'african'			# African cinema. Includes all african countries.

	# PLEASURE TYPES

	Drug			= 'drug'
	Cannabis		= 'cannabis'
	Psychedelic		= 'psychedelic'
	Cocaine			= 'cocaine'
	Alcohol			= 'alcohol'
	Pill			= 'pill'

	Love			= 'love'
	Romance			= 'romance'
	Kiss			= 'kiss'
	Lgbtq			= 'lgbtq'
	Gay				= 'gay'
	Lesbian			= 'lesbian'

	Sex				= 'sex'
	Nudity			= 'nudity'
	Erotica			= 'erotica'
	Pornography		= 'pornography'
	Prostitution	= 'prostitution'
	Orgy			= 'orgy'

	Violence		= 'violence'
	Robbery			= 'robbery'
	Smuggle			= 'smuggle'
	Hostage			= 'hostage'
	Torture			= 'torture'
	Murder			= 'murder'

	Religion		= 'religion'
	Cult			= 'cult'
	Secret			= 'secret'
	Terrorism		= 'terrorism'
	Psycho			= 'psycho'
	Sadism			= 'sadism'

	Profanity		= 'profanity'
	Blasphemy		= 'blasphemy'
	Sarcasm			= 'sarcasm'
	Parody			= 'parody'
	Satire			= 'satire'
	Humor			= 'humor'

	# EXPLORE TYPES
	# These types are not used to label media, but to retrieve subsections in the discover menus, filtered and/or sorted by a specific attributes.
	All				= 'all'				# All unfiltered releases.
	New				= 'new'				# New releases. Typically sorted descending by release date.
	Home			= 'home'			# Home releases for movies. Typically sorted descending by release date.
	Best			= 'best'			# Best rated titles. Typically sorted descending by rating.
	Worst			= 'worst'			# Worst rated titles. Typically sorted ascending by rating.
	Prestige		= 'prestige'		# High quality releases. Typically filtered by a minimum rating and minimum number of votes.
	Popular			= 'popular'			# Most popular titles. Typically sorted descending by number of watches or votes.
	Unpopular		= 'unpopular'		# Least popular titles. Typically sorted ascending by number of watches or votes.
	Viewed			= 'viewed'			# Widely  viewed titles. Typically filtered by a minimum number of votes.
	Gross			= 'gross'			# Highest grossing box office hits. Typically sorted descending by gross income.
	Award			= 'award'			# Award winners.
	Trend			= 'trend'			# Currently trending titles. Typically filtered/sorted by current temporary trendiness or popularity.

	class _Bonus():
		def __eq__(self, media):
			return (
				media == Media.Recap or
				media == Media.Extra
			)

	class _Film():
		def __eq__(self, media):
			return (
				media == Media.Movie or
				media == Media.Feature or
				media == Media.Short or
				media == Media.Special
			)

	class _Serie():
		def __eq__(self, media):
			return (
				media == Media.Show or
				media == Media.Season or
				media == Media.Episode or

				media == Media.Standard or
				media == Media.Exclusive or
				media == Media.Premiere or
				media == Media.Finale or
				media == Media.Outer or
				media == Media.Inner or
				media == Media.Middle or

				media == Media.Multi or
				media == Media.Mini or

				media == Media.Telly or
				media == Media.Soap
			)

	class _Topic():
		def __eq__(self, media):
			return (
				media == Media.Anima or
				media == Media.Anime or
				media == Media.Donghua or
				media == Media.Docu or
				media == Media.Family or
				media == Media.Music or
				media == Media.Sport or
				media == Media.Telly or
				media == Media.Soap
			)

	class _Mood():
		def __eq__(self, media):
			return (
				media == Media.Loved or
				media == Media.Relaxed or
				media == Media.Cheerful or
				media == Media.Imaginary or
				media == Media.Suspicious or
				media == Media.Adventurous or
				media == Media.Aggressive or
				media == Media.Frightened or
				media == Media.Curious or
				media == Media.Energetic or
				media == Media.Indifferent or
				media == Media.Experimental
			)

	class _Age():
		def __eq__(self, media):
			return (
				media == Media.Future or
				media == Media.Recent or
				media == Media.Modern or
				media == Media.Mature or
				media == Media.Vintage or
				media == Media.Ancient
			)

	class _Quality():
		def __eq__(self, media):
			return (
				media == Media.Great or
				media == Media.Good or
				media == Media.Fair or
				media == Media.Poor or
				media == Media.Bad
			)

	class _Audience():
		def __eq__(self, media):
			return (
				media == Media.Kid or
				media == Media.Teen or
				media == Media.Adult
			)

	class _Enterprise():
		def __eq__(self, media):
			return (
				media == Media.Studio or
				media == Media.Network or
				media == Media.Vendor or
				media == Media.Producer or
				media == Media.Broadcaster or
				media == Media.Distributor or
				media == Media.Original
			)

	class _Region():
		def __eq__(self, media):
			return (
				media == Media.Local or
				media == Media.American or
				media == Media.Oceanic or
				media == Media.British or
				media == Media.French or
				media == Media.Germanic or
				media == Media.Spanish or
				media == Media.Portuguese or
				media == Media.Italian or
				media == Media.Russian or
				media == Media.Turkish or
				media == Media.Benelux or
				media == Media.Nordic or
				media == Media.Slavic or
				media == Media.Balkan or
				media == Media.Baltic or
				media == Media.Mexican or
				media == Media.Latin or
				media == Media.Indian or
				media == Media.Chinese or
				media == Media.Japanese or
				media == Media.Korean or
				media == Media.Eastern or
				media == Media.Arabian or
				media == Media.African
			)

	class _Substance():
		def __eq__(self, media):
			return (
				media == Media.Drug or
				media == Media.Cannabis or
				media == Media.Psychedelic or
				media == Media.Cocaine or
				media == Media.Alcohol or
				media == Media.Pill
			)

	class _Relation():
		def __eq__(self, media):
			return (
				media == Media.Love or
				media == Media.Romance or
				media == Media.Kiss or
				media == Media.Lgbtq or
				media == Media.Gay or
				media == Media.Lesbian
			)

	class _Intimacy():
		def __eq__(self, media):
			return (
				media == Media.Sex or
				media == Media.Nudity or
				media == Media.Erotica or
				media == Media.Pornography or
				media == Media.Prostitution or
				media == Media.Orgy
			)

	class _Felony():
		def __eq__(self, media):
			return (
				media == Media.Violence or
				media == Media.Robbery or
				media == Media.Smuggle or
				media == Media.Hostage or
				media == Media.Torture or
				media == Media.Murder

			)

	class _Society():
		def __eq__(self, media):
			return (
				media == Media.Religion or
				media == Media.Cult or
				media == Media.Secret or
				media == Media.Terrorism or
				media == Media.Psycho or
				media == Media.Sadism
			)

	class _Lingual():
		def __eq__(self, media):
			return (
				media == Media.Profanity or
				media == Media.Blasphemy or
				media == Media.Sarcasm or
				media == Media.Parody or
				media == Media.Satire or
				media == Media.Humor
			)

	class _Explore():
		def __eq__(self, media):
			return (
				media == Media.All or
				media == Media.New or
				media == Media.Home or
				media == Media.Best or
				media == Media.Worst or
				media == Media.Prestige or
				media == Media.Popular or
				media == Media.Unpopular or
				media == Media.Viewed or
				media == Media.Gross or
				media == Media.Award or
				media == Media.Trend
			)

	# Can be used as follows:
	# if media == Media.Serie: ...
	Bonus		= _Bonus()
	Film		= _Film()
	Serie		= _Serie()
	Topic		= _Topic()
	Mood		= _Mood()
	Age			= _Age()
	Quality		= _Quality()
	Audience	= _Audience()
	Enterprise	= _Enterprise()
	Region		= _Region()
	Substance	= _Substance()
	Relation	= _Relation()
	Intimacy	= _Intimacy()
	Felony		= _Felony()
	Society		= _Society()
	Lingual		= _Lingual()
	Explore		= _Explore()

	class _Pleasure():
		def __eq__(self, media):
			return (
				media == Media.Substance or
				media == Media.Relation or
				media == Media.Intimacy or
				media == Media.Felony or
				media == Media.Society or
				media == Media.Lingual
			)

	Pleasure	= _Pleasure()

	class _Niche():
		def __eq__(self, media):
			return (
				media == Media.Short or
				media == Media.Special or
				media == Media.Mini or
				media == Media.Television or

				media == Media.Topic or
				media == Media.Mood or
				media == Media.Age or
				media == Media.Quality or
				media == Media.Audience or
				media == Media.Enterprise or
				media == Media.Region or
				media == Media.Pleasure
			)
	Niche		= _Niche()

	Separator	= '-'

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def index(self, media, type):
		media = self.stringFrom(media = media)
		try: return media.index(type)
		except: return None

	@classmethod
	def type(self, media, type):
		media = self.stringFrom(media = media)
		try: return media[media.index(type)]
		except: return None

	@classmethod
	def remove(self, media, type):
		media = self.stringFrom(media = media)
		try: return [i for i in media if not i == type]
		except: return media # media is None.

	@classmethod
	def add(self, media, type, copy = False):
		media = self.stringFrom(media = media)
		if not media: media = []
		elif copy: media = Tools.copy(media)
		if type:
			if Tools.isArray(type): media.extend(type)
			else: media.append(type)
		return media

	##############################################################################
	# STRING
	##############################################################################

	@classmethod
	def stringTo(self, media):
		if not media: return None
		elif Tools.isArray(media): return Media.Separator.join(media)
		else: return str(media)

	@classmethod
	def stringFrom(self, media, single = False):
		if media is None: return Media.Unknown
		elif not Tools.isString(media): return media
		media = media.split(Media.Separator)
		if single and len(media) == 1: return media[0]
		else: return media

	##############################################################################
	# IS - GENERAL
	##############################################################################

	@classmethod
	def isMedia(self, media, type, full = False):
		if not type: return True
		if Tools.isArray(media):
			if Tools.isArray(type): return all(i in type for i in media) if full else any(i in type for i in media)
			else: return all(i == type for i in media) if full else any(i == type for i in media)
		else:
			return media == type

	@classmethod
	def isSingle(self, media):
		if Tools.isArray(media): return len(media) <= 1
		elif media: return not Media.Separator in media
		else: return True

	@classmethod
	def isBonus(self, media):
		return self.isMedia(media = media, type = Media.Bonus)

	@classmethod
	def isFilm(self, media):
		return self.isMedia(media = media, type = Media.Film)

	@classmethod
	def isSerie(self, media):
		return self.isMedia(media = media, type = Media.Serie)

	@classmethod
	def isTopic(self, media):
		return self.isMedia(media = media, type = Media.Topic)

	@classmethod
	def isMood(self, media):
		return self.isMedia(media = media, type = Media.Mood)

	@classmethod
	def isAge(self, media):
		return self.isMedia(media = media, type = Media.Age)

	@classmethod
	def isQuality(self, media):
		return self.isMedia(media = media, type = Media.Quality)

	@classmethod
	def isAudience(self, media):
		return self.isMedia(media = media, type = Media.Audience)

	@classmethod
	def isEnterprise(self, media):
		return self.isMedia(media = media, type = Media.Enterprise)

	@classmethod
	def isRegion(self, media):
		return self.isMedia(media = media, type = Media.Region)

	@classmethod
	def isPleasure(self, media):
		return self.isMedia(media = media, type = Media.Pleasure)

	@classmethod
	def isExplore(self, media):
		return self.isMedia(media = media, type = Media.Explore)

	@classmethod
	def isNiche(self, media):
		return self.isMedia(media = media, type = Media.Niche)

	##############################################################################
	# IS - BASE
	##############################################################################

	@classmethod
	def isMovie(self, media):
		return self.isMedia(media = media, type = Media.Movie)

	@classmethod
	def isSet(self, media):
		return self.isMedia(media = media, type = Media.Set)

	@classmethod
	def isShow(self, media):
		return self.isMedia(media = media, type = Media.Show)

	@classmethod
	def isSeason(self, media):
		return self.isMedia(media = media, type = Media.Season)

	@classmethod
	def isEpisode(self, media):
		return self.isMedia(media = media, type = Media.Episode)

	@classmethod
	def isPerson(self, media):
		return self.isMedia(media = media, type = Media.Person)

	@classmethod
	def isMixed(self, media):
		return self.isMedia(media = media, type = Media.Mixed)

	@classmethod
	def isPack(self, media):
		return self.isMedia(media = media, type = Media.Pack)

	##############################################################################
	# IS - ADDITIONAL
	##############################################################################

	@classmethod
	def isRecap(self, media):
		return self.isMedia(media = media, type = Media.Recap)

	@classmethod
	def isExtra(self, media):
		return self.isMedia(media = media, type = Media.Extra)

	@classmethod
	def isList(self, media):
		return self.isMedia(media = media, type = Media.List)

	@classmethod
	def isCompany(self, media):
		return self.isMedia(media = media, type = Media.Company)

	##############################################################################
	# IS - DERIVED
	##############################################################################

	@classmethod
	def isFeature(self, media):
		return self.isMedia(media = media, type = Media.Feature)

	@classmethod
	def isShort(self, media):
		return self.isMedia(media = media, type = Media.Short)

	@classmethod
	def isSpecial(self, media):
		return self.isMedia(media = media, type = Media.Special)

	@classmethod
	def isMulti(self, media):
		return self.isMedia(media = media, type = Media.Multi)

	@classmethod
	def isMini(self, media):
		return self.isMedia(media = media, type = Media.Mini)

	##############################################################################
	# IS - SERIE
	##############################################################################

	@classmethod
	def isStandard(self, media):
		return self.isMedia(media = media, type = Media.Standard)

	@classmethod
	def isExclusive(self, media):
		return self.isMedia(media = media, type = Media.Exclusive)

	@classmethod
	def isPremiere(self, media):
		return self.isMedia(media = media, type = Media.Premiere)

	@classmethod
	def isFinale(self, media):
		return self.isMedia(media = media, type = Media.Finale)

	@classmethod
	def isOuter(self, media):
		return self.isMedia(media = media, type = Media.Outer)

	@classmethod
	def isInner(self, media):
		return self.isMedia(media = media, type = Media.Inner)

	@classmethod
	def isMiddle(self, media):
		return self.isMedia(media = media, type = Media.Middle)

	##############################################################################
	# IS - RELEASE
	##############################################################################

	@classmethod
	def isCinema(self, media):
		return self.isMedia(media = media, type = Media.Cinema)

	@classmethod
	def isTelevision(self, media):
		return self.isMedia(media = media, type = Media.Television)

	##############################################################################
	# IS - TOPIC
	##############################################################################

	@classmethod
	def isAnima(self, media):
		return self.isMedia(media = media, type = Media.Anima)

	@classmethod
	def isAnime(self, media):
		return self.isMedia(media = media, type = Media.Anime)

	@classmethod
	def isDonghua(self, media):
		return self.isMedia(media = media, type = Media.Donghua)

	@classmethod
	def isDocu(self, media):
		return self.isMedia(media = media, type = Media.Docu)

	@classmethod
	def isFamily(self, media):
		return self.isMedia(media = media, type = Media.Family)

	@classmethod
	def isMusic(self, media):
		return self.isMedia(media = media, type = Media.Music)

	@classmethod
	def isSport(self, media):
		return self.isMedia(media = media, type = Media.Sport)

	@classmethod
	def isTelly(self, media):
		return self.isMedia(media = media, type = Media.Telly)

	@classmethod
	def isSoap(self, media):
		return self.isMedia(media = media, type = Media.Soap)

	##############################################################################
	# IS - MOOD
	##############################################################################

	@classmethod
	def isLoved(self, media):
		return self.isMedia(media = media, type = Media.Loved)

	@classmethod
	def isRelaxed(self, media):
		return self.isMedia(media = media, type = Media.Relaxed)

	@classmethod
	def isCheerful(self, media):
		return self.isMedia(media = media, type = Media.Cheerful)

	@classmethod
	def isImaginary(self, media):
		return self.isMedia(media = media, type = Media.Imaginary)

	@classmethod
	def isSuspicious(self, media):
		return self.isMedia(media = media, type = Media.Suspicious)

	@classmethod
	def isAdventurous(self, media):
		return self.isMedia(media = media, type = Media.Adventurous)

	@classmethod
	def isAggressive(self, media):
		return self.isMedia(media = media, type = Media.Aggressive)

	@classmethod
	def isFrightened(self, media):
		return self.isMedia(media = media, type = Media.Frightened)

	@classmethod
	def isCurious(self, media):
		return self.isMedia(media = media, type = Media.Curious)

	@classmethod
	def isEnergetic(self, media):
		return self.isMedia(media = media, type = Media.Energetic)

	@classmethod
	def isIndifferent(self, media):
		return self.isMedia(media = media, type = Media.Indifferent)

	@classmethod
	def isExperimental(self, media):
		return self.isMedia(media = media, type = Media.Experimental)

	##############################################################################
	# IS - AGE
	##############################################################################

	@classmethod
	def isFuture(self, media):
		return self.isMedia(media = media, type = Media.Future)

	@classmethod
	def isRecent(self, media):
		return self.isMedia(media = media, type = Media.Recent)

	@classmethod
	def isModern(self, media):
		return self.isMedia(media = media, type = Media.Modern)

	@classmethod
	def isMature(self, media):
		return self.isMedia(media = media, type = Media.Mature)

	@classmethod
	def isVintage(self, media):
		return self.isMedia(media = media, type = Media.Vintage)

	@classmethod
	def isAncient(self, media):
		return self.isMedia(media = media, type = Media.Ancient)

	##############################################################################
	# IS - QUALITY
	##############################################################################

	@classmethod
	def isGreat(self, media):
		return self.isMedia(media = media, type = Media.Great)

	@classmethod
	def isGood(self, media):
		return self.isMedia(media = media, type = Media.Good)

	@classmethod
	def isFair(self, media):
		return self.isMedia(media = media, type = Media.Fair)

	@classmethod
	def isPoor(self, media):
		return self.isMedia(media = media, type = Media.Poor)

	@classmethod
	def isBad(self, media):
		return self.isMedia(media = media, type = Media.Bad)

	##############################################################################
	# IS - AUDIENCE
	##############################################################################

	@classmethod
	def isKid(self, media):
		return self.isMedia(media = media, type = Media.Kid)

	@classmethod
	def isTeen(self, media):
		return self.isMedia(media = media, type = Media.Teen)

	@classmethod
	def isAdult(self, media):
		return self.isMedia(media = media, type = Media.Adult)

	##############################################################################
	# IS - ENTERPRISE
	##############################################################################

	@classmethod
	def isStudio(self, media):
		return self.isMedia(media = media, type = Media.Studio)

	@classmethod
	def isNetwork(self, media):
		return self.isMedia(media = media, type = Media.Network)

	@classmethod
	def isVendor(self, media):
		return self.isMedia(media = media, type = Media.Vendor)

	@classmethod
	def isProducer(self, media):
		return self.isMedia(media = media, type = Media.Producer)

	@classmethod
	def isBroadcaster(self, media):
		return self.isMedia(media = media, type = Media.Broadcaster)

	@classmethod
	def isDistributor(self, media):
		return self.isMedia(media = media, type = Media.Distributor)

	@classmethod
	def isOriginal(self, media):
		return self.isMedia(media = media, type = Media.Original)

	##############################################################################
	# IS - REGION
	##############################################################################

	@classmethod
	def isLocal(self, media):
		return self.isMedia(media = media, type = Media.Local)

	@classmethod
	def isAmerican(self, media):
		return self.isMedia(media = media, type = Media.American)

	@classmethod
	def isOceanic(self, media):
		return self.isMedia(media = media, type = Media.Oceanic)

	@classmethod
	def isBritish(self, media):
		return self.isMedia(media = media, type = Media.British)

	@classmethod
	def isFrench(self, media):
		return self.isMedia(media = media, type = Media.French)

	@classmethod
	def isGermanic(self, media):
		return self.isMedia(media = media, type = Media.Germanic)

	@classmethod
	def isSpanish(self, media):
		return self.isMedia(media = media, type = Media.Spanish)

	@classmethod
	def isPortuguese(self, media):
		return self.isMedia(media = media, type = Media.Portuguese)

	@classmethod
	def isItalian(self, media):
		return self.isMedia(media = media, type = Media.Italian)

	@classmethod
	def isRussian(self, media):
		return self.isMedia(media = media, type = Media.Russian)

	@classmethod
	def isTurkish(self, media):
		return self.isMedia(media = media, type = Media.Turkish)

	@classmethod
	def isBenelux(self, media):
		return self.isMedia(media = media, type = Media.Benelux)

	@classmethod
	def isNordic(self, media):
		return self.isMedia(media = media, type = Media.Nordic)

	@classmethod
	def isSlavic(self, media):
		return self.isMedia(media = media, type = Media.Slavic)

	@classmethod
	def isBalkan(self, media):
		return self.isMedia(media = media, type = Media.Balkan)

	@classmethod
	def isBaltic(self, media):
		return self.isMedia(media = media, type = Media.Baltic)

	@classmethod
	def isMexican(self, media):
		return self.isMedia(media = media, type = Media.Mexican)

	@classmethod
	def isLatin(self, media):
		return self.isMedia(media = media, type = Media.Latin)

	@classmethod
	def isIndian(self, media):
		return self.isMedia(media = media, type = Media.Indian)

	@classmethod
	def isChinese(self, media):
		return self.isMedia(media = media, type = Media.Chinese)

	@classmethod
	def isJapanese(self, media):
		return self.isMedia(media = media, type = Media.Japanese)

	@classmethod
	def isKorean(self, media):
		return self.isMedia(media = media, type = Media.Korean)

	@classmethod
	def isEastern(self, media):
		return self.isMedia(media = media, type = Media.Eastern)

	@classmethod
	def isArabian(self, media):
		return self.isMedia(media = media, type = Media.Arabian)

	@classmethod
	def isAfrican(self, media):
		return self.isMedia(media = media, type = Media.African)

	##############################################################################
	# IS - PLEASURE
	##############################################################################

	@classmethod
	def isSubstance(self, media):
		return self.isMedia(media = media, type = Media.Substance)

	@classmethod
	def isDrug(self, media):
		return self.isMedia(media = media, type = Media.Drug)

	@classmethod
	def isCannabis(self, media):
		return self.isMedia(media = media, type = Media.Cannabis)

	@classmethod
	def isPsychedelic(self, media):
		return self.isMedia(media = media, type = Media.Psychedelic)

	@classmethod
	def isCocaine(self, media):
		return self.isMedia(media = media, type = Media.Cocaine)

	@classmethod
	def isAlcohol(self, media):
		return self.isMedia(media = media, type = Media.Alcohol)

	@classmethod
	def isPill(self, media):
		return self.isMedia(media = media, type = Media.Pill)

	@classmethod
	def isRelation(self, media):
		return self.isMedia(media = media, type = Media.Relation)

	@classmethod
	def isLove(self, media):
		return self.isMedia(media = media, type = Media.Love)

	@classmethod
	def isRomance(self, media):
		return self.isMedia(media = media, type = Media.Romance)

	@classmethod
	def isKiss(self, media):
		return self.isMedia(media = media, type = Media.Kiss)

	@classmethod
	def isLgbtq(self, media):
		return self.isMedia(media = media, type = Media.Lgbtq)

	@classmethod
	def isGay(self, media):
		return self.isMedia(media = media, type = Media.Gay)

	@classmethod
	def isLesbian(self, media):
		return self.isMedia(media = media, type = Media.Lesbian)

	@classmethod
	def isIntimacy(self, media):
		return self.isMedia(media = media, type = Media.Intimacy)

	@classmethod
	def isSex(self, media):
		return self.isMedia(media = media, type = Media.Sex)

	@classmethod
	def isNudity(self, media):
		return self.isMedia(media = media, type = Media.Nudity)

	@classmethod
	def isErotica(self, media):
		return self.isMedia(media = media, type = Media.Erotica)

	@classmethod
	def isPornography(self, media):
		return self.isMedia(media = media, type = Media.Pornography)

	@classmethod
	def isProstitution(self, media):
		return self.isMedia(media = media, type = Media.Prostitution)

	@classmethod
	def isOrgy(self, media):
		return self.isMedia(media = media, type = Media.Orgy)

	@classmethod
	def isFelony(self, media):
		return self.isMedia(media = media, type = Media.Felony)

	@classmethod
	def isViolence(self, media):
		return self.isMedia(media = media, type = Media.Violence)

	@classmethod
	def isRobbery(self, media):
		return self.isMedia(media = media, type = Media.Robbery)

	@classmethod
	def isSmuggle(self, media):
		return self.isMedia(media = media, type = Media.Smuggle)

	@classmethod
	def isHostage(self, media):
		return self.isMedia(media = media, type = Media.Hostage)

	@classmethod
	def isTorture(self, media):
		return self.isMedia(media = media, type = Media.Torture)

	@classmethod
	def isMurder(self, media):
		return self.isMedia(media = media, type = Media.Murder)

	@classmethod
	def isSociety(self, media):
		return self.isMedia(media = media, type = Media.Society)

	@classmethod
	def isReligion(self, media):
		return self.isMedia(media = media, type = Media.Religion)

	@classmethod
	def isCult(self, media):
		return self.isMedia(media = media, type = Media.Cult)

	@classmethod
	def isSecret(self, media):
		return self.isMedia(media = media, type = Media.Secret)

	@classmethod
	def isTerrorism(self, media):
		return self.isMedia(media = media, type = Media.Terrorism)

	@classmethod
	def isPsycho(self, media):
		return self.isMedia(media = media, type = Media.Psycho)

	@classmethod
	def isSadism(self, media):
		return self.isMedia(media = media, type = Media.Sadism)

	@classmethod
	def isLingual(self, media):
		return self.isMedia(media = media, type = Media.Lingual)

	@classmethod
	def isProfanity(self, media):
		return self.isMedia(media = media, type = Media.Profanity)

	@classmethod
	def isBlasphemy(self, media):
		return self.isMedia(media = media, type = Media.Blasphemy)

	@classmethod
	def isSarcasm(self, media):
		return self.isMedia(media = media, type = Media.Sarcasm)

	@classmethod
	def isParody(self, media):
		return self.isMedia(media = media, type = Media.Parody)

	@classmethod
	def isSatire(self, media):
		return self.isMedia(media = media, type = Media.Satire)

	@classmethod
	def isHumor(self, media):
		return self.isMedia(media = media, type = Media.Humor)

	##############################################################################
	# IS - EXPLORE
	##############################################################################

	@classmethod
	def isAll(self, media):
		return self.isMedia(media = media, type = Media.All)

	@classmethod
	def isNew(self, media):
		return self.isMedia(media = media, type = Media.New)

	@classmethod
	def isHome(self, media):
		return self.isMedia(media = media, type = Media.Home)

	@classmethod
	def isBest(self, media):
		return self.isMedia(media = media, type = Media.Best)

	@classmethod
	def isWorst(self, media):
		return self.isMedia(media = media, type = Media.Worst)

	@classmethod
	def isPrestige(self, media):
		return self.isMedia(media = media, type = Media.Prestige)

	@classmethod
	def isPopular(self, media):
		return self.isMedia(media = media, type = Media.Popular)

	@classmethod
	def isUnpopular(self, media):
		return self.isMedia(media = media, type = Media.Unpopular)

	@classmethod
	def isViewed(self, media):
		return self.isMedia(media = media, type = Media.Viewed)

	@classmethod
	def isGross(self, media):
		return self.isMedia(media = media, type = Media.Gross)

	@classmethod
	def isAward(self, media):
		return self.isMedia(media = media, type = Media.Award)

	@classmethod
	def isTrend(self, media):
		return self.isMedia(media = media, type = Media.Trend)


###################################################################
# AUDIENCE
###################################################################

class Audience(object):

	TypeKid				= 'kid'
	TypeTeen			= 'teen'
	TypeAdult			= 'adult'

	AgeAll				= 0		# 0+
	AgeToddler 			= 2		# 2+
	AgeMinor			= 7		# 7+
	AgeChild			= 8		# 8+
	AgeTeen				= 13	# 13+
	AgeYouth			= 14	# 14+
	AgeAdult			= 17	# 17+
	AgeUnlimited		= 99

	CertificateNr		= 'nr'		# Not rated yet.
	CertificateG		= 'g'		# General Audience (All- Age: Any)
	CertificatePg 		= 'pg'		# Parental Guidance Suggested (Kids - Age: 8+)
	CertificatePg13		= 'pg13'	# Parents Strongly Cautioned (Teens - Age: 13+)
	CertificateR		= 'r'		# Restricted (Teens - Age: 14+)
	CertificateNc17		= 'nc17'	# Adults Only (Adults - Age: 17+)
	CertificateTvg		= 'tvg'		# General Audience (All - Age: Any)
	CertificateTvy		= 'tvy'		# All Children (Kids - Age: 2+)
	CertificateTvy7		= 'tvy7'	# Directed to Older Children (Kids - Age: 7+)
	CertificateTvpg		= 'tvpg'	# Parental Guidance Suggested (Kids - Age: 8+)
	CertificateTv13		= 'tv13'	# Parents Strongly Cautioned (Teens - Age: 13+)
	CertificateTv14		= 'tv14'	# Parents Strongly Cautioned (Teens - Age: 14+)
	CertificateTvma		= 'tvma'	# Mature Audiences Only (Adults - Age: 17+)

	CertificatesMedia	= {
		CertificateNr	: CertificateNr,

		CertificateG	: CertificateTvg,
		CertificatePg	: CertificateTvpg,
		CertificatePg13	: CertificateTv13,
		CertificateR	: CertificateTv14,
		CertificateNc17	: CertificateTvma,

		CertificateTvg	: CertificateG,
		CertificateTvy	: CertificateG,
		CertificateTvy7	: CertificateG,
		CertificateTvpg	: CertificatePg,
		CertificateTv13	: CertificatePg13,
		CertificateTv14	: CertificateR,
		CertificateTvma	: CertificateNc17,
	}

	SelectAll			= True		# All certificates allowed for the type. Eg: for teens, include certificates for teens and kids, but exclude adults.
	SelectExclusive		= None		# Only certificates exclusive for the type. Eg: for teens, include certificates for teens, but exclude kids and adults.
	SelectSingle		= False		# Only the highest certificate for the type. Eg: for teens, only the maximum certificate, eg AgeYouth.

	Default				= {
		TypeKid			: AgeChild,
		TypeTeen		: AgeYouth,
		TypeAdult		: AgeUnlimited,
	}

	Certificates		= {}
	Expressions			= None

	@classmethod
	def reset(self, settings = True):
		if settings: Audience.Certificates = {}

	@classmethod
	def clean(self, certificate):
		if not certificate: return certificate
		return certificate.lower().replace(' ', '').replace('-', '').replace('_', '').replace('us:', '').strip()

	@classmethod
	def format(self, certificate):
		if not certificate: return certificate
		return Tools.stringSplit(value = certificate.upper(), length = 2, join = '-')

	@classmethod
	def enabled(self):
		return Settings.getBoolean('metadata.general.audience')

	@classmethod
	def age(self, type):
		if self.enabled(): return Settings.getInteger('metadata.general.audience.%s' % type)
		else: return Audience.Default.get(type)

	@classmethod
	def ageKid(self, type):
		return self.age(type = Audience.TypeKid)

	@classmethod
	def ageTeen(self, type):
		return self.age(type = Audience.TypeTeen)

	@classmethod
	def ageAdult(self, type):
		return self.age(type = Audience.TypeAdult)

	@classmethod
	def allowed(self, certificate, certificates = None, type = None, invalid = None, unrated = None, select = SelectAll):
		if certificates is None:
			if unrated is None: unrated = type == Audience.TypeAdult
			certificates = self.certificate(type = type, age = True, unrated = unrated, select = select)
		else:
			certificates = [self.clean(certificate = i) for i in certificates]
			if unrated is None: unrated = Audience.CertificateNr in certificates or Audience.CertificateNc17 in certificates or Audience.CertificateTvma in certificates

		if not certificate: return unrated if invalid is None else invalid

		certificate = self.clean(certificate = certificate)
		if certificate in certificates: return True

		# TV movies and TV specials often have a TV MPAA (https://imdb.com/title/tt0385690).
		certificate = Audience.CertificatesMedia.get(certificate)
		if certificate and certificate in certificates: return True

		return False

	@classmethod
	def allowedKid(self, certificate, invalid = None, unrated = None, select = SelectAll):
		return self.allowed(certificate = certificate, type = Audience.TypeKid, invalid = invalid, unrated = unrated, select = select)

	@classmethod
	def allowedTeen(self, certificate, invalid = None, unrated = None, select = SelectAll):
		return self.allowed(certificate = certificate, type = Audience.TypeTeen, invalid = invalid, unrated = unrated, select = select)

	@classmethod
	def allowedAdult(self, certificate, invalid = None, unrated = None, select = SelectAll):
		return self.allowed(certificate = certificate, type = Audience.TypeAdult, invalid = invalid, unrated = unrated, select = select)

	@classmethod
	def certificate(self, type = None, age = None, media = None, unrated = None, select = SelectAll):
		if unrated is None: unrated = type == Audience.TypeAdult and not select == Audience.SelectExclusive
		key = (type, age, media, unrated, select)

		if not key in Audience.Certificates:
			minimum = -1
			maximum = age

			if age is None or age is True: maximum = self.age(type = type)
			elif age is False: maximum = Audience.AgeAll

			if select == Audience.SelectExclusive:
				# If any of the values here are changed, make sure that the Progress/Arrivals menus under the Audience niche menus load the correct stuff, and not eg PG titles under the Kids menu.
				if type == Audience.TypeKid: maximum -= 1 # Everything below a certain age for children. Otherwise TV-PG (8+) is added to the kids niche menu, which are mostly adult shows..
				elif type == Audience.TypeTeen: minimum = self.age(type = Audience.TypeKid) # Not +1, since we want to include PG/TV-PG.
				elif type == Audience.TypeAdult: minimum = self.age(type = Audience.TypeTeen) # Not +1, since otherwise it is only TV-MA, which might return too few for the niche menus.

			result = []
			isMovie = media is None or Media.isMovie(media)
			isSerie = media is None or Media.isSerie(media)

			if maximum >= Audience.AgeAll:
				if minimum <= Audience.AgeAll:
					if isMovie: result.append(Audience.CertificateG)
					if isSerie: result.append(Audience.CertificateTvg)

				if maximum >= Audience.AgeToddler:
					if minimum <= Audience.AgeToddler:
						if isSerie: result.append(Audience.CertificateTvy)

					if maximum >= Audience.AgeMinor:
						if minimum <= Audience.AgeMinor:
							if isSerie: result.append(Audience.CertificateTvy7)

						if maximum >= Audience.AgeChild:
							if minimum <= Audience.AgeChild:
								if isMovie: result.append(Audience.CertificatePg)
								if isSerie: result.append(Audience.CertificateTvpg)

							if maximum >= Audience.AgeTeen:
								if minimum <= Audience.AgeTeen:
									if isMovie: result.append(Audience.CertificatePg13)
									if isSerie: result.append(Audience.CertificateTv13)

								if maximum >= Audience.AgeYouth:
									if minimum <= Audience.AgeYouth:
										if isMovie: result.append(Audience.CertificateR)
										if isSerie: result.append(Audience.CertificateTv14)

									if maximum >= Audience.AgeAdult:
										if minimum <= Audience.AgeAdult:
											if isMovie: result.append(Audience.CertificateNc17)
											if isSerie: result.append(Audience.CertificateTvma)

			if result: result = list(reversed(result))
			if unrated: result.append(Audience.CertificateNr)
			if select == Audience.SelectSingle: result = result[0] if result else None
			Audience.Certificates[key] = result

		return Audience.Certificates[key]

	@classmethod
	def certificateKid(self, media = None, unrated = None, select = SelectAll):
		return self.certificate(type = Audience.TypeKid, media = media, unrated = unrated, select = select)

	@classmethod
	def certificateTeen(self, media = None, unrated = None, select = SelectAll):
		return self.certificate(type = Audience.TypeTeen, media = media, unrated = unrated, select = select)

	@classmethod
	def certificateAdult(self, media = None, unrated = None, select = SelectAll):
		return self.certificate(type = Audience.TypeAdult, media = media, unrated = unrated, select = select)

	@classmethod
	def convert(self, certificate, media = None):
		if not certificate or certificate in Audience.CertificatesMedia: return certificate

		# Should add more for toher countries.
		# https://help.imdb.com/article/contribution/titles/certificates/GU757M8ZJ9ZPXB39#
		if Audience.Expressions is None:
			Audience.Expressions = {
				# International Age Rating Coalition
				'^3'								: Audience.CertificateG,	# 3+
				'^7'								: Audience.CertificatePg,	# 7+
				'^12'								: Audience.CertificatePg13,	# 12+
				'^16'								: Audience.CertificateR,	# 16+
				'^18'								: Audience.CertificateNc17,	# 18+

				# United Kingdom
				'^u$'								: Audience.CertificateG,	# U
				'^r18'								: Audience.CertificateNc17,	# R18

				# Canada
				'^e$'								: Audience.CertificateG,	# E
				'^14a'								: Audience.CertificateR,	# 14A
				'^18a'								: Audience.CertificateNc17,	# 18A
				'^a$'								: Audience.CertificateNc17,	# A

				# Australia
				#'^e$'								: Audience.CertificateG,	# E - same as Canada
				'^g[\s\-]*8'						: Audience.CertificatePg,	# G8+
				'^m(?:$|a?[\s\-]?15)'				: Audience.CertificateR,	# M, M15+, MA15+
				'^(?:[rx][\s\-]?18|rc)'				: Audience.CertificateNc17,	# X18+, R18+, RC
				'^ctc$'								: Audience.CertificateNr,	# CTC

				# Spain
				'^al?(?:$|\/)'						: Audience.CertificateG,	# A, AL, A/fig, A/i, A/i/fig (this clashes with Canada's A)
				'^tp$'								: Audience.CertificateG,	# TP
				'^x$'								: Audience.CertificateNc17,	# X

				# Generic
				'(?<!\d)(?:0|1|2|3|4|5|6|7)(?!\d)'	: Audience.CertificateG,
				'(?<!\d)(?:8|9|10|11)(?!\d)'		: Audience.CertificatePg,
				'(?<!\d)(?:12|13)(?!\d)'			: Audience.CertificatePg13,
				'(?<!\d)(?:14|15|16)(?!\d)'			: Audience.CertificateR,
				'(?<!\d)(?:17|18|19|20|21)(?!\d)'	: Audience.CertificateNc17,
			}

		for k, v in Audience.Expressions.items():
			if Regex.match(data = certificate, expression = k, cache = True):
				if Media.isSerie(media) and not 'tv' in v: v = Audience.CertificatesMedia.get(v)
				return v

		return certificate # Otherwise just return whatever certificate there is.

###################################################################
# TITLE
###################################################################

class Title(object):

	OrderTitle = 0
	OrderTitleYear = 1
	OrderYearTitle = 2
	OrderSeason = 3
	OrderEpisode = 4
	OrderSeasonEpisode = 5
	OrderEpisodeTitle = 6
	OrderSeasonEpisodeTitle = 7

	Default = 0
	Native = 1

	DefaultMovie = 0
	DefaultShow = 0
	DefaultSeason = 0
	DefaultEpisode = 11

	DefaultAeonMovie = 0
	DefaultAeonShow = 0
	DefaultAeonSeason = 0
	DefaultAeonEpisode = 11

	NameSeasonSeries = None
	NameSeasonSpecial = None
	NameSeasonLong = None
	NameSeasonShort = None
	NameEpisodeLong = None
	NameEpisodeShort = None

	FormatTitle = None
	FormatSeason = None
	FormatEpisode = None

	FormatSkin = None
	FormatDefault = None

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		if settings:
			Title.NameSeasonSeries = None
			Title.NameSeasonSpecial = None
			Title.NameSeasonLong = None
			Title.NameSeasonShort = None
			Title.NameEpisodeLong = None
			Title.NameEpisodeShort = None

			Title.FormatTitle = None
			Title.FormatSeason = None
			Title.FormatEpisode = None

			Title.FormatSkin = None
			Title.FormatDefault = None

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def _format(self, format, title = None, year = None, season = None, episode = None, special = False, series = False):
		order = format[0]
		format = format[1]
		if title is None: title = ''
		if order == Title.OrderTitle:
			result = format % (title)
		elif order == Title.OrderTitleYear:
			result = format % (title, year)
		elif order == Title.OrderYearTitle:
			result = format % (year, title)
		elif order == Title.OrderSeason:
			if season is None and series: result = Title.NameSeasonSeries
			elif season == 0 and special and len(format) > 5: result = Title.NameSeasonSpecial
			else: result = format % (season)
		elif order == Title.OrderEpisode:
			result = format % (episode)
		elif order == Title.OrderSeasonEpisode:
			result = format % (season, episode)
		elif order == Title.OrderEpisodeTitle:
			result = format % (episode, title)
		elif order == Title.OrderSeasonEpisodeTitle:
			result = format % (season, episode, title)
		else:
			result = title

		if not title: result = result.strip(' ').strip('-').strip(' ')

		return result

	@classmethod
	def _extract(self, metadata, encode = False):
		title = metadata['tvshowtitle'] if 'tvshowtitle' in metadata else metadata['title']
		if encode: title = Converter.unicodeNormalize(string = title, umlaut = True)
		try: year = int(metadata['year'])
		except: year = None
		try: season = int(metadata['season']) if 'season' in metadata else None
		except: season = None
		try: episode = int(metadata['episode']) if 'episode' in metadata else None
		except: episode = None
		try: pack = bool(metadata['pack'])
		except: pack = None
		return (title, year, season, episode, pack)

	@classmethod
	def _data(self, title, year, season, episode, encode = False):
		if not title is None and encode: title = Converter.unicodeNormalize(string = title, umlaut = True)
		if not year is None: year = int(year)
		if not season is None: season = int(season)
		if not episode is None: episode = int(episode)
		return (title, year, season, episode)

	@classmethod
	def _initialize(self, skin = True):
		if Title.NameSeasonSpecial is None:
			from lib.modules.interface import Translation

			Title.NameSeasonSeries = Translation.string(32003)
			Title.NameSeasonSpecial = Translation.string(35637)
			Title.NameSeasonLong = Translation.string(32055)
			Title.NameSeasonShort = Title.NameSeasonLong[0].upper()
			Title.NameEpisodeLong = Translation.string(33028)
			Title.NameEpisodeShort = Title.NameEpisodeLong[0].upper()

			Title.FormatTitle = [
				(Title.OrderTitle,		'%s'),
				(Title.OrderTitleYear,	'%s %d'),
				(Title.OrderTitleYear,	'%s. %d'),
				(Title.OrderTitleYear,	'%s - %d'),
				(Title.OrderTitleYear,	'%s (%d)'),
				(Title.OrderTitleYear,	'%s [%d]'),
				(Title.OrderYearTitle,	'%d %s'),
				(Title.OrderYearTitle,	'%d. %s'),
				(Title.OrderYearTitle,	'%d - %s'),
				(Title.OrderYearTitle,	'(%d) %s'),
				(Title.OrderYearTitle,	'[%d] %s'),
			]

			Title.FormatSeason = [
				(Title.OrderSeason,		Title.NameSeasonLong + ' %01d'),
				(Title.OrderSeason,		Title.NameSeasonLong + ' %02d'),
				(Title.OrderSeason,		Title.NameSeasonShort + '%01d'),
				(Title.OrderSeason,		Title.NameSeasonShort + '%02d'),
				(Title.OrderSeason,		'%01d ' + Title.NameSeasonLong),
				(Title.OrderSeason,		'%02d ' + Title.NameSeasonLong),
				(Title.OrderSeason,		'%01d. ' + Title.NameSeasonLong),
				(Title.OrderSeason,		'%02d. ' + Title.NameSeasonLong),
				(Title.OrderSeason,		'%01d'),
				(Title.OrderSeason,		'%02d'),
			]

			Title.FormatEpisode = [
				(Title.OrderTitle,					'%s'),
				(Title.OrderEpisodeTitle,			'%01d %s'),
				(Title.OrderEpisodeTitle,			'%02d %s'),
				(Title.OrderEpisodeTitle,			'%01d. %s'),
				(Title.OrderEpisodeTitle,			'%02d. %s'),
				(Title.OrderEpisodeTitle,			'%01d - %s'),
				(Title.OrderEpisodeTitle,			'%02d - %s'),
				(Title.OrderSeasonEpisodeTitle,		'%01dx%01d %s'),
				(Title.OrderSeasonEpisodeTitle,		'%01dx%02d %s'),
				(Title.OrderSeasonEpisodeTitle,		'%02dx%02d %s'),
				(Title.OrderSeasonEpisodeTitle,		'%01dx%01d - %s'),
				(Title.OrderSeasonEpisodeTitle,		'%01dx%02d - %s'),
				(Title.OrderSeasonEpisodeTitle,		'%02dx%02d - %s'),
				(Title.OrderEpisodeTitle,			Title.NameEpisodeShort + '%01d %s'),
				(Title.OrderEpisodeTitle,			Title.NameEpisodeShort + '%02d %s'),
				(Title.OrderEpisodeTitle,			Title.NameEpisodeShort + '%01d. %s'),
				(Title.OrderEpisodeTitle,			Title.NameEpisodeShort + '%02d. %s'),
				(Title.OrderEpisodeTitle,			Title.NameEpisodeShort + '%01d - %s'),
				(Title.OrderEpisodeTitle,			Title.NameEpisodeShort + '%02d - %s'),
				(Title.OrderSeasonEpisodeTitle,		Title.NameSeasonShort + '%01d' + Title.NameEpisodeShort + '%01d %s'),
				(Title.OrderSeasonEpisodeTitle,		Title.NameSeasonShort + '%01d' + Title.NameEpisodeShort + '%02d %s'),
				(Title.OrderSeasonEpisodeTitle,		Title.NameSeasonShort + '%02d' + Title.NameEpisodeShort + '%02d %s'),
				(Title.OrderSeasonEpisodeTitle,		Title.NameSeasonShort + '%01d' + Title.NameEpisodeShort + '%01d - %s'),
				(Title.OrderSeasonEpisodeTitle,		Title.NameSeasonShort + '%01d' + Title.NameEpisodeShort + '%02d - %s'),
				(Title.OrderSeasonEpisodeTitle,		Title.NameSeasonShort + '%02d' + Title.NameEpisodeShort + '%02d - %s'),
				(Title.OrderEpisode,				'%01d'),
				(Title.OrderEpisode,				'%02d'),
				(Title.OrderSeasonEpisode,			'%01dx%01d'),
				(Title.OrderSeasonEpisode,			'%01dx%02d'),
				(Title.OrderSeasonEpisode,			'%02dx%02d'),
				(Title.OrderEpisode,				Title.NameEpisodeShort + '%01d'),
				(Title.OrderEpisode,				Title.NameEpisodeShort + '%02d'),
				(Title.OrderSeasonEpisode,			Title.NameSeasonShort + '%01d' + Title.NameEpisodeShort + '%01d'),
				(Title.OrderSeasonEpisode,			Title.NameSeasonShort + '%01d' + Title.NameEpisodeShort + '%02d'),
				(Title.OrderSeasonEpisode,			Title.NameSeasonShort + '%02d' + Title.NameEpisodeShort + '%02d'),
			]

		data = Title.FormatSkin if skin else Title.FormatDefault
		if data is None:
			from lib.modules.interface import Skin
			aeon = Skin.isAeon() if skin else False
			data = {}

			enabled = Settings.getBoolean('menu.label.layout')

			setting = Settings.getInteger('menu.label.layout.movie') if enabled else Title.Default
			if setting == Title.Native: setting = Title.Default
			if setting == Title.Default: setting = Title.DefaultAeonMovie if aeon else Title.DefaultMovie
			else: setting -= 2
			data[Media.Movie] = Title.FormatTitle[setting]

			setting = Settings.getInteger('menu.label.layout.show') if enabled else Title.Default
			if setting == Title.Native: setting = Title.Default
			if setting == Title.Default: setting = Title.DefaultAeonShow if aeon else Title.DefaultShow
			else: setting -= 2
			data[Media.Show] = data[Media.Mini] = Title.FormatTitle[setting]

			setting = Settings.getInteger('menu.label.layout.season') if enabled else Title.Default
			if setting == Title.Native: setting = Title.Default
			if setting == Title.Default: setting = Title.DefaultAeonSeason if aeon else Title.DefaultSeason
			else: setting -= 2
			data[Media.Season] = Title.FormatSeason[setting]

			setting = Settings.getInteger('menu.label.layout.episode') if enabled else Title.Default
			if setting == Title.Native: setting = Title.Default
			if setting == Title.Default: setting = Title.DefaultAeonEpisode if aeon else Title.DefaultEpisode
			else: setting -= 2

			data[Media.Episode] = Title.FormatEpisode[setting]

			if skin: Title.FormatSkin = data
			else: Title.FormatDefault = data

		return data

	@classmethod
	def title(self, media = Media.Unknown, metadata = None, title = None, year = None, season = None, episode = None, encode = False, pack = False, series = False, special = False, skin = True):
		if metadata: title, year, season, episode, packs = self._extract(metadata = metadata, encode = encode)
		title, year, season, episode = self._data(title = title, year = year, season = season, episode = episode, encode = encode)

		if media == Media.Extra or media == Media.Recap: media = Media.Unknown

		if media == Media.List:
			return title
		elif media == Media.Set:
			media = Media.Movie
		elif media == Media.Unknown:
			pack = (pack and packs)
			if not season is None and not episode is None and not pack:
				media = Media.Episode
			elif not season is None:
				media = Media.Season
			else:
				media = Media.Movie

		formats = self._initialize(skin = skin)
		format = formats[media]

		result = self._format(format = format, title = title, year = year, season = season, episode = episode, series = series, special = special)
		if not title: result = Regex.remove(data = result, expression = '(\s*[\-\.]\s*)$') # For episode titles for the History streams window.

		return result

	# Raw title to search on the web/scrapers.
	@classmethod
	def titleUniversal(self, metadata = None, title = None, year = None, season = None, episode = None, encode = False):
		if not metadata is None: title, year, season, episode, packs = self._extract(metadata = metadata, encode = encode)
		title, year, season, episode = self._data(title = title, year = year, season = season, episode = episode, encode = encode)

		if not season is None and not episode is None:
			return '%s S%02dE%02d' % (title, season, episode)
		elif not year is None:
			year = '(%s)' % year
			if not year in title: title = '%s %s' % (title, year)
			return title
		else:
			return title

	@classmethod
	def number(self, media = Media.Unknown, metadata = None, title = None, season = None, episode = None, encode = False, pack = False, special = False, skin = True):
		if not metadata is None: title, year, season, episode, packs = self._extract(metadata = metadata, encode = encode)
		title, year, season, episode = self._data(title = None, year = None, season = season, episode = episode, encode = encode)

		if media == Media.Unknown:
			pack = (pack and packs)
			if not season is None and not episode is None and not pack:
				media = Media.Episode
			elif not season is None:
				media = Media.Season

		formats = self._initialize(skin = skin)
		format = formats[media]
		return self._format(format = format, title = title, season = season, episode = episode, special = special)

	@classmethod
	def numberUniversal(self, media = Media.Unknown, metadata = None, season = None, episode = None, encode = False):
		if not metadata is None: title, year, season, episode, packs = self._extract(metadata = metadata, encode = encode)
		title, year, season, episode = self._data(title = None, year = None, season = season, episode = episode, encode = encode)
		return 'S%02dE%02d' % (season, episode)

########################################
# SUBPROCESS
########################################

class Subprocess(object):

	@classmethod
	def _error(self, exception):
		exception = str(exception)

		# On Apple:
		#	in output\n    return Converter.unicode(check_output(self.command(command), shell = True))  File "Kodi.app/Frameworks/lib/python3.11/subprocess.py", line 465, in check_output\n    return run(*popenargs, stdout=PIPE, timeout=timeout, check=True,  File "Kodi.app/Frameworks/lib/python3.11/subprocess.py", line 546, in run\n    with Popen(*popenargs, **kwargs) as process:, '  File "Kodi.app/Frameworks/lib/python3.11/subprocess.py", line 816, in __init__\n    raise OSError(\n', 'OSError: [Errno 45] darwin does not support processes.\n']
		# And:
		#	File "Library/Caches/Kodi/addons/plugin.video.gaia/lib/modules/tools.py", line 7339, in fallback\n    os.system(command + \' > \' + path)\n    ^^^^^^^^^\n', "AttributeError: module 'os' has no attribute 'system'\n"]
		if 'does not support processes' in exception or 'has no attribute \'system\'' in exception:
			Logger.log('Your operating system does not support processes and certain features, like hardware optimization, will not work.', type = Logger.TypeError)
			return False

		return True

	@classmethod
	def command(self, command, environment = True):
		# NB: When using "shell", the command cannot be a list, it must be a string.
		# https://stackoverflow.com/questions/26417658/subprocess-call-arguments-ignored-when-using-shell-true-w-list
		if Tools.isArray(command): command = ' '.join(command)

		if environment:
			from lib.modules.environment import Environment
			command = Environment.command(command = command)

		return command

	@classmethod
	def output(self, command):
		try:
			# Use "shell", otherwise Windows will show a CMD window popup.
			from subprocess import check_output, CalledProcessError, STDOUT
			return Converter.unicode(check_output(self.command(command), shell = True, stderr = STDOUT))
		except CalledProcessError as exception:
			# On Android this exception is thrown:
			#	subprocess.CalledProcessError: Command 'lscpu' returned non-zero exit status 127.
			# Do not print the error.
			# Update: This happens to valid programs as well, if the program returns a non-valid exit code (eg: "ping -h")..
			if System.developer(): Logger.error()
			try: return Converter.unicode(exception.output) # Important for environment.py - returning output even if the exit code is wrong.
			except: pass
		except Exception as exception:
			if self._error(exception = exception) or System.developer(): Logger.error()
			return False

	@classmethod
	def live(self, command, function = None):
		try:
			if function is None: function = Logger.log
			from subprocess import Popen, PIPE
			process = Popen(self.command(command), stdout = PIPE, stderr = PIPE, stdin = PIPE, shell = True)
			while process.poll() is None:
				output = process.stdout.readline()
				if output: function(Converter.unicode(output).strip())
				if System.aborted():
					try:
						# NB: It is very important to sleep after calling kill().
						# If not, for some reason the process remains active.
						process.kill()
						Time.sleep(0.1)
						return None
					except:
						Logger.error()
						return False
					break
			process.poll()
		except Exception as exception:
			if self._error(exception = exception) or System.developer(): Logger.error()
			return False

	@classmethod
	def open(self, command, communicate = True, timeout = None):
		try:
			# Use "shell", otherwise Windows will show a CMD window popup.
			from subprocess import Popen, PIPE, TimeoutExpired
			process = Popen(self.command(command), stdout = PIPE, stderr = PIPE, stdin = PIPE, shell = True)
			if communicate is True: return Converter.unicode(process.communicate(timeout = timeout)[0])
			elif communicate: return Converter.unicode(process.communicate(input = Converter.bytes(communicate), timeout = timeout)[0])
			else: return None
		except TimeoutExpired:
			# NB: The timeout only waits for the process output for a number of seconds.
			# However, it does not terminate the child process.
			# When calling "bluetoothctl" and there is no Bluetooth dongle, the command hangs with: Waiting to connect to bluetoothd...
			# Simply timing out keeps the subprocess running in the task manager (eg Linux: 'sh' in the system monitor).
			# Manually terminate the subprocess
			try:
				# NB: It is very important to sleep after calling kill().
				# If not, for some reason the process remains active.
				process.kill()
				Time.sleep(0.1)
				return None
			except:
				Logger.error()
				return False
		except Exception as exception:
			if (not timeout and self._error(exception = exception)) or System.developer(): Logger.error()
			return False

	@classmethod
	def fallback(self, command):
		# On AppleTV we get the following error:
		#	python3.11/subprocess.py", line 816, in __init__    raise OSError(OSError: [Errno 45] darwin does not support processes.
		# Try os.system() if the subprocess does not work.
		# Not sure if os.system uses processes in the background and has the same issue.
		# os.system also does not return the output, so we have to write it to file.
		# UPDATE: os.system() is not available on Mac.
		result = None
		try:
			from subprocess import check_output
			raise Exception()
			return Converter.unicode(check_output(self.command(command), shell = True))
		except:
			try:
				path = System.temporary(directory = 'subprocess', file = str(Hash.random()) + '.dat', gaia = True, make = True)
				os.system(command + ' > ' + path)
				if File.exists(path):
					result = Converter.unicode(File.readNow(path))
					File.delete(path)
			except Exception as exception:
				if self._error(exception = exception) or System.developer(): Logger.error()
				return False
		return result

###################################################################
# PLATFORM
###################################################################

class Platform(object):

	# Family
	FamilyWindows		= 'windows'
	FamilyUnix			= 'unix'

	# System
	SystemWindows		= 'windows'
	SystemMacintosh		= 'macintosh'
	SystemLinux			= 'linux'
	SystemAndroid		= 'android'

	# Architecture
	ArchitectureX86		= 'x86'
	ArchitectureArm		= 'arm'
	ArchitectureArc		= 'arc'

	# Bits
	Bits64				= 64
	Bits32				= 32

	# Kodi
	# https://kodi.wiki/view/Forks
	KodiOfficial		= 'official'
	KodiCoreelec		= 'coreelec'
	KodiLibreelec		= 'libreelec'
	KodiOpenelec		= 'openelec'
	KodiXbian			= 'xbian'
	KodiRasplex			= 'rasplex'
	KodiRaspbmc			= 'raspbmc'
	KodiNodi			= 'nodi'
	KodiSpmc			= 'spmc'
	KodiOsmc			= 'osmc'
	KodiCemc			= 'cemc'
	KodiFtmc			= 'ftmc'
	KodiEbmc			= 'ebmc'
	KodiE2bmc			= 'e2bmc'
	KodiZdmc			= 'zdmc'
	KodiStvmc			= 'stvmc'
	KodiFiremc			= 'firemc'
	KodiVdubstylemc		= 'vdubstylemc'
	KodiTofu			= 'tofu'
	KodiMrmc			= 'mrmc'
	KodiMygica			= 'mygica'
	KodiKato			= 'kato'
	KodiJesusbox		= 'jesusbox'
	KodiTerrarium		= 'terrarium'
	KodiOpenpht			= 'openpht'
	KodiWetek			= 'wetek'
	KodiOpenbricks		= 'openbricks'
	KodiCrystalbuntu	= 'crystalbuntu'
	KodiIconsole		= 'iconsole'
	KodiGeexbox			= 'geexbox'
	KodiBoxee			= 'boxee'
	KodiMeego			= 'meego'
	KodiDvdfab			= 'dvdfab'
	KodiAlienware		= 'alienware'

	Kodi				= {
		KodiOfficial		: {'name' : 'Official',			'expression' : None},
		KodiCoreelec		: {'name' : 'CoreELEC',			'expression' : 'core[\s\-\_\.]*elec'},
		KodiLibreelec		: {'name' : 'LibreELEC',		'expression' : 'libre[\s\-\_\.]*elec'},
		KodiOpenelec		: {'name' : 'OpenELEC',			'expression' : 'open[\s\-\_\.]*elec'},
		KodiXbian			: {'name' : 'XBian',			'expression' : 'xbian'},
		KodiRasplex			: {'name' : 'RasPlex',			'expression' : 'ras[\s\-\_\.]*plex'},
		KodiRaspbmc			: {'name' : 'Raspbmc',			'expression' : 'raspbmc'},
		KodiNodi			: {'name' : 'Nodi',				'expression' : 'Nodi'},
		KodiSpmc			: {'name' : 'SPMC',				'expression' : 'spmc'},
		KodiOsmc			: {'name' : 'OSMC',				'expression' : 'osmc'},
		KodiCemc			: {'name' : 'CEMC',				'expression' : 'cemc'},
		KodiFtmc			: {'name' : 'FTMC',				'expression' : 'ftmc'},
		KodiEbmc			: {'name' : 'EBox MC',			'expression' : 'e(?:[\s\-\_\.]*box)?[\s\-\_\.]*bmc'},
		KodiE2bmc			: {'name' : 'E2BMC',			'expression' : 'e2bmc'},
		KodiZdmc			: {'name' : 'ZDMC',				'expression' : 'zdmc'},
		KodiStvmc			: {'name' : 'STVMC',			'expression' : 'stvmc'},
		KodiFiremc			: {'name' : 'FireMC',			'expression' : 'fire[\s\-\_\.]*mc'},
		KodiVdubstylemc		: {'name' : 'Vdub Style MC',	'expression' : 'vdub[\s\-\_\.]*style[\s\-\_\.]*mc'},
		KodiTofu			: {'name' : 'TOFU',				'expression' : 'tofu'},
		KodiMrmc			: {'name' : 'MrMC',				'expression' : 'mr[\s\-\_\.]*mc'},
		KodiMygica			: {'name' : 'MyGica',			'expression' : 'my[\s\-\_\.]*gica'},
		KodiKato			: {'name' : 'Kato',				'expression' : 'kato'},
		KodiJesusbox		: {'name' : 'Jesus Box',		'expression' : 'jesus[\s\-\_\.]*box'},
		KodiTerrarium		: {'name' : 'Terrarium TV',		'expression' : 'terrarium[\s\-\_\.]*tv'},
		KodiOpenpht			: {'name' : 'OpenPHT',			'expression' : 'open[\s\-\_\.]*pht'},
		KodiWetek			: {'name' : 'WeTek',			'expression' : 'we[\s\-\_\.]*tek'},
		KodiOpenbricks		: {'name' : 'OpenBricks',		'expression' : 'open[\s\-\_\.]*bricks'},
		KodiCrystalbuntu	: {'name' : 'Crystalbuntu',		'expression' : 'Crystal[\s\-\_\.]*u?buntu'},
		KodiIconsole		: {'name' : 'iConsole',			'expression' : 'i[\s\-\_\.]*console'},
		KodiGeexbox			: {'name' : 'GeeXboX',			'expression' : 'gee[\s\-\_\.]*xbox'},
		KodiBoxee			: {'name' : 'Boxee',			'expression' : 'box[\s\-\_\.]*ee'},
		KodiMeego			: {'name' : 'MeeGo',			'expression' : 'mee[\s\-\_\.]*go'},
		KodiDvdfab			: {'name' : 'DVDFab',			'expression' : 'dvd[\s\-\_\.]*fab'},
		KodiAlienware		: {'name' : 'Alienware Alpha',	'expression' : 'alienware'},
	}

	SettingIdentifier	= 'internal.identifier'

	PropertyFull		= 'GaiaPlatformFull'
	PropertyBasic		= 'GaiaPlatformBasic'

	DataFull			= None
	DataBasic			= None

	########################################
	# DATA
	########################################

	@classmethod
	def data(self, refresh = False, full = True):
		if full:
			data = Platform.DataFull
			property = Platform.PropertyFull
		else:
			data = Platform.DataBasic
			property = Platform.PropertyBasic

		if data is None:
			# Some parameters can take a while to detect. Rather try to load/save to global vars.
			if not refresh:
				platform = System.windowPropertyGet(property)
				if platform:
					platform = Converter.jsonFrom(platform)
					if platform:
						try: version = platform['addon']['version']
						except: version = None
						if version and version == System.version(): data = platform

			if data is None:
				data = self.detect(full = full)
				System.windowPropertySet(property, Converter.jsonTo(data))

			if data:
				if full: Platform.DataFull = data
				else: Platform.DataBasic = data

		return data

	@classmethod
	def identifier(self, refresh = False, full = True):
		return self.data(refresh = refresh, full = full)['identifier']

	@classmethod
	def identifierReset(self):
		Settings.set(Platform.SettingIdentifier, '')

	@classmethod
	def family(self, refresh = False, full = True):
		return self.data(refresh = refresh, full = full)['family']

	@classmethod
	def familyType(self, refresh = False, full = True):
		return self.family(refresh = refresh, full = full)['type']

	@classmethod
	def familyTypeWindows(self, refresh = False, full = True):
		return self.familyType(refresh = refresh, full = full) == Platform.FamilyWindows

	@classmethod
	def familyTypeUnix(self, refresh = False, full = True):
		return self.familyType(refresh = refresh, full = full) == Platform.FamilyUnix

	@classmethod
	def familyName(self, refresh = False, full = True):
		return self.family(refresh = refresh, full = full)['name']

	@classmethod
	def system(self, refresh = False, full = True):
		return self.data(refresh = refresh, full = full)['system']

	@classmethod
	def systemType(self, refresh = False, full = True):
		return self.system(refresh = refresh, full = full)['type']

	@classmethod
	def systemTypeWindows(self, refresh = False, full = True):
		return self.systemType(refresh = refresh, full = full) == Platform.SystemWindows

	@classmethod
	def systemTypeMacintosh(self, refresh = False, full = True):
		return self.systemType(refresh = refresh, full = full) == Platform.SystemMacintosh

	@classmethod
	def systemTypeLinux(self, refresh = False, full = True):
		return self.systemType(refresh = refresh, full = full) == Platform.SystemLinux

	@classmethod
	def systemTypeAndroid(self, refresh = False, full = True):
		return self.systemType(refresh = refresh, full = full) == Platform.SystemAndroid

	@classmethod
	def systemName(self, refresh = False, full = True):
		return self.system(refresh = refresh, full = full)['name']

	@classmethod
	def distribution(self, refresh = False, full = True):
		return self.data(refresh = refresh, full = full)['distribution']

	@classmethod
	def distributionType(self, refresh = False, full = True):
		return self.distribution(refresh = refresh, full = full)['type']

	@classmethod
	def distributionName(self, refresh = False, full = True):
		return self.distribution(refresh = refresh, full = full)['name']

	@classmethod
	def architecture(self, refresh = False, full = True):
		return self.data(refresh = refresh, full = full)['architecture']

	@classmethod
	def architectureType(self, refresh = False, full = True):
		return self.architecture(refresh = refresh, full = full)['type']

	@classmethod
	def architectureTypeX86(self, refresh = False, full = True):
		return self.architectureType(refresh = refresh, full = full) == Platform.ArchitectureX86

	@classmethod
	def architectureTypeArm(self, refresh = False, full = True):
		return self.architectureType(refresh = refresh, full = full) == Platform.ArchitectureArm

	@classmethod
	def architectureTypeArc(self, refresh = False, full = True):
		return self.architectureType(refresh = refresh, full = full) == Platform.ArchitectureArc

	@classmethod
	def architectureBits(self, refresh = False, full = True):
		return self.architecture(refresh = refresh, full = full)['bits']

	@classmethod
	def architectureBits64(self, refresh = False, full = True):
		return self.architectureBits(refresh = refresh, full = full) == Platform.Bits64

	@classmethod
	def architectureBits32(self, refresh = False, full = True):
		return self.architectureBits(refresh = refresh, full = full) == Platform.Bits32

	@classmethod
	def architectureName(self, refresh = False, full = True):
		return self.architecture(refresh = refresh, full = full)['name']

	@classmethod
	def architectureLabel(self, refresh = False, full = True):
		return self.architecture(refresh = refresh, full = full)['label']

	@classmethod
	def version(self, refresh = False, full = True):
		return self.data(refresh = refresh, full = full)['version']

	@classmethod
	def versionNumber(self, refresh = False, full = True):
		return self.version(refresh = refresh, full = full)['number']

	@classmethod
	def versionName(self, refresh = False, full = True):
		return self.version(refresh = refresh, full = full)['name']

	@classmethod
	def versionLabel(self, refresh = False, full = True):
		return self.version(refresh = refresh, full = full)['label']

	@classmethod
	def environment(self, refresh = False, full = True):
		return self.data(refresh = refresh, full = full)['environment']

	@classmethod
	def environmentType(self, refresh = False, full = True):
		return self.environment(refresh = refresh, full = full)['type']

	@classmethod
	def environmentName(self, refresh = False, full = True):
		return self.environment(refresh = refresh, full = full)['name']

	@classmethod
	def environmentLabel(self, refresh = False, full = True):
		return self.environment(refresh = refresh, full = full)['label']

	@classmethod
	def python(self, refresh = False, full = True):
		return self.data(refresh = refresh, full = full)['python']

	@classmethod
	def pythonBuild(self, refresh = False, full = True):
		return self.python(refresh = refresh, full = full)['build']

	@classmethod
	def pythonVersion(self, refresh = False, full = True):
		return self.python(refresh = refresh, full = full)['version']

	@classmethod
	def pythonImplementation(self, refresh = False, full = True):
		return self.python(refresh = refresh, full = full)['implementation']

	@classmethod
	def pythonRelease(self, refresh = False, full = True):
		return self.python(refresh = refresh, full = full)['release']

	@classmethod
	def pythonConcurrency(self, refresh = False, full = True):
		return self.python(refresh = refresh, full = full)['concurrency']

	@classmethod
	def pythonConcurrencyThread(self, refresh = False, full = True):
		return self.pythonConcurrency(refresh = refresh, full = full)['thread']

	@classmethod
	def pythonConcurrencyProcess(self, refresh = False, full = True):
		return self.pythonConcurrency(refresh = refresh, full = full)['process']

	@classmethod
	def pythonConcurrencyLabel(self, refresh = False, full = True):
		return self.pythonConcurrency(refresh = refresh, full = full)['label']

	@classmethod
	def kodi(self, refresh = False, full = True):
		return self.data(refresh = refresh, full = full)['kodi']

	@classmethod
	def kodiBuild(self, refresh = False, full = True):
		return self.kodi(refresh = refresh, full = full)['build']

	@classmethod
	def kodiName(self, refresh = False, full = True):
		return self.kodi(refresh = refresh, full = full)['name']

	@classmethod
	def kodiUptime(self, refresh = False, full = True):
		return self.kodi(refresh = refresh, full = full)['uptime']

	@classmethod
	def kodiVersion(self, refresh = False, full = True):
		return self.kodi(refresh = refresh, full = full)['version']

	@classmethod
	def kodiVersionNumber(self, refresh = False, full = True):
		return self.kodiVersion(refresh = refresh, full = full)['number']

	@classmethod
	def kodiVersionCode(self, refresh = False, full = True):
		return self.kodiVersion(refresh = refresh, full = full)['code']

	@classmethod
	def kodiVersionLabel(self, refresh = False, full = True):
		return self.kodiVersion(refresh = refresh, full = full)['label']

	@classmethod
	def kodiRelease(self, refresh = False, full = True):
		return self.kodi(refresh = refresh, full = full)['kodi']['release']

	@classmethod
	def kodiReleaseNumber(self, refresh = False, full = True):
		return self.kodiRelease(refresh = refresh, full = full)['number']

	@classmethod
	def kodiReleaseDate(self, refresh = False, full = True):
		return self.kodiRelease(refresh = refresh, full = full)['date']

	@classmethod
	def kodiReleaseLabel(self, refresh = False, full = True):
		return self.kodiRelease(refresh = refresh, full = full)['label']

	@classmethod
	def addon(self, refresh = False, full = True):
		return self.data(refresh = refresh, full = full)['addon']

	@classmethod
	def addonId(self, refresh = False, full = True):
		return self.addon(refresh = refresh, full = full)['id']

	@classmethod
	def addonName(self, refresh = False, full = True):
		return self.addon(refresh = refresh, full = full)['name']

	@classmethod
	def addonAuthor(self, refresh = False, full = True):
		return self.addon(refresh = refresh, full = full)['author']

	@classmethod
	def addonVersion(self, refresh = False, full = True):
		return self.addon(refresh = refresh, full = full)['version']

	@classmethod
	def agent(self, refresh = False, full = True):
		return self.data(refresh = refresh, full = full)['agent']

	########################################
	# INTERNAL
	########################################

	@classmethod
	def psutil(self):
		from lib.modules.external import Psutil
		return Psutil().module()

	########################################
	# DETECT
	########################################

	@classmethod
	def detectWindows(self):
		try:
			import platform
			system = platform.system().lower()
			return 'windows' in system or 'win32' in system or 'win64' in system
		except: return False

	@classmethod
	def detectMacintosh(self):
		try:
			import platform
			version = platform.mac_ver()
			return not version[0] is None and not version[0] == ''
		except: return False

	@classmethod
	def detectLinux(self):
		try:
			import platform
			return 'linux' in platform.system().lower() and not self.detectAndroid()
		except: return False

	@classmethod
	def detectAndroid(self):
		try:
			# Nvidia Shield (with Android TV) is detected as Linux.
			# A more robust solution seems to be to check the file path, eg: /storage/emulated/0/Android/data/net.kodinerds.maven.kodi/files/.kodi/addons/...
			path = File.translatePath('special://temp/')
			if path and '/android/' in path.lower(): return True

			import platform
			system = platform.system().lower()
			try: distribution = self.detectDistribution()
			except: distribution = None

			if Platform.SystemAndroid in system or Platform.SystemAndroid in system or (distribution and len(distribution) > 0 and Tools.isString(distribution[0]) and Platform.SystemAndroid in distribution[0].lower()):
				return True

			# Python 3.7+
			try:
				if hasattr(sys, 'getandroidapilevel'): return True
			except: pass

			# Environment variables.
			try:
				if 'ANDROID_ARGUMENT' in os.environ or 'ANDROID_BOOTLOGO' in os.environ or 'ANDROID_STORAGE' in os.environ: return True
			except: pass

			if system == Platform.SystemLinux:
				id = ''
				if not id:
					try: id = Subprocess.open('getprop ril.serialnumber').strip()
					except: pass
				if not id:
					try: id = Subprocess.open('getprop ro.serialno').strip()
					except: pass
				if not id:
					try: id = Subprocess.open('getprop sys.serialnumber').strip()
					except: pass
				if not id:
					try: id = Subprocess.open('getprop gsm.sn1').strip()
					except: pass
				if not id:
					try: id = Subprocess.open('getprop init.svc.adbd').strip()
					except: pass
				if id:
					try: return not 'not found' in id
					except: return True
		except: pass
		return False

	@classmethod
	def detectDistribution(self):
		import platform

		# linux_distribution() not on CoreElec.
		# Both distro function have been removed in Python 3.
		try: return platform.linux_distribution()
		except:
			try: return platform.dist()
			except:
				try:
					# https://docs.python.org/3/library/platform.html
					result = platform.freedesktop_os_release()
					return [result['NAME'], result['VERSION'], result['VARIANT ']]
				except: pass

		return None

	@classmethod
	def detectPython(self):
		build = None
		version = None
		implementation = None
		release = None
		concurrencyThread = False
		concurrencyProcess = False
		concurrencyLabel = []

		try:
			import platform

			try:
				build = list(platform.python_build())
				try: build[0] = build[0].capitalize()
				except: pass
				build = '%s (%s)' % (build[0], build[1])
			except: Logger.error()

			try: version = platform.python_version()
			except: Logger.error()

			try:
				implementation1 = platform.python_implementation()
				implementation2 = platform.python_compiler()
				if implementation1 and implementation2: implementation = '%s (%s)' % (implementation1, implementation2)
				elif implementation1: implementation = implementation1
				elif implementation2: implementation = implementation2
			except: Logger.error()

			try:
				release1 = platform.python_branch()
				release2 = platform.python_revision()
				if release1 and release2: release = '%s (%s)' % (release1, release2)
				elif release1: release = release1
				elif release2: release = release2
			except: Logger.error()

		except: Logger.error()

		concurrencyProcess = Pool.processSupport()
		if concurrencyProcess: concurrencyLabel.append('Multi-Processing')

		concurrencyThread = Pool.threadSupport()
		if concurrencyThread: concurrencyLabel.append('Multi-Threading')

		if concurrencyLabel: concurrencyLabel = ' and '.join(concurrencyLabel)
		else: concurrencyLabel = 'No Multi-Execution Support'

		interpreterType, interpreterLabel = Settings.interpreter(full = True, label = True)

		return {
			'build' : build,
			'version' : version,
			'implementation' : implementation,
			'release' : release,
			'interpreter' : {
				'reuse' : bool(interpreterType),
				'label' : interpreterLabel,
			},
			'concurrency' : {
				'process' : concurrencyProcess,
				'thread' : concurrencyThread,
				'label' : concurrencyLabel,
			},
		}

	@classmethod
	def detectKodi(self):
		name = None
		build = None
		uptime = None
		versionNumber = None
		versionCode = None
		versionLabel = None
		releaseNumber = None
		releaseDate = None
		releaseLabel = None

		try:
			System.infoLabelLoad(['System.OSVersionInfo', 'System.FriendlyName', 'System.BuildVersion', 'System.BuildVersionCode', 'System.BuildVersionGit', 'System.BuildDate', 'System.Uptime'])

			try:
				found = False
				build = Platform.Kodi[Platform.KodiOfficial]['name']
				infos = [System.infoLabel('System.OSVersionInfo'), File.translatePath('special://xbmc'), File.translatePath('special://logpath')]
				for info in infos:
					if info:
						for key, value in Platform.Kodi.items():
							if value['expression'] and Regex.match(data = info, expression = value['expression']):
								build = value['name']
								found = True
								break
						if found: break
			except: Logger.error()

			try: name = System.infoLabel('System.FriendlyName')
			except: Logger.error()
			try: uptime = System.infoLabel('System.Uptime')
			except: Logger.error()

			try:
				versionNumber = System.infoLabel('System.BuildVersion')
				index = versionNumber.find(' ')
				if index >= 0: versionNumber = versionNumber[:index].strip()
			except: Logger.error()
			try:
				versionCode = System.infoLabel('System.BuildVersionCode')
				index = versionCode.find(' ')
				if index >= 0: versionCode = versionCode[:index].strip()
			except: Logger.error()
			try:
				if versionNumber and versionCode: versionLabel = '%s (%s)' % (versionNumber, versionCode)
				elif versionCode: versionLabel = versionCode
				elif versionNumber: versionLabel = versionNumber
			except: Logger.error()

			try: releaseNumber = System.infoLabel('System.BuildVersionGit')
			except: Logger.error()
			try: releaseDate = System.infoLabel('System.BuildDate')
			except: Logger.error()
			try:
				if releaseNumber and releaseDate: releaseLabel = '%s (%s)' % (releaseNumber, releaseDate)
				elif releaseNumber: releaseLabel = releaseNumber
				elif releaseDate: releaseLabel = releaseDate
			except: Logger.error()

		except: Logger.error()

		return {
			'name' : name,
			'build' : build,
			'uptime' : uptime,
			'version' : {
				'number' : versionNumber,
				'code' : versionCode,
				'label' : versionLabel,
			},
			'release' : {
				'number' : releaseNumber,
				'date' : releaseDate,
				'label' : releaseLabel,
			},
		}

	@classmethod
	def detectAddon(self):
		return {
			'id' : System.id(),
			'name' : System.name(),
			'author' : System.author(),
			'version' : System.version(),
		}

	@classmethod
	def detectAgent(self, systemType = None, architectureType = None, architectureBits = None, distributionName = None, versionNumber = None, versionName = None):
		agent = None
		try:
			system = ''
			if systemType == Platform.SystemWindows:
				system += 'Windows NT'
				if versionName: system += ' ' + versionName
				if architectureBits == Platform.Bits64: system += '; Win64; x64'
				elif architectureType == Platform.ArchitectureArm: system += '; ARM'
				elif architectureType == Platform.ArchitectureArc: system += '; ARC'
			elif systemType == Platform.SystemMacintosh:
				system += 'Macintosh; Intel Mac OS X ' + versionNumber.replace('.', '_')
			elif systemType == Platform.SystemLinux:
				system += 'X11;'
				if distributionName: system += ' ' + distributionName + ';'
				system += ' Linux;'
				if architectureBits == Platform.Bits32: system += ' x86'
				elif architectureBits == Platform.Bits64: system += ' x86_64'
				elif architectureType == Platform.ArchitectureArm: system += ' arm'
				elif architectureType == Platform.ArchitectureArc: system += ' arc'
			elif systemType == Platform.SystemAndroid:
				system += 'Linux; Android ' + versionNumber
			if not system == '': system = '(' + system + ') '
			system = System.name() + '/' + System.version() + ' ' + system + 'Kodi/' + str(System.versionKodi())

			# Do in 2 steps, previous statement can fail
			agent = system
		except: Logger.error()
		return agent

	@classmethod
	def detectIdentifier(self):
		id = None

		try:
			# Windows
			if self.detectWindows():
				if not id or ' ' in id or id == 'None':
					try:
						import _winreg
						registry = _winreg.HKEY_LOCAL_MACHINE
						address = 'SOFTWARE\\Microsoft\\Cryptography'
						keyargs = _winreg.KEY_READ | _winreg.KEY_WOW64_64KEY
						key = _winreg.OpenKey(registry, address, 0, keyargs)
						value = _winreg.QueryValueEx(key, 'MachineGuid')
						_winreg.CloseKey(key)
						id = Converter.unicode(value[0])
					except: pass

				# NB: use "shell", otherwise a CMD window pops up in Windows.
				if not id or ' ' in id or id == 'None':
					try: id = Subprocess.open('wmic csproduct get uuid')
					except: pass

				if not id or ' ' in id or id == 'None':
					try: id = Subprocess.open('dmidecode.exe -s system-uuid')
					except: pass

			# Android
			if self.detectAndroid():
				if not id or ' ' in id or id == 'None':
					try: id = Subprocess.open('getprop ril.serialnumber')
					except: pass
				if not id or ' ' in id or id == 'None':
					try: id = Subprocess.open('getprop ro.serialno')
					except: pass
				if not id or ' ' in id or id == 'None':
					try: id = Subprocess.open('getprop sys.serialnumber')
					except: pass
				if not id or ' ' in id or id == 'None':
					try: id = Subprocess.open('getprop gsm.sn1')
					except: pass

			# Linux
			if not id or ' ' in id or id == 'None':
				try: id = Subprocess.fallback('hal-get-property --udi /org/freedesktop/Hal/devices/computer --key system.hardware.uuid')
				except: pass
			if not id or ' ' in id or id == 'None':
				try: id = Subprocess.fallback('/sys/class/dmi/id/board_serial')
				except: pass
			if not id or ' ' in id or id == 'None':
				try: id = Subprocess.fallback('/sys/class/dmi/id/product_uuid')
				except: pass
			if not id or ' ' in id or id == 'None':
				try: id = Subprocess.fallback('cat /var/lib/dbus/machine-id')
				except: pass

			# If still not found, get the MAC address.
			if not id or ' ' in id or id == 'None':
				try:
					nics = Platform.psutil().net_if_addrs()
					nics.pop('lo')
					for i in nics:
						for j in nics[i]:
							if j.family == 17:
								id = Converter.unicode(j.address)
								break
				except: pass
			if not id or ' ' in id or id == 'None':
				try:
					import netifaces
					interface = [i for i in netifaces.interfaces() if not i.startswith('lo')][0]
					id = Converter.unicode(netifaces.ifaddresses(interface)[netifaces.AF_LINK])
				except: pass

			# If still not found,use the UUID.
			if not id or ' ' in id or id == 'None':
				try:
					import uuid
					# Might return a random ID on failure
					# In such a case, save it to the settings and return it, ensuring that the same ID is used.
					id = Settings.getString(Platform.SettingIdentifier)
					if id == None or id == '':
						id = Converter.unicode(uuid.getnode())
						Settings.set(Platform.SettingIdentifier, id)
				except: pass

			if id is None: id = ''
			else: id = Converter.unicode(id) + '_'

			try:
				import platform
				id += '_'.join([Converter.unicode(platform.system()), Converter.unicode(platform.machine())])
			except: pass

			try:
				id += '_'.join([Converter.unicode(Hardware.processorModel()), Converter.unicode(Hardware.memoryBytes())])
			except: pass

			id = Hash.sha256(id)
		except: Logger.error()

		return id

	@classmethod
	def detect(self, full = True):
		familyType = None
		familyName = None

		systemType = None
		systemName = None

		distributionType = None
		distributionName = None

		architectureType = None
		architectureBits = None
		architectureName = None
		architectureLabel = None

		versionName = None
		versionNumber = None
		versionLabel = None

		environmentType = None
		environmentName = None
		environmentLabel = None

		try:
			import platform

			if self.detectWindows():
				familyType = Platform.FamilyWindows
				systemType = Platform.SystemWindows
				try:
					version = platform.win32_ver()
					versionName = version[0]
					versionNumber = version[1]
				except: Logger.error()
			elif self.detectAndroid():
				familyType = Platform.FamilyUnix
				systemType = Platform.SystemAndroid
				try:
					distribution = self.detectDistribution()
					if distribution:
						versionName = distribution[2]
						versionNumber = distribution[1]
				except: Logger.error()
			elif self.detectMacintosh():
				familyType = Platform.FamilyUnix
				systemType = Platform.SystemMacintosh
				try:
					version = platform.mac_ver()
					versionName = version[0]
					versionNumber = version[1]
					if versionNumber and Tools.isArray(versionNumber):
						if not versionNumber[0]: versionNumber = version[0]
						else: versionNumber = '.'.join(versionNumber)
				except: Logger.error()
			elif self.detectLinux():
				familyType = Platform.FamilyUnix
				systemType = Platform.SystemLinux
				try:
					distribution = self.detectDistribution()
					if distribution:
						distributionType = distribution[0].lower().replace('"', '').replace(' ', '')
						distributionName = distribution[0].replace('"', '')
						if 'elementary os' in distributionName.lower(): distributionName = 'elementary'

						versionName = distribution[2]
						versionNumber = distribution[1]
				except: Logger.error()

			if not familyName: familyName = familyType.capitalize()
			if not systemName: systemName =  systemType.capitalize()

			try:
				if versionName: versionName = versionName.capitalize()
			except: pass

			release = platform.release()
			if not versionName:
				if release: versionNumber = Regex.extract(data = release, expression = '([\d\.]+).*')
				if not versionNumber: versionNumber = release

			if not versionLabel:
				try:
					if versionName and versionNumber: versionLabel = '%s (%s)' % (versionName, versionNumber)
				except: pass
				if not versionLabel:
					if versionName: versionLabel = versionName
					elif versionNumber: versionLabel = versionNumber

			try:
				if sys.maxsize > 2**32: architectureBits = Platform.Bits64 # https://docs.python.org/3/library/platform.html
			except: pass

			try: architectureName = platform.machine()
			except: pass
			if architectureName:
				if not architectureBits:
					if Regex.match(data = architectureName, expression = '(64)'): architectureBits = Platform.Bits64
					elif Regex.match(data = architectureName, expression = '(86|32|i\d{3}|ulv|atom)'): architectureBits = Platform.Bits32

				if Regex.match(data = architectureName, expression = '(intel|x86|i\d{3}|ulv|atom|ia.32|amd)'): architectureType = Platform.ArchitectureX86
				elif Regex.match(data = architectureName, expression = '(arm|aarch|risc|acorn|a32|a64)'): architectureType = Platform.ArchitectureArm
				elif Regex.match(data = architectureName, expression = '(arc)'): architectureType = Platform.ArchitectureArc

				# AppleTV
				# Eg: AppleTV14,1
				if not architectureType:
					if Regex.match(data = architectureName, expression = '(appletv1,)'): architectureType = Platform.ArchitectureX86 # Pentium M.
					elif Regex.match(data = architectureName, expression = '(appletv)'): architectureType = Platform.ArchitectureArm # Native ARM or new Apple A ARM-based processors .

				architectureLabel = architectureName
				if architectureBits: architectureLabel = '%s (%dbit)' % (architectureLabel, architectureBits)

		except: Logger.error()

		try:
			from lib.modules.environment import Environment
			environmentType = Environment.type()
			environmentName = Environment.name()
			environmentLabel = Environment.label()
		except: Logger.error()

		result = {
			'family' : {
				'type' : familyType,
				'name' : familyName,
			},
			'system' : {
				'type' : systemType,
				'name' : systemName,
			},
			'distribution' : {
				'type' : distributionType,
				'name' : distributionName,
			},
			'architecture' : {
				'type' : architectureType,
				'bits' : architectureBits,
				'name' : architectureName,
				'label' : architectureLabel,
			},
			'version' : {
				'number' : versionNumber,
				'name' : versionName,
				'label' : versionLabel,
			},
			'environment' : {
				'type' : environmentType,
				'name' : environmentName,
				'label' : environmentLabel,
			},
			'python' : self.detectPython(),
			'kodi' : self.detectKodi(),
			'addon' : self.detectAddon(),
			'agent' : self.detectAgent(systemType = systemType, architectureType = architectureType, architectureBits = architectureBits, distributionName = distributionName, versionNumber = versionNumber, versionName = versionName),
		}

		if full:
			from lib.modules.external import Importer, Psutil, Ujson
			from lib.modules.compression import Compressor
			result['identifier'] = self.detectIdentifier()
			result['module'] = {
				'cloudscraper' : Importer.moduleCloudScraper(label = True),
				'psutil' : Psutil().moduleLabel(),
				'ujson' : Ujson().moduleLabel(),
				'image' : Importer.moduleQrImage(label = True),
			}
			result['compression'] = Compressor.details()

		return result

###################################################################
# HARDWARE
###################################################################

class Hardware(object):

	CategoryProcessor	= 'processor'
	CategoryMemory		= 'memory'
	CategoryStorage		= 'storage'
	CategoryConnection	= 'connection'

	ProcessorIntel		= 'intel'
	ProcessorAmd		= 'amd'
	ProcessorArm		= 'arm'
	ProcessorArc		= 'arc'
	Processor			= {
		ProcessorIntel	: {'name' : 'Intel'},
		ProcessorAmd	: {'name' : 'AMD'},
		ProcessorArm	: {'name' : 'ARM'},
		ProcessorArc	: {'name' : 'ARC'},
	}

	PerformanceExcellent = 'excellent'
	PerformanceGood = 'good'
	PerformanceMedium = 'medium'
	PerformancePoor = 'poor'
	PerformanceBad = 'bad'

	Performance = {
		'performance' : [
			{'performance' : PerformanceExcellent, 'label' : 35241, 'rating' : 0.8},
			{'performance' : PerformanceGood, 'label' : 35242, 'rating' : 0.6},
			{'performance' : PerformanceMedium, 'label' : 33999, 'rating' : 0.4},
			{'performance' : PerformancePoor, 'label' : 35243, 'rating' : 0.2},
			{'performance' : PerformanceBad, 'label' : 35244, 'rating' : 0.0},
		],
		'processor' : {
			'total' : {
				'weight' : 0.25,
				'minimum' : 5000000000, # 5.0 GHz. Raspberry Pi 4 has 6.0GHz (4 cores @ 1.5GHz). Use a lower value than 6.0GHz.
				'maximum' : 20000000000, # 20.0GHz
			},
			'single' : {
				'weight' : 0.5,
				'minimum' : 1600000000, # 1.6GHz
				'maximum' : 3000000000, # 3.0GHz
			},
		},
		'memory' : {
			'weight' : 0.05,
			'minimum' : 1610612736, # 1.5GB
			'maximum' : 5368709120, # 5GB
		},
		'storage' : {
			# SSD: +- 325MB/s avg (500MB/s read | 150MB/s write)
			# eMMC: +- 175MB/s avg (300MB/s read | 50MB/s write | although some newer ones might be faster)
			# HDD (7200rpm): +- 235MB/s avg (420MB/s read | 50MB/s write)
			# HDD (5400rpm): +- 175MB/s avg (315MB/s read | 35MB/s write)
			# SD Card (Class 10): +- 10MB/s
			# SD Card (Class 8): +- 8MB/s
			# SD Card (Class 6): +- 6MB/s

			# There is a difference between theoretical and practical speeds.
			# Do not make these values too high, otherwise good storages will have a relatively low rating.
			'read' : {
				'weight' : 0.05,
				'minimum' : 52428800, # 50MB/s
				'maximum' : 157286400, # 150MB/s
			},
			'write' : {
				'weight' : 0.05,
				'minimum' : 26214400, # 25MB/s
				'maximum' : 78643200, # 75MB/s
			},
		},
		'connection' : {
			'latency' : {
				'weight' : 0.005,
				'minimum' : 100, # 100ms
				'maximum' : 1000, # 1000ms
			},
			'speed' : {
				'weight' : 0.095,
				'minimum' : 2097152, # 2mbps
				'maximum' : 20971520, # 20mbps
			},
		},
	}

	PropertyFull	= 'GaiaHardwareFull'
	PropertyBasic	= 'GaiaHardwareBasic'

	DataFull		= None
	DataBasic		= None

	@classmethod
	def _extractSize(self, size):
		from lib.modules.convert import ConverterSize
		return ConverterSize(size).value()

	@classmethod
	def _labelSize(self, size):
		from lib.modules.convert import ConverterSize
		return ConverterSize(size).stringOptimal(places = ConverterSize.PlacesUnknown if size < 10737418240 else ConverterSize.PlacesNone)

	@classmethod
	def _labelPercent(self, percent):
		return str(int(Math.round(percent * 100, places = 0))) + '%'

	@classmethod
	def _labelProcessor(self, cores, threads = None):
		return '%d%s Core%s' % (cores, '' if (not threads or cores == threads) else ('(%d)' % threads), '' if cores == 1 else 's')

	########################################
	# THREAD
	########################################

	@classmethod
	def threadSize(self, default = True):
		# New threads that are created have a default stack size.
		# This is the maximum memory the thread can use, not necessarily the real used memory.
		# These limits are just estimates. They can differ on different OSs, different versions of the same OS, 32bit vs 64bit, and is also subject to OS and user settings.
		# Hence, there is a theoretical upper limit for the number of thread objects that can be created and executed at the SAME time, since the system might run out of memory.

		base = 1048576 # 1MB
		sizes = {
			Platform.SystemWindows : 1048576, # 1MB
			Platform.SystemLinux : 8388608, # 8MB (ulimit -a)
			Platform.SystemMacintosh : 524288, # 512KB
			Platform.SystemAndroid : 1048576, # 1MB
		}

		size = sizes.get(Platform.systemType(), default)
		if size: size = max(size, base) # For smaller stack sizes, assume it is at least 1MB.
		else: size = default

		return size

	@classmethod
	def threadLimit(self, memory = False, adjust = True, minimum = None, maximum = None, default = None):
		# Estimate the number of threads that can be created and executed at the SAME time, due to system memory restrictions.

		free = False
		if not Tools.isInteger(memory):
			if memory:
				free = True
				memory = self.memoryUsageFreeBytes()
			else:
				memory = self.memoryBytes()
		if adjust is True: adjust = 0.8 if free else 0.7

		limit = None
		size = self.threadSize()

		if size and memory:
			limit = memory / float(size)
			if adjust: limit *= adjust
			limit = int(Math.roundDown(limit))
		if limit:
			if minimum: limit = max(limit, minimum)
			if maximum: limit = min(limit, maximum)
		if not limit: limit = default

		return limit

	########################################
	# DATA
	########################################

	@classmethod
	def data(self, full = False, refresh = False, detect = True, callback = None):
		if full:
			data = Hardware.DataFull
			property = Hardware.PropertyFull
		else:
			# If the full data was already detected, use that instead.
			data = self.data(full = True, refresh = refresh, detect = False, callback = callback)
			if data: return data

			data = Hardware.DataBasic
			property = Hardware.PropertyBasic

		if data is None:
			# Calculating the storage speed can take a long time 15 - 60 seconds.
			# By default do not detect the storage speed and only the processor/memory, since that is a lot faster.
			# Some parameters can take a while to detect. Rather try to load/save to global vars.
			if not refresh:
				data = System.windowPropertyGet(property)
				if data: data = Converter.jsonFrom(data)
				else: data = None
			if detect and data is None:
				data = self.detect(full = full, callback = callback)
				System.windowPropertySet(property, Converter.jsonTo(data))

		if full: Hardware.DataFull = data
		else: Hardware.DataBasic = data

		return data

	@classmethod
	def processor(self, refresh = False):
		return self.data(refresh = refresh)['processor']

	@classmethod
	def processorType(self, refresh = False):
		return self.processor(refresh = refresh)['type']

	@classmethod
	def processorName(self, refresh = False):
		return self.processor(refresh = refresh)['name']

	@classmethod
	def processorModel(self, refresh = False):
		return self.processor(refresh = refresh)['model']

	@classmethod
	def processorLabel(self, refresh = False):
		return self.processor(refresh = refresh)['label']

	@classmethod
	def processorCount(self, refresh = False):
		return self.processor(refresh = refresh)['count']

	@classmethod
	def processorCountCore(self, refresh = False):
		return self.processorCount(refresh = refresh)['core']

	@classmethod
	def processorCountThread(self, refresh = False):
		return self.processorCount(refresh = refresh)['thread']

	@classmethod
	def processorCountLabel(self, refresh = False):
		return self.processorCount(refresh = refresh)['label']

	@classmethod
	def processorClock(self, refresh = False):
		return self.processor(refresh = refresh)['clock']

	@classmethod
	def processorClockTotal(self, refresh = False):
		return self.processorClock(refresh = refresh)['total']

	@classmethod
	def processorClockAverage(self, refresh = False):
		return self.processorClock(refresh = refresh)['average']

	@classmethod
	def processorClockHigh(self, refresh = False):
		return self.processorClock(refresh = refresh)['high']

	@classmethod
	def processorClockLow(self, refresh = False):
		return self.processorClock(refresh = refresh)['low']

	@classmethod
	def processorClockCommon(self, refresh = False):
		return self.processorClock(refresh = refresh)['common']

	@classmethod
	def processorClockCore(self, refresh = False):
		return self.processorClock(refresh = refresh)['core']

	@classmethod
	def processorClockLabel(self, refresh = False):
		return self.processorClock(refresh = refresh)['label']

	@classmethod
	def processorUsage(self, refresh = False):
		return self.processor(refresh = refresh)['usage']

	@classmethod
	def processorUsageLabel(self, refresh = False):
		return self.processorUsage(refresh = refresh)['label']

	@classmethod
	def processorUsageTotal(self, refresh = False):
		return self.processorUsage(refresh = refresh)['total']

	@classmethod
	def processorUsageTotalPercent(self, refresh = False):
		return self.processorUsageTotal(refresh = refresh)['percent']

	@classmethod
	def processorUsageTotalLabel(self, refresh = False):
		return self.processorUsageTotal(refresh = refresh)['label']

	@classmethod
	def processorUsageFree(self, refresh = False):
		return self.processorUsage(refresh = refresh)['free']

	@classmethod
	def processorUsageFreePercent(self, refresh = False):
		return self.processorUsageFree(refresh = refresh)['percent']

	@classmethod
	def processorUsageFreeLabel(self, refresh = False):
		return self.processorUsageFree(refresh = refresh)['label']

	@classmethod
	def processorUsageUsed(self, refresh = False):
		return self.processorUsage(refresh = refresh)['used']

	@classmethod
	def processorUsageUsedPercent(self, refresh = False):
		return self.processorUsageUsed(refresh = refresh)['percent']

	@classmethod
	def processorUsageUsedLabel(self, refresh = False):
		return self.processorUsageUsed(refresh = refresh)['label']

	@classmethod
	def memory(self, refresh = False):
		return self.data(refresh = refresh)['memory']

	@classmethod
	def memoryBytes(self, refresh = False):
		return self.memory(refresh = refresh)['bytes']

	@classmethod
	def memoryLabel(self, refresh = False):
		return self.memory(refresh = refresh)['label']

	@classmethod
	def memoryUsage(self, refresh = False):
		return self.memory(refresh = refresh)['usage']

	@classmethod
	def memoryUsageTotal(self, refresh = False):
		return self.memoryUsage(refresh = refresh)['total']

	@classmethod
	def memoryUsageTotalBytes(self, refresh = False):
		return self.memoryUsageTotal(refresh = refresh)['bytes']

	@classmethod
	def memoryUsageTotalPercent(self, refresh = False):
		return self.memoryUsageTotal(refresh = refresh)['percent']

	@classmethod
	def memoryUsageTotalLabel(self, refresh = False):
		return self.memoryUsageTotal(refresh = refresh)['label']

	@classmethod
	def memoryUsageFree(self, refresh = False):
		return self.memoryUsage(refresh = refresh)['free']

	@classmethod
	def memoryUsageFreeBytes(self, refresh = False):
		return self.memoryUsageFree(refresh = refresh)['bytes']

	@classmethod
	def memoryUsageFreePercent(self, refresh = False):
		return self.memoryUsageFree(refresh = refresh)['percent']

	@classmethod
	def memoryUsageFreeLabel(self, refresh = False):
		return self.memoryUsageFree(refresh = refresh)['label']

	@classmethod
	def memoryUsageUsed(self, refresh = False):
		return self.memoryUsage(refresh = refresh)['used']

	@classmethod
	def memoryUsageUsedBytes(self, refresh = False):
		return self.memoryUsageUsed(refresh = refresh)['bytes']

	@classmethod
	def memoryUsageUsedPercent(self, refresh = False):
		return self.memoryUsageUsed(refresh = refresh)['percent']

	@classmethod
	def memoryUsageUsedLabel(self, refresh = False):
		return self.memoryUsageUsed(refresh = refresh)['label']

	@classmethod
	def storage(self, refresh = False):
		return self.data(refresh = refresh)['storage']

	@classmethod
	def storageBytes(self, refresh = False):
		return self.storage(refresh = refresh)['bytes']

	@classmethod
	def storageLabel(self, refresh = False):
		return self.storage(refresh = refresh)['label']

	@classmethod
	def storageSpeed(self, refresh = False):
		return self.data(full = True, refresh = refresh)['storage']['speed'] # Retrieve the full data, since by default the storage speed is not detected.

	@classmethod
	def storageSpeedLabel(self, refresh = False):
		return self.storageSpeed(refresh = refresh)['label']

	@classmethod
	def storageSpeedBytes(self, refresh = False):
		return self.storageSpeed(refresh = refresh)['bytes']

	@classmethod
	def storageSpeedRead(self, refresh = False):
		return self.storageSpeed(refresh = refresh)['read']

	@classmethod
	def storageSpeedReadLabel(self, refresh = False):
		return self.storageSpeedRead(refresh = refresh)['label']

	@classmethod
	def storageSpeedReadBytes(self, refresh = False):
		return self.storageSpeedRead(refresh = refresh)['bytes']

	@classmethod
	def storageSpeedWrite(self, refresh = False):
		return self.storageSpeed(refresh = refresh)['write']

	@classmethod
	def storageSpeedWriteLabel(self, refresh = False):
		return self.storageSpeedWrite(refresh = refresh)['label']

	@classmethod
	def storageSpeedWriteBytes(self, refresh = False):
		return self.storageSpeedWrite(refresh = refresh)['bytes']

	@classmethod
	def storageUsage(self, refresh = False):
		return self.storage(refresh = refresh)['usage']

	@classmethod
	def storageUsageTotal(self, refresh = False):
		return self.storageUsage(refresh = refresh)['total']

	@classmethod
	def storageUsageTotalBytes(self, refresh = False):
		return self.storageUsageTotal(refresh = refresh)['bytes']

	@classmethod
	def storageUsageTotalPercent(self, refresh = False):
		return self.storageUsageTotal(refresh = refresh)['percent']

	@classmethod
	def storageUsageTotalLabel(self, refresh = False):
		return self.storageUsageTotal(refresh = refresh)['label']

	@classmethod
	def storageUsageFree(self, refresh = False):
		return self.storageUsage(refresh = refresh)['free']

	@classmethod
	def storageUsageFreeBytes(self, refresh = False):
		return self.storageUsageFree(refresh = refresh)['bytes']

	@classmethod
	def storageUsageFreePercent(self, refresh = False):
		return self.storageUsageFree(refresh = refresh)['percent']

	@classmethod
	def storageUsageFreeLabel(self, refresh = False):
		return self.storageUsageFree(refresh = refresh)['label']

	@classmethod
	def storageUsageUsed(self, refresh = False):
		return self.storageUsage(refresh = refresh)['used']

	@classmethod
	def storageUsageUsedBytes(self, refresh = False):
		return self.storageUsageUsed(refresh = refresh)['bytes']

	@classmethod
	def storageUsageUsedPercent(self, refresh = False):
		return self.storageUsageUsed(refresh = refresh)['percent']

	@classmethod
	def storageUsageUsedLabel(self, refresh = False):
		return self.storageUsageUsed(refresh = refresh)['label']

	########################################
	# USAGE
	########################################

	@classmethod
	def _usageCheck(self, processor = True, memory = True, interval = 3):
		total = 0
		while True:
			if Hardware.UsageStop: break
			if total > 900: break # If not manually stopped, stop after 15 minutes.
			usage = {}
			if processor: usage['processor'] = self.detectProcessorUsage()['used']['percent']
			if memory: usage['memory'] = self.detectMemoryUsage()['used']['percent']
			Hardware.UsageValues.append(usage)
			Time.sleep(interval)
			total += interval

	@classmethod
	def usageStart(self, processor = True, memory = True, interval = 3):
		Hardware.UsageStop = False
		Hardware.UsageValues = []
		Hardware.UsageThread = Pool.thread(target = self._usageCheck, kwargs = {'processor' : processor, 'memory' : memory, 'interval' : interval})
		Hardware.UsageThread.start()

	@classmethod
	def usageStop(self):
		Hardware.UsageStop = True
		try: started = Hardware.UsageThread
		except: started = False
		if started:
			Hardware.UsageThread.join()

			result = {}
			if Hardware.UsageValues:
				if 'processor' in Hardware.UsageValues[0]:
					processor = [i['processor'] for i in Hardware.UsageValues]
					processor = sum(processor) / float(len(processor))
					result['processor'] = {
						'percent' : processor,
						'label' : self._labelPercent(processor),
					}
				if 'memory' in Hardware.UsageValues[0]:
					memory = [i['memory'] for i in Hardware.UsageValues]
					memory = sum(memory) / float(len(memory))
					result['memory'] = {
						'percent' : memory,
						'label' : self._labelPercent(memory),
					}

			return result
		return None

	########################################
	# PERFORMANCE
	########################################

	@classmethod
	def performance(self, processor = True, processorTotal = True, processorSingle = True, memory = True, storage = False, storageRead = True, storageWrite = True, connection = False, connectionLatency = True, connectionSpeed = True, connectionIterations = 2, callback = None, fallback = True):
		from lib.modules.interface import Translation, Format
		from lib.modules.speedtest import SpeedTesterGlobal

		self.data(callback = callback, refresh = True, full = storage)

		# Make sure labels have a minimum of 1% instead of 0% and a maximum of 99% instead of 100%, purley for display purposes.
		minimum = 0.01
		maximum = 0.9949

		# Processor

		if not processor:
			if processorTotal is True: processorTotal = False
			if processorSingle is True: processorSingle = False

		if processorTotal is True: processorTotal = self.processorClockTotal()
		processorTotalValue = processorTotal
		if processorTotal:
			processorTotal = Math.scale(value = processorTotal, fromMinimum = Hardware.Performance['processor']['total']['minimum'], fromMaximum = Hardware.Performance['processor']['total']['maximum'], toMinimum = 0, toMaximum = 1)
			processorTotal = max(minimum, min(maximum, processorTotal))
		else:
			processorTotal = None

		if processorSingle is True: processorSingle = self.processorClockHigh()
		processorSingleValue = processorSingle
		if processorSingle:
			processorSingle = Math.scale(value = processorSingle, fromMinimum = Hardware.Performance['processor']['single']['minimum'], fromMaximum = Hardware.Performance['processor']['single']['maximum'], toMinimum = 0, toMaximum = 1)
			processorSingle = max(minimum, min(maximum, processorSingle))
		else:
			processorSingle = None

		# Memory
		if memory is True: memory = self.memoryBytes()
		memoryValue = memory
		if memory:
			memory = Math.scale(value = memory, fromMinimum = Hardware.Performance['memory']['minimum'], fromMaximum = Hardware.Performance['memory']['maximum'], toMinimum = 0, toMaximum = 1)
			memory = max(minimum, min(maximum, memory))
		else:
			memory = None

		# Storage

		if not storage:
			if storageRead is True: storageRead = False
			if storageWrite is True: storageWrite = False

		if storageRead is True: storageRead = self.storageSpeedReadBytes()
		storageReadValue = storageRead
		if storageRead:
			storageRead = Math.scale(value = storageRead, fromMinimum = Hardware.Performance['storage']['read']['minimum'], fromMaximum = Hardware.Performance['storage']['read']['maximum'], toMinimum = 0, toMaximum = 1)
			storageRead = max(minimum, min(maximum, storageRead))
		else:
			storageRead = None

		if storageWrite is True: storageWrite = self.storageSpeedWriteBytes()
		storageWriteValue = storageWrite
		if storageWrite:
			storageWrite = Math.scale(value = storageWrite, fromMinimum = Hardware.Performance['storage']['write']['minimum'], fromMaximum = Hardware.Performance['storage']['write']['maximum'], toMinimum = 0, toMaximum = 1)
			storageWrite = max(minimum, min(maximum, storageWrite))
		else:
			storageWrite = None

		# Connection

		if not connection:
			if connectionLatency is True: connectionLatency = False
			if connectionSpeed is True: connectionSpeed = False

		if callback and (connectionLatency is True or connectionSpeed is True): callback(Hardware.CategoryConnection)

		if connectionLatency is True:
			connectionLatency = []
			tester = SpeedTesterGlobal()
			for i in range(connectionIterations):
				connectionLatency.append(tester.testLatency())
			connectionLatency = [i for i in connectionLatency if i]
			if connectionLatency: connectionLatency = min(connectionLatency)
			else: connectionLatency = None
		connectionLatencyValue = connectionLatency
		if connectionLatency:
			# Switch minimum and maximum, since lower values are better.
			connectionLatency = Math.scale(value = connectionLatency, fromMinimum = Hardware.Performance['connection']['latency']['maximum'], fromMaximum = Hardware.Performance['connection']['latency']['minimum'], toMinimum = 0, toMaximum = 1)
			connectionLatency = max(minimum, min(maximum, connectionLatency))
		else:
			connectionLatency = None

		if connectionSpeed is True:
			connectionSpeed = []
			tester = SpeedTesterGlobal()
			# First iteration takes about 13-20 secs and subsequent tests take only 10 secs, probably because of detecting the best server.
			# Subsequent tests also seem to often have better speeds.
			for i in range(connectionIterations):
				connectionSpeed.append(tester.testDownload())
			connectionSpeed = [i for i in connectionSpeed if i]
			if connectionSpeed: connectionSpeed = max(connectionSpeed)
			else: connectionSpeed = None

			# Also set in speedtest.py, but here we want to pick the highest value.
			# Used to generate more accurate colors for the bandwidth/filesize labels in the stream window.
			if connectionSpeed: Settings.set('internal.speedtest', int(connectionSpeed))
		connectionSpeedValue = connectionSpeed
		if connectionSpeed:
			connectionSpeed = Math.scale(value = connectionSpeed, fromMinimum = Hardware.Performance['connection']['speed']['minimum'], fromMaximum = Hardware.Performance['connection']['speed']['maximum'], toMinimum = 0, toMaximum = 1)
			connectionSpeed = max(minimum, min(maximum, connectionSpeed))
		else:
			connectionSpeed = None

		# Fallback

		# On some devices some hardware cannot be detected.
		# Use fallback ratings, otherwise various code (like provider optimization) will have ratings that are too high, since some hardware values are excluded.
		# Eg: On Nvidia Shield and AppleTV the CPU (at least the clock) cannot be detected.

		processorTotalFallback = None
		processorSingleFallback = None
		memoryFallback = None
		storageReadFallback = None
		storageWriteFallback = None
		connectionLatencyFallback = None
		connectionSpeedFallback = None
		if fallback:
			if processorTotal is None or processorSingle is None:
				processorType = self.processorType()
				processorCount = self.processorCountCore() or 0
				if processorType == Hardware.ProcessorIntel or processorType == Hardware.ProcessorAmd:
					if processorCount >= 6:
						if processorTotal is None: processorTotalFallback = 0.6
						if processorSingle is None: processorSingleFallback = 0.6
					else:
						if processorTotal is None: processorTotalFallback = 0.5
						if processorSingle is None: processorSingleFallback = 0.5
				elif processorType == Hardware.ProcessorArm:
					if processorCount >= 6:
						if processorTotal is None: processorTotalFallback = 0.25
						if processorSingle is None: processorSingleFallback = 0.25
					elif processorCount >= 4:
						if processorTotal is None: processorTotalFallback = 0.2
						if processorSingle is None: processorSingleFallback = 0.2
					else:
						if processorTotal is None: processorTotalFallback = 0.15
						if processorSingle is None: processorSingleFallback = 0.15
				else:
					if processorCount >= 6:
						if processorTotal is None: processorTotalFallback = 0.2
						if processorSingle is None: processorSingleFallback = 0.2
					elif processorCount >= 4:
						if processorTotal is None: processorTotalFallback = 0.15
						if processorSingle is None: processorSingleFallback = 0.15
					else:
						if processorTotal is None: processorTotalFallback = 0.1
						if processorSingle is None: processorSingleFallback = 0.1
			if memory is None: memoryFallback = 0.3
			if storageRead is None: storageReadFallback = 0.5
			if storageWrite is None: storageWriteFallback = 0.2
			if connectionLatency is None: connectionLatencyFallback = 0.5
			if connectionSpeed is None: connectionSpeedFallback = 0.5

		processorTotalRater = processorTotalFallback if fallback and processorTotal is None else processorTotal
		processorSingleRater = processorSingleFallback if fallback and processorSingle is None else processorSingle
		memoryRater = memoryFallback if fallback and memory is None else memory
		storageReadRater = storageReadFallback if fallback and storageRead is None else storageRead
		storageWriteRater = storageWriteFallback if fallback and storageWrite is None else storageWrite
		connectionLatencyRater = connectionLatencyFallback if fallback and connectionLatency is None else connectionLatency
		connectionSpeedRater = connectionSpeedFallback if fallback and connectionSpeed is None else connectionSpeed

		# Weight

		weightProcessorTotal = Hardware.Performance['processor']['total']['weight']
		weightProcessorSingle = Hardware.Performance['processor']['single']['weight']
		weightProcessor = weightProcessorTotal + weightProcessorSingle
		weightMemory = Hardware.Performance['memory']['weight']
		weightStorageRead = Hardware.Performance['storage']['read']['weight']
		weightStorageWrite = Hardware.Performance['storage']['write']['weight']
		weightStorage = weightStorageRead + weightStorageWrite
		weightConnectionLatency = Hardware.Performance['connection']['latency']['weight']
		weightConnectionSpeed = Hardware.Performance['connection']['speed']['weight']
		weightConnection = weightConnectionLatency + weightConnectionSpeed

		weights = []
		if not processorTotalRater is None: weights.append(weightProcessorTotal)
		if not processorSingleRater is None: weights.append(weightProcessorSingle)
		if not memoryRater is None: weights.append(weightMemory)
		if not storageReadRater is None: weights.append(weightStorageRead)
		if not storageWriteRater is None: weights.append(weightStorageWrite)
		if not connectionLatencyRater is None: weights.append(weightConnectionLatency)
		if not connectionSpeedRater is None: weights.append(weightConnectionSpeed)
		weights = sum(weights)

		# Rating

		rating = []
		ratingProcessor = None if (processorTotalRater is None and processorSingleRater is None) else 0
		ratingMemory = None
		ratingStorage = None if (storageReadRater is None and storageWriteRater is None) else 0
		ratingConnection = None if (connectionLatencyRater is None and connectionSpeedRater is None) else 0

		if not processorTotalRater is None:
			rating.append(processorTotalRater * (weightProcessorTotal / weights))
			ratingProcessor += processorTotalRater * (weightProcessorTotal / weightProcessor)
		if not processorSingleRater is None:
			rating.append(processorSingleRater * (weightProcessorSingle / weights))
			ratingProcessor += processorSingleRater * (weightProcessorSingle / weightProcessor)
		if not memoryRater is None:
			rating.append(memoryRater * (weightMemory / weights))
			ratingMemory = memoryRater
		if not storageReadRater is None:
			rating.append(storageReadRater * (weightStorageRead / weights))
			ratingStorage += storageReadRater * (weightStorageRead / weightStorage)
		if not storageWriteRater is None:
			rating.append(storageWriteRater * (weightStorageWrite / weights))
			ratingStorage += storageWriteRater * (weightStorageWrite / weightStorage)
		if not connectionLatencyRater is None:
			rating.append(connectionLatencyRater * (weightConnectionLatency / weights))
			ratingConnection += connectionLatencyRater * (weightConnectionLatency / weightConnection)
		if not connectionSpeedRater is None:
			rating.append(connectionSpeedRater * (weightConnectionSpeed / weights))
			ratingConnection += connectionSpeedRater * (weightConnectionSpeed / weightConnection)

		rating = sum([i for i in rating if i])
		rating = Math.round(rating, places = 2)
		if ratingProcessor: ratingProcessor = Math.round(ratingProcessor, places = 2)
		if ratingMemory: ratingMemory = Math.round(ratingMemory, places = 2)
		if ratingStorage: ratingStorage = Math.round(ratingStorage, places = 2)
		if ratingConnection: ratingConnection = Math.round(ratingConnection, places = 2)

		# Label

		labelRating = None
		labelPerformance = None
		labelDescription = None
		labelProcessorDevice = None
		labelProcessorRating = None
		labelProcessorPerformance = None
		labelProcessorDescription = None
		labelMemoryDevice = None
		labelMemoryRating = None
		labelMemoryPerformance = None
		labelMemoryDescription = None
		labelStorageDevice = None
		labelStorageRating = None
		labelStoragePerformance = None
		labelStorageDescription = None
		labelConnectionDevice = None
		labelConnectionRating = None
		labelConnectionPerformance = None
		labelConnectionDescription = None
		if not rating is None:
			labelRating = self._labelPercent(rating)
		if not ratingProcessor is None:
			labelProcessorDevice = self.processorClockLabel()
			labelProcessorRating = self._labelPercent(ratingProcessor)
		if not ratingMemory is None:
			labelMemoryDevice = self.memoryLabel()
			labelMemoryRating = self._labelPercent(ratingMemory)
		if not ratingStorage is None:
			labelStorageDevice = self.storageLabel()
			labelStorageRating = self._labelPercent(ratingStorage)
		if not ratingConnection is None:
			labelConnection1 = SpeedTesterGlobal._formatSpeed(connectionSpeedValue)
			labelConnection2 = SpeedTesterGlobal._formatLatency(connectionLatencyValue)
			if labelConnection1 == SpeedTesterGlobal.UnknownCapitalize and labelConnection2 == SpeedTesterGlobal.UnknownCapitalize:
				labelConnectionDevice = labelConnection1
			elif labelConnection1 == SpeedTesterGlobal.UnknownCapitalize:
				labelConnectionDevice = labelConnection2
			elif labelConnection2 == SpeedTesterGlobal.UnknownCapitalize:
				labelConnectionDevice = labelConnection1
			else:
				labelConnectionDevice = '%s @ %s' % (labelConnection1, labelConnection2)
			labelConnectionRating = self._labelPercent(ratingConnection)

		# Performance

		performance = None
		performanceProcessor = None
		performanceMemory = None
		performanceStorage = None
		performanceConnection = None
		for item in Hardware.Performance['performance']:
			if performance is None and rating >= item['rating']:
				performance = item['performance']
				labelPerformance = Translation.string(item['label'])
			if performanceProcessor is None and not ratingProcessor is None and ratingProcessor >= item['rating']:
				performanceProcessor = item['performance']
				labelProcessorPerformance = Translation.string(item['label'])
			if performanceMemory is None and not ratingMemory is None and ratingMemory >= item['rating']:
				performanceMemory = item['performance']
				labelMemoryPerformance = Translation.string(item['label'])
			if performanceStorage is None and not ratingStorage is None and ratingStorage >= item['rating']:
				performanceStorage = item['performance']
				labelStoragePerformance = Translation.string(item['label'])
			if performanceConnection is None and not ratingConnection is None and ratingConnection >= item['rating']:
				performanceConnection = item['performance']
				labelConnectionPerformance = Translation.string(item['label'])

		separator = Format.iconSeparator(color = True, pad = True)
		if not rating is None: labelDescription = '%s%s%s' % (labelPerformance, separator, labelRating)
		if not ratingProcessor is None: labelProcessorDescription = '%s%s%s (%s)' % (labelProcessorPerformance, separator, labelProcessorRating, labelProcessorDevice)
		if not ratingMemory is None: labelMemoryDescription = '%s%s%s (%s)' % (labelMemoryPerformance, separator, labelMemoryRating, labelMemoryDevice)
		if not ratingStorage is None: labelStorageDescription = '%s%s%s (%s)' % (labelStoragePerformance, separator, labelStorageRating, labelStorageDevice)
		if not ratingConnection is None: labelConnectionDescription = '%s%s%s (%s)' % (labelConnectionPerformance, separator, labelConnectionRating, labelConnectionDevice)

		# Result

		return {
			'rating' : rating,
			'performance' : performance,
			'label' : {
				'rating' : labelRating,
				'performance' : labelPerformance,
				'description' : labelDescription,
			},
			'processor' : {
				'rating' : ratingProcessor,
				'performance' : performanceProcessor,
				'value' : {
					'total' : processorTotalValue,
					'single' : processorSingleValue,
				},
				'label' : {
					'device' : labelProcessorDevice,
					'rating' : labelProcessorRating,
					'performance' : labelProcessorPerformance,
					'description' : labelProcessorDescription,
				},
			},
			'memory' : {
				'rating' : ratingMemory,
				'performance' : performanceMemory,
				'value' : memoryValue,
				'label' : {
					'device' : labelMemoryDevice,
					'rating' : labelMemoryRating,
					'performance' : labelMemoryPerformance,
					'description' : labelMemoryDescription,
				},
			},
			'storage' : {
				'rating' : ratingStorage,
				'performance' : performanceStorage,
				'value' : {
					'read' : storageReadValue,
					'write' : storageWriteValue,
				},
				'label' : {
					'device' : labelStorageDevice,
					'rating' : labelStorageRating,
					'performance' : labelStoragePerformance,
					'description' : labelStorageDescription,
				},
			},
			'connection' : {
				'rating' : ratingConnection,
				'performance' : performanceConnection,
				'value' : {
					'speed' : connectionSpeedValue,
					'latency' : connectionLatencyValue,
				},
				'label' : {
					'device' : labelConnectionDevice,
					'rating' : labelConnectionRating,
					'performance' : labelConnectionPerformance,
					'description' : labelConnectionDescription,
				},
			},
		}

	@classmethod
	def performanceRating(self, processor = True, processorTotal = True, processorSingle = True, memory = True, storage = False, storageRead = True, storageWrite = True, connection = False, connectionLatency = True, connectionSpeed = True, connectionIterations = 3):
 		return self.performance(processor = processor, processorTotal = processorTotal, processorSingle = processorSingle, memory = memory, storage = storage, storageRead = storageRead, storageWrite = storageWrite, connection = connection, connectionLatency = connectionLatency, connectionSpeed = connectionSpeed, connectionIterations = connectionIterations)['rating']

	@classmethod
	def performanceType(self, processor = True, processorTotal = True, processorSingle = True, memory = True, storage = False, storageRead = True, storageWrite = True, connection = False, connectionLatency = True, connectionSpeed = True, connectionIterations = 3):
 		return self.performance(processor = processor, processorTotal = processorTotal, processorSingle = processorSingle, memory = memory, storage = storage, storageRead = storageRead, storageWrite = storageWrite, connection = connection, connectionLatency = connectionLatency, connectionSpeed = connectionSpeed, connectionIterations = connectionIterations)['performance']

	@classmethod
	def performanceDevices(self, common = False):
		#	Intel i7 8700 (8th Gen, 2017):	25.0GHz	(6(12)cores @ 3.2GHz)
		#	Intel i5 8600 (8th Gen, 2018):	18.6GHz	(6(6)cores @ 3.1GHz)
		#	Intel i3 8300 (8th Gen, 2018):	14.8GHz	(4(4)cores @ 3.7GHz)
		# 	Amazon Fire TV Cube:			12.6GHz	(4cores @ 2.2GHz + 2cores @ 1.9GHz)		2GB
		# 	Amazon Fire TV Stick:			6.8GHz	(4cores @ 1.7GHz)						1GB
		# 	Amazon Fire TV Stick 4K:		6.8GHz	(4cores @ 1.7GHz)						1.5GB
		# 	Amazon Fire TV Stick 4K Max:	7.2GHz	(4cores @ 1.8GHz)						2GB
		# 	AppleTV HD:						3.0GHz	(2cores @ 1.5GHz)						2GB
		# 	AppleTV 4K:						14.3GHz	(6cores @ 2.38GHz)						3GB
		# 	Nvidia Shield TV:				12.8GHz	(4cores @ 1.9GHz + 4cores @ 1.3GHz)		2GB
		# 	Nvidia Shield TV Pro:			12.8GHz	(4cores @ 1.9GHz + 4cores @ 1.3GHz)		3GB
		#	Roku Premiere:					4.8GHz	(4cores @ 1.2GHz)						1GB
		#	Roku Ultra:						4.8GHz	(4cores @ 1.2GHz)						1GB
		#	Roku Streaming Stick:			3.2GHz	(4cores @ 0.8GHz)						512MB
		# 	Raspberry Pi 4:					6.0GHz	(4cores @ 1.5GHz)						2GB/4GB/8GB
		# 	Odroid N2+:						12.6GHz	(4cores @ 2.2GHz + 2cores @ 1.9GHz)		4GB
		#	Asus Tinker Board S:			7.2GHz	(4cores @ 1.8GHz)						2GB
		#	Zidoo Z9S:						8.0GHz	(4cores @ 2.0GHz)						2GB
		#	Beelink BT3 Pro II Mini:		7.6GHz	(4cores @ 1.9Hz)						4GB
		#	Xiaomi Mi Box S:				8.0GHz	(4cores @ 2.0GHz)						2GB
		#	MINIX NEO U9-H:					16.0GHz	(8cores @ 2.0GHz)						2GB
		#	Pendoo X6 PRO:					6.0GHz	(4cores @ 1.5GHz)						4GB
		#	Vero 4K+:						6.4GHz	(4cores @ 1.6GHz)						2GB
		#	UGOOS AM6 Plus:					8.8GHz	(4cores @ 2.2GHz)						4GB

		result = [
			{'name' : 'Intel i7 8700', 'hardware' : '6 cores @ 3.2GHz | 16GB', 'common' : True, 'processor' : {'total' : 25000000000, 'single' : 3200000000}, 'memory' : 17179869184, 'storage' : {'read' : 314572800, 'write' : 31457280}},
			{'name' : 'Intel i5 8600', 'hardware' : '6 cores @ 3.1GHz | 12GB', 'common' : False, 'processor' : {'total' : 18600000000, 'single' : 3100000000}, 'memory' : 12884901888, 'storage' : {'read' : 314572800, 'write' : 31457280}},
			{'name' : 'Intel i3 8300', 'hardware' : '4 cores @ 3.7GHz | 8GB', 'common' : True, 'processor' : {'total' : 14800000000, 'single' : 3700000000}, 'memory' : 8589934592, 'storage' : {'read' : 314572800, 'write' : 31457280}},

			{'name' : 'Amazon Fire TV Cube', 'hardware' : '4 cores @ 2.2GHz + 2 cores @ 1.9GHz | 2GB', 'common' : False, 'processor' : {'total' : 12600000000, 'single' : 2200000000}, 'memory' : 2147483648, 'storage' : {'read' : 52428800, 'write' : 31457280}},
			{'name' : 'Amazon Fire TV Stick', 'hardware' : '4 cores @ 1.7GHz | 1GB', 'common' : True, 'processor' : {'total' : 6800000000, 'single' : 1700000000}, 'memory' : 1073741824, 'storage' : {'read' : 52428800, 'write' : 31457280}},
			{'name' : 'Amazon Fire TV Stick 4K Max', 'hardware' : '4 cores @ 1.8GHz | 2GB', 'common' : False, 'processor' : {'total' : 7200000000, 'single' : 1800000000}, 'memory' : 2147483648, 'storage' : {'read' : 52428800, 'write' : 31457280}},

			{'name' : 'AppleTV HD', 'hardware' : '2 cores @ 1.5GHz | 2GB', 'common' : False, 'processor' : {'total' : 3000000000, 'single' : 1500000000}, 'memory' : 2147483648, 'storage' : {'read' : 52428800, 'write' : 31457280}},
			{'name' : 'AppleTV 4K', 'hardware' : '6 cores @ 2.38GHz | 3GB', 'common' : True, 'processor' : {'total' : 14280000000, 'single' : 2380000000}, 'memory' : 3221225472, 'storage' : {'read' : 52428800, 'write' : 31457280}},

			{'name' : 'Roku Ultra', 'hardware' : '4 cores @ 1.2GHz | 1GB', 'common' : False, 'processor' : {'total' : 4800000000, 'single' : 1200000000}, 'memory' : 1073741824, 'storage' : {'read' : 52428800, 'write' : 31457280}},
			{'name' : 'Roku Streaming Stick', 'hardware' : '4 cores @ 800MHz | 512MB', 'common' : False, 'processor' : {'total' : 3200000000, 'single' : 800000000}, 'memory' : 536870912, 'storage' : {'read' : 52428800, 'write' : 31457280}},

			{'name' : 'Nvidia Shield TV', 'hardware' : '4 cores @ 1.9GHz + 4 cores @ 1.3GHz | 2GB', 'common' : True, 'processor' : {'total' : 12800000000, 'single' : 1900000000}, 'memory' : 2147483648, 'storage' : {'read' : 52428800, 'write' : 31457280}},

			{'name' : 'Raspberry Pi 4', 'hardware' : '4 cores @ 1.5GHz | 4GB', 'common' : True, 'processor' : {'total' : 6000000000, 'single' : 1500000000}, 'memory' : 4294967296, 'storage' : {'read' : 10485760, 'write' : 10485760}},
			{'name' : 'Odroid N2+', 'hardware' : '4 cores @ 2.2GHz + 2 cores @ 1.9GHz | 4GB', 'common' : True, 'processor' : {'total' : 12600000000, 'single' : 2200000000}, 'memory' : 4294967296, 'storage' : {'read' : 10485760, 'write' : 10485760}},
			{'name' : 'Beelink BT3 Pro II Mini', 'hardware' : '4 cores @ 1.9Hz | 4GB', 'common' : False, 'processor' : {'total' : 7600000000, 'single' : 1900000000}, 'memory' : 4294967296, 'storage' : {'read' : 10485760, 'write' : 10485760}},
			{'name' : 'Vero 4K+', 'hardware' : '4 cores @ 1.6GHz | 2GB', 'common' : False, 'processor' : {'total' : 6400000000, 'single' : 1600000000}, 'memory' : 2147483648, 'storage' : {'read' : 10485760, 'write' : 10485760}},
		]
		if common: result = [i for i in result if i['common']]
		return result

	@classmethod
	def performanceTest(self):
		devices = self.performanceDevices()
		identation = '     '
		Logger.log('DEVICE PERFORMANCE')
		for device in devices:
			performance = self.performance(processorTotal = device['processor']['total'], processorSingle = device['processor']['single'], memory = device['memory'])
			Logger.log(device['name'])
			Logger.log(identation + 'Hardware:  %s' % device['hardware'])
			Logger.log(identation + 'Overall:   %s | %s' % (performance['label']['performance'], performance['label']['rating']))
			Logger.log(identation + 'Processor: %s | %s' % (performance['processor']['label']['performance'], performance['processor']['label']['rating']))
			Logger.log(identation + 'Memory:    %s | %s' % (performance['memory']['label']['performance'], performance['memory']['label']['rating']))

	@classmethod
	def performanceWeightProcessor(self):
		return Hardware.Performance['processor']['total']['weight'] + Hardware.Performance['processor']['single']['weight']

	@classmethod
	def performanceWeightMemory(self):
		return Hardware.Performance['memory']['weight']

	@classmethod
	def performanceWeightConnection(self):
		return Hardware.Performance['connection']['latency']['weight'] + Hardware.Performance['connection']['speed']['weight']

	########################################
	# DETECT - PROCESSOR
	########################################

	@classmethod
	def detectProcessorType(self, model = None):
		type = None

		try:
			model = model if model else self.detectProcessorModel()
			if model:
				if Regex.match(data = model, expression = '(intel)'): type = Hardware.ProcessorIntel
				elif Regex.match(data = model, expression = '(amd)'): type = Hardware.ProcessorAmd
				elif Regex.match(data = model, expression = '(arm|aarch|risc|acorn|a32|a64)'): type = Hardware.ProcessorArm
				elif Regex.match(data = model, expression = '(arc)'): type = Hardware.ProcessorArc
				elif Regex.match(data = model, expression = '(appletv1,)'): type = Hardware.ProcessorIntel # AppleTV: Pentium M.
				elif Regex.match(data = model, expression = '(appletv)'): type = Hardware.ProcessorArm # AppleTV: Native ARM or new Apple A ARM-based processors .
		except: Logger.error()

		return type

	@classmethod
	def detectProcessorName(self, type = None):
		type = type if type else self.detectProcessorType()

		try: name = Hardware.Processor[type]['name']
		except: name = None

		return name

	@classmethod
	def detectProcessorModel(self):
		# Manual
		windows = False
		mac = False
		linux = False
		android = Platform.detectAndroid()
		try:
			import platform
			system = platform.system()
			if system:
				system = system.lower()
				if 'windows' in system: windows = True
				elif 'darwin' in system or 'mac' in system: mac = True
				elif 'linux' in system or 'unix' in system: linux = True
		except: pass

		# Windows
		try:
			if windows:
				result = Subprocess.output(['wmic', 'cpu', 'get', 'name']).strip().split('\r\n')[1]
				if result:
					processor = platform.processor()
					if processor in result: return result
					else: return ' '.join([result, processor])
		except: pass

		# Mac
		try:
			if mac:
				try:
					import os
					os.environ['PATH'] = os.environ['PATH'] + os.pathsep + '/usr/sbin'
				except: pass
				try:
					result = Subprocess.fallback('sysctl -n machdep.cpu.brand_string').strip()
					if result: return result
				except: pass
				try:
					data = Subprocess.fallback('system_profiler').strip()
					if data:
						result = Regex.extract(data = data, expression = 'processor\s*name\s*:?\s*(.*?)(?:$|\n)')
						if result: return result
				except: pass
		except: pass

		# Linux
		try:
			if linux or android or mac:
				data = Converter.unicode(open('/proc/cpuinfo').read())
				if data:
					result = Regex.extract(data = data, expression = 'model\s*name\s*:\s*(.*?)[\n\r]')
					if result: return result.strip()
					result = Regex.extract(data = data, expression = 'processor\s*:\s*(.*?(?:intel|amd|arm|aarch|risc|acorn|a32|a64|arc).*?)(?:$|\n)') # Android devices.
					if result: return result.strip()
		except: pass

		# CpuInfo
		try:
			# The get_cpu_info() function fails on Android, because it calls get_cpu_info_json() which in turn calls Popen() which does not have permissions on Android.
			from lib.modules.external import Importer
			result = Importer.moduleCpuInfo()._get_cpu_info_internal()
			if result:
				result = result['brand_raw']
				if result: return result
		except: pass

		# Others
		try:
			import platform
			result = platform.processor()
			if result: return result
		except: pass

		# At least ARM devices can be detected from the architecture.
		try:
			# NB: Not full, otherwise there is infinite recuysrions between Platform and Hardware.
			result = Platform.architectureLabel(full = False)
			if result: return result
		except: pass

		return None

	@classmethod
	def detectProcessorCount(self):
		# http://stackoverflow.com/questions/1006289/how-to-find-out-the-number-of-cpus-using-python

		def _result(cores = None, threads = None):
			try:
				if cores:
					cores = int(cores)
					if cores and cores > 0:
						if threads is None: threads = cores
						label = self._labelProcessor(cores = cores, threads = threads)
						return {
							'core' : cores,
							'thread' : threads,
							'label' : label,
						}
			except: Logger.error()
			return {
				'core' : None,
				'thread' : None,
				'label' : None,
			}

		# PSUtil
		try:
			psutil = Platform.psutil()
			cores = psutil.cpu_count(logical = False)
			threads = psutil.cpu_count(logical = True)
			result = _result(cores = cores, threads = threads)
			if result and result['core']: return result
		except: pass

		# CpuInfo
		try:
			# The get_cpu_info() function fails on Android, because it calls get_cpu_info_json() which in turn calls Popen() which does not have permissions on Android.
			from lib.modules.external import Importer
			result = Importer.moduleCpuInfo()._get_cpu_info_internal()
			if result:
				result = _result(result['count'])
				if result and result['core']: return result
		except: pass

		# Python 2.6+
		try:
			import multiprocessing
			result = multiprocessing.cpu_count()
			result = _result(result)
			if result and result['core']: return result
		except: pass

		# POSIX
		try:
			result = int(os.sysconf('SC_NPROCESSORS_ONLN'))
			result = _result(result)
			if result and result['core']: return result
		except: pass

		# Windows
		try:
			result = int(os.environ['NUMBER_OF_PROCESSORS'])
			result = _result(result)
			if result and result['core']: return result
		except: pass

		# jython
		try:
			from java.lang import Runtime
			runtime = Runtime.getRuntime()
			result = runtime.availableProcessors()
			result = _result(result)
			if result and result['core']: return result
		except: pass

		# cpuset
		# cpuset may restrict the number of *available* processors
		try:
			result = Converter.unicode(open('/proc/self/status').read())
			result = Regex.extract(data = result, expression = '(?m)^Cpus_allowed:\s*(.*)$')
			if result:
				result = bin(int(result.replace(',', ''), 16)).count('1')
				result = _result(result)
				if result and result['core']: return result
		except: pass

		# BSD
		try:
			result = Subprocess.fallback('sysctl -n hw.ncpu')
			result = _result(result)
			if result and result['core']: return result
		except: pass

		# Linux
		try:
			result = Converter.unicode(open('/proc/cpuinfo').read()).count('processor\t:')
			result = _result(result)
			if result and result['core']: return result
		except: pass

		# Solaris
		try:
			devices = os.listdir('/devices/pseudo/')
			result = 0
			for device in devices:
				if Regex.match(data = device, expression = '^cpuid@[0-9]+$'): result += 1
			result = _result(result)
			if result and result['core']: return result
		except: pass

		# Other Unix (heuristic)
		try:
			try:
				dmesg = Converter.unicode(open('/var/run/dmesg.boot').read())
			except IOError:
				dmesg = Subprocess.fallback('dmesg')
			result = 0
			while '\ncpu' + str(result) + ':' in dmesg:
				result += 1
			result = _result(result)
			if result and result['core']: return result
		except: pass

		return _result()

	@classmethod
	def detectProcessorClock(self, model = None, count = None):
		def _label(clock, cores = None):
			if cores: cores = self._labelProcessor(cores = cores) + ' @ '
			else: cores = ''
			return '%s%.1f GHz' % (cores, (clock / 1000000000.0))

		def _result(clock = None, unit = None, count = None):
			try:
				if clock:
					multiplier = 1
					if unit == 'khz': multiplier = 1000
					elif unit == 'mhz': multiplier = 1000000
					elif unit == 'ghz': multiplier = 1000000000

					cores = count['core']
					threads = count['thread']

					clocks = []
					if Tools.isArray(clock):
						for i in clock:
							i = int(float(i) * multiplier)
							if i or i > 0: clocks.append(i)
					else:
						clock = int(float(clock) * multiplier)
						if not clock or clock <= 0: return _result()
						clocks = [clock] * cores

					total = int(sum(clocks))
					counter = len(clocks)

					# Some CPUs, like Intel i, allow more threads to run on fewer physical cores (eg: 6 cores with 12 threads).
					# Multiple threads cannot excute at 100% performance on the cores.
					# Intel claims that hyper-threading increases performance by about 30%.
					# With 6 cores and 12 threads, 6 threads will run at 100% and the other 6 threads at 30%.
					ratio = None
					factor = 0.3
					if counter > cores:
						ratio = (counter - cores) / float(counter)
						total = int((total * (1 - ratio)) + (total * ratio * factor))
					elif counter < threads:
						ratio = (threads - counter) / float(threads)
						total = int(total + (total * ratio * factor))

					average = int(total / float(counter))
					high = max(clocks)
					low = min(clocks)

					group = {}
					for i in clocks:
						if not i in group: group[i] = 0
						group[i] += 1
					group = [{'clock' : key, 'cores' : value} for key, value in group.items()]
					group = Tools.listSort(data = group, key = lambda i : i['cores'], reverse = True)
					common = group[0]['clock']

					label = _label(clock = common, cores = cores)
					if len(group) > 1: # Windows only detects 1 core.
						description = []
						for i in range(len(group)):
							description.append(_label(clock = group[i]['clock'], cores = group[i]['cores']))
						description = ' / '.join(description)
					else:
						description = label

					return {
						'total' : total,
						'average' : average,
						'high' : high,
						'low' : low,
						'common' : common,
						'core' : clocks,
						'label' : label,
						'description' : description,
					}
			except: Logger.error()
			return {
				'total' : None,
				'average' : None,
				'high' : None,
				'low' : None,
				'common' : None,
				'core' : None,
				'label' : None,
				'description' : None,
			}

		count = count if count else self.detectProcessorCount()

		# PSUtil
		try:
			result = Platform.psutil().cpu_freq(percpu = True)
			if len(result) == 1 and count['core'] > 1: result *= count['core'] # On windows only 1 core is detected.
			if result:
				result = [(i.max if (i.max and i.max > 0) else i.current) for i in result]
				result = _result(result, unit = 'mhz', count = count)
				if result and result['total']: return result
		except: pass

		# CpuInfo
		try:
			# The get_cpu_info() function fails on Android, because it calls get_cpu_info_json() which in turn calls Popen() which does not have permissions on Android.
			from lib.modules.external import Importer
			result = Importer.moduleCpuInfo()._get_cpu_info_internal()
			if result:
				result = _result(result['hz_advertised'][0], count = count)
				if result and result['total']: return result
		except: pass

		# Manual
		windows = False
		mac = False
		linux = False
		android = Platform.detectAndroid()
		try:
			import platform
			system = platform.system()
			if system:
				system = system.lower()
				if 'windows' in system: windows = True
				elif 'darwin' in system or 'mac' in system: mac = True
				elif 'linux' in system or 'unix' in system: linux = True
		except: pass

		# Windows
		try:
			if windows:
				for clock in ['MaxClockSpeed', 'CurrentClockSpeed']:
					try:
						result = Subprocess.output(['wmic', 'cpu', 'get', clock]).strip().split('\r\n')[1]
						result = _result(result, unit = 'mhz', count = count)
						if result and result['total']: return result
					except: pass
		except: pass

		# Mac
		try:
			if mac:
				for clock in ['hw.cpufrequency_max', 'hw.cpufrequency']:
					try:
						import os
						os.environ['PATH'] = os.environ['PATH'] + os.pathsep + '/usr/sbin'
						result = Subprocess.fallback('sysctl ' + clock).strip()
						result = _result(result, unit = 'hz', count = count)
						if result and result['total']: return result
					except: pass
		except: pass

		# Linux
		try:
			if linux or android or mac:
				infos = []
				try: infos.append(Subprocess.fallback('lscpu'))
				except: pass
				try: infos.append(Converter.unicode(open('/proc/cpuinfo').read()))
				except: pass
				for info in infos:
					try:
						data = info.strip()
						if data:
							result = Regex.extract(data = data, expression = 'cpu\s*mhz.*?([\d\.]+)')
							result = _result(result, unit = 'mhz', count = count)
							if result and result['total']: return result

							result = Regex.extract(data = data, expression = 'cpu\s*ghz.*?([\d\.]+)')
							result = _result(result, unit = 'ghz', count = count)
							if result and result['total']: return result
					except: pass
		except: pass

		# CPU Model
		try:
			data = model if model else self.detectProcessorModel()
			if data:
				result = Regex.extract(data = data, expression = '([\d\.\-]+)\s*mhz')
				result = _result(result, unit = 'mhz', count = count)
				if result and result['total']: return result

				result = Regex.extract(data = data, expression = '([\d\.\-]+)\s*ghz')
				result = _result(result, unit = 'ghz', count = count)
				if result and result['total']: return result
		except:	pass

		# Only use Kodi's InfoLabel last, since it takes long and sometimes returns -1MHz.
		try:
			data = System.infoLabel('System.CpuFrequency', wait = True)
			if result:
				result = Regex.extract(data = data, expression = '([\d\.\-]+)\s*mhz')
				result = _result(result, unit = 'mhz', count = count)
				if result and result['total']: return result

				result = Regex.extract(data = data, expression = '([\d\.\-]+)\s*ghz')
				result = _result(result, unit = 'ghz', count = count)
				if result and result['total']: return result
		except: pass

		return _result()

	@classmethod
	def detectProcessorUsage(self):
		# On Linux, the output might look like: #0:  24% #1:  24% #2:  25% #3:  24% #4:  24% #5:  23%
		# On Windows, the output might look like: 5%
		usage = System.infoLabel('System.CpuUsage')

		percentTotal = 1.0
		percentFree = 0.0
		percentUsed = 0.0
		cores = 0
		try:
			# NB: On Windows only one core might be detected with one reading, instead of individual cores with individual readings on Linux.
			usage = Regex.extract(data = usage, expression = ':?\s*([\d.]+)%', group = None, all = True)
			cores = len(usage)
			average = sum(float(i) for i in usage) / cores
			percentFree = int(100 - average) / 100.0
			percentUsed = percentTotal - percentFree
		except: pass

		# On some Android devices the CPU usage is not available, System.CpuUsage returns "Not Available".
		# The usage will still stay at 0%, but at least get the number of cores.
		# If there is only one core detected from the Kodi reading (eg Windows), detect the actual number of cores.
		if not cores or cores == 1:
			try: cores = self.detectProcessorCount()['core']
			except: pass

		percentTotal = Math.round(percentTotal, places = 3)
		percentFree = Math.round(percentFree, places = 3)
		percentUsed = Math.round(percentUsed, places = 3)

		labelTotal = self._labelPercent(percentTotal)
		labelFree = self._labelPercent(percentFree)
		labelUsed = self._labelPercent(percentUsed)

		return {
			'total' : {
				'percent' : percentTotal,
				'label' : labelTotal,
			},
			'free' : {
				'percent' : percentFree,
				'label' : labelFree,
			},
			'used' : {
				'percent' : percentUsed,
				'label' : labelUsed,
			},
			'label' : labelFree + ' free of ' + str(cores) + ' core' + ('' if cores == 1 else 's'),
		}

	@classmethod
	def detectProcessor(self):
		model = self.detectProcessorModel()
		type = self.detectProcessorType(model = model)
		name = self.detectProcessorName(type = type)
		count = self.detectProcessorCount()
		clock = self.detectProcessorClock(model = model, count = count)
		usage = self.detectProcessorUsage()

		label = None
		try:
			label = clock['description']
			del clock['description']
		except: pass
		if name and label: label = '%s (%s)' % (name, label)
		elif name: label = name

		return {
			'type' : type,
			'name' : name,
			'model' : model,
			'count' : count,
			'clock' : clock,
			'usage' : usage,
			'label' : label,
		}

	########################################
	# DETECT - MEMORY
	########################################

	@classmethod
	def detectMemorySize(self):
		def _result(result = None):
			# On some Android devices (eg: emulator), System.Memory(total) returns large values like 4503598983544832. Ignore them.
			if result and result > 0 and result < 1073741824000: return result
			return None

		try:
			result = self._extractSize(System.infoLabel('System.Memory(total)'))
			result = _result(result)
			if result: return result
		except: pass

		try:
			result = Platform.psutil().virtual_memory().total
			result = _result(result)
			if result: return result
		except: pass

		try:
			result = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
			result = _result(result)
			if result: return result
		except: pass

		try:
			result = dict((i.split()[0].rstrip(':'),int(i.split()[1])) for i in open('/proc/meminfo').readlines())
			result = result['MemTotal'] * 1024
			result = _result(result)
			if result: return result
		except: pass

		try:
			from ctypes import Structure, c_int32, c_uint64, sizeof, byref, windll
			class MemoryStatusEx(Structure):
				_fields_ = [
					('length', c_int32),
					('memoryLoad', c_int32),
					('totalPhys', c_uint64),
					('availPhys', c_uint64),
					('totalPageFile', c_uint64),
					('availPageFile', c_uint64),
					('totalVirtual', c_uint64),
					('availVirtual', c_uint64),
					('availExtendedVirtual', c_uint64)]
				def __init__(self):
					self.length = sizeof(self)
			result = MemoryStatusEx()
			windll.kernel32.GlobalMemoryStatusEx(byref(result))
			result = memory.totalPhys
			result = _result(result)
			if result: return result
		except: pass

		return _result()

	@classmethod
	def detectMemoryUsage(self):
		bytesTotal = self._extractSize(System.infoLabel('System.Memory(total)'))
		bytesFree = self._extractSize(System.infoLabel('System.Memory(free)'))
		bytesUsed = bytesTotal - bytesFree

		# On some Android devices (eg: emulator), System.Memory(total/free) returns large values like 4503598983544832.
		# Adjust them using other detection methods.
		if bytesTotal > 1073741824000:
			bytesUsed = bytesTotal - bytesFree
			bytesTotal = self.detectMemorySize()
			bytesFree = bytesTotal - bytesUsed

		percentTotal = Math.round(1.0, places = 3)
		percentFree = Math.round(bytesFree / float(bytesTotal), places = 3)
		percentUsed = Math.round(bytesUsed / float(bytesTotal), places = 3)

		labelTotal = self._labelSize(bytesTotal)
		labelFree = self._labelSize(bytesFree)
		labelUsed = self._labelSize(bytesUsed)

		return {
			'total' : {
				'bytes' : bytesTotal,
				'percent' : percentTotal,
				'label' : labelTotal,
			},
			'free' : {
				'bytes' : bytesFree,
				'percent' : percentFree,
				'label' : labelFree,
			},
			'used' : {
				'bytes' : bytesUsed,
				'percent' : percentUsed,
				'label' : labelUsed,
			},
			'label' : labelFree + ' free of ' + labelTotal,
		}

	@classmethod
	def detectMemory(self):
		bytes = self.detectMemorySize()
		return {
			'bytes' : bytes,
			'usage' : self.detectMemoryUsage(),
			'label' : self._labelSize(bytes)
		}

	########################################
	# DETECT - STORAGE
	########################################

	@classmethod
	def detectStorageSpeed(self, iterations = 5):
		# https://github.com/thodnev/MonkeyTest
		# https://stackoverflow.com/questions/40665591/how-to-achieve-maximum-write-speed-with-python

		speedWrite = 0
		speedRead = 0

		try:
			try: # if Python >= 3.3 use new high-res counter.
				# NB: Do not use process_time, since it only includes CPU time and not sleep time (eg while waiting on disk I/O).
				# Although this works on Linux, on Windows the read time with process_time is always 0.
				# https://stackoverflow.com/questions/52222002/what-is-the-difference-between-time-perf-counter-and-time-process-time
				# For some reason the read/write speeds on Windows are different to the ones on Linux, even with the same disk.
				# Seems to be the same issue with all kinds of timers on Windows.
				#from time import process_time as timer
				from time import perf_counter as timer
			except ImportError: # Else select highest available resolution counter.
				if sys.platform[:3] == 'win':
					try: from time import clock as timer
					except: from time import time as timer
				else:
					from time import time as timer
			from random import shuffle
			from lib.modules.convert import ConverterSpeed

			size = 67108864 # 64MB
			limit = 10 # Maximum number of seconds to run one test (read or write).
			path = System.temporary(file = 'disk.txt')
			File.delete(path)

			# Write Speed
			chunkSize = 131072 # 128KB
			chunkCount = int(size / chunkSize)
			total = 0
			flags = os.O_CREAT | os.O_WRONLY
			try: flags |= os.O_SYNC # Not available in Windows.
			except: pass
			for i in range(iterations):
				times = 0
				chunks = 0
				file = os.open(path, flags, 0o777) # Low-level I/O.
				for j in range(chunkCount):
					chunk = os.urandom(chunkSize)
					start = timer()
					os.write(file, chunk)
					os.fsync(file) # Force write to disk.
					end = timer() - start
					times += end
					chunks += chunkSize
					if (total + times) > limit: break
				os.close(file)
				File.delete(path)
				total += times
				speed = int(chunks / times) if times else 0
				if not speedWrite or speed > speedWrite: speedWrite = speed
				if total > limit: break

			# Read Speed
			file = os.open(path, flags, 0o777)
			for j in range(chunkCount):
				os.write(file, os.urandom(chunkSize))
				os.fsync(file)
			os.close(file)
			chunkSize = 1024 # 1KB
			chunkCount = int(size / chunkSize)
			total = 0
			speedRead = None
			flags = os.O_RDONLY
			try: flags |= os.O_SYNC # Not available in Windows.
			except: pass
			for i in range(iterations):
				times = 0
				chunks = 0
				file = os.open(path, flags, 0o777) # Low-level I/O.
				offsets = list(range(0, chunkCount * chunkSize, chunkSize))
				shuffle(offsets) # Generate random read positions.
				for j, offset in enumerate(offsets, 1):
					start = timer()
					os.lseek(file, offset, os.SEEK_SET) # Set position.
					buffer = os.read(file, chunkSize) # Read from position.
					end = timer() - start
					if not buffer: break # EOF reached.
					times += end
					chunks += chunkSize
					if (total + times) > limit: break
				os.close(file)
				total += times
				speed = int(chunks / times) if times else 0
				if not speedRead or speed > speedRead: speedRead = speed
				if total > limit: break
			File.delete(path)
		except: Logger.error()

		speed = int((speedWrite + speedRead) / 2.0)
		return {
			'bytes' : speed,
			'label' : ConverterSpeed(value = speed).string(unit = ConverterSpeed.ByteMega),
			'read' : {
				'bytes' : speedRead,
				'label' : ConverterSpeed(value = speedRead).string(unit = ConverterSpeed.ByteMega),
			},
			'write' : {
				'bytes' : speedWrite,
				'label' : ConverterSpeed(value = speedWrite).string(unit = ConverterSpeed.ByteMega),
			},
		}

	@classmethod
	def detectStorageUsage(self):
		bytesTotal = None
		bytesFree = None

		lookup = __file__

		try:
			if not bytesTotal:
				psutil = Platform.psutil()
				stats = psutil.disk_usage(lookup)
				bytesTotal = stats.total
				bytesFree = stats.free
		except: pass

		try:
			if not bytesTotal:
				stats = os.statvfs(lookup)
				bytesTotal = stats.f_frsize * stats.f_blocks
				bytesFree = stats.f_frsize * stats.f_bavail
		except: pass

		try:
			if not bytesTotal:
				import shutil
				bytesTotal, _, bytesFree = shutil.disk_usage(lookup)
		except: pass

		try:
			if not bytesTotal:
				import platform
				system = platform.system()
				if system:
					system = system.lower()
					if 'windows' in system:
						try:
							if not bytesTotal:
								import ctypes
								total = ctypes.c_ulonglong(0)
								free = ctypes.c_ulonglong(0)
								ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(lookup), None, ctypes.pointer(total), ctypes.pointer(free))
								bytesTotal = total.value
								bytesFree = free.value
						except: pass
						try:
							if not bytesTotal:
								import win32file
								sectorsPerCluster, bytesPerSector, freeClusters, totalClusters = win32file.GetDiskFreeSpace(lookup)
								bytesTotal = sectorsPerCluster * bytesPerSector * totalClusters
								bytesFree = sectorsPerCluster * bytesPerSector * freeClusters
						except: pass
		except: pass

		# Only use the Kodi function as last resort:
		#	1. The space returned by Kodi is slightly off, and even different to the values show in Kodi's System Information menu.
		#	2. Kodi always returns the space for the FIRST partition. On many Linux devices the first partition is a small Flash partition and not the main partition.
		#	   And the following does not work: System.TotalSpace(1) or System.TotalSpace(/dev/sdaX) or System.TotalSpace('/dev/sdaX')
		if not bytesTotal:
			bytesTotal = self._extractSize(System.infoLabel('System.TotalSpace'))
			bytesFree = self._extractSize(System.infoLabel('System.FreeSpace'))

		bytesUsed = bytesTotal - bytesFree

		percentTotal = Math.round(1.0, places = 3)
		percentFree = Math.round(bytesFree / float(bytesTotal), places = 3)
		percentUsed = Math.round(bytesUsed / float(bytesTotal), places = 3)

		labelTotal = self._labelSize(bytesTotal)
		labelFree = self._labelSize(bytesFree)
		labelUsed = self._labelSize(bytesUsed)

		return {
			'label' : labelFree + ' free of ' + labelTotal,
			'total' : {
				'bytes' : bytesTotal,
				'percent' : percentTotal,
				'label' : labelTotal,
			},
			'free' : {
				'bytes' : bytesFree,
				'percent' : percentFree,
				'label' : labelFree,
			},
			'used' : {
				'bytes' : bytesUsed,
				'percent' : percentUsed,
				'label' : labelUsed,
			},
		}

	@classmethod
	def detectStorage(self, full = True):
		speed = self.detectStorageSpeed() if full else None
		usage = self.detectStorageUsage()
		try: label = '%s @ %s' % (usage['total']['label'], speed['label'])
		except: label = usage['total']['label']
		return {
			'bytes' : usage['total']['bytes'],
			'label' : label,
			'speed' : speed,
			'usage' : usage,
		}

	########################################
	# DETECT - NETWORK
	########################################

	@classmethod
	def detectNetwork(self, duration = 3.0, single = True):
		try:
			rates = {}
			duration = float(duration)
			psutil = Platform.psutil()

			if psutil:
				timer = Time(mode = Time.ModeSystem, start = True) # In case threads are interleaved, get the real elapsed time to also include sleep time.
				before = psutil.net_io_counters(pernic = True)
				Time.sleep(duration)
				after = psutil.net_io_counters(pernic = True)
				duration = timer.elapsed(milliseconds = True) / 1000.0

				for id, values in after.items():
					sent = after[id].bytes_sent - before[id].bytes_sent
					received = after[id].bytes_recv - before[id].bytes_recv
					rates[id] = {'download' : received / duration, 'upload' : sent / duration}
			else:
				# Psutil does not work on Windows (or at least under Kodi's Python).
				if Platform.detectWindows():
					command = 'wmic path Win32_PerfRawData_Tcpip_NetworkInterface Get BytesReceivedPersec,BytesSentPersec'
					timer = Time(mode = Time.ModeSystem, start = True) # In case threads are interleaved, get the real elapsed time to also include sleep time.
					before = Subprocess.output(command)
					Time.sleep(duration)
					after = Subprocess.output(command)
					duration = timer.elapsed(milliseconds = True) / 1000.0

					expression = '(\d+)\s*(\d+)'
					before = Regex.extract(data = before, expression = expression, group = None, all = True)[0]
					after = Regex.extract(data = after, expression = expression, group = None, all = True)[0]
					sent = int(after[1]) - int(before[1])
					received = int(after[0]) - int(before[0])
					rates['main'] = {'download' : received / duration, 'upload' : sent / duration}
				else:
					command = '/proc/net/dev'
					timer = Time(mode = Time.ModeSystem, start = True) # In case threads are interleaved, get the real elapsed time to also include sleep time.
					try: before = Converter.unicode(open(command).read())
					except: before = ''
					Time.sleep(duration)
					try: after = Converter.unicode(open(command).read())
					except: after = ''
					duration = timer.elapsed(milliseconds = True) / 1000.0

					def _detectNetworkExtract(data):
						data = data.split('\n')

						header = data[1]
						header = header[header.index('|') + 1:].replace('|', ' ').split()

						indexReceived = header.index('bytes')
						indexSent = header.index('bytes', indexReceived + 1)

						values = {}
						for line in data[2:]:
							try:
								name = line[:line.index(':')].strip()
								value = [int(i) for i in line[line.index(':') + 1:].split()]
								values[name] = {'received' : value[indexReceived], 'sent' : value[indexSent]}
							except: pass
						return values

					before = _detectNetworkExtract(before)
					after = _detectNetworkExtract(after)
					for key in before.keys():
						rates[key] = {'download' : (after[key]['received'] - before[key]['received']) / duration, 'upload' : (after[key]['sent'] - before[key]['sent']) / duration}

			if single:
				values = list(rates.values())
				if len(values) == 1: return values[0]

				# Try to select the network interface if we can find the corresponding address.
				addressIp = System.infoLabel('Network.IPAddress')
				addressMac = System.infoLabel('Network.MacAddress')
				if psutil:
					for id, values in psutil.net_if_addrs().items():
						for value in values:
							if value.address == addressIp or value.address == addressMac:
								if id in rates: return rates[id]

					# Otherwise fall back to the network interface with the highest traffic.
					maximum = 0
					rate = None
					for id, values in rates.items():
						if values['download'] > maximum:
							maximum = values['download']
							rate = values
					return rate
				else:
					import netifaces
					for key, value in rates.items():
						addresses = netifaces.ifaddresses(key)
						addresses = [i[0]['addr'] for i in addresses.values()]
						if addressIp in addresses or addressMac in addresses:
							return value

				return values[0]
			else:
				return rates
		except:
			Logger.error()
			return None

	########################################
	# DETECT
	########################################

	@classmethod
	def detect(self, full = True, callback = None):
		if callback: callback(Hardware.CategoryProcessor)
		processor = self.detectProcessor()
		if callback: callback(Hardware.CategoryMemory)
		memory = self.detectMemory()
		if callback: callback(Hardware.CategoryStorage)
		storage = self.detectStorage(full = full)
		return {
			'processor' : processor,
			'memory' : memory,
			'storage' : storage,
		}

###################################################################
# EXTENSION
###################################################################

class Extension(object):

	# Type
	TypeRequired = 'required'
	TypeRecommended = 'recommended'
	TypeOptional = 'optional'

	# ID
	IdGaiaAddon = 'plugin.video.gaia'
	IdGaiaBinaries = 'script.gaia.binaries'
	IdGaiaExternals = 'script.gaia.externals'
	IdGaiaResources = 'script.gaia.resources'
	IdGaiaMetadata = 'script.gaia.metadata'
	IdGaiaIcons = 'script.gaia.icons'
	IdGaiaSkins = 'script.gaia.skins'
	IdGaiaRepositoryCore = 'repository.gaia.core'
	IdGaiaRepositoryFull = 'repository.gaia.full'
	IdResolveUrl = 'script.module.resolveurl'
	IdUrlResolver = 'script.module.urlresolver'
	IdOpeScrapers = 'script.module.openscrapers'
	IdFenScrapers = 'script.module.fenomscrapers'
	IdOatScrapers = 'script.module.oathscrapers'
	IdCreScrapers = 'script.module.thecrew'
	IdLamScrapers = 'script.module.lambdascrapers'
	IdCivScrapers = 'script.module.civitasscrapers'
	IdGloScrapers = 'script.module.globalscrapers'
	IdUniScrapers = 'script.module.universalscrapers'
	IdNanScrapers = 'script.module.nanscrapers'
	IdElementum = 'plugin.video.elementum'
	IdElementumRepository = 'repository.elementum'
	IdQuasar = 'plugin.video.quasar'
	IdQuasarRepository = 'repository.quasar'
	IdExtendedInfo = 'script.extendedinfo'
	IdDiamondInfo = 'script.diamondinfo'
	IdEmbuaryInfo = 'script.embuary.info'
	IdYouTube = 'plugin.video.youtube'
	IdUpNext = 'service.upnext'
	IdAddonSignals = 'script.module.addon.signals'
	IdTmdbHelper = 'plugin.video.themoviedb.helper'
	IdVpnManager = 'service.vpn.manager'
	IdStudioIcons = 'resource.images.studios.white'

	ConfirmDisabled = 0 # Do not show a confirmation dialog.
	ConfirmBasic = 1 # Show a confirmation dialog with basic info.
	ConfirmRequired = 2 # Show a confirmation dialog with required account info.
	ConfirmOptional = 3 # Show a confirmation dialog with optional account info.
	ConfirmDefault = ConfirmBasic

	@classmethod
	def statistics(self, id = None):
		from lib.modules.cache import Cache
		from lib.modules.network import Networker
		data = Cache.instance().cacheMedium(Networker().requestJson, link = Settings.getString('internal.link.statistics', raw = True))
		if id:
			try: return data[id]
			except: return None
		else:
			return data

	@classmethod
	def settings(self, id, setting = None, category = None, wait = False):
		try:
			Settings.launch(addon = id, id = setting, category = category, wait = wait)
			return True
		except:
			return False

	@classmethod
	def help(self, full = False):
		from lib.modules.interface import Dialog
		items = [
			{'type' : 'title', 'value' : 'Extensions', 'break' : 2} if full else None,
			{'type' : 'text', 'value' : 'Extensions are third-party Kodi addons that can be installed to add additional functionality to Gaia. Most extensions are optional and are therefore not installed by default. These extensions have to be installed manually in order to unlock the features. All extensions are available from the Gaia repository, but can also be installed from any other repository.', 'break' : 2} if full else None,
			{'type' : 'title', 'value' : 'Dependencies', 'break' : 2} if full else None,
			{'type' : 'text', 'value' : 'Kodi has a bug that sometimes cause dependency addons not to be installed automatically. When installing an external addon, like YouTube, you might get an error message indicating that a dependency was not met, even though those dependencies are available in a repository. There might also be recursive sub-dependencies, that is, one addon might depend on a second addon, which in turn depends on a third addon.', 'break' : 2},
			{'type' : 'text', 'value' : 'The only solution is to install all dependencies manually. You can download and install each ZIP file manually. However, a quicker option is to manually install the dependencies through the Kodi addon manager. Our repository contains all necessary dependencies for addons that are incorporated into Gaia.', 'break' : 2},
			{'type' : 'text', 'value' : 'For example, if the YouTube addon installation fails, follow these steps:', 'break' : 1},
			{'type' : 'list', 'value' : [
				{'value' : 'Navigate to the Gaia repository addon and find [I]YouTube[/I]  under the video addon section.'},
				{'value' : 'Open the information dialog of the YouTube addon.'},
				{'value' : 'Click the [I]Install[/I]  button and take note of the failed addon ID in the error notification, such as the [I]requests[/I]  addon.'},
				{'value' : 'Open the [I]Dependencies[/I]  dialog of the YouTube addon and select the previously failed addon. This will open a new information dialog for the dependency addon.'},
				{'value' : 'Click the [I]Install[/I]  button of the dependency addon. You might get an additional error notification saying that another dependency was not met. For instance, the [I]requests[/I]  addon depends on the [I]certifi[/I], [I]chardet[/I], [I]idna[/I], and [I]urllib3[/I]  addons. Repeat the above steps for each of these sub-dependencies.'},
				{'value' : 'Once all sub-dependencies have been installed, try to install the YouTube addon again.'},
			], 'number' : True},
		]
		Dialog.details(title = 33720 if full else 36204, items = items)

	@classmethod
	def launch(self, id):
		try:
			System.execute('RunAddon(%s)' % id)
			return True
		except:
			return False

	@classmethod
	def size(self, id):
		try: return File.sizeDirectory(path = System.path(id = id))
		except: return 0

	@classmethod
	def installed(self, id, enabled = True):
		return System.installed(id = id, enabled = enabled)

	@classmethod
	def enable(self, id, name = None, refresh = False, confirm = ConfirmDefault, notification = True, automatic = True, action = None, wait = True):
		from lib.modules.interface import Format, Dialog, Translation, Loader

		originalId = id
		originalName = name
		originalRefresh = refresh
		originalConfirm = confirm
		originalNotification = notification
		originalAutomatic = automatic
		originalAction = action
		originalWait = wait

		if not name:
			for addon in self.list(lookup = False):
				if addon['id'] == id:
					name = addon['name']
					break
			if not name:
				try: name = System.executeJson(addon = id, method = 'Addons.GetAddonDetails', parameters = {'properties' : ['name']})['result']['addon']['name']
				except: pass

		if confirm:
			if confirm is True: confirm = Extension.ConfirmBasic

			if name: label = '%s (%s)' % (Format.fontBold(name), Format.fontItalic(id))
			else: label = Format.fontBold(id)
			message = Translation.string(33745)

			if confirm == Extension.ConfirmRequired: message = message % ((Translation.string(36235) % label) + ' ', '')
			elif confirm == Extension.ConfirmOptional: message = message % ((Translation.string(36236) % label) + ' ', '')
			else: message = message % ('', label + ' ')

			while True:
				choice = Dialog.options(title = 35865, message = message, labelConfirm = 33743, labelDeny = 33736, labelCustom = 33239)
				if choice == Dialog.ChoiceCustom: self.help(full = True)
				elif choice == Dialog.ChoiceNo: break
				else: return False

		Loader.show()
		installed = self.installed(id = id, enabled = False)

		if not installed:
			try:
				System.execute('InstallAddon(%s)' % id)
				if automatic: System.executeClick(control = System.ControlConfirmYes) # Click the "Yes" button automatically.
			except: pass

			# Wait for the download/install dialog to finish.
			Time.sleep(0.1)
			while not System.aborted() and Dialog.dialogProgressVisible():
				Time.sleep(0.02)

		if action:
			Loader.show()
			if not Tools.isArray(action): action = [action]
			for i in action: i()

		# Wait for the installation to finish.
		# InstallAddon() might show its own dialogs. Wait for them to close.
		if not installed:
			if wait or wait is None:
				if wait is None:
					# Only check native Kodi dialogs, and not all dialogs/windows.
					# Eg: When Trakt is installed, it will show the authentication dialog, which might need to be ignored (eg: called from account.py).
					from lib.modules.window import Window
					checker = lambda: Window.currentKodi(loader = False)
				else:
					checker = lambda: Dialog.dialogVisible(loader = False)

				while not System.aborted():
					Time.sleep(0.1)
					if not checker():
						for i in range(5):
							Time.sleep(0.1)
							if checker(): break
						if not checker(): break

		try: System.executeJson(addon = id, method = 'Addons.SetAddonEnabled', parameters = {'enabled' : True})
		except: pass

		if refresh:
			Time.sleep(0.1)
			System.execute('Container.Refresh')
			Time.sleep(0.1)
			System.execute('Container.Refresh')

		# If an addon is not compatible with Kodi 19, a loader is shown that cannot be manually canceled (eg: UrlResolver).
		# Sleep a bit, since this loader takes a while to popup.
		Time.sleep(0.5)
		Loader.hide()
		installed = self.installed(id = id, enabled = True)

		# On Linux, Kodi shows error notifications when an addon cannot be installed, due to compatibility issues (eg: Python  2) or dependency issues.
		# On Windows, no error notifications are show.
		# Therefore always show Gaia notifications manually.
		# Only do this if waiting for the installation to finish. Otherwise the error notification might be shown because "installed == False", since the installation is still busy.
		if (wait or wait is None) and notification:
			if installed:
				Dialog.notification(title = 36231, message = Translation.string(36221) % Format.fontBold(name), icon = Dialog.IconSuccess)
			elif not '.gaia' in id:
				Dialog.notification(title = 36220, message = Translation.string(36222) % Format.fontBold(name), icon = Dialog.IconError)
				if not id == Extension.IdGaiaRepositoryFull and not self.installed(id = Extension.IdGaiaRepositoryFull, enabled = True):
					if Dialog.option(title = 36220, message = 33272):
						if self.enable(id = Extension.IdGaiaRepositoryFull, confirm = Extension.ConfirmDisabled, notification = True, automatic = True, wait = True):
							Loader.show()
							System.execute('UpdateAddonRepos')
							Loader.show()

							# Wait for the newley installed repo to update.
							# Otherwise installing any of the addons from the repo below, will fail, since Kodi has not pulled in the addon data from the new repo.
							# 5 secs is too little in some cases. Even 10 secs might sometimes not be enough if the user has slow internet or many other repos installed.
							for i in range(20):
								Loader.show()
								Time.sleep(0.5)

							return self.enable(id = originalId, name = originalName, refresh = originalRefresh, confirm = originalConfirm, notification = originalNotification, automatic = originalAutomatic, action = originalAction, wait = originalWait)

		return installed

	@classmethod
	def disable(self, id, refresh = False):
		from lib.modules.interface import Loader
		Loader.show()

		try: System.executeJson(addon = id, method = 'Addons.SetAddonEnabled', parameters = {'enabled' : False})
		except: pass

		if refresh:
			# Sometimes when disabling an addon (eg: Orion), the container does not refresh and remove the menu entry.
			# Trying twice seems to work.
			Time.sleep(0.1)
			System.execute('Container.Refresh')
			Time.sleep(0.1)
			System.execute('Container.Refresh')

		# If an addon is not compatible with Kodi 19, a loader is shown that cannot be manually canceled (eg: UrlResolver).
		# Sleep a bit, since this loader takes a while to popup.
		Time.sleep(0.5)
		Loader.hide()

	@classmethod
	def list(self, lookup = True):
		from lib.modules import orionoid
		from lib.modules import interface

		result = [
			{
				'id' : Extension.IdGaiaRepositoryCore,
				'name' : 'Gaia Repository (Core)',
				'type' : Extension.TypeOptional,
				'description' : 33917,
				'icon' : 'extensionsgaia.png',
			},
			{
				'id' : Extension.IdGaiaRepositoryFull,
				'name' : 'Gaia Repository (Full)',
				'type' : Extension.TypeOptional,
				'description' : 33917,
				'icon' : 'extensionsgaia.png',
			},
			{
				'id' : Extension.IdGaiaExternals,
				'name' : 'Gaia Externals',
				'type' : Extension.TypeRequired,
				'description' : 33727,
				'icon' : 'extensionsgaia.png',
			},
			{
				'id' : Extension.IdGaiaResources,
				'name' : 'Gaia Resources',
				'type' : Extension.TypeRequired,
				'description' : 33731,
				'icon' : 'extensionsgaia.png',
			},
			{
				'id' : Extension.IdGaiaMetadata,
				'name' : 'Gaia Metadata',
				'type' : Extension.TypeOptional,
				'description' : 33732,
				'icon' : 'extensionsgaia.png',
			},
			{
				'id' : Extension.IdGaiaBinaries,
				'name' : 'Gaia Binaries',
				'type' : Extension.TypeOptional,
				'description' : 33728,
				'icon' : 'extensionsgaia.png',
			},
			{
				'id' : Extension.IdGaiaIcons,
				'name' : 'Gaia Icons',
				'type' : Extension.TypeOptional,
				'description' : 33729,
				'icon' : 'extensionsgaia.png',
			},
			{
				'id' : Extension.IdGaiaSkins,
				'name' : 'Gaia Skins',
				'type' : Extension.TypeOptional,
				'description' : 33730,
				'icon' : 'extensionsgaia.png',
			},
			{
				'id' : Extension.IdResolveUrl,
				'name' : 'ResolveUrl',
				'type' : Extension.TypeRecommended,
				'description' : 33732,
				'icon' : 'extensionsresolveurl.png',
			},
			{
				'id' : Extension.IdUrlResolver,
				'name' : 'UrlResolver',
				'type' : Extension.TypeOptional,
				'description' : 33732,
				'icon' : 'extensionsurlresolver.png',
			},
			{
				'id' : orionoid.Orionoid.Id,
				'name' : orionoid.Orionoid.Name,
				'type' : Extension.TypeRecommended,
				'description' : 35401,
				'icon' : 'extensionsorion.png',
			},
			{
				'id' : Extension.IdCreScrapers,
				'name' : 'Crew Scrapers',
				'type' : Extension.TypeOptional,
				'description' : 33963,
				'icon' : 'extensionscrescrapers.png',
			},
			{
				'id' : Extension.IdOpeScrapers,
				'name' : 'Open Scrapers',
				'type' : Extension.TypeOptional,
				'description' : 33963,
				'icon' : 'extensionsopescrapers.png',
			},
			{
				'id' : Extension.IdFenScrapers,
				'name' : 'Fenom Scrapers',
				'type' : Extension.TypeOptional,
				'description' : 33963,
				'icon' : 'extensionsfenscrapers.png',
			},
			{
				'id' : Extension.IdOatScrapers,
				'name' : 'Oath Scrapers',
				'type' : Extension.TypeOptional,
				'description' : 33963,
				'icon' : 'extensionsfenscrapers.png',
			},
			{
				'id' : Extension.IdLamScrapers,
				'name' : 'Lambda Scrapers',
				'type' : Extension.TypeOptional,
				'description' : 33963,
				'icon' : 'extensionslamscrapers.png',
			},
			{
				'id' : Extension.IdCivScrapers,
				'name' : 'Civitas Scrapers',
				'type' : Extension.TypeOptional,
				'description' : 33963,
				'icon' : 'extensionscivscrapers.png',
			},
			{
				'id' : Extension.IdGloScrapers,
				'name' : 'Global Scrapers',
				'type' : Extension.TypeOptional,
				'description' : 33963,
				'icon' : 'extensionsgloscrapers.png',
			},
			{
				'id' : Extension.IdUniScrapers,
				'name' : 'Universal Scrapers',
				'type' : Extension.TypeOptional,
				'description' : 33963,
				'icon' : 'extensionsuniscrapers.png',
			},
			{
				'id' : Extension.IdNanScrapers,
				'name' : 'NaN Scrapers',
				'type' : Extension.TypeOptional,
				'description' : 33963,
				'icon' : 'extensionsnanscrapers.png',
			},
			{
				'id' : Extension.IdElementum,
				'dependencies' : [Extension.IdElementumRepository],
				'name' : 'Elementum',
				'type' : Extension.TypeOptional,
				'description' : 33735,
				'icon' : 'extensionselementum.png',
			},
			{
				'id' : Extension.IdQuasar,
				'dependencies' : [Extension.IdQuasarRepository],
				'name' : 'Quasar',
				'type' : Extension.TypeOptional,
				'description' : 33735,
				'icon' : 'extensionsquasar.png',
			},
			{
				'id' : Extension.IdExtendedInfo,
				'name' : 'ExtendedInfo',
				'type' : Extension.TypeOptional,
				'description' : 35570,
				'icon' : 'extensionsextendedinfo.png',
			},
			{
				'id' : Extension.IdDiamondInfo,
				'name' : 'DiamondInfo',
				'type' : Extension.TypeOptional,
				'description' : 35570,
				'icon' : 'extensionsdiamondinfo.png',
			},
			{
				'id' : Extension.IdEmbuaryInfo,
				'name' : 'EmbuaryInfo',
				'type' : Extension.TypeRecommended,
				'description' : 35570,
				'icon' : 'extensionsembuaryinfo.png',
			},
			{
				'id' : Extension.IdYouTube,
				'name' : 'YouTube',
				'type' : Extension.TypeRecommended,
				'description' : 35297,
				'icon' : 'extensionsyoutube.png',
			},
			{
				'id' : Extension.IdUpNext,
				'name' : 'UpNext',
				'type' : Extension.TypeOptional,
				'description' : 35409,
				'icon' : 'extensionsupnext.png',
			},
			{
				'id' : Extension.IdAddonSignals,
				'name' : 'AddonSignals',
				'type' : Extension.TypeOptional,
				'description' : 35410,
				'icon' : 'extensionsaddonsignals.png',
			},
			{
				'id' : Extension.IdTmdbHelper,
				'name' : 'TMDbHelper',
				'type' : Extension.TypeOptional,
				'description' : 36383,
				'icon' : 'extensionstmdbhelper.png',
			},
			{
				'id' : Extension.IdVpnManager,
				'name' : 'VpnManager',
				'type' : Extension.TypeOptional,
				'description' : 34211,
				'icon' : 'extensionsvpnmanager.png',
			},
			{
				'id' : Extension.IdStudioIcons,
				'name' : 'StudioIcons',
				'type' : Extension.TypeRecommended,
				'description' : 34243,
				'icon' : 'extensionsstudioicons.png',
			},
		]

		if lookup:
			for i in range(len(result)):
				result[i]['installed'] = self.installed(result[i]['id'])
				if 'dependencies' in result[i]:
					for dependency in result[i]['dependencies']:
						if not self.installed(dependency):
							result[i]['installed'] = False
							break
				result[i]['description'] = interface.Translation.string(result[i]['description'])

		return result

	@classmethod
	def dialog(self, id):
		extensions = self.list()
		for extension in extensions:
			if extension['id'] == id:
				from lib.modules import interface

				type = ''
				if extension['type'] == Extension.TypeRequired:
					type = 33723
				elif extension['type'] == Extension.TypeRecommended:
					type = 33724
				elif extension['type'] == Extension.TypeOptional:
					type = 33725
				if not type == '':
					type = ' (%s)' % interface.Translation.string(type)

				message = ''
				message += interface.Format.fontBold(extension['name'] + type)
				message += interface.Format.newline() + extension['description']

				#action = 33737 if extension['installed'] else 33736
				#choice = interface.Dialog.option(title = 33391, message = message, labelConfirm = action, labelDeny = 33743)
				#if choice:

				interface.Dialog.confirm(title = 33391, message = message)
				if True:
					if extension['installed']:
						if extension['type'] == Extension.TypeRequired:
							interface.Dialog.confirm(title = 33391, message = 33738)
						else:
							label = '%s (%s) ' % (interface.Format.fontBold(extension['name']), interface.Format.fontItalic(extension['id']))
							message = interface.Translation.string(36237) % label
							if interface.Dialog.option(title = 33391, message = message, labelConfirm = 33737, labelDeny = 33743):
								self.disable(extension['id'], refresh = True)
					else:
						if 'dependencies' in extension:
							for dependency in extension['dependencies']:
								self.enable(dependency, refresh = False)
						self.enable(extension['id'], refresh = True, confirm = Extension.ConfirmBasic)

				return True
		return False

	# Get Gaia addon versions from the Gaia repo.
	@classmethod
	def version(self, id = IdGaiaAddon):
		path = System.path(System.GaiaRepositoryCore)
		if not path: path = System.path(System.GaiaRepositoryFull)
		if not path: path = System.path(System.GaiaRepositoryTest)
		if not path: return None # No repo installed.
		path = File.joinPath(path, 'addon.xml')
		data = File.readNow(path)
		link = None
		for match in re.findall('<info.*?>(.*?)<\/info>', data, flags = re.IGNORECASE):
			if not 'common' in match:
				link = match
				break
		if link:
			from lib.modules import network
			data = network.Networker().requestText(link)
			if data:
				match = re.search('id\s*=\s*[\'"]' + id + '[\'"].*?version\s*=\s*[\'"](.*?)[\'"]', data, flags = re.IGNORECASE)
				if match: return match.group(1)
		return None

	@classmethod
	def versionCheck(self, id = IdGaiaAddon, wait = True):
		thread = Pool.thread(target = self._versionCheck, args = (id,))
		thread.start()
		if wait: thread.join()

	@classmethod
	def _versionCheck(self, id = IdGaiaAddon):
		try:
			versionCurrent = System.versionNumber(version = System.version(id = id))
			versionRepoFull = self.version(id = id)
			versionRepo = System.versionNumber(version = versionRepoFull)
			if versionRepo > versionCurrent:
				from lib.modules import interface
				message = interface.Translation.string(35705) % (System.name(), versionRepoFull)
				interface.Dialog.notification(title = 35704, message = message, icon = interface.Dialog.IconInformation)
		except:
			Logger.error()

###################################################################
# ELEMENTUM
###################################################################

class Elementum(object):

	Id = Extension.IdElementum
	Name = 'Elementum'

	@classmethod
	def settings(self, settings = False):
		Extension.settings(id = Elementum.Id, wait = settings)
		if settings: self.settingsLocal('settings')

	@classmethod
	def settingsLocal(self, type = None):
		if type is None: type = 'connection' if self.installed() else 'installation'
		Settings.launch('stream.elementum.' + type)

	@classmethod
	def launch(self):
		Extension.launch(id = Elementum.Id)

	@classmethod
	def install(self, refresh = False, confirm = Extension.ConfirmDefault):
		Extension.enable(id = Elementum.Id, refresh = refresh, confirm = confirm)

	@classmethod
	def installed(self):
		return Extension.installed(Elementum.Id)

	@classmethod
	def interface(self):
		from lib.modules.network import Networker
		Networker.linkShow(link = self.linkWeb())

	@classmethod
	def link(self, type = None, parameters = None):
		host = Settings.getString('stream.elementum.host')
		port = Settings.getString('stream.elementum.port')
		if type is None: type = ''
		if parameters is None or parameters == [] or parameters == {}: parameters = ''
		else: parameters = '?' + ('&'.join(['%s=%s' % (key, value) for key, value in parameters.items()]))
		return 'http://%s:%s/%s%s' % (host, port, type, parameters)

	@classmethod
	def linkWeb(self, parameters = None):
		return self.link(type = 'web', parameters = parameters)

	@classmethod
	def linkPlay(self, parameters = None):
		return self.link(type = 'playuri', parameters = parameters)

	@classmethod
	def linkAdd(self, parameters = None):
		return self.link(type = 'torrents/add', parameters = parameters)

	@classmethod
	def linkList(self, parameters = None):
		return self.link(type = 'torrents/list', parameters = parameters)

	@classmethod
	def connect(self, install = False, background = False, settings = False, wait = True):
		thread = Pool.thread(target = self._connect, args = (install, background, settings))
		thread.start()
		if wait: thread.join()

	@classmethod
	def _connect(self, install = False, background = False, settings = False):
		from lib.modules.interface import Dialog, Translation, Loader

		if install and not self.installed(): self.install(confirm = not background)

		if self.installed():
			if not background: Loader.show()
			from lib.modules.network import Networker
			result = Networker().requestJson(link = self.link())
			if not background: Loader.hide()

			if result:
				Settings.set('stream.elementum.connection', Translation.string(35857))
				if settings: self.settingsLocal()
				return True

		self.disconnect(settings = settings)
		return False

	@classmethod
	def disconnect(self, settings = False):
		from lib.modules.interface import Translation
		Settings.set('stream.elementum.connection', Translation.string(35858))
		if settings: self.settingsLocal()

###################################################################
# QUASAR
###################################################################

class Quasar(object):

	Id = Extension.IdQuasar
	Name = 'Quasar'

	@classmethod
	def settings(self, settings = False):
		Extension.settings(id = Quasar.Id, wait = settings)
		if settings: self.settingsLocal('settings')

	@classmethod
	def settingsLocal(self, type = None):
		if type is None: type = 'connection' if self.installed() else 'installation'
		Settings.launch('stream.quasar.' + type)

	@classmethod
	def launch(self):
		Extension.launch(id = Quasar.Id)

	@classmethod
	def install(self, refresh = False, confirm = Extension.ConfirmDefault):
		Extension.enable(id = Quasar.Id, refresh = refresh, confirm = confirm)

	@classmethod
	def installed(self):
		return Extension.installed(Quasar.Id)

	@classmethod
	def interface(self):
		from lib.modules.network import Networker
		Networker.linkShow(link = self.linkWeb())

	@classmethod
	def link(self, type = None, parameters = None):
		host = Settings.getString('stream.quasar.host')
		port = Settings.getString('stream.quasar.port')
		if type is None: type = ''
		if parameters is None or parameters == [] or parameters == {}: parameters = ''
		else: parameters = '?' + ('&'.join(['%s=%s' % (key, value) for key, value in parameters.items()]))
		return 'http://%s:%s/%s%s' % (host, port, type, parameters)

	@classmethod
	def linkWeb(self, parameters = None):
		return self.link(type = 'web', parameters = parameters)

	@classmethod
	def linkPlay(self, parameters = None):
		return self.link(type = 'playuri', parameters = parameters)

	@classmethod
	def linkAdd(self, parameters = None):
		return self.link(type = 'torrents/add', parameters = parameters)

	@classmethod
	def linkList(self, parameters = None):
		return self.link(type = 'torrents/list', parameters = parameters)

	@classmethod
	def connect(self, confirm = False, wait = True, settings = False):
		thread = Pool.thread(target = self._connect, args = (confirm, settings))
		thread.start()
		if wait: thread.join()

	@classmethod
	def connect(self, install = False, background = False, settings = False, wait = True):
		thread = Pool.thread(target = self._connect, args = (install, background, settings))
		thread.start()
		if wait: thread.join()

	@classmethod
	def _connect(self, install = False, background = False, settings = False):
		from lib.modules.interface import Dialog, Translation, Loader

		if install and not self.installed(): self.install(confirm = not background)

		if self.installed():
			if not background: Loader.show()
			from lib.modules.network import Networker
			result = Networker().requestJson(link = self.link())
			if not background: Loader.hide()

			if result:
				Settings.set('stream.quasar.connection', Translation.string(35857))
				if settings: self.settingsLocal()
				return True

		self.disconnect(settings = settings)
		return False

	@classmethod
	def disconnect(self, settings = False):
		from lib.modules.interface import Translation
		Settings.set('stream.quasar.connection', Translation.string(35858))
		if settings: self.settingsLocal()

###################################################################
# RESOLVER
###################################################################

class Resolver(object):

	@classmethod
	def settings(self, universal = False, settings = False, wait = None):
		try:
			Extension.settings(id = self.Addon, category = 1 if universal else None, wait = settings if wait is None else wait)
			if settings: self.settingsLocal(type = 'settings')
		except:
			resolver = self.select()
			if resolver:
				resolver.settings(universal = universal, settings = False, wait = True)
				self.settingsLocal(id = 'premium.external.settings')

	@classmethod
	def settingsLocal(self, type = None, id = None):
		if not id:
			if type is None: type = 'connection' if self.installed() else 'installation'
			id = 'stream.%s.%s' % (self.Id, type)
		Settings.launch(id)

	@classmethod
	def install(self, help = False, settings = False):
		from lib.modules.interface import Dialog
		if help: self.help()
		resolver = self.select(installed = False)
		if resolver: resolver.enable(refresh = True, confirm = False)
		self.authenticationCheck()
		if settings: Settings.launch('premium.external.install')

	@classmethod
	def installed(self):
		return Extension.installed(id = self.Addon)

	@classmethod
	def enable(self, refresh = False, confirm = True, settings = False):
		result = Extension.enable(id = self.Addon, refresh = refresh, confirm = confirm)
		self.authenticationCheck()
		if settings: self.settingsLocal()
		return result

	@classmethod
	def disable(self, refresh = False, settings = False):
		Extension.disable(id = self.Addon, refresh = refresh)
		self.authenticationCheck()
		if settings: self.settingsLocal()

	@classmethod
	def resolvers(self, installed = True):
		resolvers = [ResolveUrl, UrlResolver]
		if installed: resolvers = [i for i in resolvers if i.installed()]
		return resolvers

	@classmethod
	def resolver(self, id, installed = True):
		resolvers = self.resolvers(installed = installed)
		for resolver in resolvers:
			if id == resolver.Id: return resolver
		return None

	@classmethod
	def select(self, type = None, installed = True):
		resolvers = self.resolvers(installed = installed)
		count = len(resolvers)

		if count == 0: return False
		if count > 1:
			from lib.modules.interface import Dialog, Directory, Translation
			directory = Directory()
			items = [directory.item(label = i.Name, label2 = Translation.string(33216 if i.authenticated(type = type) else 33642) if type else i.Name + ' ' + Translation.string(35614), icon = i.Id) for i in resolvers]
			choice = Dialog.select(title = 33101, items = items, details = True)
		else:
			choice = 0

		if choice >= 0: return resolvers[choice]
		return None

	@classmethod
	def help(self):
		from lib.modules.account import Premium
		Premium.help()

	@classmethod
	def verification(self, type):
		# This is not perfect.
		# Some services, like SimplyDebrid and RapidPremium, do not require aunthitcation for the function calls below.
		try:
			from lib.debrid.external import External
			resolver = self.select(type = type)
			instance = External.resolverInstance(id = resolver.Id, service = type)
			if instance: # If no account was authenticated, the addon might not return the instance (eg: AllDebrid).
			# Unwrap the decorator from the functions, otherwise old cached values might be returned.
				try: return bool(instance.get_all_hosters.__wrapped__(instance()))
				except:
					try: return bool(instance.get_hosters.__wrapped__(instance()))
					except:
						try: return bool(instance.get_hosts.__wrapped__(instance()))
						except:
							try: return bool(instance.get_regexes.__wrapped__(instance()))
							except: pass
		except: Logger.error()
		return False

	@classmethod
	def authentication(self, type = None, direct = True, help = False, settings = False):
		from lib.modules.interface import Translation, Dialog, Loader

		if help: self.help()

		id = self._authenticationId(type = type)
		resolver = self.select(type = type)
		if not resolver:
			if resolver is False:
				self.install()
				if self.resolvers():
					resolver = self.select(type = type)
				else:
					if settings: Settings.launch(id = id)
					return False
			else:
				if settings: Settings.launch(id = id)
				return False

		if resolver:
			addon = System.addon(resolver.Addon)
			data = resolver._authenticationData()

			if direct:
				try: action = data[type]['authentication']['action']
				except: action = None

				authenticate = True
				if resolver.authenticated(type = type):
					choice = Dialog.options(title = 33101, message = 32511, labelConfirm = 32512, labelDeny = 33743, labelCustom = 32513)
					if choice == Dialog.ChoiceCustom:
						authenticate = False
					elif choice == Dialog.ChoiceNo:
						self.authenticationCheck(type = type)
						if settings: Settings.launch(id = id)
						return False

				if action:
					# Resolvers close all dialogs when authenticating or resetting.
					# This makes the wizard window close.
					# Disable the close and afterwards revert back to the original code.
					path = File.joinPath(File.translate('special://home'), 'addons', resolver.Addon, 'lib', resolver.Id, 'lib', 'kodi.py')
					fileOriginal = None
					if File.exists(path):
						fileOriginal = file = File.readNow(path)
						file = Regex.replace(data = file, expression = 'xbmc\.executebuiltin\([\'"]Dialog\.Close\(all\)[\'"]\)', replacement = 'pass', all = True)
						File.writeNow(path, file)

					if authenticate:
						Loader.show()
						for key in data[type]['authentication']['bool']:
							addon.setSetting(key, 'true')

						System.executePlugin(id = resolver.Addon, parameters = {'mode' : 'auth_' + action})
						popup = False
						for i in range(20):
							if Dialog.dialogVisible(id = Dialog.IdDialogProgress):
								popup = True
								break
							Time.sleep(0.5)
						Loader.hide()
						if popup:
							while Dialog.dialogVisible(id = Dialog.IdDialogProgress):
								Time.sleep(0.5)
							Loader.show()
							Time.sleep(5) # That the external settings are populated.
							Loader.hide()
					else:
						Loader.show()
						System.executePlugin(id = resolver.Addon, parameters = {'mode' : 'reset_' + action})
						for key in data[type]['authentication']['bool']:
							addon.setSetting(key, 'false')
						Time.sleep(2) # That the external settings are populated.
						Loader.hide()

					# Revert back to the original.
					if fileOriginal: File.writeNow(path, fileOriginal)
				else:
					settingUsername = None
					settingPassword = None
					for i in data[type]['authentication']['string']:
						if 'username' in i: settingUsername = i
						elif 'password' in i: settingPassword = i

					if authenticate:
						for key in data[type]['authentication']['bool']:
							addon.setSetting(key, 'true')
						username = Dialog.input(title = 33267, default = addon.getSetting(settingUsername))
						if username:
							password = Dialog.input(title = 32307, default = addon.getSetting(settingPassword))
							if password:
								addon.setSetting(settingUsername, username)
								addon.setSetting(settingPassword, password)
					else:
						for key in data[type]['authentication']['bool']:
							addon.setSetting(key, 'false')
						addon.setSetting(settingUsername, '')
						addon.setSetting(settingPassword, '')
			else:
				Settings.launch(addon = resolver.Addon, category = 1, idOld = data[type]['offset'], wait = True)

			self.authenticationCheck(type = type)

		if settings: Settings.launch(id = id)

	@classmethod
	def authenticationCheck(self, type = None):
		from lib.modules.interface import Translation

		if type is None:
			data = self._authenticationData()
			types = data.keys()
		else:
			types = [type]

		for type in types:
			id = self._authenticationId(type = type)
			if self.authenticated(type = type): Settings.set(id, Translation.string(33216))
			else: Settings.default(id)

	@classmethod
	def authenticated(self, type, installed = True):
		try:
			if installed and not self.installed(): return False
			addon = System.addon(self.Addon)
			data = self._authenticationData()
			return all([addon.getSettingBool(i) for i in data[type]['authentication']['bool']]) and all([addon.getSettingString(i) for i in data[type]['authentication']['string']])
		except:
			resolvers = self.resolvers()
			return any([(not installed or i.installed()) and i.authenticated(type = type) for i in resolvers])

	@classmethod
	def _authenticationId(self, type):
		return 'premium.external.%s' % type

	@classmethod
	def authenticationData(self, type):
		try:
			addon = System.addon(self.Addon)
			data = self._authenticationData()
			result = {}
			for i in data[type]['authentication']['string']:
				try: key = i.split('_')[1]
				except: key = i
				result[key] = addon.getSettingString(i)

			# Check first before settings the values in the dictionary, since we scan all values.
			valid = all(result.values())
			enabled = all([addon.getSettingBool(i) for i in data[type]['authentication']['bool']])

			result['resolver'] = self.Id
			result['enabled'] = enabled
			result['valid'] = valid

			return result
		except:
			result = None
			resolvers = self.resolvers()
			for i in resolvers:
				result = i.authenticationData(type = type)
				if result and all(result.values()): return result
			return result

	@classmethod
	def _authenticationData(self):
		data = {
			'premiumize' : {
				'authentication' : {
					'bool' : ['PremiumizeMeResolver_enabled'],
					'string' : ['PremiumizeMeResolver_token'],
					'action' : 'pm',
				},
				'offset' : 49,
			},
			'realdebrid' : {
				'authentication' : {
					'bool' : ['RealDebridResolver_enabled'],
					'string' : ['RealDebridResolver_token'],
					'action' : 'rd',
				},
				'offset' : 60,
			},
			'alldebrid' : {
				'authentication' : {
					'bool' : ['AllDebridResolver_enabled'],
					'string' : ['AllDebridResolver_token'],
					'action' : 'ad',
				},
				'offset' : 6,
			},
			'debridlink' : {
				'authentication' : {
					'bool' : ['DebridLinkResolver_enabled'],
					'string' : ['DebridLinkResolver_token'],
					'action' : 'dl',
				},
				'offset' : 16,
			},
			'linksnappy' : {
				'authentication' : {
					'bool' : ['LinksnappyResolver_enabled'],
					'string' : ['LinksnappyResolver_username', 'LinksnappyResolver_password'],
					'action' : 'ls',
				},
				'offset' : 27,
			},
			'megadebrid' : {
				'authentication' : {
					'bool' : ['MegaDebridResolver_enabled', 'MegaDebridResolver_login'],
					'string' : ['MegaDebridResolver_username', 'MegaDebridResolver_password'],
				},
				'offset' : 38,
			},
			'rapidpremium' : {
				'authentication' : {
					'bool' : ['RPnetResolver_enabled', 'RPnetResolver_login'],
					'string' : ['RPnetResolver_username', 'RPnetResolver_password'],
				},
				'offset' : 70,
			},
			'simplydebrid' : {
				'authentication' : {
					'bool' : ['SimplyDebridResolver_enabled', 'SimplyDebridResolver_login'],
					'string' : ['SimplyDebridResolver_username', 'SimplyDebridResolver_password'],
				},
				'offset' : 77,
			},
			'smoozed' : {
				'authentication' : {
					'bool' : ['SmoozedResolver_enabled', 'SmoozedResolver_login'],
					'string' : ['SmoozedResolver_username', 'SmoozedResolver_password'],
				},
				'offset' : 83,
			},
		}
		try: data = Tools.update(data, self.Authentication)
		except: pass
		return data

###################################################################
# RESOLVEURL
###################################################################

class ResolveUrl(Resolver):

	Id = 'resolveurl'
	Name = 'ResolveUrl'
	Addon = Extension.IdResolveUrl

	Authentication = {
	}

###################################################################
# URLRESOLVER
###################################################################

class UrlResolver(Resolver):

	Id = 'urlresolver'
	Name = 'UrlResolver'
	Addon = Extension.IdUrlResolver

	Authentication = {
		'premiumize' : {
			'offset' : 50,
		},
		'realdebrid' : {
			'offset' : 61,
		},
		'linksnappy' : {
			'offset' : 28,
		},
		'megadebrid' : {
			'offset' : 39,
		},
		'rapidpremium' : {
			'offset' : 71,
		},
		'simplydebrid' : {
			'offset' : 78,
		},
		'smoozed' : {
			'offset' : 84,
		},
	}

###################################################################
# OPESCRAPERS
###################################################################

class OpeScrapers(object):

	Name = 'OpenScrapers'

	IdAddon = Extension.IdOpeScrapers
	IdLibrary = 'openscrapers'
	IdGaia = 'opescrapersx'

	@classmethod
	def settings(self):
		Extension.settings(id = OpeScrapers.IdAddon)

	@classmethod
	def providers(self, settings = True):
		from lib.providers.core.manager import Manager
		from lib.providers.core.base import ProviderBase
		Manager.settings(addon = OpeScrapers.IdGaia, type = ProviderBase.TypeExternal, mode = ProviderBase.ModeUniversal, access = ProviderBase.AccessOpen, settings = settings)

	@classmethod
	def installed(self):
		return Extension.installed(id = OpeScrapers.IdAddon)

	@classmethod
	def enable(self, refresh = False, settings = False):
		result = Extension.enable(id = OpeScrapers.IdAddon, refresh = refresh)
		if settings: Settings.launch(Settings.CategoryProvider)
		return result

	@classmethod
	def disable(self, refresh = False, settings = False):
		result = Extension.disable(id = OpeScrapers.IdAddon, refresh = refresh)
		if settings: Settings.launch(Settings.CategoryProvider)
		return result

###################################################################
# FENSCRAPERS
###################################################################

class FenScrapers(object):

	Name = 'FenomScrapers'

	IdAddon = Extension.IdFenScrapers
	IdParent = 'plugin.video.fen'
	IdLibrary = 'fenomscrapers'
	IdGaia = 'fenscrapersx'

	@classmethod
	def settings(self):
		Extension.settings(id = FenScrapers.IdAddon)

	@classmethod
	def providers(self, settings = True):
		from lib.providers.core.manager import Manager
		from lib.providers.core.base import ProviderBase
		Manager.settings(addon = FenScrapers.IdGaia, type = ProviderBase.TypeExternal, mode = ProviderBase.ModeUniversal, access = ProviderBase.AccessOpen, settings = settings)

	@classmethod
	def installed(self):
		return Extension.installed(id = FenScrapers.IdAddon)

	@classmethod
	def enable(self, refresh = False, settings = False):
		result = Extension.enable(id = FenScrapers.IdAddon, refresh = refresh)
		if settings: Settings.launch(Settings.CategoryProvider)
		return result

	@classmethod
	def disable(self, refresh = False, settings = False):
		result = Extension.disable(id = FenScrapers.IdAddon, refresh = refresh)
		if settings: Settings.launch(Settings.CategoryProvider)
		return result

###################################################################
# OATSCRAPERS
###################################################################

class OatScrapers(object):

	Name = 'OathScrapers'

	IdAddon = Extension.IdOatScrapers
	IdParent = 'plugin.video.theoath'
	IdLibrary = 'oathscrapers'
	IdGaia = 'oatscrapersx'

	@classmethod
	def settings(self):
		Extension.settings(id = OatScrapers.IdAddon)

	@classmethod
	def providers(self, settings = True):
		from lib.providers.core.manager import Manager
		from lib.providers.core.base import ProviderBase
		Manager.settings(addon = OatScrapers.IdGaia, type = ProviderBase.TypeExternal, mode = ProviderBase.ModeUniversal, access = ProviderBase.AccessOpen, settings = settings)

	@classmethod
	def installed(self):
		return Extension.installed(id = OatScrapers.IdAddon)

	@classmethod
	def enable(self, refresh = False, settings = False):
		result = Extension.enable(id = OatScrapers.IdAddon, refresh = refresh)
		if settings: Settings.launch(Settings.CategoryProvider)
		return result

	@classmethod
	def disable(self, refresh = False, settings = False):
		result = Extension.disable(id = OatScrapers.IdAddon, refresh = refresh)
		if settings: Settings.launch(Settings.CategoryProvider)
		return result

###################################################################
# CRESCRAPERS
###################################################################

class CreScrapers(object):

	Name = 'CrewScrapers'

	IdAddon = Extension.IdCreScrapers
	IdParent = 'plugin.video.thecrew'
	IdLibrary = 'thecrew'
	IdGaia = 'crescrapersx'

	@classmethod
	def settings(self):
		Extension.settings(id = CreScrapers.IdAddon)

	@classmethod
	def providers(self, settings = True):
		from lib.providers.core.manager import Manager
		from lib.providers.core.base import ProviderBase
		Manager.settings(addon = CreScrapers.IdGaia, type = ProviderBase.TypeExternal, mode = ProviderBase.ModeUniversal, access = ProviderBase.AccessOpen, settings = settings)

	@classmethod
	def installed(self):
		return Extension.installed(id = CreScrapers.IdAddon)

	@classmethod
	def enable(self, refresh = False, settings = False):
		result = Extension.enable(id = CreScrapers.IdAddon, refresh = refresh)
		if settings: Settings.launch(Settings.CategoryProvider)
		return result

	@classmethod
	def disable(self, refresh = False, settings = False):
		result = Extension.disable(id = CreScrapers.IdAddon, refresh = refresh)
		if settings: Settings.launch(Settings.CategoryProvider)
		return result

###################################################################
# LAMSCRAPERS
###################################################################

class LamScrapers(object):

	Name = 'LambdaScrapers'

	IdAddon = Extension.IdLamScrapers
	IdLibrary = 'lambdascrapers'
	IdGaia = 'lamscrapersx'

	@classmethod
	def settings(self):
		Extension.settings(id = LamScrapers.IdAddon)

	@classmethod
	def providers(self, settings = True):
		from lib.providers.core.manager import Manager
		from lib.providers.core.base import ProviderBase
		Manager.settings(addon = LamScrapers.IdGaia, type = ProviderBase.TypeExternal, mode = ProviderBase.ModeUniversal, access = ProviderBase.AccessOpen, settings = settings)

	@classmethod
	def installed(self):
		return Extension.installed(id = LamScrapers.IdAddon)

	@classmethod
	def enable(self, refresh = False, settings = False):
		result = Extension.enable(id = LamScrapers.IdAddon, refresh = refresh)
		if settings: Settings.launch(Settings.CategoryProvider)
		return result

	@classmethod
	def disable(self, refresh = False, settings = False):
		result = Extension.disable(id = LamScrapers.IdAddon, refresh = refresh)
		if settings: Settings.launch(Settings.CategoryProvider)
		return result

###################################################################
# CIVSCRAPERS
###################################################################

class CivScrapers(object):

	Name = 'CivitasScrapers'

	IdAddon = Extension.IdCivScrapers
	IdLibrary = 'civitasscrapers'
	IdGaia = 'civscrapersx'

	@classmethod
	def settings(self):
		Extension.settings(id = CivScrapers.IdAddon)

	@classmethod
	def providers(self, settings = True):
		from lib.providers.core.manager import Manager
		from lib.providers.core.base import ProviderBase
		Manager.settings(addon = CivScrapers.IdGaia, type = ProviderBase.TypeExternal, mode = ProviderBase.ModeUniversal, access = ProviderBase.AccessOpen, settings = settings)

	@classmethod
	def installed(self):
		return Extension.installed(id = CivScrapers.IdAddon)

	@classmethod
	def enable(self, refresh = False, settings = False):
		result = Extension.enable(id = CivScrapers.IdAddon, refresh = refresh)
		if settings: Settings.launch(Settings.CategoryProvider)
		return result

	@classmethod
	def disable(self, refresh = False, settings = False):
		result = Extension.disable(id = CivScrapers.IdAddon, refresh = refresh)
		if settings: Settings.launch(Settings.CategoryProvider)
		return result

###################################################################
# GLOSCRAPERS
###################################################################

class GloScrapers(object):

	Name = 'GlobalScrapers'

	IdAddon = Extension.IdGloScrapers
	IdLibrary = 'globalscrapers'
	IdGaia = 'gloscrapersx'

	@classmethod
	def settings(self):
		Extension.settings(id = GloScrapers.IdAddon)

	@classmethod
	def providers(self, settings = True):
		from lib.providers.core.manager import Manager
		from lib.providers.core.base import ProviderBase
		Manager.settings(addon = GloScrapers.IdGaia, type = ProviderBase.TypeExternal, mode = ProviderBase.ModeUniversal, access = ProviderBase.AccessOpen, settings = settings)

	@classmethod
	def installed(self):
		return Extension.installed(id = GloScrapers.IdAddon)

	@classmethod
	def enable(self, refresh = False, settings = False):
		result = Extension.enable(id = GloScrapers.IdAddon, refresh = refresh)
		if settings: Settings.launch(Settings.CategoryProvider)
		return result

	@classmethod
	def disable(self, refresh = False, settings = False):
		result = Extension.disable(id = GloScrapers.IdAddon, refresh = refresh)
		if settings: Settings.launch(Settings.CategoryProvider)
		return result

###################################################################
# UNISCRAPERS
###################################################################

class UniScrapers(object):

	Name = 'UniversalScrapers'

	IdAddon = Extension.IdUniScrapers
	IdLibrary = 'universalscrapers'
	IdGaia = 'uniscrapersx'

	@classmethod
	def settings(self):
		Extension.settings(id = UniScrapers.IdAddon)

	@classmethod
	def providers(self, settings = True):
		from lib.providers.core.manager import Manager
		from lib.providers.core.base import ProviderBase
		Manager.settings(addon = UniScrapers.IdGaia, type = ProviderBase.TypeExternal, mode = ProviderBase.ModeUniversal, access = ProviderBase.AccessOpen, settings = settings)

	@classmethod
	def installed(self):
		return Extension.installed(id = UniScrapers.IdAddon)

	@classmethod
	def enable(self, refresh = False, settings = False):
		result = Extension.enable(id = UniScrapers.IdAddon, refresh = refresh)
		if settings: Settings.launch(Settings.CategoryProvider)
		return result

	@classmethod
	def disable(self, refresh = False, settings = False):
		result = Extension.disable(id = UniScrapers.IdAddon, refresh = refresh)
		if settings: Settings.launch(Settings.CategoryProvider)
		return result

###################################################################
# NANSCRAPERS
###################################################################

class NanScrapers(object):

	Name = 'NanScrapers'

	IdAddon = Extension.IdNanScrapers
	IdLibrary = 'nanscrapers'
	IdGaia = 'nanscrapersx'

	@classmethod
	def settings(self):
		Extension.settings(id = NanScrapers.IdAddon)

	@classmethod
	def providers(self, settings = True):
		from lib.providers.core.manager import Manager
		from lib.providers.core.base import ProviderBase
		Manager.settings(addon = NanScrapers.IdGaia, type = ProviderBase.TypeExternal, mode = ProviderBase.ModeUniversal, access = ProviderBase.AccessOpen, settings = settings)

	@classmethod
	def installed(self):
		return Extension.installed(id = NanScrapers.IdAddon)

	@classmethod
	def enable(self, refresh = False, settings = False):
		result = Extension.enable(id = NanScrapers.IdAddon, refresh = refresh)
		if settings: Settings.launch(Settings.CategoryProvider)
		return result

	@classmethod
	def disable(self, refresh = False, settings = False):
		result = Extension.disable(id = NanScrapers.IdAddon, refresh = refresh)
		if settings: Settings.launch(Settings.CategoryProvider)
		return result

###################################################################
# YOUTUBE
###################################################################

class YouTube(object):

	Id = Extension.IdYouTube
	Website = 'https://youtube.com'

	@classmethod
	def settings(self, settings = False):
		Extension.settings(id = YouTube.Id, wait = settings)
		if settings: self.settingsLocal('settings')

	@classmethod
	def settingsLocal(self, type = None):
		if type is None: type = 'connection' if self.installed() else 'installation'
		Settings.launch('stream.youtube.' + type)

	@classmethod
	def launch(self):
		Extension.launch(id = YouTube.Id)

	@classmethod
	def installed(self):
		return Extension.installed(id = YouTube.Id)

	@classmethod
	def enable(self, refresh = False, settings = False):
		result = Extension.enable(id = YouTube.Id, refresh = refresh)
		if settings: self.settingsLocal('settings')
		return result

	@classmethod
	def disable(self, refresh = False):
		return Extension.disable(id = YouTube.Id, refresh = refresh)

	@classmethod
	def website(self, open = False):
		if open:
			from lib.modules.network import Networker
			Networker.linkShow(link = YouTube.Website)
		return YouTube.Website

	@classmethod
	def quality(self):
		quality = None

		try:
			# Check addon if not installed.
			addon = System.addon(Extension.IdYouTube)
			if addon and addon.getSettingBool('kodion.mpd.videos'):
				selection = addon.getSettingInt('kodion.mpd.quality.selection')
				if selection == 0: quality = 'SD240'
				elif selection == 1: quality = 'SD360'
				elif selection == 2: quality = 'SD480'
				elif selection == 3: quality = 'HD720'
				elif selection == 4: quality = 'HD1080'
				elif selection == 5: quality = 'HD2K'
				elif selection == 6: quality = 'HD4K'
				elif selection == 7: quality = 'HD8K'
		except: Logger.error()

		if not quality:
			from lib.modules.interface import Translation
			quality = Translation.string(33564)

		return quality

	@classmethod
	def qualityUpdate(self):
		Settings.set('stream.youtube.quality', self.quality())

	@classmethod
	def qualitySelect(self, settings = False):
		Extension.settings(id = Extension.IdYouTube, category = 0, wait = True)
		self.qualityUpdate()
		if settings: Settings.launch('stream.youtube.quality')

###################################################################
# UPNEXT
###################################################################

class UpNext(object):

	Id = Extension.IdUpNext

	@classmethod
	def settings(self):
		Extension.settings(id = UpNext.Id)

	@classmethod
	def installed(self):
		return Extension.installed(id = UpNext.Id)

	@classmethod
	def enable(self, refresh = False):
		return Extension.enable(id = UpNext.Id, refresh = refresh)

	@classmethod
	def disable(self, refresh = False):
		return Extension.disable(id = UpNext.Id, refresh = refresh)

###################################################################
# VPNMANAGER
###################################################################

class VpnManager(object):

	Id = Extension.IdVpnManager
	Name = 'VpnManager'

	@classmethod
	def launch(self):
		Extension.launch(id = VpnManager.Id)

	@classmethod
	def settings(self, wait = False):
		Extension.settings(id = VpnManager.Id, wait = wait)

	@classmethod
	def settingsLocal(self, type = None):
		if type is None: type = 'configuration' if self.installed() else 'installation'
		Settings.launch('network.vpn.' + type)

	@classmethod
	def configured(self):
		return not System.addon(id = VpnManager.Id).getSettingBool('vpn_wizard_enabled')

	@classmethod
	def installed(self):
		return Extension.installed(id = VpnManager.Id)

	@classmethod
	def enable(self, refresh = False, confirm = True, settings = False):
		result = Extension.enable(id = VpnManager.Id, refresh = refresh, confirm = confirm)
		if settings: self.settingsLocal()
		return result

	@classmethod
	def disable(self, refresh = False):
		return Extension.disable(id = VpnManager.Id, refresh = refresh)

	@classmethod
	def execute(self, action, parameters = None, loader = False):
		if parameters:
			if Tools.isArray(parameters): parameters = '?'.join(parameters)
			parameters = '?%s' % parameters
		else:
			parameters = ''

		result = System.executePlugin(command = '%s%s/?%s%s' % (System.PluginPrefix, VpnManager.Id, action, parameters))

		if loader:
			# Loader is still showing after VpnManager finished, even if it shows dialogs. Manually hide the loader.
			from lib.modules.interface import Loader
			Loader.show()
			Pool.thread(target = Loader.hide, kwargs = {'delay' : 3}, start = True)

		return result

	@classmethod
	def change(self, profile = None, dialog = False, loader = True):
		if not profile: profile = 'Czech Republic'

		profiles = []
		addon = System.addon(id = VpnManager.Id)
		for i in range(1, 11):
			value = addon.getSetting('%d_vpn_validated_friendly' % i)
			if value: profiles.append(value)
		if len(profiles) <= 0: return False

		current = System.windowPropertyGet('VPN_Manager_Connected_Profile_Friendly_Name')

		if dialog:
			from lib.modules.interface import Dialog
			choice = Dialog.select(title = 33801, items = profiles, selection = current if current else None)
			if choice < 0: return False
			profile = profiles[choice]
		else:
			if len(profiles) == 1:
				profile = profiles[0]
			else:
				if current: profiles.remove(current)
				profile = Tools.listPick(profiles)

		self.execute(action = 'change', parameters = profile, loader = loader)
		return True

	@classmethod
	def disconnect(self, loader = True):
		self.execute(action = 'disconnect', loader = loader)
		return True

	@classmethod
	def status(self, loader = True):
		self.execute(action = 'display', loader = loader)
		return True

###################################################################
# TMDBHELPER
###################################################################

class TmdbHelper(object):

	Id = Extension.IdTmdbHelper
	Directory = 'players'
	Player = 'gaia.json'

	@classmethod
	def launch(self):
		Extension.launch(id = TmdbHelper.Id)

	@classmethod
	def settings(self, wait = False):
		Extension.settings(id = TmdbHelper.Id, wait = wait)

	@classmethod
	def installed(self):
		return Extension.installed(id = TmdbHelper.Id)

	@classmethod
	def enable(self, refresh = False, confirm = True):
		result = Extension.enable(id = TmdbHelper.Id, refresh = refresh, confirm = confirm)
		return result

	@classmethod
	def disable(self, refresh = False):
		return Extension.disable(id = TmdbHelper.Id, refresh = refresh)

	@classmethod
	def path(self, directory = False, player = False, translate = True):
		path = System.profile(id = TmdbHelper.Id, translate = translate)
		if directory or player: path = File.joinPath(path, TmdbHelper.Directory)
		if player: path = File.joinPath(path, TmdbHelper.Player)
		return path

	@classmethod
	def command(self, action, media, season = None, episode = None):
		prefix = '-_1_-'
		suffix = '-_2_-'
		parameters = {}

		if action == 'scrape':
			parameters = {'action' : action, 'media' : media, 'imdb' : '{imdb}', 'tmdb' : '{tmdb}', 'tvdb' : '{tvdb}', 'trakt' : '{trakt}', 'title' : '{title_url}', 'year' : '{year}', 'premiered' : '{premiered}'}
			if Media.isSerie(media):
				parameters.update({
					'season' : '{season}',
					'episode' : '{episode}',
					'tvshowtitle' : '{showname_url}',
					'year' : '{showyear}',
				})
		elif action == 'search':
			parameters = {'action' : action, 'media' : media, 'query' : '{clearname_url}'}

		for key, value in parameters.items(): parameters[key] = value.replace('{', prefix).replace('}', suffix)
		command = System.command(parameters = parameters, origin = 'themoviedbhelper', optimize = False)
		command = command.replace(prefix, '{').replace(suffix, '}')

		return command

	@classmethod
	def integrate(self):
		try:
			from lib.modules.interface import Dialog, Format
			title = 36382

			if Dialog.option(title = title, message = 36385):
				directory = self.path(directory = True)
				path = self.path(player = True)
				plugin = System.id()

				# Check if the addon is installed.
				if not self.installed():
					Dialog.confirm(title = title, message = 36386)
					Dialog.notification(title = title, message = 36391, icon = Dialog.IconError)
					return False

				# Create the players directory.
				if not File.existsDirectory(directory):
					File.makeDirectory(directory)
					if not File.existsDirectory(directory):
						Dialog.confirm(title = title, message = 36387)
						Dialog.notification(title = title, message = 36391, icon = Dialog.IconError)
						return False

				# Check if any other unofficial Gaia players are installed.
				installed = []
				_, files = File.listDirectory(path = directory, absolute = True)
				for file in files:
					if file.lower().endswith('.json') and not file == path:
						try:
							data = Converter.jsonFrom(File.readNow(file))
							if data and data['plugin'].lower() == plugin: installed.append(file)
						except:
							Logger.error()
							pass
				if installed:
					if Dialog.option(title = title, message = 36388):
						for file in installed: File.delete(file)

				# Check if the player was already installed.
				if File.exists(path):
					if not Dialog.option(title = title, message = 36389):
						return False

				data = {
					'name' : Format.fontColor(System.name(), color = Format.colorPrimary()),
					'plugin' : plugin,
					'priority' : 200,
					'is_resolvable' : 'false',
					'play_movie' : self.command(action = 'scrape', media = Media.Movie),
					'play_episode' : self.command(action = 'scrape', media = Media.Show),
					'search_movie' : self.command(action = 'search', media = Media.Movie),
					'search_episode' : self.command(action = 'search', media = Media.Show),
				}

				File.writeNow(path, Converter.jsonPrettify(data))
				if not File.exists(path):
					Dialog.notification(title = title, message = 36391, icon = Dialog.IconError)
					Dialog.confirm(title = title, message = 36387)
					return False

				Dialog.notification(title = title, message = 36390, icon = Dialog.IconSuccess)
				return True
			else:
				return False
		except: Logger.error()
		Dialog.notification(title = title, message = 36391, icon = Dialog.IconError)
		return False

###################################################################
# BACKUP
###################################################################

class Backup(object):

	Extension = 'zip'
	Directory = 'Backups'

	TypeEverything = 'everything'
	TypeSettings = 'settings'
	TypeDatabases = 'databases'

	ResultFailure = 'failure'
	ResultPartial = 'partial'
	ResultSuccess = 'success'
	ResultVersion = 'version'

	@classmethod
	def _path(self, clear = False):
		return System.temporary(directory = 'backup', gaia = True, make = True, clear = clear)

	@classmethod
	def _name(self):
		from lib.modules import interface
		from lib.modules import convert
		date = convert.ConverterTime(Time.timestamp(), convert.ConverterTime.FormatTimestamp).string(convert.ConverterTime.FormatDateTime)
		date = date.replace(':', '.') # Windows does not support colons in file names.
		return System.name() + ' ' + interface.Translation.string(33773) + ' ' + date + '%s.' + Backup.Extension

	@classmethod
	def _import(self, path):
		try:
			Logger.log('Importing Settings Backup')

			directory = File.joinPath(self._path(clear = True), File.name(path = path, extension = False))
			directoryData = System.profile()

			import zipfile
			file = zipfile.ZipFile(path, 'r')

			# Do not allow to import old settings backups.
			with file.open('settings.xml') as subfile:
				version = Regex.extract(data = Converter.unicode(subfile.read()), expression = 'id\s*=\s*"internal.version".*?>(.*?)<')
				version = int(version.replace('.', ''))
				if version < 600:
					file.close()
					return Backup.ResultVersion

			file.extractall(directory)
			file.close()

			directories, files = File.listDirectory(directory)
			counter = 0
			for file in files:
				fileFrom = File.joinPath(directory, file)
				fileTo = File.joinPath(directoryData, file)
				if File.move(fileFrom, fileTo, replace = True):
					counter += 1

			File.deleteDirectory(path = directory, force = True)

			# Clear the data from the old file.
			Settings.cacheClear()

			# Very important.
			# Otherwise if writing to the settings file (Settings.set(...)), like with Platform.identifierReset() below, Kodi replaces the settings with its own internally cached settings data before the backup was imported.
			# Getting a setting seems to force Kodi to replaces its internal cached settings with the new data from after the backup import.
			Settings.get('internal.dummy')

			Platform.identifierReset()

			if counter == 0: return Backup.ResultFailure
			elif counter == len(files): return Backup.ResultSuccess
			else: return Backup.ResultPartial
		except:
			Logger.error()
			return Backup.ResultFailure

	@classmethod
	def _export(self, type, path, automatic = False):
		try:
			Logger.log('Exporting Settings Backup')

			File.makeDirectory(path)
			name = self._name()
			path = File.joinPath(path, name)
			if automatic:
				path = path % ''
			else:
				counter = 0
				suffix = ''
				while File.exists(path % suffix):
					counter += 1
					suffix = ' [%d]' % counter
				path = path % suffix

			import zipfile
			file = zipfile.ZipFile(path, 'w')

			content = []
			directory = self._path(clear = True)
			directoryData = System.profile()
			directories, files = File.listDirectory(directoryData)

			from lib.modules import database
			settingsDatabase = (Settings.Database + database.Database.Extension).lower()

			if type == Backup.TypeEverything or type == Backup.TypeSettings:
				settings = ['settings.xml', settingsDatabase]
				for i in range(len(files)):
					if files[i].lower() in settings:
						content.append(files[i])

			if type == Backup.TypeEverything or type == Backup.TypeDatabases:
				extension = '.db'
				for i in range(len(files)):
					if files[i].lower().endswith(extension) and not files[i].lower() == settingsDatabase:
						content.append(files[i])

			tos = [File.joinPath(directory, i) for i in content]
			froms = [File.joinPath(directoryData, i) for i in content]

			for i in range(len(content)):
				try:
					File.copy(froms[i], tos[i], overwrite = True)
					file.write(tos[i], content[i])
				except: pass

			file.close()
			File.deleteDirectory(path = directory, force = True)
			return Backup.ResultSuccess
		except:
			Logger.error()
			return Backup.ResultFailure

	@classmethod
	def automaticPath(self):
		return File.joinPath(System.profile(), Backup.Directory)

	@classmethod
	def automaticSize(self):
		return File.sizeDirectory(self.automaticPath())

	@classmethod
	def automaticClear(self):
		return File.deleteDirectory(self.automaticPath())

	@classmethod
	def automaticClean(self):
		limit = Settings.getInteger('general.settings.backup.limit', cached = False)
		path = self.automaticPath()
		directories, files = File.listDirectory(path)
		count = len(files)
		if count >= limit:
			files.sort(reverse = False)
			i = 0
			while count >= limit:
				File.delete(File.joinPath(path, files[i]), force = True)
				i += 1
				count -= 1

	@classmethod
	def automaticImport(self, force = False, notification = True):
		try:
			from lib.modules import interface

			# The problem here is that if the settings are corrupt, the user's preferences, set previously, cannot be determined.
			# Hence, always load the last backup if settings are corrupt. Then check if automatic/selection was enabled.
			# If automatic, don't do anything further.
			# If selection, ask the user which backup to load.

			# For some reasons the setting returns nothing, but when getting it again immediately afterwards, it returns a value.
			timestamp = Settings.getInteger('general.settings.backup.time', cached = False)
			if not timestamp:
				Time.sleep(0.5)
				timestamp = Settings.getInteger('general.settings.backup.time', cached = False)

			if force or (not timestamp and File.existsDirectory(self.automaticPath())):
				directories, files = File.listDirectory(self.automaticPath())
				Settings.set('general.settings.backup.time', Time.timestamp(), cached = True)

				if len(files) > 0:
					files.sort(reverse = True)
					result = self._import(path = File.joinPath(self.automaticPath(), files[0]))
					if result == Backup.ResultSuccess or result == Backup.ResultPartial:
						Settings.set('general.settings.backup.time', Time.timestamp(), cached = True)

					if not Settings.getBoolean('general.settings.backup.enabled', cached = False):
						return False

					restore = Settings.getInteger('general.settings.backup.restore', cached = False)
					choice = -1
					if not force and restore == 0:
						choice = 0
					elif force or (restore == 1 and interface.Dialog.option(title = 33773, message = 35210)):
						items = [interface.Format.fontBold(re.search('\\d*-\\d*-\\d*\\s*\\d*\\.\\d*\\.\\d*', file).group(0).replace('.', ':')) for file in files]
						choice = interface.Dialog.select(title = 33773, items = items)

					if choice >= 0:
						result = self._import(path = File.joinPath(self.automaticPath(), files[choice]))
						if result == Backup.ResultSuccess or result == Backup.ResultPartial:
							Settings.set('general.settings.backup.time', Time.timestamp(), cached = True)
							if notification: interface.Dialog.notification(title = 33773, message = 35211, icon = interface.Dialog.IconSuccess, duplicates = True)
						elif result == Backup.ResultFailure:
							if notification: interface.Dialog.notification(title = 33773, message = 33932, icon = interface.Dialog.IconError, duplicates = True)
						return result == Backup.ResultSuccess

					return False

			# Not returned from the inner if.
			if force and notification: interface.Dialog.notification(title = 33773, message = 35247, icon = interface.Dialog.IconError, duplicates = True)
			return False
		except:
			Logger.error()
		return False

	@classmethod
	def automaticExport(self, force = False):
		try:
			if Settings.getBoolean('general.settings.backup.enabled', cached = False) or force:
				self.automaticClean()
				Settings.set('general.settings.backup.time', Time.timestamp(), cached = True)
				return self._export(type = Backup.TypeSettings, path = self.automaticPath(), automatic = True) == Backup.ResultSuccess
		except: Logger.error()
		return False

	@classmethod
	def automatic(self):
		from lib.modules import interface

		interface.Dialog.confirm(title = 33773, message = 35209)

		items = [
			interface.Format.bold(interface.Translation.string(33774) + ':') + ' ' + interface.Translation.string(35214),
			interface.Format.bold(interface.Translation.string(35212) + ':') + ' ' + interface.Translation.string(35215),
			interface.Format.bold(interface.Translation.string(33011) + ':') + ' ' + interface.Translation.string(35216),
		]

		choice = interface.Dialog.select(title = 33773, items = items)
		if choice == 0:
			if interface.Dialog.option(title = 33773, message = 35217):
				self.automaticImport(force = True)
		elif choice == 1:
			if self.automaticExport(force = True):
				interface.Dialog.notification(title = 33773, message = 35218, icon = interface.Dialog.IconSuccess, duplicates = True)
			else:
				interface.Dialog.notification(title = 33773, message = 35219, icon = interface.Dialog.IconError, duplicates = True)
		elif choice == 2:
			Settings.launch(Settings.CategoryGeneral)

	@classmethod
	def manualImport(self):
		from lib.modules import interface

		choice = interface.Dialog.option(title = 33773, message = 33782)
		if not choice: return

		path = interface.Dialog.browse(title = 33773, type = interface.Dialog.BrowseFile, mask = Backup.Extension)
		result = self._import(path = path)

		if result == Backup.ResultSuccess:
			interface.Dialog.notification(title = 33773, message = 33785, icon = interface.Dialog.IconSuccess, duplicates = True)
		elif result == Backup.ResultPartial:
			interface.Dialog.confirm(title = 33773, message = interface.Translation.string(33783) % System.id())
		elif result == Backup.ResultVersion:
			interface.Dialog.confirm(title = 33773, message = 33980)
		else:
			interface.Dialog.confirm(title = 33773, message = 33778)

	@classmethod
	def manualExport(self):
		from lib.modules import interface

		choice = interface.Dialog.option(title = 33773, message = 35213)
		if not choice: return

		types = [
			Backup.TypeEverything,
			Backup.TypeSettings,
			Backup.TypeDatabases,
		]
		items = [
			interface.Format.bold(interface.Translation.string(33776) + ':') + ' ' + interface.Translation.string(33779),
			interface.Format.bold(interface.Translation.string(33011) + ':') + ' ' + interface.Translation.string(33780),
			interface.Format.bold(interface.Translation.string(33775) + ':') + ' ' + interface.Translation.string(33781),
		]

		choice = interface.Dialog.select(title = 33773, items = items)
		if choice >= 0:
			path = interface.Dialog.browse(title = 33773, type = interface.Dialog.BrowseDirectoryWrite)
			result = self._export(type = types[choice], path = path)

			if result == Backup.ResultSuccess:
				interface.Dialog.notification(title = 33773, message = 33784, icon = interface.Dialog.IconSuccess, duplicates = True)
			else:
				interface.Dialog.confirm(title = 33773, message = 33777)

	@classmethod
	def directImport(self, path):
		from lib.modules import interface
		self._import(path)
		interface.Dialog.notification(title = 33773, message = 35326, icon = interface.Dialog.IconSuccess, duplicates = True)

###################################################################
# DONATIONS
###################################################################

class Donations(object):

	# Popup
	PopupThreshold = 50

	@classmethod
	def donor(self):
		return System.developer(version = False) or System.developerCode() == Converter.base64From('ZG9ub3I=')

	@classmethod
	def increment(self, update = True):
		counter = Settings.getInteger('internal.donation') + 1
		if update: Settings.set('internal.donation', counter)
		return counter

	@classmethod
	def reset(self):
		Settings.set('internal.donation', 0)

	@classmethod
	def show(self, type = None, wait = False):
		if type is None:
			from lib.modules.window import WindowDonation
			WindowDonation.show(wait = wait)
		else:
			from lib.modules.window import WindowQr
			from lib.modules.api import Api
			donations = Api.donation(cache = True)
			WindowQr.show(donations = donations, symbol = type, wait = wait)

	@classmethod
	def popup(self, full = True, wait = False):
		if wait:
			self._popup(full = full, wait = wait)
		else:
			thread = Pool.thread(target = self._popup, kwargs = {'full' : full})
			thread.start()

	@classmethod
	def _popup(self, full = True, increment = False, wait = False):
		from lib.modules import interface
		if not self.donor():
			counter = self.increment(update = increment)
			if counter >= Donations.PopupThreshold:
				self.reset()
				if full or not interface.Dialog.option(title = 33505, message = interface.Translation.string(35014), labelConfirm = 35015, labelDeny = 33505):
					self.show(wait = wait)
					interface.Loader.hide()
					return True
				interface.Loader.hide()
		return False

###################################################################
# DISCLAIMER
###################################################################

class Disclaimer(object):

	@classmethod
	def message(self):
		from lib.modules.interface import Translation
		return Translation.string(35111) + ' ' + Translation.string(35112)

	@classmethod
	def agreed(self):
		return Settings.getBoolean('internal.initial.disclaimer')

	@classmethod
	def disagreed(self):
		return not self.agreed()

	@classmethod
	def agree(self, agree = True):
		Settings.set('internal.initial.disclaimer', agree)
		return agree

	@classmethod
	def disagree(self, disagree = True):
		return self.agree(agree = not disagree)

	@classmethod
	def show(self, exit = True, short = False):
		from lib.modules.interface import Translation, Format
		if short:
			message = Translation.string(35111) + Format.newline() + Translation.string(35112) + Format.newline() + Translation.string(35113)
			choice = self._option(message = message, left = 35116, right = 35115)
		else:
			while True:
				choice = self._option(message = 35111, left = 33743, right = 33821)
				if choice: self._confirm(message = 35114)
				else: break
			while True:
				choice = self._option(message = 35112, left = 33743, right = 33821)
				if choice: self._confirm(message = 35114)
				else: break
			choice = self._option(message = 35113, left = 35116, right = 35115)
		if choice:
			self.disagree()
			System.launchDataClear()
			System.quit()
			return False
		else:
			self.agree()
			return True

	@classmethod
	def _option(self, message, left, right):
		from lib.modules.interface import Dialog
		return Dialog.option(title = 35109, message = message, labelConfirm = left, labelDeny = right)

	@classmethod
	def _confirm(self, message):
		from lib.modules.interface import Dialog
		return Dialog.confirm(title = 35109, message = message)


###################################################################
# PLAYLIST
###################################################################

class Playlist(object):

	Id = xbmc.PLAYLIST_VIDEO

	@classmethod
	def playlist(self):
		return xbmc.PlayList(Playlist.Id)

	@classmethod
	def show(self):
		from lib.modules import window
		window.Window.show(window.Window.IdWindowPlaylist)

	@classmethod
	def clear(self, notification = True):
		self.playlist().clear()
		if notification:
			from lib.modules import interface
			interface.Dialog.notification(title = 35515, message = 35521, icon = interface.Dialog.IconSuccess)

	@classmethod
	def items(self):
		try: return [i['label'] for i in System.executeJson(method = 'Playlist.GetItems', parameters = {'playlistid' : Playlist.Id})['result']['items']]
		except: return []

	@classmethod
	def size(self):
		return len(self.items())

	@classmethod
	def empty(self):
		return len(self.items()) == 0

	@classmethod
	def contains(self, label):
		return label in self.items()

	@classmethod
	def position(self, label):
		try: return self.items().index(label)
		except: return -1

	@classmethod
	def add(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, metadata = None, link = None, label = None, images = None, context = None, notification = True):
		if link is None:
			System.execute('Action(Queue)')
			return None
		else:
			if not metadata:
				from lib.meta.manager import MetaManager
				metadata = MetaManager.instance().metadata(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

			if metadata:
				from lib.modules import interface

				# These skins add their own labels using the title and season/episode numbers.
				label = not(interface.Skin.isEstuary() or interface.Skin.isEstouchy())

				# Do not add the context, rather use the global context menu instead.
				from lib.meta.tools import MetaTools
				item = MetaTools.instance().item(label = label, metadata = metadata, context = False, content = False, extend = MetaTools.ExtendNone)

				link = System.originSet(origin = System.OriginPlaylist, command = link) # Helps to identify calls coming from the playlist, especially for the "scrape" endpoint.
				self.playlist().add(url = link, listitem = item['item'])
				if notification: interface.Dialog.notification(title = 35515, message = 35519, icon = interface.Dialog.IconSuccess)

				return True
		return False

	@classmethod
	def remove(self, label, notification = True):
		#self.playlist().remove(link) # This doesn't seem to work all the time.
		position = self.position(label = label)
		if position >= 0:
			# The first item in the playlist cannot be removed using Playlist.Remove().
			#	https://forum.kodi.tv/showthread.php?tid=236016
			# If there is only 1 item in the playlist, clear it instead.
			if self.size() == 1: self.clear(notification = False)
			else: System.executeJson(method = 'Playlist.Remove', parameters = {'playlistid' : Playlist.Id, 'position' : position})

			if notification:
				from lib.modules import interface
				interface.Dialog.notification(title = 35515, message = 35520, icon = interface.Dialog.IconSuccess)

	@classmethod
	def settings(self, settings = False, silent = False):
		# When Gaia's scraping on streaming process is initiated from anywhere else than Gaia (eg: external addons, widgets, Gaia's local library feature, or Kodi's playlists, the following error dialog might show:
		#	Playback failed - One or more items failed to play. Check the log for more information abouth this message.
		# Gaia's streaming process (eg: add a stream link to the local library) seems to not have this problem, since tools.System.pluginResolvedSet() is called from player.py.
		# However, Gaia's scraping process (eg: add a movie/episode to the local library) still has this problem. Using tools.System.pluginResolvedSet() in core.py -> scrape() seems to get rid of it when launched from the local library.
		# However, when adding a movie to Kodi's playlist, then playing the movie from the playlist (no dialog shows), but then playing the movie a 2nd time from the playlist, the dialog still pops up.
		# Setting playlistretries and playlisttimeout in advancedsettings.xml seems to make sure these dialogs do not show.
		# Changing DialogConfirm.xml in Gaia Eminence also does not work, since the labels in the dialog are set AFTER the dialog has been shown, so adding "<visible>...</visible>" or "<onload condition="String.IsEqual(Control.GetLabel(9),$LOCALIZE[16027])">Dialog.Close(okdialog)</onload>" does not work, since the label is not ALWAYS available yet when the condition is evaluated.
		# 	https://forum.kodi.tv/showthread.php?tid=207602

		from lib.modules.interface import Dialog, Translation

		comment = ' <!-- GAIA - Added By Gaia Settings -> %s -> %s. -->' % (Translation.string(32330), Translation.string(35532))

		found = False
		data = None
		flags = Regex.FlagCaseInsensitive | Regex.FlagAllLines
		if File.exists(System.AdvancedSettings):
			data = File.readNow(System.AdvancedSettings)
			if Regex.match(data = data, expression = '<playlistretries>.*?<\/playlistretries>', flags = flags): found = True
			elif Regex.match(data = data, expression = '<playlisttimeout>.*?<\/playlisttimeout>', flags = flags): found = True

		if not silent:
			Dialog.text(title = 35532, message = 32028)

			if found:
				message = Translation.string(32029)
				choice = Dialog.options(title = 35532, message = message, labelConfirm = 33743, labelDeny = 33925, labelCustom = 35479)
				if choice == Dialog.ChoiceYes:
					return self._settingsResult(result = None, settings = settings)
				elif choice == Dialog.ChoiceYes:
					data = Regex.remove(data = data, expression = '(\n?\s*<playlistretries>.*?<\/playlistretries>(?:\s*<!--.*?-->)?)', flags = flags, all = True)
					data = Regex.remove(data = data, expression = '(\n?\s*<playlisttimeout>.*?<\/playlisttimeout>(?:\s*<!--.*?-->)?)', flags = flags, all = True)
					if File.writeNow(System.AdvancedSettings, data):
						data = File.readNow(System.AdvancedSettings)
						if '<playlistretries>' in data or '<playlisttimeout>' in data:
							Dialog.confirm(title = 35532, message = 32030)
							return self._settingsResult(result = True, settings = settings)
						else:
							Dialog.confirm(title = 35532, message = 32048)
							return self._settingsResult(result = False, settings = settings)

		playlistRetries = '<playlistretries>999999</playlistretries>'
		playlistTimeout = '<playlisttimeout>7200</playlisttimeout>'

		if not data or not '</advancedsettings>' in data: data = '<advancedsettings></advancedsettings>'
		data = Regex.remove(data = data, expression = '(\n?\s*<playlistretries>.*?<\/playlistretries>(?:\s*<!--.*?-->)?)', flags = flags, all = True)
		data = Regex.remove(data = data, expression = '(\n?\s*<playlisttimeout>.*?<\/playlisttimeout>(?:\s*<!--.*?-->)?)', flags = flags, all = True)
		data = data.replace('</advancedsettings>', '\n\t%s%s\n\t%s%s\n</advancedsettings>' % (playlistRetries, comment, playlistTimeout, comment))
		if File.writeNow(System.AdvancedSettings, data):
			data = File.readNow(System.AdvancedSettings)
			if playlistRetries in data and playlistTimeout in data:
				if not silent: Dialog.confirm(title = 35532, message = 32049)
				return self._settingsResult(result = True, settings = settings)
		if not silent: Dialog.confirm(title = 35532, message = 32030)

		return self._settingsResult(result = False, settings = settings)

	@classmethod
	def _settingsResult(self, result, settings = False):
		from lib.modules.interface import Translation
		id = 'playback.playlist.error'
		if not result is None: Settings.set(id = id, value = Translation.string(32301 if result else 32302))
		if settings: Settings.launch(id = id)
		return bool(result)

	@classmethod
	def initialize(self):
		from lib.modules.interface import Translation
		setting = Settings.getString(id = 'playback.playlist.error')
		if setting == '$ADDON[plugin.video.gaia 33564]' or setting == Translation.string(33564):
			self.settings(settings = False, silent = True)

###################################################################
# BINGE
###################################################################

class Binge(object):

	ModeNone = 0
	ModeFirst = 1
	ModeContinue = 2
	ModeBackground = 3

	DialogNone = 0
	DialogFull = 1
	DialogOverlay = 2
	DialogButton = 3
	DialogUpNext = 4

	ActionContinue = 0
	ActionCancel = 1

	ActionInterrupt = 0
	ActionFinish = 1

	@classmethod
	def enabled(self):
		return Settings.getBoolean('activity.binge.enabled')

	@classmethod
	def pack(self):
		return Settings.getBoolean('playback.autoplay.binge')

	@classmethod
	def dialog(self):
		return Settings.getInteger('activity.binge.dialog')

	@classmethod
	def dialogNone(self):
		return self.dialog() == Binge.DialogNone

	@classmethod
	def dialogFull(self):
		return self.dialog() == Binge.DialogFull

	@classmethod
	def dialogOverlay(self):
		return self.dialog() == Binge.DialogOverlay

	@classmethod
	def dialogButton(self):
		return self.dialog() == Binge.DialogButton

	@classmethod
	def dialogUpNext(self):
		return self.dialog() == Binge.DialogUpNext

	@classmethod
	def scrape(self):
		return Settings.getCustom('activity.binge.scrape')

	@classmethod
	def delay(self):
		return Settings.getCustom('activity.binge.delay')

	@classmethod
	def suppress(self):
		return Settings.getInteger('activity.binge.suppress')

	@classmethod
	def actionNone(self):
		return Settings.getInteger('activity.binge.action.none')

	@classmethod
	def actionContinue(self):
		return Settings.getInteger('activity.binge.action.continue')

	@classmethod
	def actionCancel(self):
		return Settings.getInteger('activity.binge.action.cancel')

	@classmethod
	def continueEnabled(self):
		return Settings.getBoolean('activity.binge.continue')

	@classmethod
	def continueTimeout(self):
		return Settings.getCustom('activity.binge.continue.timeout')

	@classmethod
	def continueAction(self):
		return Settings.getInteger('activity.binge.continue.action')

	@classmethod
	def continueInteract(self):
		return Settings.getBoolean('activity.binge.continue.interact')

	@classmethod
	def continuePropagate(self):
		return Settings.getInteger('activity.binge.continue.propagate')

###################################################################
# OBSERVER
###################################################################

class Observer(object):

	ModePlayback		= 'playback'
	ModeInteract		= 'interact'

	TypeStart			= 'start'		# Playback started.
	TypeStop			= 'stop'		# Playback stopped/finihsed.
	TypeRating			= 'rating'		# Interacted with the rating dialog.
	TypeContinue		= 'continue'	# Interacted with the continue dialog.
	TypeSkip			= 'skip'		# Interacted with the skip intro button.
	TypeBinge			= 'binge'		# Interacted with the continue button or binge dialog.
	TypeScrape			= 'scrape'		# Manually started a new scrape.
	TypeStream			= 'stream'		# Manually interacted with the stream window.

	ActionNone			= None
	ActionContinue		= 'continue'
	ActionStop			= 'stop'
	ActionPowerdown		= System.PowerPowerdown
	ActionShutdown		= System.PowerShutdown
	ActionReboot		= System.PowerReboot
	ActionRestart		= System.PowerRestart
	ActionSuspend		= System.PowerSuspend
	ActionHibernate		= System.PowerHibernate
	ActionStandby		= System.PowerStandby
	ActionMinimize		= System.PowerMinimize
	ActionQuit			= System.PowerQuit
	ActionScreensaver	= System.PowerScreensaver

	Setting				= 'activity.automation.observer'
	Property			= 'GaiaObserver'

	@classmethod
	def evaluate(self, binge = None, notify = None):
		try:
			observations = self.settings()
			if observations:
				entries = Converter.jsonFrom(System.windowPropertyGet(property = Observer.Property))
				if entries:
					old = Time.past(hours = 24)
					keys = ['imdb', 'tmdb', 'tvdb', 'trakt', 'set', 'season', 'episode']

					for observation in observations:
						items = list(reversed(Tools.copy(entries)))
						current = {
							'watched' : {'counter' : [], 'duration' : 0},
							'inactive' : {'counter' : [], 'duration' : 0},
						}

						# Allow exception for the last episode.
						if binge is False:
							value = observation['exception']['last']
							if value is True: return observation['activity']
							elif value is False: return False

						# Allow exception movies or other standalone titles.
						if binge is None:
							value = observation['exception']['discrete']
							if value is True: return observation['activity']
							elif value is False: return False

						# Ignore all older entries before the last item from a different show.
						if observation['exception']['reset']:
							last = None
							for item in items:
								if item['mode'] == Observer.ModePlayback:
									last = item
									break
							if last:
								for i in range(len(items)):
									item = items[i]
									if item['mode'] == Observer.ModePlayback:
										if not Tools.dictionaryEqual(item, last, keys = keys):
											items = items[:i]
											break

						# Calculate the total duration.
						# Note that there could be multiple entries for the same episode, if we stop playback to select another working stream.
						start = 0
						end = 0
						interact = False
						for item in items:
							if item['time'] < old:
								break # Ignore old stuff.
							elif item['mode'] == Observer.ModePlayback:
								if item['type'] == Observer.TypeStop:
									end = item['time']
								elif item['type'] == Observer.TypeStart:
									if end:
										duration = end - item['time']
										end = 0
										current['watched']['duration'] += duration
										current['watched']['counter'].append(item)
										if not interact:
											current['inactive']['duration'] += duration
											current['inactive']['counter'].append(item)
							elif item['mode'] == Observer.ModeInteract:
								interact = True

						# Do not count duplicates.
						temp = []
						for item in current['watched']['counter']:
							contains = False
							for item2 in temp:
								if Tools.dictionaryEqual(item, item2, keys = keys):
									contains = True
									break
							if not contains: temp.append(item)
						current['watched']['counter'] = len(temp)

						# Do not count duplicates.
						temp = []
						for item in current['inactive']['counter']:
							contains = False
							for item2 in temp:
								if Tools.dictionaryEqual(item, item2, keys = keys):
									contains = True
									break
							if not contains: temp.append(item)
						current['inactive']['counter'] = len(temp)

						valid = 0
						for i in ['inactive', 'watched']:
							for j in ['counter', 'duration']:
								if observation['condition'][i][j]:
									if current[i][j] and current[i][j] >= observation['condition'][i][j]: valid += 1
									else: break
								else: valid += 1

						if valid == 4 and observation['activity']['action']:
							if notify: self.notify(observation = observation)
							return observation['activity']
		except: Logger.error()
		return None

	@classmethod
	def notify(self, observation, notification = None, sound = None):
		from lib.modules.interface import Dialog, Translation, Format

		if not observation: return False
		if 'activity' in observation: observation = observation['activity']

		label = 33387
		for i in self.settingsActions():
			if i['action'] == observation['action']:
				label = i['label']
				break
		label = Translation.string(label)

		Logger.log('Observer Action: %s' % label)
		if sound or observation['sound']: Sound.executePowerStart()
		if notification or observation['notification']: Dialog.notification(title = 36517, message = '%s: %s' % (Format.fontBold(36519), label), time = 8000, icon = Dialog.IconWarning)
		return True

	@classmethod
	def update(self, mode, type, imdb = None, tmdb = None, tvdb = None, trakt = None, set = None, season = None, episode = None):
		try:
			items = Converter.jsonFrom(System.windowPropertyGet(property = Observer.Property))
			if not items: items = []

			value = {'mode' : mode, 'type' : type, 'time' : Time.timestamp()}
			if mode == Observer.ModeInteract:
				# Delete old entry if we are doing the same thing again.
				if items and items[-1]['mode'] == mode and items[-1]['type'] == type: del items[-1]
			else:
				value.update({
					'imdb' : imdb,
					'tmdb' : tmdb,
					'tvdb' : tvdb,
					'trakt' : trakt,
					'set' : set,
					'season' : season,
					'episode' : episode,
				})

			items.append(value)
			items = items[:200]
			System.windowPropertySet(property = Observer.Property, value = Converter.jsonTo(items))
			return True
		except: Logger.error()
		return False

	@classmethod
	def updatePlayback(self, type, imdb = None, tmdb = None, tvdb = None, trakt = None, set = None, season = None, episode = None):
		return self.update(mode = Observer.ModePlayback, type = type, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, set = set, season = season, episode = episode)

	@classmethod
	def updatePlaybackStart(self, imdb = None, tmdb = None, tvdb = None, trakt = None, set = None, season = None, episode = None):
		return self.updatePlayback(type = Observer.TypeStart, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, set = set, season = season, episode = episode)

	@classmethod
	def updatePlaybackStop(self, imdb = None, tmdb = None, tvdb = None, trakt = None, set = None, season = None, episode = None):
		return self.updatePlayback(type = Observer.TypeStop, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, set = set, season = season, episode = episode)

	@classmethod
	def updateInteract(self, type):
		return self.update(mode = Observer.ModeInteract, type = type)

	@classmethod
	def updateInteractRating(self):
		return self.updateInteract(type = Observer.TypeRating)

	@classmethod
	def updateInteractContinue(self):
		return self.updateInteract(type = Observer.TypeContinue)

	@classmethod
	def updateInteractSkip(self):
		return self.updateInteract(type = Observer.TypeSkip)

	@classmethod
	def updateInteractBinge(self):
		return self.updateInteract(type = Observer.TypeBinge)

	@classmethod
	def updateInteractScrape(self):
		return self.updateInteract(type = Observer.TypeScrape)

	@classmethod
	def updateInteractStream(self):
		return self.updateInteract(type = Observer.TypeStream)

	@classmethod
	def clear(self):
		System.windowPropertyClear(property = Observer.Property)

	@classmethod
	def settings(self):
		# Use the default settings as base, in case new attributes were added or old ones removed in a later version.
		result = []
		data = Settings.getDataList(id = Observer.Setting)
		if data:
			default = self.settingsDefault()
			for i in data: result.append(Tools.update(Tools.copy(default), i))
		return result

	@classmethod
	def settingsDefault(self):
		return {
			'condition' : {
				'watched' : {'counter' : None, 'duration' : None},
				'inactive' : {'counter' : None, 'duration' : None},
			},
			'exception' : {
				'reset' : True,
				'last' : False,
				'discrete' : False,
			},
			'activity' : {
				'action' : Observer.ActionStop,
				'timeout' : 60,
				'notification' : True,
				'sound' : True,
			},
		}

	@classmethod
	def settingsActions(self):
		from lib.modules.interface import Translation, Format

		actions = [
			{'action' : Observer.ActionContinue,	'label' : Translation.string(36497)},
			{'action' : Observer.ActionStop,		'label' : Translation.string(36507)},
		]
		for i in actions:
			format = i['label'].split(' ')
			i['format'] = Format.fontBold(' '.join(format[:-1])) + ' ' + format[-1]

		power = System.power(level = 1, execute = False)
		for i in power:
			i['label'] = Translation.string(i['label'])
		actions.extend(power)

		return actions

	@classmethod
	def settingsUpdate(self, settings = False):
		from lib.modules.interface import Dialog, Translation
		from lib.modules.convert import ConverterDuration

		self.tCanceled = False
		self.tChanged = False
		self.tOffset = 0
		self.tObservations = self.settings()
		self.tActions = self.settingsActions()

		def _settingsHelp():
			Dialog.details(title = 36517, items = [
				{'type' : 'title', 'value' : 'Overview', 'break' : 2},
				{'type' : 'text', 'value' : 'The [I]Observer[/I]  allows you to created observations that automatically execute specified actions after playback has finished if certain conditions have been met. Note that these automations run on a timeout, so you will still have some time to change your mind in the rating and continue dialogs. These automations are only used once playback has finished and between binging episodes, but it will not interrupt any current playback. Multiple observations can be specified which are sequentially evaluated until the first one that holds true.', 'break' : 2},
				{'type' : 'title', 'value' : 'Asleep', 'break' : 2},
				{'type' : 'text', 'value' : 'Observers are useful if, for instance, you want to automatically power down your device if you fall asleep. The [I]Asleep[/I]  option is just a predefined observation which will shut down your device during binging if you did not interact with Gaia for more than 2 hours.', 'break' : 2},
				{'type' : 'title', 'value' : 'Conditions', 'break' : 2},
				{'type' : 'text', 'value' : 'Each observation can have multiple conditions. A given observation is only executed if [B]all[/B] its conditions are met. The [I]Inactive[/I]  options are based on wether or not you interacted with Gaia. If you fall asleep and do not press any remote button while letting binging continue automatically, the inactive conditions will be triggered. If at some point in the process you press any button, the inactive conditions are reset. The following actions are considered interactions and will reset the inactive counter and duration:', 'break' : 2},
				{'type' : 'list', 'value' : [
					{'title' : 'Skip Intro', 'value' : 'Pressing the skip intro button during playback.'},
					{'title' : 'Binge Dialog', 'value' : 'Pressing any button in the binge dialog or button during playback.'},
					{'title' : 'Rating Dialog', 'value' : 'Pressing any button in the rating dialog after playback.'},
					{'title' : 'Continue Dialog', 'value' : 'Pressing any button in the continue dialog after playback.'},
					{'title' : 'Start Scrape', 'value' : 'Manually starting a new scrape.'},
					{'title' : 'Select Stream', 'value' : 'Manually selecting or otherwise interacting with the stream list.'},
				], 'number' : False},
				{'type' : 'text', 'value' : 'On the other hand, the [I]Watched[/I]  options do not consider interactions and will triggered irrespective of any button being pressed. The following conditions are available:', 'break' : 2},
				{'type' : 'list', 'value' : [
					{'title' : 36501, 'value' : 'The minimum number of episodes that have to be watched. This condition is not subject to inactivity and will be triggered whether you interact with Gaia or not.'},
					{'title' : 36502, 'value' : 'The minimum total playback duration that has to be watched. This condition is not subject to inactivity and will be triggered whether you interact with Gaia or not.'},
					{'title' : 36503, 'value' : 'The minimum number of episodes that have to be watched. This condition is only triggered if you do not interact with Gaia.'},
					{'title' : 36504, 'value' : 'The minimum total playback duration that has to be watched. This condition is only triggered if you do not interact with Gaia.'},
				], 'number' : False},
				{'type' : 'text', 'value' : 'Note that the duration is calculated as the time between starting and finishing playback, and not the actual duration of the video. For instance, if a video is 1 hour long, but you resume playback from the middle, only 30 minutes will be added to the observed duration and not the entire 1 hour.', 'break' : 2},
				{'type' : 'title', 'value' : 'Exceptions', 'break' : 2},
				{'type' : 'text', 'value' : 'Certain exception can be specified which allows the observer to execute, even if not all of the conditions are met. The following exceptions are available:', 'break' : 2},
				{'type' : 'list', 'value' : [
					{'title' : 36510, 'value' : 'Resets any previous observer info if a new show or movie is played. If [I]Disabled[/I], all episodes are evaluated for the conditions, even if they come from different shows. If [I]Enabled[/I], the conditions only apply to the binging process of the current show. If you start playing episodes from a different show, all internal counters are reset and the conditions will not take the episodes from the previous show into account.'},
					{'title' : 33316, 'value' : 'Makes an exception if it is the last available episode for binging. If [I]Disabled[/I], the action is never applied for the last episode, even if the conditions are met. If [I]Enabled[/I], the action is always applied, even if the conditions are not met. If [I]Conditional[/I], the action is only applied if the conditions are met.'},
					{'title' : 36520, 'value' : 'Also uses the observer for single standalone titles that are not part of a binging process. This can be used to also apply an observer to movies. If [I]Disabled[/I], the action is never applied for standalone titles, even if the conditions are met. If [I]Enabled[/I], the action is always applied, even if the conditions are not met. If [I]Conditional[/I], the action is only applied if the conditions are met.'},
				], 'number' : False},
				{'type' : 'title', 'value' : 'Activity', 'break' : 2},
				{'type' : 'text', 'value' : 'If all the conditions are met, or if an exception applies, certain actions can be executed. The action and timeout of an observer will overwrite any default action or timeout in the continue dialog. The following actions are available:', 'break' : 2},
				{'type' : 'list', 'value' : [
					{'title' : 35625, 'value' : 'The action that is executed if all the above conditions are met.'},
					{'title' : 36518, 'value' : 'The amount of time to wait before executing the default action.'},
					{'title' : 36516, 'value' : 'A notification is shown before the action is executed.'},
					{'title' : 36515, 'value' : 'A sound effect is played before the action is executed.'},
				], 'number' : False},
			])

		def _settingsActions():
			if self.tCanceled: return None

			items = []
			for i in range(len(self.tObservations)):
				observation = self.tObservations[i]
				count = sum([1 if j else 0 for j in [observation['condition']['watched']['counter'], observation['condition']['watched']['duration'], observation['condition']['inactive']['counter'], observation['condition']['inactive']['duration']]])
				title = '%s %s' % (Translation.string(36505), i + 1)
				value = '%s %s' % (count, Translation.string(33197 if count == 1 else 36506))
				items.append({'title' : title, 'value' : value, 'action' : _settingsUpdate, 'parameters' : {'observation' : observation}})

			return [
				{'title' : Dialog.prefixBack(33486), 'close' : True},
				{'title' : Dialog.prefixNext(33239), 'action' : _settingsHelp},
				{'title' : Dialog.prefixNext(35069), 'action' : _settingsAdd},
				{'title' : Dialog.prefixNext(36508), 'action' : _settingsAsleep},
				{'title' : Dialog.prefixNext(33013), 'action' : _settingsClear},
				{'title' : 33371, 'items' : items} if items else None,
			]

		def _settingsAction(observation):
			if self.tChanged:
				self.tChanged = False
				return None
			return [
				{'title' : Dialog.prefixBack(35374), 'close' : True},
				{'title' : Dialog.prefixNext(35406), 'action' : _settingsRemove, 'parameters' : {'observation' : observation}},
				{'title' : Dialog.prefixNext(35403), 'action' : _settingsMoveUp, 'parameters' : {'observation' : observation}},
				{'title' : Dialog.prefixNext(35404), 'action' : _settingsMoveDown, 'parameters' : {'observation' : observation}},
				{'title' : 36506, 'items' : [
					{'title' : 36501, 'value' : _settingsLabelCounter(observation['condition']['watched']), 'action' : _settingsUpdateCounter, 'parameters' : {'condition' : observation['condition']['watched'], 'title' : 36501}},
					{'title' : 36502, 'value' : _settingsLabelDuration(observation['condition']['watched']), 'action' : _settingsUpdateDuration, 'parameters' : {'condition' : observation['condition']['watched'], 'title' : 36502}},
					{'title' : 36503, 'value' : _settingsLabelCounter(observation['condition']['inactive']), 'action' : _settingsUpdateCounter, 'parameters' : {'condition' : observation['condition']['inactive'], 'title' : 36503}},
					{'title' : 36504, 'value' : _settingsLabelDuration(observation['condition']['inactive']), 'action' : _settingsUpdateDuration, 'parameters' : {'condition' : observation['condition']['inactive'], 'title' : 36504}},
				]},
				{'title' : 36509, 'items' : [
					{'title' : 36510, 'value' : _settingsLabelReset(observation), 'action' : _settingsUpdateReset, 'parameters' : {'observation' : observation}},
					{'title' : 33316, 'value' : _settingsLabelLast(observation), 'action' : _settingsUpdateLast, 'parameters' : {'observation' : observation}},
					{'title' : 36520, 'value' : _settingsLabelDiscrete(observation), 'action' : _settingsUpdateDiscrete, 'parameters' : {'observation' : observation}},
				]},
				{'title' : 36505, 'items' : [
					{'title' : 35625, 'value' : _settingsLabelAction(observation), 'action' : _settingsUpdateAction, 'parameters' : {'observation' : observation}},
					{'title' : 36518, 'value' : _settingsLabelTimeout(observation), 'action' : _settingsUpdateTimeout, 'parameters' : {'observation' : observation, 'title' : 36518}},
					{'title' : 36516, 'value' : _settingsLabelNotification(observation), 'action' : _settingsUpdateNotification, 'parameters' : {'observation' : observation}},
					{'title' : 36515, 'value' : _settingsLabelSound(observation), 'action' : _settingsUpdateSound, 'parameters' : {'observation' : observation}},
				]},
			]

		def _settingsLabelCounter(condition):
			if not condition['counter']: return Translation.string(32302)
			return str(int(condition['counter']))

		def _settingsLabelDuration(condition):
			if not condition['duration']: return Translation.string(32302)
			return ConverterDuration(value = int(condition['duration']), unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatWordShort, capitalize = True)

		def _settingsLabelReset(observation):
			return Translation.string(32301 if observation['exception']['reset'] else 32302)

		def _settingsLabelLast(observation):
			current = observation['exception']['last']
			return Translation.string(32301 if current is True else 36521 if current is None else 32302)

		def _settingsLabelDiscrete(observation):
			current = observation['exception']['discrete']
			return Translation.string(32301 if current is True else 36521 if current is None else 32302)

		def _settingsLabelAction(observation):
			if observation['activity']['action']:
				for i in self.tActions:
					if i['action'] == observation['activity']['action']:
						return Translation.string(i['label'])
			return Translation.string(32302)

		def _settingsLabelTimeout(condition):
			if not condition['activity']['timeout']: return Translation.string(32302)
			return ConverterDuration(value = int(condition['activity']['timeout']), unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatWordShort, capitalize = True)

		def _settingsLabelNotification(observation):
			return Translation.string(32301 if observation['activity']['notification'] else 32302)

		def _settingsLabelSound(observation):
			return Translation.string(32301 if observation['activity']['sound'] else 32302)

		def _settingsSave():
			label = None
			if self.tObservations:
				count = len(self.tObservations)
				label = '%d %s' % (count, Translation.string(36505 if count == 1 else 33371))
			else:
				label = Translation.string(32302)
			Settings.setData(id = Observer.Setting, value = self.tObservations, label = label)

		def _settingsOffset():
			offset = self.tOffset
			self.tOffset = 0
			return offset

		def _settingsAdd():
			observation = self.settingsDefault()
			self.tObservations.append(observation)
			_settingsUpdate(observation = observation)

		def _settingsAsleep():
			observation = self.settingsDefault()
			observation['condition']['inactive']['duration'] = 120
			observation['exception']['last'] = True
			observation['activity']['action'] = System.PowerShutdown
			self.tObservations.append(observation)

		def _settingsClear():
			self.tObservations = []

		def _settingsRemove(observation):
			self.tObservations.remove(observation)
			self.tChanged = True

		def _settingsMoveUp(observation):
			index = self.tObservations.index(observation)
			index -= 1
			self.tChanged = True
			if index >= 0:
				self.tObservations.remove(observation)
				self.tObservations.insert(index, observation)
				self.tOffset = -1

		def _settingsMoveDown(observation):
			index = self.tObservations.index(observation)
			index += 1
			self.tChanged = True
			if index < len(self.tObservations):
				self.tObservations.remove(observation)
				self.tObservations.insert(index, observation)
				self.tOffset = +1

		def _settingsUpdate(observation):
			choice = Dialog.information(title = 36517, refresh = lambda : _settingsAction(observation), reselect = Dialog.ReselectYes)
			if choice == -1: self.tCanceled = True

		def _settingsUpdateCounter(condition, title):
			value = Dialog.input(type = Dialog.InputNumeric, title = title, default = condition['counter'])
			condition['counter'] = int(value) if value else None

		def _settingsUpdateDuration(condition, title):
			value = Dialog.input(type = Dialog.InputNumeric, title = title, default = int(condition['duration'] / 60.0) if condition['duration'] else None)
			condition['duration'] = int(value * 60) if value else None

		def _settingsUpdateReset(observation):
			observation['exception']['reset'] = not observation['exception']['reset']

		def _settingsUpdateLast(observation):
			current = new = observation['exception']['last']
			if current is False: new = None
			elif current is None: new = True
			else: new = False
			observation['exception']['last'] = new

		def _settingsUpdateDiscrete(observation):
			current = new = observation['exception']['discrete']
			if current is False: new = None
			elif current is None: new = True
			else: new = False
			observation['exception']['discrete'] = new

		def _settingsUpdateAction(observation):
			selection = None
			if observation['activity']['action']:
				for i in self.tActions:
					if i['action'] == observation['activity']['action']:
						selection = i['format']
						break
			choice = Dialog.select(title = 36505, items = [i['format'] for i in self.tActions], selection = selection)
			if choice is None or choice < 0: return None
			observation['activity']['action'] = self.tActions[choice]['action']

		def _settingsUpdateTimeout(observation, title):
			value = Dialog.input(type = Dialog.InputNumeric, title = title, default = int(observation['activity']['timeout']) if observation['activity']['timeout'] else None)
			observation['activity']['timeout'] = int(value) if value else None

		def _settingsUpdateNotification(observation):
			observation['activity']['notification'] = not observation['activity']['notification']

		def _settingsUpdateSound(observation):
			observation['activity']['sound'] = not observation['activity']['sound']

		Dialog.information(title = 36517, refresh = _settingsActions, reselect = Dialog.ReselectYes, offset = _settingsOffset)
		_settingsSave()

		if settings: Settings.launchData(id = Observer.Setting)

###################################################################
# ANNOUNCEMENT
###################################################################

class Announcements(object):

	# Minimum free storage space required by Gaia to function correctly.
	# Gaia needs about 50MB for all its files in "addon_data", excluding the "Downloads", "Library", and "Backup" directories.
	# Do not make this value too large (eg: 200MB), since it is only the current free disk space required, and already includes the sizes of the current files.
	# This value should only represent the maximum space required for the next session until Gaia/Kodi restarts (eg: the additional space required for an increse in size of cache.db, or temporary torrent or NZB container downloads).
	# Do not make this value too small, since other addons/Kodi/OS might also fill up the space during the session.
	StorageMinimum = 104857600 # 100 MB. After which a notification is shown.
	StorageRecommended = 262144000 # 250 MB. After using Gaia for a few months, databases are around 500-600MB in total. Around 250MB is about the minimum these databases should have available for the addon to function correctly.

	@classmethod
	def enabled(self):
		return Settings.getBoolean('general.announcement.enabled')

	@classmethod
	def enabledPublic(self):
		return self.enabled() and Settings.getBoolean('general.announcement.public')

	@classmethod
	def enabledPrivate(self):
		return self.enabled() and Settings.getBoolean('general.announcement.private')

	@classmethod
	def enabledChangelog(self):
		return self.enabled() and Settings.getBoolean('general.announcement.changelog')

	@classmethod
	def show(self, force = False, version = None, wait = False, sleep = False):
		if force or self.enabledPublic() or (version and self.enabledChangelog()):
			thread = Pool.thread(target = self._show, kwargs = {'force' : force, 'version' : version, 'sleep' : sleep}, start = True)
			if wait: thread.join()

	@classmethod
	def _show(self, force = False, version = None, sleep = False):
		try:
			from lib.modules import api
			from lib.modules import interface

			if sleep: Time.sleep(1.5) # Wait a bit so that everything has been loaded.

			message = []
			result = None
			newline = interface.Format.newline() * 2

			if force:
				interface.Loader.show()
				last = Time.past(days = 365)
				result = api.Api.announcement(last = last, version = System.version(), count = 5)
			elif self.enabledPublic():
				last = Settings.getInteger('internal.announcement')
				if not last: last = Time.past(days = 14) # Make sure Gaia 6 does not retrieve old Gaia 5 announcements. Also limits old announcements if the user newley installs Gaia.
				result = api.Api.announcement(last = last, version = System.version(), count = 5)

			if result:
				if Tools.isDictionary(result): result = [result]
				if not force: Settings.set('internal.announcement', max(i['time']['added'] for i in result))

				title = interface.Translation.string(33962)
				color = interface.Format.colorSecondary()
				text = [interface.Format.font('%s (%s)' % (title, Time.format(i['time']['added'], format = Time.FormatDate)), bold = True, color = color) + newline + i['message']['format'] for i in result]
				text = interface.Format.font(35277, bold = True, color = interface.Format.colorPrimary(), uppercase = True) + newline + newline.join(text)

				'''single = len(result) == 1
				mode = result[0]['mode'] if single else 'page'
				if mode == 'dialog': interface.Dialog.confirm(title = 33962, message = text)
				elif mode == 'splash': interface.Splash.popupMessage(message = text)
				elif mode == 'page': interface.Dialog.text(title = 33962, message = text)'''

				message.append(text)

			if version and self.enabledChangelog():
				changelog = Changelog.extract(limit = 5, version = version, format = True)
				if changelog: message.append(interface.Format.font(35331, bold = True, color = interface.Format.colorPrimary(), uppercase = True) + newline + changelog)

			if message: interface.Dialog.text(title = 35201, message = (interface.Format.newline() * 3).join(message))

			if force:
				if not message: interface.Dialog.notification(title = 35201, message = 33992, icon = interface.Dialog.IconInformation)
				interface.Loader.hide()
		except: Logger.error()

	@classmethod
	def storage(self, wait = False, sleep = False):
		if self.enabledPrivate():
			thread = Pool.thread(target = self._storage, args = (sleep,))
			thread.start()
			if wait: thread.join()

	@classmethod
	def _storage(self, sleep = False):
		if sleep: Time.sleep(2) # Wait a bit so that everything has been loaded.
		free = Hardware.storageUsageFreeBytes()
		if free < Announcements.StorageMinimum:
			from lib.modules.interface import Translation, Dialog
			from lib.modules.convert import ConverterSize
			message = Translation.string(35279) % (ConverterSize(free).stringOptimal(), ConverterSize(Announcements.StorageRecommended).stringOptimal())
			Dialog.confirm(title = 35280, message = message)
		else:
			from lib.modules.database import Dummy
			if not Dummy().test():
				from lib.modules.interface import Dialog
				Dialog.confirm(title = 36044, message = 36045)

###################################################################
# CHANGELOG
###################################################################

class Changelog(object):

	@classmethod
	def extract(self, limit = None, version = None, format = False):
		from lib.modules.interface import Translation, Format

		result = []
		if version and Tools.isString(version): version = System.versionNumber(version = version)

		data = File.readNow(File.joinPath(System.path(), 'changelog.txt'))
		if data:
			releases = Regex.extract(data = data, expression = '\[B\](\d+\.\d+\.\d+).*?\((.*?)\)\s*\[\/B]\s*(.*?)\s*\n{2,}', all = True, group = None, flags = Regex.FlagCaseInsensitive | Regex.FlagAllLines)
			if releases:
				for release in releases:
					if not version or System.versionNumber(version = release[0]) > version:
						result.append({'version' : release[0], 'date' : release[1], 'data' : release[2]})
				if limit: result = result[:limit]

		if format:
			newline = Format.newline()
			color = Format.colorSecondary()
			title = Translation.string(33359)
			text = []
			for release in result:
				text.append(Format.font('%s %s (%s)' % (title, release['version'], release['date']), bold = True, color = color) + newline + release['data'])
			result = (newline * 2).join(text)

		return result

	@classmethod
	def show(self, limit = None, version = None, format = True):
		from lib.modules.interface import Dialog
		Dialog.text(title = 33503, message = self.extract(limit = limit, version = version, format = format))

###################################################################
# PROMOTIONS
###################################################################

class Promotions(object):

	Cache = None
	OrionAnonymous = 'orionanonymous'

	@classmethod
	def update(self, wait = False, refresh = True):
		thread = Pool.thread(target = self._update, args = (refresh,))
		thread.start()

	@classmethod
	def _update(self, refresh = True):
		try:
			from lib.modules.api import Api
			self._cache()
			enabled = self.enabled()
			result = []
			promotions = Api.promotion()
			for i in promotions:
				i['viewed'] = False
				for j in Promotions.Cache:
					if i['id'] == j['id']:
						i['viewed'] = j['viewed']
						break
				result.append(i)
			self._cacheUpdate(result)
			if refresh and self.enabled() and not enabled:
				from lib.modules import interface
				interface.Directory.refresh(clear = True)
		except: pass

	@classmethod
	def _cache(self):
		if Promotions.Cache is None: Promotions.Cache = Settings.getList('internal.promotions')
		return Promotions.Cache

	@classmethod
	def _cacheUpdate(self, data = None):
		if not data is None: Promotions.Cache = data
		Settings.set('internal.promotions', Promotions.Cache)

	@classmethod
	def _fixed(self):
		try:
			from lib.modules.interface import Translation
			from lib.modules.orionoid import Orionoid
			orion = Orionoid()
			return [{
				'id' : Promotions.OrionAnonymous,
				'viewed' : not orion.accountPromotionEnabled(),
				'provider' : 'Orion',
				'start' : Time.timestamp(),
				'expiration' : None,
				'title' : Translation.string(35428),
			}]
		except: Logger.error()

	@classmethod
	def enabled(self):
		try:
			from lib.modules import orionoid
			if not Settings.getBoolean('menu.main.promotion'): return False
			elif orionoid.Orionoid().accountPromotionEnabled(): return True
			current = Time.timestamp()
			for i in self._cache():
				if not i['viewed'] and (i['expiration'] is None or i['expiration'] > current):
					return True
		except: Logger.error()
		return False

	@classmethod
	def menu(self, force = False):
		from lib.modules.interface import Loader, Dialog, Directory, Icon

		if force:
			Loader.show()
			self.update(wait = True, refresh = False)
			Loader.hide()
		elif not Settings.getBoolean('internal.initial.promotions'):
			Settings.set('internal.initial.promotions', True)
			Dialog.confirm(title = 35442, message = 35445)

		items = []
		promotions = [i['provider'] for i in self._fixed()]
		lower = []
		for i in self._cache():
			if not i['provider'] in promotions:
				promotions.append(i['provider'])
				lower.append(i['provider'].lower())

		if len(promotions) == 0:
			Dialog.notification(title = 35443, message = 35444, icon = Dialog.IconNativeInformation)
		else:
			# Use a specific order.
			for i in ['orion', 'premiumize', 'offcloud', 'realdebrid']:
				try:
					i = lower.index(i)
					items.append(promotions[i])
					del promotions[i]
					del lower[i]
				except: pass
			items.extend(promotions)

			directory = Directory()
			for i in items: directory.add(label = i, action = 'promotionsSelect', parameters = {'provider' : i}, icon = '%s.png' % (i.lower() if Icon.exists(i.lower()) else 'promotion'), iconDefault = 'DefaultAddonProgram.png')
			directory.finish()

	@classmethod
	def select(self, provider):
		from lib.modules.interface import Translation, Format, Dialog
		from lib.modules.convert import ConverterDuration, ConverterTime

		current = Time.timestamp()
		promotions = []
		items = Tools.copy(self._cache()) # Deep copy because we append Orion.

		if provider.lower() == 'orion':
			items.extend(self._fixed())

		for i in items:
			if i['provider'].lower() == provider.lower():
				if i['expiration']:
					timer = i['expiration'] - current
					if timer < 0: continue
					timer = ConverterDuration(value = timer, unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatWordMinimal).title()
					timer += ' ' + Translation.string(35449)
				else:
					timer = Translation.string(35446)
				status = Translation.string(35448 if i['viewed'] else 35447)
				status = '[%s]' % status
				status = Format.font(status, bold = True, color = Format.colorPoor() if i['viewed'] else Format.colorExcellent())
				promotions.append({
					'id' : i['id'],
					'title' : '%s %s: %s' % (status, i['title'], timer),
					'time' : i['start'],
				})
		promotions = sorted(promotions, key = lambda i : i['time'], reverse = True)

		choice = Dialog.select(title = provider + ' ' + Translation.string(provider), items = [i['title'] for i in promotions])
		if choice >= 0:
			choice = promotions[choice]['id']
			if choice == Promotions.OrionAnonymous:
				try:
					from lib.modules.orionoid import Orionoid
					Orionoid().accountPromotion()
				except: Logger.error()
			else:
				for i in range(len(Promotions.Cache)):
					if Promotions.Cache[i]['id'] == choice:
						Promotions.Cache[i]['viewed'] = True
						self._cacheUpdate()
						message = Format.fontBold(Promotions.Cache[i]['title']) + Format.newline()
						if Promotions.Cache[i]['expiration']: message += Format.newline() + Format.fontBold('Expiration: ') + ConverterTime(Promotions.Cache[i]['expiration']).string(format = ConverterTime.FormatDateTime)
						if Promotions.Cache[i]['link']: message += Format.newline() + inteace.Format.fontBold('Link: ') + Format.fontItalic(Promotions.Cache[i]['link'])
						if Promotions.Cache[i]['expiration'] or Promotions.Cache[i]['link']: message += Format.newline()
						message += Format.newline() + Promotions.Cache[i]['description'] + Format.newline()
						Dialog.text(title = Promotions.Cache[i]['provider'] +' ' + interfe.Translation.string(35442), message = message)
						break

###################################################################
# BUFFER
###################################################################

class Buffer(object):

	@classmethod
	def settings(self, settings = False):
		from lib.modules.interface import Dialog, Translation
		from lib.modules.convert import ConverterSize

		default = 20971520 # Kodi's default buffer size of 20MB (60MB of memory).
		multiplier = 3.0 # Kodi requires free memory of 3x the size of the buffer.
		factor = 20 # Kodi's buffer "fill" factor. Seems like a good value from the examples.
		memory = Hardware.memory()
		comment = ' <!-- GAIA - Added By Gaia Settings -> %s -> %s. -->' % (Translation.string(32330), Translation.string(33264))

		currentPercent = 0.5
		currentMemory = int(memory['usage']['free']['bytes'] * currentPercent)
		currentBuffer = int(currentMemory / multiplier)

		cache = None
		data = None
		flags = Regex.FlagCaseInsensitive | Regex.FlagAllLines
		if File.exists(System.AdvancedSettings):
			data = File.readNow(System.AdvancedSettings)
			extract = Regex.extract(data = data, expression = '(<cache>.*?<\/cache>)', flags = flags)
			if extract:
				cache = extract
				extract = Regex.extract(data = cache, expression = '<memorysize>(.*?)<\/memorysize>', flags = flags)
				if extract:
					try:
						currentBuffer = int(extract)
						currentMemory = int(currentBuffer * multiplier)
						currentPercent = currentMemory / float(memory['usage']['free']['bytes'])
					except: Logger.error()

		Dialog.text(title = 33262, message = 36191)

		if cache:
			message = Translation.string(36187) % (ConverterSize(currentBuffer).stringOptimal(), ConverterSize(currentMemory).stringOptimal(), int(currentPercent * 100), memory['usage']['free']['label'], memory['usage']['total']['label'])
			choice = Dialog.options(title = 33262, message = message, labelConfirm = 33743, labelDeny = 33925, labelCustom = 35479)
			if choice == Dialog.ChoiceCanceled or choice == Dialog.ChoiceYes:
				return self._settingsResult(result = False, settings = settings)
			elif choice == Dialog.ChoiceCustom:
				data = Regex.remove(data = data, expression = '(\n?\s*<cache>.*?<\/cache>)', flags = flags, all = True)
				if File.writeNow(System.AdvancedSettings, data):
					data = File.readNow(System.AdvancedSettings)
					if '<cache>' in data and '<memorysize>' in data:
						Dialog.confirm(title = 33262, message = 36189)
						return self._settingsResult(result = False, settings = settings)
					else:
						Dialog.confirm(title = 33262, message = 36190)
						return self._settingsResult(result = True, settings = settings)

		while True:
			newPercent = None
			newMemory = None
			newBuffer = None

			choice = Dialog.options(title = 33262, message = 36180, labelConfirm = 33743, labelDeny = 33348, labelCustom = 33383)
			if choice == Dialog.ChoiceCanceled or choice == Dialog.ChoiceYes:
				return self._settingsResult(result = False, settings = settings)
			elif choice == Dialog.ChoiceNo:
				newPercent = Dialog.input(title = 33262, type = Dialog.InputNumeric, default = int(currentPercent * 100))
				if not newPercent: continue
				newPercent /= 100.0
			elif choice == Dialog.ChoiceCustom:
				newBuffer = Dialog.input(title = 33262, type = Dialog.InputNumeric, default = Math.roundClosest(value = (currentBuffer / 1048576), base = 10))
				if not newBuffer: continue
				newBuffer *= 1048576

			if newBuffer:
				newBuffer = int(max(0, min(max(memory['usage']['free']['bytes'], (memory['usage']['total']['bytes'] * 0.85)) / multiplier, newBuffer)))
				newMemory = int(newBuffer * multiplier)
				newPercent = newMemory / float(memory['usage']['free']['bytes'])
			elif newPercent:
				newPercent = max(0, min(1, newPercent))
				newMemory = int(memory['usage']['free']['bytes'] * newPercent)
				newBuffer = int(newMemory / multiplier)

			if newBuffer < default: message = 36182
			elif newPercent <= 0.55: message = 36183
			elif newPercent <= 0.75: message = 36184
			elif newPercent <= 0.95: message = 36185
			else: message = 36186
			message = Translation.string(36181) % (ConverterSize(newBuffer).stringOptimal(), ConverterSize(newMemory).stringOptimal(), int(newPercent * 100), memory['usage']['free']['label'], memory['usage']['total']['label'], Translation.string(message))

			choice = Dialog.options(title = 33262, message = message, labelConfirm = 33743, labelDeny = 33926, labelCustom = 33925)
			if choice == Dialog.ChoiceCanceled or choice == Dialog.ChoiceYes:
				return self._settingsResult(result = False, settings = settings)
			elif choice == Dialog.ChoiceNo:
				cache = '\n\t<cache>\n\t\t<buffermode>1</buffermode>%s\n\t\t<memorysize>%d</memorysize>%s\n\t\t<readfactor>%d</readfactor>%s\n\t</cache>\n' % (comment, newBuffer, comment, factor, comment)
				if not data or not '</advancedsettings>' in data: data = '<advancedsettings></advancedsettings>'
				data = Regex.remove(data = data, expression = '(\n?\s*<cache>.*?<\/cache>)', flags = flags, all = True)
				data = data.replace('</advancedsettings>', cache + '</advancedsettings>')
				if File.writeNow(System.AdvancedSettings, data):
					if ('<memorysize>%d</memorysize>' % newBuffer) in File.readNow(System.AdvancedSettings):
						Dialog.confirm(title = 33262, message = 36188)
						return self._settingsResult(result = newBuffer, settings = settings)
				Dialog.confirm(title = 33262, message = 36189)
				return self._settingsResult(result = False, settings = settings)
			elif choice == Dialog.ChoiceCustom:
				continue

		return self._settingsResult(result = False, settings = settings)

	@classmethod
	def _settingsResult(self, result, settings = False):
		from lib.modules.convert import ConverterSize
		id = 'playback.buffer.size'
		if result is True: Settings.default(id = id) # Reset
		elif result: Settings.set(id = id, value = ConverterSize(result).stringOptimal())
		if settings: Settings.launch(id = id)
		return bool(result)

	@classmethod
	def initialize(self):
		result = True

		if File.exists(System.AdvancedSettings):
			flags = Regex.FlagCaseInsensitive | Regex.FlagAllLines
			data = File.readNow(System.AdvancedSettings)
			extract = Regex.extract(data = data, expression = '(<cache>.*?<\/cache>)', flags = flags)
			if extract:
				extract = Regex.extract(data = extract, expression = '<memorysize>(.*?)<\/memorysize>', flags = flags)
				if extract:
					try: result = int(extract)
					except: Logger.error()

		return self._settingsResult(result)

###################################################################
# TIMEOUT
###################################################################

class Timeout(object):

	Default = 30 # Kodi's default cURL timeout seems to be 30 secconds.

	@classmethod
	def settings(self, settings = False):
		from lib.modules.interface import Dialog, Translation
		from lib.modules.convert import ConverterDuration

		current = Timeout.Default
		comment = ' <!-- GAIA - Added By Gaia Settings -> %s -> %s. -->' % (Translation.string(32330), Translation.string(35003))

		found = False
		network = None
		data = None
		flags = Regex.FlagCaseInsensitive | Regex.FlagAllLines
		if File.exists(System.AdvancedSettings):
			data = File.readNow(System.AdvancedSettings)
			extract = Regex.extract(data = data, expression = '(<network>.*?<\/network>)', flags = flags)
			if extract:
				network = extract
				extract = Regex.extract(data = network, expression = '<curlclienttimeout>(.*?)<\/curlclienttimeout>', flags = flags)
				if extract:
					try:
						current = int(extract)
						found = True
					except: Logger.error()

		Dialog.text(title = 35003, message = 32019)

		if found:
			message = Translation.string(32020) % ConverterDuration(current, unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatWordShort)
			choice = Dialog.options(title = 35003, message = message, labelConfirm = 33743, labelDeny = 33925, labelCustom = 35479)
			if choice == Dialog.ChoiceCanceled or choice == Dialog.ChoiceYes:
				return self._settingsResult(result = False, settings = settings)
			elif choice == Dialog.ChoiceCustom:
				data = Regex.remove(data = data, expression = '(\n?\s*<curlclienttimeout>.*?<\/curlclienttimeout>(?:\s*<!--.*?-->)?)', flags = flags, all = True)
				if File.writeNow(System.AdvancedSettings, data):
					data = File.readNow(System.AdvancedSettings)
					if '<network>' in data and '<curlclienttimeout>' in data:
						Dialog.confirm(title = 35003, message = 32021)
						return self._settingsResult(result = False, settings = settings)
					else:
						Dialog.confirm(title = 35003, message = 32022)
						return self._settingsResult(result = True, settings = settings)

		while True:
			new = Dialog.input(title = 35003, type = Dialog.InputNumeric, default = current)
			message = Translation.string(32023) % ConverterDuration(new, unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatWordShort)
			choice = Dialog.options(title = 35003, message = message, labelConfirm = 33743, labelDeny = 33926, labelCustom = 33925)
			if choice == Dialog.ChoiceCanceled or choice == Dialog.ChoiceYes:
				return self._settingsResult(result = False, settings = settings)
			elif choice == Dialog.ChoiceNo:
				if not new:
					data = Regex.remove(data = data, expression = '(\n?\s*<curlclienttimeout>.*?<\/curlclienttimeout>(?:\s*<!--.*?-->)?)', flags = flags, all = True)
					if File.writeNow(System.AdvancedSettings, data):
						data = File.readNow(System.AdvancedSettings)
						if '<network>' in data and '<curlclienttimeout>' in data:
							Dialog.confirm(title = 35003, message = 32021)
							return self._settingsResult(result = False, settings = settings)
						else:
							Dialog.confirm(title = 35003, message = 32022)
							return self._settingsResult(result = True, settings = settings)

				if network:
					network = Regex.remove(data = network, expression = '(\n?\s*<curlclienttimeout>.*?<\/curlclienttimeout>(?:\s*<!--.*?-->)?)', flags = flags, all = True)
					network = network.replace('</network>', '\t<curlclienttimeout>%d</curlclienttimeout>%s\n\t</network>' % (new, comment))
				else:
					network = '<network>\n\t\t<curlclienttimeout>%d</curlclienttimeout>%s\n\t</network>\n' % (new, comment)

				if not data or not '</advancedsettings>' in data: data = '<advancedsettings></advancedsettings>'
				data = Regex.remove(data = data, expression = '(\n?\s*<network>.*?<\/network>)', flags = flags, all = True)
				data = data.replace('</advancedsettings>', '\n\t' + network + '\n</advancedsettings>')
				if File.writeNow(System.AdvancedSettings, data):
					if ('<curlclienttimeout>%d</curlclienttimeout>' % new) in File.readNow(System.AdvancedSettings):
						Dialog.confirm(title = 35003, message = 32024)
						return self._settingsResult(result = new, settings = settings)
				Dialog.confirm(title = 35003, message = 32021)
				return self._settingsResult(result = False, settings = settings)
			elif choice == Dialog.ChoiceCustom:
				continue

		return self._settingsResult(result = False, settings = settings)

	@classmethod
	def _settingsResult(self, result, settings = False):
		from lib.modules.convert import ConverterDuration
		id = 'playback.time.connection'
		if result is True: Settings.default(id = id) # Reset
		elif result: Settings.set(id = id, value = ConverterDuration(result, unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatAbbreviationShort, capitalize = True))
		if settings: Settings.launch(id = id)
		return bool(result)

	@classmethod
	def initialize(self):
		result = True

		if File.exists(System.AdvancedSettings):
			flags = Regex.FlagCaseInsensitive | Regex.FlagAllLines
			data = File.readNow(System.AdvancedSettings)
			extract = Regex.extract(data = data, expression = '(<network>.*?<\/network>)', flags = flags)
			if extract:
				extract = Regex.extract(data = extract, expression = '<curlclienttimeout>(.*?)<\/curlclienttimeout>', flags = flags)
				if extract:
					try: result = int(extract)
					except: Logger.error()

		return self._settingsResult(result)

###################################################################
# LINK
###################################################################

class Link(object):

	TypeImdb			= 'imdb'
	TypeTmdb			= 'tmdb'
	TypeTvdb			= 'tvdb'
	TypeTrakt			= 'trakt'

	TypeSimkl			= 'simkl'
	TypeTvmaze			= 'tvmaze'
	TypeTomatoes		= 'tomatoes'
	TypeMetacritic		= 'metacritic'
	TypeCommonsense		= 'commonsense'
	TypeLetterboxd		= 'letterboxd'
	TypeCriticker		= 'criticker'

	TypeFanart			= 'fanart'
	TypeHome			= 'home'
	TypeTrailer			= 'trailer'
	TypeGoogle			= 'google'
	TypeDuckduckgo		= 'duckduckgo'

	@classmethod
	def _slug(self, title, year = None, separator = '-', symbol = None, lower = True):
		from lib.meta.tools import MetaTools
		return MetaTools.slug(title = title, year = year, separator = separator, symbol = symbol, lower = lower)

	@classmethod
	def _test(self, link):
		from lib.modules.network import Networker
		return Networker().requestSuccess(link = link)

	@classmethod
	def _query(self, query, plus = False):
		from lib.modules.network import Networker
		return Networker.linkQuote(data = query, plus = plus)

	@classmethod
	def _extract(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, slug = None, title = None, year = None, season = None, episode = None, metadata = None):
		if not metadata:
			from lib.meta.manager import MetaManager
			metadata = MetaManager.instance().metadata(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, episode = episode, pack = False)

		if metadata:
			if not media:
				if 'tvshowtitle' in metadata:
					if 'episode' in metadata: media = Media.Episode
					elif 'season' in metadata: media = Media.Season
					else: media = Media.Show
				elif 'set' in metadata and not 'collection' in metadata:
					media = Media.Set
				else:
					media = Media.Movie

			if not imdb and 'id' in metadata and 'imdb' in metadata['id']: imdb = metadata['id']['imdb']
			if not tmdb and 'id' in metadata and 'tmdb' in metadata['id']: tmdb = metadata['id']['tmdb']
			if not tvdb and 'id' in metadata and 'tvdb' in metadata['id']: tvdb = metadata['id']['tvdb']
			if not trakt and 'id' in metadata and 'trakt' in metadata['id']: trakt = metadata['id']['trakt']
			if not slug and 'id' in metadata and 'slug' in metadata['id']: slug = metadata['id']['slug']

			if not title and media == Media.Set and 'collection' in metadata and 'title' in metadata['collection']: title = metadata['collection']['title']
			if not title and 'tvshowtitle' in metadata: title = metadata['tvshowtitle']
			if not title and 'title' in metadata: title = metadata['title']
			if not year and 'year' in metadata: year = metadata['year']

			if season is None and 'season' in metadata: season = metadata['season']
			if episode is None and 'episode' in metadata: episode = metadata['episode']

		if media == Media.Show:
			episode = None
			season = None
		elif media == Media.Season:
			episode = None

		return {
			'media' : media,
			'imdb' : imdb,
			'tmdb' : tmdb,
			'tvdb' : tvdb,
			'trakt' : trakt,
			'slug' : slug,
			'title' : title,
			'year' : year,
			'season' : season,
			'episode' : episode,
			'metadata' : metadata,
		}

	@classmethod
	def qr(self, type = None, media = None, id = None, imdb = None, tmdb = None, tvdb = None, trakt = None, slug = None, title = None, year = None, season = None, episode = None, metadata = None, query = None, search = False, test = False, fallback = False, loader = True, notification = True, overlay = True, wait = False):
		from lib.modules.interface import Dialog, Translation, Format, Loader
		from lib.modules.window import WindowQr
		if loader: Loader.show()

		data = self._extract(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, slug = slug, title = title, year = year, season = season, episode = episode, metadata = metadata)
		metadata = data.get('metadata')

		if data['media'] == Media.Set:
			types = [
				{'type' : Link.TypeTmdb,		'name' : 33508,	'condition' : bool(data['tmdb'])},
				{'type' : Link.TypeGoogle,		'name' : 36414,	'condition' : bool(data['title'])},
				{'type' : Link.TypeDuckduckgo,	'name' : 36487,	'condition' : bool(data['title'])},
			]
		else:
			types = [
				{'type' : Link.TypeTrakt,		'name' : 32315,	'condition' : bool(data['trakt'] or data['slug'] or data['title'])},
				{'type' : Link.TypeImdb,		'name' : 32034,	'condition' : bool(data['imdb'] or data['title'])},
				{'type' : Link.TypeTmdb,		'name' : 33508,	'condition' : bool(data['tmdb'] or data['title'])},
				{'type' : Link.TypeTvdb,		'name' : 35668,	'condition' : bool(data['tvdb'] or data['title'])},

				{'type' : Link.TypeSimkl,		'name' : 36473,	'condition' : bool(data['imdb'] or data['tmdb'] or data['tvdb'] or data['title'])},
				{'type' : Link.TypeTvmaze,		'name' : 35669,	'condition' : bool(Media.isSerie(data['media']) and data['title'])},
				{'type' : Link.TypeTomatoes,	'name' : 36474,	'condition' : bool(data['title'])},
				{'type' : Link.TypeMetacritic,	'name' : 35719,	'condition' : bool(data['title'])},
				{'type' : Link.TypeCommonsense,	'name' : 36475,	'condition' : bool(data['title'])},
				{'type' : Link.TypeLetterboxd,	'name' : 36476,	'condition' : bool(Media.isFilm(data['media']) and data['title'])},
				{'type' : Link.TypeCriticker,	'name' : 36477,	'condition' : bool(data['title'])},

				{'type' : Link.TypeFanart,		'name' : 35260,	'condition' : bool(data['tmdb'] or data['tvdb'] or data['title'])},
				{'type' : Link.TypeHome,		'name' : 36413,	'condition' : bool((metadata and 'homepage' in metadata and metadata['homepage']) or data['title'])},
				{'type' : Link.TypeTrailer,		'name' : 35536,	'condition' : bool((metadata and 'trailer' in metadata and metadata['trailer']) or data['title'])},
				{'type' : Link.TypeGoogle,		'name' : 36414,	'condition' : bool(data['title'])},
				{'type' : Link.TypeDuckduckgo,	'name' : 36487,	'condition' : bool(data['title'])},
			]
		display = [i for i in types if i['condition']]

		if type is None:
			label = Translation.string(33058)
			choice = Dialog.select(title = 33381, items = [label % Format.fontBold(i['name']) for i in display])
			if not(choice is None or choice is False or choice < 0): type = display[choice]['type']

		if type:
			link = self.link(type = type, media = media, id = id, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, slug = slug, title = title, year = year, season = season, episode = episode, metadata = metadata, search = search, test = test)
			if link:
				WindowQr.show(link = link, overlay = overlay, wait = wait)
				return True
			else:
				if notification:
					message = Translation.string(36478)
					name = None
					for i in types:
						if i['type'] == type:
							name = i['name']
							break
					if name: message = Format.fontBold(name) + ' ' + message
					Dialog.notification(title = 33381, message = message, icon = Dialog.IconWarning)
				if fallback:
					link = self.link(type = Link.TypeGoogle if fallback is True else fallback, media = media, id = id, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, slug = slug, title = title, year = year, season = season, episode = episode, metadata = metadata, search = search, test = test)
					if link:
						WindowQr.show(link = link, overlay = overlay, wait = wait)
						return True

		if loader: Loader.hide()
		return False

	@classmethod
	def link(self, type, media = None, id = None, imdb = None, tmdb = None, tvdb = None, trakt = None, slug = None, title = None, year = None, season = None, episode = None, metadata = None, query = None, search = False, test = False):
		if type == Link.TypeImdb: return self.linkImdb(media = media, id = id, imdb = imdb, title = title, year = year, season = season, metadata = metadata, search = search)
		elif type == Link.TypeTmdb: return self.linkTmdb(media = media, id = id, tmdb = tmdb, title = title, year = year, season = season, episode = episode, metadata = metadata, search = search)
		elif type == Link.TypeTvdb: return self.linkTvdb(media = media, id = id, tvdb = tvdb, slug = slug, title = title, year = year, season = season, metadata = metadata, search = search, test = test)
		elif type == Link.TypeTrakt: return self.linkTrakt(media = media, id = id, imdb = imdb, trakt = trakt, slug = slug, title = title, year = year, season = season, episode = episode, metadata = metadata, search = search, test = test)

		elif type == Link.TypeSimkl: return self.linkSimkl(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, slug = slug, title = title, year = year, season = season, episode = episode, metadata = metadata, search = search)
		elif type == Link.TypeTvmaze: return self.linkTvmaze(media = media, title = title, metadata = metadata, search = search)
		elif type == Link.TypeTomatoes: return self.linkTomatoes(media = media, title = title, year = year, season = season, episode = episode, metadata = metadata, search = search, test = test)
		elif type == Link.TypeMetacritic: return self.linkMetacritic(media = media, title = title, season = season, metadata = metadata, search = search, test = test)
		elif type == Link.TypeCommonsense: return self.linkCommonsense(media = media, title = title, metadata = metadata, search = search, test = test)
		elif type == Link.TypeLetterboxd: return self.linkLetterboxd(media = media, title = title, year = year, metadata = metadata, search = search, test = test)
		elif type == Link.TypeCriticker: return self.linkCriticker(media = media, title = title, year = year, season = season, metadata = metadata, search = search, test = test)

		elif type == Link.TypeFanart: return self.linkFanart(media = media, tmdb = tmdb, tvdb = tvdb, title = title, metadata = metadata, search = search)
		elif type == Link.TypeHome: return self.linkHome(media = media, title = title, year = year, metadata = metadata, search = search)
		elif type == Link.TypeTrailer: return self.linkTrailer(media = media, title = title, year = year, metadata = metadata, search = search)
		elif type == Link.TypeGoogle: return self.linkGoogle(media = media, title = title, year = year, season = season, episode = episode, metadata = metadata, query = query, search = search)
		elif type == Link.TypeDuckduckgo: return self.linkDuckduckgo(media = media, title = title, year = year, season = season, episode = episode, metadata = metadata, query = query, search = search)

	@classmethod
	def linkImdb(self, media = None, id = None, imdb = None, title = None, year = None, season = None, metadata = None, search = False):
		from lib.meta.providers.imdb import MetaImdb
		return MetaImdb.link(media = media, id = imdb or id, title = title, year = year, season = season, metadata = metadata, search = search)

	@classmethod
	def linkTmdb(self, media = None, id = None, tmdb = None, title = None, year = None, season = None, episode = None, metadata = None, search = False):
		from lib.meta.providers.tmdb import MetaTmdb
		return MetaTmdb.link(media = media, id = tmdb or id, title = title, year = year, season = season, episode = episode, metadata = metadata, search = search)

	@classmethod
	def linkTvdb(self, media = None, id = None, tvdb = None, slug = None, title = None, year = None, season = None, metadata = None, search = False, test = False):
		from lib.meta.services.tvdb import MetaTvdb
		return MetaTvdb.link(media = media, id = tvdb or id, slug = slug, title = title, year = year, season = season, metadata = metadata, search = search, test = test)

	@classmethod
	def linkTrakt(self, media = None, id = None, imdb = None, trakt = None, slug = None, title = None, year = None, season = None, episode = None, metadata = None, search = False, test = False):
		from lib.meta.providers.trakt import MetaTrakt
		return MetaTrakt.link(media = media, id = trakt or imdb or id, slug = slug, title = title, year = year, season = season, episode = episode, metadata = metadata, search = search, test = test)

	@classmethod
	def linkSimkl(self, media = None, imdb = None, tmdb = None, tvdb = None, slug = None, title = None, year = None, season = None, episode = None, metadata = None, search = False):
		data = self._extract(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, slug = slug, title = title, year = year, season = season, episode = episode, metadata = metadata)
		if data:
			link = 'https://api.simkl.com/redirect?to=Simkl'
			if data['media']: link += '&type=' + ('show' if Media.isSerie(data['media']) else 'movie')
			if data['imdb']: link += '&imdb=' + data['imdb']
			elif data['tmdb']: link += '&tmdb=' + data['tmdb']
			elif data['tvdb']: link += '&tvdb=' + data['tvdb']
			elif data['slug']: link += '&traktslug=' + data['slug']
			else:
				if data['title']: link += '&title=' + data['title']
				else: return None
				if data['year']: link += '&year=' + str(data['year'])
			if not data['season'] is None: link += '&season=' + str(data['season'])
			if not data['episode'] is None: link += '&episode=' + str(data['episode'])
			return link
		return None

	@classmethod
	def linkTvmaze(self, media = None, title = None, metadata = None, search = True):
		data = self._extract(media = media, title = title, metadata = metadata)
		if data and data['title'] and search: return 'https://tvmaze.com/search?q=' + self._query(query = data['title'], plus = True)
		return None

	@classmethod
	def linkTomatoes(self, media = None, title = None, year = None, season = None, episode = None, metadata = None, search = False, test = False):
		data = self._extract(media = media, title = title, year = year, season = season, metadata = metadata)
		if data and data['title']:
			base = 'https://rottentomatoes.com'
			search = (base + '/search?search=' + self._query(query = data['title'], plus = False)) if search else None
			slug1 = self._slug(title = data['title'], year = data['year'], separator = '_', symbol = None, lower = True)
			slug2 = self._slug(title = data['title'], separator = '_', symbol = None, lower = True)
			if Media.isSerie(data['media']):
				base += '/tv/'
				if test:
					link = base + slug1
					if data['season']: link += '/s%02d' % data['season']
					if data['episode']: link += '/e%02d' % data['episode']
					if self._test(link = link): return link
					elif not slug1 == slug2:
						link = base + slug2
						if data['season']: link += '/s%02d' % data['season']
						if data['episode']: link += '/e%02d' % data['episode']
						if self._test(link = link): return link
				else: return base + slug2
			else:
				base += '/m/'
				if test:
					link = base + slug1
					if self._test(link = link): return link
					elif not slug1 == slug2:
						link = base + slug2
						if self._test(link = link): return link
				else: return base + slug2
			return search
		return None

	@classmethod
	def linkMetacritic(self, media = None, title = None, season = None, metadata = None, search = False, test = False):
		data = self._extract(media = media, title = title, season = season, metadata = metadata)
		if data and data['title']:
			link = 'https://metacritic.com'
			search = (link + '/search/%s/%s/results') if search else None
			slug = self._slug(title = data['title'], separator = '-', symbol = None, lower = True) # Does not seem to use year.
			if Media.isSerie(data['media']):
				link += '/tv/' + slug
				if data['season']: link += '/season-' + str(data['season'])
				# The episode part contains the episode number + episode title. But even with the title, sometimes Metacritic adds some random number at the end (GoT S08). Not not add the episode number.
				if not test or self._test(link = link): return link
				elif search: return search % ('tv', self._query(query = data['title'], plus = False))
			else:
				link += '/movie/' + slug
				if not test or self._test(link = link): return link
				elif search: return search % ('movie', self._query(query = data['title'], plus = False))
		return None

	@classmethod
	def linkCommonsense(self, media = None, title = None, metadata = None, search = False, test = False):
		data = self._extract(media = media, title = title, metadata = metadata)
		if data and data['title']:
			base = 'https://commonsensemedia.org'
			search = (base + '/search/category/%s/' + self._query(query = data['title'], plus = True)) if search else None
			slug = self._slug(title = data['title'], separator = '-', symbol = None, lower = True)
			if Media.isSerie(data['media']):
				link = base + '/tv-reviews/' + slug
				if test:
					if self._test(link = link): return link
					elif search: return search % 'tv'
				else: return link
			else:
				link = base + '/movie-reviews/' + slug
				if test:
					if self._test(link = link): return link
					elif search: return search % 'movie'
				else: return link
		return None

	@classmethod
	def linkLetterboxd(self, media = None, title = None, year = None, metadata = None, search = False, test = False):
		data = self._extract(media = media, title = title, year = year, metadata = metadata)
		if data and data['title']:
			base = 'https://letterboxd.com'
			search = (base + '/search/' + self._query(query = data['title'], plus = True)) if search else None
			slug1 = self._slug(title = data['title'], year = data['year'], separator = '-', symbol = None, lower = True)
			slug2 = self._slug(title = data['title'], separator = '-', symbol = None, lower = True)
			if Media.isSerie(data['media']):
				return None # Does not contain shows.
			else:
				base += '/film/'
				if test:
					link = base + slug1
					if self._test(link = link): return link
					elif not slug1 == slug2:
						link = base + slug2
						if self._test(link = link): return link
				else: return base + slug2
			return search
		return None

	@classmethod
	def linkCriticker(self, media = None, title = None, year = None, season = None, metadata = None, search = False, test = False):
		data = self._extract(media = media, title = title, year = year, season = season, metadata = metadata)
		if data and data['title']:
			base = 'https://criticker.com'
			search = (base + '/?type=films&search=%s' + self._query(query = data['title'], plus = False)) if search else None
			slug1 = self._slug(title = data['title'], year = data['year'], separator = '-', symbol = None, lower = True)
			slug2 = self._slug(title = data['title'], separator = '-', symbol = None, lower = True)
			if Media.isSerie(data['media']):
				base += '/tv/'
				if test:
					link = base + slug1
					if data['season']: link += '/episodes/?season=%s' % data['season']
					if self._test(link = link): return link
					elif not slug1 == slug2:
						link = base + slug2
						if data['season']: link += '/episodes/?season=%s' % data['season']
						if self._test(link = link): return link
				else: return base + slug2
			else:
				base += '/film/'
				if test:
					link = base + slug1
					if self._test(link = link): return link
					elif not slug1 == slug2:
						link = base + slug2
						if self._test(link = link): return link
				else: return base + slug2
			return search
		return None

	@classmethod
	def linkFanart(self, media = None, tmdb = None, tvdb = None, title = None, metadata = None, search = False):
		data = self._extract(media = media, tmdb = tmdb, tvdb = tvdb, title = title, metadata = metadata)
		if data:
			link = 'https://fanart.tv'
			if Media.isSerie(data['media']):
				if data['tvdb']: return link + '/series/' + data['tvdb']
				elif data['title'] and search: return link + '/?sect=1&s=' + self._query(query = data['title'], plus = False)
			else:
				if data['tmdb']: return link + '/movie/' + data['tmdb']
				elif data['title'] and search: return link + '/?sect=3&s=' + self._query(query = data['title'], plus = False)
		return None

	@classmethod
	def linkHome(self, media = None, title = None, year = None, metadata = None, search = False):
		try: link =  metadata['homepage']
		except: link = None
		if not link and search:
			data = self._extract(media = media, title = title, year = year, metadata = metadata)
			if data and data['title']:
				query = data['title']
				if data['media'] == Media.Movie and data['year']: query += ' ' + str(data['year'])
				query += ' homepage'
				link = self.linkGoogle(media = data['media'], title = data['title'], year = data['year'], metadata = metadata, query = query, search = search)
		return link

	@classmethod
	def linkTrailer(self, media = None, title = None, year = None, metadata = None, search = False):
		try: link = metadata['trailer']
		except: link = None
		if not link and search:
			data = self._extract(media = media, title = title, year = year, metadata = metadata)
			if data and data['title']:
				query = data['title']
				if data['media'] == Media.Movie and data['year']: query += ' ' + str(data['year'])
				query += ' trailer'
				link = 'https://youtube.com/results?search_query=' + self._query(query = query, plus = True)
		return link

	@classmethod
	def linkGoogle(self, media = None, title = None, year = None, season = None, episode = None, metadata = None, query = None, search = False):
		if not query:
			data = self._extract(media = media, title = title, year = year, season = season, episode = episode, metadata = metadata)
			if data and data['title']:
				query = [data['title']]
				if Media.isSerie(data['media']):
					if not data['season'] is None: query.extend(['Season', data['season']])
					if not data['episode'] is None: query.extend(['Episode', data['episode']])
				elif data['media'] == Media.Set:
					if not 'collection' in data['title'].lower(): query.append('Collection')
				elif data['media'] == Media.Movie:
					if data['year']: query.append(data['year'])
				query = [Converter.unicode(i) for i in query if not i is None]
			else:
				return None

		if query:
			if Tools.isArray(query): query = ' '.join(query)
			return 'https://google.com/search?q=%s' % self._query(query = query, plus = True)
		return None

	@classmethod
	def linkDuckduckgo(self, media = None, title = None, year = None, season = None, episode = None, metadata = None, query = None, search = False):
		if not query:
			data = self._extract(media = media, title = title, year = year, season = season, episode = episode, metadata = metadata)
			if data and data['title']:
				query = [data['title']]
				if Media.isSerie(data['media']):
					if not data['season'] is None: query.extend(['Season', data['season']])
					if not data['episode'] is None: query.extend(['Episode', data['episode']])
				elif data['media'] == Media.Set:
					if not 'collection' in data['title'].lower(): query.append('Collection')
				elif data['media'] == Media.Movie:
					if data['year']: query.append(data['year'])
				query = [Converter.unicode(i) for i in query if not i is None]
			else:
				return None

		if query:
			if Tools.isArray(query): query = ' '.join(query)
			return 'https://duckduckgo.com/?q=%s' % self._query(query = query, plus = True)
		return None
