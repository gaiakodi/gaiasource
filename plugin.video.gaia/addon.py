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

import xbmcaddon
developer = xbmcaddon.Addon().getAddonInfo('version') == '9.9.9'
if developer:
	import time as timer
	timeStart = timer.time()

from lib.modules import tools

parameters = tools.System.commandResolve()
action = parameters.get('action')

# For Gaia Eminence.
action = tools.System.redirect(parameters = parameters) or action

if developer: tools.Logger.log('EXECUTION STARTED [Action: %s]' % str(action))

# Execute on first launch.
# Initiate the launch of certain submenus as well, since there might be skin shortcuts linking directly to submenus without going through the main menu (action is None).
if action is None or action == 'home' or action.startswith('movie') or action.startswith('show') or action.startswith('season') or action.startswith('episode') or action.startswith('documentar') or action.startswith('short') or action.startswith('search'): tools.System.launch()

# For Gaia Eminence.
menu = tools.System.menu(action = action, menu = parameters.get('menu'))

# Otherwise importing modules in sub-threads might cause the execution to deadlock.
# Check the modulePrepare() function for more info.
# The deadlock can happen from various places in the indexers (navigator/movies/shows/season/episodes).
#	Eg: navigator -> History -> Seasons (sporadic - sometimes it works).
#	Eg: movies/shows/season/episodes -> metadata().
# There are too many sporadic deadlocks at various places, so it seems better to just place it here.
# Although it takes about 250-300ms, most plugin calls will probably use some of the Networker features anyways, and will then have to import the modules at a later stage.
from lib.modules.network import Networker
Networker.modulePrepare()

media = parameters.get('media')
kids = parameters.get('kids')
kids = int(kids) if kids else 0

source = parameters.get('source')
if not source is None:
	source = tools.Converter.dictionary(source)
	if tools.Tools.isArray(source): source = source[0]

metadata = parameters.get('metadata')
if not metadata is None: metadata = tools.Converter.dictionary(metadata)

from lib.modules import shortcuts
shortcuts.Shortcuts.process(parameters)

if action is None or action == 'home':
	from lib.indexers.navigator import Navigator
	Navigator(media = media, kids = kids, menu = menu).root()

	# Reset the restart flag here, since an addon restart will end up in this function.
	tools.System.restartFinish()

	# Launch the donations dialog.
	# Only show if System.launched(), since the donations dialog is also shown after the intial launch process and we do not want to show it twice.
	# Also call it here, for users who do not shut down their devices and keep it running for a long time.
	if tools.System.launched(): tools.Donations.popup(wait = True)

####################################################
# MOVIE
####################################################

elif action.startswith('movies'):

	if action == 'movies':
		from lib.indexers.navigator import Navigator
		lite = tools.Converter.boolean(parameters.get('lite'))
		Navigator(media = media, kids = kids, menu = menu).movies(lite = lite)

	elif action == 'moviesFavourites':
		from lib.indexers.navigator import Navigator
		lite = tools.Converter.boolean(parameters.get('lite'))
		Navigator(media = media, kids = kids, menu = menu).moviesFavourites(lite = lite)

	elif action == 'moviesRetrieve':
		from lib.indexers.movies import Movies

		link = parameters.get('link')
		refresh = tools.Converter.boolean(parameters.get('refresh'))
		Movies(media = media, kids = kids).retrieve(link, refresh = refresh)

	elif action == 'moviesSearch':
		from lib.indexers.movies import Movies
		Movies(media = media, kids = kids).search(parameters.get('terms'))

	elif action == 'moviesSearches':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).moviesSearches()

	elif action == 'moviesPerson':
		from lib.indexers.movies import Movies
		Movies(media = media, kids = kids).person(parameters.get('terms'))

	elif action == 'moviesPersons':
		from lib.indexers.movies import Movies
		link = parameters.get('link')
		Movies(media = media, kids = kids).persons(link)

	elif action == 'moviesHome':
		from lib.indexers.movies import Movies
		refresh = tools.Converter.boolean(parameters.get('refresh'))
		Movies(media = media, kids = kids).home(refresh = refresh)

	elif action == 'moviesArrivals':
		from lib.indexers.movies import Movies
		refresh = tools.Converter.boolean(parameters.get('refresh'))
		Movies(media = media, kids = kids).arrivals(refresh = refresh)

	elif action == 'moviesCollections':
		from lib.indexers.movies import Movies
		Movies(media = media, kids = kids).collections()

	elif action == 'moviesGenres':
		from lib.indexers.movies import Movies
		Movies(media = media, kids = kids).genres()

	elif action == 'moviesLanguages':
		from lib.indexers.movies import Movies
		Movies(media = media, kids = kids).languages()

	elif action == 'moviesCertificates':
		from lib.indexers.movies import Movies
		Movies(media = media, kids = kids).certifications()

	elif action == 'moviesAge':
		from lib.indexers.movies import Movies
		Movies(media = media, kids = kids).age()

	elif action == 'moviesYears':
		from lib.indexers.movies import Movies
		Movies(media = media, kids = kids).years()

	elif action == 'moviesUserlists':
		from lib.indexers.movies import Movies
		mode = parameters.get('mode')
		watchlist = tools.Converter.boolean(parameters.get('watchlist'))
		Movies(media = media, kids = kids).listUser(mode = mode, watchlist = watchlist)

	elif action == 'moviesDrugs':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).moviesDrugs()

	elif action == 'moviesRandom':
		from lib.indexers.movies import Movies
		Movies(media = media, kids = kids).random()

	elif action == 'moviesCategories':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).moviesCategories()

	elif action == 'moviesLists':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).moviesLists()

	elif action == 'moviesSets':
		#gaiaremove
		#from lib.indexers.navigator import Navigator
		#Navigator(media = media, kids = kids, menu = menu).moviesSets()
		#from lib.meta.processors.tmdb import MetaTmdb
		from lib.meta.tools import MetaTools
		#x =MetaTmdb.set(id = 10)
		x=MetaTools.idSet(title = 'Star Wars', cache = False)
		tools.Logger.log("UUUUUUUUUUUUUUU: "+tools.Converter.jsonTo(x))

	elif action == 'moviesPeople':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).moviesPeople()

####################################################
# SHOW
####################################################

elif action.startswith('shows'):

	if action == 'shows':
		from lib.indexers.navigator import Navigator
		lite = tools.Converter.boolean(parameters.get('lite'))
		Navigator(media = media, kids = kids, menu = menu).shows(lite = lite)

	elif action == 'showsFavourites':
		from lib.indexers.navigator import Navigator
		lite = tools.Converter.boolean(parameters.get('lite'))
		Navigator(media = media, kids = kids, menu = menu).showsFavourites(lite = lite)

	elif action == 'showsRetrieve':
		from lib.indexers.shows import Shows
		link = parameters.get('link')
		refresh = tools.Converter.boolean(parameters.get('refresh'))
		Shows(kids = kids).retrieve(link, refresh = refresh)

	elif action == 'showsSearch':
		from lib.indexers.shows import Shows
		Shows(kids = kids).search(parameters.get('terms'))

	elif action == 'showsSearches':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).showsSearches()

	elif action == 'showsGenres':
		from lib.indexers.shows import Shows
		Shows(kids = kids).genres()

	elif action == 'showsNetworks':
		from lib.indexers.shows import Shows
		Shows(kids = kids).networks()

	elif action == 'showsCertificates':
		from lib.indexers.shows import Shows
		Shows(kids = kids).certifications()

	elif action == 'showsAge':
		from lib.indexers.shows import Shows
		Shows(kids = kids).age()

	elif action == 'showsPerson':
		from lib.indexers.shows import Shows
		Shows(kids = kids).person(parameters.get('terms'))

	elif action == 'showsPersons':
		from lib.indexers.shows import Shows
		link = parameters.get('link')
		Shows(kids = kids).persons(link)

	elif action == 'showsUserlists':
		from lib.indexers.shows import Shows
		mode = parameters.get('mode')
		watchlist = tools.Converter.boolean(parameters.get('watchlist'))
		Shows(kids = kids).listUser(mode = mode, watchlist = watchlist)

	elif action == 'showsRandom':
		from lib.indexers.shows import Shows
		Shows(kids = kids).random()

	elif action == 'showsHome':
		from lib.indexers.episodes import Episodes
		refresh = tools.Converter.boolean(parameters.get('refresh'))
		Episodes(kids = kids).home(refresh = refresh)

	elif action == 'showsArrivals':
		from lib.indexers.episodes import Episodes
		refresh = tools.Converter.boolean(parameters.get('refresh'))
		Episodes(kids = kids).arrivals(refresh = refresh)

	elif action == 'showsCalendars':
		from lib.indexers.episodes import Episodes
		Episodes(kids = kids).calendar()

	elif action == 'showsCategories':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).showsCategories()

	elif action == 'showsLists':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).showsLists()

	elif action == 'showsPeople':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).showsPeople()

	elif action == 'showsYears':
		from lib.indexers.shows import Shows
		Shows(kids = kids).years()

	elif action == 'showsLanguages':
		from lib.indexers.shows import Shows
		Shows(kids = kids).languages()

	elif action == 'showsBinge':
		from lib.indexers.episodes import Episodes
		imdb = parameters.get('imdb')
		tmdb = parameters.get('tmdb')
		tvdb = parameters.get('tvdb')
		trakt = parameters.get('trakt')
		season = parameters.get('season')
		if not season is None: season = int(season)
		episode = parameters.get('episode')
		if not episode is None: episode = int(episode)
		Episodes(kids = kids).binge(scrape = True, idImdb = imdb, idTmdb = tmdb, idTvdb = tvdb, idTrakt = trakt, season = season, episode = episode)

