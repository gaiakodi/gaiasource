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
from lib.debrid.offcloud import Core

class Provider(ProviderDebrid):

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderDebrid.initialize(self, core = Core())

	##############################################################################
	# SEARCH
	##############################################################################

	def search(self, media = None, niche = None, titles = None, years = None, time = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, numberSeason = None, numberEpisode = None, numberPack = None, language = None, country = None, network = None, studio = None, pack = None, exact = None, silent = False, cacheLoad = True, cacheSave = True, hostersAll = None, hostersPremium = None):
		try:
			threads = [
				self.thread(self.searchRetrieve, self.core().CategoryCloud, media, titles, years, numberSeason, numberEpisode, numberPack, language, country, network, studio),
				self.thread(self.searchRetrieve, self.core().CategoryInstant, media, titles, years, numberSeason, numberEpisode, numberPack, language, country, network, studio)
			]
			self.threadExecute(threads, limit = self.concurrencyTasks(level = 1))
		except: self.logError()

	def searchRetrieve(self, category, media, titles, years, numberSeason, numberEpisode, numberPack, language, country, network, studio):
		try:
			finished = self.core().StatusFinished
			instant = category == self.core().CategoryInstant
			items = self.cacheRequest(function = 'items', category = category)

			if not self.stopped() and not items is None:
				ids = []
				threads = []
				for item in items:
					if item['status'] == finished: # Only finished downloads.
						id = item['id']
						if not id in ids: # The same torrent/NZB can be added multiple times to the downloader.
							if self.searchValidName(name = item['name']):
								ids.append(id)
								if instant: self.searchDetails(category, item, media, titles, years, numberSeason, numberEpisode, numberPack, language, country, network, studio)
								else: threads.append(self.thread(self.searchDetails, category, item, media, titles, years, numberSeason, numberEpisode, numberPack, language, country, network, studio))

				if self.verifyBusy(): self.verifyCore()
				else: self.threadExecute(threads, limit = self.concurrencyTasks(level = 3))
		except: self.logError()

	def searchDetails(self, category, item, media, titles, years, numberSeason, numberEpisode, numberPack, language, country, network, studio):
		try:
			try: size = item['size']['bytes']
			except: size = None
			try: time = item['time']
			except: time = None

			if category == self.core().CategoryInstant: result = item
			else: result = self.cacheRequest(function = 'item', category = category, id = item['id'], transfer = True, files = True)

			if not self.stopped() and result:
				try: parent = result['name']
				except: parent = None
				parts = [parent] if parent else []

				try: size = result['size']['bytes']
				except: pass
				try: time = result['time']
				except: pass

				files = []
				if 'files' in result:
					for item in result['files']:
						try:
							# Do not do this, since OffCloud marks AVI files as non-streams.
							#if 'stream' in item and not item['stream']: continue # Exclude non-video files.
							files.append({'name' : item['name'], 'link' : item['link']})
						except: self.logError()

				for i in range(len(files)):
					files[i]['parent'] = parent
					files[i]['parts'] = parts
					files[i]['time'] = time
					files[i]['size'] = size

				self.searchProcess(files = files, separateSize = False)
		except: self.logError()
