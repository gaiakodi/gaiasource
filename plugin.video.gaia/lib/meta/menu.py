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

from lib.modules.tools import Media, Audience, Tools, Converter, Logger, Settings, Language, Country, Time, Math, System, Regex
from lib.modules.interface import Dialog, Loader, Directory, Translation, Format
from lib.modules.network import Networker
from lib.modules.concurrency import Pool
from lib.modules.shortcut import Shortcut
from lib.modules.cache import Memory

from lib.meta.tools import MetaTools
from lib.meta.manager import MetaManager
from lib.meta.provider import MetaProvider

class MetaMenu(object):

	Action					= 'menu'

	ParameterMedia			= 'media'
	ParameterNiche			= 'niche'
	ParameterImdb			= 'imdb'
	ParameterTmdb			= 'tmdb'
	ParameterTvdb			= 'tvdb'
	ParameterTrakt			= 'trakt'
	ParameterSeason			= 'season'
	ParameterEpisode		= 'episode'
	ParameterAction			= 'action'
	ParameterMenu			= 'menu'
	ParameterContent		= 'content'
	ParameterExplore		= 'explore'
	ParameterCategory		= 'category'
	ParameterSearch			= 'search'
	ParameterProgress		= 'progress'
	ParameterQuery			= 'query'
	ParameterKeyword		= 'keyword'
	ParameterRelease		= 'release'
	ParameterStatus			= 'status'
	ParameterYear			= 'year'
	ParameterDate			= 'date'
	ParameterDuration		= 'duration'
	ParameterGenre			= 'genre'
	ParameterLanguage		= 'language'
	ParameterCountry		= 'country'
	ParameterCertificate	= 'certificate'
	ParameterCompany		= 'company'
	ParameterStudio			= 'studio'
	ParameterNetwork		= 'network'
	ParameterAward			= 'award'
	ParameterRanking		= 'ranking'
	ParameterRating			= 'rating'
	ParameterVotes			= 'votes'
	ParameterFilter			= 'filter'
	ParameterSort			= 'sort'
	ParameterOrder			= 'order'
	ParameterPage			= 'page'
	ParameterLimit			= 'limit'
	ParameterProvider		= 'provider'
	ParameterMore			= 'more'
	ParameterLabel			= 'label'						# Internal
	ParameterImage			= 'image'						# Internal
	ParameterContext		= 'context'						# Internal
	ParameterFolder			= 'folder'						# Internal
	ParameterLoad			= 'load'						# Internal
	ParameterRefresh		= 'refresh'						# Internal
	ParameterContainer		= 'container'					# Internal
	ParameterOrigin			= System.OriginsParameter		# Internal
	ParameterNavigation		= System.NavigationParameter	# Internal

	LoadAutomatic			= None			# Automatically load using the best option below, given the parameters and system state.
	LoadSilent				= 'silent'		# Only run the retrieval, without loading the menu or showing any interactive process (eg dialogs).
	LoadInternal			= 'internal'	# Load the menu directly. Must be called internally with xbmcplugin.addDirectoryItem(..., isFolder=True), or externally using Container.Update(...) or ActivateWindow(...).
	LoadExternal			= 'external'	# Load the menu in another Python process. Useful if the menu was incorrectly called using RunPlugin(...) instead of Container.Update(...), such as poorley written external addons or widgets.
	LoadRefresh				= 'refresh'		# Do not load a new menu, just retrieve the content and then execute Container.Refresh() to reload the content of the current menu.

	MenuFolder				= 'folder'
	MenuMedia				= 'media'
	MenuPerson				= 'person'
	MenuExtra				= 'extra'
	MenuTool				= 'tool'

	ContentSmart			= 'smart'
	ContentQuick			= 'quick'
	ContentFavorite			= 'favorite'
	ContentProgress			= 'progress'
	ContentHistory			= 'history'
	ContentArrival			= 'arrival'
	ContentDiscover			= 'discover'
	ContentExplore			= 'explore'
	ContentRelease			= 'release'
	ContentDate				= 'date'
	ContentGenre			= 'genre'
	ContentLocation			= 'location'
	ContentGeneration		= 'generation'
	ContentRanking			= 'ranking'
	ContentAward			= 'award'
	ContentCompany			= 'company'
	ContentNiche			= 'niche'
	ContentSet				= 'set'
	ContentTopic			= 'topic'
	ContentMood				= 'mood'
	ContentAge				= 'age'
	ContentRegion			= 'region'
	ContentAudience			= 'audience'
	ContentQuality			= 'quality'
	ContentEnterprise		= 'enterprise'
	ContentPleasure			= 'pleasure'
	ContentPerson			= 'person'
	ContentList				= 'list'
	ContentSearch			= 'search'
	ContentRandom			= 'random'
	ContentTrakt			= 'trakt'
	ContentImdb				= 'imdb'
	ContentSeason			= 'season'
	ContentEpisode			= 'episode'
	ContentShortcut			= 'shortcut'

	ProgressAll				= MetaTools.ProgressAll
	ProgressStarted			= MetaTools.ProgressStarted
	ProgressPartial			= MetaTools.ProgressPartial
	ProgressConclude		= MetaTools.ProgressConclude
	ProgressUnfinished		= MetaTools.ProgressUnfinished
	ProgressFinished		= MetaTools.ProgressFinished
	ProgressRewatch			= MetaTools.ProgressRewatch
	ProgressRewatching		= MetaTools.ProgressRewatching
	ProgressRewatched		= MetaTools.ProgressRewatched
	ProgressDefault			= MetaTools.ProgressDefault

	HistoryStream			= MetaTools.HistoryStream
	HistoryMovie			= MetaTools.HistoryMovie
	HistorySet				= MetaTools.HistorySet
	HistoryShow				= MetaTools.HistoryShow
	HistorySeason			= MetaTools.HistorySeason
	HistoryEpisode			= MetaTools.HistoryEpisode

	ReleaseNew				= 'new'
	ReleaseHome				= 'home'
	ReleaseFuture			= 'future'

	DateCentury				= 'century'
	DateDecade				= 'decade'
	DateYear				= 'year'
	DateQuarter				= 'quarter'
	DateMonth				= 'month'
	DateWeek				= 'week'
	DateDay					= 'day'

	RegionCountry			= 'country'
	RegionLanguage			= 'language'

	AudienceAge				= 'age'
	AudienceCertificate		= 'certificate'

	AwardGeneral			= 'general'
	AwardPicture			= 'picture'
	AwardDirector			= 'director'
	AwardActor				= 'actor'
	AwardActress			= 'actress'
	AwardSupportor			= 'supportor'
	AwardSupportress		= 'supportress'
	AwardWinner				= 'winner'
	AwardNominee			= 'nominee'
	AwardLoser				= 'loser'
	AwardAcademy			= 'academy'
	AwardGlobe				= 'globe'
	AwardEmmy				= 'emmy'
	AwardRazzie				= 'razzie'
	AwardNational			= 'national'
	AwardImdb				= 'imdb'

	CompanyStudio			= MetaProvider.CompanyStudio
	CompanyNetwork			= MetaProvider.CompanyNetwork
	CompanyVendor			= MetaProvider.CompanyVendor
	CompanyProducer			= MetaProvider.CompanyProducer
	CompanyBroadcaster		= MetaProvider.CompanyBroadcaster
	CompanyDistributor		= MetaProvider.CompanyDistributor
	CompanyOriginal			= MetaProvider.CompanyOriginal

	PleasureLingual			= 'lingual'
	PleasureSubstance		= 'substance'
	PleasureRelation		= 'relation'
	PleasureIntimacy		= 'intimacy'
	PleasureFelony			= 'felony'
	PleasureSociety			= 'society'

	SearchTitle				= 'title'
	SearchAdvanced			= 'advanced'
	SearchSet				= 'set'
	SearchList				= 'list'
	SearchPerson			= 'person'
	SearchHistory			= 'history'
	SearchOracle			= 'oracle'
	SearchExact				= 'exact'

	RankingRating			= 'rating'
	RankingVoting			= 'voting'
	RankingCustom			= 'custom'
	RankingUpward			= 'upward'
	RankingDownward			= 'downward'
	RankingRange			= 'range'
	RankingCharts			= 'charts'

	SetDiscover				= MetaTools.SetDiscover
	SetAlphabetic			= MetaTools.SetAlphabetic
	SetArrival				= MetaTools.SetArrival
	SetPopular				= MetaTools.SetPopular
	SetRandom				= MetaTools.SetRandom

	ListRecommendation		= MetaTools.ListRecommendation
	ListCalendar			= MetaTools.ListCalendar
	ListWatchlist			= MetaTools.ListWatchlist
	ListFavorite			= MetaTools.ListFavorite
	ListRating				= MetaTools.ListRating
	ListCollection			= MetaTools.ListCollection
	ListHistory				= MetaTools.ListHistory
	ListProgress			= MetaTools.ListProgress
	ListHidden				= MetaTools.ListHidden
	ListCheckin				= MetaTools.ListCheckin
	ListCustom				= MetaTools.ListCustom
	ListPersonal			= MetaTools.ListPersonal
	ListLike				= MetaTools.ListLike
	ListComment				= MetaTools.ListComment
	ListCollaboration		= MetaTools.ListCollaboration
	ListPopular				= MetaTools.ListPopular
	ListTrending			= MetaTools.ListTrending
	ListOfficial			= MetaTools.ListOfficial
	ListDiscover			= MetaTools.ListDiscover
	ListArrival				= MetaTools.ListArrival
	ListQuality				= MetaTools.ListQuality
	ListAward				= MetaTools.ListAward
	ListReal				= MetaTools.ListReal
	ListBucket				= MetaTools.ListBucket
	ListMind				= MetaTools.ListMind

	PersonDiscover			= MetaTools.PersonDiscover
	PersonFamous			= MetaTools.PersonFamous
	PersonAward				= MetaTools.PersonAward
	PersonGender			= MetaTools.PersonGender
	PersonFilmmaker			= MetaTools.PersonFilmmaker
	PersonCreator			= MetaTools.PersonCreator
	PersonDirector			= MetaTools.PersonDirector
	PersonCinematographer	= MetaTools.PersonCinematographer
	PersonWriter			= MetaTools.PersonWriter
	PersonProducer			= MetaTools.PersonProducer
	PersonEditor			= MetaTools.PersonEditor
	PersonComposer			= MetaTools.PersonComposer
	PersonActor				= MetaTools.PersonActor
	PersonActress			= MetaTools.PersonActress

	Instance				= {}

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, media = None, niche = None):
		self.mMedia = media
		self.mNiche = Media.stringFrom(niche)

		self.mTools = MetaTools.instance()

		# We could probably use the singleton here.
		# But maybe use a separate manager for the menu, since there are some parameters that we might not always want to share with other code using the manager (eg: MetaManager.mLocks for concurrent metadata retrieval).
		# Although using the singleton should not be a problem.
		self.mManager = MetaManager()

	@classmethod
	def instance(self, media = None, niche = None):
		if niche: niche = Media.stringFrom(niche)
		id = str(media) + str(niche)
		if not id in MetaMenu.Instance: MetaMenu.Instance[id] = self(media = media, niche = niche)
		return MetaMenu.Instance[id]

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		if settings:
			MetaMenu.Instance = {}

	##############################################################################
	# MEDIA
	##############################################################################

	def _media(self, media = None, mixed = False):
		return media or self.mMedia or (Media.Mixed if mixed else None)

	def _mediaFilm(self):
		return Media.isFilm(self.mMedia)

	def _mediaSerie(self):
		return Media.isSerie(self.mMedia)

	def _mediaMixed(self):
		return not self.mMedia or Media.isMixed(self.mMedia)

	def _niche(self, niche = None, copy = None, add = None):
		if niche is None: niche = self.mNiche

		if not niche: niche = []
		elif copy or add: niche = Tools.copy(niche)

		if add:
			if Tools.isArray(add): niche.extend([i for i in add if not i in niche])
			elif not add in niche: niche.append(add)

		return niche

	##############################################################################
	# PROVIDER
	##############################################################################

	def _provider(self, content = None, media = None, niche = None, **parameters):
		if media is None: media = self._media()
		if niche is None: niche = self._niche()
		return self.mManager.provider(content = content, media = media, niche = niche, **parameters)

	##############################################################################
	# SETTINGS
	##############################################################################

	def _settingsExplore(self):
		return Settings.getInteger('menu.general.explore')

	def _settingsLevel(self, content, media = None):
		level = Settings.getInteger('menu.level.' + content)
		if media: return level == 1 or level == 3
		else: return level == 1 or level == 2

	##############################################################################
	# PARAMETER
	##############################################################################

	def _parameters(self, parameters, none = None, clean = None):
		if clean: parameters = self._parametersClean(parameters = parameters, remove = clean, empty = False, reduce = False)
		basic = {'query' : True, 'label' : True, 'title' : True, 'tvshowtitle' : True, 'name' : True, 'tagline' : True, 'plot' : True, 'overview' : True, 'description' : True}
		return {k : self._parameter(value = v, key = k, basic = k in basic) for k, v in parameters.items()} if parameters else parameters

	def _parameter(self, value, key = None, none = None, basic = None):
		string = Tools.isString(value)
		if string: value = value.strip()
		else: return value

		# Do not do advanced conversion for certain attributes.
		# These attributes can naturally contain characters that are interpreted as a structure below.
		# Eg: "title" and "query" might contain commas, but are not lists.
		# Eg: "label" might start with a "[", but is not a list.
		if basic:
			if none and value == '': return None
			else: return value

		lower = value.lower()

		# URL-quoted
		if lower.startswith('%') or '%2c' in lower or '%3d' in lower:
			data = Networker.linkUnquote(value)
			if data: value = data

		# None
		if none is None: none = False if key == MetaMenu.ParameterGenre else True # Allow the "None" genre and do not interpret it as the Python None.
		if none and (lower == '' or lower == 'null' or lower == 'none'): return None

		# Number
		if Tools.isNumericInteger(value, exact = True): return int(value)
		elif Tools.isNumericFloat(value, exact = True): return float(value)

		# Boolean
		if lower == 'true' or lower == 'false':
			data = Converter.boolean(value = value, default = True)
			if data is False or data is True: return data

		# Dictionary
		if value.startswith('{'):
			data = Converter.jsonFrom(value)
			if data: return {k.lower() : self._parameter(value = v, none = False) for k, v in data.items()}
		elif '=' in value:
			data = Networker.linkDecode(value)
			if data: return {k.lower() : self._parameter(value = v, none = none) for k, v in data.items()}

		# List
		if value.startswith('['):
			data = Converter.jsonFrom(value)
			if data: return [self._parameter(value = v, none = False) for v in data]
		elif ',' in value:
			data = value.split(',')
			if data: return [self._parameter(value = v, none = none) for v in data]

		# Custom
		if key == MetaMenu.ParameterCompany and Tools.isString(value) and '-' in value:
			value = value.split('-')
			return {value[0] : value[1]}

		return value

	@classmethod
	def _parametersClean(self, parameters, remove = None, empty = True, reduce = True):
		if parameters:
			if remove: parameters = {k : v for k, v in parameters.items() if not k in remove}
			if empty: parameters = {k : v for k, v in parameters.items() if v or v is False or v == 0}

			# Make certain parameters "simpler" to make them more readable int he URL (eg: change a JSON list into a command-separated list).
			if reduce:
				for k, v in parameters.items():
					if not k == MetaMenu.ParameterNiche and Tools.isList(v) and not any(Tools.isStructure(i) for i in v): # Eg: rating=[7.5,None]
						parameters[k] = ','.join(['' if i is None else str(i) for i in v])
					elif k == MetaMenu.ParameterCompany and Tools.isDictionary(v) and len(v.values()) == 1: # Eg: company={'netflix':'studio'}
						parameters[k] = '-'.join([next(iter(v.keys())), next(iter(v.values()))])
		return parameters

	##############################################################################
	# COMMAND
	##############################################################################

	@classmethod
	def commandDecode(self, command):
		if '?' in command: return Networker.linkParameters(link = command) # Full URL.
		else: return Networker.linkDecode(command) # Parameters only.

	@classmethod
	def commandEncode(self, parameters, base = None):
		return Networker.linkCreate(link = base, parameters = parameters)

	@classmethod
	def commandIs(self, action = None, content = None, command = None, parameters = None):
		if command:
			# More efficient string matching rather than calling commandDecode().
			if action: return (MetaMenu.ParameterAction + '=' + action) in command
			elif content: return (MetaMenu.ParameterContent + '=' + content) in command
			parameters = self.commandDecode(command = command)
		if parameters:
			if action: return action == parameters.get(MetaMenu.ParameterAction)
			elif content: return content == parameters.get(MetaMenu.ParameterContent)
		return False

	@classmethod
	def commandIsDiscover(self, command = None, parameters = None):
		return self.commandIs(content = MetaMenu.ContentDiscover, command = command, parameters = parameters)

	@classmethod
	def commandIsSearch(self, command = None, parameters = None):
		return self.commandIs(content = MetaMenu.ContentSearch, command = command, parameters = parameters)

	@classmethod
	def commandCreate(self, command = None, parameters = None, clean = True, **kwargs):
		basic = parameters is False
		parameters = Tools.copy(parameters) if parameters else {}

		# This does not work from widgets.
		# But it is fine, since the original query/parameters is passed in from the context menu, called from commandCreateRefresh().
		if not parameters and not basic:
			if not command: command = System.infoLabel('Container.FolderPath')
			parameters = System.commandResolve(command = command)

		if kwargs: parameters.update(kwargs)
		if clean: parameters = self._parametersClean(parameters = parameters)
		return parameters

	@classmethod
	def commandCreateMore(self, media = None, command = None, parameters = None, clean = True):
		return self.commandCreate(command = command, parameters = parameters, clean = clean, **{
			MetaMenu.ParameterAction	: MetaMenu.Action,
			MetaMenu.ParameterMenu		: MetaMenu.MenuPerson if Media.isPerson(media) else MetaMenu.MenuMedia,
		})

	@classmethod
	def commandCreateRefresh(self, container = None, command = None, parameters = None, clean = True):
		return self.commandCreate(command = command, parameters = parameters, clean = clean, **{
			MetaMenu.ParameterRefresh	: True,
			MetaMenu.ParameterLoad		: MetaMenu.LoadRefresh,
			MetaMenu.ParameterContainer	: container,
		})

	@classmethod
	def commandCreateMenu(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, command = None, parameters = False, clean = True): # "parameters=False" to avoid adding the parameters of the current menu.
		return self.commandCreate(command = command, parameters = parameters, clean = clean, **{
			MetaMenu.ParameterAction	: MetaMenu.Action,
			MetaMenu.ParameterMenu		: MetaMenu.MenuMedia,
			MetaMenu.ParameterContent	: MetaMenu.ContentEpisode if Media.isEpisode(media) else MetaMenu.ContentSeason if Media.isSeason(media) else None,
			MetaMenu.ParameterMedia		: media,
			MetaMenu.ParameterImdb		: imdb,
			MetaMenu.ParameterTmdb		: tmdb,
			MetaMenu.ParameterTvdb		: tvdb,
			MetaMenu.ParameterTrakt		: trakt,
			MetaMenu.ParameterSeason	: season,
		})

	@classmethod
	def commandCreateProvider(self, provider = None, command = None, parameters = None, clean = True):
		return self.commandCreate(command = command, parameters = parameters, clean = clean, **{
			MetaMenu.ParameterProvider	: provider,
		})

	##############################################################################
	# EMPTY
	##############################################################################

	def _empty(self, content = None, notification = True, resolve = True, loader = True):
		# NB: This is very important when <reuselanguageinvoker> is enabled.
		# Otherwise if an empty menu is opened and the "Nothing Found" notification is shown, no other menus work afterwards.
		# There is no new Python process being started for any new action/menu afterwards.
		# Kodi probably tries to reuse the previous invoker, but that invoker is somehow stuck, since it thought it would open a menu, but then no menu was loaded.
		# Calling the resolve function fixed this.
		# Eg: Open Movies -> Favorites -> Trakt -> Hidden (make sure there are no hidden items). Then try to open another menu.
		System.pluginResolvedSet(success = False, dummy = True)

		if loader: Loader.hide()
		if notification: self._notificationEmpty(content = content)

	##############################################################################
	# NOTIFICATION
	##############################################################################

	def _notification(self, content, type = None, background = True, delay = False):
		notification = None

		if content == MetaMenu.ContentProgress:
			title = '%s ' + Translation.string(32037)
			if type == MetaMenu.ProgressAll:				notification = {'title' : title % Translation.string(33029), 'message' : 36545}
			elif type == MetaMenu.ProgressStarted:			notification = {'title' : title % Translation.string(33303), 'message' : 36546}
			elif type == MetaMenu.ProgressPartial:			notification = {'title' : title % Translation.string(33165), 'message' : 36547}
			elif type == MetaMenu.ProgressConclude:			notification = {'title' : title % Translation.string(35308), 'message' : 36548}
			elif type == MetaMenu.ProgressUnfinished:		notification = {'title' : title % Translation.string(35612), 'message' : 36549}
			elif type == MetaMenu.ProgressFinished:			notification = {'title' : title % Translation.string(35755), 'message' : 36550}
			elif type == MetaMenu.ProgressRewatch:			notification = {'title' : title % Translation.string(35611), 'message' : 36551}
			elif type == MetaMenu.ProgressRewatching:		notification = {'title' : title % Translation.string(36680), 'message' : 35189}
			elif type == MetaMenu.ProgressRewatched:		notification = {'title' : title % Translation.string(36681), 'message' : 35190}
		elif content == MetaMenu.ContentSearch:
			if type == MetaMenu.SearchExact:				notification = {'title' : '%s %s' % (Translation.string(35157), Translation.string(32010)), 'message' : 35159}
		elif content == MetaMenu.ContentEnterprise:
			more = MetaMenu.CompanyOriginal + MetaMenu.ParameterMore
			if type == MetaMenu.CompanyOriginal:			notification = {'title' : 36600, 'message' : 36631, 'dialog' : 'notification'}
			elif type == more:								notification = {'title' : 36600, 'message' : 36632, 'dialog' : 'notification', 'wait' : False}
		elif content == MetaMenu.ContentSmart:
			if True:										notification = {'title' : 35572, 'message' : 35573, 'more' : self._notificationSmart}
		elif content == Media.Anime:
			# gaiafuture - This can be removed once anime is fully supproted.
			notification = {
				'title'		: 'Anime Support',
				'message'	: 'Anime is now fully supported in the menus, but still needs improvements for scraping, which will be added in future updates.',
				'more'		: self._notificationAnime,
			}

		if notification:
			if background: Pool.thread(target = self._notificationUpdate, kwargs = {'notification' : notification, 'content' : content, 'type' : type, 'delay' : delay}, start = True)
			else: self._notificationUpdate(notification = notification, content = content, type = type, delay = delay)

	def _notificationUpdate(self, notification, content, type = None, delay = False):
		if type is None: type = '' # None keys get converted to a string during JSON-encoding.

		id = 'internal.initial.menu'
		data = Settings.getData(id) or {}
		if not content in data: data[content] = {}
		if not type in data[content]: data[content][type] = {'count' : 0, 'time' : 0}

		time = Time.timestamp()
		dialog = notification.get('dialog', 'confirm')
		more = notification.get('more')
		count = notification.get('count')
		if not count: count = 5 if dialog == 'notification' else 3

		# Only show max once a day.
		if data[content][type]['count'] < count and (time - data[content][type]['time']) > 86400:
			title = notification.get('title', 33102)
			message = notification.get('message')
			close = notification.get('close')
			wait = notification.get('wait')

			if delay: Time.sleep(0.3 if delay is True else delay)
			if dialog == 'notification':
				if close: Dialog.closeNotification()
				Dialog.notification(title = title, message = message, icon = notification.get('icon', Dialog.IconInformation), wait = wait)
			elif dialog == 'text':
				if close: Dialog.closeText()
				Dialog.text(title = title, message = message)
			elif more:
				if close: Dialog.closeOption()
				choice = Dialog.option(title = title, message = message, labelConfirm = 33432, labelDeny = 33821, default = Dialog.ChoiceNo)
				if choice == Dialog.ChoiceYes: Dialog.details(title = title, items = more() if Tools.isFunction(more) else more)
			else:
				if close: Dialog.closeConfirm()
				Dialog.confirm(title = title, message = message)

			data[content][type]['count'] += 1
			data[content][type]['time'] = time
			Settings.setData(id, data)

	def _notificationEmpty(self, media = None, content = None):
		media = self._media(media)

		if content == MetaMenu.ContentSearch: title = 32010
		elif content == MetaMenu.ContentQuick: title = 35550
		elif content == MetaMenu.ContentProgress: title = 32037
		elif content == MetaMenu.ContentArrival: title = 33490
		elif content == MetaMenu.ContentHistory: title = 32036
		elif Media.isFilm(media): title = 32001
		elif Media.isShow(media): title = 32002
		elif Media.isSeason(media): title = 32054
		elif Media.isEpisode(media): title = 32326
		elif Media.isSet(media): title = 33527
		elif Media.isPerson(media): title = 32013
		else: title = 33102

		Dialog.notification(title = title, message = 33049, icon = Dialog.IconInformation)

	def _notificationFuture(self):
		Dialog.confirm(title = 'Future Feature', message = 'This menu requires additional work and will be implemented in a future update.')

	def _notificationSmart(self):
		return [
			{'type' : 'text', 'value' : 'Quick, Progress, and Arrivals are smart menus, which systematically retrieve metadata over longer periods of time.', 'break' : 2},
			{'type' : 'text', 'value' : 'The majority of menus in Gaia are normal page-based menus. This means a single page of 50 titles, for instance, is requested from a provider, detailed metadata is retrieved for each of those titles, and then the menu is displayed. If the next page of the menu is loaded, the process is repeated. This approach is adequate for most menus, but has its limitations. Large lists cannot be loaded in a single go, and filtering and sorting over all pages is not possible.', 'break' : 2},
			{'type' : 'text', 'value' : 'Smart menus, on the other hand, are designed to handle very large lists. This is useful for big Trakt histories and new arrivals, which might at times contain thousands of titles. The detailed metadata for all these titles cannot be retrieved in a single go. All providers have rate limits, but especially Trakt and IMDb heavily restrict the number of requests that can be made per minute. Hence, smart menus will systematically load detailed metadata in smaller chunks over time, in order to avoid hitting these rate limits.', 'break' : 2},
			{'type' : 'text', 'value' : 'Smart menus will therefore become more detailed the longer you use Gaia. Every time you open one of these menus or your Trakt history changes, a little more metadata is retrieved in the background. This allows for better filtering and sorting using advanced metadata attributes, over all titles in the list, not just a single page.', 'break' : 2},
			{'type' : 'text', 'value' : 'Smart menus will also load faster over time as more metadata is cached locally. This is especially important for the Show Progress menu which loads individually episodes from different shows, which requires considerably more metadata and processing than loading a simple menu containing only shows or movies.', 'break' : 2},
		]

	def _notificationAnime(self):
		# gaiafuture - This can be removed once anime is fully supproted.
		return [
			{'type' : 'text', 'value' : 'Anime is now supported, but still has some issues. Metadata and menus fully accommodate anime, but the scraping and playback phases still need some work.', 'break' : 2},
			{'type' : 'text', 'value' : 'Currently the following is supported:', 'break' : 2},
			{'type' : 'list', 'value' : [
				{'value' : 'Season-based episode numbering (S03E017). There might be some inconsistencies between Trakt, TVDb, TMDb, and IMDb. Gaia will map between numbering systems from different providers as far as possible.'},
				{'value' : 'Absolute episode numbering (S01E245). Trakt, TVDb, and TMDb often have differences in their absolute numbering, have missing absolute episode, or do not have absolute orders at all. Gaia therefore creates its own sequential numbering.'},
				{'value' : 'Season-based absolute numbering (S03E341).  Trakt and TMDb sometimes divide a show by seasons, but within each season use absolute episode numbering. Gaia will establish a traditional season-based numbering and map them to the absolute numbers.'},
				{'value' : 'Title translations and aliases, with a focus on Japanese and English titles.'},
				{'value' : 'Global ID and number support across Trakt, TVDb, TMDb, and IMDb. This means that shows are listed as long as they are available from at least one provider. Unlike older versions which filtered out all titles not on IMDb, which is the majority of anime.'},
				{'value' : 'Trakt history syncing, playback scrobbeling, and casting ratings are now supported, even if Trakt uses a different numbering system.'},
			]},
			{'type' : 'text', 'value' : 'The following still needs work:', 'break' : 2},
			{'type' : 'list', 'value' : [
				{'value' : 'Handling of numbering inconsistencies that are currently not accommodated. Please report any issues you find in the menus.'},
				{'value' : 'Adding custom scraping rules for anime. Many anime file names do not use proper naming conventions.'},
				{'value' : 'Adding support for Japanese file names and alphabet, which does not use spaces. Probably also supporting Chinese and Korean.'},
				{'value' : 'Adding anime-specific scrapers to find more streams.'},
			]},
		]

	# This function shows a notification if a lot of metadata has to be retrieved in the foreground.
	# For some menus, this can take a long time when loaded for the first time (20-40 secs or more), and we want to inform the user not to cancel and wait for it to load.
	# The counts might not be perfect, but at least it gives some indication on how long to wait.
	def _notificationJob(self, busy = None):
		setting = Settings.getInteger('menu.general.notification')
		if setting == 0: return

		from lib.meta.cache import MetaCache
		self.mManager.jobReset() # Do this outside the thread.

		def _notificationShow(media, busy):
			try:
				if busy.get('busy') and Loader.visible(): # Only show if loading is still busy.
					job = self.mManager.job()
					if job:
						countNone = job[None]['count']
						countForeground = job[MetaCache.RefreshForeground]['count']
						count = countNone or countForeground

						# Packs can take longer to retrieve and sometimes substantially longer to generate locally.
						if MetaCache.TypePack in job[MetaCache.RefreshForeground]['media']: count += 75

						limits = {
							Media.Unknown : [30, 60, 100],
							Media.Movie : [50, 100, 200],
							Media.Show : [50, 100, 200],
							Media.Season : [20, 50, 100],
							Media.Episode : [20, 50, 100],
						}
						limit = limits.get(media) or limits.get(Media.Unknown)

						if countNone > 10:
							level = 3
							if job[None]['content'] == MetaMenu.ContentArrival: message = 33490
							else: message = Translation.string(33538).lower()
							message = Translation.string(36686) % Translation.string(message)
						elif count > limit[2]:
							level = 3
							message = 36683
						elif count > limit[1]:
							level = 2
							message = 36684
						elif count > limit[0]:
							level = 1
							message = 36685
						else:
							level = 0
							message = None

						if message and level > busy['level']: # Only show 2nd notification if there is a substantial increase.
							if (setting == 1 and level >= 3) or (setting == 2 and level >= 2) or (setting == 3 and level >= 1):
								busy['count'] = count
								busy['level'] = level
								Dialog.notification(title = 33232, message = message, icon = Dialog.IconWarning if level >= 3 else Dialog.IconInformation, wait = False) # Do not wait for a previous notification.
								return True
					return None
			except: Logger.error()
			return False

		def _notificationCheck(media, busy):
			try:
				if not busy: busy = {}
				busy['count'] = 0
				busy['level'] = -1
				Time.sleep(0.3)

				# Wait a little while, since individual metadata retrieval can trigger further internal retrievals.
				# Eg: retrieving episodes might later trigger retrieval of seasons, shows, and packs.
				for i in range(6):
					if not busy.get('busy') or not Loader.visible(): break # Loading is done or cancled.
					if self.mManager.jobBusy(media = media, count = 0, none = True): break
					Time.sleep(0.5)

				if not _notificationShow(media = media, busy = busy) is False:
					# Check if the counter increases for subrequests and show another message.
					for i in range(10):
						if not busy.get('busy') or not Loader.visible(): break # Loading is done or cancled.
						if self.mManager.jobBusy(count = busy.get('count')):
							if _notificationShow(media = media, busy = busy) is False: break
						Time.sleep(0.5)
			except: Logger.error()

		Pool.thread(target = _notificationCheck, kwargs = {'media' : self._media(), 'busy' : busy}, start = True)

	def _notificationAccount(self, provider):
		type = None
		message = None

		if provider == MetaTools.ProviderTrakt:
			from lib.meta.providers.trakt import MetaTrakt
			type = MetaTrakt
			message = 33646
		elif provider == MetaTools.ProviderImdb:
			from lib.meta.providers.imdb import MetaImdb
			type = MetaImdb
			message = 33647

		if type:
			instance = type.instance()
			if not instance.accountValid():
				if Dialog.option(title = 33339, message = message, labelConfirm = 32512, labelDeny = 33743):
					instance.accountAuthenticate()
					if not instance.accountValid(): return False
				else: return False

		return True

	def _notificationContent(self, error, content = None, list = None, **parameters):
		from lib.meta.providers.imdb import MetaImdb
		if error == MetaImdb.Privacy:
			if list == MetaMenu.ListWatchlist: message = 35608
			elif list == MetaMenu.ListRating: message = 35609
			else: message = 36062
			Dialog.confirm(title = 32034, message = message)

	def _notificationCached(self, delay = True):
		try:
			def _notificationCached(delay):
				stats = self.mManager._metadataSmartStats()
				if stats and MetaMenu.ContentProgress in stats:
					if (Time.timestamp() - stats['time']['notification']) > 21600: # 6 hours.
						if delay: Time.sleep(5) # Wait for the intro splash to finish.

						total = 0
						done = 0
						for i in [Media.Movie, Media.Show]:
							data = stats[MetaMenu.ContentProgress].get(i) or {}
							total += data.get('all') or 0
							done += data.get('done') or 0
						progress = int(min(100, (done / float(total)) * 100))

						total = 0
						done = 0
						for i in [Media.Movie, Media.Show]:
							data = stats[MetaMenu.ContentArrival].get(i) or {}
							total += data.get('all') or 0
							done += data.get('done') or 0
						arrivals = int(min(100, (done / float(total)) * 100))

						if progress > 0 or arrivals > 0: # Not on a fresh install during wizard.
							if progress < 95 or arrivals < 95:
								progress = Format.fontBold(str(progress) + '%')
								arrivals = Format.fontBold(str(arrivals) + '%')
								message = '%s: %s %s %s %s %s' % (Translation.string(36722), progress, Translation.string(32037), Format.iconSeparator(), arrivals, Translation.string(33490))
								Dialog.notification(title = 35572, message = message, icon = Dialog.IconInformation)
							self.mManager._metadataSmartStats(notification = True)
			if delay: Pool.thread(target = _notificationCached, kwargs = {'delay' : delay}, start = True)
			else: _notificationCached(delay = delay)
		except: Logger.error()

	##############################################################################
	# CONTENT
	##############################################################################

	# Retrieve metadata items using a menu command, without rendering the menu.
	# Used by library.py.
	def content(self, command = None, **parameters):
		values = {}
		if command: values = self.commandDecode(command = command)
		values.update(parameters)

		parameters = self._parameters(parameters = values, clean = [MetaMenu.ParameterOrigin, MetaMenu.ParameterNavigation, MetaMenu.ParameterAction])
		if not MetaMenu.ParameterMedia in parameters: parameters[MetaMenu.ParameterMedia] = self._media()
		if not MetaMenu.ParameterNiche in parameters: parameters[MetaMenu.ParameterNiche] = self._niche()

		return self.mManager.content(**parameters)

	##############################################################################
	# MENU
	##############################################################################

	def menu(self, menu = None, **parameters):
		items = None
		load = parameters.get(MetaMenu.ParameterLoad)
		container = parameters.get(MetaMenu.ParameterContainer)

		'''
			The menu can be initiated from the endpoint (addon.py) and loaded in one of the following ways:
				1. xbmcplugin.addDirectoryItem(..., isFolder=True): This is the correct way to do it. This is how Gaia creates its internal menus. Kodi probably uses something similar to Container.Update(...) for this.
				2. Container.Update(plugin://plugin.video.gaia/?action=menu&...): This is the next best option. This should be used if menus are loaded outside the directory navigation (eg: load a menu from a command in the context menu, or from an external addon or widget).
				3. ActivateWindow(10025,plugin://plugin.video.gaia/?action=menu&...): This seems similar to option 2, but opens Gaia (or the "video" window) first and then loads the content.
				4. Container.Refresh(): This will refresh the content in the current menu, without creating/loading a new one. This is useful if the menu should be reloaded in-place, like the metadata refresh command from the context menu.
				5. RunPlugin(plugin://plugin.video.gaia/?action=menu&...): This is the incorrect way of calling the endpoint, since it does not tell Kodi that a menu/folder should be loaded, just that an addon script should be executed. Container.Update(...) should be used instead. But in case an external addon or widget does call it this way (System.handle() == -1), Gaia will start a new Python process which then calls Container.Update(...). So even calling it this way still works, although with a slight overhead.
			This is also important if a "folder" is added as an action.
			For instance, a Show or Season menu is added with "folder=False".
			Certain Kodi menu functionality does not work in Kodi 20 anymore if it is added as a folder (eg: show/season progress icon).
			Eg: From MetaTools._items()
		'''
		exception = parameters.get(MetaMenu.ParameterSearch) in [MetaMenu.SearchOracle, MetaMenu.SearchExact] # Add all non-folder actions here.

		if self.menuExternal(menu = menu, **parameters):
			# Important for episode submenus that are executed in a separate process.
			# Otherwise on slow devices the loader might take too long to show up when an episode is clicked that opens the submenu.
			# The user might then think nothing is happening and click again, only slowing down things more.
			Loader.show()

			parameters[MetaMenu.ParameterMenu] = menu
			parameters[MetaMenu.ParameterLoad] = MetaMenu.LoadInternal
			self._menuExecute(**parameters)
		else:
			parameters = self._parameters(parameters = parameters, clean = [MetaMenu.ParameterOrigin, MetaMenu.ParameterNavigation, MetaMenu.ParameterAction, MetaMenu.ParameterMedia, MetaMenu.ParameterNiche])

			if menu == MetaMenu.MenuMedia or menu == MetaMenu.MenuPerson: items = self._menuMedia(**parameters)
			elif menu == MetaMenu.MenuExtra: items = self._menuExtra(**parameters)
			else: items = self._menuFolder(**parameters)

			# The loader shown for the _menuExecute() call above does not automatically hide once the menu is loaded.
			if load == MetaMenu.LoadInternal: Loader.hide()

			if load == MetaMenu.LoadSilent:
				Loader.hide()
			elif not items and (not items is False or parameters.get(MetaMenu.ParameterContent) == MetaMenu.ContentSearch) and not exception:
				# Important if there are no items and reuselanguageinvoker is enabled.
				# Otherwise if an empty menu is opened, not subsequent menu loads anymore.
				# Check False for cancelled search dialog, season extras, or history streams.
				# Update: Also do if search dialog is cancelled.
				notification = False if parameters.get(MetaMenu.ParameterContent) == MetaMenu.ContentSearch and items is False else True # Do not show the notification if the search dialog was canceled.
				self._empty(content = parameters.get(MetaMenu.ParameterContent), notification = notification)
			elif load == MetaMenu.LoadRefresh:
				# Check Context commandRefreshList() for more info.
				Loader.hide()
				Directory.refresh(id = container)

		return items or None

	@classmethod
	def menuExternal(self, menu = None, **parameters):
		load = parameters.get(MetaMenu.ParameterLoad)
		if load == MetaMenu.LoadExternal: return True
		elif load == MetaMenu.LoadAutomatic:
			# When clicking on a show in a widget, it should open the Gaia season/episode menu, unlike movies which immediately start scraping.
			# However, it is almost impossible to distinguish between calls coming in from widgets and calls coming internally from Gaia.
			# InfoLabels are mostly useless for this.
			# For instance, "Container.FolderPath" is empty when a call comes from a widget, while it has a value when it comes from Gaia or other addons.
			# 	if System.handle() < 0 or (not System.infoLabel('Container.FolderPath') and menu == MetaMenu.MenuMedia and parameters.get(MetaMenu.ParameterContent)):
			# However, when CREATING the widget from Kodi's skin settings, the folder path is also empty when using the dialog to select a path within an addon, and can therefore not be used.
			# The best alternative is to check if the call is made when the Kodi Home window is visible.
			# Do not use the InfoLabel "System.CurrentWindow", since sometimes its value is empty. Use Python to check this instead.
			# Also only do this if the content is "season"/"episode".
			# Do not do this if the content is "show", since otherwise the list inside the widget will itself cause a Gaia window to be opened when the widget is loaded during boot.
			seriesWidget = Dialog.windowVisibleHome() and menu == MetaMenu.MenuMedia and parameters.get(MetaMenu.ParameterContent) in [MetaMenu.ContentSeason, MetaMenu.ContentEpisode]

			if System.handle() < 0 or seriesWidget:
				if not parameters.get(MetaMenu.ParameterSearch) in [MetaMenu.SearchOracle, MetaMenu.SearchExact]: # Add all non-folder actions here.
					return True
		return False

	def _menuExecute(self, action = None, **parameters):
		parameters[MetaMenu.ParameterMedia] = self._media()
		parameters[MetaMenu.ParameterNiche] = self._niche()

		# Do not add empty media or niche array.
		for i in [MetaMenu.ParameterMedia, MetaMenu.ParameterNiche]:
			if not parameters.get(i):
				try: del parameters[i]
				except: pass

		# Container.Update(...) only works if there is already a vdeio addon opened and there is a menu/container to update.
		# If the call is initiated externally, especially from a widget, no addon/container is opened, and Container.Update(...) will have no effect.
		# We first have to open the addon and then update the container, which can be done in one go using ActivateWindow(...).
		# Do not optimzie to keep the URL clean and readable, so it can be easily edited for eg widgets.
		if System.originMenu():
			return System.executeContainer(action = action or MetaMenu.Action, parameters = parameters, optimize = False)
		else:
			# NB: Important when a season/episode menu is opened from show widgets.
			# Otherwise Kodi logs: Activate of window '10025' refused because there are active modal dialogs
			Loader.hide()

			# Add 'return', so that navigating back from a window opened by a widget, goes back to the Kodi home menu and not the Gaia main menu.
			return System.executeWindow(action = action or MetaMenu.Action, parameters = parameters, optimize = False, parent = 'return')

	def _menuItem(self, label = None, image = None, media = None, niche = None, menu = None, content = None, category = None, explore = None, context = None, condition = True, default = None, **parameters):
		if not condition: return default() if Tools.isFunction(default) else default

		item = {}
		if parameters: item.update(parameters)

		if label: item[MetaMenu.ParameterLabel] = label
		if image: item[MetaMenu.ParameterImage] = image

		if media: item[MetaMenu.ParameterMedia] = media
		if niche: item[MetaMenu.ParameterNiche] = niche

		if menu: item[MetaMenu.ParameterMenu] = menu
		if content: item[MetaMenu.ParameterContent] = content
		if explore: item[MetaMenu.ParameterExplore] = explore
		if category: item[MetaMenu.ParameterCategory] = category
		if context: item[MetaMenu.ParameterContext] = context

		return item

	'''
		Available Parameters:
			content

			query
			keyword
			release
			status
			year
			date
			duration
			genre
			language
			country
			certificate
			company
			studio
			network
			award
			ranking
			rating
			votes

			page
			limit
			sort
			order

			provider
			direct
			more

			detail
			quick
			refresh
			load
	'''
	def _menuMedia(self, content = None, refresh = None, load = None, **parameters):
		if content == MetaMenu.ContentSearch:
			parameters = self._search(**parameters)
			if parameters.get(MetaMenu.ParameterQuery) is None: return False

		# Do not retrieve full pack data when loading show menus.
		# This requires more and longer API calls to providers, and more local processing to generate the packs.
		# For most of the shows in the menu, the user is not interested in them and it would be a waste to retrieve packs for them.
		# Only if a season/episode is opened underneath a show, or other calls such as scraping or the context menu, will the full pack data be retrieved.
		# That is: only retrieve/generate packs if they will actually be used.
		# More info at MetaManager.metadata().
		# Update: Moved to MetaManager.content() - more info there.
		#if (Media.isShow(self._media()) or self._mediaMixed()) and not content == MetaMenu.ContentProgress:
		#	pack = parameters.get('pack')
		#	if pack is None: parameters['pack'] = False

		busy = {'busy' : True}
		self._notificationJob(busy = busy)

		# Not that important, but allows season/episode menu loads without adding the "media" parameter with the same value.
		if self._media() is None:
			if content == MetaMenu.ContentSeason: self.mMedia = Media.Season
			elif content == MetaMenu.ContentEpisode: self.mMedia = Media.Episode

		data = self.mManager.content(media = self._media(), niche = self._niche(), content = content, refresh = refresh, **parameters)
		items = data.get('items')
		error = data.get('error')
		busy['busy'] = False

		if items and not load == MetaMenu.LoadSilent: self.buildMedia(data = data, content = content)
		elif error: self._notificationContent(error = error, content = content, **parameters)

		return items

	def _menuExtra(self, **parameters):
		self.buildExtra(**parameters)
		return False # Avoid notification, sicne not items are returned.

	def _menuFolder(self, content = None, category = None, explore = None, more = None, load = None, **parameters):
		items = []

		if Media.isAnime(self._niche()) and not content and not category: self._notification(content = Media.Anime)

		if Tools.isString(more):
			if Tools.isNumeric(more): more = int(more)
			else: more = Converter.boolean(more)
		elif more is None: more = True

		date = parameters.get(MetaMenu.ParameterDate)
		genre = parameters.get(MetaMenu.ParameterGenre)
		country = parameters.get(MetaMenu.ParameterCountry)
		language = parameters.get(MetaMenu.ParameterLanguage)
		certificate = parameters.get(MetaMenu.ParameterCertificate)

		# Items
		if content == MetaMenu.ContentProgress: items = self._menuProgress()
		elif content == MetaMenu.ContentFavorite: items = self._menuFavorite()
		elif content == MetaMenu.ContentHistory: items = self._menuHistory(category = category)
		elif content == MetaMenu.ContentTrakt: items = self._menuTrakt(category = category)
		elif content == MetaMenu.ContentImdb: items = self._menuImdb(category = category)

		elif content == MetaMenu.ContentDiscover: items = self._menuDiscover(date = date, genre = genre, language = language, country = country, certificate = certificate)
		elif content == MetaMenu.ContentExplore: items = self._menuExplore(parameters = parameters)
		elif content == MetaMenu.ContentRelease: items, category, explore, more = self._menuRelease(category = category, explore = explore, more = more)
		elif content == MetaMenu.ContentDate: items, category, explore, more = self._menuDate(category = category, explore = explore, more = more)
		elif content == MetaMenu.ContentGenre: items, category, explore, more = self._menuGenre(category = category, genre = genre, explore = explore, more = more)
		elif content == MetaMenu.ContentLocation: items, category, explore, more = self._menuLocation(category = category, country = country, language = language, explore = explore, more = more)
		elif content == MetaMenu.ContentGeneration: items, category, explore, more = self._menuGeneration(category = category, certificate = certificate, explore = explore, more = more)
		elif content == MetaMenu.ContentRanking: items, category, explore, more = self._menuRanking(category = category, explore = explore, more = more)
		elif content == MetaMenu.ContentAward: items, category, explore, more = self._menuAward(category = category, explore = explore, more = more)
		elif content == MetaMenu.ContentCompany: items, category, explore, more = self._menuCompany(category = category, explore = explore, more = more)

		elif content == MetaMenu.ContentSearch: items, more = self._menuSearch(category = category, more = more)

		elif content == MetaMenu.ContentNiche: items = self._menuNiche()
		elif content == MetaMenu.ContentTopic: items = self._menuTopic()
		elif content == MetaMenu.ContentMood: items = self._menuMood()
		elif content == MetaMenu.ContentAge: items = self._menuAge()
		elif content == MetaMenu.ContentRegion: items = self._menuRegion()
		elif content == MetaMenu.ContentAudience: items = self._menuAudience()
		elif content == MetaMenu.ContentQuality: items = self._menuQuality()
		elif content == MetaMenu.ContentEnterprise: items, category, explore, more = self._menuEnterprise(category = category, explore = explore, more = more)
		elif content == MetaMenu.ContentPleasure: items, category, explore, more = self._menuPleasure(category = category, explore = explore, more = more)
		elif content == MetaMenu.ContentSet: items = self._menuSet(category = category)
		elif content == MetaMenu.ContentPerson: items = self._menuPerson(category = category)
		elif content == MetaMenu.ContentList: items = self._menuList(category = category)

		elif content == MetaMenu.ContentShortcut: items = self._menuShortcut(content = content, **parameters)
		else: items = self._menuBase() if self._media() else self._menuMain()

		# Menu
		if items:
			if Tools.isInteger(more): items.append(self._menuItem(label = 33432, image = 'next', content = content, category = category, more = more + 1)) # More item.

			entries = []
			excludeCommon = {MetaMenu.ParameterLabel : True, MetaMenu.ParameterImage : True, MetaMenu.ParameterAction : True, MetaMenu.ParameterFolder : True, MetaMenu.ParameterContext : True}
			excludeInternal = {MetaMenu.ParameterContent : True, MetaMenu.ParameterCategory : True, MetaMenu.ParameterProvider : True, MetaMenu.ParameterNiche : True, MetaMenu.ParameterMedia : True, MetaMenu.ParameterMore : True}
			for item in items:
				if item:
					menu = item.get(MetaMenu.ParameterMenu)
					folder = item.get(MetaMenu.ParameterFolder)
					action = item.get(MetaMenu.ParameterAction)

					parameters = {k : v for k, v in item.items() if not k in excludeCommon}
					base = {k : v for k, v in parameters.items() if not k in excludeInternal}

					context = item.get(MetaMenu.ParameterContext)
					if not context: context = {}
					elif not Tools.isDictionary(context): context = {'provider' : context}

					# Directly load an Explore submenu, or manually select one.
					explored = item.get(MetaMenu.ParameterExplore, explore) # Allow specific submenus to not Explore (eg: Future Releases).
					submenu = None
					if explored and base and not item.get(MetaMenu.ParameterMore):
						submenus = self._menuExplore(parameters = parameters)

						if Tools.isString(explored): # Pick a specific submenu.
							for i in submenus:
								if explored in i[MetaMenu.ParameterNiche]:
									submenu = i
									break
						else: # Use the user settings.
							setting = self._settingsExplore()
							if setting > 0:
								try:
									submenu = submenus[setting - 1]
								except:
									Logger.error()
									setting = 0
							if setting == 0: parameters[MetaMenu.ParameterContent] = MetaMenu.ContentExplore

						if submenu:
							try:
								parameters[MetaMenu.ParameterNiche] = (parameters.get(MetaMenu.ParameterNiche) or []) + submenu[MetaMenu.ParameterNiche]

								subcontext = submenu.get(MetaMenu.ParameterContext)
								if not subcontext: subcontext = {}
								elif not Tools.isDictionary(subcontext): subcontext = {'provider' : subcontext}
								if subcontext: context.update(subcontext)
							except: Logger.error()

					if not menu:
						if content == MetaMenu.ContentExplore or (content == MetaMenu.ContentSearch and not parameters.get(MetaMenu.ParameterCategory)) or (not explored and base) or (explored and submenu):
							menu = MetaMenu.MenuMedia
							if not MetaMenu.ParameterContent in parameters: parameters[MetaMenu.ParameterContent] = MetaMenu.ContentDiscover
						elif content == MetaMenu.ContentSet or content == MetaMenu.ContentList:
							menu = MetaMenu.MenuMedia
							if not MetaMenu.ParameterContent in parameters: parameters[MetaMenu.ParameterContent] = content
						else:
							menu = MetaMenu.MenuFolder
					if not MetaMenu.ParameterMenu in parameters: parameters[MetaMenu.ParameterMenu] = menu

					# For provider-fixed menus that do not have an Explore menu, still add the providers to the context menu.
					# Eg: Discover -> Rankings -> Rating -> Best Rated.
					if not context and not context is None and not content == MetaMenu.ContentSet and not content == MetaMenu.ContentList and not content == MetaMenu.ContentTrakt and not content == MetaMenu.ContentImdb:
						provider = parameters.get(MetaMenu.ParameterProvider)
						if provider: context['provider'] = provider

					entries.append({
						'label'			: item.get(MetaMenu.ParameterLabel),
						'image'			: item.get(MetaMenu.ParameterImage),
						'action'		: action or MetaMenu.Action,
						'folder'		: folder,
						'context'		: context,
						'parameters'	: self._parametersClean(parameters = parameters),
					})

			if not load == MetaMenu.LoadSilent: self.buildFolder(entries)
		return items

	def _menuMain(self):
		provider = self._provider(content = MetaManager.ContentSearch) # Add provider for context menu options.
		menu = [
			#self._menuItem(label = 'XXX',	image = 'oracle',		action = MetaMenu.SearchOracle,		folder = False),#gaiaremove

			self._menuItem(label = 35550,	image = 'quick',	menu = MetaMenu.MenuMedia,	content = MetaMenu.ContentQuick,														condition = self._settingsLevel(content = MetaMenu.ContentQuick)),
			self._menuItem(label = 32037,	image = 'progress',	menu = MetaMenu.MenuMedia,	content = MetaMenu.ContentProgress,	progress = MetaMenu.ProgressDefault,				condition = self._settingsLevel(content = MetaMenu.ContentProgress)),
			self._menuItem(label = 33490,	image = 'arrival',	menu = MetaMenu.MenuMedia,	content = MetaMenu.ContentArrival,														condition = self._settingsLevel(content = MetaMenu.ContentArrival)),
			self._menuItem(label = 32001,	image = 'movies',	media = Media.Movie,																								condition = self._settingsLevel(content = Media.Movie)),
			self._menuItem(label = 32002,	image = 'shows',	media = Media.Show,																									condition = self._settingsLevel(content = Media.Show)),
			self._menuItem(label = 32010,	image = 'search',	menu = MetaMenu.MenuMedia,	content = MetaMenu.ContentSearch,	search = MetaMenu.SearchTitle,	context = provider,	condition = self._settingsLevel(content = MetaMenu.ContentSearch)),
			self._menuItem(label = 32008,	image = 'tools',	menu = MetaMenu.MenuTool,																							condition = self._settingsLevel(content = MetaMenu.MenuTool)),
		]

		shortcut = self._menuShortcut(location = Shortcut.LocationMenu)
		if shortcut: menu.insert(0, shortcut)

		from lib.modules.tools import Promotions
		if Promotions.enabled(): menu.insert(0, self._menuItem(label = 35442, image = 'promotion', action = 'promotionsMenu', folder = True, condition = self._settingsLevel(content = 'promotion')))

		self._notificationCached()

		return menu

	def _menuBase(self):
		niche = self._niche()
		return [
			self._menuShortcut(location = Shortcut.LocationMenu) if not niche else None,
			self._menuItem(label = 35550,	image = 'quick',			content = MetaMenu.ContentQuick,		menu = MetaMenu.MenuMedia,						condition = self._settingsLevel(content = MetaMenu.ContentQuick, media = True)),
			self._menuItem(label = 32037,	image = 'progress',			content = MetaMenu.ContentProgress,		progress = MetaMenu.ProgressDefault,			condition = self._settingsLevel(content = MetaMenu.ContentProgress, media = True)),
			self._menuItem(label = 33490,	image = 'arrival',			content = MetaMenu.ContentArrival,		menu = MetaMenu.MenuMedia,						condition = self._settingsLevel(content = MetaMenu.ContentArrival, media = True)),
			self._menuItem(label = 33000,	image = 'favorite',			content = MetaMenu.ContentFavorite,														condition = self._settingsLevel(content = MetaMenu.ContentFavorite, media = True)),

			self._menuItem(label = 36556,	image = 'genreanime',		niche = Media.Anime,																	condition = not niche and self.mTools.settingsContentAnime(level = MetaTools.ContentFrequent)),
			self._menuItem(label = 36557,	image = 'genredonghua',		niche = Media.Donghua,																	condition = not niche and self.mTools.settingsContentDonghua(level = MetaTools.ContentFrequent)),
			self._menuItem(label = 36555,	image = 'genreanimation',	niche = Media.Anima,																	condition = not niche and self.mTools.settingsContentAnima(level = MetaTools.ContentFrequent)),
			self._menuItem(label = 36558,	image = 'genrefamily',		niche = Media.Family,																	condition = not niche and self.mTools.settingsContentFamily(level = MetaTools.ContentFrequent)),
			self._menuItem(label = 33470,	image = 'genredocumentary',	niche = Media.Docu,																		condition = not niche and self.mTools.settingsContentDocu(level = MetaTools.ContentFrequent)),
			self._menuItem(label = 33471,	image = 'genreshort',		niche = Media.Short,																	condition = not niche and self.mTools.settingsContentShort(level = MetaTools.ContentFrequent)),

			self._menuItem(label = 32031,	image = 'discover',			content = MetaMenu.ContentDiscover),
			self._menuItem(label = 35560,	image = 'niche',			content = MetaMenu.ContentNiche,														condition = not niche),
			self._menuItem(label = 32010,	image = 'search',			content = MetaMenu.ContentSearch,		default = lambda : self._menuSearch()[0][0],	condition = self._settingsLevel(content = MetaMenu.ContentSearch, media = True) and not niche),
		]

	def _menuFavorite(self):
		from lib.modules.library import Library
		niche = self._niche()
		return [
			self._menuShortcut(location = Shortcut.LocationFavorite) if not niche else None,
			self._menuItem(label = 32037,	image = 'progress',		content = MetaMenu.ContentProgress),
			self._menuItem(label = 32036,	image = 'history',		content = MetaMenu.ContentHistory),
			self._menuItem(label = 33675,	image = 'oracle',		content = MetaMenu.ContentSearch,	search = MetaMenu.SearchOracle,		folder = False),
			self._menuItem(label = 32315,	image = 'trakt',		content = MetaMenu.ContentTrakt),
			self._menuItem(label = 32034,	image = 'imdb',			content = MetaMenu.ContentImdb),
			self._menuItem(label = 35170,	image = 'library',		action = 'libraryLocal',			condition = Library.enabled(),		folder = False),
		]

	def _menuShortcut(self, location = None, content = None, base = False, **parameters):
		if Shortcut.enabled():
			def _shortcut(shortcut):
				id = shortcut.get(Shortcut.ParameterId)
				label = shortcut.get(Shortcut.ParameterLabel)
				command = shortcut.get(Shortcut.ParameterCommand)
				folder = shortcut.get(Shortcut.ParameterFolder)

				command = System.commandResolve(command = command, initialize = False)
				command[Shortcut.Parameter] = id
				action = command.get('action')
				try: del command['action']
				except: pass

				if base: # This is currently only used for the Tools menu shortcuts.
					command = System.command( action = action, parameters = command)
					return {'label' : label, 'image' : 'shortcuts', 'command' : command, 'folder' : folder}
				else:
					return self._menuItem(label = label, image = 'shortcuts', action = action, folder = folder, **command)

			values = Shortcut.instance().retrieve(media = self._media(), location = location)
			if values:
				if content: return [_shortcut(shortcut = i) for i in values]
				elif len(values) == 1: return _shortcut(shortcut = values[0])
				else: return self._menuItem(label = 35119, image = 'shortcuts', content = MetaMenu.ContentShortcut, menu = MetaMenu.MenuFolder, location = location, folder = True)
		return None

	def _menuProgress(self):
		try:
			return [
				self._menuItem(label = 33029,					image = 'progressnone',			content = MetaMenu.ContentProgress,	progress = MetaMenu.ProgressAll),
				self._menuItem(label = 33303,					image = 'progressstarted',		content = MetaMenu.ContentProgress,	progress = MetaMenu.ProgressStarted),
				self._menuItem(label = Format.fontBold(33165),	image = 'progresspartial',		content = MetaMenu.ContentProgress,	progress = MetaMenu.ProgressPartial),
				self._menuItem(label = 35612,					image = 'progressconclude',		content = MetaMenu.ContentProgress,	progress = MetaMenu.ProgressConclude),
				self._menuItem(label = 35308,					image = 'progressunfinished',	content = MetaMenu.ContentProgress,	progress = MetaMenu.ProgressUnfinished),
				self._menuItem(label = 35755,					image = 'progressfinished',		content = MetaMenu.ContentProgress,	progress = MetaMenu.ProgressFinished),
				self._menuItem(label = Format.fontBold(35611),	image = 'progressrewatch',		content = MetaMenu.ContentProgress,	progress = MetaMenu.ProgressRewatch),
				self._menuItem(label = 36680,					image = 'progressrewatching',	content = MetaMenu.ContentProgress,	progress = MetaMenu.ProgressRewatching),
				self._menuItem(label = 36681,					image = 'progressrewatched',	content = MetaMenu.ContentProgress,	progress = MetaMenu.ProgressRewatched),
			]
		except: Logger.error()
		return None

	def _menuHistory(self, category = None):
		try:
			if category == MetaMenu.HistoryStream:
				Loader.show()
				from lib.modules.history import History
				media = Media.Episode if self._mediaSerie() else Media.Movie
				items = History().retrieve(media = media, niche = self._niche(), limit = 20 if self._mediaSerie() else 30, stream = True, load = True)
				if items:
					from lib.modules.core import Core
					Core(media = self._media()).showStreams(items = items, filter = False, process = False, metadata = False)
				else:
					self._empty(content = MetaMenu.ContentHistory)
				return False # Avoid notification.
			else:
				items = [self._menuItem(label = 33481,					image = 'historystreams',			content = MetaMenu.ContentHistory,	category = MetaMenu.HistoryStream,	folder = False)]
				if self._mediaMixed() or self._mediaFilm():
					items.extend([
						self._menuItem(label = 32001,					image = 'historymovies',			content = MetaMenu.ContentHistory,	history = MetaMenu.HistoryMovie,	media = Media.Movie),
						self._menuItem(label = 33527,					image = 'historysets',				content = MetaMenu.ContentHistory,	history = MetaMenu.HistorySet,		media = Media.Set),
					])
				elif self._mediaMixed() or self._mediaSerie():
					items.extend([
						self._menuItem(label = 32002,					image = 'historyshows',				content = MetaMenu.ContentHistory,	history = MetaMenu.HistoryShow,		media = Media.Show),
						self._menuItem(label = 32054,					image = 'historyshows',				content = MetaMenu.ContentHistory,	history = MetaMenu.HistorySeason,	media = Media.Season),
						self._menuItem(label = 32326,					image = 'historyshows',				content = MetaMenu.ContentHistory,	history = MetaMenu.HistoryEpisode,	media = Media.Episode),
					])
				return items
		except: Logger.error()
		return None

	def _menuTrakt(self, category = None):
		try:
			if not self._notificationAccount(provider = MetaTools.ProviderTrakt): return False
			if category:
				media = self._media()
				if Media.isSerie(media) and category == MetaMenu.ListCustom:
					return [
						self._menuItem(label = 32040,	image = 'traktlist',		content = MetaMenu.ContentTrakt,	category = Media.Show,				menu = MetaMenu.MenuFolder,		media = Media.Show),
						self._menuItem(label = 33665,	image = 'traktlist',		content = MetaMenu.ContentTrakt,	category = Media.Season,			menu = MetaMenu.MenuFolder,		media = Media.Season),
						self._menuItem(label = 32041,	image = 'traktlist',		content = MetaMenu.ContentTrakt,	category = Media.Episode,			menu = MetaMenu.MenuFolder,		media = Media.Episode),
					]
				else:
					return [
						self._menuItem(label = 36687,	image = 'traktlist',		content = MetaMenu.ContentList,		list = MetaMenu.ListPersonal,		provider = MetaTools.ProviderTrakt),
						self._menuItem(label = 36688,	image = 'traktlist',		content = MetaMenu.ContentList,		list = MetaMenu.ListLike,			provider = MetaTools.ProviderTrakt),
						self._menuItem(label = 36689,	image = 'traktlist',		content = MetaMenu.ContentList,		list = MetaMenu.ListComment,		provider = MetaTools.ProviderTrakt),
						self._menuItem(label = 36690,	image = 'traktlist',		content = MetaMenu.ContentList,		list = MetaMenu.ListCollaboration,	provider = MetaTools.ProviderTrakt),
					]
			else:
				return [
					self._menuItem(label = 35203,	image = 'traktrecommendation',	content = MetaMenu.ContentList,		list = MetaMenu.ListRecommendation,	provider = MetaTools.ProviderTrakt),
					self._menuItem(label = 32027,	image = 'traktcalendar',		content = MetaMenu.ContentList,		list = MetaMenu.ListCalendar,		provider = MetaTools.ProviderTrakt),
					self._menuItem(label = 32033,	image = 'traktwatch',			content = MetaMenu.ContentList,		list = MetaMenu.ListWatchlist,		provider = MetaTools.ProviderTrakt),
					self._menuItem(label = 33000,	image = 'traktfavorite',		content = MetaMenu.ContentList,		list = MetaMenu.ListFavorite,		provider = MetaTools.ProviderTrakt),
					self._menuItem(label = 32032,	image = 'traktcollection',		content = MetaMenu.ContentList,		list = MetaMenu.ListCollection,		provider = MetaTools.ProviderTrakt),
					self._menuItem(label = 35602,	image = 'traktrating',			content = MetaMenu.ContentList,		list = MetaMenu.ListRating,			provider = MetaTools.ProviderTrakt),
					self._menuItem(label = 32036,	image = 'trakthistory',			content = MetaMenu.ContentList,		list = MetaMenu.ListHistory,		provider = MetaTools.ProviderTrakt),
					self._menuItem(label = 32037,	image = 'traktprogress',		content = MetaMenu.ContentList,		list = MetaMenu.ListProgress,		provider = MetaTools.ProviderTrakt),
					self._menuItem(label = 36358,	image = 'trakthidden',			content = MetaMenu.ContentList,		list = MetaMenu.ListHidden,			provider = MetaTools.ProviderTrakt),
					self._menuItem(label = 33002,	image = 'traktlist',			content = MetaMenu.ContentTrakt,	category = MetaMenu.ListCustom,		menu = MetaMenu.MenuFolder),
				]
		except: Logger.error()
		return None

	def _menuImdb(self, category = None):
		try:
			if not self._notificationAccount(provider = MetaTools.ProviderImdb): return False
			return [
				self._menuItem(label = 32033,	image = 'imdbwatch',	content = MetaMenu.ContentList,		list = MetaMenu.ListWatchlist,		provider = MetaTools.ProviderImdb),
				self._menuItem(label = 35602,	image = 'imdbrating',	content = MetaMenu.ContentList,		list = MetaMenu.ListRating,			provider = MetaTools.ProviderImdb),
				self._menuItem(label = 35195,	image = 'imdbcheckin',	content = MetaMenu.ContentList,		list = MetaMenu.ListCheckin,		provider = MetaTools.ProviderImdb),
				self._menuItem(label = 33002,	image = 'imdblist',		content = MetaMenu.ContentList,		list = MetaMenu.ListPersonal,		provider = MetaTools.ProviderImdb),
			]
		except: Logger.error()
		return None

	def _menuDiscover(self, date = None, genre = None, language = None, country = None, certificate = None):
		niche = self._niche()
		region = bool(language) and bool(country)
		if not region:
			region = self.mTools.nicheRegion(niche = niche)
			region = bool(region) and (region.get('language') and region.get('country'))

		age = bool(date) or Media.isAge(niche)
		audience = bool(certificate) or Media.isAudience(niche)
		enterprise = Media.isEnterprise(niche)

		return [
			self._menuItem(label = 33537,	image = 'explore',	content = MetaMenu.ContentExplore),
			self._menuItem(label = 35164,	image = 'arrival',	content = MetaMenu.ContentRelease),
			self._menuItem(label = 35385,	image = 'date',		content = MetaMenu.ContentDate,			condition = not age),
			self._menuItem(label = 32011,	image = 'genre',	content = MetaMenu.ContentGenre), # Allow genres for niches, since IMDb will AND the genres.
			self._menuItem(label = 35129,	image = 'region',	content = MetaMenu.ContentLocation,		condition = not region),
			self._menuItem(label = 35823,	image = 'people',	content = MetaMenu.ContentGeneration,	condition = not audience),
			self._menuItem(label = 35158,	image = 'company',	content = MetaMenu.ContentCompany,		condition = not enterprise),
			self._menuItem(label = 33442,	image = 'quality',	content = MetaMenu.ContentRanking),
			self._menuItem(label = 33302,	image = 'award',	content = MetaMenu.ContentAward),
		]

	def _menuExplore(self, parameters = None):
		media = self._media()
		niche = self._niche()
		release = False
		rating = False
		votes = False
		award = False
		if parameters:
			if MetaMenu.ParameterRelease in parameters or MetaMenu.ParameterDate in parameters: release = True
			if MetaMenu.ParameterRating in parameters: rating = True
			if MetaMenu.ParameterVotes in parameters: votes = True
			if MetaMenu.ParameterAward in parameters: award = True
		if not release and Media.isAge(niche): release = True
		if not rating and Media.isQuality(niche): rating = True
		if not award and Media.isAward(niche): award = True

		# Not available on IMDb.
		air = release and (Media.isSeason(media) or Media.isEpisode(media))

		explore = [
			self._menuItem(label = 36527,	image = 'category',	niche = Media.All),
			self._menuItem(label = 33004,	image = 'arrival',	niche = Media.New,		condition = not release),
			self._menuItem(label = 33571,	image = 'home',		niche = Media.Home,		condition = not release),
			self._menuItem(label = 33733,	image = 'rate',		niche = Media.Best),
			self._menuItem(label = 36528,	image = 'quality',	niche = Media.Prestige,	condition = not rating and not votes),
			self._menuItem(label = 32018,	image = 'voteup',	niche = Media.Popular),
			self._menuItem(label = 36529,	image = 'views',	niche = Media.Viewed,	condition = not votes),
			self._menuItem(label = 33008,	image = 'award',	niche = Media.Award,	condition = not air and not award),
			self._menuItem(label = 33010,	image = 'tickets',	niche = Media.Gross,	condition = not air),
			self._menuItem(label = 33007,	image = 'trendup',	niche = Media.Trend,	condition = not release),
		]

		items = []
		data = {k : v for k, v in parameters.items() if not k in [MetaMenu.ParameterNiche, MetaMenu.ParameterProvider, MetaMenu.ParameterMenu, MetaMenu.ParameterAction]} if parameters else {}
		for item in explore:
			if item:
				item.update(data)
				if not MetaMenu.ParameterContent in item: item[MetaMenu.ParameterContent] = MetaMenu.ContentDiscover
				item[MetaMenu.ParameterNiche] = self._niche(add = item[MetaMenu.ParameterNiche])

				# Do not add directly as 'provider' to the item.
				# Otherwise it will be seen as the (available) providers to USE for the menu data-retrieval, instead of the provider commands to add to the context menu.
				# Also do this per Explore niche type, and pass in the other parameters, so that we get the correct order back.
				# The correct order is not absolutely necessary, but it will list the best provider first in the context menu (eg: Trakt before IMDb for Anime, IMDb before Trakt for movie Networks).
				item[MetaMenu.ParameterContext] = self._provider(content = MetaManager.ContentDiscover, niche = item[MetaMenu.ParameterNiche], **parameters) # Add provider for context menu options.

				items.append(item)

		if not release:
			item = self._menuItem(label = 33104, image = 'random', content = MetaMenu.ContentRandom)
			item.update(data)
			items.append(item)

		return items

	def _menuRelease(self, category = None, country = None, language = None, explore = None, more = None):
		try:
			items = None
			if category and not Tools.isArray(category): category = [category]
			if explore is None: explore = True
			more = False

			# Movie menu.
			if self._mediaFilm():
				items = [
					self._menuItem(label = 33004,	image = 'new',		release = MetaMenu.ReleaseNew),
					self._menuItem(label = 33571,	image = 'home',		release = MetaMenu.ReleaseHome),
					self._menuItem(label = 33410,	image = 'future',	release = MetaMenu.ReleaseFuture,	explore = Media.All),
				]

			# Series media menu.
			elif self._mediaSerie():
				if category is None:
					items = [
						self._menuItem(label = 33004,	image = 'new',		content = MetaMenu.ContentRelease,	category = MetaMenu.ReleaseNew),
						self._menuItem(label = 33410,	image = 'future',	content = MetaMenu.ContentRelease,	category = MetaMenu.ReleaseFuture),
					]
				else:
					future = category[0] == MetaMenu.ReleaseFuture
					items = [
						self._menuItem(label = 36552 if future else 36524,	image = 'quadruple',	release = category[0],	media = Media.Show),
						self._menuItem(label = 36553 if future else 36525,	image = 'double',		release = category[0],	media = Media.Season),
						self._menuItem(label = 36554 if future else 36526,	image = 'single',		release = category[0],	media = Media.Episode),
					]

			return items, category, explore, more
		except: Logger.error()
		return None, None, None, None

	def _menuDate(self, category = None, explore = None, more = None):
		try:
			items = None

			# Main menu.
			if category is None:
				items = [
					self._menuItem(label = 35126,	image = 'datecentury',	content = MetaMenu.ContentDate,	category = MetaMenu.DateCentury),
					self._menuItem(label = 35193,	image = 'datedecade',	content = MetaMenu.ContentDate,	category = MetaMenu.DateDecade),
					self._menuItem(label = 35526,	image = 'dateyear',		content = MetaMenu.ContentDate,	category = MetaMenu.DateYear),
					self._menuItem(label = 35127,	image = 'datequarter',	content = MetaMenu.ContentDate,	category = MetaMenu.DateQuarter),
					self._menuItem(label = 33663,	image = 'datemonth',	content = MetaMenu.ContentDate,	category = MetaMenu.DateMonth),
					self._menuItem(label = 33664,	image = 'dateweek',		content = MetaMenu.ContentDate,	category = MetaMenu.DateWeek),
					self._menuItem(label = 33347,	image = 'dateday',		content = MetaMenu.ContentDate,	category = MetaMenu.DateDay),
				]

			elif category: # Sub menus.
				if explore is None: explore = True
				if more is True: more = 0
				limit = self.mManager.limit(media = self._media())

				# Century menu.
				if MetaMenu.DateCentury in category:
					count = (limit * 100)
					minimum = MetaTools.TimeOldest
					maximum = Time.year()
					start = Math.roundDownClosest(maximum, base = 100) - (count * more)
					end = start - count
					if end < minimum:
						end = Math.roundDownClosest(minimum, base = 100) - 1
						more = False

					items = [self._menuItem(label = str(i) + 's', image = 'datecentury', year = [i, min(i + 99, maximum)]) for i in range(start, end, -100)]

				# Decade menu.
				elif MetaMenu.DateDecade in category:
					count = (limit * 10)
					minimum = MetaTools.TimeOldest
					maximum = Time.year()
					start = Math.roundDownClosest(maximum, base = 10) - (count * more)
					end = start - count
					if end < minimum:
						end = Math.roundDownClosest(minimum, base = 10) - 1
						more = False

					items = [self._menuItem(label = str(i) + 's', image = 'datedecade', year = [i, min(i + 9, maximum)]) for i in range(start, end, -10)]

				# Year menu.
				elif MetaMenu.DateYear in category:
					count = limit
					minimum = MetaTools.TimeOldest
					start = Time.year() - (count * more)
					end = start - count
					if end < minimum:
						end = minimum - 1
						more = False

					items = [self._menuItem(label = str(i), image = 'dateyear', year = i) for i in range(start, end, -1)]

				# Quarter menu.
				elif MetaMenu.DateQuarter in category:
					dates = []
					count = limit
					format = Time.FormatDate
					skip = more * count

					minimum = Time.datetime(str(MetaTools.TimeOldest) + '-01-01', format = format)
					start = Time.datetime(Time.format(format = '%Y-%m-%d'), format = format)
					start = start.replace(day = 1).replace(month = (Math.roundDown(start.month / 3.01) * 3) + 1)

					while len(dates) < count:
						if start is None or start < minimum:
							more = False
							break
						elif skip:
							skip -= 1
						else:
							end = start + Time.delta(days = 85)
							if end is None: break
							for i in [31, 30, 29, 28]:
								try:
									end = end.replace(day = i)
									break
								except: pass
							dates.append([start, end])

						start -= Time.delta(days = 85)
						start = start.replace(day = 1).replace(month = (Math.roundDown(start.month / 3.01) * 3) + 1)

					quarter = Translation.string(35128)
					items = [self._menuItem(label = '%s. %s %s' % ((i[0].month - 1) // 3 + 1, quarter, i[0].strftime('%Y')), image = 'datequarter', date = [j.strftime(format) for j in i]) for i in dates]

				# Month menu.
				elif MetaMenu.DateMonth in category:
					dates = []
					count = limit
					format = Time.FormatDate
					skip = more * count

					minimum = Time.datetime(str(MetaTools.TimeOldest) + '-01-01', format = format)
					start = Time.datetime(Time.format(format = '%Y-%m-01'), format = format)

					while len(dates) < count:
						if start is None or start < minimum:
							more = False
							break
						elif skip:
							skip -= 1
						else:
							next = start.replace(day = 28) + Time.delta(days = 4)
							end = next - Time.delta(days = next.day)
							if end is None: break
							dates.append([start, end])
						start = (start - Time.delta(days = 14)).replace(day = 1)

					items = [self._menuItem(label = i[0].strftime('%b %Y'), image = 'datemonth', date = [j.strftime(format) for j in i]) for i in dates]

				# Week menu.
				elif MetaMenu.DateWeek in category:
					dates = []
					count = limit
					format = Time.FormatDate
					skip = more * count

					minimum = Time.datetime(str(MetaTools.TimeOldest) + '-01-01', format = format)
					start = Time.datetime(Time.format(format = '%Y-%m-%d'), format = format)
					while start.weekday() > 0: start -= Time.delta(days = 1)

					while len(dates) < count:
						if start is None or start < minimum:
							more = False
							break
						elif skip:
							skip -= 1
						else:
							end = start + Time.delta(days = 6) # Not 7 days.
							if end is None: break
							dates.append([start, end])
						start -= Time.delta(days = 7)

					week = Translation.string(33491)
					items = [self._menuItem(label = '%s. %s %s' % (i[0].strftime('%W'), week, i[0].strftime('%Y')), image = 'dateweek', date = [j.strftime(format) for j in i]) for i in dates]

				# Day menu.
				elif MetaMenu.DateDay in category:
					dates = []
					count = limit
					format = Time.FormatDate
					skip = more * count

					minimum = Time.datetime(str(MetaTools.TimeOldest) + '-01-01', format = format)
					start = Time.datetime(Time.format(format = '%Y-%m-%d'), format = format)

					while len(dates) < count:
						if start is None or start < minimum:
							more = False
							break
						elif skip:
							skip -= 1
						else:
							dates.append(start)
						start -= Time.delta(days = 1)

					# Specify a range, otherwise a single date is seen as the upper limit, instead of a single day.
					items = [self._menuItem(label = i.strftime('%d %b %Y'), image = 'dateday', date = [i.strftime(format)] * 2) for i in dates]

			return items, category, explore, more
		except: Logger.error()
		return None, None, None, None

	def _menuGenre(self, category = None, genre = None, explore = None, more = None):
		try:
			if explore is None: explore = True
			if more is True: more = 0

			media = self._media()
			label = 'short' if more == 0 else 'full'

			genres = []
			count = 0
			for k, v in self.mTools.genre().items():
				order = v['support'].get(media)
				if order and self._provider(content = MetaManager.ContentDiscover, genre = k):
					if k == MetaTools.GenreNone and genre: continue # Do not combine the None genre with other genres.
					order = int(order)
					if (more == 0 and order < 1000) or (more == 1 and order >= 1000): genres.append((k, v))
					else: count += 1
			genres = Tools.listSort(genres, key = lambda i : i[1]['label'].get(label).lower())
			genres = Tools.listSort(genres, key = lambda i : i[1]['support'].get(media))

			items = [self._menuItem(label = i[1].get('label').get(label), image = 'genre%s' % i[0], genre = i[0]) for i in genres]
			if more == 1 or not count: more = None
			return items, category, explore, more
		except: Logger.error()
		return None, None, None, None

	def _menuLocation(self, category = None, country = None, language = None, explore = None, more = None):
		try:
			items = None

			# Main menu.
			if category is None:
				region = self.mTools.nicheRegion(niche = self.mNiche)
				country = bool(country) or (region and region.get('country'))
				language = bool(language) or (region and region.get('language'))
				if not language and not country:
					explore = False
					more = False
					items = [
						self._menuItem(label = 35192,	image = 'flag',		content = MetaMenu.ContentLocation,	category = MetaMenu.RegionCountry,	condition = not country),
						self._menuItem(label = 32014,	image = 'language',	content = MetaMenu.ContentLocation,	category = MetaMenu.RegionLanguage,	condition = not language),
					]
				else: # If only one of the menus are supported, directly load it.
					category = MetaMenu.RegionCountry if language else MetaMenu.RegionLanguage

			# Sub menus.
			if category: # if, not elif, since category can be set above.
				if explore is None: explore = True
				if more is True: more = 0

				# Country menu.
				if MetaMenu.RegionCountry in category:
					# Move countries from the user settings to the first page.
					settings = []
					value = Language.settings()
					if value: settings.extend([i[Language.Country] for i in value])
					value = self.mTools.settingsCountry()
					if value: settings.append(value)
					settings = Tools.listUnique(settings)

					# Move long names to the next menu.
					long = Country.countries(universal = False, frequency = Country.FrequencyCommon)
					long = [i for i in long if len(i[Country.Name][Country.NamePrimary]) >= 15]

					country = []
					if more:
						country = Tools.copy(Country.countries(universal = False, frequency = [Country.FrequencyOccasional, Country.FrequencyUncommon]))
						country.extend(long)
						country = [i for i in country if not i[Country.Code][Country.CodePrimary] in settings]
					else:
						country = Tools.copy(Country.countries(universal = False, frequency = [Country.FrequencyCommon]))
						country = [i for i in country if not i in long]
						country.extend([Country.country(i) for i in settings])
					country = Tools.listSort(data = Tools.listUnique(country), key = lambda i : i[Country.Name][Country.NamePrimary])

					if more == 1: more = None
					items = [self._menuItem(label = i[Country.Name][Country.NamePrimary], image = 'flag', country = i[Country.Code][Country.CodePrimary]) for i in country]

				# Language menu.
				if MetaMenu.RegionLanguage in category:
					# Move languages from the user settings to the first page.
					settings = []
					value = Language.settings()
					if value: settings.extend([i[Language.Code][Language.CodePrimary] for i in value])
					value = self.mTools.settingsLanguage()
					if value: settings.append(value)
					settings = Tools.listUnique(settings)

					language = []
					if more:
						language = Tools.copy(Language.languages(universal = False, frequency = [Language.FrequencyUncommon]))
						language = [i for i in language if not i[Language.Code][Language.CodePrimary] in settings]
					else:
						language = Tools.copy(Language.languages(universal = False, frequency = [Language.FrequencyCommon, Language.FrequencyOccasional]))
						language.extend([Language.language(i) for i in settings])
					language = Tools.listSort(data = Tools.listUnique(language), key = lambda i : i[Language.Name][Language.NameEnglish])

					if more == 1: more = None
					items = [self._menuItem(label = i[Language.Name][Language.NameEnglish], image = 'language', language = i[Language.Code][Language.CodePrimary]) for i in language]

			return items, category, explore, more
		except: Logger.error()
		return None, None, None, None

	def _menuGeneration(self, category = None, certificate = None, explore = None, more = None):
		try:
			items = None

			# Main menu.
			if category is None:
				explore = False
				more = False
				certificate = bool(certificate) or Media.isAudience(self.mNiche)
				items = [
					self._menuItem(label = 35824,	image = 'audience',		content = MetaMenu.ContentGeneration,	category = MetaMenu.AudienceAge,			condition = not certificate),
					self._menuItem(label = 32015,	image = 'certificate',	content = MetaMenu.ContentGeneration,	category = MetaMenu.AudienceCertificate,	condition = not certificate),
				]

			# Sub menus.
			elif category:
				if explore is None: explore = True
				more = None

				# Age menu.
				if MetaMenu.AudienceAge in category:
					certificate = [[33433, Audience.AgeAll]]
					if Media.isSerie(self.mMedia):
						certificate.extend([
							[33434, Audience.AgeToddler],
							[33435, Audience.AgeMinor],
						])
					certificate.extend([
						[33436, Audience.AgeChild],
						[36534, Audience.AgeTeen],
						[36535, Audience.AgeYouth],
						[36536, Audience.AgeAdult],
					])
					for i in certificate: i[1] = Audience.certificate(age = i[1], media = self.mMedia, unrated = False, select = Audience.SelectSingle)
					items = [self._menuItem(label = Regex.replace(data = Translation.string(i[0]), expression = '(\d+)', replacement = r'\1+'), image = 'audience', certificate = i[1]) for i in certificate]

				# Certificate menu.
				elif MetaMenu.AudienceCertificate in category:
					certificate = [[36537, Audience.AgeAll]]
					if Media.isSerie(self.mMedia):
						certificate.extend([
							[36538, Audience.AgeToddler],
							[36539, Audience.AgeMinor],
						])
					certificate.extend([
						[36540, Audience.AgeChild],
						[36541, Audience.AgeTeen],
						[36542, Audience.AgeYouth],
						[36543, Audience.AgeAdult],
					])
					for i in certificate: i[1] = Audience.certificate(age = i[1], media = self.mMedia, unrated = False, select = Audience.SelectSingle)
					certificate.append([36544, Audience.CertificateNr])
					items = [self._menuItem(label = '%s (%s)' % (Translation.string(i[0]), Audience.format(i[1])), image = 'certificate', certificate = i[1]) for i in certificate]

			return items, category, explore, more
		except: Logger.error()
		return None, None, None, None

	def _menuRanking(self, category = None, explore = None, more = None):
		try:
			if category and not Tools.isArray(category): category = [category]
			explore = Tools.isArray(category) and len(category) > 1 # The Explore submenus do not make sense here, since most of them use sorting that contradicts the rating/votes sorting.
			more = False

			if category is None:
				items = [
					self._menuItem(label = 35187,	image = 'rate',		content = MetaMenu.ContentRanking,	category = MetaMenu.RankingRating),
					self._menuItem(label = 33443,	image = 'voteup',	content = MetaMenu.ContentRanking,	category = MetaMenu.RankingVoting),
					self._menuItem(label = 33445,	image = 'trendup',	content = MetaMenu.ContentRanking,	category = MetaMenu.RankingCharts),
				]
			else:
				quality = Media.isQuality(self._niche())
				provider = self._provider(content = MetaManager.ContentDiscover, ranking = category)

				if MetaMenu.RankingRating in category:
					if len(category) == 1:
						items = [
							self._menuItem(label = 33733,	image = 'rateup',	ranking = Media.Best,				context = provider),
							self._menuItem(label = 33734,	image = 'ratedown',	ranking = Media.Worst,				context = provider),
							self._menuItem(label = 36609,	image = 'ratenone',	content = MetaMenu.ContentRanking,	category = category + [MetaMenu.RankingCustom],	condition = not quality),
						]
					elif len(category) == 2:
						items = [
							self._menuItem(label = 36610,	image = 'ratenone',	content = MetaMenu.ContentRanking,	category = category + [MetaMenu.RankingUpward]),
							self._menuItem(label = 36611,	image = 'ratenone',	content = MetaMenu.ContentRanking,	category = category + [MetaMenu.RankingDownward]),
							self._menuItem(label = 36612,	image = 'ratenone',	content = MetaMenu.ContentRanking,	category = category + [MetaMenu.RankingRange]),
						]
					else:
						devider = 0
						niche = self._niche()
						if Media.isSerie(niche): devider = 1.5
						elif Media.isShort(niche) or Media.isSpecial(niche): devider = 2.5
						elif Media.isTopic(niche): devider = 2.5

						values = [0, 10, 50, 75, 100, 200, 500, 750, 1000, 2000]
						if devider: values = [int(i / devider) for i in values]

						label = Translation.string(35187)
						if MetaMenu.RankingUpward in category:
							items = [self._menuItem(label = '%0.1f+ %s ' % (i, label), image = 'ratenone', rating = [float(i), None], votes = [values[i], None], ranking = True) for i in range(9, -1, -1)]
						elif MetaMenu.RankingDownward in category:
							items = [self._menuItem(label = '%0.1f- %s ' % (i, label), image = 'ratenone', rating = [None, float(i)], votes = [values[i - 1], None], ranking = True) for i in range(10, 0, -1)]
						elif MetaMenu.RankingRange in category:
							items = [self._menuItem(label = '%0.1f - %0.1f %s ' % (i - 1, i, label), image = 'ratenone', rating = [float(i - 1), float(i)], votes = [values[i - 1], None], ranking = True) for i in range(10, 0, -1)]
				elif MetaMenu.RankingVoting in category:
					if len(category) == 1:
						items = [
							self._menuItem(label = 36617,	image = 'voteup',	ranking = Media.Popular,			context = provider),
							self._menuItem(label = 36618,	image = 'votedown',	ranking = Media.Unpopular,			context = provider),
							self._menuItem(label = 36613,	image = 'votenone',	content = MetaMenu.ContentRanking,	category = category + [MetaMenu.RankingCustom],	condition = not quality),
						]
					elif len(category) == 2:
						items = [
							self._menuItem(label = 36614,	image = 'votenone',	content = MetaMenu.ContentRanking,	category = category + [MetaMenu.RankingUpward]),
							self._menuItem(label = 36615,	image = 'votenone',	content = MetaMenu.ContentRanking,	category = category + [MetaMenu.RankingDownward]),
							self._menuItem(label = 36616,	image = 'votenone',	content = MetaMenu.ContentRanking,	category = category + [MetaMenu.RankingRange]),
						]
					else:
						values = [1000000, 750000, 500000, 250000, 100000, 75000, 50000, 25000, 10000, 7500, 5000, 2500, 1000, 750, 500, 250, 100, 75, 50, 25, 0]
						label = Translation.string(35188)
						if MetaMenu.RankingUpward in category:
							items = [self._menuItem(label = '%s+ %s' % (Math.human(i), label), image = 'votenone', votes = [i, None], ranking = True) for i in values]
						elif MetaMenu.RankingDownward in category:
							items = [self._menuItem(label = '%s- %s' % (Math.human(i), label), image = 'votenone', votes = [None, i], ranking = True) for i in values[:-1]]
						elif MetaMenu.RankingRange in category:
							items = [self._menuItem(label = '%s - %s %s' % (Math.human(values[i]), Math.human(values[i - 1]), label), image = 'votenone', votes = [values[i], values[i - 1]], ranking = True) for i in range(1, len(values))]
				elif MetaMenu.RankingCharts in category:
					items = [
						self._menuItem(label = 33638,	image = 'trendup',		award = MetaTools.AwardTop250,		context = provider),
						self._menuItem(label = 33639,	image = 'trenddown',	award = MetaTools.AwardBottom250,	context = provider),
					]

			return items, category, explore, more
		except: Logger.error()
		return None, None, None, None

	def _menuAward(self, category = None, explore = None, more = None):
		try:
			if category and not Tools.isArray(category): category = [category]
			if explore is None: explore = True
			more = False

			if category is None:
				items = [
					self._menuItem(label = 33324,	image = 'academy',	content = MetaMenu.ContentAward,	category = MetaMenu.AwardAcademy,	condition = self._mediaFilm()),
					self._menuItem(label = 33326,	image = 'emmy',		content = MetaMenu.ContentAward,	category = MetaMenu.AwardEmmy,		condition = self._mediaSerie()),
					self._menuItem(label = 33325,	image = 'globe',	content = MetaMenu.ContentAward,	category = MetaMenu.AwardGlobe),
					self._menuItem(label = 33327,	image = 'razzie',	content = MetaMenu.ContentAward,	category = MetaMenu.AwardRazzie,	condition = self._mediaFilm()),
					self._menuItem(label = 33446,	image = 'national',	award = MetaTools.AwardNationalWinner,									condition = self._mediaFilm()),
					self._menuItem(label = 35873,	image = 'imdb',		content = MetaMenu.ContentAward,	category = MetaMenu.AwardImdb),
				]
			elif MetaMenu.AwardAcademy in category and len(category) == 1:
				items = [
					self._menuItem(label = 33700,	image = 'category',	content = MetaMenu.ContentAward,	category = category + [MetaMenu.AwardGeneral]),
					self._menuItem(label = 33698,	image = 'studio',	content = MetaMenu.ContentAward,	category = category + [MetaMenu.AwardPicture]),
					self._menuItem(label = 33699,	image = 'director',	content = MetaMenu.ContentAward,	category = category + [MetaMenu.AwardDirector]),
				]
			elif MetaMenu.AwardImdb in category:
				items = [
					self._menuItem(label = 33638,	image = 'rateup',	award = MetaTools.AwardTop250),
					self._menuItem(label = 33639,	image = 'ratedown',	award = MetaTools.AwardBottom250),
				]
			else:
				winner = None
				nominee = None
				if MetaMenu.AwardAcademy in category:
					if MetaMenu.AwardGeneral in category:
						winner = MetaTools.AwardAcademyWinner
						nominee = MetaTools.AwardAcademyNominee
					elif MetaMenu.AwardPicture in category:
						winner = MetaTools.AwardPictureWinner
						nominee = MetaTools.AwardPictureNominee
					elif MetaMenu.AwardDirector in category:
						winner = MetaTools.AwardDirectorWinner
						nominee = MetaTools.AwardDirectorNominee
				elif MetaMenu.AwardEmmy in category:
					winner = MetaTools.AwardEmmyWinner
					nominee = MetaTools.AwardEmmyNominee
				elif MetaMenu.AwardGlobe in category:
					winner = MetaTools.AwardGlobeWinner
					nominee = MetaTools.AwardGlobeNominee
				elif MetaMenu.AwardRazzie in category:
					winner = MetaTools.AwardRazzieWinner
					nominee = MetaTools.AwardRazzieNominee
				items = [
					self._menuItem(label = 33885,	image = 'rateup',	award = winner),
					self._menuItem(label = 33886,	image = 'ratedown',	award = nominee),
				]

			return items, category, explore, more
		except: Logger.error()
		return None, None, None, None

	def _menuCompany(self, category = None, explore = None, more = None):
		try:
			if explore is None: explore = True

			if category is None:
				items = [
					self._menuItem(label = 35613,	image = 'studio',		content = MetaMenu.ContentCompany,	category = MetaMenu.CompanyStudio),
					self._menuItem(label = 32016,	image = 'broadcast',	content = MetaMenu.ContentCompany,	category = MetaMenu.CompanyNetwork),
				]
			else:
				if more is True: more = 0
				media = Media.Movie if self._mediaFilm() else Media.Show

				companies = []
				count = 0
				for k, v in MetaTools.company().items():
					v = v.get(category)
					if v:
						order = v.get(media)
						if order:
							order = int(order)
							if (more == 0 and order < 1000) or (more == 1 and order >= 1000): companies.append(Tools.update({'id' : k}, v))
							else: count += 1
				companies = Tools.listSort(companies, key = lambda i : i['label'].lower()) # Lower, otherwise FX is listed before Fox.
				companies = Tools.listSort(companies, key = lambda i : i.get(media))

				items = [self._menuItem(label = i['label'], image = 'company%s' % i['id'], company = {i['id'] : category}) for i in companies]
				if more == 1 or not count: more = None

			return items, category, explore, more
		except: Logger.error()
		return None, None, None, None

	def _menuEnterprise(self, category = None, explore = None, more = None):
		try:
			if category is None:
				items = [
					self._menuItem(label = 36600,	image = 'bulb',			content = MetaMenu.ContentEnterprise,	category = MetaMenu.CompanyOriginal),
					self._menuItem(label = 35458,	image = 'studio',		content = MetaMenu.ContentEnterprise,	category = MetaMenu.CompanyProducer),
					self._menuItem(label = 33050,	image = 'broadcast',	content = MetaMenu.ContentEnterprise,	category = MetaMenu.CompanyBroadcaster),
					self._menuItem(label = 36630,	image = 'distribute',	content = MetaMenu.ContentEnterprise,	category = MetaMenu.CompanyDistributor),
				]
			else:
				if more is True: more = 0

				if category == MetaMenu.CompanyOriginal: self._notification(content = MetaMenu.ContentEnterprise, type = MetaMenu.CompanyOriginal + (MetaMenu.ParameterMore if more else ''))
				media = Media.Movie if Media.isFilm(self._media()) else Media.Show

				companies = []
				count = 0
				for k, v in MetaTools.company().items():
					if category == MetaMenu.CompanyProducer: type = MetaMenu.CompanyStudio
					elif category == MetaMenu.CompanyBroadcaster: type = MetaMenu.CompanyNetwork
					elif category == MetaMenu.CompanyDistributor: type = MetaMenu.CompanyVendor
					else: type = category
					v = v.get(type)
					if v:
						order = v.get(media)
						if order:
							order = int(order)
							if (more == 0 and order < 1000) or (more == 1 and order >= 1000): companies.append(Tools.update({'id' : k}, v))
							else: count += 1
				companies = Tools.listSort(companies, key = lambda i : i['label'].lower()) # Lower, otherwise FX is listed before Fox.

				items = [self._menuItem(label = i['label'], image = 'company%s' % i['id'], niche = self._niche(add = [i['id'], category])) for i in companies]
				if more == 1 or not count: more = None

			return items, category, explore, more
		except: Logger.error()
		return None, None, None, None

	def _menuPleasure(self, category = None, explore = None, more = None):
		try:
			if category is None:
				items = [
					self._menuItem(label = 36635,	image = 'pleasuredrug',			content = MetaMenu.ContentPleasure,	category = MetaMenu.PleasureSubstance),
					self._menuItem(label = 36636,	image = 'pleasurelove',			content = MetaMenu.ContentPleasure,	category = MetaMenu.PleasureRelation),
					self._menuItem(label = 36637,	image = 'pleasuresex',			content = MetaMenu.ContentPleasure,	category = MetaMenu.PleasureIntimacy),
					self._menuItem(label = 36638,	image = 'pleasuremurder',		content = MetaMenu.ContentPleasure,	category = MetaMenu.PleasureFelony),
					self._menuItem(label = 36639,	image = 'pleasurecult',			content = MetaMenu.ContentPleasure,	category = MetaMenu.PleasureSociety),
					self._menuItem(label = 36634,	image = 'pleasureprofanity',	content = MetaMenu.ContentPleasure,	category = MetaMenu.PleasureLingual),
				]
			else:
				pleasures = []
				if category == MetaMenu.PleasureSubstance: pleasures = [Media.Drug, Media.Cannabis, Media.Psychedelic, Media.Cocaine, Media.Alcohol, Media.Pill]
				elif category == MetaMenu.PleasureRelation: pleasures = [Media.Love, Media.Romance, Media.Kiss, Media.Lgbtq, Media.Gay, Media.Lesbian]
				elif category == MetaMenu.PleasureIntimacy: pleasures = [Media.Sex, Media.Nudity, Media.Erotica, Media.Pornography, Media.Prostitution, Media.Orgy]
				elif category == MetaMenu.PleasureFelony: pleasures = [Media.Violence, Media.Robbery, Media.Smuggle, Media.Hostage, Media.Torture, Media.Murder]
				elif category == MetaMenu.PleasureSociety: pleasures = [Media.Religion, Media.Cult, Media.Secret, Media.Terrorism, Media.Psycho, Media.Sadism]
				elif category == MetaMenu.PleasureLingual: pleasures = [Media.Profanity, Media.Blasphemy, Media.Sarcasm, Media.Parody, Media.Satire, Media.Humor]

				items = [self._menuItem(label = self.mTools.pleasure(pleasure = i).get('label'), image = 'pleasure%s' % i, niche = self._niche(add = i)) for i in pleasures]

			return items, category, explore, more
		except: Logger.error()
		return None, None, None, None

	def _menuSet(self, category = None):
		try:
			if category is None:
				context = self._provider(media = Media.Set, content = MetaManager.ContentSearch)
				return [
					self._menuItem(label = 33537,	image = 'explore',			content = MetaMenu.ContentSet,		media = Media.Set,			set = MetaMenu.SetDiscover),
					self._menuItem(label = 32031,	image = 'discover',			content = MetaMenu.ContentSet,		media = Media.Set,			category = MetaMenu.ContentDiscover,	menu = MetaMenu.MenuFolder),
					self._menuItem(label = 32010,	image = 'search',			content = MetaMenu.ContentSearch,	menu = MetaMenu.MenuMedia,	search = MetaMenu.SearchSet,			context = context),
				]
			elif category == MetaMenu.SetAlphabetic:
				return [
					self._menuItem(label = 35149 if i == '_' else i, image = 'alphabet', content = MetaMenu.ContentSet, media = Media.Set, set = i)
				for i in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_']
			else:
				return [
					self._menuItem(label = 35392,	image = 'voteup',			content = MetaMenu.ContentSet,		set = MetaMenu.SetPopular),
					self._menuItem(label = 35375,	image = 'random',			content = MetaMenu.ContentSet,		set = MetaMenu.SetRandom),
					self._menuItem(label = 33490,	image = 'arrival',			content = MetaMenu.ContentSet,		set = MetaMenu.SetArrival),
					self._menuItem(label = 33565,	image = 'alphabet',			content = MetaMenu.ContentSet,		media = Media.Set,		category = MetaMenu.SetAlphabetic,	menu = MetaMenu.MenuFolder),
				]
		except: Logger.error()
		return None

	def _menuPerson(self, category = None):
		try:
			if category and not Tools.isArray(category): category = [category]
			if category is None:
				context = self._provider(media = Media.Person)
				return [
					self._menuItem(label = 33537,	image = 'explore',			content = MetaMenu.ContentPerson,	person = MetaMenu.PersonDiscover,												context = context),
					self._menuItem(label = 32031,	image = 'discover',			content = MetaMenu.ContentPerson,	menu = MetaMenu.MenuFolder,				category = MetaMenu.ContentDiscover),
					self._menuItem(label = 32010,	image = 'search',			content = MetaMenu.ContentSearch,	menu = MetaMenu.MenuMedia,				search = MetaMenu.SearchPerson,			context = context),
				]
			elif MetaMenu.PersonFamous in category:
				serie = self._mediaSerie()
				return [
					self._menuItem(label = 35339,	image = 'studio',			content = MetaMenu.ContentPerson,	person = MetaMenu.PersonFilmmaker,		condition = not serie),
					self._menuItem(label = 35376,	image = 'studio',			content = MetaMenu.ContentPerson,	person = MetaMenu.PersonCreator,		condition = serie),
					self._menuItem(label = 35340,	image = 'director',			content = MetaMenu.ContentPerson,	person = MetaMenu.PersonDirector),
					self._menuItem(label = 35457,	image = 'camera',			content = MetaMenu.ContentPerson,	person = MetaMenu.PersonCinematographer),
					self._menuItem(label = 35341,	image = 'writer',			content = MetaMenu.ContentPerson,	person = MetaMenu.PersonWriter),
					self._menuItem(label = 35458,	image = 'producer',			content = MetaMenu.ContentPerson,	person = MetaMenu.PersonProducer),
					self._menuItem(label = 35459,	image = 'editor',			content = MetaMenu.ContentPerson,	person = MetaMenu.PersonEditor,			condition = not serie),
					self._menuItem(label = 35512,	image = 'genremusical',		content = MetaMenu.ContentPerson,	person = MetaMenu.PersonComposer),
					self._menuItem(label = 35342,	image = 'gendermale',		content = MetaMenu.ContentPerson,	person = MetaMenu.PersonActor),
					self._menuItem(label = 35343,	image = 'genderfemale',		content = MetaMenu.ContentPerson,	person = MetaMenu.PersonActress),
				]
			elif MetaMenu.PersonAward in category:
				if len(category) == 1:
					return [
						self._menuItem(label = 33324,	image = 'academy',		content = MetaMenu.ContentPerson,	category = category + [MetaMenu.AwardAcademy]),
						self._menuItem(label = 33326,	image = 'emmy',			content = MetaMenu.ContentPerson,	category = category + [MetaMenu.AwardEmmy]),
						self._menuItem(label = 33325,	image = 'globe',		content = MetaMenu.ContentPerson,	category = category + [MetaMenu.AwardGlobe]),
					]
				elif MetaMenu.AwardAcademy in category and len(category) == 2:
					return [
						self._menuItem(label = 33700,	image = 'category',		content = MetaMenu.ContentPerson,	category = category + [MetaMenu.AwardGeneral]),
						self._menuItem(label = 33699,	image = 'director',		content = MetaMenu.ContentPerson,	category = category + [MetaMenu.AwardDirector]),
						self._menuItem(label = 35561,	image = 'gendermale',	content = MetaMenu.ContentPerson,	category = category + [MetaMenu.AwardActor]),
						self._menuItem(label = 35562,	image = 'genderfemale',	content = MetaMenu.ContentPerson,	category = category + [MetaMenu.AwardActress]),
						self._menuItem(label = 35563,	image = 'gendermale',	content = MetaMenu.ContentPerson,	category = category + [MetaMenu.AwardSupportor]),
						self._menuItem(label = 35564,	image = 'genderfemale',	content = MetaMenu.ContentPerson,	category = category + [MetaMenu.AwardSupportress]),
					]
				else:
					winner = None
					nominee = None
					if MetaMenu.AwardAcademy in category:
						if MetaMenu.AwardGeneral in category:
							winner = MetaTools.AwardAcademyWinner
							nominee = MetaTools.AwardAcademyNominee
						elif MetaMenu.AwardDirector in category:
							winner = MetaTools.AwardDirectorWinner
							nominee = MetaTools.AwardDirectorNominee
						elif MetaMenu.AwardActor in category:
							winner = MetaTools.AwardActorWinner
							nominee = MetaTools.AwardActorNominee
						elif MetaMenu.AwardActress in category:
							winner = MetaTools.AwardActressWinner
							nominee = MetaTools.AwardActressNominee
						elif MetaMenu.AwardSupportor in category:
							winner = MetaTools.AwardSupportorWinner
							nominee = MetaTools.AwardSupportorNominee
						elif MetaMenu.AwardSupportress in category:
							winner = MetaTools.AwardSupportressWinner
							nominee = MetaTools.AwardSupportressNominee
					elif MetaMenu.AwardEmmy in category:
						winner = MetaTools.AwardEmmyWinner
						nominee = MetaTools.AwardEmmyNominee
					elif MetaMenu.AwardGlobe in category:
						winner = MetaTools.AwardGlobeWinner
						nominee = MetaTools.AwardGlobeNominee
					return [
						self._menuItem(label = 33885,	image = 'rateup',		content = MetaMenu.ContentPerson,	person = MetaMenu.PersonDiscover,	award = winner),
						self._menuItem(label = 33886,	image = 'ratedown',		content = MetaMenu.ContentPerson,	person = MetaMenu.PersonDiscover,	award = nominee),
					]
			elif MetaMenu.PersonGender in category:
				return [
					self._menuItem(label = 35270,	image = 'gendermale',		content = MetaMenu.ContentPerson,	person = MetaMenu.PersonDiscover,	gender = MetaTools.GenderMale),
					self._menuItem(label = 35271,	image = 'genderfemale'	,	content = MetaMenu.ContentPerson,	person = MetaMenu.PersonDiscover,	gender = MetaTools.GenderFemale),
					self._menuItem(label = 35272,	image = 'gendernonbinary',	content = MetaMenu.ContentPerson,	person = MetaMenu.PersonDiscover,	gender = MetaTools.GenderNonbinary),
					self._menuItem(label = 35149,	image = 'genderother',		content = MetaMenu.ContentPerson,	person = MetaMenu.PersonDiscover,	gender = MetaTools.GenderOther),
				]
			elif MetaMenu.ContentDiscover in category:
				return [
					self._menuItem(label = 35315,	image = 'famous',			content = MetaMenu.ContentPerson,	menu = MetaMenu.MenuFolder,			category = MetaMenu.PersonFamous),
					self._menuItem(label = 33302,	image = 'award',			content = MetaMenu.ContentPerson,	menu = MetaMenu.MenuFolder,			category = MetaMenu.PersonAward),
					self._menuItem(label = 35306,	image = 'gender',			content = MetaMenu.ContentPerson,	menu = MetaMenu.MenuFolder,			category = MetaMenu.PersonGender),
				]
		except: Logger.error()
		return None

	def _menuList(self, category = None):
		try:
			if category:
				return [
					self._menuItem(label = 36691,	image = 'voteup',			content = MetaMenu.ContentList,		list = MetaMenu.ListPopular),
					self._menuItem(label = 36692,	image = 'trendup',			content = MetaMenu.ContentList,		list = MetaMenu.ListTrending),
					self._menuItem(label = 36695,	image = 'arrival',			content = MetaMenu.ContentList,		list = MetaMenu.ListArrival),
					self._menuItem(label = 36528,	image = 'quality',			content = MetaMenu.ContentList,		list = MetaMenu.ListQuality),
					self._menuItem(label = 33008,	image = 'award',			content = MetaMenu.ContentList,		list = MetaMenu.ListAward),
					self._menuItem(label = 36694,	image = 'genrebiography',	content = MetaMenu.ContentList,		list = MetaMenu.ListReal),
					self._menuItem(label = 35245,	image = 'genreromance',		content = MetaMenu.ContentList,		list = MetaMenu.ListBucket),
					self._menuItem(label = 35191,	image = 'genre',			content = MetaMenu.ContentList,		list = MetaMenu.ListMind),
					self._menuItem(label = 36693,	image = 'sets',				content = MetaMenu.ContentList,		list = MetaMenu.ListOfficial,		condition = not self._mediaSerie()),
				]
			else:
				context = self._provider(media = Media.List, content = MetaManager.ContentSearch)
				return [
					self._menuItem(label = 33537,	image = 'explore',			content = MetaMenu.ContentList,		list = MetaMenu.ListDiscover), # Trakt popular lists. Same as doing a list search without a query parameter.
					self._menuItem(label = 32031,	image = 'discover',			content = MetaMenu.ContentList,		menu = MetaMenu.MenuFolder,			category = MetaMenu.ContentDiscover),
					self._menuItem(label = 32315,	image = 'trakt',			content = MetaMenu.ContentTrakt,	menu = MetaMenu.MenuFolder),
					self._menuItem(label = 32034,	image = 'imdb',				content = MetaMenu.ContentImdb,		menu = MetaMenu.MenuFolder),
					self._menuItem(label = 32010,	image = 'search',			content = MetaMenu.ContentSearch,	menu = MetaMenu.MenuMedia,			search = MetaMenu.SearchList,	context = context),
				]
		except: Logger.error()
		return None

	def _menuSearch(self, category = None, more = None):
		try:
			items = []

			if category == MetaMenu.SearchHistory:
				from lib.modules.search import Search

				limit = self.mManager.limit(media = self._media(), content = MetaManager.ContentSearch)
				if more is True: more = 0

				history = Search.instance().retrieve(media = self._media(), niche = self._niche(), limit = limit, page = more + 1)

				if history:
					for i in history:
						search = i.get('type')
						query = i.get('query')
						item = self._menuItem(
							label = i.get('label'),
							image = 'search%s' % i.get('type') or '',
							niche = self._niche(niche = i.get('niche')),
							content = MetaMenu.ContentSearch,
							search = search,
							folder = search in [MetaMenu.SearchTitle, MetaMenu.SearchAdvanced],
						)
						if query: item.update(query)
						items.append(item)

				if not history or len(history) < limit: more = False
			else:
				provider = self._provider(content = MetaManager.ContentSearch) # Add provider for context menu options.
				if self._mediaMixed() or self._niche():
					items = [
						self._menuItem(label = 32010,	image = 'search',			content = MetaMenu.ContentSearch,	search = MetaMenu.SearchTitle,		context = provider),
					]
				else:
					providerSet = self._provider(media = Media.Set, content = MetaManager.ContentSearch)
					providerList = self._provider(media = Media.List, content = MetaManager.ContentSearch)
					providerPerson = self._provider(media = Media.Person, content = MetaManager.ContentSearch)
					items = [
						self._menuItem(label = 33039,	image = 'searchtitle',		content = MetaMenu.ContentSearch,	search = MetaMenu.SearchTitle,		context = provider),
						self._menuItem(label = 35534,	image = 'searchset',		content = MetaMenu.ContentSearch,	search = MetaMenu.SearchSet,		context = providerSet,		condition = self._mediaFilm()),
						self._menuItem(label = 33297,	image = 'searchlist',		content = MetaMenu.ContentSearch,	search = MetaMenu.SearchList,		context = providerList),
						self._menuItem(label = 32013,	image = 'searchperson',		content = MetaMenu.ContentSearch,	search = MetaMenu.SearchPerson,		context = providerPerson),
						self._menuItem(label = 33894,	image = 'searchadvanced',	content = MetaMenu.ContentSearch,	search = MetaMenu.SearchAdvanced),
						self._menuItem(label = 33675,	image = 'searchoracle',		content = MetaMenu.ContentSearch,	search = MetaMenu.SearchOracle,		folder = False),
						self._menuItem(label = 35157,	image = 'searchexact',		content = MetaMenu.ContentSearch,	search = MetaMenu.SearchExact,		folder = False),
						self._menuItem(label = 32036,	image = 'searchhistory',	content = MetaMenu.ContentSearch,	category = MetaMenu.SearchHistory),
					]

			return items, more
		except: Logger.error()
		return None, None

	def _menuNiche(self):
		media = self._media()
		movie = Media.isFilm(media)
		show = Media.isSerie(media)
		return [
			self._menuItem(label = 33527,	image = 'sets',				content = MetaMenu.ContentSet,					condition = movie),
			self._menuItem(label = 35369,	image = 'genremini',		niche = self._niche(add = Media.Mini),			condition = show),
			self._menuItem(label = 33471,	image = 'genreshort',		niche = self._niche(add = Media.Short)),
			self._menuItem(label = 35637,	image = 'genreholiday',		niche = self._niche(add = Media.Special),		media = Media.Movie), # Allow TV Specials for shows as well, since many shows have a movie or holiday specials. Just redirect to movies.
			self._menuItem(label = 35368,	image = 'genretelevision',	niche = self._niche(add = Media.Television),	condition = movie),
			self._menuItem(label = 35610,	image = 'topic',			content = MetaMenu.ContentTopic),
			self._menuItem(label = 36563,	image = 'mood',				content = MetaMenu.ContentMood),
			self._menuItem(label = 35824,	image = 'date',				content = MetaMenu.ContentAge),
			self._menuItem(label = 36606,	image = 'quality',			content = MetaMenu.ContentQuality),
			self._menuItem(label = 35129,	image = 'region',			content = MetaMenu.ContentRegion),
			self._menuItem(label = 35823,	image = 'audience',			content = MetaMenu.ContentAudience),
			self._menuItem(label = 35158,	image = 'company',			content = MetaMenu.ContentEnterprise),
			self._menuItem(label = 36633,	image = 'pleasure',			content = MetaMenu.ContentPleasure),
			self._menuItem(label = 32013,	image = 'people',			content = MetaMenu.ContentPerson),
			self._menuItem(label = 33002,	image = 'lists',			content = MetaMenu.ContentList),
		]

	def _menuTopic(self):
		try:
			items = [
				self._menuItem(label = 36555,	image = 'genreanimation',	niche = self._niche(add = Media.Anima)),
				self._menuItem(label = 36556,	image = 'genreanime',		niche = self._niche(add = Media.Anime)),
				self._menuItem(label = 36557,	image = 'genredonghua',		niche = self._niche(add = Media.Donghua)),
				self._menuItem(label = 35497,	image = 'genredocumentary',	niche = self._niche(add = Media.Docu)),
				self._menuItem(label = 36558,	image = 'genrefamily',		niche = self._niche(add = Media.Family)),
				self._menuItem(label = 36559,	image = 'genremusic',		niche = self._niche(add = Media.Music)),
				self._menuItem(label = 36560,	image = 'genresport',		niche = self._niche(add = Media.Sport)),
				self._menuItem(label = 36561,	image = 'genretelevision',	niche = self._niche(add = Media.Telly)),
				self._menuItem(label = 36562,	image = 'genresoap',		niche = self._niche(add = Media.Soap)),
			]

			# Do not show eg Soap for movies.
			items = [i for i in items if i and any(self._provider(content = MetaManager.ContentDiscover, niche = False, genre = j) for j in self.mTools.nicheTopic(niche = i[MetaMenu.ParameterNiche]))]

			return items
		except: Logger.error()
		return None

	def _menuMood(self):
		try:
			return [
				self._menuItem(label = 36564,	image = 'moodloved',		niche = self._niche(add = Media.Loved)),
				self._menuItem(label = 36565,	image = 'moodrelaxed',		niche = self._niche(add = Media.Relaxed)),
				self._menuItem(label = 36566,	image = 'moodcheerful',		niche = self._niche(add = Media.Cheerful)),
				self._menuItem(label = 36567,	image = 'moodimaginary',	niche = self._niche(add = Media.Imaginary)),
				self._menuItem(label = 36568,	image = 'moodsuspicious',	niche = self._niche(add = Media.Suspicious)),
				self._menuItem(label = 36569,	image = 'moodadventurous',	niche = self._niche(add = Media.Adventurous)),
				self._menuItem(label = 36570,	image = 'moodaggressive',	niche = self._niche(add = Media.Aggressive)),
				self._menuItem(label = 36571,	image = 'moodfrightened',	niche = self._niche(add = Media.Frightened)),
				self._menuItem(label = 36572,	image = 'moodcurious',		niche = self._niche(add = Media.Curious)),
				self._menuItem(label = 36573,	image = 'moodenergetic',	niche = self._niche(add = Media.Energetic)),
				self._menuItem(label = 36574,	image = 'moodindifferent',	niche = self._niche(add = Media.Indifferent)),
				self._menuItem(label = 36575,	image = 'moodexperimental',	niche = self._niche(add = Media.Experimental)),
			]
		except: Logger.error()
		return None

	def _menuAge(self):
		try:
			return [
				self._menuItem(label = 36601,	image = 'datenone',		niche = self._niche(add = Media.Future)),
				self._menuItem(label = 33038,	image = 'dateday',		niche = self._niche(add = Media.Recent)),
				self._menuItem(label = 36602,	image = 'datemonth',	niche = self._niche(add = Media.Modern)),
				self._menuItem(label = 36603,	image = 'dateyear',		niche = self._niche(add = Media.Mature)),
				self._menuItem(label = 36604,	image = 'datedecade',	niche = self._niche(add = Media.Vintage)),
				self._menuItem(label = 36605,	image = 'datecentury',	niche = self._niche(add = Media.Ancient)),
			]
		except: Logger.error()
		return None

	def _menuRegion(self):
		try:
			return [
				self._menuItem(label = 32314,	image = 'regionlocal',		niche = self._niche(add = Media.Local)),
				self._menuItem(label = 36576,	image = 'regionamerican',	niche = self._niche(add = Media.American)),
				self._menuItem(label = 36577,	image = 'regionbritish',	niche = self._niche(add = Media.British)),
				self._menuItem(label = 36578,	image = 'regionfrench',		niche = self._niche(add = Media.French)),
				self._menuItem(label = 36580,	image = 'regionspanish',	niche = self._niche(add = Media.Spanish)),
				self._menuItem(label = 36581,	image = 'regionportuguese',	niche = self._niche(add = Media.Portuguese)),
				self._menuItem(label = 36582,	image = 'regionitalian',	niche = self._niche(add = Media.Italian)),
				self._menuItem(label = 36579,	image = 'regiongermanic',	niche = self._niche(add = Media.Germanic)),
				self._menuItem(label = 36583,	image = 'regionbenelux',	niche = self._niche(add = Media.Benelux)),
				self._menuItem(label = 36584,	image = 'regionnordic',		niche = self._niche(add = Media.Nordic)),
				self._menuItem(label = 36587,	image = 'regionbaltic',		niche = self._niche(add = Media.Baltic)),
				self._menuItem(label = 36585,	image = 'regionslavic',		niche = self._niche(add = Media.Slavic)),
				self._menuItem(label = 36586,	image = 'regionbalkan',		niche = self._niche(add = Media.Balkan)),
				self._menuItem(label = 36588,	image = 'regionrussian',	niche = self._niche(add = Media.Russian)),
				self._menuItem(label = 36589,	image = 'regionturkish',	niche = self._niche(add = Media.Turkish)),
				self._menuItem(label = 36590,	image = 'regionmexican',	niche = self._niche(add = Media.Mexican)),
				self._menuItem(label = 36591,	image = 'regionlatin',		niche = self._niche(add = Media.Latin)),
				self._menuItem(label = 36592,	image = 'regionoceanic',	niche = self._niche(add = Media.Oceanic)),
				self._menuItem(label = 36593,	image = 'regionindian',		niche = self._niche(add = Media.Indian)),
				self._menuItem(label = 36594,	image = 'regionchinese',	niche = self._niche(add = Media.Chinese)),
				self._menuItem(label = 36595,	image = 'regionjapanese',	niche = self._niche(add = Media.Japanese)),
				self._menuItem(label = 36596,	image = 'regionkorean',		niche = self._niche(add = Media.Korean)),
				self._menuItem(label = 36597,	image = 'regioneastern',	niche = self._niche(add = Media.Eastern)),
				self._menuItem(label = 36598,	image = 'regionarabian',	niche = self._niche(add = Media.Arabian)),
				self._menuItem(label = 36599,	image = 'regionafrican',	niche = self._niche(add = Media.African)),
			]
		except: Logger.error()
		return None

	def _menuAudience(self):
		try:
			return [
				self._menuItem(label = 33429,	image = 'audiencekid',		niche = self._niche(add = Media.Kid)),
				self._menuItem(label = 36283,	image = 'audienceteen',		niche = self._niche(add = Media.Teen)),
				self._menuItem(label = 36284,	image = 'audienceadult',	niche = self._niche(add = Media.Adult)),
			]
		except: Logger.error()
		return None

	def _menuQuality(self):
		try:
			return [
				self._menuItem(label = 36607,	image = 'qualitygreat',		niche = self._niche(add = Media.Great)),
				self._menuItem(label = 35242,	image = 'qualitygood',		niche = self._niche(add = Media.Good)),
				self._menuItem(label = 36608,	image = 'qualityfair',		niche = self._niche(add = Media.Fair)),
				self._menuItem(label = 35243,	image = 'qualitypoor',		niche = self._niche(add = Media.Poor)),
				self._menuItem(label = 35244,	image = 'qualitybad',		niche = self._niche(add = Media.Bad)),
			]
		except: Logger.error()
		return None

	##############################################################################
	# DISCOVER
	##############################################################################

	def discover(self, **parameters):
		parameters[MetaMenu.ParameterMenu] = MetaMenu.MenuMedia
		parameters[MetaMenu.ParameterContent] = MetaMenu.ContentDiscover
		return self.menu(**parameters)

	##############################################################################
	# SEARCH
	##############################################################################

	def search(self, **parameters):
		parameters[MetaMenu.ParameterMenu] = MetaMenu.MenuMedia
		parameters[MetaMenu.ParameterContent] = MetaMenu.ContentSearch
		return self.menu(**parameters)

	def _search(self, **parameters):
		extra = None
		search = parameters.get(MetaMenu.ParameterSearch)
		query = parameters.get(MetaMenu.ParameterQuery)
		provider = parameters.get(MetaMenu.ParameterProvider)

		# This is needed to prevent the search dialog from popping up again when the container is refreshed later.
		# To replicate: Movies -> Search -> Title -> search a title -> scrape the movie -> play one of the streams -> if playback starts, stop playback -> in the reload-streams dialog, click cancel -> the search dialog shows again asking for input.
		# Save the query as a global variable. If the container containing search results is refreshed, instead of showing the input dialog again, just use the saved query to reload the container.
		id = 'GaiaSearch'
		reload = False
		path = System.infoLabel('Container.FolderPath')
		if path:
			path = Networker.linkDecode(path)
			if path and path.get(MetaMenu.ParameterMenu) == MetaMenu.MenuMedia:
				memory = Memory.get(id = id, local = False, kodi = True)
				if memory:
					reload = True
					query = memory.get('query')
					extra = memory.get('extra')

		if not reload:
			if search == MetaMenu.SearchAdvanced: query, extra = self._searchAdvanced(query = query, provider = provider)
			elif search == MetaMenu.SearchSet: query = self._searchSet(query = query)
			elif search == MetaMenu.SearchList: query = self._searchList(query = query)
			elif search == MetaMenu.SearchPerson: query = self._searchPerson(query = query)
			elif search == MetaMenu.SearchOracle: query = self._searchOracle(query = query)
			elif search == MetaMenu.SearchExact: query = self._searchExact(query = query)
			else: query = self._searchTitle(query = query, provider = provider)
			Memory.set(id = id, value = {'query' : query, 'extra' : extra}, local = False, kodi = True)

		if extra: parameters.update(extra)
		parameters[MetaMenu.ParameterQuery] = query
		return parameters

	def _searchBase(self, type, query = None, provider = None, default = None):
		try:
			from lib.modules.search import Search

			queried = query
			if not query:
				loader = Loader.visible()
				query = Dialog.input(title = Search._title(), type = Dialog.InputAlphabetic, default = default)
				if loader:
					if query: Loader.show() # Since the input dialog closed the loader.
					else: Loader.hide() # Input dialog canceled.
			if not query: return None

			if Tools.isDictionary(query):
				provider = provider or query.get(MetaMenu.ParameterProvider)
				query = query.get(MetaMenu.ParameterQuery)

			if queried: function = Search.instance().update
			else: function = Search.instance().insert
			function(type = type, media = self._media(), niche = self._niche(), query = {MetaMenu.ParameterQuery : query, MetaMenu.ParameterProvider : provider})
		except: Logger.error()
		return query

	def _searchTitle(self, query = None, provider = None):
		from lib.modules.search import Search
		return self._searchBase(type = Search.TypeTitle, query = query, provider = provider)

	def _searchAdvanced(self, query = None, provider = None):
		#gaiafuture
		self._notificationFuture()
		return None, None

		parameters = {}
		try:
			from lib.modules.search import Search

			queried = query
			if not query:
				loader = Loader.visible()
				query = Dialog.input(title = Search._title(), type = Dialog.InputAlphabetic)
				if loader:
					if query: Loader.show() # Since the input dialog closed the loader.
					else: Loader.hide() # Input dialog canceled.
			if not query: return None

			if Tools.isDictionary(query):
				provider = provider or query.get(MetaMenu.ParameterProvider)
				query = query.get(MetaMenu.ParameterQuery)

			if queried: function = Search.instance().update
			else: function = Search.instance().insert
			function(type = Search.TypeAdvanced, media = self._media(), niche = self._niche(), query = {MetaMenu.ParameterQuery : query, MetaMenu.ParameterProvider : provider})

			#parameters['genre'] = 'action'
		except: Logger.error()
		return query, parameters

	def _searchSet(self, query = None, provider = None):
		from lib.modules.search import Search
		return self._searchBase(type = Search.TypeSet, query = query, provider = provider)

	def _searchList(self, query = None, provider = None):
		from lib.modules.search import Search
		return self._searchBase(type = Search.TypeList, query = query, provider = provider)

	def _searchPerson(self, query = None, provider = None):
		from lib.modules.search import Search
		return self._searchBase(type = Search.TypePerson, query = query, provider = provider)

	def _searchOracle(self, query = None):
		try:
			from lib.oracle import Oracle
			Oracle.execute(media = self._media(), history = query)
		except: Logger.error()
		return None

	def _searchExact(self, query = None):
		try:
			from lib.modules.search import Search

			self._notification(content = MetaMenu.ContentSearch, type = MetaMenu.SearchExact, background = False)
			if not query: query = Dialog.input(title = Search._title(), type = Dialog.InputAlphabetic)
			if not query: return None

			if Tools.isDictionary(query): query = query.get(MetaMenu.ParameterQuery)
			Search.instance().insert(type = Search.TypeExact, media = self._media(), niche = self._niche(), query = {MetaMenu.ParameterQuery : query})

			from lib.modules.core import Core
			Core(media = self._media()).scrapeExact(query = query)
		except: Logger.error()
		return None

	##############################################################################
	# BUILD
	##############################################################################

	def buildMedia(self, media = None, niche = None, data = None, content = None):
		items = data.get('items')
		base = data.get('base') or {}
		submenu = base.get('submenu')

		isQuick = content == MetaMenu.ContentQuick
		isProgress = content == MetaMenu.ContentProgress
		isSearch = content == MetaMenu.ContentSearch
		isArrival = content == MetaMenu.ContentArrival
		isRelease = content == MetaMenu.ContentDiscover and base.get(MetaMenu.ParameterRelease)

		if media is None:
			mediad = items[0].get('media') if items else None
			if mediad == Media.Set or content == MetaMenu.ContentSet:
				media = mediad
			elif mediad == Media.List:
				media = Media.List
			elif mediad == Media.Person:
				media = Media.Person
			elif submenu:
				media = Media.Episode
			elif self._mediaSerie() and (isProgress or isQuick): # Display these as shows, since it has a different layout/view with bigger posters.
				media = Media.Show
			else:
				media = self._media(mixed = True)

				# For New Seasons/Episodes release menus where the show metadata is used.
				if base.get(MetaMenu.ParameterRelease) and (Media.isSeason(media) or Media.isEpisode(media)): media = Media.Show

		# Do before isProgress is edited below.
		if (isProgress or isQuick) and Media.isSerie(media): multiple = True
		else: multiple = self.mTools.multiple(items)

		progress = base.get('progress')
		if progress:
			if progress == MetaMenu.ProgressDefault: isProgress = [False, True]
			else: isProgress = [False, 0.98] # Only show progress percentage in the label if 0 <= progress <= 97%.
			if progress == MetaMenu.ProgressRewatch:
				if Media.isSerie(media): media = Media.Show
				isProgress = False # Do not show progress percentage in the label at all.

		decorate = False if isRelease else None

		isEpisode = Media.isEpisode(media)
		isSequential = MetaTools.submenuIsSequential(submenu)
		isAbsolute = MetaTools.submenuIsAbsolute(submenu)

		more = data.get('more')
		page = base.get('page')
		first = not page or page == 1
		bonus = isEpisode and not isSequential and not isAbsolute

		# For Trakt History/Progress menus.
		if submenu is None and isEpisode and not content == MetaMenu.ContentEpisode and not content == MetaMenu.ContentProgress and not content == MetaMenu.ContentQuick: submenu = False

		#gaiafuture - this call takes 400-500ms for an episode page of GoT underneath a season. That is half the time of the entire Python execution. Can anything be improved? Any specific function maybe that causes the slowness?e
		items = self.mTools.items(
			media = media,
			niche = self._niche(niche = niche),
			metadatas = items,
			progress = isProgress,
			decorate = decorate,
			more = more,
			multiple = multiple,
			submenu = submenu,
			recap = bonus,
			extra = bonus,
			hide = True,
			hideSearch = isSearch,
			hideRelease = isRelease or isArrival,
			contextPlaylist = not Media.isShow(media) and not Media.isSeason(media),
			contextShortcut = Shortcut.item(create = True),
		)

		# Auto-select the next episode to watch from the menu.
		select = None
		if isEpisode:
			if first and not multiple: select = self.mTools.selectIndex(items = items, adjust = True)
			else: select = None

		directory = Directory(content = Directory.ContentSettings, media = media, cache = True, lock = False)
		directory.addItems(items = items)
		directory.finish(select = select, loader = isSearch) # The loader initiated from _searchTitle() is not automatically hidden by Kodi once the menu has loaded.

		# Show notifications for the various Progress menus on what they are used for.
		# This can also be used for other menus, to show some description or warning about the menu, for the first few times the menu is opened.
		# Delay to let the menu load first and views.py select an item.
		if content == MetaMenu.ContentProgress and progress and not progress == MetaMenu.ProgressDefault: self._notification(content = content, type = progress, delay = True)
		elif content == MetaMenu.ContentQuick or content == MetaMenu.ContentProgress or content == MetaMenu.ContentArrival: self._notification(content = MetaMenu.ContentSmart, delay = True)

	def buildExtra(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, content = None):
		metadata = self.mManager.metadataSeason(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season)
		directory = Directory(content = Directory.ContentSettings, media = Media.Episode, cache = True, lock = False)
		directory.addItems(items = self.mTools.itemsExtra(metadata = metadata))
		directory.finish()

	def buildFolder(self, metadatas, niche = None):
		media = self._media(mixed = True)
		directory = Directory(content = Directory.ContentSettings, cache = True, lock = False)
		directory.addItems(items = self.mTools.directories(
			media = media,
			niche = self._niche(niche = niche),
			metadatas = metadatas,
		))
		directory.finish()

	def buildContext(self, niche = None, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, episode = None):
		media = self._media()
		niche = self._niche(niche = niche)
		metadata = self.mManager.metadata(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, episode = episode)
		return self.mTools.context(
			media = media,
			niche = niche,
			metadata = metadata,
			playlist = not Media.isShow(media) and not Media.isSeason(media),
			contextShortcut = Shortcut.item(create = True),
		)