####################################################
# SEASON
####################################################

elif action.startswith('seasons'):

	if action == 'seasonsRetrieve':
		from lib.indexers.seasons import Seasons
		link = parameters.get('link')
		imdb = parameters.get('imdb')
		tvdb = parameters.get('tvdb')
		title = parameters.get('tvshowtitle')
		if not title: title = parameters.get('title')
		year = parameters.get('year')
		if year: year = int(year)
		refresh = tools.Converter.boolean(parameters.get('refresh'))
		Seasons(kids = kids).retrieve(link = link, idImdb = imdb, idTvdb = tvdb, title = title, year = year, refresh = refresh)

	elif action == 'seasonsUserlists':
		from lib.indexers.seasons import Seasons
		mode = parameters.get('mode')
		watchlist = tools.Converter.boolean(parameters.get('watchlist'))
		Seasons(kids = kids).listUser(mode = mode, watchlist = watchlist)

	elif action == 'seasonsExtras':
		from lib.indexers.seasons import Seasons
		Seasons(kids = kids).extras(metadata = metadata)

####################################################
# EPISODE
####################################################

elif action.startswith('episodes'):

	if action == 'episodesRetrieve':
		from lib.indexers.episodes import Episodes
		link = parameters.get('link')
		imdb = parameters.get('imdb')
		tvdb = parameters.get('tvdb')
		title = parameters.get('tvshowtitle')
		if not title: title = parameters.get('title')
		year = parameters.get('year')
		if year: year = int(year)
		season = parameters.get('season')
		if not season is None: season = float(season) # NB: Make float so we can have a negative zero offset (-0.0) for the specials season.
		episode = parameters.get('episode')
		if not episode is None: episode = float(episode) # NB: Make float so we can have a negative zero offset (-0.0) for the specials season.
		limit = parameters.get('limit')
		if not limit is None: limit = int(limit)
		refresh = tools.Converter.boolean(parameters.get('refresh'))
		Episodes(kids = kids).retrieve(link = link, idImdb = imdb, idTvdb = tvdb, title = title, year = year, season = season, episode = episode, limit = limit, refresh = refresh)

	elif action == 'episodesUserlists':
		from lib.indexers.episodes import Episodes
		mode = parameters.get('mode')
		watchlist = tools.Converter.boolean(parameters.get('watchlist'))
		Episodes(kids = kids).listUser(mode = mode, watchlist = watchlist)

####################################################
# REFRESH
####################################################

elif action.startswith('refresh'):

	if action == 'refreshMenu':
		from lib.modules import interface
		interface.Loader.show()

		if tools.Converter.boolean(parameters.get('playback')):
			from lib.modules.playback import Playback
			media = parameters.get('media')
			Playback.instance().refresh(media = media, wait = True)

		interface.Loader.hide() # Hide before, since Kodi will show its own laoder when refreshing the directory.
		interface.Directory.refresh()

	elif action == 'refreshMetadata':
		from lib.modules import interface
		interface.Loader.show()

		media = parameters.get('media')
		imdb = parameters.get('imdb')
		tmdb = parameters.get('tmdb')
		tvdb = parameters.get('tvdb')
		trakt = parameters.get('trakt')
		season = parameters.get('season')
		if not season is None: season = int(season)
		episode = parameters.get('episode')
		if not episode is None: episode = int(episode)

		if tools.Media.typeMovie(media):
			from lib.indexers.movies import Movies
			Movies(media = media, kids = kids).metadata(idImdb = imdb, idTmdb = tmdb, idTvdb = tvdb, idTrakt = trakt, refresh = True)
		elif media == tools.Media.TypeShow:
			from lib.indexers.shows import Shows
			Shows(kids = kids).metadata(idImdb = imdb, idTmdb = tmdb, idTvdb = tvdb, idTrakt = trakt, refresh = True)
		elif media == tools.Media.TypeSeason:
			from lib.indexers.seasons import Seasons
			Seasons(kids = kids).metadata(idImdb = imdb, idTmdb = tmdb, idTvdb = tvdb, idTrakt = trakt, season = season, refresh = True)
		elif media == tools.Media.TypeEpisode:
			from lib.indexers.episodes import Episodes
			Episodes(kids = kids).metadata(idImdb = imdb, idTmdb = tmdb, idTvdb = tvdb, idTrakt = trakt, season = season, episode = episode, refresh = True)

		interface.Loader.hide() # Hide before, since Kodi will show its own laoder when refreshing the directory.
		interface.Directory.refresh()

####################################################
# SYSTEM
####################################################

elif action.startswith('system'):

	if action == 'systemNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).systemNavigator()

	elif action == 'systemInformation':
		tools.System.information()

	elif action == 'systemManager':
		tools.System.manager()

	elif action == 'systemTools':
		tools.System.tools()

	if action == 'systemBenchmark':
		from lib.modules.tester import Tester
		Tester.benchmarkDialog()

	elif action == 'systemRestart':
		tools.System.restart()

####################################################
# EXTERNAL
####################################################

elif action.startswith('external'):

	if action == 'externalImport':
		from lib.modules.external import Loader
		module = parameters.get('module')
		Loader.instance(module = module).moduleLoad()

####################################################
# LOG
####################################################

elif action.startswith('log'):

	if action == 'logNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).logNavigator()

	elif action == 'logScrape':
		tools.Logger.dialogScrape()

	elif action == 'logKodi':
		tools.Logger.dialog()

####################################################
# UTILITY
####################################################

elif action.startswith('utility'):

	if action == 'utilityNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).utilityNavigator()

####################################################
# NFORMATION
####################################################

elif action.startswith('information'):

	if action == 'informationNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).informationNavigator()

	elif action == 'informationPremium':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).informationPremium()

	elif action == 'informationChangelog':
		from lib.modules import interface
		interface.Changelog.show()

	elif action == 'informationDisclaimer':
		tools.Disclaimer.show(exit = True)

	elif action == 'informationAnnouncement':
		tools.Announcements.show(force = True)

	elif action == 'informationAttribution':
		from lib.modules.window import WindowAttribution
		WindowAttribution.show(progress = False)

	elif action == 'informationAbout':
		from lib.modules import interface
		interface.Splash.popupAbout()

####################################################
# PROMOTIONS
####################################################

elif action.startswith('promotions'):

	if action == 'promotionsNavigator':
		tools.Promotions.navigator(force = tools.Converter.boolean(parameters.get('force')))

	elif action == 'promotionsSelect':
		tools.Promotions.select(provider = parameters.get('provider'))

####################################################
# PLAYLIST
####################################################

elif action.startswith('playlist'): # Must be before the 'play' section.

	if action == 'playlistShow':
		tools.Playlist.show()

	elif action == 'playlistClear':
		tools.Playlist.clear()

	elif action == 'playlistAdd':
		label = parameters.get('label')
		link = parameters.get('link')
		context = parameters.get('context')
		tools.Playlist.add(link = link, label = label, metadata = metadata, context = context)

	elif action == 'playlistRemove':
		label = parameters.get('label')
		tools.Playlist.remove(label = label)

####################################################
# PLAYBACK
####################################################

