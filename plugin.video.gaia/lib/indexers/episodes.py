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

from lib.modules import trakt

from lib.indexers.shows import Shows
from lib.indexers.seasons import Seasons

from lib.modules.tools import System, Time, Media, Selection, Logger, Tools, Regex, Converter, Settings, Language, Math
from lib.modules.interface import Directory, Dialog, Loader, Translation
from lib.modules.cache import Cache, Memory
from lib.modules.account import Trakt, Tmdb
from lib.modules.network import Networker
from lib.modules.concurrency import Pool, Lock, Semaphore

from lib.meta.data import MetaData
from lib.meta.cache import MetaCache
from lib.meta.image import MetaImage
from lib.meta.tools import MetaTools
from lib.meta.manager import MetaManager
from lib.meta.processors.imdb import MetaImdb

class Episodes(object):

	def __init__(self, media = Media.TypeEpisode, kids = Selection.TypeUndefined):
		self.mMetatools = MetaTools.instance()
		self.mCache = Cache.instance()

		self.mDeveloper = System.developerVersion()
		self.mDetail = self.mMetatools.settingsDetail()
		self.mLimit = self.mMetatools.settingsPageEpisode()
		self.mInterleave = self.mMetatools.settingsShowInterleave()

		self.mMedia = media
		self.mKids = kids
		self.mKidsOnly = self.mMetatools.kidsOnly(kids = self.mKids)

		self.mYear = Time.year()
		self.mLanguage = self.mMetatools.settingsLanguage()

		self.mModeRelease = False
		self.mModeSearch = False
		self.mModeWatched = False

		self.mAccountTrakt = Trakt().dataUsername()
		self.mAccountTmdb = Tmdb().key()

		self.added_link = 'https://api.tvmaze.com/schedule'
		self.calendar_link = 'https://api.tvmaze.com/schedule?date=%s'
		self.webcalendar_link = 'https://api.tvmaze.com/schedule/web?date=%s'

		self.mycalendar_link = 'https://api.trakt.tv/calendars/my/shows/date[90]/97/' # Make the number of days greater than the start day.
		self.trakthistory_link = 'https://api.trakt.tv/users/me/history/shows?limit=%d' % self.mLimit
		self.progress_link = 'https://api.trakt.tv/users/me/watched/shows'
		self.hiddenprogress_link = 'https://api.trakt.tv/users/hidden/progress_watched?type=show&limit=1000000'

		self.traktwatchlist_link = 'https://api.trakt.tv/users/me/watchlist/episodes?limit=%d&page=1' % self.mLimit
		self.traktlists_link = 'https://api.trakt.tv/users/me/lists'
		self.traktlikedlists_link = 'https://api.trakt.tv/users/likes/lists?limit=10000'
		self.traktlist_link = 'https://api.trakt.tv/users/%s/lists/%s/items?limit=%d&page=1' % ('%s', '%s', self.mLimit)
		self.traktunfinished_link = 'https://api.trakt.tv/sync/playback/episodes'

	##############################################################################
	# RETRIEVE
	##############################################################################

	def retrieve(self, link = None, idImdb = None, idTvdb = None, title = None, year = None, season = None, episode = None, detailed = True, menu = True, single = False, clean = True, quick = None, limit = None, refresh = False):
		try:
			items = []
			mixed = None

			if link:
				self.mModeRelease = True

				try: link = getattr(self, link + '_link')
				except: pass

				domain = Networker.linkDomain(link, subdomain = False, topdomain = False, ip = False, scheme = False, port = False)

				if domain == 'trakt':

					if self.progress_link in link:
						mixed = True
						items = self.cache('cacheRefreshShort', refresh, self.traktListProgress, link = self.progress_link, user = self.mAccountTrakt) # Use original link, since the link passed in here can contain the limit/page.
						items = self.page(link = link, items = items, sort = 'progress')
						if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh, next = False) # 'next' was already done in self.page(). Do  not do it again, otherwise the 2nd-next episode is listed.

					elif self.mycalendar_link in link:
						mixed = True
						items = self.cache('cacheRefreshShort', refresh, self.traktList, link = self.mycalendar_link, user = self.mAccountTrakt) # Use original link, since the link passed in here can contain the limit/page.
						items = self.page(link = link, items = items, sort = 'calendar')
						if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)

					elif link and '/users/' in link:
						mixed = True # The history page can have all episodes from the same show, and then it is not automatically detected as mixed.
						items = self.cache('cacheRefreshShort', refresh, self.traktList, link = link, user = self.mAccountTrakt)
						if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)

					elif self.traktunfinished_link in link:
						#self.mModeWatched = True # Do not hide watched items, in case of a rewatch.
						items = self.cache('cacheRefreshShort', refresh, self.traktList, link = self.traktunfinished_link, user = self.mAccountTrakt) # Use original link, since the link passed in here can contain the limit/page.
						items = self.page(link = link, items = items)
						if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)

					else:
						items = self.cache('cacheRefreshShort', refresh, self.traktList, link = link, user = self.mAccountTrakt)
						if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)

				elif domain == 'tvmaze':

					if link == self.added_link:
						items = self.cache('cacheRefreshShort', refresh, self.tvmazeSchedule)
						if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)
						items = self.sort(items = items, type = 'release')

					else:
						items = self.cache('cacheRefreshShort', refresh, self.tvmazeSchedule, link = link)
						if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)

					items = self.mMetatools.filterRelease(items = items) # Must be after detailed metadata retrieval, since TVmaze has the incorrect aired date.
					items = self.mMetatools.filterDuplicate(items = items)
					if limit is None: limit = self.mMetatools.settingsPageEpisode() # Since mutiple lists are requested, there can be too many items.

			else:
				if self.mInterleave and Math.negative(season) and season == -0.0: season = -1
				items = self.metadata(idImdb = idImdb, idTvdb = idTvdb, title = title, year = year, season = season, episode = episode, clean = clean, quick = quick, refresh = refresh)

			# Limit the number of episodes shown for indirect or flattened episode menus (eg Trakt Progress list).
			# Otherwise menus with many episodes per season take too long to load and the user probably does not access the last episodes in the list anyway.
			if not limit and (not season is None and Math.negative(season)): limit = self.mMetatools.settingsPageFlatten() if (episode is None or self.mInterleave) else self.mMetatools.settingsPageMixed()

			items = self.mMetatools.filterNumber(items = items, season = season, episode = episode, single = single)
		except: Logger.error()

		return self.process(items = items, menu = menu, limit = limit, mixed = mixed, refresh = refresh)

	# kids: Filter by age restriction.
	# search: Wether or not the items are from search results.
	# duplicate: Filter out duplicates.
	# release: Filter out unreleased items. If True, return any items released before 3 hours. If date-string,return items before the date. If integer, return items older than the given number of hours.
	# limit: Limit the number of items. If True, use the setting's limit. If integer, limit up to the given number.
	def process(self, items, menu = True, kids = True, search = False, duplicate = False, release = False, limit = False, mixed = None, refresh = False):
		if items:
			if duplicate: items = self.mMetatools.filterDuplicate(items = items)

			if kids: items = self.mMetatools.filterKids(items = items, kids = self.mKids)

			if release:
				date = None
				hours = None
				if release is True: hours = 3
				elif Tools.isInteger(release) and release < 10000: hours = release
				elif release: date = release
				items = self.mMetatools.filterRelease(items = items, date = date, hours = hours)

			if limit: items = self.mMetatools.filterLimit(items = items, limit = self.mLimit if limit is True else limit)

			if items and menu:
				if refresh: # Check Context commandMetadataList() for more info.
					Loader.hide()
					Directory.refresh()
				else:
					self.menu(items, mixed = mixed)

		if not items:
			Loader.hide()
			if menu: Dialog.notification(title = 32010 if search else 32326, message = 33049, icon = Dialog.IconInformation)
		return items

	def cache(self, cache, refresh, *args, **kwargs):
		return Tools.executeFunction(self.mCache, 'cacheClear' if refresh else cache, *args, **kwargs)

	##############################################################################
	# PAGE
	##############################################################################

	def page(self, link, items, limit = None, sort = None, maximum = None):
		# Some Trakt API endpoint do not support pagination.
		# If the user has many watched shows, these list can get very long, making menu loading slow while extended metadata is retrieved.
		# Manually handle paging.

		page = 1
		if limit is None: limit = self.mMetatools.settingsPageEpisode()
		parameters = Networker.linkParameters(link = link)
		if 'limit' in parameters and 'page' in parameters: page = int(parameters['page'])
		parameters['page'] = page + 1
		parameters['limit'] = limit

		# Do not retrieve extended metadata, only get the next episode.
		if items and 'episodeLast' in items[0]: items = self.metadata(items = items, clean = False, detailed = False)

		items = items[(page - 1) * limit : page * limit]

		# Sort first, since we want to page in accordance to the user's preferred sorting.
		if sort: self.sort(items = items, type = sort)

		if len(items) >= limit and (not maximum or (page + 1) * limit <= maximum):
			next = Networker.linkCreate(link = Networker.linkClean(link, parametersStrip = True, headersStrip = True), parameters = parameters).replace('%2C', ',')
			for item in items: item['next'] = next

		return items

	##############################################################################
	# SORT
	##############################################################################

	def sort(self, items, type = 'show', force = False):
		try:
			attribute = None
			reverse = None
			if type == 'release':
				force = True
				attribute = 4
				reverse = True

			if force or Settings.getBoolean('navigation.sort.favourite'):
				attribute = Settings.getInteger('navigation.sort.favourite.%s.type' % type) if attribute is None else attribute
				reverse = Settings.getInteger('navigation.sort.favourite.%s.order' % type) == 1 if reverse is None else reverse
				if attribute > 0:
					if attribute == 1:
						if Settings.getBoolean('navigation.sort.favourite.article'):
							try: items = sorted(items, key = lambda k: Regex.remove(data = k['tvshowtitle'], expression = '(^the\s|^an?\s)', group = 1), reverse = reverse)
							except: items = sorted(items, key = lambda k: Regex.remove(data = k['title'], expression = '(^the\s|^an?\s)', group = 1), reverse = reverse)
						else:
							try: items = sorted(items, key = lambda k: k['tvshowtitle'].lower(), reverse = reverse)
							except: items = sorted(items, key = lambda k: k['title'].lower(), reverse = reverse)
					elif attribute == 2:
						for i in range(len(items)):
							if not 'rating' in items[i]: items[i]['rating'] = None
						items = sorted(items, key = lambda k: float(k['rating']), reverse = reverse)
					elif attribute == 3:
						for i in range(len(items)):
							if not 'votes' in items[i]: items[i]['votes'] = None
						items = sorted(items, key = lambda k: int(k['votes']), reverse = reverse)

					# Add he season and episode numbers.
					# This is especially important for "premiered" sorting of Trakt calendars.
					# All episodes of a show might be released on the same day and then they are listed in random order.
					# Adding the season/episode numbers first sorts by date, and then makes sure episodes from the same show are listed sequentially.
					elif attribute == 4:
						for i in range(len(items)):
							if not 'premiered' in items[i] or not items[i]['premiered']: items[i]['premiered'] = items[i]['aired'] if 'aired' in items[i] else None
						items = sorted(items, key = lambda k: '%s_%s_%s_%s' % (k['premiered'], k['tvshowtitle'], k['season'], k['episode']), reverse = reverse)
					elif attribute == 5:
						for i in range(len(items)):
							if not 'timeAdded' in items[i]: items[i]['timeAdded'] = None
						items = sorted(items, key = lambda k: '%s_%s_%s_%s' % (k['timeAdded'], k['tvshowtitle'], k['season'], k['episode']), reverse = reverse)
					elif attribute == 6:
						for i in range(len(items)):
							if not 'timeWatched' in items[i]: items[i]['timeWatched'] = None
						items = sorted(items, key = lambda k: '%s_%s_%s_%s' % (k['timeWatched'], k['tvshowtitle'], k['season'], k['episode']), reverse = reverse)
				elif reverse:
					items.reverse()
		except: Logger.error()
		return items

	##############################################################################
	# ARRIVALS
	##############################################################################

	def arrivals(self, menu = True, clean = True, detailed = True, quick = None, refresh = False):
		self.mModeRelease = True

		if self.mAccountTrakt: setting = Settings.getInteger('navigation.arrival.show.trakt')
		else: setting = Settings.getInteger('navigation.arrival.show')

		if setting == 0: return self.retrieve(link = self.added_link, menu = menu, clean = clean, detailed = detailed, quick = quick, refresh = refresh)
		elif setting == 1: return self.home(menu = menu, clean = clean, detailed = detailed, quick = quick, refresh = refresh)
		elif setting == 2: return Shows(kids = self.mKids).retrieve(link = 'airing', menu = menu, clean = clean, detailed = detailed, quick = quick, refresh = refresh)
		elif setting == 3: return self.retrieve(link = self.progress_link, menu = menu, clean = clean, detailed = detailed, quick = quick, refresh = refresh)
		elif setting == 4: return self.retrieve(link = self.mycalendar_link, menu = menu, clean = clean, detailed = detailed, quick = quick, refresh = refresh)
		else: return self.home(menu = menu, clean = clean, detailed = detailed, quick = quick, refresh = refresh)

	def home(self, menu = True, clean = True, limit = None, detailed = True, quick = None, refresh = False):
		self.mModeRelease = True

		items = self.cache('cacheRefreshShort', refresh, self.tvmazeSchedule, offset = 1)
		if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)
		items = self.sort(items = items, type = 'release')

		if limit is None: limit = self.mMetatools.settingsPageEpisode()

		# Filter by release date must be after detailed metadata retrieval, since TVmaze has the incorrect aired date.
		return self.process(items = items, menu = menu, duplicate = True, release = True, limit = limit, refresh = refresh, mixed = True)

	##############################################################################
	# CALENDAR
	##############################################################################

	def calendar(self, menu = True):
		self.mModeRelease = True

		month = Translation.string(32060).split('|')
		try: months = [(month[0], 'January'), (month[1], 'February'), (month[2], 'March'), (month[3], 'April'), (month[4], 'May'), (month[5], 'June'), (month[6], 'July'), (month[7], 'August'), (month[8], 'September'), (month[9], 'October'), (month[10], 'November'), (month[11], 'December')]
		except: months = []

		day = Translation.string(32061).split('|')
		try: days = [(day[0], 'Monday'), (day[1], 'Tuesday'), (day[2], 'Wednesday'), (day[3], 'Thursday'), (day[4], 'Friday'), (day[5], 'Saturday'), (day[6], 'Sunday')]
		except: days = []

		items = []
		for i in range(0, 30):
			try:
				date = '[B]%s:[/B] %s' % (Time.past(days = i, format = '%A'), Time.past(days = i, format = '%d %B'))
				for month in months: name = date.replace(month[1], month[0])
				for day in days: name = date.replace(day[1], day[0])

				link = self.calendar_link % Time.past(days = i, format = Time.FormatDate)

				items.append({'name' : name, 'link' : link, 'image' : 'calendar.png', 'action' : 'episodesRetrieve'})
			except: Logger.error()

		if menu: self.directory(items)
		return items

	##############################################################################
	# BINGE
	##############################################################################

	def binge(self, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, season = None, episode = None, notification = True, scrape = True):
		from lib.modules.playback import Playback
		last = Playback.instance().historyLast(imdb = idImdb, tmdb = idTmdb, tvdb = idTvdb, trakt = idTrakt, season = season, episode = episode)
		if last and 'episode' in last and not last['episode'] is None:
			season = last['season']
			episode = last['episode']
		else:
			if episode: episode = max(0, episode - 1) # Starting to binge from a specific episode.
		if season is None: season = 1
		if episode is None: episode = 0

		if scrape: Loader.show()
		metadata = self.metadataNext(idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, season = season, episode = episode)

		aired = False
		if metadata:
			premiered = None
			for i in ['aired', 'premiered']:
				if i in metadata and metadata[i]:
					premiered = metadata[i]
					break
			if premiered:
				# Check <= instead of <, since we only deal with dates and not times, hence we cannot compare on an hourly basis, but only on a daily basis.
				# Important for shows where all episodes are released on the same day.
				premiered = Time.integer(premiered)
				today = Time.integer(Time.past(hours = 3, format = Time.FormatDate))
				if premiered < today: aired = True

		if (not metadata or not aired) and notification:
			Loader.hide()
			Dialog.notification(title = 35580, message = 35587, icon = Dialog.IconWarning)
		elif metadata and scrape:
			Dialog.notification(title = 35580, message = Translation.string(35599) % (metadata['tvshowtitle'], Media.number(metadata = metadata)), icon = Dialog.IconSuccess)
			from lib.modules.core import Core
			Core(media = self.mMedia, kids = self.mKids).scrape(binge = True, tvshowtitle = metadata['tvshowtitle'], title = metadata['title'], year = metadata['year'], imdb = metadata['imdb'], tvdb = metadata['tvdb'], season = metadata['season'], episode = metadata['episode'], metadata = metadata)
		elif not scrape:
			Loader.hide()
		return metadata

	##############################################################################
	# LIST
	##############################################################################

	def listUser(self, mode = None, watchlist = False):
		items = []
		userlists = []

		if not mode is None: mode = mode.lower().strip()
		enabledTrakt = (mode is None or mode == 'trakt') and self.mAccountTrakt

		if enabledTrakt:
			try:
				lists = self.mCache.cacheRefreshShort(self.traktListUser, self.traktlists_link, self.mAccountTrakt)
				for i in range(len(lists)): lists[i]['image'] = 'traktlists.png'
				userlists += lists
			except: pass
			try:
				lists = self.mCache.cacheRefreshShort(self.traktListUser, self.traktlikedlists_link, self.mAccountTrakt)
				for i in range(len(lists)): lists[i]['image'] = 'traktlists.png'
				userlists += lists
			except: pass

		# Filter the user's own lists that were
		for i in range(len(userlists)):
			contains = False
			adapted = userlists[i]['link'].replace('/me/', '/%s/' % self.mAccountTrakt)
			for j in range(len(items)):
				if adapted == items[j]['link'].replace('/me/', '/%s/' % self.mAccountTrakt):
					contains = True
					break
			if not contains:
				items.append(userlists[i])

		for i in range(0, len(items)): items[i]['action'] = 'episodesRetrieve'

		# Watchlist
		if watchlist:
			if enabledTrakt: items.insert(0, {'name' : Translation.string(32033), 'link' : self.traktwatchlist_link, 'image': 'traktwatch.png', 'action' : 'episodesRetrieve'})

		self.directory(items)
		return items

	##############################################################################
	# TRAKT
	##############################################################################

	def traktList(self, link, user, dulicates = True, specials = False):
		list = []
		items = []
		dulicated = []

		try:
			for i in Regex.extract(data = link, expression = 'date\[(\d+)\]', group = None, all = True):
				link = link.replace('date[%s]' % i, Time.past(days = int(i), format = Time.FormatDate))

			parameters = Networker.linkParameters(link = link)
			parameters['extended'] = 'full'
			link = Networker.linkCreate(link = Networker.linkClean(link, parametersStrip = True, headersStrip = True), parameters = parameters).replace('%2C', ',')

			items = trakt.getTraktAsJson(link)
		except:
			Logger.error()
			return list

		next = None
		try:
			parameters = Networker.linkParameters(link = link)
			if 'limit' in parameters and int(parameters['limit']) == len(items):
				parameters['page'] = (int(parameters['page']) + 1) if 'page' in parameters else 2
				next = Networker.linkCreate(link = Networker.linkClean(link, parametersStrip = True, headersStrip = True), parameters = parameters).replace('%2C', ',')
		except: Logger.error()

		for item in items:
			try:
				if not 'show' in item or not 'episode' in item: continue

				tvshowtitle = item['show']['title']
				if not tvshowtitle: continue
				tvshowtitle = Networker.htmlDecode(tvshowtitle)
				tvshowtitle = Regex.remove(data = tvshowtitle, expression = '\s+[\|\[\(](us|uk|gb|au|\d{4})[\|\]\)]\s*$')

				title = item['episode']['title']
				title = Networker.htmlDecode(title)

				try:
					year = item['show']['year']
					if year > self.mYear: continue
				except: year = None

				season = item['episode']['season']
				if season is None or (not specials and season == 0): continue

				episode = item['episode']['number']
				if episode is None or (not specials and episode == 0): continue

				idImdb = item.get('show', {}).get('ids', {}).get('imdb', None)
				if idImdb: idImdb = str(idImdb)
				idTmdb = item.get('show', {}).get('ids', {}).get('tmdb', None)
				if idTmdb: idTmdb = str(idTmdb)
				idTvdb = item.get('show', {}).get('ids', {}).get('tvdb', None)
				if idTvdb: idTvdb = str(idTvdb)
				idTvrage = item.get('show', {}).get('ids', {}).get('tvrage', None)
				if idTvrage: idTvrage = str(idTvrage)
				idTrakt = item.get('show', {}).get('ids', {}).get('trakt', None)
				if idTrakt: idTrakt = str(idTrakt)

				if not idImdb and not idTvdb: continue
				if not dulicates:
					if idImdb in dulicated or idTvdb in dulicated: continue
					if idImdb: dulicated.append(idImdb)
					if idTvdb: dulicated.append(idTvdb)

				try: plot = Networker.htmlDecode(item['episode']['overview'])
				except:
					try: plot = Networker.htmlDecode(item['show']['overview'])
					except: plot = None

				try: premiered = Regex.extract(data = item['episode']['first_aired'], expression = '(\d{4}-\d{2}-\d{2})', group = 1)
				except: premiered = None

				try: added = Time.timestamp(fixedTime = item['episode']['last_updated_at'], iso = True)
				except:
					try: added = Time.timestamp(item['show']['last_updated_at'], iso = True)
					except: added = None

				try: watched = Time.timestamp(item['episode']['last_watched_at'], iso = True)
				except:
					try: watched = Time.timestamp(item['show']['last_watched_at'], iso = True)
					except: watched = None

				# This seems to be always null.
				try: rewatched = Time.timestamp(item['episode']['reset_at'], iso = True)
				except:
					try: rewatched = Time.timestamp(item['show']['reset_at'], iso = True)
					except: rewatched = None

				try: studio = item['show']['network']
				except: studio = None

				try: genre = [i.title() for i in item['show']['genres']]
				except: genre = None

				try: duration = int(item['runtime']) * 60
				except:
					try: duration = int(item['show']['runtime']) * 60
					except: duration = None

				try: rating = item['episode']['rating']
				except: rating = None

				try: votes = item['episode']['votes']
				except: votes = None

				try: mpaa = item['show']['certification']
				except: mpaa = None

				try: progress = max(0, min(1, item['progress'] / 100.0))
				except: progress = None

				list.append({
					'imdb' : idImdb,
					'tmdb' : idTmdb,
					'tvdb' : idTvdb,
					'tvrage' : idTvrage,
					'trakt' : idTrakt,

					'tvshowtitle' : tvshowtitle,
					'title' : title,
					'originaltitle' : title,
					'plot' : plot,
					'year' : year,
					'premiered' : premiered,

					'season' : season,
					'episode' : episode,

					'genre' : genre,
					'duration' : duration,
					'mpaa' : mpaa,
					'studio' : studio,
					'status' : 'Continuing',

					'timeAdded' : added,
					'timeWatched' : watched,
					'timeRewatched' : rewatched,

					'progress' : progress,
					'next' : next,

					'temp' : {
						'trakt' : {
							'rating' : rating,
							'votes' : votes,
						},
					}
				})
			except: Logger.error()

		return list

	def traktListProgress(self, link, user, filter = True):
		try:
			items = []
			link += '?extended=full'
			result = trakt.getTraktAsJson(link)

			for item in result:
				try:
					# Ignore shows where all the episodes were played, since "completed" shows should not show up in the progress list.
					# Also accomodate rewatches, that is, if all episodes were played once, and the first episode is played a second time, the show should be shown in the progress list again.
					# If all episodes where played exactly twice, etc, hide it from the progress list again.
					# This is important, otherwise if the user has 100s of fully watched shows, all the detailed metadata for all these shows will be retrieved before they are filtered out.
					# Remove them here, to reduce the number of requests that have to be made later.
					if filter:
						episodeTotal = item['show']['aired_episodes']
						episodePlays = {}
						for season in item['seasons']:
							for episode in season['episodes']:
								plays = episode['plays']
								if not plays in episodePlays: episodePlays[plays] = 0
								episodePlays[plays] += 1
						if all(plays == episodeTotal for plays in episodePlays.values()): continue

					title = item['show']['title']
					if not title: continue
					title = Networker.htmlDecode(title)
					title = Regex.remove(data = title, expression = '\s+[\|\[\(](us|uk|gb|au|\d{4})[\|\]\)]\s*$')

					try:
						year = item['show']['year']
						if year > self.mYear: continue
					except: year = None

					idImdb = item.get('show', {}).get('ids', {}).get('imdb', None)
					if idImdb: idImdb = str(idImdb)
					idTmdb = item.get('show', {}).get('ids', {}).get('tmdb', None)
					if idTmdb: idTmdb = str(idTmdb)
					idTvdb = item.get('show', {}).get('ids', {}).get('tvdb', None)
					if idTvdb: idTvdb = str(idTvdb)
					idTvrage = item.get('show', {}).get('ids', {}).get('tvrage', None)
					if idTvrage: idTvrage = str(idTvrage)
					idTrakt = item.get('show', {}).get('ids', {}).get('trakt', None)
					if idTrakt: idTrakt = str(idTrakt)

					try: added = Time.timestamp(fixedTime = item['last_updated_at'], iso = True)
					except:
						try: added = Time.timestamp(item['show']['last_updated_at'], iso = True)
						except: added = None

					try: watched = Time.timestamp(item['last_watched_at'], iso = True)
					except:
						try: watched = Time.timestamp(item['show']['last_watched_at'], iso = True)
						except: watched = None

					# This seems to be always null.
					try: rewatched = Time.timestamp(item['reset_at'], iso = True)
					except:
						try: rewatched = Time.timestamp(item['show']['reset_at'], iso = True)
						except: rewatched = None

					# Trakt only returns seasons and episodes that where watched by the user, and not all available/aired seasons and episodes.
					# There are some issues with picking the "last" episode:
					#	1. We can use the playcount and pick the episode with the lowest playcount. However, for some shows with non-sequential episodes (eg: Love Death + Robots), some users might skip an episode or watch it in a different order.
					#	2. We can use the last watched time. But in some cases if Gaia does not mark episodes as watched on Trakt, and the user manually marks them, multiple episodes might have the same watched time, or later episodes might have an earlier watched time, because the user manually marked them as watched out-of-order.
					# No solution is perfect, but the best option seems to be:
					#	1. If all playcounts are the same, pick the episode with the highest season-episode number.
					#	2. If playcounts differ, pick the last watched episode, and if there are multiple episodes with the same watched time, pick the highest season-episode number.
					episodes = []
					for season in item['seasons']:
						for episode in season['episodes']:
							episodes.append({
								'plays' : episode['plays'],
								'time' : Time.timestamp(fixedTime = episode['last_watched_at'], iso = True),
								'season' : season['number'],
								'episode' : episode['number'],
							})
					if not episodes: continue
					if len(Tools.listUnique([i['plays'] for i in episodes])) == 1: last = sorted(episodes, key = lambda i : (i['season'], i['episode']))[-1]
					else: last = sorted(episodes, key = lambda i : (i['time'], i['season'], i['episode']))[-1]

					items.append({
						'imdb' : idImdb,
						'tmdb' : idTmdb,
						'tvdb' : idTvdb,
						'tvrage' : idTvrage,
						'trakt' : idTrakt,

						'tvshowtitle' : title,
						'year' : year,

						'seasonLast' : last['season'],
						'episodeLast' : last['episode'],

						'timeAdded' : added,
						'timeWatched' : watched,
						'timeRewatched' : rewatched,
					})
				except:	Logger.error()

			try:
				result = trakt.getTraktAsJson(self.hiddenprogress_link)
				result = [str(i['show']['ids']['tvdb']) for i in result]
				items = [i for i in items if not i['tvdb'] in result]
			except: Logger.error()

			return items
		except: Logger.error()
		return None

	def traktListUser(self, link, user):
		list = []

		try: items = trakt.getTraktAsJson(link)
		except: items = None
		if not items: return list

		for item in items:
			try:
				try: name = item['list']['name']
				except: name = item['name']
				name = Networker.htmlDecode(name)

				try: link = (trakt.slug(item['list']['user']['username']), item['list']['ids']['slug'])
				except: link = ('me', item['ids']['slug'])
				link = self.traktlist_link % link

				list.append({'name': name, 'link': link})
			except: Logger.error()

		list = sorted(list, key = lambda k : Regex.remove(data = k['name'], expression = '(^the\s|^an?\s)', group = 1))
		return list

	##############################################################################
	# TVMAZE
	##############################################################################

	def tvmazeSchedule(self, link = None, normal = True, web = True, days = 3, offset = 0, limit = True):
		links = []

		if link:
			plain = Networker.linkClean(link = link, parametersStrip = True, headersStrip = True)
			parameters = Networker.linkParameters(link = link)

			if normal: links.append(Networker.linkCreate(link = Networker.linkClean(link = self.calendar_link, parametersStrip = True, headersStrip = True), parameters = parameters))
			if web: links.append(Networker.linkCreate(link = Networker.linkClean(link = self.webcalendar_link, parametersStrip = True, headersStrip = True), parameters = parameters))
		else:
			dates = []
			for i in range(offset, days + offset):
				dates.append(Time.past(days = i, format = Time.FormatDate))
				if not dates: return []

			if normal: links.extend([self.calendar_link % i for i in dates])
			if web: links.extend([self.webcalendar_link % i for i in dates])

		if not links: return []

		countries = ['us', self.mMetatools.settingsCountry()]
		for language in Language.settings():
			countries.append(language[Language.Country])
		countries = Tools.listUnique([country for country in countries if country])
		countries = countries[:3]

		temp = []
		for country in countries:
			temp.extend([link + '&country=' + country for link in links])
		links = temp

		def _tvmazeSchedule(result, link, limit):
			items = self.tvmazeList(link = link, limit = limit)
			if items: result.extend(items)

		result = []
		threads = []
		for link in links:
			threads.append(Pool.thread(target = _tvmazeSchedule, kwargs = {'result' : result, 'link' : link, 'limit' : limit}, start = True))
		[thread.join() for thread in threads]

		return result

	def tvmazeList(self, link, limit = False):
		list = []
		items = Networker().requestJson(link = link)

		if items:
			languages = [i.lower() for i in Language.settingsName()]
			today = Time.integer(Time.past(hours = 3, format = Time.FormatDate))

			for item in items:
				try:
					try: show = item['show'] # Normal schedule.
					except: show = item['_embedded']['show'] # Web schedule.

					language = show['language']
					if language:
						language = language.lower()
						if not language == 'english' and not language in languages: continue

					if limit and (not show['type'] or not 'scripted' in show['type'].lower()): continue

					tvshowtitle = show['name']
					if not tvshowtitle:	continue
					tvshowtitle = Networker.htmlDecode(tvshowtitle)

					title = item['name']
					title = Networker.htmlDecode(title)

					season = item['season']
					if not season: continue

					# TVmaze uses the year as season number for some shows (eg: Days of our Lives).
					# TVDb and Trakt use other season numbers and won't be able to find the episode details based on the year.
					if season >= 1950: continue

					episode = item['number']
					if not episode: continue

					try: premiered = item['airdate'] # This is the date the episode was aired on some network, not necessarily the date the episode was initially released.
					except: premiered = None

					try:
						year = show['premiered']
						if year: year = int(Regex.extract(data = year, expression = '(\d{4})'))
					except: year = None

					try: plot = Networker.htmlRemove(item['summary'])
					except: plot = None
					if not plot:
						try: plot = Networker.htmlRemove(show['summary'])
						except: plot = None
					if plot: plot = plot.replace('\u00a0', '')

					try:
						imdb = show['externals']['imdb']
						if imdb: imdb = str(imdb)
					except: imdb = None

					try:
						tvdb = show['externals']['thetvdb']
						if tvdb: tvdb = str(tvdb)
					except: tvdb = None

					try:
						tvrage = show['externals']['tvrage']
						if tvrage: tvrage = str(tvrage)
					except: tvrage = None

					try:
						tvmaze = show['id']
						if tvmaze: tvmaze = str(tvmaze)
					except: tvmaze = None

					try: studio = show['network']['name'] # Normal schedule.
					except:
						try: studio = show['webChannel']['name'] # Web schedule.
						except: studio = None

					try: genre = [i.title() for i in show['genres']]
					except: genre = None

					try: duration = item['runtime'] * 60
					except:
						try: duration = show['runtime'] * 60
						except:
							try: duration = show['averageRuntime'] * 60
							except: duration = None

					try: rating = item['rating']['average']
					except: rating = None
					if rating is None:
						try: rating = show['rating']['average']
						except: rating = None

					try: airsDay = show['schedule']['days']
					except: airsDay = None

					try: airsTime = show['schedule']['time']
					except: airsTime = None
					if not airsTime or airsTime == '00:00':
						try: airsTime = item['airtime']
						except: airsTime = None
					if not airsTime or airsTime == '00:00': airsTime = None

					try: airsZone = show['network']['country']['timezone']
					except: airsZone = None

					try: poster = show['image']['original']
					except: poster = None

					try: thumb = item['image']['original']
					except: thumb = None

					list.append({
						'imdb' : imdb,
						'tvdb' : tvdb,
						'tvrage' : tvrage,
						'tvmaze' : tvmaze,

						'tvshowtitle' : tvshowtitle,
						'title' : title,
						'plot' : plot,

						'season' : season,
						'episode' : episode,

						'year' : year,
						'premiered' : premiered,
						'aired' : premiered,

						'studio' : studio,
						'genre' : genre,
						'duration' : duration,

						'airs' : {
							'day' : airsDay,
							'time' : airsTime,
							'zone' : airsZone,
						},

						'temp' : {
							'tvmaze' : {
								'rating' : rating,
								'poster' : poster,
								'thumb' : thumb,
							},
						}
					})
				except: Logger.error()

		list = list[::-1]
		return list

	##############################################################################
	# PACK
	##############################################################################

	def pack(self, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, title = None, year = None, cache = True):
		if cache: return self.mCache.cacheLong(self._pack, idImdb = idImdb, idTvdb = idTvdb, title = title, year = year)
		else: return self._pack(idImdb = idImdb, idTvdb = idTvdb, title = title, year = year)

	def _pack(self, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, title = None, year = None):
		if not idTvdb:
			ids = self.metadataId(idImdb = idImdb, idTvdb = idTvdb, title = title, year = year)
			if ids:
				ids = ids['data']
				if ids and 'id' in ids:
					if not idImdb and 'imdb' in ids['id']: idImdb = ids['id']['imdb']
					if not idTmdb and 'tmdb' in ids['id']: idTmdb = ids['id']['tmdb']
					if not idTvdb and 'tvdb' in ids['id']: idTvdb = ids['id']['tvdb']
					if not idTrakt and 'trakt' in ids['id']: idTrakt = ids['id']['trakt']

		if idTvdb:
			manager = MetaManager(provider = MetaManager.ProviderTvdb)
			show = manager.show(idTvdb = idTvdb, level = MetaManager.Level4)
			if show: return self.mMetatools.pack(show = show, extended = True, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt)

		return None

	##############################################################################
	# INTERLEAVE
	##############################################################################

	def interleave(self, items):
		timeStart = None
		timeEnd = None
		timePrevious = None
		timeNext = None
		seasonLast = None
		pack = None

		result = []
		for item in items:
			time = None
			try: time = item['aired']
			except: pass
			if not time:
				try: time = item['premiered']
				except: pass
			if not 'aired' in item: item['aired'] = time
			if not 'premiered' in item: item['premiered'] = time

			if not item['season'] == 0:
				if seasonLast is None or item['season'] > seasonLast: seasonLast = item['season']
				if 'pack' in item and item['pack']: pack = item['pack']
				if time:
					time = Time.integer(time)
					if not item['season'] == 1 and (timeStart is None or time < timeStart): timeStart = time # Include all specials prior to S01E01.
					if timeEnd is None or time > timeEnd: timeEnd = time

			result.append(item)
		items = result

		if pack and seasonLast:
			seasonCurrent = None
			seasonPrevious = None
			seasonNext = None
			for season in pack['seasons']:
				if season['number'] == seasonLast: seasonCurrent = season
				elif season['number'] > 0 and season['number'] == seasonLast - 1: seasonPrevious = season
				elif season['number'] == seasonLast + 1: seasonNext = season

			if seasonCurrent:
				if seasonPrevious:
					if 'ended' in seasonPrevious and seasonPrevious['ended']: timePrevious = Time.integer(Time.format(timestamp = seasonPrevious['ended'], format = Time.FormatDate))
				else:
					timeStart = None # Is the first season. Inluce all previous specials.

				if seasonNext:
					if 'released' in seasonNext and seasonNext['released']: timeNext = Time.integer(Time.format(timestamp = seasonNext['released'], format = Time.FormatDate))
				else:
					timeEnd = None # Is the last season. Inluce all remaining specials.

		if timeStart or timeEnd:
			supplementary = self.mMetatools.settingsShowInterleaveSupplementary()
			unofficial = self.mMetatools.settingsShowInterleaveUnofficial()
			duration = self.mMetatools.settingsShowInterleaveDuration()

			average = None
			if pack:
				average = pack['duration']['mean']['main']
				if average: average *= duration

			result = []
			for item in items:
				if item['season'] == 0:
					if supplementary and (not 'story' in item or not item['story']): continue
					if unofficial and (not 'episode' in item['id'] or not 'tvdb' in item['id']['episode'] or not item['id']['episode']['tvdb']): continue
					if duration and average and (not 'duration' in item or not item['duration'] or item['duration'] < average): continue

					time = None
					try: time = item['aired']
					except: pass
					if not time:
						try: time = item['premiered']
						except: pass

					if time:
						time = Time.integer(time)
						if (timeStart is None or time >= timeStart) and (timeEnd is None or time <= timeEnd):
							result.append(item)

						# For specials between seasons, determine if the special is closer to the current or the previous/next season.
						elif (timeStart is None or time < timeStart) and timePrevious:
							differenceCurrent = abs(timeStart - time)
							differencePrevious = abs(timePrevious - time)
							if differenceCurrent < differencePrevious: result.append(item)
						elif (timeEnd is None or time > timeEnd) and timeNext:
							differenceCurrent = abs(timeEnd - time)
							differenceNext = abs(timeNext - time)
							if differenceCurrent < differenceNext: result.append(item)
				else:
					result.append(item)
		else:
			result = items

		result = sorted(result, key = lambda i : (Time.integer(i['aired']) if i['aired'] else 0, i['season'] if i['season'] else 0, i['episode'] if i['episode'] else 0))
		return result

	##############################################################################
	# METADATA
	##############################################################################

	# By default, do not cache internal requests (eg: Trakt/TVDb/IMDb/Fanart API requests).
	# For a list of 50 items, this will use an additional 8-9MB of the cache (disc space), plus it takes 4 secs longer to write to disc (the entire list takes 17-25 secs).
	# There is no real reason to cache intermediary requests, since the final processed metadata is already cached with MetaCache.
	# The only reason for intermediary caching is if the metadata is imcomplete, and on subsequent menu loading, all of the show's metadata is requested again, even though some of them might have suceeded previously.
	# quick = Quickly retrieve items from cache without holding up the process of retrieving detailed metadata in the foreground. This is useful if only a few random items are needed from the list and not all of them.
	# quick = positive integer (retrieve the given number of items in the foreground and the rest in the background), negative integer (retrieve the given number of items in the foreground and do not retrieve the rest at all), True (retrieve whatever is in the cache and the rest in the background - could return no items at all), False (retrieve whatever is in the cache and the rest not at all - could return no items at all).
	def metadata(self, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, title = None, year = None, season = None, episode = None, items = None, filter = None, clean = True, quick = None, next = True, detailed = True, refresh = False, cache = False):
		try:
			pickSingle = False
			pickSingles = False
			pickMultiple = False
			pickNext = False

			if items or (idImdb or idTvdb) or (title and year):
				if items:
					if Tools.isArray(items):
						if 'episodeLast' in items[0]: pickNext = True
						elif 'episode' in items[0]: pickSingles = True
					else:
						if 'episodeLast' in items: pickNext = True
						pickSingle = True
						items = [items]

				# Negative values mean the season offset for flattened show menus. "-0.0" means offset from the Special season.
				# Make sure this is not executed if +0.0 is passed in, meaning retrieve all episodes the Special season.
				elif not season is None and Math.negative(season):
					items = []
					limit = self.mMetatools.settingsPageFlatten() if (episode is None or self.mInterleave) else self.mMetatools.settingsPageMixed()

					if self.mInterleave: items.append({'imdb' : idImdb, 'tmdb' : idTmdb, 'tvdb' : idTvdb, 'trakt' : idTrakt, 'title' : title, 'year' : year, 'season' : 0})

					pickMultiple = True
					seasonStart = abs(int(season))
					seasonEnd = seasonStart + 2
					seasonLast = None
					episodeStart = None if episode is None else abs(int(episode))
					episodeLast = None

					specialSeason = self.mMetatools.settingsShowSpecialSeason()
					specialEpisode = self.mMetatools.settingsShowSpecialEpisode()

					# Reduce the number of seasons to retrieve if they do not exist in the first place or if they are not included in the menu.
					show = Shows().metadata(idImdb = idImdb, idTvdb = idTvdb, title = title, year = year)
					if show and 'pack' in show and show['pack']:
						seasonLast = max([i['number'] for i in show['pack']['seasons']])
						for i in show['pack']['seasons']: # Do in a separate loop, since the loop below breaks.
							if i['number'] == seasonLast: episodeLast = max([j['number'] for j in i['episodes']])

						count = 0
						for i in show['pack']['seasons']:
							if i['number'] >= seasonStart and (specialSeason or not i['number'] == 0):
								if episodeStart is None or not i['number'] == seasonStart: count += len(i['episodes'])
								else: count += len([j for j in i['episodes'] if j['number'] >= episodeStart and (specialEpisode or not j['number'] == 0)]) # Only do this for seasonStart and not subsequent seasons.
								seasonEnd = i['number'] + 1
								if count >= limit: break

					if count == 0 and limit == 0:
						seasonStart += 1
						seasonEnd = seasonStart + 1

					items.extend([{'imdb' : idImdb, 'tmdb' : idTmdb, 'tvdb' : idTvdb, 'trakt' : idTrakt, 'title' : title, 'year' : year, 'season' : i} for i in range(seasonStart, seasonEnd)])
				else:
					pickSingle = True
					items = [{'imdb' : idImdb, 'tmdb' : idTmdb, 'tvdb' : idTvdb, 'trakt' : idTrakt, 'title' : title, 'year' : year, 'season' : season}]
				if filter is None: filter = not pickSingle

				# When there is a mistake calling this function with seasonLast or episodeLast being None, it screws up the metadata saved to the database.
				# Eg: When calling metadataNext(..., season = None, episode = None), eg from binge(), typically the last season of the show this function was called on, contains all episodes of the show (similar to the Series/flattened menus).
				# If seasonLast/episodeLast was set but is None, filter out thos items.
				# Not sure if there is any place where this function is called that actually wants None for seasonLast/episodeLast?
				items = [item for item in items if (not 'seasonLast' in item or not item['seasonLast'] is None) and (not 'episodeLast' in item or not item['episodeLast'] is None)]

				lock = Lock()
				locks = {}
				semaphore = Semaphore(50)
				metacache = MetaCache.instance()

				if next and pickNext:
					threadsNext = []
					for item in items:
						semaphore.acquire()
						threadsNext.append(Pool.thread(target = self.metadataIncrement, kwargs = {'item' : item, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'cache' : cache}, start = True))
					[thread.join() for thread in threadsNext]
					items = [i for i in items if not 'invalid' in i or not i['invalid']] # No more episodes available.

				if detailed:
					metadataForeground = []
					metadataBackground = []
					threadsForeground = []
					threadsBackground = []

					items = metacache.select(type = MetaCache.TypeEpisode, items = items)

					if quick is None:
						for item in items:
							try: refreshing = item[MetaCache.Attribute][MetaCache.AttributeRefresh]
							except: refreshing = MetaCache.RefreshForeground
							if refreshing == MetaCache.RefreshForeground or refresh:
								semaphore.acquire()
								threadsForeground.append(Pool.thread(target = self.metadataUpdate, kwargs = {'item' : item, 'result' : metadataForeground, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'filter' : filter, 'cache' : cache, 'mode' : 'foreground'}, start = True))
							elif refreshing == MetaCache.RefreshBackground:
								semaphore.acquire()
								threadsBackground.append(Pool.thread(target = self.metadataUpdate, kwargs = {'item' : item, 'result' : metadataBackground, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'filter' : filter, 'cache' : cache, 'mode' : 'background'}, start = True))
					else:
						items = Tools.listShuffle(items)
						lookup = []
						counter = abs(quick) if Tools.isInteger(quick) else None
						foreground = Tools.isInteger(quick)
						background = (Tools.isInteger(quick) and quick > 0) or (quick is True)
						for item in items:
							try: refreshing = item[MetaCache.Attribute][MetaCache.AttributeRefresh]
							except: refreshing = MetaCache.RefreshForeground
							if refreshing == MetaCache.RefreshNone:
								lookup.append(item)
							elif refreshing == MetaCache.RefreshForeground and (counter is None or len(lookup) < counter):
								if foreground:
									lookup.append(item)
									semaphore.acquire()
									threadsForeground.append(Pool.thread(target = self.metadataUpdate, kwargs = {'item' : item, 'result' : metadataForeground, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'filter' : filter, 'cache' : cache, 'mode' : 'foreground'}, start = True))
							elif refreshing == MetaCache.RefreshBackground or (counter is None or len(lookup) >= counter):
								if background:
									semaphore.acquire()
									threadsBackground.append(Pool.thread(target = self.metadataUpdate, kwargs = {'item' : item, 'result' : metadataBackground, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'filter' : filter, 'cache' : cache, 'mode' : 'background'}, start = True))
						items = lookup

					# Wait for metadata that does not exist in the metacache.
					[thread.join() for thread in threadsForeground]
					if metadataForeground: metacache.insert(type = MetaCache.TypeEpisode, items = metadataForeground)

					# Let the refresh of old metadata run in the background for the next menu load.
					if threadsBackground:
						def _metadataBackground():
							[thread.join() for thread in threadsBackground]
							if metadataBackground: metacache.insert(type = MetaCache.TypeEpisode, items = metadataBackground)
						Pool.thread(target = _metadataBackground, start = True)
				else:
					return items

				if filter:
					# Remove items that do not have episodes.
					# Eg: Emmerdale 1972 has a season 53, but the last season on TVDb is 51, so no episodes are returned.
					items = [i for i in items if 'episodes' in i]

					items = [i for i in items if 'tvdb' in i and i['tvdb']]

					# Filter out episodes that do not have a TVDb or Trakt ID.
					# Otherwise episodes appearing on on IMDb, but no other provider, will show up.
					# Eg: Downton Abbey has S0E09 on IMDb, but this episode does not exist on TVDb/TMDb/Trakt. The season finale is a Christmas Special (S00E02) on TVDb/TMDb/Trakt.
					for item in items:
						if not item['season'] == 0:
							item['episodes'] = [i for i in item['episodes'] if 'tvdb' in i and 'id' in i and 'episode' in i['id'] and (('tvdb' in i['id']['episode'] and i['id']['episode']['tvdb']) or ('trakt' in i['id']['episode'] and i['id']['episode']['trakt']))]

			# Remove temporary, useless, or already aggregatd data, to keep the size of the data passed arround small.
			if clean:
				for item in items:
					try: del item['temp']
					except: pass
					try: del item[MetaCache.Attribute]
					except: pass

			# Add detailed season metadata.
			self.metadataAggregate(items = items)

			# Re-add next page to individual episodes.
			for item in items:
				if 'next' in item and 'episodes' in item:
					for episode in item['episodes']:
						episode['next'] = item['next']

			if pickSingles or pickNext:
				result = []
				for item in items:
					if 'episodes' in item:
						for episode in item['episodes']:
							if episode['season'] == item['season'] and episode['episode'] == item['episode']:
								for attribute in ['timeWatched', 'timeAdded']:
									try: episode[attribute] = item[attribute]
									except: pass
								result.append(episode)
								break
				if pickSingle: return result[0] if result else None
				else: return result
			elif pickSingle:
				if items:
					result = []
					for item in items:
						result.extend(item['episodes'])
					if episode is None: return result
					for i in result:
						if i['episode'] == episode: return i
				return None
			elif pickMultiple:
				result = []
				for item in items:
					result.extend(item['episodes'])

				# Filter here already, since the previous season might still be included in items.
				# This makes the detecting the first episode from the season in interleave() impossible.
				result = self.mMetatools.filterNumber(items = result, season = season, episode = episode)

				for item in result:
					# Add an 'empty' command to force itemNext() in MetaTools to stop scanning previous episodes.
					if (not seasonLast is None and item['season'] >= seasonLast) and (not episodeLast is None and item['episode'] >= episodeLast): command = None
					else: command = self.mMetatools.command(metadata = item, media = Media.TypeShow if episode is None else Media.TypeEpisode, submenu = True, increment = True)
					item['next'] = command

				if self.mInterleave: result = self.interleave(items = result)
				return result
			else:
				return [item['episodes'] for item in items]
		except: Logger.error()
		return None

	def metadataUpdate(self, item, result = None, lock = None, locks = None, semaphore = None, filter = None, cache = False, mode = None):
		try:
			id = None
			complete = True

			idImdb = str(item['imdb']) if item and 'imdb' in item and item['imdb'] else None
			idTmdb = str(item['tmdb']) if item and 'tmdb' in item and item['tmdb'] else None
			idTvdb = str(item['tvdb']) if item and 'tvdb' in item and item['tvdb'] else None
			idTvmaze = str(item['tvmaze']) if item and 'tvmaze' in item and item['tvmaze'] else None
			idTvrage = str(item['tvrage']) if item and 'tvrage' in item and item['tvrage'] else None
			idTrakt = str(item['trakt']) if item and 'trakt' in item and item['trakt'] else None
			idSlug = str(item['slug']) if item and 'slug' in item and item['slug'] else None

			title = item['tvshowtitle'] if item and 'tvshowtitle' in item and item['tvshowtitle'] else item['title'] if item and 'title' in item and item['title'] else None
			year = item['year'] if item and 'year' in item and item['year'] else None
			numberSeason = item['season'] if item and 'season' in item and not item['season'] is None else None

			# By default we do not cache requests to disc, since it takes longer and requires more storage space.
			# If the same show appears multiple times in the list (some Trakt lists, eg watched list where a show was watched twice), sub-requests will also have to be executed multiple times, since they are not disc-cached.
			# Cache in memory and use locks to block subsequent calls with the same ID/title until the first request is done and then use those results without executing all the code again.
			id = Memory.id(idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, idTvmaze = idTvmaze, idTvrage = idTvrage, title = title, year = year, season = numberSeason)
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

			# Trakt requires either a Trakt or IMDb ID.
			# TMDb requires a TMDb ID.
			if not idTvdb or (not idImdb and not idTrakt) or (not idTmdb and self.mDetail == MetaTools.DetailExtended):
				title = item['tvshowtitle'] if item and 'tvshowtitle' in item and item['tvshowtitle'] else item['title'] if item and 'title' in item and item['title'] else None
				year = item['year'] if 'year' in item else None
				ids = self.metadataId(idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, title = title, year = year)
				if ids:
					if not ids['complete']: complete = False
					ids = ids['data']
					if ids and 'id' in ids:
						ids = ids['id']
						if ids:
							if not idImdb and 'imdb' in ids: idImdb = ids['imdb']
							if not idTmdb and 'tmdb' in ids: idTmdb = ids['tmdb']
							if not idTvdb and 'tvdb' in ids: idTvdb = ids['tvdb']
							if not idTvmaze and 'tvmaze' in ids: idTvmaze = ids['tvmaze']
							if not idTvrage and 'tvrage' in ids: idTvrage = ids['tvrage']
							if not idTrakt and 'trakt' in ids: idTrakt = ids['trakt']
							if not idSlug and 'slug' in ids: idSlug = ids['slug']
			if filter and not idTvdb: return False

			developer = self.metadataDeveloper(idImdb = idImdb, idTvdb = idTvdb, idTrakt = idTrakt, title = title, year = year, item = item, season = numberSeason)
			if developer: Logger.log('EPISODE METADATA RETRIEVAL [%s]: %s' % (mode.upper() if mode else 'UNKNOWN', developer))

			season = Seasons().metadata(idImdb = idImdb, idTvdb = idTvdb, season = numberSeason)
			if not season:
				Memory.set(id = id, value = {}, local = True, kodi = False)
				return False

			if self.mDetail == MetaTools.DetailEssential:
				requests = [
					{'id' : 'tvdb', 'function' : self.metadataTvdb, 'parameters' : {'idImdb' : idImdb, 'idTvdb' : idTvdb, 'season' : numberSeason, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
					{'id' : 'imdb', 'function' : self.metadataImdb, 'parameters' : {'idImdb' : idImdb, 'season' : numberSeason, 'full' : False, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
					{'id' : 'tvmaze', 'function' : self.metadataTvmaze, 'parameters' : {'season' : numberSeason, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
				]
			elif self.mDetail == MetaTools.DetailStandard:
				requests = [
					{'id' : 'tvdb', 'function' : self.metadataTvdb, 'parameters' : {'idImdb' : idImdb, 'idTvdb' : idTvdb, 'season' : numberSeason, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
					{'id' : 'trakt', 'function' : self.metadataTrakt, 'parameters' : {'idImdb' : idImdb, 'idTrakt' : idTrakt, 'season' : numberSeason, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
					{'id' : 'imdb', 'function' : self.metadataImdb, 'parameters' : {'idImdb' : idImdb, 'season' : numberSeason, 'full' : False, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
					{'id' : 'tvmaze', 'function' : self.metadataTvmaze, 'parameters' : {'season' : numberSeason, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
				]
			elif self.mDetail == MetaTools.DetailExtended:
				requests = [
					{'id' : 'tvdb', 'function' : self.metadataTvdb, 'parameters' : {'idImdb' : idImdb, 'idTvdb' : idTvdb, 'season' : numberSeason, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
					{'id' : 'trakt', 'function' : self.metadataTrakt, 'parameters' : {'idImdb' : idImdb, 'idTrakt' : idTrakt, 'season' : numberSeason, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
					{'id' : 'imdb', 'function' : self.metadataImdb, 'parameters' : {'idImdb' : idImdb, 'season' : numberSeason, 'full' : True, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
					{'id' : 'tmdb', 'function' : self.metadataTmdb, 'parameters' : {'idTmdb' : idTmdb, 'season' : numberSeason, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
					{'id' : 'tvmaze', 'function' : self.metadataTvmaze, 'parameters' : {'season' : numberSeason, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
				]
			else:
				requests = []

			datas = self.metadataRetrieve(requests = requests)

			data = {'episodes' : []}
			images = {}
			votings = {}
			voting = {
				'rating' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
				'user' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
				'votes' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
			}
			for i in ['tvmaze', 'metacritic', 'imdb', 'tmdb', 'fanart', 'trakt', 'tvdb']: # Keep a specific order. Later values replace newer values.
				if i in datas:
					values = datas[i]
					if values:
						if not Tools.isArray(values): values = [values]
						for value in values:
							if not value['complete']:
								complete = False
								if developer: Logger.log('INCOMPLETE EPISODE METADATA [%s]: %s' % (i.upper(), developer))
							provider = value['provider']
							value = Tools.copy(value['data']) # Copy, since we do title/plot/studio replacement below in another loop.
							if value:
								for episode in value['episodes']:
									numberSeason = episode['season']
									numberEpisode = episode['episode']

									if MetaImage.Attribute in episode:
										if not numberSeason in images: images[numberSeason] = {}
										if not numberEpisode in images[numberSeason]: images[numberSeason][numberEpisode] = {}
										images[numberSeason][numberEpisode] = Tools.update(images[numberSeason][numberEpisode], episode[MetaImage.Attribute], none = True, lists = True, unique = False)
										del episode[MetaImage.Attribute]

									if not numberSeason in votings: votings[numberSeason] = {}
									if not numberEpisode in votings[numberSeason]: votings[numberSeason][numberEpisode] = Tools.copy(voting)
									if 'rating' in episode: votings[numberSeason][numberEpisode]['rating'][provider] = episode['rating']
									if 'ratinguser' in episode: votings[numberSeason][numberEpisode]['user'][provider] = episode['ratinguser']
									if 'votes' in episode: votings[numberSeason][numberEpisode]['votes'][provider] = episode['votes']

									found = False
									for j in data['episodes']:
										if j['season'] == numberSeason and j['episode'] == numberEpisode:
											found = True
											Tools.update(j, episode, none = True, lists = False, unique = False)
											break
									if not found: data['episodes'].append(episode)

			# Special episodes that are on Trakt, but not on TVDb, might not have certain  attributes.
			attributes = ['studio', 'genre', 'country', 'cast']
			values = {i : {} for i in attributes}
			for episode in data['episodes']:
				for attribute in attributes:
					if attribute in episode and episode[attribute]:
						if episode['season'] in values[attribute]:
							if len(str(values[attribute][episode['season']])) > len(str(episode[attribute])): continue
						values[attribute][episode['season']] = episode[attribute]
			for episode in data['episodes']:
				for attribute in attributes:
					if not attribute in episode or not episode[attribute]:
						try: episode[attribute] = values[attribute][episode['season']]
						except: pass

			for i in range(len(data['episodes'])):
				episode = data['episodes'][i]
				numberSeason = episode['season']
				numberEpisode = episode['episode']
				if numberSeason in votings and numberEpisode in votings[numberSeason]: episode['voting'] = votings[numberSeason][numberEpisode]

				data['episodes'][i] = {k : v for k, v in episode.items() if not v is None}
				episode = data['episodes'][i]

				if 'id' in episode and episode['id']:
					if not idImdb and 'imdb' in episode['id']: idImdb = episode['id']['imdb']
					if not idTmdb and 'tmdb' in episode['id']: idTmdb = episode['id']['tmdb']
					if not idTvdb and 'tvdb' in episode['id']: idTvdb = episode['id']['tvdb']
					if not idTvmaze and 'tvmaze' in episode['id']: idTvmaze = episode['id']['tvmaze']
					if not idTvrage and 'tvrage' in episode['id']: idTvrage = episode['id']['tvrage']
					if not idTrakt and 'trakt' in episode['id']: idTrakt = episode['id']['trakt']
					if not idSlug and 'slug' in episode['id']: idSlug = episode['id']['slug']
				if 'id' in season and season['id']:
					if not idImdb and 'imdb' in season['id']: idImdb = season['id']['imdb']
					if not idTmdb and 'tmdb' in season['id']: idTmdb = season['id']['tmdb']
					if not idTvdb and 'tvdb' in season['id']: idTvdb = season['id']['tvdb']
					if not idTvmaze and 'tvmaze' in season['id']: idTvmaze = season['id']['tvmaze']
					if not idTvrage and 'tvrage' in season['id']: idTvrage = season['id']['tvrage']
					if not idTrakt and 'trakt' in season['id']: idTrakt = season['id']['trakt']
					if not idSlug and 'slug' in season['id']: idSlug = season['id']['slug']

				# This is for legacy purposes, since all over Gaia the IDs are accessed at the top-level of the dictionary.
				# At some later point the entire addon should be updated to have the new ID structure
				if not 'id' in episode: episode['id'] = {}
				if idImdb: episode['id']['imdb'] = episode['imdb'] = idImdb
				if idTmdb: episode['id']['tmdb'] = episode['tmdb'] = idTmdb
				if idTvdb: episode['id']['tvdb'] = episode['tvdb'] = idTvdb
				if idTvmaze: episode['id']['tvmaze'] = episode['tvmaze'] = idTvmaze
				if idTvrage: episode['id']['tvrage'] = episode['tvrage'] = idTvrage
				if idTrakt: episode['id']['trakt'] = episode['trakt'] = idTrakt
				if idSlug: episode['id']['slug'] = episode['slug'] = idSlug

				# Use the show/season average episode duration in there is no extact duration.
				if (not 'duration' in episode or not episode['duration']) and 'durationEstimate' in episode:
					episode['duration'] = episode['durationEstimate']
					del episode['durationEstimate']

				if numberSeason in images and images[numberSeason] and numberEpisode in images[numberSeason] and images[numberSeason][numberEpisode]: MetaImage.update(media = MetaImage.MediaEpisode, images = images[numberSeason][numberEpisode], data = episode)

				# Do this before here already.
				# Otherwise a bunch of regular expressions are called every time the menu is loaded.
				self.mMetatools.cleanPlot(metadata = episode)

				# Calculate the rating here already, so that we have a default rating/votes if this metadata dictionary is passed around without being cleaned first.
				# More info under meta -> tools.py -> cleanVoting().
				self.mMetatools.cleanVoting(metadata = episode)

			# Sort so that the list is in the order of the episode numbers.
			data['episodes'].sort(key = lambda i : i['episode'])

			# Set the show details.
			if idImdb: data['imdb'] = idImdb
			if idTmdb: data['tmdb'] = idTmdb
			if idTvdb: data['tvdb'] = idTvdb
			if idTvmaze: data['tvmaze'] = idTvmaze
			if idTvrage: data['tvrage'] = idTvrage
			if idTrakt: data['trakt'] = idTrakt
			if idSlug: data['slug'] = idSlug
			title = season['tvshowtitle'] if season and 'tvshowtitle' in season else None
			if title: data['tvshowtitle'] = data['title'] = title
			year = season['year'] if season and 'year' in season else None
			if year: data['year'] = year
			if not numberSeason is None: data['season'] = numberSeason

			Memory.set(id = id, value = data, local = True, kodi = False)
			item.update(data)

			data[MetaCache.Attribute] = {MetaCache.AttributeComplete : complete}
			result.append(data)
		except:
			Logger.error()
		finally:
			if locks and id: locks[id].release()
			if semaphore: semaphore.release()

	def metadataAggregate(self, items):
		# Adding the previous/current/next season metadata to individual episodes in metadataUpdate() is a bad idea, since the metadata is saved to the MetaCache database.
		# This increases the database size to quickly grow beyond 1GB+.
		# Especially for shows with many seasons, and seasons with a lot of episodes (eg S00 - Specials), this can easily increase the database size by more than 50%.
		# Instead, retrieve the season metadata from the season table on demand and add it to the dictionary.
		# This increases processing time slightly, although only by a few ms, but saves 100s of MBs of storage space.

		# The same applies to the 'pack'.
		# For shows with many episodes (eg S00 - Specials - can sometimes have 100s of episodes), this dictionary can be very large, since the title, duration, and numbers for each episode is stored.
		# The pack can further increase the database size by more than 50%.

		# Also add season images here.
		# The image URLs do not require that much extra storage space, so its not as bad as the seasons and pack attributes.
		# However, an advantage of doing this here, is that if the season updates with new images, the episodes will always have the latest ones.

		try:
			seasons = []
			for item in items:
				try:
					try: idImdb = item['imdb']
					except: idImdb = None
					try: idTvdb = item['tvdb']
					except: idTvdb = None
					seasons.append({'imdb' : idImdb, 'tvdb' : idTvdb})
				except: Logger.error()
			seasons = Tools.listUnique(seasons)
			seasons = Seasons().metadata(items = seasons) if seasons else None

			if seasons:
				for item in items:
					try:
						try: idImdb = item['imdb']
						except: idImdb = None
						try: idTvdb = item['tvdb']
						except: idTvdb = None
						number = item['season']

						for season in seasons:
							if season:
								first = season[0]
								if ('imdb' in first and first['imdb'] and first['imdb'] == idImdb) or ('tvdb' in first and first['tvdb'] and first['tvdb'] == idTvdb):
									pack = next((i['pack'] for i in season if 'pack' in i and i['pack']), None)
									seasonCurrent = next((i for i in season if i['season'] == number), None)
									seasonPrevious = next((i for i in season if i['season'] == number - 1), None)
									seasonNext = next((i for i in season if i['season'] == number + 1), None)

									for episode in item['episodes']:
										if pack: episode['pack'] = pack
										if seasonCurrent: episode['seasonCurrent'] = seasonCurrent
										if seasonPrevious: episode['seasonPrevious'] = seasonPrevious
										if seasonNext: episode['seasonNext'] = seasonNext

										if seasonCurrent and MetaImage.Attribute in seasonCurrent:
											MetaImage.update(media = MetaImage.MediaSeason, images = Tools.copy(seasonCurrent[MetaImage.Attribute]), data = episode, category = MetaImage.MediaSeason) # Add season images.
											if MetaImage.MediaShow in seasonCurrent[MetaImage.Attribute]: MetaImage.update(media = MetaImage.MediaShow, images = Tools.copy(seasonCurrent[MetaImage.Attribute][MetaImage.MediaShow]), data = episode, category = MetaImage.MediaShow) # Add show images.

									break
					except: Logger.error()
		except: Logger.error()

	def metadataDeveloper(self, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, title = None, year = None, season = None, item = None):
		if self.mDeveloper:
			data = []

			if not idImdb and item and 'imdb' in item: idImdb = item['imdb']
			if idImdb: data.append('IMDb: ' + idImdb)

			if not idTvdb and item and 'tvdb' in item: idTvdb = item['tvdb']
			if idTvdb: data.append('TVDb: ' + idTvdb)

			if not idImdb and not idTvdb:
				if not idTrakt and item and 'trakt' in item: idTrakt = item['trakt']
				if idTrakt: data.append('Trakt: ' + idTrakt)

			if data: data = ['[%s]' % (' | '.join(data))]
			else: data = ['']

			if not title and item:
				if 'tvshowtitle' in item: title = item['tvshowtitle']
				elif 'title' in item: title = item['title']
			if not year and item and 'year' in item: year = item['year']

			if title:
				data.append(title)
				if year: data.append('(%d)' % year)
			if not season is None: data.append('Season %s' % str(int(season)))

			return ' '.join(data)
		return None

	# requests = [{'id' : required-string, 'function' : required-function, 'parameters' : optional-dictionary}, ...]
	def metadataRetrieve(self, requests):
		def _metadataRetrieve(request, result):
			try:
				if 'parameters' in request: data = request['function'](**request['parameters'])
				else: data = request['function']()
				result[request['id']] = data
			except:
				Logger.error()
				result[request['id']] = None
		result = {}
		if requests:
			threads = []
			for request in requests:
				threads.append(Pool.thread(target = _metadataRetrieve, kwargs = {'request' : request, 'result' : result}, start = True))
			[thread.join() for thread in threads]
		return result

	def metadataRequest(self, link, data = None, headers = None, method = None, cache = True):
		networker = Networker()
		if cache:
			if cache is True: cache = Cache.TimeoutLong
			result = self.mCache.cache(mode = None, timeout = cache, refresh = None, function = networker.request, link = link, data = data, headers = headers, method = method)
			if not result or result['error']['type'] in Networker.ErrorNetwork:
				# Delete the cache, otherwise the next call will return the previously failed request.
				self.mCache.cacheDelete(networker.request, link = link, data = data, headers = headers, method = method)
				return False
		else:
			result = networker.request(link = link, data = data, headers = headers, method = method)
			if not result or result['error']['type'] in Networker.ErrorNetwork: return False
		return Networker.dataJson(result['data'])

	def metadataId(self, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, title = None, year = None):
		result = self.mMetatools.idShow(idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, title = title, year = year)
		return {'complete' : True, 'data' : {'id' : result} if result else result}

	def metadataNext(self, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, title = None, year = None, season = None, episode = None, released = True):
		try:
			item = {'imdb' : idImdb, 'tmdb' : idTmdb, 'tvdb' : idTvdb, 'trakt' : idTrakt, 'title' : title, 'year' : year, 'seasonLast' : season, 'episodeLast' : episode}
			item = self.metadata(items = item)
			if item:
				premiered = None
				if not premiered and 'premiered' in item: premiered = item['premiered']
				if not premiered and 'aired' in item: premiered = item['aired']
				if not released or not premiered or Time.integer(premiered) <= Time.integer(Time.past(hours = 3, format = Time.FormatDate)): return item
		except: Logger.error()
		return None

	def metadataIncrement(self, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, title = None, year = None, season = None, episode = None, item = None, lock = None, locks = None, semaphore = None, cache = False):
		try:
			if idImdb is None: idImdb = str(item['imdb']) if item and 'imdb' in item and item['imdb'] else None
			if idTmdb is None: idTmdb = str(item['tmdb']) if item and 'tmdb' in item and item['tmdb'] else None
			if idTvdb is None: idTvdb = str(item['tvdb']) if item and 'tvdb' in item and item['tvdb'] else None
			if idTrakt is None: idTrakt = str(item['trakt']) if item and 'trakt' in item and item['trakt'] else None

			if title is None: title = item['tvshowtitle'] if item and 'tvshowtitle' in item and item['tvshowtitle'] else item['title'] if item and 'title' in item and item['title'] else None
			if year is None: year = item['year'] if item and 'year' in item and item['year'] else None

			if season is None:
				season = item['season'] if item and 'season' in item and not item['season'] is None else None
				if season is None: season = item['seasonLast'] if item and 'seasonLast' in item and not item['seasonLast'] is None else None
			if episode is None:
				episode = item['episode'] if item and 'episode' in item and not item['episode'] is None else None
				if episode is None: episode = item['episodeLast'] if item and 'episodeLast' in item and not item['episodeLast'] is None else None

			if not idTvdb:
				ids = self.metadataId(idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, title = title, year = year)
				if ids:
					ids = ids['data']
					if ids and 'id' in ids:
						ids = ids['id']
						if ids:
							if not idImdb and 'imdb' in ids: idImdb = ids['imdb']
							if not idTmdb and 'tmdb' in ids: idTmdb = ids['tmdb']
							if not idTvdb and 'tvdb' in ids: idTvdb = ids['tvdb']
							if not idTrakt and 'trakt' in ids: idTrakt = ids['trakt']
			if not idImdb and not idTvdb: return False

			id = Memory.id(idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, title = title, year = year, season = season, episode = episode)
			if not locks is None:
				if not id in locks:
					lock.acquire()
					if not id in locks: locks[id] = Lock()
					lock.release()
				locks[id].acquire()
				data = Memory.get(id = id, uncached = True, local = True, kodi = False)
				if Memory.cached(data):
					if item: item.update(data)
					return data

			developer = self.metadataDeveloper(idImdb = idImdb, idTvdb = idTvdb, idTrakt = idTrakt, title = title, year = year, item = item)
			try:
				pack = Seasons().metadata(idImdb = idImdb, idTvdb = idTvdb, season = season, cache = cache)['pack']['seasons']
				if not pack: raise Exception()
			except:
				if developer: Logger.log('CANNOT DETERMINE NEXT EPISODE: ' + developer + (' [%s]' % Media.numberUniversal(season = season, episode = episode)))
				return False

			# Retrieve the next available episode after the last watched episode.
			# If the next episode is in the same season as the last watched episode, continue like normal and retrieve all episodes for the current season.
			# If the next episode is in the next season (aka last watched episode was the last episode from the previous season), retrieve the all episodes for next season.
			seasonNext = season + 1
			episodeNext = episode + 1
			episodeFirst = 1
			found = 0

			# Next episode in the same season.
			for i in pack:
				if i['number'] == season:
					if i['episodes']:
						episodeLast = max([j['number'] for j in i['episodes']])
						if episodeNext <= episodeLast: found = 1
					break

			# First episode in the next season.
			if not found:
				for i in pack:
					if i['number'] == seasonNext:
						if i['episodes']:
							episodeLast = max([j['number'] for j in i['episodes']])
							if episodeFirst <= episodeLast: found = 2
						break

			if found == 0:
				data = {'invalid' : True}

				Memory.set(id = id, value = data, local = True, kodi = False)
				if item: item.update(data)

				if developer: Logger.log('NO NEXT EPISODE: ' + developer + (' [%s]' % Media.numberUniversal(season = season, episode = episode)))
				return None
			else:
				if found == 1: data = {'season' : season, 'episode' : episodeNext}
				elif found == 2: data = {'season' : seasonNext, 'episode' : episodeFirst}

				Memory.set(id = id, value = data, local = True, kodi = False)
				if item: item.update(data)

				if developer: Logger.log('NEXT EPISODE FOUND: ' + developer + (' [%s -> %s]' % (Media.numberUniversal(season = season, episode = episode), Media.numberUniversal(season = data['season'], episode = data['episode']))))
				return data
		except:
			Logger.error()
		finally:
			if locks and id: locks[id].release()
			if semaphore: semaphore.release()
			return None

	def metadataTrakt(self, idImdb = None, idTrakt = None, season = None, language = None, item = None, people = False, cache = False):
		complete = True
		result = None
		try:
			id = idTrakt if idTrakt else idImdb
			if id:
				translation = language and not language == Language.EnglishCode
				requests = [{'id' : 'season', 'function' : trakt.getTVSeasonSummary, 'parameters' : {'id' : id, 'season' : season, 'lang' : language if translation else None, 'full' : True, 'cache' : cache, 'failsafe' : True}}]

				# We already retrieve the cast from TMDb and those values contain thumnail images.
				# Retrieving the cast here as well will not add any new info and just prolong the request/processing time.
				# This actually gets the people for the season, since getting them for each episode requires multiple API calls.
				if people: requests.append({'id' : 'people', 'function' : trakt.getPeopleShow, 'parameters' : {'id' : id, 'season' : season, 'full' : True, 'cache' : cache, 'failsafe' : True}})

				data = self.metadataRetrieve(requests = requests)
				if data:
					dataSeason = data['season']
					dataPeople = data['people'] if people else None
					if dataSeason is False or (people and dataPeople is False): complete = False

					if dataSeason or dataPeople:
						result = {'episodes' : []}

						if dataSeason:
							for episode in dataSeason:
								resultEpisode = {}

								ids = episode.get('ids')
								if ids:
									ids = {k : str(v) for k, v in ids.items() if v}
									if ids: resultEpisode['id'] = {'episode' : ids}

								resultEpisode['season'] = episode.get('season')
								resultEpisode['episode'] = episode.get('number')

								title = episode.get('title')
								if title: resultEpisode['title'] = Networker.htmlDecode(title)

								plot = episode.get('overview')
								if plot: resultEpisode['plot'] = Networker.htmlDecode(plot)

								if 'translations' in episode and episode['translations']:
									translation = episode['translations'][0]

									title = translation.get('title')
									if title:
										if 'title' in resultEpisode: resultEpisode['originaltitle'] = resultEpisode['title']
										resultEpisode['title'] = Networker.htmlDecode(title)

									plot = translation.get('overview')
									if plot: resultEpisode['plot'] = Networker.htmlDecode(plot)

								premiered = episode.get('first_aired')
								if premiered:
									premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
									if premiered:
										resultEpisode['premiered'] = premiered
										resultEpisode['aired'] = premiered

								rating = episode.get('rating')
								if not rating is None: resultEpisode['rating'] = rating

								votes = episode.get('votes')
								if not votes is None: resultEpisode['votes'] = votes

								duration = episode.get('runtime')
								if not duration is None: resultEpisode['duration'] = duration * 60

								if dataPeople and ('crew' in dataPeople or 'cast' in dataPeople):
									if 'crew' in dataPeople:
										dataCrew = dataPeople['crew']
										if dataCrew:
											def _metadataTraktPeople(data, job):
												people = []
												if data:
													for i in data:
														if 'jobs' in i:
															jobs = i['jobs']
															if jobs and any(j.lower() in job for j in jobs):
																people.append(i['person']['name'])
												return Tools.listUnique(people)

											if 'directing' in dataCrew:
												director = _metadataTraktPeople(data = dataCrew['directing'], job = ['director'])
												if director: resultEpisode['director'] = director
											if 'writing' in dataCrew:
												writer = _metadataTraktPeople(data = dataCrew['writing'], job = ['writer', 'screenplay', 'author'])
												if writer: resultEpisode['writer'] = writer

									if 'cast' in dataPeople:
										dataCast = dataPeople['cast']
										if dataCast:
											cast = []
											order = 0
											for i in dataCast:
												if 'characters' in i and i['characters']: character = ' / '.join(i['characters'])
												else: character = None
												cast.append({'name' : i['person']['name'], 'role' : character, 'order' : order})
												order += 1
											if cast: resultEpisode['cast'] = cast

								result['episodes'].append(resultEpisode)
		except: Logger.error()
		return {'provider' : 'trakt', 'complete' : complete, 'data' : result}

	def metadataTvdb(self, idImdb = None, idTvdb = None, season = None, language = None, item = None, cache = False):
		complete = True
		result = None
		try:
			if idTvdb or idImdb:
				manager = MetaManager(provider = MetaManager.ProviderTvdb)
				show = manager.show(idTvdb = idTvdb, idImdb = idImdb, level = MetaManager.Level6, numberSeason = season, cache = cache)
				if show and show.idTvdb():
					seasons = show.season(sort = True)

					# This does not work if we only retrieve a single season.
					# Retrieving all seasons (and their episodes) takes unnecessarily long with MetaManager.Level6, since requests are not cached and each season/episode needs its own API call.
					# Instead retrieve the pack data from the MetaCache from the previous seasons.py in metadataUpdate().

					if seasons:
						showId = show.id()
						showTitle = show.titleSettings(selection = MetaData.SelectionSingle, fallback = MetaData.FallbackSecondary)
						showPlot = show.overviewSettings(selection = MetaData.SelectionSingle, fallback = MetaData.FallbackSecondary)
						showYear = show.year()
						showPremiered = show.releaseDateFirst(zone = MetaData.ZoneOriginal, format = MetaData.FormatDate)
						showAirTime = show.releaseTime(zone = MetaData.ZoneOriginal)
						showAirDay = show.releaseDay()
						showAirZone = show.releaseZoneName()
						showGenre = show.genreName()
						showMpaa = show.certificateCode(country = MetaData.CountryOriginal, selection = MetaData.SelectionSingle)
						showDuration = show.durationSeconds()
						showStatus = show.statusLabel()
						showCountry = show.releaseCountry()
						showLanguage = show.languageOriginal()
						showStudio = show.companyNameNetwork()
						showCast = show.personKodiCast()
						showDirector = show.personKodiDirector()
						showWriter = show.personKodiWriter()

						result = {'episodes' : []}
						if not Tools.isArray(seasons): seasons = [seasons]

						for season in seasons:
							seasonId = None
							seasonPlot = None
							seasonYear = None
							seasonPremiered = None
							seasonAirTime = None
							seasonAirDay = None
							seasonAirZone = None
							seasonGenre = None
							seasonMpaa = None
							seasonDuration = None
							seasonStatus = None
							seasonCountry = None
							seasonLanguage = None
							seasonStudio = None
							seasonCast = None
							seasonDirector = None
							seasonWriter = None
							seasonImage = None

							try:
								seasonId = season.id()

								seasonPlot = season.overviewSettings(selection = MetaData.SelectionSingle, fallback = MetaData.FallbackSecondary)
								if not seasonPlot: seasonPlot = showPlot

								seasonPremiered = season.releaseDateFirst(zone = MetaData.ZoneOriginal, format = MetaData.FormatDate)
								if not seasonPremiered: seasonPremiered = showPremiered
								if seasonPremiered: seasonPremiered = Regex.extract(data = seasonPremiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)

								seasonAirs = {}
								seasonAirTime = season.releaseTime(zone = MetaData.ZoneOriginal)
								if not seasonAirTime: seasonAirTime = showAirTime
								seasonAirDay = season.releaseDay()
								if not seasonAirDay: seasonAirDay = showAirDay
								seasonAirZone = season.releaseZoneName()
								if not seasonAirZone: seasonAirZone = showAirZone

								seasonGenre = season.genreName()
								if not seasonGenre: seasonGenre = showGenre

								seasonMpaa = season.certificateCode(country = MetaData.CountryOriginal, selection = MetaData.SelectionSingle)
								if not seasonMpaa: seasonMpaa = showMpaa

								seasonDuration = season.durationSeconds()
								if seasonDuration is None: seasonDuration = showDuration

								seasonStatus = season.statusLabel()
								if not seasonStatus: seasonStatus = showStatus

								seasonCountry = season.releaseCountry()
								if not seasonCountry: seasonCountry = showCountry

								seasonLanguage = season.languageOriginal()
								if not seasonLanguage: seasonLanguage = showLanguage

								seasonStudio = season.companyNameNetwork()
								if not seasonStudio: seasonStudio = showStudio

								seasonCast = season.personKodiCast()
								if not seasonCast: seasonCast = showCast

								seasonDirector = season.personKodiDirector()
								if not seasonDirector: seasonDirector = showDirector

								seasonWriter = season.personKodiWriter()
								if not seasonWriter: seasonWriter = showWriter
							except: Logger.error()

							episodes = season.episode(sort = True)
							if episodes: # Some Special or not-yet-released seasons do not have episodes.
								for episode in episodes:
									if episode: # Sometimes TVDb fails to retrieve the episode, and then the episode is None.
										try:
											resultEpisode = {}

											resultEpisode['id'] = Tools.copy(showId) # Copy, since we edit it for each episode by adding the season/episode IDs.
											if seasonId: resultEpisode['id']['season'] = seasonId
											id = episode.id()
											if id: resultEpisode['id']['episode'] = id

											resultEpisode['season'] = episode.numberSeason()
											resultEpisode['episode'] = episode.numberEpisode()

											if showTitle: resultEpisode['tvshowtitle'] = showTitle

											title = episode.titleSettings(selection = MetaData.SelectionSingle, fallback = MetaData.FallbackSecondary)
											if title: resultEpisode['title'] = title

											title = episode.titleOriginal(selection = MetaData.SelectionSingle)
											if title:
												resultEpisode['originaltitle'] = title
												if not 'title' in resultEpisode: resultEpisode['title'] = title

											plot = episode.overviewSettings(selection = MetaData.SelectionSingle, fallback = MetaData.FallbackSecondary)
											if not plot: plot = seasonPlot
											if plot: resultEpisode['plot'] = plot

											# Always use the show's year, used for search by title-and-year and for adding multiple seasons under the same tvshowtitle-and-year folder in the local library.
											if showYear: resultEpisode['year'] = showYear

											premiered = episode.releaseDateFirst(zone = MetaData.ZoneOriginal, format = MetaData.FormatDate)
											if not premiered: premiered = seasonPremiered
											if premiered:
												premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
												if premiered:
													resultEpisode['premiered'] = premiered
													resultEpisode['aired'] = premiered

											airs = {}
											airTime = episode.releaseTime(zone = MetaData.ZoneOriginal)
											if not airTime: airTime = seasonAirTime
											if airTime: airs['time'] = airTime
											airDay = episode.releaseDay()
											if not airDay: airDay = seasonAirDay
											if airDay: airs['day'] = [i.title() for i in airDay]
											airZone = episode.releaseZoneName()
											if not airZone: airZone = seasonAirZone
											if airZone: airs['zone'] = airZone
											if airs: resultEpisode['airs'] = airs

											genre = episode.genreName()
											if not genre: genre = seasonGenre
											if genre: resultEpisode['genre'] = [i.title() for i in genre]

											mpaa = episode.certificateCode(country = MetaData.CountryOriginal, selection = MetaData.SelectionSingle)
											if not mpaa: mpaa = seasonMpaa
											if mpaa: resultEpisode['mpaa'] = mpaa

											duration = episode.durationSeconds()
											if duration is None: resultEpisode['durationEstimate'] = seasonDuration
											else: resultEpisode['duration'] = duration

											status = episode.statusLabel()
											# It does not make sense to have a status for episodes.
											# It only clutters the info dialog with an extra label.
											# And Kodi docs say it is for shows only.
											#if not status: status = seasonStatus
											if status: resultEpisode['status'] = status.title()

											country = episode.releaseCountry()
											if not country: country = seasonCountry
											if country: resultEpisode['country'] = [country]

											language = episode.languageOriginal()
											if not language: language = seasonLanguage
											if language: resultEpisode['language'] = language if Tools.isArray(language) else [language]

											studio = episode.companyNameNetwork()
											if not studio: studio = seasonStudio
											if studio: resultEpisode['studio'] = studio

											cast = episode.personKodiCast()
											if not cast: cast = seasonCast
											if cast: resultEpisode['cast'] = cast

											director = episode.personKodiDirector()
											if not director: director = seasonDirector
											if director: resultEpisode['director'] = director

											writer = episode.personKodiWriter()
											if not writer: writer = seasonWriter
											if writer: resultEpisode['writer'] = writer

											special = episode.special()
											if special: resultEpisode['special'] = special
											story = episode.specialStory()
											if not story is None: resultEpisode['story'] = story

											image = {
												MetaImage.TypePoster : episode.imageKodiPoster(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
												MetaImage.TypeThumb : episode.imageKodiThumb(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
												MetaImage.TypeFanart : episode.imageKodiFanart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
												MetaImage.TypeLandscape : episode.imageKodiLandscape(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
												MetaImage.TypeBanner : episode.imageKodiBanner(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
												MetaImage.TypeClearlogo : episode.imageKodiClearlogo(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
												MetaImage.TypeClearart : episode.imageKodiClearart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
												MetaImage.TypeDiscart : episode.imageKodiDiscart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
												MetaImage.TypeKeyart : episode.imageKodiKeyart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
											}
											for k, v in image.items(): image[k] = [MetaImage.create(link = i, provider = MetaImage.ProviderTvdb) for i in v] if v else []
											if image: resultEpisode[MetaImage.Attribute] = image

											result['episodes'].append(resultEpisode)
										except: Logger.error()
		except: Logger.error()
		return {'provider' : 'tvdb', 'complete' : complete, 'data' : result}

	def metadataTmdb(self, idTmdb = None, season = None, language = None, item = None, cache = False):
		complete = True
		result = None
		try:
			if idTmdb:
				def _metadataTmdb(id, season, language = None, cache = True):
					link = 'https://api.themoviedb.org/3/tv/%s/season/%d' % (id, season)
					data = {'api_key' : self.mAccountTmdb}
					if language: data['language'] = language
					return self.metadataRequest(method = Networker.MethodGet, link = link, data = data, cache = cache)

				data = self.metadataRetrieve(requests = [
					{'id' : 'season', 'function' : _metadataTmdb, 'parameters' : {'id' : idTmdb, 'season' : season, 'language' : language, 'cache' : cache}},
				])

				if data:
					dataSeason = data['season']
					if dataSeason is False or not 'episodes' in dataSeason: complete = False

					if dataSeason and 'episodes' in dataSeason:
						result = {'episodes' : []}

						try: idSeason = str(dataSeason['id'])
						except: idSeason = None

						for episode in dataSeason['episodes']:
							resultEpisode = {}

							ids = {}
							id = episode.get('show_id')
							if id: ids['tmdb'] = str(id)
							if idSeason: ids['season'] = {'tmdb' : idSeason}
							id = episode.get('id')
							if id: ids['episode'] = {'tmdb' : str(id)}
							if ids: resultEpisode['id'] = ids

							resultEpisode['season'] = episode.get('season_number')
							resultEpisode['episode'] = episode.get('episode_number')

							title = episode.get('name')
							if title: resultEpisode['title'] = Networker.htmlDecode(title)

							plot = episode.get('overview')
							if plot: resultEpisode['plot'] = Networker.htmlDecode(plot)

							premiered = episode.get('air_date')
							if premiered:
								premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
								if premiered:
									resultEpisode['premiered'] = premiered
									resultEpisode['aired'] = premiered

							rating = episode.get('vote_average')
							if not rating is None: resultEpisode['rating'] = rating

							votes = episode.get('vote_count')
							if not votes is None: resultEpisode['votes'] = votes

							duration = episode.get('runtime')
							if duration: resultEpisode['duration'] = duration * 60

							try:
								if 'crew' in episode:
									dataCrew = episode['crew']
									if dataCrew:
										def _metadataTmdbPeople(data, department, job):
											people = []
											if data:
												for i in data:
													if 'department' in i and department == i['department'].lower():
														if 'job' in i and i['job'].lower() in job:
															people.append(i['name'])
											return Tools.listUnique(people)

										# https://api.themoviedb.org/3/configuration/jobs?api_key=xxx

										director = _metadataTmdbPeople(data = dataCrew, department = 'directing', job = ['director', 'co-director', 'series director'])
										if director: resultEpisode['director'] = director

										writer = _metadataTmdbPeople(data = dataCrew, department = 'writing', job = ['writer', 'screenplay', 'author', 'co-writer', 'original film writer', 'original film writer', 'original story', 'story'])
										if writer: resultEpisode['writer'] = writer

								if 'guest_stars' in episode:
									dataCast = episode['guest_stars']
									if dataCast:
										# https://www.themoviedb.org/talk/53c11d4ec3a3684cf4006400
										imageLink = 'https://image.tmdb.org/t/p/w%d%s'
										imageSize = {MetaImage.TypePhoto : 185}

										cast = []
										for i in dataCast:
											if 'name' in i and i['name']:
												if 'character' in i and i['character']: character = i['character']
												else: character = None
												if 'order' in i: order = i['order']
												else: order = None
												if 'profile_path' in i and i['profile_path']: thumbnail = imageLink % (imageSize[MetaImage.TypePhoto], i['profile_path'])
												else: thumbnail = None
												cast.append({'name' : i['name'], 'role' : character, 'order' : order, 'thumbnail' : thumbnail})
										if cast: resultEpisode['cast'] = cast
							except: Logger.error()

							result['episodes'].append(resultEpisode)
		except: Logger.error()
		return {'provider' : 'tmdb', 'complete' : complete, 'data' : result}

	def metadataImdb(self, idImdb = None, season = None, language = None, full = False, item = None, cache = False):
		# Only do this if there is no IMDb rating in in the item, that is, the item does not come from a IMDb list.
		# Retrieving the detailed IMDb data does not really add extra metadata above TMDb/Trakt, except for the rating/vote and the revenue (which is also on TMDb).
		# A single IMDb page is more than 200KB.
		if full and idImdb and (not item or not 'episodes' in item or not item['episodes'] or not 'temp' in item['episodes'][0] or not 'imdb' in item['episodes'][0]['temp'] or not 'rating' in item['episodes'][0]['temp']['imdb']):
			data = MetaImdb.detailsSeason(id = idImdb, season = season, cache = cache)
			if data: item = data

		results = []

		complete = True
		result = {'episodes' : []}
		try:
			if item and 'episodes' in item:
				for episode in item['episodes']:
					# Do not include special episodes from IMDb.
					# Eg: Sherlock has a S01E00 on IMDb which is the unaired pilot.
					# This episodes is listed under the Specials S00 on TVDb/Trakt.
					# Some specials are listed on IMDb (eg: Sherlock S03E00) that do not form part of TVDb/Trakt special season (Update: this episode is listed on Trakt, but for some reason is missing on TVDb).
					if episode and not episode['episode'] == 0:
						if 'season' in episode and 'episode' in episode:
							resultEpisode = Tools.copy(episode)
							try: del resultEpisode['temp']
							except: pass

							if 'temp' in episode and 'imdb' in episode['temp']:
								try:
									if 'thumbnail' in episode['temp']['imdb']:
										thumbnail = episode['temp']['imdb']['thumbnail']
										if thumbnail: resultEpisode[MetaImage.Attribute] = {MetaImage.TypeThumb : [MetaImage.create(link = thumbnail, provider = MetaImage.ProviderImdb)]}
								except: Logger.error()

								for i in ['rating', 'ratinguser', 'votes']:
									try:
										if i in episode['temp']['imdb']:
											resultEpisode[i] = episode['temp']['imdb'][i]
									except: Logger.error()

							if resultEpisode: result['episodes'].append(resultEpisode)
		except: Logger.error()
		results.append({'provider' : 'imdb', 'complete' : complete, 'data' : result if result['episodes'] else None})

		complete = True
		result = {'episodes' : []}
		try:
			if item and 'episodes' in item:
				for episode in item['episodes']:
					if episode and 'temp' in episode and 'metacritic' in episode['temp']:
						if 'season' in episode and 'episode' in episode:
							resultEpisode = {'season' : episode['season'], 'episode' : episode['episode']}
							for i in ['rating', 'ratinguser', 'votes']:
								try:
									if i in item['temp']['metacritic']:
										resultEpisode[i] = item['temp']['metacritic'][i]
								except: Logger.error()
							if resultEpisode: result['episodes'].append(resultEpisode)
		except: Logger.error()
		results.append({'provider' : 'metacritic', 'complete' : complete, 'data' : result if result['episodes'] else None})

		return results

	def metadataTvmaze(self, season = None, language = None, item = None, cache = False):
		complete = True
		result = {'episodes' : []}
		try:
			if item and 'episodes' in item:
				for episode in item['episodes']:
					if episode and 'temp' in episode and 'tvmaze' in episode['temp']:
						if 'season' in episode and 'episode' in episode:
							resultEpisode = {}

							try:
								if 'poster' in episode['temp']['tvmaze']:
									poster = episode['temp']['tvmaze']['poster']
									if poster: resultEpisode[MetaImage.Attribute] = {MetaImage.TypePoster : [MetaImage.create(link = poster, provider = MetaImage.ProviderTvmaze)]}
							except: Logger.error()

							try:
								if 'thumb' in episode['temp']['tvmaze']:
									thumb = episode['temp']['tvmaze']['thumb']
									if thumb: resultEpisode[MetaImage.Attribute] = {MetaImage.TypeThumb : [MetaImage.create(link = thumb, provider = MetaImage.ProviderTvmaze)]}
							except: Logger.error()

							for i in ['rating', 'ratinguser', 'votes']:
								try:
									if i in episode['temp']['tvmaze']:
										resultEpisode[i] = episode['temp']['tvmaze'][i]
								except: Logger.error()

							if resultEpisode: result['episodes'].append(resultEpisode)
		except: Logger.error()
		return {'provider' : 'tvmaze', 'complete' : complete, 'data' : result if result['episodes'] else None}

	##############################################################################
	# NAVIGATION
	##############################################################################

	def check(self, metadatas):
		if Tools.isString(metadatas):
			try: metadatas = Converter.jsonFrom(metadatas)
			except: pass
		if not metadatas:
			Loader.hide()
			Dialog.notification(title = 32326, message = 33049, icon = Dialog.IconInformation)
			return None
		return metadatas

	def menu(self, metadatas, mixed = None, submenu = None, next = True, recap = True, extra = True):
		metadatas = self.check(metadatas = metadatas)
		if metadatas:
			mixed = self.mMetatools.mixed(metadatas) if mixed is None else mixed
			directory = Directory(content = Directory.ContentSettings, media = Media.TypeMixed if mixed else Media.TypeEpisode, cache = True, lock = False)
			directory.addItems(items = self.mMetatools.items(metadatas = metadatas, media = self.mMedia, kids = self.mKids, mixed = mixed, submenu = submenu, next = next, recap = recap, extra = extra, hide = True, hideSearch = self.mModeSearch, hideRelease = self.mModeRelease, hideWatched = self.mModeWatched, contextPlaylist = True, contextShortcutCreate = True))
			directory.finish()

	def directory(self, metadatas):
		metadatas = self.check(metadatas = metadatas)
		if metadatas:
			directory = Directory(content = Directory.ContentSettings, cache = True, lock = False)
			directory.addItems(items = self.mMetatools.directories(metadatas = metadatas, media = self.mMedia, kids = self.mKids))
			directory.finish()

	def context(self, idImdb = None, idTvdb = None, title = None, year = None, season = None, episode = None):
		metadata = self.metadata(idImdb = idImdb, idTvdb = idTvdb, title = title, year = year, season = season, episode = episode)
		return self.mMetatools.context(metadata = metadata, media = self.mMedia, kids = self.mKids, playlist = True, shortcutCreate = True)
