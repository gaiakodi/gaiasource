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

import re
import math
import time
import datetime

class ConverterBase(object):

	@classmethod
	def _isString(self, value):
		try: return isinstance(value, (str, bytes))
		except:
			try: return isinstance(value, (basestring, unicode))
			except: pass
		return False

	@classmethod
	def _isBoolean(self, value):
		return isinstance(value, bool)

	@classmethod
	def _isNumber(self, value, bool = False):
		if not bool and self._isBoolean(value): return False
		return isinstance(value, (int, float))

	@classmethod
	def _isDictionary(self, value):
		return isinstance(value, dict)

class ConverterData(ConverterBase):

	Unknown = None
	Failure = None

	SpeedSymbol = '/s'
	SpeedLetter = 'ps'
	SpeedDefault = SpeedSymbol

	PlacesUnknown = Unknown
	PlacesNone = 'none'
	PlacesSingle = 'single'
	PlacesDouble = 'double'
	PlacesTriple = 'triple'

	TypeUnknown = Unknown
	TypeSize = 'size'
	TypeSpeed = 'speed'

	Bit = 'bit'
	BitKilo = 'bitkilo'
	BitMega = 'bitmega'
	BitGiga = 'bitgiga'
	BitTera = 'bittera'
	BitPeta = 'bitpeta'

	Byte = 'byte'
	ByteKilo = 'bytekilo'
	ByteMega = 'bytemega'
	ByteGiga = 'bytegiga'
	ByteTera = 'bytetera'
	BytePeta = 'bytepeta'

	Units = {

		# BIT

		Bit : {
			'unit' : Bit,
			'multiplier' : 8,
			'name' : 'bit',
			'abbreviation' : 'b',
			'labels' : {
				'main' : ['bit', 'bits'],
				'case' : ['b'],
				'other' : ['bi', 'b'],
			},
		},
		BitKilo : {
			'unit' : BitKilo,
			'multiplier' : 0.0078125,
			'name' : 'kilobit',
			'abbreviation' : 'kb',
			'labels' : {
				'main' : ['kilobit', 'kbit', 'kibit', 'kibib', 'bitkilo', 'bitskilo', 'bitki', 'bitski'],
				'case' : ['kb', 'kilob', 'kib'],
				'other' : ['kb', 'kilob'],
			},
		},
		BitMega : {
			'unit' : BitMega,
			'multiplier' : 0.00000762939453125,
			'name' : 'megabit',
			'abbreviation' : 'mb',
			'labels' : {
				'main' : ['megabit', 'mbit', 'mebit', 'mebib', 'bitmega', 'bitsmega', 'bitme', 'bitsme'],
				'case' : ['mb', 'megab', 'mib'],
				'other' : ['mb', 'megab'],
			},
		},
		BitGiga : {
			'unit' : BitGiga,
			'multiplier' : 0.00000000745058059692383,
			'name' : 'gigabit',
			'abbreviation' : 'gb',
			'labels' : {
				'main' : ['gigabit', 'gbit', 'gibit', 'gibib', 'bitgiga', 'bitsgiga', 'bitgi', 'bitsgi'],
				'case' : ['gb', 'gigab', 'gib'],
				'other' : ['gb', 'gigab'],
			},
		},
		BitTera : {
			'unit' : BitTera,
			'multiplier' : 0.0000000000072759576141834,
			'name' : 'terabit',
			'abbreviation' : 'tb',
			'labels' : {
				'main' : ['terabit', 'tbit', 'tebit', 'tebib', 'bittera', 'bitstera', 'bitte', 'bitste'],
				'case' : ['tb', 'terab', 'teb'],
				'other' : ['tb', 'terab'],
			},
		},
		BitPeta : {
			'unit' : BitPeta,
			'multiplier' : 0.000000000000007105427357601,
			'name' : 'petabit',
			'abbreviation' : 'pb',
			'labels' : {
				'main' : ['petabit', 'pbit', 'pebit', 'pebib', 'bitpeta', 'bitspeta', 'bitpe', 'bitspe'],
				'case' : ['pb', 'petab', 'peb'],
				'other' : ['pb', 'petab'],
			},
		},

		# BYTES

		Byte : {
			'unit' : Byte,
			'multiplier' : 1,
			'name' : 'byte',
			'abbreviation' : 'B',
			'labels' : {
				'main' : ['byte', 'bytes'],
				'case' : ['B', 'Б'],
				'other' : ['by', 'b'],
			},
		},
		ByteKilo : {
			'unit' : ByteKilo,
			'multiplier' : 0.0009765625,
			'name' : 'kilobyte',
			'abbreviation' : 'KB',
			'labels' : {
				'main' : ['kilobyte', 'kbyte', 'kibyte', 'bytekilo', 'byteskilo', 'byteki', 'byteski'],
				'case' : ['KB', 'K', 'kiloB', 'KiloB', 'KiB', 'Kib', 'KIB', 'КБ'],
				'other' : ['kb', 'k', 'kilob', 'kil', 'kils'],
			},
		},
		ByteMega : {
			'unit' : ByteMega,
			'multiplier' : 0.00000095367431640625,
			'name' : 'megabyte',
			'abbreviation' : 'MB',
			'labels' : {
				'main' : ['megabyte', 'mbyte', 'mebyte', 'bytemega', 'bytesmega', 'byteme', 'bytesme'],
				'case' : ['MB', 'M', 'megaB', 'MegaB', 'MiB', 'Mib', 'MIB', 'МБ'],
				'other' : ['mb', 'm', 'megab', 'meg', 'megs'],
			},
		},
		ByteGiga : {
			'unit' : ByteGiga,
			'multiplier' : 0.00000000093132257461548,
			'name' : 'gigabyte',
			'abbreviation' : 'GB',
			'labels' : {
				'main' : ['gigabyte', 'gbyte', 'gibyte', 'bytegiga', 'bytesgiga', 'bytegi', 'bytesgi'],
				'case' : ['GB', 'G', 'gigaB', 'GigaB', 'GiB', 'Gib', 'GIB', 'ГБ'],
				'other' : ['gb', 'g', 'gigab', 'gig', 'gigs'],
			},
		},
		ByteTera : {
			'unit' : ByteTera,
			'multiplier' : 0.00000000000090949470177293,
			'name' : 'terabyte',
			'abbreviation' : 'TB',
			'labels' : {
				'main' : ['terabyte', 'tbyte', 'tebyte', 'bytetera', 'bytestera', 'bytete', 'byteste'],
				'case' : ['TB', 'T', 'teraB', 'TeraB', 'TiB', 'Tib', 'TIB', 'ТБ'],
				'other' : ['tb', 't', 'terab', 'ter', 'ters'],
			},
		},
		BytePeta : {
			'unit' : BytePeta,
			'multiplier' : 0.00000000000000088817841970013,
			'name' : 'petabyte',
			'abbreviation' : 'PB',
			'labels' : {
				'main' : ['petabyte', 'pbyte', 'pebyte', 'bytepeta', 'bytespeta', 'bytepe', 'bytespe'],
				'case' : ['PB', 'P', 'petaB', 'PetaB', 'PiB', 'Pib', 'PIB', 'ТБ'],
				'other' : ['pb', 'p', 'petab', 'pet', 'pets'],
			},
		},
	}

	UnitsBit = [Units[Bit], Units[BitKilo], Units[BitMega], Units[BitGiga], Units[BitTera], Units[BitPeta]]
	UnitsByte = [Units[Byte], Units[ByteKilo], Units[ByteMega], Units[ByteGiga], Units[ByteTera], Units[BytePeta]]
	UnitsAll = UnitsByte + UnitsBit

	# value: string, int, or float.
	def __init__(self, value, unit = Unknown, type = Unknown):
		self.mBytes = self.toBytes(value = value, unit = unit, type = type)
		self.mType = type

	@classmethod
	def _round(self, value, places = 0):
		value = round(value, places)
		if places <= 0: value = int(value)
		return value

	# Extracts number from string.
	@classmethod
	def _extractNumber(self, string):
		number = re.search('\d+\.*\d*', str(string))
		if not number is None: number = float(number.group(0))
		return number

	# Extracts number and unit from string.
	# labels: main or other
	@classmethod
	def _extractString(self, string, units, labels):
		regex = '\d+\.*\d*[\s,_]*'
		unit = ConverterData.Unknown
		value = ConverterData.Failure
		stop = False
		for i in range(1, len(units)): # 1: Skip Byte/Nit and test later.
			for label in units[i]['labels'][labels]:
				value = re.search(regex + label, string)
				if not value is None:
					unit = units[i]['unit']
					value = value.group(0)
					stop = True
					break
			if stop:
				break

		if unit == ConverterData.Unknown:
			for label in units[0]['labels'][labels]:
				value = re.search(regex + label, string)
				if not value is None:
					unit = units[0]['unit']
					value = value.group(0)
					break

		if not unit == ConverterData.Unknown:
			value = self._extractNumber(value)
		try: value = float(value)
		except: value = ConverterData.Failure
		return (value, unit)

	# unit: single or list of units. If None, search for all.
	@classmethod
	def extract(self, string, units = Unknown):
		stringLower = string.lower()
		unit = ConverterData.Unknown
		value = ConverterData.Failure
		if units == ConverterData.Unknown:
			value, unit = self._extractString(stringLower, ConverterData.UnitsByte, 'main')
			if unit == ConverterData.Unknown:
				value, unit = self._extractString(stringLower, ConverterData.UnitsBit, 'main')
				if unit == ConverterData.Unknown:
					value, unit = self._extractString(string, ConverterData.UnitsByte, 'case')
					if unit == ConverterData.Unknown:
						value, unit = self._extractString(string, ConverterData.UnitsBit, 'case')
						if unit == ConverterData.Unknown:
							value, unit = self._extractString(stringLower, ConverterData.UnitsByte, 'other')
							if unit == ConverterData.Unknown:
								value, unit = self._extractString(stringLower, ConverterData.UnitsBit, 'other')
		else:
			if self._isString(units):
				units = ConverterData.Units[units]
			if self._isDictionary(units):
				units = [units]
			value, unit = self._extractString(stringLower, units, 'main')
			if unit == ConverterData.Unknown:
				value, unit = self._extractString(string, units, 'case')
				if unit == ConverterData.Unknown:
					value, unit = self._extractString(stringLower, units, 'other')

		return (value, unit)

	# value: string, int, or float.
	@classmethod
	def toBytes(self, value, unit = Unknown, type = Unknown):
		if self._isString(value):
			# Remove comma (eg: 1,007.00 MB).
			# Only remove if there is not dot (eg: 27,3GB).
			if ',' in value:
				if '.' in value: value = value.replace(',', '')
				else: value = value.replace(',', '.')

			try: value = float(value)
			except: value, unit = self.extract(string = value, units = unit)

		if unit == ConverterData.Unknown: unit = ConverterData.Byte

		try: return value / float(ConverterData.Units[unit]['multiplier'])
		except: return ConverterData.Failure

	@classmethod
	def fromBytes(self, value, unit = Unknown):
		if unit == ConverterData.Unknown: unit = ConverterData.Byte
		return value * float(ConverterData.Units[unit]['multiplier'])

	def value(self, unit = Byte, places = PlacesUnknown):
		if self.mBytes is None: return self.mBytes
		value = self.fromBytes(self.mBytes, unit)
		if unit == ConverterData.Bit or unit == ConverterData.Byte:
			places = 0
		if not places == ConverterData.PlacesUnknown:
			value = self._round(value, places)
		return value

	def _string(self, unit = Unknown, places = PlacesUnknown, type = Unknown, optimal = False, notation = SpeedDefault):
		value = self.value()
		if value is None: return ''

		string = ''
		placesDigits = 0

		if type == ConverterData.Unknown:
			type = self.mType

		if unit == ConverterData.Unknown:
			unit = ConverterData.Byte

		if optimal:
			if self.mBytes >= 0:
				if unit in ConverterData.Units:
					unit = ConverterData.Units[unit]
				units = ConverterData.UnitsBit if unit in ConverterData.UnitsBit else ConverterData.UnitsByte

				for i in range(1, len(units)):
					if self.mBytes < 1.0 / units[i]['multiplier']:
						unit = units[i - 1]
						break

				unit = unit['unit']

				if places == ConverterData.PlacesNone:
					placesDigits = 0
				elif self._isNumber(places):
					placesDigits = int(places)
				elif places in [ConverterData.PlacesUnknown, ConverterData.PlacesSingle, ConverterData.PlacesDouble, ConverterData.PlacesTriple]:
					placesDigits = 0

					if any(u == unit for u in [ConverterData.ByteGiga, ConverterData.BitGiga]):
						placesDigits = 1
					elif any(u == unit for u in [ConverterData.ByteTera, ConverterData.BitTera]):
						placesDigits = 2
					elif any(u == unit for u in [ConverterData.BytePeta, ConverterData.BitPeta]):
						placesDigits = 3

					if type == ConverterData.TypeSpeed:
						if placesDigits > 0:
							placesDigits += 1
						if any(u == unit for u in [ConverterData.ByteMega, ConverterData.BitMega]):
							placesDigits = 1

					if places == ConverterData.PlacesDouble: placesDigits += 1
					elif places == ConverterData.PlacesTriple: placesDigits += 2
		try:
			if places in [ConverterData.PlacesUnknown, ConverterData.PlacesSingle, ConverterData.PlacesDouble, ConverterData.PlacesTriple] and (unit == ConverterData.Byte or unit == ConverterData.Bit):
				placesDigits = 0

			value = self.value(unit = unit, places = placesDigits)
			if value is None: return ''

			speed = notation if type == ConverterData.TypeSpeed else ''
			if places == ConverterData.PlacesUnknown: string = '%f' % (value)
			else: string = '%.*f' % (placesDigits, value)

			# Sometimes float has trailing zeros.
			if places == ConverterData.PlacesUnknown:
				string = string.strip('0')
				if string.startswith('.'): string = '0' + string
				if string.endswith('.'):
					if placesDigits > 0: string = string + '0'
					else: string = string[:-1]

			string = '%s %s%s' % (string, ConverterData.Units[unit]['abbreviation'], speed)
		except:
			pass
		return string

	def string(self, unit = Unknown, places = PlacesUnknown, type = Unknown, optimal = False, notation = SpeedDefault): # Subclasses overwrite.
		return self._string(unit = unit, places = places, optimal = optimal, type = type, notation = notation)

	def stringSize(self, unit = Unknown, places = PlacesUnknown, optimal = False):
		return self._string(unit = unit, places = places, optimal = optimal, type = ConverterData.TypeSize)

	def stringSpeed(self, unit = Unknown, places = PlacesUnknown, optimal = False, notation = SpeedDefault):
		return self._string(unit = unit, places = places, optimal = optimal, type = ConverterData.TypeSpeed, notation = notation)

	def stringOptimal(self, unit = Unknown, places = PlacesUnknown, type = Unknown, notation = SpeedDefault):
		return self._string(unit = unit, places = places, optimal = True, type = type, notation = notation)

	def stringSizeOptimal(self, unit = Unknown, places = PlacesUnknown):
		return self.stringSize(unit = unit, places = places, optimal = True)

	def stringSpeedOptimal(self, unit = Unknown, places = PlacesUnknown, notation = SpeedDefault):
		return self.stringSpeed(unit = unit, places = places, optimal = True, notation = notation)