elif action.startswith('playback'): # Must be before the 'play' section.

	if action == 'playbackWatch':
		from lib.modules.playback import Playback
		media = parameters.get('media')
		imdb = parameters.get('imdb')
		tmdb = parameters.get('tmdb')
		tvdb = parameters.get('tvdb')
		trakt = parameters.get('trakt')
		season = parameters.get('season')
		if not season is None: season = int(season)
		episode = parameters.get('episode')
		if not episode is None: episode = int(episode)
		Playback.instance().dialogWatch(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

	elif action == 'playbackUnwatch':
		from lib.modules.playback import Playback
		media = parameters.get('media')
		imdb = parameters.get('imdb')
		tmdb = parameters.get('tmdb')
		tvdb = parameters.get('tvdb')
		trakt = parameters.get('trakt')
		season = parameters.get('season')
		if not season is None: season = int(season)
		episode = parameters.get('episode')
		if not episode is None: episode = int(episode)
		Playback.instance().dialogUnwatch(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

	elif action == 'playbackRate':
		from lib.modules.playback import Playback
		media = parameters.get('media')
		imdb = parameters.get('imdb')
		tmdb = parameters.get('tmdb')
		tvdb = parameters.get('tvdb')
		trakt = parameters.get('trakt')
		season = parameters.get('season')
		if not season is None: season = int(season)
		episode = parameters.get('episode')
		if not episode is None: episode = int(episode)
		Playback.instance().dialogRate(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

	elif action == 'playbackUnrate':
		from lib.modules.playback import Playback
		media = parameters.get('media')
		imdb = parameters.get('imdb')
		tmdb = parameters.get('tmdb')
		tvdb = parameters.get('tvdb')
		trakt = parameters.get('trakt')
		season = parameters.get('season')
		if not season is None: season = int(season)
		episode = parameters.get('episode')
		if not episode is None: episode = int(episode)
		Playback.instance().dialogUnrate(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

	elif action == 'playbackRefresh':
		from lib.modules.playback import Playback
		media = parameters.get('media')
		Playback.instance().dialogRefresh(media = media)

	elif action == 'playbackReset':
		from lib.modules.playback import Playback
		media = parameters.get('media')
		imdb = parameters.get('imdb')
		tmdb = parameters.get('tmdb')
		tvdb = parameters.get('tvdb')
		trakt = parameters.get('trakt')
		season = parameters.get('season')
		if not season is None: season = int(season)
		episode = parameters.get('episode')
		if not episode is None: episode = int(episode)
		Playback.instance().dialogReset(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

####################################################
# PLAY
####################################################

elif action.startswith('play'):

	if action == 'play':
		if not tools.System.globalLocked(id = 'play'): # Check playcount.py for more details.
			from lib.modules import interface
			from lib.modules import core
			interface.Loader.show() # Immediately show the loader, since slow system will take long to show it in play().
			try: binge = int(parameters.get('binge'))
			except: binge = None
			try: resume = int(parameters.get('resume'))
			except: resume = None
			try: autoplay = tools.Converter.boolean(parameters.get('autoplay'))
			except: autoplay = False
			try: library = tools.Converter.boolean(parameters.get('library'))
			except: library = False
			try: new = tools.Converter.boolean(parameters.get('new'))
			except: new = False
			try: add = tools.Converter.boolean(parameters.get('add'))
			except: add = False
			try: reload = tools.Converter.boolean(parameters.get('reload'))
			except: reload = True
			downloadType = parameters.get('downloadType')
			downloadId = parameters.get('downloadId')
			handleMode = parameters.get('handleMode')
			core.Core(media = media, kids = kids).play(source = source, metadata = metadata, downloadType = downloadType, downloadId = downloadId, handleMode = handleMode, autoplay = autoplay, library = library, new = new, add = add, binge = binge, reload = reload, resume = resume)

	if action == 'playCache':
		from lib.modules import core
		try: binge = int(parameters.get('binge'))
		except: binge = None
		try: reload = tools.Converter.boolean(parameters.get('reload'))
		except: reload = True
		handleMode = parameters.get('handleMode')
		core.Core(media = media, kids = kids).playCache(source = source, metadata = metadata, handleMode = handleMode, binge = binge, reload = reload)

	elif action == 'playLocal':
		from lib.modules import core
		try: binge = int(parameters.get('binge'))
		except: binge = None
		path = parameters.get('path')
		downloadType = parameters.get('downloadType')
		downloadId = parameters.get('downloadId')
		core.Core(media = media, kids = kids).playLocal(path = path, source = source, metadata = metadata, downloadType = downloadType, downloadId = downloadId, binge = binge)

####################################################
# CLEAN
####################################################

elif action.startswith('clean'):

	if action == 'clean':
		tools.Cleanup.clean()

####################################################
# VERIFICATION
####################################################

elif action.startswith('verification'):

	if action == 'verificationNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).verificationNavigator()

	elif action == 'verificationAccounts':
		from lib.modules.account import Account
		Account.verifyDialog()

####################################################
# SEARCH
####################################################

elif action.startswith('search'):

	if action == 'search':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).search()

	elif action == 'searchExact':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).searchExact()

	elif action == 'searchHistory':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).searchHistory()

	elif action == 'searchHistoryMovies':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).searchHistoryMovies()

	elif action == 'searchHistoryShows':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).searchHistoryShows()

####################################################
# PROVIDERS
####################################################

elif action.startswith('providers'):

	if action == 'providersPresets':
		from lib.providers.core.manager import Manager
		settings = tools.Converter.boolean(parameters.get('settings'))
		Manager.presets(settings = settings)

	elif action == 'providersConfigure':
		from lib.modules.interface import Loader
		Loader.show() # Show here already for slow devices.
		from lib.providers.core.manager import Manager
		id = parameters.get('id')
		type = parameters.get('type')
		mode = parameters.get('mode')
		access = parameters.get('access')
		addon = parameters.get('addon')
		settings = tools.Converter.boolean(parameters.get('settings'))
		Manager.settings(id = id, type = type, mode = mode, access = access, addon = addon, settings = settings)

	elif action == 'providersVerify':
		from lib.providers.core.manager import Manager
		Manager.verify()

	elif action == 'providersOptimize':
		from lib.providers.core.manager import Manager
		settings = tools.Converter.boolean(parameters.get('settings'))
		Manager.optimizeProvider(settings = settings)

####################################################
# DOWNLOADS
####################################################

elif action.startswith('download'):

	if action == 'download':
		from lib.modules import interface
		try:
			interface.Loader.show()

			from lib.modules import core
			from lib.modules import downloader

			downloadType = parameters.get('downloadType')
			downloadId = parameters.get('downloadId')
			refresh = tools.Converter.boolean(parameters.get('refresh'))
			downer = downloader.Downloader(downloadType)
			if downloadId is None:
				image = parameters.get('image')
				handleMode = parameters.get('handleMode')
				link = core.Core(media = media, kids = kids).sourceResolve(source, info = True, internal = False, download = True, handleMode = handleMode)['link']
				if link is None:
					interface.Loader.hide()
				else:
					title = tools.Media.title(type = media, metadata = metadata)
					downer.download(media = media, title = title, link = link, image = image, metadata = metadata, source = tools.Converter.jsonTo(source), refresh = refresh)
			else:
				downer.download(id = downloadId, forceAction = True, refresh = refresh)
		except:
			interface.Loader.hide()
			tools.Logger.error()

	if action == 'downloadExecute':
		import sys
		from lib.modules import downloader
		downloader.Downloader.execute(action = tools.System.arguments(3), type = tools.System.arguments(4), id = tools.System.arguments(5), observation = tools.System.arguments(6))

	elif action == 'downloadDetails':
		from lib.modules import downloader
		downloadType = parameters.get('downloadType')
		downloadId = parameters.get('downloadId')
		downloader.Downloader(type = downloadType, id = downloadId).details()

	elif action == 'downloads':
		from lib.indexers.navigator import Navigator
		downloadType = parameters.get('downloadType')
		Navigator(media = media, kids = kids, menu = menu).downloads(downloadType)

	elif action == 'downloadsManager':
		from lib.modules import downloader
		downloadType = parameters.get('downloadType')
		if downloadType is None: downloadType = downloader.Downloader.TypeManual
		downer = downloader.Downloader(type = downloadType)
		downer.items(status = downloader.Downloader.StatusAll, refresh = False)

	elif action == 'downloadsBrowse':
		from lib.indexers.navigator import Navigator
		downloadType = parameters.get('downloadType')
		downloadError = parameters.get('downloadError')
		Navigator(media = media, kids = kids, menu = menu).downloadsBrowse(downloadType, downloadError)

	elif action == 'downloadsList':
		downloadType = parameters.get('downloadType')
		downloadStatus = parameters.get('downloadStatus')
		if downloadStatus is None:
			from lib.indexers.navigator import Navigator
			Navigator(media = media, kids = kids, menu = menu).downloadsList(downloadType)
		else:
			from lib.modules import downloader
			downer = downloader.Downloader(downloadType)
			# Do not refresh the list using a thread. Seems like the thread is not always stopped and then it ends with multiple threads updating the list.
			# During the update duration multiple refreshes sometimes happen due to this. Hence, you will see the loader flash multiple times during the 10 secs.
			# Also, with a fresh the front progress dialog also flashes and reset it's focus.
			#downer.items(status = status, refresh = True)
			downer.items(status = downloadStatus, refresh = False)

	elif action == 'downloadsClear':
		downloadType = parameters.get('downloadType')
		downloadStatus = parameters.get('downloadStatus')
		if downloadStatus is None:
			from lib.indexers.navigator import Navigator
			Navigator(media = media, kids = kids, menu = menu).downloadsClear(downloadType)
		else:
			from lib.modules import downloader
			downer = downloader.Downloader(downloadType)
			downer.clear(status = downloadStatus)

	elif action == 'downloadsRefresh':
		from lib.modules import downloader
		downloadType = parameters.get('downloadType')
		downer = downloader.Downloader(downloadType)
		downer.itemsRefresh()

	elif action == 'downloadsSettings':
		tools.Settings.launch(tools.Settings.CategoryDownload)

	elif action == 'downloadCloud':
		from lib.modules import core
		core.Core(media = media, kids = kids).sourceCloud(source)

####################################################
# AMBILIGHT
####################################################

elif action.startswith('ambilight'):

	if action == 'ambilightNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).ambilightNavigator()

####################################################
# LIGHTPACK
####################################################

elif action.startswith('lightpack'):

	if action == 'lightpackNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).lightpackNavigator()

	elif action == 'lightpackSwitchOn':
		tools.Lightpack().switchOn(message = True)

	elif action == 'lightpackSwitchOff':
		tools.Lightpack().switchOff(message = True)

	elif action == 'lightpackAnimate':
		force = parameters.get('force')
		force = True if force is None else tools.Converter.boolean(force)
		tools.Lightpack().animate(force = force, message = True, delay = True)

	elif action == 'lightpackSettings':
		tools.Lightpack().settings()

####################################################
# KIDS
####################################################

elif action.startswith('kids'):

	if action == 'kids':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).kids()

	elif action == 'kidsLock':
		tools.Kids.lock()

	elif action == 'kidsUnlock':
		tools.Kids.unlock()

####################################################
# DOCUMENTARIES
####################################################

elif action.startswith('documentaries'):

	if action == 'documentaries':
		from lib.indexers.navigator import Navigator
		Navigator(media = tools.Media.TypeDocumentary, kids = kids, menu = menu).movies()

####################################################
# SHORTS
####################################################

elif action.startswith('shorts'):

	if action == 'shorts':
		from lib.indexers.navigator import Navigator
		Navigator(media = tools.Media.TypeShort, kids = kids, menu = menu).movies()

####################################################
# SHORTS
####################################################

