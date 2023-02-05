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
from lib.modules.tools import Tools
from lib.modules.external import Importer

BeautifulSoup = Importer.moduleBeautifulSoup()
SoupStrainer = Importer.moduleBeautifulStrainer()
Tag = Importer.moduleBeautifulTag()
Navigable = Importer.moduleBeautifulNavigable()

class Parser(BeautifulSoup):

	# https://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-a-parser
	#	ParserXml: Very fast (implemented in C). Cannot handle HTML mistakes (eg: unclosed tags). Does not work (maybe because the library is updated for Python 3), throwing an "RuntimeError: restricted attribute" error. Not supported by Kodi 19 yet (2021-02-24).
	#	ParserHtml: Fast (implemented in C). Can handle many HTML mistakes (eg: unclosed tags).
	#	ParserHtml5: Slow (implemented in Python). Can handle most HTML mistakes (eg: unclosed tags). Cannot use optimized extraction, making it even slower. Should only be used if none of the other parsers work.
	# HTML/HTML5 can handle unopened, unclosed, and incorrectly nested tags, which the default XML parser cannot. Eg: KickAssTorrents has unopened and unclosed tags.
	ParserXml		= 'lxml'
	ParserHtml		= 'html.parser'
	ParserHtml5		= 'html5lib'
	ParserDefault	= ParserHtml

	def __init__(self, data, parser = ParserDefault, only = None, convert = True):
		# gaiaremove - once Kodi 20 comes out, try adding lxml back (should be part of Kodi build).
		# lxml is about 30-40% faster than html.parser.
		# Test this on Windows, since on Linux the OS's Python environment is used, which might already have lxml istalled via PIP. On Windows, Kodi ships with its own Python.
		# UPDATE: With Kodi 20 under Linux still getting:
		#	ImportError: Interpreter change detected - this module can only be loaded into one interpreter per process.
		# https://groups.google.com/g/cython-users/c/mmWEyUjpV6M

		# LXML currently does not work in Kodi 19.
		# Even when fixing the LXML errors, just importing the module cause sporadic freezes of Kodi.
		# Since LXML is currently not used anywhere in Gaia, remove it for now.
		# More information in the BeautifulSoup and LXML Gaia external ReadMe.
		if parser == Parser.ParserXml:
			from lib.modules.tools import System, Logger
			Logger.error('Cannot use the LXML parser in Gaia under Kodi 19 (yet).')
			System.exit()

		if convert: data = self.convert(data = data, full = False)
		BeautifulSoup.__init__(self, data, parser, parse_only = only)

	# Do not name this funnction "decode", since BeautifulSoup has its own function with that name.
	@classmethod
	def convert(self, data, full = False):
		# https://github.com/aswalin/msan692/blob/master/notes/html.md
		# BeautifulSoup replaces &nbsp; with the ASCII char 160 instead of a space (ASCII 32). 160 is the ASCII value for a non-breakable space.
		try: data = data.decode('utf-8') # Important, otherwise some &nbsp; end up being \xa0.
		except: pass
		try:
			data = data.replace('&nbsp;', ' ').replace(unichr(160), ' ').replace('\\xa0', ' ').replace('<br>', ' ').replace('<br/>', ' ').replace('<br />', ' ')
			if full:
				# https://beautiful-soup-4.readthedocs.io/en/latest/#output-formatters
				# BeautifulSoup does not replace &amp; &lt; &gt;, because this can invalidate the HTML during processing.
				data = data.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
		except: pass # Not a string, such as extracting the class attribute. If multiple classes are set, it is returned as a list.
		return data

class Strainer(SoupStrainer):

	def __init__(self, tag = None, string = None, attributes = None):
		# SoupStrainer cannot deal with multiple classes.
		# Manually split the text and check if it is inside.
		# https://stackoverflow.com/questions/13413470/beautifulsoup-soupstrainer-doesnt-work-when-element-has-multiple-classes
		if attributes and 'class' in attributes and Tools.isString(attributes['class']):
			value = attributes['class']
			attributes['class'] = lambda text: text and value in text.split(' ')

		SoupStrainer.__init__(self, name = True if tag is None else tag, string = string, attrs = attributes)