class ConverterSize(ConverterData):

	def __init__(self, value, unit = ConverterData.Unknown):
		try: value = value.upper()
		except: pass
		ConverterData.__init__(self, value = value, unit = unit, type = ConverterData.TypeSize)

	@classmethod
	def toBytes(self, value, unit = ConverterData.Unknown, type = ConverterData.Unknown):
		try: value = value.upper() # To upper, otherwise interpreted as bit instead of byte.
		except: pass
		#return ConverterData.toBytes(self, value = value, unit = unit, type = type)
		return super(ConverterSize, self).toBytes(value = value, unit = unit, type = type)

	def string(self, unit = ConverterData.Unknown, places = ConverterData.PlacesUnknown, optimal = False):
		return ConverterData.stringSize(self, unit = unit, places = places, optimal = optimal)

	def stringOptimal(self, unit = ConverterData.Unknown, places = ConverterData.PlacesUnknown):
		return ConverterData.stringSizeOptimal(self, unit = unit, places = places)

class ConverterSpeed(ConverterData):

	def __init__(self, value, unit = ConverterData.Unknown):
		ConverterData.__init__(self, value = value, unit = unit, type = ConverterData.TypeSpeed)

	def string(self, unit = ConverterData.Unknown, places = ConverterData.PlacesUnknown, optimal = False, notation = ConverterData.SpeedDefault):
		return ConverterData.stringSpeed(self, unit = unit, places = places, optimal = optimal, notation = notation)

	def stringOptimal(self, unit = ConverterData.Unknown, places = ConverterData.PlacesUnknown, notation = ConverterData.SpeedDefault):
		return ConverterData.stringSpeedOptimal(self, unit = unit, places = places, notation = notation)

