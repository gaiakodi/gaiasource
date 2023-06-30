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
			name				= 'OfflineParadise',
			link				= [
									'https://github.com/offlineindexer/data/raw/main/torrentparadise/meta.json',
									'https://gitlab.com/offlineindexer/data/raw/main/torrentparadise/meta.json',
								],
			performance			= ProviderOffline.PerformanceMedium, # Takes a long time to scan all the databases.

			dumpProviderName	= 'TorrentParadise',
			dumpReleaseTime		= 1642377600, # 2022-01-17
			dumpSizeDownload	= 489919315,
			dumpSizeStorage		= 874745856,
			dumpSizeCount		= 5287859,
			dumpLinkWeb			= 'https://torrent-paradise.ml',
			dumpLinkSource		= 'https://github.com/urbanguacamole/torrent-paradise',
			dumpLinkOrignal		= 'https://cloudflare-ipfs.com/ipfs/QmcsjpRsLkSojdJ19PpTYoevP8ZdeCqmtEvjqa2R28rxWs', # https://ipfs.io/ipfs/QmcsjpRsLkSojdJ19PpTYoevP8ZdeCqmtEvjqa2R28rxWs
			dumpProcessFilter	= '.*?,(.*)(?:,\d+){4}',
		)

	##############################################################################
	# GENERATE
	##############################################################################

	def _generateExtract(self, data):
		try:
			if data and not data.startswith('#'):
				name = Regex.extract(data = data, expression = self.dumpProcessFilter(), group = 1)
				if name:
					hash = None
					size = None
					seeds = None
					leeches = None
					downloads = None

					# In case the file name contains a comma.
					# Only replace the 1st occurance of the name.
					# Eg ("11" occurs twice): 8eb895d06e42e44dda7002cb2b7e6b7cd804c21c,11,732693911,0,0,0
					values = data.replace('%s,' % name, '', 1).split(',')

					try: hash = values[0]
					except: self.logError()
					if hash:
						try: size = int(values[1])
						except: self.logError()
						try: seeds = int(values[2])
						except: self.logError()
						try: leeches = int(values[3])
						except: self.logError()
						try: downloads = int(values[4])
						except: self.logError()
						return {
							ProviderOffline.AttributeName : name,
							ProviderOffline.AttributeHash : hash,
							ProviderOffline.AttributeSize : size,
							ProviderOffline.AttributeSeeds : seeds,
							ProviderOffline.AttributeLeeches : leeches,
							ProviderOffline.AttributeDownloads : downloads,
						}
		except: self.logError()
		return None
