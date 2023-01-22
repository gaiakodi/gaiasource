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
from lib.debrid.realdebrid import Core

class Provider(ProviderDebrid):

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderDebrid.initialize(self, core = Core())

	##############################################################################
	# SEARCH
	##############################################################################

	def search(self, media, titles, years = None, date = None, idImdb = None, idTmdb = None, idTvdb = None, numberSeason = None, numberEpisode = None, language = None, pack = None, exact = None, silent = False, cacheLoad = True, cacheSave = True, hostersAll = None, hostersPremium = None):
		sources = []
		self.items = [] # NB: The same object of the provider is used for both normal episodes and season packs. Make sure it is cleared from the previous run.
		try:
			items = self.cacheRequest(function = 'items')
			if not self.stopped() and not items is None:
				threads = []
				for item in items:
					try:
						if item['transfer']['progress']['completed']['value'] == 1: # Only finished downloads.
							if self.searchValidName(name = item['name']):
								threads.append(self.thread(self.searchRetrieve, item['id'], media, titles, years, numberSeason, numberEpisode, language))
					except: self.logError()

				if self.verifyBusy(): self.verifyCore()
				else: self.threadExecute(threads, limit = self.concurrencyTasks(level = 3))
		except: self.logError()

	def searchRetrieve(self, id, media, titles, years, numberSeason, numberEpisode, language):
		try:
			result = self.cacheRequest(function = 'item', id = id)
			if result:
				titlesAll = titles['processed']['all']
				titlesMain = titles['processed']['main']

				time = result['time']['started']

				files = []
				for item in result['files']:
					try:
						name = item['name']

						parent = item['parts']
						if parent: parent = ' '.join(parent)
						else: parent = name

						parts = item['parts']
						path = ' '.join(parts + [name])

						link = item['link']
						size = item['size']['bytes']

						files.append({'name' : name, 'parent' : parent, 'parts' : parts, 'link' : link, 'time' : time, 'size' : size})
					except: self.logError()

				self.searchProcess(files = files)
		except: self.logError()
