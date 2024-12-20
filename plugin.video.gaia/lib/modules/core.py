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

import xbmc
import sys
import re

from lib import debrid
from lib.debrid.external import External, Orion, Alldebrid, Debridlink

from lib.modules import trakt as traktx
from lib.modules import network
from lib.modules import interface
from lib.modules import window
from lib.modules import tools
from lib.modules import convert
from lib.modules import handler
from lib.modules import history
from lib.modules import video
from lib.modules import orionoid
from lib.modules import cache as cachex
from lib.modules.stream import Stream, Filters, Settings, Termination
from lib.modules.library import Library
from lib.modules.database import Database
from lib.modules.theme import Theme
from lib.modules.concurrency import Pool, Lock, Premaphore

from lib.meta.image import MetaImage
from lib.meta.tools import MetaTools
from lib.meta.pack import MetaPack
from lib.meta.manager import MetaManager

from lib.providers.core.manager import Manager as ProviderManager
from lib.providers.core.base import ProviderBase

class Core(object):

	Hosters = None
	HostersPremium = None
	HostersCaptcha = None
	HostersBlocked = None

	ServicesDebrid = None
	ServicesExternal = None

	StatusInitialize = 'initialize'
	StatusScrape = 'scrape'
	StatusFinalize = 'finalize'
	StatusFinished = 'finished'
	StatusCancel = 'cancel'

	SilentActive = True
	SilentInactive = False
	SilentCancel = 'cancel'
	SilentInteract = 'interact'

	PropertyItems = 'GaiaScrapeItems'
	PropertyMetadata = 'GaiaScrapeMetadata'
	PropertyExtras = 'GaiaScrapeExtras'
	PropertyProcess = 'GaiaScrapeProcess'
	PropertyStatus = 'GaiaScrapeStatus'
	PropertyNotification = 'GaiaScrapeNofitifcation'
	PropertySilent = 'GaiaScrapeSilent'

	GlobalItems = None
	GlobalItemsJson = None
	GlobalMetadata = None
	GlobalMetadataJson = None
	GlobalThreads = []

	Instance = None

	def __init__(self, media = tools.Media.Unknown, silent = False):
		self.media = media
		self.new = None
		self.sources = []
		self.providers = []
		self.terminated = False
		self.downloadCanceled = False
		self.filter = None
		self.reload = None

		self.silent = silent
		self.silentThread = None

		self.lock = Lock()

		self.binge = None
		self.autoplay = Settings.settingsModeAutomatic()

		self.navigationCinema = video.Trailer.cinemaEnabled()
		self.navigationCinemaProgress = self.navigationCinema and video.Trailer.cinemaProgress()
		self.navigationCinemaInerrupt = self.navigationCinema and video.Trailer.cinemaInterrupt()
		if self.navigationCinema: self.navigationCinemaTrailer = video.Trailer(media = tools.Media.Show if tools.Media.isSerie(self.media) else self.media)

		self.navigationScrape = tools.Settings.getInteger('interface.scrape.interface')
		self.navigationScrapeSpecial = self.navigationScrape == 0
		self.navigationScrapeDialog = self.navigationScrape == 1
		self.navigationScrapeBar = self.navigationScrape == 2

		self.navigationStreams = tools.Settings.getInteger('interface.stream.interface')
		self.navigationStreamsSpecial = self.navigationStreams == 0
		self.navigationStreamsDirectory = self.navigationStreams == 1
		self.navigationStreamsDialogDetailed = self.navigationStreams == 2
		self.navigationStreamsDialogPlain = self.navigationStreams == 3

		self.navigationPlayback = tools.Settings.getInteger('interface.playback.interface')
		self.navigationPlaybackSpecial = self.navigationPlayback == 0 # Accessed from RealDebrid interface.py.
		self.navigationPlaybackDialog = self.navigationPlayback == 1
		self.navigationPlaybackBar = self.navigationPlayback == 2

	@classmethod
	def instance(self):
		if Core.Instance is None: Core.Instance = Core()
		return Core.Instance

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		# NB: Do not clear GlobalItems and GlobalMetadata, since it makes reloading the stream window faster if the interpreter is reused.
		# Update: The scraping process is always started with a new interpreter (handle: -1), probably because it is not a menu item, but a standalone action that Kodi executes.
		# Hence, these variables are not available on the next execution and will not make stream reloading faster.

		Core.Instance = None

		if settings:
			Core.Hosters = None
			Core.ServicesDebrid = None
			Core.ServicesExternal = None

	##############################################################################
	# PROPERTY
	##############################################################################

	@classmethod
	def propertyItems(self, load = True):
		'''
			This function can take very long, around 2-4 seconds for each 100 links.
			Makes reloading the streams window and sequential playback very slow.
			Binge watching has been improved using a waiting background process, so that in most cases propertyItems() does not need to be called.
			However, reloading and sequential playback still remains slow.
			Slightly less than half the time is used for Converter.jsonFrom().
		'''
		'''
			It might seem intuitive that reloading the stream window could be made faster when using reuselanguageinvoker.
			The raw Stream objects could be stored in a global variable and quickly accessed using the same interpreter when reloading the stream window, avoiding the computationally expensive:
				Stream.dataImport(Converter.jsonFrom(...))
			However, this does not work, since a new interpreter is used every time we start playback from the stream window (handle -1).

			Currently the scraping process is started with a new interpreter (handle -1). This could be changed to reuse the interpreter, by marking all items in the movie/show menus as folders.
				meta -> tools.py -> items() -> items.append([item['command'], item['item'], True])
			This will at least reuse the interpreter for scraping and the stream window.

			However, when initiating playback from the stream window, it ALWAYS starts a new interpreter. This is because the listItem URL/path is not executed in custom XML windows.
			Even when adding an XML button with an <onclick> event, the event is never fired. In order for an action to be executed with custom XML:
				window.py -> WindowStream -> _actionSelect()
			which in turn calls:
				tools.System.executePlugin()
			which will always start a new interpreter and the handle is -1.

			There seems to be no way around this. For Kodi to reuse the interpreter, one of these has to be done:
				1. Create a directory and make sure that ListItems have "isFolder = True".
				2. Create ListItems with the property "IsPlayable = 'true'".
				   When using this option, Kodi will show a "Player: skipping unplayable item: 0, path [plugin://…]" error in the log with the entire plugin command printed out.
				   Even when using "xbmcplugin.setResolvedUrl()", it seems there is no way to get rid of this error (setting the success parameter to True or False, using a fake ListItem, using the original ListItem store in a global variable, etc).
				   Even if we would just ignore this error in the log, it still does not allow playback initiated from the stream window to reuse the interpreter, even if we set "IsPlayable" on the items added to the window.
				   It seems that IsPlayable and isFolder are only applicable to Kodi directories/dialogs, but are ignored if set in a custom XML.

			A new Listitem property was added for Kodi 20: ForceResolvePlugin. Maybe that can be used to somehow fix issues with xbmcplugin.setResolvedUrl().
		'''

		if not Core.GlobalItems is None: return Core.GlobalItems

		items = window.Window.propertyGlobal(Core.PropertyItems)
		if items:
			items = tools.Converter.jsonFrom(items)
			if items and load:
				for i in range(len(items)):
					# Using dataImport() is about twice as fast as load().
					# We do not need to validate, cache, etc, since we know these streams were already fully processed bbefore being saved to the global property.
					#items[i]['stream'] = Stream.load(data = items[i]['stream'])
					stream = Stream()
					stream.dataImport(data = items[i]['stream'], full = True)
					items[i]['stream'] = stream
		return items

	@classmethod
	def propertyItemsSet(self, items, wait = False):
		Core.GlobalItems = items
		def _propertyItemsSet(items):
			if Core.GlobalItemsJson:
				window.Window.propertyGlobalSet(Core.PropertyItems, Core.GlobalItemsJson)
				Core.GlobalItemsJson = None
			else:
				window.Window.propertyGlobalSet(Core.PropertyItems, tools.Converter.jsonTo(items))
		if wait: _propertyItemsSet(items = items)
		else: Core.GlobalThreads.append(Pool.thread(target = _propertyItemsSet, kwargs = {'items' : items}, start = True))

	@classmethod
	def propertyItemsPrepare(self, items, wait = False):
		Core.GlobalItemsJson = None
		def _propertyItemsPrepare(items):
			Core.GlobalItemsJson = tools.Converter.jsonTo(items)
		if wait: _propertyItemsPrepare(items = items)
		else: Core.GlobalThreads.append(Pool.thread(target = _propertyItemsPrepare, kwargs = {'items' : items}, start = True))

	@classmethod
	def propertyItemsClear(self):
		Core.GlobalItems = None
		window.Window.propertyGlobalClear(Core.PropertyItems)

	@classmethod
	def propertyMetadata(self):
		if not Core.GlobalMetadata is None: return Core.GlobalMetadata
		metadata = window.Window.propertyGlobal(Core.PropertyMetadata)
		if metadata: metadata = tools.Converter.jsonFrom(metadata)
		return metadata

	@classmethod
	def propertyMetadataSet(self, metadata, wait = False):
		Core.GlobalMetadata = metadata
		def _propertyMetadataSet(metadata):
			if Core.GlobalMetadataJson:
				window.Window.propertyGlobalSet(Core.PropertyMetadata, Core.GlobalMetadataJson)
				Core.GlobalMetadataJson = None
			else:
				window.Window.propertyGlobalSet(Core.PropertyMetadata, tools.Converter.jsonTo(metadata))
		if wait: _propertyMetadataSet(metadata = metadata)
		else: Core.GlobalThreads.append(Pool.thread(target = _propertyMetadataSet, kwargs = {'metadata' : metadata}, start = True))

	@classmethod
	def propertyMetadataPrepare(self, metadata, wait = False):
		Core.GlobalMetadataJson = None
		def _propertyMetadataPrepare(metadata):
			Core.GlobalMetadataJson = tools.Converter.jsonTo(metadata)
		if wait: _propertyMetadataPrepare(metadata = metadata)
		else: Core.GlobalThreads.append(Pool.thread(target = _propertyMetadataPrepare, kwargs = {'metadata' : metadata}, start = True))

	@classmethod
	def propertyMetadataClear(self):
		Core.GlobalMetadata = None
		window.Window.propertyGlobalClear(Core.PropertyMetadata)

	@classmethod
	def propertyWait(self):
		[thread.join() for thread in Core.GlobalThreads]

	@classmethod
	def propertyExtras(self, load = True):
		extras = window.Window.propertyGlobal(Core.PropertyExtras)
		if extras:
			extras = tools.Converter.jsonFrom(extras)
			if extras and load:
				for i in range(len(extras)):
					extras[i]['stream'] = Stream.load(data = extras[i]['stream'])
		return extras

	@classmethod
	def propertyExtrasSet(self, extras):
		return window.Window.propertyGlobalSet(Core.PropertyExtras, tools.Converter.jsonTo(extras))

	@classmethod
	def propertyExtrasClear(self):
		window.Window.propertyGlobalClear(Core.PropertyExtras)

	@classmethod
	def propertyProcess(self):
		return tools.Converter.boolean(window.Window.propertyGlobal(Core.PropertyProcess))

	@classmethod
	def propertyProcessSet(self, process = True):
		return window.Window.propertyGlobalSet(Core.PropertyProcess, process)

	@classmethod
	def propertyProcessClear(self):
		window.Window.propertyGlobalClear(Core.PropertyProcess)

	@classmethod
	def propertyStatus(self):
		return window.Window.propertyGlobal(Core.PropertyStatus)

	@classmethod
	def propertyStatusSet(self, status):
		return window.Window.propertyGlobalSet(Core.PropertyStatus, status)

	@classmethod
	def propertyStatusClear(self):
		window.Window.propertyGlobalClear(Core.PropertyStatus)

	@classmethod
	def propertyNotification(self):
		return tools.Converter.boolean(window.Window.propertyGlobal(Core.PropertyNotification))

	@classmethod
	def propertyNotificationSet(self, notification = True):
		return window.Window.propertyGlobalSet(Core.PropertyNotification, notification)

	@classmethod
	def propertyNotificationClear(self):
		window.Window.propertyGlobalClear(Core.PropertyNotification)

	@classmethod
	def propertySilent(self):
		silent = window.Window.propertyGlobal(Core.PropertySilent)
		if silent == Core.SilentCancel or silent == Core.SilentInteract: return silent
		else: return tools.Converter.boolean(silent)

	@classmethod
	def propertySilentSet(self, silent = True):
		return window.Window.propertyGlobalSet(Core.PropertySilent, silent)

	@classmethod
	def propertySilentClear(self):
		window.Window.propertyGlobalClear(Core.PropertySilent)

	def propertySilentCheck(self, wait = False):
		def _propertySilentCheck():
			# We wait a maximum of 2x 10 minutes (when binge scraping starts).
			# Wait longer, in case the user pauses playback for some time, or takes time to rate in the rating dialog after playback.
			# Do not wait forever, just in case the global Kodi property is not set (eg: something is canceled or exception is thrown).
			# Otherwise this thread might run forever.

			from lib.modules.player import Player
			from lib.modules.interface import Player as PlayerBase
			player = PlayerBase()
			finished = False

			wait = tools.Binge.scrape()
			wait += min(wait, 900) # Add a max overlap time of 15 mins, since the user can increase the binge scraping time. Eg: user pauses for a few minutes after binge scraping started.

			step = 0.5
			for i in range(int(wait / step)):
				# Make sure the loop is exited once the player stops playing.
				# Otherwise this loop continues even though binging was continued/cancled.
				busy = player.isPlayingVideo() and not tools.System.aborted()
				if not busy and not self.propertyStatus() == Core.StatusScrape: # Do not execute this if playback stopped before scraping finished.
					tools.Time.sleep(step)
					finished = True

					# Allow enough time for player.py to call propertyStatusSet() with a new value.
					for j in range(30):
						tools.Time.sleep(0.1)
						if not self.propertyStatus() == Core.StatusFinalize: break

				silent = self.propertySilent()
				if silent == Core.SilentCancel:
					break
				elif not silent == Core.SilentInteract:
					if not silent == self.silent:
						self.silent = silent
						status = self.propertyStatus()
						# Do not popup the scraping window if background scraping has finished.
						# Directly move to the stream window, or the playback window for autopack.
						if status == Core.StatusFinished:
							interface.Loader.show()
						elif not status == Core.StatusFinalize:
							self._scrapeProgressShow()
							self._scrapeProgressUpdate()
						break
					elif finished:
						break

				if tools.System.aborted(): break
				tools.Time.sleep(step)

		if self.silentThread is None:
			self.propertySilentSet(self.silent)
			self.silentThread = Pool.thread(target = _propertySilentCheck)
			self.silentThread.start()
		if wait: self.silentThread.join(wait if tools.Tools.isNumber(wait) else None)

		silent = self.propertySilent()
		return silent and not silent == Core.SilentCancel and not silent == Core.SilentInteract

	def parameterize(self, action = None, media = None, parameters = None):
		if parameters is None:
			if media is None: media = self.media
			if not media is None: action += '&media=%s' % media
			return action
		else:
			if media is None: media = self.media
			if not media is None: parameters['media'] = media
			return parameters

	def loaderShow(self):
		if not self.silent: interface.Loader.show()

	def loaderHide(self):
		if not self.silent:
			if not(self.autoplay and self.binge == tools.Binge.ModeContinue):
				interface.Loader.hide()

	def progressFailure(self, single = False):
		if not self.silent:
			self.loaderHide()
			interface.Dialog.notification(title = 33448, message = 32401 if single else 32402, icon = interface.Dialog.IconError)

	def progressNotification(self, loader = False, force = False, mixed = False):
		# Check if the dialog was already shown.
		# Otherwise the notification might be shown twice if:
		#    1. Streams are shown in the directory structure.
		#    2. Playback fails or cache download starts.
		# If playback doesn't start, the directory structure is reloaded and showStreams() is called again.
		if not self.silent:
			if not self.propertyNotification() or force:
				self.progressClose(force = True, loader = loader)
				if (not self.filter or self.filter['initial'] == 0) and not mixed:
					window.WindowBackground.close()
					interface.Dialog.notification(title = 33448, message = 35372, icon = interface.Dialog.IconError)
				elif self.filter:
					counts = []
					counts.append((33497, self.filter['initial'] if self.filter['initial'] else 0))
					counts.append((35453, self.filter['exclusion'] if self.filter['exclusion'] else 0))
					counts.append((35455, self.filter['limit'] if self.filter['limit'] else 0)) # Include the limited count, in case the number of streams are limited.
					counts = interface.Format.iconJoin(['%s: %d' % (interface.Translation.string(i[0]), i[1]) for i in counts])
					interface.Dialog.notification(title = 35373, message = counts, icon = interface.Dialog.IconWarning if self.filter['filter'] == 0 else interface.Dialog.IconSuccess, time = 5000)
			if self.filter and self.filter['final'] == 0 and self.filter['initial'] > 0:
				# Always show unfiltered results without asking first if:
				#	1. We are currently bingeing.
				#	2. The user has the default filter configuration.
				#	3. There are less than 100 unfiltered streams.
				if self.binge or Settings.settingsFilterDefault() or self.filter['initial'] <= 100:
					result = True
				else:
					self.loaderHide()
					result = interface.Dialog.option(title = 33448, message = 35380)
				if result: self.loaderShow()
				else: window.WindowBackground.close()
				return result
			else:
				self.propertyNotificationSet(True)
		return False

	def progressClose(self, loader = True, force = False, immediate = False):
		if self.navigationCinema:
			self.navigationCinemaTrailer.cinemaStop() # Eg if no streams were found.
		if not self.silent:
			if self.navigationScrapeSpecial:
				if force or not self.navigationStreamsSpecial or self.autoplay:
					if not immediate: window.WindowScrape.update(finished = True)
					window.WindowScrape.close()
			else:
				interface.Core.close()
				if force: interface.Dialog.closeAllProgress() # If called from another process, the interface.Core instance might be lost. Close all progress dialogs.
			if loader: self.loaderHide()
		tools.Hardware.usageStop()

	def progressCanceled(self):
		if not self.silent:
			if self.navigationCinema:
				return self.navigationCinemaTrailer.cinemaCanceled()
			elif self.navigationScrapeSpecial:
				try:
					if tools.System.aborted():
						tools.System.exit()
						return True
				except: pass

				# Only assume that if WindowScrape is not visible that it was canceled, if it was previously visible.
				# This is important for binge watching where the next scraping is still busy when the current video playback finishes.
				# From player.py -> propertySilentSet(False) -> this will make the current binge scrape progress to show, but it might stop immediatly because the scraping window has not been loaded yet, but progressCanceled() checks the visibility.
				if self.progressVisible: return not window.WindowScrape.visible()
				else: self.progressVisible = window.WindowScrape.visible()
			else:
				if interface.Core.background():
					return False
				else:
					try:
						if tools.System.aborted():
							tools.System.exit()
							return True
					except: pass
					return interface.Core.canceled()
		return False

	def progressPlaybackEnabled(self):
		return self.navigationPlaybackSpecial

	def progressPlaybackInitialize(self, title = None, message = None, metadata = None, force = False, loader = True):
		if not self.silent:
			if not force and (self.navigationCinema and self.autoplay):
				self.mLastTitle = title
				interface.Dialog.notification(title = title, message = message, icon = interface.Dialog.IconInformation)
			else:
				if self.navigationPlaybackSpecial:
					self.progressClose(loader = loader) # For autoplay.
					try: background = MetaImage.extract(data = metadata)['fanart']
					except: background = None
					window.WindowPlayback.show(background = background, status = message)

					def _progressClose():
						tools.Time.sleep(1)
						window.WindowScrape.close()
						window.WindowBackground.close() # Might still be open from player.py -> interact() to allow a continues background during rating/continue/next-episode-playback.
					Pool.thread(target = _progressClose, start = True)
				else:
					if message is None: message = ''
					else: message = interface.Format.fontBold(message) + '%s'
					interface.Core.create(type = interface.Core.TypePlayback, background = self.navigationPlaybackBar, title = title, message = message, progress = 0)
					if interface.Core.background() and loader: self.loaderHide()

	def progressPlaybackUpdate(self, progress = None, title = None, message = None, status = None, substatus1 = None, substatus2 = None, total = None, remaining = None, force = False):
		if not self.silent:
			if force or not self.navigationCinema or not self.autoplay:
				if self.navigationPlaybackSpecial:
					if status is None: status = message
					window.WindowPlayback.update(progress = progress, status = status, substatus1 = substatus1, substatus2 = substatus2, total = total, remaining = remaining)
				else:
					if message is None: message = ''
					else: message = interface.Format.fontBold(message) + '%s'
					interface.Core.update(progress = progress, title = title, message = message)

	def progressPlaybackClose(self, background = True, loader = True, force = False):
		if not self.silent:
			self.progressPlaybackUpdate(progress = 100)

			if self.navigationPlaybackSpecial:
				window.WindowPlayback.update(finished = True)
				window.WindowPlayback.close()
				if background: window.WindowBackground.close()
			else:
				interface.Core.close()
				if force: interface.Dialog.closeAllProgress() # If called from another process, the interface.Core instance might be lost. Close all progress dialogs.
			if loader and not self.reload: self.loaderHide() # Do not close if we are busy reloading the stream window from player.py. Otherwise there is a short time where there is neither a loader, not the stream loading window.

	def progressPlaybackCanceled(self):
		if not self.silent:
			if self.downloadCanceled:
				return True
			elif self.navigationPlaybackSpecial:
				try:
					if tools.System.aborted():
						tools.System.exit()
						return True
				except: pass
				return window.WindowPlayback.canceled()
			else:
				if interface.Core.background():
					return False
				else:
					try:
						if tools.System.aborted():
							tools.System.exit()
							return True
					except: pass
					if interface.Core.canceled():
						interface.Player().stop() # If the playback has started but Kodi cannot connect and/or start streaming (stuck at "Establishing Stream Connection").
						return True
		return False

	##############################################################################
	# BINGE
	##############################################################################

	def bingeStart(self, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, notification = True, scrape = True):
		from lib.modules.playback import Playback

		last = Playback.instance().historyLast(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number)
		if last and not last.get('episode') is None:
			season = last.get('season')
			episode = last.get('episode')
		else:
			if episode: episode = max(0, episode - 1) # Starting to binge from a specific episode.
		if season is None: season = 1
		if episode is None: episode = 0

		if scrape: interface.Loader.show()
		metadata = MetaManager.instance().metadataEpisodeNext(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

		aired = False
		if metadata:
			premiered = None
			for i in ['aired', 'premiered']:
				premiered = metadata.get(i)
				if premiered: break
			if premiered:
				# Check <= instead of <, since we only deal with dates and not times, hence we cannot compare on an hourly basis, but only on a daily basis.
				# Important for shows where all episodes are released on the same day.
				premiered = tools.Time.integer(premiered)
				today = tools.Time.integer(tools.Time.past(hours = 3, format = tools.Time.FormatDate))
				if premiered < today: aired = True

		if (not metadata or not aired) and notification:
			interface.Loader.hide()
			interface.Dialog.notification(title = 35580, message = 35587, icon = interface.Dialog.IconWarning)
		elif metadata and scrape:
			interface.Dialog.notification(title = 35580, message = interface.Translation.string(35599) % (metadata.get('tvshowtitle'), tools.Title.number(metadata = metadata)), icon = interface.Dialog.IconSuccess)
			self.scrape(binge = True, tvshowtitle = metadata.get('tvshowtitle'), title = metadata.get('title'), year = metadata.get('year'), imdb = metadata.get('imdb'), tmdb = metadata.get('tmdb'), tvdb = metadata.get('tvdb'), trakt = metadata.get('trakt'), season = metadata.get('season'), episode = metadata.get('episode'), metadata = metadata)
		elif not scrape:
			interface.Loader.hide()
		return metadata

	##############################################################################
	# SCRAPE
	##############################################################################

	def scrape(self, title = None, tvshowtitle = None, year = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, premiered = None, metadata = None, pack = None, autoplay = None, autopack = None, preset = None, library = None, exact = False, items = None, process = True, binge = None, cache = True):
		try:
			self.propertyStatusSet(Core.StatusInitialize)

			# External addons (eg OpenMeta) does not call functions correctly, and the type might not be set.
			if self.media is None: self.media = tools.Media.Show if season or episode else tools.Media.Movie

			if binge == tools.Binge.ModeBackground:
				self.propertySilentCheck()
			elif binge == tools.Binge.ModeContinue:
				# Loader still showing after continuing with binge watching.
				# The loader is shown in _bingePlay in the player.
				# Update: not sure if the hiding the loader should be enabled again. This causes the loader to be hidden while propertyItems() executes for 5-10 seconds.
				#if self.navigationStreamsSpecial and binge == tools.Binge.ModeContinue: self.loaderHide()
				if items is None: items = self.propertyItems()
			else:
				# Only do this if it is not a binge scrape.
				# That is, the user manually started the scraping, aka interacted.
				tools.Observer.updateInteractScrape()

				if not self.silent: tools.Sound.executeScrapeStart()

			#self.propertyItemsClear() # Do not do this, since the background binge scrape will reset these values, making reloading the stream window impossible if playback is paused in the middle.

			if library is None: library = tools.System.originLibrary() or False

			# When the play action is called from the skin's widgets.
			# Otherwise the directory with streams is not shown.
			# Only has to be done if accessed from the home screen. Not necessary if the user is already in a directory structure.
			# Check for tools.Binge.ModeBackground. Seems to be an issue on Mac devices causing the episode direcotry list to be loaded if binge scraping happens in the background.
			if not binge == tools.Binge.ModeBackground and self.navigationStreamsDirectory and not tools.System.originGaia() and not tools.System.originPlaylist(): tools.System.launchAddon()

			self.binge = binge
			self.new = items is None
			if not self.navigationCinema: self.loaderShow()
			self.propertyNotificationClear()
			if binge is None or binge == tools.Binge.ModeBackground: binge = tools.Binge.ModeFirst if tools.Binge.enabled() else tools.Binge.ModeNone
			if cache is None: cache = True

			if autoplay is None:
				if tools.Converter.boolean(window.Window.propertyGlobal('PseudoTVRunning')): autoplay = True
				else: autoplay = self.autoplay

			# Show here for autoplay. Manual is shown after the streams are listed.
			#if autoplay and not self.silent: tools.Donations.popup() # Do not show here, since users might just want to play. Show the donation dialog on Gaia launch.
			tools.Donations.increment()

			if tools.Tools.isString(metadata): metadata = tools.Converter.jsonFrom(metadata)

			# Retrieve metadata if not available.
			# Applies to links from Kodi's local library or when launched from an external addon. The metadata cannot be saved in the link, since Kodi cuts off the link if too long. Retrieve it here afterwards.
			if not exact:
				manager = MetaManager.instance()

				if not metadata:
					if tvshowtitle or not season is None:
						# Lookup using a specific numbering system if explicity stated. Otherwise use the universal numbers.
						# This is useful for the _scrapeNumber() when the same number can mean different things.
						# Eg: Star Wars: Young Jedi Adventures S01E26 (under the S01 menu, TVDb has this as the uncombined episode S01E26, whereas under the Absolute menu this maps to the Trakt/TMDb episode S02E01).

						# For Donwton Abbey -> Absolute menu -> S01E00 (Christmas Specials).
						lookup = number
						if number == MetaPack.NumberSequential and not season == 1: lookup = MetaPack.NumberStandard

						metadata = manager.metadataEpisode(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = tvshowtitle if tvshowtitle else title, year = year, season = season, episode = episode, number = lookup, filter = True)
					else:
						metadata = manager.metadataMovie(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, filter = True)

					if not metadata:
						interface.Dialog.notification(title = 33458, message = 33459, icon = interface.Dialog.IconError)
						self.progressClose(force = True)
						return

			# Ask the user if the episode is available under alternative numbers.
			ignore = False
			change = self._scrapeNumber(metadata = metadata, number = number)
			if change:
				#gaiaremove - this can be removed once proper absolute and season-absolute numbering is correctly filtered.
				# This ignores seasons that are very different between Trakt/TMDb and TVDb.
				# Still allow specials (S00) and absolute (S01).
				# See the comments at the top of tester.py.
				# Eg: One Piece S03E01
				#	Gaia: S03E01
				#	Trakt/TMDb: S03E78
				#	TVDb: S06E09 (one scraped link was valid for E78, but the rest is for Trakt/TMDb's S06. Ignore this one, as it is also the number for a different episode.)
				#	Absolute: S01E78
				#gaiaremove - Also ignore absolute scrapes for now, since those packs are almost always for the normal S01, not the absolute S01 with all episodes.
				# Maybe for absolute scraping, only check the episode numbers, not the season number.
				# Eg: One Piece Collection 1-648 + 4 Movies
				# Also test this when initiated from the Absolute menu vs from a season menu and then changing the number in the dialog.
				numbers = metadata.get('number') or {}
				numberStandard = numbers.get(MetaPack.NumberStandard) == [change['season'], change['episode']]
				try: numberTrakt = numbers.get(MetaPack.ProviderTrakt).get(MetaPack.NumberStandard)[MetaPack.PartSeason] == change['season'] # Eg: One Piece S01E62 (Absolute menu) and then selecting S02E62.
				except: numberTrakt = False
				if change['season'] > 1 and not change['season'] == season and not change['number'] == MetaPack.NumberStandard and not numberStandard and not numberTrakt: ignore = True
				elif MetaPack.NumberAbsolute in change['number'] or MetaPack.NumberSequential in change['number']:
					if (MetaPack.NumberAbsolute in number or MetaPack.NumberSequential in number) and not numberStandard: ignore = True # When an absolute number is selected in from the Absolute menu.
					elif not change['episode'] == episode: ignore = True # When an absolute number is selected in from the dialog.

				# Retrieve the metadata if the number changed, in order to get the correct metadata (title, number, etc).
				changed = not(change['season'] == season and change['episode'] == episode and (change['number'] == (number or MetaPack.NumberStandard)))
				if changed:
					season = change['season']
					episode = change['episode']
					number = change['number']
					if number and tools.Tools.isArray(number): number = number[0]
					metadata = manager.metadataEpisode(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = tvshowtitle if tvshowtitle else title, year = year, season = season, episode = episode, number = number, filter = True)
			elif change is False: # Canceled.
				self.progressClose(force = True)
				return

			# Do after the new metadata has been retrieved.
			if metadata:
				imdb = metadata.get('imdb')
				tmdb = metadata.get('tmdb')
				tvdb = metadata.get('tvdb')
				trakt = metadata.get('trakt')

				title = metadata.get('title')
				tvshowtitle = metadata.get('tvshowtitle')
				year = metadata.get('year')

				season = metadata.get('season')
				episode = metadata.get('episode')

				pack = metadata.get('pack')

			if not pack and (tvshowtitle or not season is None):
				pack = manager.metadataPack(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = tvshowtitle if tvshowtitle else title, year = year)

			history.History().add(media = self.media, metadata = metadata) # If already added, will just increase the counter.

			if exact: self.scrapeLabel = title if title else tvshowtitle
			else: self.scrapeLabel = tools.Title.titleUniversal(metadata = metadata, title = title if tvshowtitle is None else tvshowtitle, year = year, season = season, episode = episode)

			# Clear temporary filter settings.
			# Must be before self.scrapeItem().
			if not self.silent: self._showClear()

			# Clear any possible invalid data if we reuse the invoker.
			Stream.invalidClear()

			if self.new:
				if not self.silent and self.navigationCinema:
					try: background = MetaImage.extract(data = metadata)[MetaImage.TypeFanart]
					except: background = None
					self.navigationCinemaTrailer.cinemaStart(media = self.media, background = background)
				tools.Logger.log('Scraping Initialized', name = 'CORE', type = tools.Logger.TypeInfo)

				self.timerTotal = None
				self.timerGlobal = tools.Time(start = True)
				self.propertyStatusSet(Core.StatusScrape)

				result = self.scrapeItem(title = title, year = year, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, tvshowtitle = tvshowtitle, premiered = premiered, metadata = metadata, pack = pack, preset = preset, exact = exact, autoplay = autoplay, cache = cache)

				if result is None or (self.progressCanceled() and not self.navigationCinema): # Avoid the no-streams notification right after the unavailable notification.
					self.progressClose(force = True)
					self.propertyStatusSet(Core.StatusFinished)
					return None
				try:
					if not exact and not ignore:
						api = orionoid.Orionoid(silent = True)
						if api.accountAllow(): api.streamUpdate(metadata, self.sources)
				except: pass
			else:
				self.timerGlobal = tools.Time(start = True)
				if tools.Tools.isString(items): items = tools.Converter.jsonFrom(items)
				self.sources = items

			self.sources = self.sourcesPrepare(items = self.sources)

			# Calling propertyItemsSet() can take a long time converting to JSON if the are 100s or 1000s of streams.
			# This consumes processing power and the round progress bar in the rating/continue window takes a few seconds to update for the first time (in WindowRating._progress()).
			# Convert to JSON here already, so free up the CPU if the current episode is done.
			# UPDATE: Seems the problem is somewhere else which holds up the animation. But leave this here, since it cannot hurt to do this earlier.
			if self.binge == tools.Binge.ModeBackground:
				self.propertyItemsPrepare(self.sources, wait = True)
				self.propertyMetadataPrepare(metadata, wait = True)

			if self.new and Termination.settingsEnabled() and Termination.settingsMode() == Termination.ModeOverwrite:
				autoplay = self.terminated or self.timerGlobal.elapsed() < ProviderBase.settingsGlobalLimitTime()

			self.propertyStatusSet(Core.StatusFinalize)

			# Measure the time here, since the propertySilentCheck() below could wait 10 mins or more.
			# Otherwise the total time in the scrape report will be too high for background binge scraping.
			self.timerTotal = self.timerGlobal.elapsed()

			# There are 2 ways in which binge scraping can be done.
			#	1. Run the background scraping, let the process finish, and after playback call scrape again which will pull the streams using self.propertyItems().
			#	   This can take a long time, since self.propertyItems() can take 5-10 seconds for a few 100 streams, since they all have to be loaded from JSON again.
			#	2. Run the background scraping, but once scraping is finished just sleep. Once playback is finished, just wake up again and continue the code below to show the streams or continue autoplay.
			#	   This is faster, since the streams don't have to be loaded again.
			# The if-statement below can be removed and binge scraping should still work, but will end up with solution #1 above, aka slow.
			# Note that propertySilentCheck() will not wait forever, but time out at some point.
			# If the user pauses playback for a long time, or takes considerable time to rate in the rating dialog (eg goes a grabs some popcorn between episodes), propertySilentCheck() might timeout.
			# In this case, the user will just have to wait a few seconds for the next stream window to load with #1.
			# If the user doesn't wait between episodes, then this waiting will work with #2 and loading time will be faster.
			if self.binge == tools.Binge.ModeBackground:
				if not self.propertySilentCheck(wait = True):
					self.silent = False
					if autoplay: self.loaderShow()
				if tools.System.aborted(): return None

			# Restart here and add to self.timerTotal in scrapeStatistics().
			self.timerGlobal = tools.Time(start = True)

			# Do not set these values if playback was stopped in the middle during binge playback.
			# Ensures that the stream window is reloaded for an unfinished episode.
			if not self.propertyStatus() == Core.StatusCancel:
				self.propertyExtrasClear()
				self.propertyItemsSet(self.sources)
				self.propertyMetadataSet(metadata)
				self.propertyProcessSet(process)

			# NB: Must be set here instead of AFTER self._autopack()/self.showStreams().
			# Otherwise during binging, this status is only set AFTER the current episode playback finished, which sometimes sporadically interferes with the global status property of the NEXT episode being started.
			# This in some cases causes the next episode to be played to start 2 playback processes after each other. The 1st one gets cancled quickly, and the 2nd one plays as intended.
			status = self.propertyStatus() # We need the old value for the the code below.
			self.propertyStatusSet(Core.StatusFinished)

			# Do not play the sound if autoplay and there is also a sound for starting streaming, otherwise they will collide.
			if not self.silent and not self.binge and not status == Core.StatusCancel and (not autoplay or not tools.Sound.enabledStreamStart()): tools.Sound.executeScrapeFinish()

			if self.silent or status == Core.StatusCancel:
				self.sourcesFilter(items = self.sources, metadata = metadata, autoplay = autoplay)
				self.scrapeStatistics()
				self.progressClose(force = True, immediate = True) # Important when "Cancel" (not "Stop") is clicked in the Continue dialog.
			elif not autoplay and self._autopack(id = autopack, metadata = metadata, binge = binge):
				pass
			elif not self.progressPlaybackCanceled(): # Do not show the streams if the playback window was canceled in _autopack().
				self.showStreams(items = self.sources, metadata = metadata, autoplay = autoplay, initial = True, library = library, direct = exact, new = self.new, process = process, binge = binge)

			self.scrapeResolve()
			return self.sources
		except:
			tools.Logger.error()
			self.progressClose(force = True)
		finally:
			# Clear the stream data, settings, filters, etc, in case we reuse the invoker.
			Stream.reset(invalid = False) # Do not clear invalid, since they arte still used by Orion. This is cleared at the end of addon.py in any case.
			ProviderManager.reset()

	def _scrapeNumber(self, metadata, number = None):
		# Test this with:
		#	One Piece:
		#		Absolute Menu: S01E61, S01E62
		#		S00 Menu: S00E42/S00E19
		#		S02 Menu: S02E01, S02E16, S02E17
		#		S03 Menu: S03E01
		#	Dragon Ball Super:
		#		Absolute Menu: S01E14, S01E15, S01E28
		#		S01 Menu: S01E14, S01E15
		#		S02 Menu: S02E01
		#	Downton Abbey:
		#		Absolute Menu: S01E00, S01E16
		#		S02 Menu: S02E09
		#	Star Wars: Young Jedi Adventures
		#		Absolute Menu: S01E25, S01E26
		#		S01 Menu: S01E25, S01E26

		try:
			if not self.silent and tools.Media.isEpisode(metadata.get('media')):
				setting = tools.Settings.getInteger('scrape.alternative.number')
				if setting == 0: return None

				def _mergeNumber(values, *extra):
					if values:
						number = [i['number'] for i in values if i['number']]
						if extra:
							for i in extra:
								i = i.get('number')
								if i: number.extend(i)
						number = tools.Tools.listUnique(number)
						return {'season' : values[0].get('season'), 'episode' : values[0].get('episode'), 'number' : number or None}
					return None

				def _mergeLabel(values, provider = True, exclude = False):
					if values:
						label = []
						for i in values:
							if exclude and any(i['season'] == j['season'] and i['episode'] == j['episode'] for j in exclude): continue
							number = _mergeProvider(i['number'])
							if number:
								title = interface.Format.fontBold(tools.Title.number(media = tools.Media.Episode, season = i['season'], episode = i['episode']))
								if provider: label.append('%s (%s)' % (title, number))
								else: label.append('%s' % title)
						if label: return ', '.join(label)
					return None

				def _mergeProvider(values):
					if values:
						# Order matters for readability.
						label = []
						if MetaPack.NumberStandard in values or MetaPack.NumberSequential in values: label.append(35639)
						if MetaPack.ProviderTrakt in values: label.append(32315)
						if MetaPack.ProviderTvdb in values: label.append(35668)
						if MetaPack.ProviderTmdb in values: label.append(33508)
						if MetaPack.ProviderImdb in values: label.append(32034)
						if label: return '/'.join([interface.Translation.string(i) for i in label])
					return None

				metadata2 = MetaManager.instance().metadataEpisode(imdb = metadata.get('imdb'), tmdb = metadata.get('tmdb'), tvdb = metadata.get('tvdb'), trakt = metadata.get('trakt'), season = metadata.get('season'), episode = metadata.get('episode'), number = MetaPack.NumberStandard, filter = True)

				base = metadata.get('number') or {}
				season = metadata.get('season')
				episode = metadata.get('episode')

				packed = metadata.get('packed') or {}
				type = packed.get('type') or {}

				pack = metadata.get('pack')
				if pack: pack = MetaPack.instance(pack)

				niche = metadata.get('niche')
				niche = tools.Media.isAnime(niche) or tools.Media.isDonghua(niche)
				sequential = number == MetaPack.NumberSequential or type.get(MetaPack.NumberSequential) or niche

				numbers = [{'number' : None, 'season' : season, 'episode' : episode}]

				numberStandard = base.get(MetaPack.NumberStandard)
				if numberStandard and not numberStandard[MetaPack.PartEpisode] is None: numbers.append({'number' : MetaPack.NumberStandard, 'season' : numberStandard[MetaPack.PartSeason], 'episode' : numberStandard[MetaPack.PartEpisode]})

				if sequential:
					# Exclude sequential numbers S01E00.
					# Eg: Donwton Abbey -> Absolute menu -> S01E00 (Christmas Specials).
					numberSequential = base.get(MetaPack.NumberSequential)
					if numberSequential and numberSequential[MetaPack.PartEpisode]: numbers.append({'number' : MetaPack.NumberSequential, 'season' : numberSequential[MetaPack.PartSeason], 'episode' : numberSequential[MetaPack.PartEpisode]})

				for provider, i in base.items():
					if tools.Tools.isDictionary(i):
						numberSeasoned = i.get(MetaPack.NumberStandard)
						if numberSeasoned and not numberSeasoned[MetaPack.PartEpisode] is None: numbers.append({'number' : provider, 'season' : numberSeasoned[MetaPack.PartSeason], 'episode' : numberSeasoned[MetaPack.PartEpisode]})

				numbersDefault = {}
				numbersSeason = {}
				numbersSpecial = {}
				numbersSequential = {}

				for i in numbers:
					lookup = []
					value = i.get('number')

					if not value: lookup.append(numbersDefault)

					if value == MetaPack.NumberSequential: lookup.append(numbersSequential)
					elif i.get('season') == 0: lookup.append(numbersSpecial)
					else: lookup.append(numbersSeason)

					if lookup:
						id = (i.get('season'), i.get('episode'))
						for j in lookup:
							if not id in j: j[id] = []
							j[id].append(i)

				numbersDefault = [_mergeNumber(i) for i in numbersDefault.values()]
				numbersSeason = [_mergeNumber(i) for i in numbersSeason.values()]
				numbersSpecial = [_mergeNumber(i, {'number' : [MetaPack.NumberStandard]}) for i in numbersSpecial.values()]
				numbersSequential = [_mergeNumber(i, *numbersSeason, *numbersSpecial) for i in numbersSequential.values()]

				# Remove numbers that are the same between season and special/sequential.
				# Do not do for specials only.
				# Eg: One Piece S00E42.
				numbersSpecial = [i for i in numbersSpecial if season == 0 or not(i['season'] == season and i['episode'] == episode)]
				if not sequential: numbersSequential = [i for i in numbersSequential if not(i['season'] == season and i['episode'] == episode)]

				labelDefault = tools.Title.number(media = tools.Media.Episode, season = numbersDefault[0]['season'], episode = numbersDefault[0]['episode']) if numbersDefault else None
				labelSeason = _mergeLabel(numbersSeason)
				labelSequential = _mergeLabel(numbersSequential)
				labelSpecial = _mergeLabel(numbersSpecial)

				choose = False
				if labelSpecial:
					choose = True
				elif labelSequential:
					# Do not show a dialog if only TVDb has a season number different to the sequential number, since we do not scrape TVDb numbers.
					# Eg: One Piece -> Absolute menu -> S01E61 vs S01E62.
					# Update: Allow this now, since we added a "More" button which allows all numbers to be scraped.
					#numbersFilter = [i for i in numbersSeason if not(i['season'] == numbersSequential[0]['season'] and i['episode'] == numbersSequential[0]['episode'])]
					numbersFilter = numbersSeason

					if numbersFilter:
						if len(numbersFilter) > 1:
							choose = True
						else:
							numbering = numbersFilter[0]['number']
							if MetaPack.NumberStandard in numbering or MetaPack.ProviderTrakt in numbering: choose = True
							else:
								# Still allow if TVDb has the only season-based numbering.
								# Eg: Dragon Ball Super -> S01 menu -> S01E30.
								numbering = numbering[0]
								lookup = pack.episode(season = numbersFilter[0]['season'], episode = numbersFilter[0]['episode'], number = numbering)
								if lookup:
									# Check if other providers also have this season.
									# Allow for eg: Dragon Ball Super S01E14 vs S01E15.
									# Do not allow for eg: One Piece S01E61 vs S01E62.
									lookup2 = pack.numberStandard(item = lookup, provider = numbering)
									if lookup2:
										lookup2 = pack.episode(season = lookup2[MetaPack.PartSeason], episode = lookup2[MetaPack.PartEpisode], number = numbering)
										if pack.typeUnofficial(item = lookup2): choose = True
				elif len(numbersSeason) > 1:
					# Eg: Star Wars: Young Jedi Adventures S01E26.
					lookup1 = pack.episode(season = numbersSeason[0]['season'], episode = numbersSeason[0]['episode'], number = numbersSeason[0]['number'][0])
					lookup2 = pack.episode(season = numbersSeason[-1]['season'], episode = numbersSeason[-1]['episode'], number = numbersSeason[-1]['number'][0])
					if (pack.typeOfficial(item = lookup1) and pack.typeUnofficial(item = lookup2)) or (pack.typeOfficial(item = lookup2) and pack.typeUnofficial(item = lookup1)): choose = True

				if choose:
					option1 = tools.Tools.copy(numbersDefault[0])
					option1['number'] = number or MetaPack.NumberStandard

					if labelSpecial:
						option2 = next((i for i in numbersSpecial if not(i['season'] == option1['season'] and i['episode'] == option1['episode'])), numbersSpecial[0]) # Eg: One Piece S00E42.
						option2 = tools.Tools.copy(option2)
						if not option2['number']: option2['number'] = MetaPack.NumberStandard
					elif labelSequential and not(numbersSequential[0]['season'] == option1['season'] and numbersSequential[0]['episode'] == option1['episode']):
						option2 = next((i for i in numbersSequential if not(i['season'] == option1['season'] and i['episode'] == option1['episode'])), numbersSequential[0])
						option2 = tools.Tools.copy(option2)
						if not option2['number']: option2['number'] = MetaPack.NumberSequential
					else:
						option2 = next((i for i in numbersSeason if not(i['season'] == option1['season'] and i['episode'] == option1['episode'])), numbersSeason[0])
						option2 = tools.Tools.copy(option2)
						if not option2['number']: option2['number'] = MetaPack.NumberStandard

					if not(option1['season'] == option2['season'] and option1['episode'] == option2['episode']):
						if setting == 1:
							label1 = tools.Title.number(media = tools.Media.Episode, season = option1['season'], episode = option1['episode'])
							label2 = tools.Title.number(media = tools.Media.Episode, season = option2['season'], episode = option2['episode'])

							label = ''
							if labelSeason: label += interface.Format.fontNewline() + '   ' + interface.Format.fontBold('%s: ' % interface.Translation.string(32055)) + labelSeason
							if labelSpecial: label += interface.Format.fontNewline() + '   ' + interface.Format.fontBold('%s: ' % interface.Translation.string(33105)) + labelSpecial
							if labelSequential: label += interface.Format.fontNewline() + '   ' + interface.Format.fontBold('%s: ' % interface.Translation.string(36677)) + labelSequential

							message = interface.Translation.string(36678) % (interface.Format.fontBold(labelDefault), label)
							choice = interface.Dialog.options(title = 36679, message = message, labelConfirm = label2, labelDeny = 33432, labelCustom = interface.Format.fontBold(label1), default = interface.Dialog.ChoiceCustom)

							if choice == interface.Dialog.ChoiceYes:
								return option2
							elif choice == interface.Dialog.ChoiceCustom:
								return option1
							if choice == interface.Dialog.ChoiceNo:
								added = {}
								items = []
								values = []
								for i in [[numbersSeason, MetaPack.NumberStandard, 32055], [numbersSpecial, MetaPack.NumberSpecial, 33105], [numbersSequential, MetaPack.NumberSequential, 36677], [numbersDefault, number, 33564]]:
									for j in i[0]:
										id = '%s_%s_%s' % (j['season'], j['episode'], str(j.get('number')))
										if not id in added and j.get('number'):
											added[id] = True
											values.append(j)
											items.append('%s: %s' % (interface.Format.fontBold(i[2]), _mergeLabel([j])))

								choice = interface.Dialog.select(title = 36679, items = items)
								if choice >= 0: return values[choice]
								else: return False
							else:
								return False
						else:
							episode = None
							if setting == 2:
								episode = option1
							elif setting == 3:
								if numbersSpecial:
									episode = numbersSpecial[0]
									episode['number'] = MetaPack.NumberStandard
							elif setting == 4:
								if numbersSpecial:
									episode = numbersSpecial[0]
									episode['number'] = MetaPack.NumberStandard
								elif numbersSequential:
									episode = numbersSequential[0]
									episode['number'] = MetaPack.NumberSequential
							if not episode: episode = option1

							def _notify(wait = False):
								# Wait for the scraping window to show.
								# Otherwise the notification pops up first and is then displayed underneath the window and is not visible.
								if wait:
									for i in range(6):
										if window.WindowScrape.visible(): break
										tools.Time.sleep(0.5)

								labelSequential = _mergeLabel(numbersSequential, provider = False)
								labelSpecial = _mergeLabel(numbersSpecial, provider = False)
								labelSeason = _mergeLabel(numbersSeason, provider = False, exclude = numbersSequential + numbersSpecial)

								message = interface.Translation.string(36063) % (labelSpecial or labelSequential, labelSeason)
								interface.Dialog.notification(title = 36679, message = message, icon = interface.Dialog.IconInformation)

							if self.navigationScrapeSpecial: Pool.thread(target = _notify, kwargs = {'wait' : True}, start = True)
							else: _notify(wait = False)

							return episode
		except: tools.Logger.error()
		return None

	def scrapeResolve(self):
		# When launching a scrape process from a STRM file from the Kodi library, and then exiting the streams window, Kodi shows a dialog:
		#	Playback failed - One or more items failed to play. Check the log for more information abouth this message.
		# Setting the plugin call as resolved prevents this dialog from showing.
		# Do not set "success = True", since this does not work and actually makes Kodi call the plugin URI from the STRM file multiple times, hence, starting the scrape process multiple times after clicking on the title in the Kodi library.
		# Update: The duplicate call problem could probably be solved by using a dummy URL for pluginResolvedSet:
		#	plugin://plugin.video.gaia/?action=dummy
		# Kodi will then call the dummy URL which does nothing, without playing the 'scrape' action multiple times.
		# Update 2: It seems that the error dialog always has some places were it pops up.
		# Eg: add a movie to the playlist. Open t he playlist and play the movie from there. 1st time the dialog does not open. When navigating back and then opening the playlist again and play the movie again, the dialog shows.
		# Maybe Kodi expects the player to launch. If nothing is played, Kodi might assume the playback failed.
		# Update 3: Place this at the END of the scrape() function. If placed at the START of the scrape() function, Kodi for some reason still shows the dialog.
		# Update 3: Solves the issue when played from the local library. However, the dialog is still shown when played from the playlist (when the item is played the 2nd time, not the 1st time, from the playlist).
		# Update 4: These dialogs are now suppressed through advancedsettings.xml. Check tools.Playlist.settings() for more info.
		# Check the 3rd post here: https://forum.kodi.tv/showthread.php?tid=257787

		# Update 5 (2024-09-04):
		# There is another problem with playlists. If a scrape is initiated from the playlist, and the Python process finishes here, Kodi assumes the playback to have failed, and immediatly starts plyaing the enxt item from the playlist, although the user has not selected a stream for playback for the current item yet.
		# To reproduce:
		#	1. Add a title to the playlist.
		#	2. Add another title to the playlist.
		#	3. Open the playlist menu.
		#	4. Click on the first item.
		#	5. Scraping starts, and once finished loads the stream window.
		#	6. Once the stream window has finished loaded, scraping of the next item immediately starts.
		#	7. This error is in the log: Playlist Player: skipping unplayable item: 0, path [plugin://plugin.video.gaia/....]
		# Note that this ONLY happens when the playlist was edited.
		# Once this error occurred, and the steps above are followed, this does not happen anymore.
		# To make the problem happen again, remove the last item from the playlist, add it again, and then play the 1st item from the playlist. Now the problem should occur again.
		# Every combination of:
		#	xbmcplugin.setResolvedUrl(...)
		#	xbmcplugin.endOfDirectory(...)
		# was tried, but the problem persists, and "skipping unplayable item" keeps showing up in the log.
		# Not sure if this can be solved, or this is just how Kodi works.
		# Also note sure if xbmcplugin.setResolvedUrl() even does anything in this case.
		# The problem seems as follows (probably?):
		#	1. Kodi expects the player to start playing something.
		#	2. If the item is selected from the playlist, Gaia is executed and scrapes.
		#	3. Once scraping is done, the stream window is shown, and the Gaia Python process exists.
		#	4. If at the end of the Python process nothing has played, Kodi throws the "skipping unplayable item" and starts playing the next item in the playlist.
		# Even if we enable "autoplay", etc, the problem persists, since playback starts with a new Python process, and the previous scraping process exists (which Kodi expects to start playback).
		# While the Python scraping process is still running, the problem does not show. Only if the process exits, does Kodi do this.
		# So the problem is that the command added to the playlist must start playback, or at least not exit while the user selects a stream.
		# A possible solution:
		#	1. Use a special command/endpoint for playlists. Do not use the "scrape" endpoint directly.
		#	2. The special endpoint starts the scraping in another process.
		#	3. The special endpoint does not exit, but keeps running in the background until as video starts playing, or the streams window (or the dialog/directory) closes.
		# Update: This has its own problems. The special process has to wait until playback finishes. If the process just waits for playback to start, and then exists, the Kodi playlist code will stop playback.
		# Maybe playlists should only be used to play direct links, not plugin-URLs that exit before playback.
		# The only reliable way to do this is to create a single process that does the scraping, stream window, and playback all in one single process. Essentially the process has to finish playback before it exists.
		# Update: xbmcplugin.setResolvedUrl(...) is there to set an already-resolved URL. If you call that function with a direct HTTP URL, Kodi starts playing that URL automatically.
		# Hence, xbmcplugin.setResolvedUrl(...) should not be called with a Gaia plugin URI (that is not resolved yet).
		# Basically, xbmcplugin.setResolvedUrl(...) is an alternative to directly calling xbmc.Player().play(...).
		# Maybe the only way to reliably solve this is to make the entire process (scrape -> stream select -> playback -> rating+binge) run in a single Python process, that holds up the current playlist until scraping/playback has finished.
		# This would require a fundamental redesign of core.py, since the Python process finishes once the stream window loads, and each ListItem in the window has its own command that it executes.
		# For now, we implement a horrible hack to make the scrape process wait until all windows are closed and playback finished.

		# Update 6 (2024-09-05):
		# Similar to playlists, library playbacks also automatically go on to the next episode scrape, the moment scraping of the previous episode is done.
		# This only happens if the user enabled Kodi Settings -> Player -> Video -> Play next video automatically (disabled by default).

		wait = False
		if tools.System.originPlaylist():
			wait = True
		elif tools.System.originLibrary():
			setting = tools.Settings.kodi(id = 'videoplayer.autoplaynextitem')
			if setting:
				# Should be a list with integers.
				# Not sure what the autoplay of "TV Shows" does in this setting. Stick to movies and episodes.
				if tools.Media.isShow(self.media) and 2 in setting: wait = True
				elif tools.Media.isFilm(self.media) and 3 in setting: wait = True

		if wait:
			# This still does not work perfect.
			# If we scrape and then start playback of the 1st playlist item, after playback is done, the next item is not initiated, and Kodi shows an error notification: "PLAYLIST Cant find a next item to play".
			# This only happens if the actually play the 1st item. If we just exit the streams window without playing, the next item in the playlist is correctly started.

			player = interface.Player()
			def busy():
				if player.isPlayback(): return True # Player is playing.
				if window.Window.currentGaia(): return True # Any of the Gaia windows (scraping, streams, playback, rating, binge).
				if interface.Dialog.dialogVisible(): return True # Any other native Kodi dialog (Gaia scrape/streams dialog if settings changed, context menu opened in the streams window, subtitle dialog, or any other dialog that might pop up).
				if self.navigationStreamsDirectory:
					if interface.Loader.visible(): return True # While the directory with the streams loads.
					if tools.System.infoLabel('Container.Property(GaiaStreams)') == '1': return True # The streams directory itself.
				return False

			interval = 1.0
			iterations = int(10800 / interval) # Only do this for up to 3 hours. If this loop has not exited by then, there is probably a problem with the detection somewhere, and we do not want to make this process run forever.
			for i in range(iterations):
				if busy():
					tools.Time.sleep(interval)
				else:
					# Although some time to change between dialogs, end playback, etc.
					tools.Time.sleep(interval)
					if not busy(): break

		#tools.System.pluginResolvedSet(success = False)
		tools.System.pluginResolvedSet(success = False, dummy = True)

	def scrapeExact(self, query = None):
		if query is None: query = interface.Dialog.input(title = 32010, type = interface.Dialog.InputAlphabetic)
		if query:
			if tools.Media.isSerie(self.media): return self.scrape(title = query, exact = True)
			else: return self.scrape(title = query, exact = True)

	def scrapeExecute(self, link, parameters):
		command = tools.System.commandResolve(command = link)
		command.update(parameters)
		command = tools.System.executePlugin(parameters = command)

	def scrapePreset(self, link, autoplay):
		if not self.navigationCinema: self.loaderShow()
		preset = ProviderManager.presetsSelection()
		if preset: self.scrapeExecute(link = link, parameters = {'autoplay' : autoplay, 'preset' : preset})
		self.loaderHide()

	def scrapePresetManual(self, link):
		self.scrapePreset(link = link, autoplay = False)

	def scrapePresetAutomatic(self, link):
		self.scrapePreset(link = link, autoplay = True)

	def scrapeAgain(self, link):
		self.scrapeExecute(link = link, parameters = {'cache' : False})

	def scrapeManual(self, link):
		self.scrapeExecute(link = link, parameters = {'autoplay' : False})

	def scrapeAutomatic(self, link):
		self.scrapeExecute(link = link, parameters = {'autoplay' : True})

	def scrapeSingle(self, link):
		self.scrapeExecute(link = link, parameters = {'binge' : tools.Binge.ModeNone})

	def scrapeBinge(self, link):
		self.scrapeExecute(link = link, parameters = {'binge' : tools.Binge.ModeFirst})

	def scrapeAlternative(self, link):
		self.scrapeExecute(link = link, parameters = {'autoplay' : False if self.autoplay else True})

	def _scrapeProgressShow(self, title = None, message = None, metadata = None):
		if title: self.mLastTitle = title
		if message: self.mLastMessage1 = message
		if metadata: self.mLastMetadata = metadata

		if not self.silent:
			if self.navigationCinemaProgress:
				interface.Dialog.notification(title = self.mLastTitle, message = self.mLastMessage1, icon = interface.Dialog.IconInformation)
			elif not self.navigationCinema:
				if self.navigationScrapeSpecial:
					try: background = MetaImage.extract(data = self.mLastMetadata)['fanart']
					except: background = None
					window.WindowScrape.show(background = background, status = self.mLastMessage1)
					window.WindowBackground.close() # Might still be open from player.py -> interact() to allow a continues background during rating/continue/next-episode-playback.
				else:
					interface.Core.create(type = interface.Core.TypeScrape, background = self.navigationScrapeBar, title = self.mLastTitle, message = self.mLastMessage1)

	def _scrapeProgressUpdate(self, percentage = None, message1 = None, message2 = None, message2Alternative = None, showElapsed = True):
		if not self.silent:
			if percentage is None: percentage = self.progressPercentage
			else: self.progressPercentage = max(percentage, self.progressPercentage) # Do not let the progress bar go back if more streams are added while precheck is running.

			if self.navigationCinemaProgress:
				percentageChange = (self.progressPercentage - self.progressPercentageLast) > 20
				messageChange = not self.mLastMessage1 == message1
				self.mLastMessage1 = message1
				if percentageChange or messageChange or self.progressPercentage == 100:
					self.progressPercentageLast = self.progressPercentage
					interface.Dialog.notification(title = self.mLastTitle, message = interface.Format.iconSeparator(color = True, pad = True).join([self.mLastMessage1, str(int(self.progressPercentage)) + '%']), icon = interface.Dialog.IconInformation)
			elif not self.navigationCinema:
				if self.navigationScrapeSpecial:
					self.mLastMessage1 = message1
					window.WindowScrape.update(
						status = message1, progress = self.progressPercentage, time = self._scrapeProgressElapsed(),
						streamsTotal = self.streamsTotal, streamsHdUltra = self.streamsHdUltra, streamsHd1080 = self.streamsHd1080, streamsHd720 = self.streamsHd720, streamsSd = self.streamsSd, streamsLd = self.streamsLd,
						streamsTorrent = self.streamsTorrent, streamsUsenet = self.streamsUsenet, streamsHoster = self.streamsHoster,
						streamsCached = self.streamsCached, streamsDebrid = self.streamsDebrid, streamsDirect = self.streamsDirect, streamsPremium = self.streamsPremium, streamsLocal = self.streamsLocal,
						streamsFinished = self.streamsFinished, streamsBusy = self.streamsBusy,
						providersFinished = self.providersFinished, providersBusy = self.providersBusy, providersLabels = self.providersLabels,
						skip = self.skip
					)
				else:
					if not message2: message2 = ''
					if interface.Core.background():
						messageNew = self.mLastName + message1
						if message2Alternative: message2 = message2Alternative
						# Do last, because of message2Alternative. Must be done BEFORE dialog update, otherwise stream count sometimes jumps back.
						self.mLastMessage1 = message1
						self.mLastMessage2 = message2
						elapsedTime = self._scrapeProgressElapsed(mini = True) + Format.iconSeparator(color = True, pad = True) if showElapsed and message2 else ''
						interface.Core.update(progress = self.progressPercentage, title = messageNew, message = elapsedTime + message2)
					else:
						messageNew = interface.Format.fontBold(message1) + '%s'
						# Do last, because of message2Alternative. Must be done BEFORE dialog update, otherwise stream count sometimes jumps back.
						self.mLastMessage1 = message1
						self.mLastMessage2 = message2
						elapsedTime = self._scrapeProgressElapsed(full = True) if showElapsed else ' '
						interface.Core.update(progress = self.progressPercentage, message = interface.Format.newline().join([messageNew, elapsedTime, message2]))

	def _scrapeProgressTime(self):
		while not self.stopThreads:
			self._scrapeProgressUpdate(self.progressPercentage, self.mLastMessage1, self.mLastMessage2)
			tools.Time.sleep(0.2)

	def _scrapeProgressElapsed(self, raw = True, mini = False, full = False):
		seconds = max(0, self.timerScrape.elapsed())
		if full: return self.timeStringDescription % seconds
		elif mini: return self.timeString % seconds
		else: return seconds

	def scrapeItem(self, title, year, imdb, tmdb, tvdb, trakt, season, episode, tvshowtitle, premiered, metadata, pack = None, preset = None, exact = False, autoplay = False, cache = True):
		try:
			def titleClean(value, year = None, internal = None):
				values = []
				if value is None: return values

				# Titles with mutiple dots, eg: S.W.A.T.
				if not internal == 1 and value.count('.') >= 3:
					temp = [value, value.replace('.', ''), value.replace('.', ' ')]
					values = tools.Tools.listFlatten(temp + [titleClean(value = i, year = year, internal = 1) for i in temp])
					return tools.Tools.listUnique([i.strip() for i in values])

				# Remove years in brackets from titles.
				# Do not remove years that are not between brackets, since it might be part of the title. Eg: 2001 A Space Oddesy
				# Eg: Heartland (CA) (2007) -> Heartland (CA)
				temp = re.sub('[\(\{\[](?:19|2[01])\d{2}[\)\}\]]', '', value)
				if temp: value = temp

				# Remove the exact year if it is part of the title.
				# Eg: For "Eternals 2021" there exists an alias "Eternos 2021" -> "Eternos" (otherwise the search query will be "Eternos 2021 2021").
				if year:
					temp = re.sub('\s*[\(\{\[]?\s*' + str(year) + '\s*[\)\}\]]?\s*$', '', value)
					if temp: value = temp

				# Replace country codes. Otherwise "U.S." will end up as "U S".
				value = re.sub('u\.s\.', 'us', value, flags = re.IGNORECASE)
				value = re.sub('u\.k\.', 'uk', value, flags = re.IGNORECASE)

				# Remove apostrophes.
				# Create two different versions of apostrophes (one with "'s" -> "s", and the other one "'s" -> ""), since some sites can only use one of them.

				valueNew = re.sub('([\'\`])([a-zA-Z](?:$|[\s\-\–\!\$\%%\^\&\*\(\)\_\+\|\~\=\`\{\}\\\[\]\:\"\;\'\`\<\>\?\,\.\\\/]))', '\g<2>', value) # Replace apostrophes at the end of the word with an empty string (eg: Peter's -> Peters).
				if value == valueNew: values1 = [valueNew]
				else: values1 = [valueNew, re.sub('([\'\`][a-zA-Z])($|[\s\-\–\!\$\%%\^\&\*\(\)\_\+\|\~\=\`\{\}\\\[\]\:\"\;\'\`\<\>\?\,\.\\\/])', '\g<2>', value)]

				values2 = []
				for val in values1:
					# Replace apostrophes at the start of the word with a space (eg: "L'Ascension de Skywalker" -> "L Ascension de Skywalker" and "LAscension de Skywalker").
					values2.append(re.sub('([\'\`])', ' ', val)) # Place this before the one below, since the one below might exceed the maximum number of search titles. YggTorrent can only find with the "'" or " ", but not with "".
					values2.append(re.sub('([\'\`])', '', val))

				seen = set()
				values2 = [i for i in values2 if not (i in seen or seen.add(i))]

				for val in values2:
					# Remove symbols.
					# Eg: Heartland (CA) -> Heartland CA
					# Replace with space: Brooklyn Nine-Nine -> Brooklyn Nine Nine
					val = re.sub('[\-\–\!\$\%%\^\&\*\(\)\_\+\|\~\=\`\{\}\\\[\]\:\"\;\'\`\<\>\?\,\.\\\/]', ' ', val)

					# Replace extra spaces.
					val = re.sub('\s+', ' ', val).strip()

					values.append(val)

				# Censored words which are mostly given in full in the filename.
				# Eg: The Pimp No F**ing Fairytale
				if not internal == 2:
					censored = {'(s\*x)' : 'sex', '(p\*+r?n)[a-z]*' : 'porn', '(f\*+(?:c?k|ck)?)(?:ed|ing)?' : 'fuck'}
					expression = '(?:^|[\.\,\:\-\–\s])%s(?:$|[\.\,\:\-\–\s])'
					for valFrom, valTo in censored.items():
						if tools.Regex.match(data = value, expression = expression % valFrom):
							# Add the unccensored title in FRONT, ssince it is more likley to find values.
							values = titleClean(tools.Regex.replace(data = value, expression = expression % valFrom, replacement = valTo, group = 1), year = year, internal = 2) + values

				return tools.Tools.listUnique([i.strip() for i in values])

			def titleStrip(title):
				# Strip mutiple times, since eg after we stripped a "-", there might be a new " " before the "-" that now has to be removed as well.
				# Eg: "XXXX - "
				for i in range(3): title = title.strip(' ').strip(':').strip('-').strip('.').strip(',').strip('(').strip(')').strip('[').strip(']')
				return title

			def titleValid(title, year):
				# If titles are stripped, ignore certain results.

				if not title: return False

				year = str(year)
				temp = re.sub('\s*[\(\{\[]?\s*' + year + '\s*[\)\}\]]?', '', title)
				if temp: title = temp
				lower = titleStrip(title).lower()

				# Ignore if title is too short.
				# Eg: "Sing 2" -> "2"
				# Eg: "X特遣队：全员集结" -> "X:" (when unicode characters are normalized)
				if len(lower) < 3: return False

				# Ignore if the stripped title is only "The".
				# Eg: Main title "Hitman's Wife's Bodyguard" and alias "The Hitman's Wife's Bodyguard" results in "The"
				if lower == 'the': return False

				# Ingore if after stripping, it only contains the year.
				if lower == year: return False

				# Ignore if it only contains numbers and collection keywords.
				# Eg: "The Suicide Squad 2 The Suicide Squad Collection" -> "2 Collection"
				temp = lower.replace('collection', '').replace('trilogy', '').replace('saga', '').strip()
				if not temp == lower: return titleValid(temp, year)

				return True

			def titleProcess(title, titleShow, year):
				if titleShow:
					self.titles['main'] = titleShow
					self.titles['episode'] = title
				else:
					self.titles['main'] = title

				# Make all titles unicode types (if they are not already unicode).
				try: self.titles['main'] = self.titles['main'].decode('utf-8')
				except: pass
				try: self.titles['native'] = {key : [v.decode('utf-8') for v in val] for key, val in self.titles['native'].items()}
				except: pass
				try: self.titles['local'] = self.titles['local'].decode('utf-8')
				except: pass
				try: self.titles['original'] = self.titles['original'].decode('utf-8')
				except: pass
				try: self.titles['collection'] = self.titles['collection'].decode('utf-8')
				except: pass
				try: self.titles['episode'] = self.titles['episode'].decode('utf-8')
				except: pass
				try:
					for key, value in self.titles['alias'].items():
						for i in range(len(value)):
							try: self.titles['alias'][key][i] = self.titles['alias'][key][i].decode('utf-8')
							except: pass
				except: pass

				# Also search titles that contain abbreviations (consecutive capital letters).
				# Eg: "K.C. Undercover" is retrieved as "KC Undercover" by informants. Most providers have it as "K C Undercover".
				titleAbbreviation = self.titles['main']
				if 'original' in self.titles and self.titles['original']: titleAbbreviation = self.titles['original']
				if titleAbbreviation:
					abbreviations = re.findall('[A-Z]{2,}', titleAbbreviation)
					for abbreviation in abbreviations:
						titleAbbreviation = titleAbbreviation.replace(abbreviation, ' '.join(list(abbreviation)))
				if titleAbbreviation:
					try: self.titles['abbreviation'] = titleAbbreviation.decode('utf-8')
					except: self.titles['abbreviation'] = titleAbbreviation

				limit = min(10, max(5, int(ProviderBase.settingsGlobalLimitQuery() / (2.0 if titleShow else 1.2))))
				settingCharacter = ProviderBase.settingsGlobalTitleCharacter()
				settingAlias = ProviderBase.settingsGlobalTitleAlias()
				settingLocal = ProviderBase.settingsGlobalTitleLocal()
				settingNative = ProviderBase.settingsGlobalTitleNative()

				titles = []
				titleAlias = None
				processedMain = []
				processedCollection = []
				processedEpisode = []
				processedBasic = []

				# In the US, the movie is named "Sorcerer" and in the rest of the world "Philosopher".
				# Both return links, but "Sorcerer" returns slightly more.
				# "Sorcerer" is part of the aliases, but can be cut off if there the query limit setting is strict (considering there are a few collection queries).
				# Push to the front. Maybe not a nice thing to hard-code this, but this seems to be an exception.
				if self.titles['main'] == 'Harry Potter and the Philosopher\'s Stone':
					potter = 'Harry Potter and the Sorcerer\'s Stone'
					titles.append(potter)
					processedMain.append(potter)
					processedBasic.append(potter)

				if 'main' in self.titles and self.titles['main']:
					titles.append(self.titles['main'])
					processedMain.append(self.titles['main'])
					processedBasic.append(self.titles['main'])
				if 'original' in self.titles and self.titles['original']:
					# If the user selected a different Primary Language to English, the 'main' title will be in that language.
					# In such a case, push the original title to the front, so that the first title being searched is more likley to return results.
					if tools.Language.settingsCode(single = True) == tools.Language.EnglishCode:
						titles.append(self.titles['original'])
						processedMain.append(self.titles['original'])
						processedBasic.append(self.titles['original'])
					else:
						titles.insert(0, self.titles['original'])
						processedMain.insert(0, self.titles['original'])
						processedBasic.insert(0, self.titles['original'])
				if 'native' in self.titles and self.titles['native']:
					#if settingNative: titles.extend(self.titles['native'].values()) # Do not add to the main titles, since we do not want to search these like the other alternative titles.
					processedMain.extend(tools.Tools.listFlatten(self.titles['native'].values()))
					processedBasic.extend(tools.Tools.listFlatten(self.titles['native'].values()))
				if 'local' in self.titles and self.titles['local']:
					if settingLocal: titles.append(self.titles['local'])
					processedMain.append(self.titles['local'])
					processedBasic.append(self.titles['local'])
				if 'extra' in self.titles and self.titles['extra']:
					processedMain.extend(tools.Tools.listFlatten(self.titles['extra'].values()))
					processedBasic.extend(tools.Tools.listFlatten(self.titles['extra'].values()))
				if 'abbreviation' in self.titles and self.titles['abbreviation']:
					titles.append(self.titles['abbreviation'])
					processedMain.append(self.titles['abbreviation'])
				if 'alias' in self.titles and self.titles['alias']:
					# Also add the Brazilian title if Portuguese is selected.
					countries = []

					# Do this before ProviderBase.settingsGlobalTitleLanguage() below, since that function will return alternative languages (aka Secondary/Tertary language instead of the Primary).
					countries1 = tools.Language.settingsCountry(variation = True)
					if countries1: countries.extend(countries1)
					countries2 = tools.Language.countries(ProviderBase.settingsGlobalTitleLanguage(), variation = True)
					if countries1: countries.extend(countries2)

					aliases = []
					for country in tools.Tools.listUnique(countries):
						if country in self.titles['alias']: aliases.extend(self.titles['alias'][country])
					if 'us' in self.titles['alias']: aliases.extend(self.titles['alias']['us'])
					if None in self.titles['alias']: aliases.extend(self.titles['alias'][None])
					aliases = tools.Tools.listUnique(aliases)

					if aliases: titleAlias = aliases[0]
					if settingAlias: titles.extend(aliases)

					# Make sure language-setting country aliases are added first to be picked for search titles.
					# English or user-language titles should be placed before eg Chinese titles.
					processedMain.extend(aliases)

					for value in self.titles['alias'].values(): processedMain.extend(value)

				titles = tools.Tools.listUnique(titles)
				processedMain = tools.Tools.listUnique(processedMain)

				# Add title without the collection name.
				# Eg: "The Lord of the Rings: The Two Towers" -> "The Two Towers"
				if 'collection' in self.titles and self.titles['collection']:
					if 'main' in self.titles and self.titles['main']:
						titleReduced = re.sub(self.titles['collection'], '', self.titles['main'], re.IGNORECASE)
						if not titleReduced == self.titles['main']:
							titleReduced = titleStrip(titleReduced)
							# Avoid: "Hotel Transylvania 3 Summer Vacation" -> "3 Summer Vacation"
							if titleReduced and titleValid(titleReduced, year) and not tools.Tools.isNumeric(titleReduced[0]):
								titles.append(titleReduced)
								processedMain.append(titleReduced)

				# If there is an abbreviation in the title, remove it.
				# Eg: "XMA: Xtreme Martial Arts" -> "Xtreme Martial Arts"
				if processedMain:
					abbreviation = tools.Regex.extract(data = processedMain[0], expression = '^([A-Z]{3,})', flags = tools.Regex.FlagNone)
					if abbreviation:
						capital = tools.Regex.extract(data = processedMain[0], expression = '\s([A-Z])[a-z\d]', group = None, all = True, flags = tools.Regex.FlagNone)
						if capital:
							capital = ''.join(capital)
							if abbreviation.startswith(capital):
								capital = tools.Regex.remove(data = processedMain[0], expression = '^(%s.*?\s)' % abbreviation, all = True)
								if capital:
									titles.append(capital)
									processedMain.insert(1, capital)

				# Add native and alias titles stripped from the main title.
				# For instance, the Portuguese title for "Eternals" is "Eternals (Eternos)".
				# However, many releases have only the Portuguese name "Eternos".
				# Strip the main title and add them, eg: {"pt" : ["Eternals (Eternos)", "Eternos"]}
				# Exclude stripped titles that end with "'s", otherwise too many invalid links might be accepted as valid.
				# Eg: FX's The Old Man -> FX's
				# Eg: James Cameron's Avatar -> James Cameron'
				# Ignore director names.
				# Otherwise replacing the main title might result in only the director's name.
				# Eg: Nineteen Eighty Four George Orwell -> George Orwell
				# And this can return too many incorrect links (books, audio books, etc).
				# Do not include: 'guillermo del toro', since there are 2 Pinocchios released in 2022:
				#	Guillermo del Toro's Pinocchio (2022)
				#	Pinocchio (2022)
				people = ['james cameron', 'george orwell', 'jack snyder', 'christopher nolan', 'stanley kubrick', 'steven spielberg', 'stephen king', 'clint wastwood', 'quentin tarantino', 'ridley scott', 'alfred hitchcock', 'peter jackson', 'spike lee', 'george lucas', 'woody allen', 'martin scorsese']
				ignore = False
				for type in ['native', 'alias']:
					if type in self.titles and self.titles[type]:
						for key, values in self.titles[type].items():
							for val in values:
								# replaceNotAlphaNumeric: Also remove symbols from the title.
								# Eg: "Nineteen Eighty-Four" + "George Orwell Nineteen Eighty Four 1984" = "George Orwell 1984"
								titleStripped = val.replace(self.titles['main'], '').replace(tools.Tools.replaceNotAlphaNumeric(data = self.titles['main'], replace = ' '), '')
								titleStripped = titleStrip(titleStripped.replace('  ', ' ')) # strip brackets, etc.
								if titleStripped and not titleStripped == val and titleValid(titleStripped, year) and not titleStripped.endswith('\'s') and not titleStripped.lower() in people:
									# From: The Terminator (1984) [BluRay] [1080p] REMASTERED
									# To: 1984) [BluRay] [1080p] REMASTERED
									if (titleStripped.count('(') + titleStripped.count('[')) < 2 and (titleStripped.count(')') + titleStripped.count(']')) < 2:
										titleStripped = titleStripped.replace('(', '').replace(')', '').replace('[', '').replace(']', '').replace('  ', ' ').strip(' ')

										# Do not include if the 2nd part is just a description that is too vague to scrape.
										# Eg: Gran Turismo: Based on a True Story
										# Eg: Gran Turismo. No spēles līdz trasei
										# Eg: Gran Turismo - De Jogador a Corredor
										# Eg: Gran Turismo: D'après une histoire vraie
										# Set a global var, so we also ignore other languages once we detected this for the English title.
										if tools.Regex.match(data = titleStripped, expression = '($based\s+on|true\s*story)'): ignore = True
										if not ignore:
											# Do not strip the main title to only end up with eg "Extended Version".
											# Avatar Extended Version
											# Avatar - Collector's Edition
											# Avatar - Extended Collector's Edition
											# Avatar - Collector's Extended Edition
											if not tools.Regex.match(data = titleStripped, expression = '(?:edition|version|cut|release|extended|collector|director|ece|special|ultimate|limited|theatrical|retail|imax|colecionador|estendida|colecionador|3d|edição|edicion|coleccionista|edi\u00e7\u00e3o|edicao|edio|wersja|specjalna|rozszerzona|ungeschnittene|fassung|unrated|uncensored|remastered|the\smovie|dvd|bluray|4k|2160p|1080p|disc)(?:\s|$)'):
												# Do not include short titles.
												# Eg: Trakt returns aliases titles for Westworld that are actually the title of the seasons.
												#	Westworld: The Maze
												#	Westworld: The Door
												#	Westworld: The New World
												# We do not want to search eg "The Door S01E01", since it might actually be a different show.
												if not tools.Regex.match(data = val, expression = '([a-z\d\s\-\–\\\']+){1,2}\s*:\s*(the|an?)(\s*[a-z]+){1,2}'):
													self.titles[type][key].append(titleStripped)
													if (type == 'native' and settingNative) or (type == 'alias' and settingAlias):
														if not type == 'native': titles.append(titleStripped) # Do not include the native titles, otherwise universal providers also scrape these titles.
													processedMain.append(titleStripped)
							self.titles[type][key] = tools.Tools.listUnique(self.titles[type][key])

				# Regex check what remains after unicode decoding, otherwise titles like "Harry Potter 1" might degress into "1:" or "1".
				main = []
				expression = '^%s*$' % tools.Regex.Nonalpha
				for title in titles:
					nonalpha = tools.Regex.match(data = title, expression = expression)
					titlesCleaned = titleClean(title, year)
					for titleCleaned in titlesCleaned:
						if not titleCleaned.lower() in people:
							if nonalpha or not tools.Regex.match(data = titleCleaned, expression = expression):
								main.append(titleCleaned)

						titleCleaned2 = tools.Converter.unicodeNormalize(string = titleCleaned, umlaut = False)
						if not titleCleaned2.lower() in people:
							if nonalpha or not tools.Regex.match(data = titleCleaned2, expression = expression):
								main.append(titleCleaned2)

						if settingCharacter:
							titleCleaned3 = tools.Converter.unicodeNormalize(string = titleCleaned, umlaut = True)
							if not titleCleaned3.lower() in people:
								if nonalpha or not tools.Regex.match(data = titleCleaned3, expression = expression):
									main.append(titleCleaned3)

						# Some sites do not deal with encoding unicode at all. Instead, they just strip any unicode characters.
						titleCleaned4 = tools.Converter.unicodeStrip(string = titleCleaned)
						if not titleCleaned4.lower() in people:
							if nonalpha or not tools.Regex.match(data = titleCleaned4, expression = expression):
								main.append(titleCleaned4)
				for i in range(len(main)):
					try: main[i] = main[i].decode('utf-8')
					except: pass
				seen = set()
				main = [i.strip() for i in main]
				main = [i for i in main if i and not(i.lower() in seen or seen.add(i.lower()))]
				processedMain.extend(main)

				native = {}
				if 'native' in self.titles and self.titles['native']:
					for key, val in self.titles['native'].items():
						nativeTitles = []
						for title in val:
							titlesCleaned = titleClean(title, year)
							for titleCleaned in titlesCleaned:
								if titleValid(titleCleaned, year): nativeTitles.append(titleCleaned)

								titleNative = tools.Converter.unicodeNormalize(string = titleCleaned, umlaut = False)
								if titleValid(titleNative, year): nativeTitles.append(titleNative)

								if settingCharacter:
									titleNative = tools.Converter.unicodeNormalize(string = titleCleaned, umlaut = True)
									if titleValid(titleNative, year): nativeTitles.append(titleNative)

								titleNative = tools.Converter.unicodeStrip(string = titleCleaned) # Some sites do not deal with encoding unicode at all. Instead, they just strip any unicode characters.
								if titleValid(titleNative, year): nativeTitles.append(titleNative)
							native[key] = nativeTitles
					for key, val in native.items():
						for i in range(len(val)):
							try: val[i] = val[i].decode('utf-8')
							except: pass
						seen = set()
						val = [i.strip() for i in val]
						val = [i for i in val if i and not(i.lower() in seen or seen.add(i.lower()))]
						native[key] = val
					for val in native.values():
						processedMain.extend(val)

				collection = []
				if 'collection' in self.titles and self.titles['collection']:
					collection.extend(titleClean(self.titles['collection']))
					processedCollection.append(self.titles['collection'])
				for i in range(len(collection)):
					try: collection[i] = collection[i].decode('utf-8')
					except: pass
				seen = set()
				collection = [i.strip() for i in collection]
				collection = [i for i in collection if i and not(i.lower() in seen or seen.add(i.lower()))]

				episode = []
				if 'episode' in self.titles and self.titles['episode']:
					episode.extend(titleClean(self.titles['episode']))
					processedEpisode.append(Stream.titleEpisodeIgnore(self.titles['episode'])) # Do not search for very common episode titles (eg: "VII", "Episode 2", etc).
				for i in range(len(episode)):
					try: episode[i] = episode[i].decode('utf-8')
					except: pass
				seen = set()
				episode = [i.strip() for i in episode]
				episode = [i for i in episode if i and not(i.lower() in seen or seen.add(i.lower()))]

				# Remove release info from the title, otherwise we might have multiple queries that would return the same result as the main query:
				#	Avatar Extended Version
				#	Avatar Collectors Edition
				#	Avatar Collector Edition
				#	Avatar Extended Collectors Edition
				#	Taken 1 (Unrated)
				temp = []
				removes = ['edition', 'version', 'extended', 'ece', 'collector', 'collector\'?s', 'extended', 'director', 'director\'?s', 'special', 'ultimate', 'limited', 'theatrical', 'retail', 'imax', 'estendida\sde\scolecionador', 'estendida', 'colecionador', '3d\sexperience', '3d', 'edicion', 'coleccionista', 'edi\u00e7\u00e3o', 'edicao', 'edio', 'wersja', 'specjalna', 'rozszerzona', 'ungeschnittene', 'fassung', 'unrated', 'uncensored', 'remastered', 'dvd', 'bluray', '4k', '2160p', '1080p', 'disc']
				for i in removes: # Do not exclude keywords that appear in the main title.
					i = '((?:\s|^)%s)(?:\s|$)' % i
					found = False
					for j in processedBasic:
						if tools.Regex.match(data = j, expression = i):
							found = True
							break
					if not found: temp.append(i)
				removes = temp

				temp = []
				excludes = ['the\smovie', str(year), 'james\scameron(?:\'?s)?', '(?<!\s[a-z\d]\s)an?(?!\s[a-z\d]\s)'] # The the lookahead/lookbehind for "an?", otherwise "S.W.A.T." -> "S W A T" will match the "A".
				for i in excludes: # Do not exclude keywords that appear in the main title.
					i = '(?:^|\s)\s*%s\s*(?:$|\s)' % i
					found = False
					for j in processedBasic:
						if tools.Regex.match(data = j, expression = i):
							found = True
							break
					if not found: temp.append(i)
				excludes = temp

				search = []
				for i in main:
					for j in removes:
						i = tools.Regex.remove(data = i, expression = j, group = 1, all = True)
					if i:
						found = False
						for j in excludes:
							if tools.Regex.match(data = i, expression = j):
								found = True
								break
						if not found: search.append(i)
				search = tools.Tools.listUnique(search)

				# Remove similar titles that would just increase scraping time.
				# Eg: with a current search list of: ["Taken","96 Hours","Taken 1 96 hours","96 Hours Taken","Taken 01 Taken","Taken 1"]
				# It should only search: ["Taken","96 Hours"]
				# Count this as a percentage of total words in the other titles.
				# Otherwise similar, but clearly different search queries, will get ignored.
				# Eg: "Harry Potter and the Philosophers Stone" vs "Harry Potter and the Sorcerers Stone".
				if search:
					searchExtra = search
					searchMain = [search[0]]
					countMain = len(searchMain[0].split(' '))
					for i in search:
						duplicates = False
						split1 = i.lower().split(' ')
						for j in searchMain:
							split2 = j.lower().split(' ')
							countCurrent = sum([1 if x in split1 else 0 for x in split2])
							if countCurrent >= max(1, countMain * 0.85):
								duplicates = True
								break
						if not duplicates:
							if collection and tools.Regex.match(data = i, expression = '^\s*\d+\s*$'): continue # Number only. "Taken 1" -> "1".
							searchMain.append(i)

					temp = tools.Tools.copy(searchMain)
					searchBasic = tools.Regex.remove(data = searchMain[0], expression = '^((?:the|an?)\s)', all = True)
					for i in search:
						searchBase = i
						searchReplace = None

						for j in searchMain:
							searchReplace = j
							i = tools.Tools.replaceInsensitive(data = i, value = j, replacement = '')

							# Eg: "The Terminator": replace "Terminator" and not just the full "The Terminator".
							#i = tools.Tools.replaceInsensitive(data = i, value = tools.Regex.remove(data = j, expression = '((?:the|an?)\s)'), replacement = '', all = True)

						# Do not include if the 2nd part is just a description that is too vague to scrape.
						# Eg: Gran Turismo: Based on a True Story
						# Eg: Gran Turismo. No spēles līdz trasei
						# Eg: Gran Turismo - De Jogador a Corredor
						# Eg: Gran Turismo: D'après une histoire vraie
						if i and not tools.Regex.match(data = i, expression = '($based\s+on|true\s*story)'):
							i = ' '.join([j for j in i.split(' ') if j])
							if i:
								# Very short titles, which will probably not return good search results.
								if len(i) <= 2: continue

								# Number only.
								# Eg: "Taken 1" -> "1".
								if collection and tools.Regex.match(data = i, expression = '^\s*\d+\s*$'): continue

								# If the main keyword appears multiple times.
								# Eg: Terminator the 01 Terminator The
								if searchBasic and len(searchBasic) > 5:
									matches = tools.Regex.extract(data = i, expression = '(%s)' % searchBasic, group = None, all = True)
									if matches and len(matches) > 1: continue

								# Ignore numbers.
								# Eg: If "Terminator" is already in the list, do not use "Terminator 1".
								if tools.Regex.remove(data = i, expression = '(\s\d)$', all = True).strip() in temp: continue

								# Ignore only symbols or single digit.
								# Eg: "#9" -> "9".
								if tools.Regex.match(data = i, expression = '^[\d\s\-\–\!\?\$\%%\^\&\*\(\)\_\+\|\~\=\#\`\{\}\\\[\]\:\"\;\'\<\>\,\.\\\/]$'): continue

								# Do not include short titles.
								# Eg: Trakt returns aliases titles for Westworld that are actually the title of the seasons.
								#	Westworld: The Maze
								#	Westworld: The Door
								#	Westworld: The New World
								# We do not want to search eg "The Door S01E01", since it might actually be a different show.
								if searchReplace and tools.Regex.match(data = searchBase, expression = '^%s (the|an?)(\s*[a-z]+){1,2}$' % searchReplace): continue

								if not i.lower() in people: temp.append(i)

					# Add all removed titles again.
					# The ones later in the list will get removed by the limit below.
					temp.extend(searchExtra)
					search = tools.Tools.listUnique(temp)

					# For movies with only a single search title, always add an alias if available, even if ProviderBase.settingsGlobalTitleAlias() is disabled.
					# Eg: ["Nineteen Eighty Four"] -> add the alias "1984"
					# Do not add similar titles.
					# Eg: Gran Turismo" and "Gran Turismo: Based on a True Story"
					if not titleShow and len(search) == 1 and titleAlias and not titleAlias.lower().startswith(search[0].lower()) and not search[0].lower().startswith(titleAlias.lower()):
						# Ignore very similar titles.
						# Eg: Hotel Transylvania 3 Summer Vacation
         				# Eg: Hotel Transylvania 03 Hotel Transylvania 3 Summer Vacation
						if tools.Matcher.levenshtein(search[0], titleAlias) <= 0.5:
							search.append(titleAlias)
							search = tools.Tools.listUnique(search)

				# Remove specific titles.
				# Each entry in "removals": if 1st value matches any of the search titles, exclude search titles that match the 2nd value.
				# Eg: Guillermo del Toro's Pinocchio (2022)
				# Trakt returns a US alias as "Pinocchio".
				# However, another movie was released that year called "Pinocchio (2022)", and we want to exclude those results.
				# These are special cases that cannot be eliminated with any of the code above, and needs to be hard-coded on a per-movie basis.
				removals = [
					('del\s+toro', '^pinocchio$'),
				]
				exclusions = []
				temp = []
				for i in search:
					for j in removals:
						if tools.Regex.match(data = i, expression = j[0]):
							exclusions.append(j[1])
				exclusions = tools.Tools.listUnique(exclusions)
				for i in search:
					add = True
					for j in exclusions:
						if tools.Regex.match(data = i, expression = j):
							add = False
							break
					if add: temp.append(i)
				search = tools.Tools.listUnique(temp)

				self.titles['search'] = {}
				self.titles['search']['main'] = search
				self.titles['search']['native'] = native if settingNative else {}
				self.titles['search']['collection'] = collection
				self.titles['search']['episode'] = Stream.titleEpisodeIgnore(episode) # Do not search for very common episode titles (eg: "VII", "Episode 2", etc).

				if limit > 0:
					if len(self.titles['search']['main']) > limit:
						self.titles['search']['main'] = self.titles['search']['main'][:limit]

					count = limit - len(self.titles['search']['main'])
					if count <= 0: count = 1
					self.titles['search']['native'] = {key : val[:count] for key, val in self.titles['search']['native'].items()}

					count = limit - len(self.titles['search']['main'])
					if count <= 0: count = 1
					self.titles['search']['collection'] = self.titles['search']['collection'][:count]

					count = limit - len(self.titles['search']['main'])
					if count <= 0: count = 1
					self.titles['search']['episode'] = self.titles['search']['episode'][:count]

				# This is important for matching titles in stream.py.
				# Eg: The title "Amélie", but most file names contain "Amelie".
				processedExtra = []
				expression = re.compile('^\s*[\s\d\-\–\!\$\%%\^\&\*\(\)\_\+\|\~\=\`\{\}\\\[\]\:\"\;\'\`\<\>\?\,\.\\\/]*\s*$') # Ignore titles with single symbol (when unicode fails leaving only spaces/symbols/digits behind).
				seen = set()
				processedMain = [i for i in processedMain if i and not(i.lower() in seen or seen.add(i.lower()))] # Reduce computation.
				for title in processedMain:
					titleNew = tools.Converter.unicodeNormalize(string = title, umlaut = False).strip()
					if titleNew and (titleNew == title or not expression.match(titleNew)) and titleValid(titleNew, year):
						processedExtra.append(titleNew)
					if settingCharacter:
						titleNew = tools.Converter.unicodeNormalize(string = title, umlaut = True).strip()
						if titleNew and (titleNew == title or not expression.match(titleNew)) and titleValid(titleNew, year):
							processedExtra.append(titleNew)
				for i in range(len(processedExtra)):
					try: processedExtra[i] = processedExtra[i].decode('utf-8')
					except: pass
				processedMain.extend(processedExtra)

				# Sometimes there are weird aliases, which hinders metadata extraction (eg keywords like "1080p", "BluRay", etc).
				#	The Terminator BluRay 1080p REMASTERED
				#	The Terminator (1984) [BluRay] [1080p] REMASTERED
				for i in ['2160p?', '1080p?', '720p?', '4k', '(?:hd.*?)?dvd', 'bluray', 'vhs']:
					expression = '(?:^|\s)(%s?%s%s?)(?:$|\s)' % (tools.Regex.Symbol, i, tools.Regex.Symbol)
					if not tools.Regex.match(data = self.titles['main'], expression = expression):
						for j in range(len(processedMain)):
							processedNew = tools.Regex.remove(data = processedMain[j], expression = expression, group = 1, all = True)
							if not processedNew == processedMain[j]: processedMain[j] = tools.Regex.replace(data = processedNew, expression = '\s{2,}', replacement = ' ', all = True)

				# Exclude network/studio prefixes.
				# Eg: "FX's 将軍" -> "FX's"
				processedMain = [i for i in processedMain if not tools.Regex.match(data = i, expression = '^[A-Z0-9]+\\\'s$', flags = tools.Regex.FlagNone)]

				seen = set()
				processedMain = [i for i in processedMain if i and not(i.lower() in seen or seen.add(i.lower()))]
				seen = set()
				processedCollection = [i for i in processedCollection if i and not(i.lower() in seen or seen.add(i.lower()))]
				seen = set()
				processedEpisode = [i for i in processedEpisode if i and not(i.lower() in seen or seen.add(i.lower()))]
				seen = set()
				processedAll = processedMain + processedCollection + processedEpisode
				processedAll = [i for i in processedAll if i and not(i.lower() in seen or seen.add(i.lower()))]

				self.titles['processed'] = {}
				self.titles['processed']['all'] = processedAll
				self.titles['processed']['main'] = processedMain
				self.titles['processed']['collection'] = processedCollection
				self.titles['processed']['episode'] = processedEpisode

				# Used by providers -> web.py -> queryGenerate().
				if 'original' in self.titles and self.titles['original']:
					original = self.titles['original']

					titles = []
					titles.extend([i for i in self.titles['search']['main'] if tools.Matcher.levenshtein(original, i) > 0.75])
					seen = set()
					titles = [i for i in titles if i and not(i.lower() in seen or seen.add(i.lower()))]
					self.titles['search']['original'] = titles

					titles = [original]
					titles.extend([i for i in self.titles['processed']['main'] if tools.Matcher.levenshtein(original, i) > 0.75])
					titles = [tools.Regex.extract(data = i, expression = '^\s*[\-\_\:\+]*\s*(.*?)\s*[\-\_\:\+]*\s*$', cache = True) for i in titles] # Remove leading/trailing symbols (except a dot), Eg: ["S.W.A.T.", "S.W.A.T. -", "S.W.A.T.:"]
					seen = set()
					titles = [i for i in titles if i and not(i.lower() in seen or seen.add(i.lower()))]
					self.titles['processed']['original'] = titles

				# Convert all titles to unicode, otherwise there are encode/decode errors down the line during scraping and in stream.py.
				titleDecode(self.titles)

			def titleDecode(titles):
				for key, value in titles.items():
					if value:
						if tools.Tools.isDictionary(value):
							titleDecode(value)
						else:
							if tools.Tools.isArray(value):
								for i in range(len(value)):
									value[i] = titleFinish(value[i])
							else:
								value = titleFinish(value)
							titles[key] = value

			def titleFinish(title):
				try: title = title.decode('utf-8')
				except: pass
				title = tools.Regex.replace(data = title, expression = '\s{2,}', replacement = ' ', all = True)
				return title

			def additional(title, titleShow, year, imdb, tmdb, tvdb, trakt, season, episode, metadata):
				additionalInitialize(title = title, titleShow = titleShow, year = year, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, metadata = metadata)
				self.additionalLockTrakt = Lock()
				self.additionalLockTmdb = Lock()
				self.additionalLockImdb = Lock()
				threads = []
				threads.append(Pool.thread(target = additionalTitle, kwargs = {'title' : title, 'titleShow' : titleShow, 'year' : year, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt}, start = True))
				threads.append(Pool.thread(target = additionalYear, kwargs = {'title' : title, 'titleShow' : titleShow, 'year' : year, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt}, start = True))
				[thread.join() for thread in threads]
				additionalFinalize()

			def additionalInitialize(title, titleShow, year, imdb, tmdb, tvdb, trakt, season, episode, metadata):
				originalLanguage = []
				originalCountry = []
				originalNetwork = []
				originalStudio = []

				if titleShow:
					if metadata:
						originalLanguage.append(metadata.get('language'))
						originalCountry.append(metadata.get('country'))
						originalNetwork.append(metadata.get('network'))
						originalStudio.append(metadata.get('studio'))
					item = MetaManager.instance().metadataShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = titleShow or title, year = year)
					if item:
						originalLanguage.append(item.get('language'))
						originalCountry.append(item.get('country'))
						originalNetwork.append(item.get('network'))
						originalStudio.append(item.get('studio'))
				else:
					if metadata:
						originalLanguage.append(metadata.get('language'))
						originalCountry.append(metadata.get('country'))
						originalNetwork.append(metadata.get('network'))
						originalStudio.append(metadata.get('studio'))

				if originalLanguage:
					items = []
					for i in originalLanguage: None if not i else items.extend(i) if tools.Tools.isArray(i) else items.append(i)
					if items: self.originalLanguage = items

				if originalCountry:
					items = []
					for i in originalCountry: None if not i else items.extend(i) if tools.Tools.isArray(i) else items.append(i)
					if items: self.originalCountry = items

				if originalNetwork:
					items = []
					for i in originalNetwork: None if not i else items.extend(i) if tools.Tools.isArray(i) else items.append(i)
					if items: self.originalNetwork = items

				if originalStudio:
					items = []
					for i in originalStudio: None if not i else items.extend(i) if tools.Tools.isArray(i) else items.append(i)
					if items: self.originalStudio = items

			def additionalFinalize():
				if self.originalLanguage: self.originalLanguage = tools.Tools.listUnique(self.originalLanguage)
				if self.originalCountry: self.originalCountry = tools.Tools.listUnique(self.originalCountry)
				if self.originalNetwork:
					for i in self.originalNetwork:
						try:
							# Eg: British Broadcasting Corporation (BBC)
							abbrivation = tools.Regex.extract(data = i, expression = '(.*?)\s*[\(\[]([A-Z0-9\-\s]{3,6}\+?)[\)\]]\s*$', flags = tools.Regex.FlagNone, group = None, all = True, cache = True)
							if abbrivation:
								self.originalNetwork.append(abbrivation[0][0])
								self.originalNetwork.append(abbrivation[0][1])
						except: tools.Logger.error()
					self.originalNetwork = tools.Tools.listUnique(self.originalNetwork)
				if self.originalStudio:
					for i in self.originalStudio:
						try:
							# Eg: British Broadcasting Corporation (BBC)
							abbrivation = tools.Regex.extract(data = i, expression = '(.*?)\s*[\(\[]([A-Z0-9\-\s]{3,6}\+?)[\)\]]\s*$', flags = tools.Regex.FlagNone, group = None, all = True, cache = True)
							if abbrivation:
								self.originalStudio.append(abbrivation[0][0])
								self.originalStudio.append(abbrivation[0][1])
						except: tools.Logger.error()
					self.originalStudio = tools.Tools.listUnique(self.originalStudio)

			def additionalTrakt(trakt, imdb):
				try:
					self.additionalLockTrakt.acquire() # Lock, since this function can be called for extracting the year OR the original title, and we only want to make the request once.
					if imdb: return traktx.SearchMovie(trakt = trakt, imdb = imdb)
				except:
					tools.Logger.error()
				finally:
					try: self.additionalLockTrakt.release()
					except: pass
				return None

			def additionalTmdb(imdb):
				try:
					self.additionalLockTmdb.acquire() # Lock, since this function can be called for extracting the year OR the original title, and we only want to make the request once.
					if imdb:
						from lib.modules.account import Tmdb
						key = Tmdb.instance().key()
						if key: return cachex.Cache.instance().cacheExtended(network.Networker().requestJson, 'http://api.themoviedb.org/3/find/%s?api_key=%s&external_source=imdb_id' % (imdb, key))
				except:
					tools.Logger.error()
				finally:
					try: self.additionalLockTmdb.release()
					except: pass
				return None

			def additionalImdb(imdb):
				try:
					self.additionalLockImdb.acquire() # Lock, since this function can be called for extracting the year OR the original title, and we only want to make the request once.
					if imdb:
						# NB: Request the English version of the website.
						# Otherwise IMDb might use the public IP address (eg: VPN) to return the page (and the original title) in another language.
						from lib.meta.providers.imdb import MetaImdb
						result = MetaImdb.instance().metadata(id = imdb, language = tools.Language.EnglishCode, cache = True)
						if result: return result
				except:
					tools.Logger.error()
				finally:
					try: self.additionalLockImdb.release()
					except: pass
				return None

			def additionalYear(title, titleShow, year, imdb, tmdb, tvdb, trakt):
				# Sometimes the release year of a movie can be different from different sources.
				# For instance, when searching for "Danny's Game", the search results are from Trakt and show the year as 2019, but on IMDb the year is listed as 2020.
				# Sometimes the year can be off by 1, for movies released at the start/end of the year with different release dates in different countries.
				# During COVID, there were a number of movies which premier was delayed. The website therefore shows the originally planned released date and did not update to the new date.
				# During COVID, some movies delayed their theater release date, but when that took too long, they decided to release on streaming services instead, changing the release date.
				# Check on Trakt, TMdb, and IMDb. If there are different years, generate separate search queries for each year.
				try:
					# Intitialize here already, in case the thread does not finish.
					try: year = int(year)
					except: year = None
					self.years = {
						'common' : year,				# The most common year amongst sources.
						'original' : year,				# The year returned by the original menu source.
						'median' : year,				# The median/middle year.
						'all' : [year] if year else [],	# All available years.
						'imdb' : None,
						'tmdb' : None,
						'tvdb' : None,
						'trakt' : None,
					}

					if imdb and not titleShow and self.enabledYear: # Only movies.
						threads = []
						threads.append(Pool.thread(target = additionalYearTrakt, kwargs = {'trakt' : trakt, 'imdb' : imdb}, start = True))
						threads.append(Pool.thread(target = additionalYearTmdb, kwargs = {'imdb' : imdb}, start = True))
						threads.append(Pool.thread(target = additionalYearImdb, kwargs = {'imdb' : imdb}, start = True))
						[thread.join() for thread in threads]

						sources = {i : self.years[i] for i in ['imdb', 'tmdb', 'trakt'] if self.years[i]}

						years = []
						for key, value in sources.items():
							# Add the IMDb year twice, so it is more likley to be picked with tools.Tools.listCommon().
							# It seems that most release file names rather contain the IMDb year than the year from other sources.
							if key == 'imdb':
								years.insert(0, value)
								years.insert(0, value)
							else:
								years.append(value)
						self.years['common'] = tools.Tools.listCommon(years)

						range = [year - 2, year - 1, year, year + 1, year + 2]
						years = [year]
						for i in sources.values():
							try:
								# Only use years that are +- 1 year apart.
								# Search by +- 2 years, since the original year might not be the media year (eg: original year might be 2019, but other years might be 2020 and 2021).
								# These extra years will be removed below.
								# Any year further apart was probably wrongly detected, extracted, or was incorrectly entered on the source website.
								if i in range: years.append(i)
							except: tools.Logger.error()

						years = tools.Tools.listUnique(years)
						years = tools.Tools.listSort(years)

						# Remove years that are too far off.
						total = len(years)
						if total > 3:
							index = int(total / 2.0)
							years = [years[index] - 1, years[index], years[index] + 1]

						self.years['all'] = years
						self.years['median'] = tools.Tools.listMiddle(years)
				except: tools.Logger.error()
				self.progressYearTrakt = 100
				self.progressYearImdb = 100
				self.progressYearTmdb = 100

			def additionalYearTrakt(trakt, imdb):
				self.progressYearTrakt = 0
				try:
					result = additionalTrakt(trakt = trakt, imdb = imdb)
					if result:
						for i in result:
							if i['type'] == 'movie':
								year = int(i['movie']['year'])
								if year: self.years['trakt'] = year
								break
				except: tools.Logger.error()
				self.progressYearTrakt = 90

			def additionalYearTmdb(imdb):
				self.progressYearTmdb = 0
				try:
					result = additionalTmdb(imdb = imdb)
					if result and 'movie_results' in result:
						result = result['movie_results']
						if result:
							result = result[0]
							if result:
								year = int(tools.Regex.extract(data = result['release_date'], expression = '((?:1[89]|2[01])\d{2})'))
								if year: self.years['tmdb'] = year
				except: tools.Logger.error()
				self.progressYearTmdb = 90

			def additionalYearImdb(imdb):
				self.progressYearImdb = 0
				try:
					result = additionalImdb(imdb = imdb)
					if result:
						year = result.get('year')
						if year: self.years['imdb'] = year
				except: tools.Logger.error()
				self.progressYearImdb = 90

			def additionalTitle(title, titleShow, year, imdb, tmdb, tvdb, trakt):
				threads = []

				original = self.enabledTitle and ProviderBase.settingsGlobalTitleOriginal()
				threads.append(Pool.thread(target = additionalTitleOriginal, args = (original, title, titleShow, imdb, tmdb, tvdb, trakt)))

				if self.enabledTitle:
					native = ProviderBase.settingsGlobalTitleNative()
					local = ProviderBase.settingsGlobalTitleLocal()

					# Always add the native/local/alias titles to the "processed" list for filename matching, irrespective of the setting.
					# Only later on, exclude these titles from the "search" list if the setting is disbaled.
					#if native or local: threads.append(Pool.thread(target = additionalTitleTranslation, args = (title, titleShow, imdb, tvdb, native, local)))
					#if ProviderBase.settingsGlobalTitleAlias(): threads.append(Pool.thread(target = additionalTitleAlias, args = (title, titleShow, imdb, tvdb)))
					threads.append(Pool.thread(target = additionalTitleTranslation, args = (title, titleShow, imdb, tmdb, tvdb, trakt, True, True)))
					threads.append(Pool.thread(target = additionalTitleAlias, args = (title, titleShow, imdb, tmdb, tvdb, trakt)))

				if self.enabledCollection and not titleShow:
					threads.append(Pool.thread(target = additionalTitleCollection, args = (title, imdb, tmdb, tvdb, trakt)))

				[thread.start() for thread in threads]
				[thread.join() for thread in threads]

				titleProcess(title, titleShow, year)

				self.progressTitleOriginal = 100
				self.progressTitleTranslation = 100
				self.progressTitleAlias = 100
				self.progressTitleCollection = 100

			def additionalTitleOriginal(update, title, titleShow, imdb, tmdb, tvdb, trakt):
				self.progressTitleOriginal = 0
				try:
					originalTitle = None
					originalLanguage = None
					originalCountry = None
					originalNetwork = None
					originalStudio = None

					result = additionalTmdb(imdb)
					if result:
						self.progressTitleOriginal = 35
						if not tools.Tools.isArray(result): result = [result]
						for i in result:
							for j in i:
								for key, value in i.items():
									if not tools.Tools.isArray(value): value = [value]
									for k in value:
										if 'original_title' in k: # Movies
											originalTitle = k['original_title']
											try: originalLanguage = k['original_language']
											except: pass
											try: originalCountry = k['origin_country']
											except: pass
											break
										elif 'original_name' in k: # Shows
											originalTitle = k['original_name']
											try: originalLanguage = k['original_language']
											except: pass
											try: originalCountry = k['origin_country']
											except: pass
											break
									if originalTitle: break
								if originalTitle: break
							if originalTitle: break

					if not originalTitle:
						result = additionalImdb(imdb)
						self.progressTitleOriginal = 70
						if result:
							originalTitle = result.get('originaltitle') or result.get('title')
							originalLanguage = result.get('language')
							originalCountry = result.get('country')
							originalStudio = result.get('studio')

					if update and originalTitle: self.titles['original'] = originalTitle.strip() or titleShow or title # Sometimes foreign titles have a space at the end.

					if originalLanguage:
						if not tools.Tools.isArray(originalLanguage): originalLanguage = [originalLanguage]
						originalLanguage = [tools.Language.code(i) for i in originalLanguage]
						if self.originalLanguage: self.originalLanguage.extend(originalLanguage)
						else: self.originalLanguage = originalLanguage

					if originalCountry:
						if not tools.Tools.isArray(originalCountry): originalCountry = [originalCountry]
						originalCountry = [tools.Country.code(i) for i in originalCountry]
						if self.originalCountry: self.originalCountry.extend(originalCountry)
						else: self.originalCountry = originalCountry

					if originalNetwork:
						if not tools.Tools.isArray(originalNetwork): originalNetwork = [originalNetwork]
						if self.originalNetwork: self.originalNetwork.extend(originalNetwork)
						else: self.originalNetwork = originalNetwork

					if originalStudio:
						if not tools.Tools.isArray(originalStudio): originalStudio = [originalStudio]
						if self.originalStudio: self.originalStudio.extend(originalStudio)
						else: self.originalStudio = originalStudio

				except: tools.Logger.error()
				self.progressTitleOriginal = 90

			def additionalTitleTranslation(title, titleShow, imdb, tmdb, tvdb, trakt, native = True, local = True):
				try:
					self.progressTitleTranslation = 0
					languages = []
					if local:
						languagesLocal = ProviderBase.settingsGlobalTitleLanguage()
						if languagesLocal: languages.append(languagesLocal)
					if native:
						languagesProviders = [i.languages() for i in self.providers]
						languagesProviders = tools.Tools.listFlatten(languagesProviders)
						languagesProviders = tools.Tools.listUnique(languagesProviders)
						languages = [i for i in languages if not i == tools.Language.UniversalCode and not i == tools.Language.EnglishCode]
						if languagesProviders: languages.extend(languagesProviders)

					translations = {language : [] for language in languages}
					extra = {}

					self.progressTitleTranslation = 25
					if titleShow and (imdb or tvdb):
						from lib.meta.data import MetaData
						from lib.meta.core import MetaCore

						# Do not filter by language here. We do it manually below, so that we can use all titlers for 'extra'.
						#items = MetaCore(MetaCore.ProviderTvdb, threaded = MetaCore.ThreadedEnable).translationTitle(media = MetaData.MediaShow, idImdb = imdb, idTvdb = tvdb, language = languages)
						items = MetaCore(MetaCore.ProviderTvdb, threaded = MetaCore.ThreadedEnable).translationTitle(media = MetaData.MediaShow, idImdb = imdb, idTvdb = tvdb)

						if items:
							for key, val in items.items():
								if key in languages: translations[key].extend(val)

								if not key in extra: extra[key] = []
								extra[key].extend(val)

					self.progressTitleTranslation = 50
					found = False
					if languages:
						found = True
						for language in languages:
							if not language in translations or not translations[language]:
								found = False
								break

					if not found and imdb:
						items = traktx.getTVShowTranslation if titleShow else traktx.getMovieTranslation

						# Do not filter by language here. We do it manually below, so that we can use all titlers for 'extra'.
						#items = items(imdb, languages, full = True)
						items = items(imdb, full = True)

						if items:
							for item in items:
								if not item['language'] in translations: translations[item['language']] = []
								if item['title']: # Sometimes title is null and there is only an overview.
									key = item['language']
									if key in languages: translations[key].append(item['title'])

									if not key in extra: extra[key] = []
									extra[key].append(item['title'])

					# We use all alias titles here.
					# If the user has disabled 'alias' searches from the settings (to reduce scraping time), no alias titles are retrieved.
					# These aliases titles are retrieved here as well. So we can just use them without increasing time.
					# These 'extra' titles are only used for stream matching (eg: exclude in languageExtract()), and not for scraping.
					# This can cause eg incorrect language detection. The Polish title for "Peter Pan & Wendy" is "Piotrus Pan i Wendy". Without the Polish title, the "Pan" will be detected as Punjabi language, since the exclude does not work with "Piotrus" instead of "Peter".
					self.titles['extra'] = extra

					self.progressTitleTranslation = 75
					titleLower = titleShow.lower() if titleShow else title.lower()
					for key, val in translations.items():
						translations[key] = [i for i in val if i and not i.lower() == titleLower]

					try: titlesLocal = translations[languagesLocal][0]
					except: titlesLocal = None
					self.titles['local'] = titlesLocal or titleShow or title

					# Allow multiple native titles.
					# Eg: Portuguese might have multiple translations, one for Portugal and a different one for Brazil.
					self.titles['native'] = {key : val for key, val in translations.items() if key in languagesProviders}
				except: tools.Logger.error()
				self.progressTitleTranslation = 90

			def additionalTitleAlias(title, titleShow, imdb, tmdb, tvdb, trakt):
				self.progressTitleAlias = 25
				try:
					aliases = traktx.getTVShowAliases(imdb or trakt) if titleShow else traktx.getMovieAliases(imdb or trakt)
					if not aliases: aliases = []

					titleAliases = {}
					for alias in aliases:
						country = alias['country']
						if country: country = country.lower()
						else: country = None
						if not country in titleAliases: titleAliases[country] = []
						titleAliases[country].append(alias['title'])

					for key, value in titleAliases.items():
						seen = set()
						titleAliases[key] = [i for i in value if i and not(i.lower() in seen or seen.add(i.lower()))]

					self.titles['alias'] = titleAliases
				except: tools.Logger.error()
				self.progressTitleAlias = 90

			def additionalTitleCollection(title, imdb, tmdb, tvdb, trakt):
				self.progressTitleCollection = 0
				try:
					from lib.modules.account import Tmdb
					key = Tmdb.instance().key()
					if key:
						self.tmdbDetails = {}
						def tmdbDetails(id, key):
							self.tmdbDetails[id] = cachex.Cache.instance().cacheExtended(network.Networker().requestJson, 'https://api.themoviedb.org/3/movie/%s?api_key=%s' % (str(id), key))
							return self.tmdbDetails[id]
						result = tmdbDetails(id = imdb, key = key)
						self.progressTitleCollection = 50
						try: self.titles['collection'] = re.sub('collection$', '', result['belongs_to_collection']['name'], flags = re.IGNORECASE).strip()
						except: self.titles['collection'] = None
						try: id = result['belongs_to_collection']['id']
						except: id = None
						if id:
							result = cachex.Cache.instance().cacheExtended(network.Networker().requestJson, 'https://api.themoviedb.org/3/collection/%d?api_key=%s' % (id, key))
							titleCollection = result['name']
							# Many collections on TMDb contain sequels that have not been released.
							# This means movie packs are scraped, although only 1 movie in the collection was released.
							# Ignore collections if it only has 1 movie that has been released.
							movies = []
							if result and 'parts' in result:
								parts = result['parts']
								if parts:
									current = tools.Time.timestamp()
									for part in parts:
										try: time = part['release_date']
										except: time = None
										if time:
											time = tools.Time.timestamp(fixedTime = time, format = tools.Time.FormatDate)

											# Let MetaPack decide which movies to remove.
											#if time and time < current: movies.append(part)
											movies.append(part)
							if len(movies) <= 1:
								self.titles['collection'] = None
								self.pack = None
							else:
								threads = []
								for movie in movies:
									if movie: threads.append(Pool.thread(target = tmdbDetails, kwargs = {'id' : movie['id'], 'key' : key}, start = True))
								[thread.join() for thread in threads]

								for i in range(len(movies)):
									movie = movies[i]
									try: time = movie['release_date']
									except: time = None
									if time:
										time = tools.Time.timestamp(fixedTime = time, format = tools.Time.FormatDate)
									try: year = int(tools.Regex.extract(data = movie['release_date'], expression = '((?:1[89]|2[01])\d{2})'))
									except: year = None
									try: duration = self.tmdbDetails[movie['id']]['runtime'] * 60 # Runtime is in minutes.
									except: duration = None
									try: status = self.tmdbDetails[movie['id']]['status']
									except: status = None

									movies[i] = {
										'title' : tools.Tools.listUnique([movie['original_title'], movie['title']]),
										'year' : year,
										'time' : time,
										'duration' : duration,
										'status' : status,
									}

								self.pack = MetaPack().generateMovie(title = titleCollection, movies = movies)
							self.progressTitleCollection = 75
				except: tools.Logger.error()
				self.progressTitleCollection = 90

			def initializeProviders(media, preset, exclude = None):
				self.providers = ProviderManager.providers(enabled = True, exclude = exclude, preset = preset, sort = True)
				self.providersBusy = len(self.providers)

			tools.Logger.log('Scraping Started', name = 'CORE', type = tools.Logger.TypeInfo)

			tools.Hardware.usageStart()

			# Clear statistics. Important for binge watching, where the sequential binge scrapes happen in the same execution (aka global variables are still in memory).
			# Should not be a problem anymore, since binge scrapes are now done in a separate process without shared memory (System.executePlugin).
			ProviderBase.statisticsClear()

			threads = []
			movie = tvshowtitle is None if self.media is None else self.media == tools.Media.Movie
			media = tools.Media.Movie if movie else tools.Media.Show

			niche = (metadata.get('niche') if metadata else None)
			if niche: niche = [i for i in niche if i in [tools.Media.Film, tools.Media.Serie, tools.Media.Topic, tools.Media.Audience]]

			release = None
			if metadata:
				try: release = metadata['premiered']
				except: pass
				if not release:
					try: release = metadata['aired']
					except: pass
			if not release: release = premiered
			if release and tools.Tools.isString(release):
				try: release = tools.Time.timestamp(fixedTime = release, format = tools.Time.FormatDate)
				except: release = None

			try: duration = int(metadata['duration']) # Might come in as a string from "Random Play".
			except: duration = None
			self.usage = None

			self.pack = pack or (metadata.get('pack') if metadata else None)
			if not self.pack and tools.Media.isSerie(media): tools.Logger.log('No pack metadata available. Pack scraping will be inaccurate.')

			number = None
			if not number and metadata: number = metadata.get('number')
			number = MetaPack.reduceNumber(data = number, pack = self.pack, season = season, episode = episode)

			self.timeInitialize = None
			self.timeMetadata = None
			self.timeScrape = None
			self.timePrecheck = None
			self.timeMetadata = None
			self.timeFinalize = None
			self.timeExclusion = None
			self.timeCache = None
			self.timeSave = None

			try: year = int(year)
			except: pass
			try: season = int(season)
			except: pass
			try: episode = int(episode)
			except: pass

			self.originalLanguage = None
			self.originalCountry = None
			self.originalNetwork = None
			self.originalStudio = None

			self.titles = {}
			self.years = None
			if exact:
				if not movie and not title: title = tvshowtitle
				self.titles['processed'] = {'all' : [title], 'main' : [title]}
				self.titles['search'] = {'exact' : [title]}
			else:
				titleProcess(title, tvshowtitle, year)

			self.streamsTotal = 0
			self.streamsHdUltra = 0
			self.streamsHd1080 = 0
			self.streamsHd720 = 0
			self.streamsSd = 0
			self.streamsLd = 0
			self.streamsTorrent = 0
			self.streamsUsenet = 0
			self.streamsHoster = 0
			self.streamsCached = 0
			self.streamsDebrid = 0
			self.streamsDirect = 0
			self.streamsPremium = 0
			self.streamsLocal = 0

			self.skip = False
			self.providersLabels = None
			self.providersFinished = 0
			self.providersBusy = 0
			self.providersWait = -1
			self.streamsFinished = 0
			self.streamsBusy = 0
			self.streamsRunning = False

			self.startedThreads = False
			self.stopThreads = False
			self.finishedThreads = False
			self.sourcesAdjusted = []
			self.tasksAdjusted = []

			# Do not use too many threads, since they are anyways executed sequentially, and we do not want to waste unnecessary threads for low-end devices.
			# Allow more threads at the end of the process.
			cores = tools.Hardware.processorCountCore()
			self.synchronizerAdjusted = {False : Premaphore(min(16, max(int(cores * 1.5), 8))), True : Premaphore(min(24, max(int(cores * 2.0), 16)))}

			labels = []

			self.threadsLock = Lock()
			self.dataLock = Lock()

			# Termination
			self.terminated = False
			self.termination = Termination.instance()
			self.terminationLock = Lock()
			self.terminationEnabled = self.termination.enabled()
			if self.terminationEnabled:
				mode = self.termination.mode()
				self.terminationEnabled = (mode == Termination.ModeAny) or (mode == Termination.ModeOverwrite) or (mode == Termination.ModeManual and not autoplay) or (mode == Termination.ModeAutomatic and autoplay)

			self.unresponsiveEnabled = tools.Settings.getBoolean('scrape.termination.unresponsive')
			self.unresponsiveTime = tools.Settings.getCustom('scrape.termination.unresponsive.time')
			self.unresponsiveTimeLabel = tools.Settings.customLabel(id = 'scrape.termination.unresponsive.time', value = self.unresponsiveTime)
			self.unresponsiveLimit = tools.Settings.getCustom('scrape.termination.unresponsive.limit')
			self.unresponsiveLimitLabel = tools.Settings.customLabel(id = 'scrape.termination.unresponsive.limit', value = self.unresponsiveLimit)

			self.enabledDeveloper = tools.System.developer(version = False)
			self.enabledProviders = tools.Settings.getBoolean('interface.scrape.interface.providers')
			self.enabledTitle = ProviderBase.settingsGlobalTitleEnabled()
			self.enabledYear = ProviderBase.settingsGlobalYearEnabled()
			self.enabledPack = ProviderBase.settingsGlobalPackEnabled()
			self.enabledCollection = ProviderBase.settingsGlobalPackMovie()
			self.enabledFailures = ProviderManager.failureEnabled()

			self.preloadEnabled = self.enabledDeveloper and tools.Settings.getBoolean('general.developer.preload.container')
			self.preloadEnabledTorrent = self.preloadEnabled and tools.Settings.getBoolean('general.developer.preload.container.torrent')
			self.preloadEnabledUsenet = self.preloadEnabled and tools.Settings.getBoolean('general.developer.preload.container.usenet')

			self.precheckLink = self.enabledDeveloper and tools.Settings.getBoolean('general.developer.precheck.link')
			self.precheckLinkTime = tools.Settings.getCustom('general.developer.precheck.link.time')
			if not self.precheckLinkTime: self.precheckLinkTime = 30
			self.precheckMetadata = self.enabledDeveloper and tools.Settings.getBoolean('general.developer.precheck.metadata')
			self.precheckMetadataTime = tools.Settings.getCustom('general.developer.precheck.metadata.time')
			if not self.precheckMetadataTime: self.precheckMetadataTime = 30

			self.cacheCount = 0
			self.cacheBusy = 0
			self.cacheLookup = False

			self.cacheEnabled = tools.Settings.getBoolean('scrape.cache.inspection')
			self.cacheEnabledPremiumize = self.cacheEnabled and tools.Settings.getInteger('scrape.cache.inspection.premiumize') == 1
			self.cacheEnabledOffcloud = self.cacheEnabled and tools.Settings.getInteger('scrape.cache.inspection.offcloud') == 1
			self.cacheEnabledRealdebrid = self.cacheEnabled and tools.Settings.getInteger('scrape.cache.inspection.realdebrid') == 1
			self.cacheEnabledDebridlink = self.cacheEnabled and tools.Settings.getInteger('scrape.cache.inspection.debridlink') == 1
			self.cacheEnabledAlldebrid = self.cacheEnabled and tools.Settings.getInteger('scrape.cache.inspection.alldebrid') == 1
			self.cacheTime = tools.Settings.getCustom('scrape.cache.inspection.time')
			self.cacheTimeLabel = tools.Settings.customLabel(id = 'scrape.cache.inspection.time', value = self.cacheTime)
			self.cacheSave = tools.Time.timestamp() - ProviderBase.settingsGlobalSaveCache()

			self.enabledExtra = self.cacheEnabled or self.precheckLink or self.precheckMetadata

			self.filters = Filters.instance()
			self.excludeDuplicate = self.filters.excludeDuplicate()
			self.excludeKeyword = self.filters.excludeKeyword()
			self.excludeMetadata = self.filters.excludeMetadata()
			self.excludeFormat = self.filters.excludeFormat()
			self.excludeFake = self.filters.excludeFake()
			self.excludeSupport = self.filters.excludeSupport()
			self.excludeBlocked = self.filters.excludeBlocked()
			self.excludeCaptcha = self.filters.excludeCaptcha()
			self.excludePrecheck = self.filters.excludePrecheck()

			if self.cacheEnabled:
				try:
					# Sometimes Orion identifier requets time out during scraping if there are too many other scraping requests busy.
					# Make silent to not show any error notifications if this happens.
					self.cacheOrion = orionoid.Orionoid(silent = True)
					if not self.cacheOrion.accountValid(): self.cacheOrion = None
				except:
					self.cacheOrion = None

				resolverTorrent = (tools.ResolveUrl.installed() and handler.HandleResolveUrl().enabled(handler.Handler.TypeTorrent)) or (tools.UrlResolver.installed() and handler.HandleUrlResolver().enabled(handler.Handler.TypeTorrent))

				self.cacheTypes = []
				self.cacheObjects = []
				self.cacheThreads = []
				if self.cacheEnabledPremiumize:
					premiumizeCore = debrid.premiumize.Core()
					if premiumizeCore.accountValid():
						if premiumizeCore.streamingTorrent():
							self.cacheTypes.append(handler.Handler.TypeTorrent)
							self.cacheObjects.append(premiumizeCore)
						if premiumizeCore.streamingUsenet() and (self.cacheOrion or self.preloadEnabledUsenet):
							self.cacheTypes.append(handler.Handler.TypeUsenet)
							self.cacheObjects.append(premiumizeCore)
						if premiumizeCore.streamingHoster():
							self.cacheTypes.append(handler.Handler.TypeHoster)
							self.cacheObjects.append(premiumizeCore)
					else:
						self.cacheEnabledPremiumize = False
				if self.cacheEnabledOffcloud:
					offcloudCore = debrid.offcloud.Core()
					if offcloudCore.accountValid():
						if offcloudCore.streamingTorrent():
							self.cacheTypes.append(handler.Handler.TypeTorrent)
							self.cacheObjects.append(offcloudCore)
						if offcloudCore.streamingUsenet() and (self.cacheOrion or self.preloadEnabledUsenet):
							self.cacheTypes.append(handler.Handler.TypeUsenet)
							self.cacheObjects.append(offcloudCore)
					else:
						self.cacheEnabledOffcloud = False
				if self.cacheEnabledRealdebrid:
					realdebridCore = debrid.realdebrid.Core()
					if realdebridCore.accountValid() and realdebridCore.streamingTorrent():
						self.cacheTypes.append(handler.Handler.TypeTorrent)
						self.cacheObjects.append(realdebridCore)
					else:
						self.cacheEnabledRealdebrid = False
				if self.cacheEnabledDebridlink:
					if resolverTorrent and Debridlink.authenticated():
						self.cacheTypes.append(handler.Handler.TypeTorrent)
						self.cacheObjects.append(Debridlink)
					else:
						self.cacheEnabledDebridlink = False
				if self.cacheEnabledAlldebrid:
					if resolverTorrent and Alldebrid.authenticated():
						self.cacheTypes.append(handler.Handler.TypeTorrent)
						self.cacheObjects.append(Alldebrid)
					else:
						self.cacheEnabledAlldebrid = False
				if Orion.id():
					self.cacheTypes.append({handler.Handler.TypeTorrent : True, handler.Handler.TypeUsenet : True, handler.Handler.TypeHoster : True})
					self.cacheObjects.append(Orion)

				self.cacheEnabled = len(self.cacheTypes) > 0

			tools.File.makeDirectory(tools.System.profile())

			self.progressTitleOriginal = 0
			self.progressTitleTranslation = 0
			self.progressTitleAlias = 0
			self.progressTitleCollection = 0
			self.progressYearTrakt = 0
			self.progressYearImdb = 0
			self.progressYearTmdb = 0

			self.progressVisible = False
			self.progressPercentage = 0
			self.progressPercentageLast = 0

			percentageDone = 0
			percentageInitialize = 0.05
			percentageAdditional = 0.05 if (self.enabledTitle or self.enabledYear or self.enabledCollection) else 0
			percentagePrecheck = 0.13 if self.precheckLink else 0
			percentageMetadata = 0.13 if self.precheckMetadata else 0
			percentageCache = 0.05 if self.cacheEnabled else 0
			percentageFinalize = 0.04
			percentageExclusion = 0.03
			percentageSaveStreams = 0.02
			percentageProviders = 1 - percentageInitialize - percentageAdditional - percentagePrecheck - percentageMetadata - percentageCache - percentageFinalize - percentageExclusion - percentageSaveStreams - 0.01 # Subtract 0.01 to keep the progress bar always a bit empty in case provided sources something like 123 of 123, even with threads still running.

			self.mLastName = interface.Dialog.title(extension = '', bold = False)
			self.mLastMessage1 = ''
			self.mLastMessage2 = ''

			self.timerScrape = tools.Time()
			timerSingle = tools.Time()
			timeStep = 0.5
			self.timeString = '%s ' + interface.Translation.string(32405)
			self.timeStringDescription = interface.Translation.string(32404) + ': ' + self.timeString

			heading = 'Stream Search'
			message = 'Initializing Providers'
			self._scrapeProgressShow(title = heading, message = message, metadata = metadata)
			self.loaderHide()
			self.timerScrape.start()

			# Ensures that the elapsed time in the dialog is updated more frequently.
			# Otherwise the update is laggy if many threads run.
			timeThread = Pool.thread(target = self._scrapeProgressTime)
			timeThread.start()

			message = 'Initializing Providers'
			self._scrapeProgressUpdate(0, message)

			# Clear old sources from database.
			# Due to long links and metadata, the database entries can grow very large, not only wasting disk space, but also reducing search/insert times.
			# Delete old entries that will be ignored in any case.
			# NB: quick = True: Do not clear the streams database.
			# If the streams database is very large (300MB+), removing old streams and then compressing the database can take very long (15-20 secs).
			# This holds up the scraping process ('Initializing Providers' takes 20secs+ instead of the normal 5secs). Instead compress the streams database only on addon launch.
			ProviderManager.databaseInitialize(quick = True)

			self.skip = False
			specialAllow = False

			if (specialAllow or not self.progressCanceled()):
				timeout = 30 # Do not make this too low, since native titles retrival depends on this.
				message = 'Initializing Providers'
				thread = Pool.thread(target = initializeProviders, args = (media, preset))

				thread.start()
				timerSingle.start()
				while True:
					try:
						if self.progressCanceled():
							specialAllow = False
							break
						if not thread.is_alive(): break
						self._scrapeProgressUpdate(int((min(1, timerSingle.elapsed() / float(timeout))) * percentageInitialize * 100), message)
						tools.Time.sleep(timeStep)
					except:
						tools.Logger.error()

				self.timeInitialize = timerSingle.elapsed()

			if len(self.providers) == 0 and (specialAllow or not self.progressCanceled()):
				if not self.silent: interface.Dialog.notification(message = 'No Providers Available', icon = interface.Dialog.IconError)
				self.stopProviders()
				tools.Time.sleep(0.3) # Ensure the time thread (0.2 interval) is stopped.
				if len(self.sourcesAdjusted) == 0: return None # Orion found a few links, but not enough, causing other providers to be searched.
			elif (not specialAllow and self.progressCanceled()):
				self.stopProviders()
				tools.Time.sleep(0.3) # Ensure the time thread (0.2 interval) is stopped.
				return None

			if not exact and (specialAllow or not self.progressCanceled()):
				percentageDone = percentageInitialize
				message = 'Retrieving Additional Metadata'
				timeout = 45

				thread = Pool.thread(target = additional, args = (title, tvshowtitle, year, imdb, tmdb, tvdb, trakt, season, episode, metadata))
				thread.start()

				timerSingle.start()
				while True:
					try:
						if self.progressCanceled():
							specialAllow = False
							break
						if (not thread or not thread.is_alive()): break

						total = [self.progressTitleOriginal, self.progressTitleTranslation, self.progressTitleAlias, self.progressTitleCollection, self.progressYearTrakt, self.progressYearImdb, self.progressYearTmdb]
						total = sum(total) / float(len(total))
						self._scrapeProgressUpdate(int((total * percentageAdditional) + percentageDone), message)
						tools.Time.sleep(timeStep)
						if timerSingle.elapsed() >= timeout: break
					except:
						tools.Logger.error()

				self.timeMetadata = timerSingle.elapsed()

				if not specialAllow and self.progressCanceled():
					self.stopProviders()
					tools.Time.sleep(0.3) # Ensure the time thread (0.2 interval) is stopped.
					return None

			# Finding Sources
			self.skip = True

			threadProvider = Pool.thread(target = self.scrapeProviders, args = (threads, labels, self.providers, media, niche, self.titles, self.years, release, imdb, tmdb, tvdb, trakt, season, episode, number, self.originalLanguage, self.originalCountry, self.originalNetwork, self.originalStudio, self.pack, duration, exact, cache))
			threadProvider.start()

			if (specialAllow or not self.progressCanceled()):
				percentageDone = percentageAdditional + percentageInitialize
				message = 'Finding Stream Sources'
				stringInput1 = 'Processed Providers: %d of %d'
				stringInput2 = 'Providers: %d of %d'
				stringInput3 = interface.Format.newline() + 'Streams Found: %d'
				timeout = ProviderBase.settingsGlobalLimitTime()
				timerSingle.start()

				# Wait until providers were started, so that we can correctly calculate self.providersFinished.
				while not self.startedThreads and not self.stopThreads:
					if self.progressCanceled(): break
					if self.finishedThreads: break
					tools.Time.sleep(0.1)

				totalProviders = len(self.providers)

				unresponsiveTime = 0
				self.unresponsiveEnabled = self.unresponsiveEnabled and totalProviders > self.unresponsiveLimit # Ignore if only a few providers are enabled.
				while True:
					try:
						if self.progressCanceled():
							interface.Loader.show()
							specialAllow = True
							self.stopProviders()
							break
						if timerSingle.elapsed() >= timeout:
							tools.Logger.log('Scraping Timeout Reached', name = 'CORE', type = tools.Logger.TypeInfo)
							self.stopProviders()
							break
						if self.terminated:
							self.stopProviders()
							break

						totalThreads = len(threads)
						providersLabels = []
						if self.startedThreads and totalThreads > 0:
							self.providersLabels = []
							for x in range(totalThreads):
								if threads[x].is_alive():
									self.providersLabels.append(labels[x])
							providersLabels = self.providersLabels
						else:
							self.providersLabels = None

						busy = len(providersLabels)
						if self.stopThreads: self.providersBusy = 0
						else: self.providersBusy = busy + self.providersWait
						self.providersFinished = totalProviders - self.providersBusy

						foundStreams = []
						if len(foundStreams) < 2 and self.streamsHdUltra > 0: foundStreams.append('%sx HDULTRA' % self.streamsHdUltra)
						if len(foundStreams) < 2 and self.streamsHd1080 > 0: foundStreams.append('%sx HD1080' % self.streamsHd1080)
						if len(foundStreams) < 2 and self.streamsHd720 > 0: foundStreams.append('%sx HD720' % self.streamsHd720)
						if len(foundStreams) < 2 and self.streamsSd > 0: foundStreams.append('%sx SD' % self.streamsSd)
						if len(foundStreams) < 2 and self.streamsLd > 0: foundStreams.append('%sx LD' % self.streamsLd)
						if len(foundStreams) > 0: foundStreams = ' [%s]' % (', '.join(foundStreams))
						else: foundStreams = ''

						percentage = int((((self.providersFinished / float(totalProviders)) * percentageProviders) + percentageDone) * 100)
						stringProvidersValue1 = stringInput1 % (self.providersFinished, totalProviders)
						stringProvidersValue2 = stringInput2 % (self.providersFinished, totalProviders)
						if self.enabledProviders and busy > 0: stringProvidersValue1 += ' [%s]' % (', '.join(providersLabels[:3]))
						stringProvidersValue1 += (stringInput3 % len(self.sourcesAdjusted)) + foundStreams
						self._scrapeProgressUpdate(percentage, message, stringProvidersValue1, stringProvidersValue2)

						# Make  sure to update the final stats in the window before breaking out.
						if self.providersBusy == 0 and ((threadProvider and not threadProvider.is_alive()) or self.stopThreads): break
						if self.unresponsiveEnabled:
							if self.providersBusy <= self.unresponsiveLimit:
								unresponsiveTime += timeStep
								if unresponsiveTime >= self.unresponsiveTime:
									tools.Logger.log('Unresponsive Termination Triggered', name = 'CORE', type = tools.Logger.TypeInfo)
									break

						tools.Time.sleep(timeStep)
					except:
						tools.Logger.error()
						break

				self.timeScrape = timerSingle.elapsed()
				self.usage = tools.Hardware.usageStop()

				# NB: Check in the end. In case the movie/episode is accessed on a subsequent run, it will be retrieved from the local cache database.
				# In such a case the early termination is not triggered.
				self.adjustTermination()

			self.skip = False
			self.providersLabels = []

			# Special handle for cancel on scraping. Allows to still inspect debrid cache after cancellation.
			if (specialAllow or not self.progressCanceled()):
				specialAllow = True
				if self.progressCanceled(): self.progressClose()
				tools.Time.sleep(0.2) # Important, otherwise close and open can clash.
				percentageDone = percentageAdditional + percentageProviders + percentageInitialize
				message = 'Stopping Stream Collection'
				self._scrapeProgressShow(title = heading, message = message, metadata = metadata)
				self._scrapeProgressUpdate(percentageDone, message, ' ', ' ')
				interface.Loader.hide()

			# Failures
			# Do not detect failures if the scraping was canceled.
			if (specialAllow or not self.progressCanceled()) and self.enabledFailures:
				self._scrapeProgressUpdate(None, 'Detecting Provider Failures', ' ', ' ')
				threadsFinished = []
				threadsUnfinished = []
				for i in range(len(threads)):
					# Since various timeouts in the providers are automatically adjusted based on the scraping timeout, provider threads will typically exit before the scrape timeout.
					# Hence, checking if threads are still alive is not a reliable way of detecting failures.
					#if threads[i].is_alive(): threadsUnfinished.append(self.providers[i]['id'])
					#else: threadsFinished.append(self.providers[i]['id'])
					if self.providers[i].resultCount(): threadsFinished.append(self.providers[i]['id'])
					else: threadsUnfinished.append(self.providers[i]['id'])
				ProviderManager.failureUpdate(finished = threadsFinished, unfinished = threadsUnfinished)

			del threads[:] # Make sure all providers are stopped.

			# Prechecks
			if (specialAllow or not self.progressCanceled()) and self.precheckLink:
				percentageDone = percentageAdditional + percentageProviders + percentageInitialize
				message = 'Checking Stream Availability'
				stringInput1 = 'Processed Streams: %d of %d'
				stringInput2 = 'Streams: %d of %d'
				timeout = self.precheckLinkTime
				timerSingle.start()

				while True:
					try:
						if self.progressCanceled():
							specialAllow = False
							break
						if timerSingle.elapsed() >= timeout:
							break

						totalThreads = self.cacheCount + len(self.tasksAdjusted)
						self.streamsFinished = self.cacheCount + len([x for x in self.tasksAdjusted if x['status'] == 'done'])
						self.streamsBusy = totalThreads - self.streamsFinished

						if self.streamsBusy == 0: break

						percentage = int((((self.streamsFinished / float(totalThreads)) * percentagePrecheck) + percentageDone) * 100)
						stringSourcesValue1 = stringInput1 % (self.streamsFinished, totalThreads)
						stringSourcesValue2 = stringInput2 % (self.streamsFinished, totalThreads)
						self._scrapeProgressUpdate(percentage, message, stringSourcesValue1, stringSourcesValue2)

						tools.Time.sleep(timeStep)
					except:
						tools.Logger.error()
						break

				self.timePrecheck = timerSingle.elapsed()

			# Metadata
			if (specialAllow or not self.progressCanceled()) and self.precheckMetadata:
				percentageDone = percentagePrecheck + percentageAdditional + percentageProviders + percentageInitialize
				message = 'Checking Additional Metadata'
				stringInput1 = 'Processed Streams: %d of %d'
				stringInput2 = 'Streams: %d of %d'
				timeout = self.precheckMetadataTime
				timerSingle.start()

				while True:
					try:
						if self.progressCanceled():
							specialAllow = False
							break
						if timerSingle.elapsed() >= timeout:
							break

						totalThreads = self.cacheCount + len(self.tasksAdjusted)
						self.streamsFinished = self.cacheCount + len([x for x in self.tasksAdjusted if x['status'] == 'done'])
						self.streamsBusy = totalThreads - self.streamsFinished

						if self.streamsBusy == 0: break

						percentage = int((((self.streamsFinished / float(totalThreads)) * percentageMetadata) + percentageDone) * 100)
						stringSourcesValue1 = stringInput1 % (self.streamsFinished, totalThreads)
						stringSourcesValue2 = stringInput2 % (self.streamsFinished, totalThreads)
						self._scrapeProgressUpdate(percentage, message, stringSourcesValue1, stringSourcesValue2)

						tools.Time.sleep(timeStep)
					except:
						tools.Logger.error()
						break

				self.timeMetadata = timerSingle.elapsed()

			# Finalizing Providers
			# Wait for all the source threads to complete.
			# This is especially important if there are not prechecks, metadata, or debrid cache inspection, and a provider finishes with a lot of streams just before the timeout.
			if specialAllow or not self.progressCanceled():
				percentageDone = percentageMetadata + percentagePrecheck + percentageAdditional + percentageProviders + percentageInitialize
				message = 'Finalizing Stream Collection'
				stringInput1 = 'Processed Streams: %d of %d'
				stringInput2 = 'Streams: %d of %d'
				timeout = 60 # Can take some while for a lot of streams.
				unfinishedCounter = 0
				timerSingle.start()

				self.adjustSourceStart(full = True) # Sometimes there is just 1 unfinished stream adjustment (not sure why). Maybe this helps.

				while True:
					try:
						elapsedTime = timerSingle.elapsed()
						if self.progressCanceled() or elapsedTime >= timeout:
							break

						totalThreads = self.cacheCount + len(self.tasksAdjusted)
						self.streamsFinished = self.cacheCount + len([x for x in self.tasksAdjusted if x['status'] == 'done'])
						self.streamsBusy = totalThreads - self.streamsFinished

						if self.streamsBusy == 0: break

						# Sometimes adjusting is stuck on processing a few remaining links (eg: 2 links).
						# If less than 3% of links are busy, do not wait for the full timeout.
						# NB: This should not happen anymore (aka fixed). Check the explanation in adjustSourceStart().
						if self.streamsBusy <= 10 or (self.streamsBusy / float(totalThreads)) < 0.03:
							unfinishedCounter += 1
							if unfinishedCounter >= (15 / timeStep): break # 15 secs.

						percentage = int((((elapsedTime / float(timeout)) * percentageFinalize) + percentageDone) * 100)
						stringSourcesValue1 = stringInput1 % (self.streamsFinished, totalThreads)
						stringSourcesValue2 = stringInput2 % (self.streamsFinished, totalThreads)
						self._scrapeProgressUpdate(percentage, message, stringSourcesValue1, stringSourcesValue2)

						tools.Time.sleep(timeStep)
					except:
						tools.Logger.error()
						break

				self.timeFinalize = timerSingle.elapsed()

			# Debrid Cache
			if (specialAllow or not self.progressCanceled()) and self.cacheEnabled:
				percentageDone = percentageFinalize + percentageMetadata + percentagePrecheck + percentageAdditional + percentageProviders + percentageInitialize
				message = 'Inspecting Debrid Cache'
				stringInput1 = ' ' # Must have space to remove line.
				stringInput2 = 'Inspecting Debrid Cache'
				timeout = self.cacheTime
				timerSingle.start()

				thread = Pool.thread(target = self.adjustSourceCache, args = (timeout, False))
				thread.start()
				while True:
					try:
						elapsedTime = timerSingle.elapsed()
						if self.progressCanceled():
							specialAllow = False
							break
						if elapsedTime >= timeout:
							break
						if not thread.is_alive():
							if not self.cacheBusy: break

						percentage = int((((elapsedTime / float(timeout)) * percentageCache) + percentageDone) * 100)
						self._scrapeProgressUpdate(percentage, message, stringInput1, stringInput2)

						tools.Time.sleep(timeStep)
					except:
						tools.Logger.error()
						break

				self.timeCache = timerSingle.elapsed()

			# Must be after debrid cache inspection finished, since the cache status is propagated to other streams in adjustSourceExclusion().
			if specialAllow or not self.progressCanceled():
				percentageDone = percentageFinalize + percentageMetadata + percentagePrecheck + percentageAdditional + percentageProviders + percentageCache + percentageInitialize
				message = 'Finalizing Stream Exclusions'
				stringInput1 = ' ' # Must have space to remove line.
				stringInput2 = 'Excluding Undesired Streams'
				timeout = 60
				timerSingle.start()

				thread = Pool.thread(target = self.adjustSourceExclusion)
				thread.start()
				while True:
					try:
						elapsedTime = timerSingle.elapsed()
						if self.progressCanceled():
							specialAllow = False
							break
						if elapsedTime >= timeout:
							break
						if not thread.is_alive():
							break

						percentage = int((((elapsedTime / float(timeout)) * percentageExclusion) + percentageDone) * 100)
						self._scrapeProgressUpdate(percentage, message, stringInput1, stringInput2)

						tools.Time.sleep(timeStep)
					except:
						tools.Logger.error()
						break

				self.timeExclusion = timerSingle.elapsed()

			# Saving Streams

			percentageDone = percentageFinalize + percentageExclusion + percentageMetadata + percentagePrecheck + percentageAdditional + percentageProviders + percentageCache + percentageInitialize
			message = 'Saving Streams'
			stringInput1 = ' ' # Must have space to remove line.
			stringInput2 = 'Saving Streams'
			timeout = 60 # 30 secs sometimes too little for a few 1000 streams.
			timerSingle.start()
			thread = Pool.thread(target = self.adjustSourceDatabase) # Update Database
			thread.start()

			if not self.progressCanceled(): # The thread is still running in the background, even if the dialog was canceled previously.
				while True:
					try:
						elapsedTime = timerSingle.elapsed()
						if not thread.is_alive():
							break
						if self.progressCanceled() or elapsedTime >= timeout:
							break

						percentage = int((((elapsedTime / float(timeout)) * percentageSaveStreams) + percentageDone) * 100)
						self._scrapeProgressUpdate(percentage, message, stringInput1, stringInput2)

						tools.Time.sleep(timeStep)
					except:
						tools.Logger.error()
						break

				self.timeSave = timerSingle.elapsed()

			# Sources
			metadata = MetaTools.reduce(metadata = metadata, seasons = True, copy = False) # Remove excessive unused metadata.
			self.sources = self.sourcesAdjusted
			for i in range(len(self.sources)):
				self.sources[i]['media'] = self.media
				self.sources[i]['metadata'] = metadata # Required by handler for selecting the correct episode from a season pack.

			self.stopThreads = True
			tools.Time.sleep(0.3) # Ensure the time thread (0.2 interval) is stopped.

			self._scrapeProgressUpdate(100, 'Preparing Streams', ' ', ' ', showElapsed = False)

			# Clear because member variable.
			self.tasksAdjusted = []
			self.sourcesAdjusted = []

			tools.Logger.log('Scraping Finished', name = 'CORE', type = tools.Logger.TypeInfo)

			return self.sources
		except:
			tools.Logger.error()
			tools.Hardware.usageStop()
			return None

	def scrapeStatistics(self):
		try:
			# Do not print statistics when reloading the stream window.
			if not self.new: return

			from lib.modules.convert import ConverterDuration
			items = []

			try:
				unresponsiveEnabled = self.unresponsiveEnabled
				unresponsiveTimeLabel = self.unresponsiveTimeLabel
				unresponsiveLimitLabel = self.unresponsiveLimitLabel
			except:
				unresponsiveEnabled = tools.Settings.getBoolean('scrape.termination.unresponsive')
				unresponsiveTimeLabel = tools.Settings.customLabel(id = 'scrape.termination.unresponsive.time', value = tools.Settings.getCustom('scrape.termination.unresponsive.time'))
				unresponsiveLimitLabel = tools.Settings.customLabel(id = 'scrape.termination.unresponsive.limit', value = tools.Settings.getCustom('scrape.termination.unresponsive.limit'))

			try:
				cacheEnabled = self.cacheEnabled
				cacheTimeLabel = self.cacheTimeLabel
			except:
				cacheEnabled = tools.Settings.getBoolean('scrape.cache.inspection')
				cacheTimeLabel = tools.Settings.customLabel(id = 'scrape.cache.inspection.time', value = tools.Settings.getCustom('scrape.cache.inspection.time'))
			cacheEnabledPremiumize = cacheEnabled and tools.Settings.getInteger('scrape.cache.inspection.premiumize')
			cacheEnabledOffcloud = cacheEnabled and tools.Settings.getInteger('scrape.cache.inspection.offcloud')
			cacheEnabledRealdebrid = cacheEnabled and tools.Settings.getInteger('scrape.cache.inspection.realdebrid')
			cacheEnabledDebridlink = cacheEnabled and tools.Settings.getInteger('scrape.cache.inspection.debridlink')
			cacheEnabledAlldebrid = cacheEnabled and tools.Settings.getInteger('scrape.cache.inspection.alldebrid')

			# Summary

			duration = self.timerGlobal.elapsed()
			if self.timerTotal: duration += self.timerTotal
			duration = ConverterDuration(duration, unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatInitialShort).lower()
			items1 = [
				{'label' : 'Scrape Title', 'value' : self.scrapeLabel},
				{'label' : 'Scrape Duration', 'value' : duration},
				{'label' : 'Provider Count', 'value' : len(self.providers)},
				{'label' : 'Stream Count', 'value' : self.filter['final'] if self.filter and 'final' in self.filter else 0},
			]
			items.append({'section' : 'Summary', 'items' : items1, 'align' : True, 'empty' : True})

			# Duration

			items2 = [
				{'label' : 'Provider Initialize Duration', 'value' : ConverterDuration(self.timeInitialize, unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatInitialShort).lower()},
				{'label' : 'Metadata Retrieve Duration', 'value' : ConverterDuration(self.timeMetadata, unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatInitialShort).lower()},
				{'label' : 'Provider Scrape Duration', 'value' : ConverterDuration(self.timeScrape, unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatInitialShort).lower()},
				{'label' : 'Stream Precheck Duration', 'value' : ConverterDuration(self.timePrecheck, unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatInitialShort).lower()},
				{'label' : 'Stream Metadata Duration', 'value' : ConverterDuration(self.timeMetadata, unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatInitialShort).lower()},
				{'label' : 'Stream Finalize Duration', 'value' : ConverterDuration(self.timeFinalize, unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatInitialShort).lower()},
				{'label' : 'Stream Exclusion Duration', 'value' : ConverterDuration(self.timeExclusion, unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatInitialShort).lower()},
				{'label' : 'Debrid Cache Duration', 'value' : ConverterDuration(self.timeCache, unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatInitialShort).lower()},
				{'label' : 'Stream Save Duration', 'value' : ConverterDuration(self.timeSave, unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatInitialShort).lower()},
			]
			items1 = [{'label' : 'Total Duration', 'value' : duration, 'items' : items2}]
			items.append({'section' : 'Duration', 'items' : items1, 'align' : True, 'empty' : True})

			# Hardware

			items1 = [
				{'label' : 'Processor Utilized', 'value' : self.usage['processor']['label'] if self.usage else 'Unknown'},
				{'label' : 'Memory Utilized', 'value' : self.usage['memory']['label'] if self.usage else 'Unknown'},
			]
			items.append({'section' : 'Hardware', 'items' : items1, 'align' : True, 'empty' : True})

			# Providers

			labelLength = 0
			queryHas = False
			for provider in self.providers:
				length = len(provider.name())
				if length > labelLength: labelLength = length
				for query in provider.statistics()['search'].keys():
					if query:
						queryHas = True
						length = len(query)
						if length > labelLength: labelLength = length
			if queryHas and labelLength: labelLength += 3 # Quotes + colon

			items1 = []
			for provider in tools.Tools.listSort(self.providers, key = lambda i : i.name().lower()):
				statistics = provider.statistics()

				items2 = []
				for query, data in statistics['search'].items():
					if data['cache']: label = 'Cached'
					elif query: label = '"%s"' % query
					else: label = 'Default' # For providers other than web.py, or for web providers where a "request" is counted outside a query (eg: authentication, token, or cookie retrieval).
					duration = ConverterDuration(data['duration'], unit = ConverterDuration.UnitMillisecond).string(format = ConverterDuration.FormatInitialFixed, unit = ConverterDuration.UnitSecond).lower().ljust(3)
					value = 'Duration: %s | Streams: %s | Queries: %s | Pages: %s | Requests: %s' % (duration, str(data['stream']).ljust(4), str(data['query']).ljust(2), str(data['page']).ljust(2), str(data['request']).ljust(3))
					items2.append({'label' : label, 'value' : value, 'level' : tools.Logger.LevelExtended})

				duration = ConverterDuration(statistics['duration'], unit = ConverterDuration.UnitMillisecond).string(format = ConverterDuration.FormatInitialFixed, unit = ConverterDuration.UnitSecond).lower().ljust(3)
				value = 'Duration: %s | Streams: %s | Queries: %s | Pages: %s | Requests: %s' % (duration, str(statistics['stream']).ljust(4), str(statistics['query']).ljust(2), str(statistics['page']).ljust(2), str(statistics['request']).ljust(3))
				if items2: items1.append({'label' : provider.name(), 'value' : value, 'items' : items2}) # Check if there are items2, to remove providers that did not search (eg: searched movie, but the provider can only search shows).

			items.append({'section' : 'Providers', 'items' : items1, 'align' : True, 'empty' : True})

			# Metadata

			statistics = Stream.statisticsSummary()
			items1 = []
			labelLength = 0
			for type in [Stream.StatisticGlobal, Stream.StatisticExtracted, Stream.StatisticCached, Stream.StatisticFailed]:
				length = len(type)
				if length > labelLength: labelLength = length
			labelLength += 1
			for type in [Stream.StatisticGlobal, Stream.StatisticExtracted, Stream.StatisticCached, Stream.StatisticFailed]:
				total = ConverterDuration(statistics[type]['total'], unit = ConverterDuration.UnitMillisecond).string(format = ConverterDuration.FormatInitialShort).lower().ljust(6)
				average = ConverterDuration(statistics[type]['average'], unit = ConverterDuration.UnitMillisecond).string(format = ConverterDuration.FormatInitialFixed, unit = ConverterDuration.UnitMillisecond).lower().ljust(5)
				minimum = ConverterDuration(statistics[type]['minimum'], unit = ConverterDuration.UnitMillisecond).string(format = ConverterDuration.FormatInitialFixed, unit = ConverterDuration.UnitMillisecond).lower()
				maximum = ConverterDuration(statistics[type]['maximum'], unit = ConverterDuration.UnitMillisecond).string(format = ConverterDuration.FormatInitialFixed, unit = ConverterDuration.UnitMillisecond).lower()
				value = 'Streams: %s | Total Duration: %s | Average Duration: %s (%s - %s)' % (str(statistics[type]['count']).ljust(4), total, average, minimum, maximum)
				items1.append({'label' : type.capitalize(), 'value' : value})
			items.append({'section' : 'Metadata', 'items' : items1, 'align' : True, 'empty' : True})

			# Filter

			count = 0
			filters = [
				['initial', 'Count Initial Before Filtering'],
				['duplicate', 'Count After Duplicates Removal'],
				['keyword', 'Count After Prohibited Keywords'],
				['format', 'Count After Incorrect Formats'],
				['metadata', 'Count After Invalid Metadata'],
				['fake', 'Count After Fake Uploads'],
				['support', 'Count After Unsupported Streams'],
				['blocked', 'Count After Blocked Hosters'],
				['captcha', 'Count After Captcha Protected'],
				['precheck', 'Count After Precheck Failures'],
				['filter', 'Count After Stream Filtering'],
				['limit', 'Count After Stream Limiting'],
				['final', 'Count Final After Filtering'],
			]
			items2 = []
			if self.filter:
				for i in filters:
					if not self.filter[i[0]] is None: count = self.filter[i[0]]
					items2.append({'label' : i[1], 'value' : count})
			items1 = [{'label' : 'Stream Count', 'value' : count, 'items' : items2}]
			items.append({'section' : 'Filters', 'items' : items1, 'align' : True, 'empty' : True})

			# Settings

			enabled = 'Enabled'
			disabled = 'Disabled'
			unlimited = 'Unlimited'
			native = 'Native'
			orion = 'Orion'
			full = 'Full'
			quick = 'Quick'
			items1 = []

			items2 = [
				{'label' : 'Time Limit', 'value' : ProviderBase.settingsGlobalLimitTimeLabel()},
				{'label' : 'Query Limit', 'value' : ProviderBase.settingsGlobalLimitQueryLabel()},
				{'label' : 'Page Limit', 'value' : ProviderBase.settingsGlobalLimitPageLabel()},
				{'label' : 'Request Limit', 'value' : ProviderBase.settingsGlobalLimitRequestLabel()},
			]
			items1.append({'label' : 'Limits', 'items' : [i for i in items2 if not i is None]})

			packEnabled = ProviderBase.settingsGlobalPackEnabled()
			items2 = [
				{'label' : 'Pack Scraping', 'value' : enabled if packEnabled else disabled},
				{'label' : 'Movie Packs', 'value' : enabled if ProviderBase.settingsGlobalPackMovie() else disabled} if packEnabled else None,
				{'label' : 'Show Packs', 'value' : enabled if ProviderBase.settingsGlobalPackShow() else disabled} if packEnabled else None,
				{'label' : 'Season Packs', 'value' : enabled if ProviderBase.settingsGlobalPackSeason() else disabled} if packEnabled else None,
			]
			items1.append({'label' : 'Packs', 'items' : [i for i in items2 if not i is None]})

			titleEnabled = ProviderBase.settingsGlobalTitleEnabled()
			items2 = [
				{'label' : 'Alternative Titles', 'value' : enabled if titleEnabled else disabled},
				{'label' : 'Special Characters', 'value' : enabled if ProviderBase.settingsGlobalTitleCharacter() else disabled} if titleEnabled else None,
				{'label' : 'Original Title', 'value' : enabled if ProviderBase.settingsGlobalTitleOriginal() else disabled} if titleEnabled else None,
				{'label' : 'Native Title', 'value' : enabled if ProviderBase.settingsGlobalTitleNative() else disabled} if titleEnabled else None,
				{'label' : 'Local Title', 'value' : enabled if ProviderBase.settingsGlobalTitleLocal() else disabled} if titleEnabled else None,
				{'label' : 'Alias Titles', 'value' : enabled if ProviderBase.settingsGlobalTitleAlias() else disabled} if titleEnabled else None,
				{'label' : 'Title Language', 'value' : tools.Language.name(ProviderBase.settingsGlobalTitleLanguage())} if titleEnabled and (ProviderBase.settingsGlobalTitleLocal() or ProviderBase.settingsGlobalTitleAlias()) else None,
			]
			items1.append({'label' : 'Titles', 'items' : [i for i in items2 if not i is None]})

			keywordEnabled = ProviderBase.settingsGlobalKeywordEnabled()
			items2 = [
				{'label' : 'Alternative Keywords', 'value' : enabled if keywordEnabled else disabled},
				{'label' : 'English Keywords', 'value' : quick if ProviderBase.settingsGlobalKeywordEnglish() == 1 else full if ProviderBase.settingsGlobalKeywordEnglish() == 2 else disabled} if keywordEnabled else None,
				{'label' : 'Original Keywords', 'value' : quick if ProviderBase.settingsGlobalKeywordOriginal() == 1 else full if ProviderBase.settingsGlobalKeywordOriginal() == 2 else disabled} if keywordEnabled else None,
				{'label' : 'Native Keywords', 'value' : quick if ProviderBase.settingsGlobalKeywordNative() == 1 else full if ProviderBase.settingsGlobalKeywordNative() == 2 else disabled} if keywordEnabled else None,
				{'label' : 'Custom Keywords', 'value' : quick if ProviderBase.settingsGlobalKeywordCustom() == 1 else full if ProviderBase.settingsGlobalKeywordCustom() == 2 else disabled} if keywordEnabled else None,
				{'label' : 'Keyword Language', 'value' : tools.Language.name(ProviderBase.settingsGlobalKeywordLanguage())} if keywordEnabled and ProviderBase.settingsGlobalKeywordCustom() > 0 else None,
			]
			items1.append({'label' : 'Keywords', 'items' : [i for i in items2 if not i is None]})

			yearEnabled = ProviderBase.settingsGlobalYearEnabled()
			items2 = [
				{'label' : 'Alternative Years', 'value' : enabled if titleEnabled else disabled},
			]
			items1.append({'label' : 'Years', 'items' : [i for i in items2 if not i is None]})

			mirrorEnabled = ProviderBase.settingsGlobalMirrorEnabled()
			unblockEnabled = ProviderBase.settingsGlobalUnblockEnabled()
			items2 = [
				{'label' : 'Mirror Domains', 'value' : enabled if mirrorEnabled else disabled},
				{'label' : 'Mirror Limit', 'value' : ProviderBase.settingsGlobalMirrorLimit()} if mirrorEnabled else None,
				{'label' : 'Mirror Unlock', 'value' : enabled if unblockEnabled else disabled},
				{'label' : 'Mirror Service', 'value' : ProviderBase.settingsGlobalUnblockType()} if unblockEnabled else None,
			]
			items1.append({'label' : 'Mirrors', 'items' : [i for i in items2 if not i is None]})

			preemptionEnabled = Termination.settingsEnabled()
			items2 = [
				{'label' : 'Preemptive Termination', 'value' : enabled if preemptionEnabled else disabled},
				{'label' : 'Termination Mode', 'value' : Termination.settingsMode().capitalize()} if preemptionEnabled else None,
				{'label' : 'Unresponsive Termination', 'value' : enabled if unresponsiveEnabled else disabled},
				{'label' : 'Time Limit', 'value' : unresponsiveTimeLabel} if unresponsiveEnabled else None,
				{'label' : 'Provider Limit', 'value' : unresponsiveLimitLabel} if unresponsiveEnabled else None,
			]
			items1.append({'label' : 'Termination', 'items' : [i for i in items2 if not i is None]})

			failureEnabled = ProviderManager.failureEnabled()
			items2 = [
				{'label' : 'Failure Detection', 'value' : enabled if failureEnabled else disabled},
				{'label' : 'Failure Limit', 'value' : ProviderManager.failureLimit()} if failureEnabled else None,
				{'label' : 'Retry Delay', 'value' : ProviderManager.failureTimeLabel()} if failureEnabled else None,
			]
			items1.append({'label' : 'Failures', 'items' : [i for i in items2 if not i is None]})

			items2 = [
				{'label' : 'Cache Inspection', 'value' : enabled if cacheEnabled else disabled},
				{'label' : 'Time Limit', 'value' : cacheTimeLabel} if cacheEnabled else None,
				{'label' : 'Premiumize Inspection', 'value' : orion if cacheEnabledPremiumize == 2 else native if cacheEnabledPremiumize == 1 else disabled} if cacheEnabled else None,
				{'label' : 'OffCloud Inspection', 'value' : orion if cacheEnabledOffcloud == 2 else native if cacheEnabledOffcloud == 1 else disabled} if cacheEnabled else None,
				{'label' : 'RealDebrid Inspection', 'value' : orion if cacheEnabledRealdebrid == 2 else native if cacheEnabledRealdebrid == 1 else disabled} if cacheEnabled else None,
				{'label' : 'DebridLink Inspection', 'value' : orion if cacheEnabledDebridlink == 2 else native if cacheEnabledDebridlink == 1 else disabled} if cacheEnabled else None,
				{'label' : 'AllDebrid Inspection', 'value' : orion if cacheEnabledAlldebrid == 2 else native if cacheEnabledAlldebrid == 1 else disabled} if cacheEnabled else None,
			]
			items1.append({'label' : 'Cache', 'items' : [i for i in items2 if not i is None]})

			concurrency = Pool.settingData()
			items2 = [
				{'label' : 'Concurrency Scrape', 'value' : 'Binge' if self.binge else 'Normal'},
				{'label' : 'Concurrency Mode', 'value' : concurrency['mode']['label']},
				{'label' : 'Concurrency Limit', 'value' : concurrency['binge']['label'] if self.binge else concurrency['scrape']['label']},
				{'label' : 'Concurrency Connections', 'value' : concurrency['connection']['label']},
			]
			items1.append({'label' : 'Concurrency', 'items' : [i for i in items2 if not i is None]})

			items2 = [
				{'label' : 'Developer Options', 'value' : enabled if tools.System.developer(version = False) else disabled},
			]
			items1.append({'label' : 'Developer', 'items' : [i for i in items2 if not i is None]})

			items.append({'section' : 'Settings', 'items' : items1, 'align' : True, 'empty' : True})

			data = tools.Logger.details(title = 'Scrape Statistics', items = items)
			tools.Logger.scrape(data)
		except: tools.Logger.error()

	def scrapeProviders(self, threads, labels, providers, media, niche, titles, years, time, imdb, tmdb, tvdb, trakt, season, episode, number, language, country, network, studio, pack, duration, exact, cache):
		# Reduce the pack data passed to Stream.
		# More info at MetaPack.reduceStream().
		if pack: pack = MetaPack.instance(pack = pack).reduceStream()

		binge = self.binge == tools.Binge.ModeBackground
		ProviderBase.concurrencyInitialize(tasks = len(providers), binge = binge)

		# Do this here instead of inside scrapeProvider().
		# Because the locking in those functions often cause the highest priority provider to get the lock last, while the lowest priority providers get it first.
		# This basically reverses the order in which execute() in the scrapeProvider() threads are executed.
		# This happens because all the hoster...() functions use the same lock.
		hostersAll = self.hosters()
		hostersPremium = self.hostersPremium()

		providers = ProviderManager.providersPrioritize(providers = providers)
		self.providersWait = sum([len(sub) for sub in providers])
		self.finishedThreads = False

		for sub in providers:
			if not self.stopThreads:
				threadsSub = []
				for provider in sub:
					thread = Pool.thread(target = self.scrapeProvider, args = (provider, media, niche, titles, years, time, imdb, tmdb, tvdb, trakt, season, episode, number, language, country, network, studio, pack, duration, exact, cache, hostersAll, hostersPremium))
					threadsSub.append(thread)
					threads.append(thread)
					labels.append(provider.label())

				totalSub = len(threadsSub)
				[thread.start() for thread in threadsSub]
				self.providersWait -= totalSub
				self.startedThreads = True
				[thread.join() for thread in threadsSub]
				self.startedThreads = False

		# If a single provider is scraped a second time, just retrieving thyew results from cache, "startedThreads" is set to True and then immediately  to False.
		# The GUI can then get stuck on "Providers Started", because the value of the variable is set to False again.
		# Use a second variable to indicate everything is done.
		self.finishedThreads = True

	def scrapeProvider(self, provider, media, niche, titles, years, time, imdb, tmdb, tvdb, trakt, season, episode, number, language, country, network, studio, pack, duration, exact, cache, hostersAll, hostersPremium):
		try:
			streams = provider.execute(
				media = media,
				niche = niche,
				titles = titles,
				years = years,
				time = time,

				idImdb = imdb,
				idTmdb = tmdb,
				idTvdb = tvdb,
				idTrakt = trakt,

				numberSeason = season,
				numberEpisode = episode,
				numberPack = number,

				language = language,
				country = country,
				network = network,
				studio = studio,
				pack = pack,
				duration = duration,

				exact = exact,
				silent = self.silent,
				cacheLoad = cache,

				hostersAll = hostersAll,
				hostersPremium = hostersPremium,
			)

			streamsCache = []
			streamsScrape = []
			if streams:
				for stream in streams:
					if stream['stream'].infoCache(): streamsCache.append(stream)
					else: streamsScrape.append(stream)

				self.addSources(streamsCache, False)
				self.addSources(streamsScrape, True)

			termination = provider.scrapeTermination()
			if termination and len(streams) > termination:
				self.stopThreads = True
				tools.Logger.log('Enough links found. Provider termination triggered (%s).' % provider.label(), name = 'CORE', type = tools.Logger.TypeInfo)
		except:
			tools.Logger.error()

	def stopProviders(self):
		self.stopThreads = True
		for provider in self.providers:
			provider.stop()

	def addLink(self, link = None, extras = None, metadata = None):
		if not link:
			interface.Loader.hide()
			link = interface.Dialog.input(title = 35434)

		interface.Loader.show()
		item = None
		if link:
			if metadata is None: metadata = self.propertyMetadata()
			elif tools.Tools.isString(metadata): metadata = tools.Converter.jsonFrom(network.Networker.linkUnquote(metadata))

			try: title = metadata['tvshowtitle']
			except:
				try: title = metadata['title']
				except: title = None
			try: year = metadata['year']
			except: year = None
			try: season = metadata['season']
			except: season = None
			try: episode = metadata['episode']
			except: episode = None

			container = network.Container(link)
			if container.torrentIs(): sourceType = Stream.SourceTypeTorrent
			elif container.usenetIs(): sourceType = Stream.SourceTypeUsenet
			elif network.Networker.linkIsLocal(link) or re.search('^(\/|file|[a-z]:)', link, re.IGNORECASE) or tools.File.samba(link) or tools.File.exists(link): sourceType = Stream.SourceTypeLocal
			else: sourceType = Stream.SourceTypeHoster

			stream = Stream(
				validate = False,
				metaTitle = title, metaYear = year, metaSeason = season, metaEpisode = episode,
				link = link,
				sourceType = sourceType, sourceOrigin = tools.System.name(), sourceProvider = 'Custom',
				accessDirect = sourceType == Stream.SourceTypeLocal,
				infoCustom = True,
			)
			stream.videoQualitySet(value = Stream.VideoQualityHdUltra, extract = False)
			item = {'stream' : stream}

		if extras is None: extras = self.propertyExtras()
		elif tools.Tools.isString(extras): extras = tools.Converter.jsonFrom(network.Networker.linkUnquote(extras))
		if not extras: extras = []
		if item: extras.append(item)
		extras = self.sourcesPrepare(items = extras)

		self.propertyExtrasSet(tools.Tools.copy(extras))

		interface.Loader.show()
		window.WindowStreams.close()
		self.showStreams(extras = extras, metadata = metadata, autoplay = False, add = True)

	def filterStreams(self):
		filters = Filters.instance()
		data = tools.Tools.copy(filters.data()) # Make a copy, otherwise this dictionary is changed as well.
		filters.show()
		if not filters.data() == data: # Only reload if the filters have changed.
			# Without this, when using the Filters dialog from the context menu, about 50% of the time the new WindowStreams does not load, and Kodi goes back to the directory without showing the streams.
			# Manually closing the window seems to solve the problem.
			if 'WindowStreams' in window.Window.currentType(): window.WindowStreams.close()

			interface.Loader.show()
			self.showStreams()

	def mixedStreams(self, items):
		try:
			if items and 'metadata' in items[0]:
				different = False
				previous = None
				for item in items:
					current = item['metadata']

					# Do not just compare the entire metadata, since it can be different when the stream window is reloaded after playback is stopped.
					current = {i : current.get(i) for i in ['trakt', 'imdb', 'tmdb', 'tvdb', 'season', 'episode']}

					if previous and current and not previous == current: return True
					previous = current
		except: tools.Logger.error()
		return False

	def showStreams(self, items = None, extras = None, metadata = None, direct = False, filter = True, autoplay = False, clear = False, library = False, initial = False, new = True, add = False, process = True, binge = None):
		try:
			if clear: self._showClear()

			if items is None:
				items = self.propertyItems()
				# Important for History Streams window.
				# Otherwise the items are processed id the window is reloaded.
				process = self.propertyProcess()
			elif tools.Tools.isString(items):
				items = tools.Converter.jsonFrom(network.Networker.linkUnquote(items))

			if not process: autoplay = False

			if self.navigationScrapeDialog and self.navigationStreamsDirectory:
				# Important to close here and not later.
				self.progressClose(loader = self.navigationStreamsSpecial and new and not autoplay)

			if not direct and self.navigationStreamsDirectory and not(self.navigationCinema and autoplay):
				return self._showStreamsDirectory(filter = filter and (new or binge), autoplay = autoplay, library = library, initial = initial, new = new, add = add, process = process, binge = binge)

			if extras is None: extras = self.propertyExtras()
			elif tools.Tools.isString(extras): extras = tools.Converter.jsonFrom(network.Networker.linkUnquote(extras))

			if (items is None or len(items) == 0) and (extras is None or len(extras) == 0):
				if new:
					self.progressNotification(loader = True, mixed = self.mixedStreams(items = items))
					self.scrapeStatistics()
				self.loaderHide()
				return False

			if metadata is None: metadata = self.propertyMetadata()
			elif tools.Tools.isString(metadata): metadata = tools.Converter.jsonFrom(network.Networker.linkUnquote(metadata))

			itemsFiltered = []
			if items:
				for i in range(len(items)):
					items[i]['stream'] = Stream.load(data = items[i]['stream'])
				if filter:
					if process: itemsFiltered = self.sourcesFilter(items = items, metadata = metadata, autoplay = autoplay)
					else: itemsFiltered = items
					if len(itemsFiltered) == 0:
						if not new or self.progressNotification(mixed = self.mixedStreams(items = itemsFiltered)):
							return self.showStreams(items = items, extras = extras, metadata = metadata, direct = False if autoplay else True, library = library, filter = False, autoplay = False, clear = True, new = new, add = add, binge = binge)
						else:
							self.progressClose(force = True, loader = self.navigationStreamsSpecial and new and not autoplay)
							return False
				else:
					if process: itemsFiltered = self.sourcesFilter(items = items, metadata = metadata, apply = False, autoplay = False)
					else: itemsFiltered = items
				itemsFiltered = self.sourcesLabel(items = itemsFiltered, metadata = metadata)

			self.scrapeStatistics()

			if extras:
				for i in range(len(extras)):
					extras[i]['stream'] = Stream.load(data = extras[i]['stream'])
				itemsFiltered = extras + itemsFiltered

			if autoplay: return self._autoplay(items = itemsFiltered, metadata = metadata, extras = extras, library = library, new = new, add = add, binge = binge, execute = True)

			mixed = self.mixedStreams(items = itemsFiltered) # Determine here, since the 'metadata' attribute is removed from the items in _showStreams().
			if self.navigationStreamsDialogDetailed or self.navigationStreamsDialogPlain:
				self.loaderShow()
				if new: self.progressNotification(mixed = mixed)
			result = self._showStreams(items = itemsFiltered, metadata = metadata, initial = initial, library = library, add = add, binge = binge)
			if not(self.navigationStreamsDialogDetailed or self.navigationStreamsDialogPlain):
				if new: self.progressNotification(mixed = mixed)

			self.progressClose(force = True, loader = self.navigationStreamsSpecial and new)
			return result
		except:
			tools.Logger.error()
			self.progressClose(force = True)
			return None

	def showStreamsExternal(self, filter = None, binge = None, autoplay = None, reload = None):
		interface.Loader.show() # When the streams are filtered/sorted again.
		self.reload = reload
		parameters = {'media' : self.media}
		if not filter is None: parameters['filterx'] = filter
		if not binge is None: parameters['binge'] = binge
		if not autoplay is None: parameters['autoplay'] = autoplay
		tools.System.executePlugin(action = 'streamsShow', parameters = parameters)

	def _showClear(self, filter = False, autoplay = False):
		Filters.clear()

	def _showStreamsDirectory(self, filter = False, autoplay = False, library = False, initial = False, new = True, add = False, process = True, binge = None):
		try:
			if not self.navigationCinema: self.loaderShow()
			tools.Time.sleep(0.2)
			# NB: Use "filterx" and not "filter" as parameters.
			# Otherwise for some weird reason the back button in the directory does not work.
			# Maybe Kodi uses that parameter name internally (eg: left side menu "Filter" option).
			command = '%s?action=streamsShow&direct=%d&filterx=%d&autoplay=%d&library=%d&initial=%d&new=%d&add=%d&process=%d&binge=%d' % (tools.System.arguments(0), True, filter, autoplay, library, initial, new, add, process, int(binge))
			command = self.parameterize(command)
			self.progressClose(force = True, loader = False) # Important to close to free up window memory, since Container.Update is in a separate process which does not know the window anymore.
			if not self.navigationCinema: self.loaderShow()
			if self.navigationCinema and not autoplay: self.navigationCinemaTrailer.cinemaStop() # Must happen here, otherwise the player won't stop.
			if autoplay: result = tools.System.execute('RunPlugin(%s)' % command)
			else: result = tools.System.execute('Container.Update(%s)' % command)
			return result
		except:
			tools.Logger.error()
			return None

	def _showStreams(self, items = None, metadata = None, library = False, initial = False, add = False, binge = None):
		from lib.modules.shortcut import Shortcut

		metatools = MetaTools.instance()

		hasFanart = Theme.artwork()
		addonPoster = Theme.poster()
		addonBanner = Theme.banner()
		addonFanart = Theme.fanart()

		total = len(items)
		mixed = self.mixedStreams(items = items)

		# When loading a menu for 500+ episodes, this function can take 30-40secs, even on an fast CPU.
		# Removing the pack reduces it down to 3-4secs.
		# Not sure if the pack is needed somewhere (eg: context menu, data passed onto the player, binge, etc).
		# If we ever need the pack again and have to remove this statement, take the loading time into account.
		# This is also done below for the stream history window with mutiple titles.
		try: del metadata['pack']
		except: pass

		try: media = metadata['media']
		except: media = None

		try: title = metadata['tvshowtitle']
		except:
			try: title = metadata['originaltitle']
			except:
				try: title = metadata['title']
				except: title = ''

		try: year = metadata['year']
		except: year = None
		try: season = metadata['season']
		except: season = None
		try: episode = metadata['episode']
		except: episode = None

		try: imdb = metadata['imdb']
		except: imdb = None
		try: tmdb = metadata['tmdb']
		except: tmdb = None
		try: tvdb = metadata['tvdb']
		except: tvdb = None
		try: trakt = metadata['trakt']
		except: trakt = None
		id = '' if mixed else tools.Hash.sha1((imdb if imdb else trakt if trakt else tmdb if tmdb else tvdb if tvdb else tools.Converter.jsonTo(metadata)) + '_' + str(season) + '_' + str(episode) + '_' + str(total))

		images = MetaImage.extract(data = metadata)
		if not hasFanart or not MetaImage.TypeFanart in images: images[MetaImage.TypeFanart] = addonFanart
		try: fanart = images[MetaImage.TypeFanart]
		except: fanart = None
		posters = MetaImage.getPoster(data = metadata)
		try: poster1 = posters[0]
		except: poster1 = None
		try: poster2 = posters[1]
		except: poster2 = None
		try: poster3 = posters[2]
		except: poster3 = None
		if not poster1 and not poster2 and not poster3: poster1 = Theme.poster() # Exact searches.

		lookup = {'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt}
		if not season is None: lookup['season'] = season
		if not episode is None: lookup['episode'] = episode

		if self.navigationStreamsDirectory: metadataKodi = metatools.clean(metadata = metadata, exclude = True)
		else: metadataKodi = metatools.clean(metadata = metadata)

		if self.navigationStreamsSpecial:
			if self.navigationCinema and not self.navigationCinemaInerrupt:
				self.navigationCinemaTrailer.cinemaStop()

			window.WindowStreams.show(background = None if mixed else fanart, status = 'Loading Streams', metadata = metadata, items = items, close = not initial)
			window.WindowBackground.close() # Might still be open from player.py -> interact() to allow a continues background during rating/continue/next-episode-playback.

			window.Window.propertyGlobalSet('GaiaIndexId', id) # Used in WindowStreams.
			window.Window.propertyGlobalSet('GaiaPosterStatic', tools.Settings.getInteger('interface.stream.interface.poster') == 0)

			window.Window.propertyGlobalSet('GaiaColorPrimary', interface.Format.colorPrimary())
			window.Window.propertyGlobalSet('GaiaColorSecondary', interface.Format.colorSecondary())
			window.Window.propertyGlobalSet('GaiaColorTertiary', interface.Format.colorTertiary())
			window.Window.propertyGlobalSet('GaiaColorMain', interface.Format.colorMain())
			window.Window.propertyGlobalSet('GaiaColorDisabled', interface.Format.colorDisabled())
			window.Window.propertyGlobalSet('GaiaColorAlternative', interface.Format.colorAlternative())
			window.Window.propertyGlobalSet('GaiaColorSpecial', interface.Format.colorSpecial())
			window.Window.propertyGlobalSet('GaiaColorUltra', interface.Format.colorUltra())
			window.Window.propertyGlobalSet('GaiaColorExcellent', interface.Format.colorExcellent())
			window.Window.propertyGlobalSet('GaiaColorGood', interface.Format.colorGood())
			window.Window.propertyGlobalSet('GaiaColorMedium', interface.Format.colorMedium())
			window.Window.propertyGlobalSet('GaiaColorPoor', interface.Format.colorPoor())
			window.Window.propertyGlobalSet('GaiaColorBad', interface.Format.colorBad())

			for quality in Stream.KodiVideoQuality.keys():
				if quality: window.Window.propertyGlobalSet('GaiaColor' + quality.capitalize(), interface.Format.colorQuality(quality))

			colorHighlightDefault = 'FF000000'
			colorHighlightBase = Stream.accessCacheColor()
			colorHighlightLocal = interface.Format.colorAlpha(color = colorHighlightBase, alpha = 'FF')
			colorHighlightCached = interface.Format.colorAlpha(color = colorHighlightBase, alpha = 'EE')
			colorHighlightDirect = interface.Format.colorAlpha(color = colorHighlightBase, alpha = '77')
			colorHighlightDebrid = interface.Format.colorAlpha(color = colorHighlightBase, alpha = '55')
			colorHighlightCustom = Stream.infoCustomColor()
			colorHighlightDuplicate = Stream.exclusionDuplicateColor()
			colorHighlightKeyword = Stream.exclusionKeywordColor()
			colorHighlightMetadata = Stream.exclusionMetadataColor()
			colorHighlightFormat = Stream.exclusionFormatColor()
			colorHighlightFake = Stream.exclusionFakeColor()
			colorHighlightSupport = Stream.exclusionSupportColor()
			colorHighlightBlocked = Stream.exclusionBlockedColor()
			colorHighlightCaptcha = Stream.exclusionCaptchaColor()

			decorations = tools.Settings.getInteger('interface.stream.interface.decorations')
			decorationsIcons = decorations == 2
			flagLanguage = tools.Settings.getInteger('interface.stream.interface.language')
			flagDisabled = flagLanguage == 0
			flagLabel = flagLanguage == 1
			flagIndividual = flagLanguage == 2
			flagCombined = flagLanguage == 3
		else:
			icons = tools.Settings.getInteger('interface.stream.interface.icons')

		# NB: Using GUI locking might seem to be faster when there only a handlful of streams. However, if there are many streams (eg: 500), not using locking is a lot faster, especially for the directory and special window.
		directoryUpdate = not initial or binge == tools.Binge.ModeContinue
		directory = interface.Directory(content = interface.Directory.ContentFiles, view = False, cache = True, update = directoryUpdate, lock = False)

		format = Stream.settingsFormat()
		separator = Stream.labelSeparator(format = format)
		labelFill = Stream._labelFill()
		enabledCache = tools.Settings.getBoolean('download.cache.enabled')
		controls = []
		contexts = []
		flags = {}
		flagsDefault = {}

		for i in range(total):
			try:
				extra = ''
				itemJson = items[i]
				stream = itemJson['stream']

				orionItem = stream.idOrionItem()
				orionStream = stream.idOrionStream()
				if orionItem and orionStream: orion = {'item' : orionItem, 'stream' : orionStream}
				else: orion = None

				# Set from history where each item is from a differnt movie/show.
				try:
					if mixed:
						metadata = itemJson['metadata']

						# Way faster loading. See full explanation at the top of the function.
						try: del metadata['pack']
						except: pass

						if self.navigationStreamsDirectory: metadataKodi = metatools.clean(metadata = metadata, exclude = True)
						else: metadataKodi = metatools.clean(metadata = metadata)

						try: media = metadata['media']
						except: media = None

						try: title = metadata['tvshowtitle']
						except:
							try: title = metadata['originaltitle']
							except:
								try: title = metadata['title']
								except: title = interface.Translation.string(35160) # Exact searches have not metadata.

						try: year = metadata['year']
						except: year = None
						try: season = metadata['season']
						except: season = None
						try: episode = metadata['episode']
						except: episode = None

						try: imdb = metadata['imdb']
						except: imdb = None
						try: tmdb = metadata['tmdb']
						except: tmdb = None
						try: tvdb = metadata['tvdb']
						except: tvdb = None
						try: trakt = metadata['trakt']
						except: trakt = None

						lookup = {'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt}
						if not season is None: lookup['season'] = season
						if not episode is None: lookup['episode'] = episode

						extra = interface.Format.font((title + ' ' + tools.Title.title(metadata = None, title = '', year = year, season = season, episode = episode, skin = False).strip()).strip(), bold = True)
						if not self.navigationStreamsSpecial: extra += Stream.labelSeparator()

						images = MetaImage.extract(data = metadata)
						if not hasFanart or not MetaImage.TypeFanart in images: images[MetaImage.TypeFanart] = addonFanart
						posters = MetaImage.getPoster(data = metadata)
						try: poster1 = posters[0]
						except: poster1 = None
						try: poster2 = posters[1]
						except: poster2 = None
						try: poster3 = posters[2]
						except: poster3 = None
						if not poster1 and not poster2 and not poster3: poster1 = Theme.poster() # Exact searches.
				except:
					tools.Logger.error()

				# ACTION URL.
				try: del itemJson['metadata'] # Remove the internal metadata dictionary, since the metadata is added to the root level, and this only increases loading time.
				except: pass
				parameters = {
					'handleMode' : handler.Handler.ModeDefault,
					'binge' : bool(binge),
					'reload' : not mixed,
					'source' : {'stream' : itemJson['stream']}, # itemJson can contain other attributes as well, including a full copy of the metadata. Remove all attributes, except the stream.
				}
				parameters.update(lookup)
				parameters = self.parameterize(parameters = parameters)
				url = tools.System.command(action = 'playCache' if not stream.sourceTypeLocal() and enabledCache else 'play', parameters = parameters)

				# ITEM
				if self.navigationStreamsSpecial:
					label = ''
					label2 = ''
					try: images[MetaImage.TypeIcon] = images[MetaImage.TypeThumb]
					except: pass
				else:
					if self.navigationStreamsDialogDetailed:
						label = itemJson['label'][0]
						try: label2 = itemJson['label'][1]
						except: label2 = ''
					else:
						label = interface.Format.fontNewline().join(itemJson['label'])
						label2 = ''

					try: label = label.replace('[GAIANUMBER]', Stream.labelNumber(0 if 'custom' in itemJson and itemJson['custom'] else (i + 1), separator = True, format = format))
					except: pass
					try: label = label.replace('[GAIAEXTRA]', extra)
					except: pass

					if mixed:
						try: images[MetaImage.TypeIcon] = images[MetaImage.TypeThumb]
						except: pass
					else:
						# NB: If icons == 0, the list is a directory, and the icon/poster/etc are set to '' or None, then Kodi throws this error:
						# Kodi ERROR: InputStream: Error opening
						# Set to a non-existing value(eg 'x') to get rid of the errors.
						if icons == 0:
							images[MetaImage.TypeIcon] = 'x'
							images[MetaImage.TypeThumb] = 'x'
							images[MetaImage.TypePoster] = 'x'
							images[MetaImage.TypeBanner] = 'x'
						elif icons == 1:
							try: images[MetaImage.TypeIcon] = images[MetaImage.TypeThumb]
							except: pass
						elif icons == 2:
							images[MetaImage.TypeIcon] = images[MetaImage.TypeThumb] = interface.Icon.path(icon = 'quality' + stream.videoQuality().lower(), quality = interface.Icon.QualityLarge)
						else:
							images[MetaImage.TypeIcon] = images[MetaImage.TypeThumb] = interface.Icon.path(icon = stream.videoQuality().lower(), quality = interface.Icon.QualityLarge, special = interface.Icon.SpecialQuality)

						for x in [MetaImage.PrefixNone, MetaImage.PrefixShow, MetaImage.PrefixSeason]:
							try: images[x + MetaImage.TypePoster] = images[MetaImage.TypeIcon]
							except: pass

				properties = {}

				# SPECIAL WINDOW
				if self.navigationStreamsSpecial:
					name = stream.fileName()
					quality = stream.videoQuality()

					if not name: name = stream.linkPrimary()
					prefix = int(bool(stream.sourceOrigin(label = Stream.LabelSettings, orion = True)))

					# Order is important, since some streams can be True for multiple of the attributes.
					highlight = colorHighlightDefault

					if stream.infoCustom(): highlight = colorHighlightCustom
					elif stream.exclusionSupport(): highlight = colorHighlightSupport
					elif stream.exclusionFormat(): highlight = colorHighlightFormat
					elif stream.exclusionBlocked(): highlight = colorHighlightBlocked
					elif stream.exclusionMetadata(): highlight = colorHighlightMetadata
					elif stream.exclusionDuplicate(): highlight = colorHighlightDuplicate
					elif stream.exclusionKeyword(exception = False): highlight = colorHighlightKeyword
					elif stream.exclusionFake(): highlight = colorHighlightFake
					elif stream.exclusionCaptcha(): highlight = colorHighlightCaptcha
					elif stream.exclusionPrecheck(): highlight = Stream.exclusionPrecheckColor(value = stream.exclusionPrecheck())
					elif stream.sourceTypeLocal(): highlight = colorHighlightLocal
					elif stream.accessCacheAny(account = True): highlight = colorHighlightCached
					elif stream.accessTypeDirect(): highlight = colorHighlightDirect
					elif stream.accessDebridAny(account = True): highlight = colorHighlightDebrid

					languages = stream.language(sort = True) or []
					audioLanguages = stream.audioLanguage(sort = True) or []
					subtitleLanguages = stream.subtitleLanguage(sort = True) or []
					defaultLanguages = stream.audioDefault() or []

					language = stream.labelLanguage(format = format) if flagLabel or not decorationsIcons or not languages else '' # Check "not languages" for exact seaches.
					if languages and (flagIndividual or flagCombined):
						languageHas = not labelFill in language
						contains = []
						index = 0
						for j in range(len(languages)):
							if languages[j] in defaultLanguages and not languages[j] in subtitleLanguages:
								if not languages[j] in flagsDefault:
									# The "colordiffuse" element and the "diffuse" texture attribute both don't change properly when scrolling through the list items (most likley a Kodi bug). Use "light images instead."
									flagsDefault[languages[j]] = tools.Language.flag(languages[j], quality = interface.Icon.QualityLight, combined = flagCombined)
								flag = flagsDefault[languages[j]]
							else:
								if not languages[j] in flags:
									flags[languages[j]] = tools.Language.flag(languages[j], quality = interface.Icon.QualityMini, combined = flagCombined)
								flag = flags[languages[j]]
							if not flag in contains:
								index += 1
								contains.append(flag)
								properties['GaiaLanguageFlag' + str(index)] = flag

					audio1 = stream.labelAudio(type = False, language = False, format = format)
					audio2 = stream.labelAudio(language = flagLabel, format = format)

					if audioLanguages and (flagIndividual or flagCombined):
						audioHas = not labelFill in audio2
						contains = []
						index = 0
						if len(audioLanguages) > 0:
							if audioHas: audio2 += separator
							else: audio2 = None
						for j in range(len(audioLanguages)):
							if audioLanguages[j] in defaultLanguages:
								if not audioLanguages[j] in flagsDefault:
									# The "colordiffuse" element and the "diffuse" texture attribute both don't change properly when scrolling through the list items (most likley a Kodi bug). Use "light images instead."
									flagsDefault[audioLanguages[j]] = tools.Language.flag(audioLanguages[j], quality = interface.Icon.QualityLight, combined = flagCombined)
								flag = flagsDefault[audioLanguages[j]]
							else:
								if not audioLanguages[j] in flags:
									flags[audioLanguages[j]] = tools.Language.flag(audioLanguages[j], quality = interface.Icon.QualityMini, combined = flagCombined)
								flag = flags[audioLanguages[j]]
							if not flag in contains:
								index += 1
								contains.append(flag)
								properties['GaiaAudioFlag' + str(index)] = flag

					subtitle1 = subtitle2 = stream.labelSubtitle(language = flagLabel, format = format)
					if subtitleLanguages and (flagIndividual or flagCombined):
						subtitleHas = not labelFill in subtitle2
						contains = []
						index = 0
						if len(subtitleLanguages) > 0:
							if subtitleHas: subtitle2 += separator
							else: subtitle2 = None
						for j in range(len(subtitleLanguages)):
							if not subtitleLanguages[j] in flags: flags[languages[j]] = tools.Language.flag(subtitleLanguages[j], quality = interface.Icon.QualityMini, combined = flagCombined)
							flag = flags[subtitleLanguages[j]]
							if not flag in contains:
								index += 1
								contains.append(flag)
								properties['GaiaSubtitleFlag' + str(index)] = flag

					properties['GaiaPoster1'] = poster1 if poster1 else ''
					properties['GaiaPoster2'] = poster2 if poster2 else ''
					properties['GaiaPoster3'] = poster3 if poster3 else ''
					properties['GaiaAction'] = url
					properties['GaiaHighlight'] = highlight
					properties['GaiaNumber'] = Stream.labelNumber(i + 1, format = format)
					properties['GaiaExtra'] = extra
					properties['GaiaIcon'] = stream.sourceOriginIcon()
					properties['GaiaPrefix'] = tools.Converter.unicode(prefix)
					properties['GaiaType'] = stream.sourceType()
					properties['GaiaSource'] = stream.labelSource(format = format)
					properties['GaiaSourceExtra'] = stream.labelSource(format = format, extra = extra)
					properties['GaiaPopularity'] = stream.labelPopularity(format = format)
					properties['GaiaTime'] = stream.labelTime(format = format)
					properties['GaiaPeers'] = stream.labelPeers(format = format)
					properties['GaiaSeeds'] = stream.labelSeeds(format = format)
					properties['GaiaLeeches'] = stream.labelLeeches(format = format)
					properties['GaiaRelease1'] = stream.labelRelease(format = format, format_ = False, uploader = False)
					properties['GaiaRelease2'] = stream.labelRelease(format = format, uploader = False, label = Stream.LabelForce)
					properties['GaiaName'] = name
					properties['GaiaSize'] = stream.labelSize(format = format)
					properties['GaiaBandwidth'] = stream.labelBandwidth(format = format)
					properties['GaiaAccess'] = stream.labelAccess(format = format)
					properties['GaiaInfo'] = stream.labelType(format = format)
					properties['GaiaVideo1'] = stream.labelVideo(format = format, _3dPlain = True)
					properties['GaiaVideo2'] = stream.labelVideo(format = Stream.FormatColor if format == Stream.FormatDecorate else format, label = Stream.LabelForce)
					properties['GaiaQuality'] = quality
					properties['GaiaLanguage'] = language
					properties['GaiaAudio1'] = audio1
					properties['GaiaAudio2'] = audio2
					properties['GaiaSubtitle1'] = subtitle1
					properties['GaiaSubtitle2'] = subtitle2

				width, height = stream.videoResolution(format = Stream.FormatKodi)
				audioLanguage = stream.audioLanguage(format = Stream.FormatKodi)
				subtitleLanguage = stream.subtitleLanguage(format = Stream.FormatKodi)
				metadataStream = metatools.stream(
					duration = None if self.navigationStreamsDirectory else stream.metaDuration(), # Otherwise the duration shows in the directory menu.
					videoCodec = stream.videoCodec(format = Stream.FormatKodi),
					videoAspect = stream.videoAspect(format = Stream.FormatKodi),
					videoWidth = width,
					videoHeight = height,
					audioCodec = stream.audioCodec(format = Stream.FormatKodi),
					audioChannels = stream.audioChannels(format = Stream.FormatKodi),
					audioLanguage = audioLanguage,
					subtitleLanguage = subtitleLanguage,
				)

				# NB: playable = False: Needed to transfer the addon handle ID to play.
				# True causes popup dialog from Kodi if playback was unsuccesful.
				# https://forum.kodi.tv/showthread.php?tid=328080
				item = directory.item(label = label, label2 = label2)

				#gaiafuture - Creating a ListItem still take longer than it should.
				#gaiafuture - Can we do this similar to the metadata? That is, rather than passing the link/stream data to each ListItem, store the streams on disk or memory, create a unique ID for each of them.
				#gaiafuture - Then only add the ID to the ListItem and if the item is played or the context menu opened on it (eg: copy stream link), load the data of stream using ID.
				result = metatools.item(label = label, item = item, metadata = metadata, clean = metadataKodi, stream = metadataStream, properties = properties, images = images, playable = False, content = False, command = False, context = not(self.navigationStreamsDialogDetailed or self.navigationStreamsDialogPlain), contextAdd = not self.navigationStreamsSpecial, contextSource = itemJson, contextOrion = orion, contextCommand = url, contextPlaylist = True, contextShortcut = Shortcut.item(create = True)) # Important to command=False, otherwise it creates a new command that is not used and takes longer.

				# ADD ITEM
				if self.navigationStreamsDialogDetailed or self.navigationStreamsDialogPlain:
					controls.append(item)
				else:
					context = result['context']
					if self.navigationStreamsSpecial:
						contexts.append(context)
						controls.append(item)
						window.WindowStreams.update(progress = i / float(total))
					else:
						controls.append([url, item, False])
			except: tools.Logger.error()

		if self.navigationStreamsSpecial:
			window.WindowStreams.itemAdd(item = controls, context = contexts)
			window.WindowStreams.update(progress = 100, finished = True)
			window.WindowStreams.focus()
			if not mixed: window.WindowStreams.itemReselect() # Go to previously selected position if window is reopened.
			self.loaderHide() # When window is reloaded during paused playback and the reloaded window is closed.
		elif self.navigationStreamsDialogDetailed or self.navigationStreamsDialogPlain:
			self.loaderHide()
			if self.navigationStreamsDialogDetailed: choice = interface.Dialog.select(items = controls, details = True)
			else: choice = interface.Dialog.select(items = [i.getLabel() for i in controls])
			if choice >= 0: self.play(items[choice], metadata = metadata, binge = binge)
		else:
			tools.System.pluginPropertySet(property = 'GaiaStreams', value = '1') # Used by scrapeResolve().
			directory.addItems(items = controls)
			directory.finish()
			self.progressClose(force = True, loader = False)
			def closeLoader():
				# Wait until the streams directory is shown.
				for i in range(60):
					if tools.System.infoLabel('Container.Content') == interface.Directory.ContentFiles: break
					tools.Time.sleep(0.5)
				self.loaderHide()
			threadLoader = Pool.thread(target = closeLoader)
			threadLoader.start()

		if self.navigationCinema:
			self.navigationCinemaTrailer.cinemaStop()

		# When launching from the local library, Kodi shows an OK dialog and/or a notification stating that the item couldn't be played, or that it coudln't find the next item in the playlist.
		# These popups happen random and sometimes not at all. It probably depends on the time it takes to scrape/launch Gaia.
		# There seems to be nothing that can be done about these popups, except closing them automatically.
		if library:
			def closePopups():
				for i in range(30): # Don't make this too large, otherwise the Gaia stream notification takes too long to show. 20 is too low.
					interface.Dialog.closeConfirm()
					interface.Dialog.closeNotification()
					tools.Time.sleep(0.05)
				self.progressNotification(force = True) # Reopen.
			threadLibrary = Pool.thread(target = closePopups)
			threadLibrary.start()

	def _autoplay(self, items = None, metadata = None, extras = None, library = None, new = None, add = None, binge = None, reload = False, execute = False):
		self.loaderShow()
		interface.Player.canceledClear()

		# Execute in a separate process, so that we have a "action=play" command which we can re-execute if the VPN disconnects and playback has to be restarted.
		# Only do this if VPN is enabled, since this will cause longer loading times, since the streams have to be retrieved with self.propertyItems().
		if execute:
			from lib.modules.vpn import Vpn
			if Vpn.settingsEnabled():
				self.propertyWait() # Wait for the global properties to be written, otherwise the new process will not be able to load them, since the threads are still busy.
				tools.System.executePlugin(action = 'play', parameters = self.parameterize(parameters = {'library' : library, 'new' : new, 'add' : add, 'binge' : binge, 'autoplay' : True}))
				return None

		if items is None: items = self.propertyItems()
		if metadata is None: metadata = self.propertyMetadata()
		if extras is None: extras = self.propertyExtras()

		items = [i for i in items if ('autoplay' in i and i['autoplay'] == True) or not 'autoplay' in i]
		items = self.sourcesFilter(items = items, metadata = metadata, autoplay = True)

		autoplayInstant = tools.Settings.getBoolean('playback.autoplay.instant')
		autoplayManual = tools.Settings.getBoolean('playback.autoplay.manual')
		if autoplayInstant or autoplayManual:
			instant = []
			uninstant = []
			for item in items:
				stream = item['stream']
				if stream.sourceTypeLocal() or stream.sourceTypePremium() or stream.accessTypeDirect() or stream.accessCacheAny(account = True): instant.append(item)
				else: uninstant.append(item)
			if instant:
				# The order of the streams should be still be intact from sourcesFilter() above.
				# We only move the instant streams to the front.
				if autoplayInstant: items = instant + uninstant
			else:
				if autoplayManual:
					interface.Dialog.notification(title = 35848, message = 36392, icon = interface.Dialog.IconWarning)
					return self.showStreams(items = items, extras = extras, metadata = metadata, autoplay = False, library = library, new = new, add = add, binge = binge)

		imdb = metadata['imdb'] if 'imdb' in metadata else None
		tmdb = metadata['tmdb'] if 'tmdb' in metadata else None
		tvdb = metadata['tvdb'] if 'tvdb' in metadata else None
		trakt = metadata['trakt'] if 'trakt' in metadata else None

		title = metadata['tvshowtitle'] if 'tvshowtitle' in metadata else metadata['title']
		year = metadata['year'] if 'year' in metadata else None
		season = metadata['season'] if 'season' in metadata else None
		episode = metadata['episode'] if 'episode' in metadata else None

		binging = tools.Media.isSerie(self.media) and binge
		success = False
		unsupported = 0
		result = None
		autoHandler = handler.Handler()
		heading = interface.Translation.string(33451)
		message = interface.Translation.string(33452)

		for i in range(len(items)):
			self.progressPlaybackInitialize(title = heading, message = message, metadata = metadata, loader = False)
			if not self.navigationCinema and self.progressPlaybackCanceled(): break
			percentage = int(((i / float(len(items))) * 30) + 20)
			self.progressPlaybackUpdate(progress = percentage, title = heading, message = message)
			try:
				handle = autoHandler.serviceDetermine(mode = handler.Handler.ModeDefault, item = items[i], popups = False)
				if handle == handler.Handler.ReturnUnavailable:
					unsupported += 1
				else:
					result = self.sourceResolve(items[i], handle = handle, info = False, strict = items[i]['stream'].filePack() and not episode is None)
					items[i]['stream'].streamSet(result)
					if result['success']:
						history.History().add(media = self.media, metadata = metadata, stream = items[i]['stream'])
						if not self.navigationCinema and self.progressPlaybackCanceled(): break
						if self.navigationCinema:
							self.navigationCinemaTrailer.cinemaStop()
							self.loaderShow()
							self.progressPlaybackInitialize(title = heading, message = message, metadata = metadata, force = True) # Make sure it is shown after the trailer playback stops.
							self.progressPlaybackUpdate(progress = percentage, title = heading, message = message, force = True)

						tools.Sound.executeStreamFinish()
						from lib.modules.player import Player
						player = Player.instance(reinitialize = True)
						success = player.run(media = self.media, title = title, year = year, season = season, episode = episode, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, metadata = metadata, source = items[i], binge = binge, reload = reload, autoplay = self.autoplay, handle = result['handle'] if 'handle' in result else None, service = result['service'] if 'service' in result else None)

						if success:
							binging = player.bingeContinue
							result = items[i]
							break
			except: tools.Logger.error()

		if not success: binging = False
		if not success and unsupported == len(items): handler.Handler.serviceUnsupported()

		if self.navigationCinema: self.navigationCinemaTrailer.cinemaStop()
		if not binging: self.progressPlaybackClose(loader = not success)
		if not success: interface.Dialog.notification(title = 33448, message = 33574, sound = False, icon = interface.Dialog.IconInformation)

		if result:
			if not binging: self.progressClose(force = True, loader = not success)
			return result
		else:
			return self.showStreams(items = items, extras = extras, metadata = metadata, direct = True, library = library, filter = False, autoplay = False, clear = True, new = new, add = add, binge = binge)

	def _autopack(self, id, metadata = None, binge = None):
		if id and tools.Binge.pack():
			for i in self.sources:
				if i['stream'].hash() == id or id in i['stream'].link():
					return self.play(source = i, metadata = metadata, autopack = True, strict = True, binge = binge)
		return False

	def _metadata(self, metadata = None, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, pack = None):
		try:
			if metadata is None:
				metadata = self.propertyMetadata()

				different = False
				if metadata:
					for k, v in {'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode}.items():
						value = metadata.get(k)
						if not value is None and not v is None and not value == v:
							different = True
							break
				if different: metadata = None

			if not metadata and media and (imdb or tmdb or tvdb or trakt): metadata = MetaManager.instance().metadata(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, pack = pack)
		except: tools.Logger.error()
		return metadata

	def play(self, source, metadata = None, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, downloadType = None, downloadId = None, handle = None, handleMode = None, index = None, autoplay = None, autopack = None, library = None, new = None, add = None, binge = None, reload = True, resume = None, strict = False):
		try:
			tools.Sound.executeStreamStart()
			interface.Player.canceledClear()
			if autoplay and not autopack: return self._autoplay(library = library, new = new, add = add, binge = binge)

			if tools.Tools.isDictionary(source) and 'stream' in source and tools.Tools.isDictionary(source['stream']):
				stream = Stream()
				stream.dataImport(data = source['stream'], full = True)
				source['stream'] = stream

			self.downloadCanceled = False
			sequential = tools.Settings.getBoolean('playback.autoplay.sequential')
			if sequential:
				items = self.propertyItems()
				if index is None:
					for i in range(len(items)):
						if items[i]['stream'].linkPrimary() == source['stream'].linkPrimary():
							index = i
							break
				if not index is None: # Ignore for locally downloaded files (files played from the download manager while the sequential playback option is enabled).
					try:
						source = items[index]
					except:
						tools.Logger.error()
						self.progressClose(force = True)
						return

			labelInitiate = interface.Translation.string(33674)
			labelResolve = interface.Translation.string(35282)
			labelContainer = interface.Translation.string(35283)
			labelEstablish = interface.Translation.string(33452)
			labelRemote = interface.Translation.string(35537)

			heading = interface.Translation.string(33451)
			message = labelInitiate

			title = None
			year = None

			metadata = self._metadata(metadata = metadata, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)
			if metadata:
				title = metadata['tvshowtitle'] if 'tvshowtitle' in metadata else metadata['title']
				year = metadata['year'] if 'year' in metadata else None
				season = metadata['season'] if 'season' in metadata else None
				episode = metadata['episode'] if 'episode' in metadata else None
				imdb = metadata['imdb'] if 'imdb' in metadata else None
				tmdb = metadata['tmdb'] if 'tmdb' in metadata else None
				tvdb = metadata['tvdb'] if 'tvdb' in metadata else None
				trakt = metadata['trakt'] if 'trakt' in metadata else None

			self.progressPlaybackInitialize(title = heading, message = labelInitiate, metadata = metadata)
			self.progressPlaybackUpdate(progress = 1, title = heading, message = message)

			try:
				# Why do we copy here?
				# Deep copying here can result in the error:
				#	deepcopy(value, memo) RecursionError: maximum recursion depth exceeded
				# when there are duplicate links from the same provider resulting in source['provider']['data'] being the same object, and we do a fresh scrape (not retrieving from cache).
				# Happens especially when called from _autopack().
				# Setting "source['provider']['data'] = None" before copying solves the problem.
				item = source
				#item = tools.Tools.copy(source)

				if tools.Tools.isArray(item): item = item[0]
				item['stream'] = Stream.load(data = item['stream'])
				self.progressPlaybackUpdate(progress = 2, title = heading, message = message)

				if handle is None and not item['stream'].sourceTypeLocal():
					links = item['stream'].link()
					try: handle = handler.Handler().serviceDetermine(mode = handleMode, item = item, popups = True)
					except: handle = handler.Handler.ReturnUnavailable

					# Important for Incursion and Placenta providers that must be resolved first.
					if handle == handler.Handler.ReturnUnavailable:
						message = labelResolve
						self.progressPlaybackUpdate(progress = 5, title = heading, message = message)
						self.sourceResolveProvider(item = item)
						if not item['stream'].linkProvider() in links: # Only if a new link is resolved through the provider.
							self.progressPlaybackUpdate(progress = 8, title = heading, message = message)
							handle = handler.Handler().serviceDetermine(mode = handleMode, item = item, popups = True)

					if handle == handler.Handler.ReturnUnavailable:
						interface.Dialog.notification(title = 33448, message = 33203, icon = interface.Dialog.IconError)

					if handle == handler.Handler.ReturnUnavailable or handle == handler.Handler.ReturnExternal or handle == handler.Handler.ReturnCancel:
						self.progressPlaybackClose()
						self.loaderHide()
						return None

				try:
					if self.progressPlaybackCanceled():
						self.loaderHide()
						return None
				except: pass

				self.progressPlaybackUpdate(progress = 10, title = heading, message = message)
				self.tProcessed = False
				self.tResolved = None

				stream = item['stream']
				typeLocal = stream.sourceTypeLocal()
				typePremium = stream.sourceTypePremium()
				typeTorrent = stream.sourceTypeTorrent()
				typeUsenet = stream.sourceTypeUsenet()
				typeHoster = stream.sourceTypeHoster()

				# OffCloud cloud downloads require a download, even if it is a hoster. Only instant downloads on OffCloud do not need this.
				try: cloud = not typePremium and not typeTorrent and not typeUsenet and not debrid.offcloud.Core().instant() and handler.Handler(handler.Handler.TypeHoster).service(handle).id() == debrid.offcloud.Core().id()
				except: cloud = False

				# Torrents and usenet have a download dialog with their own thread. Do not start a thread for them here.
				if not typeLocal and (cloud or typeTorrent or typeUsenet):
					# Do not close the dialog, otherwise there is a period where no dialog is showing.
					# The progress dialog in the debrid downloader (through sourceResolve), will overwrite this.
					#progressDialog.close()

					self.tMessage = message
					def _resolve(item, handle):
						try:
							stream = item['stream']
							notify = False
							if typeHoster and stream.linkProvider():
								self.tProcessed = True
							else:
								# Download the container. This is also done by sourceResolve(), but download it here to show it to the user in the dialog, because it takes some time.
								download = typeTorrent or typeUsenet
								sourceObject = self.sourceProviderObject(stream = stream)
								if sourceObject:
									resolved = None

									# Generate a magnet link if the hash is available.
									# This allows users to stream eg cached YggTorrent links, even if they do not have an account and can therefore not download the .torrent file.
									# Also works if the YggTorrent domain is down, old torrent links are invalid, or Cloudflare prevents downloading the .torrent file.
									# This is useful if Orion returns YggTorrent links that are cached, but the user does not have a YggTorrent account.
									for link in stream.link(generate = True):
										self.tMessage = labelResolve
										resolved = sourceObject.resolve(link = link)
										if resolved:
											if download:
												container = network.Container(link = resolved, download = True)

												# First try the original link when calling resolve() for the first time.
												# This will use the original link (or the redirection link if applicbale).
												# If the download fails (eg: due to an old non-exisiting domain - eg: old links from Orion), try replacing the domain with the domain in the provider code and try again.
												if not container.isFile():
													resolved2 = sourceObject.resolve(link = link, renew = True)
													if not resolved == resolved2:
														resolved = resolved2
														container = network.Container(link = resolved, download = True)

												if (typeTorrent and not container.torrentIsMagnet()) or typeUsenet: self.tMessage = labelContainer
												if not container.isFile(): notify = True
												hash = container.hash(type = stream.sourceType()) # Pass in the type, otherwise the container will load/construct the providers to check to which provider the container belongs to.
												if hash: self.tProcessed = True
											else:
												self.tProcessed = True
											if self.tProcessed:
												stream.linkProviderSet(resolved, hoster = True)
												break
								elif stream.infoCustom():
									self.tProcessed = True
									stream.linkProviderSet(stream.linkPrimary())
							if not self.tProcessed and notify: interface.Dialog.notification(title = 35600, message = 35601, icon = interface.Dialog.IconError)
						except:
							tools.Logger.error()

					thread = Pool.thread(target = _resolve, args = (item, handle))
					thread.start()

					progress = 0
					while thread.is_alive():
						try:
							if tools.System.aborted():
								tools.System.exit()
								self.loaderHide()
								return None
							if self.progressPlaybackCanceled():
								self.progressPlaybackClose()
								return None
						except:
							self.loaderHide()

						progress += 0.25
						progressCurrent = 10 + min(int(progress), 25)
						self.progressPlaybackUpdate(progress = progressCurrent, title = heading, message = self.tMessage)
						tools.Time.sleep(0.5)

					if not self.tProcessed:
						self.progressPlaybackClose()
						return None

					message = labelRemote
					self.progressPlaybackUpdate(progress = 50, title = heading, message = message)
					self.tResolved = self.sourceResolve(item, info = True, handle = handle, handleMode = handleMode, handleClose = False, strict = strict)

					loader = True
					if 'loader' in self.tResolved and self.tResolved['loader']:
						loader = False
						interface.Loader.show()

					if handler.Handler.serviceExternal(handle) and self.tResolved['error'] == handler.Handler.ReturnExternal: # Do not return if there is a different error.
						stream.streamSet(self.tResolved)
						history.History().add(media = self.media, metadata = metadata, stream = stream)
						self.progressPlaybackUpdate(progress = 100, title = heading, message = message)
						self.progressPlaybackClose(loader = loader)
						return self.tResolved['link']
					if self.tResolved['link']:
						if not self.progressPlaybackCanceled():
							message = labelEstablish
							self.progressPlaybackUpdate(progress = 65, title = heading, message = message)
				else:
					def _resolve(item, handle):
						self.tResolved = self.sourceResolve(item, info = True, handle = handle, handleMode = handleMode, handleClose = False, strict = strict)

					message = labelResolve
					thread = Pool.thread(target = _resolve, args = (item, handle))
					thread.start()

					end = 3600
					for x in range(end):
						try:
							if tools.System.aborted():
								tools.System.exit()
								self.loaderHide()
								return None
							if self.progressPlaybackCanceled():
								self.progressPlaybackClose()
								return None
						except:
							self.loaderHide()

						if not interface.Dialog.dialogId() in [interface.Dialog.IdDialogKeyboard, interface.Dialog.IdDialogYesNo]:
							break

						progress = 10 + int((x / float(end)) * 20)
						self.progressPlaybackUpdate(progress = progress, title = heading, message = message)

						tools.Time.sleep(0.5)

					if not self.progressPlaybackCanceled():
						end = 30
						for x in range(end):
							try:
								if tools.System.aborted():
									tools.System.exit()
									self.loaderHide()
									return None
								if self.progressPlaybackCanceled():
									self.progressPlaybackClose()
									return None
							except:
								self.loaderHide()

							if not thread.is_alive(): break

							progress = 30 + int((x / float(end)) * 25)
							self.progressPlaybackUpdate(progress = progress, title = heading, message = message)

							tools.Time.sleep(0.5)

						# For pairing dialogs to remain open.
						# Have it in two steps to have a smoother progress, instead of a very long single timeout.
						if not self.progressPlaybackCanceled() and thread.is_alive():
							end = 3600
							for x in range(end):
								try:
									if tools.System.aborted():
										tools.System.exit()
										self.loaderHide()
										return None
									if self.progressPlaybackCanceled():
										self.progressPlaybackClose()
										return None
								except:
									self.loaderHide()

								if not thread.is_alive(): break

								progress = 60
								self.progressPlaybackUpdate(progress = progress, title = heading, message = message)

								tools.Time.sleep(0.5)

				loader = True
				if 'loader' in self.tResolved and self.tResolved['loader']:
					loader = False
					interface.Loader.show()

				# Close download dialog if opened.
				if self.navigationPlaybackSpecial:
					interface.Core.close()

				if self.progressPlaybackCanceled():
					self.progressPlaybackClose(loader = loader)
					return None
				elif handler.Handler.serviceExternal(handle) and self.tResolved['error'] == handler.Handler.ReturnExternal: # Do not return if there is a different error.
					stream.streamSet(self.tResolved)
					history.History().add(media = self.media, metadata = metadata, stream = stream)
					self.progressPlaybackUpdate(progress = 100, title = heading, message = message)
					self.progressPlaybackClose(loader = loader)
					return self.tResolved['link']
				else:
					self.progressPlaybackUpdate(progress = 70, title = heading, message = message)

				if not self.tResolved['success']:
					if sequential:
						return self.play(source = source, metadata = metadata, downloadType = downloadType, downloadId = downloadId, handle = handle, handleMode = handleMode, index = index + 1, binge = binge)
					else:
						self.progressPlaybackClose(loader = loader)
						return None

				stream.streamSet(self.tResolved)
				history.History().add(media = self.media, metadata = metadata, stream = stream)

				tools.Time.sleep(0.2)
				interface.Dialog.close(id = interface.Dialog.IdDialogKeyboard)
				interface.Dialog.close(id = interface.Dialog.IdDialogYesNo)

				# If the background dialog is not closed, when another background dialog is launched, it will contain the old information from the previous dialog.
				# Manually close it. Do not close the foreground dialog, since it does not have the issue and keeping the dialog shown is smoother transition.
				# NB: This seems to not be neccessary with the new interface.Core. However, enable again if the problems are observed.
				#if interface.Core.background():
				#	interface.Core.close()
				#	self.loaderShow() # Since there is no dialog anymore.

				tools.Sound.executeStreamFinish()
				from lib.modules.player import Player
				Player.instance(reinitialize = True).run(media = self.media, title = title, year = year, season = season, episode = episode, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, metadata = metadata, downloadType = downloadType, downloadId = downloadId, source = item, binge = binge, reload = reload, resume = resume, autoplay = self.autoplay, handle = self.tResolved['handle'] if 'handle' in self.tResolved else None, service = self.tResolved['service'] if 'service' in self.tResolved else None)

				return self.tResolved['link']
			except:
				tools.Logger.error()
				self.loaderHide()

			self.progressPlaybackClose()
			self.progressFailure(single = True)
			return True
		except:
			tools.Logger.error()
			self.progressPlaybackClose()
			return False

	def playCache(self, source, metadata = None, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, handleMode = None, binge = None, reload = True):
		try:
			if tools.Settings.getBoolean('download.cache.enabled'):
				self.loaderShow()

				metadata = self._metadata(metadata = metadata, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

				item = tools.Tools.copy(source)
				if tools.Tools.isArray(item): item = item[0]
				item['stream'] = Stream.load(data = item['stream'])

				handle = handler.Handler().serviceDetermine(mode = handleMode, item = item, popups = True)
				if handle == handler.Handler.ReturnUnavailable or handle == handler.Handler.ReturnExternal or handle == handler.Handler.ReturnCancel:
					self.loaderHide()
					return None

				result = self.sourceResolve(item, handle = handle, handleMode = handleMode, handleClose = False) # Do not use item['urlresolved'], because it has the | HTTP header part removed, which is needed by the downloader.

				# If the Premiumize download is still running and the user clicks cancel in the dialog.
				if not result['success']: return

				link = result['link']
				item['stream'].streamSet(result)

				if item['stream'].sourceTypeLocal(): # Must be after self.sourceResolve.
					self.play(source = item, metadata = metadata, handle = handle, binge = binge)
					return

				downloadType = None
				downloadId = None
				if not link is None and not link == '':
					from lib.modules import downloader
					downer = downloader.Downloader(downloader.Downloader.TypeCache)
					path = downer.download(media = self.media, link = link, metadata = metadata, source = tools.Converter.jsonTo(item), automatic = True)
					if path and not path == '':
						downloadType = downer.type()
						downloadId = downer.id()

						tools.Time.sleep(3) # Allow a few seconds for the download to start. Otherwise the download was queued but not started and the file was not created yet.
						downer.refresh()

				self.loaderHide()
				self.playLocal(path = path, source = item, metadata = metadata, downloadType = downloadType, downloadId = downloadId, binge = binge, reload = reload)
			else:
				self.play(source = item, metadata = metadata, binge = binge, reload = reload)
		except:
			self.loaderHide()
			tools.Logger.error()

	# Used by downloader.
	def playLocal(self, path, source, metadata = None, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, downloadType = None, downloadId = None, binge = None, reload = True):
		source['stream'] = Stream.load(data = source['stream'])
		source['stream'].linkSet(path)
		source['stream'].streamLinkSet(path)
		source['stream'].sourceTypeSet(Stream.SourceTypeLocal)
		self.play(source = source, metadata = metadata, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, downloadType = downloadType, downloadId = downloadId, binge = binge, reload = reload)

	def addSources(self, sources, check):
		# Do not stop this, otherwise the stats in the window do not update once the providers are finished.
		# Especially when cached streams are retrieved, the providers might be done before the window can be fully updated.
		#if self.stopThreads: return

		try:
			if len(sources) > 0:
				self.sources.extend(sources)
				services = self.servicesDebrid()

				for source in sources:
					try:
						source['stream'] = Stream.load(data = source['stream'])

						lookups = [source['stream'].sourceHoster(), source['stream'].sourceProvider(), source['stream'].sourcePublisher()]
						lookups = [lookup.lower() for lookup in lookups if lookup]

						# External providers do not always set the full hoster domain (eg: vidoza instead of vidoza.net).
						# Do not just check if the domain contains the hoster, since this would match eg: "cloud" and "icloud".
						# Instead check if the domain starts with the hoster and followed by a ".".
						lookups2 = [lookup + '.' for lookup in lookups if not '.' in lookup]

						lookups.insert(0, source['stream'].sourceType())

						# Add debrid.
						debrid = False
						for key, value in services.items():
							if value: # In case the service list request failed, returning None.
								for val in value:
									if any(k == val for k in lookups) or ('.' in val and any(val.startswith(k) for k in lookups2)) or key in lookups:
										source['stream'].accessDebridSet(id = key)
										debrid = True
										break

						# Clear the termination status, since it could change after various parameters were set after the scraper returned it (debrid, provider, etc).
						source['stream'].infoTerminationClear()

						# Ignore duplicates if retrieving cached streams, otherwise the stats in the scraping window are incomplete when reloading cached streams.
						# The duplication is checked and set again in adjustSourceAppend() below.
						if not check: source['stream'].exclusionDuplicateSet(value = False)

						source['time'] = tools.Time.timestamp() # Used for cache lookup.
						self.adjustSourceAppend(source)

						priority = False
						if(
							not(self.excludeDuplicate and source['stream'].exclusionDuplicate())
							and not(self.excludeKeyword and source['stream'].exclusionKeyword())
							and not(self.excludeMetadata and source['stream'].exclusionMetadata())
							and not(self.excludeFormat and source['stream'].exclusionFormat())
							and not(self.excludeFake and source['stream'].exclusionFake())
							and not(self.excludeSupport and source['stream'].exclusionSupport())
							and not(self.excludePrecheck and source['stream'].exclusionPrecheck())
							and not(self.excludeCaptcha and source['stream'].exclusionCaptcha())
							and not(self.excludeBlocked and source['stream'].exclusionBlocked())
						):
							if debrid: self.streamsDebrid += 1

							# When loading from cache.
							if source['stream'].accessCacheAny(account = True): self.streamsCached += 1

							quality = source['stream'].videoQualityCategory()
							if quality == Stream.VideoQualityHdUltra:
								priority = True
								self.streamsHdUltra += 1 # 4K or higher
							elif quality == Stream.VideoQualitySd:
								self.streamsSd += 1
							elif quality == Stream.VideoQualityScr or quality == Stream.VideoQualityCam:
								self.streamsLd += 1
							else:
								quality = source['stream'].videoQuality()
								if quality == Stream.VideoQualityHd1080:
									priority = True
									self.streamsHd1080 += 1
								elif quality == Stream.VideoQualityHd720:
									priority = True
									self.streamsHd720 += 1

							if source['stream'].sourceTypeTorrent(): self.streamsTorrent += 1
							elif source['stream'].sourceTypeUsenet(): self.streamsUsenet += 1
							elif source['stream'].sourceTypeHoster(): self.streamsHoster += 1
							elif source['stream'].sourceTypePremium(): self.streamsPremium += 1
							elif source['stream'].sourceTypeLocal(): self.streamsLocal += 1

							if source['stream'].accessTypeDirect() and not source['stream'].sourceTypePremium(): self.streamsDirect += 1

							self.streamsTotal += 1

						if check and self.enabledExtra and not source['stream'].exclusionDuplicate():
							# Do not create a thread here. Only create it if we execute it.
							index = len(self.tasksAdjusted)
							self.tasksAdjusted.append({'target' : self.adjustSource, 'args' : (source, index), 'priority' : priority, 'status' : 'queued'}) # Give priority to HD links
						else:
							self.cacheCount += 1
					except:
						tools.Logger.error()

				self.adjustSourceStart()
				self.adjustTermination()
				Pool.thread(target = self.adjustSourceCache, args = (None, True), start = True)
		except:
			tools.Logger.error()

	def adjustLock(self):
		# NB: For some reason Python somtimes throws an exception saying that a unlocked/locked lock (tried) to aquire/release. Always keep these statements in a try-catch.
		try: self.threadsLock.acquire()
		except: pass

	def adjustUnlock(self):
		# NB: For some reason Python somtimes throws an exception saying that a unlocked/locked lock (tried) to aquire/release. Always keep these statements in a try-catch.
		try: self.threadsLock.release()
		except: pass

	def adjustTerminationLock(self):
		try: self.terminationLock.acquire()
		except: pass

	def adjustTerminationUnlock(self):
		try: self.terminationLock.release()
		except: pass

	def adjustTermination(self):
		try:
			self.adjustTerminationLock()
			if self.terminationEnabled and not self.terminated:
				if self.termination.process(items = self.sourcesAdjusted):
					self.terminated = True
					if self.termination.notification(): interface.Dialog.notification(title = 33882, message = 35638, icon = interface.Dialog.IconInformation)
					tools.Logger.log('Preemptive Termination Triggered', name = 'CORE', type = tools.Logger.TypeInfo)
		except:
			tools.Logger.error()
		finally:
			try: self.adjustTerminationUnlock()
			except: pass
		return self.terminated

	def adjustSourceExclusion(self, duplicate = True):
		self.sourcesAdjusted = self.filters.exclude(items = self.sourcesAdjusted, duplicate = duplicate)

	def adjustSourceCache(self, timeout = None, partial = False):
		# Premiumize seems to take long to verify usenet hashes.
		# Split torrents and usenet up, with the hope that torrents will complete, even when usenet takes very long.
		# Can also be due to expensive local hash calculation for NZBs.
		if self.cacheEnabled:
			if partial and self.cacheBusy: return # If it is the final full inspection, always execute, even if another partial inspection is still busy.

			self.adjustLock()
			self.cacheBusy += 1

			if timeout is None:
				timeout = self.cacheTime
				if not timeout: timeout = 45

			if self.cacheOrion:
				links = []
				for source in self.sourcesAdjusted:
					if not source['stream'].hashContainer() and (source['stream'].sourceTypeTorrent() or source['stream'].sourceTypeUsenet()):
						# NB: Only do this on a new scrape, not on reloading previously cached streams.
						# Otherwise, if there are some links for which Orion does not have a hash, every time we reload the stream window, identifiers will be checked again on Orion, only for nothing to be returned.
						# If on a new scrape no hahes are returned from Orion, do not check again when retrieving links from providers.db cache.
						# Checking infoIdentifier() also prevents links from being checked multiple times during the same scrape if Orion did not return as hash the previous time this function was called.
						# Also do not check if the link comes from  Orion. Since if Orion did not return a hash together with the link, checking through this function will also not return anything.
						if not source['stream'].infoIdentifier() and not source['stream'].accessTypeOrion():
							source['stream'].infoIdentifierSet()
							links.append(source['stream'].linkPrimary())
				if links:
					identifiers = self.cacheOrion.identifiers(links = links, chunked = partial)
					for link, identifier in identifiers.items():
						for i in range(len(self.sourcesAdjusted)):
							if self.sourcesAdjusted[i]['stream'].linkPrimary() == link:
								if not identifier is None:
									self.sourcesAdjusted[i]['stream'].hashContainerSet(identifier['hash'])
									self.sourcesAdjusted[i]['stream'].segmentSet(identifier['segment'])
								break

			self.cacheLookup = False
			before = len(self.sourcesAdjusted)
			threads = []
			for i in range(len(self.cacheTypes)):
				threads.append(Pool.thread(target = self._adjustSourceCache, args = (self.cacheObjects[i], self.cacheTypes[i], timeout, partial)))

			self.adjustUnlock()

			[thread.start() for thread in threads]
			[thread.join() for thread in threads]

			self.adjustLock()
			self.cacheBusy -= 1
			self.adjustUnlock()
			self.adjustTermination()

			# Start another lookup if the previous one was successful, in order not to waste time until a new stream comes in to trigger this.
			if partial and not self.cacheBusy and self.cacheLookup and len(self.sourcesAdjusted) > before:
				Pool.thread(target = self.adjustSourceCache, args = (None, True), start = True)

	def _adjustSourceCache(self, object, type, timeout, partial = False):
		try:
			debridId = object.id()
			self.adjustLock()
			times = []
			hashes = []
			sources = []

			modes = object.cachedModes()
			modeHash = handler.Handler.TypeTorrent in modes or handler.Handler.TypeUsenet in modes
			modeLink = handler.Handler.TypeHoster in modes
			for source in self.sourcesAdjusted:
				if not source['stream'].exclusionDuplicate():
					if (source['stream'].sourceType() in type or (modeLink and handler.Handler.TypeHoster in type)) and (not 'premium' in source or not source['premium']):
						# Only check those that were not previously inspected.
						if not source['stream'].accessCacheHas(debridId, exact = Stream.ExactYes, time = self.cacheSave):
							# NB: Do not calculate the hash if it is not available.
							# The hash is not available because the NZB could not be downloaded, or is still busy in the thread.
							# Calling container.hash() will cause the NZB to download again, which causes long delays.
							# Since the hashes are accumlated here sequentially, it might cause the download to take so long that the actual debrid cache query has never time to execute.
							# If the NZBs' hashes are not available at this stage, ignore it.
							'''if not source['stream'].hashContainer():
								container = network.Container(link = source['stream'].linkPrimary())
								source['stream'].hashContainerSet(container.hash(type = source['stream'].sourceType())) # Pass in the type, otherwise the container will load/construct the providers to check to which provider the container belongs to.
							'''

							added = False
							torrentOrUsenet = source['stream'].sourceTypeTorrent() or source['stream'].sourceTypeUsenet()
							hash = source['stream'].hashContainer()
							if torrentOrUsenet and modeHash and hash:
								added = True
								times.append(source['time'])
								hashes.append(hash)
								sources.append(source)
							elif not torrentOrUsenet and modeLink:
								link = source['stream'].linkPrimary()
								if link:
									added = True
									times.append(source['time'])
									hashes.append(link)
									sources.append(source)

							# Make sure the new cache status is written to the database and overwrites the old cache status and cache time values.
							# NB: Only do this if the stream was added to the cache lookup queue.
							# Otherwise, NZBs coming from Orion might not have a hash.
							# Without checking "added", these NZB streams will set their cache to expired.
							# If the stream window is reloaded (with streams already cached in providers.db), these links will be written to the database again in adjustSourceDatabase(), since "stream.infoCache(expired = False)" will be false.
							# This in turn will make all the old cached Orion streams in providers.db be overwritten with these few failed NZB links.
							# To replicate this problem:
							#	1. Scrape an episode where NZB links (that do not have a hash) are retrieved from Orion.
							#	2. Make sure that the same Gaia NZB provider is also enabled and scrapes the same link.
							#	3. Orion links will correctly show  in the stream window.
							#	4. Back out and scrape the episoode again. Not rescrape, just retrieve the previously cached links.
							#	5. The Orion links will still show at this point. However, a few NZB links will overwrite ALL the Orion links in providers.db.
							#	6. Back out and scrape the episoode again. Now only/mostly Gaia links are shown, since most of the Orion links in providers.db were replaced in the previous step.
							if added and source['stream'].accessCacheExpired(debridId, time = self.cacheSave): source['stream'].infoCacheExpire()

			self.adjustUnlock()

			# Partial will inspect the cache will the scraping is still busy.
			# Only check if there are a bunch of them, otherwise there are too many API calls (heavy load on both server and local machine).
			# Also check smaller chunks if the streams were added a while back (30 secs):
			#	1. If there are only a few streams (eg 10) available for the title, this threshold is never reached, and cache lookup is only done at the end of the scrape process.
			#	2. There are many streams. Currently there are 10 streams left for checkup, but the last provider is stuck (eg domain unreachable). Do not wait eg 1 minute for the provider to finish. While waiting, we can already look up.
			if not hashes: return
			if partial and len(hashes) < 40 and (tools.Time.timestamp() - min(times) < 30): return

			self.cacheLookup = True
			time = tools.Time.timestamp()

			# NB: Set all statuses to false, otherwise the same links will be send multiple times for inspection, if multiple hosters finish in a short period of time before the previous inspection is done.
			# This will exclude all currently-being-looked-up links from the next iteration in the for-loop above.
			for i in range(len(self.sourcesAdjusted)):
				hash = self.sourcesAdjusted[i]['stream'].hashContainer()
				if (modeHash and hash and hash in hashes) or (modeLink and self.sourcesAdjusted[i]['stream'].linkPrimary() in hashes):
					self.sourcesAdjusted[i]['stream'].accessCacheSet(id = debridId, value = False, time = time, exact = Stream.ExactYes)
					self.sourcesAdjusted[i]['stream'].infoTerminationClear() # Clear the termination status, since it could change after the cache changed.
			self.adjustUnlock()

			def _updateIndividually(id, hash, cached):
				try:
					hash = tools.Converter.unicode(hash)
					hashLower = hash.lower()
					self.adjustLock()
					for i in range(len(self.sourcesAdjusted)):
						try:
							if self.sourcesAdjusted[i]['stream'].hashContainer() == hashLower or self.sourcesAdjusted[i]['stream'].linkPrimary() == hash:
								if cached and not self.sourcesAdjusted[i]['stream'].accessCache(id, exact = Stream.ExactYes):
									self.sourcesAdjusted[i]['stream'].accessCacheSet(id = id, value = cached, time = time, exact = Stream.ExactYes)
									self.sourcesAdjusted[i]['stream'].infoTerminationClear() # Clear the termination status, since it could change after the cache changed.
									if cached and self.sourcesAdjusted[i]['stream'].accessCacheCount(account = True) == 1: # Only count one of the debird service caches.
										self.streamsCached += 1
								break
						except: tools.Logger.error()
					self.adjustUnlock()
				except: tools.Logger.error()

			object.cached(id = hashes, timeout = timeout, callback = _updateIndividually, sources = sources)
		except: tools.Logger.error()
		finally: self.adjustUnlock()

	# Priority starts stream checks HD720 and greater first.
	def adjustSourceStart(self, priority = True, full = False):
		# NB: Do not return here if stopped, otherwise the "Finalizing Stream Collection" will get stuck.
		# Otherwise a bunch of streams will remain in "queued" status, because this function does not get executed.
		# This sometimes happens during normal scraping, but is very prominent during preemptive termination (which sets self.stopThreads).
		#if self.stopThreads: return

		# NB: Do not add the threads to a list member variable.
		# Otherwise the thread object stays in memory until the full scrape has finished and the garbage collector removes them, since the list still keeps a reference to the object, preventing it from being deleted earlier.
		# When not storing the thread object, it gets deleted the momement the thread is done.
		# This can save quite a lot of threads, reducing the chances of system threads being used up on low-end devices.

		try:
			synchronizer = self.synchronizerAdjusted[full]

			# HD links
			for task in self.tasksAdjusted:
				if task['priority'] is True and task['status'] == 'queued':
					task['status'] = 'busy'
					Pool.thread(target = task['target'], args = task['args'], start = True, synchronizer = synchronizer)

			# Non-HD links
			for task in self.tasksAdjusted:
				if task['status'] == 'queued':
					task['status'] = 'busy'
					Pool.thread(target = task['target'], args = task['args'], start = True, synchronizer = synchronizer)

		except: tools.Logger.error()

	def adjustSourceAppend(self, source):
		#if self.stopThreads: return # Do not stop here, otherwise the stats in the window are not fully updated when cached streams are retrieved from the database.
		try:
			self.adjustSourceContains(source)
			self.sourcesAdjusted.append(source)
		except: tools.Loggere.error()

	def adjustSourceContains(self, source): # Filter out duplicate URLs early on, to reduce the prechecks & metadata on them.
		#if self.stopThreads: return # Do not stop here, otherwise the stats in the window are not fully updated when cached streams are retrieved from the database.
		contains = False
		try:
			debrids = [debrid.premiumize.Core().id(), debrid.offcloud.Core().id(), debrid.realdebrid.Core().id()]
			for i in range(len(self.sourcesAdjusted)):
				sourceAdjusted = self.sourcesAdjusted[i]
				sourceLink = sourceAdjusted['stream'].link()
				sourceHash = sourceAdjusted['stream'].hash()
				if any(link in sourceLink for link in source['stream'].link()) or (sourceHash and sourceHash == source['stream'].hash()):
					source['stream'].exclusionDuplicateSet()

					# NB: Compare both debrid caches.
					# If there are different providers and/or different variations of the provider (for different foreign languages or umlauts), the same item might be detected by multiple providers.
					# This is especially important for debrid cached links. One provider might have it flagged as cache, the other one not. Then on the second run of the scraping procees, the values are read from database, and which ever one was written first to the DB will be returned.
					# Later pick the longest dict, since that one is expected to contains most metadata/info.

					# If any one is cached, make both cached.
					for exact in [Stream.ExactYes, Stream.ExactNo]:
						for id in debrids:
							cache = sourceAdjusted['stream'].accessCache(id = id, exact = exact)
							cacheNew = source['stream'].accessCache(id = id, exact = exact)
							if cache is None: cache = cacheNew
							elif not cacheNew is None: cache = cache or cacheNew
							if not cache is None:
								time = sourceAdjusted['stream'].accessCache(id = id, exact = Stream.ExactTime)
								sourceAdjusted['stream'].accessCacheSet(id = id, value = cache, time = time, exact = exact)
								source['stream'].accessCacheSet(id = id, value = cache, time = time, exact = exact)
								source['stream'].infoTerminationClear() # Clear the termination status, since it could change after the cache changed.

					contains = True
					break
		except:
			tools.Logger.error()
		return contains

	def adjustSourceUpdate(self, index, stream = None, precheck = None, resolved = None, hash = None):
		if self.stopThreads: return
		try:
			if index >= 0:
				if not stream is None: self.sourcesAdjusted[index]['stream'] = stream
				if not precheck is None: self.sourcesAdjusted[index]['stream'].exclusionPrecheckSet(precheck)
				if not resolved is None: self.sourcesAdjusted[index]['stream'].linkProviderSet(resolved)
				if not hash is None: self.sourcesAdjusted[index]['stream'].hashContainerSet(hash)
		except: pass

	# Write changes to database.
	def adjustSourceDatabase(self, timeout = 30):
		try:
			sources = {}
			items = self.sourcesAdjusted # In case self.sourcesAdjusted is reset to [] before this function finishes.
			for i in range(len(items)):
				try:
					result = items[i]
					stream = result['stream']

					# Make sure not to skip the stream if the cache status was newley looked up.
					# Otherwise, if the cache status expired and we do a fresh cache lookup, the new cache status is not written to the database.
					# That means, reloading the streams a few seconds appart will always cause a new cache lookup, since the cache lookup time of the stream is still the original/first lookup, instead of the new lookup a few seconds ago.
					if stream.infoCache(expired = False): continue

					provider = stream.provider()
					imdb = stream.idImdb()
					tmdb = stream.idTmdb()
					tvdb = stream.idTvdb()
					trakt = stream.idTrakt()
					query = stream.infoQuerySearch()

					id = [provider.id(), imdb, tmdb, tvdb, trakt, query]
					id = [x if x else ' ' for x in id]
					id = '_'.join(id)

					if not id in sources:
						sources[id] = {
							'provider' : provider,
							'query' : query,
							'imdb' : imdb,
							'tmdb' : tmdb,
							'tvdb' : tvdb,
							'trakt' : trakt,
							'season' : stream.metaSeason(),
							'episode' : stream.metaEpisode(),
							'streams' : [],
						}

					sources[id]['streams'].append(stream)
				except: tools.Logger.error()

			try:
				for source in sources.values():
					ProviderManager.streamsInsert(data = source['streams'], provider = source['provider'], query = source['query'], idImdb = source['imdb'], idTmdb = source['tmdb'], idTvdb = source['tvdb'], idTrakt = source['trakt'], numberSeason = source['season'], numberEpisode = source['episode'])
			except: tools.Logger.error()

		except: tools.Logger.error()

	def adjustSourceDone(self, index):
		try:
			if index >= 0 and index < len(self.tasksAdjusted):
				self.tasksAdjusted[index]['status'] = 'done'
		except: tools.Logger.error()

	def adjustSource(self, source, index):
		if self.stopThreads:
			self.adjustSourceDone(index = index)
			return None
		try:
			if not source['stream'].exclusionDuplicate():
				link = source['stream'].linkPrimary()
				local = source['stream'].sourceTypeLocal()
				special = source['stream'].sourceTypeTorrent() or source['stream'].sourceTypeUsenet()
				status = network.Networker.StatusUnknown

				# Resolve Link
				if not special and (self.precheckLink or self.precheckMetadata):
					if not source['stream'].linkProvider():
						resolved = network.Resolver.resolve(source = source, clean = True)
						if resolved:
							self.adjustSourceUpdate(index, resolved = link)
							link = resolved

				# Debrid Cache
				# Do before precheck and metadata, because it is a lot faster and more important. So execute first.
				if special and self.cacheEnabled and not source['stream'].hashContainer():
					# Do not automatically get the hash, since this will have to download the torrent/NZB files.
					# Sometimes more than 150 MB of torrents/NZBs can be downloaded on one go, wasting bandwidth and slowing down the addon/Kodi.
					download = False
					if source['stream'].sourceTypeTorrent(): download = self.preloadEnabledTorrent
					elif source['stream'].sourceTypeUsenet(): download = self.preloadEnabledUsenet

					container = network.Container(link = link, download = download)

					# Pass in the type, otherwise the container will load the providers to check to which provider the container belongs to.
					# This in turn calls the provider constructor for each of the lookups.
					# So Usenet links, or torrent tiles (without a hash) will instantiate the corresponding provider for each link found, which uses unnecessary processing power.
					hash = container.hash(type = source['stream'].sourceType())

					if not hash is None: self.adjustSourceUpdate(index, hash = hash)

				# Precheck
				if not special and self.precheckLink:
					if local: status = network.Networker.StatusOnline
					else: status = network.Networker().requestStatus(link = link, timeout = self.precheckLinkTime)
					self.adjustSourceUpdate(index, precheck = status)

				# Metadata
				if not special and self.precheckMetadata:
					if index < 0: return None # Already in list.
					if 'stream' in source: stream = source['stream']
					else: stream = Stream()
					if not local: stream.loadHeaders(link = link, timeout = self.precheckMetadataTime, force = False)
					self.adjustSourceUpdate(index, stream = stream)
		except:
			tools.Logger.error()

		self.adjustSourceDone(index)
		return source

	def sourcesFilter(self, items, metadata, autoplay = False, apply = True):
		try:
			filters = Filters.instance(mode = Filters.ModeNone if autoplay else Filters.ModeManual)
			self.filter, items = filters.process(items = items, filter = apply, exclude = apply)
		except: tools.Logger.error()
		return items

	def sourcesPrepare(self, items):
		try:
			# Create Metadata
			# Important update = true, because otherwise the debrid cache status is not always shown in the history window (shows as debrid instead of cached)
			if items:
				for i in range(len(items)):
					items[i]['stream'] = Stream.load(data = items[i]['stream'])
		except:
			tools.Logger.error()
		return items

	def sourcesLabel(self, items, metadata):
		try:
			if not self.navigationStreamsSpecial:
				prefix = '[GAIANUMBER][GAIAEXTRA]'
				unknown = interface.Format.fontItalic(35248)
				separator = Stream.labelSeparator()
				format = Stream.settingsFormat()
				padding = tools.Settings.getInteger('interface.stream.interface.padding') # Try with Confluence. 3 and 3.5 is not enough. 4 by default.

				layout = tools.Settings.getInteger('interface.stream.interface.layout')
				layoutSingle = layout == 0
				layoutMultiple = layout == 1

				layoutName = tools.Settings.getInteger('interface.stream.interface.name')
				layoutNameExclusiveFront = layoutName == 1
				layoutNameExclusiveBack = layoutName == 2
				layoutNamePrependFront = layoutName == 3
				layoutNameAppendFront = layoutName == 4
				layoutNamePrependBack = layoutName == 5
				layoutNameAppendBack = layoutName == 6

				for i in range(len(items)):
					stream = items[i]['stream']

					labelTop = ''
					labelBottom = ''
					spaceTop = ''
					spaceBottom = ''

					if layoutSingle:
						if layoutNameExclusiveFront:
							name = stream.fileName()
							if not name: name = unknown
							labelTop = [name, stream.labelSingle(format = format)]
						elif layoutNameExclusiveBack:
							name = stream.fileName()
							if not name: name = unknown
							labelTop = [stream.labelSingle(format = format), name]
						elif layoutNamePrependFront:
							labelTop = [stream.fileName(), stream.labelTop(format = format), stream.labelBottom(format = format)]
						elif layoutNameAppendFront:
							labelTop = [stream.labelTop(format = format), stream.fileName(), stream.labelBottom(format = format)]
						elif layoutNamePrependBack:
							labelTop = [stream.labelTop(format = format), stream.fileName(), stream.labelBottom(format = format)]
						elif layoutNameAppendBack:
							labelTop = [stream.labelTop(format = format), stream.labelBottom(format = format), stream.fileName()]
						else:
							labelTop = stream.labelSingle(format = format)

						if tools.Tools.isArray(labelTop): labelTop = separator.join([x for x in labelTop if x])
					elif layoutMultiple:
						if layoutNameExclusiveFront:
							labelBottom = stream.labelSingle(format = format)
							labelTop = stream.fileName()
							if not labelTop: labelTop = unknown
						elif layoutNameExclusiveBack:
							labelTop = stream.labelSingle(format = format)
							labelBottom = stream.fileName()
							if not labelBottom: labelBottom = unknown
						elif layoutNamePrependFront:
							labelTop = [stream.fileName(), stream.labelTop(format = format)]
						elif layoutNameAppendFront:
							labelTop = [stream.labelTop(format = format), stream.fileName()]
						elif layoutNamePrependBack:
							labelBottom = [stream.fileName(), stream.labelBottom(format = format)]
						elif layoutNameAppendBack:
							labelBottom = [stream.labelBottom(format = format), stream.fileName()]
						else:
							labelBottom = stream.labelTop(format = format)
							labelTop = stream.labelBottom(format = format)

						if tools.Tools.isArray(labelTop): labelTop = separator.join([x for x in labelTop if x])
						if tools.Tools.isArray(labelBottom): labelBottom = separator.join([x for x in labelBottom if x])

						if padding > 0:
							# Spaces needed, otherwise the second line is cut off when shorter than the first line
							spaceTop = 0
							spaceBottom = 0
							if not labelTop: labelTop = ''
							if not labelBottom: labelBottom = ''
							lengthTop = len(re.sub('\\[(.*?)\\]', '', labelTop))
							lengthBottom = len(re.sub('\\[(.*?)\\]', '', labelBottom))
							if lengthBottom > lengthTop: spaceTop = int((lengthBottom - lengthTop) * padding)
							else: spaceBottom = int((lengthBottom - lengthTop) * padding)
							spaceTop = ' ' * max(8, spaceTop)
							spaceBottom = ' ' * max(8, spaceBottom)

					labels = []
					if labelTop:
						labelTop = prefix + labelTop + spaceTop
						labels.append(labelTop)
					if labelBottom:
						labelBottom += spaceBottom
						labels.append(labelBottom)

					items[i]['label'] = labels
		except:
			tools.Logger.error()
		return items

	def sourceCloud(self, item):
		result = self.sourceResolve(item = item, info = True, handleMode = handler.Handler.ModeSelection, cloud = True)
		if result['success']: interface.Dialog.notification(title = 33229, message = 33230, icon = interface.Dialog.IconSuccess)

	def sourceResult(self, error = None, id = None, link = None, local = False, loader = False):
		if error is None and not local:
			if not network.Networker.linkIs(link):
				error = 'unknown'
		return {
			'success' : (error is None),
			'error' : error,
			'id' : id,
			'link' : link,
			'loader' : loader,
		}

	def sourceExternal(self, stream):
		lookups = [stream.sourceHoster(), stream.sourcePublisher(), stream.sourceProvider()]
		if not stream.idOrionHas(): lookups.extend([stream.providerId(), stream.providerName()])
		lookups = [lookup.lower() for lookup in lookups if lookup]
		tools.Tools.listUnique(lookups)
		services = self.servicesExternal()
		for lookup in lookups:
			try: return services[lookup]
			except: pass
		return None

	def sourceProviderObject(self, stream):
		object = stream.providerObject()
		if not object or (stream.idOrionHas() and stream.sourceHoster()):
			object2 = self.sourceExternal(stream = stream) # If the stream comes from Orion, lookup the actual external provider.
			if object2: object = object2
		return object

	def sourceResolveProvider(self, item, force = False):
		if not force and item['stream'].linkProvider():
			return item['stream'].linkProvider()
		else:
			sourceObject = self.sourceProviderObject(stream = item['stream'])
			if sourceObject:
				download = item['stream'].sourceTypeTorrent() or item['stream'].sourceTypeUsenet()
				resolved = None
				for link in item['stream'].link(generate = True):
					resolved = sourceObject.resolve(link)
					if resolved:
						success = False
						if download:
							container = network.Container(link = resolved, download = True)

							# First try the original link when calling resolve() for the first time.
							# This will use the original link (or the redirection link if applicbale).
							# If the download fails (eg: due to an old non-exisiting domain - eg: old links from Orion), try replacing the domain with the domain in the provider code and try again.
							if not container.isFile():
								resolved2 = sourceObject.resolve(link = link, renew = True)
								if not resolved == resolved2:
									resolved = resolved2
									container = network.Container(link = resolved, download = True)

							hash = container.hash(type = item['stream'].sourceType()) # Pass in the type, otherwise the container will load/construct the providers to check to which provider the container belongs to.
							if hash: success = True
						else:
							success = True

						if success:
							item['stream'].linkProviderSet(resolved, hoster = True)
							return resolved
			elif item['stream'].infoCustom():
				resolved = item['stream'].linkPrimary()
				item['stream'].linkProviderSet(resolved)
				return resolved
		return None

	def sourceResolve(self, item, info = False, internal = False, download = False, handle = None, handleMode = None, handleClose = True, resolve = network.Resolver.ModeService, cloud = False, strict = False):
		try:
			error = None
			loader = False
			self.downloadCanceled = False
			log = True

			item['stream'] = Stream.load(data = item['stream'])
			url = self.sourceResolveProvider(item = item)

			if item['stream'].videoRangeDolby():
				if not tools.Settings.getBoolean('internal.dolbyvision'):
					hdr = item['stream'].videoRange(label = Stream.LabelShort)
					message = interface.Translation.string(35186) % (hdr, hdr)
					choice = interface.Dialog.options(title = 35185, message = message, labelDeny = 33065, labelCustom = 33821, labelConfirm = 33743, default = interface.Dialog.ChoiceCustom)
					if choice == interface.Dialog.ChoiceYes: return self.sourceResult(link = url, error = 'dolbyvision', loader = loader)
					elif choice == interface.Dialog.ChoiceNo: tools.Settings.set('internal.dolbyvision', True)

			if resolve == network.Resolver.ModeProvider: return self.sourceResult(link = url, loader = loader)

			# Do not retrieve the original link.
			# If external providers cannot resolve the link, they return None.
			# In such a case, resolving should stop immediately, instead of passing the original link to the handler/resolver.
			# If the resolve() function is not implemented by the provider, the original link is returned as the resolved link, and will be set as linkProvider in the stream.
			url = item['stream'].linkResolved(original = False, provider = True, stream = False)
			if url is None: # Provider (especially external providers) could not internally resolve the link via the resolve() function.
				interface.Dialog.notification(title = 33448, message = 33691, icon = interface.Dialog.IconError)
				return self.sourceResult(error = 'resolve', loader = loader)

			url = url.replace('filefactory.com/stream/', 'filefactory.com/file/')
			if resolve == network.Resolver.ModeNone: return self.sourceResult(link = url, loader = loader)

			# Allow magnet links and local files.
			#if url is None or not '://' in str(url): raise Exception()
			isLocalFile = item['stream'].sourceTypeLocal() or tools.File.exists(url)
			if isLocalFile:
				# STRM files containing a plugin link.
				# Eg: The .strm files that are added by Gaia to the library.
				if Library.pathStrm(url):
					url = Library().resolveStrm(url)
					if url.startswith('plugin'):
						tools.System.executePlugin(command = url)
						return self.sourceResult(loader = loader)
					elif tools.File.exists(url):
						return self.sourceResult(link = url, local = True, loader = loader)
					else:
						# In case the STRM file contains a HTTP link, continue like normal.
						pass
				else:
					url = item['stream'].linkResolved(original = False, provider = True, stream = True) # Local cache downloads.
					return self.sourceResult(link = url, local = True, loader = loader)

			if url is None or (not isLocalFile and not '://' in str(url) and not 'magnet:' in str(url)):
				error = 'Resolve Error'

			if not error:
				if not internal: item['stream'] = Stream.load(data = item['stream'])

				popups = (not internal)
				sourceHandler = handler.Handler()
				if handle is None:
					handle = sourceHandler.serviceDetermine(mode = handleMode, item = item, popups = popups, cloud = cloud)
					if handle == handler.Handler.ReturnUnavailable or handle == handler.Handler.ReturnExternal or handle == handler.Handler.ReturnCancel:
						info = False
						url = None
						self.downloadCanceled = (handle == handler.Handler.ReturnCancel)
						error = 'Handler Error'

				if not error:
					result = sourceHandler.handle(link = url, item = item, name = handle, download = download, popups = popups, close = handleClose, mode = handleMode, cloud = cloud, strict = strict)
					if 'loader' in result and result['loader']:
						loader = True
						interface.Loader.show()

					if not result['success']:
						if result['error'] in [handler.Handler.ReturnUnavailable, handler.Handler.ReturnExternal, handler.Handler.ReturnCancel, handler.Handler.ReturnPack]:
							info = False
							url = None
							self.downloadCanceled = (result['error'] == handler.Handler.ReturnCancel)
							if result['error'] == handler.Handler.ReturnExternal: log = False
							error = 'Handler Error: ' + result['error']
						else:
							error = 'Url Error: ' + result['error']

					if not error:
						# Kodi Player fails if there are spaces in the URL.
						# OffCloud sometimes returns links with spaces (eg: season packs).
						result['link'] = network.Networker.linkClean(result['link'], headersStrip = False)

						extension = network.Networker().linkExtension(link = result['link'])
						extensions = ['rar', 'zip', '7zip', '7z', 's7z', 'tar', 'gz', 'gzip', 'iso', 'bz2', 'lz', 'lzma', 'dmg']
						if extension in extensions:
							if info:
								message = interface.Translation.string(33757) % extension.upper()
								interface.Dialog.notification(title = 33448, message = message, icon = interface.Dialog.IconError)
							try: orionoid.Orionoid(silent = True).streamVote(idItem = item['stream'].idOrionItem(), idStream = item['stream'].idOrionStream(), vote = orionoid.Orionoid.VoteDown, automatic = True)
							except: pass
							return self.sourceResult(error = 'filetype', loader = loader)

						# Do not do prechecks at the moment.
						# If every re-enabled, do not do checks for Emby/Jellyfin, since those servers return an empty reply on HEAD requests.
						'''if result['link'].startswith('http') and '.m3u8' in result['link']:
							if not network.Networker().requestSuccess(link = result['link']):
								error = 'M3U8 Error'
						elif result['link'].startswith('http'):
							# Some Premiumize hoster links, eg Vidto, return a 403 error when doing this precheck, even though the link works.
							# Do not conduct these prechecks for debrid services. If there is a problem with the link, the Kodi player will just fail.
							if not 'handle' in result or not result['handle'] in [i['id'] for i in handler.Handler.handles()]:
								if not network.Networker().requestSuccess(link = result['link']):
									error = 'Server Error'
						'''

					if not error or result['error'] == handler.Handler.ReturnExternal: return result
		except:
			if log: tools.Logger.error()
			error = True

		if error:
			if log and not error is True: tools.Logger.log(error)
			if info: interface.Dialog.notification(title = 33448, message = 33449, icon = interface.Dialog.IconError)
			try: orionoid.Orionoid(silent = True).streamVote(idItem = item['stream'].idOrionItem(), idStream = item['stream'].idOrionStream(), vote = orionoid.Orionoid.VoteDown, automatic = True)
			except: pass
			return self.sourceResult(link = url, error = 'unknown', loader = loader)

	def hosters(self):
		if Core.Hosters is None:
			self.lock.acquire() # Is accessed from multiple provider threads. Make sure it is only done once.
			if Core.Hosters is None:
				Core.Hosters = []
				try: Core.Hosters.extend(handler.HandleUrlResolver().services())
				except: pass
				try: Core.Hosters.extend(handler.HandleResolveUrl().services())
				except: pass
			self.lock.release()
		return Core.Hosters

	def hostersPremium(self):
		if Core.HostersPremium is None:
			self.lock.acquire() # Is accessed from multiple provider threads. Make sure it is only done once.
			if Core.HostersPremium is None:
				Core.HostersPremium = ['1fichier.com', 'oboom.com', 'rapidgator.net', 'rg.to', 'uploaded.net', 'uploaded.to', 'ul.to', 'filefactory.com', 'nitroflare.com', 'turbobit.net', 'uploadrocket.net']
			self.lock.release()
		return Core.HostersPremium

	def hostersCaptcha(self):
		if Core.HostersCaptcha is None:
			self.lock.acquire() # Is accessed from multiple provider threads. Make sure it is only done once.
			if Core.HostersCaptcha is None:
				Core.HostersCaptcha = ['hugefiles.net', 'kingfiles.net', 'openload.io', 'openload.co', 'oload.tv', 'thevideo.me', 'vidup.me', 'streamin.to', 'torba.se']
			self.lock.release()
		return Core.HostersCaptcha

	def hostersBlocked(self):
		if Core.HostersBlocked is None:
			self.lock.acquire() # Is accessed from multiple provider threads. Make sure it is only done once.
			if Core.HostersBlocked is None:
				# Guard or paste links (TheCrew - 2DDL).
				# Can be domain name + TLD, or just the domain name (to match all TLDs).
				#	http://new.myvideolinks.net/2022/04/08/halo-s01e03-emergence/
				#	https://guard.li/folder/f90ac6bf
				#	https://controlc.com/0bc67004
				#	https://paste2.org/gsImNOKH
				#	https://pastebin.com/
				#	https://justpaste.it
				#	https://i.postimg.cc/MHcQc5mB/The-Green-Knight-2021-1080p-WEBRip-x264-RARBG-Max-Rls-mp4-thumbs.png
				#	https://www.xvinlink.com/?a_fid=TwoDDL

				Core.HostersBlocked = [
					'myvideolinks.net',
					'guard.li',
					'linkguard.org',
					'controlc.com',
					'paste2.org',
					'pastebin.com',
					'justpaste.it',
					'xvinlink.com',
					'postimg',
					'postimages',
				]

			self.lock.release()
		return Core.HostersBlocked

	def servicesDebrid(self):
		if Core.ServicesDebrid is None:
			self.lock.acquire() # Is accessed from multiple provider threads. Make sure it is only done once.
			if Core.ServicesDebrid is None:
				# Native Services
				Core.ServicesDebrid = debrid.Debrid.services()

				# External Services
				for instance in External.instances():
					Core.ServicesDebrid[instance.id()] = instance.services()

			self.lock.release()
		return Core.ServicesDebrid

	def servicesExternal(self):
		try:
			if Core.ServicesExternal is None:
				self.lock.acquire() # Is accessed from multiple provider threads. Make sure it is only done once.
				if Core.ServicesExternal is None:
					external = {}
					symbols = ['.', '-', '_']

					# Do not retrieve only the enabled providers.
					# The user might have disabled external providers, but might still want to use hosters links from Orion that require these disabled providers.
					providers = ProviderManager.providers(type = ProviderBase.TypeExternal, enabled = None, local = False)

					for provider in providers:
						keys = []

						keys.append(provider.id())
						keys.append(provider.name())
						keys.append(provider.name().lower())
						try: keys.append(provider.instanceId())
						except: pass

						links = provider.links()
						if links:
							for link in links:
								keys.append(link)
								link = link.lower()
								keys.append(link)

								domain1 = network.Networker.linkDomain(link = link, subdomain = False, topdomain = True, ip = True)
								keys.append(domain1)
								keys.append(tools.Tools.replaceNotAlphaNumeric(domain1)) # Legacy Orion has hosters without TLD dot (eg: "nitrodownload" instead of "nitro.download").

								domain2 = network.Networker.linkDomain(link = link, subdomain = False, topdomain = False, ip = True)
								keys.append(domain2)
								keys.append(tools.Tools.replaceNotAlphaNumeric(domain2))

								for symbol in symbols:
									domain1 = domain1.replace(symbol, '')
									domain2 = domain2.replace(symbol, '')
								keys.append(domain1)
								keys.append(domain2)

						keys = [key for key in keys if key]
						keys = tools.Tools.listUnique(keys)

						for key in keys:
							external[key] = provider

					Core.ServicesExternal = external # Only set this at the end, in case multiple threads call the function at the same time
				self.lock.release()
		except:
			tools.Logger.error()
			try: self.lock.release()
			except: pass
		return Core.ServicesExternal