elif action.startswith('channels'):

	if action == 'channels':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).channels()

	elif action == 'channelsIndividuals':
		from lib.indexers.channels import Channels
		Channels(media = media, kids = kids).channels()

	elif action == 'channelsBroadcasters':
		from lib.indexers.channels import Channels
		Channels(media = media, kids = kids).broadcasters()

	elif action == 'channelsRetrieve':
		from lib.indexers.channels import Channels
		link = parameters.get('link')
		Channels(media = media, kids = kids).retrieve(link = link)

####################################################
# SERVICES
####################################################

elif action.startswith('services'):

	if action == 'servicesNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).servicesNavigator()

	elif action == 'servicesPremiumNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).servicesPremiumNavigator()

	elif action == 'servicesScraperNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).servicesScraperNavigator()

	elif action == 'servicesResolverNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).servicesResolverNavigator()

	elif action == 'servicesDownloaderNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).servicesDownloaderNavigator()

	elif action == 'servicesUtilityNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).servicesUtilityNavigator()

####################################################
# PREMIUMIZE
####################################################

elif action.startswith('premiumize'):

	if action == 'premiumizeAuthentication':
		from lib.debrid import premiumize
		settings = tools.Converter.boolean(parameters.get('settings'))
		premiumize.Interface().accountAuthentication(settings = settings)

	elif action == 'premiumizeNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).premiumizeNavigator()

	elif action == 'premiumizeDownloadsNavigator':
		from lib.indexers.navigator import Navigator
		lite = tools.Converter.boolean(parameters.get('lite'))
		Navigator(media = media, kids = kids, menu = menu).premiumizeDownloadsNavigator(lite = lite)

	elif action == 'premiumizeList':
		from lib.debrid import premiumize
		premiumize.Interface().directoryList()

	elif action == 'premiumizeListAction':
		from lib.debrid import premiumize
		item = parameters.get('item')
		context = parameters.get('context')
		premiumize.Interface().directoryListAction(item, context)

	elif action == 'premiumizeItem':
		from lib.debrid import premiumize
		item = parameters.get('item')
		premiumize.Interface().directoryItem(item)

	elif action == 'premiumizeItemAction':
		from lib.debrid import premiumize
		item = parameters.get('item')
		premiumize.Interface().directoryItemAction(item)

	elif action == 'premiumizeAdd':
		from lib.debrid import premiumize
		premiumize.Interface().addManual()

	elif action == 'premiumizeInformation':
		from lib.debrid import premiumize
		premiumize.Interface().downloadInformation()

	elif action == 'premiumizeAccount':
		from lib.debrid import premiumize
		premiumize.Interface().account()

	elif action == 'premiumizeWebsite':
		from lib.debrid import premiumize
		premiumize.Core().website(open = True)

	elif action == 'premiumizeVpn':
		from lib.debrid import premiumize
		premiumize.Core().vpn(open = True)

	elif action == 'premiumizeClear':
		from lib.debrid import premiumize
		premiumize.Interface().clear()

	elif action == 'premiumizeSettings':
		tools.Settings.launch(id = 'premium.premiumize.enabled')

####################################################
# PREMIUMIZE
####################################################

elif action.startswith('offcloud'):

	if action == 'offcloudAuthentication':
		from lib.debrid import offcloud
		settings = tools.Converter.boolean(parameters.get('settings'))
		offcloud.Interface().accountAuthentication(settings = settings)

	elif action == 'offcloudNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).offcloudNavigator()

	elif action == 'offcloudDownloadsNavigator':
		from lib.indexers.navigator import Navigator
		lite = tools.Converter.boolean(parameters.get('lite'))
		category = parameters.get('category')
		Navigator(media = media, kids = kids, menu = menu).offcloudDownloadsNavigator(lite = lite, category = category)

	elif action == 'offcloudList':
		from lib.debrid import offcloud
		category = parameters.get('category')
		offcloud.Interface().directoryList(category = category)

	elif action == 'offcloudListAction':
		from lib.debrid import offcloud
		item = parameters.get('item')
		context = parameters.get('context')
		offcloud.Interface().directoryListAction(item = item, context = context)

	elif action == 'poffcloudItem':
		from lib.debrid import offcloud
		item = parameters.get('item')
		offcloud.Interface().directoryItem(item)

	elif action == 'offcloudItemAction':
		from lib.debrid import offcloud
		item = parameters.get('item')
		offcloud.Interface().directoryItemAction(item)

	elif action == 'offcloudAdd':
		from lib.debrid import offcloud
		category = parameters.get('category')
		offcloud.Interface().addManual(category = category)

	elif action == 'offcloudInformation':
		from lib.debrid import offcloud
		category = parameters.get('category')
		offcloud.Interface().downloadInformation(category = category)

	elif action == 'offcloudAdd':
		from lib.debrid import offcloud
		offcloud.Interface().addManual()

	elif action == 'offcloudAccount':
		from lib.debrid import offcloud
		offcloud.Interface().account()

	elif action == 'offcloudWebsite':
		from lib.debrid import offcloud
		offcloud.Core().website(open = True)

	elif action == 'offcloudClear':
		from lib.debrid import offcloud
		category = parameters.get('category')
		offcloud.Interface().clear(category = category)

	elif action == 'offcloudSettings':
		tools.Settings.launch(id = 'premium.offcloud.enabled')

	elif action == 'offcloudSettingsLocation':
		from lib.debrid import offcloud
		offcloud.Interface().settingsLocation()

####################################################
# REALDEBRID
####################################################

elif action.startswith('realdebrid'):

	if action == 'realdebridAuthentication':
		from lib.debrid import realdebrid
		settings = tools.Converter.boolean(parameters.get('settings'))
		realdebrid.Interface().accountAuthentication(settings = settings)

	elif action == 'realdebridNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).realdebridNavigator()

	elif action == 'realdebridDownloadsNavigator':
		from lib.indexers.navigator import Navigator
		lite = tools.Converter.boolean(parameters.get('lite'))
		Navigator(media = media, kids = kids, menu = menu).realdebridDownloadsNavigator(lite = lite)

	elif action == 'realdebridList':
		from lib.debrid import realdebrid
		realdebrid.Interface().directoryList()

	elif action == 'realdebridListAction':
		from lib.debrid import realdebrid
		item = parameters.get('item')
		realdebrid.Interface().directoryListAction(item)

	elif action == 'realdebridAdd':
		from lib.debrid import realdebrid
		realdebrid.Interface().addManual()

	elif action == 'realdebridInformation':
		from lib.debrid import realdebrid
		realdebrid.Interface().downloadInformation()

	elif action == 'realdebridAccount':
		from lib.debrid import realdebrid
		realdebrid.Interface().account()

	elif action == 'realdebridWebsite':
		from lib.debrid import realdebrid
		realdebrid.Core().website(open = True)

	elif action == 'realdebridClear':
		from lib.debrid import realdebrid
		realdebrid.Interface().clear()

	elif action == 'realdebridSettings':
		tools.Settings.launch(id = 'premium.realdebrid.enabled')

####################################################
# EASYNEWS
####################################################

elif action.startswith('easynews'):

	if action == 'easynewsAuthentication':
		from lib.debrid import easynews
		settings = tools.Converter.boolean(parameters.get('settings'))
		easynews.Interface().accountAuthentication(settings = settings)

	elif action == 'easynewsNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).easynewsNavigator()

	elif action == 'easynewsAccount':
		from lib.debrid import easynews
		easynews.Interface().account()

	elif action == 'easynewsWebsite':
		from lib.debrid import easynews
		easynews.Core().website(open = True)

	elif action == 'easynewsVpn':
		from lib.debrid import easynews
		easynews.Core().vpn(open = True)

	elif action == 'easynewsSettings':
		tools.Settings.launch(id = 'premium.realdebrid.easynews')

####################################################
# EMBY
####################################################

elif action.startswith('emby'):

	if action == 'embyNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).embyNavigator()

	elif action == 'embySettings':
		from lib.modules.center import Emby
		Emby().settings()

	elif action == 'embyWebsite':
		from lib.modules.center import Emby
		Emby().website(open = True)

####################################################
# JELLYFIN
####################################################

elif action.startswith('jellyfin'):

	if action == 'jellyfinNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).jellyfinNavigator()

	elif action == 'jellyfinSettings':
		from lib.modules.center import Jellyfin
		Jellyfin().settings()

	elif action == 'jellyfinWebsite':
		from lib.modules.center import Jellyfin
		Jellyfin().website(open = True)

####################################################
# ELEMENTUM
####################################################

elif action.startswith('elementum'):

	if action == 'elementumNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).elementumNavigator()

	elif action == 'elementumConnect':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Elementum.connect(install = False, settings = settings)

	elif action == 'elementumInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Elementum.connect(install = True, settings = settings)

	elif action == 'elementumLaunch':
		tools.Elementum.launch()

	elif action == 'elementumInterface':
		tools.Elementum.interface()

	elif action == 'elementumSettings':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Elementum.settings(settings = settings)

####################################################
# QUASAR
####################################################

elif action.startswith('quasar'):

	if action == 'quasarNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).quasarNavigator()

	elif action == 'quasarConnect':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Quasar.connect(install = False, settings = settings)

	elif action == 'quasarInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Quasar.connect(install = True, settings = settings)

	elif action == 'quasarLaunch':
		tools.Quasar.launch()

	elif action == 'quasarInterface':
		tools.Quasar.interface()

	elif action == 'quasarSettings':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Quasar.settings(settings = settings)

####################################################
# RESOLVER
####################################################

