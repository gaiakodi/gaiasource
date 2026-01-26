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

# NB: Careful when importing this file, since it can take a long time (100ms).
# Only import on-demand and not at the top of a file. Otherwise menus are slow, when the nested imports import this file without it actually being used during execution.

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
		#gaiaremove - once Kodi 22 comes out, try adding lxml back (should be part of Kodi build).
		# lxml is about 30-40% faster than html.parser.
		# Test this on Windows, since on Linux the OS's Python environment is used, which might already have lxml istalled via PIP. On Windows, Kodi ships with its own Python.
		# UPDATE: With Kodi 20 under Linux still getting:
		#	ImportError: Interpreter change detected - this module can only be loaded into one interpreter per process.
		# https://groups.google.com/g/cython-users/c/mmWEyUjpV6M
		# UPDATE (2026-06): Kodi 21 still does not have lxml. On their Github repo is also does not seem that lxml is included in the current build:
		# https://github.com/xbmc/xbmc/tree/master/addons

		# LXML currently does not work in Kodi 19 - 21.
		# Even when fixing the LXML errors, just importing the module cause sporadic freezes of Kodi.
		# Since LXML is currently not used anywhere in Gaia, remove it for now.
		# More information in the BeautifulSoup and LXML Gaia external ReadMe.
		if parser == Parser.ParserXml:
			from lib.modules.tools import System, Logger
			Logger.error('Cannot use the LXML parser in Gaia under Kodi 21 (yet).')
			System.exit()

		if convert: data = self.convert(data = data, full = False)

		try:
			BeautifulSoup.__init__(self, data, parser, parse_only = only)
		except Exception as error:
			# If html5lib is not available in the Python environment.
			# html5lib is now also available from script.gaia.externals, but leave here as las resort.
			if type(error).__name__ == 'FeatureNotFound':
				from lib.modules.tools import Logger
				Logger.error('The BeautifulSoup parser is not available: %s.' % parser)
				if not parser == Parser.ParserHtml:
					parser = Parser.ParserHtml
					BeautifulSoup.__init__(self, data, parser, parse_only = only)

	# Do not name this funnction "decode", since BeautifulSoup has its own function with that name.
	@classmethod
	def convert(self, data, full = False):
		# https://github.com/aswalin/msan692/blob/master/notes/html.md
		# BeautifulSoup replaces &nbsp; with the ASCII char 160 instead of a space (ASCII 32). 160 is the ASCII value for a non-breakable space.
		try: data = data.decode('utf-8') # Important, otherwise some &nbsp; end up being \xa0.
		except: pass
		try:
			data = data.replace('&nbsp;', ' ').replace(chr(160), ' ').replace('\\xa0', ' ').replace('<br>', ' ').replace('<br/>', ' ').replace('<br />', ' ')
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
