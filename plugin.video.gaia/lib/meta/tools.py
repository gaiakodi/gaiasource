# -*- coding: utf-8 -*-

'''
	Gaia Add-on
	Copyright (C) 2016 Gaia

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

try: from xbmc import Actor, VideoStreamDetail, AudioStreamDetail, SubtitleStreamDetail # Kodi 20+
except: pass

from lib.meta.data import MetaData
from lib.meta.image import MetaImage

from lib.modules.tools import Media, Language, Country, Tools, Converter, Regex, Logger, System, Settings, Selection, Kids, Time
from lib.modules.interface import Context, Directory, Icon, Format, Translation, Skin, Font
from lib.modules.convert import ConverterTime
from lib.modules.theme import Theme
from lib.modules.cache import Cache, Memory
from lib.modules.concurrency import Pool, Lock
from lib.modules.video import Recap, Review, Extra, Deleted, Making, Director, Interview, Explanation

class MetaTools(object):

	Instance				= None
	Lock					= Lock()

	DetailEssential			= 'essential'
	DetailStandard			= 'standard'
	DetailExtended			= 'extended'
	Details					= [DetailEssential, DetailStandard, DetailExtended]

	ProviderImdb			= 'imdb'
	ProviderTmdb			= 'tmdb'
	ProviderTvdb			= 'tvdb'
	ProviderTvmaze			= 'tvmaze'
	ProviderTvrage			= 'tvrage'
	ProviderTrakt			= 'trakt'
	ProviderFanart			= 'fanart'
	Providers				= [ProviderImdb, ProviderTmdb, ProviderTvdb, ProviderTvmaze, ProviderTvrage, ProviderTrakt, ProviderFanart]

	StreamVideo				= 'video'
	StreamAudio				= 'audio'
	StreamSubtitle			= 'subtitle'
	StreamDuration			= 'duration'
	StreamCodec				= 'codec'
	StreamAspect			= 'aspect'
	StreamWidth				= 'width'
	StreamHeight			= 'height'
	StreamChannels			= 'channels'
	StreamLanguage			= 'language'

	RatingImdb				= 'imdb'
	RatingTmdb				= 'tmdb'
	RatingTvdb				= 'tvdb'
	RatingTrakt				= 'trakt'
	RatingTvmaze			= 'tvmaze'
	RatingMetacritic		= 'metacritic'
	RatingAverage			= 'average'
	RatingAverageWeighted	= 'averageweighted'
	RatingAverageLimited	= 'averagelimited'
	RatingDefault			= RatingAverageWeighted
	RatingProviders			= [RatingImdb, RatingTmdb, RatingTvdb, RatingTrakt, RatingTvmaze, RatingMetacritic]
	RatingVotes				= 10 # Default vote count if there is a rating by no vote count (eg Metacritic or Tvmaze).

	DiscrepancyDisabbled	= 0
	DiscrepancyLenient		= 1
	DiscrepancyStrict		= 2

	TimeUnreleased			= 10800 # 3 hours.
	TimeFuture				= 86400 # 1 day.

	PropertyBusy			= 'GaiaMetadataBusy'
	PropertySelect			= 'GaiaSelect'

	SubmenuParameter		= 'submenu'
	SubmenuSeries			= 'series'		# Submenu under the Series menu.
	SubmenuEpisodes			= 'episodes'	# Submenu under the Arrivals/Progress menu.
	SubmenuHistory			= 3

	###################################################################
	# CONSTRUCTOR
	###################################################################

	def __init__(self):
		self.mConcurrency = {}
		self.mKodiNew = System.versionKodiMinimum(version = 20)

		self.mSettingsDetail = Settings.getString('metadata.general.detail').lower()
		self.mSettingsExternal = not Settings.getString('metadata.general.external') == Translation.string(32302) # Enable by default if user has a different language set.
		self.mSettingsLanguage = Language.settingsCustom('metadata.location.language')
		self.mSettingsCountry = Country.settings('metadata.location.country')

		self.mMetaAllowed = ['genre', 'country', 'year', 'episode', 'season', 'sortepisode', 'sortseason', 'episodeguide', 'showlink', 'top250', 'setid', 'tracknumber', 'rating', 'userrating', 'watched', 'playcount', 'overlay', 'cast', 'castandrole', 'director', 'mpaa', 'plot', 'plotoutline', 'title', 'originaltitle', 'sorttitle', 'duration', 'studio', 'tagline', 'writer', 'tvshowtitle', 'premiered', 'status', 'set', 'setoverview', 'tag', 'imdbnumber', 'code', 'aired', 'credits', 'lastplayed', 'album', 'artist', 'votes', 'path', 'trailer', 'dateadded', 'mediatype', 'dbid']
		self.mMetaNonzero = ['genre', 'country', 'year', 'episodeguide', 'showlink', 'top250', 'cast', 'castandrole', 'director', 'mpaa', 'plot', 'plotoutline', 'title', 'originaltitle', 'sorttitle', 'duration', 'studio', 'tagline', 'writer', 'tvshowtitle', 'premiered', 'status', 'set', 'setoverview', 'tag', 'imdbnumber', 'aired', 'credits', 'path', 'trailer', 'dateadded', 'mediatype']
		self.mMetaExclude = ['userrating', 'watched', 'playcount', 'overlay', 'duration', 'title']
		self.mMetaFunctions = {
			'genre'			: 'setGenres',
			'country'		: 'setCountries',
			'year'			: 'setYear',
			'episode'		: 'setEpisode',
			'season'		: 'setSeason',
			'sortepisode'	: 'setSortEpisode',
			'sortseason'	: 'setSortSeason',
			'episodeguide'	: 'setEpisodeGuide',
			'showlink'		: 'setShowLinks',
			'top250'		: 'setTop250',
			'setid'			: 'setSetId',
			'tracknumber'	: 'setTrackNumber',
			'rating'		: 'setRating',
			'userrating'	: 'setUserRating',
			'watched'		: None,
			'playcount'		: 'setPlaycount',
			'overlay'		: None,
			'cast'			: None,
			'castandrole'	: None,
			'director'		: 'setDirectors',
			'mpaa'			: 'setMpaa',
			'plot'			: 'setPlot',
			'plotoutline'	: 'setPlotOutline',
			'title'			: 'setTitle',
			'originaltitle'	: 'setOriginalTitle',
			'sorttitle'		: 'setSortTitle',
			'duration'		: 'setDuration',
			'studio'		: 'setStudios',
			'tagline'		: 'setTagLine',
			'writer'		: 'setWriters',
			'tvshowtitle'	: 'setTvShowTitle',
			'premiered'		: 'setPremiered',
			'status'		: 'setTvShowStatus',
			'set'			: 'setSet',
			'setoverview'	: 'setSetOverview',
			'tag'			: 'setTags',
			'imdbnumber'	: 'setIMDBNumber',
			'code'			: 'setProductionCode',
			'aired'			: 'setFirstAired',
			'credits'		: None,
			'lastplayed'	: 'setLastPlayed',
			'album'			: 'setAlbum',
			'artist'		: 'setArtists',
			'votes'			: 'setVotes',
			'path'			: 'setPath',
			'trailer'		: 'setTrailer',
			'dateadded'		: 'setDateAdded',
			'mediatype'		: 'setMediaType',
			'dbid'			: 'setDbId',
		}

		self.mStudioIgnore = [
			'Duplass Brothers Productions',
			'Double Dare You Productions',
			'Square Peg',
			'Secret Engine',
			'Tango Entertainment',
			'Rosetory',
			'Carnival Films',
			'Imagenation Abu Dhabi FZ',
			'Lost City',
			'AGC Studios',
			'Spooky Pictures',
			'Divide / Conquer',
			'Palm Drive Productions',
			'Municipal Pictures',
			'Brooksfilms Ltd.',
			'Mass Animation',
			'Cinesite Animation',
			'HB Wink Animation',
			'Aniventure',
			'Align',
			'GFM Animation',
			'Flying Tigers Entertainment',
			'Blazing Productions',
			'BoulderLight Pictures',
			'SSS Entertainments',
			'mm2 Asia',
			'Post Film',
			'Burn Later Productions',
			'American High',
			'Atlas Industries',
			'Hantz Motion Pictures',
			'Greendale Productions',
			'BlazNick Wechsler Productions',
			'Barry Linen Motion Pictures',
			'Jackson Pictures',
			'Komplizen Film',
			'Fabula',
			'Shoebox Films',
			'Topic Studios',
			'Elevated Films',
			'Involving Pictures',
			'Zero Gravity Management',
			'The Solution',
			'Lightstream Entertainment',
			'Bento Box Entertainment',
			'Buck & Millie Productions',
			'Wilo Productions',
			'Big Indie Pictures',
			'BCDF Pictures',
			'Vertical Entertainment',
			'Mister Smith Entertainment',
			'Federal Films',
			'Convergent Media',
			'South Australian Film Corporation',
			'Stan Australia',
			'Deeper Water',
			'Rogue Star Productions',
			'Smoke House Pictures',
			'Grand Illusion Films',
			'Saban Films',
			'Paper Street Pictures',
			'Film Bridge International',
			'Forma Pro Films',
			'Altit Media Group',
			'Evolution Pictures',
			'Metrol Technology',
			'Kreo Films FZ',
			'Kreo Films',
			'Trigger Films',
			'GFM films',
			'GFM Films',
			'Red Production',
			'The Walk-Up Company',
		]
		self.mStudioReplacePartial = {
			'(20th century)(?!\sfox)' : 'Twentieth Century Fox',
			'(20th century)' : 'Twentieth Century',
		}
		self.mStudioReplaceFull = {
			'^amazon(?:$|\s*prime|\s*video)?' : 'Amazon', # Amazon Prime Video
			'history\s*[\(\[\{]?canada[\)\]\}]?' : 'History (CA)', # History Canada
			'sony\s*liv' : 'Sony Pictures Television International', # SonyLIV
			'^film4\s*productions?$' : 'Film4', # Film4
			'^twentieth\s*century\s*fox\s*studios?$' : 'Twentieth Century Fox Film',
			'^big\s*beach$' : 'Big Beach Films',
			'^searchlight\s*pictures$' : 'Fox Searchlight Pictures', # Searchlight
			'^syndication$' : 'Syndicated', # Syndication (means it was released to multiple TV stations back in the day)
		}

		self.mTimeCurrent = Time.timestamp()
		self.mTimeClock = Time.format(timestamp = self.mTimeCurrent, format = Time.FormatTime, local = True)

		from lib.modules.playback import Playback
		self.mItemPlayback = Playback.instance()
		self.mItemPlayable = not System.originPlugin()
		self.mItemContext = Context.enabled()

		self.mHideAll = False
		self.mHideRelease = False
		hide = Settings.getInteger('navigation.general.hide')
		if hide == 1: self.mHideRelease = True
		elif hide == 2: self.mHideAll = True

		self.mPageMovie = Settings.getInteger('navigation.page.movie')
		self.mPageShow = Settings.getInteger('navigation.page.show')
		self.mPageEpisode = Settings.getInteger('navigation.page.episode')
		self.mPageMultiple = Settings.getInteger('navigation.page.multiple')
		self.mPageSubmenu = Settings.getInteger('navigation.page.submenu')
		self.mPageFlatten = Settings.getInteger('navigation.page.flatten')
		self.mPageSearch = Settings.getInteger('navigation.page.search')
		self.mPageMixed = Settings.getInteger('navigation.page.mixed')

		self.mShowDirect = Settings.getBoolean('navigation.show.direct')
		self.mShowExtra = Settings.getBoolean('navigation.show.extra')
		self.mShowFlatten = Settings.getBoolean('navigation.show.flatten')

		self.mShowSeries = not self.mShowFlatten and Settings.getBoolean('navigation.show.series')

		self.mShowInterleave = Settings.getBoolean('navigation.show.interleave')
		self.mShowInterleaveUnofficial = {
			None : Settings.getInteger('navigation.show.interleave.unofficial'),
			True : {0 : None, 1 : True, 2 : True}, # Arrivals submenus.
			False : {0 : None, 1 : None, 2 : True}, # Series menus.
		}
		self.mShowInterleaveExtra = {
			None : Settings.getInteger('navigation.show.interleave.extra'),
			True : {0 : None, 1 : False, 2 : False, 3 : True}, # Arrivals submenus.
			False : {0 : None, 1 : None, 2 : False, 3 : True}, # Series menus.
		}
		self.mShowInterleaveDuration = {
			None : Settings.getInteger('navigation.show.interleave.duration'),  # Automatic: 0.0 for series menus, 0.5 for other interleaved submenus (eg Trakt progress list).
			True : {0 : 0.0, 1 : 0.5, 2 : 0.25, 3 : 0.5}, # Arrivals submenus.
			False : {0 : 0.0, 1 : 0.0, 2 : 0.25, 3 : 0.5}, # Series menus.
		}

		self.mShowSpecial = Settings.getBoolean('navigation.show.special')
		self.mShowSpecialSeason = Settings.getBoolean('navigation.show.special.season') if self.mShowSpecial else False
		self.mShowSpecialEpisode = Settings.getBoolean('navigation.show.special.episode') if self.mShowSpecial else False

		self.mShowFuture = Settings.getBoolean('navigation.show.future')
		self.mShowFutureSeason = Settings.getBoolean('navigation.show.future.season') if self.mShowFuture else False
		self.mShowFutureEpisode = Settings.getBoolean('navigation.show.future.episode') if self.mShowFuture else False

		self.mShowCounterEnabled = Settings.getBoolean('navigation.show.counter')
		self.mShowCounterSpecial = Settings.getBoolean('navigation.show.counter.special')
		self.mShowCounterUnwatched = Settings.getBoolean('navigation.show.counter.unwatched')
		self.mShowCounterLimit = Settings.getBoolean('navigation.show.counter.limit')

		self.mShowDiscrepancy = Settings.getInteger('navigation.show.discrepancy')

		self.mLabelForce = Settings.getInteger('metadata.label.force')
		if self.mLabelForce == 2: self.mLabelForce = not Skin.supportLabelCustom(default = True)
		else: self.mLabelForce = bool(self.mLabelForce)

		self.mLabelDetailEnabled = Settings.getBoolean('metadata.detail.enabled')
		self.mLabelDetailLevel = Settings.getInteger('metadata.detail.level')
		self.mLabelDetailPlacement = Settings.getInteger('metadata.detail.placement')
		self.mLabelDetailDecoration = Settings.getInteger('metadata.detail.decoration')
		self.mLabelDetailStyle = Settings.getInteger('metadata.detail.style')
		self.mLabelDetailColor = Settings.getInteger('metadata.detail.color')

		self.mLabelPlayEnabled = Settings.getBoolean('metadata.detail.play')
		self.mLabelPlayThreshold = Settings.getInteger('metadata.detail.play.threshold')

		self.mLabelProgressEnabled = Settings.getBoolean('metadata.detail.progress')
		self.mLabelRatingEnabled = Settings.getBoolean('metadata.detail.rating')

		self.mLabelAirEnabled = Settings.getBoolean('metadata.detail.air')
		self.mLabelAirZone = Settings.getInteger('metadata.detail.air.zone') if self.mLabelAirEnabled else None
		self.mLabelAirFormat = Settings.getInteger('metadata.detail.air.format') if self.mLabelAirEnabled else None
		self.mLabelAirFormatDay = Settings.getInteger('metadata.detail.air.format.day') if self.mLabelAirEnabled else None
		self.mLabelAirFormatTime = Settings.getInteger('metadata.detail.air.format.time') if self.mLabelAirEnabled else None

		self.mDirectory = Directory()

		self.mThemeFanart = Theme.fanart()
		self.mThemeBanner = Theme.banner()
		self.mThemePoster = Theme.poster()
		self.mThemeThumb = Theme.thumbnail()
		self.mThemeNextBanner = Theme.nextBanner()
		self.mThemeNextPoster = Theme.nextPoster()
		self.mThemeNextThumb = Theme.nextThumbnail()

		ratingsUser = [False, None, True]
		ratingsMovie = [MetaTools.RatingImdb, MetaTools.RatingTmdb, MetaTools.RatingTrakt, MetaTools.RatingMetacritic, MetaTools.RatingAverage, MetaTools.RatingAverageWeighted, MetaTools.RatingAverageLimited]
		ratingsShow = [MetaTools.RatingImdb, MetaTools.RatingTmdb, MetaTools.RatingTrakt, MetaTools.RatingTvmaze, MetaTools.RatingAverage, MetaTools.RatingAverageWeighted, MetaTools.RatingAverageLimited]

		self.mRatingMovieMain = MetaTools.RatingDefault
		try: self.mRatingMovieMain = ratingsMovie[Settings.getInteger('metadata.rating.movie')]
		except: self.mRatingMovieMain = MetaTools.RatingDefault
		try: self.mRatingMovieFallback = ratingsMovie[Settings.getInteger('metadata.rating.movie.fallback')]
		except: self.mRatingMovieFallback = MetaTools.RatingDefault
		try: self.mRatingMovieUser = ratingsUser[Settings.getInteger('metadata.rating.movie.user')]
		except: self.mRatingMovieUser = None

		self.mRatingShowMain = MetaTools.RatingDefault
		try: self.mRatingShowMain = ratingsShow[Settings.getInteger('metadata.rating.show')]
		except: self.mRatingShowMain = MetaTools.RatingDefault
		try: self.mRatingShowFallback = ratingsShow[Settings.getInteger('metadata.rating.show.fallback')]
		except: self.mRatingShowFallback = MetaTools.RatingDefault
		try: self.mRatingShowUser = ratingsUser[Settings.getInteger('metadata.rating.show.user')]
		except: self.mRatingShowUser = None

	# Use a singleton, since it is more efficient to initialize the settings and other variables only once.
	# Especially if the functions are called multiple times in a loop.
	@classmethod
	def instance(self):
		if MetaTools.Instance is None:
			MetaTools.Lock.acquire()
			if MetaTools.Instance is None: MetaTools.Instance = MetaTools()
			MetaTools.Lock.release()
		return MetaTools.Instance

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True, full = True):
		self.busyClear()

		if settings:
			MetaTools.Instance = None

		if full:
			from lib.meta.cache import MetaCache
			from lib.meta.image import MetaImage
			from lib.meta.provider import MetaProvider
			from lib.meta.processors.fanart import MetaFanart
			from lib.meta.providers.tvdb import MetaTvdb

			MetaCache.reset(settings = settings)
			MetaImage.reset(settings = settings)
			MetaProvider.reset(settings = settings)
			MetaFanart.reset(settings = settings)
			MetaTvdb.reset(settings = settings)

	###################################################################
	# SETTINGS
	###################################################################

	@classmethod
	def settingsInitialize(self):
		self.settingsExternalInitialize()

	def settingsLanguage(self):
		return self.mSettingsLanguage

	def settingsCountry(self):
		return self.mSettingsCountry

	def settingsPageMovie(self):
		return self.mPageMovie

	def settingsPageShow(self):
		return self.mPageShow

	def settingsPageEpisode(self):
		return self.mPageEpisode

	def settingsPageMultiple(self):
		return self.mPageMultiple

	def settingsPageSubmenu(self):
		return self.mPageSubmenu

	def settingsPageFlatten(self):
		return self.mPageFlatten

	def settingsPageSearch(self):
		return self.mPageSearch

	def settingsPageMixed(self):
		return self.mPageMixed

	def settingsShowFlatten(self):
		return self.mShowFlatten

	def settingsShowSeries(self):
		return self.mShowSeries

	def settingsShowInterleave(self):
		return self.mShowInterleave

	# If submenu = True/False, then return: True = strict, None = disabled.
	def settingsShowInterleaveUnofficial(self, submenu = None):
		interleave = self.mShowInterleaveUnofficial[None]
		return self.mShowInterleaveUnofficial[submenu][interleave]

	# If submenu = True/False, then return: True = strict, False = lenient, None = disabled.
	def settingsShowInterleaveExtra(self, submenu = None):
		interleave = self.mShowInterleaveExtra[None]
		return self.mShowInterleaveExtra[submenu][interleave]

	def settingsShowInterleaveDuration(self, submenu = None):
		interleave = self.mShowInterleaveDuration[None]
		return self.mShowInterleaveDuration[submenu][interleave]

	def settingsShowSpecial(self):
		return self.mShowSpecial

	def settingsShowSpecialSeason(self):
		return self.mShowSpecialSeason

	def settingsShowSpecialEpisode(self):
		return self.mShowSpecialEpisode

	def settingsShowDiscrepancy(self):
		return self.mShowDiscrepancy

	def settingsDetail(self):
		return self.mSettingsDetail

	@classmethod
	def settingsDetailSet(self, detail):
		Settings.set('metadata.general.detail', detail.capitalize())

	@classmethod
	def settingsDetailShow(self, settings = False):
		from lib.modules.window import WindowMetaDetail
		WindowMetaDetail.show(wait = True)
		if settings: Settings.launch(id = 'metadata.general.detail')

	def settingsExternal(self):
		return self.mSettingsExternal

	@classmethod
	def settingsExternalSet(self, enabled = True):
		Settings.set('metadata.general.external', Translation.string(32301 if enabled else 32302))

	@classmethod
	def settingsExternalInitialize(self):
		from lib.modules.tools import Extension
		if not Extension.installed(id = Extension.IdGaiaMetadata):
			Settings.set('metadata.general.external', Translation.string(35859))

	@classmethod
	def settingsExternalHas(self):
		return not Settings.defaultIs('metadata.general.external')

	@classmethod
	def settingsExternalShow(self, settings = False):
		from lib.modules.window import WindowMetaExternal
		WindowMetaExternal.show(wait = True)
		if settings: Settings.launch(id = 'metadata.general.external')

	###################################################################
	# CONCURRENCY
	##################################################################

	# Kodi can run out of threads if we load the Trakt show arrivals list the first time.
	# Too many sub-threads are created to retrieve shows, seasons, and episodes, all within the same execution.
	# hierarchical: retrieve a list of episodes from different shows, each of them retrieving their own season and show metadata.
	def concurrency(self, media = None, hierarchical = False):
		id = str(media) + '_' + str(hierarchical)
		if not id in self.mConcurrency:
			tasks = Pool.limitTask()
			if hierarchical:
				from lib.modules.tools import Hardware, Math
				adjust = Math.scale(Hardware.performanceRating(), fromMinimum = 0, fromMaximum = 1, toMinimum = 0.6, toMaximum = 0.9)
				tasks = max(10, tasks * adjust)
			self.mConcurrency[id] = max(3, int(tasks))
		return self.mConcurrency[id]

	###################################################################
	# NETWORK
	##################################################################

	# Create a "Accept-Language" HTTP header, to return metadata in a specifc language.
	# Eg: IMDb uses the public IP address (eg: VPN) if this header is not set, and might return some titles in another unwanted language.
	def headerLanguage(self, weighted = True, wildcard = True, structured = True):
		from lib.modules.network import Networker

		language = []
		language.append(self.settingsLanguage())
		language.extend(Language.settingsCode())
		language = Tools.listUnique([i for i in language if i])

		return Networker.headersAcceptLanguage(language = language, country = self.settingsCountry(), weighted = weighted, wildcard = wildcard, structured = structured)

	###################################################################
	# MEDIA
	###################################################################

	@classmethod
	def media(self, metadata):
		if Tools.isArray(metadata): metadata = metadata[0]
		if metadata:
			if 'media' in metadata and metadata['media']: return metadata['media']
			elif 'episode' in metadata: return Media.TypeEpisode
			elif 'season' in metadata: return Media.TypeSeason
			elif 'tvshowtitle' in metadata: return Media.TypeShow
			else: return Media.TypeMovie
		return None

	@classmethod
	def slug(self, title, year = None, separator = '-', symbol = None, lower = True):
		slug = ''
		try:
			for char in title:
				if char == ' ': slug += separator
				elif char.isalnum(): slug += char.lower() if lower else char
				elif symbol: slug += symbol
		except: pass
		if slug:
			if year: slug += separator + str(year)
			if separator: slug = Regex.replace(data = slug, expression = '(\%s{2,})' % separator, replacement = separator, group = None, all = True).strip(separator)
			if symbol and not symbol == separator: slug = Regex.replace(data = slug, expression = '(\%s{2,})' % symbol, replacement = symbol, group = None, all = True).strip(symbol)
		return slug if slug else None

	###################################################################
	# COMMAND
	###################################################################

	def command(self, metadata, media = None, action = None, video = None, multiple = None, submenu = None, reduce = None, increment = False, next = False):
		force = False

		if (media == Media.TypeSeason and not 'season' in metadata) or self.submenuIs(submenu = submenu, type = MetaTools.SubmenuSeries): # Series menu.
			media = Media.TypeShow
			force = True
			if not Tools.isString(submenu): submenu = MetaTools.SubmenuSeries

		flatten = self.submenuFlatten(media = media, force = force)
		if submenu is None: submenu = self.submenu(media = media, multiple = multiple, force = force)
		if submenu is True: submenu = MetaTools.SubmenuSeries if flatten else MetaTools.SubmenuEpisodes

		parameters = {}
		if not action:
			if not video is None: action = 'streamsVideo'
			elif Media.typeTelevision(media) and submenu:
				# gaiasubmenu - Check addon.py -> episodesRetrieve for more info.
				#action = 'episodesRetrieve'
				#parameters['submenu'] = 'next' if next else True # Check addon.py -> episodesRetrieve for more info. # Do it differently for the "Next Page" in submenus.
				action = 'episodesSubmenu'
			elif media == Media.TypeSpecialExtra: action = 'seasonsExtras'
			elif media == Media.TypeShow: action = 'seasonsRetrieve'
			elif media == Media.TypeSeason: action = 'episodesRetrieve'
			elif media == Media.TypeSet: action = 'setsRetrieve'
			if not action: action = 'scrape'

		# Removes the current/next/previous season data to reduce time to encode/decode the metadata.
		# Almost halfs the time to load menus.
		if action == 'scrape' or action == 'seasonsExtras': parameters['metadata'] = self.reduce(metadata)

		if Media.typeTelevision(media) and multiple and submenu: parameters['limit'] = self.mPageSubmenu

		for attribute in ['imdb', 'tmdb', 'tvdb', 'title', 'tvshowtitle', 'year', 'premiered', 'season', 'episode']:
			try: parameters[attribute] = metadata[attribute]
			except: pass

		# Season offset for "Next Page" of flattened show menus.
		# NB: Make the season/episode number floats, since Python allows -0.0, but a negative zero is not possible for integers.
		# -0.0 is used to indicate the offset for the Specials season.
		if Media.typeTelevision(media) and (submenu or force):
			if flatten and self.mPageFlatten == 0: # Flattened show menus.

				parameters['season'] = -1 * float((metadata['season'] if 'season' in metadata else 0) + int(increment))
				try: del parameters['episode']
				except: pass
			elif 'episode' in metadata: # Submenus for multiple episode menus.
				# Include the last 3 watched episodes, in case the user wants to rewatch them (aka fell asleep yesterday while watching).
				season = metadata['season'] if 'season' in metadata else 1
				episode = metadata['episode'] + int(increment)
				if reduce is None:
					episode -= self.submenuHistory()
					if season > 1 and episode <= 0 and 'pack' in metadata and metadata['pack']:
						try:
							for i in metadata['pack']['seasons']:
								if i['number'][MetaData.NumberOfficial] == season:
									season -= 1
									episode = i['count'] + episode - 1
									break
						except: Logger.error()

				parameters['season'] = -1 * float(season)
				parameters['episode'] = -1 * float(max(1, episode))

		# Season recaps and extras.
		if metadata and 'query' in metadata: parameters['title'] = parameters['tvshowtitle'] = metadata['query']
		if not video is None: parameters['video'] = video
		parameters['media'] = Media.TypeEpisode if media == Media.TypeSpecialRecap or media == Media.TypeSpecialExtra else media

		parameters['reduce'] = reduce

		if submenu:
			parameters[MetaTools.SubmenuParameter] = self.submenuIncrement(submenu = submenu)
			submenu = '&%s=%s' % (MetaTools.SubmenuParameter, submenu)

		# gaiasubmenu - Check addon.py -> episodesRetrieve for more info.
		#return System.command(action = action, parameters = parameters)
		command = System.command(action = action, parameters = parameters)

		# Add this here as well, since elsewhere in this class we check if the parameter is in the commmand.
		# Also add it to the parameters above, since we use the value in the episodesRetrieve endpoint.
		if submenu: command += submenu

		return command

	###################################################################
	# MULTIPLE
	###################################################################

	def multiple(self, metadata):
		if not Tools.isArray(metadata): metadata = [metadata]
		titles = [meta['tvshowtitle'] for meta in metadata if 'tvshowtitle' in meta and meta['tvshowtitle']]
		titles = Tools.listUnique(titles)

		# Sometimes different episodes of the same season have different show titles.
		# Eg: 'Hollywood Medium with Tyler Henry' vs 'Hollywood Medium'
		result = []
		for title in titles:
			found = False
			for i in result:
				if title in i or i in title:
					found = True
					break
			if not found: result.append(title)

		return len(result) > 1

	###################################################################
	# SUBMENU
	###################################################################

	def submenu(self, media, multiple, force = False):
		return self.submenuFlatten(media = media, force = force) or self.submenuDirect(media = media, multiple = multiple)

	def submenuFlatten(self, media, force = False):
		return media == Media.TypeShow and (force or self.mShowFlatten)

	def submenuDirect(self, media, multiple):
		return media == Media.TypeEpisode and multiple and not self.mShowDirect

	@classmethod
	def submenuHistory(self):
		return MetaTools.SubmenuHistory

	@classmethod
	def submenuContains(self, command):
		return (MetaTools.SubmenuParameter + '=') in command

	@classmethod
	def submenuCreate(self, submenu, page = None):
		try: submenu = submenu.split('-')[0]
		except: pass
		if submenu is True: submenu = MetaTools.SubmenuEpisodes
		return submenu + ('' if page is None else ('-' + str(page)))

	@classmethod
	def submenuIncrement(self, submenu):
		page = self.submenuPage(submenu = submenu)
		page = 0 if page is None else (page + 1)
		return self.submenuCreate(submenu = submenu, page = page)

	@classmethod
	def submenuIs(self, submenu, type):
		return Tools.isString(submenu) and submenu.startswith(type)

	@classmethod
	def submenuPage(self, submenu):
		try: return int(submenu.split('-')[-1])
		except: return None

	###################################################################
	# LABEl
	###################################################################

	def label(self, metadata, media = None, future = None, multiple = False, extend = True):
		if not media: media = self.media(metadata = metadata)

		season = None
		episode = None

		if media == Media.TypeSeason:
			try: title = metadata['title']
			except: title = None
			try: year = metadata['year']
			except: year = None
			try: season = metadata['season']
			except: season = None
			series = season is None and not 'season' in metadata
			label = Media.title(type = media, title = None if multiple else title, year = year, season = season, series = series, special = True)
		elif media == Media.TypeEpisode:
			try: title = metadata['title']
			except: title = None
			try: year = metadata['year']
			except: year = None
			try: season = metadata['season']
			except: season = None
			try: episode = metadata['episode']
			except: episode = None
			label = Media.title(type = media, title = None if multiple else title, year = year, season = season, episode = episode)
		else:
			try: year = metadata['year']
			except: year = None
			try: title = metadata['title']
			except:
				try: title = metadata['originaltitle']
				except:
					try: title = metadata['tvshowtitle']
					except: title = None

			label = Media.title(type = media, title = title, year = year)
			if not label: label = title

		if multiple and (media == Media.TypeSeason or media == Media.TypeEpisode):
			try: title = metadata['tvshowtitle']
			except: title = None

			# Always add the title.
			# Eg: The first episode's title of the show "1883" is also "1883".
			#if title and not title in label and not label in title: label = '%s - %s' % (title, label)
			if title: label = '%s - %s' % (title, label)

		fontItalic = False
		fontLight = False
		if not future is None and not future is True:
			if future > -MetaTools.TimeUnreleased:
				fontItalic = True
				label = Format.fontItalic(label)
			if future >= MetaTools.TimeFuture:
				fontLight = True
				label = Format.fontLight(label)

		if media == Media.TypeEpisode and season == 0:
			if not 'special' in metadata or not metadata['special'] or not 'story' in metadata['special'] or not metadata['special']['story']:
				# Only do this if not already made italic.
				# Otherwise there might be nested italic tags, and then Kodi will display the title with an ending "[/I]" visible to the user.
				# Eg: Breaking Bad S0, the last few specials that do not have a release date.
				if not fontItalic: label = Format.fontItalic(label)

		# Mark new episodes/seasons in multiple menus as bold.
		if (media == Media.TypeSeason or media == Media.TypeEpisode) and (not future or future < 0):
			new = False
			time = Time.timestamp()

			# New episode.
			if not new and not 'playcount' in metadata or not metadata['playcount']:
				if 'premiered' in metadata and metadata['premiered']: date = metadata['premiered']
				elif 'aired' in metadata and metadata['aired']: date = metadata['aired']
				else: date = None
				if date:
					date = time - Time.timestamp(date, format = '%Y-%m-%d')
					if date > 0 and date < 604800: new = True # 1 week.

			# New Season.
			if not new and 'pack' in metadata and metadata['pack']:
				date = 0
				seasoned = None
				for i in metadata['pack']['seasons']:
					if i['time']['start'] and i['time']['start'] < time and i['time']['start'] >= date:
						date = i['time']['start']
						seasoned = i['number']['official']

				# Only do this for the season that is newley released.
				# Otherwise a new season might cause all unwatched episodes in older seasons to also be marked in bold.
				# Or mark as bold if multiple, so that shows in the Arrivals menu are highlighted if a new season comes out, even if the user still watches an older season.
				if date and not seasoned is None and (season == seasoned or multiple):
					date = time - date
					if date > 0 and date < 2419200: # 4 weeks.
						# NB: Only do this if at least 1 episode in the show was previously watched.
						# Otherwise shows without any watched episodes also show in bold (Quick menu - recommendations/featured/trending/arrivals).
						history = self.mItemPlayback.history(media = media, imdb = metadata.get('imdb'), tmdb = metadata.get('tmdb'), tvdb = metadata.get('tvdb'), trakt = metadata.get('trakt'))
						if history and history['count']['total']:
							if media == Media.TypeEpisode:
								# Do not bolden already watched episodes.
								history = self.mItemPlayback.history(media = media, imdb = metadata.get('imdb'), tmdb = metadata.get('tmdb'), tvdb = metadata.get('tvdb'), trakt = metadata.get('trakt'), season = season, episode = episode)
								if not history or not history['count']['total']:
									new = True
							else:
								new = True

			if new: label = Format.fontBold(label)

		# Do this last, after Format.fontBold(label).
		# Otherwise the labelBefore/labelAfter, which might have its own bold formatting, is formatted a second time.
		# There could then be 2 nested bold tags, and then the title in the label is not actually bold and ends with "[/B]".
		# Make sure there is no nested formatting.
		if extend:
			# Show user, progress, or airing details.
			if 'labelBefore' in metadata and metadata['labelBefore']: label = metadata['labelBefore'] + ' ' + label
			if 'labelAfter' in metadata and metadata['labelAfter']: label = label + ' ' + metadata['labelAfter']

		return label

	###################################################################
	# SELECT
	###################################################################

	def select(self, items, next = True, adjust = False):
		index = None
		size = len(items)
		for i in range(size):
			if items[i][1].getProperty(MetaTools.PropertySelect):
				index = i

				# Skip specials, recaps, and extras.
				try:
					while index < (size - 1):
						info = items[index + 1][1].getVideoInfoTag()
						season = info.getSeason()
						episode = info.getEpisode()
						if (season and season > 0) and (episode and episode > 0): break
						index += 1
				except: Logger.error()

				break

		if next and not index is None and (index + 1) < len(items): index += 1

		# If all episodes in the show were watched (the same number of times), the index will be on the 'Next Page' item.
		# Therefore, opening an Arrivals submenu of a fully watched show will always auto-select the last item on the page, which is the 'Next Page' item.
		# In such a case (eg: user wants to rewatch the show), set the index to None in order to select the first item in the list.
		try:
			episode = items[index][1].getVideoInfoTag().getEpisode()
			if episode is None or episode < 0: index = None
		except: pass

		return index

	###################################################################
	# STREAM
	###################################################################

	def stream(self, duration = None, videoCodec = None, videoAspect = None, videoWidth = None, videoHeight = None, audioCodec = None, audioChannels = None, audioLanguage = None, subtitleLanguage = None):
		# https://alwinesch.github.io/group__python__xbmcgui__listitem.html#ga99c7bf16729b18b6378ea7069ee5b138

		audioLanguage = [audioLanguage] if audioLanguage and not Tools.isArray(audioLanguage) else []
		subtitleLanguage = [subtitleLanguage] if subtitleLanguage and not Tools.isArray(subtitleLanguage) else []

		video = []
		audio = []
		subtitle = []

		# Video
		data = {}
		if duration: data[MetaTools.StreamDuration] = duration
		if videoCodec: data[MetaTools.StreamCodec] = videoCodec
		if videoAspect: data[MetaTools.StreamAspect] = videoAspect
		if videoWidth: data[MetaTools.StreamWidth] = videoWidth
		if videoHeight: data[MetaTools.StreamHeight] = videoHeight
		if data:
			if self.mKodiNew: data = VideoStreamDetail(**data) # Kodi 20+
			video.append(data)

		# Audio
		for i in audioLanguage:
			if i:
				data = {}
				if audioCodec: data[MetaTools.StreamCodec] = audioCodec
				if audioChannels: data[MetaTools.StreamChannels] = audioChannels
				data[MetaTools.StreamLanguage] = i
				if data:
					if self.mKodiNew: data = AudioStreamDetail(**data) # Kodi 20+
					audio.append(data)

		# Subtitle
		for i in subtitleLanguage:
			if i:
				data = {}
				data[MetaTools.StreamLanguage] = i
				if data:
					if self.mKodiNew: data = SubtitleStreamDetail(**data) # Kodi 20+
					subtitle.append(data)

		return {MetaTools.StreamVideo : video, MetaTools.StreamAudio : audio, MetaTools.StreamSubtitle : subtitle}

	###################################################################
	# ITEM
	###################################################################

	def items(self,
		metadatas,

		media = None,
		kids = None,

		item = None,
		stream = None,
		properties = None,
		playable = None,
		multiple = None,
		mixed = None,
		submenu = None,
		next = None,
		recap = None,
		extra = None,

		context = None,
		contextAdd = None,
		contextMode = None,
		contextLibrary = None,
		contextPlaylist = None,
		contextShortcutCreate = None,
		contextShortcutDelete = None,

		hide = False,
		hideSearch = False,
		hideRelease = False,
		hideWatched = False,

		label = True,
		command = True,
		clean = True,
		images = True,
	):
		if media is None: media = self.media(metadata = metadatas)
		if multiple is None: multiple = self.multiple(metadata = metadatas) if (media == Media.TypeSeason or media == Media.TypeEpisode) else False
		if mixed is None: mixed = media == Media.TypeMixed
		if submenu is None: submenu = self.submenu(media = media, multiple = multiple)

		items = []
		if not mixed and media == Media.TypeEpisode and sum(Tools.listUnique([i['season'] for i in metadatas if 'season' in i and not i['season'] == 0])) > 1:
			# NB: when there are submenus in the Arrivals menu that contain episodes from multiple seasons (eg: last episodes of S02 and first episodes of S03).
			# The season extras, recap, and the occasional special episodes between seasons, are all mixed up (eg: S03 recap is listed before S02 extras).
			# This is because adding the recap/extras item cannot deal with mutiple seasons, always moving the recap before the extras while assuming it is the same season.
			# Instead, break the episodes into chuncks, one for each season.
			# Process each subset separately, each with their own recap/extras, and then combine them into one linear list.

			index = -1
			season = -1
			chunks = []
			for i in range(len(metadatas)):
				metadata = metadatas[i]

				# Determine for special episodes between seasons, if they belong to the previous or next season (closest release date).
				if metadata['season'] == 0:
					timePrevious = 0
					for j in range(i, 0, -1):
						if metadatas[j]['season'] > 0:
							time = None
							try: time = item['aired']
							except: pass
							if not time:
								try: time = item['premiered']
								except: pass
							if time:
								timePrevious = Time.integer(time)
								break

					timeNext = 0
					for j in range(i, len(metadatas)):
						if metadatas[j]['season'] > 0:
							time = None
							try: time = item['aired']
							except: pass
							if not time:
								try: time = item['premiered']
								except: pass
							if time:
								timeNext = Time.integer(time)
								break

					if timeNext > timePrevious:
						chunks.append([])
						index += 1

				if index < 0 or (metadata['season'] > 0 and not metadata['season'] == season):
					chunks.append([])
					index += 1
					if metadata['season'] > 0: season = metadata['season']
				if season < 0 or metadata['season'] > 0: season = metadata['season']
				chunks[index].append(metadata)
		else:
			chunks = [metadatas]

		for chunk in chunks:
			items.append(self._items(
				metadatas = chunk,

				media = media,
				kids = kids,

				item = item,
				stream = stream,
				properties = properties,
				playable = playable,
				multiple = multiple,
				mixed = mixed,
				submenu = submenu,
				recap = recap,
				extra = extra,

				context = context,
				contextAdd = contextAdd,
				contextMode = contextMode,
				contextLibrary = contextLibrary,
				contextPlaylist = contextPlaylist,
				contextShortcutCreate = contextShortcutCreate,
				contextShortcutDelete = contextShortcutDelete,

				hide = hide,
				hideSearch = hideSearch,
				hideRelease = hideRelease,
				hideWatched = hideWatched,

				label = label,
				command = command,
				clean = clean,
				images = images,
			))
		items = Tools.listFlatten(data = items, recursive = False)

		# Make sure that special episodes are listed after the recap.
		# Check the series menu for Game of Thrones S02 and S03 which has specials before E01.
		# Only do this for series menus, otherwise the recap will be pulled above specials from the previous seaosn in Arrivals/Progress.
		if self.submenuIs(submenu = submenu, type = MetaTools.SubmenuSeries):
			try:
				for i in range(len(items)):
					if 'metadata' in items[i]:
						if not items[i]['metadata']['season'] == 0: break
					else:
						items.insert(0, items.pop(i))
						break
			except: Logger.error()

		if next:
			itemNext = self.itemNext(metadata = metadatas, media = media, kids = kids, multiple = multiple, submenu = submenu)
			if itemNext: items.append({'data' : itemNext})

		# Specify the last watched item to auto-select from view.py.
		if media == Media.TypeEpisode:
			plays = []
			for i in range(len(items)):
				item = items[i]
				if 'metadata' in item:
					metadata = item['metadata']
					if metadata:
						play = {'time' : 0, 'count' : 0, 'season' : metadata['season'], 'item' : item['data'][1]}
						if 'lastplayed' in metadata: play['time'] = Time.integer(metadata['lastplayed'])
						if 'playcount' in metadata: play['count'] = metadata['playcount']
						plays.append(play)

			# Ignore specials, except if we are in the specials menu.
			if len(Tools.listUnique([play['season'] for play in plays])) > 1:
				plays = [play for play in plays if not play['season'] == 0]

			playItem = None
			plays.reverse() # Pick the last one with max time/count.
			try: play = max(plays, key = lambda i : i['time'])
			except: play = None
			if play and play['time'] > 0:
				playItem = play['item']
			else:
				try: play = max(plays, key = lambda i : i['count'])
				except: play = None
				if play and play['count'] and play['count'] > 0: playItem = play['item']
			if playItem: playItem.setProperty(MetaTools.PropertySelect, '1')

		return [item['data'] for item in items]

	def _items(self,
		metadatas,

		media = None,
		kids = None,

		item = None,
		stream = None,
		properties = None,
		playable = None,
		multiple = None,
		mixed = None,
		submenu = None,
		recap = None,
		extra = None,

		context = None,
		contextAdd = None,
		contextMode = None,
		contextLibrary = None,
		contextPlaylist = None,
		contextShortcutCreate = None,
		contextShortcutDelete = None,

		hide = False,
		hideSearch = False,
		hideRelease = False,
		hideWatched = False,

		label = True,
		command = True,
		clean = True,
		images = True,
	):
		folder = None if media == Media.TypeMixed else (submenu or (media == Media.TypeSet or media == Media.TypeShow or media == Media.TypeSeason))

		seasons = []
		items = []
		itemsRecap = []
		itemsExtra = []

		for metadata in metadatas:
			try:
				item = self.item(
					metadata = metadata,

					media = self.media(metadata = metadata) if mixed else media,
					kids = kids,

					stream = stream,
					properties = properties,
					playable = playable,
					multiple = multiple,
					mixed = mixed,
					submenu = submenu,

					context = context,
					contextAdd = contextAdd,
					contextMode = contextMode,
					contextLibrary = contextLibrary,
					contextPlaylist = contextPlaylist,
					contextShortcutCreate = contextShortcutCreate,
					contextShortcutDelete = contextShortcutDelete,

					hide = hide,
					hideSearch = hideSearch,
					hideRelease = hideRelease,
					hideWatched = hideWatched,

					label = label,
					command = command,
					clean = clean,
					images = images
				)
				if item:
					if folder is None:
						itemMedia = self.media(metadata)
						itemFolder = submenu or (itemMedia == Media.TypeSet or itemMedia == Media.TypeShow or itemMedia == Media.TypeSeason)
					else: itemFolder = folder

					# gaiasubmenu - Check addon.py -> episodesRetrieve for more info.
					if self.submenuContains(command = item['command']): itemFolder = False

					if 'season' in metadata: seasons.append(metadata['season'])
					items.append({'metadata' : item['metadata'], 'data' : [item['command'], item['item'], itemFolder]})

					# Add here instead of after the loop, since recaps/extras have to be inserted between episodes for flattened menus.
					# Insert AFTER the episode item() above was created, since we want to use the cleaned metadata with the watched status.
					# There can be multiple recaps/extras for multiple submenus (if the number of episodes listed is less than the navigation.page.multiple).
					if recap or extra:
						cleaned = Tools.update(self.copy(metadata), item['metadata'])
						if recap:
							item = self.itemRecap(metadata = cleaned, media = media, kids = kids, multiple = multiple)
							if item: itemsRecap.append({'index' : len(items) - 1, 'season' : cleaned['season'], 'media' : Media.TypeSpecialRecap, 'item' : {'data' : item}})
						if extra:
							item = self.itemExtra(metadata = cleaned, media = media, kids = kids, multiple = multiple)
							if item: itemsExtra.append({'index' : len(items) - 1, 'season' : cleaned['season'], 'media' : Media.TypeSpecialExtra, 'item' : {'data' : item}})
			except: Logger.error()

		offset = 0
		if itemsRecap:
			for itemMore in itemsRecap: # Iterate from front to back.
				index = 0
				itemIndex = itemMore['index']
				itemSeason = itemMore['season']
				for i in range(itemIndex, -1, -1): # If special episodes are interleaved, make sure the recap/extra is placed before/after all interleaved specials.
					if seasons[i] == 0: index -= 1
					elif seasons[i] < itemSeason: break
				for i in range(itemIndex, len(seasons)):
					if seasons[i] > 0 and seasons[i] >= itemSeason:
						index += i
						break
				items.insert(index + offset, itemMore['item'])
				offset += 1

		if itemsExtra:
			found = {}
			for itemMore in reversed(itemsExtra): # Iterate from back to front.
				index = 0
				itemIndex = itemMore['index']
				itemSeason = itemMore['season']
				for i in range(itemIndex, len(seasons)): # If special episodes are interleaved, make sure the recap/extra is placed before/after all interleaved specials.
					if seasons[i] == 0: index += 1
					elif seasons[i] > itemSeason: break
				for i in range(itemIndex, -1, -1):
					if seasons[i] > 0 and seasons[i] <= itemSeason:
						index += i + 1
						break

				# Sometimes Trakt has more episodes in the season than TVDb.
				# The pack data will therefore have 1 less episode than the actual episode list.
				# Eg: Shark Tank India S01 has 35 episodes on TVDb and 36 episodes on Trakt (last episode is online special).
				# This will add 2 Season Extras menus, one after E35 and one after E36.
				# Start from the back and only add
				if not itemSeason in found:
					found[itemSeason] = True
					items.insert(index + offset, itemMore['item'])

		return items

	def itemsExtra(self,
		metadata,
		kids = None,
		item = None,
		label = True,
		command = True,
		clean = True,
		images = True
	):
		label = Translation.string(32055)
		media = Media.TypeEpisode
		query = metadata['tvshowtitle']

		for i in ['episode', 'premiered', 'genre', 'rating', 'userrating', 'votes', 'duration']:
			try: del metadata[i]
			except: pass

		items = []
		videos = [Review, Extra, Deleted, Making, Director, Interview, Explanation]
		for video in videos:
			try:
				if video.enabled():
					metadata['query'] = query
					metadata['duration'] = video.Duration
					metadata['title'] = metadata['originaltitle'] = metadata['tagline'] = label + ' ' + Translation.string(video.Label)
					metadata['plot'] = Translation.string(video.Description) % (str(metadata['season']), query)

					item = self.item(
						metadata = metadata,

						media = Media.TypeSpecialExtra,
						kids = kids,

						contextMode = Context.ModeVideo,

						video = video.Id,
						label = metadata['title'],
						command = command,
						clean = clean,
						images = images
					)
					if item: items.append([item['command'], item['item'], False])
			except: Logger.error()

		return items

	'''
		clean:
			True: Clean the metadata before adding it to the item.
			False: Do not clean the metadata before adding it to the item. This assumes that the "metadata" parameter wass already cleaned.
			Dictionary: An already cleaned metadata dictionary. Can be used to avoid cleaning and already cleaned dictionary.
		stream:
			dictionary created by stream().
		properties:
			dictionary with custom properties.
		multiple:
			Whether or not the seasons/episodes are from different shows.
		mixed:
			Whether or not the items are a mixture of movies and shows.
		extend:
			Add extra info to the label or plot.
			Should mostly be used with items in a menu, but not items in the player.
		images:
			True: Extract images from the metadata and add them to the item.
			False: Do not extract images from the metadata and do not add them to the item.
			Dictionary: Use already extracted images and add them to the item.
		context:
			True: Add a context menu to the item.
			False: Do not add a context menu to the item.
			None: Use the settings to determine wether or not to add a context menu to the item.
	'''
	def item(self,
		metadata,

		media = None,
		kids = None,

		item = None,
		stream = None,
		properties = None,
		playable = None,
		video = None,
		multiple = False,
		mixed = False,
		submenu = False,

		context = None, # If False, do not create a context menu.
		contextAdd = None, # Add the context to the list item. Otherwise the context menu iss just returned.
		contextMode = None, # The type of context menu to create.
		contextCommand = None, # The link/command for the context menu.
		contextLibrary = None, # The link/command to add to the library. If True, uses contextCommand.
		contextPlaylist = None, # Wether or not to allow the item to be queued to the playlist.
		contextSource = None, # The stream source dictionary for stream list items.
		contextOrion = None, # Orion identifiers for stream list items.
		contextShortcutId = None, # The ID to use for the shortcut.
		contextShortcutLabel = None, # The default label to use for the shortcut.
		contextShortcutLocation = None, # The root location for the shortcuts.
		contextShortcutCreate = None, # Wether or not to allow a shortcut to be created for the item.
		contextShortcutDelete = None, # Wether or not to allow a shortcut to be deleted for the item.

		hide = False,
		hideSearch = False,
		hideRelease = False,
		hideWatched = False,

		extend = True,
		extendLabel = True,
		extendPlot = True,

		label = True,
		command = True,
		clean = True,
		images = True,
		content = True
	):
		mediaOriginal = media
		if not media: media = mediaOriginal = self.media(metadata = metadata)

		# Hide special seasons and episodes.
		if (media == Media.TypeSeason or media == Media.TypeEpisode) and not self.mShowSpecialSeason and (not 'season' in metadata or metadata['season'] == 0): return None
		elif media == Media.TypeEpisode and not self.mShowSpecialEpisode and (not 'episode' in metadata or metadata['episode'] == 0): return None

		if not extend:
			extendLabel = extend
			extendPlot = extend

		future = None
		if content:
			# Hide future seasons and episodes.
			future = self.itemFuture(metadata = metadata, media = media) if (media == Media.TypeSeason or media == Media.TypeEpisode) else None
			if future is True:
				future = None
			else:
				if (media == Media.TypeSeason and not self.mShowFutureSeason) or (media == Media.TypeEpisode and not self.mShowFutureEpisode):
					if future is None: return None # No release date.
					if future > -MetaTools.TimeUnreleased: return None # Released in the past 3 hours or sometime in the future.

		if not item: item = self.itemCreate()
		tag = self.itemTag(item = item)

		if content:
			# Add missing attributes.
			# Will be removed by clean(), but added to commands and context.
			self.itemShow(media = media, item = item, metadata = metadata)

			# Must be before clean() and setInfo().
			self.itemPlayback(media = media, item = item, tag = tag, metadata = metadata)

			# Must be before setInfo() and itemPlot().
			# Must be after itemPlayback().
			self.itemDetail(media = media, item = item, metadata = metadata, mixed = mixed)

			# Must be before setInfo().
			self.itemDate(media = media, item = item, metadata = metadata)

			# Must be before setInfo().
			self.itemPlot(media = media, item = item, metadata = metadata, extend = extendPlot)

			if hide:
				if not hideSearch: # Always show watched items in the search menu.
					try: watched = metadata['playcount'] > 0
					except: watched = False
					if watched:
						if (hideRelease and self.mHideRelease) or (not hideRelease and self.mHideAll): return None
						if hideWatched and (not 'progress' in metadata or not metadata['progress']): return None # Skip episodes marked as watched for the unfinished list.

		# Must be done before the title/label is changed below.
		if command is True: command = self.command(media = media, metadata = metadata, video = video, multiple = multiple, submenu = submenu)
		elif not command: command = None
		elif command: item.setPath(command)

		if clean is True: cleaned = self.clean(media = media, metadata = metadata)
		elif Tools.isDictionary(clean): cleaned = clean
		else: cleaned = metadata

		# Adding Label or Label2 to the ListItem does not work.
		# Instead of the label, the title set in setInfo() is used.
		# This is most likley a skin bug (including the default Kodi skin), since skins seem to not check if there is a label, but only always just pick the title.
		# The only way to use a custom title seems to be to replace the title attribute.
		# Note that this will propagate to all places where the ListItem is used. Eg: The Kodi info dialog will show the custom label instead of the title and might eg have 2 years in the label.
		if label:
			if label is True: label = self.label(metadata = metadata, media = mediaOriginal, future = future, multiple = multiple, extend = extendLabel)

			# Use original, since we can pass docu/short in.
			# Always force for seasons, since a few seasons have their own title and we do not want to have naming inconsistencies.
			# Eg: Breaking Bad's special season has an English title "Minisodes".
			# Update: not needed anymore, since the setting "metadata.title.layout" is now enabled by default.
			if self.mLabelForce: cleaned['title'] = label

			item.setLabel(label)

		# NB: call setInfo() first, before any of the other functions below.
		# Otherwise Kodi might replace values set by the other functions with the values from setInfo().
		# For instance, setInfo() will replace the values set by setCast(), and then actor thumbnails do not show in the Kodi info dialog.
		self.itemInfo(item = item, tag = tag, metadata = cleaned)

		self.itemId(item = item, tag = tag, metadata = metadata)
		self.itemVoting(item = item, tag = tag, metadata = metadata)
		self.itemCast(item = item, tag = tag, metadata = metadata)
		self.itemStream(item = item, tag = tag, stream = stream)
		self.itemProperty(item = item, properties = properties, playable = playable)

		images = self.itemImage(item = item, media = media, metadata = metadata, images = images, video = video, multiple = multiple)

		if context is False:
			context = None
		else:
			if contextMode is None and not content: contextMode = Context.ModeStream

			# For episode submenus, make sure that the command passed to the context is the scrape command and not the episodesSubmenu command.
			# Eg: Open the Arrivals main menu -> open the context menu on an episode -> Scrape -> Rescrape -> this should launch the scrape process.
			if contextCommand is None and submenu: contextCommand = self.command(media = media, metadata = metadata, video = video, multiple = multiple, submenu = False)

			context = self.itemContext(item = item, context = context, add = contextAdd, mode = contextMode, media = mediaOriginal, kids = kids, video = video, command = contextCommand if contextCommand else command, library = contextLibrary, playlist = contextPlaylist, source = contextSource, metadata = metadata, orion = contextOrion, shortcutId = contextShortcutId, shortcutLabel = contextShortcutLabel, shortcutLocation = contextShortcutLocation, shortcutCreate = contextShortcutCreate, shortcutDelete = contextShortcutDelete)

		return {'item' : item, 'command' : command, 'context' : context, 'metadata' : cleaned, 'images' : images}

	# ListItem passed to Kodi's player.
	def itemPlayer(self,
		metadata,

		media = None,
		kids = None,

		item = None,
		stream = None,
		properties = None,

		label = False,
		command = True,
		clean = True,
		images = True
	):
		return self.item(
			metadata = metadata,

			media = media,
			kids = kids,

			item = item,
			stream = stream,
			properties = properties,
			playable = True,
			multiple = False,

			context = False,

			hide = False,
			extend = False,

			label = label,
			command = command,
			clean = clean,
			images = images
		)

	def itemCreate(self):
		return self.mDirectory.item()

	def itemTag(self, item):
		if self.mKodiNew:
			try: return item.getVideoInfoTag() # Kodi 20+
			except: pass
		return False

	def itemShow(self, media, metadata, item):
		if metadata:
			if media == Media.TypeShow or media == Media.TypeSeason:
				if not 'tvshowtitle' in metadata and 'title' in metadata: metadata['tvshowtitle'] = metadata['title']
				if not 'tvshowyear' in metadata and 'year' in metadata: metadata['tvshowyear'] = metadata['year']

			# For Gaia Eminence.
			if media == Media.TypeEpisode:
				item.setProperty('GaiaShowNumber', Media.number(metadata = metadata))

				try: special = metadata['special']
				except: special = None

				specialType = None
				if special and 'type' in special: specialType = special['type']
				item.setProperty('GaiaShowSpecial', '-'.join(specialType) if specialType else '')

				specialStory = metadata['season'] > 0
				if not specialStory and special and 'story' in special: specialStory = special['story']
				item.setProperty('GaiaShowStory', str(int(False if specialStory is None else specialStory)))

				specialExtra = metadata['season'] == 0 or metadata['episode'] == 0
				if special and 'extra' in special: specialExtra = special['extra']
				item.setProperty('GaiaShowExtra', str(int(False if specialExtra is None else specialExtra)))

			elif media == Media.TypeSpecialExtra or media == Media.TypeSpecialRecap:
				item.setProperty('GaiaShowExtra', '1')

	def itemDetail(self, media, metadata, item, mixed = False):
		if metadata and self.mLabelDetailEnabled:
			details = False
			if self.mLabelDetailLevel == 0: details = Media.typeMovie(media) or media == Media.TypeEpisode
			elif self.mLabelDetailLevel == 1: details = Media.typeMovie(media) or media == Media.TypeSeason or media == Media.TypeEpisode
			elif self.mLabelDetailLevel == 2: details = Media.typeMovie(media) or media == Media.TypeShow or media == Media.TypeSeason or media == Media.TypeEpisode

			if details:
				values = []

				color = None
				if self.mLabelDetailColor == 1: color = Format.colorPrimary()
				elif self.mLabelDetailColor == 2: color = Format.colorSecondary()
				elif self.mLabelDetailColor == 3: color = True

				if self.mLabelPlayEnabled:
					try: playcount = metadata['playcount']
					except: playcount = None
					if not playcount: playcount = 0
					if playcount >= self.mLabelPlayThreshold:
						values.append((32006, Font.IconWatched, Format.colorExcellent() if color is True else color, str(playcount)))

				# For mixed menus, do not add the progress if it is <= 1% or >= 99%.
				# Still show the progress for unfinished lists.
				if self.mLabelProgressEnabled and 'progress' in metadata and not metadata['progress'] is None and (not mixed or (metadata['progress'] > 0.01 and metadata['progress'] < 0.99)):
					values.append((32037, Font.IconProgress, Format.colorPoor() if color is True else color, '%.0f%%' % (metadata['progress'] * 100.0)))

				if self.mLabelRatingEnabled and 'userrating' in metadata and not metadata['userrating'] is None:
					values.append((35187, Font.IconRating, Format.colorMedium() if color is True else color, '%.1f' % metadata['userrating']))

				if Media.typeTelevision(media) and self.mLabelAirEnabled and 'airs' in metadata:
					try: airTime = metadata['airs']['time']
					except: airTime = None
					try: airDay = metadata['airs']['day'][0]
					except: airDay = None
					try: airZone = metadata['airs']['zone']
					except: airZone = None

					if airTime and airDay:
						if airZone:
							if self.mLabelAirZone == 1: zoneTo = airZone
							elif self.mLabelAirZone == 2: zoneTo = Time.ZoneUtc
							else: zoneTo = Time.ZoneLocal

							if self.mLabelAirFormatTime == 0: formatOutput = '%I:%M %p'
							elif self.mLabelAirFormatTime == 1: formatOutput = '%H:%M'

							abbreviate = self.mLabelAirFormatDay == 1
							airTime = Time.convert(stringTime = airTime, stringDay = airDay, zoneFrom = airZone, zoneTo = zoneTo, abbreviate = abbreviate, formatOutput = formatOutput)
							if airDay:
								airDay = airTime[1]
								airTime = airTime[0]

						air = []
						if airDay: air.append(airDay)
						if airTime: air.append(airTime)
						if air:
							if self.mLabelAirFormat == 0: air = airTime
							elif self.mLabelAirFormat == 1: air = airDay
							elif self.mLabelAirFormat == 2: air = air = ' '.join(air)
							values.append((35032, Font.IconCalendar, Format.colorSpecial() if color is True else color, air))

				if values:
					if self.mLabelDetailDecoration == 0: values = [Format.fontColor(i[3], color = i[2]) for i in values]
					elif self.mLabelDetailDecoration == 1: values = [Format.fontColor('%s: %s' % (Translation.string(i[0]), i[3]), color = i[2]) for i in values]
					elif self.mLabelDetailDecoration == 2: values = [Format.fontColor('%s: %s' % (Translation.string(i[0])[0], i[3]), color = i[2]) for i in values]
					elif self.mLabelDetailDecoration == 3: values = ['%s %s' % (Format.fontColor(Font.icon(i[1]), color = i[2]), i[3]) for i in values]

					values = Format.iconJoin(values)
					if self.mLabelDetailPlacement == 0 or self.mLabelDetailPlacement == 1:
						color = Format.colorDisabled()
						values = Format.fontColor('[', color = color) + values + Format.fontColor(']', color = color)

					if self.mLabelDetailStyle == 1: values = Format.fontBold(values)
					elif self.mLabelDetailStyle == 2: values = Format.fontItalic(values)
					elif self.mLabelDetailStyle == 3: values = Format.fontLight(values)

					if self.mLabelDetailPlacement == 0: attribute = 'labelBefore'
					elif self.mLabelDetailPlacement == 1: attribute = 'labelAfter'
					elif self.mLabelDetailPlacement == 2: attribute = 'plotBefore'
					elif self.mLabelDetailPlacement == 3: attribute = 'plotAfter'
					metadata[attribute] = values

	def itemDate(self, media, metadata, item):
		if metadata:
			# For Gaia Eminence.
			# These are needed to use sorting in the menus.
			# date/SORT_METHOD_DATE seems to be broken and does not return the correct order.
			# dateadded/SORT_METHOD_DATEADDED can correctly sort by date.
			if 'premiered' in metadata and metadata['premiered']: date = metadata['premiered']
			elif 'aired' in metadata and metadata['aired']: date = metadata['aired']
			else: date = None

			if date:
				# Needs to be set in a specific format.
				dated = ConverterTime(date, format = '%Y-%m-%d')
				metadata['date'] = dated.string(format = '%d.%m.%Y')
				metadata['dateadded'] = dated.string(format = '%Y-%m-%d %H:%M:%S')

				if media == Media.TypeSeason or media == Media.TypeEpisode:
					year = Regex.extract(data = date, expression = '(\d{4})')
					if year: metadata['year'] = int(year)

	def itemPlot(self, media, metadata, item, extend = True):
		if metadata and extend:
			if 'plotBefore' in metadata and metadata['plotBefore']:
				if not 'plot' in metadata or not metadata['plot']: metadata['plot'] = metadata['plotBefore']
				else: metadata['plot'] = metadata['plotBefore'] + '\n\n' + metadata['plot']
			if 'plotAfter' in metadata and metadata['plotAfter']:
				if not 'plot' in metadata or not metadata['plot']: metadata['plot'] = metadata['plotAfter']
				else: metadata['plot'] = metadata['plot'] + '\n\n' + metadata['plotAfter']

	def itemId(self, metadata, item, tag = None):
		try:
			if metadata:
				if tag is None: tag = self.itemTag(item = item)
				ids = {}
				imdb = None
				for id in [MetaTools.RatingImdb, MetaTools.RatingTmdb, MetaTools.RatingTvdb, MetaTools.RatingTrakt if tag else None]:
					if id and id in metadata and metadata[id]:
						ids[id] = str(metadata[id])
						if id == MetaTools.RatingImdb: imdb = metadata[id]
				try: tag.setUniqueIDs(ids, 'imdb') # Kodi 20+
				except: item.setUniqueIDs(ids, 'imdb') # Kodi 19
				if imdb: metadata['imdbnumber'] = imdb
		except: Logger.error()

	def itemInfo(self, metadata, item, tag = None, type = None):
		if tag is None: tag = self.itemTag(item = item)
		if tag and metadata: # Kodi 20+
			for key, value in metadata.items():
				try:
					if not value is None:
						function = self.mMetaFunctions[key]
						if function: Tools.executeFunction(tag, function, value)
				except: Logger.error(key)
		else: # Kodi 19
			item.setInfo(type = type if type else 'video', infoLabels = metadata)

	def itemFuture(self, metadata, media = None):
		if metadata:
			if 'status' in metadata and MetaData.statusExtract(metadata['status']) == MetaData.StatusEnded: return True

			time = None
			if not time and 'aired' in metadata: time = metadata['aired']
			if not time and 'premiered' in metadata: time = metadata['premiered']

			if not time:
				# Trakt sometimes returns new/unaired seasons that or not yet on TVDb, and also sometimes vice versa.
				# These seasons seem to not have a premiered/aired date, year, or even the number of episodes aired.
				# Make them italic to inidcate that they are unaired.
				# Update: Sometimes the year and airs attributes are available.
				if media == Media.TypeSeason:
					if not 'year' in metadata:
						try: episodes = metadata['airs']['episodes']
						except: episodes = None
						if not episodes: return MetaTools.TimeFuture
					elif 'pack' in metadata:
						# Slow Horses has a year for S03, although not aired yet.
						try:
							season = metadata['season']
							found = False
							for i in metadata['pack']['seasons']:
								if i['number']['official'] == season:
									found = True
									break
							if not found: return MetaTools.TimeFuture
						except: pass
				if media == Media.TypeSeason or media == Media.TypeEpisode:
					if metadata and (not 'rating' in metadata or not metadata['rating']) and (not 'votes' in metadata or not metadata['votes']):
						# If no rating, votes or images.
						images = False
						if MetaImage.Attribute in metadata and metadata[MetaImage.Attribute]:
							for k, v in metadata[MetaImage.Attribute].items():
								if not Tools.isDictionary(v) and v:
									images = True
									break
						if not images: return MetaTools.TimeFuture

				return None

			time = Time.timestamp(fixedTime = time + ' ' + self.mTimeClock, format = Time.FormatDateTime)
			if not time: return None

			return time - self.mTimeCurrent
		return None

	def itemVoting(self, metadata, item, tag = None):
		try:
			if metadata and 'voting' in metadata:
				if tag is None: tag = self.itemTag(item = item)
				for i in [MetaTools.RatingImdb, MetaTools.RatingTmdb, MetaTools.RatingTvdb, MetaTools.RatingTrakt if tag else None]:
					if i:
						if i in metadata['voting']['rating']:
							rating = metadata['voting']['rating'][i]
							if not rating is None and i in metadata['voting']['votes']:
								votes = metadata['voting']['votes'][i]
								if votes is None: votes = 0
								try: tag.setRating(rating, votes, i, False) # Kodi 20+
								except: item.setRating(i, rating, votes, False) # Kodi 19
						if i in metadata['voting']['user']:
							rating = metadata['voting']['user'][i]
							if not rating is None:
								try: tag.setUserRating(rating) # Kodi 20+
								except: pass
		except: Logger.error()

	def itemImage(self, media, metadata, item, images = True, video = None, multiple = False):
		if Tools.isDictionary(images):
			return MetaImage.set(item = item, images = images)
		elif images:
			if media == Media.TypeSeason and metadata and not 'season' in metadata: media = Media.TypeShow # Series menu.

			if video is None: return MetaImage.setMedia(media = media, data = metadata, item = item, multiple = multiple)
			elif video == Recap.Id: return MetaImage.setRecap(data = metadata, item = item)
			else: return MetaImage.setExtra(data = metadata, item = item)
		return None

	def itemCast(self, metadata, item, tag = None):
		# There is a bug in Kodi when setting a ListItem in the Player.
		# When setting the cast, the name/role/order is added correctly, but for some unknown reason the thumbnail is removed.
		# This only happens in Kodi's player. The cast thumbnails are correct when creating a directory or showing the movie/show info dialog.
		# To replicate the problem, add this to player.py:
		#	self.item.setCast([{'name' : 'vvv', 'role' : 'uuu', 'thumbnail' : 'https://image.tmdb.org/t/p/w185/gwQ5MfY68BvvyIbef3kr2XPilTx.jpg'}])
		#	self.updateInfoTag(self.item)
		#	tools.Time.sleep(1)
		#	tools.System.executeJson(method = 'Player.GetItem', parameters = {'playerid' : interface.Player().id(), 'properties':['cast']})
		# The RPC returns:
		#	{"id":1,"jsonrpc":"2.0","result":{"item":{"cast":[{"name":"vvv","order":-1,"role":"uuu"}],"label":"The Shawshank Redemption","type":"movie"}}}
		# The name/role/order is returned, but the thumbnail is missing.
		# This is most likley also the reason why the cast thumbnails do not show up in Kodi Kore or Yatse, since both probably use the RPC.
		# Various attempts were made to solve the problem, but without any success:
		#	1. Removing the cast/castandrole attributes before setting item.setInfo() and only use item.setCast().
		#	2. Setting the thumbnail as a HTTP URL, local file path, special:// path, URL-encoded image:// path, or <thumb>https://...</thumb>.
		#	3. Inserting the actor and thumbnail into Kodi's local DB (MyVideosXXX.db), in case the RPC retrieves the thumbnail from there.
		#	4. Using differnt attributes (thumbnail/thumb/photo/image) in the dictionaries set with item.setCast().
		# Maybe this will be fixed in Kodi 20 with the new functions/classes:
		#	self.item.setCast([xbmc.Actor('vvv', 'role', order=1, thumbnail='https://image.tmdb.org/t/p/w185/gwQ5MfY68BvvyIbef3kr2XPilTx.jpg')])

		if metadata and 'cast' in metadata:
			cast = metadata['cast']
			if cast:
				if Tools.isDictionary(cast[0]):
					castDetail = cast
				else:
					try: multi = Tools.isArray(cast[0]) and len(cast[0]) > 1
					except: multi = False
					if multi: castDetail = [{'name' : i[0], 'role' : i[1]} for i in cast]
					else: castDetail = [{'name' : i} for i in cast]

				# There is a bug in Kodi that the thumbnails are not shown, even if they were set.
				if tag is None: tag = self.itemTag(item = item)
				try: tag.setCast([Actor(**i) for i in castDetail]) # Kodi 20+
				except: item.setCast(castDetail) # Kodi 19

	def itemStream(self, stream, item, tag = None):
		if stream:
			if tag is None: tag = self.itemTag(item = item)
			if tag: # Kodi 20+
				for type, datas in stream.items():
					if type == MetaTools.StreamVideo:
						for data in datas: tag.addVideoStream(data)
					elif type == MetaTools.StreamAudio:
						for data in datas: tag.addAudioStream(data)
					elif type == MetaTools.StreamSubtitle:
						for data in datas: tag.addSubtitleStream(data)
			else: # Kodi 19
				for type, datas in stream.items():
					for data in datas: item.addStreamInfo(type, data)

	def itemProperty(self, properties, item, playable = None):
		if not properties: properties = {}
		if not 'IsPlayable' in properties:
			if playable is None: playable = self.mItemPlayable
			properties['IsPlayable'] = 'true' if playable else 'false'
		item.setProperties(properties)

	def itemPlayback(self, media, metadata, item, tag = None):
		if metadata:
			if tag is None: tag = self.itemTag(item = item)

			try: idImdb = metadata['imdb']
			except: idImdb = None
			try: idTmdb = metadata['tmdb']
			except: idTmdb = None
			try: idTvdb = metadata['tvdb']
			except: idTvdb = None
			try: idTrakt = metadata['trakt']
			except: idTrakt = None
			try: season = metadata['extra']['season']
			except:
				try: season = metadata['season']
				except: season = None
			try: episode = metadata['extra']['episode']
			except:
				try: episode = metadata['episode']
				except: episode = None

			# Series menu.
			if media == Media.TypeSeason and not 'season' in metadata: media = Media.TypeShow

			playback = self.mItemPlayback.retrieve(media = media, imdb = idImdb, tmdb = idTmdb, tvdb = idTvdb, trakt = idTrakt, season = season, episode = episode, adjust = self.mItemPlayback.AdjustSettings)
			count = playback['history']['count']['total']
			time = playback['history']['time']['last']
			progress = playback['progress']
			rating = playback['rating']

			# If the 1st episode is in-progress, already mark the recap as watched, and not also as in-progress.
			if progress:
				if media == Media.TypeSpecialRecap:
					progress = None
					if not count: count = 1
				elif media == Media.TypeSpecialExtra:
					progress = None

			# Do not use overlay/watched attribute, since Kodi (or maybe the Kodi skin) resets the playcount to 1, even if playcount is higher than 1.
			# https://github.com/xbmc/xbmc/blob/master/xbmc/guilib/GUIListItem.h
			#metadata['overlay'] = 5 if count else 4

			metadata['playcount'] = count

			if time: metadata['lastplayed'] = Time.format(time, format = Time.FormatDateTime)

			# Resume/Progress
			# Do not set TotalTime, otherwise Kodi shows a resume popup dialog when clicking on the item, instead of going directly to scraping.
			# item.setProperty('TotalTime', str(metadata['duration']))
			# For some skins (eg: skin.eminence.2) the TotalTime has to be set for a different progress icon to show (25%, 50%, 75%).
			# Without TotalTime, the skins justs shows the default 25% icon.
			if progress:
				# Not listed under the Python docs, but listed under the infolabels docs.
				# Do not add, since Kodi throws a warning in the log: Unknown Video Info Key "percentplayed"
				#metadata['percentplayed'] = progress * 100

				if not media == Media.TypeShow and not media == Media.TypeSeason:
					if 'duration' in metadata and metadata['duration']: resume = progress * metadata['duration']
					else: resume = progress * (3600 if Media.typeTelevision(media) else 7200)
					try: tag.setResumePoint(int(resume))
					except: item.setProperty('ResumeTime', str(int(resume)))

				# Used by the context menu to add a "Clear Progress" option.
				if not media == Media.TypeShow and not media == Media.TypeSeason: metadata['progress'] = progress

			if rating:
				try: tag.setUserRating(rating) # Kodi 20+
				except: pass
				metadata['userrating'] = rating

			if Media.typeTelevision(media):
				seasonsTotal = None
				episodesTotal = None
				episodesWatched = None
				episodesUnwatched = None

				if 'pack' in metadata and metadata['pack']:
					pack = metadata['pack']
					if season is None and episode is None:
						key = 'total' if self.mShowCounterSpecial else 'main'
						seasonsTotal = pack['count']['season'][key]
						episodesTotal = pack['count']['episode'][key]
					elif episode is None:
						seasonsTotal = 1
						for i in pack['seasons']:
							if i['number'][MetaData.NumberOfficial] == season:
								episodesTotal = i['count']
								break
					else:
						seasonsTotal = 1
						episodesTotal = 1

				episodesWatched = playback['history']['count']['main']['unique'] if ('main' in playback['history']['count'] and not self.mShowCounterSpecial) else playback['history']['count']['unique']
				if not episodesWatched: episodesWatched = 0
				if episodesTotal: episodesUnwatched = episodesTotal - episodesWatched

				if self.mShowCounterEnabled:
					if not seasonsTotal is None: item.setProperty('TotalSeasons', str(seasonsTotal))
					if not episodesTotal is None: item.setProperty('TotalEpisodes', str(episodesTotal))
					if not episodesWatched is None: item.setProperty('WatchedEpisodes', str(episodesWatched))
					if not episodesUnwatched is None and self.mShowCounterUnwatched:
						if self.mShowCounterLimit: episodesUnwatched = min(99, episodesUnwatched)
						item.setProperty('UnWatchedEpisodes', str(episodesUnwatched))

					# Set this to allow the context menu to add "Mark As Unwatched" for partially watched shows/seasons.
					metadata['count'] = {
						'season' : {'total' : seasonsTotal},
						'episode' : {'total' : episodesTotal, 'watched' : episodesWatched, 'unwatched' : episodesUnwatched},
					}

				# For shows and seasons, only mark as watched if all episodes were watched.
				# If some episodes are watched and some are unwatched, add a resume time to indicate there are still some unwatched episodes.
				if media == Media.TypeShow or media == Media.TypeSeason:
					if episodesUnwatched and episodesUnwatched > 0:
						metadata['playcount'] = None
					else:
						count, remaining = self.mItemPlayback.count(media = media, imdb = idImdb, tmdb = idTmdb, tvdb = idTvdb, trakt = idTrakt, season = season, episode = episode, specials = self.mShowCounterSpecial, metadata = metadata, history = playback['history'])
						metadata['playcount'] = count

					if (episodesWatched and episodesUnwatched) or progress:
						try: tag.setResumePoint(1)
						except: item.setProperty('ResumeTime', str(1))

	def itemContext(self,
		item,

		add = None,
		context = None,
		mode = None,

		media = None,
		kids = None,
		video = None,

		command = None,
		library = None,
		playlist = None,

		source = None,
		metadata = None,
		orion = None,

		shortcutId = None,
		shortcutLabel = None,
		shortcutLocation = None,
		shortcutCreate = None,
		shortcutDelete = None
	):
		# NB: Do not pass the cleaned metadata, since we need to extract the raw YouTube trailer URL, not the already created Gaia plugin command.
		menu = self.context(context = context, mode = mode, media = media, kids = kids, video = video, command = command, library = library, playlist = playlist, source = source, metadata = metadata, orion = orion, shortcutId = shortcutId, shortcutLabel = shortcutLabel, shortcutLocation = shortcutLocation, shortcutCreate = shortcutCreate, shortcutDelete = shortcutDelete)
		if menu and (add or add is None): item.addContextMenuItems(menu.menu(full = True))
		return menu

	def itemNext(self, metadata = None, media = None, kids = None, multiple = False, submenu = None, link = None, item = None):
		try:
			if link is None:
				if not Tools.isArray(metadata): metadata = [metadata]
				linkFallback1 = None
				linkFallback2 = None
				for value in reversed(metadata): # Do reverse, since in flattened show menus the 'next' attribute might be different for each episode.
					# Do not check if 'next' has a value, since scanning should stop after the first (or rather last) 'next' has been found.
					# in episodes.py 'next' can be set to None to avoid a 'Next Page' to be show in flattened show menus if we are on the last page no more seasons).
					#if 'next' in value and value['next']:
					if 'next' in value:
						if not linkFallback1 or not 'season' in value or not value['season'] == 0: linkFallback1 = value['next']
						linkFallback2 = value['next']
						if not self.mShowInterleave or not 'season' in value or not value['season'] == 0: # Skip interleaved special episodes.
							link = value['next']
							break
				if not link: link = linkFallback1 or linkFallback2

			if link:
				if not item: item = self.itemCreate()
				tag = self.itemTag(item = item)
				if not media: media = self.media(metadata = metadata[0])

				title = Format.fontItalic(32306)
				item.setLabel(title)

				self.itemInfo(item = item, tag = tag, metadata = {'title' : title, 'tagline' : Translation.string(35317), 'plot' : Translation.string(35318)})

				icon = Icon.pathIcon(icon = 'next.png', default = 'DefaultFolder.png')
				image = self.mThemeNextThumb if media == Media.TypeEpisode and not multiple else self.mThemeNextPoster
				images = {
					MetaImage.TypePoster : image,
					MetaImage.TypeThumb : icon,
					MetaImage.TypeFanart : self.mThemeFanart,
					MetaImage.TypeLandscape : self.mThemeFanart,
					MetaImage.TypeBanner : self.mThemeNextBanner,
					MetaImage.TypeClearlogo : icon,
					MetaImage.TypeClearart : icon,
					MetaImage.TypeDiscart : image,
					MetaImage.TypeIcon : icon,
				}
				MetaImage.set(item = item, images = images)

				if link and link.startswith(System.plugin()):
					command = link # Flattened show menus.
				else:
					parameters = {'link' : link, 'media' : media}
					if not kids is None: parameters['kids'] = kids
					if submenu: parameters[MetaTools.SubmenuParameter] = self.submenuIncrement(submenu = submenu)
					if 'person' in metadata[0] and metadata[0]['person']: action = 'showsPersons' if Media.typeTelevision(media) else 'moviesPersons'
					elif media == Media.TypeShow or media == Media.TypeSeason: action = 'showsRetrieve'
					elif media == Media.TypeEpisode: action = 'episodesRetrieve'
					elif media == Media.TypeSet: action = 'setsRetrieve'
					else: action = 'moviesRetrieve'
					command = System.command(action = action, parameters = parameters)

				folder = True

				# gaiasubmenu - Check addon.py -> episodesRetrieve for more info.
				if self.submenuContains(command = command): folder = False

				return [command, item, folder]
		except: Logger.error()
		return None

	def itemRecap(self, metadata, media = None, kids = None, multiple = None):
		try:
			if media is None: media = self.media(metadata = metadata)
			if multiple is None: multiple = self.multiple(metadata = metadata) if (media == Media.TypeSeason or media == Media.TypeEpisode) else False

			if media == Media.TypeEpisode and not multiple:
				if self.mShowExtra and Recap.enabled():
					if Tools.isArray(metadata): metadata = metadata[0]
					season = metadata['season'] - 1
					episode = metadata['episode'] - 1
					if season > 0 and episode == 0:
						# Ensures that the Recaps are automatically marked as watched if the first episode in the season was watched.
						metadataReuse = {i : metadata[i] for i in ['playcount', 'watched', 'overlay', 'lastplayed', 'date', 'dateadded'] if i in metadata}
						metadataReuse['extra'] = {'season' : metadata['season'], 'episode' : metadata['episode']}

						metadataCurrent = metadata['seasonCurrent'] if 'seasonCurrent' in metadata else None
						metadataPrevious = metadata['seasonPrevious'] if 'seasonPrevious' in metadata else None
						metadataNext = metadata['seasonNext'] if 'seasonNext' in metadata else None
						metadata = self.copy(metadataPrevious if metadataPrevious else metadataCurrent)
						if not metadata: return None

						# Copy images, otherwise if there is an Extras from the previous season and a Recap from the next seasons (eg: Trakt progress submenu), the image dictionary is changed, causing exceptions.
						if metadataCurrent and MetaImage.Attribute in metadataCurrent:
							MetaImage.update(media = MetaImage.MediaSeason, images = metadataCurrent[MetaImage.Attribute], data = metadata, copy = True)
							MetaImage.update(media = MetaImage.MediaSeason, images = metadataCurrent[MetaImage.Attribute], data = metadata, category = MetaImage.MediaSeason, copy = True)
						if metadataCurrent and MetaImage.Attribute in metadataCurrent and MetaImage.MediaShow in metadataCurrent[MetaImage.Attribute]: MetaImage.update(media = MetaImage.MediaSeason, images = metadataCurrent[MetaImage.Attribute][MetaImage.MediaShow], data = metadata, category = MetaImage.MediaShow, copy = True)
						if metadataPrevious and MetaImage.Attribute in metadataPrevious: MetaImage.update(media = MetaImage.MediaSeason, images = metadataPrevious[MetaImage.Attribute], data = metadata, category = MetaImage.IndexPrevious, copy = True)
						if metadataNext and MetaImage.Attribute in metadataNext: MetaImage.update(media = MetaImage.MediaSeason, images = metadataNext[MetaImage.Attribute], data = metadata, category = MetaImage.IndexNext, copy = True)

						for i in ['episode', 'premiered', 'aired', 'genre', 'duration', 'airs', 'voting', 'rating', 'votes', 'userrating', 'labelBefore', 'labelAfter', 'plotBefore', 'plotAfter']:
							try: del metadata[i]
							except: pass
						metadata.update(metadataReuse)

						title = metadata['tvshowtitle'] if 'tvshowtitle' in metadata else metadata['title']
						label = Regex.replace(data = Translation.string(35362) % '', expression = '\s+', replacement = ' ', all = True)

						metadata['query'] = title
						metadata['duration'] = Recap.Duration
						metadata['title'] = metadata['originaltitle'] = label
						metadata['tagline'] = Translation.string(35362) % str(metadata['season'])
						metadata['plot'] = Translation.string(35456) % (str(metadata['season']), title)

						item = self.item(
							metadata = metadata,

							media = Media.TypeSpecialRecap,
							kids = kids,

							contextMode = Context.ModeVideo,

							video = Recap.Id,
							label = label,
						)
						return [item['command'], item['item'], False]
		except: Logger.error()
		return None

	def itemExtra(self, metadata, media = None, kids = None, multiple = None):
		try:
			if media is None: media = self.media(metadata = metadata)
			if multiple is None: multiple = self.multiple(metadata = metadata) if (media == Media.TypeSeason or media == Media.TypeEpisode) else False

			if media == Media.TypeEpisode and not multiple:
				if self.mShowExtra and Recap.enabled():
					if Tools.isArray(metadata): metadata = metadata[-1]
					season = metadata['season']
					if season > 0:
						ended = True

						# If the current last episode has not been aired yet, do not show extras.
						if ended:
							try: premiered = metadata['aired']
							except:
								try: premiered = metadata['premiered']
								except: premiered = None
							if premiered and Time.timestamp(fixedTime = premiered, format = Time.FormatDate) > Time.timestamp(): ended = False
							if not premiered and metadata['episode'] == 1: ended = False # Only a single new unaired episode without a release date.

						# If the current last episode is lower than the available episodes in the season, do not show extras.
						if ended and 'pack' in metadata and metadata['pack']:
							found = False
							for i in metadata['pack']['seasons']:
								if i['number'][MetaData.NumberOfficial] == metadata['season']:
									found = True
									last = max([j['number'][MetaData.NumberOfficial] for j in i['episodes']])
									if metadata['episode'] < last: ended = False
									break

							# Sometimes the new unaired season does not form part of the pack data.
							if not found and season > max([i['number'][MetaData.NumberOfficial] for i in metadata['pack']['seasons']]): ended = False

						if ended:
							# Ensures that the Extras are automatically marked as watched if the last episode in the season was watched.
							metadataReuse = {i : metadata[i] for i in ['playcount', 'watched', 'overlay', 'lastplayed', 'date', 'dateadded'] if i in metadata}
							metadataReuse['extra'] = {'season' : metadata['season'], 'episode' : metadata['episode']}

							metadataCurrent = metadata['seasonCurrent'] if 'seasonCurrent' in metadata else None
							metadataPrevious = metadata['seasonPrevious'] if 'seasonPrevious' in metadata else None
							metadataNext = metadata['seasonNext'] if 'seasonNext' in metadata else None
							metadata = self.copy(metadataCurrent if metadataCurrent else metadataNext)
							if not metadata: return None

							# Copy images, otherwise if there is an Extras from the previous season and a Recap from the next seasons (eg: Trakt progress submenu), the image dictionary is changed, causing exceptions.
							if metadataCurrent and MetaImage.Attribute in metadataCurrent:
								MetaImage.update(media = MetaImage.MediaSeason, images = metadataCurrent[MetaImage.Attribute], data = metadata, copy = True)
								MetaImage.update(media = MetaImage.MediaSeason, images = metadataCurrent[MetaImage.Attribute], data = metadata, category = MetaImage.MediaSeason, copy = True)
							if metadataCurrent and MetaImage.Attribute in metadataCurrent and MetaImage.MediaShow in metadataCurrent[MetaImage.Attribute]: MetaImage.update(media = MetaImage.MediaSeason, images = metadataCurrent[MetaImage.Attribute][MetaImage.MediaShow], data = metadata, category = MetaImage.MediaShow, copy = True)
							if metadataPrevious and MetaImage.Attribute in metadataPrevious: MetaImage.update(media = MetaImage.MediaSeason, images = metadataPrevious[MetaImage.Attribute], data = metadata, category = MetaImage.IndexPrevious, copy = True)
							if metadataNext and MetaImage.Attribute in metadataNext: MetaImage.update(media = MetaImage.MediaSeason, images = metadataNext[MetaImage.Attribute], data = metadata, category = MetaImage.IndexNext, copy = True)

							for i in ['episode', 'premiered', 'aired', 'genre', 'duration', 'airs', 'voting', 'rating', 'votes', 'userrating', 'labelBefore', 'labelAfter', 'plotBefore', 'plotAfter']:
								try: del metadata[i]
								except: pass
							metadata.update(metadataReuse)

							title = metadata['tvshowtitle'] if 'tvshowtitle' in metadata else metadata['title']
							label = Regex.replace(data = Translation.string(35791) % '', expression = '\s+', replacement = ' ', all = True)

							metadata['title'] = metadata['originaltitle'] = label
							metadata['tagline'] = Translation.string(35791) % str(metadata['season'])
							metadata['plot'] = Translation.string(35649) % (str(metadata['season']), title)

							item = self.item(
								metadata = metadata,

								media = Media.TypeSpecialExtra,
								kids = kids,

								label = label,
							)
							return [item['command'], item['item'], True]
		except: Logger.error()
		return None

	###################################################################
	# DIRECTORY
	###################################################################

	def directories(self, metadatas, media = None, kids = None, next = True):
		items = []

		for metadata in metadatas:
			try:
				item = self.directory(media = media, kids = kids, metadata = metadata)
				if item: items.append([item['command'], item['item'], True])
			except: Logger.error()

		if next:
			itemNext = self.itemNext(metadata = metadatas, media = media, kids = kids)
			if itemNext: items.append(itemNext)

		return items

	def directory(self, metadata = None, media = None, kids = None, link = None, item = None, context = None):
		try:
			if not item: item = self.itemCreate()
			if not link and 'link' in metadata: link = metadata['link']

			try: media = metadata['media']
			except: pass

			name = metadata['name']

			if metadata:
				data = {}

				if 'person' in metadata and metadata['person']: data['title'] = name

				if 'plot' in metadata and metadata['plot']: data['plot'] = metadata['plot']
				elif 'description' in metadata and metadata['description']: data['plot'] = metadata['description']
				else: data['plot'] = System.menuDescription(name = name)

				if data: self.itemInfo(item = item, metadata = data)

			item.setLabel(name)

			if metadata['image'].startswith('http'):
				icon = thumb = poster = banner = metadata['image']
			else:
				icon, thumb, poster, banner = Icon.pathAll(icon = metadata['image'], default = self.mThemeThumb)
				Directory.decorate(item = item, icon = metadata['image']) # For Gaia Eminence.

			images = {
				MetaImage.TypePoster : poster,
				MetaImage.TypeThumb : thumb,
				MetaImage.TypeFanart : self.mThemeFanart,
				MetaImage.TypeLandscape : self.mThemeFanart,
				MetaImage.TypeBanner : banner,
				MetaImage.TypeClearlogo : icon,
				MetaImage.TypeClearart : icon,
				MetaImage.TypeDiscart : poster,
				MetaImage.TypeIcon : icon,
			}
			MetaImage.set(item = item, images = images)

			try: parameters = metadata['parameters']
			except: parameters = {}
			if not 'media' in parameters: parameters['media'] = media
			if not 'link' in parameters and link: parameters['link'] = link
			if not 'kids' in parameters and not kids is None: parameters['kids'] = kids
			parameters['menu'] = System.menu(name = name)
			command = System.command(action = metadata['action'], parameters = parameters)

			context = self.itemContext(item = item, context = context, mode = Context.ModeGeneric, media = media, kids = kids, command = command, library = link, shortcutLabel = name, shortcutCreate = True)

			return {'item' : item, 'command' : command, 'context' : context, 'images' : images}
		except: Logger.error()
		return None

	###################################################################
	# CONTEXT
	###################################################################

	def context(self,
		context = None,
		mode = None,

		media = None,
		kids = None,
		video = None,

		command = None,
		library = None,
		playlist = None,

		source = None,
		metadata = None,
		orion = None,

		shortcutId = None,
		shortcutLabel = None,
		shortcutLocation = None,
		shortcutCreate = None,
		shortcutDelete = None,
	):
		if context is None: context = self.mItemContext
		if context:
			if metadata:
				if not mode: mode = Context.ModeItem
				if not media: media = self.media(metadata = metadata)
				if not command: command = self.command(metadata = metadata)
			else:
				if not mode: mode = Context.ModeGeneric

			return Context(
				mode = mode,
				media = media,
				kids = kids,
				video = video,

				link = command,
				library = library,
				playlist = playlist,

				source = source,
				metadata = metadata,
				orion = orion,

				shortcutId = shortcutId,
				shortcutLabel = shortcutLabel,
				shortcutLocation = shortcutLocation,
				shortcutCreate = shortcutCreate,
				shortcutDelete = shortcutDelete,
			)
		return None

	###################################################################
	# COPY
	###################################################################

	@classmethod
	def copy(self, metadata):
		# Do not copy the pack and season data.
		# For shows with a lot of seasons/episodes, the pack dictionary can be very large.
		# Just copying the pack already takes a long time.
		# And there should not be a reason to copy the pack, because it is static and not edited/cleaned like the rest of the metadata.
		# Eg: Coronation Street - S01 has only 7 episodes, but loads 4-5 secs without the code below, or 2.5 secs with the code.

		if metadata and 'pack' in metadata:
			temp = {}
			attributes = ['pack', 'seasonPrevious', 'seasonCurrent', 'seasonNext']

			for i in attributes:
				try:
					temp[i] = metadata[i]
					del metadata[i]
				except: pass

			result = Tools.copy(metadata)

			for key, value in temp.items():
				metadata[key] = value
				result[key] = value

			return result
		else:
			return Tools.copy(metadata)

	@classmethod
	def reduce(self, metadata):
		return self.cleanSeason(Tools.copy(metadata, deep = False))

	###################################################################
	# CLEAN
	###################################################################

	'''
		exclude:
			True: Attributes that should be removed even if they are officially supported by Kodi. Uses the default exclude attributes. This is useful if the skin should be forced (eg: streams directory - do not show the movie title, but use the custom createrd label instead).
			List: Attributes that should be removed even if they are officially supported by Kodi.
		studio:
			True: If no studio is specified in the metadata, add an empty string as the studio. This prevents some skins (eg: Aeon Nox) from showing thumbnails instead of of the stuio logo for certain views.
			False: If no studio is specified in the metadata, leave it as is and do not add an empty string.
	'''
	def clean(self, metadata, media = None, exclude = None, studio = True):
		if not metadata: return None
		if Tools.isString(metadata): metadata = Converter.jsonFrom(metadata)
		else: metadata = self.copy(metadata) # Create a copy, since we do not want to edit the outside dictionary passed to this function.
		if media is None: media = self.media(metadata = metadata)

		# Do not replace if already set (eg: video.py -> playing trailers in cinematic mode).
		if not 'mediatype' in metadata or not metadata['mediatype']:
			if Media.typeMovie(media): metadata['mediatype'] = 'movie'
			elif media == Media.TypeShow: metadata['mediatype'] = 'tvshow'
			elif media == Media.TypeSeason: metadata['mediatype'] = 'season'
			elif media == Media.TypeEpisode: metadata['mediatype'] = 'episode'
			elif media == Media.TypeSpecialRecap: metadata['mediatype'] = 'episode'
			elif media == Media.TypeSpecialExtra: metadata['mediatype'] = 'episode'

		# Do before cleaning the metadata, since we need the IDs.
		self.cleanTrailer(metadata = metadata, media = media)

		# Do before cleaning the metadata, since we need the 'voting'.
		self.cleanVoting(metadata = metadata)

		# Filter out non-existing/custom keys.
		# Otherise there are tons of errors in Kodi 18 log.
		allowed = self.mMetaAllowed
		if exclude:
			if not Tools.isArray(exclude): exclude = self.mMetaExclude
			allowed = [i for i in allowed if not i in exclude]
		metadata = {k : v for k, v in metadata.items() if k in allowed}

		try: metadata['duration'] = int(metadata['duration'])
		except: pass
		try: metadata['year'] = int(metadata['year'])
		except: pass

		# Do this before data is saved to the MetaCache.
		# Otherwise a bunch of regular expressions are called every time the menu is loaded.
		#self.cleanPlot(metadata = metadata)

		self.cleanCountry(metadata = metadata)
		self.cleanCast(metadata = metadata)
		self.cleanCrew(metadata = metadata)
		self.cleanStudio(metadata = metadata, media = media, empty = studio)

		return metadata

	@classmethod
	def cleanId(self, metadata = None, id = None):
		# Sometimes IMDb IDs show up as "ttt..." (tripple t).
		# Not sure where it comes from.
		# Maybe some APIs have mistakes in their IDs.
		# Eg: ttt4154796
		# Update: this was caused by:
		#	'tt' + Regex.remove(data = str(idImdb), expression = '[^0-9]', all = True)
		# That was called without "all = True", therefore only replacing the first t.
		# This has been fixed now.
		if metadata:
			try:
				if metadata['imdb'].startswith('ttt'): metadata['imdb'] = 'tt' + metadata['imdb'].replace('t', '')
			except: pass
			for i in ['show', 'season', 'episode']:
				try:
					if metadata['id'][i]['imdb'].startswith('ttt'): metadata['id'][i]['imdb'] = 'tt' + metadata['id'][i]['imdb'].replace('t', '')
				except: pass
			return metadata
		elif id:
			if id.startswith('ttt'): id = 'tt' + id.replace('t', '')
			return id
		else:
			return None

	@classmethod
	def cleanSeason(self, metadata):
		for i in ['seasonCurrent', 'seasonPrevious', 'seasonNext']:
			try: del metadata[i]
			except: pass
		return metadata

	def cleanPlot(self, metadata):
		try:
			if 'plot' in metadata:
				plot = original = metadata['plot']
				if plot:
					# Some have no plot, just showing "Add a Plot<a ...".
					if Regex.match(data = plot, expression = '(add\s*a\s*plot)'): plot = None

					if plot:
						# Some plots end with a URL.
						plot = Regex.remove(data = plot, expression = '.{10,}\.(\s*(?:[a-z\d\s\-\,\;\:\\\']*)(?:https?:\/\/|www\.).*?$)', group = 1)

						# Some plots end with "see full summary".
						plot = Regex.remove(data = plot, expression = '.{10,}(see\s*full\s*summary.*$)', group = 1).strip()

						# Some plots start with "Short synopsis (50 words)".
						# https://www.imdb.com/title/tt20158938/
						plot = Regex.remove(data = plot, expression = '(short\s*synopsis\s*(?:[\[\(]\d+\s*words?[\]\)]\s*)?(?:docu(?:mentary)?|short|movie|film|(?:tv\s*)?show|series?)?,?\s*)', group = 1)

						# Some plots are cut off and do not end with a full stop.
						if Regex.match(data = plot, expression = '[a-z\d]$'): plot += ' ...'

					if plot: metadata['plot'] = plot.strip()
		except: Logger.error()

	def cleanCountry(self, metadata):
		try:
			# Change country codes to names.
			if 'country' in metadata and metadata['country']: metadata['country'] = [Country.name(i) if len(i) <= 3 else i for i in metadata['country']]
		except: Logger.error()

	def cleanVoting(self, metadata):
		'''
			The rating is calculated twice:
				1. Once the metadata is retrieved the first time and before it is saved to the MetaCache.
				   This ensures there is always a rating/votes if the metadata dictionary is used/passed elsewhere where is does not get cleaned first.
				2. Every time the metadata gets cleaned, that is every time amenu is loaded.
				   This has the advantage of not having to re-retrieve metadata (invalidating the metadata in MetaCache due to the 'settings' property) if the user changes the rating settings.
				   Another advantage is that we can later add code to retrieve the user's ratings from Trakt and overlaying it (similar to the playcount, watched, progress).
				   Then if the user casts a new vote, the rating can be dynamically added and reculated once the menu iss loaded, without having to re-retrieve metadata before saving it to MetaCache.
		'''
		voting = self.voting(metadata = metadata)
		if voting:
			for i in ['rating', 'userrating']:
				if i in voting and not voting[i] is None:
					rating = voting[i]
					if rating and rating > 0 and rating < 0.1: rating = 0.1 # Some skins (eg: Estaury) show a 0.0 rating for low ratings like 0.004 (eg: Jeopardy! S38).
					metadata[i] = rating
			for i in ['votes']:
				if i in voting and not voting[i] is None: metadata[i] = voting[i]

	def cleanCast(self, metadata):
		try:
			for i in ['cast', 'castandrole']:
				if i in metadata:
					cast = metadata[i]
					if not cast: del metadata[i]
					elif cast and Tools.isDictionary(cast[0]): metadata[i] = [(j['name'], j['role']) for j in cast]
		except: Logger.error()

	def cleanCrew(self, metadata):
		try:
			for i in ['director', 'writer']:
				if i in metadata:
					crew = metadata[i]
					if crew:
						if Tools.isDictionary(crew[0]): metadata[i] = [j['name'] for j in crew]
						elif Tools.isArray(crew[0]): metadata[i] = [j[0] for j in crew]
					else: del metadata[i]
		except: Logger.error()

	def cleanStudio(self, metadata, media = None, empty = True):
		try:
			# Some studio names are not detected and no logos are shown in the menus (eg: Aeon Nox).
			if 'studio' in metadata and metadata['studio']:
				studios = None

				# Kodi documentation states that the studio attribute can be a string or a list.
				# However, with a list, some skins can for insatnce not set the studio logo (eg: Aeon Nox).
				if Tools.isArray(metadata['studio']):
					# These currently do not have logos in resource.images.studios.white.
					# Try picking another studio if possible.
					studios = [i for i in metadata['studio'] if not i in self.mStudioIgnore]
				else:
					studios = [metadata['studio']]

				if studios:
					for key, value in self.mStudioReplacePartial.items():
						for i in range(len(studios)):
							studios[i] = Regex.replace(data = studios[i], expression = key, replacement = value, group = 1)
					for key, value in self.mStudioReplaceFull.items():
						for i in range(len(studios)):
							if Regex.match(data = studios[i], expression = key):
								studios[i] = value

				# Studio logos do not work if there are multiple studios.
				# Eg:  DoWork - Direct texture file loading failed for resource://resource.images.studios.white/Columbia Pictures / Relativity Media / Pariah.png
				if studios: metadata['studio'] = [studios[0]] if self.mKodiNew else studios[0]

			# Some skins, like Aeon Nox (List View), show the poster in the menu when there is no studio.
			# This looks ugly, so set an empty studio.
			# Do not use space or empty string, since it will be ignored by the skin.
			# Do not use a string that contains visible characters (eg: '0'), since some view types (eg: Aeon Nox - Icons) will show the studio as text if no icon is availble.
			if empty and not 'studio' in metadata  and not media == Media.TypeSet: metadata['studio'] = ['\u200c'] if self.mKodiNew else '\u200c'
		except: Logger.error()

	@classmethod
	def cleanTrailer(self, metadata, media = None):
		if metadata:
			trailer = {}
			if media is None: media = self.media(metadata = metadata)

			trailer['video'] = 'trailer'
			trailer['media'] = media
			try:
				if metadata['imdb']: trailer['imdb'] = metadata['imdb']
			except: pass
			try:
				if metadata['tmdb']: trailer['tmdb'] = metadata['tmdb']
			except: pass
			try:
				if metadata['tvdb']: trailer['tvdb'] = metadata['tvdb']
			except: pass
			try: trailer['title'] = metadata['tvshowtitle']
			except:
				try: trailer['title'] = metadata['title']
				except: pass
			try: trailer['year'] = metadata['year']
			except: pass
			try: trailer['season'] = metadata['season']
			except: pass
			try: trailer['link'] = metadata['trailer']
			except: pass

			metadata['trailer'] = System.command(action = 'streamsVideo', parameters = trailer)

	###################################################################
	# VOTING
	###################################################################

	def voting(self, metadata):
		if not metadata or not 'voting' in metadata: return None

		settingMain = None
		settingFallback = None
		settingUser = None
		if Media.typeTelevision(self.media(metadata = metadata)):
			settingMain = self.mRatingShowMain
			settingFallback = self.mRatingShowFallback
			settingUser = self.mRatingShowUser
		else:
			settingMain = self.mRatingMovieMain
			settingFallback = self.mRatingMovieFallback
			settingUser = self.mRatingMovieUser

		voting = metadata['voting']
		result = self.votingCalculate(setting = settingMain, voting = voting)
		if not result:
			result = self.votingCalculate(setting = settingFallback, voting = voting)
			if not result:
				result = self.votingCalculate(setting = MetaTools.RatingDefault, voting = voting)

		if not settingUser is False:
			rating = self.votingUser(voting = voting)
			if rating:
				if not result: result = {}
				result['userrating'] = rating
				if settingUser: result['rating'] = rating

		return result

	def votingUser(self, voting):
		if 'user' in voting:
			voting = voting['user']
			for provider in MetaTools.RatingProviders:
				if provider in voting:
					rating = voting[provider]
					if rating: return rating
		return None

	def votingCalculate(self, setting, voting):
		if setting in MetaTools.RatingProviders: return self.votingProvider(voting = voting, provider = setting)
		elif setting == MetaTools.RatingAverage: return self.votingAverage(voting = voting)
		elif setting == MetaTools.RatingAverageWeighted: return self.votingAverageWeighted(voting = voting)
		elif setting == MetaTools.RatingAverageLimited: return self.votingAverageLimited(voting = voting)
		else: return None

	def votingProvider(self, voting, provider):
		if provider in voting['rating'] and voting['rating'][provider]: return {'rating' : voting['rating'][provider], 'votes' : voting['votes'][provider]}
		else: return None

	def votingExtract(self, voting):
		result = {'rating' : [], 'votes' : []}

		for provider in MetaTools.RatingProviders:
			if provider in voting['rating']:
				rating = voting['rating'][provider]
				if rating:
					votes = 0
					if provider in voting['votes']: votes = voting['votes'][provider]
					if Tools.isArray(rating): result['rating'].extend(rating)
					else: result['rating'].append(rating)
					if Tools.isArray(votes): result['votes'].extend(votes)
					else: result['votes'].append(votes if votes else MetaTools.RatingVotes)

		return result

	def votingAverage(self, voting):
		result = self.votingExtract(voting = voting)
		if not result['rating']: return None
		result['rating'] = sum(result['rating']) / len(result['rating'])
		result['votes'] = sum(result['votes'])
		return result

	def votingAverageWeighted(self, voting):
		result = self.votingExtract(voting = voting)
		if not result['rating']: return None

		votes = sum(result['votes'])
		rating = 0
		for i in range(len(result['rating'])):
			rating += result['rating'][i] * result['votes'][i]
		if votes: rating /= float(votes)

		result['rating'] = rating
		result['votes'] = votes
		return result

	def votingAverageLimited(self, voting):
		result = self.votingExtract(voting = voting)
		if not result['rating']: return None

		# If the highest votes are more than 1000, limit it to twice the 2nd highest.
		# Example:
		#	Before: IMDb=100200 | TMDb=5000 | Trakt=100
		#	After: IMDb=10000 | TMDb=5000 | Trakt=100
		votesHighest = max(result['votes'])
		try: votesLimit = sorted(result['votes'])[-2]
		except: votesLimit = votesHighest
		votesLimit = (votesLimit * 2) if (votesHighest > 1000 and votesLimit > 500) else votesHighest

		votes = 0
		rating = 0
		for i in range(len(result['rating'])):
			vote = min(result['votes'][i], votesLimit)
			rating += result['rating'][i] * vote
			votes += vote
		rating /= float(votes)

		result['rating'] = rating
		result['votes'] = sum(result['votes'])
		return result

	###################################################################
	# KIDS
	###################################################################

	@classmethod
	def kidsOnly(self, kids):
		return kids == Selection.TypeInclude

	def kidsFilter(self, kids, items):
		if self.kidsOnly(kids = kids): items = [item for item in items if 'mpaa' in item and Kids.allowed(item['mpaa'])]
		return items

	###################################################################
	# FILTER
	###################################################################

	def filterKids(self, items, kids):
		return self.kidsFilter(kids = kids, items = items)

	def filterRelease(self, items, unknown = False, date = None, days = 0, hours = 0):
		result = []
		if date: date = Time.integer(str(date))
		else: date = Time.integer(Time.past(days = days, hours = hours, format = Time.FormatDate))

		for item in items:
			release = None
			if not release:
				try: release = item['aired']
				except: pass
			if not release:
				try: release = item['premiered']
				except: pass
			if not release:
				try: release = '%d-01-01' % item['year']
				except: pass

			if not release and unknown: result.append(item)
			elif release and Time.integer(release) <= date: result.append(item)

		return result

	def filterDuplicate(self, items, id = True, title = False, number = False):
		if id:
			result = []
			duplicates = {'imdb' : [], 'tmdb' : [], 'tvdb' : [], 'trakt' : []}
			keys = list(duplicates.keys())
			for item in items:
				found = False
				for i in keys:
					if i in item and item[i]:
						j = item[i]
						if number:
							try: season = str(item['season'])
							except: season = 'z'
							try: episode = str(item['episode'])
							except: episode = 'z'
							j = '%s_%s_%s' % (j, season, episode)
						if j in duplicates[i]:
							found = True
							break
						else: duplicates[i].append(j)
				if not found: result.append(item)
			items = result

		if title:
			result = []
			duplicates = []
			keys = ['title', 'originaltitle']
			for item in items:
				found = False
				values = []
				for i in keys:
					if i in item and item[i]:
						# Important to use lower case, since sometimes the titles between IMDb and TMDb do not use the sasme case.
						# Eg: "Operation Fortune: Ruse de guerre" vs Operation Fortune: Ruse de Guerre
						j = Regex.remove(data = item[i].lower(), expression = Regex.Symbol, all = True).replace('  ', ' ')
						if number:
							try: season = str(item['season'])
							except: season = 'z'
							try: episode = str(item['episode'])
							except: episode = 'z'
							j = '%s_%s_%s' % (j, season, episode)
						if j in duplicates: found = True
						else: values.append(j)
				duplicates.extend(values)
				if not found: result.append(item)
			items = result

		return items

	def filterContains(self, items, item, number = False, result = False):
		duplicates = {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None}

		for id in duplicates.keys():
			if id in item and item[id]:
				i = item[id]
				if number:
					try: season = str(item['season'])
					except: season = 'z'
					try: episode = str(item['episode'])
					except: episode = 'z'
					i = '%s_%s_%s' % (i, season, episode)
				duplicates[id] = i

		for item in items:
			for id in duplicates.keys():
				if id in item and item[id] and duplicates[id]:
					i = item[id]
					if number:
						try: season = str(item['season'])
						except: season = 'z'
						try: episode = str(item['episode'])
						except: episode = 'z'
						i = '%s_%s_%s' % (i, season, episode)
					if i == duplicates[id]: return item if result else True

		return None if result else False

	def filterLimit(self, items, limit = True):
		if limit: return items[:50 if limit is True else limit]
		else: return items

	def filterNumber(self, items, season = None, episode = None, single = False):
		if Tools.isArray(items) and not season is None and not episode is None:
			season = abs(season)
			episode = abs(episode)

			number = [x for x, y in enumerate(items) if y['season'] == season and y['episode'] == episode]
			if not number: number = [x for x, y in enumerate(items) if y['season'] == season + 1 and (y['episode'] == 0 or y['episode'] == 1)]
			if number:
				number = number[-1]
				if self.mShowInterleave:
					if single: items = [y for x, y in enumerate(items) if x == number or y['season'] == 0]
					else: items = [y for x, y in enumerate(items) if x >= number or y['season'] == 0]
				else:
					if single: items = [y for x, y in enumerate(items) if x == number]
					else: items = [y for x, y in enumerate(items) if x >= number]

		return items

	def filterGenre(self, items, genre):
		genre = genre.lower()
		return [item for item in items if 'genre' in item and genre in [j.lower() for j in item['genre']]]

	###################################################################
	# PACK
	###################################################################

	# By default set cache = True, since this function is called from shows/seasons/episodes.py, and without caching this can take long when eg trakt progress list is loaded from scratch.
	@classmethod
	def pack(self, show = None, season = None, episode = None, extended = True, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, cache = True):
		try:
			def _packNumber(season, episode):
				return int(('%06d' % season) + ('%06d' % episode))

			# Trakt sometimes has more specials than TVDb.
			# Eg: Game of Thrones: TVDb has 53 specials, Trakt has 236 specials.
			if extended:
				from lib.modules.tools import Matcher
			if extended is True:
				from lib.modules import trakt as Trakt

				entries = []
				if show: entries.append(show)
				if season: entries.append(season[0])
				if episode: entries.append(episode[0])

				for entry in entries:
					if not idImdb: idImdb = entry.idTrakt()
					if not idTmdb: idTmdb = entry.idTmdb()
					if not idTvdb: idTvdb = entry.idTvdb()
					if not idTrakt: idTrakt = entry.idTrakt()

				if not idImdb and not idTrakt:
					ids = self.idShow(idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt)
					if 'trakt' in ids: idTrakt = ids['trakt']
					if 'imdb' in ids: idImdb = ids['imdb']

				if idTrakt or idImdb: extended = Trakt.getTVSeasonSummary(id = idTrakt or idImdb, season = 0, full = True, cache = cache)

			# Determine the number of episodes per season to estimate season pack episode sizes.
			counts = {} # Do not use a list, since not all seasons are labeled by number. Eg: MythBusters
			episodes = []
			seasons = {}

			if show:
				season = show.season(sort = True)
				episode = show.episode(sort = True)

			if season:
				if not Tools.isArray(season): season = [season]
				for i in season:
					seasons[i.numberSeason()] = i
					i = i.episode(sort = True)
					if i: episodes.extend(i)

			if episode:
				if not Tools.isArray(episode): episode = [episode]
				if episode: episodes.extend(episode)

			temp = []
			seen = set()
			for i in episodes:
				number = i.number(format = MetaData.FormatUniversal)
				if not number in seen:
					seen.add(number)
					temp.append(i)
			episodes = temp

			episodesNumber = {}
			episodesOrder = []
			for i in episodes:
				number = i.numberSeason()
				if not number in counts: counts[number] = 0
				counts[number] += 1
				if not number in episodesNumber: episodesNumber[number] = []
				episodesNumber[number].append(i)
				if number > 0: episodesOrder.append(_packNumber(season = number, episode = i.numberEpisode()))

			# Some shows have 0 special episodes on TVDb, but do have specials on Trakt.
			# Make sure to add the Trakt episodes even if TVDb does not have a S0.
			# Eg: It's Always Sunny in Philadelphia
			try:
				if not 0 in episodesNumber and Tools.isArray(extended):
					specials = False
					for i in extended:
						if i and 'season' in i and i['season'] == 0:
							specials = True
							break
					if specials: episodesNumber[0] = []
			except: Logger.error()

			episodesOrder = Tools.listSort(episodesOrder)
			temp = {}
			for i in range(len(episodesOrder)):
				temp[episodesOrder[i]] = i + 1
			episodesOrder = temp

			if not episodesNumber and show:
				i = show.season()
				if i:
					for j in i:
						number = j.numberSeason()
						counts[number] = 0
						episodesNumber[number] = []

			time = Time.timestamp()
			seasonItems = []
			for number, item in episodesNumber.items():
				if item or item == []:
					try: numbersSeason = item[0].numbersSeason()
					except: numbersSeason = None
					if not numbersSeason: numbersSeason = {MetaData.NumberOfficial : number}
					if not MetaData.NumberAbsolute in numbersSeason: numbersSeason[MetaData.NumberAbsolute] = 1 if number > 0 else 0

					releases = []
					episodeItems = {}
					for i in item:
						release = i.releaseDateFirst(format = MetaData.FormatTimestamp)
						releases.append(release if release else 0)
						episodeNumber = i.numberEpisode()

						try: numbers = i.numbersEpisode()
						except: numbers = None
						if not numbers: numbers = {MetaData.NumberOfficial : episodeNumber}
						try: numbers[MetaData.NumberAbsolute] = episodesOrder[_packNumber(season = number, episode = episodeNumber)]
						except: pass

						episodeItems[episodeNumber] = {
							'title' : i.title(),
							'number' : numbers,
							'duration' : i.duration(),
							'time' : release,
							'year' : None,
						}
					if number == 0 and Tools.isArray(extended):
						for i in extended:
							episodeNumber = i.get('number')
							episodeTitle = i.get('title')
							episodeDuration = i.get('runtime')
							if episodeDuration: episodeDuration *= 60
							episodePremiered = i.get('first_aired')
							if episodePremiered: episodePremiered = Time.timestamp(fixedTime = episodePremiered, iso = True)

							if episodeNumber in episodeItems:
								# TVDb often has missing duration and release dates.
								# Use Trakt values instead.
								# Compare titles and not episode numbers, since TVDb and Trakt specials sometimes do not have the same order.
								found = False
								if episodeTitle:
									for key, value in episodeItems.items():
										if value['title'] and Matcher.levenshtein(episodeTitle, value['title'][0], ignoreCase = True, ignoreSpace = True, ignoreNumeric = False, ignoreSymbol = True) > 0.99:
											if not value['duration']: value['duration'] = episodeDuration
											if not value['time']: value['time'] = episodePremiered
											found = True
											break

								# If both titles are missing, fall back to the episode number.
								if not found:
									episodeItem = episodeItems[episodeNumber]
									if not episodeItem['title']:
										if not episodeItem['duration']: episodeItem['duration'] = episodeDuration
										if not episodeItem['time']: episodeItem['time'] = episodePremiered

							else:
								episodeItems[episodeNumber] = {
									'title' : [episodeTitle],
									'number' : {MetaData.NumberOfficial : episodeNumber},
									'duration' : episodeDuration,
									'time' : episodePremiered,
									'year' : None,
								}

					episodeItems = list(episodeItems.values())
					episodeItems = Tools.listSort(episodeItems, key = lambda x : x['number'][MetaData.NumberOfficial])

					counts[number] = 0
					episodesNumber[number] = []
					for i in episodeItems:
						counts[number] += 1
						episodesNumber[number].append(i['number'][MetaData.NumberOfficial])

					# In case an episode does not have a duration, use the mean duration of other episodes as replacement.
					duration = []
					missing = 0
					for i in episodeItems:
						if i['duration']: duration.append(i['duration'])
						else: missing += 1
					total = sum(duration)
					valid = len(duration)
					duration = total
					if missing and valid: duration += int(total / float(valid)) * missing
					if not duration: duration = None

					seasonItems.append({
						'number' : numbersSeason,
						'status' : MetaData.StatusEnded if len(releases) > 1 and releases[-1] > 0 and max(releases) < time else MetaData.StatusContinuing, # TVDb only has a status for shows, but not for seasons. Calculate the status based on the episode release dates.
						'count' : len(episodeItems),
						'duration' : {'total' : duration, 'mean' : duration if duration is None else int(duration / float(len(episodeItems)))},
						'time' : {'start' : episodeItems[0]['time'] if episodeItems else None, 'end' : episodeItems[-1]['time'] if episodeItems else None, 'times' : None},
						'year' : {'start' : None, 'end' : None, 'years' : None},
						'episodes' : sorted(episodeItems, key = lambda i : i['number'][MetaData.NumberOfficial]),
					})
				else:
					seasonItems.append({
						'number' : {MetaData.NumberOfficial : number, MetaData.NumberAbsolute : 1 if number > 0 else 0},
						'status' : None,
						'count' : 0,
						'duration' : {'total' : None, 'mean' : None},
						'time' : {'start' : None, 'end' : None, 'times' : None},
						'year' : {'start' : None, 'end' : None, 'years' : None},
						'episodes' : [],
					})
			seasonItems.sort(key = lambda i : i['number'][MetaData.NumberOfficial])

			countEpisodeTotal = sum(list(counts.values()))
			countSeasonTotal = len(counts.keys())
			try: countMeanTotal = int(round(float(countEpisodeTotal) / len(counts.keys())))
			except: countMeanTotal = 0 # If counts is empty

			countSpecial = 0
			if 0 in counts:
				countSpecial = counts[0]
				del counts[0]

			countEpisodeMain = sum(list(counts.values()))
			countSeasonMain = len(counts.keys())
			try: countMeanMain = int(round(float(countEpisodeMain) / len(counts.keys())))
			except: countMeanMain = 0 # If counts is empty

			timeStart = None
			timeEnd = None
			timesShow = []
			yearsShow = []
			for itemSeason in seasonItems:
				timesSeason = []
				yearsSeason = []

				# Calculate episode year.
				for itemEpisode in itemSeason['episodes']:
					if 'time' in itemEpisode and itemEpisode['time']:
						timesSeason.append(itemEpisode['time'])
						itemEpisode['year'] = Time.year(timestamp = itemEpisode['time'])
						yearsSeason.append(itemEpisode['year'])

				# Do not include the end time if the season is still running.
				if 'status' in itemSeason and itemSeason['status'] and not itemSeason['status'] in [MetaData.StatusEnded, MetaData.StatusCanceled]:
					try: itemSeason['time']['end'] = None
					except: pass

				# Calculate season time.
				itemSeason['time']['times'] = Tools.listSort(Tools.listUnique(timesSeason))
				timesShow.extend(itemSeason['time']['times'])

				# Calculate season year.
				if 'time' in itemSeason:
					if 'start' in itemSeason['time'] and itemSeason['time']['start']: itemSeason['year']['start'] = Time.year(timestamp = itemSeason['time']['start'])
					if 'end' in itemSeason['time'] and itemSeason['time']['end']: itemSeason['year']['end'] = Time.year(timestamp = itemSeason['time']['end'])
				itemSeason['year']['years'] = Tools.listSort(Tools.listUnique(yearsSeason))
				yearsShow.extend(itemSeason['year']['years'])

				# Calculate show time period.
				if itemSeason['number'][MetaData.NumberOfficial] > 0:
					if 'start' in itemSeason['time'] and itemSeason['time']['start']:
						timeStart = itemSeason['time']['start'] if timeStart is None else min(timeStart, itemSeason['time']['start'])
					if 'end' in itemSeason['time'] and itemSeason['time']['end']:
						timeEnd = itemSeason['time']['end'] if timeEnd is None else max(timeEnd, itemSeason['time']['end'])

			yearStart = Time.year(timestamp = timeStart) if timeStart else None
			yearEnd = Time.year(timestamp = timeEnd) if timeEnd else None
			yearsShow = Tools.listSort(Tools.listUnique(yearsShow))

			if show and season is None and episode is None:
				return {
					'status' : show.status(),
					'count' : {
						'season' : {'total' : countSeasonTotal, 'main' : countSeasonMain},
					},
					'time' : {'start' : timeStart, 'end' : timeEnd, 'times' : timesShow},
					'year' : {'start' : yearStart, 'end' : yearEnd, 'years' : yearsShow},
					'seasons' : seasonItems,
				}
			else:
				temp = [i['duration']['total'] for i in seasonItems if i['duration']['total']]
				count = sum([i['count'] for i in seasonItems if i['count']])
				durationShowTotal = sum(temp)
				if not durationShowTotal: durationShowTotal = None
				durationMeanTotal = durationShowTotal if durationShowTotal is None else int(durationShowTotal / float(count))
				temp = [i['duration']['total'] for i in seasonItems if i['duration']['total'] and not i['number'][MetaData.NumberOfficial] == 0]
				count = sum([i['count'] for i in seasonItems if i['count'] and not i['number'][MetaData.NumberOfficial] == 0])
				durationShowMain = sum(temp)
				if not durationShowMain: durationShowMain = None
				durationMeanMain = durationShowMain if durationShowMain is None else int(durationShowMain / float(count))
				return {
					'status' : show.status() if show else None,
					'count' : {
						'season' : {'total' : countSeasonTotal, 'main' : countSeasonMain},
						'episode' : {'total' : countEpisodeTotal, 'main' : countEpisodeMain},
						'mean' : {'total' : countMeanTotal, 'main' : countMeanMain},
						'special' : countSpecial,
					},
					'duration' : {
						'show' : {'total' : durationShowTotal, 'main' : durationShowMain},
						'mean' : {'total' : durationMeanTotal, 'main' : durationMeanMain},
					},
					'time' : {'start' : timeStart, 'end' : timeEnd, 'times' : timesShow},
					'year' : {'start' : yearStart, 'end' : yearEnd, 'years' : yearsShow},
					'seasons' : seasonItems,
				}
		except: Logger.error()
		return None

	###################################################################
	# ID
	###################################################################

	@classmethod
	def _idCache(self, function, **kwargs):
		return Cache.instance().cache(None, Cache.TimeoutWeek1, None, function, **kwargs)

	@classmethod
	def id(self, media, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, title = None, year = None, deviation = True, cache = True, extra = False, extended = False):
		if media == Media.TypeSet: return self.idSet(idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, title = title, year = year, deviation = deviation, cache = cache, extra = extra, extended = extended)
		elif Media.typeTelevision(media): return self.idShow(idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, title = title, year = year, deviation = deviation, cache = cache, extra = extra)
		else: return self.idMovie(idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, title = title, year = year, deviation = deviation, cache = cache, extra = extra)

	@classmethod
	def idMovie(self, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, title = None, year = None, deviation = True, cache = True, extra = False):
		if cache:
			# Do these separately, otherwise if this function is called with different ID-combination, it will not use the cached result.
			# Eg: the function is called 1st with only an IMDb ID, and a 2nd time with an IMDb and TMDb ID.
			result = None
			if not result and idImdb: result = self._idCache(function = self.idMovie, idImdb = idImdb, extra = extra, cache = False)
			if not result and idTmdb: result = self._idCache(function = self.idMovie, idTmdb = idTmdb, extra = extra, cache = False)
			if not result and idTrakt: result = self._idCache(function = self.idMovie, idTrakt = idTrakt, extra = extra, cache = False)
			if not result and idTvdb: result = self._idCache(function = self.idMovie, idTvdb = idTvdb, extra = extra, cache = False)
			if not result and title: result = self._idCache(function = self.idMovie, title = title, year = year, deviation = deviation, extra = extra, cache = False)
			return result

		result = {}
		lookup = False

		# Search Trakt by ID.
		try:
			if not result or not 'imdb' in result or not result['imdb']:
				if idImdb or idTmdb or idTvdb or idTrakt:
					from lib.modules import trakt
					lookup = True
					data = trakt.SearchMovie(imdb = idImdb, tmdb = idTmdb, tvdb = idTvdb, trakt = idTrakt, single = True, full = extra, cache = False)
					if data and 'movie' in data:
						ids = data['movie'].get('ids')
						if ids:
							ids = {k : str(v) for k, v in ids.items() if v}
							if ids:
								Tools.update(result, ids, none = False)
								if extra: Tools.update(result, {'title' : data['movie'].get('title'), 'year' : data['movie'].get('year'), 'score' : data.get('score'), 'rating' : data['movie'].get('rating'), 'votes' : data['movie'].get('votes'), 'comments' : data['movie'].get('comment_count')}, none = False)
		except: Logger.error()

		# Search TMDb by ID.
		# Do this after Trakt, since it only returns the IMDb/TMDb ID.
		try:
			if not result or not 'imdb' in result or not result['imdb']:
				if idImdb or idTmdb:
					from lib.modules.network import Networker
					from lib.modules.account import Tmdb
					key = Tmdb().key()
					lookup = True
					if idTmdb:
						link = 'https://api.themoviedb.org/3/movie/%s/external_ids' % idTmdb
						data = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key})
						if data:
							id = data.get('imdb_id')
							if id:
								Tools.update(result, {'imdb' : id}, none = False)
								if extra: Tools.update(result, {'score' : data.get('popularity'), 'rating' : data.get('vote_average'), 'votes' : data.get('vote_count')}, none = False)
					elif idImdb:
						link = 'https://api.themoviedb.org/3/find/%s' % idImdb
						data = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key, 'external_source' : 'imdb_id'})
						if data and 'movie_results' in data and data['movie_results']:
							id = data['movie_results'][0].get('id')
							if id:
								Tools.update(result, {'tmdb' : id}, none = False)
								if extra:
									data2 = data['movie_results'][0]
									release = None
									if 'release_date' in data2:
										release = Regex.extract(data = data2['release_date'], expression = '(\d{4})-', group = 1)
										release = int(release) if release else None
									Tools.update(result, {'title' : data2.get('title'), 'year' : release, 'score' : data2.get('popularity'), 'rating' : data2.get('vote_average'), 'votes' : data2.get('vote_count')}, none = False)
		except: Logger.error()

		if not lookup and title:

			# Search Trakt by title.
			try:
				if not result or not 'imdb' in result or not result['imdb']:
					from lib.modules import trakt
					data = trakt.SearchMovie(title = title, year = year, single = True, full = extra, cache = False)
					if not(data and 'movie' in data and data['movie']) and deviation and year: data = trakt.SearchMovie(title = title, year = [int(year) - 1, int(year) + 1], single = True, full = extra, cache = False)
					if data and 'movie' in data:
						ids = data['movie'].get('ids')
						if ids:
							result = {}
							ids = {k : str(v) for k, v in ids.items() if v}
							if ids:
								Tools.update(result, ids, none = False)
								if extra: Tools.update(result, {'title' : data.get('title'), 'year' : data.get('year'), 'score' : data.get('score'), 'rating' : data['movie'].get('rating'), 'votes' : data['movie'].get('votes'), 'comments' : data['movie'].get('comment_count')}, none = False)
			except: Logger.error()

			# Search TMDb by title.
			# Do this after Trakt, since it only returns the IMDb ID.
			try:
				if not result or not 'imdb' in result or not result['imdb']:
					from lib.modules.account import Tmdb
					from lib.modules.network import Networker
					from lib.modules.clean import Title
					key = Tmdb().key()
					query = Title.clean(title)
					yearDeviated = year
					link = 'https://api.themoviedb.org/3/search/movie'

					data = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key, 'query' : query, 'year' : year})
					if not(data and 'results' in data and data['results']) and deviation and year:
						yearDeviated = int(year) + 1
						data = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key, 'query' : query, 'year' : yearDeviated})
						if not(data and 'results' in data and data['results']) and deviation and year:
							yearDeviated = int(year) - 1
							data = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key, 'query' : query, 'year' : yearDeviated})

					if data and 'results' in data:
						data = data['results']
						for i in data:
							if (query == Title.clean(i['title']) or query == Title.clean(i['original_title'])):
								release = None
								if 'release_date' in i:
									release = Regex.extract(data = i['release_date'], expression = '(\d{4})-', group = 1)
									release = int(release) if release else None
								if not year or yearDeviated == release:
									link = 'https://api.themoviedb.org/3/movie/%s/external_ids' % str(i['id'])
									data2 = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key})
									if data2:
										id = data2.get('imdb_id')
										if id:
											Tools.update(result, {'imdb' : id, 'tmdb' : str(data2.get('id'))}, none = False)
											if extra: Tools.update(result, {'title' : i.get('title'), 'year' : release, 'score' : i.get('popularity'), 'rating' : i.get('vote_average'), 'votes' : i.get('vote_count')}, none = False)
									break
			except: Logger.error()

		return result if result else None

	@classmethod
	def idSet(self, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, title = None, year = None, deviation = True, cache = True, extra = False, extended = False):
		if cache:
			result = None
			if not result and title: result = self._idCache(function = self.idSet, title = title, year = year, deviation = deviation, extra = extra, extended = extended, cache = False)
			return result

		result = {}
		lookup = False
		prefix = 'the '
		suffix = ' collection'
		if not lookup and title:

			# Search TMDb by title.
			try:
				if not result or not 'tmdb' in result or not result['tmdb']:
					from lib.modules.account import Tmdb
					from lib.modules.network import Networker
					from lib.modules.clean import Title
					key = Tmdb().key()
					query = Title.clean(title)

					link = 'https://api.themoviedb.org/3/search/collection'
					data = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key, 'query' : query})

					# Searching "The Harry Potter Collection" does not return anything, but "Harry Potter Collection" does return.
					if data and 'results' in data and not data['results'] and query.startswith(prefix):
						data = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key, 'query' : Tools.stringRemovePrefix(data = query, remove = prefix)})

					if data and 'results' in data:
						data = data['results']
						query = Tools.stringRemoveAffix(data = query, prefix = prefix, suffix = suffix)

						# Find exact match.
						for i in data:
							if query == Tools.stringRemoveAffix(data = Title.clean(i['name']), prefix = prefix, suffix = suffix):
								id = i.get('id')
								if id:
									Tools.update(result, {'tmdb' : str(id)}, none = False)
									if extra: Tools.update(result, {'title' : i.get('name'), 'score' : i.get('popularity'), 'rating' : i.get('vote_average'), 'votes' : i.get('vote_count')}, none = False)
									break

						# Find closest match.
						if not result:
							from lib.modules.tools import Matcher
							matches = []
							for i in data:
								if i.get('id'):
									match = Matcher.levenshtein(title, i['name'], ignoreCase = True, ignoreSpace = True, ignoreNumeric = False, ignoreSymbol = True)
									matches.append((match, i))
							if matches:
								matches = Tools.listSort(matches, key = lambda x : x[0])
								i = matches[-1][1]
								if i:
									Tools.update(result, {'tmdb' : str(i.get('id'))}, none = False)
									if extra: Tools.update(result, {'title' : i.get('name'), 'score' : i.get('popularity'), 'rating' : i.get('vote_average'), 'votes' : i.get('vote_count')}, none = False)
			except: Logger.error()

		# Search for the movie title that is part of the collection, instead of searching the collection name.
		if not result and extended and title:
			try:
				if not result or not 'imdb' in result or not result['imdb']:
					from lib.modules.account import Tmdb
					from lib.modules.network import Networker
					from lib.modules.clean import Title
					key = Tmdb().key()
					query = Title.clean(title)
					yearDeviated = year
					link = 'https://api.themoviedb.org/3/search/movie'

					data = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key, 'query' : query, 'year' : year})
					if not(data and 'results' in data and data['results']) and deviation and year:
						yearDeviated = int(year) + 1
						data = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key, 'query' : query, 'year' : yearDeviated})
						if not(data and 'results' in data and data['results']) and deviation and year:
							yearDeviated = int(year) - 1
							data = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key, 'query' : query, 'year' : yearDeviated})

					if data and 'results' in data:
						data = data['results']
						for i in data:
							if (query == Title.clean(i['title']) or query == Title.clean(i['original_title'])):
								id = i['id']
								if id:
									link = 'https://api.themoviedb.org/3/movie/%s' % id
									data2 = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key})
									if data2 and 'belongs_to_collection' in data2 and data2['belongs_to_collection']:
										id = data2['belongs_to_collection']['id']
										if id:
											link = 'https://api.themoviedb.org/3/collection/%s' % id
											data3 = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key})
											if data3:
												Tools.update(result, {'tmdb' : str(data3.get('id'))}, none = False)
												if extra: Tools.update(result, {'title' : data3.get('name'), 'score' : data3.get('popularity'), 'rating' : data3.get('vote_average'), 'votes' : data3.get('vote_count')}, none = False)
											break
			except: Logger.error()

		return result if result else None

	@classmethod
	def idShow(self, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, title = None, year = None, deviation = True, cache = True, extra = False):
		if cache:
			# Do these separately, otherwise if this function is called with different ID-combination, it will not use the cached result.
			# Eg: the function is called 1st with only an IMDb ID, and a 2nd time with an IMDb and TVDb ID.
			result = None
			if not result and idImdb: result = self._idCache(function = self.idShow, idImdb = idImdb, extra = extra, cache = False)
			if not result and idTvdb: result = self._idCache(function = self.idShow, idTvdb = idTvdb, extra = extra, cache = False)
			if not result and idTrakt: result = self._idCache(function = self.idShow, idTrakt = idTrakt, extra = extra, cache = False)
			if not result and idTmdb: result = self._idCache(function = self.idShow, idTmdb = idTmdb, extra = extra, cache = False)
			if not result and title: result = self._idCache(function = self.idShow, title = title, year = year, deviation = deviation, extra = extra, cache = False)
			return result

		result = {}
		manager = None
		lookup = False

		# Search TVDb by ID.
		# Search TVDb before Trakt, since Trakt sometimes returns multiple shows.
		def _idShowTvdbId():
			try:
				nonlocal idImdb
				nonlocal idTmdb
				nonlocal idTvdb
				nonlocal idTrakt
				nonlocal title
				nonlocal year
				nonlocal result
				nonlocal manager
				nonlocal lookup
				nonlocal extra
				nonlocal deviation

				if not result or not 'tvdb' in result or not result['tvdb']:
					if idImdb or idTvdb or idTmdb: # TVDb does not have the Trakt ID.
						if manager is None:
							from lib.meta.manager import MetaManager
							manager = MetaManager(provider = MetaManager.ProviderTvdb, threaded = MetaManager.ThreadedDisable)
						lookup = True
						data = manager.search(idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, media = MetaData.MediaShow, limit = 1, cache = False)
						if data:
							result = {}
							ids = data.id()
							if ids:
								Tools.update(result, ids, none = False)
								if extra: Tools.update(result, {'title' : data.title(), 'year' : data.year(), 'rating' : data.voteRating(), 'votes' : data.voteCount()}, none = False)
			except: Logger.error()

		# Search Trakt by ID.
		# Trakt can sometimes return multiple shows for the same IMDb ID.
		# Eg: For "TVF Pitchers" Trakt returns
		#	{"trakt":100814,"slug":"tvf-pitchers-2015","tvdb":298807,"imdb":"tt4742876","tmdb":63180}
		#	{"trakt":185757,"slug":"tvf-pitchers-2015-185757","tvdb":298868,"imdb":"tt4742876","tmdb":63180}
		def _idShowTraktId():
			try:
				nonlocal idImdb
				nonlocal idTmdb
				nonlocal idTvdb
				nonlocal idTrakt
				nonlocal title
				nonlocal year
				nonlocal result
				nonlocal manager
				nonlocal lookup
				nonlocal extra
				nonlocal deviation

				if not result or not 'tvdb' in result or not result['tvdb']:
					if idImdb or idTvdb or idTrakt:
						from lib.modules import trakt
						lookup = True
						data = trakt.SearchTVShow(imdb = idImdb, tmdb = idTmdb, tvdb = idTvdb, trakt = idTrakt, single = True, full = extra, cache = False)
						if data and 'show' in data:
							ids = data['show'].get('ids')
							if ids:
								result = {}
								ids = {k : str(v) for k, v in ids.items() if v}
								if ids:
									Tools.update(result, ids, none = False)
									if extra: Tools.update(result, {'title' : data['show'].get('title'), 'year' : data['show'].get('year'), 'score' : data.get('score'), 'rating' : data['show'].get('rating'), 'votes' : data['show'].get('votes'), 'comments' : data['show'].get('comment_count')}, none = False)
			except: Logger.error()

		# Search TVDb by title.
		def _idShowTvdbTitle():
			try:
				nonlocal idImdb
				nonlocal idTmdb
				nonlocal idTvdb
				nonlocal idTrakt
				nonlocal title
				nonlocal year
				nonlocal result
				nonlocal manager
				nonlocal lookup
				nonlocal extra
				nonlocal deviation

				if not result or not 'tvdb' in result or not result['tvdb']:
					from lib.modules.clean import Title
					if manager is None:
						from lib.meta.manager import MetaManager
						manager = MetaManager(provider = MetaManager.ProviderTvdb, threaded = MetaManager.ThreadedDisable)
					query = Title.clean(title)

					if year:
						year = int(year)
						if deviation: years = [year, year + 1, year - 1]
						else: years = [year]
					else:
						years = [None]

					found = False
					for i in years:
						data = manager.search(query = query, year = i, media = MetaData.MediaShow, cache = False)
						if data:
							for j in data:
								if query == Title.clean(j.titleOriginal(selection = MetaData.SelectionSingle)) and (not year or j.year() in years):
									result = {}
									ids = j.id()
									if ids:
										Tools.update(result, ids, none = False)
										if extra: Tools.update(result, {'title' : j.title(), 'year' : j.year(), 'rating' : j.voteRating(), 'votes' : j.voteCount()}, none = False)
										found = True
										break
							if found: break
			except: Logger.error()

		# Search Trakt by title.
		def _idShowTraktTitle():
			try:
				nonlocal idImdb
				nonlocal idTmdb
				nonlocal idTvdb
				nonlocal idTrakt
				nonlocal title
				nonlocal year
				nonlocal result
				nonlocal manager
				nonlocal lookup
				nonlocal extra
				nonlocal deviation

				if not result or not 'tvdb' in result or not result['tvdb']:
					from lib.modules import trakt
					data = trakt.SearchTVShow(title = title, year = year, single = True, full = extra, cache = False)
					if not(data and 'show' in data and data['show']) and deviation and year: data = trakt.SearchTVShow(title = title, year = [int(year) - 1, int(year) + 1], single = True, full = extra, cache = False)
					if data and 'show' in data:
						ids = data['show'].get('ids')
						if ids:
							result = {}
							ids = {k : str(v) for k, v in ids.items() if v}
							if ids:
								Tools.update(result, ids, none = False)
								if extra: Tools.update(result, {'title' : data['show'].get('title'), 'year' : data['show'].get('year'), 'score' : data.get('score'), 'rating' : data['show'].get('rating'), 'votes' : data['show'].get('votes'), 'comments' : data['show'].get('comment_count')}, none = False)
			except: Logger.error()

		# TVDb does not have rating/votes in the search endpoint.
		# Utilize Trakt first. Used by Oracle to determine if a title is a movie or show based on these values.
		if extra:
			_idShowTraktId()
			_idShowTvdbId()
			if not lookup and title:
				_idShowTraktTitle()
				_idShowTvdbTitle()
		else:
			_idShowTvdbId()
			_idShowTraktId()
			if not lookup and title:
				_idShowTvdbTitle()
				_idShowTraktTitle()

		return result if result else None

	###################################################################
	# BUSY
	###################################################################

	'''
		Scenario:
			a. Clear the local metadata.db and load a show menu (eg: Highest Rated).
			b. Since no local metadata is available, the metadata is now retrieved from script.gaia.metadata, returned immediatly, and the new metadata is retrieved/refreshed in the background.
			c. When the menu is loaded/decorated, in playback.py -> _historyItems() -> each show in the list is retrieved again individually with Shows().metadata(...).
			d. This causes eg 50 separate calls to Shows().metadata(), each of them retrieving the metadata from script.gaia.metadata and refreshing the metadata in the background for a second time.
			e. The metadata is refreshed in the background again, since the original background threads for retrieving the metadata have not yet finished and have not written to MetaCache.
			f. In metadataUpdate() the Memory class is used to check if there are multiple concurrent requests to the same show, and let any subsequent request wait and then just use the cached data without making all the provider requests again.
			g. However, just starting background threads in metadata(), just for them to exit shortly after being started, requires a lot of time, making the "cached" menu still load slowly.
		To solve this, we check if metadata is already retrieved by another thread, BEFORE starting the new background threads.
		This is done with a local Memory variable, and will therefore only work for calls from within the same process/interpreter.
		If eg loading the menu twice (either double clicking by accident, or opening a menu, immediatly going back and then reopening the menu before the previous call fully finished), multiple interpreters are started and this detection will not work, since the class variable is not shared.
		In that case, bad luck, make the background threads start twice. New metadata retrieval should still be skipped inside the thread in metadataUpdate() where Memory is used.
		We could use Memory(kodi = True) to make this work accross interpreters, but the time it takes for looking up and setting the global Kodi variable might not be worth the effort, and would only be used very few times.
	'''

	@classmethod
	def busyClear(self):
		Memory.clear(id = MetaTools.PropertyBusy, local = True, kodi = False)

	@classmethod
	def busyStart(self, media, item):
		busy = False

		values = Memory.get(id = MetaTools.PropertyBusy, local = True, kodi = False)
		if not values:
			values = {}
			Memory.set(id = MetaTools.PropertyBusy, value = values, local = True, kodi = False)

		for i in MetaTools.Providers:
			try:
				if item[i] and item[i] in values[media][i]:
					busy = True
					break
			except: pass

		if not busy:
			for i in MetaTools.Providers:
				try:
					if item[i]:
						if not media in values: values[media] = {}
						if not i in values[media]: values[media][i] = {}
						values[media][i][item[i]] = True
				except: pass

		return busy

	@classmethod
	def busyFinish(self, media, item):
		values = Memory.get(id = MetaTools.PropertyBusy, local = True, kodi = False)
		for i in MetaTools.Providers:
			try: del values[media][i][item[i]]
			except: pass

	###################################################################
	# BATCH
	###################################################################

	@classmethod
	def batchPreload(self):
		from lib.modules.tools import Hardware, Math
		from lib.modules.interface import Dialog
		from lib.modules.concurrency import Pool
		from lib.indexers.movies import Movies
		from lib.indexers.shows import Shows
		from lib.indexers.episodes import Episodes

		performance = Hardware.performance()
		year = Time.year()

		# Do not add more - this already takes 7 minutes on a fast device (if all options are enabled).
		# Update: remove even more and only use the bare minimum.
		# Not only does this slow down the device, but TMDb also has a rate limit based on the IP address, not API key.
		menus = [
			lambda : Movies().arrivals(menu = False),
			lambda : Episodes().arrivals(menu = False),
		]
		if performance in [Hardware.PerformancePoor, Hardware.PerformanceMedium, Hardware.PerformanceGood, Hardware.PerformanceExcellent]:
			menus.extend(menus = [
				lambda : Movies().retrieve(link = 'new', menu = False),
				lambda : Movies().retrieve(link = 'home', menu = False),
				lambda : Episodes().home(menu = False),
			])
			if performance in [Hardware.PerformanceMedium, Hardware.PerformanceGood, Hardware.PerformanceExcellent]:
				menus.extend(menus = [
					lambda : Movies().year(year = year, menu = False),
					#lambda : Movies().retrieve(link = 'popular', menu = False),
					lambda : Shows().year(year = year, menu = False),
					#lambda : Shows().retrieve(link = 'popular', menu = False),
				])
				if performance in [Hardware.PerformanceGood, Hardware.PerformanceExcellent]:
					menus.extend(menus = [
						#lambda : Movies().retrieve(link = 'oscars', menu = False),
						#lambda : Movies().retrieve(link = 'rating', menu = False),
						#lambda : Movies().retrieve(link = 'boxoffice', menu = False),
						#lambda : Movies().retrieve(link = 'theaters', menu = False),
						#lambda : Movies().retrieve(link = 'trending', menu = False),
						#lambda : Movies().retrieve(link = 'featured', menu = False),
						#lambda : Shows().retrieve(link = 'emmies', menu = False),
						#lambda : Shows().retrieve(link = 'rating', menu = False),
						#lambda : Shows().retrieve(link = 'airing', menu = False),
						#lambda : Shows().retrieve(link = 'premiere', menu = False),
						#lambda : Shows().retrieve(link = 'trending', menu = False),
						#lambda : Shows().retrieve(link = 'featured', menu = False),
					])
					if performance in [Hardware.PerformanceExcellent]:
						menus.extend(menus = [
							#lambda : Movies().year(year = year - 1, menu = False),
							#lambda : Shows().year(year = year - 1, menu = False),
							#lambda : Episodes().retrieve(link = 'added', menu = False),
						])

		dialog = None
		def _batchProgress(percent):
			dialog = Dialog.progress(title = 35390, message = 33421, background = True, percent = percent)
			Time.sleep(5)
			try: dialog.close()
			except: pass

		# NB: Do this sequentially and not in concurrent threads.
		# Uses less local resources, and reduces server load.
		previous = None
		total = len(menus)
		for i in range(total):
			if System.aborted(): return False
			# Show dialog before execution, so that the 0% progress shows right at the start.
			percent = min(99, Math.roundDownClosest((i / total) * 100, base = 5))
			if previous is None or percent > previous:
				previous = percent
				Pool.thread(target = _batchProgress, kwargs = {'percent' : percent}, start = True)
			try: menus[i]()
			except: Logger.error()

		try: dialog.close()
		except: pass
		Dialog.notification(title = 35390, message = 33993, icon = Dialog.IconSuccess)
		return True

	@classmethod
	def batchGenerate(self, pagesMovie = None, pagesShow = None, yearsMovie = 70, yearsShow = 35, validation = 2, detail = DetailExtended, clear = False):
		from lib.modules.tools import Math, File
		from lib.modules.interface import Dialog, Format
		from lib.modules.database import Database
		from lib.modules.concurrency import Pool
		from lib.indexers.movies import Movies
		from lib.indexers.sets import Sets
		from lib.indexers.shows import Shows
		from lib.indexers.seasons import Seasons
		from lib.indexers.episodes import Episodes
		from lib.meta.cache import MetaCache
		from lib.modules import trakt

		Settings.default('general.language.primary')
		Settings.default('general.language.secondary')
		Settings.default('general.language.tertiary')
		Settings.default('metadata.location.country')
		self.settingsDetailSet(MetaTools.DetailExtended)

		metacache = MetaCache.instance()
		MetaCache.External = False
		metacache._externalDisable() # Do not use the already preprocessed database.
		if clear: metacache._deleteFile()

		time = Time.timestamp()
		settings = metacache.settingsId()
		for i in MetaCache.Types:
			metacache._update('UPDATE `%s` SET time = %d, settings = "%s";' % (i, time, settings))

		# Trakt has a rate limit of 1000 requests per 5 minutes.
		#	https://trakt.docs.apiary.io/#introduction/rate-limiting
		# TMDb does not have a rate limit anymore.
		# But there are forum posts that says the CDN/Cloudflare might limit concurrent connections to 40 or 50.
		#	https://developers.themoviedb.org/3/getting-started/request-rate-limiting
		#	https://www.themoviedb.org/talk/62c7c1b258361b005fd2e747
		# Cannot find any rate limit for TVDb.
		# Cannot find any rate limit for Fanart.

		# Wait if limit was reached and retry requests again.
		# Otherwise after some time, many entries in the metacache do not have a Trakt ID.
		# Trakt does not strictly enforce the limits. Sometimes a few thousand requests can be made before Trakt returns HTTP 429.
		trakt._limitEnable()

		year = Time.year()

		# Try to reduce the number of pages, otherwise the database can become too large for devices with limited storage space, eg Firesticks (8GB).
		# We do not want to retrieve too much, since the user will probably not use many of these, and it just uses up storage and increases processing time.
		#	Movies:
		#		70 years | [20, 15, 10, 5, 2] pages: 155 MB
		#	Shows:
		#		35 years | [10, 7, 5, 3, 2] pages: 135 MB
		#		35 years | [10, 8, 6, 3, 2] pages: 145 MB (+ new season metadata for the newly added shows)
		#		35 years | [12, 10, 8, 3, 2, 1] pages: 165 MB (+ new season metadata for the newly added shows)
		#	Seasons:
		#		35 years | [10, 7, 5, 3, 2] pages | year >= 1990 | votes >= 0|50000: 15 MB
		#		35 years | [10, 7, 5, 3, 2] pages | year >= 1990 | votes >= 0|30000: 20 MB
		#		35 years | [10, 7, 5, 3, 2] pages | year >= 1990 | votes >= 0|20000: 31 MB
		#		35 years | [10, 7, 5, 3, 2] pages | year >= 1990 | votes >= 0|15000: 36 MB
		#		35 years | [10, 7, 5, 3, 2] pages | year >= 1990 | votes >= 0|10000: 43 MB
		#		35 years | [10, 7, 5, 3, 2] pages | year >= 1990 | votes >= 0|5000: 52 MB
		#		35 years | [10, 7, 5, 3, 2] pages | year >= 1990 | votes >= 20000|3000: 67 MB
		#		35 years | [10, 7, 5, 3, 2] pages | year >= 1990 | votes >= 20000|2500: 70 MB
		#	Episodes:
		#		35 years | [10, 7, 5, 3, 2] pages | year >= 1990 | votes >= 100000|100000|100000|100000: 100 MB
		#		35 years | [10, 7, 5, 3, 2] pages | year >= 1990 | votes >= 100000|95000|85000|75000: 108 MB
		#		35 years | [10, 7, 5, 3, 2] pages | year >= 1990 | votes >= 100000|90000|80000|70000: 114 MB
		#		35 years | [10, 7, 5, 3, 2] pages | year >= 1990 | votes >= 100000|80000|70000|60000: 121 MB
		#		35 years | [10, 7, 5, 3, 2] pages | year >= 1990 | votes >= 100000|70000|60000|50000: 150 MB
		#		35 years | [10, 7, 5, 3, 2] pages | year >= 1990 | votes >= 100000|65000|55000|45000: 160 MB
		#		35 years | [10, 7, 5, 3, 2] pages | year >= 1990 | votes >= 100000|60000|50000|40000: 170 MB
		# NB: Keep the total compressed size to under 100 MB, since Github has file size restrictions.

		if pagesMovie is None: pagesMovie = [20, 15, 10, 5, 2, 1]
		elif Tools.isInteger(pagesMovie): pagesMovie = [pagesMovie, max(1, int(pagesMovie * 0.75)), max(1, int(pagesMovie * 0.50)), max(1, int(pagesMovie * 0.25)), min(2, pagesMovie)]
		if pagesShow is None: pagesShow = [12, 10, 8, 3, 2, 1]
		elif Tools.isInteger(pagesShow): pagesShow = [pagesShow, max(1, int(pagesShow * 0.75)), max(1, int(pagesShow * 0.50)), max(1, int(pagesShow * 0.25)), min(2, pagesShow)]

		# Do not add more - this already takes 7 minutes on a fast device (if all options are enabled).
		# Update: remove even more and only use the bare minimum.
		# Not only does this slow down the device, but TMDb also has a rate limit based on the IP address, not API key.
		menus = []

		# Movies

		menusMovie = [
			{'data' : 'new',				'level' : 2},
			{'data' : 'home',				'level' : 2},

			{'data' : 'popular',			'level' : 0},
			{'data' : 'oscars',				'level' : 0},
			{'data' : 'rating',				'level' : 0},
			{'data' : 'boxoffice',			'level' : 0},

			{'data' : 'theaters',			'level' : 2},
			{'data' : 'trending',			'level' : 2},
			{'data' : 'featured',			'level' : 2},

			{'data' : 'drugsgeneral',		'level' : 3},
			{'data' : 'drugsalcohol',		'level' : 3},
			{'data' : 'drugsmarijuana',		'level' : 3},
			{'data' : 'drugspsychedelics',	'level' : 3},
		]

		values = Movies().genres(menu = False)
		for i in values:
			if 'link' in i and i['link']: menusMovie.append({'label' : 'Genre (%s)' % i['name'], 'data' : i['link'], 'level' : 1})

		values = Movies().years(menu = False)[:yearsMovie]
		counter = 0
		for i in values:
			counter += 1
			if 'link' in i and i['link']: menusMovie.append({'label' : 'Year (%s)' % i['name'], 'data' : i['link'], 'level' : 1 if counter <= 10 else 2 if counter <= 20 else 3 if counter <= 35 else 4})

		menus.extend([{'class' : Movies, 'label' : i['label'] if 'label' in i else None, 'data' : i['data'], 'level' : i['level'], 'pages' : pagesMovie, 'years' : yearsMovie, 'year' : year - yearsMovie} for i in menusMovie])

		# Sets
		menusSets = [
			{'data' : 'browse',				'level' : 0},
			{'data' : 'arrivals',			'level' : 0},
		]

		values = Sets().alphabetic(menu = False)
		for i in values:
			if 'link' in i and i['link']: menusSets.append({'label' : 'Character (%s)' % i['name'], 'data' : i['link'], 'level' : 0})

		menus.extend([{'class' : Sets, 'label' : i['label'] if 'label' in i else None, 'data' : i['data'], 'level' : i['level'], 'pages' : [j * 2 for j in pagesMovie], 'years' : yearsMovie, 'year' : year - yearsMovie} for i in menusSets])

		# Shows

		menusShow = [
			{'data' : 'rating',		'level' : 0},
			{'data' : 'popular',	'level' : 0},
			{'data' : 'emmies',		'level' : 0},
			{'data' : 'views',		'level' : 0},

			{'data' : 'airing',		'level' : 2},
			{'data' : 'premiere',	'level' : 2},
			{'data' : 'trending',	'level' : 2},
			{'data' : 'featured',	'level' : 2},
			{'data' : 'active',		'level' : 2},

			{'data' : 'random1',	'level' : 2},
			{'data' : 'random2',	'level' : 2},
			{'data' : 'random3',	'level' : 2},
		]

		values = Shows().genres(menu = False)
		for i in values:
			if i['name'].lower().startswith(('news', 'reality', 'talk', 'game', 'sport')): level = 5
			elif i['name'].lower().startswith(('biography')): level = 4
			elif i['name'].lower().startswith(('music', 'musical')): level = 3
			else: level = 1
			if 'link' in i and i['link']: menusShow.append({'label' : 'Genre (%s)' % i['name'], 'data' :i['link'], 'level' : level})

		values = Shows().years(menu = False)[:yearsShow]
		counter = 0
		for i in values:
			counter += 1
			if 'link' in i and i['link']: menusShow.append({'label' : 'Year (%s)' % i['name'], 'data' :i['link'], 'level' : 0 if counter <= 2 else 1 if counter <= 10 else 2 if counter <= 15 else 3 if counter <= 20 else 4})

		menus.extend([{'class' : Shows, 'label' : i['label'] if 'label' in i else None, 'data' : i['data'], 'level' : i['level'], 'pages' : pagesShow, 'years' : yearsShow, 'year' : year - yearsShow} for i in menusShow])

		# Episodes

		menusEpisode = [
			{'data' : 'added',	'level' : 3},
		]
		menus.extend([{'class' : Episodes, 'label' : i['label'] if 'label' in i else None, 'data' : i['data'], 'level' : i['level'], 'pages' : pagesShow, 'years' : yearsShow, 'year' : year - yearsShow} for i in menusEpisode])

		# Retrieve

		total = len(menus)
		title = 'Generating Metadata'
		self.tMessage = 'Generating Metadata Database ...'
		self.tPrevious = None
		self.tDetail = detail
		self.tLimit = 50
		self.tEnded = Time.past(days = 30)
		self.tLanguage = Language.CodeEnglish
		self.tDialog = Dialog.progress(title = title, message = self.tMessage, background = False)

		def _batchCanceled():
			return System.aborted() or self.tDialog.iscanceled()

		def _batchInitialize(instance):
			instance.mDetail = self.tDetail
			instance.mLimit = self.tLimit
			instance.mLanguage = self.tLanguage
			return instance

		def _batchProgress(iteration, pages, message = None):
			if _batchCanceled(): return False

			# Show dialog before execution, so that the 0% progress shows right at the start.
			percent = min(99, Math.roundDownClosest((iteration / (total * pages[0])) * 100, base = 1))
			if self.tPrevious is None or percent > self.tPrevious:
				self.tPrevious = percent
				self.tDialog.update(percent, self.tMessage + Format.newline() + ('   Progress: [B]%d%%[/B]' % percent) + ((Format.newline() + message) if message else ''))
				Logger.log('%s: %d%%' % (title, percent))
			return True

		def _batchShow(items, level = 0):
			#return True

			if _batchCanceled(): return False

			if level <= 2 and (items and 'tvshowtitle' in items[0] and not 'season' in items[0]):
				# Improve retrieval duration by multi-threading.
				# Limit to 10 threads to reduce the number of concurrent API calls.
				threads = []
				for item in items:
					try: year = item['year'] or 0
					except: year = 0
					try: votes = item['votes'] or 0
					except: votes = 0

					# Only retrieve season/episode data for newer shows.
					# Only retrieve season/episode data for shows with a minimum vote count.
					if (year and votes >= 20000) or (year >= 1990 and votes >= 2500):
							while len(threads) >= 10:
								Time.sleep(0.2)
								threads = [thread for thread in threads if thread.alive()]
							threads.append(Pool.thread(target = _batchShowRetrieve, args = (item, level), start = True))

				[thread.join() for thread in threads]
			return True

		def _batchShowRetrieve(item, level = 0):
			if _batchCanceled(): return False

			try: idImdb = item['imdb']
			except: idImdb = None
			try: idTvdb = item['tvdb']
			except: idTvdb = None

			try: year = item['year'] or 0
			except: year = 0
			try: votes = item['votes'] or 0
			except: votes = 0

			if idImdb or idTvdb:
				instance = _batchInitialize(Seasons())
				seasons = instance.metadata(idImdb = idImdb, idTvdb = idTvdb)

				#return True

				if level <= 2 and seasons:
					# Do not retrieve seasons for daytime shows that have yearly seasons since the 1970s.
					# Only do this above 20 seasons, since 'Criminal Minds' or 'Its Always Sunny in Philadelphia' have 15+ seasons.
					if len(seasons) < 20:
						# Only retrieve season/episode data for shows with a minimum vote count.
						# Must be greater-equal to the value in _batchShow().
						if (year and votes >= 100000) or (year >= 1990 and votes >= 60000) or (year >= 2000 and votes >= 50000) or (year >= 2010 and votes >= 40000):
							for season in seasons:
								if _batchCanceled(): return False

								# Only include finished seasons.
								# Otherwise a season which didn't have any episodes while generating this database might be used instead of forcing a refresh of the data to get the latests episodes.
								# Seasons do not have a 'status' attribute. Use premiered day instead.
								try: status = season['status'].lower()
								except:
									try: status = item['status'].lower()
									except: status = None
								try: premiered = Time.timestamp(fixedTime = season['premiered'], format = Time.FormatDate)
								except:
									try: premiered = Time.timestamp(fixedTime = season['aired'], format = Time.FormatDate)
									except: premiered = None

								if status in [MetaData.StatusEnded, MetaData.StatusCanceled] or (premiered and premiered <= self.tEnded):
									try: number = season['season']
									except: number = None
									if not number is None:
										instance = _batchInitialize(Episodes())
										instance.metadata(idImdb = idImdb, idTvdb = idTvdb, season = number)
			return True

		# NB: Do this sequentially and not in concurrent threads.
		# Uses less local resources, and reduces server load.
		for i in range(total):
			class_ = menus[i]['class']
			function = menus[i]['data']
			level = menus[i]['level']
			pages = menus[i]['pages']
			label = '   Media: [B]%s[/B] | List: [B]%s[/B]%s   Level: [B]%d[/B] | Pages: [B]%s[/B] of [B]%d[/B]' % (class_.__name__, (menus[i]['label'] if 'label' in menus[i] and menus[i]['label'] else str(menus[i]['data']).capitalize()), Format.newline(), level, '%d', pages[level])

			# Rerun every request multiple times, in case there is imcomplete metadata (eg: due to rate limits).
			page = 0
			iteration = 0
			for j in range(validation):
				if j == 0:
					page = 1
					iteration = i * pages[0]
				if not _batchProgress(iteration = iteration, pages = pages, message = label % page): return False

				try:
					instance = _batchInitialize(class_())

					if Tools.isString(function): items = instance.retrieve(link = function, menu = False)
					else: items = function()

					_batchShow(items = items, level = level)

					for k in range(pages[level] - 1):
						if j == 0:
							page = (k + 2)
							iteration = (i * pages[0]) + k
						if not _batchProgress(iteration = iteration, pages = pages, message = label % page): return False

						try: next = items[-1]['next']
						except: next = None
						if not next: break

						items = instance.retrieve(link = next, menu = False)
						_batchShow(items = items, level = level)
				except: Logger.error()

		Pool.join()

		path = System.temporary(directory = 'metadata', gaia = True, make = True, clear = True)
		path = File.joinPath(path, 'metadata.db')
		File.copy(pathFrom = metacache._mPath, pathTo = path, overwrite = True)

		queries = []
		database = Database(path = path)
		for i in database._tables():
			primary = ''
			extra1 = ''
			extra2 = ''
			extra3 = ''
			if i == MetaCache.TypeMovie:
				primary = 'idImdb, idTmdb'
			elif i == MetaCache.TypeSet:
				primary = 'idTmdb'
			elif i == MetaCache.TypeShow or i == MetaCache.TypeSeason:
				primary = 'idImdb, idTvdb'
			elif i == MetaCache.TypeEpisode:
				extra1 = 'season INTEGER, '
				extra2 = 'season, '
				extra3 = ', season'
				primary = 'idImdb, idTvdb, season'

			# Old SQLite does not have "DROP COLUMN", copy the table instead.
			#queries.append('DELETE FROM `%s` WHERE complete != 1;' % i) # Many specials have incomplete metadata. Keep them. We now copy this value below.
			queries.append('CREATE TABLE `backup_%s` (idImdb TEXT, idTmdb TEXT, idTvdb TEXT, idTrakt TEXT, idTvmaze TEXT, idSlug TEXT, %sdata TEXT, PRIMARY KEY(%s));' % (i, extra1, primary))

			# Create MetaCache and additional indices.
			# All the extra indices cannot hurt, since we only ever do reads from the database and not writes.
			# And it will speed up some SELECT queries.
			# UPDATE: All the extra indices substantially increase the file size. Do not add them, since they  will probably not be used anyway, since there are not SELECT queries for these indices.

			'''queries.append('CREATE INDEX IF NOT EXISTS %s_index_01 ON `backup_%s`(idImdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_02 ON `backup_%s`(idTmdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_03 ON `backup_%s`(idTvdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_04 ON `backup_%s`(idTrakt%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_05 ON `backup_%s`(idTvmaze%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_06 ON `backup_%s`(idSlug%s);' % (i, i, extra3))

			queries.append('CREATE INDEX IF NOT EXISTS %s_index_07 ON `backup_%s`(idImdb, idTmdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_08 ON `backup_%s`(idImdb, idTvdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_09 ON `backup_%s`(idImdb, idTrakt%s);' % (i, i, extra3))

			queries.append('CREATE INDEX IF NOT EXISTS %s_index_10 ON `backup_%s`(idTmdb, idImdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_11 ON `backup_%s`(idTmdb, idTvdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_12 ON `backup_%s`(idTmdb, idTrakt%s);' % (i, i, extra3))

			queries.append('CREATE INDEX IF NOT EXISTS %s_index_13 ON `backup_%s`(idTvdb, idImdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_14 ON `backup_%s`(idTvdb, idTmdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_15 ON `backup_%s`(idTvdb, idTrakt%s);' % (i, i, extra3))

			queries.append('CREATE INDEX IF NOT EXISTS %s_index_16 ON `backup_%s`(idTrakt, idImdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_17 ON `backup_%s`(idTrakt, idTmdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_18 ON `backup_%s`(idTrakt, idTvdb%s);' % (i, i, extra3))

			queries.append('CREATE INDEX IF NOT EXISTS %s_index_19 ON `backup_%s`(idImdb, idTmdb, idTvdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_20 ON `backup_%s`(idImdb, idTmdb, idTrakt%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_21 ON `backup_%s`(idImdb, idTvdb, idTmdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_22 ON `backup_%s`(idImdb, idTvdb, idTrakt%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_23 ON `backup_%s`(idImdb, idTrakt, idTmdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_24 ON `backup_%s`(idImdb, idTrakt, idTvdb%s);' % (i, i, extra3))

			queries.append('CREATE INDEX IF NOT EXISTS %s_index_25 ON `backup_%s`(idTmdb, idImdb, idTvdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_26 ON `backup_%s`(idTmdb, idImdb, idTrakt%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_27 ON `backup_%s`(idTmdb, idTvdb, idImdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_28 ON `backup_%s`(idTmdb, idTvdb, idTrakt%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_29 ON `backup_%s`(idTmdb, idTrakt, idImdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_30 ON `backup_%s`(idTmdb, idTrakt, idTvdb%s);' % (i, i, extra3))

			queries.append('CREATE INDEX IF NOT EXISTS %s_index_31 ON `backup_%s`(idTvdb, idImdb, idTmdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_32 ON `backup_%s`(idTvdb, idImdb, idTrakt%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_33 ON `backup_%s`(idTvdb, idTmdb, idImdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_34 ON `backup_%s`(idTvdb, idTmdb, idTrakt%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_35 ON `backup_%s`(idTvdb, idTrakt, idImdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_36 ON `backup_%s`(idTvdb, idTrakt, idTmdb%s);' % (i, i, extra3))

			queries.append('CREATE INDEX IF NOT EXISTS %s_index_37 ON `backup_%s`(idTrakt, idImdb, idTmdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_38 ON `backup_%s`(idTrakt, idImdb, idTvdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_39 ON `backup_%s`(idTrakt, idTmdb, idImdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_40 ON `backup_%s`(idTrakt, idTmdb, idTvdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_41 ON `backup_%s`(idTrakt, idTvdb, idImdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_42 ON `backup_%s`(idTrakt, idTvdb, idTmdb%s);' % (i, i, extra3))

			queries.append('CREATE INDEX IF NOT EXISTS %s_index_43 ON `backup_%s`(idImdb, idTmdb, idTvdb, idTrakt%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_44 ON `backup_%s`(idImdb, idTvdb, idTrakt, idTmdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_45 ON `backup_%s`(idImdb, idTrakt, idTmdb, idTvdb%s);' % (i, i, extra3))

			queries.append('CREATE INDEX IF NOT EXISTS %s_index_46 ON `backup_%s`(idTmdb, idImdb, idTvdb, idTrakt%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_47 ON `backup_%s`(idTmdb, idTvdb, idTrakt, idImdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_48 ON `backup_%s`(idTmdb, idTrakt, idImdb, idTvdb%s);' % (i, i, extra3))

			queries.append('CREATE INDEX IF NOT EXISTS %s_index_49 ON `backup_%s`(idTvdb, idImdb, idTmdb, idTrakt%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_50 ON `backup_%s`(idTvdb, idTmdb, idTrakt, idImdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_51 ON `backup_%s`(idTvdb, idTrakt, idImdb, idTmdb%s);' % (i, i, extra3))

			queries.append('CREATE INDEX IF NOT EXISTS %s_index_52 ON `backup_%s`(idTrakt, idImdb, idTmdb, idTvdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_53 ON `backup_%s`(idTrakt, idTmdb, idTvdb, idImdb%s);' % (i, i, extra3))
			queries.append('CREATE INDEX IF NOT EXISTS %s_index_54 ON `backup_%s`(idTrakt, idTvdb, idImdb, idTmdb%s);' % (i, i, extra3))

			if extra3:
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_55 ON `backup_%s`(idImdb);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_56 ON `backup_%s`(idTmdb);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_57 ON `backup_%s`(idTvdb);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_58 ON `backup_%s`(idTrakt);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_59 ON `backup_%s`(idTvmaze);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_60 ON `backup_%s`(idSlug);' % (i, i))

				queries.append('CREATE INDEX IF NOT EXISTS %s_index_61 ON `backup_%s`(idImdb, idTmdb);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_62 ON `backup_%s`(idImdb, idTvdb);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_63 ON `backup_%s`(idImdb, idTrakt);' % (i, i))

				queries.append('CREATE INDEX IF NOT EXISTS %s_index_64 ON `backup_%s`(idTmdb, idImdb);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_65 ON `backup_%s`(idTmdb, idTvdb);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_66 ON `backup_%s`(idTmdb, idTrakt);' % (i, i))

				queries.append('CREATE INDEX IF NOT EXISTS %s_index_67 ON `backup_%s`(idTvdb, idImdb);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_68 ON `backup_%s`(idTvdb, idTmdb);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_69 ON `backup_%s`(idTvdb, idTrakt);' % (i, i))

				queries.append('CREATE INDEX IF NOT EXISTS %s_index_70 ON `backup_%s`(idTrakt, idImdb);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_71 ON `backup_%s`(idTrakt, idTmdb);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_72 ON `backup_%s`(idTrakt, idTvdb);' % (i, i))
			'''

			queries.append('INSERT INTO `backup_%s` SELECT idImdb, idTmdb, idTvdb, idTrakt, idTvmaze, idSlug, %sdata FROM `%s`;' % (i, extra2, i))
			queries.append('DROP TABLE `%s`;' % i)
			queries.append('ALTER TABLE `backup_%s` RENAME TO `%s`;' % (i, i))

			if i == MetaCache.TypeMovie:
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idImdb, idTmdb);' % (MetaCache.TypeMovie, MetaCache.TypeMovie))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_2 ON `%s`(idImdb);' % (MetaCache.TypeMovie, MetaCache.TypeMovie))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_3 ON `%s`(idTmdb);' % (MetaCache.TypeMovie, MetaCache.TypeMovie))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_4 ON `%s`(idTrakt);' % (MetaCache.TypeMovie, MetaCache.TypeMovie))
			elif i == MetaCache.TypeSet:
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idTmdb);' % (MetaCache.TypeSet, MetaCache.TypeSet))
			elif i == MetaCache.TypeShow:
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idImdb, idTvdb);' % (MetaCache.TypeShow, MetaCache.TypeShow))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_2 ON `%s`(idImdb);' % (MetaCache.TypeShow, MetaCache.TypeShow))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_3 ON `%s`(idTvdb);' % (MetaCache.TypeShow, MetaCache.TypeShow))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_4 ON `%s`(idTrakt);' % (MetaCache.TypeShow, MetaCache.TypeShow))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_5 ON `%s`(idTvmaze);' % (MetaCache.TypeShow, MetaCache.TypeShow))
			elif i == MetaCache.TypeSeason:
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idImdb, idTvdb);' % (MetaCache.TypeSeason, MetaCache.TypeSeason))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_2 ON `%s`(idImdb);' % (MetaCache.TypeSeason, MetaCache.TypeSeason))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_3 ON `%s`(idTvdb);' % (MetaCache.TypeSeason, MetaCache.TypeSeason))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_4 ON `%s`(idTrakt);' % (MetaCache.TypeSeason, MetaCache.TypeSeason))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_5 ON `%s`(idTvmaze);' % (MetaCache.TypeSeason, MetaCache.TypeSeason))
			elif i == MetaCache.TypeEpisode:
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idImdb, idTvdb, season);' % (MetaCache.TypeEpisode, MetaCache.TypeEpisode))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_2 ON `%s`(idImdb, season);' % (MetaCache.TypeEpisode, MetaCache.TypeEpisode))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_3 ON `%s`(idTvdb, season);' % (MetaCache.TypeEpisode, MetaCache.TypeEpisode))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_4 ON `%s`(idTrakt, season);' % (MetaCache.TypeEpisode, MetaCache.TypeEpisode))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_5 ON `%s`(idTvmaze, season);' % (MetaCache.TypeEpisode, MetaCache.TypeEpisode))

		for query in queries: database._execute(query = query, commit = True, compress = False)
		database._commit()
		database._compress()

		try: self.tDialog.close()
		except: pass
		Logger.log('%s: Done' % title)
		Dialog.confirm(title = title, message = 'Metadata database generated successfully:' + Format.newline() + path)
		return True
