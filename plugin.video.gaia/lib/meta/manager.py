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

from lib.modules.tools import Media, Logger, Tools, System, Time, Regex, Math, Title, Language, Audience, Hardware, Settings
from lib.modules.concurrency import Pool, Lock, Semaphore
from lib.modules.cache import Cache, Memory
from lib.modules.network import Networker

from lib.meta.core import MetaCore
from lib.meta.data import MetaData
from lib.meta.pack import MetaPack
from lib.meta.cache import MetaCache
from lib.meta.tools import MetaTools
from lib.meta.image import MetaImage

from lib.meta.provider import MetaProvider
from lib.meta.providers.imdb import MetaImdb
from lib.meta.providers.tmdb import MetaTmdb
from lib.meta.providers.tvdb import MetaTvdb
from lib.meta.providers.trakt import MetaTrakt
from lib.meta.providers.fanart import MetaFanart

class MetaManager(object):

	Smart				= 'smart'

	ContentDiscover		= 'discover'
	ContentSearch		= 'search'
	ContentQuick		= 'quick'
	ContentProgress		= 'progress'
	ContentHistory		= 'history'
	ContentArrival		= 'arrival'
	ContentRandom		= 'random'
	ContentList			= 'list'
	ContentPerson		= 'person'
	ContentSeason		= 'season'
	ContentEpisode		= 'episode'
	ContentSet			= 'set'

	SpecialSettings		= None
	SpecialInclude		= True
	SpecialExclude		= False
	SpecialReduce		= 'reduce'

	ModeSynchronous		= 'synchronous'	# Make various background threads run in the foreground, waiting for them to finish before continuing.
	ModeUndelayed		= 'undelayed'	# Make Cache write updates immediatly,. instead of scheduling in a background thread to execute at the end of execution.
	ModeGenerative		= 'generative'	# Put MetaCache into generative mode to create the external metadata addon.
	ModeAccelerate		= 'accelerate'	# Try to accelerate smart menu refreshes by doing the minimal amount of work. Eg: useful during binging when we do not want to hold up the playback of the next episode if smart-refreshing is going on in the background.

	Instance			= None
	Batch				= None

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, mode = None):
		self.mTools = MetaTools.instance()
		self.mLanguage = self.mTools.settingsLanguage()

		self.mDetail = self.mTools.settingsDetail()
		self.mLevel = self.mTools.settingsDetail(level = True)

		self.mDeveloper = System.developerVersion()
		self.mDeveloperExtra = False

		self.mModeSynchronous = None
		self.mModeGenerative = None
		self.mModeUndelayed = None
		self.mModeAccelerate = None
		if mode:
			if MetaManager.ModeSynchronous in mode: self.mModeSynchronous = True
			if MetaManager.ModeGenerative in mode: self.mModeGenerative = True
			if MetaManager.ModeUndelayed in mode: self.mModeUndelayed = True
			if MetaManager.ModeAccelerate in mode: self.mModeAccelerate = True

		self.mPerformance = Hardware.performanceRating()
		self.mPerformanceFast = False
		self.mPerformanceMedium = False
		self.mPerformanceSlow = False
		if self.mPerformance >= 0.75: self.mPerformanceFast = True
		elif self.mPerformance >= 0.6: self.mPerformanceMedium = True
		else: self.mPerformanceSlow = True

		self.mReloadMedia = None
		self.mReloadBusy = False
		self.mReloadQuick = False

		self.mLock = Lock()
		self.mLocks = {}

		self.mProviders = None
		self.mLimits = {}

		self.mJob = None
		self.jobReset()

		# Using a long delay makes loading menus, like Quick, faster.
		# If cache data is refreshed in the background, the refresh call to the cache function is delayed, allowing other code to continue.
		# Hence, the detailed metadata retrieval, paging, and sorting can execute before the cache data refresh thread is executed.
		# Eg: This reduces Quick menu loading from 1.5 secs to 1.0 secs.
		self.mCache = None
		self._cacheInitialize(mode = Cache.ModeSynchronous if self.mModeSynchronous else Cache.ModeDefault, delay = Cache.DelayDisable if self.mModeUndelayed else Cache.DelayLong)

	@classmethod
	def instance(self):
		if MetaManager.Instance is None: MetaManager.Instance = self()
		return MetaManager.Instance

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		MetaManager.Instance = None
		MetaManager.Batch = None

	##############################################################################
	# CACHE
	##############################################################################

	def _cache(self, cache_, refresh_, *args, **kwargs):
		return Tools.executeFunction(self.mCache, 'cacheClear' if refresh_ else cache_, *args, **kwargs)

	def _cacheRetrieve(self, *args, **kwargs):
		return Tools.executeFunction(self.mCache, 'cacheRetrieve', *args, **kwargs)

	def _cacheDelete(self, *args, **kwargs):
		self.mCache.cacheDelete(*args, **kwargs)

	def _cacheTime(self, *args, **kwargs):
		return self.mCache.cacheTime(*args, **kwargs)

	def _cacheInitialize(self, mode = Cache.ModeDefault, delay = Cache.DelayLong):
		self.mCache = Cache.instance(mode = mode, delay = delay)
		return self.mCache

	##############################################################################
	# JOB
	##############################################################################

	def job(self):
		return self.mJob

	def jobBusy(self, media = None, count = 0, foreground = True, background = False, none = False):
		type = []
		if foreground: type.append(MetaCache.RefreshForeground)
		if background: type.append(MetaCache.RefreshBackground)
		if none: type.append(None)
		for i in type:
			if (not media or media in self.mJob[i]['media']) and self.mJob[i]['count'] > count: return True
		return False

	def jobCount(self, media = None, foreground = True, background = False, none = False):
		count = 0
		type = []
		if foreground: type.append(MetaCache.RefreshForeground)
		if background: type.append(MetaCache.RefreshBackground)
		if none: type.append(None)
		for i in type:
			if not media or media in self.mJob[i]['media']: count += self.mJob[i]['count']
		return count

	def jobReset(self):
		self.mJob = {
			None						: {'count' : 0, 'media' : [], 'content' : None},
			MetaCache.RefreshForeground	: {'count' : 0, 'media' : [], 'content' : None},
			MetaCache.RefreshBackground	: {'count' : 0, 'media' : [], 'content' : None},
		}

	def _jobUpdate(self, media, foreground = None, background = None, none = None, content = None, hint = None):
		multiplier = 1
		foreign = not self.mLanguage == Language.CodeEnglish

		pack = None
		if hint and hint.get('pack'): pack = MetaPack.instance(pack = hint.get('pack'))

		# Estimate the number of subrequests per media type.
		# The detailed request count can be found in each _metadataXXXUpdate() function.
		if media == Media.Movie:
			if self.mDetail == MetaTools.DetailEssential: multiplier = 3 if foreign else 2
			elif self.mDetail == MetaTools.DetailStandard: multiplier = 7 if foreign else 6
			elif self.mDetail == MetaTools.DetailExtended: multiplier = 9 if foreign else 8
		elif media == Media.Show:
			if self.mDetail == MetaTools.DetailEssential: multiplier = 3 if foreign else 2
			elif self.mDetail == MetaTools.DetailStandard: multiplier = 5 if foreign else 4
			elif self.mDetail == MetaTools.DetailExtended: multiplier = 9 if foreign else 8
		elif media == Media.Season:
			# The exact number of seasons are not known beforehand.
			count = 0
			if pack: count = pack.countSeasonTotal()
			if not count: count = 10
			if self.mDetail == MetaTools.DetailEssential: multiplier = count + 2
			elif self.mDetail == MetaTools.DetailStandard: multiplier = ((2 * count) if foreign else count) + 3
			elif self.mDetail == MetaTools.DetailExtended: multiplier = ((4 * count) if foreign else (3 * count)) + 7
		elif media == Media.Episode:
			# The exact number of episodes are not known beforehand.
			count = 0
			if pack: count = pack.countEpisodeOfficial(season = hint.get('season'))
			if not count: count = 15
			if self.mDetail == MetaTools.DetailEssential: multiplier = count + 3
			elif self.mDetail == MetaTools.DetailStandard: multiplier = count + 3
			elif self.mDetail == MetaTools.DetailExtended: multiplier = (2 * count) + 5
		elif media == Media.Pack:
			if self.mDetail == MetaTools.DetailEssential: multiplier = 3
			elif self.mDetail == MetaTools.DetailStandard: multiplier = 4
			elif self.mDetail == MetaTools.DetailExtended: multiplier = 5
		elif media == Media.Set:
			if self.mDetail == MetaTools.DetailEssential: multiplier = 2
			elif self.mDetail == MetaTools.DetailStandard: multiplier = 3
			elif self.mDetail == MetaTools.DetailExtended: multiplier = 3

		# Episodes from multiple shows.
		# Eg: Progress menu.
		# No accurate counts available. Just mutiply the number of shows in the menu with the default count.
		if hint and hint.get('count'): multiplier *= hint.get('count')

		if not foreground is None:
			self.mJob[MetaCache.RefreshForeground]['count'] += foreground * multiplier
			self.mJob[MetaCache.RefreshForeground]['media'].append(media)
			if not content is None: self.mJob[MetaCache.RefreshForeground]['content'] = content

		if not background is None:
			self.mJob[MetaCache.RefreshBackground]['count'] += background * multiplier
			self.mJob[MetaCache.RefreshBackground]['media'].append(media)
			if not content is None: self.mJob[MetaCache.RefreshBackground]['content'] = content

		if not none is None:
			self.mJob[None]['count'] += none
			self.mJob[None]['media'].append(media)
			if not content is None: self.mJob[None]['content'] = content

	##############################################################################
	# PROVIDER
	##############################################################################

	def providers(self, id = None):
		if self.mProviders is None:
			self.mProviders = {
				MetaTrakt.id() : MetaTrakt,
				MetaImdb.id() : MetaImdb,
				MetaTmdb.id() : MetaTmdb,
			}
		return self.mProviders.get(id) if id else self.mProviders

	def providerName(self, id):
		provider = self.providers(id = id)
		return provider.name() if provider else None

	def provider(self, content = None, media = None, niche = None, keyword = None, release = None, genre = None, certificate = None, company = None, studio = None, network = None, award = None, gender = None, ranking = None, **parameters):
		providers = self.providers()

		trakt = MetaTrakt.id()
		imdb = MetaImdb.id()
		tmdb = MetaTmdb.id()
		weight = {i : 0 for i in providers.keys()}

		extra = 10
		full = 3
		good = 2
		poor = 1
		none = -1000

		# Basic support for TMDb.
		if Media.isSet(media): return [tmdb]
		elif content == MetaManager.ContentSearch: weight[tmdb] = poor
		else: weight[tmdb] = none

		# EXPLORE
		# If sorting is involved, prefer IMDb over Trakt, since Trakt cannot sort by most attributes.
		# If no sorting is involved, prefer Trakt over IMDb, since IMDb has a page limit.
		if Media.isAll(niche):
			# Prefer Trakt, since it has no page limit.
			weight[trakt]	+= full
			weight[imdb]	+= poor
		elif Media.isNew(niche):
			# Prefer IMDb, since Trakt returns few links and has no proper paging.
			weight[trakt]	+= poor
			weight[imdb]	+= full
		elif Media.isHome(niche):
			# Prefer Trakt, since it has better home release dates.
			weight[trakt]	+= full
			weight[imdb]	+= poor
		elif Media.isBest(niche):
			# Prefer IMDb, since it has better ratings.
			weight[trakt]	+= poor
			weight[imdb]	+= full
		elif Media.isWorst(niche):
			# Prefer IMDb, since it can sort by rating.
			weight[trakt]	+= poor
			weight[imdb]	+= full
		elif Media.isPrestige(niche):
			# Prefer Trakt, since it has no page limit.
			weight[trakt]	+= full
			weight[imdb]	+= poor
		elif Media.isPopular(niche):
			# Prefer IMDb, since it has more votes.
			weight[trakt]	+= poor
			weight[imdb]	+= full
		elif Media.isUnpopular(niche):
			# Prefer IMDb, since it can sort by votes.
			weight[trakt]	+= poor
			weight[imdb]	+= full
		elif Media.isViewed(niche):
			# Prefer Trakt, since it uses the actual watches, not the vote count.
			weight[trakt]	+= full
			weight[imdb]	+= poor
		elif Media.isGross(niche):
			# Trakt does not have any finacial details.
			weight[trakt]	+= none
			weight[imdb]	+= poor
		elif Media.isAward(niche):
			# Trakt does not have any award details.
			weight[trakt]	+= none
			weight[imdb]	+= poor
		elif Media.isTrend(niche):
			# Trakt's Trending enpoint is more current/temporary, since it shows the titles currently watched by users.
			# IMDb's Moviemeter also incorporates trends, but a lot seems to be based on the rating/votes.
			# Prefer IMDb, because the other explore menus already use Trakt a lot.
			weight[trakt]	+= poor
			weight[imdb]	+= good

		if release:
			if release == MetaProvider.ReleaseFuture:
				weight[trakt]	+= good
				weight[imdb]	+= poor		# Mostly only has year, but no full premiere date.

		if genre:
			genres = self.mTools.genre()
			if not Tools.isList(genre): genre = [genre]
			for i in genre:
				i = genres.get(i)
				if i and i['support'].get(media):
					m = i['provider']
					for p in weight.keys():
						v = m.get(p, {}).get(media, False)
						if v is True: weight[p] += good
						elif v is None: weight[p] += poor
						elif v is False: weight[p] += none
				else: # Unsupport genre by media or all providers.
					for p in weight.keys():
						weight[p] += none

			# Only IMDb supports AND genres.
			# Trakt ORs genres.
			if Media.isTopic(niche) or Media.isMood(niche): weight[trakt] += none

		# Trakt can only filter by year, which is the cur rent year and might already be released titles.
		if Media.isFuture(niche):
			weight[trakt]	+= poor
			weight[imdb]	+= extra

		# Trakt has few titles listed for Sports/Sporting-Event.
		if Media.isSport(niche):
			weight[trakt]	+= poor
			weight[imdb]	+= extra # Add double to use IMDb for Explore, eg All Releases.

		# IMDb can search by primary language/country, whereas Trakt searches any language/country.
		# Hence, many unrelated titles show up when using Trakt (eg: Germanic cinema lists almost no German movies).
		if Media.isRegion(niche):
			weight[trakt]	+= poor
			weight[imdb]	+= extra # Add double to force using IMDb.

		# IMDb has a separate keyword parameter, whereas Trakt adds it to the search query.
		if keyword or Media.isPleasure(niche):
			# Do not do this atm. IMDb might have separate keywords, but the results return too many un or less related titles.
			# Eg: for "Cannabis", IMDb returns few stoners movies and a ton of titles where weed might have only be mentioned once, whereas Trakt returns mostly stoner movies.
			# Plus we can search mutiple keywords on Trakt (ORed).
			#weight[trakt]	+= poor
			#weight[imdb]	+= extra
			weight[trakt]	+= extra
			weight[imdb]	+= full

		# IMDb has its own media type for miniseries.
		# Trakt hasw a mini-series genre, but there are 0 titles listed under it.
		if Media.isMini(niche):
			weight[trakt]	+= poor # Still allow it, in case the genre ever starts to work on Trakt.
			weight[imdb]	+= extra # Add double to force using IMDb.

		# IMDb (1m titles): has more titles listed under its "Shorts" and "TV Shorts" media types.
		# Trakt (330k titles): has way less titles listed under its "Short" genre. Hence, shorts are retrieved from Trakt using the duration parameter.
		if Media.isShort(niche):
			# IMDb has 6k+ shows listed under the "Short" genre.
			# Trakt only has 3 shows listed under the "Short" genre.
			if Media.isSerie(media):
				weight[trakt]	+= poor # Still allow it, in case the genre ever starts to work on Trakt.
				weight[imdb]	+= extra # Add double to force using IMDb.
			else:
				weight[trakt]	+= good
				weight[imdb]	+= extra # Add double to force using IMDb.

		# IMDb (50k titles): has more titles listed under its "TV Specials" media type.
		# Trakt (1k titles): has way less titles listed under, since it uses the "Holiday" genre and extra keywords in the query.
		if Media.isSpecial(niche):
			weight[trakt]	+= poor
			weight[imdb]	+= extra # Add double to force using IMDb.

		# IMDb (150k titles): has more titles listed under its "TV Movies" media type.
		# Trakt (1k titles): has way less titles listed under, since it uses extra keywords in the query.
		if Media.isTelevision(niche):
			weight[trakt]	+= poor
			weight[imdb]	+= extra # Add double to force using IMDb.

		# IMDb has more titles listed for studios than Trakt.
		# Trakt has a "network" parameter, but very few titles are listed under it and it only works for shows.
		# IMDb has a hacky way of searching by a network and excluding other rival companies, that works well enough.
		# Trakt is also more accurate, since IMDb can list the same company as studio, network, or other producer or distributor.
		company = MetaProvider.company(niche = niche, company = company, studio = studio, network = network)
		if company:
			if content == MetaManager.ContentSearch:
				weight[trakt]	+= good
				weight[imdb]	+= full
			else:
				networked = False
				advanced = False
				types = [MetaProvider.CompanyVendor, MetaProvider.CompanyProducer, MetaProvider.CompanyBroadcaster, MetaProvider.CompanyDistributor, MetaProvider.CompanyOriginal]
				for k, v in company.items():
					if MetaProvider.CompanyNetwork in v: networked = True
					elif any(i in types for i in v): advanced = True
				if networked and Media.isFilm(media):
					weight[trakt]	+= poor
					weight[imdb]	+= extra
				elif advanced:
					weight[trakt]	+= good
					weight[imdb]	+= extra

		if award:
			weight[trakt]	+= poor if award in [MetaTools.AwardTop100, MetaTools.AwardTop250, MetaTools.AwardTop1000, MetaTools.AwardBottom100, MetaTools.AwardBottom250, MetaTools.AwardBottom1000] else none
			weight[imdb]	+= extra # Add double to force using IMDb.

		if ranking:
			weight[trakt]	+= poor
			weight[imdb]	+= extra # Add double to force using IMDb.

		# IMDb often has titles not on Trakt/TMDb/TVDb yet. Eg: the unreleased Avatar movies ("Avatar 5").
		# When searching with IMDb (eg: query=avatar), titles are returned that do not have detailed metadata (eg: duration), since they are not on Trakt/etc yet, making the menu look ugly.
		# It is therefore better to use Trakt, where the search results look cleaner, having all the durations.
		# Plus IMDb's results deviate quickly from the search query, whereas Trakt has more accurate results at the top.
		if content == MetaManager.ContentSearch:
			if media == Media.List:
				weight[trakt]	+= full
				weight[imdb]	+= none
			elif not company:
				weight[trakt]	+= full
				weight[imdb]	+= good

		# Trakt does not have images for people. IMDb does.
		# Only IMDb can lookup by gender.
		if media == Media.Person or content == MetaManager.ContentPerson:
			weight[imdb]	+= full
			weight[trakt]	+= none if (gender or award) else poor

		# IMDb does not support seasons at all
		if Media.isSeason(media): weight[imdb] = none

		# IMDb does support episodes, but the discover/search does not return the episode number, only the show and episode titles and IDs.
		# Additionally, IMDb episode searches often contain mutiple (different) episodes from the same show, instead of episodes from all different shows.
		elif Media.isEpisode(media): weight[imdb] = poor

		return [i[0] for i in Tools.listSort(weight.items(), key = lambda i : i[1], reverse = True) if i[1] >= 0]

	##############################################################################
	# PROCESS
	##############################################################################

	def _process(self, media, items, parameters = None, filter = False, sort = False, order = False, page = False, limit = False, more = None, unknown = None):
		try:
			if items:
				# Filter
				if filter:
					full = Tools.isInteger(more) and len(items) == more
					if filter.get(MetaTools.FilterDuplicate) is True and (Media.isSeason(media) or Media.isEpisode(media)): filter[MetaTools.FilterDuplicate] = {'number' : True}
					items = self.mTools.filter(items = items, filter = filter, unknown = unknown)
					if full: more = len(items) # Update smart paging, eg: Anime filtered Progress menu.

				# Sort
				if sort or order: items = self.mTools.sort(items = items, sort = sort, order = order, inplace = True)

				# Limit
				if not page is False: items = self._limitPage(media = media, items = items, page = page, limit = limit, more = more, parameters = parameters)
				elif limit: items = self._limitItems(media = media, items = items, limit = limit, parameters = parameters)
		except: Logger.error()
		return items

	def _processSerie(self, media, items):
		# Certain menus contain seasons or episodes, instead of shows.
		# Eg: New Releases -> New Seasons/Episodes
		# Loading these menus as season/episode menus is very inefficient, since each entry is from a different show and would have to retrieve/generate pack metadata and full episode/season/show metadata.
		# Just create these menus as show menus with some additional metadata/labels from the season/episode.
		# This then only requires the show metadata retrieval, and only if the user clicks on a shopw, is the full pack/season metadata loaded.
		# Note that Trakt and IMDb return different structures in this case.

		if Media.isSeason(media) or Media.isEpisode(media):
			result = []

			for item in items:
				try: show = item['temp'][MetaTrakt.id()]['detail']['show']
				except: show = None

				try: premiere = item['time'][MetaTools.TimePremiere]
				except: premiere = None
				if not premiere:
					premiere = item.get('aired') or item.get('premiered')
					if premiere: premiere = Time.timestamp(premiere, format = Time.FormatDate, utc = True)

				# Trakt metadata.
				if show:
					season = item.get('season')
					if not season is None: show['season'] = season

					episode = item.get('episode')
					if not episode is None: show['episode'] = episode

					if premiere:
						if not show.get('time'): show['time'] = {}
						show['time'][MetaTools.TimeSerie] = premiere

					result.append(show)

				# IMDb metadata.
				# Does not have season/episode numbers.
				elif not Media.isShow(item.get('metadata')):
					item['media'] = Media.Show
					if premiere:
						if not item.get('time'): item['time'] = {}
						item['time'][MetaTools.TimeSerie] = premiere
					result.append(item)

			items = result

		return items

	def _processor(self, media = None, niche = None, release = None, year = None, date = None, genre = None, language = None, country = None, certificate = None, award = None, ranking = None, rating = None, votes = None, filter = None, sort = None, order = None, page = None, limit = None, strict = None):
		if filter is None: filter = {}

		niche = Tools.copy(niche)
		if not niche: niche = []
		nicheFilter = []
		if ranking: niche.append(ranking)

		if page is None: page = 1
		if limit is None: limit = self.limit(media = media)

		if Media.isAll(niche):
			sort = MetaTools.SortNone
		elif Media.isNew(niche):
			sort = MetaTools.SortNewest
			filter[MetaTools.FilterTime] = MetaTools.TimeLaunch
		elif Media.isHome(niche):
			sort = MetaTools.SortLatest
			filter[MetaTools.FilterTime] = MetaTools.TimeHome
		elif Media.isBest(niche):
			sort = MetaTools.SortBest
		elif Media.isWorst(niche):
			sort = MetaTools.SortWorst
		elif Media.isPrestige(niche):
			sort = MetaTools.SortNone
		elif Media.isPopular(niche):
			sort = MetaTools.SortPopular
		elif Media.isUnpopular(niche):
			sort = MetaTools.SortUnpopular
		elif Media.isViewed(niche):
			sort = MetaTools.SortNone
		elif Media.isGross(niche):
			sort = MetaTools.SortNone
		elif Media.isAward(niche):
			sort = MetaTools.SortNone
		elif Media.isTrend(niche):
			sort = MetaTools.SortNone

		if Media.isTopic(niche): filter[MetaTools.FilterGenre] = self.mTools.nicheTopic(niche = niche, strict = strict)
		elif Media.isMood(niche): filter[MetaTools.FilterGenre] = self.mTools.nicheMood(niche = niche)

		if Media.isKid(niche): filter[MetaTools.FilterKid] = True
		elif Media.isTeen(niche): filter[MetaTools.FilterTeen] = True

		if Media.isRegion(niche):
			region = self.mTools.nicheRegion(niche = niche)
			if region.get('language'): filter[MetaTools.FilterLanguage] = region.get('language')
			elif region.get('country'): filter[MetaTools.FilterCountry] = region.get('country')

		if Media.isQuality(niche): filter[MetaTools.FilterRating] = {'include' : self.mTools.nicheQuality(niche = niche, media = media), 'deviation' : True}

		if Media.isAge(niche): filter[MetaTools.FilterTime] = {'include' : self.mTools.nicheAge(niche = niche, format = True), 'time' : MetaTools.TimeLaunch, 'deviation' : True}

		if release:
			if MetaProvider.ReleaseNew in release:
				if sort is None: sort = MetaTools.SortNewest
				filter[MetaTools.FilterTime] = {'include' : [None, Time.format(format = Time.FormatDate)], 'time' : MetaTools.TimeLaunch, 'deviation' : True}
			elif MetaProvider.ReleaseHome in release:
				if sort is None: sort = MetaTools.SortLatest
				filter[MetaTools.FilterTime] = {'include' : [None, Time.format(format = Time.FormatDate)], 'time' : MetaTools.TimeHome, 'deviation' : True}
			elif MetaProvider.ReleaseFuture in release:
				if sort is None: sort = MetaTools.SortOldest
				filter[MetaTools.FilterTime] = {'include' : [Time.future(days = 1, format = Time.FormatDate), None], 'time' : MetaTools.TimeLaunch, 'deviation' : False}

		# Trakt sometimes returns titles that do not fall within the date range.
		# This is because dates can vary greatly between providers, such as which date (premiere/limited/theatrical/digital) is used as the release, or there being big gaps between these different dates.
		# Set "deviation = True" to allow some margin during filtering. Titles who's dates are a little bit off will be acepted, only only dates that are far off will be filtered out.
		if date:
			# Do not filter if we only retrieve a single day.
			# Otherwise in most cases ALL titles get filtered out, since more accurate release dates are retrieved from TMDb, which are mostly not the exact requested date.
			if not(Tools.isArray(date) and len(date) == 2 and date[0] == date[1]):
				filter[MetaTools.FilterTime] = {'include' : date, 'time' : MetaTools.TimeHome if Media.isHome(niche) else MetaTools.TimeLaunch, 'deviation' : True}

		if genre:
			if not Tools.isArray(genre): genre = [genre]
			genre = [i for i in genre if not i == MetaTools.GenreNone] # Do not filter by "None" genre.
			if genre:
				if filter.get(MetaTools.FilterGenre): filter[MetaTools.FilterGenre].extend(genre)
				else: filter[MetaTools.FilterGenre] = genre

		if language:
			if filter.get(MetaTools.FilterLanguage): filter[MetaTools.FilterCountry].extend(language if Tools.isArray(language) else [language])
			else: filter[MetaTools.FilterLanguage] = language if Tools.isArray(language) else [language]

		if country:
			if filter.get(MetaTools.FilterCountry): filter[MetaTools.FilterCountry].extend(country if Tools.isArray(country) else [country])
			else: filter[MetaTools.FilterCountry] = country if Tools.isArray(country) else [country]

		if certificate:
			if filter.get(MetaTools.FilterCertificate): filter[MetaTools.FilterCertificate].extend(certificate if Tools.isArray(certificate) else [certificate])
			else: filter[MetaTools.FilterCertificate] = certificate if Tools.isArray(certificate) else [certificate]

		if award:
			if sort is None:
				if award in [MetaTools.AwardTop100, MetaTools.AwardTop250, MetaTools.AwardTop1000]: sort = MetaTools.SortBest
				elif award in [MetaTools.AwardBottom100, MetaTools.AwardBottom250, MetaTools.AwardBottom1000]: sort = MetaTools.SortWorst

		return {
			'niche' : niche,
			'filter' : filter or None,
			'sort' : sort,
			'order' : order,
			'page' : page,
			'limit' : limit,
		}

	# Should not be used if the list comes from a niche-filtered provider request (normal menus), since that should be enough to be included in the menu, even if their detailed metadata has some values missing, like a secondary company or genre, or discrepancies in other values (eg: network "CBS" vs "CBS All Access" are both "cbs" in the niche).
	# Only use for smart Progress menus, where we want to exclude non-niche history items.
	def _processorNiche(self, niche = None, filter = None, generic = False):
		if filter is None: filter = {}

		# Only add this for niches if specifically requested.
		# Since studios/networks might be missing from the metadata, or the name has discrepancies (eg: "CBS" vs "CBS All Access").
		# Used for Progress menus.
		if niche:
			niche = Media.stringFrom(niche)

			if generic:
				exclude = []

				# Only use the company ID, not the company type, otherwise too few might be returned.
				exclude.extend([Media.Original, Media.Producer, Media.Broadcaster, Media.Distributor])

				niche = Tools.copy(niche) # Copy in order not to edit the original.
				for i in exclude: niche = Media.remove(media = niche, type = i)

			value = filter.get(MetaTools.FilterNiche)
			filter[MetaTools.FilterNiche] = [] # Do not edit the original niche list.

			if value:
				value = Media.stringFrom(value)
				if Tools.isArray(value): filter[MetaTools.FilterNiche].extend(value)
				else: filter[MetaTools.FilterNiche].append(value)

			if Tools.isArray(niche): filter[MetaTools.FilterNiche].extend(niche)
			else: filter[MetaTools.FilterNiche].append(niche)

		return filter

	def _processorFilter(self, media = None, niche = None, niched = None, year = None, date = None, genre = None, language = None, country = None, certificate = None, award = None, ranking = None, rating = None, votes = None, page = None, limit = None, strict = None):
		return self._processor(media = media, niche = niche, niched = niched, year = year, date = date, genre = genre, language = language, country = country, certificate = certificate, award = award, ranking = ranking, rating = rating, votes = votes, page = page, limit = limit, strict = strict).get('filter')

	def _processorSort(self, media = None, niche = None, year = None, date = None, genre = None, language = None, country = None, certificate = None, award = None, ranking = None, rating = None, votes = None, page = None, limit = None, strict = None):
		return self._processor(media = media, niche = niche, year = year, date = date, genre = genre, language = language, country = country, certificate = certificate, award = award, ranking = ranking, rating = rating, votes = votes, page = page, limit = limit, strict = strict).get('sort')

	def _processorOrder(self, media = None, niche = None, year = None, date = None, genre = None, language = None, country = None, certificate = None, award = None, ranking = None, rating = None, votes = None, page = None, limit = None, strict = None):
		return self._processor(media = media, niche = niche, year = year, date = date, genre = genre, language = language, country = country, certificate = certificate, award = award, ranking = ranking, rating = rating, votes = votes, page = page, limit = limit, strict = strict).get('order')

	##############################################################################
	# LIMIT
	##############################################################################

	def limit(self, media = None, content = None, submenu = None):
		if not media in self.mLimits: self.mLimits[media] = {}
		if not content in self.mLimits[media]:
			limit = 50
			if content == MetaManager.ContentSearch:
				limit = self.mTools.settingsPageSearch()
			elif content == MetaManager.ContentProgress:
				limit = self.mTools.settingsPageProgress()
			elif submenu:
				if self.mTools.submenuIsEpisode(submenu = submenu): limit = self.mTools.settingsPageSubmenu()
				elif self.mTools.submenuIsSequential(submenu = submenu): limit = self.mTools.settingsPageAbsolute()
				elif self.mTools.submenuIsAbsolute(submenu = submenu): limit = self.mTools.settingsPageAbsolute()
				else: limit = self.mTools.settingsPageSerie()
			else:
				if media is None or Media.isMixed(media): limit = self.mTools.settingsPageMixed()
				elif Media.isEpisode(media): limit = self.mTools.settingsPageEpisode()
				elif Media.isSeason(media): limit = self.mTools.settingsPageEpisode()
				elif Media.isSerie(media): limit = self.mTools.settingsPageShow()
				else: limit = self.mTools.settingsPageMovie()
			self.mLimits[media][content] = limit
		return self.mLimits[media][content]

	def _limitItems(self, items, limit = None, media = None, parameters = None):
		try:
			if limit is True or limit is None: limit = self.limit(media = media, content = parameters.get('content'))
			if limit: return items[:limit]
		except: Logger.error()
		return items

	# more: True = force add a More menu, False = never add a More menu, None = add a More menu if there are enough items, Integer = add a More menu if there are enough items, the value is the total/maximum titles in a fixed list that is not paged through an API.
	def _limitPage(self, items, page = None, limit = None, more = None, media = None, parameters = None):
		try:
			parent = False
			content = None
			submenu  = False
			season = None
			episode = None
			offset = None

			if parameters:
				parent = True
				if page is None and 'page' in parameters:
					try: page = int(parameters['page'])
					except: pass
				if limit is None and 'limit' in parameters:
					try: limit = int(parameters['limit'])
					except: pass
				content = parameters.get('content')
				submenu = parameters.get('submenu')
				season = parameters.get('season')
				episode = parameters.get('episode')
				offset = parameters.get('offset')
			else:
				parameters = {}

			if page is None or page is True: page = 1
			if limit is None or limit is True: limit = self.limit(media = media, content = content, submenu = submenu)

			total = None
			if more and Tools.isInteger(more):
				total = more
				more = None
			elif not more is True:
				total = len(items)
				if total == limit: total = None

			# Filter out any specials that were already shown on the previous page.
			# Only allow specials after the last special of the previous page.
			if submenu and offset:
				for i in range(len(items)):
					item = items[i]
					if item.get('season') == 0 and item.get('episode') == offset:
						items = [item for j, item in enumerate(items) if not item.get('season') == 0 or j > i]
						break

			if self.mTools.submenuIsEpisode(submenu = submenu):
				history = MetaTools.submenuHistory()

				# Use the actual episode we want to watch, not the values passed in by parameters, which are offsetted by submenuHistory().
				# Only do this for the 1st page where we add the history.
				if page <= 1:
					count = 0
					for item in items:
						if item.get('season') > 0:
							count += 1
							if count > history:
								season = item.get('season')
								episode = item.get('episode')
								break

				# Sometimes there are too many specials at the end of a season, which prevents a submenu from opening at the correct last watched episode.
				# Eg: It's Always Sunny in Philadelphia - watch all episodes until and including S07E01.
				# If one opens the submenu, one expects S07E02 to be listed.
				# However, it still lists S06E11+ with all the specials at the end of S06, requiring to go to the next page before finding S07.
				# Not sure if this impacts any other operations, like flatten series menus, etc.
				# Another example: Bunch of specials at the end of GoT S07.
				try:
					# Still keep the actual history episodes one might want to rewatch.
					include = []
					for i in range(0, min(history, len(items))):
						if items[i].get('season') > 0:
							include.append(items[i])

					actual = -1
					for i in range(history, len(items)):
						if items[i].get('season') > 0:
							actual = i + 1
							break

					if actual > 0 and actual > limit: items = Tools.listUnique(include + items[actual - history - 1:]) # The same item can be in both "include" and the sub-array. Remove duplicate references.
				except: Logger.error()

				# Limit the maximum number of specials before the 1st official episode to 3.
				# Otherwise the submenu under Progress might only show 10 specials, and the user has to page to the next page to get the actual episode to watch.
				try:
					if (not page or page == 1) and not season is None and not episode is None:
						exclude = []
						for i in range(len(items)):
							item = items[i]
							if item.get('season') == 0: exclude.append(i)
							elif item.get('season') == season and item.get('episode') == episode: break

						# Keep the last (probably the most relevant) specials, preceeding the 1st episode.
						# Remove the older specials that exceed "history" count, namely all specials before the ones we exclude in the previous statement.
						exclude = exclude[:len(exclude) - history]
						if exclude: items = [i for j, i in enumerate(items) if j not in exclude]
				except: Logger.error()

				# If the menu limit is so small that it is lower than the "irrelevant" previously-watched episodes and specials, start removing the earlier ones.
				# Eg: menu limit is 6, but there are 3 specials + 3 previously-watched episodes, filling the menu, so that the actual episode of interest is cut off at position 7+.
				# This will cut away both episodes and specials, until the episode of interest is in the menu.
				try:
					if limit:
						index = -1
						for i in range(len(items)):
							item = items[i]
							if item.get('season') == season and item.get('episode') == episode:
								index = i
								break
						if index >= 0 and index >= limit: items = items[index - limit + 1:]
				except: Logger.error()

			if total and limit and len(items) > limit:
				if submenu: items = items[0 : limit] # Do not apply the page for episode submenus, since they have their own internal paging system.
				else: items = items[(page - 1) * limit : page * limit]

			page += 1
			parameters['page'] = page
			parameters['limit'] = limit

			# Arbitrary paging for episode submenus.
			if submenu and parameters:
				item = None
				for i in reversed(items):
					# Ignore Recaps, Extras, and Specials for series menu.
					# Ignore "sequential" marked specials in the Absolute menu. Eg: Downtown Abbey S06E09.
					if Media.isEpisode(i.get('media')) and (i.get('season') or i.get('season') == season) and not i.get('sequential'):
						item = i
						break
				if item:
					ranged = self._metadataEpisodeRange(pack = item.get('pack'), season = season, episode = episode, limit = limit, number = submenu)
					if ranged:
						if self.mTools.submenuIsSequential(submenu = submenu) or self.mTools.submenuIsAbsolute(submenu = submenu):
							seasonLast = 1
							episodeLast = ranged[submenu]['last']
						else:
							seasonLast = ranged['season']['last']
							episodeLast = ranged['episode']['last']
						if (not seasonLast is None and item['season'] >= seasonLast) and (not episodeLast is None and item['episode'] >= episodeLast): more = False

				# Some shows are only available on IMDb, and have only one episode listed there (eg: tt31566242, tt30346074).
				# Do not add More if there is only one episode in the Series menu.
				if more is None and len(items) > 1: more = True

			if more is None and limit:
				count = len(items)
				offset = page * limit
				if count >= limit and not total and not content == MetaManager.ContentEpisode:
					more = True
				elif total:
					last = Math.roundUpClosest(total, base = limit)
					if count >= limit and offset <= last: more = True
					elif count and offset >= last: more = False

			parameters['more'] = bool(more is True and parent)
		except: Logger.error()
		return items

	##############################################################################
	# RELOAD
	##############################################################################

	# Prevent mutiple reloads running at the same time, or shortly after each other.
	@classmethod
	def _lock(self, mode, media, content, update = True, delay = None, force = False):
		id = 'GaiaManagerReload'

		# Reload from global var, in case another Python process updated the values.
		data = Memory.get(id = id, local = False, kodi = True)
		if not data:
			data = {
				'refresh' : {
					Media.Show	: {MetaManager.ContentQuick : 0, MetaManager.ContentProgress : 0, MetaManager.ContentArrival : 0},
					Media.Movie	: {MetaManager.ContentQuick : 0, MetaManager.ContentProgress : 0, MetaManager.ContentArrival : 0},
					Media.Mixed	: {MetaManager.ContentQuick : 0, MetaManager.ContentProgress : 0, MetaManager.ContentArrival : 0},
				},
				'reload' : {
					Media.Show	: {MetaManager.ContentQuick : 0, MetaManager.ContentProgress : 0, MetaManager.ContentArrival : 0},
					Media.Movie	: {MetaManager.ContentQuick : 0, MetaManager.ContentProgress : 0, MetaManager.ContentArrival : 0},
					Media.Mixed	: {MetaManager.ContentQuick : 0, MetaManager.ContentProgress : 0, MetaManager.ContentArrival : 0},
				},
				MetaManager.Smart : {
					Media.Show	: {MetaManager.ContentQuick : 0, MetaManager.ContentProgress : 0, MetaManager.ContentArrival : 0},
					Media.Movie	: {MetaManager.ContentQuick : 0, MetaManager.ContentProgress : 0, MetaManager.ContentArrival : 0},
					Media.Mixed	: {MetaManager.ContentQuick : 0, MetaManager.ContentProgress : 0, MetaManager.ContentArrival : 0},
				},
			}

		time = Time.timestamp()
		timeout = 180 # 3 minutes.

		if force or (time - data[mode][media][content]) > timeout:
			data[mode][media][content] = time
			if update: Memory.set(id = id, value = data, local = True, kodi = True)

			if delay is None: delay = False if mode == MetaManager.Smart else True
			if delay: Time.sleep(0.03) # Add short sleeps in between, to allow some breating space so that other threads/code can execute.

			return True
		return False

	@classmethod
	def _lockRefresh(self, media, content, update = True, delay = None, force = False):
		return self._lock(mode = 'refresh', media = media, content = content, update = update, delay = delay, force = force)

	@classmethod
	def _lockReload(self, media, content, update = True, delay = None, force = False):
		return self._lock(mode = 'reload', media = media, content = content, update = update, delay = delay, force = force)

	@classmethod
	def _lockSmart(self, media, content, update = True, delay = None, force = False):
		return self._lock(mode = MetaManager.Smart, media = media, content = content, update = update, delay = delay, force = force)

	##############################################################################
	# RELOAD
	##############################################################################

	# Called from playback.py, which in turn is called from trakt.py.
	# history = only update lists/items that are affected by changes in the history (a title was watched/unwatched).
	# progress = only update lists/items that are affected by changes in the progress (a title's unfinished playback progress).
	# arrival = only update lists/items that are affected by changes in the arrivals.
	# delay = whether or not to delay the cache refreshes for the lists by a few seconds in order not to hold up other processes. If False, immediately refresh the cache without waiting.
	@classmethod
	def reload(self, media = None, history = False, progress = False, rating = False, arrival = False, accelerate = False, delay = False, force = False):
		# This function should never be called from the singleton, since its changes the cache delay, and sets self.mReloadBusy.
		# Read the comment below for self.mReloadBusy.
		if self == MetaManager.instance():
			Logger.log('Reloading the menus should never be done with MetaManager.instance().', type = Logger.TypeFatal)
			return False

		if not media:
			for i in [Media.Show, Media.Movie, Media.Mixed]:
				self.reload(media = i, history = history, progress = progress, rating = rating, arrival = arrival, delay = delay, force = force)
			return True

		# Do not use the singleton.
		# Create a custom instance that expires at the end of the call.
		# Since we change the cache and set various member variables that do not change back.
		# By default, do not delay.
		# Since this function is called directly after playback ended, and the cache data should immediately be refreshed.
		# The Kodi menu currently shown might be the one that needs reloading, and the newly refreshed cache data should immediately be available if the Kodi container/menu is reloaded.
		# Do not use DelayNone, but DelayDisable, since we do not want to use threads at all in the cache.
		# Otherwise if we make the refresh calls below, internally they might threaded cache functions still executing, while we already continue to the reload call, which assumes the refresh calls are done and it can directly retrieve from cache.
		# Eg: The progress data might be outdated, which will immediately return the data and then refresh in a background cache thread. The code continues to the reload call, and the reload call will ALSO refresh the data, since the previous refresh call has not finished and updated the cache entry.
		mode = []
		if accelerate: mode.append(MetaManager.ModeAccelerate)
		if not delay: mode.append(MetaManager.ModeUndelayed)
		manager = MetaManager(mode = mode)
		developer = manager.mDeveloper

		# During mixed menu reloads, just retrieve the smart data from cache without causing the cached function to possibly refresh and execute again.
		# Otherwise, if we eg reload during binge watching after an episode is watched, then the show menus are reloaded, and in the end the mixed menus as well.
		# This might then cause the movie menu code to be refreshed/executed, especially if the cache timeout for that menu is very low (eg Quick).
		# Hence, if we refresh movies, only movie menu functions should execute, but not any show functions, and vice versa.
		# If we reload mixed menus, then the internally used data should already be refreshed from a previous call. We should not trigger and possible internal refreshes by calling the cached function with a timeout.
		# Eg: Reload shows after an episode playback finished, this happens:
		#	1. The show Progress/Quick data is refreshed.
		#	2. The show Progress/Quick outer menus from content() are reloaded.
		#	3. The outer mixed menus from content() are reloaded. This will use the refreshed show data from #1, and the "old" movie data from cache from whenever it was last refreshed.
		#	4. At no point during this process should any movie cache-function execute or any movie smart-reloads happen.
		# Sometimes titles from the other media can still be re-retrieved in the background. Namely if a mixed menu is reloaded from content(), it loads the detailed metadata of all titles from page 1 to add them to the cache for quicker access.
		# If the metadata of these titles is outdated, they will be refreshed in the background. Although this should not happen too often.
		manager.mReloadMedia = media

		if not Media.isMixed(media):
			if (history or progress) and self._lockRefresh(media = media, content = MetaManager.ContentProgress, force = force):
				if developer: Logger.log('RELOAD: Refreshing %s Progress ...' % media.capitalize())
				manager.progress(media = media, refresh = True)

			if arrival and self._lockRefresh(media = media, content = MetaManager.ContentArrival, force = force):
				if developer: Logger.log('RELOAD: Refreshing %s Arrivals ...' % media.capitalize())
				manager.arrival(media = media, refresh = True)

			if (history or progress) and self._lockRefresh(media = media, content = MetaManager.ContentQuick, force = force):
				if developer: Logger.log('RELOAD: Refreshing %s Quick ...' % media.capitalize())
				manager.quick(media = media, refresh = True) # Do this last, since it uses the data of the other functions.

		# Reload the cached first page. This is quick, since no full refresh is done.
		# Also do if ratings were updated, to display the user rating in the progress menu after the rating dialog at the end of playback.
		# Do this AFTER all the refresh calls, otherwise it would prevent them from smart-reloading.
		manager.mReloadBusy = True # Prevent smart-reloads if we only reloading the cached menu.

		if (history or progress or rating) and self._lockReload(media = media, content = MetaManager.ContentProgress, force = force):
			if developer: Logger.log('RELOAD: Reloading %s Progress ...' % media.capitalize())
			manager.progress(media = media, reload = True)

		if arrival and self._lockReload(media = media, content = MetaManager.ContentArrival, force = force):
			if developer: Logger.log('RELOAD: Reloading %s Arrivals ...' % media.capitalize())
			manager.arrival(media = media, reload = True)

		if (history or progress or rating) and self._lockReload(media = media, content = MetaManager.ContentQuick, force = force):
			if developer: Logger.log('RELOAD: Reloading %s Quick ...' % media.capitalize())
			manager.quick(media = media, reload = True) # Do this last, since it uses the data of the other functions.

		# Do not disable here again.
		# The reloading in content() will execute the cache function in a background thread that might be delayed (egv GIL switching between threads).
		# Hence, we can already reach this statement before those threads are executed and get to the smart-reload part that checks this variable.
		# This might then cause smart-reloads we do not want if the thread timing is just right.
		# Therefore, the reload() function should NEVER be called by the singleton MetaManager.instance().
		# Create a csutom MetaManager object which is ONLY use for calling the reload() function, and should be discarded afterwards, since it will never smart-reload again.
		#manager.mReloadBusy = False

		return True

	def reloading(self, busy = True, quick = True, mixed = True):
		if busy and self.mReloadBusy: return True
		if quick and self.mReloadQuick: return True
		if mixed and Media.isMixed(self.mReloadMedia): return True
		return False

	def reloadingMixed(self):
		return self.reloading(busy = False, quick = False, mixed = True)

	def reloadingMedia(self):
		return self.mReloadMedia

	##############################################################################
	# PRELOAD
	##############################################################################

	@classmethod
	def preload(self, callback = None):
		try:
			def _update():
				while True:
					if self._batch('status', 'cool'): self._batchProgress(status = 'Cooling Down Requests', detail = 'Pausing retrievals to give APIs some breathing space.')
					if self._batchCanceled():
						self._batchStop()
						return
					Time.sleep(1)

			def _base(data, season = False):
				result = {'imdb' : data.get('imdb'), 'tmdb' : data.get('tmdb'), 'tvdb' : data.get('tvdb'), 'trakt' : data.get('trakt')}
				if season: result['season'] = data.get('season')
				return result

			batch = self._batchStart(strict = True, callback = callback, status = 'Initializing Smart Menus', detail = 'Preparing smart menus for metadata retrieval.')
			Pool.thread(target = _update, start = True)

			# MetaManager:
			#	Use ModeSynchronous to wait for threads.
			# 	Make all MetaCache retrievals execute in the foreground.
			# 	Make smart-reloads execute in the foreground.
			# 	This makes sure any internal threads are completed before moving to the next task.
			# MetaCache:
			# 	Use ModeUndelayed to wait for the cache functions to finish, instead of executing them in a background thread.
			# 	This makes sure any cache threads are completed before moving to the next task.
			manager = MetaManager(mode = [MetaManager.ModeSynchronous, MetaManager.ModeUndelayed]) # Do not use MetaManager.instance(), since we change the cache mode and delay.

			from lib.modules.playback import Playback
			playback = Playback.instance()
			progress = 0.0

			# SYNC TRAKT DATA
			part = 0.05
			if playback._traktEnabled():
				tasks = [
					{'media' : Media.Movie},
					{'media' : Media.Show},
				]
				for i, task in enumerate(tasks):
					media = task.get('media')
					status = 'Synchronizing Trakt %ss' % media.title()
					detail = 'Retrieving your Trakt %s history, progress, and ratings.' % media
					self._batchProgress(percent = progress + ((i + 1) / float(len(tasks)) * part), status = status, detail = detail)

					playback.refresh(media = task.get('media'), history = True, progress = True, rating = True, force = True, reload = False, wait = True)
					if not self._batchCool(): break
			self._batchCool()
			progress += part

			# LOAD SMART MENUS
			part = 0.45
			tasks = [
				{'media' : Media.Movie,	'content' : MetaManager.ContentProgress,	'count' : 3}, # Do this mutiple time to retrieve more detailed metadata.
				{'media' : Media.Show,	'content' : MetaManager.ContentProgress,	'count' : 3},
				{'media' : Media.Movie,	'content' : MetaManager.ContentArrival,		'count' : 3},
				{'media' : Media.Show,	'content' : MetaManager.ContentArrival,		'count' : 3},
				{'media' : Media.Movie,	'content' : MetaManager.ContentQuick,		'count' : 1},
				{'media' : Media.Show,	'content' : MetaManager.ContentQuick,		'count' : 1},
			]
			tasks = [
				{'media' : Media.Movie,	'content' : MetaManager.ContentProgress,	'count' : 1},
				{'media' : Media.Show,	'content' : MetaManager.ContentProgress,	'count' : 1},
			]

			for i, task in enumerate(tasks):
				if self._batchCanceled(): break
				for j in range(task.get('count')):
					if not self._batchCool(): break

					media = task.get('media')
					content = task.get('content')
					status = 'Creating %s %ss' % (content.title(), media.title())
					if content == MetaManager.ContentProgress: detail = 'Assembling custom %s %s smart menus based on your Trakt history.'
					elif content == MetaManager.ContentArrival: detail = 'Assembling custom %s %s smart menus from multiple sources.'
					elif content == MetaManager.ContentQuick: detail = 'Assembling custom %s %s smart menus for swift navigation.'
					self._batchProgress(percent = progress + ((i + 1) / float(len(tasks)) * part), status = status, detail = detail % (media, content))

					manager.content(refresh = True, **task)
					self._batchWait(5)
			self._batchCool()
			progress += part

			# LOAD PROGRESS SEASONS + PACKS
			part = 0.15
			status = 'Populating Progress Seasons'
			detail = 'Fetching seasons for your favorite shows.'
			self._batchProgress(percent = progress, status = status, detail = detail)

			episodes = []
			shows = manager.progress(media = Media.Show, pack = False, detail = False)
			if shows:
				shows = shows.get('items')
				if shows:
					# Remove season number from the progress, otherwise metadataSeason() will only retrieve that season, instead of all seasons.
					shows = [_base(data = i, season = False) for i in shows]

					# Do not make the chunk too large, since packs and detailed metadata for all seasons are retrieved.
					shows = Tools.listChunk(shows, chunk = 5)

					self._batchCool()
					for i, show in enumerate(shows):
						self._batchProgress(percent = progress + ((i + 1) / float(len(shows)) * part))
						seasons = manager.metadataSeason(items = show, pack = False) # Still retrieves the pack, just does not aggregate it.
						if seasons:
							for season in seasons:
								if season:
									values = []
									season = Tools.listSort(season, key = lambda i : 9999 if i.get('season') is None else i.get('season'))

									# Always add the specials, since they take long to load and are interleaved in progress submenus.
									if season[0].get('season') == 0: values.append(_base(data = season.pop(0), season = True))

									# Add the first and last 5 seasons.
									limit = 5
									values.extend([_base(data = i, season = True) for i in season[:limit]])
									values.extend([_base(data = i, season = True) for i in season[-limit:]])

									if values:
										values = manager.mTools.filterDuplicate(items = values, id = True, number = True)
										episodes.extend(values)

						if not self._batchCool(): break

			self._batchCool()
			progress += part

			# LOAD PROGRESS EPISODES
			part = 0.15

			status = 'Populating Progress Episodes'
			detail = 'Fetching episodes for your favorite shows.'
			self._batchProgress(percent = progress, status = status, detail = detail)

			if episodes:
				# Do not make the chunk too large, since some seasons can contain many episodes.
				episodes = Tools.listChunk(episodes, chunk = 3)

				self._batchCool()
				for i, episode in enumerate(episodes):
					self._batchProgress(percent = progress + ((i + 1) / float(len(episodes)) * part))
					manager.metadataEpisode(items = episode, pack = False)
					if not self._batchCool(): break

			self._batchCool()
			progress += part

			# RELOAD CACHED MENUS
			part = 0.1
			count = 2
			for i in range(count):
				if not self._batchCool(): break

				status = 'Creating Smart Menus'
				detail = 'Caching custom smart menus for faster loading.'
				self._batchProgress(percent = progress + ((i + 1) / float(count) * part), status = status, detail = detail)

				playback.reload(history = True, progress = True, rating = True, arrival = True, force = True, wait = True)
				self._batchWait(5)
			self._batchCool()
			progress += part

			self._batchProgress(percent = 0.95, status = 'Finalizing Smart Menus', detail = 'Preparing the smart menus and cleaning up.')
			self._batchWait(30) # Wait for any thread that might still be busy.
			self._batchProgress(percent = 1.0, status = 'Smart Menus Preloaded', detail = 'The smart menus were preloaded and are now ready to use.')
			self._batchStop()
			return True
		except:
			Logger.error()
			self._batchProgress(percent = 1.0, status = 'Smart Preload Failure', detail = 'The smart menus could not be fully preloaded, but should still work.')
			self._batchStop()
			return False

	@classmethod
	def preloadCancel(self):
		self._batchStop()

	##############################################################################
	# GENERATE
	##############################################################################

	# Generate a large metadata.db for the external metadata addon.
	@classmethod
	def generate(self, refresh = False):
		# Size (LZMA is almost the same as ZLIB (default compression) for smaller objects, but can be better for larger objects, such as packs and seasons):
		# The cleaned and ZIP-compressed addon reduces the size by a few 10MBs.
		#	Movie:		+-5KB
		#	Set:		+-2KB
		#	Show:		+-7KB
		#	Pack:		+-10KB
		#	Season:		+-20KB
		#	Episode:	+-210KB

		from lib.modules.tools import Settings
		from lib.modules.interface import Dialog, Format
		from lib.modules.convert import ConverterSize, ConverterDuration

		def _update():
			dialog = Dialog.progress(title = 'Metadata Generation', message = 'Initializing ...')
			cache = MetaCache.instance(generate = True)

			while True:
				progress = self._batch('progress', 'percent')

				detail = self._batch('progress', 'detail')
				if not detail or (Time.timestamp() - detail['time']) > 20:
					detail = cache.details()
					self._batchProgress(detail = detail)

				message = []
				message.append(Format.bold('Status: ') + '%s - %s - %d%% - %s' % (
					Format.bold(ConverterSize(detail.get('size')).stringOptimal()),
					'Cooling Down' if self._batch('status', 'cool') else self._batch('progress', 'status'),
					int(progress * 100),
					ConverterDuration(self._batch('progress', 'time'), unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatClockShort),
				))
				message.append(Format.bold('Usage: ') + '[B]%s%%[/B] (%d%% Trakt, %d%% IMDb, %d%% TMDb)' % (
					int(self._batch('usage', 'global') * 100),
					int(self._batch('usage', 'trakt') * 100),
					int(self._batch('usage', 'imdb') * 100),
					int(self._batch('usage', 'tmdb') * 100),
				))
				message.append(Format.bold('Films: ') + ', '.join(['%s %ss' % (Format.bold(Math.thousand(detail['count'][i])), i.title()) for i in [Media.Movie, Media.Set]]))
				message.append(Format.bold('Series: ') + ', '.join(['%s %ss' % (Format.bold(Math.thousand(detail['count'][i])), i.title()) for i in [Media.Show, Media.Season, Media.Episode, Media.Pack]]))
				message = Format.newline().join(message)

				if progress >= 1:
					dialog.update(101, message)
					self._batchStop()
					while not dialog.iscanceled(): Time.sleep(1)
					return
				else:
					dialog.update(int(progress * 100), message)

				if dialog.iscanceled():
					self._batchStop()
					return
				Time.sleep(1)

		self._batchStart(status = 'Initializing')
		thread = Pool.thread(target = _update, start = True)
		manager = MetaManager(mode = [MetaManager.ModeGenerative, MetaManager.ModeSynchronous, MetaManager.ModeUndelayed])

		# Change all the settings for the best possible metadata.
		settings = [
			'general.language.primary',
			'general.language.secondary',
			'general.language.tertiary',

			'metadata.general.language',
			'metadata.general.country'

			'metadata.rating.movie',
			'metadata.rating.movie.fallback',
			'metadata.rating.show',
			'metadata.rating.show.fallback',

			'image.location',
			'image.style.movie',
			'image.style.set',
			'image.style.show',
			'image.style.season',
			'image.style.episode',
			'image.selection.movie',
			'image.selection.set',
			'image.selection.show',
			'image.selection.season',
			'image.selection.episode',
			'image.selection.episode.show',
			'image.selection.episode.season',
			'image.selection.multiple',
			'image.selection.multiple.show',
			'image.selection.multiple.season',
			'image.special.season',
			'image.special.season.show',
			'image.special.episode',
			'image.special.episode.show',
			'image.special.episode.season',
		]
		for i in settings: Settings.default(i)
		MetaTools.settingsDetailSet(MetaTools.DetailExtended)

		self._batchProgress(status = 'Generating ID List')
		self._batchCool()
		items = manager._cache('cacheExtended', refresh, self._generateAssemble)
		self._batchCool()

		limit = {
			Media.Movie : 8200,
			Media.Set : 2500,
			Media.Show : 8200,
			Media.Pack : 1500,
			Media.Season : 1500, # Should be the same as the items for Media.Pack, since seasons will also retrieve/generate the pack.
		}
		chunk = {
			Media.Movie : 50,
			Media.Set : 50,
			Media.Show : 50,
			Media.Pack : 10,
			Media.Season : 10,
		}

		data = {}
		for i in limit.keys():
			data[i] = []
			values = items.get(Media.Show if i in [Media.Season, Media.Pack] else i)
			if values:
				values = values[:limit[i]]
				values = Tools.copy(values) # Copy, since we change the media.
				for j in values: j['media'] = i # Change the media for seasons and packs.
				data[i] = Tools.listChunk(values, chunk = chunk[i])

		step = 0
		total = sum([len(i) for i in data.values()])
		for k, v in data.items():
			if self._batchCanceled(): break
			self._batchProgress(status = 'Generating %ss' % k.title())
			for i in v:
				step += 1
				self._batchProgress(percent = (step / total) * 0.95)
				manager.metadata(items = i, pack = False)
				if not self._batchCool(): break

		self._batchProgress(percent = 0.95, status = 'Processing Database')
		self._batchWait(30) # Wait for any writes to the database to finish.
		MetaCache.externalGenerate()

		self._batchProgress(percent = 1, status = 'Finished')
		thread.join()
		self._batchStop()

		return True

	@classmethod
	def _generateAssemble(self):
		trakt = MetaTrakt.instance()

		tasks = {
			Media.Movie : {'result' : [], 'limit' : [1350, 1.4, 0.8]},
			Media.Show : {'result' : [], 'limit' : [1200, 1.6, 0.8]},
		}

		year = Time.year()
		for media, task in tasks.items():
			requests = []
			limit = task.get('limit')[0]
			offset = year

			requests.append({'year' : [offset - 3, offset], 'limit' : limit})
			offset -= 4

			limit = int(limit *  task.get('limit')[1])
			for i in range(6):
				requests.append({'year' : [offset - 9, offset], 'limit' : limit})
				offset -= 10
				limit = int(limit *  task.get('limit')[2])

			result = task.get('result')
			for i in requests:
				if i.get('limit') > 0:
					items = trakt.discover(media = media, extended = True, sort = MetaTrakt.SortPopular, **i)
					if items:
						boost = 1.5 # Increase to give recent releases a higher popularity boost.
						for item in items:
							popularity = item.get('votes') or 10
							y = item.get('year')
							if y:
								difference = abs(year - y)
								if difference <= 3: popularity *= boost * (4 - difference) # More recent releases had less time to accumulate votes.
							result.append({'popularity' : int(popularity), 'media' : media, 'imdb' : item.get('imdb'), 'tmdb' : item.get('tmdb'), 'tvdb' : item.get('tvdb'), 'trakt' : item.get('trakt'), 'title' : item.get('title')})

			task['result'] = Tools.listSort(result, key = lambda i : i['popularity'], reverse = True)

		tasks[Media.Set] = {'result' : []}
		items = MetaTmdb.instance().discoverSet()
		if items: tasks[Media.Set]['result'] = [{'media' : item.get('media'), 'tmdb' : item.get('tmdb'), 'title' : item.get('title')} for item in items]

		return {
			Media.Movie : tasks[Media.Movie]['result'],
			Media.Show : tasks[Media.Show]['result'],
			Media.Set : tasks[Media.Set]['result'],
		}

	##############################################################################
	# BATCH
	##############################################################################

	@classmethod
	def _batch(self, *key):
		result = MetaManager.Batch
		for i in key: result = result[i]
		return result

	@classmethod
	def _batchSet(self, type1, type2, value):
		MetaManager.Batch[type1][type2] = value

	@classmethod
	def _batchCanceled(self):
		return self._batch('status', 'cancel')

	@classmethod
	def _batchProgress(self, percent = None, status = None, detail = None):
		if not percent is None: self._batchSet('progress', 'percent', percent)
		if not status is None: self._batchSet('progress', 'status', status)
		if not detail is None: self._batchSet('progress', 'detail', detail)

	@classmethod
	def _batchStart(self, strict = False, status = None, detail = None, callback = None):
		# Keep start/stop close together, to more evenly spread out the requests and reduce the chances of IMDb blocking the IP.
		# When it drops below start, then a bunch of new requests are made, but we quickly cool down again if stop is hit shortly after.
		# Hence, we have smaller batches of requests with shorter cool downs. Instead of having one huge batch and then waiting very long.
		strict = 0.1 if strict else 0.0
		MetaManager.Batch = {
			'limit' : {
				'start' : [0.5 - strict, 0.75 - strict],
				'stop' : 0.6,
			},
			'usage' : {
				'global' : 0,
				'trakt' : 0,
				'imdb' : 0,
				'tmdb' : 0,
			},
			'status' : {
				'cool' : None,
				'cancel' : None,
			},
			'progress' : {
				'time' : 0,
				'percent' : 0,
				'status' : status,
				'detail' : detail,
			},
			'count' : {
				'total' : 0,
				Media.Movie : 0,
				Media.Show : 0,
				Media.Season : 0,
				Media.Episode : 0,
				Media.Pack : 0,
				Media.Set : 0,
				'data' : {
					Media.Movie : {},
					Media.Show : {},
					Media.Season : {},
					Media.Episode : {},
					Media.Pack : {},
					Media.Set : {},
				},
			},
		}
		Pool.thread(target = self._batchUpdate, kwargs = {'callback' : callback}, start = True)
		return MetaManager.Batch

	@classmethod
	def _batchStop(self):
		if MetaManager.Batch: self._batchSet('status', 'cancel', True)

	@classmethod
	def _batchWait(self, seconds):
		for i in range(seconds):
			if self._batchCanceled(): break
			Time.sleep(1)

	@classmethod
	def _batchUpdate(self, callback = None):
		timer = Time(start = True)
		while not self._batchCanceled():
			# Set "authenticated=None" to allow more requests to Trakt with and without authentication data.
			# Speed up Trakt, since Trakt is typiclly causing the cooldown.
			MetaManager.Batch['usage'].update(MetaProvider.usageGlobal(authenticated = None, full = True))
			self._batchSet('progress', 'time', timer.elapsed())
			if callback: callback(MetaManager.Batch)
			Time.sleep(1)

		countTotal = self._batch('count', 'total')
		countMovie = self._batch('count', Media.Movie)
		countShow = self._batch('count', Media.Show)
		countSeason = self._batch('count', Media.Season)
		countEpisode = self._batch('count', Media.Episode)
		countPack = self._batch('count', Media.Pack)
		countSet = self._batch('count', Media.Set)
		Logger.log('BATCH LOADED (Total: %d | %ds): %d Movies | %d Shows | %d Seasons | %d Episodes | %d Packs | %d Sets' % (countTotal, timer.elapsed(), countMovie, countShow, countSeason, countEpisode, countPack, countSet))

		# Clear some memory.
		for k in MetaManager.Batch['count']['data'].keys():
			MetaManager.Batch['count']['data'][k] = {}

		if callback: callback(MetaManager.Batch)

	@classmethod
	def _batchLoad(self, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None):
		if MetaManager.Batch:
			id = None
			if imdb: id = 'imdb' + str(imdb)
			elif trakt: id = 'trakt' + str(trakt)
			elif tmdb: id = 'tmdb' + str(tmdb)
			elif tvdb: id = 'tvdb' + str(tvdb)
			if id:
				id = '%s_%s_%s' % (media, id, str(season))
				count = MetaManager.Batch['count']
				if not id in count['data'][media]:
					count['data'][media][id] = True
					count[media] += 1
					count['total'] += 1

	@classmethod
	def _batchCool(self):
		if not self._batchCanceled() and self._batch('usage', 'global') > self._batch('limit', 'stop'):
			self._batchSet('status', 'cool', Time.timestamp())

			for i in range(10):
				if self._batchCanceled(): break
				Time.sleep(1)

			if not self._batchCanceled():
				limit1 = self._batch('limit', 'start', 0)
				limit2 = self._batch('limit', 'start', 1)
				while True:
					if self._batchCanceled(): break
					if self._batch('usage', 'global') < limit1: break
					elif self._batch('usage', 'trakt') < limit2 and self._batch('usage', 'imdb') < limit2 and self._batch('usage', 'tmdb') < limit2: break

					for i in range(5):
						if self._batchCanceled(): break
						Time.sleep(1)

		self._batchSet('status', 'cool', False)
		return not self._batchCanceled()

	##############################################################################
	# METADATA
	##############################################################################

	# Either pass in a list of items to retrieve the detailed metadata for all of them.
	# Or pass in an ID or title/year to get the details of a single item.

	# By default, do not cache internal requests (eg: Trakt/TVDb/IMDb/Fanart API requests).
	# For a list of 50 items, this will use an additional 8-9MB of the cache (disc space), plus it takes 4 secs longer to write to disc (the entire list takes 17-25 secs).
	# There is no real reason to cache intermediary requests, since the final processed metadata is already cached with MetaCache.
	# The only reason for intermediary caching is if the metadata is imcomplete, and on subsequent menu loading, all of the show's metadata is requested again, even though some of them might have suceeded previously.

	# filter: remove uncommon movies, like those without an IMDb ID. If None, will set to True for multiple items, and to False for a single item.
	# By default, do not cache internal requests (eg: Trakt/TMDb/IMDb/Fanart API requests).
	# For a list of 50 items, this will use an additional 5MB of the cache (disc space), plus it takes 100-200 ms longer to write to disc (although this is insignificant, since the entire list takes 20-25 secs).
	# There is no real reason to cache intermediary reque7sts, since the final processed metadata is already cached with MetaCache.
	# The only reason for intermediary caching is if the metadata is imcomplete, and on subsequent menu loading, all of the movie's metadata is requested again, even though some of them might have suceeded previously.
	# quick = Quickly retrieve items from cache without holding up the process of retrieving detailed metadata in the foreground. This is useful if only a few random items are needed from the list and not all of them.
	# quick = positive integer (retrieve the given number of items in the foreground and the rest in the background), negative integer (retrieve the given number of items in the foreground and do not retrieve the rest at all), True (retrieve whatever is in the cache and the rest in the background - could return no items at all), False (retrieve whatever is in the cache and the rest not at all - could return no items at all), Dictionary {'foreground' : X, 'background' : Y} (retrieve a maximum foreground/background items).
	# threaded = If sub-function calls should use threads or not. None: threaded for single item, non-threaded for multiple items. True: threaded. False: non-threaded.

	# NB NB NB: pack
	#	Take note of the following when calling this function for shows/seasons/episode.
	#	If the pack data is not needed by the caller, pass in "pack=False".
	#	Not only will this save local resources, by not having to read from disk, decompress and JSON-decode large pack data, but also avoids unnecessary pack generation for shows where we do not really need it.
	#	Some pack generations can take 5+ seconds, due to title matching, if there are many episodes with different titles. Eg: Rick and Morty S0 (TVDb vs Trakt/TMDb).
	#	Although the data needed from provider APIs for pack creation only requires a few API calls, those calls can be very large and take a long time (eg: Trakt), since a lot of episode data is retrieved.
	#	For instance, when loading a menu with shows, do not retrieve the pack data, since otherwise it will generate pack data for every show in the menu, although the user might only be interested in a single show.
	#	If "pack=None" (default) or "pack=True" is passed in, the pack will be generated and added to the show/season/episode metadata.
	#	In the future we should make this "pack=False" by default, and require the caller to explicitly pass in "pack=True" in order to get the pack.
	#	But for now, since so many callers assume the pack data will be available, return the pack by default, and let callers explicitly state "pack=False" if they do not need the pack.

	def metadata(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, episode = None, number = None, items = None, pack = None, filter = None, clean = True, quick = None, refresh = False, cache = False, threaded = None, limit = None, next = None, discrepancy = None, special = None, aggregate = True, hierarchical = False):
		# If no media is passed in, assume the items have different media.
		# Eg: Single search across movies and shows.
		if (not media or Media.isMixed(media)) and Tools.isArray(items):
			result = []
			data = {
				Media.Movie : [],
				Media.Show : [],
				Media.Season : [],
				Media.Episode : [],
				Media.Pack : [],
				Media.Set : [],
			}

			for item in items:
				try: data[item.get('media')].append(item)
				except: Logger.error()
			for media, values in data.items():
				if media and values:
					values = self.metadata(media = media, items = values, number = number, pack = pack, filter = filter, clean = clean, quick = quick, refresh = refresh, cache = cache, threaded = threaded, limit = limit, next = next, discrepancy = discrepancy, special = special, aggregate = aggregate, hierarchical = hierarchical)
					if values: result.extend([(self.mTools.index(items = items, item = i, default = -1), i) for i in values])

			return [i[1] for i in Tools.listSort(result, key = lambda i : i[0])]
		else:
			if media is None and Tools.isDictionary(items): media = items.get('media')

			if Media.isShow(media):
				if not episode is None: media = Media.Episode
				elif not season is None: media = Media.Season

			if Media.isFilm(media): return self.metadataMovie(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, items = items, filter = filter, clean = clean, quick = quick, refresh = refresh, cache = cache, threaded = threaded)
			elif Media.isShow(media): return self.metadataShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, items = items, pack = pack, filter = filter, clean = clean, quick = quick, refresh = refresh, cache = cache, threaded = threaded)
			elif Media.isSeason(media): return self.metadataSeason(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, items = items, pack = pack, filter = filter, clean = clean, quick = quick, refresh = refresh, cache = cache, threaded = threaded, aggregate = aggregate)
			elif Media.isEpisode(media): return self.metadataEpisode(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, episode = episode, number = number, items = items, pack = pack, filter = filter, clean = clean, quick = quick, refresh = refresh, cache = cache, threaded = threaded, limit = limit, next = next, discrepancy = discrepancy, special = special, aggregate = aggregate, hierarchical = hierarchical)
			elif Media.isPack(media): return self.metadataPack(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, items = items, filter = filter, clean = clean, quick = quick, refresh = refresh, cache = cache, threaded = threaded)
			elif Media.isSet(media): return self.metadataSet(tmdb = tmdb, title = title, year = year, items = items, filter = filter, clean = clean, quick = quick, refresh = refresh, cache = cache, threaded = threaded)

		return None

	def _metadataDeveloper(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, item = None, extra = None):
		if self.mDeveloper and (not extra or self.mDeveloperExtra):
			data = []

			if not imdb and item and 'imdb' in item: imdb = item['imdb']
			if imdb: data.append('IMDb: ' + str(imdb))

			if not trakt and item and 'trakt' in item: trakt = item['trakt']
			if trakt: data.append('Trakt: ' + str(trakt))

			if not media or Media.isFilm(media) or Media.isSet(media):
				if not tmdb and item and 'tmdb' in item: tmdb = item['tmdb']
				if tmdb: data.append('TMDb: ' + str(tmdb))

			if not media or Media.isSerie(media):
				if not tvdb and item and 'tvdb' in item: tvdb = item['tvdb']
				if tvdb: data.append('TVDb: ' + str(tvdb))

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

	def _metadataTemporize(self, item, result, provider):
		if item:
			temp = item.get('temp', {})
			if temp:
				temp = temp.get(provider)
				if temp:
					# Images
					try:
						data = temp.get(MetaImage.Attribute)
						if data:
							for key, value in data.items():
								if value: result.update({MetaImage.Attribute : {key : [MetaImage.create(link = value, provider = provider)]}})
					except: Logger.error()

					# Voting
					try:
						data = temp.get('voting')
						if data:
							value = data.get('rating')
							if value: result['rating'] = value

							value = data.get('votes')
							if value: result['votes'] = value

							value = data.get('user')
							if value: result['userrating'] = value
					except: Logger.error()

					# Progress
					value = temp.get('progress')
					if value: result['progress'] = value

					# Time
					value = temp.get('time')
					if value:
						if not 'time' in result: result['time'] = {}
						result['time'].update(value)

		return result

	# requests = [{'id' : required-string, 'function' : required-function, 'parameters' : optional-dictionary}, ...]
	def _metadataRetrieve(self, requests, threaded = None):
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
			if threaded is None: threaded = len(requests) > 1
			if threaded:
				threads = [Pool.thread(target = _metadataRetrieve, kwargs = {'request' : request, 'result' : result}, start = True) for request in requests]
				[thread.join() for thread in threads]
			else:
				for request in requests:
					_metadataRetrieve(request = request, result = result)
		return result

	def _metadataRequest(self, link = None, data = None, headers = None, method = None, function = None, cache = False, *args, **kwargs):
		if function:
			if cache:
				if cache is True: cache = Cache.TimeoutLong
				result = self.mCache.cache(mode = None, timeout = cache, refresh = None, function = function, *args, **kwargs)
				if not result:
					# Delete the cache, otherwise the next call will return the previously failed request.
					self.mCache.cacheDelete(function)
					return False
			else:
				result = function(*args, **kwargs)
				if not result: return False
			return result
		else:
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

	def _metadataCache(self, media, items, function, quick = None, refresh = None, cache = None, threaded = None, hierarchical = None, hint = None):
		threading = len(items) == 1 if threaded is None else threaded

		# Use memeber variables instead of local variables.
		# In case this function is called mutiple times from different places to retrieve the same metadata.
		# Eg: Smart menu background refresh while the foreground menu construction from content() also requests the same metadata.
		#lock = Lock()
		#locks = {}
		lock = self.mLock
		locks = self.mLocks

		semaphore = Semaphore(self.mTools.concurrency(media = media, hierarchical = hierarchical))
		metacache = MetaCache.instance(generate = self.mModeGenerative)

		metadataForeground = []
		metadataBackground = []
		jobsForeground = []
		jobsBackground = []

		items = metacache.select(type = media, items = items)

		if quick is None:
			for item in items:
				parameters = {'item' : item, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'cache' : cache, 'threaded' : threading}

				try: refreshing = item[MetaCache.Attribute][MetaCache.AttributeRefresh]
				except: refreshing = MetaCache.RefreshForeground

				# During external metadata addon generation, reretrieve incomplete items.
				if self.mModeGenerative and item[MetaCache.Attribute].get('part'): refreshing = MetaCache.RefreshForeground

				if refreshing == MetaCache.RefreshForeground or (refresh is True or refresh == MetaCache.RefreshForeground) or (refreshing == MetaCache.RefreshBackground and self.mModeSynchronous):
					self.mTools.busyStart(media = media, item = item)
					parameters.update({'result' : metadataForeground, 'mode' : MetaCache.RefreshForeground})
					jobsForeground.append(parameters)

				elif refreshing == MetaCache.RefreshBackground or refresh == MetaCache.RefreshBackground:
					if not self.mTools.busyStart(media = media, item = item):
						parameters.update({'result' : metadataBackground, 'mode' : MetaCache.RefreshBackground})
						jobsBackground.append(parameters)

		else:
			items = Tools.listShuffle(items, copy = True) # Create a shallow copy of the list, so that the order of the items does not change for the list that is passed into metadata().
			valid = []
			lookup = []

			foreground = None
			background = None
			if quick is True:
				foreground = False
				background = True
			elif quick is False:
				foreground = False
				background = False
			elif Tools.isDictionary(quick):
				foreground = quick.get(MetaCache.RefreshForeground, False)
				background = quick.get(MetaCache.RefreshBackground, False)
			elif Tools.isInteger(quick):
				if quick >= 0:
					foreground = quick
					background = True
				else:
					foreground = abs(quick)
					background = False

			for item in items:
				useable = False
				parameters = {'item' : item, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'cache' : cache, 'threaded' : threading}

				try: refreshing = item[MetaCache.Attribute][MetaCache.AttributeRefresh]
				except: refreshing = MetaCache.RefreshForeground

				if refreshing == MetaCache.RefreshNone:
					valid.append(item)

				# Make sure that this does not execute if called from _metadataSmartLoad() with "quick=False" and we are in synchronous mode (called from reload()).
				elif refreshing == MetaCache.RefreshForeground or (refreshing == MetaCache.RefreshBackground and background is True and self.mModeSynchronous):
					if foreground is True or (foreground and len(lookup) < foreground) or (background is True and self.mModeSynchronous):
						self.mTools.busyStart(media = media, item = item)
						valid.append(item)
						lookup.append(item)
						parameters.update({'result' : metadataForeground, 'mode' : MetaCache.RefreshForeground})
						jobsForeground.append(parameters)
					elif background is True or (background and len(jobsBackground) < background):
						useable = True
						if not self.mTools.busyStart(media = media, item = item): # Still add foreground requests to the background threads if the value of "quick" forbids foreground retrieval.
							parameters.update({'result' : metadataBackground, 'mode' : MetaCache.RefreshBackground})
							jobsBackground.append(parameters)

				elif refreshing == MetaCache.RefreshBackground:
					useable = True
					if background is True or (background and len(jobsBackground) < background):
						if not self.mTools.busyStart(media = media, item = item):
							parameters.update({'result' : metadataBackground, 'mode' : MetaCache.RefreshBackground})
							jobsBackground.append(parameters)

				# Still add incomplete metadata to the returned items, since it has metadata, even if something is missing.
				# Important for metadata that is always labeled as incomplete, because it does not exist on some providers.
				# Eg: The Office UK S03 (on IMDb, but not on Trakt/TVDb/TMDb).
				# Also do this for external metadata, other-settings metadata, etc. Everything that is not invalid.
				if useable and not item[MetaCache.Attribute][MetaCache.AttributeStatus] == MetaCache.StatusInvalid: valid.append(item)

			items = valid

		# Do this before starting to execute any threads.
		self._jobUpdate(media = media, foreground = len(jobsForeground), background = len(jobsBackground), hint = hint)

		if jobsForeground:
			if len(jobsForeground) == 1:
				if threaded is None: jobsForeground[0]['threaded'] = True # Faster parallel sub-requests if only one item needs to be retrieved.
				for i in jobsForeground:
					semaphore.acquire()
					function(**i)
			else:
				if threaded is None and len(jobsForeground) == 2: # Faster parallel sub-requests if only two items needs to be retrieved. 3 or more items use sequential requests.
					jobsForeground[0]['threaded'] = True
					jobsForeground[1]['threaded'] = True
				threads = []
				for i in jobsForeground:
					semaphore.acquire()
					threads.append(Pool.thread(target = function, kwargs = i, start = True))
				[thread.join() for thread in threads] # Wait for metadata that does not exist in the metacache.

			# 1 item: wait (do not start a background thread). Multiple items: do not wait (start a background thread).
			if metadataForeground: metacache.insert(type = media, items = metadataForeground, wait = None)

		# Let the refresh of old metadata run in the background for the next menu load.
		# Only start the threads here, so that background threads do not interfere or slow down the foreground threads.
		if jobsBackground:
			def _metadataBackground():
				if len(jobsBackground) == 1:
					if threaded is None: jobsBackground[0]['threaded'] = True # Faster parallel sub-requests if only one item needs to be retrieved. Even do for background, in case a single item in eg Progress menu is refreshed that needs to be loaded shortly afterwards.
					semaphore.acquire()
					function(**jobsBackground[0])
				else:
					# For 2 or more background items, do not use threads, to allow foreground processes to use more.
					for i in range(len(jobsBackground)):
						semaphore.acquire()
						jobsBackground[i] = Pool.thread(target = function, kwargs = jobsBackground[i], start = True)
					[thread.join() for thread in jobsBackground]

				# Wait (do not start a background thread), since we are already inside a thread.
				if metadataBackground: metacache.insert(type = media, items = metadataBackground, wait = True)

			# Make a deep copy of the items, since the items can be edited/aggregated in the calling functions, and we do not want to store the unnecessary/large data in the database.
			# Eg: Adding large pack data, next/previous seasons, show/season images, etc.
			# The data is also deep copied in MetaCache, but because the background update runs in its own thread below, the dict might get edited before MetaCache has a chance to copy it.
			for i in jobsBackground: i['item'] = Tools.copy(i['item'])

			Pool.thread(target = _metadataBackground, start = True)

		return items

	def _metadataAggregate(self, media, items):
		try:
			# The outer list metadata might be refreshed, without the inner title metadata being refreshed, just retrieving the old data from cache.
			# This means there can be new/updated values in temp from the outer list, like the progress, watched time, user rating, or even an updated global rating/votes, while the cached metadata still holds the old/outdated values.
			# Use the temp values and replace the main metadata values.

			if items:
				def _metadataAggregate(item, temp):
					voted = False

					for provider in ['metacritic', 'imdb', 'tvdb', 'tmdb', 'trakt']:
						values = temp.get(provider)
						if values:
							# Voting
							try:
								voting = values.get('voting')
								if voting:
									if not 'voting' in item: item['voting'] = {}
									votingCurrent = item.get('voting')
									for i in ['rating', 'votes', 'user']:
										value = voting.get(i)
										if value:
											if i == 'user': item['userrating'] = value
											if not value == votingCurrent.get(i, {}).get(provider):
												voted = True
												if not i in item['voting']: item['voting'][i] = {}
												item['voting'][i][provider] = value
							except: Logger.error()

							# Progress
							try:
								value = values.get('progress')
								if not value is None: item['progress'] = value
							except: Logger.error()

							# Time
							try:
								value = values.get('time')
								if value:
									if not 'time' in item: item['time'] = {}
									for k, v in value.items():
										if v: item['time'][k] = v
							except: Logger.error()

					# Recalculate the global rating/votes.
					# Only do this if the rating/votes actually changed, to save time.
					if voted: self.mTools.cleanVoting(metadata = item, round = True) # Round to reduce storage space of average ratings with many decimal places.

					aggregate = item.get('aggregate')
					if aggregate:
						del item['aggregate']
						for k, v in aggregate.items():
							item[k] = v

				values = items if Tools.isArray(items) else [items]

				if Media.isSeason(media):
					for item in values:
						temp = item.get('temp')
						if temp:
							numberSeason = item.get('season')
							if not numberSeason is None:
								for i in (item.get('seasons') or []):
									if i.get('season') == numberSeason:
										_metadataAggregate(item = i, temp = temp)
										break
				elif Media.isEpisode(media):
					for item in values:
						temp = item.get('temp')
						if temp:
							numberSeason = item.get('season')
							numberEpisode = item.get('episode')
							if not numberSeason is None and not numberSeason is None:
								for i in (item.get('episodes') or []):
									if i.get('season') == numberSeason and i.get('episode') == numberEpisode:
										_metadataAggregate(item = i, temp = temp)
										break
				else:
					for item in values:
						temp = item.get('temp')
						if temp: _metadataAggregate(item = item, temp = temp)

		except: Logger.error()
		return items

	def _metadataClean(self, media, items, clean = True, deep = True):
		try:
			if clean and items:
				if deep:
					if Media.isSeason(media): deep = 'seasons'
					elif Media.isEpisode(media): deep = 'episodes'
					else: deep = False

				values = items if Tools.isArray(items) else [items]
				if values and Tools.isArray(values[0]): values = Tools.listFlatten(values) # A list for mutiple shows, each containing a list of seasons or episodes.

				for item in values:
					try: del item['temp']
					except: pass

					# Keep the cache form smart menu refreshes.
					if not clean == 'cache':
						try: del item[MetaCache.Attribute]
						except: pass

					if deep:
						values = item.get(deep)
						if values:
							for i in values:
								try: del i['temp']
								except: pass
		except: Logger.error()
		return items

	def _metadataFilter(self, media, items, filter = None, deep = True):
		try:
			if items:
				if filter is None: filter = len(items) > 1
				if filter:
					if deep:
						if Media.isSeason(media): deep = 'seasons'
						elif Media.isEpisode(media): deep = 'episodes'
						else: deep = False
					items = [i for i in items if (not deep or i.get(deep)) and (i.get('imdb') or i.get('trakt') or i.get('tvdb') or i.get('tmdb'))]
		except: Logger.error()
		return items

	##############################################################################
	# METADATA - ID
	##############################################################################

	# Sometimes platforms have the wrong ID for one or more providers.
	# This happens a lot for new releases. Mostly shows, but occasionally movies as well.
	# This happens with TMDb/Trakt:
	#	1. A new title gets added on TMDb.
	#	2. Trakt later scrapes this from TMDb and adds it to its library.
	#	3. A few days later it turns out the info on TMDb is wrong. Either a user entered incorrect info, or more frequently, the title was added multiple times by different users.
	#	4. Trakt later scrapes TMDb again. Now it adds the second/duplicate title to its library as well. So there are now 2+ entries on Trakt.
	#	5. TMDb removes one of the duplicates. The TMDb ID for the deleted title still exists. When opening the TMDb page, the ID+slug still shows in the URL, but it redirects to a 404 page.
	#	6. The one entry on Trakt now points to a TMDb (and possibly a IMDb) ID that does not exist, so retrieving TMDb images/ratings/etc does not work for this title.
	#	7. Trakt sometimes removes the duplicate entry, but this can take very long. And sometimes it does not do this at all and duplicates remain on the platform.
	#	8. This could also mean there are now 2 entries on Trakt with the same IMDb ID. So retrieving metadata from Trakt using the IMDb ID might return the outdated duplicate entry.
	# This can also happen to IMDb, although less frequent:
	#	1. A new title gets added to IMDb.
	#	2. TMDb/TVDb/Trakt scrape these.
	#	3. Later IMDb removes the title and creates a new one with a new ID. This could be duplicates or some other reason IMDb does this.
	#	4. The old IMDb ID now goes to a 404 page, or in some cases actually HTTP redirects to the new ID.
	#	5. TMDb/TVDb/Trakt might still have the old ID and/or a duplicate entry, and it might take a long time until they get cleaned.
	# These incorrect/oudated/non-existing IDs cause various problems:
	#	1. MetaCache might have issues, because there might be multiple entries with partially the same IDs. Retrieving by eg IMDb ID from cache might therefore return the old entry.
	#	2. Retrieving certain metadata, like images and rating, might not work for these titles, since they point to old non-existing IDs.
	# This also causes issues with the Arrivals smart-list:
	#	1. A new release is retrieved from the IMDb Advanced Search or TMDb Discover, only having an IMDb/TMDb ID.
	#	2. Other IDs are looked up using the IMDb/TMDb ID.
	#	3. The looked-up IDs might be different to the original IDs. Either IMDb has the new ID, and the lookup on TVDb/Trakt has the old IDs, or vice versa.
	#	4. Now in the Arrivals smart-list, these are seen as two different titles, since their IDs are different and will not be removed during duplicate filtering.
	# This also causes issues with already cached metadata that is being refreshed.
	#	1. The metadata was retrieved the first time with the old IDs and written to MetaCache.
	#	2. Later this metadata gets fixed on IMDb/TMDb/Trakt.
	#	3. Weeks later the metadata is automatically refreshed.
	#	4. But now the IDs from the old cached metadata is used to make the new requests, possibly retrieving the wrong IMDb or TMDb metadata, or no data at all.
	#	5. Hence, with every metadata refresh, the existing IDs should be REPLACED with the new ones coming in.
	# However, there might still be some IDs that are wrong.
	# Hence, we accumulate all IDs coming in from different providers, and pick the one that occurs most frequently.
	# This will probably not solve all issues, but at least some of them.
	# Example:
	#	The Arrivals menu retrieved this show from TMDb Discover: https://www.themoviedb.org/tv/256212-cris-miro-ella
	#	On Trakt there are multiple entries for this title:
	#		a. Show: https://trakt.tv/shows/cris-miro-she-her-hers (IMDb: tt32495809 | TMDb: 256212)
	#		b. Show: https://trakt.tv/shows/cris-miro-ella (IMDb: tt32495809 | TMDb: 256723 - already deleted)
	#		c. Movie: https://trakt.tv/movies/cris-miro-she-her-hers-2024 (IMDb: None | TMDb: 1308642 - movie, not tv - already deleted)
	#	Now the detailed metadata is retrieved. First an ID lookup is done via TVDb, returning:
	#		{'tvdb': '451157', 'imdb': 'tt32495809', 'tmdb': '256212'}
	#	During detailed metadata retrieval, providers return the following:
	#		IMDb: {'imdb': 'tt32495809'}
	#		TMDb: {'tmdb': '256212', 'imdb': 'tt32495809', 'tvdb': '451157'}
	#		TVDb: {'imdb': 'tt32495809', 'tmdb': '256212', 'tvdb': '451157'}
	#		Trakt: {'imdb': 'tt32495809', 'tmdb': '256723', 'trakt': '244111', 'slug': 'cris-miro-ella'}
	#	Since Trakt is considered most important, its IMDb would be carried over into the final metadata.
	#	By now using the most frequent IDs, we can use TMDb 256212. But Trakt still points to the "wrong" entry, since we technically want https://trakt.tv/shows/cris-miro-she-her-her.

	def _metadataId(self, metadata, ids, type):
		value1 = (metadata.get('id') or {}).get(type)
		value2 = Tools.listCommon(ids[type])
		if not value1: return value2
		elif not value2: return value1
		elif Tools.listCount(ids[type], value2) > Tools.listCount(ids[type], value1): return value2
		else: return value1

	def _metadataIdAdd(self, metadata, ids, type = None):
		values = metadata.get('id')
		if values:
			if type:
				value = values.get(type)
				if value:
					ids[type].append(value)
					return value
			else:
				for k, v in values.items():
					ids[k].append(v)
				return id
		return None

	def _metadataIdUpdate(self, metadata, ids):
		# Always replace the IDs with new values.
		# Otherwise if there is an incorrect IMDb ID on Trakt/TMDb, it gets written to MetaCache.
		# At a later point the ID is corrected on Trakt/TMDb.
		# If the data is now refreshed, the old ID from MetaCache is used instead of the newly retrieved IDs.
		# Hence, always replace these.
		types = ['imdb', 'tmdb', 'tvdb', 'trakt', 'slug']
		if Media.isSerie(metadata.get('media')): types.extend(['tvmaze', 'tvrage'])
		for type in types:
			value = self._metadataId(metadata = metadata, ids = ids, type = type)
			if value:
				# Also add the top-level ID, for legacy purposes, since all over Gaia the IDs are accessed at the top-level of the dictionary.
				# At some later point the entire addon should be updated to have the new ID structure.
				metadata[type] = metadata['id'][type] = value

	def _metadataIdLookup(self, media, title, year = None, list = False):
		if title:
			id = self.mTools.id(media = media, title = title, year = year)
			if id and any(i for i in id.values()):
				result = {'imdb' : id.get('imdb'), 'tmdb' : id.get('tmdb'), 'tvdb' : id.get('tvdb'), 'trakt' : id.get('trakt')}
				return [result] if list else result
		return None

	##############################################################################
	# METADATA - SMART
	##############################################################################

	# remove:
	#	remove=True: Remove items that are not in "new".
	# detail: Wether or not to return detailed metadata.
	def _metadataSmart(self, media = None, items = None, new = None, filter = None, sort = None, order = None, limit = None, remove = None, content = None, timer = None, detail = False):
		try:
			if timer is None: timer = Time(start = True)
			current = Time.timestamp()

			stats = None
			helper = {}
			arrival = content == MetaManager.ContentArrival
			if not items: items = []

			# NB: use "number='extended'", not just "number=True", to also include standard/sequential/Trakt numbers that might be different between "new" (coming from Trakt) and "items" which are already smart-loaded.
			# Eg: One Piece - "new" items from Trakt (S02E63) vs already smart-loaded "items" (S02E02).
			number = 'extended' if Media.isSerie(media) else False

			# Add new items to the existing list.
			if new:
				# Remove any items not in new.
				# For Progress, since old watched episodes should be removed and replaced with the newly/next watched episode.

				if remove is True: # Progress
					helper = {} # Use a helper, since it is considerably faster if filterContains() is called multiple times in a loop.
					items = [i for i in items if self.mTools.filterContains(items = new, item = i, number = number, key = MetaManager.Smart, helper = helper)]

				# Copy over values that can be changed by the user to already smart-loaded items.
				# For instance, we have all movies in ProgressRewatch smart-loaded. Now we watch the top movie on the list.
				# After the update, the new watched time from the new item should be added to the current smart-loaded item.
				helper = {} # Use a helper, since it is considerably faster if filterContains() is called multiple times in a loop.
				for i in new:
					item = self.mTools.filterContains(items = items, item = i, number = number, key = MetaManager.Smart, helper = helper, result = True)
					if item:
						# Also accept None values from the new items.
						# A value could be available on the previous smart-load, but with the new smart-load, these values might be None.
						# Eg: progress cleared, item unwatched, rating removed, etc.

						item['playback'] = i.get('playback')

						for j in ['playcount', 'progress', 'userrating']: item[j] = i.get(j)

						times = i.get('time')
						if times:
							if not item.get('time'): item['time'] = {}

							for j in MetaTools.TimesTrakt:
								time = times.get(j)
								if time:
									item['time'][j] = time
								else: # Also overwrite with None. Eg: there was a paused time, but then the progress was cleared, and the new paused time is now None. Or if an item was unwatched.
									try: del item['time'][j]
									except: pass

						# For not-yet smart-loaded items, update the dates and ratings/votes, which might be higher for newer metadata.
						# Important for preliminary sorting of shows that are to be released today.
						# Otherwise new releases might end up on page 2+, because they have oudated metadata from an older cached request, with lower votes and slightly incorrect dates.
						# Once new arrival metadata comes in, use the newer dates/votes/rating.
						if arrival and not (item.get(MetaManager.Smart) or {}).get('time'):
							if times:
								for j in MetaTools.TimesRelease:
									time = times.get(j)
									if time and time > (item['time'].get(j) or 0): item['time'][j] = time

							votes = i.get('votes')
							if votes and votes > (item.get('votes') or 0):
								item['votes'] = votes
								item['rating'] = i.get('rating')

				# Only add new items that are not in the current list.
				# This makes sure that existing items with detailed metadata are not replaced with the same item without detailed metadata.
				new = [i for i in new if not self.mTools.filterContains(items = items, item = i, number = number, key = MetaManager.Smart, helper = helper)] # Reuse the helper.

				if new:
					# Do initial sorting.
					# Important for Rewatch menus, were we actually want the oldest (watched longest time ago) items first, although the history items coming in are sorted by most recently watched.
					if sort or order: new = self._process(media = media, items = new, sort = sort, order = order, filter = False, page = False, limit = False)

					# Add the new items that are not in the current list to the front of the list.
					# This makes sure that a newly watched episode is immediately moved to the front for detailed metadata retrieval on the next request.
					items = new + items

			if items:
				# Load existing metadata from the cache.
				# Over time more and more detailed metadata will be available for improved sorting.
				items, stats = self._metadataSmartLoad(media = media, items = items, content = content, stats = True)

				# Filter and sort using the more detailed metadata retrieved prior.
				if filter or sort or order: items = self._process(media = media, items = items, filter = filter, sort = sort, order = order, page = False, limit = False)

				# Filter out Wrestling titles, typically coming from IMDb.
				# Various Arrivals menu contain these, but more so niche menus (eg: TV Specials).
				# These cannot be filtered out any other way (eg: genre, etc).77
				if arrival: # Allow for the Progress menu.
					for item in items:
						title = item.get('title')
						if title and Regex.match(data = title, expression = '(?:^|[\s\-\:])(WWE|AEW|UFC|NXT|TNA|[eE]lite\s*[wW]restling|[wW]restle\s*[mM]ania)(?:$|[\s\-\:])', flags = Regex.FlagNone, cache = True):
							item[MetaManager.Smart]['removed'] = current

				if Tools.isInteger(remove):
					if remove <= 20000:
						items = items[:remove]
					else:
						# There are quite a lot of titles returned within the requested time period, that when detailed metadata is retrieved, their dates are older than the requested time.
						# Often this is just a few days, but sometimes the digital/physical release date can be 6+ months older than the date requested from the eg Trakt calendar.
						# If we simply remove titles older than 1 year, these titles will constantly be in the "new" list.
						# They then get smart-loaded, only to discover that their actual date from the detailed metadata is older than a year, so that they then gets removed here again.
						# This makes the same items stuck in "new" for a very long time, always getting smart-loaded and then removed, instead of spending the time on smart-loading other titles.
						# Instead of removing the titles older than 1 year, leave them in the list for another year (2 years total) so that they can be used to filter out old items from the "new" list.
						# These "removed" items only have IDs, but all other metadata gets removed to save disk space.

						delete = current - remove
						remove1 = current - remove
						remove2 = current - (4 * remove)
						for item in items:
							removed = item[MetaManager.Smart].get('removed')
							if removed:
								# Completely delete items that were marked as removed a long time ago.
								if removed < delete: item[MetaManager.Smart]['removed'] = True
							else:
								# Mark more recent items as "removed" and leave in the list for later deletion.
								time = self.mTools.time(type = MetaTools.TimeHome, metadata = item, estimate = False, fallback = False)
								if time and time < remove1: item[MetaManager.Smart]['removed'] = current
								else:
									# Remove very old premiered releases who recently got a digitial/physical release.
									time = self.mTools.time(type = MetaTools.TimeLaunch, metadata = item, estimate = False, fallback = False)
									if time and time < remove2: item[MetaManager.Smart]['removed'] = current

						# Delete items that were marked as "removed" a long time ago to reduce the list size and remove older items over time.
						items = [item for item in items if not item[MetaManager.Smart].get('removed') is True]

				# NB: Do not store the detailed metadata in cache.db, otherwise it will become too large.
				# We still need to retrieve the detailed metadata, since we filter by genre above, and the base metadata might not contain the genre.
				if not detail: items = self._metadataSmartReduce(media = media, items = items)

			if stats: message = 'Total: %d [%d New, %d Queued, %d Done] | Retrieved: %d [%d Cache, %d Foreground, %d Background]' % (stats['total']['all'], stats['total']['new'], stats['total']['queue'], stats['total']['done'], stats['count']['all'], stats['count']['cache'], stats['count']['foreground'], stats['count']['background'])
			else: message = 'Smart generation failed without any items'
			Logger.log('SMART REFRESH (%s %s | %dms): %s' % (media.capitalize(), (content or 'unknown').capitalize(), timer.elapsed(milliseconds = True), message))
		except: Logger.error()

		# Return this as a dictionary, not a list.
		# Otherwise if the user does not have any progress for a niche, it returns an empty list, and then the cache complaints:
		#	CACHE: Refreshing failed result data in the background (Empty List) - [Function : Movies._progressAssemble | Parameters: ...]
		# Add the time for _metadataSmartReload().
		return {
			'time' : Time.timestamp(),
			'items' : items,
		}

	def _metadataSmartLoad(self, media, items, content = None, stats = False):
		try:
			if items:
				time = Time.timestamp()

				serie = Media.isSerie(media)
				episode = Media.isEpisode(media) or (serie and content == MetaManager.ContentProgress)
				pack = content == MetaManager.ContentProgress
				arrival = content == MetaManager.ContentArrival

				itemsNew = [] # Newly added items never seen before. Most important.
				itemsRelease = [[], []] # Items recently premiered. More important.
				itemsQueue = [] # Items already in the list, but not smart-loaded before. Medium important.
				itemsDone = [] # Items already in the list, and smart-loaded before. Least important.
				itemsRenew = [[], [], []] # Items already smart-loaded, but that are recently released and should be reloaded to get more up-to-date ratings/votes.
				itemsRemoved = [] # Items removed because they are too old or other reasons.
				itemsLoad = []

				for item in items:
					self._metadataSmartUpdate(item = item)
					if content == MetaManager.ContentProgress and not 'external' in item[MetaManager.Smart]:
						self._metadataSmartUpdate(item = item, key = 'external', value = Tools.get(item, 'playback', 'source', 'external'))

					smart = item[MetaManager.Smart]
					if smart.get('removed'):
						itemsRemoved.append(item)
					else:
						smart = smart.get('time')

						if not smart:
							# The IMDb ID can change for a title, especially for new releases.
							# This can happen because of two reasons:
							#	1. A NEW request is made to an IMDb page for Arrivals, which contains the new IMDb ID. When detailed metadata is retrieved, a different IMDb ID is returned from Trakt/TMDb/TVDb which still point to the old IMDb ID, since they have not refreshed their own metadata and pulled in the new ID yet.
							#	2. A CACHED request for an IMDb page from Arrivals (days or weeks old) still returns the old IMDb, while everyone (IMDb/Trakt/TMDb/TVDb) have already updated to the new ID.
							# This makes an item coming into this function have an old IMDb ID and once the detailed metadata is retrieved, it now has a different IMDb ID and is therefore seen as a different title.
							# This makes an item get stuck in itemsNew/itemsRelease until the providers have updated their IDs.
							# In can get stuck even longer (weeks or months) if the providers do not update the IDs, or if some update it, but not others, causing an inconsistency between the IDs from Trakt/TMDb/TVDb.
							# In this case the item might only get out of the queue if it is outdated after a long time and then gets smart-removed.
							# Generally this should not be a huge issue, especially if detailed metadata is available from MetaCache and therefore only requires a local lookup.
							# However, if a number of these items get stuck, slots for foreground/background metadata retrieval during smart-loading are wasted, since every smart-refresh will load these items again, instead of using the slots for other queued/uncached items, slowing down how fast the smart Arrivals items are populated.
							# To avoid this slight "inefficiency", we add the original IMDb ID coming from one of the Arrivals lists, as a separate "imdx" ID.
							# Then during duplicate filtering, we use both those IDs and ensure the "new" item gets filtered out using the old and new IMDb IDs.
							#	Eg: And IMDb advanced search returns tt31186041. When looking up the Trakt/TMDb/TVDb IDs using this IMDb ID, and then retrieving the detailed metadata from all of them, the item ends up with tt33356012.
							#	This is the old IMDb ID, which has already changed on IMDb (and IMDb redirects tt33356012 to tt31186041), but the ID was not yet updated on Trakt/TMDb/TVDb. It might take a few days/weeks until the new ID might appear on providers.
							# This "imdx" IDs is used in MetaTools.filterDuplicate() and MetaTools.filterContains().
							imdb = item.get('imdb')
							if imdb and not item.get('imdx'):
								if not 'id' in item: item['id'] = {}
								item['id']['imdx'] = item['imdx'] = imdb

							if smart is None: item[MetaManager.Smart]['time'] = 0
							debut = self.mTools.time(metadata = item, type = MetaTools.TimeDebut, estimate = False, fallback = True) # Do not estimate, if there is only a TimeUnknown value, the show estimate date can be far off.
							if debut:
								age = time - debut
								if age < 259200: # Release in the past 3 days. More likley these are wanted in the Arrivals menu.
									itemsRelease[0].append(item)
									continue
								elif age < 1209600: # Release in the past 2 weeks. More likley these are wanted in the Arrivals menu.
									itemsRelease[1].append(item)
									continue

						if smart is None:
							item[MetaManager.Smart]['time'] = 0
							itemsNew.append(item)
						elif smart == 0:
							itemsQueue.append(item)
						else:
							debut = self.mTools.time(metadata = item, type = MetaTools.TimeDebut, estimate = False, fallback = True)
							if debut:
								age = time - debut
								if age < 604800: itemsRenew[0].append(item) # Released in the past week.
								elif age < 1209600: itemsRenew[1].append(item) # Released in the past 2 weeks.
								elif age < 1814400: itemsRenew[2].append(item) # Released in the past 3 weeks.

							itemsDone.append(item)

				# Add to the other items.
				itemsNew += itemsRelease[0]
				itemsQueue = itemsRelease[1] + itemsQueue

				countAll = 0
				countCache = 0
				countForeground = 0
				countBackground = 0
				totalAll = len(items)
				totalNew = len(itemsNew)
				totalQueue = len(itemsQueue)
				totalDone = len(itemsDone)

				# First try to retrieve whatever is in the cache from any other request that might have retrieved the detailed metadata.
				# This call should never cause any new metadata to be retrieved. Only existing metadata should be returned.
				# This should also not be a lot of metadata, since we only retrieve new items that we are not yet aware of have detailed metadata.
				# Those we do know have detailed metadata are not loaded, since they are in "itemsDone".
				itemsCache = itemsNew + itemsQueue
				if itemsCache or (arrival and itemsRenew):
					# Limit the number of items to retrieve from the cache. Retrieve the rest during the next execution.
					# Otherwise, if the user has loaded many menu pages since the last time this function was called, there might be too much new metadata to retrieve from disk, which might take too long.
					# Especially for the episode Progress menu, which will also retrieve large pack data from disk.
					# Add some randomness, otherwise we might always try to retrieve the first items only, while there are cached items later in the list.
					itemsCache = self._metadataSmartChunk(items = itemsCache, limit = 20 if episode else 50 if serie else 75)

					# Add some more randomized items for the Arrivals menu.
					# Otherwise the Arrivals with 5000+ titles takes way to long to smart-load, since most items retrieved above are not cached and will return very few items.
					# Plus the Arrivals menu is not refreshed that often. So the extra retrievals should not matter.
					if arrival:
						helper = {} # Use a helper, since it is considerably faster if filterContains() is called multiple times in a loop.
						itemsCache2 = []

						# Also reload titles that were released recently.
						# When a new show comes out, it is mostly smart-loaded on the first day from itemsNew.
						# However, on the first day there are very few votes. Even for popular shows, on the first 2 days there are often less than 20 votes.
						# Eg: American Primeval only had 14 votes and a low rating 2-3 days after release. Even after a week there were only 400 votes on Trakt.
						# Now that the title is smart-loaded, it might end up on page 2 or later, therefore not loading the detailed metadata, and MetaTools._sortGlobal() will only use the early votes (less than 20).
						# Now the title is stuck on page 2+ and might take very very long to get reloaded, since there are so many other titles in the queue. Even if it is finally reloaded, it is so old by then, that it ends up on a later page anyways.
						# Therefore, reload recent releases more frequently.
						itemsCache2 += Tools.listShuffle(itemsRenew[0][:20])
						itemsCache2 += Tools.listShuffle(itemsRenew[1][:15 + (20 - len(itemsCache2))])
						itemsCache2 += Tools.listShuffle(itemsRenew[2][:10 + (35 - len(itemsCache2))])

						itemsCache2 = Tools.listShuffle(itemsNew[:15]) + itemsCache2 + Tools.listShuffle(itemsNew[15:] + itemsQueue)
						itemsCache2 = [i for i in itemsCache2 if not self.mTools.filterContains(items = itemsCache, item = i, helper = helper)]
						itemsCache += self._metadataSmartChunk(items = itemsCache2, limit = 100) # If the limit is changed, also change itemsRenew above.

					itemsCache = self._metadataSmartRetrieve(items = itemsCache, pack = pack, quick = False) # Retrieve from cache and the rest not at all.
					if itemsCache:
						countCache += len(itemsCache)
						itemsLoad.extend(itemsCache)

						# Remove any items that now have detailed metadata.
						# NB: Do not filter by number here, since the Trakt number has been converted to a Standard number, and might mismatch here.
						# There should in any case not be mutiple episodes from the same show in the list.
						# Otherwise the converted episode number is always seen as a "new" episode and end up retrieving metadata for it again and again.
						# Eg: One Piece S02E63.
						helper = {} # Use a helper, since it is considerably faster if filterContains() is called multiple times in a loop.
						itemsNew = [i for i in itemsNew if not self.mTools.filterContains(items = itemsCache, item = i, helper = helper)]
						itemsQueue = [i for i in itemsQueue if not self.mTools.filterContains(items = itemsCache, item = i, helper = helper)]
						itemsRelease[0] = [i for i in itemsRelease[0] if not self.mTools.filterContains(items = itemsCache, item = i, helper = helper)]
						itemsRelease[1] = [i for i in itemsRelease[1] if not self.mTools.filterContains(items = itemsCache, item = i, helper = helper)]

				# Now retrieve detailed metadata for not yet smart-loaded items.
				# Only do this for as few items as possible, since more detailed metadata is retrieved outside and will be incorporated during the next smart loading.
				# Also retrieving a new episode in the Progress menu, will retrieve metadata for all episodes in the season, season metadata, show metadata, and pack metadata/generation, so even a few items can take long.
				# This should not hold up the smart list creation a long time.
				# Still retrieve at least the most recent new item, since that might be the just-watched episode and we want to correctly have the next episode from that show in the new progress list.
				count = 3
				itemsCache = None

				if self.mModeAccelerate:
					# If in accelerate mode, retrieve as little as possible.
					# This is during binge watching when starting the playback of the next episode.
					# Gaia can be laggy during the rating/binge/playback dialog, since heavy refreshing is gonig on in the background.
					# Do this only at the end of playback (action finished or stop).
					# A full refresh happens earlier during playback, when the history is updated.
					itemsCache = itemsNew[:1]
				else:
					if Math.randomProbability(0.3):
						# Sometimes an item gets "stuck" in the "new" list over and over again.
						# This can be because of some incorrect ID that makes the item get removed from the smart list, only to be added again when the smart list is refreshed.
						# These issues should all have been fixed now and this should not happen anymore.
						# But still do this, just in case some other yet-unknown problem also causes this.
						# Instead of always picking the first 3 items, every now-and-then pick random items from the first 10.
						try:
							itemsCache = Tools.listShuffle(itemsNew[:10])[:count]
							if len(itemsCache) < count: itemsCache += Tools.listShuffle(itemsQueue[:10])[:(count + 1) - len(itemsCache)] # Add more if there are no new items.
						except: Logger.error()
					if not itemsCache:
						itemsCache = itemsNew[:count]
						if len(itemsCache) < count: itemsCache += itemsQueue[:(count + 1) - len(itemsCache)] # Add more if there are no new items.

					# Items releases in the past few days should be urgently retrieved.
					# Otherwise shows released today might take too long until it shows up on the Arrivals menu, if there are too many items in the queue that are waiting for smart-loading.
					if arrival:
						# Not if it comes from MetaCache, that is, loaded with a one of the calls above.
						helper = {}
						itemsImportant = [i for i in itemsRelease[0] if not MetaCache.Attribute in i and self.mTools.filterContains(items = itemsCache, item = i, helper = helper)]
						itemsCache += itemsImportant[:10]

				if itemsCache:
					itemsCache = self._metadataSmartRetrieve(items = itemsCache, pack = pack, quick = None) # Retrieve from cache, foreground or background.
					if itemsCache:
						countForeground += len(itemsCache)
						itemsLoad.extend(itemsCache)

				# If there are few items retrieved from cache, also reload some already smart-loaded items in order to refresh their metadata if they are outdated.
				# Refresh those items that were smart-loaded the longest time ago.
				if len(itemsLoad) < (30 if arrival else 20) and itemsDone:
					itemsCache = Tools.listSort(itemsDone, key = lambda i : i.get(MetaManager.Smart).get('time'))

					# These will later on also be refreshed by _metadataSmartReload(), so no need to retrieve these in the background/foreground.
					#itemsCache = self._metadataSmartChunk(items = itemsCache, limit = 7 if episode else 15 if serie else 20)
					#itemsCache = self._metadataSmartRetrieve(items = itemsCache, pack = pack, quick = True) # Retrieve from cache and the rest in the background.
					#if itemsCache:
					#	countBackground += len(itemsCache)
					#	itemsLoad.extend(itemsCache)

					# Be more aggresive with Arrivals. Since new releases (1-2 weeks) have very few votes, although the detailed metadata might be updated with the new higher vote count.
					# The old lower vote count can make new releases have a lower order in sortGlobal().
					itemsCache = self._metadataSmartChunk(items = itemsCache, limit = (10 if episode else 40) if arrival else (7 if episode else 15 if serie else 20))
					itemsCache = self._metadataSmartRetrieve(items = itemsCache, pack = pack, quick = False) # Retrieve from cache and the rest not at all.
					if itemsCache:
						countCache += len(itemsCache)
						itemsLoad.extend(itemsCache)

				countAll = len(itemsLoad)

				# NB: The items in "itemsLoad" might not be the original dictionary from "items" that was passed into self.metadata().
				# self.metadataEpisode() returns a new dictionary, since all episodes of a season are retrieved in one go from MetaCache.
				# So do not just update the values in "itemsLoad", since it will not update the original "items" that is returned by this function.
				# Copy over the values from "itemsLoad" into the original "items".
				helper = {} # Use a helper, since it is considerably faster if filterContains() is called multiple times in a loop.
				for item in itemsLoad:
					# Do not use the number, since it might have changed.
					# Plus smart lists should not contain mutiple episodes from the same show.
					found = self.mTools.filterContains(items = items, item = item, helper = helper, result = True)
					if found:
						# Add the timestamp to indicate this item was smart-loaded.
						# If the detailed metadata comes from the external metadata addon, do not update the time, since it might be outdated metadata.
						# Generally this should not be an issue, but if the user installs Gaia for the first time a few weeks/months after the external addon was updated, it will start pulling in outdated metadata for the Arrivals smart menu from the addon,
						# This can contain incorrect release dates, and low votes/ratings, which affects global sorting.
						# Still allow the external metadata as "fallback", improving filtering/sorting when the smart list is initially created.
						# This can also greatly help with importing a large Trakt history in the Progress menu, which will have a lot of older titles and this allows for detailed metadata right from the start, and improve filtering/sorting.
						# However, since we leave the smart time at 0, on the next smart-refresh it will see this as a new/queued item and retrieve it again. This time it would have the new metadata from the local cache.
						external = (item.get(MetaCache.Attribute) or {}).get(MetaCache.AttributeStatus) == MetaCache.StatusExternal
						self._metadataSmartUpdate(item = item, key = 'time', value = 0 if external else time)

						if content == MetaManager.ContentProgress:
							if Media.isEpisode(item.get('media')):
								# Episodes coming from the Trakt history still have the Trakt numbers.
								# It is too expensive to convert all these numbers in Playback.
								# Do here, so that we do not have to do it later in metadataEpisode() for already smart-loaded items, every time the Progress menu is loaded.
								if found[MetaManager.Smart]['external']: # This is set on "found", not the "item".
									try: number = item['number'][MetaPack.NumberStandard]
									except: number = None
									if number:
										# Used to determine newly added episode of if the episode is already in the list.
										# Since the Trakt number gets replaced below.
										item[MetaManager.Smart]['season'] = item['season']
										item[MetaManager.Smart]['episode'] = item['episode']

										item['season'] = number[MetaPack.PartSeason]
										item['episode'] = number[MetaPack.PartEpisode]
										found[MetaManager.Smart]['external'] = None # Do not lookup again in metadataEpisode().

								# Determine the next episode.
								# Any show that does not have a next episode (eg: all episodes watched), should be moved further back to the list.
								# Otherwise in content() there might be less items on the page than the limit, because these are only filtered out later.
								# Only do this if the pack is available.
								# Used by MetaTools._sortLocal()
								pack = item.get('pack')
								if pack:
									pack = MetaPack.instance(pack = pack)
									item[MetaManager.Smart]['pack'] = pack.reduceSmart()

									nextItem = {'imdb' : item.get('imdb'), 'tmdb' : item.get('tmdb'), 'tvdb' : item.get('tvdb'), 'trakt' : item.get('trakt'), 'season' : item.get('season'), 'episode' : item.get('episode')}
									nextNumber = self._metadataEpisodeIncrement(item = nextItem, number = MetaPack.ProviderTrakt if found[MetaManager.Smart]['external'] else MetaPack.NumberStandard, threaded = False)

									if nextItem.get('invalid') or nextItem.get('episode') is None:
										# Set to False, to specifically indicate that there is no new episode.
										item[MetaManager.Smart]['next'] = False
									else:
										nextSeason = nextItem.get('season')
										nextEpisode = nextItem.get('episode')

										# Add the next episode's time to the smart data.
										# This is used for preliminary sorting PRIOR to the paging.
										# Otherwise future episodes cannot be filtered out BEFORE the paging is done. Meaning future episode can only be sorted to the bottom of the 1st page, instead of moving it to later pages.
										nextTime = pack.time(season = nextSeason, episode = nextEpisode, number = nextNumber)

										item[MetaManager.Smart]['next'] = {'season' : nextSeason, 'episode' : nextEpisode, 'number' : nextNumber, 'time' : nextTime}
						elif arrival:
							# NB: Add the season number to the smart dict.
							# Otherwise for Show Arrivals, the show object + season number is part of the "new" list that comes in.
							# Once the show object gets smart-loaded, the season number in the root dict gets removed.
							# This then causes the smart list to grow very large over time, since every show object is added mutiple times to the smart list, once with a season number and once without.
							# Then when we call MetaTools.filterContains(), these objects are seen as different ones, since they have different season numbers.
							if Media.isSerie(item.get('media')): item[MetaManager.Smart]['season'] = item.get('season')

						found.update(item)
					else:
						# This should never happen. If it does, something is wrong.
						Logger.log('SMART REFRESH FAILURE: %s [%s]' % (str(item.get('tvshowtitle') or item.get('title')), str(item.get('imdb') or item.get('trakt'))))

			# Recalculate values that can change.
			# Do this even if the item was not loaded above, since these values can change in the history without it being smart-loaded again.
			# Similar to the new-loop in _metadataSmart(), but these values migth require additional attributes calculated in this function.
			if content == MetaManager.ContentProgress:
				# The "play" attribute indicates the total number of plays plus the progress.
				# Eg: 2.5 means played fully twice, and currently rewatching with a progress of 50%.
				# For shows, it means the percetange of the show fully watched.
				# Eg: 2.5 means all episodes were played twice, and currently rewatching with half the episodes watched.
				# This might not be a perfect indicator, since the user might have watched a few episodes mutiple times, and others fewer or no times.
				# But for normal watches, this should be a pretty good indicator.
				for item in items:
					play = 0
					if serie:
						pack = item[MetaManager.Smart].get('pack')
						if pack:
							countTotal = Tools.get(pack, 'count', MetaPack.NumberOfficial, MetaPack.ValueEpisode)
							if countTotal:
								countWatched = Tools.get(item, 'playback', 'counts', 'main', 'total')
								progressWatched = Tools.get(item, 'playback', 'progress') # Not really needed, since this will make almost no difference.
								play = ((countWatched or 0) + (progressWatched or 0)) / float(countTotal)
					else:
						play = (Tools.get(item, 'playback', 'count') or 0) + (Tools.get(item, 'playback', 'progress') or 0)
					item[MetaManager.Smart]['play'] = Math.round(play, places = 6) if play else play

			# Important to filter duplicates for Arrivals.
			# There can be duplicate items, some with one of the IMDb/TMDb/Trakt IDs only, and others with mutiple IDs. Eg: some items come from IMDb sources, otherwise from Trakt or TMDb.
			# Only after detailed metadata retrieval are all the IDs available and can we filter out these duplicates.
			# This means the Arrivals list can get slightly smaller over time.
			# Also check the number, since the same show can have 2 seasons released within the same year. Keep both, otherwise the one is always in "new".
			# The duplicate seasons get filtered out in _arrivalProcess().
			items = self.mTools.filterDuplicate(items = items, id = True, title = False, number = True)

			statistics = {
				'total' : {'all' : totalAll, 'new' : totalNew, 'queue' : totalQueue, 'done' : totalDone},
				'count' : {'all' : countAll, 'cache' : countCache, 'foreground' : countForeground, 'background' : countBackground},
			}
			self._metadataSmartStats(media = media, content = content, stats = statistics.get('total'))

			if stats: return items, statistics
			else: return items
		except:
			Logger.error()
			if stats: return items, None
			else: return items


	# Always retrieve the pack data, since it is needed to create various smart attributes.
	# Do not aggregate the show/season data, since it is not needed here, and only slows down things and requires additional disk I/O.
	def _metadataSmartRetrieve(self, items, quick = None, pack = True, aggregate = False):
		# Clean: keep the MetaCache data to determine if it comes from the external cache.
		return self.metadata(items = items, quick = quick, pack = pack, aggregate = aggregate, clean = 'cache')

	def _metadataSmartUpdate(self, item, key = None, value = None):
		if not MetaManager.Smart in item: item[MetaManager.Smart] = {}
		if not key is None: item[MetaManager.Smart][key] = value
		return item

	def _metadataSmartStats(self, media = None, content = None, stats = None, notification = None):
		try:
			id = 'internal.smart'
			data = Settings.getData(id)

			if Media.isSerie(media): media = Media.Show
			if not data: data = {'time' : {'update' : 0, 'notification' : 0}}

			if stats or notification:
				if stats:
					data['time']['update'] = Time.timestamp()
					if not content in data: data[content] = {}
					data[content][media] = stats
				if notification:
					data['time']['notification'] = Time.timestamp()
				Settings.setData(id, data)

			if content:
				data = data.get(content)
				if media: data = data.get(media)
			return data
		except: Logger.error()
		return None

	def _metadataSmartChunk(self, items, limit, performance = True, accelerate = True):
		# Only low-end devices, background refreshes/reloads can take very long, making menus very slow.
		if performance:
			if self.mPerformanceMedium: limit *= 0.9
			elif self.mPerformanceSlow: limit *= 0.8

		if accelerate and self.mModeAccelerate: limit *= 0.9

		limit = max(1, int(limit))
		limit1 = int(limit * 0.6)
		limit2 = limit - limit1
		return items[:limit1] + Tools.listShuffle(items[limit1:])[:limit2]

	def _metadataSmartReduce(self, media, items, full = True):
		removed = ['media', 'id', 'imdb', 'imdx', 'tmdb', 'tvdb', 'trakt']

		# Include any attributes that might be used for sorting or filtering, BEFORE the detailed metadata is retrieved.
		values = [
			'media', 'niche',
			'id', 'imdb', 'imdx', 'tmdb', 'tvdb', 'trakt',
			'title', 'originaltitle',
			'year', 'premiered', 'time',
			'rating', 'votes', # Do not add "voting", since it increases the size, and only the aggregated rating/votes are needed.
			'country', 'language', 'genre', 'mpaa',
		]

		if full:
			removed.append(MetaManager.Smart)
			values.extend([
				MetaManager.Smart,
				'progress', 'playcount', 'userrating',
				#'playback', # Do not add "playback", since it increases the size, but is not needed, since all neccessary values are necessary into MetaManager.Smart.
			])

		if Media.isSerie(media):
			values.extend(['tvshowtitle', 'season', 'episode', 'number', 'aired'])
			removed.extend(['season', 'episode'])

		return [{i : item.get(i) for i in (removed if (item.get(MetaManager.Smart) or {}).get('removed') else values)} for item in items]

	def _metadataSmartAggregate(self, media, items, base):
		try:
			if base:
				if not Tools.isArray(base): base = [base]
				if any(MetaManager.Smart in i for i in base):
					smarts = {'imdb' : {}, 'tmdb' : {}, 'tvdb' : {}, 'trakt' : {}}
					for item in base:
						smart = item.get(MetaManager.Smart)
						if smart:
							for i in smarts.keys():
								id = item.get(i)
								if id: smarts[i][id] = smart

					for item in items:
						for i in smarts.keys():
							id = item.get(i)
							if id:
								smart = smarts[i].get(id)
								if smart:
									item[MetaManager.Smart] = smart
									break

		except: Logger.error()
		return items

	def _metadataSmartReload(self, media, items, time, content = None, cache = None, delay = True, force = False):
		try:
			if items:
				# Reload in one of these cases:
				#	1. If forced.
				#	2. If coming from cache and the cache call was more than a minute ago.
				#	3. If coming from cache and the overall usage is relativley low.
				# Do not reload if _metadataSmartLoad() was called immediately beforehand (either cache is None, or time is a few seconds ago).
				if force or (cache and ((Time.timestamp() - time) > 60 or MetaProvider.usageGlobal() < 0.3)):
					parameters = {'media' : media, 'items' : items, 'content' : content, 'delay' : delay}

					# NB: Do not execute in a thread if we are refreshing from reload().
					# Wait until the smart-reload is done before moving on to refreshing the next media/menu.
					if self.mModeSynchronous or self.reloadingMedia():
						if parameters['delay'] is True: parameters['delay'] = 0.05
						self._metadataSmartRefresh(**parameters)
					else:
						Pool.thread(target = self._metadataSmartRefresh, kwargs = parameters, start = True)
		except: Logger.error()

	def _metadataSmartRefresh(self, media, items, content = None, delay = True):
		try:
			if delay: Time.sleep(0.01) # Allow other code to execute.

			# Do this check only here, so that it is done in the thread and does not hold up the process.
			if self._lockSmart(media = media, content = content):
				# Allow the main code in content() to execute before we do this.
				# Prevents this code and possibly foreground metadata retrieval from delaying the menu.
				# Wait a long time, since content() can retrieve a lot of metadata when few items are cached, which can take long.
				# The wait will be less if the script execution finishes more quickly. So this is only the "maximum wait".
				# Wait at the start, so we can later get more accurate MetaTrakt/MetaImdb usage.
				Pool.wait(delay = 30.0 if delay is True else delay)
				timer = Time(start = True)

				serie = Media.isSerie(media)
				episode = Media.isEpisode(media) or (serie and content == MetaManager.ContentProgress)
				pack = content == MetaManager.ContentProgress
				arrival = content == MetaManager.ContentArrival

				# Only retrieve a few items, since this function is called quite often:
				#	1. When Gaia is launched.
				#	2. When the smart menu is opened by the user.
				#	3. When a title was watched or the Trakt history changes in some way.
				# For a normal daily use, this can easily be 5+ reloads per day.
				# Especially for episode progress menus, if a new episode is requested, metadata for all episodes in that the season, all season metadata, show metadata, and pack metadata/generation is needed, which can take very long.
				# So retrieve as minimal metadata as possible in one go. Not too little, otherwise it will take forever to fully load a large Trakt history of a few thousand items.
				# Add some randomness to avoid issues when the first items can never be retrieved.
				# If all items were smart-loaded, it will start refreshing older items in case their metadata changes in the future.
				limit = 5 if episode else 8 if serie else 10 # Just 5 items for episodes can take 60+ secs.

				# After some time most of these items are cached and will not retrieve/refresh the metadata.
				# Increase the limit if a certain percentage of items are already smart-loaded.
				countDone = 0
				countQueue = 0
				for item in items:
					if item.get(MetaManager.Smart).get('time'): countDone += 1
					else: countQueue += 1
				done = (countDone / countQueue) if (countDone and countQueue) else 2.0 if countDone else 0.0
				more = arrival and not episode and self.mPerformanceFast
				if done >= 2.0: limit *= 2.5 if more else 2.0
				elif done >= 1.5: limit *= 2.0 if more else 1.5
				elif done >= 1.0: limit *= 1.5 if more else 1.3
				elif done >= 0.75: limit *= 1.7 if more else 1.2
				elif done >= 0.5: limit *= 1.2 if more else 1.1

				# Reduce a bit for slower devices.
				# More reduction is done in _metadataSmartChunk().
				if done >= 0.5 and not self.mPerformanceFast: limit *= 0.85

				usage = MetaProvider.usageGlobal()
				if usage > 0.75: limit = 0
				elif usage > 0.25: limit = max(1, int(limit * (1.0 - usage)))

				limit = int(max(1, min(50, limit)))
				limit1 = max(1, int(limit / 2.0))
				limit2 = max(1, int(limit / 5.0))
				limit3 = max(1, int(limit / 10.0))

				# Move the new and queued items to the front.
				lookup = [[], [[], [], []], []]
				time = Time.timestamp()
				items = Tools.listShuffle(items)

				for item in items:
					smarted = item.get(MetaManager.Smart).get('time')

					# Firstly, add new releases that were not smart-loaded yet.
					if smarted is None:
						lookup[0].append(item)
						continue

					# Secondly, add recent releases that were already smart-loaded.
					# Check _metadataSmartLoad() with the "American Primeval" comment.
					# More recent releases should be reloaded more frequently, since the rating/votes are very low the first few days after release.
					# This causes important recent releases to be only listed on page 2+.
					debut = self.mTools.time(metadata = item, type = MetaTools.TimeDebut, estimate = False, fallback = True)
					if debut:
						age = time - debut
						if age < 604800:
							lookup[1][0].append(item)
							continue
						elif age < 1209600:
							lookup[1][1].append(item)
							continue
						elif age < 1814400:
							lookup[1][2].append(item)
							continue

					# Thirdly, add older releases that were already smart-loaded.
					lookup[2].append(item)

				# Titles not smart-loaded yet.
				# Prefer those that were recently released.
				lookup[0] = Tools.listSort(lookup[0], key = lambda i : time - (self.mTools.time(metadata = item, type = MetaTools.TimeDebut, estimate = False, fallback = True) or 0))
				items1 = lookup[0][:limit1]
				items2 = lookup[0][limit1:]

				# Only use 10 items released in the past week, 10 items released in the past 2 weeks, and 5 items released in the past 3 weeks.
				# Only 50 items are retrieved, and we do not always want to use recent releases only. So cap them at 25.
				# Add the rest to lookup[2].
				items3 = []
				items3 += lookup[1][0][:limit2]
				lookup[2] += lookup[1][0][limit2:]
				extra = limit2 + (limit2 - len(items3))
				items3 += lookup[1][1][:extra]
				lookup[2] += lookup[1][1][extra:]
				extra = limit3 + ((2 * limit2) - len(items3))
				items3 += lookup[1][2][:extra]
				lookup[2] += lookup[1][2][extra:]

				items = []
				items += items1 # Retrieve up to 25 titles that were not smart-loaded yet.
				items += items3 # Re-retrieve up to 25 titles released in the past 3 weeks.
				items += items2 # Retrieve the remainder of the titles that were not smart-loaded yet.
				items += Tools.listSort(lookup[2], key = lambda i : i.get(MetaManager.Smart).get('time')) # Fill the remainder with already smart-loaded titles, starting with those smart-loaded the longest time ago.

				count = 0
				total = len(items)
				if limit:
					items = self._metadataSmartChunk(items = items, limit = limit)
					items = self._metadataSmartRetrieve(items = items, quick = None, pack = pack, aggregate = True) # Retrieve from cache, foreground or background. Aggregate to also refresh the show metadata if it is outdated.
					if items: count = len(items) # Some might be retrieved from the cache. So the actual number of foreground/background retrievals might be lower.

				Logger.log('SMART RELOAD (%s %s | %dms): Total: %d | Retrieved: %d' % (media.capitalize(), (content or 'unknown').capitalize(), timer.elapsed(milliseconds = True), total, count))
		except: Logger.error()

	##############################################################################
	# METADATA - MOVIE
	##############################################################################

	def metadataMovie(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, items = None, filter = None, clean = True, quick = None, refresh = False, cache = False, threaded = None):
		try:
			media = Media.Movie

			pickSingle = False
			pickMultiple = False

			if items:
				if Tools.isArray(items):
					pickMultiple = True
				else:
					pickSingle = True
					items = [items]
			elif imdb or tmdb or tvdb or trakt:
				pickSingle = True
				items = [{'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt}]
			elif title:
				pickSingle = True
				items = self._metadataIdLookup(media = media, title = title, year = year, list = True)

			if items:
				items = self._metadataCache(media = media, items = items, function = self._metadataMovieUpdate, quick = quick, refresh = refresh, cache = cache, threaded = threaded)
				if items:
					items = self._metadataFilter(media = media, items = items, filter = filter)
					items = self._metadataAggregate(media = media, items = items)

					if pickSingle: items = items[0] if items else None

					items = self._metadataClean(media = media, items = items, clean = clean)
					return items
		except: Logger.error()
		return None

	def _metadataMovieUpdate(self, item, result = None, lock = None, locks = None, semaphore = None, cache = False, threaded = None, mode = None, part = True):
		try:
			# If many requests are made at the same time, there can be various network errors:
			#	Network Error [Error Type: Connection | Link: https://webservice.fanart.tv/v3/movies/...]: Failed to establish a new connection: [Errno 111] Connection refused
			#	Network Error [Error Type: Connection | Link: https://api.themoviedb.org/3/movie/...?api_key=...&language=en]: Connection aborted
			#	Network Error [Error Type: Connection | Link: https://api.trakt.tv/movies/.../people?extended=full]: Read timed out.
			#	Network Error [Error Type: Timeout | Link: https://webservice.fanart.tv/v3/movies/...]: Read timed out. (read timeout=45
			#	Network Error [Error Type: Connection | Link: https://api.trakt.tv/movies/.../people?extended=full]: Connection aborted
			# This applies to all providers (Trakt, TMDb, Fanart) and errors are very sporadic.
			# Although some servers might implement rate limits, it is highly unlikely that this is the cause.
			# The API would return a JSON or HTTP error if limits were exceeded. If anything, this might be caused directly by the webservers that drop connections if too many simultaneous connection are established in a short time.
			# However, this is also unlikley, because if only a single provider is used (eg just make Fanart requests and disable the rest), the errors are mostly gone.
			# It is highley likley that this is caused by a slow local internet/VPN connection.
			# Most of the errors are from Fanart, and only a few from Tratk/TMDb. Since Fanart data is larger, this might explain the errors (eg timeout) if the local internet connection is slow.
			# If these network errors occur (excluding any HTTP errors, like 404 meaning the specific movie cannot be found on the API), the following is done:
			#	1. Retrieve as much info as possible from the APIs and populate the ListItem with these values to display to the user.
			#	2. Do NOT write the data to the metadata cache, since it is incomplete. If the menu is reloaded, this function will be called again and another attempt will be made to get the metadata.
			#	3. All subrequests are cached. If eg Fanart fails, but Trakt/TMDb was successful, the menu is reloaded and this function called again, only the failed requests are redone, the other ones use the previously cached data.
			#	4. If a request fails due to network issues (excluding HTTP errors), that request is purged from the cache, so that on the next try the old/invalid cached results are not reused.

			media = Media.Movie

			ids = {'imdb' : [], 'tmdb' : [], 'tvdb' : [], 'trakt' : [], 'slug' : [], 'tvmaze' : [], 'tvrage' : []}

			imdb = item.get('imdb')
			tmdb = item.get('tmdb')
			tvdb = item.get('tvdb')
			trakt = item.get('trakt')
			slug = item.get('slug')

			title = item.get('title')
			year = item.get('year')

			# By default we do not cache requests to disc, since it takes longer and requires more storage space.
			# If the same movie appears multiple times in the list (some Trakt lists, eg watched list where a movie was watched twice), sub-requests will also have to be executed multiple times, since they are not disc-cached.
			# Cache in memory and use locks to block subsequent calls with the same ID/title until the first request is done and then use those results without executing all the code again.
			id = Memory.id(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
			if not locks is None:
				if not id in locks:
					lock.acquire()
					if not id in locks: locks[id] = Lock()
					lock.release()
				locks[id].acquire()
				data = Memory.get(id = id, uncached = True, local = True, kodi = False)
				if Memory.cached(data):
					if data: item.update(Tools.copy(data)) # Copy in case the memory is used mutiple times. Can be None if not found.
					return None

			# Previous incomplete metadata.
			partDone = True
			partOld = {}
			partNew = {MetaCache.AttributeFail : 0}
			if part:
				try:
					partCache = item.get(MetaCache.Attribute)
					if partCache and partCache.get(MetaCache.AttributeStatus) == MetaCache.StatusIncomplete:
						partOld = partCache.get(MetaCache.AttributePart) or {}
						partNew[MetaCache.AttributeFail] = partOld.get(MetaCache.AttributeFail, 0)
				except: Logger.error()

			if not imdb or not tmdb:
				values = partOld.get('id')
				if not values or not values.get('complete'): values = self._metadataMovieId(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
				partNew['id'] = values
				if values:
					if not values.get('complete'): partDone = False
					values = values.get('data')
					if values:
						value = self._metadataIdAdd(type = 'imdb', metadata = values, ids = ids)
						if not imdb: imdb = value
						value = self._metadataIdAdd(type = 'tmdb', metadata = values, ids = ids)
						if not tmdb: tmdb = value
						value = self._metadataIdAdd(type = 'tvdb', metadata = values, ids = ids)
						if not tvdb: tvdb = value
						value = self._metadataIdAdd(type = 'trakt', metadata = values, ids = ids)
						if not trakt: trakt = value
						value = self._metadataIdAdd(type = 'slug', metadata = values, ids = ids)
						if not slug: slug = value
			if not imdb and not tmdb and not tvdb and not trakt: return False

			cache = cache if cache else None
			developer = self._metadataDeveloper(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, item = item)
			if developer: Logger.log('MOVIE METADATA RETRIEVAL [%s]: %s' % (mode.upper() if mode else 'UNKNOWN', developer))

			# DetailEssential: 2-3 requests [Trakt: 1-2 (summary, optional translations), TMDb: 1 (summary), IMDb: 0, Fanart: 0]
			# DetailStandard: 6-7 requests [Trakt: 3-4 (summary, studios, releases, optional translations), TMDb: 2 (summary, images), IMDb: 0, Fanart: 1 (summary)]
			# DetailExtended: 8-9 requests [Trakt: 4-5 (summary, people, studios, releases, optional translations), TMDb: 2 (summary, images), IMDb: 1 (summary), Fanart: 1 (summary)]
			requests = []
			if self.mLevel >= 0:
				requests.append({'id' : 'trakt', 'function' : self._metadataMovieTrakt, 'parameters' : {'trakt' : trakt, 'imdb' : imdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				requests.append({'id' : 'tmdb', 'function' : self._metadataMovieTmdb, 'parameters' : {'tmdb' : tmdb, 'imdb' : imdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				requests.append({'id' : 'imdb', 'function' : self._metadataMovieImdb, 'parameters' : {'imdb' : imdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				if self.mLevel >= 1:
					requests.append({'id' : 'fanart', 'function' : self._metadataMovieFanart, 'parameters' : {'imdb' : imdb, 'tmdb' : tmdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})

			partDatas = {}
			if partOld:
				partRequests = []
				for i in requests:
					partData = partOld.get(i['id'])
					if partData and partData.get('complete'): partDatas[i['id']] = partData
					else: partRequests.append(i)
				requests = partRequests
				partDatas = Tools.copy(partDatas) # Copy inner dicts that can be carried over with the update() below.

			datas = self._metadataRetrieve(requests = requests, threaded = threaded)
			datas.update(partDatas)

			data = {}
			niches = []
			genres = []
			studios = []
			networks = []
			languages = []
			countries = []
			status = []
			times = []
			durations = []
			mpaas = []
			casts = []
			directors = []
			writers = []
			creators = []
			images = {}
			voting = {
				'rating' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
				'votes' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
			}

			providers = ['metacritic', 'imdb', 'fanart', 'tmdb', 'trakt'] # Keep a specific order. Later values replace newer values.
			providersImage = providers[::-1] # Preferred providers must be placed first. Otherwise it might pick unwanted images first (eg IMDb).

			for i in providers:
				if i in datas:
					values = datas[i]
					if values:
						if not Tools.isArray(values): values = [values]
						for value in values:
							if not value['complete']:
								partDone = False
								if developer: Logger.log('MOVIE METADATA INCOMPLETE [%s]: %s' % (i.upper(), developer))

							provider = value['provider']

							# Use "provider", not "i", since IMDb also has Metacritic data.
							# NB: Important to copy, since the dict is edited below.
							# Otherwise we edit the dict before it gets (possibly) written as partial data to MetaCache.
							# Eg: TVDb fails or has no data yet (new release). The TMDb images get deleted below, and the TMDb is later added as partial data to MetaCache. The next time the partial metadata is refreshed, the TMDb data is used, but now does not have images anymore, causing the poster to be missing in the menus.
							# This mostly happens with new releases. Either TMDb/TVDb/Trakt has not listed it yet, or Trakt has the wrong TMDb/TVDb ID.
							partNew[provider] = Tools.copy(value)

							value = value['data']
							if value:
								if MetaImage.Attribute in value:
									images = Tools.update(images, value[MetaImage.Attribute], none = False, lists = True, unique = False)
									del value[MetaImage.Attribute]

								self._metadataIdAdd(metadata = value, ids = ids)

								if 'niche' in value: niches.append(value['niche'])
								if 'genre' in value: genres.append(value['genre'])
								if 'studio' in value: studios.append(value['studio'])
								if 'network' in value: networks.append(value['network'])
								if 'language' in value: languages.append(value['language'])
								if 'country' in value: countries.append(value['country'])
								if 'status' in value: status.append(value['status'])
								if 'time' in value: times.append(value['time'])
								if 'duration' in value: durations.append(value['duration'])
								if 'mpaa' in value: mpaas.append(value['mpaa'])

								if 'cast' in value: casts.append(value['cast'])
								if 'director' in value: directors.append(value['director'])
								if 'writer' in value: writers.append(value['writer'])
								if 'creator' in value: creators.append(value['creator'])

								if 'rating' in value: voting['rating'][provider] = value['rating']
								if 'votes' in value: voting['votes'][provider] = value['votes']
								if 'userrating' in value: voting['user'][provider] = value['userrating']

								data = Tools.update(data, value, none = False, lists = False, unique = False)

			genres = self.mTools.mergeGenre(genres)
			if genres: data['genre'] = genres

			languages = self.mTools.mergeLanguage(languages)
			if languages: data['language'] = languages

			countries = self.mTools.mergeCountry(countries)
			if countries: data['country'] = countries

			networks = self.mTools.mergeNetwork(networks, country = countries)
			if networks: data['network'] = networks

			studios = self.mTools.mergeStudio(studios, other = networks, country = countries)
			if studios: data['studio'] = studios

			status = self.mTools.mergeStatus(status)
			if status: data['status'] = status

			times = self.mTools.mergeTime(times, metadata = data)
			if times:
				data['time'] = times

				# The "premiered" date returned by Trakt/TMDb/IMDb can vary greatly.
				# In most cases it is not actually the premiere date, but rather the limited/theatrical date or the digital date if the previous two are unavailable.
				# It also makes more sense to use the launch date here, since normal people cannot attend premieres, and the premiere can be weeks/months before the theatrical date.
				# Check MetaTools.timeGenerate() for more details.
				# https://trakt.tv/movies/bank-of-dave-2023
				launch = times.get(MetaTools.TimeLaunch)
				if launch: data['premiered'] = Time.format(launch, format = Time.FormatDate)

			durations = self.mTools.mergeDuration(durations)
			if durations: data['duration'] = durations

			mpaas = self.mTools.mergeCertificate(mpaas, media = media)
			if mpaas: data['mpaa'] = mpaas

			cast = self.mTools.mergeCast(casts)
			if cast: data['cast'] = cast

			director = self.mTools.mergeCrew(directors)
			if director: data['director'] = director

			writer = self.mTools.mergeCrew(writers)
			if writer: data['writer'] = writer

			creator = self.mTools.mergeCrew(creators)
			if creator: data['creator'] = creator

			data['media'] = media

			niche = self.mTools.mergeNiche(niches)
			niche = self.mTools.niche(niche = niche, metadata = data)
			if niche: data['niche'] = niche

			data['voting'] = voting

			data = {k : v for k, v in data.items() if not v is None}

			# Always replace the IDs of refreshed metadata and do not use the IDs saved to MetaCache previously.
			# Since the old metadata can contain old/outdated/wrong IDs which were fixed in the newly retrieved/refreshed metadata.
			# Check for a detailed explanation under _metadataId().
			self._metadataIdUpdate(metadata = data, ids = ids)

			if images:
				MetaImage.update(media = MetaImage.MediaMovie, images = images, data = data, sort = providersImage)
			else:
				# Sometimes the images are not available, especially for new/future releases.
				# This looks ugly in the menus. Mark as incomplete to re-retrieve sooner.
				partDone = False
				try: partNew['tmdb']['complete'] = False
				except: pass
				try: partNew['fanart']['complete'] = False
				except: pass
				if developer: Logger.log('MOVIE IMAGES INCOMPLETE: %s' % developer)

			# Do this before here already.
			# Otherwise a bunch of regular expressions are called every time the menu is loaded.
			self.mTools.cleanPlot(metadata = data)

			# Calculate the rating here already, so that we have a default rating/votes if this metadata dictionary is passed around without being cleaned first.
			# More info under meta -> tools.py -> cleanVoting().
			self.mTools.cleanVoting(metadata = data, round = True) # Round to reduce storage space of average ratings with many decimal places.

			Memory.set(id = id, value = data, local = True, kodi = False)
			if item and data: item.update(Tools.copy(data)) # Can be None if the ID was not found. Copy in case the outer item is edited before we write the data to MetaCache.

			if partDone:
				try: item[MetaCache.Attribute][MetaCache.AttributePart] = None
				except: pass
			else:
				partNew[MetaCache.AttributeFail] += 1
				data[MetaCache.Attribute] = {MetaCache.AttributePart : partNew}

			self._batchLoad(media = media, imdb = data.get('imdb'), tmdb = data.get('tmdb'), tvdb = data.get('tvdb'), trakt = data.get('trakt'))
			result.append(data)
		except:
			Logger.error()
		finally:
			if locks and id: locks[id].release()
			if semaphore: semaphore.release()
			self.mTools.busyFinish(media = media, item = item)

	def _metadataMovieId(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None):
		result = self.mTools.idMovie(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
		if result: return {'complete' : True, 'data' : {'id' : result}}
		else: return {'complete' : False, 'data' : result}

	def _metadataMovieTrakt(self, trakt = None, imdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			# Do not use the cached summarized data. Only if it comes from IMDb.
			try: origin = bool(item['temp']['trakt'])
			except: origin = False

			if detail == MetaTools.DetailEssential and item and origin: # Comes from a Trakt list with basic metadata.
				if MetaCache.Attribute in item:
					result = {}
				else:
					result = Tools.copy(item)
					try: del result['temp']
					except: pass
				result = self._metadataTemporize(item = item, result = result, provider = 'trakt')
			else: # Comes from another list, or forcefully retrieve detailed metadata.
				id = trakt or imdb
				if id:
					# Trakt has an API limit of 1000 requests per 5 minutes.
					# Retrieving all the additional metadata will very quickly consume the limit if a few pages are loaded.
					# Only retrieve the extended metadata if enough requests are still avilable for the past 5 minutes.
					instance = MetaTrakt.instance()
					usagesAuthenticated = instance.usage(authenticated = True)
					usagesUnauthenticated = instance.usage(authenticated = False)

					person = False
					studio = False
					release = False
					if detail == MetaTools.DetailStandard:
						if usagesUnauthenticated < 0.7: release = True
						if usagesUnauthenticated < 0.5: studio = True
					elif detail == MetaTools.DetailExtended:
						if usagesUnauthenticated < 0.9 or usagesAuthenticated < 0.4: release = True
						if usagesUnauthenticated < 0.8 or usagesAuthenticated < 0.3: studio = True
						if usagesUnauthenticated < 0.3: person = True

					# We already retrieve the cast (with thumbnails), translations, studios, and release dates, from TMDb.
					# Retrieving all of them here again will add little new metadata and only prolong the retrieval.
					# translation = None: only retrieve for non-English.
					return instance.metadataMovie(id = id, summary = True, translation = None, person = person, studio = studio, release = release, language = language, extended = True, detail = True, cache = cache, concurrency = bool(threaded))
		except: Logger.error()
		return {'provider' : 'trakt', 'complete' : complete, 'data' : result}

	def _metadataMovieTmdb(self, tmdb = None, imdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		try: return MetaTmdb.instance().metadataMovie(imdb = imdb, tmdb = tmdb, language = language, cache = cache, threaded = threaded, quick = detail == MetaTools.DetailEssential, detail = True)
		except: Logger.error()
		return {'provider' : 'tmdb', 'complete' : True, 'data' : None}

	def _metadataMovieImdb(self, imdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		results = []

		# Do not use the cached summarized data. Only if it comes from IMDb.
		try: origin = not item['temp']['imdb']['voting']['rating'] is None
		except: origin = False

		# Only do this if there is no IMDb rating in in the item, that is, the item does not come from a IMDb list.
		# Retrieving the detailed IMDb data does not really add extra metadata above TMDb/Trakt, except for the rating/vote and the revenue (which is also on TMDb).
		# A single IMDb page is more than 200KB, so retrieving 50 movies will take 10MB+.
		if detail == MetaTools.DetailExtended and imdb and not origin:
			data = MetaImdb.instance().metadataMovie(id = imdb, language = language, cache = cache)
			if data:
				item = data
				origin = True

		complete = True
		result = None
		try:
			if origin and item:
				# Some titles, especially less-known docus/shorts, have metadata from IMDb, but not on TMDb or Trakt.
				# Copy the entire IMDb strucuture, so we have at least a title/plot/etc from IMDb if nothing is available from TMDb or Trakt.
				# NB: Only do this if the item did not come from the MetaCache, since it then contains metadata from other providers.
				# This can cause an exception if metadata(..., refresh = True) is called, which causes a problem with MetaImage.Attribute, since the values from the local cache are URL strings, whereas the newley retrieved images are still unprocessed dictionaries (eg from TMDb), and these arrays cannot be mixed by MetaImage.
				# Update: Also do this if it comes from the cache, but the status is "invalid", meaning the data does not come from MetaCache, but the original dict comes from one of the lists/menus.
				# Eg: basic item comes from random(). It is looked up in MetaCache but cannot be found.
				if (not MetaCache.Attribute in item or (item.get(MetaCache.Attribute) or {}).get(MetaCache.AttributeStatus) == MetaCache.StatusInvalid) and 'temp' in item and 'imdb' in item['temp']:
					result = Tools.copy(item)
					try: del result['temp']
					except: pass
				else:
					result = {}
				result = self._metadataTemporize(item = item, result = result, provider = 'imdb')

				# Check MetaImdb._extractItems() for more details.
				for attribute in ['genre', 'language', 'country']:
					value = item.get(attribute)
					if value:
						value = Tools.listUnique(value + (result.get(attribute) or []))
						if value: result[attribute] = value
				for attribute in ['mpaa']:
					value = item.get(attribute)
					if value: result[attribute] = value

				if complete: complete = bool(result and 'rating' in result and result['rating'])
		except: Logger.error()
		results.append({'provider' : 'imdb', 'complete' : complete, 'data' : result})

		complete = True
		result = None
		try:
			if origin and item:
				result = self._metadataTemporize(item = item, result = {}, provider = 'metacritic')
		except: Logger.error()
		results.append({'provider' : 'metacritic', 'complete' : complete, 'data' : result})

		return results

	def _metadataMovieFanart(self, imdb = None, tmdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			if imdb or tmdb:
				images = MetaFanart.movie(imdb = imdb, tmdb = tmdb, cache = cache)
				if images is False: complete = False
				elif images: result = {MetaImage.Attribute : images}
		except: Logger.error()
		return {'provider' : 'fanart', 'complete' : complete, 'data' : result}

	##############################################################################
	# METADATA - SET
	##############################################################################

	def metadataSet(self, tmdb = None, title = None, year = None, items = None, filter = None, clean = True, quick = None, refresh = False, cache = False, threaded = None):
		try:
			media = Media.Set

			pickSingle = False
			pickMultiple = False

			if items:
				if Tools.isArray(items):
					pickMultiple = True
				else:
					pickSingle = True
					items = [items]
			elif tmdb:
				pickSingle = True
				items = [{'tmdb' : tmdb}]
			elif title:
				pickSingle = True
				items = self._metadataIdLookup(media = media, title = title, year = year, list = True)

			if items:
				items = self._metadataCache(media = media, items = items, function = self._metadataSetUpdate, quick = quick, refresh = refresh, cache = cache, threaded = threaded)
				if items:
					items = self._metadataFilter(media = media, items = items, filter = filter)
					items = self._metadataAggregate(media = media, items = items)

					if pickSingle: items = items[0] if items else None

					items = self._metadataClean(media = media, items = items, clean = clean)
					return items
		except: Logger.error()
		return None

	def _metadataSetUpdate(self, item, result = None, lock = None, locks = None, semaphore = None, cache = False, threaded = None, mode = None, part = True):
		try:
			media = Media.Set

			ids = {'imdb' : [], 'tmdb' : [], 'tvdb' : [], 'trakt' : [], 'slug' : [], 'tvmaze' : [], 'tvrage' : []}

			imdb = item.get('imdb')
			tmdb = item.get('tmdb')
			tvdb = item.get('tvdb')
			trakt = item.get('trakt')
			slug = item.get('slug')

			title = item.get('title')
			year = item.get('year')

			# By default we do not cache requests to disc, since it takes longer and requires more storage space.
			# If the same movie appears multiple times in the list (some Trakt lists, eg watched list where a movie was watched twice), sub-requests will also have to be executed multiple times, since they are not disc-cached.
			# Cache in memory and use locks to block subsequent calls with the same ID/title until the first request is done and then use those results without executing all the code again.
			id = Memory.id(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
			if not locks is None:
				if not id in locks:
					lock.acquire()
					if not id in locks: locks[id] = Lock()
					lock.release()
				locks[id].acquire()
				data = Memory.get(id = id, uncached = True, local = True, kodi = False)
				if Memory.cached(data):
					if data: item.update(Tools.copy(data)) # Copy in case the memory is used mutiple times. Can be None if not found.
					return None

			# Previous incomplete metadata.
			partDone = True
			partOld = {}
			partNew = {MetaCache.AttributeFail : 0}
			if part:
				try:
					partCache = item.get(MetaCache.Attribute)
					if partCache and partCache.get(MetaCache.AttributeStatus) == MetaCache.StatusIncomplete:
						partOld = partCache.get(MetaCache.AttributePart) or {}
						partNew[MetaCache.AttributeFail] = partOld.get(MetaCache.AttributeFail, 0)
				except: Logger.error()

			if not tmdb:
				values = partOld.get('id')
				if not values or not values.get('complete'): values = self._metadataSetId(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
				partNew['id'] = values
				if values:
					if not values.get('complete'): partDone = False
					values = values.get('data')
					if values:
						value = self._metadataIdAdd(type = 'imdb', metadata = values, ids = ids)
						if not imdb: imdb = value
						value = self._metadataIdAdd(type = 'tmdb', metadata = values, ids = ids)
						if not tmdb: tmdb = value
						value = self._metadataIdAdd(type = 'tvdb', metadata = values, ids = ids)
						if not tvdb: tvdb = value
						value = self._metadataIdAdd(type = 'trakt', metadata = values, ids = ids)
						if not trakt: trakt = value
						value = self._metadataIdAdd(type = 'slug', metadata = values, ids = ids)
						if not slug: slug = value
			if not tmdb: return False

			cache = cache if cache else None
			developer = self._metadataDeveloper(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, item = item)
			if developer: Logger.log('SET METADATA RETRIEVAL [%s]: %s' % (mode.upper() if mode else 'UNKNOWN', developer))

			# DetailEssential: 1 request [TMDb: 1 (summary), Fanart: 0]
			# DetailStandard: 3 requests [TMDb: 2 (summary, images), Fanart: 1 (summary)]
			# DetailExtended: 3 requests [TMDb: 2 (summary, images), Fanart: 1 (summary)]
			requests = []
			if self.mLevel >= 0:
				requests.append({'id' : 'tmdb', 'function' : self._metadataSetTmdb, 'parameters' : {'tmdb' : tmdb, 'imdb' : imdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				if self.mLevel >= 1:
					requests.append({'id' : 'fanart', 'function' : self._metadataSetFanart, 'parameters' : {'imdb' : imdb, 'tmdb' : tmdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})

			partDatas = {}
			if partOld:
				partRequests = []
				for i in requests:
					partData = partOld.get(i['id'])
					if partData and partData.get('complete'): partDatas[i['id']] = partData
					else: partRequests.append(i)
				requests = partRequests
				partDatas = Tools.copy(partDatas) # Copy inner dicts that can be carried over with the update() below.

			datas = self._metadataRetrieve(requests = requests, threaded = threaded)
			datas.update(partDatas)

			data = {}
			niches = []
			genres = []
			studios = []
			networks = []
			languages = []
			countries = []
			status = []
			times = []
			durations = []
			mpaas = []
			images = {}
			voting = {
				'rating' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
				'votes' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
			}

			providers = ['fanart', 'tmdb'] # Keep a specific order. Later values replace newer values.
			providersImage = providers[::-1] # Preferred providers must be placed first. Otherwise it might pick unwanted images first (eg IMDb).

			for i in providers:
				if i in datas:
					values = datas[i]
					if values:
						if not Tools.isArray(values): values = [values]
						for value in values:
							if not value['complete']:
								partDone = False
								if developer: Logger.log('SET METADATA INCOMPLETE [%s]: %s' % (i.upper(), developer))

							provider = value['provider']

							# Use "provider", not "i", since IMDb also has Metacritic data.
							# NB: Important to copy, since the dict is edited below.
							# Otherwise we edit the dict before it gets (possibly) written as partial data to MetaCache.
							# Eg: TVDb fails or has no data yet (new release). The TMDb images get deleted below, and the TMDb is later added as partial data to MetaCache. The next time the partial metadata is refreshed, the TMDb data is used, but now does not have images anymore, causing the poster to be missing in the menus.
							# This mostly happens with new releases. Either TMDb/TVDb/Trakt has not listed it yet, or Trakt has the wrong TMDb/TVDb ID.
							partNew[provider] = Tools.copy(value)

							value = value['data']
							if value:
								if MetaImage.Attribute in value:
									images = Tools.update(images, value[MetaImage.Attribute], none = False, lists = True, unique = False)
									del value[MetaImage.Attribute]

								self._metadataIdAdd(metadata = value, ids = ids)

								if 'niche' in value: niches.append(value['niche'])
								if 'genre' in value: genres.append(value['genre'])
								if 'studio' in value: studios.append(value['studio'])
								if 'network' in value: networks.append(value['network'])
								if 'language' in value: languages.append(value['language'])
								if 'country' in value: countries.append(value['country'])
								if 'status' in value: status.append(value['status'])
								if 'time' in value: times.append(value['time'])
								if 'duration' in value: durations.append(value['duration'])
								if 'mpaa' in value: mpaas.append(value['mpaa'])

								if 'rating' in value: voting['rating'][provider] = value['rating']
								if 'votes' in value: voting['votes'][provider] = value['votes']
								if 'userrating' in value: voting['user'][provider] = value['userrating']

								data = Tools.update(data, value, none = False, lists = False, unique = False)

			genres = self.mTools.mergeGenre(genres)
			if genres: data['genre'] = genres

			languages = self.mTools.mergeLanguage(languages)
			if languages: data['language'] = languages

			countries = self.mTools.mergeCountry(countries)
			if countries: data['country'] = countries

			networks = self.mTools.mergeNetwork(networks, country = countries)
			if networks: data['network'] = networks

			studios = self.mTools.mergeStudio(studios, other = networks, country = countries)
			if studios: data['studio'] = studios

			status = self.mTools.mergeStatus(status)
			if status: data['status'] = status

			times = self.mTools.mergeTime(times, metadata = data)
			if times:
				data['time'] = times
				launch = times.get(MetaTools.TimeLaunch)
				if launch: data['premiered'] = Time.format(launch, format = Time.FormatDate)

			durations = self.mTools.mergeDuration(durations)
			if durations: data['duration'] = durations

			mpaas = self.mTools.mergeCertificate(mpaas, media = media)
			if mpaas: data['mpaa'] = mpaas

			data['media'] = media

			niche = self.mTools.mergeNiche(niches)
			niche = self.mTools.niche(niche = niche, metadata = data)
			if niche: data['niche'] = niche

			data['voting'] = voting

			data = {k : v for k, v in data.items() if not v is None}

			# Always replace the IDs of refreshed metadata and do not use the IDs saved to MetaCache previously.
			# Since the old metadata can contain old/outdated/wrong IDs which were fixed in the newly retrieved/refreshed metadata.
			# Check for a detailed explanation under _metadataId().
			self._metadataIdUpdate(metadata = data, ids = ids)

			if images:
				MetaImage.update(media = MetaImage.MediaSet, images = images, data = data, sort = providersImage)
			else:
				# Sometimes the images are not available, especially for new/future releases.
				# This looks ugly in the menus. Mark as incomplete to re-retrieve sooner.
				partDone = False
				try: partNew['tmdb']['complete'] = False
				except: pass
				try: partNew['fanart']['complete'] = False
				except: pass
				if developer: Logger.log('SET IMAGES INCOMPLETE: %s' % developer)

			# Do this before here already.
			# Otherwise a bunch of regular expressions are called every time the menu is loaded.
			self.mTools.cleanPlot(metadata = data)

			# Calculate the rating here already, so that we have a default rating/votes if this metadata dictionary is passed around without being cleaned first.
			# More info under meta -> tools.py -> cleanVoting().
			self.mTools.cleanVoting(metadata = data, round = True) # Round to reduce storage space of average ratings with many decimal places.

			Memory.set(id = id, value = data, local = True, kodi = False)
			if item and data: item.update(Tools.copy(data)) # Can be None if the ID was not found. Copy in case the outer item is edited before we write the data to MetaCache.

			if partDone:
				try: item[MetaCache.Attribute][MetaCache.AttributePart] = None
				except: pass
			else:
				partNew[MetaCache.AttributeFail] += 1
				data[MetaCache.Attribute] = {MetaCache.AttributePart : partNew}

			self._batchLoad(media = media, tmdb = data.get('tmdb'))
			result.append(data)
		except:
			Logger.error()
		finally:
			if locks and id: locks[id].release()
			if semaphore: semaphore.release()
			self.mTools.busyFinish(media = media, item = item)

	def _metadataSetId(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None):
		result = self.mTools.idSet(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
		if result: return {'complete' : True, 'data' : {'id' : result}}
		else: return {'complete' : False, 'data' : result}

	def _metadataSetTmdb(self, tmdb = None, imdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		try: return MetaTmdb.instance().metadataSet(imdb = imdb, tmdb = tmdb, language = language, cache = cache, threaded = threaded, quick = detail == MetaTools.DetailEssential, detail = True)
		except: Logger.error()
		return {'provider' : 'tmdb', 'complete' : True, 'data' : None}

	def _metadataSetFanart(self, imdb = None, tmdb = None, language = None, item = None, cache = False, threaded = None, detail = None):
		complete = True
		result = None
		try:
			if imdb or tmdb:
				images = MetaFanart.set(imdb = imdb, tmdb = tmdb, cache = cache)
				if images is False: complete = False
				elif images: result = {MetaImage.Attribute : images}
		except: Logger.error()
		return {'provider' : 'fanart', 'complete' : complete, 'data' : result}

	##############################################################################
	# METADATA - SHOW
	##############################################################################

	# NB: For efficiency, call this function with "pack=False" if the pack data is not needed. More info at metadata().
	def metadataShow(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, items = None, pack = None, filter = None, clean = True, quick = None, refresh = False, cache = False, threaded = None):
		try:
			media = Media.Show

			pickSingle = False
			pickMultiple = False

			if items:
				if Tools.isArray(items):
					pickMultiple = True
				else:
					pickSingle = True
					items = [items]
			elif imdb or tmdb or tvdb or trakt:
				pickSingle = True
				items = [{'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt}]
			elif title:
				pickSingle = True
				items = self._metadataIdLookup(media = media, title = title, year = year, list = True)

			if items:
				items = self._metadataCache(media = media, items = items, function = self._metadataShowUpdate, quick = quick, refresh = refresh, cache = cache, threaded = threaded)
				if items:
					items = self._metadataFilter(media = media, items = items, filter = filter)
					items = self._metadataAggregate(media = media, items = items)

					if pickSingle: items = items[0] if items else None

					# Add "refresh" here, so that if a show is manually refreshed from the context menu, the pack is also refreshed.
					# Not sure if metadataShow() is called from elsewhere with "refresh = True", which might unnecessarily refresh packs which can take very long to generate.
					items = self._metadataPackAggregate(items = items, pack = pack, refresh = refresh, quick = quick, cache = cache, threaded = threaded)

					items = self._metadataClean(media = media, items = items, clean = clean)

					return items
		except: Logger.error()
		return None

	def _metadataShowUpdate(self, item, result = None, lock = None, locks = None, semaphore = None, cache = False, threaded = None, mode = None, part = True):
		try:
			media = Media.Show

			ids = {'imdb' : [], 'tmdb' : [], 'tvdb' : [], 'trakt' : [], 'slug' : [], 'tvmaze' : [], 'tvrage' : []}

			imdb = item.get('imdb')
			tmdb = item.get('tmdb')
			tvdb = item.get('tvdb')
			trakt = item.get('trakt')
			slug = item.get('slug')
			tvmaze = item.get('tvmaze')
			tvrage = item.get('tvrage')

			title = item.get('tvshowtitle') or item.get('title')
			year = item.get('year')

			# By default we do not cache requests to disc, since it takes longer and requires more storage space.
			# If the same show appears multiple times in the list (some Trakt lists, eg watched list where a show was watched twice), sub-requests will also have to be executed multiple times, since they are not disc-cached.
			# Cache in memory and use locks to block subsequent calls with the same ID/title until the first request is done and then use those results without executing all the code again.
			id = Memory.id(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
			if not locks is None:
				if not id in locks:
					lock.acquire()
					if not id in locks: locks[id] = Lock()
					lock.release()
				locks[id].acquire()
				data = Memory.get(id = id, uncached = True, local = True, kodi = False)
				if Memory.cached(data):
					if data: item.update(Tools.copy(data)) # Copy in case the memory is used mutiple times. Can be None if not found.
					return None

			# Previous incomplete metadata.
			partDone = True
			partOld = {}
			partNew = {MetaCache.AttributeFail : 0}
			if part:
				try:
					partCache = item.get(MetaCache.Attribute)
					if partCache and partCache.get(MetaCache.AttributeStatus) == MetaCache.StatusIncomplete:
						partOld = partCache.get(MetaCache.AttributePart) or {}
						partNew[MetaCache.AttributeFail] = partOld.get(MetaCache.AttributeFail, 0)
				except: Logger.error()

			# Trakt requires either a Trakt or IMDb ID.
			# TMDb requires a TMDb ID.
			if not tvdb or (not imdb and not trakt) or (self.mLevel >= 2 and not tmdb):
				values = partOld.get('id')
				if not values or not values.get('complete'): values = self._metadataShowId(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
				partNew['id'] = values
				if values:
					if not values.get('complete'): partDone = False
					values = values.get('data')
					if values:
						value = self._metadataIdAdd(type = 'imdb', metadata = values, ids = ids)
						if not imdb: imdb = value
						value = self._metadataIdAdd(type = 'tmdb', metadata = values, ids = ids)
						if not tmdb: tmdb = value
						value = self._metadataIdAdd(type = 'tvdb', metadata = values, ids = ids)
						if not tvdb: tvdb = value
						value = self._metadataIdAdd(type = 'trakt', metadata = values, ids = ids)
						if not trakt: trakt = value
						value = self._metadataIdAdd(type = 'slug', metadata = values, ids = ids)
						if not slug: slug = value
						value = self._metadataIdAdd(type = 'tvmaze', metadata = values, ids = ids)
						if not tvmaze: tvmaze = value
						value = self._metadataIdAdd(type = 'tvrage', metadata = values, ids = ids)
						if not tvrage: tvrage = value
			if not imdb and not tmdb and not tvdb and not trakt: return False

			cache = cache if cache else None
			developer = self._metadataDeveloper(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, item = item)
			if developer: Logger.log('SHOW METADATA RETRIEVAL [%s]: %s' % (mode.upper() if mode else 'UNKNOWN', developer))

			# DetailEssential: 2-3 requests [Trakt: 1-2 (summary, optional translations), TVDb: 1 (summary), TMDb: 0, IMDb: 0, Fanart: 0]
			# DetailStandard: 4-5 requests [Trakt: 2-3 (summary, studios, optional translations), TVDb: 1 (summary), TMDb: 0, IMDb: 0, Fanart: 1 (summary)]
			# DetailExtended: 8-9 requests [Trakt: 3-4 (summary, people, studios, optional translations), TVDb: 1 (summary), TMDb: 2 (summary), IMDb: 1 (summary), Fanart: 1 (summary)]
			requests = []
			if self.mLevel >= 0:
				requests.append({'id' : 'trakt', 'function' : self._metadataShowTrakt, 'parameters' : {'trakt' : trakt, 'imdb' : imdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				requests.append({'id' : 'tvdb', 'function' : self._metadataShowTvdb, 'parameters' : {'tvdb' : tvdb, 'imdb' : imdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				requests.append({'id' : 'imdb', 'function' : self._metadataShowImdb, 'parameters' : {'imdb' : imdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				if self.mLevel >= 1:
					requests.append({'id' : 'fanart', 'function' : self._metadataShowFanart, 'parameters' : {'tvdb' : tvdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
					if self.mLevel >= 2:
						requests.append({'id' : 'tmdb', 'function' : self._metadataShowTmdb, 'parameters' : {'tmdb' : tmdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})

			partDatas = {}
			if partOld:
				partRequests = []
				for i in requests:
					partData = partOld.get(i['id'])
					if partData and partData.get('complete'): partDatas[i['id']] = partData
					else: partRequests.append(i)
				requests = partRequests
				partDatas = Tools.copy(partDatas) # Copy inner dicts that can be carried over with the update() below.

			datas = self._metadataRetrieve(requests = requests, threaded = threaded)
			datas.update(partDatas)

			data = {}
			niches = []
			genres = []
			studios = []
			networks = [[], []]
			languages = []
			countries = []
			status = []
			times = []
			durations = []
			mpaas = []
			casts = []
			directors = []
			writers = []
			creators = []
			images = {}
			packs = {}
			voting = {
				'rating' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
				'votes' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
			}

			providers = ['metacritic', 'imdb', 'tmdb', 'fanart', 'tvdb', 'trakt'] # Keep a specific order. Later values replace newer values.
			providersImage = providers[::-1] # Preferred providers must be placed first. Otherwise some shows might pick the IMDb image. Eg: tt19401686 (Trakt: the-vikings-2015 vs the-vikings-2015-248534).

			for i in providers:
				if i in datas:
					values = datas[i]
					if values:
						if not Tools.isArray(values): values = [values]
						for value in values:
							if not value['complete']:
								partDone = False
								if developer: Logger.log('SHOW METADATA INCOMPLETE [%s]: %s' % (i.upper(), developer))

							provider = value['provider']

							# Use "provider", not "i", since IMDb also has Metacritic data.
							# NB: Important to copy, since the dict is edited below.
							# Otherwise we edit the dict before it gets (possibly) written as partial data to MetaCache.
							# Eg: TVDb fails or has no data yet (new release). The TMDb images get deleted below, and the TMDb is later added as partial data to MetaCache. The next time the partial metadata is refreshed, the TMDb data is used, but now does not have images anymore, causing the poster to be missing in the menus.
							# This mostly happens with new releases. Either TMDb/TVDb/Trakt has not listed it yet, or Trakt has the wrong TMDb/TVDb ID.
							partNew[provider] = Tools.copy(value)

							value = value['data']
							if value:
								if MetaImage.Attribute in value:
									images = Tools.update(images, value[MetaImage.Attribute], none = False, lists = True, unique = False)
									del value[MetaImage.Attribute]

								self._metadataIdAdd(metadata = value, ids = ids)

								if 'niche' in value: niches.append(value['niche'])
								if 'genre' in value: genres.append(value['genre'])
								if 'studio' in value: studios.append(value['studio'])
								if 'network' in value: networks[1 if i == 'tvdb' else 0].append(value['network'])
								if 'language' in value: languages.append(value['language'])
								if 'country' in value: countries.append(value['country'])
								if 'status' in value: status.append(value['status'])
								if 'time' in value: times.append(value['time'])
								if 'duration' in value: durations.append(value['duration'])
								if 'mpaa' in value: mpaas.append(value['mpaa'])

								if 'cast' in value: casts.append(value['cast'])
								if 'director' in value: directors.append(value['director'])
								if 'writer' in value: writers.append(value['writer'])
								if 'creator' in value: creators.append(value['creator'])

								if 'rating' in value: voting['rating'][provider] = value['rating']
								if 'votes' in value: voting['votes'][provider] = value['votes']
								if 'userrating' in value: voting['user'][provider] = value['userrating']

								if 'packed' in value: packs[i] = value['packed']

								data = Tools.update(data, value, none = False, lists = False, unique = False)

			genres = self.mTools.mergeGenre(genres)
			if genres: data['genre'] = genres

			languages = self.mTools.mergeLanguage(languages)
			if languages: data['language'] = languages

			countries = self.mTools.mergeCountry(countries)
			if countries: data['country'] = countries

			# Trakt and TMDb often list mutiple networks if shows are later taken over by a new network.
			#	Community:
			#		TMDb: ['NBC', 'Yahoo! Screen']
			#		TVDB: ['NBC', 'Yahoo! Screen', 'YouTube']
			#		Trakt: ['Yahoo! Screen']
			#	Vikings:
			#		TMDb: ['Prime Video', 'History']
			#		TVDB: ['History Canada']
			#		Trakt: ['Amazon']
			#	The Boys
			#		TMDb: ['Prime Video']
			#		TVDB: ['Prime Video', 'YouTube']
			#		Trakt: ['Amazon']
			# Although Trakt lists mutiple networks on their website (from earliest to newest network), it only returns the newest network via the API.
			# TMDb sometimes lists the earlier networks first, sometimes the newer networks.
			# TVDb has an original network attribute, which will be added first to the list. So prefer TVDb.
			networks = self.mTools.mergeNetwork(networks[0] + networks[1], order = True, country = countries) # They get reversed in merge(), so place TVDb last.
			if networks: data['network'] = networks

			studios = self.mTools.mergeStudio(studios, other = networks, country = countries)
			if studios: data['studio'] = studios

			status = self.mTools.mergeStatus(status)
			if status: data['status'] = status

			times = self.mTools.mergeTime(times, metadata = data)
			if times: data['time'] = times

			durations = self.mTools.mergeDuration(durations)
			if durations: data['duration'] = durations

			mpaas = self.mTools.mergeCertificate(mpaas, media = media)
			if mpaas: data['mpaa'] = mpaas

			cast = self.mTools.mergeCast(casts)
			if cast: data['cast'] = cast

			director = self.mTools.mergeCrew(directors)
			if director: data['director'] = director

			writer = self.mTools.mergeCrew(writers)
			if writer: data['writer'] = writer

			creator = self.mTools.mergeCrew(creators)
			if creator: data['creator'] = creator

			data['media'] = media

			niche = self.mTools.mergeNiche(niches)
			niche = self.mTools.niche(niche = niche, metadata = data)
			if niche: data['niche'] = niche

			data['voting'] = voting

			data = {k : v for k, v in data.items() if not v is None}

			# Always replace the IDs of refreshed metadata and do not use the IDs saved to MetaCache previously.
			# Since the old metadata can contain old/outdated/wrong IDs which were fixed in the newly retrieved/refreshed metadata.
			# Check for a detailed explanation under _metadataId().
			self._metadataIdUpdate(metadata = data, ids = ids)

			if not 'tvshowtitle' in data and 'title' in data: data['tvshowtitle'] = data['title']

			if images:
				MetaImage.update(media = MetaImage.MediaShow, images = images, data = data, sort = providersImage)
			else:
				# Sometimes the images are not available, especially for new/future releases.
				# This looks ugly in the menus. Mark as incomplete to re-retrieve sooner.
				partDone = False
				try: partNew['tvdb']['complete'] = False
				except: pass
				try: partNew['fanart']['complete'] = False
				except: pass
				if developer: Logger.log('SHOW IMAGES INCOMPLETE: %s' % developer)

			# Do this before here already.
			# Otherwise a bunch of regular expressions are called every time the menu is loaded.
			self.mTools.cleanPlot(metadata = data)

			# Calculate the rating here already, so that we have a default rating/votes if this metadata dictionary is passed around without being cleaned first.
			# More info under meta -> tools.py -> cleanVoting().
			self.mTools.cleanVoting(metadata = data, round = True) # Round to reduce storage space of average ratings with many decimal places.

			# Use the base pack counts/durations from TMDb and Trakt.
			# TMDb has more detailed counts than Trakt.
			# Prefer the old reduced pack data added by _metadataPackUpdate().
			# Otherwise if we refresh the show metadata, the reduced pack data is gone until the pack is updated again.
			# These "inaccurate" counters are used to display episode counts in some skins (eg Aeon Nox) in show menus.
			pack = {}
			try: pack.update(packs.get('trakt')) # Least accurate.
			except: pass
			try: pack.update(packs.get('tmdb')) # More accurate.
			except: pass
			try: pack.update(item.get('packed')) # Most accurate, since it was calculated from the full pack.
			except: pass
			if pack: data['packed'] = pack

			Memory.set(id = id, value = data, local = True, kodi = False)
			if item and data: item.update(Tools.copy(data)) # Can be None if the ID was not found. Copy in case the outer item is edited before we write the data to MetaCache.

			if partDone:
				try: item[MetaCache.Attribute][MetaCache.AttributePart] = None
				except: pass
			else:
				partNew[MetaCache.AttributeFail] += 1
				data[MetaCache.Attribute] = {MetaCache.AttributePart : partNew}

			self._batchLoad(media = media, imdb = data.get('imdb'), tmdb = data.get('tmdb'), tvdb = data.get('tvdb'), trakt = data.get('trakt'))
			result.append(data)
		except:
			Logger.error()
		finally:
			if locks and id: locks[id].release()
			if semaphore: semaphore.release()
			self.mTools.busyFinish(media = media, item = item)

	def _metadataShowId(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None):
		result = self.mTools.idShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
		if result: return {'complete' : True, 'data' : {'id' : result}}
		else: return {'complete' : False, 'data' : result}

	def _metadataShowTrakt(self, trakt = None, imdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			# Do not use the cached summarized data. Only if it comes from IMDb.
			try: origin = bool(item['temp']['trakt'])
			except: origin = False

			if detail == MetaTools.DetailEssential and item and origin: # Comes from a Trakt list with basic metadata.
				if MetaCache.Attribute in item:
					result = {}
				else:
					result = Tools.copy(item)
					try: del result['temp']
					except: pass
				result = self._metadataTemporize(item = item, result = result, provider = 'trakt')
			else: # Comes from another list, or forcefully retrieve detailed metadata.
				id = trakt or imdb
				if id:
					# Trakt has an API limit of 1000 requests per 5 minutes.
					# Retrieving all the additional metadata will very quickly consume the limit if a few pages are loaded.
					# Only retrieve the extended metadata if enough requests are still avilable for the past 5 minutes.
					instance = MetaTrakt.instance()
					usagesAuthenticated = instance.usage(authenticated = True)
					usagesUnauthenticated = instance.usage(authenticated = False)

					person = False
					studio = False
					if detail == MetaTools.DetailStandard:
						if usagesUnauthenticated < 0.5: studio = True
					elif detail == MetaTools.DetailExtended:
						if usagesUnauthenticated < 0.8 or usagesAuthenticated < 0.3: studio = True
						if usagesUnauthenticated < 0.3: person = True

					# We already retrieve the cast (with thumbnails), translations and studios, from TMDb.
					# Retrieving all of them here again will add little new metadata and only prolong the retrieval.
					# translation = None: only retrieve for non-English.
					result = instance.metadataShow(id = id, summary = True, translation = None, person = person, studio = studio, language = language, extended = True, detail = True, cache = cache, concurrency = bool(threaded))

					if result.get('complete'):
						# Create basic pack data in case the full pack metadata has not been retrieved yet.
						# Is used by some skins (eg Aeon Nox) to display episode counts for show menus.
						try:
							data = result.get('data')
							pack = MetaPack.reduceBase(episodeOfficial = data.get('count', {}).get('released'), duration = data.get('duration'))
							if pack: result['data']['packed'] = pack
						except: Logger.error()

					return result # Already contains the outer structure.
		except: Logger.error()
		return {'provider' : 'trakt', 'complete' : complete, 'data' : result}

	def _metadataShowTvdb(self, tvdb = None, imdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		try: return MetaTvdb.instance().metadataShow(tvdb = tvdb, imdb = imdb, language = language, cache = cache, threaded = threaded, detail = True)
		except: Logger.error()
		return {'provider' : 'tvdb', 'complete' : True, 'data' : None}

	def _metadataShowTmdb(self, tmdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		try: return MetaTmdb.instance().metadataShow(tmdb = tmdb, language = language, cache = cache, threaded = threaded, quick = detail == MetaTools.DetailEssential, detail = True)
		except: Logger.error()
		return {'provider' : 'tmdb', 'complete' : True, 'data' : None}

	def _metadataShowImdb(self, imdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		results = []

		# Do not use the cached summarized data. Only if it comes from IMDb.
		try: origin = not item['temp']['imdb']['voting']['rating'] is None
		except: origin = False

		# Only do this if there is no IMDb rating in in the item, that is, the item does not come from a IMDb list.
		# Retrieving the detailed IMDb data does not really add extra metadata above TMDb/Trakt, except for the rating/vote and the revenue (which is also on TMDb).
		# A single IMDb page is more than 200KB, so retrieving 50 shows will take 10MB+.
		if detail == MetaTools.DetailExtended and imdb and not origin:
			data = MetaImdb.instance().metadataShow(id = imdb, language = language, cache = cache)
			if data:
				item = data
				origin = True

		complete = True
		result = None
		try:
			if origin and item:
				# Some titles, especially less-known docus/shorts, have metadata from IMDb, but not on TMDb or Trakt.
				# Copy the entire IMDb strucuture, so we have at least a title/plot/etc from IMDb if nothing is available from TMDb or Trakt.
				# NB: Only do this if the item did not come from the MetaCache, since it then contains metadata from other providers.
				# This can cause an exception if metadata(..., refresh = True) is called, which causes a problem with MetaImage.Attribute, since the values from the local cache are URL strings, whereas the newley retrieved images are still unprocessed dictionaries (eg from TMDb), and these arrays cannot be mixed by MetaImage.
				# Update: Also do this if it comes from the cache, but the status is "invalid", meaning the data does not come from MetaCache, but the original dict comes from one of the lists/menus.
				# Eg: basic item comes from random(). It is looked up in MetaCache but cannot be found.
				if (not MetaCache.Attribute in item or (item.get(MetaCache.Attribute) or {}).get(MetaCache.AttributeStatus) == MetaCache.StatusInvalid) and 'temp' in item and 'imdb' in item['temp']:
					result = Tools.copy(item)
					try: del result['temp']
					except: pass
				else:
					result = {}
				result = self._metadataTemporize(item = item, result = result, provider = 'imdb')

				# Check MetaImdb._extractItems() for more details.
				for attribute in ['genre', 'language', 'country']:
					value = item.get(attribute)
					if value:
						value = Tools.listUnique(value + (result.get(attribute) or []))
						if value: result[attribute] = value
				for attribute in ['mpaa']:
					value = item.get(attribute)
					if value: result[attribute] = value

				if complete: complete = bool(result and 'rating' in result and result['rating'])
		except: Logger.error()
		results.append({'provider' : 'imdb', 'complete' : complete, 'data' : result})

		complete = True
		result = None
		try:
			if origin and item:
				result = self._metadataTemporize(item = item, result = {}, provider = 'metacritic')
		except: Logger.error()
		results.append({'provider' : 'metacritic', 'complete' : complete, 'data' : result})

		return results

	def _metadataShowFanart(self, tvdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			if tvdb:
				images = MetaFanart.show(tvdb = tvdb, cache = cache)
				if images is False: complete = False
				elif images: result = {MetaImage.Attribute : images}
		except: Logger.error()
		return {'provider' : 'fanart', 'complete' : complete, 'data' : result}

	##############################################################################
	# METADATA - SEASON
	##############################################################################

	# NB: For efficiency, call this function with "pack=False" if the pack data is not needed. More info at metadata().
	def metadataSeason(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, items = None, pack = None, filter = None, clean = True, quick = None, refresh = False, cache = False, threaded = None, aggregate = True, hint = None):
		try:
			media = Media.Season

			pickSingle = False
			pickMultiple = False

			if items:
				if Tools.isArray(items):
					pickMultiple = True
				else:
					pickSingle = True
					items = [items]
			elif imdb or tmdb or tvdb or trakt:
				pickSingle = True
				items = [{'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt}]
			elif title:
				pickSingle = True
				items = self._metadataIdLookup(media = media, title = title, year = year, list = True)

			if items:
				items = self._metadataCache(media = media, items = items, function = self._metadataSeasonUpdate, quick = quick, refresh = refresh, cache = cache, threaded = threaded, hint = hint)
				if items:
					items = self._metadataFilter(media = media, items = items, filter = filter)
					items = self._metadataAggregate(media = media, items = items) # Must be before picking, since it uses temp and the internal "seasons" list.

					if items:
						picks = None
						if pickSingle:
							picks = items[0].get('seasons')
							if picks and not season is None:
								temp = None
								for i in picks:
									if i['season'] == season:
										temp = i
										break
								picks = temp
						elif not items[0].get('season') is None:
							# Use to select a single season for different shows from navigator -> History -> Seasons.
							picks = []
							for item in items:
								for i in (item.get('seasons') or []):
									if i['season'] == item['season']:
										picks.append(i)
										break
						else:
							picks = [item['seasons'] for item in items]
						items = picks

						if items:
							items = self._metadataPackAggregate(items = items, pack = pack, quick = quick, cache = cache, threaded = threaded) # Do not add "refresh" here, otherwise the pack will be refreshed every time a season is refreshed.
							if aggregate: items = self._metadataSeasonAggregate(items = items, threaded = threaded)
							items = self._metadataClean(media = media, items = items, clean = clean)
							return items
		except: Logger.error()
		return None

	def _metadataSeasonUpdate(self, item, result = None, lock = None, locks = None, semaphore = None, cache = False, threaded = None, mode = None, part = True):
		try:
			media = Media.Season

			imdb = item.get('imdb')
			tmdb = item.get('tmdb')
			tvdb = item.get('tvdb')
			trakt = item.get('trakt')
			slug = item.get('slug')
			tvmaze = item.get('tvmaze')
			tvrage = item.get('tvrage')

			title = item.get('tvshowtitle') or item.get('title')
			year = item.get('year')

			# By default we do not cache requests to disc, since it takes longer and requires more storage space.
			# If the same show appears multiple times in the list (some Trakt lists, eg watched list where a show was watched twice), sub-requests will also have to be executed multiple times, since they are not disc-cached.
			# Cache in memory and use locks to block subsequent calls with the same ID/title until the first request is done and then use those results without executing all the code again.
			id = Memory.id(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
			if not locks is None:
				if not id in locks:
					lock.acquire()
					if not id in locks: locks[id] = Lock()
					lock.release()
				locks[id].acquire()
				data = Memory.get(id = id, uncached = True, local = True, kodi = False)
				if Memory.cached(data):
					if data: item.update(Tools.copy(data)) # Copy in case the memory is used mutiple times. Can be None if not found.
					return None

			# Previous incomplete metadata.
			partDone = True
			partOld = {}
			partNew = {MetaCache.AttributeFail : 0}
			if part:
				try:
					partCache = item.get(MetaCache.Attribute)
					if partCache and partCache.get(MetaCache.AttributeStatus) == MetaCache.StatusIncomplete:
						partOld = partCache.get(MetaCache.AttributePart) or {}
						partNew[MetaCache.AttributeFail] = partOld.get(MetaCache.AttributeFail, 0)
				except: Logger.error()

			# Trakt requires either a Trakt or IMDb ID.
			# TMDb requires a TMDb ID.
			if not tvdb or (not imdb and not trakt) or (self.mLevel >= 2 and (not tmdb or not not imdb)):
				ids = partOld.get('id')
				if not ids or not ids.get('complete'): ids = self._metadataSeasonId(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
				partNew['id'] = ids
				if ids:
					if not ids.get('complete'): partDone = False
					ids = ids.get('data')
					if ids:
						ids = ids.get('id')
						if ids:
							if not imdb: imdb = ids.get('imdb')
							if not tmdb: tmdb = ids.get('tmdb')
							if not tvdb: tvdb = ids.get('tvdb')
							if not trakt: trakt = ids.get('trakt')
							if not slug: slug = ids.get('slug')
							if not tvmaze: tvmaze = ids.get('tvmaze')
							if not tvrage: tvrage = ids.get('tvrage')
			if not imdb and not tmdb and not tvdb and not trakt: return False

			developer = self._metadataDeveloper(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, item = item)
			if developer: Logger.log('SEASON METADATA RETRIEVAL [%s]: %s' % (mode.upper() if mode else 'UNKNOWN', developer))

			show = self.metadataShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, pack = False, threaded = threaded)
			if not show:
				Memory.set(id = id, value = {}, local = True, kodi = False)
				return False

			pack = self.metadataPack(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, threaded = threaded)
			pack = MetaPack.instance(pack = pack)

			if not title and show and 'tvshowtitle' in show: title = show['tvshowtitle']
			cache = cache if cache else None

			# count = number of seasons.
			# DetailEssential: (count + 2) requests (eg: 10 seasons = 11 requests) [Trakt: 1 (summary), TVDb: 2-count (summary, each season), TMDb: 0, IMDb: 0, Fanart: 0 (summary)]
			# DetailStandard: ((1-2)*count + 3) requests (eg: 10 seasons = 12 requests or 21 requests with translations) [Trakt: 1 or (1-count) (summary, optional translations), TVDb: 2-count (summary, each season), TMDb: 0, IMDb: 0, Fanart: 1 (summary)]
			# DetailExtended: ((3-4)*count + 5-7) requests (eg: 10 seasons = 32 requests or 42 requests with translations) [Trakt: (2-count) or (2*count) (summary, each season, optional translations), TVDb: 2-count (summary, each season), TMDb: 2-(count/20) (summary, each season), IMDb: 1-count (each season), Fanart: 1 (summary)]
			requests = []
			if self.mLevel >= 0:
				requests.append({'id' : 'trakt', 'function' : self._metadataSeasonTrakt, 'parameters' : {'trakt' : trakt, 'imdb' : imdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				requests.append({'id' : 'tvdb', 'function' : self._metadataSeasonTvdb, 'parameters' : {'tvdb' : tvdb, 'imdb' : imdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				if self.mLevel >= 1:
					requests.append({'id' : 'fanart', 'function' : self._metadataSeasonFanart, 'parameters' : {'tvdb' : tvdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
					if self.mLevel >= 2:
						requests.append({'id' : 'tmdb', 'function' : self._metadataSeasonTmdb, 'parameters' : {'tmdb' : tmdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
						requests.append({'id' : 'imdb', 'function' : self._metadataSeasonImdb, 'parameters' : {'imdb' : imdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})

			partDatas = {}
			if partOld:
				partRequests = []
				for i in requests:
					partData = partOld.get(i['id'])
					if partData and partData.get('complete'): partDatas[i['id']] = partData
					else: partRequests.append(i)
				requests = partRequests
				partDatas = Tools.copy(partDatas) # Copy inner dicts that can be carried over with the update() below.

			datas = self._metadataRetrieve(requests = requests, threaded = threaded)
			datas.update(partDatas)

			data = {'seasons' : []}
			niches = {}
			genres = {}
			studios = {}
			networks = {}
			languages = {}
			countries = {}
			status = {}
			times = {}
			durations = {}
			mpaas = {}
			casts = {}
			directors = {}
			writers = {}
			creators = {}
			images = {}
			votings = {}
			voting = {
				'rating' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
				'votes' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
			}

			providers = ['metacritic', 'imdb', 'tmdb', 'fanart', 'tvdb', 'trakt'] # Keep a specific order. Later values replace newer values.
			providersImage = providers[::-1] # Preferred providers must be placed first. Otherwise it might pick unwanted images first (eg IMDb).

			for i in providers:
				if i in datas:
					values = datas[i]
					if values:
						if not Tools.isArray(values): values = [values]
						for value in values:
							if not value['complete']:
								partDone = False
								if developer: Logger.log('SEASON METADATA INCOMPLETE [%s]: %s' % (i.upper(), developer))

							provider = value['provider']

							# Use "provider", not "i", since IMDb also has Metacritic data.
							# NB: Important to copy, since the dict is edited below.
							# Otherwise we edit the dict before it gets (possibly) written as partial data to MetaCache.
							# Eg: TVDb fails or has no data yet (new release). The TMDb images get deleted below, and the TMDb is later added as partial data to MetaCache. The next time the partial metadata is refreshed, the TMDb data is used, but now does not have images anymore, causing the poster to be missing in the menus.
							# This mostly happens with new releases. Either TMDb/TVDb/Trakt has not listed it yet, or Trakt has the wrong TMDb/TVDb ID.
							partNew[provider] = Tools.copy(value)

							seasons = value['data']
							if seasons:
								seasons = Tools.copy(seasons) # Copy, since we do title/plot/studio replacement below in another loop.
								for season in seasons:
									number = season['season']

									if MetaImage.Attribute in season:
										if not number in images: images[number] = {}
										images[number] = Tools.update(images[number], season[MetaImage.Attribute], none = False, lists = True, unique = False)
										del season[MetaImage.Attribute]

									if 'niche' in season:
										if not number in niches: niches[number] = []
										niches[number].append(season['niche'])
									if 'genre' in season:
										if not number in genres: genres[number] = []
										genres[number].append(season['genre'])
									if 'studio' in season:
										if not number in studios: studios[number] = []
										studios[number].append(season['studio'])
									if 'network' in season:
										if not number in networks: networks[number] = [[], []]
										networks[number][1 if i == 'tvdb' else 0].append(season['network'])
									if 'language' in season:
										if not number in languages: languages[number] = []
										languages[number].append(season['language'])
									if 'country' in season:
										if not number in countries: countries[number] = []
										countries[number].append(season['country'])
									if 'status' in season:
										if not number in status: status[number] = []
										status[number].append(season['status'])
									if 'time' in season:
										if not number in times: times[number] = []
										times[number].append(season['time'])
									if 'duration' in season:
										if not number in durations: durations[number] = []
										durations[number].append(season['duration'])
									if 'mpaa' in season:
										if not number in mpaas: mpaas[number] = []
										mpaas[number].append(season['mpaa'])

									if 'cast' in season:
										if not number in casts: casts[number] = []
										casts[number].append(season['cast'])
									if 'director' in season:
										if not number in directors: directors[number] = []
										directors[number].append(season['director'])
									if 'writer' in season:
										if not number in writers: writers[number] = []
										writers[number].append(season['writer'])
									if 'creator' in season:
										if not number in creators: creators[number] = []
										creators[number].append(season['creator'])

									if not number in votings: votings[number] = Tools.copy(voting)
									if 'rating' in season: votings[number]['rating'][provider] = season['rating']
									if 'votes' in season: votings[number]['votes'][provider] = season['votes']
									if 'userrating' in season: votings[number]['user'][provider] = season['userrating']

									found = False
									for j in data['seasons']:
										if j['season'] == number:
											found = True
											Tools.update(j, season, none = False, lists = False, unique = False)
											break
									if not found: data['seasons'].append(season)

			# Fanart can sometimes return images for a season that does not exist.
			# Eg: Dexter S09.
			# Remove any season that does not have an ID or title.
			# IMDb sometimes returns a season that does not exist, such as for specials. Do not filter these out.
			# Eg: The Office UK S03 (IMDb).
			data['seasons'] = [i for i in data['seasons'] if i.get('title') or any((i.get('id') or {}).get(j) or (i.get('temp') or {}).get('imdb') for j in providers)]

			if pack:
				# Copy the additional numbers(eg: season number given as the year) from the pack.
				numbers = {pack.numberStandard(item = i) : pack.number(item = i, number = False) for i in pack.season(default = [])}
				for i in data['seasons']:
					try: i['number'] = numbers[i['season']]
					except: i['number'] = {MetaPack.NumberStandard : i['season']}
					i['packed'] = pack.reduce(season = i['season'])

				# Fanart sometimes has images for non-existing seasons.
				# Eg: "How I Met Your Mother" has Fanart posters for Season 89.
				# Remove these seasons.
				numbers = list(numbers.keys())
				numberMaximum = (max(numbers) if numbers else 0) + 10
				data['seasons'] = [i for i in data['seasons'] if i['season'] in numbers or i['season'] <= numberMaximum]

			# Add summarized pack data to seasons only existing on IMDb.
			# Eg: The Office UK S03 (IMDb).
			for i in data['seasons']:
				if not i.get('packed'):
					count = ((i.get('temp') or {}).get('imdb') or {}).get('count')
					if count: i['packed'] = MetaPack.reduceBase(episodeOfficial = count)

			# Some values are often missing or incorrect on TVDb, and should be replaced with the Trakt/TMDb metadata.
			# TVDb has often incorrect studios/networks for seasons (eg: Game of Thrones and Breaking Bad).
			# TVDb typically does not have a title and plot for seasons. Even if there are plots, it is only available in other languages, except English.
			# TVDb also does not have the cast for seasons. But we do not retrieve the cast from Trakt, since it requires an additional API call per season, and does not have actor thumbnails. Use the show cast from TVDb which has thumbnails.
			for i in ['trakt', 'tmdb']: # Place TMDb last, since it has more translated season titles than Trakt.
				if i in datas:
					values = datas[i]
					if values:
						if not Tools.isArray(values): values = [values]
						for value in values:
							seasons = value['data']
							if seasons:
								for season in seasons:
									for j in data['seasons']:
										if j['season'] == season['season']:
											for attribute in ['title', 'originaltitle', 'plot', 'studio']:
												if attribute in season and season[attribute]: j[attribute] = season[attribute]
											break

			# Some attributes might be missing. Use the show/season attributes.
			# Eg: Most episodes, if not all, do not have a studio.
			parentTitle = show.get('tvshowtitle')
			parentPlot = show.get('plot')
			parentNetwork = show.get('network')
			parentStudio = show.get('studio')
			parentLanguage = show.get('language')
			parentCountry = show.get('country')
			parentGenre = show.get('genre')
			parentMpaa = show.get('mpaa')
			parentDuration = show.get('duration')
			parentCast = show.get('cast')
			parentDirector = show.get('director')
			parentWriter = show.get('writer')
			parentCreator = show.get('creator')
			parentPremiere = show.get('premiered') or show.get('aired')
			parentTime = show.get('time')

			# Sometimes TVDb list "probably" incorrect networks for seasons.
			# Eg: One Piece. TVDb lists BBC, NBC, CBS, Adult Swim as networks, but Fuji TV only for three of the seasons. Trakt has Fuji TV for all seasons.
			# If Trakt/TMDb list a single network for all seasons, but TVDb has mutiple networks, prefer Trakt. Otherwise prefer TVDb.
			# Also switch if TVDb returns Syndication (licensed to mutiple networks).
			# Eg: Star Trek (1966).
			# Update: About 1/3 of all popular shows have at least one season that TVDb has the completely wrong network listed for seasons.
			# Eg: Black Mirror S06: Teletoon
			# Eg: Better Call Saul S05: Das Erste
			# Since TVDb does not list the network under seasons on their website, it is assumed that these values are probably not maintained anymore and can have a lot of incorrect values.
			# For seasons, always list TVDb last if it only contains a single network, which is cacluated per-season.
			networksSwitch = False
			networksTvdb = {}
			networksOther = {}
			for i in data['seasons']:
				network = networks.get(i.get('season'))
				if network:
					for j in network[1]:
						for k in j:
							try: networksTvdb[k] += 1
							except: networksTvdb[k] = 1
					for j in network[0]:
						for k in j:
							try: networksOther[k] += 1
							except: networksOther[k] = 1
			countTvdb = len(networksTvdb.keys())
			countOther = len(networksOther.keys())
			countAverage = len(data['seasons']) / 2
			if countOther == 1 and countTvdb > 2: networksSwitch = True
			elif countOther == 1 and countTvdb >= 1 and any(i in self.mTools.companySyndication() for i in networksTvdb.keys()): networksSwitch = True

			imagesMissing = False
			for i in range(len(data['seasons'])):
				season = data['seasons'][i]
				number = season['season']

				value = self.mTools.mergeGenre(genres.get(number))
				if not value and parentGenre: value = Tools.copy(parentGenre)
				if value: season['genre'] = value

				value = self.mTools.mergeLanguage(languages.get(number))
				if not value and parentLanguage: value = Tools.copy(parentLanguage)
				if value: season['language'] = value

				value = self.mTools.mergeCountry(countries.get(number))
				if not value and parentCountry: value = Tools.copy(parentCountry)
				if value: season['country'] = value

				# More info at _metadataShowUpdate().
				value = None
				network = networks.get(number)
				switch = networksSwitch
				if not switch:
					try:
						# Eg: Better Call Saul S05.
						# Eg: Black Mirror S06.
						# Only do this if the network does not appear frequently.
						# Eg: Vikings
						# Eg: Friends
						# Eg: Brooklyn Nine-Nine
						# Eg: Avatar Last Airbender
						if len(network[1][0]) == 1:
							countTvdb = networksTvdb.get(network[1][0][0], 0)
							countOther = networksOther.get(network[0][0][0], 0)
							if countTvdb <= countAverage: switch = True
							elif countOther >= countAverage and countTvdb < countOther: switch = True
					except: pass
				if network: value = self.mTools.mergeNetwork((network[1] + network[0]) if switch else (network[0] + network[1]), order = True, country = season.get('country')) # Different order if certain situations.
				if not value and parentNetwork: value = Tools.copy(parentNetwork)
				if value: season['network'] = value

				other = value # Must be right after networks.
				value = self.mTools.mergeStudio(studios.get(number), other = other, country = season.get('country'))
				if not value and parentStudio: value = Tools.copy(parentStudio)
				if value: season['studio'] = value

				value = self.mTools.mergeStatus(status.get(number))
				if value: season['status'] = value

				# If there is no time for S00 and S01, use the show's time.
				missing = False
				if number <= 1 and parentTime and not times.get(number):
					missing = True
					if not number in times: times[number] = []
					times[number].append(parentTime)
				value = self.mTools.mergeTime(times.get(number), metadata = season)
				if value:
					season['time'] = value

					# Some shows are only available on IMDb, but not other providers (eg: tt31566242, tt30346074).
					# These seasons often do not have a release date.
					# Add the date from the interpolated show date.
					if not season.get('premiered'):
						premiered = parentPremiere if missing else None
						if not premiered:
							premiered = value.get(MetaTools.TimePremiere)
							if premiered: premiered = Time.format(premiered, format = Time.FormatDate)
						if premiered:
							if not season.get('premiered'): season['premiered'] = premiered
							if not season.get('aired'): season['aired'] = premiered

				value = self.mTools.mergeDuration(durations.get(number))
				if value: season['duration'] = value

				value = self.mTools.mergeCertificate(mpaas.get(number), media = media)
				if not value and parentMpaa: value = Tools.copy(parentMpaa)
				if value: season['mpaa'] = value

				value = self.mTools.mergeCast(casts.get(number), show = parentCast)
				if value: season['cast'] = value

				value = self.mTools.mergeCrew(directors.get(number))
				if not value and parentDirector: value = Tools.copy(parentDirector)
				if value: data['director'] = value

				value = self.mTools.mergeCrew(writers.get(number))
				if not value and parentWriter: value = Tools.copy(parentWriter)
				if value: data['writer'] = value

				value = self.mTools.mergeCrew(creators.get(number))
				if not value and parentCreator: value = Tools.copy(parentCreator)
				if value: data['creator'] = value

				season['media'] = media

				niche = self.mTools.mergeNiche(niches.get(number))
				niche = self.mTools.niche(niche = niche, metadata = season, show = show, pack = pack)
				if niche: season['niche'] = niche

				if number in votings: season['voting'] = votings[number]

				# The season duration returned by providers is typically the duration of the first episode.
				# This can be off quite a lot from the average episode duration.
				# This then displays a large deviation for shows with a double-first-episode, or shows like eg Downton Abbey with a slightly longer first episode in each season.
				duration = pack.durationMean(season = number)
				if not duration: duration = season.get('duration')
				if not duration: duration = parentDuration # Eg: The Office UK S03 (IMDb)
				if duration: season['duration'] = Math.roundClosest(duration, base = 60) # Round to closest minute.

				if not season.get('tvshowtitle') and parentTitle: season['tvshowtitle'] = parentTitle

				# Unaired seasons often do not have a plot.
				if not season.get('plot') and parentPlot: season['plot'] = parentPlot

				data['seasons'][i] = {k : v for k, v in season.items() if not v is None}
				season = data['seasons'][i]

				# Always replace the IDs with new values.
				# Otherwise if there is an incorrect IMDb ID on Trakt/TMDb, it gets written to MetaCache.
				# At a later point the ID is corrected on Trakt/TMDb.
				# If the data is now refreshed, the old ID from MetaCache is used instead of the newly retrieved IDs.
				# Hence, always replace these.
				ids1 = season.get('id') or {}
				ids2 = show.get('id') or {}
				value = ids1.get('imdb') or ids2.get('imdb')
				if value: imdb = value
				value = ids1.get('tmdb') or ids2.get('tmdb')
				if value: tmdb = value
				value = ids1.get('tvdb') or ids2.get('tvdb')
				if value: tvdb = value
				value = ids1.get('trakt') or ids2.get('trakt')
				if value: trakt = value
				value = ids1.get('slug') or ids2.get('slug')
				if value: slug = value
				value = ids1.get('tvmaze') or ids2.get('tvmaze')
				if value: tvmaze = value
				value = ids1.get('tvrage') or ids2.get('tvrage')
				if value: tvrage = value

				# This is for legacy purposes, since all over Gaia the IDs are accessed at the top-level of the dictionary.
				# At some later point the entire addon should be updated to have the new ID structure.
				if not 'id' in season: season['id'] = {}
				if imdb: season['id']['imdb'] = season['imdb'] = imdb
				if tmdb: season['id']['tmdb'] = season['tmdb'] = tmdb
				if tvdb: season['id']['tvdb'] = season['tvdb'] = tvdb
				if trakt: season['id']['trakt'] = season['trakt'] = trakt
				if slug: season['id']['slug'] = season['slug'] = slug
				if tvmaze: season['id']['tvmaze'] = season['tvmaze'] = tvmaze
				if tvrage: season['id']['tvrage'] = season['tvrage'] = tvrage

				# Trakt sometimes returns new/unaired seasons that are not on TVDb.
				# This unique Trakt season does not have a show title, which will cause the season menu to be classified as "mixed" as the show title is added to the season label.
				if not 'tvshowtitle' in season and title: season['tvshowtitle'] = title

				if number in images and images[number]: MetaImage.update(media = MetaImage.MediaSeason, images = images[number], data = season, sort = providersImage)
				else: imagesMissing = True

				# Do this before here already.
				# Otherwise a bunch of regular expressions are called every time the menu is loaded.
				self.mTools.cleanPlot(metadata = season)

				# Calculate the rating here already, so that we have a default rating/votes if this metadata dictionary is passed around without being cleaned first.
				# More info under meta -> tools.py -> cleanVoting().
				self.mTools.cleanVoting(metadata = season, round = True) # Round to reduce storage space of average ratings with many decimal places.

			# Sort so that the list is in the order of the season numbers.
			data['seasons'].sort(key = lambda i : i['season'])

			# Set the show details.
			try: season = data['seasons'][1] # Season 1
			except:
				try: season = data['seasons'][0] # Specials
				except: season = None
			if imdb: data['imdb'] = imdb
			if tmdb: data['tmdb'] = tmdb
			if tvdb: data['tvdb'] = tvdb
			if trakt: data['trakt'] = trakt
			if slug: data['slug'] = slug
			if tvmaze: data['tvmaze'] = tvmaze
			if tvrage: data['tvrage'] = tvrage
			title = season['tvshowtitle'] if season and 'tvshowtitle' in season else None
			if title: data['tvshowtitle'] = data['title'] = title
			year = season['year'] if season and 'year' in season else None
			if year: data['year'] = year

			# Sometimes the images are not available, especially for new/future releases.
			# This looks ugly in the menus. Mark as incomplete to re-retrieve sooner.
			if imagesMissing:
				partDone = False
				try: partNew['tvdb']['complete'] = False
				except: pass
				try: partNew['fanart']['complete'] = False
				except: pass
				if developer: Logger.log('SEASON IMAGES INCOMPLETE: %s' % developer)

			Memory.set(id = id, value = data, local = True, kodi = False)
			if item and data: item.update(Tools.copy(data)) # Can be None if the ID was not found. Copy in case the outer item is edited before we write the data to MetaCache.

			if partDone:
				try: item[MetaCache.Attribute][MetaCache.AttributePart] = None
				except: pass
			else:
				partNew[MetaCache.AttributeFail] += 1
				data[MetaCache.Attribute] = {MetaCache.AttributePart : partNew}

			self._batchLoad(media = media, imdb = data.get('imdb'), tmdb = data.get('tmdb'), tvdb = data.get('tvdb'), trakt = data.get('trakt'))
			result.append(data)
		except:
			Logger.error()
		finally:
			if locks and id: locks[id].release()
			if semaphore: semaphore.release()
			self.mTools.busyFinish(media = media, item = item)

	def _metadataSeasonId(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None):
		result = self.mTools.idShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
		if result: return {'complete' : True, 'data' : {'id' : result}}
		else: return {'complete' : False, 'data' : result}

	def _metadataSeasonTrakt(self, trakt = None, imdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			# Do not use the cached summarized data. Only if it comes from IMDb.
			try: origin = bool(item['temp']['trakt'])
			except: origin = False

			if detail == MetaTools.DetailEssential and item and origin: # Comes from a Trakt list with basic metadata.
				if MetaCache.Attribute in item:
					result = {}
				else:
					result = Tools.copy(item)
					try: del result['temp']
					except: pass
				result = self._metadataTemporize(item = item, result = result, provider = 'trakt')
			else: # Comes from another list, or forcefully retrieve detailed metadata.
				id = trakt or imdb
				if id:
					# Trakt has an API limit of 1000 requests per 5 minutes.
					# Retrieving all the additional metadata will very quickly consume the limit if a few pages are loaded.
					# Only retrieve the extended metadata if enough requests are still avilable for the past 5 minutes.
					instance = MetaTrakt.instance()
					usagesAuthenticated = instance.usage(authenticated = True)
					usagesUnauthenticated = instance.usage(authenticated = False)

					person = False
					if detail == MetaTools.DetailExtended and usagesUnauthenticated < 0.3: person = True

					translation = None
					if detail == MetaTools.DetailEssential: translation = False # Use the translations from TVDb.

					# We already retrieve the cast (with thumbnails), translations and studios, from TMDb.
					# Retrieving all of them here again will add little new metadata and only prolong the retrieval.
					# translation = None: only retrieve for non-English.
					return instance.metadataSeason(id = id, summary = True, translation = translation, person = person, language = language, extended = True, detail = True, cache = cache, concurrency = bool(threaded))
		except: Logger.error()
		return {'provider' : 'trakt', 'complete' : complete, 'data' : result}

	def _metadataSeasonTvdb(self, tvdb = None, imdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		try: return MetaTvdb.instance().metadataSeason(imdb = imdb, tvdb = tvdb, language = language, cache = cache, threaded = threaded, detail = True)
		except: Logger.error()
		return {'provider' : 'tvdb', 'complete' : True, 'data' : None}

	def _metadataSeasonTmdb(self, tmdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		try: return MetaTmdb.instance().metadataSeason(tmdb = tmdb, language = language, cache = cache, threaded = threaded, detail = True)
		except: Logger.error()
		return {'provider' : 'tmdb', 'complete' : True, 'data' : None}

	def _metadataSeasonImdb(self, imdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			# A single IMDb season page is +- 190-250KB compressed.
			# There is no way to efficiently retrieve all/many seasons/episodes from IMDb, only one season at a time with up to 50 episodes per season.
			# Use this function conservatively, since it can make multiple requests, at retrieving too many IMDb pages in a short time can result in IMDb blocking requests.
			# Only retrieve few seasons if the item does not come from MetaCache, meaning it is newley loaded, and might be part of batch requests for Trakt Progress sync.

			instance = MetaImdb.instance()
			usage = instance.usage()

			new = True
			if item and item.get(MetaCache.Attribute, {}).get(MetaCache.AttributeStatus) in MetaCache.StatusValid: new = False

			season = []
			if item and item.get('seasons'):
				for i in item.get('seasons'):
					number = i.get('season')
					if not number is None: season.append(number)
			else:
				season = [i for i in range(10)]
			try: season.append(season.pop(0)) # Move the special seaosn to the back, since it typically does not exist on IMDb, and we want to retrieve it last.
			except: pass

			if new:
				if usage < 0.25: season = season[:4]
				elif usage < 0.50: season = season[:3]
				elif usage < 0.75: season = season[:2]
				elif usage < 0.90: season = season[:1]
				else: season = []
			else:
				if usage < 0.25: pass
				elif usage < 0.50: season = season[:20]
				elif usage < 0.75: season = season[:10]
				elif usage < 0.90: season = season[:5]
				else: season = []

			if season: result = instance.metadataSeason(id = imdb, season = season, language = language, cache = cache, threaded = threaded)
		except: Logger.error()
		return {'provider' : 'imdb', 'complete' : complete, 'data' : result}

	def _metadataSeasonFanart(self, tvdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			if tvdb:
				images = MetaFanart.show(tvdb = tvdb, season = True, cache = cache)
				if images is False: complete = False
				elif images:
					result = []
					for season, data in images.items():
						result.append({'season' : season, MetaImage.Attribute : data})
		except: Logger.error()
		return {'provider' : 'fanart', 'complete' : complete, 'data' : result or None}

	def _metadataSeasonAggregate(self, items, threaded = None):
		# Do not store duplicate or non-season data in the MetaCache database, otherwise too much unnecessary storage space will be used.
		# Check _metadataEpisodeAggregate() for more info.
		try:
			if items:
				values = items if Tools.isArray(items) else [items]
				if values and Tools.isArray(values[0]): values = Tools.listFlatten(values) # A list for mutiple shows, each containing a list of seasons.

				shows = []
				for item in values:
					try: shows.append({'imdb' : item.get('imdb'), 'tmdb' : item.get('tmdb'), 'tvdb' : item.get('tvdb'), 'trakt' : item.get('trakt')})
					except: Logger.error()
				shows = Tools.listUnique(shows)
				shows = self.metadataShow(items = shows, pack = False, threaded = threaded) if shows else None

				if shows:
					for item in values:
						try:
							imdb = item.get('imdb')
							tmdb = item.get('tmdb')
							tvdb = item.get('tvdb')
							trakt = item.get('trakt')
							for show in shows:
								if (imdb and show.get('imdb') == imdb) or (tmdb and show.get('tmdb') == tmdb) or (tvdb and show.get('tvdb') == tvdb) or (trakt and show.get('trakt') == trakt):
									# Add show images.
									if MetaImage.Attribute in show: MetaImage.update(media = MetaImage.MediaShow, images = Tools.copy(show[MetaImage.Attribute]), data = item, category = MetaImage.MediaShow)
									break
						except: Logger.error()
		except: Logger.error()
		return items

	##############################################################################
	# METADATA - EPISODE
	##############################################################################

	# NB: For efficiency, call this function with "pack=False" if the pack data is not needed. More info at metadata().
	# This function can be called in different ways, by either providing the individual parameters or using "items":
	#	1. Pass in a season: retrieve all episodes of that season.
	#		a. season = True: retrieve all episodes of all seasons of the show, including specials.
	#		b. season = False: retrieve all episodes of all seasons of the show, excluding specials.
	#	2. Pass in a season and episode: retrieve a specific episode based on the number.
	#	3. Pass in a season, episode, and limit: retrieve mutiple consecutive episodes, starting from the given number. A negative limit means retrieve up to the end of the season.
	#	4. Pass in a season, episode, and next: retrieve the next "unwatched" episode in the series, based on the parameters passed in and the Trakt playback history. Used for the Progress menu.
	def metadataEpisode(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, episode = None, number = None, items = None, pack = None, filter = None, clean = True, quick = None, refresh = False, cache = False, threaded = None, limit = None, next = None, discrepancy = None, special = SpecialExclude, aggregate = True, hierarchical = False, hint = None):
		try:
			media = Media.Episode

			packData = None
			packInstance = None
			packLookup = None

			pickSingle = False
			pickSingles = False
			pickMultiple = False
			pickSequential = number == MetaPack.NumberSequential or number == MetaPack.NumberAbsolute

			base = items
			numbering = None

			smart = False
			if next == MetaManager.Smart:
				next = True
				smart = True

			if items or (imdb or tmdb or tvdb or trakt) or title:
				if pickSequential and not items:
					numbering = episode
					if episode is True:
						season = False # All seasons, excluding specials.
						episode = None
					else:
						season = 1

				# Do a lookup in the pack data to get the real season/episode numbers.
				# Eg: looking up a sequential number to get the season/episode number for a later season.
				# Do not do for "next", since we do the lookup later after the number was incremented.
				if (pickSequential and not next) or (not items and not episode is None):
					lookup = items
					if not lookup and Tools.isInteger(season): lookup = {'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode}
					if lookup:
						packLookup = self._metadataPackLookup(items = lookup, number = number, threaded = threaded, quick = quick)
						if not items and (not numbering or Tools.isInteger(season)):
							season = lookup['season']
							episode = lookup['episode']
				elif items and Tools.isArray(items):
					# Progress menu's final metadata retrieval.
					# The progress/history might still have Trakt numbers, since they are too costly to convert in Playback if the user has a huge history.
					# Only lookup the numbers once a small subset of the items are loaded in the Progress menu page.
					# Eg: One Piece S02E63 (Trakt number).
					lookup = [i for i in items if Tools.get(i, MetaManager.Smart, 'external')] # 'external' if it comes from Trakt without numbers converted yet. Is set to None in metadataSmart() if already looked-up, so it does not have to be done here again.

					# Important to pass on "quick" here, when called from metadataSmart().
					# We do not want to generate a new pack if we are in quick mode.
					if lookup: packLookup = self._metadataPackLookup(items = lookup, number = MetaPack.ProviderTrakt, threaded = threaded, quick = quick)

				if items:
					if Tools.isArray(items):
						if 'episode' in items[0]: pickSingles = True
					else:
						pickSingle = True
						episode = items.get('episode')
						season = items.get('season')
						items = [items]

				elif not season is None and not episode is None and limit:
					items = []
					pickMultiple = True
					if not numbering and special is MetaManager.SpecialSettings: special = self.mTools.settingsShowInterleave()

					# Reduce the number of seasons to retrieve if they do not exist in the first place or if they are not included in the menu.
					packData = self.metadataPack(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, threaded = threaded)
					if packData: packInstance = MetaPack.instance(pack = packData)

					ranged = self._metadataEpisodeRange(pack = packInstance, season = season, episode = episode, limit = limit, number = number)
					if ranged:
						if special and not ranged.get('season').get('start') == 0: items.append({'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'title' : title, 'year' : year, 'season' : 0})
						items.extend([{'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'title' : title, 'year' : year, 'season' : i} for i in range(ranged.get('season').get('start'), ranged.get('season').get('end') + 1)])

				elif season is True or season is False:
					# Retrieve all episodes of all seasons for the show.
					# Used by library.py.
					items = []
					pickMultiple = True

					packData = self.metadataPack(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, threaded = threaded)
					if packData:
						packInstance = MetaPack.instance(pack = packData)
						total = packInstance.countSeasonTotal()
						if total:
							for i in range(total):
								if i == 0 and season is False: continue
								items.append({'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'title' : title, 'year' : year, 'season' : i})

				else:
					pickSingle = True
					if filter is None: filter = True

					if imdb or tmdb or tvdb or trakt: items = [{'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt}]
					elif title: items = self._metadataIdLookup(media = media, title = title, year = year, list = True)

					if items:
						items[0]['season'] = season
						if not episode is None: items[0]['episode'] = episode

						# This is used at the end of the function to remove sequential/absolute episodes from S01.
						# Update: Do not do this only for S01. We can also use this for the hint passed to _jobUpdate().
						# This takes about 150ms.
						# Update: The only reason why this takes so long is the call to MetaCache.settingsId() and Pool.settingMetadata() that is calculated here for the first time.
						# But this will be calculated eventually by some other call anyways, so this should not drastically increase time.
						if season == 1 or hint is True:
							packData = self.metadataPack(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, threaded = threaded)
							if packData: packInstance = MetaPack.instance(pack = packData)

				# UPDATE 1
				#	When there is a mistake calling this function with seasonLast or episodeLast being None, it screws up the metadata saved to the database.
				#	Eg: When calling _metadataEpisodeNext(..., season = None, episode = None), eg from binge(), typically the last season of the show this function was called on, contains all episodes of the show (similar to the Series/flattened menus).
				#	If seasonLast/episodeLast was set but is None, filter out those items.
				#	Not sure if there is any place where this function is called that actually wants None for seasonLast/episodeLast?
				# UPDATE 2
				#	Season can be None if called from MetaManager._episode().
				#	This is caused by a bug when the Series menu is opened, but loaded as an Episodes submenu instead of a Series submenu.
				#	Eg: change MetaTools._command() and replace "if not Tools.isString(submenu): submenu = MetaTools.SubmenuSerie" with "if not Tools.isString(submenu): submenu = MetaTools.SubmenuEpisode"
				#	Then open the Series menu on GoT. A bunch of metadata requests are made, which are all incorrect. And finally the incorrectly retrieved metadata of S08 is then written to metadata.db -> episodes.
				#	This should not happen under normal circumstances. But leave here in case this happens for other reasons.
				items = [item for item in items if not(item.get('season') is None and item.get('episode') is None)]

				# NB: Only execute this if-statement if we are not in quick mode.
				# Not sure if this is correct, or if there are some calls that actually require this part during quick?
				# Without checking quick here, if the Trakt progress list contains 100+ items, the Arrivals menu loads very slowly, since all items' metadata is retrieved here.
				# This also causes Kodi to crash often, once the threads run out and no new ones can be created.
				# UPDATE: Only do this if quick is not False, not if quick is True/integer. Otherwise, below where we retrieve the full metadata, the foreground/background threads fail in _metadataEpisodeUpdate(), since there is no incremented season number in the items yet.
				if next and not quick is False and items:
					itemsIncrement = None

					# This uses already incremented numbers from metadataSmart()
					# This allows faster Progress menu loading, by not having to do expensive increments every time the menu is laoded.
					# Only do the increment here, for items that do not have the next number set.
					# This can easily save 500-700ms for a Progress menu with 20 items.
					if smart:
						itemsIncrement = []
						itemsSingle = len(items) == 1
						current = Time.timestamp()
						for item in items:
							smart = item.get(MetaManager.Smart)
							# Only use this if the smart increment is not older than 3 months.
							# Otherwise if the smart increment was calculated with an old pack, newly released seasons/episodes might still have the old no-next-episode.
							# Do not make this too short, otherwise an item than was not updated in metadataSmart() for a while will hold up the process and make the menu slower.
							if smart and (current - (smart.get('time') or 0)) < 7776000:
								smart = smart.get('next')
								if smart:
									item['season'] = smart.get('season')
									item['episode'] = smart.get('episode')
									if itemsSingle:
										number = smart.get('number')
										if number: pickSequential = number == MetaPack.NumberSequential or number == MetaPack.NumberAbsolute
								elif not smart is False:
									itemsIncrement.append(item)
					else: # metadataEpisodeNext()
						itemsIncrement = items

					if itemsIncrement:
						lock = Lock()
						locks = {}
						semaphore = Semaphore(self.mTools.concurrency(media = media, hierarchical = hierarchical))

						if len(itemsIncrement) == 1:
							semaphore.acquire()
							item = itemsIncrement[0]
							numberNew = self._metadataEpisodeIncrement(item = item, number = number, lock = lock, locks = locks, semaphore = semaphore, cache = cache, threaded = threaded, discrepancy = discrepancy)
							if not number and numberNew:
								number = numberNew
								pickSequential = number == MetaPack.NumberSequential or number == MetaPack.NumberAbsolute
						else:
							threadsNext = []
							for item in itemsIncrement:
								semaphore.acquire()
								threadsNext.append(Pool.thread(target = self._metadataEpisodeIncrement, kwargs = {'item' : item, 'number' : number, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'cache' : cache, 'threaded' : threaded, 'discrepancy' : discrepancy}, start = True))
							[thread.join() for thread in threadsNext]

						# Check invalid: No more episodes available.
						# Check episode: _metadataEpisodeIncrement() can return without adding the 'invalid' attribute. Filter out all items without a valid episode number.
						# Update: Do not remove shows without a next episode (aka finished shows).
						# Otherwise some niche Progress menus are relativley empty. We simply move them to the end of the list during sorting.
						if smart:
							temp = []
							for item in items:
								invalid = False
								if item.get('invalid'): invalid = True
								if item.get('episode') is None: invalid = True
								else: temp.append(item)
								if invalid: self._metadataSmartUpdate(item = item, key = 'next', value = False)
							items = temp
						else: # metadataEpisodeNext()
							items = [i for i in items if not i.get('invalid') and not i.get('episode') is None]

						# Do the lookup here, after the numbers were incremented.
						packLookup = self._metadataPackLookup(items = items, threaded = threaded, quick = quick)
						if pickSingle and items:
							season = items[0].get('season')
							episode = items[0].get('episode')

				if items:
					if packInstance or (hint and not hint is True): hint = {'season' : items[0].get('season'), 'pack' : packInstance or hint} # Episodes fom a single show.
					elif len(items) > 1: hint = {'count' : len(items)} # Episodes fom mutiple shows.
					else: hint = None

					items = self._metadataCache(media = media, items = items, function = self._metadataEpisodeUpdate, quick = quick, refresh = refresh, cache = cache, threaded = threaded, hierarchical = hierarchical, hint = hint)

					if items:
						items = self._metadataFilter(media = media, items = items, filter = filter)
						items = self._metadataAggregate(media = media, items = items) # Must be before picking, since it uses temp and the internal "episodes" list.

						if items:
							picks = None
							if pickSingles:
								picks = []
								for item in items:
									if 'episodes' in item:
										for episode in item['episodes']:
											if episode['season'] == item['season'] and episode['episode'] == item['episode']:
												if not 'time' in episode: episode['time'] = {}
												for attribute in MetaTools.TimesTrakt: # Use the times for the last watched episode to add to the incremented episode for sorting of progress menus.
													try: episode['time'][attribute] = item['time'][attribute]
													except: pass
												picks.append(episode)
												break
							elif pickSingle:
								picks = []
								for item in items: picks.extend(item['episodes'])
								if not episode is None:
									temp = None
									for i in picks:
										if i['episode'] == episode:
											temp = i
											break
									picks = temp

							elif pickMultiple:
								picks = []

								# Remove sequential/absolute episodes from the Series menu.
								# Some providers might have the episodes in an absolute season, while others have the episodes listed under mutiple seasons.
								# Otherwise the same episode is listed twice, once as absolute number and once as season number.
								#	Eg: Dragon Ball Super.
								# Also do for Absolute menu, since seasons can have different episode counts between Trakt and TVDb.
								#	Eg: One Piece (3rd page - eg TVDb 3x16)
								if number == MetaPack.NumberSerie or number == MetaPack.NumberSequential:
									numberAll = {}
									for item in items:
										for i in item['episodes']:
											numberAll[(i.get('season'), i.get('episode'))] = True

									types = [MetaPack.NumberOfficial, MetaPack.NumberSpecial]
									if number == MetaPack.NumberSequential: types.append(MetaPack.NumberSequential)
									for item in items:
										for i in item['episodes']:
											type = packInstance.type(season = i.get('season'), episode = i.get('episode')) or {}

											# If type is None, it is an IMDb special (eg: Downton Abbey S02E09).
											# Allow unofficial specials (eg: One Piece S00E02 on TVDb, but not on Trakt).
											if (not type or any(type.get(j) for j in types)) and (not type.get(MetaPack.NumberUnofficial) or type.get(MetaPack.NumberSpecial)):
												# Sometimes TVDb has more episodes in a season than Trakt, which causes the TVDb number to clash with the sequential number.
												# Filter out these "unofficial" episodes, which might sometimes be labeled as "official", since they are the Trakt absolute numbers pointing to an episode in S02+.
												# Eg: Star Wars: Young Jedi Adventures
												if type.get(MetaPack.NumberOfficial) and i.get('season') == 1:
													numberStandard = tuple(packInstance.numberStandard(season = i.get('season'), episode = i.get('episode')))
													numberSequential = tuple(packInstance.numberSequential(season = i.get('season'), episode = i.get('episode')))
													if not numberStandard == numberSequential and numberSequential in numberAll: continue
												picks.append(i)
								else:
									for item in items: picks.extend(item['episodes'])
							else:
								picks = [item['episodes'] for item in items]

							items = picks

							# Must be called before filterNumber() below.
							# Do not do this for Series menus. If not doing this for Series menus causes some other issues, this can be removed again.
							# We do not do this for Series menus, since there might be clashes between sequential numbers and extra TVDb numbers.
							#	Eg: Star Wars: Young Jedi Adventures
							# 		The 2nd page of Series has an episode offset of S01E26.
							#		S01E26 can be a sequential number or the TVDb standard number for uncombined episodes.
							#		This makes the 2nd page have episodes: S01E26, S02E02, S02E03, ...
							#		Do not convert the numbers, so it stays at: S02E01, S02E02, S02E03, ...
							if not number == MetaPack.NumberSerie: self._metadataPackNumber(items = items, lookup = packLookup, season = season, episode = episode, numbering = numbering, number = number)

							if pickMultiple:
								# Filter here already, since the previous season might still be included in items.
								# This makes the detecting the first episode from the season in _metadataEpisodeSpecial() impossible.
								# Remove season-based episodes from the absolute menu (eg: check the last sequential menu page of Dragon Ball Super).
								if pickSequential:
									items = self.mTools.filterNumber(items = items, season = 1, episode = numbering, single = Media.Season)

									# For shows that have both sequential/absolute episodes and seasoned episodes (from different providers), the same absolute number might appear twice.
									# Once for the actual absolute episode, and once for the seasoned episode which number has been converted to absolute during _metadataPackNumber().
									# This makes the absolute episodes from S02+ appear after the last episode in the Absolute menu, creating an infinite cycle.
									# Eg: Dragon Ball Super (the last page of the Absolute menu).
									previous = 0
									for i in range(len(items)):
										numberEpisode = items[i].get('episode')
										if not numberEpisode == 0: # Allow IMDb specials.
											if numberEpisode < previous:
												items = items[:i] # Ignore everything after the largest absolute number.
												break
											else:
												previous = numberEpisode
								else:
									# This is important for Progress submenus where Trakt and TVDb have a very different season odering.
									# Eg: One Piece.
									try:
										if packInstance: numberSequential = packInstance.lookupSequential(season = season, episode = episode)
										if numberSequential: numberSequential = numberSequential[MetaPack.PartEpisode]
										else: numberSequential = 0

										sequentialFound = {}
										def _sequentialValid(item):
											# Always allow specials./ They get filtered out later on in _metadataEpisodeSpecial().
											if item.get('season') == 0 or item.get('episode') == 0: return True

											# The if-statement has 2 parts:
											# 1. (sequentialNumber >= numberSequential)
											#		Eg: One Piece: start the Progress submenu at S01E20, go to the next pages until we hit S02E01 as last item.
											#			Go to the next page and S02E17-S02E22 from TVDb are there.
											#			After S02E22, the episodes continue from S03E15 because of the aired date sorting in _metadataEpisodeSpecial() removed S03E01-S03E14.
											# 2. (not sequentialNumber in sequentialFound)
											#	Important to filter by duplicate sequential numbers here.
											#		Eg: One Piece S01E20.
											#	Progress menu starting at S01E20, going to the next page of the progress submenu will list both S01 and S02 episodes.
											#		Eg: One Piece S01E26 and S02E18 are both the same episode (S01E26 from Trakt and S02E18 from TVDb).
											#	Remove these "duplicate" episodes based on their sequential number.

											try: sequentialNumber = item['number'][MetaPack.NumberSequential][MetaPack.PartEpisode]
											except: sequentialNumber = 0
											if (sequentialNumber >= numberSequential) and (not sequentialNumber in sequentialFound):
												sequentialFound[sequentialNumber] = True
												return True
											else:
												# Allow IMDb specials.
												# Eg: Downton Abbey S02E09.
												try: imdbNumber = item['number'][MetaPack.ProviderImdb][MetaPack.NumberStandard][MetaPack.PartSeason]
												except: imdbNumber = None
												if imdbNumber:
													try: traktNumber = item['number'][MetaPack.ProviderTrakt][MetaPack.NumberStandard][MetaPack.PartSeason]
													except: traktNumber = None
													try: tvdbNumber = item['number'][MetaPack.ProviderTvdb][MetaPack.NumberStandard][MetaPack.PartSeason]
													except: tvdbNumber = None
													if not traktNumber and not tvdbNumber: return True
											return False

										items = [i for i in items if _sequentialValid(i)]
									except: Logger.error()

									items = self.mTools.filterNumber(items = items, season = season, episode = episode)

								if special: items = self._metadataEpisodeSpecial(items = items, special = special, season = season, episode = episode, number = number, pack = packInstance)

							# Still add IMDb specials to the sequential menu, which do not have an actual sequential number (S01E00).
							# Eg: Downton Abbey S02E09.
							# Eg: Star Trek (1966) S01E00.
							# Change the numbers AFTER filterNumber() above.
							if pickSequential and items:
								for item in items if Tools.isArray(items) else [items]:
									if not item.get('episode') and not packInstance.numberEpisode(item = item, number = number):
										numberSeason = packInstance.numberStandardSeason(item = item)
										numberEpisode = packInstance.numberStandardEpisode(item = item)
										if not numberSeason is None and not numberEpisode is None:
											item['sequential'] = True # Use by MetaTools.label().
											item['season'] = numberSeason
											item['episode'] = numberEpisode

							items = self._metadataPackAggregate(items = items, data = packData, pack = pack, quick = quick, cache = cache, threaded = threaded) # Do not add "refresh" here, otherwise the pack will be refreshed every time a season is refreshed.

							# For Progress menus, the episode aggregation can take very long (1.0-1.5 secs).
							# This data is not really needed for any of the menu's functionality. Or is it?
							# Still do season aggregation, since we want the show poster for the menu.
							if aggregate:
								if next: items = self._metadataSeasonAggregate(items = items, threaded = threaded)
								else: items = self._metadataEpisodeAggregate(items = items, threaded = threaded)

							# Add the smart data back, needed for sorting later on.
							# This is also important for _metadataSmartLoad() for episode Progress menus.
							# Since all episodes of a season are retrieved from the database in one go, the dictionaries returned by this function are not the same dictionaries passed into the function.
							# Hence, the items returned by this function will not have the original attributes from the p[assed in items.]
							if smart: items = self._metadataSmartAggregate(media = media, items = items, base = base)

							items = self._metadataClean(media = media, items = items, clean = clean)

							return items
		except: Logger.error()
		return None

	#gaiafuture - make this function work with storyline specials. Ask the user during binge if they want to play the special or continue with the next official episode (eg: Downton Abbey S02E09/S00E02).
	def metadataEpisodeNext(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, episode = None, number = None, pack = None, released = True):
		try:
			item = {'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'title' : title, 'year' : year, 'season' : season, 'episode' : episode}

			# NB: discrepancy = False
			# If an entire season was previously watched. Then the 1st three episodes are watched a second time.
			# The next day, the user wants to watch E02 (and E03) again, since they fell asleep after E01.
			# Otherwise when checking discrepancies, Gaia will throw an error during playback, saying no more episodes available for binge watching.
			item = self.metadataEpisode(items = item, number = number, pack = pack, next = True, discrepancy = False)

			if item:
				premiered = None
				if not premiered and 'premiered' in item: premiered = item['premiered']
				if not premiered and 'aired' in item: premiered = item['aired']
				if not released or not premiered or Time.integer(premiered) <= Time.integer(Time.past(hours = 3, format = Time.FormatDate)): return item
		except: Logger.error()
		return None

	def _metadataEpisodeUpdate(self, item, result = None, lock = None, locks = None, semaphore = None, cache = False, threaded = None, mode = None, part = True):
		try:
			media = Media.Episode

			imdb = item.get('imdb')
			tmdb = item.get('tmdb')
			tvdb = item.get('tvdb')
			trakt = item.get('trakt')
			slug = item.get('slug')
			tvmaze = item.get('tvmaze')
			tvrage = item.get('tvrage')

			title = item.get('tvshowtitle') or item.get('title')
			year = item.get('year')
			numberSeason = originalSeason = item.get('season')

			# By default we do not cache requests to disc, since it takes longer and requires more storage space.
			# If the same show appears multiple times in the list (some Trakt lists, eg watched list where a show was watched twice), sub-requests will also have to be executed multiple times, since they are not disc-cached.
			# Cache in memory and use locks to block subsequent calls with the same ID/title until the first request is done and then use those results without executing all the code again.
			id = Memory.id(media = Media.Episode, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = numberSeason)
			if not locks is None:
				if not id in locks:
					lock.acquire()
					if not id in locks: locks[id] = Lock()
					lock.release()
				locks[id].acquire()
				data = Memory.get(id = id, uncached = True, local = True, kodi = False)
				if Memory.cached(data):
					if data: item.update(Tools.copy(data)) # Copy in case the memory is used mutiple times. Can be None if not found.
					return None

			# Previous incomplete metadata.
			partDone = True
			partOld = {}
			partNew = {MetaCache.AttributeFail : 0}
			if part:
				try:
					partCache = item.get(MetaCache.Attribute)
					if partCache and partCache.get(MetaCache.AttributeStatus) == MetaCache.StatusIncomplete:
						partOld = partCache.get(MetaCache.AttributePart) or {}
						partNew[MetaCache.AttributeFail] = partOld.get(MetaCache.AttributeFail, 0)
				except: Logger.error()

			# Trakt requires either a Trakt or IMDb ID.
			# TMDb requires a TMDb ID.
			if not tvdb or (not imdb and not trakt) or (self.mLevel >= 2 and not tmdb):
				ids = partOld.get('id')
				if not ids or not ids.get('complete'): ids = self._metadataEpisodeId(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
				partNew['id'] = ids
				if ids:
					if not ids.get('complete'): partDone = False
					ids = ids.get('data')
					if ids:
						ids = ids.get('id')
						if ids:
							if not imdb: imdb = ids.get('slug')
							if not tmdb: tmdb = ids.get('tmdb')
							if not tvdb: tvdb = ids.get('tvdb')
							if not trakt: trakt = ids.get('trakt')
							if not slug: slug = ids.get('slug')
							if not tvmaze: tvmaze = ids.get('tvmaze')
							if not tvrage: tvrage = ids.get('tvrage')
			if not imdb and not tmdb and not tvdb and not trakt: return False

			developer = self._metadataDeveloper(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, item = item, season = numberSeason)
			if developer: Logger.log('EPISODE METADATA RETRIEVAL [%s]: %s' % (mode.upper() if mode else 'UNKNOWN', developer))

			show = self.metadataShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, pack = False, threaded = threaded)
			if not show:
				Memory.set(id = id, value = {}, local = True, kodi = False)
				return False

			season = self.metadataSeason(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = numberSeason, pack = False, threaded = threaded, hint = {'pack' : show.get('packed')})
			if not season:
				Memory.set(id = id, value = {}, local = True, kodi = False)
				return False

			pack = self.metadataPack(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, threaded = threaded)
			pack = MetaPack.instance(pack = pack)

			cache = cache if cache else None

			# count = number of episodes.
			# DetailEssential: (count + 3) requests (eg: 10 episodes = 13 requests) [Trakt: 1 (summary), TVDb: 3-count (show summary, season summary, each episode), TMDb: 0, IMDb: 0]
			# DetailStandard: (count + 3) requests (eg: 10 episodes = 13 requests) [Trakt: 1 (summary), TVDb: 3-count (show summary, season summary, each episode), TMDb: 0, IMDb: 0]
			# DetailExtended: (2*count + 5) requests (eg: 10 episodes = 25 requests) [Trakt: 2-count (summary, people for each episode), TVDb: 3-count (show summary, season summary, each episode), TMDb: 1 (summary), IMDb: 1 (summary)]
			requests = []
			if self.mLevel >= 0:
				requests.append({'id' : 'trakt', 'function' : self._metadataEpisodeTrakt, 'parameters' : {'trakt' : trakt, 'imdb' : imdb, 'season' : numberSeason, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				requests.append({'id' : 'tvdb', 'function' : self._metadataEpisodeTvdb, 'parameters' : {'tvdb' : tvdb, 'imdb' : imdb, 'season' : numberSeason, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				requests.append({'id' : 'imdb', 'function' : self._metadataEpisodeImdb, 'parameters' : {'imdb' : imdb, 'season' : numberSeason, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				if self.mLevel >= 2:
					requests.append({'id' : 'tmdb', 'function' : self._metadataEpisodeTmdb, 'parameters' : {'tmdb' : tmdb, 'season' : numberSeason, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})

			partDatas = {}
			if partOld:
				partRequests = []
				for i in requests:
					partData = partOld.get(i['id'])
					if partData and partData.get('complete'): partDatas[i['id']] = partData
					else: partRequests.append(i)
				requests = partRequests
				partDatas = Tools.copy(partDatas) # Copy inner dicts that can be carried over with the update() below.

			datas = self._metadataRetrieve(requests = requests, threaded = threaded)
			datas.update(partDatas)

			data = {'episodes' : []}
			niches = {}
			genres = {}
			studios = {}
			networks = {}
			languages = {}
			countries = {}
			status = {}
			times = {}
			durations = {}
			mpaas = {}
			images = {}
			votings = {}
			casts = {}
			directors = {}
			writers = {}
			creators = {}
			voting = {
				'rating' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
				'votes' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
			}

			# Create a specific order for the providers to update the metadata with.
			# MetaPack will determine the "best" order, typically based on which provider has more episodes.
			# Eg: GoT (TVDb vs Trakt) S00E56 and S00E57.
			# Eg: "Star Wars: Young Jedi Adventures" with combined/uncombined episodes. But in this case TVDb has more (uncombined) episdodes than Trakt in any case.
			providers = ['metacritic']
			support = pack.support(season = numberSeason)
			if support:
				if 'tmdb' in support: support = [i for i in support if not i == 'tmdb'] + ['tmdb'] # Always use TVDb above TMDb, even if TMDb has more episodes in the season.
				providers.extend(reversed(support))
			if not 'imdb' in providers: providers.insert(providers.index('metacritic') + 1, 'imdb')
			if not 'tmdb' in providers: providers.insert(providers.index('imdb') + 1, 'tmdb')
			if not 'fanart' in providers: providers.insert(providers.index('tmdb') + 1, 'fanart')
			if not 'trakt' in providers: providers.append('trakt')
			if not 'tvdb' in providers: providers.append('tvdb')
			providersImage = providers[::-1] # Preferred providers must be placed first.

			# Add Fanart and map to TVDb, since it uses TVDb IDs and numbering.
			# Allow additional episodes from IMDb that are not on TVDb/TMDb/Trakt (eg: IMDb Downton Abbey S02E09, which is a special elsewhere).
			def _lookupImdb(numberSeason, numberEpisode, episode, episodes, pack):
				try:
					title = episode.get('title')

					if not 'number' in episode: episode['number'] = {}
					episode['number']['imdb'] = {MetaPack.NumberStandard : [numberSeason, numberEpisode]}

					# Only do search() with expensive title matching if the episode count differs.
					# Otherwise assume the IMDb numbering is correct.
					if title and pack:
						if not pack.countEpisode(season = numberSeason) == len(episodes):
							# Only match current season and specials.
							# Allow for "lenient" matching if the strict matching did not return a result.
							# This allows for titles that do not have a perfect match. Eg: Downton Abbey S06E09 ("Christmas Special") vs S00E11 ("Christmas Day").
							match = pack.search(title = title, season = [numberSeason, 0], lenient = True)
							if match:
								actualSeason = pack.numberStandardSeason(item = match)
								actualEpisode = pack.numberStandardEpisode(item = match)
								if actualSeason == numberSeason:
									numberEpisode = actualEpisode
								else:
									# Special elsewhere (eg: Downton Abbey S02E09).
									# Add the other numbers to the episode, so a notification can be shown during scraping that the episode might also be available under a different number.
									number = pack.number(season = actualSeason, episode = actualEpisode, number = False)
									if number:
										episode['number'].update(number)
										episode['number'][MetaPack.NumberStandard] = [numberSeason, numberEpisode]
				except: Logger.error()
				return numberSeason, numberEpisode
			providersLookup = {'trakt' : 'trakt', 'tvdb' : 'tvdb', 'tmdb' : 'tmdb', 'fanart' : 'tvdb', 'imdb' : _lookupImdb}

			for i in providers:
				if i in datas:
					values = datas[i]
					if values:
						if not Tools.isArray(values): values = [values]
						for value in values:
							if not value['complete']:
								partDone = False
								if developer: Logger.log('EPISODE METADATA INCOMPLETE [%s]: %s' % (i.upper(), developer))

							provider = value['provider']

							# Use "provider", not "i", since IMDb also has Metacritic data.
							# NB: Important to copy, since the dict is edited below.
							# Otherwise we edit the dict before it gets (possibly) written as partial data to MetaCache.
							# Eg: TVDb fails or has no data yet (new release). The TMDb images get deleted below, and the TMDb is later added as partial data to MetaCache. The next time the partial metadata is refreshed, the TMDb data is used, but now does not have images anymore, causing the poster to be missing in the menus.
							# This mostly happens with new releases. Either TMDb/TVDb/Trakt has not listed it yet, or Trakt has the wrong TMDb/TVDb ID.
							partNew[provider] = Tools.copy(value)

							episodes = value['data']
							if episodes:
								episodes = Tools.copy(episodes) # Copy, since we do title/plot/studio replacement below in another loop.
								for episode in episodes:
									numberSeason = episode['season']
									numberEpisode = episode['episode']

									# Lookup the real Gaia season/episode number using the provider's native number.
									# This ensures that the correct dicts are updated with each other if the numbers differ on some.
									# If there is no lookup for the current provider (eg: IMDb), continue by assuming their numbering is correct.
									lookup = providersLookup.get(i)
									if lookup:
										if Tools.isFunction(lookup):
											numberSeason, numberEpisode = lookup(numberSeason = numberSeason, numberEpisode = numberEpisode, episode = episode, episodes = episodes, pack = pack)
										else:
											# For instance, if Trakt uses absolute episode numbering within standard seasons.
											# Eg: One Piece (Anime) - S22E1089 instead of S22E01.
											lookuped = pack.lookupStandard(season = numberSeason, episode = numberEpisode, input = lookup)

											# If a single Trakt absolute numbering maps to a TVDb multi-season numbering, stick to the Trakt absolute numbers.
											# Eg: Dragon Ball Supper - should have 131 episodes in S01 (absolute).
											if lookuped and not lookuped[0] is None and not lookuped[0] == numberSeason:
												lookuped = pack.lookup(season = numberSeason, episode = numberEpisode, input = MetaPack.NumberStandard, output = lookup)
												if lookuped and not lookuped[0] is None and not lookuped[0] == numberSeason: lookuped = None

											if lookuped and not lookuped[0] is None:
												if developer and not(numberSeason == lookuped[0] and numberEpisode == lookuped[1]): Logger.log('EPISODE NUMBER MAPPING [%s]: S%02dE%02d -> S%02dE%02d (%s)' % (i.upper(), numberSeason, numberEpisode, lookuped[0], lookuped[1], developer))

												numberSeason = lookuped[0]
												numberEpisode = lookuped[1]

												# Change these numbers, otherwise they are added twice to the season menu, once for the standard number and once for the alternative/absolute number.
												# Eg One Piece (Anime) - S22E01 vs S22E1089.
												episode['season'] = lookuped[0]
												episode['episode'] = lookuped[1]
											else:
												# The pack might be outdated and not have newley aired episodes yet.
												# Do not reject these new episodes if they cannot be found in the pack.
												# Only reject them if they are specials, or if the number of episodes in the pack is greater than the number in the current provider season.
												if numberSeason == 0 or pack.countEpisodeOfficial(season = numberSeason) > len(episodes):
													if developer: Logger.log('EPISODE NUMBER INVALID [%s]: S%02dE%02d (%s)' % (i.upper(), numberSeason, numberEpisode, developer))
													continue # Eg: GoT S00E56/S00E57 on TVDb that do not exist on Trakt/TMDb. Trakt/TMDb have different specials under that number, and do not have them under any other number.

									if MetaImage.Attribute in episode:
										if not numberSeason in images: images[numberSeason] = {}
										if not numberEpisode in images[numberSeason]: images[numberSeason][numberEpisode] = {}
										images[numberSeason][numberEpisode] = Tools.update(images[numberSeason][numberEpisode], episode[MetaImage.Attribute], none = False, lists = True, unique = False)
										del episode[MetaImage.Attribute]

									if 'niche' in episode:
										if not numberSeason in niches: niches[numberSeason] = {}
										if not numberEpisode in niches[numberSeason]: niches[numberSeason][numberEpisode] = []
										niches[numberSeason][numberEpisode].append(episode['niche'])
									if 'genre' in episode:
										if not numberSeason in genres: genres[numberSeason] = {}
										if not numberEpisode in genres[numberSeason]: genres[numberSeason][numberEpisode] = []
										genres[numberSeason][numberEpisode].append(episode['genre'])
									if 'studio' in episode:
										if not numberSeason in studios: studios[numberSeason] = {}
										if not numberEpisode in studios[numberSeason]: studios[numberSeason][numberEpisode] = []
										studios[numberSeason][numberEpisode].append(episode['studio'])
									if 'network' in episode:
										if not numberSeason in networks: networks[numberSeason] = {}
										if not numberEpisode in networks[numberSeason]: networks[numberSeason][numberEpisode] = [[], []]
										networks[numberSeason][numberEpisode][1 if i == 'tvdb' else 0].append(episode['network'])
									if 'language' in episode:
										if not numberSeason in languages: languages[numberSeason] = {}
										if not numberEpisode in languages[numberSeason]: languages[numberSeason][numberEpisode] = []
										languages[numberSeason][numberEpisode].append(episode['language'])
									if 'country' in episode:
										if not numberSeason in countries: countries[numberSeason] = {}
										if not numberEpisode in countries[numberSeason]: countries[numberSeason][numberEpisode] = []
										countries[numberSeason][numberEpisode].append(episode['country'])
									if 'status' in episode:
										if not numberSeason in status: status[numberSeason] = {}
										if not numberEpisode in status[numberSeason]: status[numberSeason][numberEpisode] = []
										status[numberSeason][numberEpisode].append(episode['status'])
									if 'time' in episode:
										if not numberSeason in times: times[numberSeason] = {}
										if not numberEpisode in times[numberSeason]: times[numberSeason][numberEpisode] = []
										times[numberSeason][numberEpisode].append(episode['time'])
									if 'duration' in episode:
										if not numberSeason in durations: durations[numberSeason] = {}
										if not numberEpisode in durations[numberSeason]: durations[numberSeason][numberEpisode] = []
										durations[numberSeason][numberEpisode].append(episode['duration'])
									if 'mpaa' in episode:
										if not numberSeason in mpaas: mpaas[numberSeason] = {}
										if not numberEpisode in mpaas[numberSeason]: mpaas[numberSeason][numberEpisode] = []
										mpaas[numberSeason][numberEpisode].append(episode['mpaa'])

									if episode.get('cast'):
										if not numberSeason in casts: casts[numberSeason] = {}
										if not numberEpisode in casts[numberSeason]: casts[numberSeason][numberEpisode] = []
										casts[numberSeason][numberEpisode].append(episode['cast'])
									if episode.get('director'):
										if not numberSeason in directors: directors[numberSeason] = {}
										if not numberEpisode in directors[numberSeason]: directors[numberSeason][numberEpisode] = []
										directors[numberSeason][numberEpisode].append(episode['director'])
									if episode.get('writer'):
										if not numberSeason in writers: writers[numberSeason] = {}
										if not numberEpisode in writers[numberSeason]: writers[numberSeason][numberEpisode] = []
										writers[numberSeason][numberEpisode].append(episode['writer'])
									if episode.get('creator'):
										if not numberSeason in creators: creators[numberSeason] = {}
										if not numberEpisode in creators[numberSeason]: creators[numberSeason][numberEpisode] = []
										creators[numberSeason][numberEpisode].append(episode['creator'])

									if not numberSeason in votings: votings[numberSeason] = {}
									if not numberEpisode in votings[numberSeason]: votings[numberSeason][numberEpisode] = Tools.copy(voting)
									if 'rating' in episode: votings[numberSeason][numberEpisode]['rating'][provider] = episode['rating']
									if 'votes' in episode: votings[numberSeason][numberEpisode]['votes'][provider] = episode['votes']
									if 'userrating' in episode: votings[numberSeason][numberEpisode]['user'][provider] = episode['userrating']

									# NB: Use the "update" dict below to replace the updated episode numbers, and only add the episode if "numberSeason == originalSeason".
									# Otherwise an episode that is originally from a different season (eg S0), will be used to update the dict (and numbers) and add it to the episode list.
									# Eg: The Office (India) - TVDb has the pilot as S00E01 while Trakt/TMDb has it as S01E01 and therefore also one more episode in the season.
									# Without the "update" replacement, the TVDb S00E01 will replace the numbering of the episode of S01E01 to now have S00E01 numbers, which we do not want. It will then also add an extra episode, so that the season has 14 instead of the correct 13.
									found = False
									for j in data['episodes']:
										if j['season'] == numberSeason and j['episode'] == numberEpisode:
											found = True
											update = None
											if not episode['season'] == numberSeason or not episode['episode'] == numberEpisode:
												update = {
													'season' : j['season'],
													'episode' : j['episode'],
													'number' : j['number'],
												}
											Tools.update(j, episode, none = False, lists = False, unique = False)
											if update: j.update(update)
											break
									if not found and numberSeason == originalSeason: data['episodes'].append(episode)

			# Special episodes that are on Trakt, but not on TVDb, might not have certain attributes.
			attributes = ['studio', 'genre', 'country', 'cast']
			values = {i : {} for i in attributes}
			for episode in data['episodes']:
				for attribute in attributes:
					if attribute in episode and episode[attribute]:
						if episode['season'] in values[attribute]:
							if len(str(values[attribute][episode['season']])) > len(str(episode[attribute])): continue
						values[attribute][episode['season']] = episode[attribute]

			# Use the average duration of episodes in the season if an episode does not have a duration.
			# Eg: Downton Abbey S06E09 - special which is only on IMDb. TMDb/TVDb/Trakt list it under the specials season.
			parentDuration = season.get('duration')
			if not parentDuration:
				parentDuration = [i.get('duration') for i in data['episodes']]
				parentDuration = [i for i in parentDuration if i]
				if parentDuration: parentDuration = int(sum(parentDuration) / float(len(parentDuration)))
				else: parentDuration = None

			# Some attributes might be missing. Use the show/season attributes.
			# Eg: Most episodes, if not all, do not have a studio.
			parentTitle = show.get('tvshowtitle')
			parentNetwork = season.get('network') or show.get('network')
			parentStudio = season.get('studio') or show.get('studio')
			parentLanguage = season.get('language') or show.get('language')
			parentCountry = season.get('country') or show.get('country')
			parentGenre = season.get('genre') or show.get('genre')
			parentMpaa = season.get('mpaa') or show.get('mpaa')
			parentCastShow = show.get('cast')
			parentCastSeason = season.get('cast')
			parentDirector = season.get('director') or show.get('director')
			parentWriter = season.get('writer') or show.get('writer')
			parentCreator = season.get('creator') or show.get('creator')
			parentPremiere = season.get('premiered') or season.get('aired')
			parentTime = season.get('time')

			lastImdb = None
			try:
				dataImdb = datas.get('imdb')
				if dataImdb:
					for i in dataImdb if Tools.isArray(dataImdb) else [dataImdb]:
						if i.get('provider') == 'imdb':
							values = i.get('data')
							if values: lastImdb = values[-1].get('episode')
							break
			except: Logger.error()
			if not lastImdb: lastImdb = -1

			imagesMissing = False
			for i in range(len(data['episodes'])):
				episode = data['episodes'][i]
				numberSeason = episode.get('season')
				numberEpisode = episode.get('episode')

				# Use the numbers from the pack, since the mapping between providers might have changed them.
				# Create default numbering, in case something is not available in the pack.
				if not 'number' in episode: episode['number'] = {}
				number = episode['number']

				if not MetaPack.NumberStandard in number: number[MetaPack.NumberStandard] = [numberSeason, numberEpisode]
				if not MetaPack.NumberSequential in number: number[MetaPack.NumberSequential] = [1, episode.get('sequential') or 0] # "or 0" for IMDb specials.
				if not MetaPack.NumberAbsolute in number: number[MetaPack.NumberAbsolute] = [1, episode.get('absolute') or 0]

				# Use the IDs from the pack, since the mapping between providers might have changed them.
				if pack:
					# Do not retrieve using pack.number(), since it will use NumberUniversal for lookups, which might not always match with NumberStandard.
					# Eg: Star Wars: Young Jedi Adventures S01E26 (NumberUniversal sees this as absolute, mapping to S02E01, while NumberStandard will retrieve the TVDb uncombined episode S01E26).
					#numbers = pack.number(season = numberSeason, episode = numberEpisode, number = False)
					entry = pack.episode(season = numberSeason, episode = numberEpisode, number = MetaPack.NumberStandard)
					numbers = entry.get(MetaPack.ValueNumber) if entry else None

					if numbers:
						numberStandard = numbers.get(MetaPack.NumberStandard)

						# Only replace if the season matches the requested season.
						# Otherwise episodes that map top another season might be added.
						# Eg: Star Wars: Young Jedi Adventures S01E26-S01E50 - uncombined S01 from TVDb clash with the absolute numbers from Trakt that uses combined episodes.
						if not numberStandard is None and numberStandard[0] == originalSeason:
							episode['season'] = numberSeason = numberStandard[0]
							episode['episode'] = numberEpisode = numberStandard[1]
						try: del episode['absolute'] # Delete the absolute number, to force extracting it from the "number" dictionary.
						except: pass

						Tools.update(episode['number'], numbers, none = False, lists = False, unique = False)

					idsEpisode = pack.id(season = numberSeason, episode = numberEpisode)
					if not 'id' in episode: episode['id'] = {}
					ids = pack.id(season = numberSeason)
					if ids:
						if not 'season' in episode['id']: episode['id']['season'] = {}
						Tools.update(episode['id']['season'], ids, none = False, lists = False, unique = False)
					ids = pack.id(season = numberSeason, episode = numberEpisode)
					if ids:
						if not 'episode' in episode['id']: i['id']['episode'] = {}
						Tools.update(episode['id']['episode'], ids, none = False, lists = False, unique = False)

					# Add reduced pack data for things like the episode type.
					episode['packed'] = pack.reduce(season = numberSeason, episode = numberEpisode)

				# Add missing IMDb numbers which are not avilable from the pack.
				# Only do this if IMDb was found, since IMDb might use absolute numbers and would not find anything on a season level.
				# Eg: One Piece S02.
				# Ignore episode numbers that do not match.
				# Eg: Star Wars: Young Jedi Adventures S01E26.
				if numberEpisode <= lastImdb:
					try: numberImdb = number[MetaPack.ProviderImdb][MetaPack.NumberSequential][MetaPack.PartEpisode]
					except: numberImdb = None
					if numberImdb is None:
						if not MetaPack.ProviderImdb in number: number[MetaPack.ProviderImdb] = {}
						for j in [MetaPack.NumberStandard, MetaPack.NumberSequential]: number[MetaPack.ProviderImdb][j] = Tools.copy(number.get(j))

				# Special episodes that are on Trakt, but not on TVDb, might not have certain attributes.
				for attribute in attributes:
					if not attribute in episode or not episode[attribute]:
						try: episode[attribute] = values[attribute][numberSeason]
						except: pass

				value = self.mTools.mergeGenre(genres.get(numberSeason, {}).get(numberEpisode))
				if not value and parentGenre: value = Tools.copy(parentGenre)
				if value: episode['genre'] = value

				value = self.mTools.mergeLanguage(languages.get(numberSeason, {}).get(numberEpisode))
				if not value and parentLanguage: value = Tools.copy(parentLanguage)
				if value: episode['language'] = value

				value = self.mTools.mergeCountry(countries.get(numberSeason, {}).get(numberEpisode))
				if not value and parentCountry: value = Tools.copy(parentCountry)
				if value: episode['country'] = value

				# More info at _metadataShowUpdate().
				value = None
				network = networks.get(numberSeason, {}).get(numberEpisode)

				# For specials, TVDb often has the wrong network.
				# Eg: One Piece has half the episodes marked as BBC One.
				# If only TVDb has a network, rather default to the season network.
				# Otherwise in Series/Progress menus, interleaved specials cause a different studio icon to pop up, which is noticeable when scrolling.
				if numberSeason == 0 and network and len(network[0]) == 0 and len(network[1]) == 1: network = None

				if network: value = self.mTools.mergeNetwork(network[0] + network[1], order = True, country = episode.get('country'))
				if not value and parentNetwork: value = Tools.copy(parentNetwork)
				if value: episode['network'] = value

				other = value # Must be right after networks.
				value = self.mTools.mergeStudio(studios.get(numberSeason, {}).get(numberEpisode), country = episode.get('country'), other = other)
				if not value and parentStudio: value = Tools.copy(parentStudio)
				if value: episode['studio'] = value

				value = self.mTools.mergeStatus(status.get(numberSeason, {}).get(numberEpisode))
				if value: episode['status'] = value

				# If there is no time for E00 and E01, use the season's time.
				missing = False
				if numberEpisode <= 1 and parentTime and not times.get(numberSeason, {}).get(numberEpisode):
					missing = True
					if not numberSeason in times: times[numberSeason] = {}
					if not numberEpisode in times[numberSeason]: times[numberSeason][numberEpisode] = []
					times[numberSeason][numberEpisode].append(parentTime)
				value = self.mTools.mergeTime(times.get(numberSeason, {}).get(numberEpisode), metadata = episode)
				if value:
					episode['time'] = value

					# Some shows are only available on IMDb, but not other providers (eg: tt31566242, tt30346074).
					# These seasons often do not have a release date.
					# Add the date from the interpolated show date.
					if not episode.get('premiered'):
						premiered = parentPremiere if missing else None
						if not premiered:
							premiered = value.get(MetaTools.TimePremiere)
							if premiered: premiered = Time.format(premiered, format = Time.FormatDate)
						if premiered:
							if not episode.get('premiered'): episode['premiered'] = premiered
							if not episode.get('aired'): episode['aired'] = premiered

				value = self.mTools.mergeDuration(durations.get(numberSeason, {}).get(numberEpisode))
				if value: episode['duration'] = value

				value = self.mTools.mergeCertificate(mpaas.get(numberSeason, {}).get(numberEpisode), media = media)
				if not value and parentMpaa: value = Tools.copy(parentMpaa)
				if value: episode['mpaa'] = value

				value = self.mTools.mergeCast(casts.get(numberSeason, {}).get(numberEpisode), season = parentCastSeason, show = parentCastShow)
				if value: episode['cast'] = value

				value = self.mTools.mergeCrew(directors.get(numberSeason, {}).get(numberEpisode))
				if not value and parentDirector: value = Tools.copy(parentDirector)
				if value: episode['director'] = value

				value = self.mTools.mergeCrew(writers.get(numberSeason, {}).get(numberEpisode))
				if not value and parentWriter: value = Tools.copy(parentWriter)
				if value: episode['writer'] = value

				value = self.mTools.mergeCrew(creators.get(numberSeason, {}).get(numberEpisode))
				if not value and parentCreator: value = Tools.copy(parentCreator)
				if value: episode['creator'] = value

				episode['media'] = media

				niche = self.mTools.mergeNiche(niches.get(numberSeason, {}).get(numberEpisode))
				niche = self.mTools.niche(niche = niche, metadata = episode, show = show, pack = pack)
				if niche: episode['niche'] = niche

				if numberSeason in votings and numberEpisode in votings[numberSeason]: episode['voting'] = votings[numberSeason][numberEpisode]

				# Use the show/season average episode duration in there is no extact duration.
				if not episode.get('duration') and parentDuration: episode['duration'] = parentDuration

				# Newer unaired episodes from shows like "Coronation Street" do not always have a tvshowtitle, which causes sorting to fail.
				if not episode.get('tvshowtitle') and parentTitle: episode['tvshowtitle'] = parentTitle

				data['episodes'][i] = {k : v for k, v in episode.items() if not v is None}
				episode = data['episodes'][i]

				# Always replace the IDs with new values.
				# Otherwise if there is an incorrect IMDb ID on Trakt/TMDb, it gets written to MetaCache.
				# At a later point the ID is corrected on Trakt/TMDb.
				# If the data is now refreshed, the old ID from MetaCache is used instead of the newly retrieved IDs.
				# Hence, always replace these.
				ids1 = episode.get('id') or {}
				ids2 = season.get('id') or {}
				value = ids1.get('imdb') or ids2.get('imdb')
				if value: imdb = value
				value = ids1.get('tmdb') or ids2.get('tmdb')
				if value: tmdb = value
				value = ids1.get('tvdb') or ids2.get('tvdb')
				if value: tvdb = value
				value = ids1.get('trakt') or ids2.get('trakt')
				if value: trakt = value
				value = ids1.get('slug') or ids2.get('slug')
				if value: slug = value
				value = ids1.get('tvmaze') or ids2.get('tvmaze')
				if value: tvmaze = value
				value = ids1.get('tvrage') or ids2.get('tvrage')
				if value: tvrage = value

				# This is for legacy purposes, since all over Gaia the IDs are accessed at the top-level of the dictionary.
				# At some later point the entire addon should be updated to have the new ID structure
				if not 'id' in episode: episode['id'] = {}
				if imdb: episode['id']['imdb'] = episode['imdb'] = imdb
				if tmdb: episode['id']['tmdb'] = episode['tmdb'] = tmdb
				if tvdb: episode['id']['tvdb'] = episode['tvdb'] = tvdb
				if trakt: episode['id']['trakt'] = episode['trakt'] = trakt
				if slug: episode['id']['slug'] = episode['slug'] = slug
				if tvmaze: episode['id']['tvmaze'] = episode['tvmaze'] = tvmaze
				if tvrage: episode['id']['tvrage'] = episode['tvrage'] = tvrage

				if numberSeason in images and images[numberSeason] and numberEpisode in images[numberSeason] and images[numberSeason][numberEpisode]:
					MetaImage.update(media = MetaImage.MediaEpisode, images = images[numberSeason][numberEpisode], data = episode, sort = providersImage)
				else:
					imagesMissing = True

				# Do this before here already.
				# Otherwise a bunch of regular expressions are called every time the menu is loaded.
				self.mTools.cleanPlot(metadata = episode)

				# Calculate the rating here already, so that we have a default rating/votes if this metadata dictionary is passed around without being cleaned first.
				# More info under meta -> tools.py -> cleanVoting().
				self.mTools.cleanVoting(metadata = episode, round = True) # Round to reduce storage space of average ratings with many decimal places.

			# Sort so that the list is in the order of the episode numbers.
			data['episodes'].sort(key = lambda i : i['episode'])

			# Set the show details.
			if imdb: data['imdb'] = imdb
			if tmdb: data['tmdb'] = tmdb
			if tvdb: data['tvdb'] = tvdb
			if trakt: data['trakt'] = trakt
			if slug: data['slug'] = slug
			if tvmaze: data['tvmaze'] = tvmaze
			if tvrage: data['tvrage'] = tvrage
			title = season['tvshowtitle'] if season and 'tvshowtitle' in season else None
			if title: data['tvshowtitle'] = data['title'] = title
			year = season['year'] if season and 'year' in season else None
			if year: data['year'] = year
			if not originalSeason is None: data['season'] = originalSeason

			# Sometimes the images are not available, especially for new/future releases.
			# This looks ugly in the menus. Mark as incomplete to re-retrieve sooner.
			if imagesMissing:
				partDone = False
				try: partNew['tvdb']['complete'] = False
				except: pass
				if developer: Logger.log('EPISODE IMAGES INCOMPLETE: %s' % developer)

			Memory.set(id = id, value = data, local = True, kodi = False)
			if item and data: item.update(Tools.copy(data)) # Can be None if the ID was not found. Copy in case the outer item is edited before we write the data to MetaCache.

			if partDone:
				try: item[MetaCache.Attribute][MetaCache.AttributePart] = None
				except: pass
			else:
				partNew[MetaCache.AttributeFail] += 1
				data[MetaCache.Attribute] = {MetaCache.AttributePart : partNew}

			self._batchLoad(media = media, imdb = data.get('imdb'), tmdb = data.get('tmdb'), tvdb = data.get('tvdb'), trakt = data.get('trakt'), season = originalSeason)
			result.append(data)
		except:
			Logger.error()
		finally:
			if locks and id: locks[id].release()
			if semaphore: semaphore.release()
			self.mTools.busyFinish(media = media, item = item)

	def _metadataEpisodeId(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None):
		result = self.mTools.idShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
		if result: return {'complete' : True, 'data' : {'id' : result}}
		else: return {'complete' : False, 'data' : result}

	def _metadataEpisodeTrakt(self, trakt = None, imdb = None, season = None, language = None, item = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			# Do not use the cached summarized data. Only if it comes from IMDb.
			try: origin = bool(item['temp']['trakt'])
			except: origin = False

			if detail == MetaTools.DetailEssential and item and origin: # Comes from a Trakt list with basic metadata.
				if MetaCache.Attribute in item:
					result = {}
				else:
					result = Tools.copy(item)
					try: del result['temp']
					except: pass
				result = self._metadataTemporize(item = item, result = result, provider = 'trakt')
			else: # Comes from another list, or forcefully retrieve detailed metadata.
				id = trakt or imdb
				if id:
					# Trakt has an API limit of 1000 requests per 5 minutes.
					# Retrieving all the additional metadata will very quickly consume the limit if a few pages are loaded.
					# Only retrieve the extended metadata if enough requests are still avilable for the past 5 minutes.
					instance = MetaTrakt.instance()
					usagesAuthenticated = instance.usage(authenticated = True)
					usagesUnauthenticated = instance.usage(authenticated = False)

					person = False
					if detail == MetaTools.DetailExtended and usagesUnauthenticated < 0.3: person = True

					translation = None
					if detail == MetaTools.DetailEssential: translation = False # Use the translations from TVDb.

					# We already retrieve the cast (with thumbnails) and translations from TVDb.
					# Retrieving all of them here again will add little new metadata and only prolong the retrieval.
					# translation = None: only retrieve for non-English.
					return instance.metadataEpisode(id = id, season = season, summary = True, translation = translation, person = person, language = language, extended = True, detail = True, cache = None if cache is False else cache, concurrency = bool(threaded))
		except: Logger.error()
		return {'provider' : 'trakt', 'complete' : complete, 'data' : result}

	def _metadataEpisodeTvdb(self, tvdb = None, imdb = None, season = None, language = None, item = None, cache = None, threaded = None, detail = None):
		try: return MetaTvdb.instance().metadataEpisode(tvdb = tvdb, imdb = imdb, season = season, language = language, cache = cache, threaded = threaded, detail = True)
		except: Logger.error()
		return {'provider' : 'tvdb', 'complete' : True, 'data' : None}

	def _metadataEpisodeTmdb(self, tmdb = None, season = None, language = None, item = None, cache = None, threaded = None, detail = None):
		try: return MetaTmdb.instance().metadataEpisode(tmdb = tmdb, season = season, language = language, cache = cache, threaded = threaded, detail = True)
		except: Logger.error()
		return {'provider' : 'tmdb', 'complete' : True, 'data' : None}

	def _metadataEpisodeImdb(self, imdb = None, season = None, language = None, item = None, cache = None, threaded = None, detail = None):
		results = []

		# Do not use the cached summarized data. Only if it comes from IMDb.
		try: origin = not item['episodes'][0]['temp']['imdb']['voting']['rating'] is None
		except:
			try: origin = not item[0]['temp']['imdb']['voting']['rating'] is None
			except: origin = False

		# Only do this if there is no IMDb rating in in the item, that is, the item does not come from a IMDb list.
		# Retrieving the detailed IMDb data does not really add extra metadata above TMDb/Trakt, except for the rating/vote and the revenue (which is also on TMDb).
		if detail == MetaTools.DetailExtended and imdb and not origin:
			data = MetaImdb.instance().metadataEpisode(id = imdb, season = season, language = language, cache = cache)
			if data:
				item = data
				origin = True

		complete = True
		result = []
		try:
			if origin and item and 'episodes' in item:
				for episode in item['episodes']:
					if episode and 'season' in episode and 'episode' in episode:
						resultEpisode = Tools.copy(episode)
						try: del resultEpisode['temp']
						except: pass

						resultEpisode = self._metadataTemporize(item = episode, result = resultEpisode, provider = 'imdb')
						if resultEpisode:
							# Check MetaImdb._extractItems() for more details.
							for attribute in ['genre', 'language', 'country']:
								value = episode.get(attribute)
								if value:
									value = Tools.listUnique(value + (resultEpisode.get(attribute) or []))
									if value: resultEpisode[attribute] = value
							for attribute in ['mpaa']:
								value = episode.get(attribute)
								if value: resultEpisode[attribute] = value

							result.append(resultEpisode)

						# Newley released seasons might not have ratings for all episodes yet.
						# Mark as incomplete in order to re-retrieve at a later stage when there are hopefully new ratings.
						if complete: complete = bool(resultEpisode and 'rating' in resultEpisode and resultEpisode['rating'])
		except: Logger.error()
		results.append({'provider' : 'imdb', 'complete' : complete, 'data' : result or None})

		complete = True
		result = []
		try:
			if origin and item and 'episodes' in item:
				for episode in item['episodes']:
					if episode and 'temp' in episode and 'metacritic' in episode['temp']:
						if 'season' in episode and 'episode' in episode:
							resultEpisode = {'season' : episode['season'], 'episode' : episode['episode']}
							resultEpisode = self._metadataTemporize(item = episode, result = resultEpisode, provider = 'metacritic')
							if resultEpisode: result.append(resultEpisode)
		except: Logger.error()
		results.append({'provider' : 'metacritic', 'complete' : complete, 'data' : result or None})

		return results

	def _metadataEpisodeAggregate(self, items, threaded = None):
		# Adding the previous/current/next season metadata to individual episodes in _metadataEpisodeUpdate() is a bad idea, since the metadata is saved to the MetaCache database.
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
			if items:
				values = items if Tools.isArray(items) else [items]
				if values and Tools.isArray(values[0]): values = Tools.listFlatten(values) # A list for mutiple shows, each containing a list of episodes.

				seasons = []
				for item in values:
					try: seasons.append({'imdb' : item.get('imdb'), 'tmdb' : item.get('tmdb'), 'tvdb' : item.get('tvdb'), 'trakt' : item.get('trakt')})
					except: Logger.error()
				seasons = Tools.listUnique(seasons)
				seasons = self.metadataSeason(items = seasons, pack = False, threaded = threaded) if seasons else None

				if seasons:
					for item in values:
						try:
							imdb = item.get('imdb')
							tmdb = item.get('tmdb')
							tvdb = item.get('tvdb')
							trakt = item.get('trakt')
							number = item.get('season')

							for season in seasons:
								first = season[0]
								if (imdb and first.get('imdb') == imdb) or (tmdb and first.get('tmdb') == tmdb) or (tvdb and first.get('tvdb') == tvdb) or (trakt and first.get('trakt') == trakt):
									seasonCurrent = next((i for i in season if i['season'] == number), None)
									seasonPrevious = next((i for i in season if i['season'] == number - 1), None)
									seasonNext = next((i for i in season if i['season'] == number + 1), None)
									if seasonCurrent: seasonCurrent = self.mTools.reduce(metadata = seasonCurrent, pack = True, seasons = True)
									if seasonPrevious: seasonPrevious = self.mTools.reduce(metadata = seasonPrevious, pack = True, seasons = True)
									if seasonNext: seasonNext = self.mTools.reduce(metadata = seasonNext, pack = True, seasons = True)

									item['seasons'] = {
										'previous' : seasonPrevious,
										'current' : seasonCurrent,
										'next' : seasonNext,
									}

									if seasonCurrent and MetaImage.Attribute in seasonCurrent:
										MetaImage.update(media = MetaImage.MediaSeason, images = Tools.copy(seasonCurrent[MetaImage.Attribute]), data = item, category = MetaImage.MediaSeason) # Add season images.
										if MetaImage.MediaShow in seasonCurrent[MetaImage.Attribute]: MetaImage.update(media = MetaImage.MediaShow, images = Tools.copy(seasonCurrent[MetaImage.Attribute][MetaImage.MediaShow]), data = item, category = MetaImage.MediaShow) # Add show images.
									break
						except: Logger.error()
		except: Logger.error()
		return items

	def _metadataEpisodeIncrement(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, episode = None, item = None, number = None, lock = None, locks = None, semaphore = None, cache = False, threaded = None, discrepancy = None):
		try:
			media = Media.Episode

			if item:
				if imdb is None:
					imdb = item.get('imdb')
					if imdb: imdb = str(imdb)
				if tmdb is None:
					tmdb = item.get('tmdb')
					if tmdb: tmdb = str(tmdb)
				if tvdb is None:
					tvdb = item.get('tvdb')
					if tvdb: tvdb = str(tvdb)
				if trakt is None:
					trakt = item.get('trakt')
					if trakt: trakt = str(trakt)

				if title is None: title = item.get('tvshowtitle') or item.get('title')
				if year is None: year = item.get('year')

				if season is None: season = item.get('season')
				if episode is None: episode = item.get('episode')

			if not tvdb:
				ids = self._metadataEpisodeId(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
				if ids:
					ids = (ids.get('data') or {}).get('id') # "data" can be None if the ID was not found.
					if ids:
						if not imdb: imdb = ids.get('imdb')
						if not tmdb: tmdb = ids.get('tmdb')
						if not tvdb: tvdb = ids.get('tvdb')
						if not trakt: trakt = ids.get('trakt')
			if not imdb and not tvdb and not trakt and not tmdb: return False

			# Important to add "number" here, since there might be mutiple lookups with different numbers (eg: standard vs sequential).
			id = Memory.id(media = Media.Episode, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, episode = episode, number = number, increment = True)
			if not locks is None:
				if not id in locks:
					lock.acquire()
					if not id in locks: locks[id] = Lock()
					lock.release()
				locks[id].acquire()
				data = Memory.get(id = id, uncached = True, local = True, kodi = False)
				if Memory.cached(data):
					if item and data: item.update(Tools.copy(data)) # Copy in case the memory is used mutiple times.
					return data

			developer = self._metadataDeveloper(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, item = item)

			pack = self.metadataPack(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, threaded = threaded)
			if not pack:
				if developer: Logger.log('CANNOT DETERMINE NEXT EPISODE: ' + developer + (' [%s]' % Title.numberUniversal(season = season, episode = episode)))
				return False
			pack = MetaPack.instance(pack = pack)

			# If a sequential/absolute episode was passed in, continue with that numbering. Else default to the standard numbering.
			# When a specific number was requested (by passing in a "number" parameter), continue with that numbering (eg: Downton Abbey S01E07 -> S02E01 ("standard") and S01E07 -> S01E08 ("sequential")).
			# Otherwise, shows where some providers have a sequential/absolute season as standard season, will continue with the sequential numbering (eg: Dragon Ball Supper S01E14 -> S01E15).
			# Otherwise, when the requestsed number is not found as an standard number, continue with the sequential numbering (eg: Downton Abbey S01E07 -> S02E01 and S01E08 -> S01E09).
			# Otherwise, when no sequential/absolute number was requestsed, continue with the default/standard numbering (eg: Downton Abbey S01E07 -> S02E01).
			if number is None:
				for i in [MetaPack.NumberStandard, MetaPack.NumberSequential, MetaPack.NumberAbsolute]:
					if pack.episode(season = season, episode = episode, number = i):
						number = i
						break
				if not number: number = MetaPack.NumberStandard

			# Retrieve the next available episode after the last watched episode.
			# If the next episode is in the same season as the last watched episode, continue like normal and retrieve all episodes for the current season.
			# If the next episode is in the next season (aka last watched episode was the last episode from the previous season), retrieve the all episodes for next season.
			seasonNext = season + 1
			seasonSelect = None
			episodeNext = episode + 1
			episodeFirst = 1
			episodeSelect = None
			found = 0

			# Important to use "type = MetaPack.NumberOfficial" in all number lookups, otherwise unofficial episodes at the end of the season might be used, therefore not going to the next season.
			# Eg: One Piece S21E892 - S21E1088.
			# If the passed-in episode is not an official episode, use the stadnard number instead.
			# Eg: Dragon Ball Super S02E01.
			type = MetaPack.NumberOfficial
			if not pack.typeOfficial(season = season, episode = episode):
				type = MetaPack.NumberStandard
			if number == MetaPack.NumberOfficial or number == MetaPack.NumberUnofficial:
				type = number
				number = MetaPack.NumberStandard

			# Next episode in the same season.
			if episodeNext <= pack.numberLastEpisode(season = season, number = number, type = type, default = -1):
				seasonSelect = season
				episodeSelect = episodeNext
				found = 1

			# First episode in the next season.
			elif episodeFirst <= pack.numberLastEpisode(season = seasonNext, number = number, type = type, default = -1):
				seasonSelect = seasonNext
				episodeSelect = episodeFirst
				found = 2

			# Sequential numbering when there are unofficial episodes.
			# Eg: Star Wars: Young Jedi Adventures: S01E25 -> S01E26
			elif number == MetaPack.NumberSequential or number == MetaPack.NumberAbsolute:
				type = number
				if episodeNext <= pack.numberLastEpisode(season = season, number = number, type = number, default = -1):
					seasonSelect = season
					episodeSelect = episodeNext
					found = 1

			# If all episodes in a show are watched 1 time, the show is hidden from the Progress menu.
			# If a single episode in the show was watched 2 times while the rest were only watched 1 time (maybe by accident or rewatched after a long time), it shows up again in the Progress menu.
			# Hide these shows where the previous N episodes have a lower playcount than the current/last-watched episode.
			if discrepancy is None: discrepancy = self.mTools.settingsShowDiscrepancy()
			if discrepancy and found and seasonSelect and episodeSelect:
				from lib.modules.playback import Playback
				playback = Playback.instance()

				# NB: Use quick, to reduce time needed by Playback to lookup Trakt episode numbers, which are not needed here.
				countCurrent = playback.history(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, pack = pack, quick = True)

				if countCurrent:
					# The episode has progress, but is not fully watched yet.
					# Do not go to the next episode, but stick to the current episode.
					if not countCurrent['count']['total']:
						if developer: Logger.log('EPISODE UNFINISHED (NEXT): ' + developer + (' [%s]' % Title.numberUniversal(season = season, episode = episode)))
						found = 3
					else:
						countNext = playback.history(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonSelect, episode = episodeSelect, pack = pack, quick = True) # NB: Use quick, to reduce time.
						if countNext and countNext['count']['total']: # Only do this if the next episode was already watched (aka rewatch).
							countNext = countNext['count']['total']
							countCurrent = countCurrent['count']['total']

							# Previous episodes have a lower count.
							if countCurrent and countCurrent > 1:
								lookups = []
								seasonCounter = season
								episodeCounter = episode
								for i in range(5):
									episodeCounter -= 1
									if episodeCounter <= 0:
										if seasonCounter == 1: break
										seasonCounter -= 1
										episodeCounter = pack.numberLastEpisode(season = seasonCounter, number = number, type = type, default = 0)
									lookups.append({'season' : seasonCounter, 'episode' : episodeCounter})

								counter = 0
								for i in lookups:
									value = playback.history(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = i['season'], episode = i['episode'], pack = pack)
									if value and value['count']['total'] and value['count']['total'] >= countCurrent: counter += 1

								# 0.4: less than 2 out of 5.
								if (discrepancy == MetaTools.DiscrepancyLenient and counter == 0 and lookups) or (discrepancy == MetaTools.DiscrepancyStrict and counter < len(lookups) * 0.4):
									if developer: Logger.log('EPISODE HIDDEN (PREVIOUS): ' + developer + (' [%s]' % Title.numberUniversal(season = season, episode = episode)))
									found = 0

							# Next episodes have the same playcount.
							# A previous season/episode might have been marked as watched at a later date than the next season/episode.
							# Hide these as well.
							if countCurrent == countNext:
								lookups = []
								seasonCounter = season
								episodeCounter = episode

								for i in range(10):
									add = True
									end = False
									episodeCounter += 1
									if episodeCounter > pack.numberLastEpisode(season = seasonCounter, number = number, type = type, default = 0):
										seasonCounter += 1
										if seasonCounter > pack.numberLastSeason(number = number, type = type, default = 0):
											add = False
											end = True
										else:
											episodeCounter = 1
									if add: lookups.append({'season' : seasonCounter, 'episode' : episodeCounter})
									if end: break

								counter = 0
								for i in lookups:
									countContinue = playback.history(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = i['season'], episode = i['episode'], pack = pack)
									if countContinue:
										countContinue = countContinue['count']['total']
										if not countContinue is None and not countContinue == countCurrent:
											counter += countContinue
											break
									else:
										counter += 1

								if (discrepancy == MetaTools.DiscrepancyLenient and counter == 0) or (discrepancy == MetaTools.DiscrepancyStrict and counter > 0):
									if developer: Logger.log('EPISODE HIDDEN (NEXT): ' + developer + (' [%s]' % Title.numberUniversal(season = season, episode = episode)))
									found = 0

			if found == 0:
				data = {'invalid' : True}

				Memory.set(id = id, value = data, local = True, kodi = False)
				if item: item.update(data)

				if developer and self.mDeveloperExtra: Logger.log('NO NEXT EPISODE: ' + developer + (' [%s]' % Title.numberUniversal(season = season, episode = episode)))
				return None
			else:
				if found == 1: data = {'season' : season, 'episode' : episodeNext}
				elif found == 2: data = {'season' : seasonNext, 'episode' : episodeFirst}
				elif found == 3: data = {'season' : season, 'episode' : episode}

				Memory.set(id = id, value = data, local = True, kodi = False)
				if item: item.update(data)

				if developer and self.mDeveloperExtra: Logger.log('NEXT EPISODE FOUND: ' + developer + (' [%s -> %s]' % (Title.numberUniversal(season = season, episode = episode), Title.numberUniversal(season = data['season'], episode = data['episode']))))
				return number
		except:
			Logger.error()
		finally:
			if locks and id: locks[id].release()
			if semaphore: semaphore.release()
		return None # Do not put inside "finally:".

	# This function takes in a list of episodes, containing both standard and special episodes.
	# It determines which specials to keep and which to remove, based on the episode type (eg: storyline special) and the user's specials settings.
	# The specials are then interleaved between the standard episodes, based on their release date and the fixed position that TVDb sometimes assigns to specials.
	def _metadataEpisodeSpecial(self, items, special = None, season = None, episode = None, number = None, pack = None):
		timeStart = None
		timeEnd = None
		timePrevious = None
		timeNext = None
		timeLimit = None
		timeBefore = None
		seasonLast = None
		seasonCurrent = season

		offset = not episode is None
		if season is None or episode is None or (season == 1 and episode == 1):
			season = None
			episode = None

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

				if time:
					timeValue = Time.integer(time)
					if timeStart is None or timeValue < timeStart: timeStart = timeValue # Include all specials prior to S01E01.
					if timeEnd is None or timeValue > timeEnd: timeEnd = timeValue

			if time and not season is None and item['season'] == season and item['episode'] == episode:
				timeLimit = Time.integer(time)

			result.append(item)
		items = result

		if number == MetaPack.NumberSerie and seasonCurrent: seasonLast = min(seasonLast, seasonCurrent)

		if pack and seasonLast:
			seasonCurrent = None
			seasonPrevious = None
			seasonNext = None
			for i in pack.season(default = []):
				if pack.typeOfficial(item = i): # Skip unofficial seasons (eg: Dragon Ball Super S02+).
					numberSeason = pack.numberStandard(item = i)
					if numberSeason == seasonLast: seasonCurrent = i
					elif numberSeason > 0 and numberSeason == seasonLast - 1: seasonPrevious = i
					elif numberSeason == seasonLast + 1: seasonNext = i

			if seasonCurrent:
				if seasonPrevious:
					time = pack.timeMaximumOfficial(item = seasonPrevious)
					if time: timePrevious = Time.integer(Time.format(timestamp = time, format = Time.FormatDate))
				else:
					timeStart = None # Is the first season. Inluce all previous specials.

				if seasonNext:
					time = pack.timeMinimumOfficial(item = seasonNext)
					if time: timeNext = Time.integer(Time.format(timestamp = time, format = Time.FormatDate))
				else:
					timeEnd = None # Is the last season. Include all remaining specials

		if timeLimit:
			if timeStart: timeStart = max(timeStart, timeLimit)
			else: timeStart = timeLimit

		# Get the last episode of the previous submenu.
		# This is used to filter out specials that belong to the previous submenu (aka they are actually placed before the last normal episode in the previous submenu).
		try:
			if pack:
				lastSeason = 0
				lastEpisode = 0
				for item in items:
					if item['season'] > 0:
						lastSeason = item['season']
						lastEpisode = item['episode']
						break
				if lastSeason > 1:
					if lastEpisode == 1:
						lastSeason -= 1
						lastEpisode = pack.countEpisode(season = lastSeason)
					else:
						lastEpisode -= 1
					timeBefore = pack.time(season = lastSeason, episode = lastEpisode)
					if timeBefore: timeBefore = Time.integer(Time.format(timestamp = timeBefore, format = Time.FormatDate))
		except: Logger.error()

		if timeStart or timeEnd or offset:
			reduce = special == MetaManager.SpecialReduce # Make sure it is boolean and not None.
			unofficial = self.mTools.settingsShowInterleaveUnofficial(reduce = reduce)
			extra = self.mTools.settingsShowInterleaveExtra(reduce = reduce)
			duration = self.mTools.settingsShowInterleaveDuration(reduce = reduce)

			average = None
			if pack:
				average = pack.durationMeanOfficial()
				if average: average *= duration

			result = []
			for item in items:
				# In case multiple specials have the same release date.
				if timeLimit:
					if not item['season'] == 0 and item['season'] < season: continue
					elif item['season'] == season and item['episode'] < episode: continue

				if item['season'] == 0:
					special = item.get('special')
					specialStory = None
					specialExtra = None
					if special:
						specialStory = special.get('story')
						specialExtra = special.get('extra')
					if not extra and specialStory: # For both None and False.
						# Only add storyline specials if they have a before/after number so that they can be placed at a predefined position.
						# This is useful for specials which have a premier date that is far off from its actual position, and will be correctly placed at the end of this function.
						# Eg: House S00E01.
						# If there is no before/after number, do not add here, but use the premier date to determine if it should be added.
						if special.get('before') or special.get('after'):
							result.append(item)
							continue
					elif extra is True and not specialStory:
						continue
					elif extra is False and not specialStory and specialExtra:
						continue

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
						# Check for "time >= timePrevious"  and "time <= timeNext" for Trakt multiple submenus that are not devided strictly according to seasons.
						elif (timeStart is None or time < timeStart) and timePrevious and time >= timePrevious:
							differenceCurrent = abs(timeStart - time)
							differencePrevious = abs(timePrevious - time)
							if differenceCurrent < differencePrevious:
								if not item['season'] == 0 or (timeBefore and time >= timeBefore):
									result.append(item)
						elif (timeEnd is None or time > timeEnd) and timeNext and time <= timeNext:
							differenceCurrent = abs(timeEnd - time)
							differenceNext = abs(timeNext - time)
							if differenceCurrent < differenceNext:
								result.append(item)
				else:
					result.append(item)
		else:
			result = items

		# Make sure that specials are interleaved by airing date.
		# But also accomodate episodes that were not aired yet.
		# Eg: If S03E01 was not released yet, it should not be moved to the front of the list because it has no airing date.
		lastSeason = 0
		lastEpisode = 0
		lastAired = 0
		for i in reversed(result):
			if 'aired' in i and i['aired']:
				lastSeason = i['season']
				lastEpisode = i['episode']
				lastAired = Time.integer(i['aired'])
				break

		# (0.1 if i['season'] == 0 else 0.0): Move specials that were released on the same day as a normal episode, to AFTER the normal episode.
		# Eg: GoT 7x04 -> 0x29 Inside Episode 4 -> 7x05 -> 0x30 Inside Episode 5
		def _sort(item):
			currentSeason = item.get('season')
			currentEpisode = item.get('episode')
			currentAired = item.get('aired')
			if currentAired: order = Time.integer(currentAired) + (0.1 if currentSeason == 0 else 0.0)
			elif (currentSeason > lastSeason or (currentSeason == lastSeason and currentEpisode > lastEpisode)): order = lastAired
			else: order = 0
			return (order, currentSeason or 0, currentEpisode or 0)
		result = sorted(result, key = _sort)

		# Specials appearing on the same day as the FIRST episode can sometimes be the same as described above.
		# Eg: GoT 8x01 -> 0x46 Inside Episode 1
		# But in most cases those specials should be placed BEFORE the first episode, since they are typically recaps, interviews, or other specials that are aired right before the new season premier.
		i = 0
		temp = []
		while i < len(result): # The index (i) in a for-loop cannot be adjusted within the loop iteself (eg: "i = j"). Use a while loop instead.
			item = result[i]
			if not item.get('season') == 0 and item.get('episode') == 1:
				aired = item.get('aired')
				if aired:
					for j in range(i + 1, len(result)):
						item2 = result[j]
						if item2.get('season') == 0 and item2.get('aired') == aired:
							i += 1
							temp.append(item2)
						else: break
			temp.append(item)
			i += 1
		result = temp

		# Move episode to a specific position, if the exact position is known.
		# That is, TVDb has set the before/after numbers.
		# Do not just go by date, since sometimes a special can be added a lot later with a later premier date, although it belongs earlier.
		# Eg: House S00E01 is an unaired pilot and should be placed before S01E01, but its premier date is only after S07.
		default = []
		fixed = []
		firstSeason = None
		firstEpisode = None
		lastSeason = None
		lastEpisode = None
		for item in result:
			currentSeason = item.get('season')
			if not currentSeason == 0:
				currentEpisode = item.get('episode')
				if firstSeason is None or currentSeason <= firstSeason:
					firstSeason = currentSeason
					if firstEpisode is None or currentEpisode < firstEpisode: firstEpisode = currentEpisode
				if lastSeason is None or currentSeason >= lastSeason:
					lastSeason = currentSeason
					if lastEpisode is None or currentEpisode > lastEpisode: lastEpisode = currentEpisode

			special = item.get('special')
			if special:
				if special.get('before') or special.get('after'):
					fixed.append(item)
					continue
			default.append(item)

		previousSeason = None
		previousEpisode = None
		if pack and default:
			first = default[0]
			if first.get('season') > 1 and first.get('episode') == 1:
				previous = pack.lookupStandard(season= first.get('season') - 1, episode = -1)
				if previous:
					previousSeason = previous[MetaPack.PartSeason]
					previousEpisode = previous[MetaPack.PartEpisode]

		if fixed:
			try:
				for item in fixed:
					before = item.get('special').get('before')
					if before:
						beforeSeason = before.get('season')
						beforeEpisode = before.get('episode') or 1

						# The before/after numbers always come from TVDb. Convert to standard numbers, so they can be placed correctly, if Trakt has different numbers.
						# Eg: One Piece, the first few specials should be interleaved in S01 (Trakt), while the before/after numbers from TVDb indicate S02+.
						if pack:
							lookup = pack.lookupStandard(season = beforeSeason, episode = beforeEpisode, input = MetaPack.ProviderTvdb)
							if lookup and lookup[MetaPack.PartEpisode]:
								beforeSeason = lookup[MetaPack.PartSeason]
								beforeEpisode = lookup[MetaPack.PartEpisode]

						if beforeSeason >= firstSeason and beforeSeason <= lastSeason: # Exclude specials that do not belong within the current seasons.
							if (beforeSeason > firstSeason or beforeEpisode >= firstEpisode) and (beforeSeason < lastSeason or beforeEpisode <= lastEpisode):
								for i, item2 in enumerate(default):
									if item2.get('season') >= beforeSeason and item2.get('episode') >= beforeEpisode:
										default.insert(i, item)
										break
			except: Logger.error()

			# Reversed, because the inner loop is also reversed.
			# Otherwise sequential specials are out of order.
			# Eg: The Office UK S00E01 and S00E02 at the end of the Series menu.
			try:
				for item in reversed(fixed):
					after = item.get('special').get('after')
					if after:
						afterSeason = after.get('season')
						afterEpisode = after.get('episode')
						afterException = not afterEpisode
						if afterException: afterEpisode = 999999

						# The before/after numbers always come from TVDb. Convert to standard numbers, so they can be placed correctly, if Trakt has different numbers.
						# Eg: One Piece, the first few specials should be interleaved in S01 (Trakt), while the before/after numbers from TVDb indicate S02+.
						if pack:
							lookup = pack.lookupStandard(season = afterSeason, episode = -1 if afterException else afterEpisode, input = MetaPack.ProviderTvdb) # Lookup function works with negative numbers.
							if lookup and lookup[MetaPack.PartEpisode]:
								afterSeason = lookup[MetaPack.PartSeason]
								afterEpisode = lookup[MetaPack.PartEpisode]

						acceptedSeason = previousSeason or firstSeason
						if afterSeason >= acceptedSeason and afterSeason <= lastSeason: # Exclude specials that do not belong within the current seasons.
							if (afterSeason > acceptedSeason or afterEpisode >= firstEpisode) and (afterSeason < lastSeason or afterEpisode <= lastEpisode or afterException):
								inserted = False

								for i, item2 in reversed(list(enumerate(default))):
									currentSeason = item2.get('season')
									currentEpisode = item2.get('episode')
									if ((currentSeason == 0 and currentSeason == afterSeason) or (currentSeason > 0 and currentSeason <= afterSeason)) and currentEpisode <= afterEpisode:
										default.insert(i + 1, item) # +1 to insert AFTER the given episode. Eg: The Office UK S00E01 and S00E02 at the end of the Series menu.
										inserted = True
										break

								# Important if there are a bunch of specials between two seasons.
								# Eg: Create an episode submenu for Doctor Who that starts at S01E01 and has 10 episodes per page.
								# Go to the page between S04E13 and S05E01, which should contain S00E09, S00E13, S00E14, S00E15, S00E16, S00E17.
								# The page starts at S05E01 (firstSeason/firstEpisode), while the placement is after S04E13 (afterSeason/afterEpisode).
								# Hence, also include the last episode of the previous season if specials cannot be placed with the for-loop above.
								if not inserted:
									if previousSeason == afterSeason and previousEpisode == afterEpisode:
										default.insert(0, item)
			except: Logger.error()

		result = default

		return result

	# This function determines the episodes (number range) that need to be retrieved to create a single menu page, based on the season/episode number offset, page limit, and the numbering type.
	# Menu performance is improved, since only the minimum number of episodes have to be retrieved from the database (all episodes of a season grouped together).
	def _metadataEpisodeRange(self, pack, season, episode = None, limit = None, number = None):
		try:
			if limit is None: limit = self.limit(submenu = True)

			count = 0
			seasonStart = 1 if season == 0 else season
			seasonLast = None
			episodeStart = None if episode is None else episode
			episodeEnd = None
			episodeLast = None

			# Retrieve an additional season, since the More page simply increments the episode, and not the season, in the parameters passed to the next page.
			# If this is the last episode of the season, the increment will obviously be incorrect (eg: last S01 episode is S01E10, but the More page increments it to S01E11).
			# Hence, we might also ahve to retrieve the next season, since the increment is for the first episode of the next season (eg: S02E01).
			seasonEnd = seasonStart + 1

			# Add another season for Episode submenus (Progress menu).
			# Do not do this for Series submenus, since the menu always stops at the last episode of the season, and the next page loads the next seaason.
			# However, Episode submenus can page across mutiple seasons (aka contain episodes from two season, plus the specials), so we might also have to include a few episodes from the next season in the menu.
			if not number == MetaPack.NumberSerie: seasonEnd += 1

			specialSeason = self.mTools.settingsShowSpecialSeason()
			specialEpisode = self.mTools.settingsShowSpecialEpisode()

			if pack:
				pack = MetaPack.instance(pack = pack)
				seasons = pack.season()

				if seasons:
					seasonLast = pack.numberLastOfficialSeason()
					episodeLast = pack.numberLastOfficialEpisode()

					# If the requested season is larger then the official last season, assume the unofficial seasons are used.
					# Eg: Dragon Ball Super. Last official season is S01 (Trakt). But the requested season might be S05, which is unofficial (TVDb).
					if not seasonLast is None and seasonLast < season:
						seasonLast = pack.numberLastUnofficialSeason()
						episodeLast = pack.numberLastUnofficialEpisode()

					for i in seasons:
						numberSeason = pack.numberStandard(item = i)
						if numberSeason >= seasonStart and (specialSeason or not numberSeason == 0):
							episodes = pack.episode(season = numberSeason) or [] # Can be None if there is a future season that does not contain any episodes yet.

							if episodeStart is None or not numberSeason == seasonStart: count += len(episodes)
							else: count += len([j for j in episodes if pack.numberStandardEpisode(item = j) >= episodeStart and (specialEpisode or not pack.numberStandardEpisode(item = j) == 0)]) # Only do this for seasonStart and not subsequent seasons.

							episodeEnd = episodeLast
							seasonEnd = numberSeason + 1
							if count >= limit: break

			if count == 0 and limit == 0:
				seasonStart += 1
				seasonEnd = seasonStart + 1
			if number == MetaPack.NumberSerie: seasonEnd = min(seasonEnd, seasonStart + 1) # Retrieve less seasons for series menus, since we know it will be cut off at the last episode of the season before paging to the next season.

			if seasonLast is None: seasonLast = seasonStart # Missing metadata for uncommon shows.
			seasonEnd = min(seasonEnd, seasonLast)

			result = {
				'limit' : limit,
				'season' : {'start' : seasonStart, 'end' : seasonEnd, 'last' : seasonLast},
				'episode' : {'start' : episodeStart, 'end' : episodeEnd, 'last' : episodeLast},
			}

			if pack and number in [MetaPack.NumberSequential, MetaPack.NumberAbsolute]:
				# Check the Absolute menu for GoT.
				# If the episode is not extracted first, the numberEnd/numberLast values are None, causing the Absolute menu for GoT to go to the next page after S01E73, starting back at S01E01.
				#numberStart = pack.numberEpisode(number = number, season = seasonStart, episode = episodeStart)
				#numberEnd = pack.numberEpisode(number = number, season = seasonEnd, episode = episodeEnd)
				#numberLast = pack.numberEpisode(number = number, season = seasonLast, episode = episodeLast)
				numberStart = pack.numberEpisode(number = number, item = pack.episode(season = seasonStart, episode = episodeStart))
				numberEnd = pack.numberEpisode(number = number, item = pack.episode(season = seasonEnd, episode = episodeEnd))
				numberLast = pack.numberEpisode(number = number, item = pack.episode(season = seasonLast, episode = episodeLast))

				result[number] = {'start' : numberStart, 'end' : numberEnd, 'last' : numberLast}

			return result
		except: Logger.error()
		return None

	##############################################################################
	# METADATA - PACK
	##############################################################################

	def metadataPack(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, items = None, filter = None, clean = True, quick = None, refresh = False, cache = False, threaded = None):
		try:
			media = Media.Pack

			pickSingle = False
			pickMutiple = False

			if items:
				if Tools.isArray(items):
					pickMutiple = True
				else:
					pickSingle = True
					items = [items]
			elif imdb or tmdb or tvdb or trakt:
				pickSingle = True
				items = [{'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt}]
			elif title:
				pickSingle = True
				items = self._metadataIdLookup(media = media, title = title, year = year, list = True)

			if items:
				# Get into the correct format for MetaCache to update the dictionaries.
				for item in items:
					value = item.get('title')
					if not value is None and not Tools.isArray(value): item['title'] = [value]
					value = item.get('year')
					if not value is None and not Tools.isDictionary(value): item['year'] = {MetaPack.ValueMinimum : value}

				items = self._metadataCache(media = media, items = items, function = self._metadataPackUpdate, quick = quick, refresh = refresh, cache = cache, threaded = threaded)
				if items:
					items = self._metadataFilter(media = media, items = items, filter = filter)

					if pickSingle: items = items[0] if items else None

					items = self._metadataClean(media = media, items = items, clean = clean)

					return items
		except: Logger.error()
		return None

	def _metadataPackUpdate(self, item, result = None, lock = None, locks = None, semaphore = None, cache = False, threaded = None, mode = None, part = True):
		try:
			media = Media.Pack

			imdb = item.get('imdb')
			tmdb = item.get('tmdb')
			tvdb = item.get('tvdb')
			trakt = item.get('trakt')
			slug = item.get('slug')
			tvmaze = item.get('tvmaze')
			tvrage = item.get('tvrage')

			title = item.get('tvshowtitle') or item.get('title')
			year = item.get('year')

			if title and Tools.isArray(title): title = title[0]
			if year and Tools.isDictionary(year): year = year.get(MetaPack.ValueMinimum)

			# By default we do not cache requests to disc, since it takes longer and requires more storage space.
			# If the same show appears multiple times in the list (some Trakt lists, eg watched list where a show was watched twice), sub-requests will also have to be executed multiple times, since they are not disc-cached.
			# Cache in memory and use locks to block subsequent calls with the same ID/title until the first request is done and then use those results without executing all the code again.
			id = Memory.id(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
			if not locks is None:
				if not id in locks:
					lock.acquire()
					if not id in locks: locks[id] = Lock()
					lock.release()
				locks[id].acquire()
				data = Memory.get(id = id, uncached = True, local = True, kodi = False)
				if Memory.cached(data):
					if data: item.update(Tools.copy(data)) # Copy in case the memory is used mutiple times. Can be None if not found.
					return None

			# Previous incomplete metadata.
			partDone = True
			partOld = {}
			partNew = {MetaCache.AttributeFail : 0}
			if part:
				try:
					partCache = item.get(MetaCache.Attribute)
					if partCache and partCache.get(MetaCache.AttributeStatus) == MetaCache.StatusIncomplete:
						partOld = partCache.get(MetaCache.AttributePart) or {}
						partNew[MetaCache.AttributeFail] = partOld.get(MetaCache.AttributeFail, 0)
				except: Logger.error()

			# Trakt requires either a Trakt or IMDb ID.
			# TMDb requires a TMDb ID.
			if not tvdb or (not imdb and not trakt) or (self.mLevel >= 1 and not tmdb) or (self.mLevel >= 2 and not imdb):
				ids = partOld.get('id')
				if not ids or not ids.get('complete'): ids = self._metadataPackId(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
				partNew['id'] = ids
				if ids:
					if not ids.get('complete'): partDone = False
					ids = ids.get('data')
					if ids:
						ids = ids.get('id')
						if ids:
							if not imdb: imdb = ids.get('imdb')
							if not tmdb: tmdb = ids.get('tmdb')
							if not tvdb: tvdb = ids.get('tvdb')
							if not trakt: trakt = ids.get('trakt')
							if not slug: slug = ids.get('slug')
							if not tvmaze: tvmaze = ids.get('tvmaze')
							if not tvrage: tvrage = ids.get('tvrage')
			if not imdb and not tmdb and not tvdb and not trakt: return False

			cache = cache if cache else None
			developer = self._metadataDeveloper(media = Media.Show, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, item = item)
			if developer: Logger.log('PACK METADATA RETRIEVAL [%s]: %s' % (mode.upper() if mode else 'UNKNOWN', developer))

			# DetailEssential: 3 requests [Trakt: 2 (episodes, translations), TVDb: 1 (episodes), TMDb: 0]
			# DetailStandard: 4 requests [Trakt: 2 (episodes, translations), TVDb: 1 (episodes), TMDb: 1 (summary)]
			# DetailExtended: 5 requests [Trakt: 2 (episodes, translations), TVDb: 1 (episodes), TMDb: 2 (summary, episodes)]
			requests = []
			if self.mLevel >= 0:
				requests.append({'id' : 'tvdb', 'function' : self._metadataPackTvdb, 'parameters' : {'tvdb' : tvdb, 'imdb' : imdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				requests.append({'id' : 'trakt', 'function' : self._metadataPackTrakt, 'parameters' : {'trakt' : trakt, 'imdb' : imdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				if self.mLevel >= 1:
					requests.append({'id' : 'tmdb', 'function' : self._metadataPackTmdb, 'parameters' : {'tmdb' : tmdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
					if self.mLevel >= 2:
						requests.append({'id' : 'imdb', 'function' : self._metadataPackImdb, 'parameters' : {'imdb' : imdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})

			partDatas = {}
			if partOld:
				partRequests = []
				for i in requests:
					partData = partOld.get(i['id'])
					if partData and partData.get('complete'): partDatas[i['id']] = partData
					else: partRequests.append(i)
				requests = partRequests
				partDatas = Tools.copy(partDatas) # Copy inner dicts that can be carried over with the update() below.

			datas = self._metadataRetrieve(requests = requests, threaded = threaded)
			datas.update(partDatas)

			data = {}
			for i in ['imdb', 'tmdb', 'trakt', 'tvdb']:
				if i in datas:
					value = datas[i]
					if value:
						partNew[i] = value
						if value['complete']:
							data[i] = value.get('data')
						else:
							partDone = False
							if developer: Logger.log('PACK METADATA INCOMPLETE [%s]: %s' % (i.upper(), developer))

			pack = MetaPack()
			if data:
				data = pack.generateShow(**data)

				# Store the reduced pack metadata (counts, durations, etc) in the show metadata.
				# This does not require a lot of extra storage space.
				# This allows for eg: season/episode counters in show menus (for certain skins that support it, like Aeon Nox).
				# Only shows that the user has shown interest in, by eg opening the season menu of the show, will retrieve these detailed counters.
				try:
					reduce = pack.reduce()
					if reduce:
						metacache = MetaCache.instance()
						show = metacache.select(type = MetaCache.TypeShow, items = [{'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt}])
						if show and show[0].get(MetaCache.Attribute, {}).get(MetaCache.AttributeStatus) in MetaCache.StatusValid: # Only if the data is already in the cache and not eg invalid or from external addon.
							# Do not update the time, rather use the old time.
							# Otherwise the show data has the time when the pack was last updated, and not the time the show was last updated.
							time = show[0][MetaCache.Attribute].get(MetaCache.AttributeTime)
							try: del show[0][MetaCache.Attribute]
							except: pass
							show[0]['packed'] = reduce
							metacache.insert(type = MetaCache.TypeShow, items = show, time = time, wait = True)
				except: Logger.error()

				if data:
					ids = data.get('id') or {}
					if not data.get('imdb'):
						if ids.get('imdb'): data['imdb'] = ids.get('imdb')
						elif imdb: data['imdb'] = imdb
					if not data.get('tmdb'):
						if ids.get('tmdb'): data['tmdb'] = ids.get('tmdb')
						elif tmdb: data['tmdb'] = tmdb
					if not data.get('tvdb'):
						if ids.get('tvdb'): data['tvdb'] = ids.get('tvdb')
						elif tvdb: data['tvdb'] = tvdb
					if not data.get('trakt'):
						if ids.get('trakt'): data['trakt'] = ids.get('trakt')
						elif trakt: data['trakt'] = trakt
					if not data.get('slug'):
						if ids.get('slug'): data['slug'] = ids.get('slug')
						elif slug: data['slug'] = slug
					if not data.get('tvmaze'):
						if ids.get('tvmaze'): data['tvmaze'] = ids.get('tvmaze')
						elif tvmaze: data['tvmaze'] = tvmaze
					if not data.get('tvrage'):
						if ids.get('tvrage'): data['tvrage'] = ids.get('tvrage')
						elif tvrage: data['tvrage'] = tvrage

			Memory.set(id = id, value = data, local = True, kodi = False)
			if item and data: item.update(Tools.copy(data)) # Can be None if the ID was not found. Copy in case the outer item is edited before we write the data to MetaCache.
			elif not data: data = {}

			if partDone:
				try: item[MetaCache.Attribute][MetaCache.AttributePart] = None
				except: pass
			else:
				partNew[MetaCache.AttributeFail] += 1
				data[MetaCache.Attribute] = {MetaCache.AttributePart : partNew}

			self._batchLoad(media = media, imdb = data.get('imdb'), tmdb = data.get('tmdb'), tvdb = data.get('tvdb'), trakt = data.get('trakt'))
			result.append(data)
		except:
			Logger.error()
		finally:
			if locks and id: locks[id].release()
			if semaphore: semaphore.release()
			self.mTools.busyFinish(media = media, item = item)

	def _metadataPackId(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, detail = None):
		result = self.mTools.idShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
		if result: return {'complete' : True, 'data' : {'id' : result}}
		else: return {'complete' : False, 'data' : result}

	def _metadataPackTrakt(self, trakt = None, imdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		try: return MetaTrakt.instance().metadataPack(trakt = trakt, imdb = imdb, cache = cache, threaded = threaded, detail = True)
		except: Logger.error()
		return {'provider' : 'trakt', 'complete' : True, 'data' : None}

	def _metadataPackTvdb(self, tvdb = None, imdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		try: return MetaTvdb.instance().metadataPack(tvdb = tvdb, imdb = imdb, cache = cache, threaded = threaded, detail = True)
		except: Logger.error()
		return {'provider' : 'tvdb', 'complete' : True, 'data' : None}

	def _metadataPackTmdb(self, tmdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		try: return MetaTmdb.instance().metadataPack(tmdb = tmdb, cache = cache, threaded = threaded, detail = True, quick = not(detail == MetaTools.DetailExtended))
		except: Logger.error()
		return {'provider' : 'tmdb', 'complete' : True, 'data' : None}

	def _metadataPackImdb(self, imdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		# IMDb currently does not have an efficient/reliable method of retrieving all, or even just many, episodes of a show.
		# Important to add the IMDb ID.
		# There are a bunch of new releases that are only on IMDb and not on other providers, and therefore only has an IMDb.
		# Add the ID, to ensure that the failed pack is written to MetaCache. Otherwise the pack is never cached and is always re-retrieved in the foreground when the season/episode menus are opened on the show.
		return {'provider' : 'imdb', 'complete' : True, 'data' : {'imdb' : imdb, 'id' : {'imdb' : imdb}}}

	def _metadataPackPrepare(self, items):
		if Tools.isArray(items):
			if items and Tools.isArray(items[0]): items = Tools.listFlatten(items, recursive = False)
		else:
			items = [items]
		return items

	def _metadataPackRetrieve(self, items = None, instance = False, quick = None, refresh = False, cache = False, threaded = None):
		try:
			if items:
				# If mutiple seasons/episodes of the same show is passed in, only retrieve the pack once for all of them.
				ids = ['trakt', 'tvdb', 'tmdb', 'imdb']
				items = self._metadataPackPrepare(items = items)
				lookup = Tools.listUnique([{i : item.get(i) for i in ids} for item in items])
				if lookup:
					data = self.metadataPack(items = lookup, quick = quick, refresh = refresh, cache = cache, threaded = threaded)
					if data:
						# Create a dictionary for faster lookups.
						packs = {i : {} for i in ids}
						for i in data:
							for j in ids:
								try: id = i.get('id').get(j)
								except: id = None
								if id: packs[j][id] = MetaPack.instance(pack = i) if instance else i
						return packs
		except: Logger.error()
		return None

	# Add pack data to the show/season/episode items.
	def _metadataPackAggregate(self, items = None, pack = None, data = None, quick = None, refresh = False, cache = False, threaded = None):
		try:
			if items:
				if pack is None: pack = True # Add pack data by default, except if explicitly stated not to (eg: from show menus).
				if pack:
					if data: # Faster if pack was already retrieved previously and all items belong to the same show.
						for item in (items if Tools.isArray(items) else [items]):
							item['pack'] = data
					else:
						values = self._metadataPackPrepare(items = items) # Do not change "items", since they are returened byt the function.
						packs = self._metadataPackRetrieve(items = values, instance = False, quick = quick, refresh = refresh, cache = cache, threaded = threaded)
						if packs:
							for item in values:
								for i in packs.keys():
									try: id = item.get('id').get(i)
									except: id = item.get(i)
									if id:
										try: data = packs.get(i).get(id)
										except: data = None
										if data:
											# Do not create a deep copy of each pack, but only add the reference to the same dictionary.
											# Pack data can get very large, and since it is static/unchangeable, there does not seem be a reason for copying the pack for each item.
											item['pack'] = data
											break
		except: Logger.error()
		return items

	# Lookup the real native season-episode numbers from other numbers, like absolute episodes.
	def _metadataPackLookup(self, items = None, number = None, provider = None, quick = None, refresh = False, cache = False, threaded = None):
		lookup = None
		try:
			if items:
				packs = self._metadataPackRetrieve(items = items, instance = True, quick = quick, refresh = refresh, cache = cache, threaded = threaded)
				if packs:
					input = number or provider
					lookup = {i : {} for i in packs.keys()}
					for item in (items if Tools.isArray(items) else [items]):
						for i in packs.keys():
							try: id = item.get('id').get(i)
							except: id = item.get(i)
							if id:
								try: pack = packs.get(i).get(id)
								except: pack = None
								if pack:
									if not id in lookup[i]: lookup[i][id] = {}
									season = item.get('season')
									episode = item.get('episode')
									original = (season, episode)
									value = pack.lookupStandard(season = season, episode = episode, input = input)
									if value:
										if Tools.isArray(value):
											item['season'] = value[0]
											item['episode'] = value[1]
											lookup[i][id][tuple(value)] = original
										else:
											item['season'] = value
									else:
										lookup[i][id][original] = original
									break
		except: Logger.error()
		return lookup

	# Revert the season/episode numbers back to the original numbers, as requested.
	def _metadataPackNumber(self, items = None, lookup = None, season = None, episode = None, numbering = None, number = None):
		try:
			if items:
				if not numbering is None:
					if not number: number = MetaPack.NumberSequential
					for item in (items if Tools.isArray(items) else [items]):
						try: value = item['number'][number][1]
						except:
							try: value = item[number][1]
							except: value = None
						item['season'] = 1
						item['episode'] = value or 0
				elif lookup:
					for item in (items if Tools.isArray(items) else [items]):
						value = (item.get('season'),) if episode is None else (item.get('season'), item.get('episode'))
						for i in lookup.keys():
							try: found = lookup.get(i).get(item.get(i)).get(value)
							except: found = None

							# NB: Only change the original number if it is not negative.
							# Since the episode Progress menu retrieves 3 "history" items, so the episode number can be negative.
							# In such a case, keep the real looked-up number.
							if found and found[1] >= 0:
								item['season'] = found[0]
								item['episode'] = found[1]
								break
		except: Logger.error()
		return items

	##############################################################################
	# CONTENT
	##############################################################################

	'''
		detail: Retrieve detailed metadata.
			True/None: Retrieve detailed metadata, which takes longer.
			False: Retrieve only basic metadata, like IDs, which is faster.
		quick: How to retrieve the detailed metadata.
			True: Retrieve whatever is in the cache and the rest in the background. Could return no items at all.
			False: Retrieve whatever is in the cache and the rest not at all. Could return no items at all.
			Positive Integer: Retrieve the given number of items in the foreground and the rest in the background.
			Negative Integer: Retrieve the given number of items in the foreground and do not retrieve the rest at all.
		refresh: Refresh the list.
			True: Forcefully refresh the list source data.
			False/None: Do not refresh the list source data, but retrieve it from the cache.
		menu: Load the menu.
			True/None: Load the Kodi directory/menu.
			False: Do not load the Kodi directory/menu, just retrun the items as a list.
		more: Add a next page.
			True/None: Add a 'More' item to the end of the list if available.
			False: Do not add a 'More' item to the end of the list.
	'''
	def content(self, media = None, niche = None, content = None, progress = None, page = None, limit = None, refresh = None, reload = None, internal = None, **parameters):
		if not niche: niche = None # Can be [].

		# Do not retrieve full pack data when loading show menus.
		# This requires more and longer API calls to providers, and more local processing to generate the packs.
		# For most of the shows in the menu, the user is not interested in them and it would be a waste to retrieve packs for them.
		# Only if a season/episode is opened underneath a show, or other calls such as scraping or the context menu, will the full pack data be retrieved.
		# That is: only retrieve/generate packs if they will actually be used.
		# More info at MetaManager.metadata().
		# Update: This was moved from MetaMenu._menuMedia() to here.
		# Otherwise when the mixed Quick menu is opened, it has parameters = {'pack' : False}
		# But when we call MetaManager.reload() after an episode was watched, this function is called with parameters = {}
		# Hence, the _cache() call below is different, since the parameters are different.
		# This makes the main Quick menu not refresh with the latests watched episode.
		if (not media or Media.isMixed(media) or Media.isShow(media)) and not content == MetaManager.ContentProgress:
			pack = parameters.get('pack')
			if pack is None: parameters['pack'] = False

		# Cache the Quick, Progress, and Arrivals menu to make them faster.
		# This reduces menu loading time by +-50%, since the cached data already contains the detailed metadata, filtered and sorted.
		# Only do this for certain menus, only for the first page, and not for niche menus, since each of these calls has to be manually refreshed from reload().
		# Also do not do this for too many types of menus, or beyond page 1, otherwise it requires too much cache disk space.
		# Every time the cache data is retrieved, it will immediately refresh the data in the background ("cacheRefresh").
		if not niche and not page and not limit and not refresh and not internal:
			if (content == MetaManager.ContentProgress and progress == MetaTools.ProgressDefault) or content == MetaManager.ContentArrival or content == MetaManager.ContentQuick:
				# Make sure the parameters are the same for the cache.
				if parameters: parameters = {k : v for k, v in parameters.items() if not v is None} # Can be a dict with all values None if called from progress().
				return self._cache('cacheRefresh', reload, self._content, media = media, niche = niche, content = content, progress = progress, **parameters)

		return self._content(media = media, niche = niche, content = content, progress = progress, page = page, limit = limit, refreshing = refresh, **parameters)

	def _content(self,
		# Use default None values, so that we can pass None in from the script parameters in addon.py.

		media = None,
		niche = None,

		content = None,
		items = None,

		type = None, # Can be used as an alias for the parameters below.
		search = None,
		progress = None,
		arrival = None,
		history = None,
		set = None,
		list = None,
		person = None,

		imdb = None,
		tmdb = None,
		tvdb = None,
		trakt = None,

		title = None,
		season = None,
		episode = None,
		pack = None,

		query = None,
		keyword = None,
		release = None,
		status = None,
		year = None,
		date = None,
		duration = None,
		genre = None,
		language = None,
		country = None,
		certificate = None,
		company = None,
		studio = None,
		network = None,
		award = None,
		gender = None,
		ranking = None,
		rating = None,
		votes = None,

		filter = None,
		sort = None,
		order = None,
		page = None,
		limit = None,
		offset = None,

		provider = None,
		more = None,

		detail = None,
		quick = None,
		refreshing = None, # "refresh" is a parameter for the Cache.

		submenu = None,		# The episode submenu opened from an episode in the Progress menu or from the Series menu.
		special = None,		# Interleave specials between episodes in the Progress menu or from the Series menu, based on their date. SpecialSettings (None): use settings, SpecialInclude (True): include specials, SpecialExclude (False): exclude specials, SpecialReduce ("reduce"): include specials, but reduce the number of specials.

		# Only for internal use.
		filters = None, # Use the "filter" parameter instead if custom filters should be passed in. Read the comments in the function below for more info on this.

		# Allow other parameters to be passed in, which will be ignored.
		# This is useful if some parameters from and old Gaia version are still passed in.
		# Eg: The user has setup a skin widget, which sets the parameters XYZ. In a later Gaia version, parameter XYZ gets renamed/removed. This should not break the widget.
		**parameters
	):
		try:
			data = None
			parameters = {}
			refresh = refreshing
			if filters: filter = filters

			if not content is None: parameters['content'] = content
			if not media is None: parameters['media'] = media
			if not niche is None: parameters['niche'] = niche

			if type:
				if content == MetaManager.ContentSearch: search = type
				elif content == MetaManager.ContentProgress: progress = type
				elif content == MetaManager.ContentArrival: arrival = type
				elif content == MetaManager.ContentHistory: history = type
				elif content == MetaManager.ContentSet: set = type
				elif content == MetaManager.ContentList: list = type
				elif content == MetaManager.ContentPerson: person = type
			if not search is None: parameters['search'] = search
			if not progress is None: parameters['progress'] = progress
			if not arrival is None: parameters['arrival'] = arrival
			if not history is None: parameters['history'] = history
			if not set is None: parameters['set'] = set
			if not list is None: parameters['list'] = list
			if not person is None: parameters['person'] = person

			# IDs can be integers when decoded in MetaMenu.
			# Trakt can have 2 values for the ID for lists (username + list ID).
			if not imdb is None: parameters['imdb'] = imdb if Tools.isArray(imdb) else str(imdb)
			if not tmdb is None: parameters['tmdb'] = tmdb if Tools.isArray(tmdb) else str(tmdb)
			if not tvdb is None: parameters['tvdb'] = tvdb if Tools.isArray(tvdb) else str(tvdb)
			if not trakt is None: parameters['trakt'] = trakt if Tools.isArray(trakt) else str(trakt)

			if not title is None: parameters['title'] = title
			if not season is None: parameters['season'] = int(season)
			if not episode is None: parameters['episode'] = int(episode)
			if not pack is None: parameters['pack'] = pack

			if not query is None: parameters['query'] = query
			if not keyword is None: parameters['keyword'] = keyword
			if not release is None: parameters['release'] = release
			if not status is None: parameters['status'] = status
			if not year is None: parameters['year'] = year
			if not date is None: parameters['date'] = date
			if not duration is None: parameters['duration'] = duration
			if not genre is None: parameters['genre'] = genre
			if not language is None: parameters['language'] = language
			if not country is None: parameters['country'] = country
			if not certificate is None: parameters['certificate'] = certificate
			if not company is None: parameters['company'] = company
			if not studio is None: parameters['studio'] = studio
			if not network is None: parameters['network'] = network
			if not award is None: parameters['award'] = award
			if not gender is None: parameters['gender'] = gender
			if not ranking is None: parameters['ranking'] = ranking
			if not rating is None: parameters['rating'] = rating
			if not votes is None: parameters['votes'] = votes

			if not filter is None: parameters['filter'] = filter
			if not sort is None: parameters['sort'] = sort
			if not order is None: parameters['order'] = order
			if not page is None: parameters['page'] = page
			if not limit is None: parameters['limit'] = limit
			if not offset is None: parameters['offset'] = offset

			if not provider is None: parameters['provider'] = provider
			if not more is None: parameters['more'] = more

			if not search is None: parameters['search'] = search
			if not progress is None: parameters['progress'] = progress

			if not detail is None: parameters['detail'] = detail
			if not quick is None: parameters['quick'] = quick
			if not refresh is None: parameters['refresh'] = refresh

			if not submenu is None: parameters['submenu'] = submenu
			if not special is None: parameters['special'] = special

			# For next pages (more), so that the search/progress type is maintained during paging.
			if not search is None: parameters['search'] = search
			if not progress is None: parameters['progress'] = progress

			if items is None: items = []
			parametersBase = Tools.copy(parameters)

			custom = {
				'filter' : bool(filter),
				'sort' : bool(sort),
				'order' : bool(order),
				'page' : bool(page),
				'limit' : bool(limit),
			}

			hierarchical = Media.isEpisode(media) and not content == MetaManager.ContentEpisode
			if filter is None: filter = {}
			if detail is None: detail = True
			if refresh is None: refresh = False
			if more is True: more = None # Do not force a More item if there are no more titles available.
			next = None
			error = None

			if content == MetaManager.ContentQuick: data = self._quick(**parameters)
			elif content == MetaManager.ContentProgress: data = self._progress(**parameters)
			elif content == MetaManager.ContentHistory: data = self._history(**parameters)
			elif content == MetaManager.ContentArrival: data = self._arrival(**parameters)
			elif content == MetaManager.ContentDiscover: data = self._discover(**parameters)
			elif content == MetaManager.ContentSearch: data = self._search(**parameters)
			elif content == MetaManager.ContentRandom: data = self._random(**parameters)
			elif content == MetaManager.ContentList: data = self._list(**parameters)
			elif content == MetaManager.ContentPerson: data = self._person(**parameters)
			elif content == MetaManager.ContentSeason: data = self._season(**parameters)
			elif content == MetaManager.ContentEpisode: data = self._episode(**parameters)
			elif content == MetaManager.ContentSet: data = self._set(**parameters)

		except: Logger.error()

		if data and Tools.isDictionary(data):
			items = data.get('items')

			# Only use the internal/automatic values, if the user did not manually pass in the parameter.
			if not data.get('media') is None: media = data.get('media')
			if not data.get('sort') is None: sort = data.get('sort')
			if not data.get('order') is None: order = data.get('order')
			if not data.get('limit') is None: limit = data.get('limit') # Do not use the user's custom value here, since it is already passed in to the API calls, and the provider/results determine which value to use here.
			if not data.get('submenu') is None: submenu = data.get('submenu')
			if not data.get('special') is None: special = data.get('special')
			if not more is False and not data.get('more') is None: more = data.get('more')
			if not data.get('pack') is None: pack = data.get('pack')
			if not data.get('next') is None: next = data.get('next')
			if not data.get('error') is None: error = data.get('error')

			# Pass the parameters on to the next page (More), for various reasons.
			#	1. Pass on "query", otherwise the next page will open up the input dialog again.
			#	2. Pass on "provider", otherwise if a non-default provider was selected fromt he context menu to discover/search, the next page will use the default provider again.
			#	3. Any custom parameters passed in by the user (eg: custom limit for an external widget), otherwise the next page will ignore those custom parameters.
			#	4. Any adjusted page/limit/more/etc, since those might be changed by the discover/search functions, like IMDb not having more than 5 pages (maximum 250 items).
			for i in ['query', 'provider']:
				if i in data: parameters[i] = data.get(i)
			for k, v in custom.items():
				if v and k in data: parameters[k] = data.get(k)

			filters = data.get('filter')
			if filters:
				filters = Tools.copy(filters)
				if Tools.isArray(filters): filter = [Tools.update(i, filter, none = False) for i in filters]
				else: filter = Tools.update(filters, filter, none = False)
			if not MetaTools.FilterDuplicate in filter: filter[MetaTools.FilterDuplicate] = True

			# For some weird reason, if we have a "filter" parameter in the plugin://... URL added to xbmcplugin.addDirectoryItems(...), the "filter" parameter gets removed from the URL.
			# That means if we allow the user to pass in custom filters and create a next page item (more), we cannot add the parameter to the URL to also apply those filters for the next page(s).
			# It seems that Kodi removes this parameter. Not sure why. Maybe Kodi uses its own internal "filter" parameter, probably in the left-hand Kodi menu that allows the user to add custom filters for any Kodi menu.
			# However, if we change the name of the parameter (eg: plural "filters"), the parameter is kept.
			# This only seems to be occuring in xbmcplugin.addDirectoryItems(...). If the "filter" parameter is hardcoded in the plugin URL and executed, it is still allowed.
			# Although using "filter" works when calling the plugin URL directly, once the menu loaded, the back button does not work anymore, and only reloads the content of the plugin URL.
			# If we either "optimize" the plugin URL (parameters are base64-encoded), or we use a different parameter name (eg "filters"), then the back navigation works again.
			filters = parameters.get('filter')
			if filters:
				parameters['filters'] = filters
				try: del parameters['filter']
				except: pass

		# Create a copy, since the parameters are adjusted in _process() for More.
		parametersLoad = Tools.copy(parameters)

		# Allow different filters for before and after the manual paging.
		if Tools.isArray(filter):
			filterBefore = filter[0] or {}
			filterAfter = filter[1] or {}
		else:
			filterBefore = filter or {}
			filterAfter = filter or {}

		if Tools.isArray(sort):
			sortBefore = sort[0] or None
			sortAfter = sort[1] or None
		else:
			sortBefore = sort or None
			sortAfter = sort or None

		if Tools.isArray(order):
			orderBefore = order[0] or None
			orderAfter = order[1] or None
		else:
			orderBefore = order or None
			orderAfter = order or None

		if items:
			if not media == Media.List and not media == Media.Person:
				# Do not do for seasons and episodes, since detailed metadata was already retrieved in _season() and _episode().
				if not content == MetaManager.ContentSeason and not content == MetaManager.ContentEpisode:
					# Sort and page before the detail metadata is retrieved.
					if (more is True or (Tools.isInteger(more) and more > 0)) and detail:
						# Do not allow unknown values during filtering for Progress/Arrivals items.
						# Otherwise filtering by eg Anime niche/genre will include all items without a genre, which will only be removed during the 2nd _process() call.
						# All attributes for filtering/sorting should already be set by _metadataSmart(), and those without these attributes are not-yet-cached items down the list.
						unknown = None
						if content == MetaManager.ContentProgress or content == MetaManager.ContentArrival: unknown = False

						full = len(items) == more

						# The MPAA certificate is mostly only available from the detailed metadata.
						if Media.isKid(niche) or Media.isTeen(niche): self.metadata(items = items, pack = pack, quick = -self.limit(media = media, content = content), special = special, hierarchical = hierarchical)

						items = self._process(media = media, items = items, parameters = parameters, filter = filterBefore, sort = sortBefore, order = orderBefore, page = page, limit = limit, more = more, unknown = unknown)

						if filterBefore.get(MetaTools.FilterDuplicate): filterAfter[MetaTools.FilterDuplicate] = False # No need to do again, unlike the other filters which might get new values from the detailed metadata.
						page = False # Already paged, do not do it again.
						if full: more = len(items) # Update smart paging, eg: Anime filtered Progress menu.

					# Do not pass the 'refresh' parameter here, since it should only be used for the list data.
					if detail: items = self.metadata(items = items, pack = pack, quick = quick, next = next, special = special, hierarchical = hierarchical)

			# Also do for lists menu paging.
			items = self._process(media = media, items = items, parameters = parameters, filter = filterAfter, sort = sortAfter, order = orderAfter, page = page, limit = limit, more = more)

		parametersMore = parameters if parameters.get('more') else None
		try: del parametersMore['more']
		except: pass

		return {
			'items'	: items,
			'base'	: parametersBase,
			'load'	: parametersLoad,
			'more'	: parametersMore,
			'error'	: error,
		}

	##############################################################################
	# DISCOVER
	##############################################################################

	def discover(self, media = None, niche = None, keyword = None, release = None, status = None, year = None, date = None, duration = None, genre = None, language = None, country = None, certificate = None, company = None, studio = None, network = None, award = None, ranking = None, rating = None, votes = None, filter = None, sort = None, order = None, page = None, limit = None, provider = None, detail = None, quick = None, refresh = None, more = None, **parameters):
		return self.content(content = MetaManager.ContentDiscover, media = media, niche = niche, keyword = keyword, release = release, status = status, year = year, date = date, duration = duration, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, award = award, ranking = ranking, rating = rating, votes = votes, filter = filter, sort = sort, order = order, page = page, limit = limit, provider = provider, detail = detail, quick = quick, refresh = refresh, more = more)

	def _discover(self, media = None, niche = None, keyword = None, release = None, status = None, year = None, date = None, duration = None, genre = None, language = None, country = None, certificate = None, company = None, studio = None, network = None, award = None, ranking = None, rating = None, votes = None, filter = None, sort = None, order = None, page = None, limit = None, provider = None, refresh = None, **parameters):
		try:
			mediad = media
			if Media.isMixed(media): media = None

			processor = self._processor(media = media, niche = niche, release = release, year = year, date = date, genre = genre, language = language, country = country, certificate = certificate, award = award, ranking = ranking, rating = rating, votes = votes, filter = filter, sort = sort, order = order, page = page, limit = limit or self.limit(media = media, content = MetaManager.ContentDiscover))
			niche = processor.get('niche')
			if filter is None: filter = processor.get('filter')
			if sort is None: sort = processor.get('sort')
			if order is None: order = processor.get('order')
			if page is None: page = processor.get('page')
			if limit is None: limit = processor.get('limit')

			if provider is True or not provider: providers = self.provider(content = MetaManager.ContentDiscover, media = media, niche = niche, release = release, genre = genre, certificate = certificate, company = company, studio = studio, network = network, award = award, ranking = ranking)
			else: providers = provider if Tools.isArray(provider) else [provider]

			for provider in providers:
				if provider == MetaTools.ProviderTrakt:
					# Otherwise paging continues to the next month/year.
					if date:
						traktPage = None
						traktLimit = None
					else:
						traktPage = page
						traktLimit = limit

					data = self._cache('cacheLong', refresh, MetaTrakt.instance().discover, media = media, niche = niche, keyword = keyword, release = release, status = status, year = year, date = date, duration = duration, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, award = award, rating = rating, votes = votes, page = traktPage, limit = traktLimit, internal = True)
					items = data.get('items')

					# Only set these values if the call was successful. Otherwise these adjusted parameters might be used by the fallback provider.
					if items:
						# Sometimes Trakt returns less items than the requested limit, or some items are locally filtered out. Return the initial count to add a next page to the menu (eg: if 49 items are returned, but 50 were requested).
						more = data.get('more')
						if more is False and date: more = len(items) # Since page/limit is set to None above.

						page = traktPage
						limit = traktLimit

						if release: limit = False # Do not limit the items in content(), since releases uses the Trakt calendar and does not return a fixed page size/limit. Eg: the page (aka one month of releases) can have 100+ titles.

				elif provider == MetaTools.ProviderImdb:
					items = self._cache('cacheLong', refresh, MetaImdb.instance().discover, media = media, niche = niche, keyword = keyword, release = release, status = status, year = year, date = date, duration = duration, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, group = award, rating = rating, votes = votes)

					# Only set these values if the call was successful. Otherwise these adjusted parameters might be used by the fallback provider.
					if items:
						more = MetaImdb.LimitDiscover

						# Future releases mostly only have a year, but not a premiered date.
						# Even when retrieving detailed metadata, most of the future titles on IMDb are not even listed on Trakt/TMDb yet.
						if release == MetaProvider.ReleaseFuture:
							try: del filter[MetaTools.FilterTime]
							except: pass

				if items:
					items = self._processSerie(media = media, items = items)
					if Media.isSeason(mediad) or Media.isEpisode(mediad): mediad = Media.Show

					return {
						'items'		: items,

						'filter'	: filter,
						'sort'		: sort,
						'order'		: order,
						'page'		: page,
						'limit'		: limit,

						'provider'	: provider,
						'more'		: more,

						# Never retrieve pack data for discover menus.
						# All menus are either show menus, or season/episode menus emulated as show menus, but any both cases we do not want to retrieve pack data.
						'pack'		: False,
					}
		except: Logger.error()
		return None

	##############################################################################
	# SEARCH
	##############################################################################

	def search(self, media = None, niche = None, search = None, query = None, keyword = None, status = None, year = None, date = None, duration = None, genre = None, language = None, country = None, certificate = None, company = None, studio = None, network = None, award = None, ranking = None, rating = None, votes = None, filter = None, sort = None, order = None, page = None, limit = None, provider = None, detail = None, quick = None, refresh = None, more = None, **parameters):
		return self.content(content = MetaManager.ContentSearch, media = media, niche = niche, search = search, query = query, keyword = keyword, status = status, year = year, date = date, duration = duration, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, award = award, ranking = ranking, rating = rating, votes = votes, page = page, limit = limit, provider = provider, detail = detail, quick = quick, refresh = refresh, more = more)

	def _search(self, media = None, niche = None, search = None, query = None, keyword = None, status = None, year = None, date = None, duration = None, genre = None, language = None, country = None, certificate = None, company = None, studio = None, network = None, award = None, ranking = None, rating = None, votes = None, filter = None, sort = None, order = None, page = None, limit = None, provider = None, refresh = None, **parameters):
		try:
			if media == Media.Set or search == Media.Set: return self._set(set = MetaManager.ContentSearch, media = media, niche = niche, query = query, filter = filter, sort = sort, order = order, page = page, limit = limit, provider = provider, refresh = refresh, **parameters)
			elif media == Media.List or search == Media.List: return self._list(list = MetaManager.ContentSearch, media = media, niche = niche, query = query, filter = filter, sort = sort, order = order, page = page, limit = limit, provider = provider, refresh = refresh, **parameters)
			elif media == Media.Person or search == Media.Person: return self._person(person = MetaManager.ContentSearch, media = media, niche = niche, query = query, filter = filter, sort = sort, order = order, page = page, limit = limit, provider = provider, refresh = refresh, **parameters)

			mediad = media
			if Media.isMixed(media): media = None

			processor = self._processor(media = media, niche = niche, year = year, date = date, genre = genre, language = language, country = country, certificate = certificate, award = award, ranking = ranking, rating = rating, votes = votes, filter = filter, sort = sort, order = order, page = page, limit = limit or self.limit(media = media, content = MetaManager.ContentSearch))
			niche = processor.get('niche')
			if filter is None: filter = processor.get('filter')
			if sort is None: sort = processor.get('sort')
			if order is None: order = processor.get('order')
			if page is None: page = processor.get('page')
			if limit is None: limit = processor.get('limit')
			more = None

			if provider is True or not provider: providers = self.provider(content = MetaManager.ContentSearch, media = media, niche = niche, genre = genre, certificate = certificate, company = company, studio = studio, network = network, award = award, ranking = ranking)
			else: providers = provider if Tools.isArray(provider) else [provider]

			for provider in providers:
				if provider == MetaTools.ProviderTrakt:
					data = self._cache('cacheLong', refresh, MetaTrakt.instance().search, media = media, niche = niche, query = query, keyword = keyword, status = status, year = year, date = date, duration = duration, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, award = award, rating = rating, votes = votes, page = page, limit = limit, internal = True)
					items = data.get('items')

					# Only set these values if the call was successful. Otherwise these adjusted parameters might be used by the fallback provider.
					# Sometimes Trakt returns less items than the requested limit, or some items are locally filtered out. Return the initial count to add a next page to the menu (eg: if 49 items are returned, but 50 were requested).
					if items: more = data.get('more')

				elif provider == MetaTools.ProviderImdb:
					items = self._cache('cacheLong', refresh, MetaImdb.instance().search, media = media, niche = niche, query = query, keyword = keyword, status = status, year = year, date = date, duration = duration, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, group = award, rating = rating, votes = votes)

					# Only set these values if the call was successful. Otherwise these adjusted parameters might be used by the fallback provider.
					if items: more = MetaImdb.LimitDiscover

				elif provider == MetaTools.ProviderTmdb:
					items = self._cache('cacheLong', refresh, MetaTmdb.instance().search, media = media, query = query, page = page)

					# Only set these values if the call was successful. Otherwise these adjusted parameters might be used by the fallback provider.
					if items:
						more = True
						limit = MetaTmdb.LimitFixed # Also set limit.

				if items:
					items = self._processSerie(media = media, items = items)
					if Media.isSeason(mediad) or Media.isEpisode(mediad): mediad = Media.Show

					return {
						'items'		: items,

						'filter'	: filter,
						'sort'		: sort,
						'order'		: order,
						'page'		: page,
						'limit'		: limit,

						'search'	: search,
						'query' 	: query, # Add this for next pages.

						'provider'	: provider,
						'more'		: more,

						# Never retrieve pack data for discover menus.
						# All menus are either show menus, or season/episode menus emulated as show menus, but any both cases we do not want to retrieve pack data.
						# This should not happen, since we do not search seasons or episodes, but still add it, just like in discover().
						'pack'		: False,
					}
		except: Logger.error()
		return None

	##############################################################################
	# PROGRESS
	##############################################################################

	def quick(self, media = None, niche = None, detail = None, quick = None, reload = None, refresh = None, **parameters):
		return self.content(content = MetaManager.ContentQuick, media = media, niche = niche, detail = detail, quick = quick, reload = reload, refresh = refresh, **parameters)

	def _quick(self, media = None, niche = None, refresh = None, **parameters):
		try:
			if media is None or Media.isMixed(media):
				data1 = self._quick(media = Media.Show, niche = niche, refresh = refresh, **parameters)
				data2 = self._quick(media = Media.Movie, niche = niche, refresh = refresh, **parameters)
				if not data1: data1 = {}
				if not data2: data2 = {}
				result = data1 or data2
				if result:
					items1 = data1.get('items') or []
					items2 = data2.get('items') or []

					# Progress: 2
					# History: 1
					# Arrival: 1
					# Recommend: 1
					# Random: 0
					result1 = []
					result2 = []
					for i in [0, 1, 3, 5, 7]:
						try: result1.append(items1[i])
						except: pass
						try: result1.append(items2[i])
						except: pass
					for i in [2, 4, 6, 8, 9]:
						try: result2.append(items1[i])
						except: pass
						try: result2.append(items2[i])
						except: pass
					items = result1 + result2
					items = items[:10]

					result.update({
						'limit'		: (data1.get('limit') or 0) + (data2.get('limit') or 0),
						'more'		: (data1.get('more') or 0) + (data2.get('more') or 0),
						'items'		: items,
					})
					return result
				return None

			items = None

			# Try to avoid the cache function execution (refreshing in the background) if we are reloading mixed menus.
			# More info in reload().
			if self.reloadingMixed(): items = self._cacheRetrieve(self._quickAssemble, media = media, niche = niche)

			# Do not use "cacheRefresh", since this will make the quick menu reload if we open an item within the Quick menu and then navigate back.
			if not items: items = self._cache('cacheQuick', refresh, self._quickAssemble, media = media, niche = niche)

			if items:
				return {
					'items'		: items,
					'next'		: MetaManager.Smart,
					'more'		: False,
					'pack'		: False,
				}
		except: Logger.error()
		return None

	def _quickAssemble(self, media = None, niche = None):
		try:
			timer = Time(start = True)
			result = []

			def _add(count, items, items2 = None):
				counter = 0

				# Add high rated titles.
				for item in items:
					if not item in result:
						rating = item.get('rating')
						if rating and rating >= 7.0:
							result.append(item)
							counter += 1
							if counter >= count: break

				# Fill up if there are still too few.
				if counter < count:
					for item in items or items2:
						if not item in result:
							result.append(item)
							counter += 1
							if counter >= count: break

			from lib.modules.playback import Playback
			playback = Playback.instance()

			countProgress = 3
			countHistory = 2
			countArrival = 2
			countRecommend = 2
			countRandom = 1
			countTotal = countProgress + countHistory + countArrival + countRecommend + countRandom

			current = Time.timestamp()
			month = 2628000 # 1 month.
			start = Playback.percentStart()
			end = Playback.percentEnd()
			total = 0

			# Prevent smart-reloads, since they already happen if the individual progress/arrivals menus are refreshed.
			# Refreshing the quick menu, either from reload() or when the user opens the menu, should never make smart-reloads.
			# Do not use self.mReloadBusy, since at the end of this function we change the value back to True, and do not want to do that to self.mReloadBusy. More info under reload().
			self.mReloadQuick = True

			itemsProgress = self.progress(media = media, niche = niche, detail = False, limit = 150, internal = True) # Internal, in order not to use the outer cache data from content().
			if itemsProgress:
				itemsProgress = itemsProgress.get('items')
				if itemsProgress: total += len(itemsProgress)

			itemsArrival = self.arrival(media = media, niche = niche, detail = False, limit = 150, internal = True)
			if itemsArrival:
				itemsArrival = itemsArrival.get('items')
				if itemsArrival: total += len(itemsArrival)

			itemsRecommend = self.list(media = media, niche = niche, list = MetaTools.ListRecommendation, provider = MetaTools.ProviderTrakt, detail = False, limit = 100, internal = True)
			if itemsRecommend:
				itemsRecommend = itemsRecommend.get('items')
				if itemsRecommend: total += len(itemsRecommend)

			itemsRandom = self.random(media = media, niche = niche, detail = False, limit = 100, internal = True)
			if itemsRandom:
				itemsRandom = itemsRandom.get('items')
				if itemsRandom: total += len(itemsRandom)

			if itemsProgress:
				if Media.isSerie(media):
					# Busy shows recently watched.
					count = 0
					for item in itemsProgress:
						time = self.mTools.time(metadata = item, type = MetaTools.TimeWatched, estimate = False, fallback = False)
						if not time: time = self.mTools.time(metadata = item, type = MetaTools.TimePaused, estimate = False, fallback = False) # Also allow when an episode is still in rpogress without an episode being fully watched.
						if time and (current - time) <= month:
							result.append(item)
							count += 1
							if count >= countProgress: break

					# Fill up if there are not recently watched shows.
					count = len(result)
					if count < countProgress:
						for item in itemsProgress:
							if not item in result:
								result.append(item)
								count += 1
								if count >= countProgress: break

					# Newley released episode for a show not watched in a while.
					count = 0
					for item in itemsProgress:
						if not item in result:
							smart = item.get(MetaManager.Smart)
							if smart:
								released = []

								release = Tools.get(smart, 'pack', 'time', 'season')
								if release:
									for i in release:
										if i and i[0]:
											seconds = current - i[0]
											if seconds >= 0: released.append(seconds)

								# Also add the next episodes time, but only if SxxE01.
								# Should be the same as the one from the pack, but this one can be newer if the pack metadata is outdated.
								next = Tools.get(smart, 'next', 'time')
								if next and item.get('episode') == 1:
									seconds = current - next
									if seconds >= 0: released.append(seconds)

								if released:
									released = min(released)
									if released < month:
										result.append(item)
										count += 1
										if count >= countHistory: break

				else:
					# Unfinished movies.
					count = 0
					for item in itemsProgress:
						progress = item.get('progress')
						if progress and progress >= start and progress <= end:
							result.append(item)
							count += 1
							if count >= countProgress: break

					# Finished movies.
					count = 0
					for item in itemsProgress:
						if not item in result:
							playcount = item.get('playcount')
							if playcount:
								result.append(item)
								count += 1
								if count >= countHistory: break

				# Fill up if there are still too few movies or shows.
				count = len(result)
				if count < (countProgress + countHistory):
					for item in itemsProgress:
						if not item in result:
							result.append(item)
							count += 1
							if count >= (countProgress + countHistory): break

			# New arrivals.
			if itemsArrival:
				items = Tools.listShuffle(itemsArrival[:20]) + itemsArrival[20:]
				_add(countArrival, items, itemsArrival)

			# Trakt recommendations.
			if itemsRecommend:
				# Trakt returns watched/rated items. Trakt can only filter out by watchlist/collection.
				# Remove already watched items.
				itemsRecommend = [i for i in itemsRecommend if not Tools.get(playback.history(media = media, imdb = i.get('imdb'), tmdb = i.get('tmdb'), tvdb = i.get('tvdb'), trakt = i.get('trakt'), quick = True), 'count', 'total')]
				if itemsRecommend:
					itemsRecommend = Tools.listShuffle(itemsRecommend)
					_add(countRecommend, itemsRecommend)

			# Random titles.
			if itemsRandom:
				itemsRandom = Tools.listShuffle(itemsRandom)
				_add(countRandom, itemsRandom)

			# Fill up if there are still too few.
			items = []
			if itemsArrival: items += itemsArrival
			if itemsRecommend: items += itemsRecommend
			if itemsRandom: items += itemsRandom
			if items:
				count = countTotal - len(result)
				if count > 0: _add(count, items)

			result = result[:countTotal]

			if Media.isSerie(media):
				for item in result:
					if item.get('season') is None: item['season'] = 1
					if item.get('episode') is None: item['episode'] = 1

			Logger.log('SMART REFRESH (%s Quick | %dms): Total: %d | Retrieved: %d' % (media.capitalize(), timer.elapsed(milliseconds = True), len(result), total))
			return result
		except: Logger.error()
		finally: self.mReloadQuick = False
		return None

	##############################################################################
	# PROGRESS
	##############################################################################

	def progress(self, media = None, niche = None, progress = None, unknown = None, filter = None, sort = None, order = None, page = None, limit = None, detail = None, quick = None, reload = None, refresh = None, more = None, **parameters):
		if not progress: progress = MetaTools.ProgressDefault # Important for the cache call in content().
		return self.content(content = MetaManager.ContentProgress, media = media, niche = niche, progress = progress, unknown = unknown, filter = filter, sort = sort, order = order, page = page, limit = limit, detail = detail, quick = quick, reload = reload, refresh = refresh, more = more, **parameters)

	def _progress(self, media = None, niche = None, progress = None, unknown = None, filter = None, sort = None, order = None, page = None, limit = None, refresh = None, **parameters):
		try:
			if media is None or Media.isMixed(media):
				data1 = self._progress(media = Media.Show, limit = 0.5, niche = niche, progress = progress, unknown = unknown, filter = filter, sort = sort, order = order, page = page, refresh = refresh, **parameters)
				data2 = self._progress(media = Media.Movie, limit = 0.5, niche = niche, progress = progress, unknown = unknown, filter = filter, sort = sort, order = order, page = page, refresh = refresh, **parameters)
				if not data1: data1 = {}
				if not data2: data2 = {}
				result = data1 or data2
				if result:
					result.update({
						'limit'		: (data1.get('limit') or 0) + (data2.get('limit') or 0),
						'more'		: (data1.get('more') or 0) + (data2.get('more') or 0),
						'items'		: Tools.listInterleave(data1.get('items') or [], data2.get('items') or []),
					})
					return result
				return None

			data = None
			time = self._cacheTime(self._progressAssemble, media = media)

			# Try to avoid the cache function execution (refreshing in the background) if we are reloading mixed menus.
			# More info in reload().
			if self.reloadingMixed(): data = self._cacheRetrieve(self._progressAssemble, media = media)

			# NB: Do not pass in any parameters to the cache call that might cause a separate cache entry to be saved.
			# Eg: niche, progress, filter, sort, order.
			# It might seem intuitive to pass in the niche, or at least the progress type or sorting, such as for ProgressRewatch which is sorted in the reverse order compared to the other progress menus.
			# However, this would establish a separate smart list which has to be updated over time. This should not be a huge issue, since these could quickly retrieve already cached metadata that other progress menus have loaded.
			# But this would mean that every type of progress menu, plus every niche, would create a larger list in the cache, and would each have to update their smart-list individually.
			# A better way is to create a SINGLE progress smart-list (technically two, one for movies, one for shows), containing all progress types, niches etc.
			# Then we only have to maintain a single list, which saves cache disk space, and if the list is updated from eg reload(), it does it for all progress menus.
			# We then filter and sort them outside below, the cache call, which should not take that long, even for larger Trakt histories.
			# This might not be perfect all the time. For instance, ProgressRewatch will only be accurate once a lot of items were smart-loaded, and would initially not have good sorting, since it is sorted in reverse and the first items in this list might not have been smart-loaded for dates yet.
			# However, overall this should improve performance, save disk space, and make things easier.
			if not data: data = self._cache('cacheShort', refresh, self._progressAssemble, media = media)

			if data:
				items = data.get('items')
				if items:
					result = self._progressProcess(items = items, media = media, niche = niche, progress = progress, unknown = unknown, filter = filter, sort = sort, order = order, page = page, limit = limit)

					# Retrieve more detailed metadata, even if the above list is loaded from cache.
					# Do not execute if we only reload the cached menu from reload(), otherwise there are too many requests.
					if not self.reloading() and not self.mModeAccelerate: self._metadataSmartReload(media = media, content = MetaManager.ContentProgress, cache = time, **data)

					result.update({
						'provider'	: MetaTrakt.id(),
						'progress'	: progress,
						'next'		: MetaManager.Smart,
						'more'		: len(result.get('items')),

						# Saves a lot of time and is not needed for the menu, is it?
						# Previously MetaTools.submenuNumber() needed the pack to calculate the negative history number offset, but this is now only done once the episode is actually opened in the menu.
						# Maybe there is some other function in MetaTools or elsewhere that requires the pack - keep your eyes open for things that do not work.
						'pack'		: False,
					})
					return result
		except: Logger.error()
		return None

	def _progressAssemble(self, media):
		timer = Time(start = True)
		from lib.modules.playback import Playback

		# Ratings are only needed for ProgressRewatch sorting, but retrieve them, since all progress types are created from the same data.
		# Use "rating=None" to retrieve the show rating instead of the episode rating.
		itemsNew = Playback.instance().items(media = media, history = True, progress = True, rating = None)

		# Retrieve the current smart-list from cache. To be updated.
		itemsCurrent = self._cacheRetrieve(self._progressAssemble, media = media)
		itemsCurrent = itemsCurrent.get('items') if itemsCurrent else None

		# SortLocal works for all progress menus, except ProgressRewatch, which sorts in reverse order. But this will be done later on.
		return self._metadataSmart(media = media, items = itemsCurrent, new = itemsNew, sort = MetaTools.SortLocal, remove = True, detail = False, timer = timer, content = MetaManager.ContentProgress)

	def _progressProcess(self, items, media = None, niche = None, progress = None, unknown = None, filter = None, sort = None, order = None, page = None, limit = None):
		# All the filtering and sorting here should only take a few milliseconds.
		# It takes about 20ms for Playback.instance(), but this has to be created in any case later on when the menu is loaded.

		# Do not use ProgressPartial for the main Progress menu.
		# For movies it might be fine to exclude those that were watched <1%.
		# But for shows, the user might start a new show, watch 50% of S01E01 and pause/stop. It should then appear on the Progress menu the next load if the user wants to continue the episode the next day.
		if not progress: progress = MetaTools.ProgressDefault

		if unknown is None: unknown = True
		if limit is None: limit = self.limit(media = media, content = MetaManager.ContentProgress)
		elif Tools.isFloat(limit): limit = int(limit * self.limit(media = media, content = MetaManager.ContentProgress))

		# The main progress menu is not filtered at all, but strictly sorted using advanced attributes.
		# The sub progress menus (under Favorites), are strictly filtered, but are then lightly sorted simply based on Trakt user dates (most recent watched/rated/scrobbled/collected dates).
		if sort is None:
			if progress == MetaTools.ProgressDefault: sort = MetaTools.SortLocal
			elif progress == MetaTools.ProgressRewatch: sort = MetaTools.SortRewatch
			else: sort = MetaTools.SortUsed

		# Filter niche Progress menus, like Anime, Originals, and Minis.
		# Filter by the niche list itself, not the derived filters, since this is faster are more reliable than possible incomplete detailed metadata attributes, like secondary companies or genres.
		filter = self._processorNiche(niche = niche, filter = filter, generic = True)

		if items:
			# Filter by progress type.
			# The main progress menu is not filtered, only sorted.
			if not progress ==  MetaTools.ProgressDefault: items = self.mTools.filterProgress(items = items, include = progress)

			# Filter directly by niche, and not the filters create from the niche.
			# Because the cache porgress list has reduced metadata, and not all prarameters might be available here, although most should.
			# Not all items can be filtered out here, if they have not detailed metadata yet.
			# Leave the final sorting to content() after the detailed metadata was retrieved.
			# This should only take a few ms, even for large lists.
			niched = filter.get(MetaTools.FilterNiche) # Only use the company ID, not the company type, otherwise too few titles might be returned.
			if niched:
				# Do not allow unknowns when a niche is specified.
				# Otherwise all shows which were not smart-loaded yet, are added to it.
				# Eg: multi-season shows are listed under Minis Progress menu, just because they do not smart-loaded yet.
				# Even if some are filtered out, after a little while the smart-list will be full enough to list more under the niche menus.
				items = self.mTools.filterNiche(items = items, include = niched, unknown = unknown)

			# Sort here, since this could not be done by metadataSmart(), since it does not know the sort/order parameters.
			if sort or order: items = self._process(media = media, items = items, sort = sort, order = order, page = False, limit = False)

			# The series Rewatch progress menu should be displayed as a show menu and not an episode menu.
			if progress == MetaTools.ProgressRewatch and Media.isSerie(media): items = self.mTools.base(media = Media.Show, items = items)

		return {
			'items'		: items,
			'filter'	: filter,
			'sort'		: [None, sort], # Already sorted here. Only do the secondary sort in content().
			'order'		: [None, order],
			'page'		: page,
			'limit'		: limit,
		}

	##############################################################################
	# HISTORY
	##############################################################################

	def history(self, media = None, niche = None, history = None, filter = None, sort = None, order = None, page = None, limit = None, detail = None, quick = None, refresh = None, more = None, **parameters):
		if not history: history = media
		return self.content(content = MetaManager.ContentHistory, media = media, niche = niche, history = history, filter = filter, sort = sort, order = order, page = page, limit = limit, detail = detail, quick = quick, refresh = refresh, more = more, **parameters)

	def _history(self, media = None, niche = None, history = None, filter = None, sort = None, order = None, page = None, limit = None, **parameters):
		try:
			if media:
				if limit is None:
					# Use the progress menu limit for seasons/episodes, which should be on the lower-end.
					# Since each item in the menu will load large pack data, and all seasons/episodes are from different shows and will therefore have to load its own pack.
					if media == Media.Season or media == Media.Episode: limit = self.limit(content = MetaManager.ContentProgress)
					else: limit = self.limit(media = media)

				from lib.modules.history import History
				items = History().retrieve(media = media, niche = niche, limit = limit, page = page, unique = True, load = media)

				if items:
					return {
						'items'		: items,

						'filter'	: filter,
						'sort'		: sort,
						'order'		: order,
						'page'		: page,
						'limit'		: limit,

						'history'	: history,
						'more'		: len(items) == limit,
					}
		except: Logger.error()
		return None

	##############################################################################
	# ARRIVAL
	##############################################################################

	def arrival(self, media = None, niche = None, unknown = None, filter = None, sort = None, order = None, page = None, limit = None, detail = None, quick = None, reload = None, refresh = None, more = None, **parameters):
		return self.content(content = MetaManager.ContentArrival, media = media, niche = niche, unknown = unknown, filter = filter, sort = sort, order = order, page = page, limit = limit, detail = detail, quick = quick, reload = reload, refresh = refresh, more = more, **parameters)

	def _arrival(self, media = None, niche = None, unknown = None, filter = None, sort = None, order = None, page = None, limit = None, refresh = None, **parameters):
		try:
			if media is None or Media.isMixed(media):
				data1 = self._arrival(media = Media.Show, limit = 0.5, niche = niche, unknown = unknown, filter = filter, sort = sort, order = order, page = page, refresh = refresh, **parameters)
				data2 = self._arrival(media = Media.Movie, limit = 0.5, niche = niche, unknown = unknown, filter = filter, sort = sort, order = order, page = page, refresh = refresh, **parameters)
				if not data1: data1 = {}
				if not data2: data2 = {}
				result = data1 or data2
				if result:
					items = Tools.listInterleave(data1.get('items') or [], data2.get('items') or [])
					items = items[:2000] # Otherwise sorting takes too long.
					result.update({
						'limit'		: (data1.get('limit') or 0) + (data2.get('limit') or 0),
						'more'		: len(items),
						'items'		: items,
					})
					return result
				return None

			data = None
			time = self._cacheTime(self._arrivalAssemble, media = media, niche = niche)

			# Show a notification if an Arrivals menu, or a niche Arrivals menu is created for the first time, since it can make 100+ requests which can take a while.
			if not time: self._jobUpdate(media = media, none = 100, content = MetaManager.ContentArrival)

			# Try to avoid the cache function execution (refreshing in the background) if we are reloading mixed menus.
			# More info in reload().
			if self.reloadingMixed(): data = self._cacheRetrieve(self._arrivalAssemble, media = media, niche = niche)

			if not data: data = self._cache('cacheBasic', refresh, self._arrivalAssemble, media = media, niche = niche)

			if data:
				items = data.get('items')
				if items:
					result = self._arrivalProcess(items = items, media = media, niche = niche, unknown = unknown, filter = filter, sort = sort, order = order, page = page, limit = limit)

					# Retrieve more detailed metadata, even if the above list is loaded from cache.
					# Do not execute if we only reload the cached menu from reload(), otherwise there are too many requests.
					if not self.reloading() and not self.mModeAccelerate: self._metadataSmartReload(media = media, content = MetaManager.ContentArrival, cache = time, **data)

					result.update({
						'next'		: MetaManager.Smart,
						'more'		: len(result.get('items')),

						# Saves a lot of time and is not needed for the menu, is it?
						# Previously MetaTools.submenuNumber() needed the pack to calculate the negative history number offset, but this is now only done once the episode is actually opened in the menu.
						# Maybe there is some other function in MetaTools or elsewhere that requires the pack - keep your eyes open for things that do not work.
						'pack'		: False,
					})
					return result
		except: Logger.error()
		return None

	def _arrivalAssemble(self, media, niche = None):
		timer = Time(start = True)

		itemsNew = self._arrivalRetrieve(media = media, niche = niche)

		# Retrieve the current smart-list from cache. To be updated.
		itemsCurrent = self._cacheRetrieve(self._arrivalAssemble, media = media, niche = niche)
		itemsCurrent = itemsCurrent.get('items') if itemsCurrent else None

		# NB: Do not remove based on the smart list length. Eg: 1000.
		# Otherwise, every time _metadataSmart() is called, a bunch of "new" items are added.
		# At the end of _metadataSmart(), most of these items get removed again, because they are sorted to the bottom of the list (eg: olderish release or low rating/votes) and then get removed by the eg 1000 limit.
		# When _metadataSmart() is called again, these previously-removed items are not in the smart list and are therefore seen as truely "new" items.
		# Then when we smart-load titles from MetaCache, it will always load these previously-removed items, because they are seen as new.
		# This means the smart list is populated very slowley, since it always quick-cache-loads the same items on every refresh, which are then removed again at the end.
		# Instead, keep the entire year's arrivals and only remove them if they are too old.
		# Even with a few thousand titles, this should be less than 2MB storage space.
		remove = 31536000 # 1 year.

		return self._metadataSmart(media = media, items = itemsCurrent, new = itemsNew, sort = MetaTools.SortGlobal, remove = remove, detail = False, timer = timer, content = MetaManager.ContentArrival)

	def _arrivalRetrieve(self, media, niche):

		def _votes(votes):
			return int(votes * 0.1) if niche else votes

		def _add(values, base, **parameters):
			base = Tools.copy(base)
			if parameters: base.update(parameters)
			values.append(base)

		def _forward(year, month):
			return [year - 1, month]

		def _backward(year, month):
			date = [year - 1, month - 1]
			if date[1] < 1:
				date[0] -= 1
				date[1] = 12
			return date

		def _date(date):
			start = [date[0], date[1], 1]
			if date[1] >= 12: end = [date[0] + 1, 1, 1]
			else: end = [date[0], date[1] + 1, 1]
			start = Time.timestamp('%d-%02d-%02d' % tuple(start), format = Time.FormatDate, utc = True)
			end = Time.timestamp('%d-%02d-%02d' % tuple(end), format = Time.FormatDate, utc = True)
			return [start, end]

		def _increase(values, base, date, **parameters):
			_add(values = values, base = base, date = _date(date), **parameters)
			date[1] += 1
			if date[1] > 12:
				date[0] += 1
				date[1] = 1

		def _decrease(values, base, date, **parameters):
			_add(values = values, base = base, date = _date(date), **parameters)
			date[1] -= 1
			if date[1] < 1:
				date[0] -= 1
				date[1] = 12

		############################################
		# INITIALIZATION
		############################################

		# MOVIES
		#	Items: +-2500 (+-5000 with duplicates)
		#	Requests: 122 + niche requests
		# SHOWS
		#	Items: +-2000 (+-4500 with duplicates)
		#	Requests: 77 + niche requests

		movie = Media.isFilm(media)
		show = Media.isSerie(media)
		mini = Media.isMini(niche)

		trakt = MetaTrakt.instance().discover
		imdb = MetaImdb.instance().discover
		tmdb = MetaTmdb.instance().discover

		providers = self.provider(content = MetaManager.ContentDiscover, media = media, niche = niche)
		if not niche or mini: providers.append(MetaTools.ProviderTmdb) # At some point MetaTmdb has to be rewritten to allow proper niches.
		if mini:
			try: providers.remove(MetaTools.ProviderTrakt)
			except: pass

		functions = {
			trakt : MetaTools.ProviderTrakt,
			imdb : MetaTools.ProviderImdb,
			tmdb : MetaTools.ProviderTmdb,
		}

		items = []
		primary = []
		secondary = []
		delete = []

		durationHour12 = 43200
		durationDay3 = 259200
		durationWeek2 = 1209600
		durationWeek3 = 1814400
		durationWeek4 = 2419200
		durationMonth1 = 2628000
		durationMonth3 = 7884000
		durationMonth6 = 15768000
		durationYear1 = 31557600

		year = Time.year()
		month = Time.month()

		# Only retrieve decent titles, since most users will not be interested in bad titles.
		# At the end we retrieve a few of the worst titles.
		if niche:
			best = [3.5, 10.0]
			worst = [0.0, 3.49999]
		else:
			best = [5.0, 10.0]
			worst = [0.0, 4.99999]

		############################################
		# SUMMARY RELEASES
		############################################

		# Most popular releases over the past year.

		timeout = durationMonth1
		time = durationYear1

		# TRAKT
		#	Movies:	250 items (1 request - 250 per request)
		#	Shows:	250 items (1 request - 250 per request)
		base = {
			'function'	: trakt,
			'timeout'	: timeout,
			'rating'	: best,
			'sort'		: MetaTrakt.SortPopular,
			'limit'		: 250,
		}
		_add(values = secondary, base = base, year = year) # Can return future releases.
		_add(values = delete, base = base, year = year - 1)

		# TMDB
		#	Movies:	200 items (10 requests - 20 per request)
		#	Shows:	200 items (10 requests - 20 per request)
		base = {
			'function'	: tmdb,
			'timeout'	: timeout,
			'time'		: time,
			'serie'		: MetaTmdb.SerieMini if mini else True,
			'rating'	: best,
			'votes'		: _votes(10 if show else 100),
			'sort'		: MetaTmdb.SortPopularity,
			'limit'		: MetaTmdb.limit(10),
		}
		_add(values = secondary, base = base)

		# IMDB
		#	Movies:	500 items (2 requests - 250 per request)
		#	Shows:	500 items (2 requests - 250 per request)
		base = {
			'function'	: imdb,
			'timeout'	: timeout,
			'time'		: time,
			'language'	: True, # Otherwise too many Indian titles are returned.
			'rating'	: best,
			'votes'		: _votes(100 if show else 1000),
			'sort'		: MetaImdb.SortPopularity,
		}
		_add(values = primary, base = base, release = MetaImdb.ReleaseHome)
		_add(values = secondary, base = base, release = MetaImdb.ReleaseNew)

		############################################
		# HOME RELEASES
		############################################

		# Most popular digital and physical releases per month over the past year.

		timeout = durationWeek3

		if movie:
			# TRAKT
			#	Movies:	300-700 items (12 requests - 30-70 per request)
			date1 = _forward(year = year, month = month)
			date2 = _backward(year = year, month = month)
			base = {
				'function'	: trakt,
				'timeout'	: timeout,
				'release'	: MetaTrakt.ReleaseHome,
				#'rating'	: best, # No rating, since already few titles are returned.
			}
			for i in range(12):
				_increase(values = primary, base = base, date = date1)
				_decrease(values = delete, base = base, date = date2)

			# TMDB
			#	Movies:	720 items (36 requests - 20 per request)
			date1 = _forward(year = year, month = month)
			date2 = _backward(year = year, month = month)
			base = {
				'function'	: tmdb,
				'timeout'	: timeout,
				'release'	: MetaTmdb.ReleaseHome,
				'serie'		: MetaTmdb.SerieMini if mini else True,
				'rating'	: best,
				'votes'		: _votes(100),
				'sort'		: MetaTmdb.SortPopularity,
				'limit'		: MetaTmdb.limit(3),
			}
			for i in range(12):
				_increase(values = primary, base = base, date = date1)
				_decrease(values = delete, base = base, date = date2)

			# IMDB
			#	Movies:	2500 items (12 requests - 250 per request - more recent months return less than 250)
			date1 = _forward(year = year, month = month)
			date2 = _backward(year = year, month = month)
			base = {
				'function'	: imdb,
				'timeout'	: timeout,
				'release'	: MetaImdb.ReleaseHome,
				'language'	: True, # Otherwise too many Indian titles are returned.
				'rating'	: best,
				'votes'		: _votes(100),
				'sort'		: MetaImdb.SortPopularity,
			}
			for i in range(12):
				_increase(values = primary, base = base, date = date1)
				_decrease(values = delete, base = base, date = date2)

		############################################
		# NEW RELEASES
		############################################

		# Most popular theatrical releases per month over the past year.

		timeout = durationWeek4

		# TRAKT
		#	Movies:	800-2000 items (12 requests - 50-200 per request)
		#	Shows:	450-650 items (12 requests - 20-80 per request)
		date1 = _forward(year = year, month = month)
		date2 = _backward(year = year, month = month)
		base = {
			'function'	: trakt,
			'timeout'	: timeout,
			'release'	: MetaTrakt.ReleaseNew,
			'rating'	: best,
			'votes'		: _votes(30 if show else 50),
		}
		for i in range(12):
			_increase(values = secondary, base = base, date = date1)
			_decrease(values = delete, base = base, date = date2)

		# TMDB
		#	Movies:	480 items (24 requests - 20 per request)
		#	Shows:	480 items (24 requests - 20 per request)
		date1 = _forward(year = year, month = month)
		date2 = _backward(year = year, month = month)
		base = {
			'function'	: tmdb,
			'timeout'	: timeout,
			'release'	: MetaTmdb.ReleaseNew,
			'serie'		: MetaTmdb.SerieMini if mini else True,
			'rating'	: best,
			'votes'		: _votes(10 if show else 100),
			'sort'		: MetaTmdb.SortPopularity,
			'limit'		: MetaTmdb.limit(2),
		}
		for i in range(12):
			_increase(values = secondary, base = base, date = date1)
			_decrease(values = delete, base = base, date = date2)

		############################################
		# SEASON RELEASES
		############################################

		# Most popular new seasons per month over the past year.
		# Unlike the other requests, this retrieves and newly premiered season, not just a new S01.

		timeout = durationWeek3

		if show:
			# TRAKT
			#	Shows:	1000-1400 items (12 requests - 50-180 per request)
			date1 = _forward(year = year, month = month)
			date2 = _backward(year = year, month = month)
			base = {
				'function'	: trakt,
				'timeout'	: timeout,
				'media'		: Media.Season,
				'rating'	: best,
				'votes'		: _votes(20), # Not too low, otherwise 1000+ titles are returned per month.
			}
			for i in range(12):
				_increase(values = primary, base = base, date = date1)
				_decrease(values = delete, base = base, date = date2)

		############################################
		# MINISERIES RELEASES
		############################################

		# Most popular new miniseries per month over the past year.

		timeout = durationMonth1
		time = durationYear1

		if show:
			# TMDB
			#	Shows:	100 items (5 requests - 20 per request)
			base = {
				'function'	: tmdb,
				'timeout'	: timeout,
				'time'		: time,
				'serie'		: MetaTmdb.SerieMini,
				'rating'	: best,
				'votes'		: _votes(20),
				'sort'		: MetaTmdb.SortPopularity,
				'limit'		: MetaTmdb.limit(5),
			}
			_add(values = secondary, base = base)

			# IMDB
			#	Shows:	250 items (1 request - 250 per request)
			base = {
				'function'	: imdb,
				'timeout'	: timeout,
				'niche'		: Media.Mini,
				'time'		: time,
				'language'	: True, # Otherwise too many Indian titles are returned.
				'rating'	: best,
				'votes'		: _votes(50),
				'sort'		: MetaImdb.SortPopularity,
			}
			_add(values = secondary, base = base)

		############################################
		# RECENT RELEASES
		############################################

		# Most popular releases over the past month.

		timeout = durationHour12
		time = durationMonth1

		# TRAKT
		#	Movies:	250-350 items (2 requests - 10-300 per request)
		#	Shows:	100-200 items (2 requests - 100-200 per request)
		base = {
			'function'	: trakt,
			'timeout'	: timeout,
			'time'		: time,
			'rating'	: best,
			'votes'		: _votes(5),
		}
		_add(values = secondary, base = base, release = MetaTrakt.ReleaseNew)
		if movie: _add(values = primary, base = base, release = MetaTrakt.ReleaseHome)
		elif show: _add(values = primary, base = base, release = MetaTrakt.ReleaseNew, media = Media.Season)

		# TMDB
		#	Movies:	120 items (6 requests - 20 per request)
		#	Shows:	60 items (3 requests - 20 per request)
		base = {
			'function'	: tmdb,
			'timeout'	: timeout,
			'time'		: time,
			'serie'		: MetaTmdb.SerieMini if mini else True,
			'rating'	: best,
			'votes'		: _votes(5),
			'sort'		: MetaTmdb.SortPopularity,
			'limit'		: MetaTmdb.limit(3),
		}
		if movie: _add(values = primary, base = base, release = MetaTmdb.ReleaseHome)
		_add(values = secondary, base = base, release = MetaTmdb.ReleaseNew)

		# IMDB
		#	Movies:	250-350 items (2 requests - 30-250 per request)
		#	Shows:	200-300 items (2 requests - 20-250 per request)
		base = {
			'function'	: imdb,
			'timeout'	: timeout,
			'time'		: time,
			'language'	: True, # Otherwise too many Indian titles are returned.
			'rating'	: best,
			'votes'		: _votes(5),
			'sort'		: MetaImdb.SortPopularity,
		}
		_add(values = primary, base = base, release = MetaImdb.ReleaseHome)
		_add(values = secondary, base = base, release = MetaImdb.ReleaseNew)

		############################################
		# WORST RELEASES
		############################################

		# Most popular amongst the worst releases. Other requests above retrieve only better ratings.

		timeout = durationMonth1
		time = durationYear1

		# TRAKT
		#	Movies:	100 items (1 request - 100 per request)
		#	Shows:	100 items (1 request - 100 per request)
		base = {
			'function'	: trakt,
			'timeout'	: timeout,
			'rating'	: worst,
			'votes'		: _votes(100),
			'sort'		: MetaTrakt.SortPopular,
			'limit'		: 100,
		}
		_add(values = secondary, base = base, year = year) # Can return future releases.
		_add(values = delete, base = base, year = year - 1)

		# TMDB
		#	Movies:	20 items (1 request - 20 per request)
		#	Shows:	20 items (1 request - 20 per request)
		base = {
			'function'	: tmdb,
			'timeout'	: timeout,
			'time'		: time,
			'serie'		: MetaTmdb.SerieMini if mini else True,
			'rating'	: worst,
			'sort'		: MetaTmdb.SortVotes,
			'limit'		: MetaTmdb.limit(1),
		}
		_add(values = secondary, base = base)

		# IMDB
		#	Movies:	100 items (1 request - 100 per request)
		#	Shows:	100 items (1 request - 100 per request)
		base = {
			'function'	: imdb,
			'timeout'	: timeout,
			'time'		: time,
			'language'	: True, # Otherwise too many Indian titles are returned.
			'rating'	: worst,
			'sort'		: MetaImdb.SortVotes,
			'limit'		: 100,
		}
		_add(values = secondary, base = base)

		############################################
		# NICHE RELEASES
		############################################

		# Add additional niche content if the user is a regular/frequent viewer.
		# There are already a number of anime titles in the other requests (especially for shows), but add a few extra.

		if not niche:
			nicheRegular = []
			nicheFrequent = []
			niches = {
				Media.Docu		: self.mTools.settingsContentDocu(),
				Media.Short		: self.mTools.settingsContentShort(),
				Media.Family	: self.mTools.settingsContentFamily(),
				Media.Anima		: self.mTools.settingsContentAnima(),
				Media.Anime		: self.mTools.settingsContentAnime(),
				Media.Donghua	: self.mTools.settingsContentDonghua(),
			}
			for k, v in niches.items():
				if v >= MetaTools.ContentFrequent: nicheFrequent.append(k)
				elif v >= MetaTools.ContentRegular: nicheRegular.append(k)

			timeout = durationWeek2
			time = durationMonth3
			for i in nicheFrequent + nicheRegular:
				base = {
					'function'	: imdb,
					'timeout'	: timeout,
					'time'		: time,
					'rating'	: best,
					'votes'		: _votes(10),
					'sort'		: MetaImdb.SortPopularity,
					'niche'		: i,
				}
				_add(values = secondary, base = base, release = MetaImdb.ReleaseNew)

			timeout = durationDay3
			time = durationMonth1
			for i in nicheFrequent:
				base = {
					'function'	: trakt,
					'timeout'	: timeout,
					'time'		: time,
					'votes'		: _votes(3),
					'niche'		: i,
				}
				_add(values = secondary, base = base, release = MetaTrakt.ReleaseNew)
				if movie: _add(values = secondary, base = base, release = MetaTrakt.ReleaseHome)
				elif show: _add(values = secondary, base = base, release = MetaTrakt.ReleaseNew, media = Media.Season)

		############################################
		# RETRIEVE
		############################################

		threads = []
		synchronizer = Semaphore(6)

		# There are two main ways of retrieving the data:
		#	1. Fixed Date Ranges:
		#		Cache entire months or weeks that are only refreshed once in a while.
		#		These calls are for data in the "far" past and will probably not change a lot anymore, and therefore do not have to be refreshed that often.
		#		These use fixed date ranges as parameters to the cached function, so that the cache entry stays the same as time progresses.
		#		For instance, the cache entry for [2024-01-01, 2024-02-01] is the same today as it is next week or next month.
		#	2. Time Spans:
		#		Reretrieve/refresh requests for recent dates more frequently.
		#		This data will probably change more frequently and should be refreshed more often.
		#		These do not use fixed date ranges, but a time span or duration instead.
		#		This means every time the cache is refreshed, the same cache entry gets replaced with the new data, even if the dates are different, saving disk space.
		#		If the date range would be passed in, the parameters to the cache are different each time, meaning a new cache entry would be created every time.
		#		Now the dynamic date range is only calculated INSIDE the cache function execution.
		#		For instance, the cache entry for [7 days] will be different today than tomorrow or the next week, because the internal date range is calculated from the current date.
		for item in primary + secondary: # Add the home releases before the new releases to the results, since they are more likley to have a digitial/physical release date and show up in the menu.
			# Skip unsupported providers for certain niches.
			provider = functions.get(item.get('function'))
			if provider and not provider in providers: continue

			item['items'] = items
			if not 'media' in item: item['media'] = media
			if 'niche' in item: item['niche'] = Media.add(item['niche'], niche)
			else: item['niche'] = niche

			threads.append(Pool.thread(target = self._arrivalCache, kwargs = item, synchronizer = synchronizer, start = True))
		[thread.join() for thread in threads]

		# Many shows can have more than one season premiered within the past year.
		# Eg: tt11612120 S02 and S03.
		# Merge duplicate items by number, to prefer the one with the highest season number.
		# NB: Also merge based on the number of votes.
		# The same title can come from an older cached page with outdated metadata (fewer votes), while the "recent" releases request can return the same title, but with more recent metadata (more votes).
		items = self.mTools.filterDuplicate(items = items, id = True, title = False, number = False, merge = ['number', 'votes'])

		# Trakt summary can return future items.
		items = self.mTools.filterTime(items = items, include = 1, time = MetaTools.TimeLaunch)

		# Start a background thread to delete old unused cached entries.
		# These will eventually be cleared by the cache itself, but if we know they will not be used anymore, we can just as well delete them here.
		for i in delete:
			try: del i['timeout']
			except: pass
		Pool.thread(target = self._arrivalClear, kwargs = {'media' : media, 'niche' : niche, 'items' : delete}, start = True)

		return items

	def _arrivalCache(self, items, function, timeout, media, **parameters):
		def _arrivalCache(result, date = None):
			if result:
				# Smart reduce here already, otherwise the cache for thousands of titles has tons of unnecessary data, filling up disk space.
				result = self._metadataSmartReduce(media = media, items = result, full = False)

				# Titles from IMDb do not have a date.
				# This causes the items to always be "new" in _metadataSmart(), since they are filtered out at the end.
				# Add an estimated date based on the date parameter to ensure they are kept in the smart list.
				if date:
					for item in result:
						if not item.get('time'): item['time'] = {MetaTools.TimeUnknown : date[-1]}

			return result

		if parameters.get('time'):
			def _arrivalCache1(time, **parameters):
				try: offset = parameters.pop('offset')
				except: offset = 0
				end = Time.timestamp() - offset
				parameters['date'] = [Time.past(timestamp = end, seconds = time), end]
				result = function(**parameters)
				return _arrivalCache(result = result, date = parameters.get('date'))
			execute = _arrivalCache1
		else:
			# Randomize the cache timeout with +-8 hours.
			# So that over time, these cache calls are out-of-sync and do not all refresh at the same time.
			# This reduces batch requests to a provider in a short time span.
			# Do not add too much, since with every cache refresh, this value is added.
			if timeout > 172800: timeout += Math.random(start = -28800, end = 28800)

			def _arrivalCache2(**parameters):
				result = function(**parameters)
				return _arrivalCache(result = result, date = parameters.get('date'))
			execute = _arrivalCache2

		data = self._cache('cacheSeconds', None, function = execute, timeout = timeout, media = media, **parameters)
		if data:
			if Media.isSerie(media):
				data = self._processSerie(media = media, items = data)
				for item in data:
					item['media'] = Media.Show # Replace season releases.
					if item.get('season') is None: item['season'] = 1
			items.extend(data)

	def _arrivalClear(self, media, niche, items):
		# Delete old cache entries to save some disk space.
		Time.sleep(5) # Wait for other processes to finish.
		for item in items:
			if not 'media' in item: item['media'] = media
			if 'niche' in item and niche: item['niche'] = Media.add(item['niche'], niche)
			else: item['niche'] = niche
			self._cacheDelete(**item)

	def _arrivalProcess(self, items, media = None, niche = None, unknown = None, filter = None, sort = None, order = None, page = None, limit = None):
		if unknown is None: unknown = True
		if limit is None: limit = self.limit(media = media, content = MetaManager.ContentArrival)
		elif Tools.isFloat(limit): limit = int(limit * self.limit(media = media, content = MetaManager.ContentArrival))
		if sort is None: sort = MetaTools.SortGlobal

		# Filter niche menus, like Anime, Originals, and Minis.
		# Filter by the niche list itself, not the derived filters, since this is faster are more reliable than possible incomplete detailed metadata attributes, like secondary companies or genres.
		filter = self._processorNiche(niche = niche, filter = filter, generic = True)

		if items:
			# Filter out items marked as "removed".
			items = [item for item in items if not (item.get(MetaManager.Smart) or {}).get('removed')]

			# Some items have an episode number, which causes them to be displayed as an episode in the Arrivals menu, instead of a season.
			# This happens spordically with only a few items in the menu, and only the first time the shows Arrivals menu is opened after Kodi launch. If the menu is opened a second time, all are displayed as seasons.
			# Not sure what causes this, maybe some items are getting cached in MetaCache's memory from smart-loading during boot, which are then reused the first time the shows Arrivals menu is opened.
			# Setting the episode number to None seems to solve the problem.
			if Media.isSerie(media):
				for item in items: item['episode'] = None

			# Filter directly by niche, and not the filters create from the niche.
			# Because the cache porgress list has reduced metadata, and not all prarameters might be available here, although most should.
			# Not all items can be filtered out here, if they have not detailed metadata yet.
			# Leave the final sorting to content() after the detailed metadata was retrieved.
			# This should only take a few ms, even for large lists.
			niched = filter.get(MetaTools.FilterNiche) # Only use the company ID, not the company type, otherwise too few titles might be returned.
			if niched:
				# Do not allow unknowns when a niche is specified.
				# Otherwise all shows which were not smart-loaded yet, are added to it.
				# Eg: multi-season shows are listed under Minis Progress menu, just because they do not smart-loaded yet.
				# Even if some are filtered out, after a little while the smart-list will be full enough to list more under the niche menus.
				items = self.mTools.filterNiche(items = items, include = niched, unknown = unknown)

			# There can be shows with 2+ seasons released within a year, and might therefore show up mutiple times in the list.
			# Filter them out and keep the one with the highest season/episode number.
			# This should not be done during smart-loading. Otherwise one of the seasons is always removed, and therefore it ends up in the "new" list again, every time the list is refreshed.
			# Hence, keep both seasons in the smart-list and only filter them out here.
			items = self.mTools.filterDuplicate(items = items, id = True, title = False, number = False, merge = 'number')

			# Reduce the number of items returned.
			# This reduces later filtering/sorting time, and we probably do not need more than this.
			# The items are already sorted, so the first N items should be the best ones.
			# This ensures linear processing time, to counter the smart list growing very large over time.
			items = items[:2000]

		return {
			'items'		: items,
			'filter'	: filter,
			'sort'		: sort,
			'order'		: order,
			'page'		: page,
			'limit'		: limit,
		}

	##############################################################################
	# RANDOM
	##############################################################################

	def random(self, media = None, niche = None, arrival = None, keyword = None, release = None, status = None, year = None, date = None, duration = None, genre = None, language = None, country = None, certificate = None, company = None, studio = None, network = None, award = None, ranking = None, rating = None, votes = None, filter = None, sort = None, order = None, page = None, limit = None, detail = None, quick = None, refresh = None, more = None, **parameters):
		return self.content(content = MetaManager.ContentRandom, media = media, niche = niche, arrival = arrival, keyword = keyword, release = release, status = status, year = year, date = date, duration = duration, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, award = award, ranking = ranking, rating = rating, votes = votes, filter = filter, sort = sort, order = order, page = page, limit = limit, detail = detail, quick = quick, refresh = refresh, more = more)

	def _random(self, media = None, niche = None, arrival = None, filter = None, sort = None, order = None, page = None, limit = None, refresh = None, **parameters):
		try:
			if media:
				if Media.isSerie(media): media = Media.Show # If episodes are scraped the media is Media.Episode.
				items = self._cache('cacheExtended', refresh, self._randomAssemble, media = media, niche = niche, arrival = arrival, **parameters)
				if items:
					return {
						'items'		: items,
						'filter'	: filter,
						'sort'		: sort,
						'order'		: order,
						'page'		: page,
						'limit'		: limit,
						'more'		: len(items),
						'pack'		: False,
					}
		except: Logger.error()
		return None

	def _randomAssemble(self, media = None, niche = None, arrival = None, keyword = None, release = None, status = None, year = None, date = None, duration = None, genre = None, language = None, country = None, certificate = None, company = None, studio = None, network = None, award = None, ranking = None, rating = None, votes = None, **parameters):
		try:
			count = 15 if niche else 10 # Niches, like Anime, return way less items.
			multi = count * 2 # Certain providers might not be supported for certain parameter combinations. Add a few more.
			random = {}

			time = release or year or date or Media.isNew(niche) or Media.isHome(niche) or Media.isAge(niche)

			# Loading a full Arrivals menu takes a lot of requests.
			# Only do this if explicitly requested (arrivals=True) or if it is not a niche.
			if arrival is None and not niche and not time: arrival = True

			# Random year.
			if not time:
				random['year'] = []
				current = Time.year()
				for i in range(multi):
					start = Math.random(start = 1970, end = current)
					random['year'].append([start, min(current, start + Math.random(start = 3, end = 10))])

			# Random genre.
			exclude = [MetaTools.GenreNone, MetaTools.GenreShort, MetaTools.GenreNews, MetaTools.GenreMusic, MetaTools.GenreMusical, MetaTools.GenreSport, MetaTools.GenreSporting, MetaTools.GenreTravel, MetaTools.GenreHoliday, MetaTools.GenreHome, MetaTools.GenreFood, MetaTools.GenreTalk, MetaTools.GenreGame, MetaTools.GenreAward, MetaTools.GenreReality, MetaTools.GenreSoap, MetaTools.GenrePodcast, MetaTools.GenreIndie, MetaTools.GenreSpecial]
			if not genre and not Media.isTopic(niche) and not Media.isMood(niche):
				genres = []
				for k, v in self.mTools.genre().items():
					if v['support'][media] and (v['provider'][MetaTools.ProviderImdb][media] or v['provider'][MetaTools.ProviderTrakt][media]):
						genres.append(k)
				for i in exclude:
					try: genres.remove(i)
					except: pass
				random['genre'] = Tools.listPick(genres, count = multi, remove = True)

			# Random certificate.
			if not certificate and not Media.isAudience(niche):
				certificates = [Audience.CertificateNr]
				if Media.isSerie(media):
					certificates.extend([
						Audience.CertificateTvg,
						Audience.CertificateTvy,
						Audience.CertificateTvy7,
						Audience.CertificateTvpg,
						Audience.CertificateTv13,
						Audience.CertificateTv14,
						Audience.CertificateTvma,
					])
				else:
					certificates.extend([
						Audience.CertificateNr,
						Audience.CertificateG,
						Audience.CertificatePg,
						Audience.CertificatePg13,
						Audience.CertificateR,
						Audience.CertificateNc17,
					])
				random['certificate'] = Tools.listPick(certificates, count = multi)

			if not ranking and not rating and not Media.isQuality(niche):
				random['rating'] = []
				for i in range(multi):
					start = Math.random(start = 4.0, end = 8.0)
					random['rating'].append([Math.round(start, places = 1), Math.round(min(10.0, start + Math.random(start = 1, end = 5)), places = 1)])

			items = []
			threads = []
			for i in range(multi):
				even = i % 2

				kwargs = Tools.copy(parameters)
				kwargs.update({
					'items' : items,
					'media' : media,
					'niche' : niche,
					'keyword' : keyword,
					'release' : release,
					'status' : status,
					'year' : year,
					'date' : date,
					'duration' : duration,
					'genre' : genre,
					'language' : language,
					'country' : country,
					'certificate' : certificate,
					'company' : company,
					'studio' : studio,
					'network' : network,
					'award' : award,
					'ranking' : ranking,
					'rating' : rating,
					'votes' : votes,
				})

				counter = 0
				values = ['year', 'genre', 'certificate', 'rating'] if even else ['year', 'genre', 'rating', 'certificate'] # Eg: Anime, do not always just pick year+certificate.
				for j in values:
					value = random.get(j)
					if value:
						counter += 1
						kwargs[j] = value[i]
						if counter >= 2: break

				# Sometimes use Trakt and sometimes IMDb.
				# Switch provider if a genre is not supported, otherwise IMDb will make a requests without a genre.
				provider = [MetaTools.ProviderTrakt, MetaTools.ProviderImdb] if even else [MetaTools.ProviderImdb, MetaTools.ProviderTrakt]
				if kwargs.get('genre') and not self.mTools.genre(genre = kwargs.get('genre'))['provider'][provider[0]][media]: provider = [provider[1], provider[0]]

				# Remove unsupported providers for certain combinations.
				# Eg: Only use IMDb, but not Trakt, for random Award Winners.
				providers = self.provider(**kwargs)
				provider = [i for i in provider if i in providers]
				if not provider: continue

				kwargs['provider'] = provider

				if not votes and not Media.isPrestige(niche) and not Media.isPopular(niche) and not Media.isUnpopular(niche) and not Media.isViewed(niche):
					kwargs['votes'] = 250 if provider[0] == MetaTools.ProviderImdb else 50

				# Although we do not specifically search by these genres, these genres can still be returned if they fall within any of the other parameters.
				# This can cause a lot of game/talk shows, etc to appear in the list.
				# Specifically exclude these genres in the query.
				value = kwargs.get('genre')
				value = [value] if value else []
				kwargs['genre'] = value + ['-' + i for i in exclude]

				threads.append(Pool.thread(target = self._randomDiscover, kwargs = kwargs, start = True))
				if len(threads) >= count: break

			if arrival:
				kwargs = Tools.copy(kwargs)
				for i in ['release', 'year', 'date', 'provider']:
					try: del kwargs[i]
					except: pass
				threads.append(Pool.thread(target = self._randomArrival, kwargs = kwargs, start = True))

			[thread.join() for thread in threads]

			if items:
				items = Tools.listShuffle(items)
				return items
		except: Logger.error()
		return None

	def _randomDiscover(self, items, **parameters):
		result = self._discover(**parameters)
		if result:
			result = result.get('items')
			if result: items.extend(result)

	def _randomArrival(self, items, **parameters):
		result = self._arrival(**parameters)
		if result:
			result = result.get('items')
			if result: items.extend(result[:500])

	##############################################################################
	# SET
	##############################################################################

	def set(self, set = None, tmdb = None, title = None, year = None, query = None, filter = None, sort = None, order = None, page = None, limit = None, provider = None, detail = None, quick = None, refresh = None, more = None, **parameters):
		return self.content(content = MetaManager.ContentSet, media = Media.Set, set = set, tmdb = tmdb, title = title, year = year, query = query, filter = filter, sort = sort, order = order, page = page, limit = limit, provider = provider, detail = detail, quick = quick, refresh = refresh, more = more)

	def _set(self, set = None, tmdb = None, title = None, year = None, query = None, filter = None, sort = None, order = None, page = None, limit = None, provider = None, detail = None, quick = None, refresh = None, more = None, **parameters):
		try:
			media = Media.Set
			processor = self._processor(media = media, filter = filter, sort = sort, order = order, page = page, limit = limit or self.limit(media = media, content = MetaManager.ContentSet))
			if filter is None: filter = processor.get('filter')
			if sort is None: sort = processor.get('sort')
			if order is None: order = processor.get('order')
			if page is None: page = processor.get('page')
			if limit is None: limit = processor.get('limit')

			mediad = media
			items = None
			parameters = {}
			function = None
			timeout = 'cacheExtended'

			alphabetic = 0
			discover = set == MetaTools.SetDiscover or set == MetaTools.SetArrival or set == MetaTools.SetPopular or set == MetaTools.SetRandom
			if set == MetaTools.SetAlphabetic:
				alphabetic = 1
				discover = True
			if not discover and set:
				set = str(set) # Alphabetic integers are converted to int.
				if len(set) == 1:
					set = set.lower()
					alphabetic = 2
					discover = True

			if not provider: provider = MetaTools.ProviderTmdb

			if provider == MetaTools.ProviderTmdb:
				instance = MetaTmdb.instance()

				# Items of a set.
				if tmdb:
					item = self.metadataSet(tmdb = tmdb, refresh = refresh)
					if item:
						mediad = Media.Movie
						items = Tools.copy(item.get('part')) # Since they will get edited.
						more = True
				elif discover:
					function = instance.discoverSet
					more = True
				elif set == MetaManager.ContentSearch:
					function = instance.searchSet
					parameters['query'] = query
					limit = MetaTmdb.LimitFixed
					more = True

			if function: items = self._cache(timeout, refresh, function, **parameters)

			if items:
				if alphabetic:
					for i in items: i['sort'] = Tools.replaceNotAlphaNumeric(i.get('title'), '').strip().lower()
					if alphabetic == 2:
						if set == '_': items = [i for i in items if not i['sort'] or not(i['sort'][0].isascii() or i['sort'][0].isdigit())]
						else: items = [i for i in items if i['sort'].startswith(set)]
					items = Tools.listSort(items, key = lambda i : i['sort'] or 'ZZZZZZZZZZZZZZZZZZ')

				elif set == MetaTools.SetArrival:
					# Assume the most recently added sets are new ones.
					# Many are not that new, many are porn, and most have no images or other metadata.
					items = Tools.listReverse(items)

				elif set == MetaTools.SetRandom:
					items = Tools.listShuffle(items)

				if more is True: more = len(items)

				return {
					'items'		: items,
					'media'		: mediad,
					'set'		: set,

					'filter'	: filter,
					'sort'		: sort,
					'order'		: order,
					'page'		: page,
					'limit'		: limit,
					'more'		: more,
				}
		except: Logger.error()
		return None

	##############################################################################
	# LIST
	##############################################################################

	def list(self, media = None, niche = None, list = None, imdb = None, tmdb = None, tvdb = None, trakt = None, query = None, status = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, company = None, studio = None, network = None, rating = None, votes = None, filter = None, sort = None, order = None, page = None, limit = None, provider = None, detail = None, quick = None, refresh = None, more = None, **parameters):
		return self.content(content = MetaManager.ContentList, media = media, niche = niche, list = list, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, query = query, status = status, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, rating = rating, votes = votes, filter = filter, sort = sort, order = order, page = page, limit = limit, provider = provider, detail = detail, quick = quick, refresh = refresh, more = more)

	def _list(self, media = None, niche = None, list = None, imdb = None, tmdb = None, tvdb = None, trakt = None, query = None, status = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, company = None, studio = None, network = None, rating = None, votes = None, filter = None, sort = None, order = None, page = None, limit = None, provider = None, refresh = None, more = None, **parameters):
		try:
			if media:
				processor = self._processor(media = media, niche = niche, year = year, genre = genre, language = language, country = country, certificate = certificate, rating = rating, votes = votes, filter = filter, sort = sort, order = order, page = page, limit = limit or self.limit(media = media, content = MetaManager.ContentList))
				niche = processor.get('niche')
				if filter is None: filter = processor.get('filter')
				if sort is None: sort = processor.get('sort')
				if order is None: order = processor.get('order')
				if page is None: page = processor.get('page')
				if limit is None: limit = processor.get('limit')

				parameters = {}
				function = None
				timeout = 'cacheMedium'
				mediad = media
				error = None
				discover = list in [MetaManager.ContentSearch, MetaTools.ListArrival, MetaTools.ListQuality, MetaTools.ListAward, MetaTools.ListReal, MetaTools.ListBucket, MetaTools.ListMind]

				if not provider:
					if trakt: provider = MetaTools.ProviderTrakt
					elif imdb: provider = MetaTools.ProviderImdb
					elif discover: provider = MetaTools.ProviderTrakt
					elif list in [MetaTools.ListDiscover, MetaTools.ListPopular, MetaTools.ListTrending, MetaTools.ListOfficial]: provider = MetaTools.ProviderTrakt

				if provider == MetaTools.ProviderTrakt:
					instance = MetaTrakt.instance()

					# Items of a list.
					if trakt:
						function = instance.list
						timeout = 'cacheShort'
						parameters['media'] = media
						parameters['niche'] = niche
						if Tools.isArray(trakt):
							parameters['user'] = trakt[0]
							parameters['id'] = trakt[1]

							# Only use "cacheRefresh" if we use paging for Trakt lists.
							# Currently all list items are retrieved at once without paging, to allow for proper local sorting.
							# Since these requests are larger and take longer, cache them for longer.
							#timeout = 'cacheRefresh'
							timeout = 'cacheShort' if trakt[0] == instance.accountUser() else 'cacheLong'
						else:
							parameters['id'] = trakt

						# We do not page for Trakt lists anymore.
						# Retrieve all (or at least up to 2000) items from the lsit in one go.
						# This allows for proper sorting across the entire list, instead of sub-par sorting over a single page.
						# Check MetaTrakt.LimitList for more info.
						#parameters['page'] = page
						#parameters['limit'] = limit
						parameters['page'] = None
						parameters['limit'] = MetaTrakt.LimitList
						more = True

					# Search for lists.
					elif list == MetaManager.ContentSearch:
						niche = media
						media = Media.List
						function = instance.search
						timeout = 'cacheExtended'
						parameters['media'] = media
						parameters['query'] = query
						parameters['page'] = page
						parameters['limit'] = limit

					# Predefined list search.
					elif discover:
						include = []
						if list == MetaTools.ListArrival:
							include = ['new', 'recent', 'latest', 'arrival']
						elif list == MetaTools.ListQuality:
							include = ['best', 'top', 'good', 'great', 'greatest', 'perfect']
						elif list == MetaTools.ListAward:
							include = ['award', 'winner']
							if Media.isMovie(media): include.extend(['oscar'])
							elif Media.isSerie(media): include.extend(['emmy', 'emmies'])
							include.extend(['golden globe', 'best picture', 'best script', 'best screenplay', 'best director'])
						elif list == MetaTools.ListReal:
							include = ['true story', 'truestory', 'true event', 'trueevent', 'real story', 'realstory', 'real event', 'realevent']
						elif list == MetaTools.ListBucket:
							include = ['bucket', 'bucketlist', 'mustwatch', 'must watch']
						elif list == MetaTools.ListMind:
							include = ['mindfuck', 'mind fuck', 'brainfuck', 'brain fuck', 'mindbending', 'mind bending', 'mindblowing', 'mind blowing', 'plot twist', 'weird']

						exclude = ['people']
						if Media.isMovie(media): exclude.extend(['tv', 'television', 'tvshow', 'show', 'serie', 'season', 'episode'])
						elif Media.isSerie(media): exclude.extend(['movie', 'film', 'cinema', 'theater'])

						include = ['"%s"' % i for i in include]
						exclude = ['!*%s*' % i for i in exclude]
						query = '(%s) && %s' % (' || '.join(include), ' && '.join(exclude))

						niche = media
						media = Media.List
						function = instance.search
						timeout = 'cacheExtended'
						parameters['media'] = media
						parameters['query'] = query
						parameters['page'] = page
						parameters['limit'] = limit

					# Lists of lists.
					elif list in [MetaTools.ListPersonal, MetaTools.ListLike, MetaTools.ListComment, MetaTools.ListCollaboration, MetaTools.ListDiscover, MetaTools.ListPopular, MetaTools.ListTrending]:
						niche = media
						media = Media.List
						function = instance.lists
						timeout = 'cacheExtended' if list in [MetaTools.ListDiscover, MetaTools.ListPopular, MetaTools.ListTrending] else 'cacheRefresh'
						parameters['list'] = MetaTools.ListPopular if list == MetaTools.ListDiscover else list
						if list in [MetaTools.ListPersonal, MetaTools.ListCollaboration]:
							more = True
						else:
							parameters['page'] = page
							parameters['limit'] = limit

					# Official Trakt lists. Currently seems to only be movie collections.
					elif list == MetaTools.ListOfficial:
						niche = media
						media = Media.List
						function = instance.search
						timeout = 'cacheExtended'
						parameters['media'] = media
						parameters['list'] = list
						parameters['page'] = page
						parameters['limit'] = limit

					# Trakt user lists.
					else:
						parameters['media'] = media
						if list in [MetaTools.ListCalendar, MetaTools.ListProgress] and Media.isSerie(media): parameters['media'] = mediad = Media.Episode
						parameters['niche'] = niche

						if list in [MetaTools.ListRecommendation, MetaTools.ListCalendar, MetaTools.ListCollection, MetaTools.ListHistory]:
							more = True
						else:
							parameters['page'] = page
							parameters['limit'] = limit

						parameters.update({
							'status' : status,
							'year' : year,
							'duration' : duration,
							'genre' : genre,
							'language' : language,
							'country' : country,
							'certificate' : certificate,
							'company' : company,
							'studio' : studio,
							'network' : network,
							'rating' : rating,
							'votes' : votes,
							'sort' : sort,
							'order' : order,
						})

						if list == MetaTools.ListRecommendation:
							function = instance.recommendation
							timeout = 'cacheExtended'
							parameters['collection'] = False # Titles collected are probably ones that were already watched.
							parameters['watchlist'] = True # Titles on the watchlist are probably ones that were not watched yet.
							more = MetaTrakt.LimitRecommendation
						elif list == MetaTools.ListCalendar:
							function = instance.release
							timeout = 'cacheMedium'
							if Media.isSerie(media):
								parameters['user'] = True
								parameters['release'] = False
							else:
								parameters['user'] = True
								parameters['release'] = MetaTrakt.ReleaseNew

							# Do not do this, since it will cause the request not to be cached, since the timestamps are different every time we make the call.
							#parameters['date'] = [Time.past(years = 1, utc = True), Time.timestamp(utc = True)]
							date = Time.format(format = Time.FormatDate) + ' 23:59:59'
							timestamp = Time.timestamp(date, format = Time.FormatDateTime, utc = True)
							parameters['date'] = [Time.past(timestamp = timestamp, years = 1, utc = True), timestamp]
						elif list == MetaTools.ListWatchlist:
							function = instance.listWatch
							timeout = 'cacheShort'
						elif list == MetaTools.ListFavorite:
							function = instance.listFavorite
							timeout = 'cacheShort'
						elif list == MetaTools.ListCollection:
							function = instance.listCollection
							timeout = 'cacheShort'
						elif list == MetaTools.ListRating:
							function = instance.listRating
							timeout = 'cacheQuick'
						elif list == MetaTools.ListHistory:
							function = instance.listWatched # Not "listHistory", which also contains scrobbles and checkins.
							timeout = 'cacheQuick'
						elif list == MetaTools.ListProgress:
							function = instance.listProgress
							timeout = 'cacheQuick'
						elif list == MetaTools.ListHidden:
							function = instance.listHidden
							timeout = 'cacheExtended'

				elif provider == MetaTools.ProviderImdb:
					instance = MetaImdb.instance()

					# Items of a list.
					if imdb:
						function = instance.list
						timeout = 'cacheQuick'
						if Tools.isArray(imdb):
							if len(imdb) > 1: timeout = 'cacheRefresh'
							imdb = imdb[-1] # User ID + list ID can be passed in.
						parameters.update({
							'media' : media,
							'id' : imdb,
							'year' : year,
							'genre' : genre,
							'rating' : rating,
							'votes' : votes,
						})

					# Lists of lists.
					elif list == MetaTools.ListPersonal:
						niche = media
						media = Media.List
						function = instance.lists
						timeout = 'cacheQuick'

					# IMDb user lists.
					else:
						if list == MetaTools.ListWatchlist: function = instance.listWatch
						elif list == MetaTools.ListRating: function = instance.listRating
						elif list == MetaTools.ListCheckin: function = instance.listCheckin
						timeout = 'cacheShort'
						parameters.update({
							'media' : media,
							'year' : year,
							'genre' : genre,
							'rating' : rating,
							'votes' : votes,
						})

				items = self._cache(timeout, refresh, function, **parameters) if function else None

				if items == MetaImdb.Privacy:
					self._cacheDelete(function, **parameters)
					error = MetaImdb.Privacy
					items = None
					more = None

				if items:
					if more is True: more = len(items)

					for item in items:
						if mediad == Media.Episode and not media == Media.List:
							item['media'] = Media.Show

							# Aggregate these attributes, otherwise the menu (eg Trakt Calendar) shows the details for the show, instead of the episode.
							aggregate = {}
							for i in ['title', 'originaltitle', 'tagline', 'plot', 'year', 'premiered', 'aired', 'time', 'rating', 'votes', 'voting', 'duration', 'status']:
								value = item.get(i)
								if value: aggregate[i] = value
							item['aggregate'] = aggregate

						item['niche'] = niche # Used in MetaTools.command() to determine which media items to retrieve from the list.

					# There are a bunch of users that spam the Trakt lists, probably to show up in addon menus.
					# These occasionally pop up in the various Trakt list discoveries (eg: New Arrivals).
					#	https://trakt.tv/search/lists?query=call%20girls
					#	Eg: Dubailand Call Girls +971505700000 Indian Call Girls ...
					if discover:
						items = [item for item in items if not Regex.match(data = item.get('title'), expression = 'call.?girl.*\d', cache = True)]
						more = True # Else the next page does not show if we filter out some itmes.

				# Also return if there are no items. To return the MetaImdb.Privacy error.
				return {
					'items'		: items,
					'media'		: media,
					'error'		: error,
					'list'		: list,

					'filter'	: filter,
					'sort'		: sort,
					'order'		: order,
					'page'		: page,
					'limit'		: limit,
					'more'		: more,

					'pack'		: False,
				}
		except: Logger.error()
		return None

	##############################################################################
	# PERSON
	##############################################################################

	def person(self, media = None, niche = None, person = None, imdb = None, tmdb = None, tvdb = None, trakt = None, query = None, gender = None, award = None, filter = None, sort = None, order = None, page = None, limit = None, provider = None, detail = None, quick = None, refresh = None, more = None, **parameters):
		return self.content(content = MetaManager.ContentPerson, media = media, niche = niche, person = person, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, query = query, gender = gender, award = award, filter = filter, sort = sort, order = order, page = page, limit = limit, provider = provider, detail = detail, quick = quick, refresh = refresh, more = more)

	def _person(self, media = None, niche = None, person = None, imdb = None, tmdb = None, tvdb = None, trakt = None, query = None, gender = None, award = None, filter = None, sort = None, order = None, page = None, limit = None, provider = None, refresh = None, more = None, **parameters):
		try:
			if media:
				processor = self._processor(media = media, niche = niche, filter = filter, sort = sort, order = order, page = page, limit = limit or self.limit(media = media, content = MetaManager.ContentPerson))
				niche = processor.get('niche')
				if filter is None: filter = processor.get('filter')
				if sort is None: sort = processor.get('sort')
				if order is None: order = processor.get('order')
				if page is None: page = processor.get('page')
				if limit is None: limit = processor.get('limit')

				parameters = {}
				function = None
				timeout = 'cacheExtended'

				if person in [MetaTools.PersonFilmmaker, MetaTools.PersonCreator, MetaTools.PersonDirector, MetaTools.PersonCinematographer, MetaTools.PersonWriter, MetaTools.PersonProducer, MetaTools.PersonEditor, MetaTools.PersonComposer, MetaTools.PersonActor, MetaTools.PersonActress]:
					imdb = {
						Media.Movie : {
							MetaTools.PersonFilmmaker		: 'ls026411399',
							MetaTools.PersonDirector		: 'ls000005319',
							MetaTools.PersonCinematographer	: 'ls000045131',
							MetaTools.PersonWriter			: 'ls026034645',
							MetaTools.PersonProducer		: 'ls009401127',
							MetaTools.PersonEditor			: 'ls020798362',
							MetaTools.PersonComposer		: 'ls026034696',
							MetaTools.PersonActor			: 'ls000005354',
							MetaTools.PersonActress			: 'ls000005315',
						},
						Media.Show : {
							MetaTools.PersonCreator			: 'ls062274560',
							MetaTools.PersonDirector		: 'ls059167873',
							MetaTools.PersonCinematographer	: 'ls075157401',
							MetaTools.PersonWriter			: 'ls059167873',
							MetaTools.PersonProducer		: 'ls098127847',
							MetaTools.PersonComposer		: 'ls068448237',
							MetaTools.PersonActor			: 'ls046978814',
							MetaTools.PersonActress			: 'ls082848195',
						},
					}[media][person]

				if not provider:
					if trakt: provider = MetaTools.ProviderTrakt
					elif imdb: provider = [MetaTools.ProviderImdb, MetaTools.ProviderTrakt] # Trakt can also search by IMDb ID.
				if provider is True or not provider: providers = self.provider(content = MetaManager.ContentPerson, gender = gender, award = award)
				else: providers = provider if Tools.isArray(provider) else [provider]

				for provider in providers:
					if provider == MetaTools.ProviderTrakt:
						instance = MetaTrakt.instance()

						# Get titles for a person.
						if trakt or imdb:
							function = instance.person
							parameters['media'] = media
							parameters['id'] = trakt or imdb
							more = True

						# Search for people.
						elif person == MetaManager.ContentSearch:
							niche = media
							media = Media.Person
							function = instance.search
							parameters['media'] = media
							parameters['query'] = query
							parameters['page'] = page
							parameters['limit'] = limit

						# Discover people. Does not have images.
						elif person == MetaTools.PersonDiscover:
							niche = media
							media = Media.Person
							function = instance.person
							parameters['media'] = media
							parameters['page'] = page
							parameters['limit'] = limit

					elif provider == MetaTools.ProviderImdb:
						instance = MetaImdb.instance()

						# Get titles for a person.
						if imdb:
							if instance.idType(imdb) == MetaImdb.IdList:
								niche = media
								media = Media.Person
								function = instance.list
								parameters['media'] = media
								parameters['id'] = imdb
								more = True
							else:
								function = instance.discover
								parameters['media'] = media
								parameters['id'] = imdb
								more = True

						# Search for people.
						elif person == MetaManager.ContentSearch:
							niche = media
							media = Media.Person
							function = instance.searchPerson
							more = True
							parameters['query'] = query

						# Discover people.
						elif person == MetaTools.PersonDiscover:
							niche = media
							media = Media.Person
							function = instance.discoverPerson
							more = True
							if gender: parameters['gender'] = gender
							if award: parameters['group'] = award

					items = self._cache(timeout, refresh, function, **parameters) if function else None

					if items:
						if more is True: more = len(items)

						for item in items:
							item['niche'] = niche # Used in MetaTools.command() to determine which media items to retrieve from the list.

						return {
							'items'		: items,
							'media'		: media,
							'person'	: person,

							'filter'	: filter,
							'sort'		: sort,
							'order'		: order,
							'page'		: page,
							'limit'		: limit,
							'more'		: more,

							'pack'		: False,
						}
		except: Logger.error()
		return None

	##############################################################################
	# SEASON
	##############################################################################

	def season(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, quick = None, refresh = None, **parameters):
		return self.content(content = MetaManager.ContentSeason, media = Media.Season, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, quick = quick, refresh = refresh)

	def _season(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, quick = None, refresh = None, **parameters):
		try:
			show = self.metadataShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, quick = quick, refresh = refresh)
			if show:
				items = self.metadataSeason(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, quick = quick, refresh = refresh, hint = {'pack' : show.get('pack') or show.get('packed')})
				if items:
					pack = MetaPack.instance(pack = show.get('pack'))
					countSeason = pack.countSeasonOfficial()
					countSpecial = pack.countEpisodeSpecial()
					countOfficial = pack.countEpisodeOfficial()
					countSeasonUniversal = pack.countSeasonUniversal()

					niche = show.get('niche')
					specialStory = pack.durationMaximumSpecial(default = 0) > (pack.durationMeanOfficial(default = 0) * 0.8) # At least one longer special.
					absoluteDefault = countSeason > 1 and pack.numberLastStandardEpisode(season = 1) == pack.numberLastSequentialEpisode(season = 1) # Eg: Dragon Ball Super (Trakt vs TVDb).
					absoluteNiche = Media.isAnime(niche) or Media.isDonghua(niche)

					index = -1
					for i in range(len(items)):
						if items[i]['season'] == 0:
							index = i
							break

					setting = self.mTools.settingsShowSpecial()
					if not(setting == 3 or (setting == 2 and countSpecial) or (setting == 1 and specialStory)):
						if index >= 0:
							items.pop(index)
							index = -1

					# Use the natively calculated Sequential instead of the Absolute order.
					# In most cases they are exactly the same.
					# But in some cases the Absolute numbering is completely screwed up. Eg: House.
					# Place the Absolute menu 2nd, since it shares details with the Series menu (eg: watched status, user rating, etc).
					if countSeason: # Not for titles only available on IMDb.
						setting = self.mTools.settingsShowAbsolute()
						if setting == 3 or (setting == 2 and (absoluteDefault or absoluteNiche)) or (setting == 1 and absoluteDefault):
							sequential = Tools.copy(show)
							sequential['sequential'] = True
							#items.insert(0 if index < 0 else (index + 1), sequential) # Placed between Specials and S01.
							items.insert(0, sequential) # Placed between Series and Specials.

					# Some shows only available on IMDb, but not other providers, will have no pack data, and therefore not countSpecial or countOfficial (eg: tt31566242, tt30346074).
					# Still show the Series menu if there is at least a season.
					setting = self.mTools.settingsShowSerie()
					if setting == 3 or (setting == 2 and (countSeason or countSeasonUniversal or countSpecial or countOfficial)) or (setting == 1 and (countSpecial and countOfficial)):
						items.insert(0, show)
				return {'items' : items}
		except: Logger.error()
		return None

	##############################################################################
	# EPISODE
	##############################################################################

	def episode(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, episode = None, page = None, limit = None, quick = None, refresh = None, submenu = None, special = None, **parameters):
		return self.content(content = MetaManager.ContentEpisode, media = Media.Episode, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, episode = episode, page = page, limit = limit, quick = quick, refresh = refresh, submenu = submenu, special = special)

	def _episode(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, episode = None, page = None, limit = None, quick = None, refresh = None, submenu = None, special = None, **parameters):
		try:
			if not season is None:
				more = None

				number = None
				if self.mTools.submenuIsSequential(submenu = submenu): number = MetaPack.NumberSequential
				elif self.mTools.submenuIsAbsolute(submenu = submenu): number = MetaPack.NumberSequential
				elif self.mTools.submenuIsSerie(submenu = submenu): number = MetaPack.NumberSerie

				# This is important if the last episode in an Episode submenu is the last episode of S01 of that show.
				# MetaTools.submenuNumber() will then increment the episode number by one for the next page.
				# Then in metadataEpisode() it will be interpreted as a sequential number, causing problems with paging.
				# Eg: GoT S01E10 will be incremented to S01E11. Make sure the 1st page of the Episode submenu has S01E10 listed as the last episode of the page for this to happen.
				elif self.mTools.submenuIsEpisode(submenu = submenu): number = MetaPack.NumberStandard

				# Reduce means to reduce the number of (unimportant) specials interleaved in submenus.
				# Reduce the number of specials in Progress submenus (episodes-submenu), but leave the extra specials for the Series menu (series-submenu).
				reduce = True if special == MetaManager.SpecialReduce else None
				interleave = self.mTools.settingsShowInterleave() if special is MetaManager.SpecialSettings else bool(special)
				if season and episode and interleave and self.mTools.submenuIsEpisode(submenu = submenu): reduce = True
				if reduce: special = MetaManager.SpecialReduce

				# Limit the number of episodes shown for indirect or flattened episode menus (eg Trakt Progress list).
				# Otherwise menus with many episodes per season take too long to load and the user probably does not access the last episodes in the list anyway.
				if not limit:
					if submenu: limit = self.limit(submenu = submenu)
					elif not episode is None: limit = self.limit(submenu = MetaTools.SubmenuSerie if (not reduce and interleave) else MetaTools.SubmenuEpisode)

				items = self.metadataEpisode(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, episode = episode, number = number, limit = limit, quick = quick, refresh = refresh, special = special, hint = True)

				if items:
					# Preferablly show an entire season per page in the Series menu.
					# If there are too many episodes (eg 100s) in a season, page that season like normal episode submenu.
					# The easiest way to do this is to simply retrieve episodes, like with episodes submenus, and remove the last ones that are in the next season.
					if self.mTools.submenuIsSerie(submenu = submenu):
						first = None
						for i in range(len(items)):
							if first is None: # The season parameter passed into this function might be wrong (eg the last episode of the previous season).
								value = items[i].get('season')
								if value: first = value
							elif items[i].get('season') > first:
								# Do not do this if there are less than 3 items.
								# Eg: Star Wars: Young Jedi Adventures
								#	A clash between Trakt's sequential numbers and TVDb's uncombined numbers make the next page always have the 1st episode as sequential number and the rest of the episodes standard numbers.
								#	This makes the series menu page 2+ always show only 1 episode per page.
								# This should not happen anymore, since in metadataEpisode() we do not convert the numbers for Series menu anymore:
								#	if not number == MetaPack.NumberSerie: self._metadataPackNumber(...)
								if i >= 3: items = items[:i]
								break

					return {
						'items' 	: items,

						'submenu'	: submenu,
						'special'	: special,

						'limit'		: limit,
						'more'		: more,
					}
		except: Logger.error()
		return None