elif action.startswith('resolver'):

	if action == 'resolverAuthentication':
		type = parameters.get('type')
		help = tools.Converter.boolean(parameters.get('help'))
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Resolver.authentication(type = type, help = help, settings = settings)

	elif action == 'resolverInstall':
		help = tools.Converter.boolean(parameters.get('help'))
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Resolver.install(help = help, settings = settings)

	elif action == 'resolverSettings':
		universal = tools.Converter.boolean(parameters.get('universal'))
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Resolver.settings(universal = universal, settings = settings)

####################################################
# RESOLVEURL
####################################################

elif action.startswith('resolveurl'):

	if action == 'resolveurlNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).resolveurlNavigator()

	elif action == 'resolveurlSettings':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.ResolveUrl.settings(settings = settings)

	elif action == 'resolveurlInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.ResolveUrl.enable(refresh = True, confirm = True, settings = settings)

	elif action == 'resolveurlAuthentication':
		type = parameters.get('type')
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.ResolveUrl.authentication(type = type, settings = settings)

####################################################
# URLRESOLVER
####################################################

elif action.startswith('urlresolver'):

	if action == 'urlresolverNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).urlresolverNavigator()

	elif action == 'urlresolverSettings':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.UrlResolver.settings(settings = settings)

	elif action == 'urlresolverInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.UrlResolver.enable(refresh = True, confirm = True, settings = settings)

	elif action == 'urlresolverAuthentication':
		type = parameters.get('type')
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.UrlResolver.authentication(type = type, settings = settings)

####################################################
# OPESCRAPERS
####################################################

elif action.startswith('opescrapers'):

	if action == 'opescrapersNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).opescrapersNavigator()

	elif action == 'opescrapersSettings':
		tools.OpeScrapers.settings()

	elif action == 'opescrapersProviders':
		tools.OpeScrapers.providers()

	elif action == 'opescrapersInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.OpeScrapers.enable(refresh = True, settings = settings)

####################################################
# FENSCRAPERS
####################################################

elif action.startswith('fenscrapers'):

	if action == 'fenscrapersNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).fenscrapersNavigator()

	elif action == 'fenscrapersSettings':
		tools.FenScrapers.settings()

	elif action == 'fenscrapersProviders':
		tools.FenScrapers.providers()

	elif action == 'fenscrapersInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.FenScrapers.enable(refresh = True, settings = settings)

####################################################
# OATSCRAPERS
####################################################

elif action.startswith('oatscrapers'):

	if action == 'oatscrapersNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).oatscrapersNavigator()

	elif action == 'oatscrapersSettings':
		tools.OatScrapers.settings()

	elif action == 'oatscrapersProviders':
		tools.OatScrapers.providers()

	elif action == 'oatscrapersInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.OatScrapers.enable(refresh = True, settings = settings)


####################################################
# CRESCRAPERS
####################################################

elif action.startswith('crescrapers'):

	if action == 'crescrapersNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).crescrapersNavigator()

	elif action == 'crescrapersSettings':
		tools.CreScrapers.settings()

	elif action == 'crescrapersProviders':
		tools.CreScrapers.providers()

	elif action == 'crescrapersInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.CreScrapers.enable(refresh = True, settings = settings)

####################################################
# LAMSCRAPERS
####################################################

elif action.startswith('lamscrapers'):

	if action == 'lamscrapersNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).lamscrapersNavigator()

	elif action == 'lamscrapersSettings':
		tools.LamScrapers.settings()

	elif action == 'lamscrapersProviders':
		tools.LamScrapers.providers()

	elif action == 'lamscrapersInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.LamScrapers.enable(refresh = True, settings = settings)

####################################################
# CIVCRAPERS
####################################################

elif action.startswith('civscrapers'):

	if action == 'civscrapersNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).civscrapersNavigator()

	elif action == 'civscrapersSettings':
		tools.CivScrapers.settings()

	elif action == 'civscrapersProviders':
		tools.CivScrapers.providers()

	elif action == 'civscrapersInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.CivScrapers.enable(refresh = True, settings = settings)

####################################################
# GLOSCRAPERS
####################################################

elif action.startswith('gloscrapers'):

	if action == 'gloscrapersNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).gloscrapersNavigator()

	elif action == 'gloscrapersSettings':
		tools.GloScrapers.settings()

	elif action == 'gloscrapersProviders':
		tools.GloScrapers.providers()

	elif action == 'gloscrapersInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.GloScrapers.enable(refresh = True, settings = settings)

####################################################
# UNISCRAPERS
####################################################

elif action.startswith('uniscrapers'):

	if action == 'uniscrapersNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).uniscrapersNavigator()

	elif action == 'uniscrapersSettings':
		tools.UniScrapers.settings()

	elif action == 'uniscrapersProviders':
		tools.UniScrapers.providers()

	elif action == 'uniscrapersInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.UniScrapers.enable(refresh = True, settings = settings)

####################################################
# NANSCRAPERS
####################################################

elif action.startswith('nanscrapers'):

	if action == 'nanscrapersNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).nanscrapersNavigator()

	elif action == 'nanscrapersSettings':
		tools.NanScrapers.settings()

	elif action == 'nanscrapersProviders':
		tools.NanScrapers.providers()

	elif action == 'nanscrapersInstall':
		tools.NanScrapers.enable(refresh = True)

####################################################
# YOUTUBE
####################################################

elif action.startswith('youtube'):

	if action == 'youtubeAuthentication':
		from lib.modules import video
		settings = tools.Converter.boolean(parameters.get('settings'))
		video.Video.authentication(settings = settings)

	elif action == 'youtubeNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).youtubeNavigator()

	elif action == 'youtubeSettings':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.YouTube.settings(settings = settings)

	elif action == 'youtubeInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.YouTube.enable(settings = settings)

	elif action == 'youtubeQuality':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.YouTube.qualitySelect(settings = settings)

	elif action == 'youtubeLaunch':
		tools.YouTube.launch()

	elif action == 'youtubeWebsite':
		tools.YouTube.website(open = True)

####################################################
# UPNEXT
####################################################

elif action.startswith('upnext'):

	if action == 'upnextNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).upnextNavigator()

	elif action == 'upnextSettings':
		tools.UpNext.settings()

	elif action == 'upnextInstall':
		tools.UpNext.enable(refresh = True)

####################################################
# VPNMANAGER
####################################################

elif action.startswith('vpnmanager'): # Make sure this is placed BEFORE the 'vpn' category.

	if action == 'vpnmanagerNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).vpnmanagerNavigator()

	elif action == 'vpnmanagerLaunch':
		tools.VpnManager.launch()

	elif action == 'vpnmanagerSettings':
		tools.VpnManager.settings()

	elif action == 'vpnmanagerInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.VpnManager.enable(refresh = True, confirm = True, settings = settings)

####################################################
# BLUETOOTH
####################################################

elif action.startswith('bluetooth'):

	if action == 'bluetoothConnect':
		from lib.modules.bluetooth import Bluetooth
		Bluetooth.connect()

	elif action == 'bluetoothDisconnect':
		from lib.modules.bluetooth import Bluetooth
		Bluetooth.disconnect()

	elif action == 'bluetoothDialog':
		from lib.modules.bluetooth import Bluetooth
		settings = tools.Converter.boolean(parameters.get('settings'))
		Bluetooth.dialog(settings = settings)

####################################################
# SPEEDTEST
####################################################

elif action.startswith('speedtest'):

	if action == 'speedtestNavigator':
		from lib.indexers.navigator import Navigator
		from lib.modules import speedtest
		Navigator(menu = menu).speedtestNavigator()

	elif action == 'speedtest':
		from lib.modules import speedtest
		speedtest.SpeedTester.select(parameters.get('update'))

	elif action == 'speedtestGlobal':
		from lib.modules import speedtest
		speedtest.SpeedTesterGlobal().show(parameters.get('update'))

	elif action == 'speedtestPremiumize':
		from lib.modules import speedtest
		speedtest.SpeedTesterPremiumize().show(parameters.get('update'))

	elif action == 'speedtestOffCloud':
		from lib.modules import speedtest
		speedtest.SpeedTesterOffCloud().show(parameters.get('update'))

	elif action == 'speedtestRealDebrid':
		from lib.modules import speedtest
		speedtest.SpeedTesterRealDebrid().show(parameters.get('update'))

	elif action == 'speedtestEasyNews':
		from lib.modules import speedtest
		speedtest.SpeedTesterEasyNews().show(parameters.get('update'))

	elif action == 'speedtestComparison':
		from lib.modules import speedtest
		speedtest.SpeedTester.comparison()

####################################################
# LOTTERY
####################################################

elif action.startswith('lottery'):

	if action == 'lotteryVoucher':
		from lib.modules import api
		api.Api.lotteryVoucher()

####################################################
# INFORMER
####################################################

elif action.startswith('informer'):

	if action == 'informerDialog':
		from lib.informers import Informer
		imdb = parameters.get('imdb')
		tmdb = parameters.get('tmdb')
		tvdb = parameters.get('tvdb')
		title = parameters.get('title')
		year = parameters.get('year')
		if year: year = int(year)
		season = parameters.get('season')
		if not season is None: season = int(season)
		episode = parameters.get('episode')
		if not episode is None: episode = int(episode)
		Informer.show(type = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year, season = season, episode = episode, metadata = metadata)

	elif action == 'informerNavigator':
		from lib.informers import Informer
		id = parameters.get('id')
		if id: Informer.instance(id).navigator()
		else: Informer.navigators()

	elif action == 'informerSettings':
		from lib.informers import Informer
		id = parameters.get('id')
		Informer.instance(id).settings()

	elif action == 'informerInstall':
		from lib.informers import Informer
		id = parameters.get('id')
		refresh = tools.Converter.boolean(parameters.get('refresh'))
		Informer.instance(id).enable(refresh = refresh)

	elif action == 'informerLaunch':
		from lib.informers import Informer
		id = parameters.get('id')
		Informer.instance(id).launch()

