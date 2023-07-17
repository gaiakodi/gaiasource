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

from lib.providers.core.debrid import ProviderDebrid
from lib.debrid.premiumize import Core

class Provider(ProviderDebrid):

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderDebrid.initialize(self,
			# Premiumize fixes the video links to a specific IP address.
			# If the IP address used to retrieve the link through the API changes, the video link will not work anymore.
			# Restrict how long provider results are cached, so retrieve new links if the IP changes (eg: VPN changes overnight and now has a new IP).
			cacheTime		= 10800, # 3 hours.

			searchThread	= True,

			core			= Core(),
		)

	##############################################################################
	# SEARCH
	##############################################################################

	def search(self, media, titles, years = None, time = None, idImdb = None, idTmdb = None, idTvdb = None, numberSeason = None, numberEpisode = None, language = None, pack = None, exact = None, silent = False, cacheLoad = True, cacheSave = True, hostersAll = None, hostersPremium = None):
		try:
			titlesAll = titles['processed']['all']
			titlesMain = titles['processed']['main']

			folderGaia = self.core().folderName()
			folderFeeds = self.core().folderFeeds()
			folderExclude = ['root', folderGaia, folderFeeds, 'Movies', 'Shows', 'Documentaries', 'Shorts']

			items = self.cacheRequest(function = 'items')

			if not self.stopped() and not items is None:
				files = []
				for item in items:
					try:
						id = item['id']
						name = item['name']

						parent = item['parent']['path']
						if not parent: parent = name

						try: parts = [part for part in item['parent']['parts'] if not part in folderExclude]
						except: parts = []

						timed = item['time']
						size = item['size']['bytes']

						files.append({'id' : id, 'name' : name, 'parent' : parent, 'parts' : parts, 'time' : timed, 'size' : size})
					except: self.logError()

				if self.verifyBusy(): self.verifyCore()
				else: self.searchProcess(files = files)
		except: self.logError()

	def searchAdd(self, id, stream):
		result = self.cacheRequest(function = 'itemDetails', idFile = id)
		if result:
			stream.linkSet(result['link'])
			self.resultAdd(stream)
