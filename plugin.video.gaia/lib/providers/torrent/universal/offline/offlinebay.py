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

from lib.providers.core.offline import ProviderOffline
from lib.modules.tools import Time, Converter, Regex

class Provider(ProviderOffline):

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderOffline.initialize(self,
			name				= 'OfflineBay',
			link				= [
									'https://github.com/offlineindexer/data/raw/main/thepiratebay/meta.json',
									'https://gitlab.com/offlineindexer/data/raw/main/thepiratebay/meta.json',
								],

			dumpProviderName	= 'ThePirateBay',
			dumpReleaseTime		= 1569283200, # 2019-09-24
			dumpSizeDownload	= 67827947,
			dumpSizeStorage		= 133771264,
			dumpSizeCount		= 804995,
			dumpLinkWeb			= 'https://thepiratebay.org',
			dumpLinkSource		= 'https://web.archive.org/web/20190915000000*/https://thepiratebay.org/static/dump/csv/torrent_dump_full.csv.gz',
			dumpLinkOrignal		= 'https://web.archive.org/web/20190924160713if_/https://thepiratebay.org/static/dump/csv/torrent_dump_full.csv.gz',
			dumpProcessFilter	= ProviderOffline.FilterQuote,
		)

	##############################################################################
	# GENERATE
	##############################################################################

	def _generateExtract(self, data):
		try:
			if data and not data.startswith('#'):
				# Do not simply split by ";", since file names can contain the as HTML entities (eg: &amp;).
				# There are also some ";" that are not an HTML entity: ...;"Otis Waygood - Ten Light Claps And A Scream (1971; 2003)";...
				name = Regex.extract(data = data, expression = self.dumpProcessFilter(), group = 1)
				if name:
					hash = None
					time = None
					size = None
					values = data.replace('"%s";' % name, '', 1).split(';')

					try: hash = Converter.base64Hex(values[1])
					except: self.logError()
					if hash:
						try: time = Time.timestamp(fixedTime = values[0], format = '%Y-%b-%d %H:%M:%S')
						except: self.logError()
						try: size = int(values[2])
						except: self.logError()
						return {
							ProviderOffline.AttributeName : name,
							ProviderOffline.AttributeHash : hash,
							ProviderOffline.AttributeTime : time,
							ProviderOffline.AttributeSize : size,
						}
		except: self.logError()
		return None