class ConverterDuration(ConverterBase):

	Unknown = 'unknown'

	FormatFixed = 'formatfixed' # Fixed according to unit. Eg: 1523 ms or 1.6 h

	FormatWordOptimal = 'formatwordoptimal' # 1 year or 5 days (either years or days)
	FormatWordMinimal = 'formatwordminimal' # 4 minutes or 1.5 days
	FormatWordShort = 'formatwordshort' # 123 hours, 1 minute, 20 seconds
	FormatWordMedium = 'formatwordmedium' # 256 days, 2 hours, 1 minute, 20 seconds
	FormatWordLong = 'formatwordlong' # 1 year, 2 months, 16 days, 2 hours, 1 minute, 20 seconds
	FormatWordFixed = 'formatwordfixed' # Fixed according to unit. Eg: 1523 seconds or 1.6 hours

	FormatAbbreviationOptimal = 'formatabbreviationoptimal' # 1 yr or 5 days (either years or days)
	FormatAbbreviationMinimal = 'formatabbreviationminimal' # 4 mins or 1.5 dys
	FormatAbbreviationShort = 'formatabbreviationshort' # 123 hrs, 1 min, 20 secs
	FormatAbbreviationMedium = 'formatabbreviationmedium' # 256 dys, 2 hrs, 1 min, 20 secs
	FormatAbbreviationLong = 'formatabbreviationlong' # 1 yr, 2 mths, 16 days, 2 hrs, 1 min, 20 secs
	FormatAbbreviationFixed = 'formatabbreviationfixed' # Fixed according to unit. Eg: 1523 secs or 1.6 hrs

	FormatInitialOptimal = 'formatinitialoptimal' # 1Y or 5D (either years or days)
	FormatInitialMinimal = 'formatinitialminimal' # 4M or 1.5D
	FormatInitialShort = 'formatinitialshort' # 256H 12M 23S
	FormatInitialMedium = 'formatinitialmedium' # 105D 23H 45M 12S
	FormatInitialLong = 'formatinitiallong' # 1Y 2M 105D 23H 45M 12S
	FormatInitialFixed = 'formatinitialfixed' # Fixed according to unit. Eg: 1523M or 1.6H

	FormatClockMini = 'formatclockmini' # MM:SS - 12:23
	FormatClockShort = 'formatclockshort' # HH:MM:SS - 256:12:23
	FormatClockMedium = 'formatclockmedium' # DD:HH:MM:SS - 105:23:45:12
	FormatClockLong = 'formatclocklong' # YY:MM:DD:HH:MM:SS - 01:11:28:14:20

	FormatDefault = FormatInitialMedium

	UnitNone = None
	UnitMillisecond = 'millisecond'
	UnitSecond = 'second'
	UnitMinute = 'minute'
	UnitHour = 'hour'
	UnitDay = 'day'
	UnitWeek = 'week'
	UnitMonth = 'month'
	UnitYear = 'year'

	Units = {
		UnitMillisecond : {
			'unit' : UnitMillisecond,
			'name' : {'single' : 'millisecond', 'multiple' : 'milliseconds'},
			'abbreviation' : {'single' : 'msec', 'multiple' : 'msecs'},
			'initial' : 'ms',
			'multiplier' : 1,
			'labels' : ['millisecond', 'ms', 'msec'],
		},
		UnitSecond : {
			'unit' : UnitSecond,
			'name' : {'single' : 'second', 'multiple' : 'seconds'},
			'abbreviation' : {'single' : 'sec', 'multiple' : 'secs'},
			'initial' : 's',
			'multiplier' : 1000,
			'labels' : ['second', 's', 'sec'],
		},
		UnitMinute : {
			'unit' : UnitMinute,
			'name' : {'single' : 'minute', 'multiple' : 'minutes'},
			'abbreviation' : {'single' : 'min', 'multiple' : 'mins'},
			'initial' : 'm',
			'multiplier' : 60000,
			'labels' : ['minute', 'm', 'min'],
		},
		UnitHour : {
			'unit' : UnitHour,
			'name' : {'single' : 'hour', 'multiple' : 'hours'},
			'abbreviation' : {'single' : 'hr', 'multiple' : 'hrs'},
			'initial' : 'h',
			'multiplier' : 3600000,
			'labels' : ['hour', 'h', 'hr'],
		},
		UnitDay : {
			'unit' : UnitDay,
			'name' : {'single' : 'day', 'multiple' : 'days'},
			'abbreviation' : {'single' : 'dy', 'multiple' : 'dys'},
			'initial' : 'd',
			'multiplier' : 86400000,
			'labels' : ['day', 'd', 'dy'],
		},
		UnitWeek : {
			'unit' : UnitWeek,
			'name' : {'single' : 'week', 'multiple' : 'weeks'},
			'abbreviation' : {'single' : 'wk', 'multiple' : 'wks'},
			'initial' : 'w',
			'multiplier' : 604800000,
			'labels' : ['week', 'w', 'wk'],
		},
		UnitMonth : {
			'unit' : UnitMonth,
			'name' : {'single' : 'month', 'multiple' : 'months'},
			'abbreviation' : {'single' : 'mth', 'multiple' : 'mths'},
			'initial' : 'm',
			'multiplier' : 2592000000,
			'labels' : ['month', 'mth', 'mon', 'mn'],
		},
		UnitYear : {
			'unit' : UnitYear,
			'name' : {'single' : 'year', 'multiple' : 'years'},
			'abbreviation' : {'single' : 'yr', 'multiple' : 'yrs'},
			'initial' : 'y',
			'multiplier' : 31536000000,
			'labels' : ['year', 'y', 'yr'],
		},
	}

	def __init__(self, value, unit = ConverterData.Unknown):
		self.mMilliseconds = self.toMilliseconds(value = value, unit = unit)

	@classmethod
	def _round(self, value, places = 0):
		value = round(value, places)
		if places <= 0:
			value = int(value)
		return value

	@classmethod
	def extract(self, string, units = Unknown):
		from lib.modules.external import Importer
		string = string.lower()
		string = string.replace('and', '')
		string = string.strip(' ').strip('.')
		result = Importer.moduleTimeParse().timeparse(string)
		if not result is None: result *= 1000
		else: result = 0
		return result

	@classmethod
	def toMilliseconds(self, value, unit = Unknown):
		if value is None:
			return 0
		elif self._isString(value):
			unit = ConverterDuration.UnitMillisecond
			try: value = float(value)
			except: value = self.extract(string = value, units = unit)
		elif unit == ConverterDuration.Unknown and self._isNumber(value):
			unit = ConverterDuration.UnitMillisecond

		try: return value * float(ConverterDuration.Units[unit]['multiplier'])
		except: return 0

	@classmethod
	def fromMilliseconds(self, value, unit = Unknown):
		if unit == ConverterDuration.Unknown:
			unit = ConverterDuration.UnitMillisecond
		return value / float(ConverterDuration.Units[unit]['multiplier'])

	def value(self, unit = UnitMillisecond, places = ConverterData.PlacesUnknown):
		value = self.fromMilliseconds(value = self.mMilliseconds, unit = unit)
		if unit == ConverterDuration.UnitMillisecond or unit == ConverterDuration.UnitSecond:
			places = 0
		if not places == ConverterData.PlacesUnknown:
			value = self._round(value, places)
		return value

	def _unit(self, total, unit):
		multiplier = ConverterDuration.Units[unit]['multiplier']
		value = int(math.floor(total / float(multiplier)))
		total -= (value * multiplier)
		return (total, value)

	def _units(self, start = UnitYear):
		years = 0
		months = 0
		days = 0
		hours = 0
		minutes = 0
		seconds = 0
		total = self.mMilliseconds

		if any(unit == start for unit in [ConverterDuration.UnitYear]):
			total, years = self._unit(total, ConverterDuration.UnitYear)
		if any(unit == start for unit in [ConverterDuration.UnitYear, ConverterDuration.UnitMonth]):
			total, months = self._unit(total, ConverterDuration.UnitMonth)
		if any(unit == start for unit in [ConverterDuration.UnitYear, ConverterDuration.UnitMonth, ConverterDuration.UnitDay]):
			total, days = self._unit(total, ConverterDuration.UnitDay)
		if any(unit == start for unit in [ConverterDuration.UnitYear, ConverterDuration.UnitMonth, ConverterDuration.UnitDay, ConverterDuration.UnitHour]):
			total, hours = self._unit(total, ConverterDuration.UnitHour)
		if any(unit == start for unit in [ConverterDuration.UnitYear, ConverterDuration.UnitMonth, ConverterDuration.UnitDay, ConverterDuration.UnitHour, ConverterDuration.UnitMinute]):
			total, minutes = self._unit(total, ConverterDuration.UnitMinute)
		if any(unit == start for unit in [ConverterDuration.UnitYear, ConverterDuration.UnitMonth, ConverterDuration.UnitDay, ConverterDuration.UnitHour, ConverterDuration.UnitMinute, ConverterDuration.UnitSecond]):
			total, seconds = self._unit(total, ConverterDuration.UnitSecond)

		return (years, months, days, hours, minutes, seconds)

	def _unitsMinimal(self):
		values = [0, 0, 0, 0, 0, 0]
		units = [ConverterDuration.UnitYear, ConverterDuration.UnitMonth, ConverterDuration.UnitDay, ConverterDuration.UnitHour, ConverterDuration.UnitMinute, ConverterDuration.UnitSecond]
		for i in range(len(units)):
			value = self.mMilliseconds / float(ConverterDuration.Units[units[i]]['multiplier'])
			if value >= 1:
				values[i] = value
				break
		return (values[0], values[1], values[2], values[3], values[4], values[5])

	def _unitsOptimal(self):
		values = [0, 0, 0, 0, 0, 0]

		units = [ConverterDuration.UnitYear, None, ConverterDuration.UnitDay, None, None, None]
		while True:
			for i in range(len(units)):
				try:
					value = self.mMilliseconds / float(ConverterDuration.Units[units[i]]['multiplier'])
					if value >= 1:
						values[i] = value
						break
				except: pass

			if sum(values) > 0 or not None in units: break
			units = [ConverterDuration.UnitYear, ConverterDuration.UnitMonth, ConverterDuration.UnitDay, ConverterDuration.UnitHour, ConverterDuration.UnitMinute, ConverterDuration.UnitSecond]
		return (values[0], values[1], values[2], values[3], values[4], values[5])

	def _stringWord(self, value, unit, places = 0):
		word = ConverterDuration.Units[unit]['name']['single'] if round(value, places) == 1 else ConverterDuration.Units[unit]['name']['multiple']
		return '%0.*f %s' % (places, value, word)

	def _stringWords(self, years, months, days, hours, minutes, seconds, places = 0):
		units = []
		if years > 0: units.append(self._stringWord(years, ConverterDuration.UnitYear, places = places))
		if months > 0: units.append(self._stringWord(months, ConverterDuration.UnitMonth, places = places))
		if days > 0: units.append(self._stringWord(days, ConverterDuration.UnitDay, places = places))
		if hours > 0: units.append(self._stringWord(hours, ConverterDuration.UnitHour, places = places))
		if minutes > 0: units.append(self._stringWord(minutes, ConverterDuration.UnitMinute, places = places))
		if seconds > 0: units.append(self._stringWord(seconds, ConverterDuration.UnitSecond))
		result = ', '.join(filter(None, units)) # Join if not empty.
		if result is None or result == '':
			result = self._stringWord(0, ConverterDuration.UnitSecond)
		return result

	def _stringAbbreviation(self, value, unit, places = 0):
		abbreviation = ConverterDuration.Units[unit]['abbreviation']['single'] if round(value, places) == 1 else ConverterDuration.Units[unit]['abbreviation']['multiple']
		return '%0.*f %s' % (places, value, abbreviation)

	def _stringAbbreviations(self, years, months, days, hours, minutes, seconds, places = 0):
		units = []
		if years > 0: units.append(self._stringAbbreviation(years, ConverterDuration.UnitYear, places = places))
		if months > 0: units.append(self._stringAbbreviation(months, ConverterDuration.UnitMonth, places = places))
		if days > 0: units.append(self._stringAbbreviation(days, ConverterDuration.UnitDay, places = places))
		if hours > 0: units.append(self._stringAbbreviation(hours, ConverterDuration.UnitHour, places = places))
		if minutes > 0: units.append(self._stringAbbreviation(minutes, ConverterDuration.UnitMinute, places = places))
		if seconds > 0: units.append(self._stringAbbreviation(seconds, ConverterDuration.UnitSecond))
		result = ', '.join(filter(None, units)) # Join if not empty.
		if result is None or result == '':
			result = self._stringAbbreviation(0, ConverterDuration.UnitSecond)
		return result

	def _stringInitial(self, value, unit, places = 0):
		initial = ConverterDuration.Units[unit]['initial']
		initial = initial.upper()
		return '%0.*f%s' % (places, value, initial)

	def _stringInitials(self, years, months, days, hours, minutes, seconds, places = 0):
		units = []
		if years > 0: units.append(self._stringInitial(years, ConverterDuration.UnitYear, places = places))
		if months > 0: units.append(self._stringInitial(months, ConverterDuration.UnitMonth, places = places))
		if days > 0: units.append(self._stringInitial(days, ConverterDuration.UnitDay, places = places))
		if hours > 0: units.append(self._stringInitial(hours, ConverterDuration.UnitHour, places = places))
		if minutes > 0: units.append(self._stringInitial(minutes, ConverterDuration.UnitMinute, places = places))
		if seconds > 0: units.append(self._stringInitial(seconds, ConverterDuration.UnitSecond))
		result = ' '.join(filter(None, units)) # Join if not empty.
		if result is None or result == '':
			result = self._stringInitial(0, ConverterDuration.UnitSecond)
		return result

	def _stringClock(self, value):
		return '%02d' % value

	def _stringClocks(self, years, months, days, hours, minutes, seconds, full = True):
		units = []
		if years > 0: units.append(self._stringClock(years))
		if months > 0: units.append(self._stringClock(months))
		if days > 0: units.append(self._stringClock(days))
		if full or hours > 0: units.append(self._stringClock(hours))
		units.append(self._stringClock(minutes))
		units.append(self._stringClock(seconds))
		result = ':'.join(filter(None, units)) # Join if not empty.
		if result is None or result == '':
			result = '00:00:00'
		return result

	def _stringFixed(self, unit, format = FormatInitialFixed, places = ConverterData.PlacesUnknown):
		if unit is None: return ''

		value = self.value(unit = unit, places = places)
		if value is None: return ''

		if format == ConverterDuration.FormatWordFixed: label = ' ' + ConverterDuration.Units[unit]['name']['single' if value == 1 else 'multiple']
		elif format == ConverterDuration.FormatAbbreviationFixed: label = ' ' + ConverterDuration.Units[unit]['abbreviation']['single' if value == 1 else 'multiple']
		else: label = ConverterDuration.Units[unit]['initial']

		return str(value) + label

	def string(self, format = FormatDefault, unit = UnitNone, places = ConverterData.PlacesUnknown, years = True, months = True, days = True, hours = True, minutes = True, seconds = True, capitalize = False):
		places = 0
		if format in [ConverterDuration.FormatWordMinimal, ConverterDuration.FormatAbbreviationMinimal, ConverterDuration.FormatInitialMinimal]:
			places = 1
			valueYears, valueMonths, valueDays, valueHours, valueMinutes, valueSeconds = self._unitsMinimal()
		elif format in [ConverterDuration.FormatWordOptimal, ConverterDuration.FormatAbbreviationOptimal, ConverterDuration.FormatInitialOptimal]:
			valueYears, valueMonths, valueDays, valueHours, valueMinutes, valueSeconds = self._unitsOptimal()
			places = 0 if (valueYears == 0 or valueYears >= 10 or format == ConverterDuration.FormatInitialOptimal) else 1
		else:
			start = ConverterDuration.UnitYear
			if format in [ConverterDuration.FormatClockMini]:
				start = ConverterDuration.UnitMinute
			elif format in [ConverterDuration.FormatWordShort, ConverterDuration.FormatAbbreviationShort, ConverterDuration.FormatInitialShort, ConverterDuration.FormatClockShort]:
				start = ConverterDuration.UnitHour
			elif format in [ConverterDuration.FormatWordMedium, ConverterDuration.FormatAbbreviationMedium, ConverterDuration.FormatInitialMedium, ConverterDuration.FormatClockMedium]:
				start = ConverterDuration.UnitDay
			valueYears, valueMonths, valueDays, valueHours, valueMinutes, valueSeconds = self._units(start = start)

		if not years: valueYears = 0
		if not months: valueMonths = 0
		if not days: valueDays = 0
		if not hours: valueHours = 0
		if not minutes: valueMinutes = 0
		if not seconds: valueSeconds = 0

		if format in [ConverterDuration.FormatWordOptimal, ConverterDuration.FormatWordMinimal, ConverterDuration.FormatWordShort, ConverterDuration.FormatWordMedium, ConverterDuration.FormatWordLong]:
			result = self._stringWords(valueYears, valueMonths, valueDays, valueHours, valueMinutes, valueSeconds, places = places)
		elif format in [ConverterDuration.FormatAbbreviationOptimal, ConverterDuration.FormatAbbreviationMinimal, ConverterDuration.FormatAbbreviationShort, ConverterDuration.FormatAbbreviationMedium, ConverterDuration.FormatAbbreviationLong]:
			result = self._stringAbbreviations(valueYears, valueMonths, valueDays, valueHours, valueMinutes, valueSeconds, places = places)
		elif format in [ConverterDuration.FormatInitialOptimal, ConverterDuration.FormatInitialOptimal, ConverterDuration.FormatInitialMinimal, ConverterDuration.FormatInitialShort, ConverterDuration.FormatInitialMedium, ConverterDuration.FormatInitialLong]:
			result = self._stringInitials(valueYears, valueMonths, valueDays, valueHours, valueMinutes, valueSeconds, places = places)
		elif format in [ConverterDuration.FormatClockMini, ConverterDuration.FormatClockShort, ConverterDuration.FormatClockMedium, ConverterDuration.FormatClockLong]:
			result = self._stringClocks(valueYears, valueMonths, valueDays, valueHours, valueMinutes, valueSeconds, full = not format == ConverterDuration.FormatClockMini)
		elif format in [ConverterDuration.FormatFixed, ConverterDuration.FormatWordFixed, ConverterDuration.FormatAbbreviationFixed, ConverterDuration.FormatInitialFixed]:
			result = self._stringFixed(unit, format = format, places = places)

		if capitalize: result = result.title()
		return result