####################################################
# HISTORY
####################################################

elif action.startswith('history'):

	if action == 'history':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).history()

	elif action == 'historyType':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).historyType()

	elif action == 'historyStream':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).historyStream()

####################################################
# FANART
####################################################

elif action.startswith('fanart'):

	if action == 'fanartAuthentication':
		from lib.modules.account import Fanart
		settings = tools.Converter.boolean(parameters.get('settings'))
		Fanart().authenticate(settings = settings)

####################################################
# IMDB
####################################################

elif action.startswith('imdb'):

	if action == 'imdbMovies':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).imdbMovies()

	elif action == 'imdbTv':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).imdbTv()

	elif action == 'imdbExport':
		from lib.modules import trakt as Trakt
		Trakt.imdbImport()

	elif action == 'imdbAuthentication':
		from lib.modules.account import Imdb
		settings = tools.Converter.boolean(parameters.get('settings'))
		Imdb().authenticate(settings = settings)

####################################################
# TVDB
####################################################

elif action.startswith('tvdb'):

	if action == 'tvdbAuthentication':
		from lib.modules.account import Tvdb
		settings = tools.Converter.boolean(parameters.get('settings'))
		Tvdb().authenticate(settings = settings)

####################################################
# TMDB
####################################################

elif action.startswith('tmdb'):

	if action == 'tmdbAuthentication':
		from lib.modules.account import Tmdb
		settings = tools.Converter.boolean(parameters.get('settings'))
		Tmdb().authenticate(settings = settings)

####################################################
# TRAKT
####################################################

elif action.startswith('trakt'):

	if action == 'traktMovies':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).traktMovies()

	elif action == 'traktMoviesLists':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).traktMoviesLists()

	elif action == 'traktTv':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).traktTv()

	elif action == 'traktTvLists':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).traktTvLists()

	elif action == 'traktManager':
		from lib.modules import trakt as Trakt
		imdb = parameters.get('imdb')
		tmdb = parameters.get('tmdb')
		tvdb = parameters.get('tvdb')
		trakt = parameters.get('trakt')
		season = parameters.get('season')
		if not season is None: season = int(season)
		episode = parameters.get('episode')
		if not episode is None: episode = int(episode)
		Trakt.manager(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

	elif action == 'traktAuthentication':
		from lib.modules import trakt as Trakt
		settings = tools.Converter.boolean(parameters.get('settings'))
		Trakt.authentication(settings = settings)

	elif action == 'traktListAdd':
		from lib.modules import trakt as Trakt
		Trakt.listAdd()

	elif action == 'traktImport':
		from lib.modules import trakt as Trakt
		Trakt.imdbImport()

####################################################
# OPENSUBTITLES
####################################################

elif action.startswith('opensubtitles'):

	if action == 'opensubtitlesAuthentication':
		from lib.modules.account import Opensubtitles
		settings = tools.Converter.boolean(parameters.get('settings'))
		Opensubtitles().authenticate(settings = settings)

####################################################
# NETWORK
####################################################

elif action.startswith('network'):

	if action == 'networkNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).networkNavigator()

	elif action == 'networkInformation':
		from lib.modules.network import Geolocator
		Geolocator.dialog()

	elif action == 'networkAuthentication':
		from lib.modules.account import Geolocation
		type = parameters.get('type')
		settings = tools.Converter.boolean(parameters.get('settings'))
		Geolocation(type = type).authenticate(settings = settings)

####################################################
# VPN
####################################################

elif action.startswith('vpn'):

	if action == 'vpnNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).vpnNavigator()

	elif action == 'vpnVerify':
		from lib.modules import vpn
		settings = tools.Converter.boolean(parameters.get('settings'))
		vpn.Vpn.verification(settings = settings)

	elif action == 'vpnConfigure':
		from lib.modules.vpn import Vpn
		settings = tools.Converter.boolean(parameters.get('settings'))
		Vpn.configuration(settings = settings)

	elif action == 'vpnSettings':
		external = tools.Converter.boolean(parameters.get('external'))
		if external:
			tools.VpnManager.settings()
		else:
			from lib.modules.vpn import Vpn
			Vpn.settingsLaunch()

	elif action == 'vpnChange':
		profile = parameters.get('profile')
		dialog = tools.Converter.boolean(parameters.get('dialog'))
		tools.VpnManager.change(profile = profile, dialog = dialog)

	elif action == 'vpnDisconnect':
		tools.VpnManager.disconnect()

	elif action == 'vpnStatus':
		tools.VpnManager.status()

####################################################
# EXTENSIONS
####################################################

elif action.startswith('extensions'):

	if action == 'extensions':
		id = parameters.get('id')
		tools.Extension.dialog(id = id)

	elif action == 'extensionsHelp':
		tools.Extension.help(full = True)

	elif action == 'extensionsNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).extensionsNavigator()

	elif action == 'extensionsAvailableNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).extensionsAvailableNavigator()

	elif action == 'extensionsInstalledNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).extensionsInstalledNavigator()

####################################################
# THEME
####################################################

elif action.startswith('theme'):

	if action == 'themeSkinSelect':
		from lib.modules.theme import Theme
		Theme.skinSettings()

	elif action == 'themeIconSelect':
		from lib.modules import interface
		interface.Icon.settings()

####################################################
# BACKUP
####################################################

elif action.startswith('backup'):

	if action == 'backupNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).backupNavigator()

	elif action == 'backupAutomatic':
		tools.Backup.automatic()

	elif action == 'backupImport':
		tools.Backup.manualImport()

	elif action == 'backupExport':
		tools.Backup.manualExport()

####################################################
# SETTINGS
####################################################

elif action.startswith('settings'):

	if action == 'settingsNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).settingsNavigator()

	elif action == 'settingsAdvanced':
		id = parameters.get('id')
		tools.Settings.launch(id = id)

	elif action == 'settingsWizard':
		from lib.modules import window
		window.WindowWizard.show()

	elif action == 'settingsOptimization':
		from lib.providers.core.manager import Manager
		Manager.optimizeShow()

	elif action == 'settingsBackground':
		id = parameters.get('id')
		addon = parameters.get('addon')
		category = parameters.get('category')
		tools.Settings.launch(id = id, addon = addon, category = category, background = False)

	elif action == 'settingsExternal':
		tools.Settings.externalSave(parameters)

	elif action == 'settingsLanguage':
		id = parameters.get('id')
		title = parameters.get('title')
		if title:
			try: title = int(title)
			except: pass
		none = tools.Converter.boolean(parameters.get('none'))
		automatic = tools.Converter.boolean(parameters.get('automatic'))
		set = parameters.get('set')
		tools.Language.settingsSelect(id = id, title = title, none = none, automatic = automatic, set = set)

	elif action == 'settingsCountry':
		id = parameters.get('id')
		title = parameters.get('title')
		if title:
			try: title = int(title)
			except: pass
		none = tools.Converter.boolean(parameters.get('none'))
		automatic = tools.Converter.boolean(parameters.get('automatic'))
		tools.Country.settingsSelect(id = id, title = title, none = none, automatic = automatic)

	elif action == 'settingsLayout':
		from lib.modules.interface import Loader
		Loader.show() # Show here already for slow devices.
		from lib.modules.stream import Layout
		Layout().show(settings = True)

	elif action == 'settingsFilters':
		from lib.modules.interface import Loader
		Loader.show() # Show here already for slow devices.
		from lib.modules.stream import Settings
		mode = parameters.get('mode')
		Settings(mode = mode).show()

	elif action == 'settingsTermination':
		from lib.modules.interface import Loader
		Loader.show() # Show here already for slow devices.
		from lib.modules.stream import Termination
		settings = tools.Converter.boolean(parameters.get('settings'))
		Termination().show(settings = settings)

	elif action == 'settingsCustom':
		id = parameters.get('id')
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Settings.custom(id = id, settings = settings)

	elif action == 'settingsBuffer':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Buffer.settings(settings = settings)

	elif action == 'settingsTimeout':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Timeout.settings(settings = settings)

	elif action == 'settingsPlaylist':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Playlist.settings(settings = settings)

	elif action == 'settingsView':
		from lib.modules.view import View
		media = parameters.get('media')
		content = parameters.get('content')
		previous = parameters.get('previous')
		settings = tools.Converter.boolean(parameters.get('settings'))
		View.settings(media = media, content = content, previous = previous, settings = settings)

	elif action == 'settingsMetadata':
		from lib.meta.tools import MetaTools
		settings = tools.Converter.boolean(parameters.get('settings'))
		MetaTools.settingsDetailShow(settings = settings)

	elif action == 'settingsImage':
		from lib.meta.image import MetaImage
		mode = parameters.get('mode')
		media = parameters.get('media')
		settings = tools.Converter.boolean(parameters.get('settings'))
		MetaImage.settingsSelect(mode = mode, media = media, settings = settings)

	elif action == 'settingsIcon':
		from lib.modules.interface import Font
		settings = tools.Converter.boolean(parameters.get('settings'))
		Font.iconSettings(settings = settings)

	elif action == 'settingsInterpreter':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Settings.interpreterSelect(settings = settings)

####################################################
# DONATIONS
####################################################

elif action.startswith('donations'):

	if action == 'donations':
		from lib.modules import tools
		type = parameters.get('type')
		tools.Donations.show(type = type)

####################################################
# SHORTCUTS
####################################################

elif action.startswith('shortcuts'):

	if action == 'shortcutsShow':
		from lib.modules import shortcuts
		location = parameters.get('location')
		id = parameters.get('id')
		link = parameters.get('link')
		name = parameters.get('name')
		create = tools.Converter.boolean(parameters.get('create'))
		delete = tools.Converter.boolean(parameters.get('delete'))
		shortcuts.Shortcuts().show(location = location, id = id, link = link, name = name, create = create, delete = delete)

	elif action == 'shortcutsNavigator':
		from lib.indexers.navigator import Navigator
		location = parameters.get('location')
		Navigator(media = media, kids = kids, menu = menu).shortcutsNavigator(location = location)

	elif action == 'shortcutsOpen':
		from lib.modules import shortcuts
		location = parameters.get('location')
		id = parameters.get('id')
		shortcuts.Shortcuts().open(location = location, id = id)

####################################################
# LIBRARY
####################################################

elif action.startswith('library'):

	if action == 'libraryNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).libraryNavigator()

	elif action == 'libraryLocalNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).libraryLocalNavigator()

	elif action == 'libraryBrowseNavigator':
		from lib.indexers.navigator import Navigator
		error = tools.Converter.boolean(parameters.get('error'))
		Navigator(media = media, kids = kids, menu = menu).libraryBrowseNavigator(error = error)

	elif action == 'libraryAdd':
		from lib.modules import library
		precheck = tools.Converter.boolean(parameters.get('precheck'))
		metadata = parameters.get('metadata')
		link = parameters.get('link')
		imdb = parameters.get('imdb')
		tmdb = parameters.get('tmdb')
		tvdb = parameters.get('tvdb')
		title = parameters.get('title')
		if title: title = tools.Converter.quoteFrom(title)
		year = parameters.get('year')
		if year: year = int(year)
		season = parameters.get('season')
		if not season is None: season = int(season)
		episode = parameters.get('episode')
		if not episode is None: episode = int(episode)
		library.Library(media = media, kids = kids).add(link = link, title = title, year = year, season = season, episode = episode, imdb = imdb, tmdb = tmdb, tvdb = tvdb, metadata = metadata, precheck = precheck)

	elif action == 'libraryResolve':
		from lib.modules import library
		metadata = parameters.get('location')
		title = parameters.get('title')
		if title: title = tools.Converter.quoteFrom(title)
		year = parameters.get('year')
		if year: year = int(year)
		season = parameters.get('season')
		if not season is None: season = int(season)
		episode = parameters.get('episode')
		if not episode is None: episode = int(episode)
		library.Library(media = media, kids = kids).resolve(title = title, year = year, season = season, episode = episode)

	elif action == 'libraryRefresh':
		from lib.modules import library
		library.Library(media = media).refresh()

	elif action == 'libraryUpdate':
		from lib.modules import library
		force = tools.Converter.boolean(parameters.get('force'))
		library.Library.update(force = force, media = media)

	elif action == 'libraryClean':
		from lib.modules import library
		library.Library(media = media).clean()

	elif action == 'libraryService':
		from lib.modules import library
		library.Library.service(background = False)

	elif action == 'libraryLocal':
		from lib.modules import library
		library.Library(media = media).local()

	elif action == 'librarySettings':
		from lib.modules import library
		library.Library.settings()

####################################################
# SUPPORT
####################################################

elif action.startswith('support'):

	if action == 'supportBugs':
		from lib.modules import support
		support.Support.bugs()

	elif action == 'supportNavigator':
		from lib.modules import support
		support.Support.navigator()

	elif action == 'supportCategories':
		from lib.modules import support
		support.Support.categories()

	elif action == 'supportReport':
		from lib.modules import support
		support.Support.report()

	elif action == 'supportQuestions':
		from lib.modules import support
		support.Support.questions(int(parameters.get('id')))

	elif action == 'supportQuestion':
		from lib.modules import support
		support.Support.question(int(parameters.get('id')))

####################################################
# ORION
####################################################

elif action.startswith('orion'):

	if action == 'orionNavigator':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).orionNavigator()

	elif action == 'orionInitialize':
		try:
			from lib.modules import orionoid
			settings = parameters.get('settings')
			if settings and not '.' in settings: settings = tools.Converter.boolean(settings)
			orionoid.Orionoid().initialize(settings = settings)
		except: pass

	elif action == 'orionSettings':
		try:
			from lib.modules import orionoid
			id = parameters.get('id')
			settings = tools.Converter.boolean(parameters.get('settings'))
			orionoid.Orionoid.addonSettings(id = id, settings = settings)
		except: pass

	elif action == 'orionFilters':
		try:
			from lib.modules import orionoid
			settings = tools.Converter.boolean(parameters.get('settings'))
			orionoid.Orionoid().settingsFilters(settings = settings)
		except: pass

	elif action == 'orionLaunch':
		try:
			from lib.modules import orionoid
			orionoid.Orionoid().addonLaunch()
		except: pass

	elif action == 'orionInstall':
		try:
			from lib.modules import orionoid
			settings = tools.Converter.boolean(parameters.get('settings'))
			orionoid.Orionoid.addonEnable(refresh = True, settings = settings)
		except: pass

	elif action == 'orionUninstall':
		try:
			from lib.modules import orionoid
			orionoid.Orionoid.uninstall()
		except: pass

	elif action == 'orionWebsite':
		try:
			from lib.modules import orionoid
			orionoid.Orionoid().addonWebsite(open = True)
		except: pass

	elif action == 'orionAuthenticate':
		try:
			from lib.modules import orionoid
			settings = tools.Converter.boolean(parameters.get('settings'))
			orionoid.Orionoid().accountAuthenticate(settings = settings)
		except: pass

	elif action == 'orionAccount':
		try:
			from lib.modules import orionoid
			orionoid.Orionoid().accountDialog()
		except: pass

	elif action == 'orionPromotion':
		try:
			from lib.modules import orionoid
			settings = tools.Converter.boolean(parameters.get('settings'))
			orionoid.Orionoid().accountPromotion(settings = settings)
		except: pass

	elif action == 'orionVoteUp':
		try:
			from lib.modules import orionoid
			notification = tools.Converter.boolean(parameters.get('notification'), none = True)
			orionoid.Orionoid().streamVote(idItem = parameters.get('idItem'), idStream = parameters.get('idStream'), vote = orionoid.Orionoid.VoteUp, notification = True if notification is None else notification)
		except: pass

	elif action == 'orionVoteDown':
		try:
			from lib.modules import orionoid
			notification = tools.Converter.boolean(parameters.get('notification'), none = True)
			orionoid.Orionoid().streamVote(idItem = parameters.get('idItem'), idStream = parameters.get('idStream'), vote = orionoid.Orionoid.VoteDown, notification = True if notification is None else notification)
		except: pass

	elif action == 'orionRemove':
		try:
			from lib.modules import orionoid
			notification = tools.Converter.boolean(parameters.get('notification'), none = True)
			orionoid.Orionoid().streamRemove(idItem = parameters.get('idItem'), idStream = parameters.get('idStream'), notification = True if notification is None else notification)
		except: pass

