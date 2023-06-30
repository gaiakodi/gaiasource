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
from lib.modules.tools import Regex

class Provider(ProviderOffline):

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderOffline.initialize(self,
			name				= 'OfflineCSV',
			link				= [
									'https://github.com/offlineindexer/data/raw/main/torrentscsv/meta.json',
									'https://gitlab.com/offlineindexer/data/raw/main/torrentscsv/meta.json',
								],

			dumpProviderName	= 'TorrentsCSV',
			dumpReleaseTime		= 1687046400, # 2023-06-18
			dumpSizeDownload	= 34347229,
			dumpSizeStorage		= 67026944,
			dumpSizeCount		= 362262,
			dumpLinkWeb			= 'https://torrents-csv.ml',
			dumpLinkSource		= 'https://git.torrents-csv.ml/heretic/torrents-csv-server',
			dumpLinkOrignal		= 'https://git.torrents-csv.ml/heretic/torrents-csv-data/raw/branch/main/torrents.csv',
			dumpProcessFilter	= ProviderOffline.FilterQuote,
		)

	##############################################################################
	# GENERATE
	##############################################################################

	def _generateExtract(self, data):
		try:
			if data and not data.startswith('#') and not data.startswith('infohash'):
				# Do not simply split by ",", since file names can contain them.
				name = Regex.extract(data = data, expression = self.dumpProcessFilter(), group = 1)
				if name:
					hash = None
					time = None
					size = None
					seeds = None
					leeches = None
					downloads = None
					values = data.replace('"%s",' % name, '', 1).split(',')

					try: hash = values[0]
					except: self.logError()
					if hash:
						try: time = int(values[2])
						except: self.logError()
						try: size = int(values[1])
						except: self.logError()
						try: seeds = int(values[3])
						except: self.logError()
						try: leeches = int(values[4])
						except: self.logError()
						try: downloads = int(values[5])
						except: self.logError()
						return {
							ProviderOffline.AttributeName : name,
							ProviderOffline.AttributeHash : hash,
							ProviderOffline.AttributeTime : time,
							ProviderOffline.AttributeSize : size,
							ProviderOffline.AttributeSeeds : seeds,
							ProviderOffline.AttributeLeeches : leeches,
							ProviderOffline.AttributeDownloads : downloads,
						}
		except: self.logError()
		return None
