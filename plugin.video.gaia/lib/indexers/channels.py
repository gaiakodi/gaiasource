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

from lib.indexers.movies import Movies

from lib.modules.tools import Media, Selection, Tools, Converter, Logger, Regex
from lib.modules.interface import Directory, Dialog, Loader
from lib.modules.cache import Cache, Memory
from lib.modules.network import Networker
from lib.modules.concurrency import Pool, Lock, Semaphore

from lib.meta.image import MetaImage
from lib.meta.tools import MetaTools

class Channels(object):

	def __init__(self, media = Media.TypeMovie, kids = Selection.TypeUndefined):
		self.mMetatools = MetaTools.instance()
		self.mCache = Cache.instance()
		self.mLimit = self.mMetatools.settingsPageMovie()

		self.mMedia = media
		self.mKids = kids

		self.mMovies = Movies(media = self.mMedia, kids = self.mKids)

		self.mBroadcasters = ['sky', 'bbc', 'tcm', '5', 'channel', 'film4', 'horror', 'itv', 'movies24', 'great', 'quest', 'rok', 'sony', 'star', 'syfy', 'talkingpictures', 'true', 'colors']

		# HD Channels (sg: 3, xsg: 3)
		# Movies (sg: 6, xsg: 6)
		# Documentaries (xsg: 11)
		#	Do not use sg: 5, that is news.
		# 14 seems to be Hindi content.
		self.mGenres = [3, 6, 11, 14]

		# https://github.com/Mermade/openSky/wiki/URL-links
		# https://github.com/Mermade/openSky/wiki/Channel-Identifiers
		self.mTime = self.timeuk()

		# Old link is blocked now.
		# Region codes: https://tvheadend.org/boards/5/topics/11130
		# 4101 = London
		#self.sky_channels_link = 'http://epgservices.sky.com/tvlistings-proxy/TVListingsProxy/init.json'
		#self.sky_programme_link = 'http://epgservices.sky.com/tvlistings-proxy/TVListingsProxy/tvlistings.json?detail=2&channels=%s&time=%s'
		self.sky_channels_link = 'https://awk.epgsky.com/hawk/linear/services/4101/1'
		self.sky_programme_link = 'https://awk.epgsky.com/hawk/linear/schedule/%s/%s'

	##############################################################################
	# TIME
	##############################################################################

	def timeuk(self):
		import datetime
		delta = datetime.datetime.utcnow() + datetime.timedelta(hours = 0)
		date = datetime.datetime(delta.year, 4, 1)
		dateOn = date - datetime.timedelta(days = date.weekday() + 1)
		date = datetime.datetime(delta.year, 11, 1)
		dateOff = date - datetime.timedelta(days = date.weekday() + 1)
		if dateOn <= delta < dateOff: time = delta + datetime.timedelta(hours = 1)
		else: time = delta
		return time.strftime('%Y%m%d')

	##############################################################################
	# RETRIEVE
	##############################################################################

	def retrieve(self, link = None, detailed = True, menu = True, clean = True):
		items = []

		try:
			if link:
				channels = link.split(',')
				if channels:
					items = self.mCache.cacheRefreshShort(self.skyList, channels = channels)
					if items:
						items = self.metadata(items = items)
						items = items[:self.mLimit * 2]
						if items and menu: self.mMovies.menu(items)
		except: Logger.error()

		if not items:
			Loader.hide()
			if menu: Dialog.notification(title = 32007, message = 33049, icon = Dialog.IconInformation)
		return items

	##############################################################################
	# NAME
	##############################################################################

	def name(self, id):
		channels = self.channels(menu = False)
		if channels:
			for channel in channels:
				if channel['id'] == id: return channel['name']
		return None

	def names(self, ids):
		channels = self.channels(menu = False)
		if channels:
			names = {}
			for id in ids:
				for channel in channels:
					if channel['id'] == id:
						names[id] = channel['name']
						break
			return names
		return None

	def nameClean(self, name, group = None):
		name = name.replace('horhd', 'horror hd')
		name = Regex.remove(data = name, expression = '\s*hd$')

		if group:
			group = group.lower()
			if Regex.match(data = name, expression = '^(%s)[^\s].*' % group): name = name.replace(group, group + ' ', 1)

		if Regex.match(data = name, expression = '[^\s](\+1)'): name = name.replace('+1', ' +1')

		name = name.replace('prem ', 'premiere ')
		name = name.replace('megahits', 'mega hits').replace('feelgood', 'feel good')

		bbc = Regex.extract(data = name, expression = '(bbc two)')
		if bbc: name = bbc

		return name.strip()

	##############################################################################
	# CHANNELS
	##############################################################################

	def channels(self, menu = True):
		channels = self.mCache.cacheLong(self.skyChannels)
		if menu and channels:
			items = sorted(channels, key = lambda i : i['name'].lower())
			items = [{'action' : 'channelsRetrieve', 'name' : i['name'].upper(), 'link' : i['id'], 'image' : 'networks.png'} for i in items]
			self.directory(items)
		return channels

	##############################################################################
	# BROADCASTERS
	##############################################################################

	def broadcasters(self, menu = True):
		channels = self.channels(menu = False)
		if menu and channels:
			items = []
			for group in sorted(self.mBroadcasters):
				ids = []
				for channel in channels:
					name = self.nameClean(name = channel['name'].lower(), group = group.replace(' ', ''))
					if name.startswith(group): ids.append(channel['id'])
				if ids: items.append({'action' : 'channelsRetrieve', 'name' : group.upper(), 'link' : ','.join(ids), 'image' : 'networks.png'})
			self.directory(items)
		return channels

	##############################################################################
	# SKY
	##############################################################################

	def skyChannels(self):
		try:
			result = Networker().requestJson(self.sky_channels_link)
			result = result['services']

			channels = []
			for i in result:
				if ('sg' in i and i['sg'] in self.mGenres) or ('xsg' in i and i['xsg'] in self.mGenres):
					channels.append({'id' : i['sid'], 'name' : i['t']})
			return channels
		except:
			Logger.error()
			return None

	def skyList(self, channels):
		try:
			def _skyList(items, channels, names):
				try:
					link = self.sky_programme_link % (self.mTime, ','.join([c for c in channels]))
					result = Networker().requestJson(link)
					result = result['schedule']
					for channel in result:
						if channel['sid'] in names: name = names[channel['sid']]
						else: name = ''

						for i in channel['events']:

							# Ignore episodes
							if 'seasonnumber' in i and i['seasonnumber']: continue
							if 'episodenumber' in i and i['episodenumber']: continue
							if 'sy' in i and i['sy'] and Regex.match(data = i['sy'], expression = '(season|episode|s\s*\d+.*(e|ep)\s*\d+)'): continue

							# Ignore other non-movies
							if not(('eg' in i and i['eg'] in self.mGenres) or ('esg' in i and i['esg'] in self.mGenres)): continue

							title = Networker.htmlDecode(i['t'].strip())
							try: year = int(Regex.extract(data = i['sy'], expression = '\(((?:19|2[01])\d{{2}})\)'))
							except: year = None

							item = {'title' : title, 'year' : year, 'channel' : name}
							if not item in items: items.append(item)
				except: Logger.error()

			names = self.names(channels)

			items = []
			chunks = [channels[i : i + 20] for i in range(0, len(channels), 20)] # Can only lookup 20 channels at a time.
			threads = [Pool.thread(target = _skyList, kwargs = {'items' : items, 'channels' : chunk, 'names' : names}, start = True) for chunk in chunks]
			[thread.join() for thread in threads]

			ids = []
			result = []
			for item in items:
				id = '%s_%s' % (str(item['title']), str(item['year']))
				if not id in ids:
					ids.append(id)
					result.append(item)

			return result
		except:
			Logger.error()
			return None

	##############################################################################
	# METADATA
	##############################################################################

	def metadata(self, items = None, filter = None, clean = True, cache = False):
		try:
			lock = Lock()
			locks = {}
			semaphore = Semaphore(self.mMetatools.concurrencyTasks())

			threads = []
			for item in items:
				semaphore.acquire()
				threads.append(Pool.thread(target = self.metadataUpdate, kwargs = {'item' : item, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore}, start = True))
			[thread.join() for thread in threads]

			items = self.mMovies.metadata(items = items, filter = filter, clean = clean, cache = cache)
		except: Logger.error()
		return items

	def metadataUpdate(self, item, lock, locks, semaphore):
		try:
			title = item['title'] if item and 'title' in item and item['title'] else None
			year = item['year'] if item and 'year' in item and item['year'] else None

			# By default we do not cache requests to disc, since it takes longer and requires more storage space.
			# If the same movie appears multiple times in the list (some Trakt lists, eg watched list where a movie was watched twice), sub-requests will also have to be executed multiple times, since they are not disc-cached.
			# Cache in memory and use locks to block subsequent calls with the same ID/title until the first request is done and then use those results without executing all the code again.
			id = Memory.id(title = title, year = year)
			if not locks is None:
				if not id in locks:
					lock.acquire()
					if not id in locks: locks[id] = Lock()
					lock.release()
				locks[id].acquire()
				data = Memory.get(id = id, uncached = True, local = True, kodi = False)
				if Memory.cached(data):
					item.update(data)
					return

			data = {}
			ids = self.mMetatools.idMovie(title = title, year = year)
			if ids:
				data['id'] = ids
				for key, value in ids.items(): data[key] = value

			Memory.set(id = id, value = data, local = True, kodi = False)
			item.update(data)
		except:
			Logger.error()
		finally:
			if locks and id: locks[id].release()
			if semaphore: semaphore.release()

	##############################################################################
	# DIRECTORY
	##############################################################################

	def check(self, metadatas):
		if Tools.isString(metadatas):
			try: metadatas = Converter.jsonFrom(metadatas)
			except: pass
		if not metadatas:
			Loader.hide()
			Dialog.notification(title = 32007, message = 33049, icon = Dialog.IconInformation)
			return None
		return metadatas

	def directory(self, metadatas):
		metadatas = self.check(metadatas = metadatas)
		if metadatas:
			directory = Directory(content = Directory.ContentSettings, cache = True, lock = False)
			directory.addItems(items = self.mMetatools.directories(metadatas = metadatas, media = self.mMedia, kids = self.mKids))
			directory.finish()