####################################################
# SCRAPE
####################################################

elif action.startswith('scrape'):

	if action == 'scrape':
		# Sometimes when using the Kore remote app and clicking on a movie/episode to start a scrape, the user might accidentally click twice, which starts the scraping process twice.
		# This is not a huge issue for other endpoints, but the scrape endpoint starts many threads and uses many resources, and should be avoided.
		# This is not a perfect solution, since both processes might call windowPropertyGet() before the other process is able to call windowPropertySet().
		# If the double scrape still happens in the future, we need a more advanced solution.
		# One way would be to rename this endpoint to “scrapeNow” and create another endpoint “scrape”.
		# “scrape” checks and sets the global property, and if not set, initiates the actual endpoint “scrapeNow” which clears the global property after scraping is done.
		# “scrapeNow” also checks the global property again, just as a second safety.
		# This would create a greater time gap between processes and would reduce the chance of both processes executing at the same time. However, it also requires two Python invokers, which slows down the starting of the scrape process.
		# Update: Hitting the ENTER key twice shortly after each other calls this endpoint twice, but in all cases only one scrape was done. So it seems to work.

		property = 'GaiaScrapeBusy'
		id = tools.System.windowPropertyGet(property)
		time = tools.Time.timestamp()

		# In case a previous scrape did not clear the property, allow a new scrape after 10 seconds.
		if not id or (time - int(id) > 10):
			try:
				tools.System.windowPropertySet(property, str(time))

				try: silent = bool(parameters.get('silent'))
				except: silent = False
				try: binge = int(parameters.get('binge'))
				except: binge = None

				from lib.modules import interface
				if not silent and not binge: interface.Loader.show()

				from lib.modules import core
				from lib.modules import video

				# Already show here, since getConstants can take long when retrieving debrid service list.
				if (not video.Trailer.cinemaEnabled() or tools.Settings.getBoolean('playback.autoplay.enabled')) and (not binge == tools.Binge.ModeBackground or binge == tools.Binge.ModeContinue): interface.Loader.show()

				imdb = parameters.get('imdb')
				tmdb = parameters.get('tmdb')
				tvdb = parameters.get('tvdb')

				title = parameters.get('title')
				tvshowtitle = parameters.get('tvshowtitle')
				year = parameters.get('year')
				if year: year = int(year)
				premiered = parameters.get('premiered')

				season = parameters.get('season')
				if not season is None: season = int(season)
				episode = parameters.get('episode')
				if not episode is None: episode = int(episode)

				library = tools.Converter.boolean(parameters.get('library'))
				autoplay = tools.Converter.boolean(parameters.get('autoplay'), none = True)
				autopack = parameters.get('autopack')
				preset = parameters.get('preset')
				cache = tools.Converter.boolean(parameters.get('cache'), none = True)
				try: pack = tools.Converter.dictionary(parameters.get('pack'))
				except: pack = None
				items = parameters.get('items')

				core.Core(media = media, kids = kids, silent = silent).scrape(title = title, tvshowtitle = tvshowtitle, year = year, imdb = imdb, tmdb = tmdb, tvdb = tvdb, season = season, episode = episode, premiered = premiered, metadata = metadata, autopack = autopack, autoplay = autoplay, library = library, preset = preset, binge = binge, cache = cache, pack = pack, items = items)
			except: tools.Logger.error()
			tools.System.windowPropertyClear(property)

	elif action == 'scrapeAgain':
		from lib.modules import core
		link = parameters.get('link')
		core.Core(media = media, kids = kids).scrapeAgain(link = link)

	elif action == 'scrapeManual':
		from lib.modules import core
		link = parameters.get('link')
		core.Core(media = media, kids = kids).scrapeManual(link = link)

	elif action == 'scrapeAutomatic':
		from lib.modules import core
		link = parameters.get('link')
		core.Core(media = media, kids = kids).scrapeAutomatic(link = link)

	elif action == 'scrapePresetManual':
		from lib.modules import core
		link = parameters.get('link')
		core.Core(media = media, kids = kids).scrapePresetManual(link = link)

	elif action == 'scrapePresetAutomatic':
		from lib.modules import core
		link = parameters.get('link')
		core.Core(media = media, kids = kids).scrapePresetAutomatic(link = link)

	elif action == 'scrapeSingle':
		from lib.modules import core
		link = parameters.get('link')
		core.Core(media = media, kids = kids).scrapeSingle(link = link)

	elif action == 'scrapeBinge':
		from lib.modules import core
		link = parameters.get('link')
		core.Core(media = media, kids = kids).scrapeBinge(link = link)

	elif action == 'scrapeExact':
		from lib.modules import core
		terms = parameters.get('terms')
		core.Core(media = media, kids = kids).scrapeExact(terms)

	elif action == 'scrapeOptimize':
		from lib.providers.core.manager import Manager
		settings = tools.Converter.boolean(parameters.get('settings'))
		Manager.optimizeScrape(settings = settings)