class ConverterTime(ConverterBase):

	Unknown = 'unknown'

	OffsetUtc = 'utc'
	OffsetGmt = 'gmt'
	OffsetLocal = 'local'

	FormatDate = '%Y-%m-%d'
	FormatDateTime = '%Y-%m-%d %H:%M:%S'
	FormatDateTimeShort = '%Y-%m-%d %H:%M'
	FormatDateTimeJson = '%Y-%m-%dT%H:%M:%S.%fZ' # Timezone microseconds with 6 decimal places.
	FormatDateTimeJsonShort = '%Y-%m-%dT%H:%M:%S._Z' # Timezone microseconds with 3 decimal places. Some features (like Trakt) can only handle 3 decimal places.
	FormatDateShort = '%d %b %Y'
	FormatTime = '%H:%M:%S'
	FormatTimeShort = '%H:%M'
	FormatTimestamp = 'timestamp'
	FormatDefault = FormatDateTime

	Formats = (
		# Use these first, because they are most common.
		'%Y-%m-%d %H:%M:%S',		# TorrentDownloads - FormatDateTime
		'%Y-%m-%d',					# ThePirateBay - FormatDate
		'%Y-%m-%d %H:%M',			# ThePirateBay
		'%Y-%m-%d %H:%M:%S %z',		# TorrentApi
		'%Y-%m-%dT%H:%M:%S.%fZ',	# FormatDateTime
		'%Y-%m-%dT%H:%M:%S',		# TNTFork
		'%Y-%m-%dT%H:%M:%S%z',
		'%d-%m-%Y %H:%M:%S',		# ETTV
		'%d-%m-%Y',					# EliteTorrent

		'%d %b %Y',					# 1337X
		'%d %b %Y %H:%M:%S',		# 1337X

		'%d/%m/%Y',					# Torrent9
		'%d/%m/%y %H:%M',			# TorrentGalaxy
		'%d/%m/%Y %H:%M:%S',		# Pirateiro

		'%d.%m.%y',					# ilCorSaRoNeRo
		'%d.%m.%Y',					# YourBittorrent

		'%b. %d \'%y',				# TorrentProject (only some dates)
		'%b %d, %Y',				# Demonoid
		'%d %b %Y, %H:%M',			# RusMedia
		'%d %b %y',					# Rutor

		'%a, %d %b %Y %H:%M:%S %z',	# NzbNab
		'%a, %d %b %Y %H:%M:%S',	# NzbNab (not all have a UTC offset)
		'%a, %d-%b-%Y (%H:%M)',		# NzbServer and NzbStars
		'%d-%b-%Y (%H:%M)',			# NzbServer and NzbStars
		'%d-%b-%Y',					# Binsearch
	)

	Languages	= {
					'ru' : {
						u'Янв' : u'Jan',
						u'Фев' : u'Feb',
						u'Мар' : u'Mar',
						u'Апр' : u'Apr',
						u'Май' : u'May',
						u'июн' : u'Jun',
						u'Июл' : u'Jul',
						u'Авг' : u'Aug',
						u'Сен' : u'Sep',
						u'Окт' : u'Oct',
						u'Ноя' : u'Nov',
						u'Дек' : u'Dec',
					},
				}

	# value can be timestamp or time string.
	# Offset:
	#	OffsetLocal: uses the local timezone.
	#	Int: the difference in number of seconds from UTC. Hence, in France (UTC+1), the offset must be 3600.
	#	String ("utc" or "gmt"): uses the UTC/GMT timezone.
	#	String ("+-hhmm"): the timezone offset, eg: +0500
	def __init__(self, value, format = None, offset = OffsetLocal):
		self.mDatetime = None
		self.mTimestamp = None

		offsetHas = False
		offsetInvert = True
		if self._isString(offset):
			offset = self.offset(offset, local = False)

		if self._isString(value):
			# Required for unicode strings (eg: Russian date).
			try: value = value.decode('utf-8')
			except: pass
			value = value.strip()

			# Replace language specific month names.
			language = None
			if re.search(u'[\u0400-\u04FF]', value): language = ConverterTime.Languages['ru'] # Cyrillic alphabet
			if language:
				before = value
				for other, english in language.items():
					value = re.sub(other, english, value, flags = re.IGNORECASE | re.UNICODE) # Must be UNICODE, otherwise unicode characters do not work with IGNORECASE.
					if not value == before: break

			if format is None:
				offsetHas = True
				format = ConverterTime.Formats
			else:
				if format == ConverterTime.FormatDateTimeJsonShort: format = ConverterTime.FormatDateTimeJson
				offsetHas = '%z' in format
				format = [format]

			valueOffsetless = None
			if offsetHas:
				offsetTemp = self.offset(value)
				if offsetTemp: offset = offsetTemp
				valueOffsetless = re.sub('[\+\-]\d{4,6}', '', value).strip()

			for form in format:
				val = value

				# Python 2 does not support UTC offsets. ±HHMM[SS[.ffffff]]
				# Even in Python 3, %z might behave differently on different operating systems.
				# And the result timestamp seems to ignore the offset, although strptime seems to pick up the offset in Python 3 (just does not use it in time.mktime).
				# So just always handle the offset manually.
				# https://timestamp.online
				# https://www.whatsmyip.org/string-timestamp-converter/
				# http://www.4webhelp.net/us/timestamp.php
				if '%z' in form and valueOffsetless:
					val = valueOffsetless
					form = re.sub('%z', '', form).strip()

				# https://forum.kodi.tv/showthread.php?tid=112916
				# NB: First use time.strptime and only try datetime.datetime.strptime afterwards.
				# If the other way around, when parsing this date (from tester.py):
				#	Wed, 27 Jan 2021 08:09:14
				#	Wed, 27 Jan 2021 08:09:14  +2000
				#	Wed, 27 Jan 2021 08:09:14  -0030 - None
				# The first time it works and the date is correctly parsed. When executing it the 2nd+ time, it does not work.
				# Kodi/Python probably caches something internally after the first call.
				# It probably is the "Wed" part.
				try:
					self.mDatetime = datetime.datetime(*(time.strptime(val, form)[0:6]))
					break # Skip rest of the formats.
				except TypeError:
					self.mDatetime = datetime.datetime.strptime(val, form)
					break # Skip rest of the formats.
				except:
					pass
		else:
			#  Windows cannot handle negative timestamps. Calculate them manually.
			try: self.mDatetime = datetime.datetime.fromtimestamp(value)
			except: self.mDatetime = datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds = value)
			offsetInvert = False

		if self.mDatetime:
			offsetInverted = -1 if offsetInvert else 1
			if offsetInvert:
				# .replace(microsecond = 0): now() and utcnow() are taken at slightly different times, so their microsecond parts are slightly off.
				# So a 2 hour offset will show as "1:59:59.999999".
				# Drop the microsecond part to get to closest second.

				offsetLocal = datetime.datetime.now().replace(microsecond = 0) - datetime.datetime.utcnow().replace(microsecond = 0) # First adjust the local time to UTC. All datetime are by default in local timezone.
				self.mDatetime = self.mDatetime - (offsetLocal * offsetInverted)

			if self._isNumber(offset): self.mDatetime = self.mDatetime + (datetime.timedelta(seconds = offset) * offsetInverted)

			try:
				self.mTimestamp = int(time.mktime(self.mDatetime.timetuple()))
			except:
				# time.mktime() relies on the underlying OS C library.
				# On Windows 10 the library does not seem to support timestamps before the epoch/1970.
				# 	OverflowError: mktime argument out of range
				# Calculate it manually, which can create a negative timestamp. But this seems to work correctly when later formatting to a date string.
				# https://stackoverflow.com/questions/2518706/python-mktime-overflow-error
				epoch = datetime.datetime(1970, 1, 1)
				difference = self.mDatetime - epoch
				self.mTimestamp = (difference.days * 86400) + difference.seconds

			if offsetHas and self.daylight(timestamp = self.mTimestamp, date = self.mDatetime, timezone = ConverterTime.OffsetUtc):
				self.mTimestamp += 3600

	@classmethod
	def offset(self, offset, local = True):
		if offset is None: return None
		if self._isNumber(offset): return offset
		else:
			offset = offset.lower().strip()
			if offset in [ConverterTime.OffsetUtc, ConverterTime.OffsetGmt]: return 0
			elif offset == ConverterTime.OffsetLocal:
				if local: return -1 * (time.altzone if time.daylight else time.timezone)
				else: return None

		result = 0
		match = re.search('([\+\-](?:\d{4}|\d{6})(?:\.\d{1,6})?)', offset)
		if match:
			match = match.group(1)

			if '-' in match:
				inverse = True
				match = match.replace('-', '')
			else:
				inverse = False
				match = match.replace('+', '')

			hours = re.search('^(\d{2}).*', match)
			if hours: hours = int(hours.group(1))
			else: hours = 0

			minutes = re.search('^\d{2}(\d{2}).*', match)
			if minutes: minutes = int(minutes.group(1))
			else: minutes = 0

			seconds = re.search('^\d{4}(\d{2}).*', match)
			if seconds: seconds = int(seconds.group(1))
			else: seconds = 0

			fraction = re.search('^\d{4,6}(\.\d{1,6})', match)
			if fraction: seconds += float(fraction.group(1))

			result = (hours * 3600) + (minutes * 60) + seconds
			if inverse: result *= -1

		return result

	@classmethod
	def daylight(self, timestamp, date = None, timezone = OffsetUtc):
		try:
			return bool(time.localtime(timestamp).tm_isdst)
		except: # Windows cannot handle negative timestamps (before 1970).
			from lib.modules.external import Importer
			timezone = Importer.modulePytz().timezone(timezone)
			timezone_aware_date = timezone.localize(date, is_dst = None)
			return timezone_aware_date.tzinfo._dst.seconds != 0

	def string(self, format = FormatDefault, offset = OffsetLocal):
		if format == ConverterTime.FormatTimestamp:
			return self.timestamp(offset = offset)
		else:
			date = self.mDatetime
			if not offset == ConverterTime.OffsetLocal:

				# First adjust the local time to UTC. All datetime are by default in local timezone.
				offsetLocal = datetime.datetime.now().replace(microsecond = 0) - datetime.datetime.utcnow().replace(microsecond = 0)
				date = date - offsetLocal

				offset = self.offset(offset)

				# Important when marking items as watched on Trakt at a specific time.
				# If the time is set as 12h00 and the date falls in daylight savings, the time is formatted to 13h00.
				if self.daylight(timestamp = self.mTimestamp, date = date, timezone = ConverterTime.OffsetUtc):
					if not offset: offset = 0
					offset -= 3600

				if offset: date = date + datetime.timedelta(seconds = offset)

			if format == ConverterTime.FormatDateTimeJsonShort:
				result = date.strftime(ConverterTime.FormatDateTimeJson)
				result = re.sub('(\d{3})(\d{3})(Z)', r'\1\3', result)
				return result
			else:
				return date.strftime(format)

	def timestamp(self, offset = OffsetUtc):
		if not offset == ConverterTime.OffsetUtc:
			offset = self.offset(offset)
			if offset: return self.mTimestamp - offset
		return self.mTimestamp