# gaiaremove - legacy - should be replaced by BeautifulSoup at some time.
class Raw(object):

	@classmethod
	def parse(self, data, tag = '', attributes = None, extract = False):
		if attributes: attributes = dict((key, re.compile(value + ('$' if value else ''))) for key, value in attributes.items())
		results = self._parse(data, tag, attributes, extract)
		if extract: results = [result.attrs[extract.lower()] for result in results]
		else: results = [result.content for result in results]
		return results

	@classmethod
	def _parse(self, data, tag = '', attributes = None, extract = False):
		from collections import namedtuple
		dom = namedtuple('DOMMatch', ['attrs', 'content'])

		if attributes is None: attributes = {}
		tag = tag.strip()
		if Tools.isInstance(data, dom):
			data = [data]
		elif Tools.isString(data):
			try:
				data = [data.decode("utf-8")]  # Replace with chardet thingy
			except:
				try: data = [data.decode("utf-8", "replace")]
				except: data = [data]
		elif not Tools.isList(data):
			return ''

		if not tag: return ''
		if not Tools.isDictionary(attributes): return ''

		if extract:
			if not Tools.isList(extract): extract = [extract]
			extract = set([key.lower() for key in extract])

		results = []
		for item in data:
			if Tools.isInstance(item, dom): item = item.content

			result = []
			for element in self._parseElements(item, tag, attributes):
				attributes = self._parseAttributes(element)
				if extract and not extract <= set(attributes.keys()): continue
				temp = self._parseDocument(item, tag, element).strip()
				result.append(dom(attributes, temp))
				item = item[item.find(temp, item.find(element)):]
			results += result

		return results

	@classmethod
	def _parseDocument(self, data, tag, match):
		if match.endswith('/>'): return ''

		# Override tag name with tag from match if possible.
		element = re.match('<([^\s/>]+)', match)
		if element: tag = element.group(1)

		prefix = '<%s' % tag
		suffix = "</%s" % tag

		# Start/end tags without matching case cause issues.
		start = data.find(match)
		end = data.find(suffix, start)
		index = data.find(prefix, start + 1)

		while index < end and not index == -1:  # Ignore too early </endstr> return.
			tend = data.find(suffix, end + len(suffix))
			if not tend == -1: end = tend
			index = data.find(prefix, index + 1)

		if start == -1 and end == -1: result = ''
		elif start > -1 and end > -1: result = data[start + len(match):end]
		elif end > -1: result = data[:end]
		elif start > -1: result = data[start + len(match):]
		else: result = ''

		return result

	@classmethod
	def _parseElements(self, item, tag, attributes):
		if not attributes:
			pattern = '(<%s(?:\s[^>]*>|/?>))' % tag
			current = re.findall(pattern, item, re.M | re.S | re.I)
		else:
			regexType = type(re.compile(''))
			last = None
			for key, value in attributes.items():
				isRegex =  Tools.isInstance(value, regexType)
				isString = Tools.isString(value)
				pattern = '''(<{tag}[^>]*\s{key}=(?P<delim>['"])(.*?)(?P=delim)[^>]*>)'''.format(tag = tag, key = key)
				extracted = re.findall(pattern, item, re.M | re.S | re.I)
				if isRegex:
					current = [r[0] for r in extracted if re.match(value, r[2])]
				else:
					temp = [value] if isString else value
					current = [r[0] for r in extracted if set(temp) <= set(r[2].split(' '))]

				if not current:
					has_space = (isRegex and ' ' in value.pattern) or (isString and ' ' in value)
					if not has_space:
						pattern = '''(<{tag}[^>]*\s{key}=([^\s/>]*)[^>]*>)'''.format(tag = tag, key = key)
						extracted = re.findall(pattern, item, re.M | re.S | re.I)
						if isRegex: current = [r[0] for r in extracted if re.match(value, r[1])]
						else: current = [r[0] for r in extracted if value == r[1]]

				if last is None: last = current
				else: last = [item for item in current if item in last]
			current = last

		return current

	@classmethod
	def _parseAttributes(self, element):
		attributes = {}
		for match in re.finditer('''\s+(?P<key>[^=]+)=\s*(?:(?P<delim>["'])(?P<value1>.*?)(?P=delim)|(?P<value2>[^"'][^>\s]*))''', element):
			match = match.groupdict()
			value1 = match.get('value1')
			value2 = match.get('value2')
			value = value1 if value1 is not None else value2
			if value is None: continue
			attributes[match['key'].lower().strip()] = value
		return attributes