####################################################
# STREAMS
####################################################

elif action.startswith('streams'):

	if action == 'streamsShow':
		from lib.modules import core
		from lib.modules import interface
		autoplay = tools.Converter.boolean(parameters.get('autoplay'))
		if autoplay: interface.Loader.show() # Only for autoplay, since showing the directory has its own loader.
		direct = tools.Converter.boolean(parameters.get('direct'))
		filter = tools.Converter.boolean(parameters.get('filterx'))
		library = tools.Converter.boolean(parameters.get('library'))
		initial = tools.Converter.boolean(parameters.get('initial'))
		new = tools.Converter.boolean(parameters.get('new'))
		add = tools.Converter.boolean(parameters.get('add'))
		process = tools.Converter.boolean(parameters.get('process'))
		try: binge = int(parameters.get('binge'))
		except: binge = None
		core.Core(media = media, kids = kids).showStreams(direct = direct, filter = filter, autoplay = autoplay, library = library, initial = initial, new = new, add = add, process = process, binge = binge)

	elif action == 'streamsFilters':
		from lib.modules.core import Core
		Core(media = media, kids = kids).filterStreams()

	elif action == 'streamsInformation':
		from lib.modules.stream import Stream
		Stream(data = source['stream']).dialog()

	elif action == 'streamsVideo':
		from lib.modules import video

		link = parameters.get('link')

		imdb = parameters.get('imdb')
		tmdb = parameters.get('tmdb')
		tvdb = parameters.get('tvdb')

		title = parameters.get('title')
		year = parameters.get('year')
		if year: year = int(year)
		season = parameters.get('season')
		if not season is None: season = int(season)

		mode = parameters.get('video')
		selection = parameters.get('selection')
		if not selection is None: selection = int(selection)

		getattr(video, mode.capitalize())(media = media, kids = kids).play(imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year, season = season, link = link, selection = selection)

####################################################
# CONTEXT
####################################################

elif action.startswith('context'):

	if action == 'contextShow':
		from lib.modules.interface import Loader
		Loader.show() # It can take some time to open the context menu on the first use after starting Gaia.
		from lib.modules.interface import Context
		menu = Context()
		menu.dataFrom(parameters.get('context'))
		menu.show()

####################################################
# COPY
####################################################

elif action.startswith('copy'):

	if action == 'copy':
		from lib.modules.interface import Loader
		try:
			Loader.show() # Needs some time to load. Show busy.
			from lib.modules.window import WindowQr

			link = parameters.get('link')
			name = parameters.get('name')
			hash = parameters.get('hash')
			code = parameters.get('code')
			wallet = parameters.get('wallet')
			payment = parameters.get('payment')
			symbol = parameters.get('symbol')

			WindowQr.show(link = link, name = name, hash = hash, code = code, wallet = wallet, payment = payment, symbol = symbol)
		except: tools.Logger.error()

####################################################
# FILE
####################################################

elif action.startswith('file'):

	if action == 'fileLink':
		from lib.modules.interface import Loader
		try:
			Loader.show() # Needs some time to load. Show busy.
			from lib.modules.network import Networker, Resolver
			from lib.modules.window import WindowQr

			mode = parameters.get('mode')
			if not mode: mode = 'original'

			if 'link' in parameters:
				link = parameters.get('link')
			elif source:
				from lib.modules.stream import Stream
				stream = Stream.load(data = source['stream'])
				if mode == 'original':
					link = stream.linkPrimary()
				elif mode == 'resolved':
					link = stream.linkProvider()
					if not link: link = Resolver.resolve(source = source, clean = True, internal = False, cloud = False, mode = Resolver.ModeProvider)
				elif mode == 'stream':
					link = stream.linkStream()
					if not link:
						link = Resolver.resolve(source = source, clean = True, internal = False, cloud = False, mode = Resolver.ModeService)
						if not link: link = Stream.load(data = source['stream']).linkResolved() # Provider-resolved link added by Resolver.resolve() and therefore reload.
				if not link: link = stream.linkPrimary() # Sometimes resolving does not work. Eg: 404 errors.

			link = Networker.linkClean(link)
			WindowQr.show(link = link)
		except: tools.Logger.error()

	elif action == 'fileName':
		from lib.modules.interface import Loader
		try:
			Loader.show() # Needs some time to load. Show busy.
			from lib.modules.stream import Stream
			from lib.modules.window import WindowQr
			if 'name' in parameters: name = parameters.get('name')
			elif source: name = Stream.load(data = source['stream']).stream.fileName()
			WindowQr.show(name = name)
		except: tools.Logger.error()

	elif action == 'fileHash':
		from lib.modules.interface import Loader
		try:
			Loader.show() # Needs some time to load. Show busy.
			from lib.modules.stream import Stream
			from lib.modules.window import WindowQr
			if 'hash' in parameters: hash = parameters.get('hash')
			elif source: hash = Stream.load(data = source['stream']).stream.hash()
			WindowQr.show(hash = hash)
		except: tools.Logger.error()

	elif action == 'fileAdd':
		from lib.modules.interface import Loader
		Loader.show()
		from lib.modules import core
		link = parameters.get('link')
		core.Core(media = media, kids = kids).addLink(link = link, metadata = metadata)

####################################################
# CLOUDFLARE
####################################################

elif action.startswith('cloudflare'):

	if action == 'cloudflareEngine':
		from lib.modules.cloudflare import Cloudflare
		settings = tools.Converter.boolean(parameters.get('settings'))
		Cloudflare.settingsEngine(settings = settings)

	elif action == 'cloudflareVerify':
		from lib.modules.cloudflare import Cloudflare
		settings = tools.Converter.boolean(parameters.get('settings'))
		Cloudflare().verify(settings = settings, notification = True)

####################################################
# NAVIGATOR
####################################################

elif action.startswith('navigator'):

	if action == 'navigatorTools':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).tools()

	elif action == 'navigatorFavourites':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).favourites()

	elif action == 'navigatorArrivals':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).arrivals()

	elif action == 'navigatorPreload':
		from lib.indexers.navigator import Navigator
		Navigator(media = media, kids = kids, menu = menu).preload()

####################################################
# DUMMY
####################################################

elif action.startswith('dummy'):

	if action == 'dummy':
		tools.System.pluginResolvedSet(success = False)

####################################################
# DEBUG
####################################################

elif action.startswith('debug'):

	if action == 'debug':
		from lib.modules.tester import Tester
		Tester.test()

####################################################
# EXECUTION
####################################################

if developer: tools.Logger.log('EXECUTION FINISHING [Action: %s | Duration: %.3f secs]' % (action, timer.time() - timeStart))

try:
	from lib.modules.vpn import Vpn
	Vpn.killStop()

	from lib.modules.concurrency import Pool
	Pool.join()

	# Do this at the end, so that timestamps of reloaded requests can be updated and won't be deleted.
	# Do this after the thread pool joining, since the cache might still have threads executing (refreshing data in the background).
	from lib.modules.cache import Cache
	Cache.instance().limitClear(log = developer)

	# Reset global variables in case the invoker is reused.
	tools.Settings.interpreterReset()
except: tools.Logger.error()

if developer: tools.Logger.log('EXECUTION FINISHED [Action: %s | Duration: %.3f secs]' % (action, timer.time() - timeStart))
