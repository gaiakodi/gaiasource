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

from lib.modules.tools import Media, Selection, Kids, System, Tools, Settings, Logger, Converter
from lib.modules.interface import Dialog, Icon, Context, Directory, Format, Translation, Loader
from lib.modules.shortcuts import Shortcuts

class Navigator(object):

	def __init__(self, media = Media.TypeNone, kids = Selection.TypeUndefined):
		self.mMedia = media
		self.mKids = kids
		self.mContext = Context.enabled()

		# Give a content type, otherwise descriptions/overviews/plots are not show in the interface.
		# Kodi only allows specific views for specific content types.
		# Instead of fixing the content type, let users choose in the settings to allow for a wider selection of views.
		self.mDirectory = Directory(content = Directory.ContentSettings, lock = False)

	def parameterize(self, action, media = None, kids = None, lite = None):
		if media is None: media = self.mMedia
		if not media is None: action += '&media=%s' % media
		if kids is None: kids = self.mKids
		if not kids is None: action += '&kids=%d' % kids
		if not lite is None: action += '&lite=%d' % lite
		return action

	def kidsOnly(self):
		return self.mKids == Selection.TypeInclude

	def addDirectoryItem(self, name, query, icon, iconDefault = None, isAction = True, isFolder = True, iconSpecial = Icon.SpecialNone, library = None, description = None):
		name = Translation.string(name)
		if description: description = Translation.string(description)
		description = System.menuDescription(name = name) + (('\n\n' + description) if description else '')

		link = System.command(query = 'action=' + query) if isAction else query
		link += '&' + System.menuParameter(name = name)

		if Tools.isArray(library):
			media = library[1]
			library = library[0]
		else:
			media = self.mMedia

		if self.mContext: context = Context(mode = Context.ModeGeneric, media = media, kids = self.mKids, link = link, shortcutCreate = True, shortcutLabel = name, library = library).menu(full = True)
		else: context = None

		self.mDirectory.add(label = name, description = description, link = link, context = context, icon = icon, iconDefault = iconDefault, iconSpecial = iconSpecial, fanart = True, folder = isFolder)

	def endDirectory(self, cache = True):
		self.mDirectory.finish(cache = cache)

	def root(self):
		if self.kidsRedirect(): return

		from lib.modules.tools import Promotions
		promotions = Promotions.enabled()
		if promotions: self.addDirectoryItem(name = 35442, query = 'promotionsNavigator', icon = 'promotion.png', iconDefault = 'DefaultAddonProgram.png')

		if Settings.getBoolean('navigation.menu.shortcut'): self.shortcutsItems(location = Shortcuts.LocationMain)

		if Settings.getBoolean('navigation.menu.movie'): self.addDirectoryItem(name = 32001, query = self.parameterize('movies', media = Media.TypeMovie), icon = 'movies.png', iconDefault = 'DefaultMovies.png')
		if Settings.getBoolean('navigation.menu.show'): self.addDirectoryItem(name = 32002, query = self.parameterize('shows', media = Media.TypeShow), icon = 'shows.png', iconDefault = 'DefaultTVShows.png')
		if Settings.getBoolean('navigation.menu.documentary'): self.addDirectoryItem(name = 33470, query = self.parameterize('documentaries', media = Media.TypeDocumentary), icon = 'documentaries.png', iconDefault = 'DefaultVideo.png')
		if Settings.getBoolean('navigation.menu.short'): self.addDirectoryItem(name = 33471, query = self.parameterize('shorts', media = Media.TypeShort), icon = 'shorts.png', iconDefault = 'DefaultVideo.png')
		if Settings.getBoolean('navigation.menu.kid'): self.addDirectoryItem(name = 33429, query = self.parameterize('kids', kids = Selection.TypeInclude), icon = 'kids.png', iconDefault = 'DefaultVideo.png')

		if Settings.getBoolean('navigation.menu.favourite'): self.addDirectoryItem(name = 33000, query = 'navigatorFavourites', icon = 'favourites.png', iconDefault = 'DefaultFavourite.png')
		if Settings.getBoolean('navigation.menu.arrival'): self.addDirectoryItem(name = 33490, query = self.parameterize('navigatorArrivals'), icon = 'new.png', iconDefault = 'DefaultAddSource.png')
		if Settings.getBoolean('navigation.menu.search'): self.addDirectoryItem(name = 32010, query = 'search', icon = 'search.png', iconDefault = 'DefaultAddonsSearch.png')

		self.addDirectoryItem(name = 32008, query = 'navigatorTools', icon = 'tools.png', iconDefault = 'DefaultAddonProgram.png')

		# Do not cache to hide the promotions entry or parental locking.
		self.endDirectory(cache = not promotions and not Kids.enabled())

	def movies(self, lite = False):
		if Settings.getBoolean('navigation.menu.shortcut'):
			if self.mMedia == Media.TypeDocumentary: self.shortcutsItems(location = Shortcuts.LocationDocumentaries)
			elif self.mMedia == Media.TypeShort: self.shortcutsItems(location = Shortcuts.LocationShorts)
			else: self.shortcutsItems(location = Shortcuts.LocationMovies)

		if not self.kidsOnly() and lite == False: self.addDirectoryItem(name = 33000, query = self.parameterize('moviesFavourites', lite = True), icon = 'favourites.png', iconDefault = 'DefaultFavourite.png')

		self.addDirectoryItem(name = 33490, query = self.parameterize('moviesArrivals'), icon = 'new.png', iconDefault = 'DefaultAddSource.png', library = 'arrivals')
		self.addDirectoryItem(name = 33001, query = self.parameterize('moviesCategories'), icon = 'categories.png', iconDefault = 'DefaultTags.png')
		self.addDirectoryItem(name = 33002, query = self.parameterize('moviesLists'), icon = 'lists.png', iconDefault = 'DefaultVideoPlaylists.png')
		if self.mMedia == Media.TypeMovie: self.addDirectoryItem(name = 33527, query = self.parameterize('sets'), icon = 'sets.png', iconDefault = 'DefaultVideoPlaylists.png')
		self.addDirectoryItem(name = 32013, query = self.parameterize('moviesPeople'), icon = 'people.png', iconDefault = 'DefaultActor.png')
		if lite is False: self.addDirectoryItem(name = 32010, query = self.parameterize('moviesSearches'), icon = 'search.png', iconDefault = 'DefaultAddonsSearch.png')
		self.endDirectory()

	def moviesFavourites(self, lite = False):
		from lib.modules.library import Library
		if Settings.getBoolean('navigation.menu.shortcut'):
			if self.mMedia == Media.TypeDocumentary: self.shortcutsItems(location = Shortcuts.LocationDocumentariesFavourites)
			elif self.mMedia == Media.TypeShort: self.shortcutsItems(location = Shortcuts.LocationShortsFavourites)
			else: self.shortcutsItems(location = Shortcuts.LocationMoviesFavourites)
		self.addDirectoryItem(32315, self.parameterize('traktMovies'), 'trakt.png', 'DefaultAddonWebSkin.png')
		self.addDirectoryItem(32034, self.parameterize('imdbMovies'), 'imdb.png', 'DefaultAddonWebSkin.png')
		self.addDirectoryItem(32036, self.parameterize('history'), 'history.png', 'DefaultYear.png')
		if not self.kidsOnly() and Library.enabled(): self.addDirectoryItem(35170, self.parameterize('libraryLocal'), 'library.png', 'DefaultAddonLibrary.png', isAction = True, isFolder = False)
		if lite == False: self.addDirectoryItem(32031, self.parameterize('movies', lite = True), 'discover.png', 'DefaultMovies.png')
		self.endDirectory()

	def history(self):
		self.addDirectoryItem(33481, self.parameterize('historyStream', media = self.mMedia), 'historystreams.png', 'DefaultYear.png', isAction = True, isFolder = False)
		if self.mMedia in [None, Media.TypeMovie]: self.addDirectoryItem(32001, self.parameterize('historyType', media = Media.TypeMovie), 'historymovies.png', 'DefaultYear.png')
		if self.mMedia in [None, Media.TypeDocumentary]: self.addDirectoryItem(33470, self.parameterize('historyType', media = Media.TypeDocumentary), 'historydocumentaries.png', 'DefaultYear.png')
		if self.mMedia in [None, Media.TypeShort]: self.addDirectoryItem(33471, self.parameterize('historyType', media = Media.TypeShort), 'historyshorts.png', 'DefaultYear.png')
		if self.mMedia in [None, Media.TypeShow, Media.TypeSeason, Media.TypeEpisode]:
			self.addDirectoryItem(32002, self.parameterize('historyType', media = Media.TypeShow), 'historyshows.png', 'DefaultYear.png')
			self.addDirectoryItem(32054, self.parameterize('historyType', media = Media.TypeSeason), 'historyshows.png', 'DefaultYear.png')
			self.addDirectoryItem(32326, self.parameterize('historyType', media = Media.TypeEpisode), 'historyshows.png', 'DefaultYear.png')
		self.endDirectory()

	def historyType(self):
		from lib.modules.history import History
		from lib.modules.tools import Converter

		def _historyFilter(histories, season = False, episode = False):
			items = []
			ids = []

			values = ['imdb', 'tmdb', 'tvdb', 'trakt', 'title', 'tvshowtitle', 'year']
			if season: values.append('season')
			if episode: values.append('episode')

			for history in histories:
				metadata = Converter.dictionary(history[4])

				try: id = metadata['tvshowtitle']
				except:
					try: id = metadata['title']
					except: id = '-'
				for i in ['imdb', 'tmdb', 'tvdb', 'trakt']:
					try:
						id = str(metadata[i])
						if id: break
					except: pass

				if season and 'season' in metadata and not metadata['season'] is None: id += '_' + str(metadata['season'])
				if episode and 'episode' in metadata and not metadata['episode'] is None: id += '_' + str(metadata['episode'])

				if not id in ids:
					item = {}
					for value in values:
						try: item[value] = metadata[value]
						except: pass
					if item:
						items.append(item)
						ids.append(id)

			items = items[:100] # Only show the last 100 items, otherwise the list can grow too large and slow down menu loading.
			return items

		histories = History().retrieve(media = Media.TypeShow if Media.typeTelevision(self.mMedia) else self.mMedia, kids = self.mKids)

		if self.mMedia == Media.TypeShow:
			from lib.indexers.shows import Shows
			instance = Shows(kids = self.mKids)
			items = _historyFilter(histories = histories)
			items = instance.metadata(items = items)
			instance.menu(items, next = False)
		elif self.mMedia == Media.TypeSeason:
			from lib.indexers.seasons import Seasons
			instance = Seasons(kids = self.mKids)
			items = _historyFilter(histories = histories, season = True)
			items = instance.metadata(items = items)
			instance.menu(items, next = False)
		elif self.mMedia == Media.TypeEpisode:
			from lib.indexers.episodes import Episodes
			instance = Episodes(kids = self.mKids)
			items = _historyFilter(histories = histories, season = True, episode = True)
			items = instance.metadata(items = items)
			instance.menu(items, next = False, submenu = False) # Always directly scrape these.
		else:
			from lib.indexers.movies import Movies
			instance = Movies(media = self.mMedia, kids = self.mKids)
			items = _historyFilter(histories = histories)
			items = instance.metadata(items = items)
			instance.menu(items, next = False)

	def historyStream(self):
		from lib.modules.tools import Converter
		from lib.modules.core import Core
		from lib.modules.history import History
		Loader.show()
		items = []
		histories = History().retrieve(media = self.mMedia, kids = self.mKids)
		if len(histories) > 0:
			for history in histories:
				metadata = Converter.dictionary(history[4])
				item = Converter.dictionary(history[5])
				if Tools.isArray(item): item = item[0]
				item['metadata'] = metadata
				items.append(item)
			Core(media = self.mMedia, kids = self.mKids).showStreams(items = items, process = False)
		else:
			Dialog.notification(title = 32036, message = 33049, icon = Dialog.IconInformation)
			Loader.hide()

	def favourites(self):
		from lib.modules.library import Library
		self.addDirectoryItem(name = 32001, query = self.parameterize('moviesFavourites', media = Media.TypeMovie), icon = 'moviesfavourites.png', iconDefault = 'DefaultFavourite.png')
		self.addDirectoryItem(name = 32002, query = self.parameterize('showsFavourites', media = Media.TypeShow), icon = 'showsfavourites.png', iconDefault = 'DefaultFavourite.png')
		self.addDirectoryItem(name = 33470, query = self.parameterize('moviesFavourites', media = Media.TypeDocumentary), icon = 'documentariesfavourites.png', iconDefault = 'DefaultFavourite.png')
		self.addDirectoryItem(name = 33471, query = self.parameterize('moviesFavourites', media = Media.TypeShort), icon = 'shortsfavourites.png', iconDefault = 'DefaultFavourite.png')
		self.addDirectoryItem(name = 32036, query = self.parameterize('history', media = None), icon = 'historyfavourites.png', iconDefault = 'DefaultFavourite.png')
		if Library.enabled(): self.addDirectoryItem(name = 35170, query = self.parameterize('libraryLocalNavigator', media = None), icon = 'libraryfavourites.png', iconDefault = 'DefaultAddonProgram.png')
		self.endDirectory()

	def arrivals(self):
		self.addDirectoryItem(name = 32001, dquery = self.parameterize('moviesArrivals', media = Media.TypeMovie), icon = 'moviesnew.png', iconDefault = 'DefaultAddSource.png', library = ('arrivals', Media.TypeMovie))
		self.addDirectoryItem(name = 32002, query = self.parameterize('showsArrivals', media = Media.TypeShow), icon = 'showsnew.png', iconDefault = 'DefaultAddSource.png', library = ('arrivals', Media.TypeShow))
		self.addDirectoryItem(name = 33470, query = self.parameterize('moviesArrivals', media = Media.TypeDocumentary), icon = 'documentariesnew.png', iconDefault = 'DefaultAddSource.png', library = ('arrivals', Media.TypeDocumentary))
		self.addDirectoryItem(name = 33471, query = self.parameterize('moviesArrivals', media = Media.TypeShort), icon = 'shortsnew.png', iconDefault = 'DefaultAddSource.png', library = ('arrivals', Media.TypeShort))
		self.endDirectory()

	def search(self):
		self.addDirectoryItem(name = 32001, query = self.parameterize('moviesSearch', media = Media.TypeMovie), icon = 'searchmovies.png', iconDefault = 'DefaultAddonsSearch.png', isAction = True, isFolder = False)
		self.addDirectoryItem(name = 33527, query = self.parameterize('setsSearch', media = Media.TypeSet), icon = 'searchsets.png', iconDefault = 'DefaultAddonsSearch.png', isAction = True, isFolder = False)
		self.addDirectoryItem(name = 32002, query = self.parameterize('showsSearch', media = Media.TypeShow), icon = 'searchshows.png', iconDefault = 'DefaultAddonsSearch.png', isAction = True, isFolder = False)
		self.addDirectoryItem(name = 33470, query = self.parameterize('moviesSearch', media = Media.TypeDocumentary), icon = 'searchdocumentaries.png', iconDefault = 'DefaultAddonsSearch.png', isAction = True, isFolder = False)
		self.addDirectoryItem(name = 33471, query = self.parameterize('moviesSearch', media = Media.TypeShort), icon = 'searchshorts.png', iconDefault = 'DefaultAddonsSearch.png', isAction = True, isFolder = False)
		self.addDirectoryItem(name = 32013, query = self.parameterize('moviesPerson'), icon = 'searchpeople.png', iconDefault = 'DefaultAddonsSearch.png', isAction = True, isFolder = False)
		self.addDirectoryItem(name = 32036, query = self.parameterize('searchHistory'), icon = 'searchhistory.png', iconDefault = 'DefaultAddonsSearch.png')
		self.addDirectoryItem(name = 35157, query = self.parameterize('searchExact'), icon = 'searchexact.png', iconDefault = 'DefaultAddonsSearch.png')
		self.endDirectory()

	def searchExact(self):
		self.addDirectoryItem(32001, self.parameterize('scrapeExact', media = Media.TypeMovie), 'searchmovies.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(32002, self.parameterize('scrapeExact', media = Media.TypeShow), 'searchshows.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(33470, self.parameterize('scrapeExact', media = Media.TypeDocumentary), 'searchdocumentaries.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(33471, self.parameterize('scrapeExact', media = Media.TypeShort), 'searchshorts.png', 'DefaultAddonsSearch.png')
		self.endDirectory()

	def searchHistory(self):
		from lib.modules.search import Searches
		from lib.modules.network import Networker
		searches = Searches().retrieveAll(kids = self.mKids)
		for item in searches:
			if item[0] == Searches.TypeMovies:
				icon = 'searchmovies.png'
				action = self.parameterize('moviesSearch', media = Media.TypeMovie)
			elif item[0] == Searches.TypeSets:
				icon = 'searchsets.png'
				action = self.parameterize('setsSearch', media = Media.TypeSet)
			elif item[0] == Searches.TypeShows:
				icon = 'searchshows.png'
				action = self.parameterize('showsSearch', media = Media.TypeShow)
			elif item[0] == Searches.TypeDocumentaries:
				icon = 'searchdocumentaries.png'
				action = self.parameterize('moviesSearch', media = Media.TypeDocumentary)
			elif item[0] == Searches.TypeShorts:
				icon = 'searchshorts.png'
				action = self.parameterize('moviesSearch', media = Media.TypeShort)
			elif item[0] == Searches.TypePeople:
				icon = 'searchpeople.png'
				action = self.parameterize('moviesPerson')
			else:
				continue

			if item[2]: icon = 'searchkids.png'
			self.addDirectoryItem(item[1], '%s&terms=%s' % (action, Networker.linkQuote(item[1], plus = True)), icon, 'DefaultAddonsSearch.png', isAction = True, isFolder = False)
		self.endDirectory()

	def searchHistoryMovies(self):
		from lib.modules.search import Searches
		from lib.modules.network import Networker

		if self.mMedia == Media.TypeDocumentary:
			icon = 'searchdocumentaries.png'
			searches = Searches().retrieveDocumentaries(kids = self.mKids)
		elif self.mMedia == Media.TypeShort:
			icon = 'searchshorts.png'
			searches = Searches().retrieveShorts(kids = self.mKids)
		else:
			icon = 'searchmovies.png'
			#searches = Searches().retrieveMovies(kids = self.mKids)
			searches = Searches().retrieveAll(kids = self.mKids, type = [Searches.TypeMovies, Searches.TypeSets])

		for item in searches:
			if len(item) == 3:
				if item[0] == Searches.TypeSets: self.addDirectoryItem(item[1], self.parameterize('setsSearch&terms=%s' % Networker.linkQuote(item[1], plus = True), media = Media.TypeSet), 'searchsets.png', 'DefaultAddonsSearch.png', isAction = True, isFolder = False)
				else: self.addDirectoryItem(item[1], self.parameterize('moviesSearch&terms=%s' % Networker.linkQuote(item[1], plus = True), media = self.mMedia), icon, 'DefaultAddonsSearch.png', isAction = True, isFolder = False)
			else:
				self.addDirectoryItem(item[0], self.parameterize('moviesSearch&terms=%s' % Networker.linkQuote(item[0], plus = True), media = self.mMedia), icon, 'DefaultAddonsSearch.png', isAction = True, isFolder = False)
		self.endDirectory()

	def searchHistoryShows(self):
		from lib.modules.search import Searches
		from lib.modules.network import Networker
		searches = Searches().retrieveShows(kids = self.mKids)
		for item in searches:
			self.addDirectoryItem(item[0], self.parameterize('showsSearch&terms=%s' % Networker.linkQuote(item[0], plus = True), media = Media.TypeShow), 'searchshows.png', 'DefaultAddonsSearch.png', isAction = True, isFolder = False)
		self.endDirectory()

	def tools(self):
		from lib.modules.api import Api
		if Settings.getBoolean('navigation.menu.shortcut'): self.shortcutsItems(location = Shortcuts.LocationTools)
		if Api.lotteryValid(): self.addDirectoryItem(name = 33876, query = 'lotteryVoucher', icon = 'tickets.png', iconDefault = 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(name = 33011, query = 'settingsNavigator', icon = 'settings.png', iconDefault = 'DefaultAddonProgram.png')
		self.addDirectoryItem(name = 33502, query = 'servicesNavigator', icon = 'services.png', iconDefault = 'DefaultAddonProgram.png')
		self.addDirectoryItem(name = 33719, query = 'networkNavigator', icon = 'network.png', iconDefault = 'DefaultAddonProgram.png')
		self.addDirectoryItem(name = 32009, query = 'downloads', icon = 'downloads.png', iconDefault = 'DefaultAddonProgram.png')
		self.addDirectoryItem(name = 35170, query = 'libraryNavigator', icon = 'library.png', iconDefault = 'DefaultAddonProgram.png')
		self.addDirectoryItem(name = 33017, query = 'verificationNavigator', icon = 'verification.png', iconDefault = 'DefaultAddonProgram.png')
		self.addDirectoryItem(name = 33720, query = 'extensionsNavigator', icon = 'extensions.png', iconDefault = 'DefaultAddonProgram.png')
		self.addDirectoryItem(name = 33989, query = 'clean', icon = 'clean.png', iconDefault = 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(name = 35330, query = 'utilityNavigator', icon = 'utility.png', iconDefault = 'DefaultAddonProgram.png')
		self.addDirectoryItem(name = Format.color(33505, 'FFB700'), query = 'donations', icon = 'donations.png', iconDefault = 'DefaultAddonProgram.png', iconSpecial = Icon.SpecialDonations, isAction = True, isFolder = False)
		self.endDirectory()

	def settingsNavigator(self):
		self.addDirectoryItem(33894, 'settingsAdvanced', 'settingsadvanced.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33893, 'settingsWizard', 'settingswizard.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(35016, 'settingsOptimization', 'settingsoptimization.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33773, 'backupNavigator', 'settingsbackup.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def backupNavigator(self):
		self.addDirectoryItem(33800, 'backupAutomatic', 'backupautomatic.png', 'DefaultHardDisk.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33774, 'backupImport', 'backupimport.png', 'DefaultHardDisk.png', isAction = True, isFolder = False)
		self.addDirectoryItem(35212, 'backupExport', 'backupexport.png', 'DefaultHardDisk.png', isAction = True, isFolder = False)
		self.endDirectory()

	def systemNavigator(self):
		self.addDirectoryItem(33344, 'systemInformation', 'systeminformation.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33472, 'systemManager', 'systemmanager.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(32008, 'systemTools', 'systemtools.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(35789, 'systemBenchmark', 'systembenchmark.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33719, 'networkInformation', 'systemnetwork.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def logNavigator(self):
		self.addDirectoryItem(32063, 'logScrape', 'logscrape.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(32064, 'logKodi', 'logkodi.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def utilityNavigator(self):
		self.addDirectoryItem(33239, 'supportNavigator', 'help.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(32062, 'logNavigator', 'log.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33467, 'systemNavigator', 'system.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33311, 'ambilightNavigator', 'ambilight.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35442, 'promotionsNavigator&force=1', 'promotion.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33344, 'informationNavigator', 'information.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def informationNavigator(self):
		self.addDirectoryItem(33354, 'copy&link=%s' % Settings.getString('internal.link.website', raw = True), 'network.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33412, 'copy&link=%s' % Settings.getString('internal.link.repository', raw = True), 'cache.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33503, 'informationChangelog', 'change.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(35109, 'informationDisclaimer', 'legal.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(35201, 'informationAnnouncement', 'announcements.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33935, 'informationAttribution', 'attribution.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33358, 'informationAbout', 'information.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def traktAccount(self):
		from lib.modules import trakt
		authenticated = trakt.authenticated()
		if not authenticated:
			if Dialog.option(title = 33339, message = 33646, labelConfirm = 32512, labelDeny = 33743):
				trakt.authentication(settings = False)
				authenticated = trakt.authenticated()
		return authenticated

	def traktMovies(self):
		if self.traktAccount():
			self.addDirectoryItem(33662, self.parameterize('moviesRetrieve&link=traktrecommendations'), 'traktfeatured.png', 'DefaultAddonWebSkin.png', library = 'traktrecommendations')
			self.addDirectoryItem(32036, self.parameterize('moviesRetrieve&link=trakthistory'), 'trakthistory.png', 'DefaultAddonWebSkin.png', library = 'trakthistory')
			self.addDirectoryItem(35308, self.parameterize('moviesRetrieve&link=traktunfinished'), 'traktunfinished.png', 'DefaultAddonWebSkin.png', library = 'traktunfinished')
			self.addDirectoryItem(32032, self.parameterize('moviesRetrieve&link=traktcollection'), 'traktcollection.png', 'DefaultAddonWebSkin.png', library = 'traktcollection')
			self.addDirectoryItem(32033, self.parameterize('moviesRetrieve&link=traktwatchlist'), 'traktwatch.png', 'DefaultVideoPlaylists.png', library = 'traktwatchlist')
			self.addDirectoryItem(33002, self.parameterize('traktMoviesLists'), 'traktlists.png', 'DefaultAddonWebSkin.png')
			self.endDirectory()

	def traktMoviesLists(self):
		if self.traktAccount():
			self.addDirectoryItem(32520, self.parameterize('traktListAdd'), 'traktadd.png', 'DefaultVideoPlaylists.png')

			if self.mMedia == Media.TypeDocumentary: label = 33663
			elif self.mMedia == Media.TypeShort: label = 33664
			else: label = 32039
			self.addDirectoryItem(label, self.parameterize('moviesUserlists&mode=trakt'), 'traktlists.png', 'DefaultVideoPlaylists.png')

			self.endDirectory()

	def traktTv(self):
		if self.traktAccount():
			self.addDirectoryItem(33662, self.parameterize('showsRetrieve&link=traktrecommendations'), 'traktfeatured.png', 'DefaultAddonWebSkin.png', library = 'traktrecommendations')
			self.addDirectoryItem(32037, self.parameterize('episodesRetrieve&link=progress'), 'traktprogress.png', 'DefaultAddonWebSkin.png', library = 'progress')
			self.addDirectoryItem(32027, self.parameterize('episodesRetrieve&link=mycalendar'), 'traktcalendar.png', 'DefaultAddonWebSkin.png', library = 'mycalendar')
			self.addDirectoryItem(32036, self.parameterize('episodesRetrieve&link=trakthistory'), 'trakthistory.png', 'DefaultAddonWebSkin.png', library = 'trakthistory')
			self.addDirectoryItem(35308, self.parameterize('episodesRetrieve&link=traktunfinished'), 'traktunfinished.png', 'DefaultAddonWebSkin.png', library = 'traktunfinished')
			self.addDirectoryItem(32032, self.parameterize('showsRetrieve&link=traktcollection'), 'traktcollection.png', 'DefaultAddonWebSkin.png', library = 'traktcollection')
			self.addDirectoryItem(32033, self.parameterize('showsRetrieve&link=traktwatchlist'), 'traktwatch.png', 'DefaultVideoPlaylists.png', library = 'traktwatchlist')
			self.addDirectoryItem(33002, self.parameterize('traktTvLists'), 'traktlists.png', 'DefaultAddonWebSkin.png')
			self.endDirectory()

	def traktTvLists(self):
		if self.traktAccount():
			self.addDirectoryItem(32520, self.parameterize('traktListAdd'), 'traktadd.png', 'DefaultVideoPlaylists.png')
			self.addDirectoryItem(32040, self.parameterize('showsUserlists&mode=trakt'), 'traktlists.png', 'DefaultVideoPlaylists.png')
			self.addDirectoryItem(33665, self.parameterize('seasonsUserlists&mode=trakt'), 'traktlists.png', 'DefaultVideoPlaylists.png')
			self.addDirectoryItem(32041, self.parameterize('episodesUserlists&mode=trakt'), 'traktlists.png', 'DefaultVideoPlaylists.png')
			self.endDirectory()

	def imdbAccount(self):
		from lib.modules.account import Imdb
		account = Imdb()
		if not account.authenticated():
			if Dialog.option(title = 33339, message = 33647, labelConfirm = 32512, labelDeny = 33743):
				return account.authenticate(settings = False)
			return False
		return True

	def imdbMovies(self):
		if self.imdbAccount():
			self.addDirectoryItem(33662, self.parameterize('moviesRetrieve&link=featured'), 'imdbfeatured.png', 'DefaultMovies.png', library = 'featured')
			self.addDirectoryItem(35602, self.parameterize('moviesRetrieve&link=imdbratings'), 'imdbrated.png', 'DefaultMovies.png', library = 'imdbratings')
			self.addDirectoryItem(32032, self.parameterize('moviesRetrieve&link=imdbcollection'), 'imdbcollection.png', 'DefaultMovies.png', library = 'imdbcollection')
			self.addDirectoryItem(32033, self.parameterize('moviesRetrieve&link=imdbwatchlist'), 'imdbwatch.png', 'DefaultMovies.png', library = 'imdbwatchlist')
			self.addDirectoryItem(33002, self.parameterize('moviesUserlists&mode=imdb'), 'imdblists.png', 'DefaultAddonWebSkin.png')
			self.addDirectoryItem(35212, self.parameterize('imdbExport'), 'imdbexport.png', 'DefaultTVShows.png')
			self.endDirectory()

	def imdbTv(self):
		if self.imdbAccount():
			self.addDirectoryItem(33662, self.parameterize('showsRetrieve&link=featured'), 'imdbfeatured.png', 'DefaultTVShows.png', library = 'featured')
			self.addDirectoryItem(35602, self.parameterize('showsRetrieve&link=imdbratings'), 'imdbrated.png', 'DefaultTVShows.png', library = 'imdbratings')
			self.addDirectoryItem(32032, self.parameterize('showsRetrieve&link=imdbcollection'), 'imdbcollection.png', 'DefaultTVShows.png', library = 'imdbcollection')
			self.addDirectoryItem(32033, self.parameterize('showsRetrieve&link=imdbwatchlist'), 'imdblists.png', 'DefaultTVShows.png', library = 'imdbwatchlist')
			self.addDirectoryItem(33002, self.parameterize('showsUserlists&mode=imdb'), 'imdblists.png', 'DefaultAddonWebSkin.png')
			self.addDirectoryItem(35212, self.parameterize('imdbExport'), 'imdbexport.png', 'DefaultTVShows.png')
			self.endDirectory()

	def moviesCategories(self):
		self.addDirectoryItem(32011, self.parameterize('moviesGenres'), 'genres.png', 'DefaultGenre.png')
		self.addDirectoryItem(35526, self.parameterize('moviesYears'), 'calendar.png', 'DefaultYear.png')
		self.addDirectoryItem(33302, self.parameterize('moviesAwards'), 'awards.png', 'DefaultFile.png')
		self.addDirectoryItem(32016, self.parameterize('moviesNetworks'), 'networks.png', 'DefaultNetwork.png')
		self.addDirectoryItem(32014, self.parameterize('moviesLanguages'), 'languages.png', 'DefaultCountry.png')
		self.addDirectoryItem(32015, self.parameterize('moviesCertificates'), 'certificates.png', 'DefaultFile.png')
		self.addDirectoryItem(33437, self.parameterize('moviesAge'), 'age.png', 'DefaultYear.png')
		if self.mMedia == Media.TypeMovie and not self.kidsOnly(): self.addDirectoryItem(35368, self.parameterize('moviesDrugs'), 'drugs.png', 'DefaultVideoPlaylists.png')
		self.endDirectory()

	def moviesLists(self):
		self.addDirectoryItem(33104, self.parameterize('moviesRandom'), 'random.png', 'DefaultVideoPlaylists.png')
		self.addDirectoryItem(33004, self.parameterize('moviesRetrieve&link=new'), 'new.png', 'DefaultVideoPlaylists.png', library = 'new')
		self.addDirectoryItem(33571, self.parameterize('moviesRetrieve&link=home'), 'home.png', 'DefaultVideoPlaylists.png', library = 'home')
		self.addDirectoryItem(33005, self.parameterize('moviesRetrieve&link=rating'), 'rated.png', 'DefaultVideoPlaylists.png', library = 'rating')
		self.addDirectoryItem(32018, self.parameterize('moviesRetrieve&link=popular'), 'popular.png', 'DefaultVideoPlaylists.png', library = 'popular')
		self.addDirectoryItem(33008, self.parameterize('moviesRetrieve&link=oscars'), 'awards.png', 'DefaultVideoPlaylists.png', library = 'oscars')
		self.addDirectoryItem(33010, self.parameterize('moviesRetrieve&link=boxoffice'), 'tickets.png', 'DefaultVideoPlaylists.png', library = 'boxoffice')
		self.addDirectoryItem(33006, self.parameterize('moviesRetrieve&link=theaters'), 'premiered.png', 'DefaultVideoPlaylists.png', library = 'theaters')
		self.addDirectoryItem(33007, self.parameterize('moviesRetrieve&link=trending'), 'trending.png', 'DefaultVideoPlaylists.png', library = 'trending')
		self.addDirectoryItem(32321, self.parameterize('moviesRetrieve&link=featured'), 'featured.png', 'DefaultVideoPlaylists.png', library = 'featured')
		self.endDirectory()

	def moviesDrugs(self):
		if self.mMedia == Media.TypeMovie and not self.kidsOnly():
			self.addDirectoryItem(32310, self.parameterize('moviesRetrieve&link=drugsgeneral'), 'drugs.png', 'DefaultVideoPlaylists.png', library = 'drugsgeneral')
			self.addDirectoryItem(35369, self.parameterize('moviesRetrieve&link=drugsalcohol'), 'drugsalcohol.png', 'DefaultVideoPlaylists.png', library = 'drugsalcohol')
			self.addDirectoryItem(35370, self.parameterize('moviesRetrieve&link=drugsmarijuana'), 'drugsmarijuana.png', 'DefaultVideoPlaylists.png', library = 'drugsmarijuana')
			self.addDirectoryItem(35371, self.parameterize('moviesRetrieve&link=drugspsychedelics'), 'drugspsychedelics.png', 'DefaultVideoPlaylists.png', library = 'drugspsychedelics')
			self.endDirectory()

	def moviesPeople(self):
		self.addDirectoryItem(33003, self.parameterize('moviesPersons'), 'browse.png', 'DefaultAddonContextItem.png')
		self.addDirectoryItem(35315, self.parameterize('moviesFamous'), 'famous.png', 'DefaultAddonContextItem.png')
		self.addDirectoryItem(33302, self.parameterize('moviesAwards&type=academyawards&category=people&generic=true'), 'awards.png', 'DefaultAddonContextItem.png')
		self.addDirectoryItem(35306, self.parameterize('moviesGenders'), 'gender.png', 'DefaultAddonContextItem.png')
		self.addDirectoryItem(32010, self.parameterize('moviesPerson'), 'search.png', 'DefaultAddonsSearch.png', isAction = True, isFolder = False)
		self.endDirectory()

	def moviesSearches(self):
		self.addDirectoryItem(33039, self.parameterize('moviesSearch'), 'searchtitle.png', 'DefaultAddonsSearch.png', isAction = True, isFolder = False)
		#self.addDirectoryItem(33040, self.parameterize('moviesSearch'), 'searchdescription.png', 'DefaultAddonsSearch.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33527, self.parameterize('setsSearch'), 'searchsets.png', 'DefaultAddonsSearch.png', isAction = True, isFolder = False)
		self.addDirectoryItem(32013, self.parameterize('moviesPerson'), 'searchpeople.png', 'DefaultAddonsSearch.png', isAction = True, isFolder = False)
		self.addDirectoryItem(32036, self.parameterize('searchHistoryMovies'), 'searchhistory.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(35157, self.parameterize('scrapeExact', media = self.mMedia), 'searchexact.png', 'DefaultAddonsSearch.png')
		self.endDirectory()

	def sets(self):
		self.addDirectoryItem(33003, self.parameterize('setsRetrieve&link=browse'), 'browse.png', 'DefaultVideoPlaylists.png')
		self.addDirectoryItem(33490, self.parameterize('setsRetrieve&link=arrivals'), 'new.png', 'DefaultVideoPlaylists.png')
		self.addDirectoryItem(35375, self.parameterize('setsRetrieve&link=random'), 'random.png', 'DefaultVideoPlaylists.png')
		self.addDirectoryItem(33565, self.parameterize('setsAlphabetic'), 'alphabet.png', 'DefaultVideoPlaylists.png')
		self.addDirectoryItem(32010, self.parameterize('setsSearch'), 'search.png', 'DefaultAddonsSearch.png', isAction = True, isFolder = False)
		self.endDirectory()

	def shows(self, lite = False):
		if Settings.getBoolean('navigation.menu.shortcut'): self.shortcutsItems(location = Shortcuts.LocationShows)
		if not self.kidsOnly() and lite == False: self.addDirectoryItem(name = 33000, query = self.parameterize('showsFavourites', lite = True), icon = 'favourites.png', iconDefault = 'DefaultFavourite.png')
		self.addDirectoryItem(name = 33490, query = self.parameterize('showsArrivals'), icon = 'new.png', iconDefault = 'DefaultAddSource.png', library = 'arrivals')
		self.addDirectoryItem(name = 33001, query = self.parameterize('showsCategories'), icon = 'categories.png', iconDefault = 'DefaultTags.png')
		self.addDirectoryItem(name = 33002, query = self.parameterize('showsLists'), icon = 'lists.png', iconDefault = 'DefaultVideoPlaylists.png')
		self.addDirectoryItem(name = 32013, query = self.parameterize('showsPeople'), icon = 'people.png', iconDefault = 'DefaultTags.png')
		if lite == False: self.addDirectoryItem(name = 32010, query = self.parameterize('showsSearches'), icon = 'search.png', iconDefault = 'DefaultAddonsSearch.png')
		self.endDirectory()

	def showsFavourites(self, lite = False):
		from lib.modules.library import Library
		if Settings.getBoolean('navigation.menu.shortcut'): self.shortcutsItems(location = Shortcuts.LocationShowsFavourites)
		self.addDirectoryItem(32315, self.parameterize('traktTv'), 'trakt.png', 'DefaultAddonWebSkin.png')
		self.addDirectoryItem(32034, self.parameterize('imdbTv'), 'imdb.png', 'DefaultAddonWebSkin.png')
		if not self.kidsOnly(): self.addDirectoryItem(32027, self.parameterize('showsCalendars'), 'calendar.png', 'DefaultYear.png') # Calendar does not have rating, so do not show for kids.
		self.addDirectoryItem(32036, self.parameterize('history'), 'history.png', 'DefaultYear.png')
		if not self.kidsOnly() and Library.enabled(): self.addDirectoryItem(35170, self.parameterize('libraryLocal'), 'library.png', 'DefaultAddonLibrary.png', isAction = True, isFolder = False)
		if lite == False: self.addDirectoryItem(32031, self.parameterize('shows', lite = True), 'discover.png', 'DefaultTVShows.png')
		self.endDirectory()

	def showsCategories(self):
		self.addDirectoryItem(32011, self.parameterize('showsGenres'), 'genres.png', 'DefaultGenre.png')
		self.addDirectoryItem(35526, self.parameterize('showsYears'), 'calendar.png', 'DefaultYear.png')
		self.addDirectoryItem(33302, self.parameterize('showsAwards'), 'awards.png', 'DefaultFile.png')
		self.addDirectoryItem(32016, self.parameterize('showsNetworks'), 'networks.png', 'DefaultNetwork.png')
		self.addDirectoryItem(32014, self.parameterize('showsLanguages'), 'languages.png', 'DefaultCountry.png')
		self.addDirectoryItem(32015, self.parameterize('showsCertificates'), 'certificates.png', 'DefaultFile.png')
		self.addDirectoryItem(33437, self.parameterize('showsAge'), 'age.png', 'DefaultYear.png')
		self.endDirectory()

	def showsLists(self):
		self.addDirectoryItem(33104, self.parameterize('showsRandom'), 'random.png', 'DefaultVideoPlaylists.png')
		self.addDirectoryItem(33004, self.parameterize('episodesRetrieve&link=added'), 'new.png', 'DefaultVideoPlaylists.png', library = 'added')
		self.addDirectoryItem(33571, self.parameterize('showsHome'), 'home.png', 'DefaultVideoPlaylists.png', library = 'home')
		self.addDirectoryItem(33005, self.parameterize('showsRetrieve&link=rating'), 'rated.png', 'DefaultVideoPlaylists.png', library = 'added')
		self.addDirectoryItem(32018, self.parameterize('showsRetrieve&link=popular'), 'popular.png', 'DefaultVideoPlaylists.png', library = 'popular')
		self.addDirectoryItem(33008, self.parameterize('showsRetrieve&link=emmies'), 'awards.png', 'DefaultVideoPlaylists.png', library = 'emmies')
		self.addDirectoryItem(33009, self.parameterize('showsRetrieve&link=airing'), 'aired.png', 'DefaultVideoPlaylists.png', library = 'airing')
		self.addDirectoryItem(33006, self.parameterize('showsRetrieve&link=premiere'), 'premiered.png', 'DefaultVideoPlaylists.png', library = 'premiere')
		self.addDirectoryItem(33007, self.parameterize('showsRetrieve&link=trending'), 'trending.png', 'DefaultVideoPlaylists.png', library = 'trending')
		self.addDirectoryItem(32321, self.parameterize('showsRetrieve&link=featured'), 'featured.png', 'DefaultVideoPlaylists.png', library = 'featured')
		self.endDirectory()

	def showsPeople(self):
		self.addDirectoryItem(33003, self.parameterize('showsPersons'), 'browse.png', 'DefaultAddonContextItem.png')
		self.addDirectoryItem(35315, self.parameterize('showsFamous'), 'famous.png', 'DefaultAddonContextItem.png')
		self.addDirectoryItem(33302, self.parameterize('showsAwards&type=academyawards&category=people&generic=true'), 'awards.png', 'DefaultAddonContextItem.png')
		self.addDirectoryItem(35306, self.parameterize('showsGenders'), 'gender.png', 'DefaultAddonContextItem.png')
		self.addDirectoryItem(32010, self.parameterize('showsPerson'), 'search.png', 'DefaultAddonsSearch.png', isAction = True, isFolder = False)
		self.endDirectory()

	def showsSearches(self):
		self.addDirectoryItem(33039, self.parameterize('showsSearch'), 'searchtitle.png', 'DefaultAddonsSearch.png', isAction = True, isFolder = False)
		#self.addDirectoryItem(33040, self.parameterize('showsSearch'), 'searchdescription.png', 'DefaultAddonsSearch.png', isAction = True, isFolder = False)
		self.addDirectoryItem(32013, self.parameterize('showsPerson'), 'searchpeople.png', 'DefaultAddonsSearch.png', isAction = True, isFolder = False)
		self.addDirectoryItem(32036, self.parameterize('searchHistoryShows'), 'searchhistory.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(35157, self.parameterize('scrapeExact', media = self.mMedia), 'searchexact.png', 'DefaultAddonsSearch.png')
		self.endDirectory()

	def channels(self):
		self.addDirectoryItem(33050, self.parameterize('channelsBroadcasters'), 'aired.png', 'DefaultNetwork.png')
		self.addDirectoryItem(32007, self.parameterize('channelsIndividuals'), 'aired.png', 'DefaultNetwork.png')
		self.endDirectory()

	def verificationNavigator(self):
		self.addDirectoryItem(32346, 'verificationAccounts', 'verificationaccount.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33014, 'providersVerify', 'verificationprovider.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(35689, 'cloudflareVerify', 'verificationcloudflare.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def networkNavigator(self):
		self.addDirectoryItem(33030, 'speedtestNavigator', 'networkspeed.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33344, 'networkInformation', 'networkinformation.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33801, 'vpnNavigator', 'networkvpn.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def speedtestNavigator(self):
		self.addDirectoryItem(33509, 'speedtestGlobal', 'speedglobal.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33566, 'speedtestPremiumize', 'speedpremiumize.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(35200, 'speedtestOffCloud', 'speedoffcloud.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33567, 'speedtestRealDebrid', 'speedrealdebrid.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33794, 'speedtestEasyNews', 'speedeasynews.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33851, 'speedtestComparison', 'speedcomparison.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def vpnNavigator(self):
		from lib.modules.tools import VpnManager
		from lib.debrid import premiumize
		from lib.debrid import easynews
		self.addDirectoryItem(33389, 'vpnVerify', 'vpnverification.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33802, 'vpnConfigure', 'vpnconfiguration.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33011, 'vpnSettings', 'vpnsettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		if VpnManager.installed(): self.addDirectoryItem(33709, 'vpnmanagerLaunch', 'vpnvpnmanager.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		if premiumize.Core().accountValid(): self.addDirectoryItem(33566, 'premiumizeVpn', 'vpnpremiumize.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		if easynews.Core().accountValid(): self.addDirectoryItem(33794, 'easynewsVpn', 'vpneasynews.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def libraryNavigator(self):
		self.addDirectoryItem(35183, 'libraryUpdate&force=true', 'libraryupdate.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33468, 'libraryClean', 'libraryclean.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(32314, 'libraryLocalNavigator', 'librarylocal.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33003, 'libraryBrowseNavigator', 'librarybrowse.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33011, 'librarySettings', 'librarysettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def libraryLocalNavigator(self):
		self.addDirectoryItem(32001, self.parameterize('libraryLocal', media = Media.TypeMovie), 'librarymovies.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(32002, self.parameterize('libraryLocal', media = Media.TypeShow), 'libraryshows.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33491, self.parameterize('libraryLocal', media = Media.TypeDocumentary), 'librarydocumentaries.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33471, self.parameterize('libraryLocal', media = Media.TypeShort), 'libraryshorts.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def libraryBrowseNavigator(self, error = False):
		if error:
			message = Translation.string(33068) % self.mMedia
			Dialog.confirm(title = 35170, message = message)
		else:
			from lib.modules.tools import File
			from lib.modules.library import Library
			for item in [(Media.TypeMovie, 'movies', 32001), (Media.TypeShow, 'shows', 32002), (Media.TypeDocumentary, 'documentaries', 33491), (Media.TypeShort, 'shorts', 33471)]:
				path = Library(media = item[0]).location()
				if File.exists(path):
					action = path
					actionIs = False
				else:
					action = 'libraryBrowse&media=%s&error=%d' % (item[0], int(True))
					actionIs = True
				self.addDirectoryItem(item[2], action, 'library%s.png' % item[1], 'DefaultAddonProgram.png', isAction = actionIs)
			self.endDirectory()

	def downloads(self, type = None):
		from lib.modules.tools import File
		from lib.modules.downloader import Downloader
		if type is None:
			self.addDirectoryItem(33290, 'downloads&downloadType=%s' % Downloader.TypeManual, 'downloadsmanual.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(33016, 'downloads&downloadType=%s' % Downloader.TypeCache, 'downloadscache.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(33566, 'premiumizeDownloadsNavigator', 'downloadspremiumize.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(35200, 'offcloudDownloadsNavigator', 'downloadsoffcloud.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(33567, 'realdebridDownloadsNavigator', 'downloadsrealdebrid.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(35316, 'elementumNavigator', 'downloadselementum.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(33570, 'quasarNavigator', 'downloadsquasar.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(33011, 'downloadsSettings', 'downloadssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.endDirectory()
		else:
			if Downloader(type).enabled(notification = True): # Do not use full check, since the download directory might be temporarley down (eg: network), and you still want to access the downloads.
				if Settings.get('downloads.%s.path.selection' % type) == '0':
					path = Settings.path('downloads.%s.path.combined' % type)
					if File.exists(path):
						action = 'downloadsBrowse&downloadType=%s' % (type)
					else:
						action = 'downloadsBrowse&downloadType=%s&downloadError=%d' % (type, int(True))
				else:
					action = 'downloadsBrowse&downloadType=%s' % type
				self.addDirectoryItem(33297, 'downloadsList&downloadType=%s' % type, 'downloadslist.png', 'DefaultAddonProgram.png')
				self.addDirectoryItem(33003, action, 'downloadsbrowse.png', 'DefaultAddonProgram.png', isAction = True)
				self.addDirectoryItem(33013, 'downloadsClear&downloadType=%s' % type, 'downloadsclean.png', 'DefaultAddonProgram.png')
				self.addDirectoryItem(33011, 'downloadsSettings&downloadType=%s' % type, 'downloadssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
				self.endDirectory()

	def downloadsBrowse(self, type = None, error = False):
		from lib.modules.tools import File
		from lib.modules.downloader import Downloader
		if error:
			Downloader(type).notificationLocation()
		else:
			downer = Downloader(type = type)
			for item in [(Downloader.MediaMovie, 'movies', 32001), (Downloader.MediaShow, 'shows', 32002), (Downloader.MediaDocumentary, 'documentaries', 33491), (Downloader.MediaShort, 'shorts', 33471), (Downloader.MediaOther, 'other', 35149)]:
				path = downer._location(item[0])
				if File.exists(path):
					action = path
					actionIs = False
				else:
					action = 'downloadsBrowse&downloadType=%s&downloadError=%d' % (type, int(True))
					actionIs = True
				self.addDirectoryItem(item[2], action, 'downloads%s.png' % item[1], 'DefaultAddonProgram.png', isAction = actionIs)
			self.endDirectory()

	def downloadsList(self, type):
		from lib.modules.downloader import Downloader
		self.addDirectoryItem(33029, 'downloadsList&downloadType=%s&downloadStatus=%s' % (type, Downloader.StatusAll), 'downloadslist.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33291, 'downloadsList&downloadType=%s&downloadStatus=%s' % (type, Downloader.StatusBusy), 'downloadsbusy.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33292, 'downloadsList&downloadType=%s&downloadStatus=%s' % (type, Downloader.StatusPaused), 'downloadspaused.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33294, 'downloadsList&downloadType=%s&downloadStatus=%s' % (type, Downloader.StatusCompleted), 'downloadscompleted.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33295, 'downloadsList&downloadType=%s&downloadStatus=%s' % (type, Downloader.StatusFailed), 'downloadsfailed.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def downloadsClear(self, type):
		from lib.modules.downloader import Downloader
		self.addDirectoryItem(33029, 'downloadsClear&downloadType=%s&downloadStatus=%s' % (type, Downloader.StatusAll), 'cleanlist.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33291, 'downloadsClear&downloadType=%s&downloadStatus=%s' % (type, Downloader.StatusBusy), 'cleanplay.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33292, 'downloadsClear&downloadType=%s&downloadStatus=%s' % (type, Downloader.StatusPaused), 'cleanpaused.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33294, 'downloadsClear&downloadType=%s&downloadStatus=%s' % (type, Downloader.StatusCompleted), 'cleancompleted.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33295, 'downloadsClear&downloadType=%s&downloadStatus=%s' % (type, Downloader.StatusFailed), 'cleanfailed.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def servicesNavigator(self):
		self.addDirectoryItem(35400, 'orionNavigator', 'orion.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33768, 'servicesPremiumNavigator', 'premium.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33749, 'servicesScraperNavigator', 'scraper.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35328, 'servicesResolverNavigator', 'change.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35822, 'informerNavigator', 'informer.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35329, 'servicesDownloaderNavigator', 'downloads.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35330, 'servicesUtilityNavigator', 'utility.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def servicesPremiumNavigator(self):
		self.addDirectoryItem(33566, 'premiumizeNavigator', 'premiumize.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35200, 'offcloudNavigator', 'offcloud.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33567, 'realdebridNavigator', 'realdebrid.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33794, 'easynewsNavigator', 'easynews.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35551, 'embyNavigator', 'emby.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35682, 'jellyfinNavigator', 'jellyfin.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def servicesScraperNavigator(self):
		self.addDirectoryItem(35548, 'opescrapersNavigator', 'opescrapers.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33318, 'fenscrapersNavigator', 'fenscrapers.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33321, 'oatscrapersNavigator', 'oatscrapers.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(36086, 'crescrapersNavigator', 'crescrapers.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35431, 'lamscrapersNavigator', 'lamscrapers.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35504, 'civscrapersNavigator', 'civscrapers.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35530, 'gloscrapersNavigator', 'gloscrapers.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35359, 'uniscrapersNavigator', 'uniscrapers.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(35349, 'nanscrapersNavigator', 'nanscrapers.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def servicesResolverNavigator(self):
		self.addDirectoryItem(35310, 'resolveurlNavigator', 'resolveurl.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33747, 'urlresolverNavigator', 'urlresolver.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def servicesDownloaderNavigator(self):
		self.addDirectoryItem(35316, 'elementumNavigator', 'elementum.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33570, 'quasarNavigator', 'quasar.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def servicesUtilityNavigator(self):
		self.addDirectoryItem(35296, 'youtubeNavigator', 'youtube.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33322, 'upnextNavigator', 'upnext.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33709, 'vpnmanagerNavigator', 'vpnmanager.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def orionNavigator(self):
		from lib.modules.orionoid import Orionoid
		orion = Orionoid()
		if orion.addonInstalled():
			self.addDirectoryItem(33256, 'orionLaunch', 'orionlaunch.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			try:
				if orion.accountPromotionEnabled() or not orion.accountValid(): self.addDirectoryItem(35428, self.parameterize('orionPromotion'), 'orion.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
				if orion.accountValid(): self.addDirectoryItem(33339, 'orionAccount', 'orionaccount.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
				if orion.accountFree(): self.addDirectoryItem(33768, 'orionWebsite', 'orionpremium.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			except: pass
			self.addDirectoryItem(33011, 'orionSettings', 'orionsettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33354, 'orionWebsite', 'orionweb.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(35636, 'orionUninstall', 'orionuninstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else:
			self.addDirectoryItem(33736, 'orionInstall', 'orioninstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def premiumizeNavigator(self):
		from lib.debrid import premiumize
		valid = premiumize.Core().accountValid()
		if valid:
			self.addDirectoryItem(32009, 'premiumizeDownloadsNavigator&lite=1', 'premiumizedownloads.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(33339, 'premiumizeAccount', 'premiumizeaccount.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33030, 'speedtestPremiumize', 'premiumizespeed.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33011, 'premiumizeSettings', 'premiumizesettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33354, 'premiumizeWebsite', 'premiumizeweb.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def premiumizeDownloadsNavigator(self, lite = False):
		from lib.debrid import premiumize
		valid = premiumize.Core().accountValid()
		if valid:
			self.addDirectoryItem(33297, 'premiumizeList', 'downloadslist.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(35069, 'premiumizeAdd', 'downloadsadd.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33013, 'premiumizeClear', 'downloadsclean.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33344, 'premiumizeInformation', 'downloadsinformation.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		if not lite:
			self.addDirectoryItem(33011, 'premiumizeSettings', 'downloadssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def offcloudNavigator(self):
		from lib.debrid import offcloud
		valid = offcloud.Core().accountValid()
		if valid:
			self.addDirectoryItem(32009, 'offcloudDownloadsNavigator&lite=1', 'offclouddownloads.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(33339, 'offcloudAccount', 'offcloudaccount.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33030, 'speedtestOffCloud', 'offcloudspeed.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33011, 'offcloudSettings', 'offcloudsettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33354, 'offcloudWebsite', 'offcloudweb.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def offcloudDownloadsNavigator(self, lite = False, category = None):
		from lib.debrid import offcloud
		valid = offcloud.Core().accountValid()
		if category is None:
			self.addDirectoryItem(35205, 'offcloudDownloadsNavigator&category=instant', 'downloadsinstant.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(35206, 'offcloudDownloadsNavigator&category=cloud', 'downloadscloud.png', 'DefaultAddonProgram.png')
			if valid:
				self.addDirectoryItem(35069, 'offcloudAdd', 'downloadsadd.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
				self.addDirectoryItem(33013, 'offcloudClear', 'downloadsclean.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
				self.addDirectoryItem(33344, 'offcloudInformation', 'downloadsinformation.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			if not lite:
				self.addDirectoryItem(33011, 'offcloudSettings', 'downloadssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else:
			if valid:
				self.addDirectoryItem(33297, 'offcloudList&category=%s' % category, 'downloadslist.png', 'DefaultAddonProgram.png')
				self.addDirectoryItem(35069, 'offcloudAdd&category=%s' % category, 'downloadsadd.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			if not lite:
				if valid: self.addDirectoryItem(33013, 'offcloudClear&category=%s' % category, 'downloadsclean.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			if valid:
				self.addDirectoryItem(33344, 'offcloudInformation&category=%s' % category, 'downloadsinformation.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def realdebridNavigator(self):
		from lib.debrid import realdebrid
		valid = realdebrid.Core().accountValid()
		if valid:
			self.addDirectoryItem(32009, 'realdebridDownloadsNavigator&lite=1', 'realdebriddownloads.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(33339, 'realdebridAccount', 'realdebridaccount.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33030, 'speedtestRealDebrid', 'realdebridspeed.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33011, 'realdebridSettings', 'realdebridsettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33354, 'realdebridWebsite', 'realdebridweb.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def realdebridDownloadsNavigator(self, lite = False):
		from lib.debrid import realdebrid
		valid = realdebrid.Core().accountValid()
		if valid:
			self.addDirectoryItem(33297, 'realdebridList', 'downloadslist.png', 'DefaultAddonProgram.png')
			self.addDirectoryItem(35069, 'realdebridAdd', 'downloadsadd.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33013, 'realdebridClear', 'downloadsclean.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33344, 'realdebridInformation', 'downloadsinformation.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		if not lite:
			self.addDirectoryItem(33011, 'realdebridSettings', 'downloadssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def easynewsNavigator(self):
		from lib.debrid import easynews
		if easynews.Core().accountValid():
			self.addDirectoryItem(33339, 'easynewsAccount', 'easynewsaccount.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33030, 'speedtestEasyNews', 'easynewsspeed.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33354, 'easynewsWebsite', 'easynewsweb.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def embyNavigator(self):
		self.addDirectoryItem(33011, 'embySettings', 'embysettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33354, 'embyWebsite', 'embyweb.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def jellyfinNavigator(self):
		self.addDirectoryItem(33011, 'jellyfinSettings', 'jellyfinsettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33354, 'jellyfinWebsite', 'jellyfinweb.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def elementumNavigator(self):
		from lib.modules.tools import Elementum
		if Elementum.installed():
			self.addDirectoryItem(33256, 'elementumLaunch', 'elementumlaunch.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33477, 'elementumInterface', 'elementumweb.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33011, 'elementumSettings', 'elementumsettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else:
			self.addDirectoryItem(33474, 'elementumInstall', 'elementuminstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def quasarNavigator(self):
		from lib.modules.tools import Quasar
		if Quasar.installed():
			self.addDirectoryItem(33256, 'quasarLaunch', 'quasarlaunch.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33477, 'quasarInterface', 'quasarweb.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33011, 'quasarSettings', 'quasarsettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else:
			self.addDirectoryItem(33474, 'quasarInstall', 'quasarinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def resolveurlNavigator(self):
		from lib.modules.tools import ResolveUrl
		if ResolveUrl.installed(): self.addDirectoryItem(33011, 'resolveurlSettings', 'resolveurlsettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else: self.addDirectoryItem(33474, 'resolveurlInstall', 'resolveurlinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def urlresolverNavigator(self):
		from lib.modules.tools import UrlResolver
		if UrlResolver.installed(): self.addDirectoryItem(33011, 'urlresolverSettings', 'urlresolversettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else: self.addDirectoryItem(33474, 'urlresolverInstall', 'urlresolverinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def opescrapersNavigator(self):
		from lib.modules.tools import OpeScrapers
		if OpeScrapers.installed(): self.addDirectoryItem(33011, 'opescrapersSettings', 'opescraperssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else: self.addDirectoryItem(33474, 'opescrapersInstall', 'opescrapersinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def fenscrapersNavigator(self):
		from lib.modules.tools import FenScrapers
		if FenScrapers.installed(): self.addDirectoryItem(33011, 'fenscrapersSettings', 'fenscraperssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else: self.addDirectoryItem(33474, 'fenscrapersInstall', 'fenscrapersinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def oatscrapersNavigator(self):
		from lib.modules.tools import OatScrapers
		if OatScrapers.installed(): self.addDirectoryItem(33011, 'oatscrapersSettings', 'oatscraperssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else: self.addDirectoryItem(33474, 'oatscrapersInstall', 'oatscrapersinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def crescrapersNavigator(self):
		from lib.modules.tools import CreScrapers
		if CreScrapers.installed(): self.addDirectoryItem(33011, 'crescrapersSettings', 'crescraperssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else: self.addDirectoryItem(33474, 'crescrapersInstall', 'crescrapersinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def lamscrapersNavigator(self):
		from lib.modules.tools import LamScrapers
		if LamScrapers.installed(): self.addDirectoryItem(33011, 'lamscrapersSettings', 'lamscraperssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else: self.addDirectoryItem(33474, 'lamscrapersInstall', 'lamscrapersinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def civscrapersNavigator(self):
		from lib.modules.tools import CivScrapers
		if CivScrapers.installed():  self.addDirectoryItem(33011, 'civscrapersSettings', 'civscraperssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else: self.addDirectoryItem(33474, 'civscrapersInstall', 'civscrapersinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def gloscrapersNavigator(self):
		from lib.modules.tools import GloScrapers
		if GloScrapers.installed(): self.addDirectoryItem(33011, 'gloscrapersSettings', 'gloscraperssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else: self.addDirectoryItem(33474, 'gloscrapersInstall', 'gloscrapersinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def uniscrapersNavigator(self):
		from lib.modules.tools import UniScrapers
		if UniScrapers.installed(): self.addDirectoryItem(33011, 'uniscrapersSettings', 'uniscraperssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else: self.addDirectoryItem(33474, 'uniscrapersInstall', 'uniscrapersinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def nanscrapersNavigator(self):
		from lib.modules.tools import NanScrapers
		if NanScrapers.installed(): self.addDirectoryItem(33011, 'nanscrapersSettings', 'nanscraperssettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else: self.addDirectoryItem(33474, 'nanscrapersInstall', 'nanscrapersinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def youtubeNavigator(self):
		from lib.modules.tools import YouTube
		if YouTube.installed():
			self.addDirectoryItem(33256, 'youtubeLaunch', 'youtubelaunch.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33011, 'youtubeSettings', 'youtubesettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else:
			self.addDirectoryItem(33474, 'youtubeInstall', 'youtubeinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33354, 'youtubeWebsite', 'youtubeweb.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def upnextNavigator(self):
		from lib.modules.tools import UpNext
		if UpNext.installed(): self.addDirectoryItem(33011, 'upnextSettings', 'upnextsettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else: self.addDirectoryItem(33474, 'upnextInstall', 'upnextinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def vpnmanagerNavigator(self):
		from lib.modules.tools import VpnManager
		if VpnManager.installed():
			self.addDirectoryItem(33256, 'vpnmanagerLaunch', 'vpnmanagerlaunch.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33011, 'vpnmanagerSettings', 'vpnmanagersettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		else:
			self.addDirectoryItem(33474, 'vpnmanagerInstall', 'vpnmanagerinstall.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def extensionsNavigator(self):
		self.addDirectoryItem(33239, 'extensionsHelp', 'extensionshelp.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33721, 'extensionsAvailableNavigator', 'extensionsavailable.png', 'DefaultAddonProgram.png')
		self.addDirectoryItem(33722, 'extensionsInstalledNavigator', 'extensionsinstalled.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def extensionsAvailableNavigator(self):
		from lib.modules.tools import Extension
		for extension in Extension.list():
			if not extension['installed']: self.addDirectoryItem(extension['name'], 'extensions&id=%s' % extension['id'], extension['icon'], 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def extensionsInstalledNavigator(self):
		from lib.modules.tools import Extension
		for extension in Extension.list():
			if extension['installed']: self.addDirectoryItem(extension['name'], 'extensions&id=%s' % extension['id'], extension['icon'], 'DefaultAddonProgram.png')
		self.endDirectory()

	def ambilightNavigator(self):
		self.addDirectoryItem(33406, 'lightpackNavigator', 'lightpack.png', 'DefaultAddonProgram.png')
		self.endDirectory()

	def lightpackNavigator(self):
		from lib.modules.tools import Lightpack
		if Lightpack().enabled():
			self.addDirectoryItem(33407, 'lightpackSwitchOn', 'lightpackon.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33408, 'lightpackSwitchOff', 'lightpackoff.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
			self.addDirectoryItem(33409, 'lightpackAnimate', 'lightpackanimate.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.addDirectoryItem(33011, 'lightpackSettings', 'lightpacksettings.png', 'DefaultAddonProgram.png', isAction = True, isFolder = False)
		self.endDirectory()

	def kidsRedirect(self):
		if Kids.enabled() and Kids.locked():
			self.kids()
			return True
		return False

	def kids(self):
		kids = Selection.TypeInclude

		if Settings.getBoolean('navigation.menu.movie'): self.addDirectoryItem(name = 32001, query = self.parameterize('movies', media = Media.TypeMovie, kids = kids), icon = 'movies.png', iconDefault = 'DefaultMovies.png')
		if Settings.getBoolean('navigation.menu.show'): self.addDirectoryItem(name = 32002, query = self.parameterize('shows', media = Media.TypeShow, kids = kids), icon = 'shows.png', iconDefault = 'DefaultTVShows.png')
		if Settings.getBoolean('navigation.menu.documentary'): self.addDirectoryItem(name = 33470, query = self.parameterize('documentaries', media = Media.TypeDocumentary, kids = kids), icon = 'documentaries.png', iconDefault = 'DefaultVideo.png')
		if Settings.getBoolean('navigation.menu.short'): self.addDirectoryItem(name = 33471, query = self.parameterize('shorts', media = Media.TypeShort, kids = kids), icon = 'shorts.png', iconDefault = 'DefaultVideo.png')

		if Settings.getBoolean('navigation.menu.arrival'): self.addDirectoryItem(name = 33490, query = self.parameterize('navigatorArrivals', kids = kids), icon = 'new.png', iconDefault = 'DefaultAddSource.png')
		if Settings.getBoolean('navigation.menu.search'): self.addDirectoryItem(name = 32010, query = self.parameterize('search', kids = kids), icon = 'search.png', iconDefault = 'DefaultAddonsSearch.png')

		if Kids.lockable(): self.addDirectoryItem(name = 33442, query = 'kidsLock', icon = 'lock.png', iconDefault = 'DefaultAddonService.png')
		elif Kids.unlockable(): self.addDirectoryItem(name = 33443, query = 'kidsUnlock', icon = 'unlock.png', iconDefault = 'DefaultAddonService.png')

		self.endDirectory()

	def shortcutsNavigator(self, location):
		values = Shortcuts().retrieve(location = location)
		if len(values) > 1:
			for value in values:
				self.shortcutsItem(location, value[0], value[1], value[2])
			self.endDirectory()

	def shortcutsItems(self, location):
		if Shortcuts.enabled():
			values = Shortcuts().retrieve(location = location)
			if len(values) == 1: self.shortcutsItem(location, values[0][0], values[0][1], values[0][2])
			elif len(values) > 1: self.addDirectoryItem(name = 35119, query = self.parameterize('shortcutsNavigator&location=%s' % location), icon = 'shortcuts.png', iconDefault = 'DefaultAddonProgram.png')

	def shortcutsItem(self, location, id, link, name):
		link = Shortcuts.parameterize(link, location, id)
		id = str(id)

		if self.mContext: context = Context(mode = Context.ModeGeneric, media = self.mMedia, kids = self.mKids, shortcutId = id, shortcutLocation = location, shortcutDelete = True).menu(full = True)
		else: context = None

		# Kodi 18 has problems with calling Container.Update/RunPlugin from another plugin call.
		# Instead, show the content directly here without going through shortcutsOpen first.
		# Shortcuts.process(params) was added to gaia.py top handle the count update with the new way.
		self.mDirectory.add(label = name, link = link, context = context, icon = 'shortcuts.png', iconDefault = 'DefaultAddonProgram.png', fanart = True, folder = not Shortcuts.direct(link), lock = False)
