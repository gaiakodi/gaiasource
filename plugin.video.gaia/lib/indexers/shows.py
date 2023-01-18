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

from lib.modules.tools import Media, Selection, Kids, Tools, Math, Time, Regex, Settings, System, Converter, Language, Logger
from lib.modules.interface import Directory, Dialog, Loader, Format, Translation
from lib.modules.convert import ConverterDuration, ConverterTime
from lib.modules.network import Networker
from lib.modules.cache import Cache, Memory
from lib.modules.clean import Genre, Title
from lib.modules.account import Trakt, Tmdb, Imdb
from lib.modules.parser import Parser, Raw
from lib.modules.concurrency import Pool, Lock, Semaphore

from lib.meta.data import MetaData
from lib.meta.cache import MetaCache
from lib.meta.image import MetaImage
from lib.meta.tools import MetaTools
from lib.meta.manager import MetaManager
from lib.meta.processors.imdb import MetaImdb
from lib.meta.processors.tmdb import MetaTmdb
from lib.meta.processors.fanart import MetaFanart

class Shows(object):

	def __init__(self, media = Media.TypeShow, kids = Selection.TypeUndefined):
		self.mMetatools = MetaTools.instance()
		self.mCache = Cache.instance()

		self.mDeveloper = System.developerVersion()
		self.mDetail = self.mMetatools.settingsDetail()
		self.mLimit = self.mMetatools.settingsPageShow()

		self.mMedia = media
		self.mKids = kids
		self.mKidsOnly = self.mMetatools.kidsOnly(kids = self.mKids)

		self.mCertificates = None
		self.mRestriction = 0

		if self.mKidsOnly:
			self.mCertificates = []
			self.mRestriction = Settings.getInteger('general.kids.restriction')
			if self.mRestriction >= 0:
				#self.mCertificates.append('TV-G') Althougn IMDb has this rating, when filtered, it returns series with other mature ratings as well.
				self.mCertificates.append('TV-Y')
			if self.mRestriction >= 1:
				self.mCertificates.append('TV-Y7')
			if self.mRestriction >= 2:
				self.mCertificates.append('TV-PG')
			if self.mRestriction >= 3:
				self.mCertificates.append('TV-13')
				self.mCertificates.append('TV-14')
			self.mCertificates = '&certificates=' + self.certificatesFormat(self.mCertificates)
		else:
			self.mCertificates = ''

		self.mYear = Time.year()
		self.mLanguage = self.mMetatools.settingsLanguage()

		self.mModeRelease = False
		self.mModeSearch = False

		self.mAccountImdb = Imdb().dataId()
		self.mAccountTmdb = Tmdb().key()
		self.mAccountTrakt = Trakt().dataUsername()

		self.tvmaze_link = 'https://www.tvmaze.com'
		self.tvmaze_info_link = 'https://api.tvmaze.com/shows/%s'

		self.search_link = 'https://api.trakt.tv/search?type=show&limit=%d&query=' % self.mMetatools.settingsPageSearch()

		self.persons_link = 'https://www.imdb.com/search/name?count=100&name='
		self.personlist_link = 'https://www.imdb.com/search/name?count=100&gender=male,female'
		self.featured_link = 'https://www.imdb.com/search/title?title_type=tvSeries,tvMiniSeries&languages=en&num_votes=100,&production_status=released&release_date=date[365],date[60]&sort=moviemeter,asc&count=%d&start=1%s' % (self.mLimit, self.mCertificates)
		self.popular_link = 'https://www.imdb.com/search/title?title_type=tvSeries,tvMiniSeries&languages=en&num_votes=100,&release_date=,date[0]&sort=moviemeter,asc&count=%d&start=1%s' % (self.mLimit, self.mCertificates)
		self.airing_link = 'https://www.imdb.com/search/title?title_type=tvEpisode&release_date=date[1],date[0]&sort=moviemeter,asc&count=%d&start=1%s' % (self.mLimit, self.mCertificates)
		self.active_link = 'https://www.imdb.com/search/title?title_type=tvSeries,tvMiniSeries&num_votes=10,&production_status=active&sort=moviemeter,asc&count=%d&start=1%s' % (self.mLimit, self.mCertificates)
		self.premiere_link = 'https://www.imdb.com/search/title?title_type=tvSeries,tvMiniSeries&languages=en&num_votes=10,&release_date=date[60],date[0]&sort=moviemeter,asc&count=%d&start=1%s' % (self.mLimit, self.mCertificates)

		if self.mKidsOnly: self.rating_link = 'https://www.imdb.com/search/title?title_type=tvSeries,tvMiniSeries&num_votes=10000,&release_date=,date[0]&sort=user_rating,desc&count=%d&start=1%s' % (self.mLimit, self.mCertificates)
		else: self.rating_link = 'https://www.imdb.com/search/title?title_type=tvSeries,tvMiniSeries&num_votes=50000,&release_date=,date[0]&sort=user_rating,desc&count=%d&start=1%s' % (self.mLimit, self.mCertificates)

		self.views_link = 'https://www.imdb.com/search/title?title_type=tvSeries,tvMiniSeries&num_votes=100,&release_date=,date[0]&sort=num_votes,desc&count=%d&start=1%s' % (self.mLimit, self.mCertificates)
		self.person_link = 'https://www.imdb.com/search/title?title_type=tvSeries,tvMiniSeries&release_date=,date[0]&role=%s&sort=year,desc&count=%d&start=1%s' % ('%s', self.mLimit, '%s')
		self.genre_link = 'https://www.imdb.com/search/title?title_type=tvSeries,tvMiniSeries&release_date=,date[0]&genres=%s&sort=moviemeter,asc&count=%d&start=1%s' % ('%s', self.mLimit, '%s')
		self.certification_link = 'https://www.imdb.com/search/title?title_type=tvSeries,tvMiniSeries&release_date=,date[0]&certificates=%s&sort=moviemeter,asc&count=%d&start=1' % ('%s', self.mLimit) # Does not use certificates, since it has it's own.
		self.trending_link = 'https://api.trakt.tv/shows/trending?limit=%d' % self.mLimit

		self.year_link = 'https://www.imdb.com/search/title?title_type=tvSeries,tvMiniSeries&languages=en&num_votes=100,&production_status=released&year=%s,%s&sort=moviemeter,asc&count=%d&start=1%s' % ('%s', '%s', self.mLimit, '%s')
		self.language_link = 'https://www.imdb.com/search/title?title_type=tvSeries,tvMiniSeries&num_votes=100,&production_status=released&languages=%s&sort=moviemeter,asc&count=%d&start=1%s' % ('%s', self.mLimit, '%s')
		self.emmies_link = 'https://www.imdb.com/search/title?title_type=tvSeries,tvMiniSeries&languages=en&production_status=released&groups=emmy_winners&sort=year,desc&count=%d&start=1%s' % (self.mLimit, self.mCertificates)

		self.random1_link = 'https://www.imdb.com/list/ls067413463/'
		self.random2_link = 'https://www.imdb.com/list/ls080165495/'
		self.random3_link = 'https://www.imdb.com/list/ls068065080/'

		self.traktlists_link = 'https://api.trakt.tv/users/me/lists'
		self.traktlikedlists_link = 'https://api.trakt.tv/users/likes/lists?limit=10000'
		self.traktlist_link = 'https://api.trakt.tv/users/%s/lists/%s/items?limit=%d&page=1' % ('%s', '%s', self.mLimit)
		self.traktcollection_link = 'https://api.trakt.tv/users/me/collection/shows'
		self.traktwatchlist_link = 'https://api.trakt.tv/users/me/watchlist?limit=%d&page=1' % self.mLimit
		self.traktrecommendations_link = 'https://api.trakt.tv/recommendations/shows' # No paging support. Only a limit of up to 100 items.

		self.imdblistname_link = 'https://www.imdb.com/list/%s/?view=detail&sort=alpha,asc&title_type=tvSeries,tvEpisode,tvMiniSeries&start=1'
		self.imdblistdate_link = 'https://www.imdb.com/list/%s/?view=detail&sort=date_added,desc&title_type=tvSeries,tvEpisode,tvMiniSeries&start=1'
		self.imdblists_link = 'https://www.imdb.com/user/%s/lists?sort=mdfd&order=desc' % self.mAccountImdb
		self.imdbcollection_link = 'https://www.imdb.com/user/%s/watchlist?sort=alpha,asc' % self.mAccountImdb
		self.imdbwatchlist_link = 'https://www.imdb.com/user/%s/watchlist?sort=date_added,desc' % self.mAccountImdb
		self.imdbratings_link = 'https://www.imdb.com/user/%s/ratings?sort=your_rating,desc&mode=detail' % self.mAccountImdb

	##############################################################################
	# RETRIEVE
	##############################################################################

	def retrieve(self, link, detailed = True, menu = True, full = False, clean = True, quick = None, refresh = False):
		try:
			items = []

			try: link = getattr(self, link + '_link')
			except: pass

			domain = Networker.linkDomain(link, subdomain = False, topdomain = False, ip = False, scheme = False, port = False)

			if domain == 'trakt':

				if '/users/' in link:
					if self.traktcollection_link in link:

						items = self.cache('cacheRefreshShort', refresh, self.traktList, link = self.traktcollection_link, user = self.mAccountTrakt)
						items = self.page(link = link, items = items)
						if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)

					else:
						# Must only check if no type is specified at the end of the link, since this function can be called for specific show, season, and episode lists.
						links = []
						if link.endswith('/watchlist/'):
							links.append(link + 'shows')
							links.append(link + 'seasons')
							links.append(link + 'episodes')
						else:
							links.append(link)

						for i in links:
							result = self.cache('cacheRefreshMini', refresh, self.traktList, link = i, user = self.mAccountTrakt)
							if result: items += result

						if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)
						items = self.sort(items = items)

				elif self.search_link in link:
					self.mModeSearch = True
					items = self.cache('cacheShort', refresh, self.traktList,  link = link, user = self.mAccountTrakt)

					# In case Trakt is down.
					if not items:
						query = Regex.extract(data = link, expression = 'query=(.*?)(?:$|&)')
						if query:
							query = Networker.linkUnquote(query)
							items = self.cache('cacheMedium', refresh, MetaTmdb.searchShow, query = query, language = self.mLanguage)

					if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)

				elif self.traktrecommendations_link in link:
					items = self.cache('cacheRefreshShort', refresh, self.traktList, link = self.traktrecommendations_link + '?limit=100', user = self.mAccountTrakt, next = False)
					items = self.page(link = link, items = items, maximum = 100)
					if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)

				else:
					items = self.cache('cacheMedium', refresh, self.traktList, link = link, user = self.mAccountTrakt)
					if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)

			elif domain == 'imdb':

				if '/user/' in link or '/list/' in link:
					items = self.cache('cacheRefreshShort', refresh, self.imdbList, link = link, full = full)
					if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)
					items = self.sort(items = items)

				else:
					items = self.cache('cacheMedium', refresh, self.imdbList, link = link, full = full)
					if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)

			elif domain == 'themoviedb':

				if MetaTmdb.LinkSearchShow in link:
					self.mModeSearch = True
					items = self.cache('cacheMedium', refresh, MetaTmdb.searchShow, link = link, language = self.mLanguage)
					if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)

			elif domain == 'tvmaze':

				items = self.cache('cacheLong', refresh, self.tvmazeList, link = link)
				if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)

		except: Logger.error()

		kids = not self.persons_link in link and not self.personlist_link in link
		search = self.search_link in link
		return self.process(items = items, menu = menu, kids = kids, search = search, refresh = refresh)

	# kids: Filter by age restriction.
	# search: Wether or not the items are from search results.
	# duplicate: Filter out duplicates.
	# release: Filter out unreleased items. If True, return any items released before 3 hours. If date-string,return items before the date. If integer, return items older than the given number of hours.
	# limit: Limit the number of items. If True, use the setting's limit. If integer, limit up to the given number.
	def process(self, items, menu = True, kids = True, search = False, duplicate = False, release = False, limit = False, refresh = False):
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
					self.menu(items)

		if not items:
			Loader.hide()
			if menu: Dialog.notification(title = 32010 if search else 32002, message = 33049, icon = Dialog.IconInformation)
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
		if limit is None: limit = self.mLimit
		parameters = Networker.linkParameters(link = link)
		if 'limit' in parameters and 'page' in parameters: page = int(parameters['page'])
		parameters['page'] = page + 1
		parameters['limit'] = limit

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

	def sort(self, items):
		try:
			if Settings.getBoolean('navigation.sort.favourite'):
				attribute = Settings.getInteger('navigation.sort.favourite.show.type')
				reverse = Settings.getInteger('navigation.sort.favourite.show.order') == 1
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
					elif attribute == 4:
						for i in range(len(items)):
							if not 'premiered' in items[i]: items[i]['premiered'] = None
						items = sorted(items, key = lambda k: k['premiered'], reverse = reverse)
					elif attribute == 5:
						for i in range(len(items)):
							if not 'added' in items[i]: items[i]['added'] = None
						items = sorted(items, key = lambda k: k['added'], reverse = reverse)
					elif attribute == 6:
						for i in range(len(items)):
							if not 'watched' in items[i]: items[i]['watched'] = None
						items = sorted(items, key = lambda k: k['watched'], reverse = reverse)
				elif reverse:
					items.reverse()
		except: Logger.error()
		return items

	##############################################################################
	# RANDOM
	##############################################################################

	def random(self, menu = True, release = True, limit = True, quick = None):
		if limit is True: limit = self.mLimit
		elif not limit: limit = 50

		limitSingle = 3
		limitLists = Math.roundUp(limit / float(limitSingle))
		if quick is None: quick = -limitSingle

		links = [
			self.random1_link,
			self.random2_link,
			self.random3_link,

			self.featured_link,
			self.rating_link,
			self.popular_link,
			self.trending_link,
			self.airing_link,
			self.active_link,
			self.premiere_link,
			self.views_link,
		]

		years = self.years(menu = False)
		if years: links.extend(Tools.listPick([i['link'] for i in years], count = 5))

		genres = self.genres(menu = False)
		if genres: links.extend(Tools.listPick([i['link'] for i in genres], count = 5))

		links = Tools.listShuffle(links)

		# First try if there are already cached lists.
		if quick is True or quick is False:
			result = []
			for link in links:
				if self.mCache.cacheExists(self.imdbList, link):
					result.append(link)
			if result:
				if len(result) < limitLists:
					for link in links:
						if not link in result:
							result.append(link)
							if len(result) >= limitLists: break
				links = result

		links = links[:limitLists]

		def _random(link, items, quick):
			result = self.mCache.cacheMedium(self.imdbList, link)
			result = self.metadata(items = result, quick = quick)
			if result: items.extend(result)

		items = []
		threads = [Pool.thread(target = _random, kwargs = {'link' : link, 'items' : items, 'quick' : quick}, start = True) for link in links]
		[thread.join() for thread in threads]

		items = self.mMetatools.filterDuplicate(items = items)
		for item in items: item['next'] = System.command(action = 'showsRandom')
		items = Tools.listShuffle(items)

		return self.process(items = items, menu = menu, release = 24 if release is True else release, limit = limit)

	##############################################################################
	# SEARCH
	##############################################################################

	def search(self, terms = None):
		try:
			from lib.modules.search import Searches

			if terms:
				if not terms: return None
				Loader.show()
				Searches().updateShows(terms)
			else:
				terms = Dialog.input(title = 32010)
				if not terms: return None
				Loader.show()
				Searches().insertShows(terms, self.mKids)

			# Use executeContainer() instead of directly calling retrieve().
			# This is important for shows. Otherwise if you open the season menu of a searched show and go back to the previous menu, the search dialog pops up again.
			link = self.search_link + Networker.linkQuote(terms, plus = True)
			System.executeContainer(action = 'showsRetrieve', parameters = {'link' : link, 'media' : self.mMedia, 'kids' : self.mKids})
			#return self.retrieve(link)
		except:
			Logger.error()
			return None

	##############################################################################
	# NETWORK
	##############################################################################

	def networks(self):
		networks = []

		if not self.mKidsOnly or self.mRestriction >= 0:
			networks.extend([
				('Cartoon Network', '/networks/11/cartoon-network'),
				('Disney Channel', '/networks/78/disney-channel'),
				('Disney XD', '/networks/25/disney-xd'),
				('Nickelodeon', '/networks/27/nickelodeon'),
			])
		if not self.mKidsOnly or self.mRestriction >= 1:
			networks.extend([
				('Animal Planet', '/networks/92/animal-planet'),
			])
		if not self.mKidsOnly or self.mRestriction >= 2:
			networks.extend([
				('National Geographic', '/networks/42/national-geographic-channel'),
			])
		if not self.mKidsOnly or self.mRestriction >= 3:
			networks.extend([
				('Discovery Channel', '/networks/66/discovery-channel'),
				('History Channel', '/networks/53/history'),
				('MTV', '/networks/22/mtv'),
			])
		if not self.mKidsOnly:
			networks.extend([
				('A&E', '/networks/29/ae'),
				('ABC', '/networks/3/abc'),
				('AMC', '/networks/20/amc'),
				('AT-X', '/networks/167/at-x'),
				('Adult Swim', '/networks/10/adult-swim'),
				('Amazon', '/webchannels/3/amazon'),
				('Audience', '/networks/31/audience-network'),
				('BBC America', '/networks/15/bbc-america'),
				('BBC Four', '/networks/51/bbc-four'),
				('BBC One', '/networks/12/bbc-one'),
				('BBC Three', '/webchannels/71/bbc-three'),
				('BBC Two', '/networks/37/bbc-two'),
				('BET', '/networks/56/bet'),
				('Bravo', '/networks/52/bravo'),
				('CBC', '/networks/36/cbc'),
				('CBS', '/networks/2/cbs'),
				('CTV', '/networks/48/ctv'),
				('CW', '/networks/5/the-cw'),
				('CW Seed', '/webchannels/13/cw-seed'),
				('Channel 4', '/networks/45/channel-4'),
				('Channel 5', '/networks/135/channel-5'),
				('Cinemax', '/networks/19/cinemax'),
				('Comedy Central', '/networks/23/comedy-central'),
				('Crackle', '/webchannels/4/crackle'),
				('Discovery ID', '/networks/89/investigation-discovery'),
				('E! Entertainment', '/networks/43/e'),
				('E4', '/networks/41/e4'),
				('FOX', '/networks/4/fox'),
				('FX', '/networks/13/fx'),
				('Freeform', '/networks/26/freeform'),
				('HBO', '/networks/8/hbo'),
				('HGTV', '/networks/192/hgtv'),
				('Hallmark', '/networks/50/hallmark-channel'),
				('ITV', '/networks/35/itv'),
				('Lifetime', '/networks/18/lifetime'),
				('NBC', '/networks/1/nbc'),
				('Netflix', '/webchannels/1/netflix'),
				('PBS', '/networks/85/pbs'),
				('Showtime', '/networks/9/showtime'),
				('Sky1', '/networks/63/sky-1'),
				('Starz', '/networks/17/starz'),
				('Sundance', '/networks/33/sundance-tv'),
				('Syfy', '/networks/16/syfy'),
				('TBS', '/networks/32/tbs'),
				('TLC', '/networks/80/tlc'),
				('TNT', '/networks/14/tnt'),
				('TV Land', '/networks/57/tvland'),
				('Travel Channel', '/networks/82/travel-channel'),
				('TruTV', '/networks/84/trutv'),
				('USA', '/networks/30/usa-network'),
				('VH1', '/networks/55/vh1'),
				('WGN', '/networks/28/wgn-america'),
			])

		networks = sorted(networks, key = lambda i : i[0])

		items = []
		for i in networks: items.append({'name' : i[0], 'link' : self.tvmaze_link + i[1], 'image' : 'networks.png', 'action' : 'showsRetrieve'})
		self.directory(items)
		return items

	##############################################################################
	# GENRE
	##############################################################################

	def genres(self, menu = True):
		genres = []

		if not self.mKidsOnly or self.mRestriction >= 0:
			genres.extend([
				('Adventure', 'adventure'),
				('Animation', 'animation'),
				('Biography', 'biography'),
				('Comedy', 'comedy'),
				('Drama', 'drama'),
				('Family', 'family'),
				('Fantasy', 'fantasy'),
				('Game Show', 'game_show'),
				('History', 'history'),
				('Music ', 'music'),
				('Musical', 'musical'),
				('Sport', 'sport'),
			])
		if not self.mKidsOnly or self.mRestriction >= 1:
			genres.extend([
				('Mystery', 'mystery'),
				('Romance', 'romance'),
				('Science Fiction', 'sci_fi'),
			])
		if not self.mKidsOnly or self.mRestriction >= 2:
			genres.extend([
				('Action', 'action'),
				('Crime', 'crime'),
				('News', 'news'),
				('Reality Show', 'reality_tv'),
				('Talk Show', 'talk_show'),
				('Thriller', 'thriller'),
				('Western', 'western'),
			])
		if not self.mKidsOnly or self.mRestriction >= 3:
			genres.extend([
				('Horror', 'horror'),
				('War', 'war'),
				('Film Noir', 'film_noir'),
			])

		items = []
		genres = sorted(genres, key = lambda i : i[0])
		for i in genres: items.append({'name': Genre.translate(genre = i[0], language = self.mLanguage), 'link': self.genre_link % (i[1], self.mCertificates), 'image': 'genres.png', 'action': 'showsRetrieve'})
		if menu: self.directory(items)
		return items

	##############################################################################
	# LANGUAGE
	##############################################################################

	def languages(self):
		items = []
		languages = Language.languages(universal = False)
		for i in languages: items.append({'name': i['name'][Language.NameEnglish], 'link': self.language_link % (i['code'][Language.CodePrimary], self.mCertificates), 'image': 'languages.png', 'action': 'showsRetrieve'})
		self.directory(items)
		return items

	##############################################################################
	# CERTIFICATION
	##############################################################################

	def certifications(self):
		certificates = []
		if not self.mKidsOnly or self.mRestriction >= 0: certificates.append(('Child Audience (Y)', 'TV-Y'))
		if not self.mKidsOnly or self.mRestriction >= 1: certificates.append(('Young Audience (Y7)', 'TV-Y7'))
		if not self.mKidsOnly or self.mRestriction >= 2: certificates.append(('Parental Guidance (PG)', 'TV-PG'))
		if not self.mKidsOnly or self.mRestriction >= 3: certificates.append(('Youth Audience (14)', ('TV-13', 'TV-14')))
		if not self.mKidsOnly: certificates.append(('Mature Audience (MA)', 'TV-MA'))

		items = []
		for i in certificates: items.append({'name': str(i[0]), 'link': self.certification_link % self.certificatesFormat(i[1]), 'image': 'certificates.png', 'action': 'showsRetrieve'})
		self.directory(items)
		return items

	def certificatesFormat(self, certificates):
		base = 'US%3A'
		if not Tools.isArray(certificates): certificates = [certificates]
		return ','.join([base + i.upper() for i in certificates])

	def age(self):
		certificates = []
		if not self.mKidsOnly or self.mRestriction >= 0: certificates.append(('Minor (1+)', 'TV-Y'))
		if not self.mKidsOnly or self.mRestriction >= 1: certificates.append(('Young (7+)', 'TV-Y7'))
		if not self.mKidsOnly or self.mRestriction >= 2: certificates.append(('Teens (10+)', 'TV-PG'))
		if not self.mKidsOnly or self.mRestriction >= 3: certificates.append(('Youth (13+)', ('TV-13', 'TV-14')))
		if not self.mKidsOnly: certificates.append(('Mature (18+)', 'TV-MA'))

		items = []
		for i in certificates: items.append({'name': str(i[0]), 'link': self.certification_link % self.certificatesFormat(i[1]), 'image': 'age.png', 'action': 'showsRetrieve'})
		self.directory(items)
		return items

	##############################################################################
	# YEAR
	##############################################################################

	def years(self, menu = True):
		items = []
		for i in range(self.mYear - 0, self.mYear - 100, -1): items.append({'name': str(i), 'link': self.year_link % (str(i), str(i), self.mCertificates), 'image': 'calendar.png', 'action': 'showsRetrieve'})
		if menu: self.directory(items)
		return items

	def year(self, year, menu = True, refresh = False):
		return self.retrieve(self.year_link % (str(year), str(year), self.mCertificates), menu = menu, refresh = refresh)

	##############################################################################
	# PEOPLE
	##############################################################################

	def persons(self, link = None):
		if link: items = self.mCache.cacheShort(self.imdbListPerson, link)
		else: items = self.mCache.cacheMedium(self.imdbListPerson, self.personlist_link)

		if items:
			for i in range(0, len(items)): items[i].update({'action': 'showsRetrieve', 'media' : self.mMedia})
			self.directory(items)
		else:
			Loader.hide()
			Dialog.notification(title = 32010, message = 33049, icon = Dialog.IconInformation)

		return items

	def person(self, terms = None):
		try:
			from lib.modules.search import Searches

			if terms:
				if not terms: return None
				Searches().updatePeople(terms)
			else:
				terms = Dialog.keyboard(title = 32010)
				if not terms: return None
				Searches().insertPeople(terms, self.mKids)

			# Use executeContainer() instead of directly calling retrieve().
			# This is important for shows. Otherwise if you open the season menu of a searched show and go back to the previous menu, the search dialog pops up again.
			link = self.persons_link + Networker.linkQuote(terms, plus = True)
			System.executeContainer(action = 'showsPersons', parameters = {'link' : link, 'media' : self.mMedia, 'kids' : self.mKids})
			#self.persons(link)
		except: Logger.error()

	##############################################################################
	# LIST
	##############################################################################

	def listUser(self, mode = None, watchlist = False):
		items = []
		userlists = []

		if not mode is None: mode = mode.lower().strip()
		enabledTrakt = (mode is None or mode == 'trakt') and self.mAccountTrakt
		enabledImdb = (mode is None or mode == 'imdb') and self.mAccountImdb

		if enabledImdb:
			try:
				lists = self.mCache.cacheRefreshShort(self.imdbListUser, self.imdblists_link)
				for i in range(len(lists)): lists[i].update({'image': 'imdblists.png'})
				userlists += lists
			except: pass

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

		for i in range(len(items)): items[i]['action'] = 'showsRetrieve'

		# Watchlist
		if watchlist:
			if enabledImdb: items.insert(0, {'name' : Translation.string(32033), 'link' : self.imdbwatchlist_link, 'image' : 'imdbwatch.png', 'action' : 'showsRetrieve'})
			if enabledTrakt: items.insert(0, {'name' : Translation.string(32033), 'link' : self.traktwatchlist_link.replace('me/watchlist', 'me/watchlist/shows'), 'image' : 'traktwatch.png', 'action' : 'showsRetrieve'})

		self.directory(items)
		return items

	##############################################################################
	# TRAKT
	##############################################################################

	def traktList(self, link, user, dulicates = False, next = True):
		list = []
		items = []
		dulicated = []

		try:
			parameters = Networker.linkParameters(link = link)
			parameters['extended'] = 'full'
			linkNew = Networker.linkCreate(link = Networker.linkClean(link, parametersStrip = True, headersStrip = True), parameters = parameters).replace('%2C', ',')
			result = trakt.getTraktAsJson(linkNew)

			for i in result:
				try: items.append(i['show'])
				except: pass
			if not items: items = result
		except:
			Logger.error()
			return list

		if next:
			next = None
			try:
				parameters = Networker.linkParameters(link = link)
				if 'limit' in parameters and int(parameters['limit']) == len(items):
					parameters['page'] = (int(parameters['page']) + 1) if 'page' in parameters else 2
					next = Networker.linkCreate(link = Networker.linkClean(link, parametersStrip = True, headersStrip = True), parameters = parameters).replace('%2C', ',')
			except: Logger.error()
		else:
			next = None

		for item in items:
			try:
				title = item['title']
				title = Networker.htmlDecode(title)
				title = Regex.remove(data = title, expression = '\s+[\|\[\(](us|uk|gb|au|\d{4})[\|\]\)]\s*$')

				try:
					year = item['year']
					if year > self.mYear: continue
				except: year = None

				idImdb = item.get('ids', {}).get('imdb', None)
				if idImdb: idImdb = str(idImdb)
				idTmdb = item.get('ids', {}).get('tmdb', None)
				if idTmdb: idTmdb = str(idTmdb)
				idTvdb = item.get('ids', {}).get('tvdb', None)
				if idTvdb: idTvdb = str(idTvdb)
				idTvrage = item.get('ids', {}).get('tvrage', None)
				if idTvrage: idTvrage = str(idTvrage)
				idTrakt = item.get('ids', {}).get('trakt', None)
				if idTrakt: idTrakt = str(idTrakt)

				if not idImdb and not idTvdb: continue
				if not dulicates:
					if idImdb in dulicated or idTvdb in dulicated: continue
					if idImdb: dulicated.append(idImdb)
					if idTvdb: dulicated.append(idTvdb)

				try: plot = Networker.htmlDecode(item['overview'])
				except: plot = None

				try: premiered = Regex.extract(data = item['first_aired'], expression = '(\d{4}-\d{2}-\d{2})', group = 1)
				except: premiered = None

				try: studio = item['network']
				except: studio = None

				try: genre = [i.title() for i in item['genres']]
				except: genre = None

				try: duration = int(item['runtime']) * 60
				except: duration = None

				try: rating = item['rating']
				except: rating = None

				try: votes = item['votes']
				except: votes = None

				try: mpaa = item['certification']
				except: mpaa = None

				list.append({
					'imdb' : idImdb,
					'tmdb' : idTmdb,
					'tvdb' : idTvdb,
					'tvrage' : idTvrage,
					'trakt' : idTrakt,

					'title' : title,
					'originaltitle' : title,
					'plot' : plot,
					'year' : year,
					'premiered' : premiered,

					'genre' : genre,
					'duration' : duration,
					'mpaa' : mpaa,
					'studio' : studio,

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
	# IMDB
	##############################################################################

	def imdbRequest(self, link):
		return MetaImdb.retrieve(link = link, full = True) # Adds additional headers.

	def imdbPrivacy(self, full, link, rating):
		self.mImdbPublic = False
		if not full:
			self.mCache.cacheDelete(self.imdbListId, link)
			Dialog.confirm(title = 32034, message = 35609 if rating else 35608)
		return Cache.Skip

	def imdbPublic(self):
		return self.mImdbPublic

	def imdbListId(self, link):
		try:
			networker = self.imdbRequest(link = link)
			result = networker.responseDataText()
			try: result = result.decode('iso-8859-1')
			except: pass
			return Raw.parse(data = result, tag = 'meta', extract = 'content', attributes = {'property': 'pageId'})[0]
		except: return None

	def imdbList(self, link, full = False):
		list = []
		items = []
		duplicates = []
		isRating = '/ratings' in link
		isOwn = '/user/' in link

		matches = Regex.extract(data = link, expression = 'date\[(\d+)\]', group = None, all = True)
		for i in matches: link = link.replace('date[%s]' % i, Time.past(days = int(i), format = Time.FormatDate))
		linkOriginal = link

		self.mImdbPublic = True
		while True:
			try:
				next = None
				id = None

				if link == self.imdbcollection_link:
					id = self.mCache.cacheMedium(self.imdbListId, link)
					if id: link = self.imdblistname_link % id
				elif link == self.imdbwatchlist_link:
					id = self.mCache.cacheMedium(self.imdbListId, link)
					if id: link = self.imdblistdate_link % id

				if isOwn and not isRating and (not id or id.startswith('ur')):
					if not items: return self.imdbPrivacy(full = full, link = linkOriginal, rating = isRating)
					else: break

				networker = self.imdbRequest(link = link)
				if isOwn and networker.responseErrorCode() == 403:
					if not items: return self.imdbPrivacy(full = full, link = linkOriginal, rating = isRating)
					else: break

				result = networker.responseDataText().replace('\n','')
				try: result = result.decode('iso-8859-1')
				except: pass

				items += Raw.parse(data = result, tag = 'div', attributes = {'class': '.+? lister-item'}) + Raw.parse(data = result, tag = 'div', attributes = {'class': 'lister-item .+?'})
				items += Raw.parse(data = result, tag = 'div', attributes = {'class': 'list_item.+?'})
			except:
				Logger.error()
				return None

			try:
				# HTML syntax error, " directly followed by attribute name. Insert space in between. Raw.parse can otherwise not handle it.
				result = result.replace('"class="lister-page-next', '" class="lister-page-next')
				next = Raw.parse(data = result, tag = 'a', extract = 'href', attributes = {'class': '.*?lister-page-next.*?'})

				if not next:
					next = Raw.parse(data = result, tag = 'div', attributes = {'class': 'pagination'})[0]
					next = zip(Raw.parse(data = next, tag = 'a', extract = 'href'), Raw.parse(data = next, tag = 'a'))
					next = [i[0] for i in next if 'Next' in i[1]]

				parameters = Networker.linkParameters(link = next[0])
				next = Networker.linkCreate(link = Networker.linkClean(link, parametersStrip = True, headersStrip = True), parameters = parameters)
				next = Networker.htmlDecode(next)
			except:
				next = None

			if not full or not next: break
			link = next

		for item in items:
			try:
				skip = True
				try:
					# Years that contain extra parts, like "Video Game" or "2019-" or "2011-2018".
					year = Raw.parse(data = item, tag = 'span', attributes = {'class' : '.*lister-item-year.*'})[0]
					if not year: year = Raw.parse(data = item, tag = 'span', attributes = {'class': 'year_type'})[0]
					if Regex.match(data = year, expression = 'game'): continue # (2018 Video Game)
					if Regex.match(data = year, expression = '\(\d{4}.*\d{4}\)'): skip = False
					year = int(Regex.extract(data = year, expression = '(\d{4})', group = 1))
					if year > self.mYear: continue
				except: year = None

				if isRating: # Rating lists cannot be filtered according to movie/show type using GET parameters.
					# Some lists contain movies.
					if 'Movie:' in item: continue

					if skip:
						try:
							duration = Regex.extract(data = item, expression = '((\d+\shr\s)?\d+\smin)', group = 1)
							duration = ConverterDuration(value = duration).value(ConverterDuration.UnitSecond)
							if duration > 18000: skip = False
						except: pass
					if skip: continue

				imdb = Raw.parse(data = item, tag = 'div', attributes = {'class': '.*lister-item-content.*'})[0] # Find the show ID, and not the episode ID if present.
				imdb = Raw.parse(data = imdb, tag = 'a', extract = 'href')[0]
				imdb = Regex.extract(data = imdb, expression = '(tt\d+)', group = 1)
				if imdb in duplicates: continue
				duplicates.append(imdb)

				title = Raw.parse(data = item, tag = 'a')[1]
				title = Networker.htmlDecode(title)

				# Raw.parse cannot handle elements without a closing tag.
				#try: poster = Raw.parse(data = item, tag = 'img', extract = 'loadlate')[0]
				#except: poster = None
				try:
					html = Parser(item)
					poster = html.find_all('img')[0]['loadlate']
					if poster:
						if '/nopicture/' in poster: poster = None
						if poster: poster = MetaImdb.image(Networker.htmlDecode(poster))
					else: poster = None
				except: poster = None

				try:
					genre = Raw.parse(data = item, tag = 'span', attributes = {'class' : 'genre'})[0]
					genre = [i.strip() for i in genre.split(',')]
					genre = [Networker.htmlDecode(i) for i in genre if i]
				except: genre = None

				try:
					mpaa = Raw.parse(data = item, tag = 'span', attributes = {'class' : 'certificate'})[0]
					if not mpaa or mpaa == 'NOT_RATED': mpaa = None
					else: mpaa = Networker.htmlDecode(mpaa.replace('_', '-'))
				except: mpaa = None

				try:
					duration = Regex.extract(data = item, expression = '((\d+\shr\s)?\d+\smin)', group = 1)
					duration = ConverterDuration(value = duration).value(ConverterDuration.UnitSecond)
				except: duration = None

				rating = None
				try: rating = float(Raw.parse(data = item, tag = 'span', attributes = {'class' : 'rating-rating'})[0])
				except:
					try: rating = float(Raw.parse(data = rating, tag = 'span', attributes = {'class' : 'value'})[0])
					except:
						try: rating = float(Raw.parse(data = item, tag = 'div', extract = 'data-value', attributes = {'class' : '.*?imdb-rating'})[0])
						except: pass
				if not rating:
					try:
						rating = Raw.parse(data = item, tag = 'span', attributes = {'class' : 'ipl-rating-star__rating'})[0]
						if not rating or rating == '' or rating == '-': rating = None
						else: rating = float(rating)
					except: rating = None

				# Do not do this for other lists, since the alternative rating might be from a different user (creator of the list) and will incorrectly overwrite the current user's rating.
				# Also ingore individual episodes, since the season and episode numbers are unknown.
				ratinguser = None
				if isOwn and (not isRating or not 'Episode:' in item):
					try:
						ratinguser = Raw.parse(data = Raw.parse(data = item, tag = 'div', attributes = {'class' : '.*?ipl-rating-star--other-user.*?'})[0], tag = 'span', attributes = {'class' : 'ipl-rating-star__rating'})[0]
						if not ratinguser or ratinguser == '' or ratinguser == '-': ratinguser = None
						else: ratinguser = float(ratinguser)
					except: ratinguser = None

				ratingtime = None
				try: ratingtime = ConverterTime(Regex.extract(data = item, expression = 'rated\son\s(.*?)<', group = 1), format = ConverterTime.FormatDateShort).timestamp()
				except: pass

				ratingmetacritic = None
				try:
					ratingmetacritic = Raw.parse(data = item, tag = 'span', attributes = {'class' : '.*?[^-]metascore.*?'})[0]
					if not ratingmetacritic or ratingmetacritic == '' or ratingmetacritic == '-': ratingmetacritic = None
					else: ratingmetacritic = float(ratingmetacritic) / 10.0 # Out of 100 and not out of 10.
				except: ratingmetacritic = None

				votes = None
				try: votes = int(Raw.parse(data = item, tag = 'span', attributes = {'name' : 'nv'})[0].replace(',', ''))
				except:
					try: votes = int(Raw.parse(data = item, tag = 'div', extract = 'title', attributes = {'class' : '.*?rating-list'})[0].replace(',', ''))
					except:
						try: votes = int(Regex.extract(data = Raw.parse(data = item, tag = 'div', extract = 'title', attributes = {'class' : '.*?rating-list'})[0], expression = '\((.+?)\svotes?\)', group = 1).replace(',', ''))
						except: pass

				try:
					director = Regex.extract(data = item, expression = 'directors?:(.+?)(?:\||<\/div>)', group = 1)
					director = Raw.parse(data = director, tag = 'a')
					director = [Networker.htmlDecode(i) for i in director]
				except: director = None

				try:
					cast = Regex.extract(data = item, expression = 'stars?:(.+?)(?:\||<\/div>)', group = 1)
					cast = Raw.parse(data = cast, tag = 'a')
					cast = [Networker.htmlDecode(i) for i in cast]
				except: cast = None

				plot = None
				try: plot = Raw.parse(data = item, tag = 'p', attributes = {'class' : 'text-muted'})[0]
				except:
					try: plot = Raw.parse(data = item, tag = 'div', attributes = {'class' : 'item_description'})[0]
					except: pass
				if plot:
					plot = plot.rsplit('<span>', 1)[0].strip()
					plot = Regex.remove(data = plot, expression = '(<.+?>|<\/.+?>)', group = 1)
					if not plot:
						try:
							plot = Raw.parse(data = item, tag = 'div', attributes = {'class' : 'lister-item-content'})[0]
							plot = Regex.replace(data = plot, expression = '(<p\s*class="">)', replacement = '<p class="plot_">', group = 1)
							plot = Raw.parse(data = plot, tag = 'p', attributes = {'class' : 'plot_'})[0]
							plot = Regex.remove(data = plot, expression = '(<.+?>|<\/.+?>)', group = 1)
						except: pass
				if plot: plot = Networker.htmlDecode(plot)
				else: plot = None

				item = {
					'imdb' : imdb,
					'title' : title,
					'originaltitle' : title,
					'plot' : plot,
					'year' : year,
					'duration' : duration,
					'mpaa' : mpaa,
					'genre' : genre,
					'director' : director,
					'cast' : cast,
					'next' : next,
					'temp' : {
						'imdb' : {
							'rating' : rating,
							'ratinguser' : ratinguser,
							'ratingtime' : ratingtime,
							'votes' : votes,
							'poster' : poster,
						},
						'metacritic' : {
							'rating' : ratingmetacritic,
						},
					}
				}
				list.append(item)
			except: Logger.error()

		return list

	def imdbListPerson(self, link):
		list = []

		try:
			networker = self.imdbRequest(link = link)
			result = networker.responseDataText()
			try: result = result.decode('iso-8859-1')
			except: pass
			items = Raw.parse(data = result, tag = 'div', attributes = {'class': '.+? lister-item'}) + Raw.parse(data = result, tag = 'div', attributes = {'class': 'lister-item .+?'})
		except: Logger.error()

		for item in items:
			try:
				name = Raw.parse(data = item, tag = 'a')[1]
				name = Networker.htmlDecode(name)

				link = Raw.parse(data = item, tag = 'a', extract = 'href')[1]
				link = Regex.extract(data = link, expression = '(nm\d+)', group = 1)
				link = self.person_link % (link, self.mCertificates)
				link = Networker.htmlDecode(link)

				image = Raw.parse(data = item, tag = 'img', extract = 'src')[0]
				image = MetaImdb.image(Networker.htmlDecode(image))

				list.append({'name': name, 'link': link, 'image': image})
			except: Logger.error()

		return list

	def imdbListUser(self, link):
		list = []

		try:
			networker = self.imdbRequest(link = link)
			result = networker.responseDataText()
			try: result = result.decode('iso-8859-1')
			except: pass
			items = []
			items += Raw.parse(data = result, tag = 'div', attributes = {'class': '(?:.+\s)?list_name(?:\s.+)?'})
			items += Raw.parse(data = result, tag = 'li', attributes = {'class': '(?:.+\s)?user-list(?:\s.+)?'})
		except: Logger.error()

		for item in items:
			try:
				name = Raw.parse(data = item, tag = 'a')[0]
				name = Networker.htmlDecode(name)

				link = Raw.parse(data = item, tag = 'a', extract = 'href')[0]
				link = link.split('/list/', 1)[-1].replace('/', '')
				link = self.imdblistname_link % link
				link = Networker.htmlDecode(link)

				list.append({'name': name, 'link': link})
			except: Logger.error()

		list = sorted(list, key = lambda k : Regex.remove(data = k['name'], expression = '(^the\s|^an?\s)', group = 1))
		return list

	def imdbUserAccount(self, watched = None, ratings = None):
		data = [[], []]

		threads = []
		if watched is None: threads.append(Pool.thread(target = self.imdbUserWatched, args = (data, 0)))
		else: data[0] = watched
		if ratings is None: threads.append(Pool.thread(target = self.imdbUserRatings, args = (data, 1)))
		else: data[1] = ratings
		[i.start() for i in threads]
		[i.join() for i in threads]

		result = data[0]
		for i in data[1]:
			found = -1
			for j in range(len(result)):
				try:
					if i['imdb'] == result[j]['imdb']:
						found = j
						break
				except: pass
				try:
					if i['tvdb'] == result[j]['tvdb']:
						found = j
						break
				except: pass
			if found >= 0: result[found].update(i)
			else: result.append(i)

		return result

	def imdbUserWatched(self, resultData = None, resultIndex = None):
		data = self.retrieve(link = 'imdbwatchlist', menu = False, detailed = False, full = True, clean = False)
		values = []
		for item in data:
			value = {}
			if 'temp' in item and item['temp'] and 'imdb' in item['temp'] and item['temp']['imdb']:
				if 'watchedtime' in item['temp']['imdb'] and item['temp']['imdb']['watchedtime']: value['time'] = item['temp']['imdb']['watchedtime']
			if 'imdb' in item and item['imdb']: value['imdb'] = item['imdb']
			if 'tvdb' in item and item['tvdb']: value['tvdb'] = item['tvdb']
			if 'imdb' in value or 'tmdb' in value: values.append(value)
		if not resultData is None: resultData[resultIndex] = values
		return values

	def imdbUserRatings(self, resultData = None, resultIndex = None):
		data = self.retrieve(link = 'imdbratings', menu = False, detailed = False, full = True, clean = False)
		values = []
		for item in data:
			if 'temp' in item and item['temp'] and 'imdb' in item['temp'] and item['temp']['imdb']:
				if 'ratinguser' in item['temp']['imdb'] and item['temp']['imdb']['ratinguser']:
					value = {'rating' : item['temp']['imdb']['ratinguser']}
					if 'ratingtime' in item['temp']['imdb'] and item['temp']['imdb']['ratingtime']: value['time'] = item['temp']['imdb']['ratingtime']
					if 'imdb' in item and item['imdb']: value['imdb'] = item['imdb']
					if 'tvdb' in item and item['tvdb']: value['tvdb'] = item['tvdb']
					if 'imdb' in value or 'tmdb' in value: values.append(value)
		if not resultData is None: resultData[resultIndex] = values
		return values

	##############################################################################
	# TVMAZE
	##############################################################################

	def tvmazeList(self, link):
		list = []
		try:
			result = Networker().requestText(link = link)
			result = Raw.parse(data = result, tag = 'section', attributes = {'id': 'this-seasons-shows'})

			items = Raw.parse(data = result, tag = 'span', attributes = {'class': 'title .*'})
			items = [Raw.parse(data = i, tag = 'a', extract = 'href') for i in items]
			items = [i[0] for i in items if len(i) > 0]
			items = [Regex.extract(data = i, expression = '/(\d+)/', group = 1) for i in items]
			items = [i for i in items if i]
			items = items[:50]

			# Although TVmaze has a rate limit per second, we just use a normal limit on concurrent requests.
			# https://www.tvmaze.com/api#rate-limiting
			threads = []
			semaphore = Semaphore(20)
			for item in items:
				semaphore.acquire()
				threads.append(Pool.thread(target = self.tvmazeItem, kwargs = {'id' : item, 'list' : list, 'semaphore' : semaphore}, start = True))
			[thread.join() for thread in threads]

			filter = [i for i in list if i['temp']['tvmaze']['content'] == 'scripted']
			filter += [i for i in list if not i['temp']['tvmaze']['content'] == 'scripted']
			list = filter
		except: Logger.error()
		return list

	def tvmazeItem(self, id, list, semaphore):
		try:
			item = Networker().requestJson(link = self.tvmaze_info_link % id)
			if item: # This can fail if the rate limit was exceeded.
				title = item['name']
				title = Regex.remove(data = title, expression = '\s+[\|\[\(](us|uk|gb|au|\d{4})[\|\]\)]\s*$')
				title = Networker.htmlDecode(title)

				try:
					year = int(Regex.extract(data = item['premiered'], expression = '(\d{4})', group = 1))
					if year > self.mYear: return None
				except: year = None

				try:
					idImdb = item['externals']['imdb']
					if idImdb:
						idImdb = 'tt' + Regex.remove(data = str(idImdb), expression = '[^0-9]')
						if idImdb == 'tt': idImdb = None
					else: idImdb = None
				except: idImdb = None

				try:
					idTvdb = item['externals']['thetvdb']
					if not idTvdb: return None
				except: idTvdb = None

				try: idTvrage = item['externals']['tvrage']
				except: idTvrage = None

				try:
					poster = item['image']['original']
					if not poster: poster = None
				except: poster = None

				try: premiered = Regex.extract(data = item['premiered'], expression = '(\d{4}-\d{2}-\d{2})', group = 1)
				except: premiered = None

				try:
					studio = item['network']['name']
					if not studio: studio = None
				except: studio = None

				try: genre = [i.title() for i in item['genres']]
				except: genre = None

				try: duration = int(item['runtime']) * 60
				except: duration = None

				try:
					rating = float(item['rating']['average'])
					if not rating: rating = None
				except: rating = None

				try: plot = Networker.htmlDecode(Regex.remove(data = item['summary'], expression = '(<.+?>|</.+?>|\n)', group = 1))
				except: plot = None

				try: content = item['type'].lower()
				except: content = None

				item = {
					'imdb' : idImdb,
					'tvdb' : idTvdb,
					'tvrage' : idTvrage,
					'tvmaze' : id,

					'title' : title,
					'originaltitle' : title,
					'plot' : plot,
					'year' : year,
					'premiered' : premiered,
					'studio' : studio,
					'duration' : duration,
					'genre' : genre,

					'temp' : {
						'tvmaze' : {
							'rating' : rating,
							'poster' : poster,
							'content' : content,
						},
					}
				}
				list.append(item)
		except: Logger.error()
		semaphore.release()

	##############################################################################
	# METADATA
	##############################################################################

	# By default, do not cache internal requests (eg: Trakt/TVDb/IMDb/Fanart API requests).
	# For a list of 50 items, this will use an additional 8-9MB of the cache (disc space), plus it takes 4 secs longer to write to disc (the entire list takes 17-25 secs).
	# There is no real reason to cache intermediary requests, since the final processed metadata is already cached with MetaCache.
	# The only reason for intermediary caching is if the metadata is imcomplete, and on subsequent menu loading, all of the show's metadata is requested again, even though some of them might have suceeded previously.
	# quick = Quickly retrieve items from cache without holding up the process of retrieving detailed metadata in the foreground. This is useful if only a few random items are needed from the list and not all of them.
	# quick = positive integer (retrieve the given number of items in the foreground and the rest in the background), negative integer (retrieve the given number of items in the foreground and do not retrieve the rest at all), True (retrieve whatever is in the cache and the rest in the background - could return no items at all), False (retrieve whatever is in the cache and the rest not at all - could return no items at all).
	def metadata(self, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, title = None, year = None, items = None, filter = None, clean = True, quick = None, refresh = False, cache = False):
		try:
			single = False
			if items or (idImdb or idTvdb) or (title and year):
				if items:
					if not Tools.isArray(items):
						single = True
						items = [items]
				else:
					single = True
					items = [{'imdb' : idImdb, 'tmdb' : idTmdb, 'tvdb' : idTvdb, 'trakt' : idTrakt, 'title' : title, 'year' : year}]
				if filter is None: filter = not single

				lock = Lock()
				locks = {}
				semaphore = Semaphore(50)
				metacache = MetaCache.instance()
				items = metacache.select(type = MetaCache.TypeShow, items = items)

				metadataForeground = []
				metadataBackground = []
				threadsForeground = []
				threadsBackground = []

				if quick is None:
					for item in items:
						try: refreshing = item[MetaCache.Attribute][MetaCache.AttributeRefresh]
						except: refreshing = MetaCache.RefreshForeground
						if refreshing == MetaCache.RefreshForeground or refresh:
							self.mMetatools.busyStart(media = self.mMedia, item = item)
							semaphore.acquire()
							threadsForeground.append(Pool.thread(target = self.metadataUpdate, kwargs = {'item' : item, 'result' : metadataForeground, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'filter' : filter, 'cache' : cache, 'mode' : 'foreground'}, start = True))
						elif refreshing == MetaCache.RefreshBackground:
							if not self.mMetatools.busyStart(media = self.mMedia, item = item):
								threadsBackground.append({'item' : item, 'result' : metadataBackground, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'filter' : filter, 'cache' : cache, 'mode' : 'background'})
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
								self.mMetatools.busyStart(media = self.mMedia, item = item)
								lookup.append(item)
								semaphore.acquire()
								threadsForeground.append(Pool.thread(target = self.metadataUpdate, kwargs = {'item' : item, 'result' : metadataForeground, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'filter' : filter, 'cache' : cache, 'mode' : 'foreground'}, start = True))
						elif refreshing == MetaCache.RefreshBackground or (counter is None or len(lookup) >= counter):
							if background and not self.mMetatools.busyStart(media = self.mMedia, item = item):
								threadsBackground.append({'item' : item, 'result' : metadataBackground, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'filter' : filter, 'cache' : cache, 'mode' : 'background'})
					items = lookup

				# Wait for metadata that does not exist in the metacache.
				[thread.join() for thread in threadsForeground]
				if metadataForeground: metacache.insert(type = MetaCache.TypeShow, items = metadataForeground)

				# Let the refresh of old metadata run in the background for the next menu load.
				# Only start the threads here, so that background threads do not interfere or slow down the foreground threads.
				if threadsBackground:
					def _metadataBackground():
						for i in range(len(threadsBackground)):
							semaphore.acquire()
							threadsBackground[i] = Pool.thread(target = self.metadataUpdate, kwargs = threadsBackground[i], start = True)
						[thread.join() for thread in threadsBackground]
						if metadataBackground: metacache.insert(type = MetaCache.TypeShow, items = metadataBackground)

					# Make a deep copy of the items, since the items can be edited below while these threads are still busy, and we do not want to store the extra details in the database.
					for i in threadsBackground: i['item'] = Tools.copy(i['item'])
					Pool.thread(target = _metadataBackground, start = True)

				if filter: items = [i for i in items if 'tvdb' in i and i['tvdb']]

			# Remove temporary, useless, or already aggregatd data, to keep the size of the data passed arround small.
			if clean:
				for item in items:
					try: del item['temp']
					except: pass
					try: del item[MetaCache.Attribute]
					except: pass
		except: Logger.error()

		if single: return items[0] if items else None
		else: return items

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

			# By default we do not cache requests to disc, since it takes longer and requires more storage space.
			# If the same show appears multiple times in the list (some Trakt lists, eg watched list where a show was watched twice), sub-requests will also have to be executed multiple times, since they are not disc-cached.
			# Cache in memory and use locks to block subsequent calls with the same ID/title until the first request is done and then use those results without executing all the code again.
			id = Memory.id(idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, idTvmaze = idTvmaze, idTvrage = idTvrage, title = title, year = year)
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
				title = item['title'] if 'title' in item else None
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

			developer = self.metadataDeveloper(idImdb = idImdb, idTvdb = idTvdb, idTrakt = idTrakt, title = title, year = year, item = item)
			if developer: Logger.log('SHOW METADATA RETRIEVAL [%s]: %s' % (mode.upper() if mode else 'UNKNOWN', developer))

			if self.mDetail == MetaTools.DetailEssential:
				requests = [
					{'id' : 'tvdb', 'function' : self.metadataTvdb, 'parameters' : {'idImdb' : idImdb, 'idTvdb' : idTvdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
					{'id' : 'imdb', 'function' : self.metadataImdb, 'parameters' : {'idImdb' : idImdb, 'full' : False, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
					{'id' : 'tvmaze', 'function' : self.metadataTvmaze, 'parameters' : {'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
				]
			elif self.mDetail == MetaTools.DetailStandard:
				requests = [
					{'id' : 'tvdb', 'function' : self.metadataTvdb, 'parameters' : {'idImdb' : idImdb, 'idTvdb' : idTvdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
					{'id' : 'trakt', 'function' : self.metadataTrakt, 'parameters' : {'idImdb' : idImdb, 'idTrakt' : idTrakt, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
					{'id' : 'imdb', 'function' : self.metadataImdb, 'parameters' : {'idImdb' : idImdb, 'full' : False, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
					{'id' : 'fanart', 'function' : self.metadataFanart, 'parameters' : {'idTvdb' : idTvdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
					{'id' : 'tvmaze', 'function' : self.metadataTvmaze, 'parameters' : {'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
				]
			elif self.mDetail == MetaTools.DetailExtended:
				requests = [
					{'id' : 'tvdb', 'function' : self.metadataTvdb, 'parameters' : {'idImdb' : idImdb, 'idTvdb' : idTvdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
					{'id' : 'trakt', 'function' : self.metadataTrakt, 'parameters' : {'idImdb' : idImdb, 'idTrakt' : idTrakt, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
					{'id' : 'imdb', 'function' : self.metadataImdb, 'parameters' : {'idImdb' : idImdb, 'full' : True, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
					{'id' : 'tmdb', 'function' : self.metadataTmdb, 'parameters' : {'idImdb' : idImdb, 'idTvdb' : idTvdb, 'idTmdb' : idTmdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
					{'id' : 'fanart', 'function' : self.metadataFanart, 'parameters' : {'idTvdb' : idTvdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
					{'id' : 'tvmaze', 'function' : self.metadataTvmaze, 'parameters' : {'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
				]
			else:
				requests = []

			datas = self.metadataRetrieve(requests = requests)

			data = {}
			images = {}
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
								if developer: Logger.log('INCOMPLETE SHOW METADATA [%s]: %s' % (i.upper(), developer))
							provider = value['provider']
							value = value['data']
							if value:
								if MetaImage.Attribute in value:
									images = Tools.update(images, value[MetaImage.Attribute], none = True, lists = True, unique = False)
									del value[MetaImage.Attribute]
								if 'rating' in value: voting['rating'][provider] = value['rating']
								if 'ratinguser' in value: voting['user'][provider] = value['ratinguser']
								if 'votes' in value: voting['votes'][provider] = value['votes']
								data = Tools.update(data, value, none = True, lists = False, unique = False)

			data['voting'] = voting
			data = {k : v for k, v in data.items() if not v is None}

			if 'id' in data and data['id']:
				if not idImdb and 'imdb' in data['id']: idImdb = data['id']['imdb']
				if not idTmdb and 'tmdb' in data['id']: idTmdb = data['id']['tmdb']
				if not idTvdb and 'tvdb' in data['id']: idTvdb = data['id']['tvdb']
				if not idTvmaze and 'tvmaze' in data['id']: idTvmaze = data['id']['tvmaze']
				if not idTvrage and 'tvrage' in data['id']: idTvrage = data['id']['tvrage']
				if not idTrakt and 'trakt' in data['id']: idTrakt = data['id']['trakt']
				if not idSlug and 'slug' in data['id']: idSlug = data['id']['slug']

			# This is for legacy purposes, since all over Gaia the IDs are accessed at the top-level of the dictionary.
			# At some later point the entire addon should be updated to have the new ID structure.
			if idImdb: data['imdb'] = idImdb
			if idTmdb: data['tmdb'] = idTmdb
			if idTvdb: data['tvdb'] = idTvdb
			if idTvmaze: data['tvmaze'] = idTvmaze
			if idTvrage: data['tvrage'] = idTvrage
			if idTrakt: data['trakt'] = idTrakt
			if idSlug: data['slug'] = idSlug

			if images: MetaImage.update(media = MetaImage.MediaShow, images = images, data = data)

			# Do this before here already.
			# Otherwise a bunch of regular expressions are called every time the menu is loaded.
			self.mMetatools.cleanPlot(metadata = data)

			# Calculate the rating here already, so that we have a default rating/votes if this metadata dictionary is passed around without being cleaned first.
			# More info under meta -> tools.py -> cleanVoting().
			self.mMetatools.cleanVoting(metadata = data)

			Memory.set(id = id, value = data, local = True, kodi = False)
			item.update(data)

			data[MetaCache.Attribute] = {MetaCache.AttributeComplete : complete}
			result.append(data)
		except:
			Logger.error()
		finally:
			if locks and id: locks[id].release()
			if semaphore: semaphore.release()
			self.mMetatools.busyFinish(media = self.mMedia, item = item)

	def metadataDeveloper(self, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, title = None, year = None, item = None):
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
		# HTTP error 429 can be thrown if too many requests were made in a short time.
		# This should only happen with Trakt (which does not call this function), since TMDb/TVDb/Fanart should not have any API limits at the moment.
		# Still check for it, since in special cases 429 might still happen (eg: the TMDb CDN/Cloudflare might block more than 50 concurrent connections).
		# This should not be an issue with normal use, only with batch-generating the preprocessed database that makes 1000s of request every few minutes.

		networker = Networker()
		if cache:
			if cache is True: cache = Cache.TimeoutLong
			result = self.mCache.cache(mode = None, timeout = cache, refresh = None, function = networker.request, link = link, data = data, headers = headers, method = method)
			if not result or result['error']['type'] in Networker.ErrorNetwork or result['error']['code'] == 429:
				# Delete the cache, otherwise the next call will return the previously failed request.
				self.mCache.cacheDelete(networker.request, link = link, data = data, headers = headers, method = method)
				return False
		else:
			result = networker.request(link = link, data = data, headers = headers, method = method)
			if not result or result['error']['type'] in Networker.ErrorNetwork or result['error']['code'] == 429: return False
		return Networker.dataJson(result['data'])

	def metadataId(self, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, title = None, year = None):
		result = self.mMetatools.idShow(idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, title = title, year = year)
		return {'complete' : True, 'data' : {'id' : result} if result else result}

	def metadataTrakt(self, idImdb = None, idTrakt = None, language = None, item = None, people = False, cache = False):
		complete = True
		result = None
		try:
			id = idTrakt if idTrakt else idImdb
			if id:
				requests = [{'id' : 'show', 'function' : trakt.getTVShowSummary, 'parameters' : {'id' : id, 'full' : True, 'cache' : cache, 'failsafe' : True}}]

				# We already retrieve the cast from TMDb and those values contain thumbnail images.
				# Retrieving the cast here as well will not add any new info and just prolong the request/processing time.
				if people: requests.append({'id' : 'people', 'function' : trakt.getPeopleShow, 'parameters' : {'id' : id, 'full' : True, 'cache' : cache, 'failsafe' : True}})

				translation = language and not language == Language.EnglishCode
				if translation: requests.append({'id' : 'translation', 'function' : trakt.getTVShowTranslation, 'parameters' : {'id' : id, 'lang' : language, 'full' : True, 'cache' : cache, 'failsafe' : True}})

				data = self.metadataRetrieve(requests = requests)
				if data:
					dataShow = data['show']
					dataPeople = data['people'] if people else None
					dataTranslation = data['translation'] if translation else None
					if dataShow is False or (people and dataPeople is False) or (translation and dataTranslation is False): complete = False

					if dataShow or dataPeople or dataTranslation:
						result = {}

						if dataShow and 'title' in dataShow and 'ids' in dataShow:
							ids = dataShow.get('ids')
							if ids:
								ids = {k : str(v) for k, v in ids.items() if v}
								if ids: result['id'] = ids

							title = dataShow.get('title')
							if title:
								title = Networker.htmlDecode(title)
								result['title'] = title
								result['tvshowtitle'] = title

							tagline = dataShow.get('tagline')
							if tagline: result['tagline'] = Networker.htmlDecode(tagline)

							plot = dataShow.get('overview')
							if plot: result['plot'] = Networker.htmlDecode(plot)

							year = dataShow.get('year')
							if year and Tools.isNumber(year): result['year'] = year

							premiered = dataShow.get('first_aired')
							if premiered:
								premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
								if premiered:
									result['premiered'] = premiered
									result['aired'] = premiered

							airs = dataShow.get('airs')
							if airs:
								result['airs'] = {}

								# Trakt only has a single air day, although some shows are aired daily (eg: The Bold and the Beautiful).
								airsDay = airs.get('day')
								if airsDay: result['airs']['day'] = [airsDay]

								airsTime = airs.get('time')
								if airsTime: result['airs']['time'] = airsTime

								airsZone = airs.get('timezone')
								if airsZone: result['airs']['zone'] = airsZone

							airs = dataShow.get('aired_episodes')
							if airs:
								if not 'airs' in result: result['airs'] = {}
								result['airs']['episodes'] = airs

							genre = dataShow.get('genres')
							if genre: result['genre'] = [i.title() for i in genre]

							mpaa = dataShow.get('certification')
							if mpaa: result['mpaa'] = mpaa

							rating = dataShow.get('rating')
							if not rating is None: result['rating'] = rating

							votes = dataShow.get('votes')
							if not votes is None: result['votes'] = votes

							duration = dataShow.get('runtime')
							if not duration is None: result['duration'] = duration * 60

							status = dataShow.get('status')
							if status: result['status'] = status.title()

							country = dataShow.get('country')
							if country: result['country'] = [country]

							languages = dataShow.get('language')
							if languages: result['language'] = [languages]

							trailer = dataShow.get('trailer')
							if trailer: result['trailer'] = trailer

							homepage = dataShow.get('homepage')
							if homepage: result['homepage'] = homepage

							studio = dataShow.get('network')
							if studio: result['studio'] = studio if Tools.isArray(studio) else [studio]

						if dataTranslation:
							title = dataTranslation.get('title')
							if title:
								if result['title']: result['originaltitle'] = result['title']
								result['title'] = Networker.htmlDecode(title)

							tagline = dataTranslation.get('tagline')
							if tagline: result['tagline'] = Networker.htmlDecode(tagline)

							plot = dataTranslation.get('overview')
							if plot: result['plot'] = Networker.htmlDecode(plot)

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
										if director: result['director'] = director
									if 'writing' in dataCrew:
										writer = _metadataTraktPeople(data = dataCrew['writing'], job = ['writer', 'screenplay', 'author'])
										if writer: result['writer'] = writer

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
									if cast: result['cast'] = cast
		except: Logger.error()
		return {'provider' : 'trakt', 'complete' : complete, 'data' : result}

	def metadataTvdb(self, idImdb = None, idTvdb = None, language = None, item = None, cache = False):
		complete = True
		result = None
		try:
			if idTvdb or idImdb:
				manager = MetaManager(provider = MetaManager.ProviderTvdb)
				data = manager.show(idTvdb = idTvdb, idImdb = idImdb, level = MetaManager.Level4, cache = cache)
				if data and data.idTvdb():
					result = {}

					result['id'] = {}
					id = data.idImdb()
					if id: result['id']['imdb'] = id
					id = data.idTmdb()
					if id: result['id']['tmdb'] = id
					id = data.idTvdb()
					if id: result['id']['tvdb'] = id

					title = data.titleSettings(selection = MetaData.SelectionSingle, fallback = MetaData.FallbackSecondary)
					if title:
						result['title'] = title
						result['tvshowtitle'] = title

					title = data.titleOriginal(selection = MetaData.SelectionSingle)
					if title:
						result['originaltitle'] = title
						if not 'title' in result: result['title'] = title
						if not 'tvshowtitle' in result: result['tvshowtitle'] = title

					plot = data.overviewSettings(selection = MetaData.SelectionSingle, fallback = MetaData.FallbackSecondary)
					if plot: result['plot'] = plot

					year = data.year()
					if year: result['year'] = year

					premiered = data.releaseDateFirst(zone = MetaData.ZoneOriginal, format = MetaData.FormatDate)
					if premiered:
						premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
						if premiered:
							result['premiered'] = premiered
							result['aired'] = premiered

					airs = {}
					airTime = data.releaseTime(zone = MetaData.ZoneOriginal)
					if airTime: airs['time'] = airTime
					airDay = data.releaseDay()
					if airDay: airs['day'] = [i.title() for i in airDay]
					airZone = data.releaseZoneName()
					if airZone: airs['zone'] = airZone
					if airs: result['airs'] = airs

					genre = data.genreName()
					if genre: result['genre'] = [i.title() for i in genre]

					mpaa = data.certificateCode(country = MetaData.CountryOriginal, selection = MetaData.SelectionSingle)
					if mpaa: result['mpaa'] = mpaa

					# TVDb does not have ratings/votes anymore.
					# Check tvdb.py -> _processVote() for more info.
					'''rating = data.voteRating()
					if not rating is None: result['rating'] = rating

					votes = data.voteCount()
					if not votes is None: result['votes'] = votes'''

					duration = data.durationSeconds()
					if not duration is None: result['duration'] = duration

					status = data.statusLabel()
					if status: result['status'] = status

					country = data.releaseCountry()
					if country: result['country'] = [country]

					language = data.languageOriginal()
					if language: result['language'] = language if Tools.isArray(language) else [language]

					studio = data.companyNameNetwork()
					if studio: result['studio'] = studio

					cast = data.personKodiCast()
					if cast: result['cast'] = cast

					director = data.personKodiDirector()
					if director: result['director'] = director

					writer = data.personKodiWriter()
					if writer: result['writer'] = writer

					# This is used by flattened and indirect show menus in episodes.py to determine which seasons to retrieve and if a 'Next Page' should be added.
					# Add here already and not only in seasons, since we need the episode counters for the ListItems (TotalSeasons, TotalEpisodes, WatchedEpisodes).
					pack = self.mMetatools.pack(show = data, extended = self.mDetail == MetaTools.DetailExtended, idImdb = result['id'].get('imdb'), idTmdb = result['id'].get('tmdb'), idTvdb = result['id'].get('tvdb'))
					if pack: result['pack'] = pack

					image = {
						MetaImage.TypePoster : data.imageKodiPoster(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeThumb : data.imageKodiThumb(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeFanart : data.imageKodiFanart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeLandscape : data.imageKodiLandscape(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeBanner : data.imageKodiBanner(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeClearlogo : data.imageKodiClearlogo(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeClearart : data.imageKodiClearart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeDiscart : data.imageKodiDiscart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeKeyart : data.imageKodiKeyart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
					}
					for k, v in image.items():
						image[k] = [MetaImage.create(link = i, provider = MetaImage.ProviderTvdb) for i in v] if v else []
					if image: result[MetaImage.Attribute] = image
		except: Logger.error()
		return {'provider' : 'tvdb', 'complete' : complete, 'data' : result}

	def metadataTmdb(self, idImdb = None, idTvdb = None, idTmdb = None, language = None, item = None, cache = False):
		complete = True
		result = None
		try:
			if idTmdb:
				def _metadataTmdb(id, mode = None, language = None, cache = True):
					link = 'https://api.themoviedb.org/3/tv/%s%s' % (id, ('/' + mode) if mode else '')
					data = {'api_key' : self.mAccountTmdb}
					if language: data['language'] = language
					return self.metadataRequest(method = Networker.MethodGet, link = link, data = data, cache = cache)

				data = self.metadataRetrieve(requests = [
					{'id' : 'show', 'function' : _metadataTmdb, 'parameters' : {'id' : idTmdb, 'language' : language, 'cache' : cache}},
				])

				if data:
					dataShow = data['show']
					if dataShow is False: complete = False

					if dataShow:
						result = {}

						if dataShow and 'name' in dataShow and 'id' in dataShow:
							ids = {}
							idTmdb = dataShow.get('id')
							if idTmdb: ids['tmdb'] = str(idTmdb)
							if ids: result['id'] = ids

							title = dataShow.get('name')
							if title: result['title'] = Networker.htmlDecode(title)

							originaltitle = dataShow.get('original_name')
							if originaltitle: result['originaltitle'] = Networker.htmlDecode(originaltitle)

							tagline = dataShow.get('tagline')
							if tagline: result['tagline'] = Networker.htmlDecode(tagline)

							plot = dataShow.get('overview')
							if plot: result['plot'] = Networker.htmlDecode(plot)

							premiered = dataShow.get('first_air_date')
							if premiered:
								premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
								if premiered:
									result['premiered'] = premiered
									result['aired'] = premiered
									year = Regex.extract(data = premiered, expression = '(\d{4})-', group = 1)
									if year: result['year'] = int(year)

							genre = dataShow.get('genres')
							if genre: result['genre'] = [i['name'].title() for i in genre]

							rating = dataShow.get('vote_average')
							if not rating is None: result['rating'] = rating

							votes = dataShow.get('vote_count')
							if not votes is None: result['votes'] = votes

							duration = dataShow.get('episode_run_time')
							if duration: result['duration'] = duration[0] * 60

							status = dataShow.get('status')
							if status: result['status'] = status.title()

							studio = dataShow.get('networks')
							if studio: result['studio'] = [i['name'] for i in studio]
							studio = dataShow.get('production_companies')
							if studio:
								if not 'studio' in result: result['studio'] = []
								result['studio'].extend([i['name'] for i in studio])

							country = dataShow.get('production_countries')
							if country: result['country'] = [i['iso_3166_1'].lower() for i in country]

							languages = dataShow.get('spoken_languages')
							if languages: result['language'] = [i['iso_639_1'].lower() for i in languages]
							languages = dataShow.get('original_language')
							if languages:
								languages = [languages]
								if 'language' in result: Tools.listUnique(languages + result['language'])
								else: result['language'] = result['language'] = languages

							homepage = dataShow.get('homepage')
							if homepage: result['homepage'] = homepage
		except: Logger.error()
		return {'provider' : 'tmdb', 'complete' : complete, 'data' : result}

	def metadataFanart(self, idTvdb = None, language = None, item = None, cache = False):
		complete = True
		result = None
		try:
			if idTvdb:
				images = MetaFanart.show(idTvdb = idTvdb, cache = cache)
				if images is False: complete = False
				elif images: result = {MetaImage.Attribute : images}
		except: Logger.error()
		return {'provider' : 'fanart', 'complete' : complete, 'data' : result}

	def metadataImdb(self, idImdb = None, language = None, full = False, item = None, cache = False):
		# Only do this if there is no IMDb rating in in the item, that is, the item does not come from a IMDb list.
		# Retrieving the detailed IMDb data does not really add extra metadata above TMDb/Trakt, except for the rating/vote and the revenue (which is also on TMDb).
		# A single IMDb page is more than 200KB, so retrieving 50 shows will take 10MB+.
		if full and idImdb and (not 'temp' in item or not 'imdb' in item['temp'] or not 'rating' in item['temp']['imdb']):
			data = MetaImdb.details(id = idImdb, cache = cache)
			if data: item = data

		results = []

		complete = True
		result = None
		try:
			if item and 'temp' in item and 'imdb' in item['temp']:
				try:
					if 'poster' in item['temp']['imdb']:
						poster = item['temp']['imdb']['poster']
						if poster: result = {MetaImage.Attribute : {MetaImage.TypePoster : [MetaImage.create(link = poster, provider = MetaImage.ProviderImdb)]}}
				except: Logger.error()

				for i in ['rating', 'ratinguser', 'votes']:
					try:
						if i in item['temp']['imdb']:
							if result is None: result = {}
							result[i] = item['temp']['imdb'][i]
					except: Logger.error()
		except: Logger.error()
		results.append({'provider' : 'imdb', 'complete' : complete, 'data' : result})

		complete = True
		result = None
		try:
			if item and 'temp' in item and 'metacritic' in item['temp']:
				for i in ['rating', 'ratinguser', 'votes']:
					try:
						if i in item['temp']['metacritic']:
							if result is None: result = {}
							result[i] = item['temp']['metacritic'][i]
					except: Logger.error()
		except: Logger.error()
		results.append({'provider' : 'metacritic', 'complete' : complete, 'data' : result})

		return results

	def metadataTvmaze(self, language = None, item = None, cache = False):
		complete = True
		result = None
		try:
			if item and 'temp' in item and 'tvmaze' in item['temp']:
				try:
					if 'poster' in item['temp']['tvmaze']:
						poster = item['temp']['tvmaze']['poster']
						if poster: result = {MetaImage.Attribute : {MetaImage.TypePoster : [MetaImage.create(link = poster, provider = MetaImage.ProviderTvmaze)]}}
				except: Logger.error()

				try:
					if 'thumb' in item['temp']['tvmaze']:
						thumb = item['temp']['tvmaze']['thumb']
						if thumb: result = {MetaImage.Attribute : {MetaImage.TypeThumb : [MetaImage.create(link = thumb, provider = MetaImage.ProviderTvmaze)]}}
				except: Logger.error()

				for i in ['rating', 'ratinguser', 'votes']:
					try:
						if i in item['temp']['tvmaze']:
							if result is None: result = {}
							result[i] = item['temp']['tvmaze'][i]
					except: Logger.error()
		except: Logger.error()
		return {'provider' : 'tvmaze', 'complete' : complete, 'data' : result}

	##############################################################################
	# NAVIGATION
	##############################################################################

	def check(self, metadatas):
		if Tools.isString(metadatas):
			try: metadatas = Converter.jsonFrom(metadatas)
			except: pass
		if not metadatas:
			Loader.hide()
			Dialog.notification(title = 32002, message = 33049, icon = Dialog.IconInformation)
			return None
		return metadatas

	def menu(self, metadatas, next = True):
		metadatas = self.check(metadatas = metadatas)
		if metadatas:
			directory = Directory(content = Directory.ContentSettings, media = Media.TypeShow, cache = True, lock = False)
			directory.addItems(items = self.mMetatools.items(metadatas = metadatas, media = self.mMedia, kids = self.mKids, next = next, hide = True, hideSearch = self.mModeSearch, hideRelease = self.mModeRelease, contextPlaylist = False, contextShortcutCreate = True))
			directory.finish(loader = self.mModeSearch) # The loader initiated from search() ios not automatically hidden by Kodi once the menu has loaded. Probably because searching starts a new sub-process and does not load the directory like other menus.

	def directory(self, metadatas):
		metadatas = self.check(metadatas = metadatas)
		if metadatas:
			directory = Directory(content = Directory.ContentSettings, cache = True, lock = False)
			directory.addItems(items = self.mMetatools.directories(metadatas = metadatas, media = self.mMedia, kids = self.mKids))
			directory.finish()

	def context(self, idImdb = None, idTvdb = None, title = None, year = None):
		metadata = self.metadata(idImdb = idImdb, idTvdb = idTvdb, title = title, year = year)
		return self.mMetatools.context(metadata = metadata, media = self.mMedia, kids = self.mKids, playlist = False, shortcutCreate = True)
