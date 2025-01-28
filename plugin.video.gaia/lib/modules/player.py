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
import xbmcvfs

from lib import debrid
from lib.modules import trakt
from lib.modules import tools
from lib.modules import interface
from lib.modules import window
from lib.modules import handler
from lib.modules import library
from lib.modules import orionoid
from lib.modules.vpn import Vpn
from lib.modules.playback import Playback
from lib.modules.stream import Stream
from lib.modules.theme import Theme
from lib.modules.concurrency import Pool, Lock

from lib.meta.image import MetaImage
from lib.meta.tools import MetaTools

# If the player automatically closes/crashes because the EOF was reached while still downloading, the player instance is never deleted.
# Now the player keeps a constant lock on the played file and the file cannot be deleted (manually, or by the downloader). The lock is only release when Kodi exits.
# Use a thread and forcefully delete the instance. Although this is still no garantuee that Kodi will release the lock on the file, but it seems to work most of the time.
def playerDelete(instance):
	tools.Time.sleep(1)
	# Do not just use "del instance", since this will only call __del__() if the reference count drops to 0. Kodi still has a reference to the instance.
	try: instance.__del__()
	except: pass
	try: del instance
	except: pass

class Player(xbmc.Player):

	# Status
	StatusIdle = 0
	StatusPlaying = 1
	StatusPaused = 2
	StatusStopped = 3
	StatusEnded = 4

	# Download
	DownloadThresholdStart = 0.01 # If the difference between the download and the playback progress is lower than this percentage, buffering will start.
	DownloadThresholdStop = DownloadThresholdStart * 2 # If the difference between the download and the playback progress is higher than this percentage, buffering will stop.
	DownloadMinimum = 1048576 # 1 MB. The minimum number of bytes that must be available to avoid buffering. If the value is too small, the player with automatically stop/crash due to insufficient data available.
	DownloadFuture = 102400 # 100 KB. The number of bytes to read and update the progress with. Small values increase disk access, large values causes slow/jumpy progress.
	DownloadChunk = 8 # 8 B. The number of null bytes that are considered the end of file.
	DownloadNull = '\x00' * DownloadChunk

	ResumeTime = 10 # Resume playback a number of seconds before the recorded playback time, to catch up on the story.

	DetailsSplit = 75 # 90 is just enough for default Estaury skin. Make it a bit less for other skins.

	Instance = None

	def __init__ (self,):
		xbmc.Player.__init__(self)
		self.status = self.statusDone = Player.StatusIdle
		self.statusStarted = False

	def __del__(self):
		try:
			self._downloadClear(delete = False)

			# Not sure why this statement is here.
			# Why would we want to cancel the playback window at the end of playback?
			# This causes a sporadic bug (maybe 10-20% of the time) during binge watching.
			# After the rating/continue dialog, the playback of the next episode starts.
			# Less than a second into it, the playback is canceled and the playback window closed, by this statement.
			# Check keepPlaybackAlive() for more details.
			#self.core.progressPlaybackClose(background = False, loader = False)
		except: tools.Logger.error()
		try: xbmc.Player.__del__(self)
		except: pass

	@classmethod
	def instance(self, reinitialize = False):
		if Player.Instance is None or reinitialize: Player.Instance = self()
		return Player.Instance

	@classmethod
	def reset(self, settings = True):
		Player.Instance = None

	def run(self, media, title, year, season, episode, imdb, tmdb, tvdb, trakt, metadata, downloadType = None, downloadId = None, source = None, binge = None, resume = None, autoplay = None, reload = None, handle = None, service = None):
		try:
			if interface.Player.canceled(): return False

			self.vpnMonitor = False
			if Vpn.settingsEnabled():
				if Vpn.statusConnectedGlobal(): self.vpnMonitor = True
				elif Vpn.killPlayback(initial = True): self.vpnMonitor = Vpn.statusConnectedGlobal() # User manually selected to continue without a VPN.
				else: return False

			self.navigationStreamsSpecial = tools.Settings.getInteger('interface.stream.interface') == 0

			from lib.modules import core
			self.core = core.Core(media = media)

			self.media = media
			self.mediaFilm = tools.Media.isFilm(self.media)
			self.mediaSerie = tools.Media.isSerie(self.media)

			self.timeTotal = 0
			self.timeCurrent = 0

			self.idImdb = imdb
			self.idTmdb = tmdb
			self.idTvdb = tvdb
			self.idTrakt = trakt
			self.title = title
			self.year = int(year) if year else year

			if metadata:
				if not self.idImdb: self.idImdb = metadata.get('imdb')
				if not self.idTmdb: self.idTmdb = metadata.get('tmdb')
				if not self.idTvdb: self.idTvdb = metadata.get('tvdb')
				if not self.idTrakt: self.idTrakt = metadata.get('trakt')
				if not self.title: self.title = metadata.get('title')
				if not self.year: self.year = metadata.get('year')

			try: self.idSet = metadata['collection']['id']
			except: self.idSet = None

			self.autoplay = autoplay
			self.reload = reload
			self.handle = handle
			self.service = service
			self.kodi = None
			try: self.name = tools.Title.titleUniversal(metadata = metadata)
			except: self.name = self.title

			try:
				self.season = int(season) if self.mediaSerie else None
				self.seasonString = '%01d' % self.season if self.mediaSerie else None
			except:
				self.season = None
				self.seasonString = None
			try:
				self.episode = int(episode) if self.mediaSerie else None
				self.episodeString = '%01d' % self.episode if self.mediaSerie else None
			except:
				self.episode = None
				self.episodeString = None

			self.binge = not episode is None and binge
			self.bingeDialogNone = tools.Binge.dialogNone()
			self.bingeDialogFull = tools.Binge.dialogFull()
			self.bingeDialogOverlay = tools.Binge.dialogOverlay()
			self.bingeDialogButton = tools.Binge.dialogButton()
			self.bingeDialogUpNext = tools.Binge.dialogUpNext()
			self.bingeSuppress = tools.Binge.suppress()
			self.bingeScrape = None
			self.bingeDelay = None
			self.bingeDelayBefore = None
			self.bingeContinue = None
			self.bingeTimeout = None
			self.bingePlay = False
			self.bingeFinishedScrape = False
			self.bingeFinishedCheck = False
			self.bingeFinishedShow = False
			self.bingeFinishedPlay = False
			self.bingeMetadata = None
			self.bingeThread = None

			# Make sure the latests Trakt status is pulled in, so that the item can be correctly marked as watched if the user changes the playcount on Trakt's website just beforehand.
			self.playback = Playback.instance()
			self.playback.refresh(media = self.media, history = True, progress = True, rating = False, reload = False, wait = False) # NB: Do not reload with this call. Otherwise there are too many requests while playback starts, slowing down things.
			self.playbackWatched = False
			self.playbackLock = Lock()

			self.playbackEnd = 80
			if self.playback.settingsHistoryEnabled(): self.playbackEnd = self.playback.settingsHistoryEnd()
			self.playbackEnd = self.playbackEnd / 100.0

			self.source = source
			self.source['stream'] = Stream.load(data = self.source['stream'])
			Audio.languageSet(self.source['stream'].metaLanguage())

			# For Emby/Jellyfin.
			if self.service and self.service.lower() == 'automatic':
				if self.source['stream'].accessTypeDirect():
					origin = self.source['stream'].sourceOrigin()
					if origin and origin.lower() in ['emby', 'jellyfin']: self.service = origin
					else: self.service = 'Direct'
				else:
					if self.handle:
						from lib.debrid import Debrid
						debrid = Debrid.meta(id = self.handle)
						if debrid: self.service = debrid['name']
						else: self.service = None
					else: self.service = None

			self.url = self.source['stream'].streamLink() # Local cache downloads.
			if not self.url: self.url = self.source['stream'].linkResolved()

			self.autopack = None
			if self.mediaSerie and self.source['stream'].filePack():
				self.autopack = self.source['stream'].hash()
				if not self.autopack: self.autopack = self.source['stream'].linkPrimary()

			self.metatools = MetaTools.instance()
			self.metadata = metadata
			item = self.metatools.item(metadata = metadata, command = self.url, context = False, label = False) # Do not create custom label with episode number.
			self.item = item['item']
			self.metadataCleaned = item['metadata']

			self.detailsThreadMain = None
			self.detailsThreadUpdate = None
			self.detailsThreadSpeed = None
			self.detailsThreadStop = None
			self.detailsPrevious = None

			self.progress = None
			self.progressBusy = False
			self.progressInitialized = False
			self.progressThread = None
			self.progressRetrieve()

			self.timeTotal = 0
			self.timeCurrent = 0
			self.timeProgress = 0
			self.sizeTotal = 0
			self.sizeCurrent = 0
			self.sizeProgress = 0
			self.dialog = None
			self.resumeTime = resume
			self.resumedTime = None

			self.interacted = False
			self.interactBackground = False
			self.interactRating = self.playback.settingsRatingEnabled()
			self.interactContinue = tools.Binge.continueEnabled()
			self.interactSpecial = self.playback.settingsDialogTypeSpecial()
			self.interactPropagate = tools.Binge.continuePropagate()
			self.interactObserver = None
			self.interactLock = Lock()
			self._interactObserverStart()

			self.playbackInitialized = False
			self.playbackFinalized = False
			self.libraryUpdated = False
			self.libraryUpdated = False

			# This is used by the Gaia Eminence to hide "Source too slow" notifications, since Gaia has its own buffering notifications.
			tools.System.windowPropertySet('GaiaPlayerLink', self.url)

			self.details = {}
			self.detailsUpdate()

			# Used by the Trakt addon to make requests to the Trakt API (scrobble, rating dialog, etc).
			# The Trakt addon seems to be able to find episodes without these IDs.
			# However, for movies these IDs are required, otherwise the addon only detects the year from the self.item set to the player, but not IDs or the title.
			# Update: Not used anymore, since ratings are now done locally.
			tools.System.windowPropertySet('script.trakt.ids', tools.Converter.jsonTo({'imdb' : '0', 'tmdb' : '0', 'tvdb' : '0', 'trakt' : '0'})) # Add these to prevent Trakt from showing its own rating dialog.
			'''ids = {}
			if imdb: ids['imdb'] = imdb
			if tmdb: ids['tmdb'] = tmdb
			if tvdb: ids['tvdb'] = tvdb
			if trakt: ids['trakt'] = trakt
			tools.System.windowPropertySet('script.trakt.ids', tools.Converter.jsonTo(ids))'''

			self.downloadCheck = False
			if downloadType and downloadId:
				from lib.modules import downloader
				self.download = downloader.Downloader(type = downloadType, id = downloadId)
				self.downloadBufferCounter = 0
				self.downloadBufferShow = True

				# Already check here, so that the player waits when the download is still queued/initialized.
				if not self._downloadCheck(): return False
			else:
				self.download = None
				self.downloadBufferCounter = None
				self.downloadBufferShow = None

			self.buffer = False
			self.bufferLock = Lock()
			self.bufferNeeded = self._bufferBits(self.source['stream'].fileBandwidth())
			self.bufferNetwork = None
			self.bufferKodi = None
			self.bufferPrevious = None
			self.bufferThread = None
			self.bufferFailures = 0
			self.bufferDuration = 0

			self.retryBusy = False
			self.retryMessage = ''
			self.retryRemaining = 0
			self.retryTotal = 1
			self.retryDelay = 0
			if tools.Settings.getBoolean('playback.retry.enabled'):
				self.retryTotal += tools.Settings.getInteger('playback.retry.limit')
				self.retryDelay = tools.Settings.getInteger('playback.retry.delay')
			self.retryRemaining = self.retryTotal

			# Once self.play() is called, Kodi can hang for some time, especially if the  connection times out (30+ seconds).
			# Update the label here already.
			self.keepPlaybackProgress(initialize = True, update = True)

			# Hide the caching/download notification if still showing.
			# Only do this when downloads are enabled, since important notifications can be shown from handler.py (eg: HandleResolver.result()).
			if self.download: interface.Dialog.closeNotification()

			success = False
			while self.retryRemaining > 0:
				if interface.Player.canceled(): break

				self.retryRemaining -= 1
				self.keepPlaybackProgress(update = True) # Make sure the retry window is shown if applicable. Must be before self.play(), because Kodi can freeze there.

				self.status = self.statusDone = Player.StatusIdle
				self.playbackInitialized = False
				self.playbackFinalized = False

				self._errorLog()
				self.error = False

				# When retrying, Kodi player might still try to play from the previous time (eg: stuck at connection timeout).
				# Manually stop to ensure everything is cleared.
				# NB: Only do this on retrying connection. Otherwise this might (maybe) cause the problem with "Retrying Stream Connection", because of internal threads that might only fire after self.play() is called below.
				# Update: The retrying connection still happens, but at least the reconnection seem to work now. Before 95% of reconnections failed.
				if self.retryBusy:
					self.stop()
					for i in range(30): # Wait for self.stop() to finish.
						if self.statusDone == Player.StatusStopped or self.statusDone == Player.StatusEnded: break
						tools.Time.sleep(0.1)
					if not self.statusDone == Player.StatusStopped and not self.statusDone == Player.StatusEnded:
						tools.Time.sleep(2)
					self.status = self.statusDone = Player.StatusIdle

				self.play(self.url, self.item)
				interface.Loader.hide()
				success = self.keepPlaybackAlive()

				if success or tools.System.aborted() or self.core.progressPlaybackCanceled():
					self.retryBusy = False
					self._closeFailure()
					break
				if self.retryRemaining > 0:
					self.retryBusy = True
					tools.Logger.log('Retrying Playback')

					if interface.Core.background() and not self.core.progressPlaybackEnabled():
						self.retryMessage = interface.Translation.string(35303)
					else:
						if self.retryRemaining == 1: self.retryMessage = interface.Translation.string(35294)
						elif self.retryRemaining > 1: self.retryMessage = interface.Translation.string(35293) % (self.retryRemaining + 1)

					self.detailsPrevious = None # Make sure the metadata is set in the Kore app if the connection fails and we reconnect.

			self._errorLog(finish = True)

			if not success:
				self.core.progressPlaybackClose()
				if self.retryRemaining == 0:
					self.retryBusy = False
					self._closeFailure()
					interface.Dialog.notification(title = 33448, message = 33450, icon = interface.Dialog.IconError)

			# This should solve the issue of Gaia videos being played twice when launched from OpenMeta or widgets when using the directory structure.
			# Setting it to True will cause the video to play again after finishing playback, when launched from the local library.
			# Update: This could probably be solved by using a dummy URL for pluginResolvedSet:
			#	plugin://plugin.video.gaia/?action=dummy
			# Kodi will then call the dummy URL which does nothing, without playing the video URL twice.
			# Update 2: if 'success = True', Kodi will call the URL of the item passed in.
			# Calling pluginResolvedSet() also hides Kodi's popup dialo:
			#	Playback failed - One or more items failed to play. Check the log for more information abouth this message.
			# Update 3: These dialogs are now suppressed through advancedsettings.xml. Check tools.Playlist.settings() for more info.
			#tools.System.pluginResolvedSet(success = True, item = self.item)
			#tools.System.pluginResolvedSet(success = False, item = self.item)
			tools.System.pluginResolvedSet(success = False, dummy = True) # When played from the local library, 'success = False' hides the dialog, 'success = True' still shows the dialog.

			# Sometimes when stopping playback, the Kodi player does not fire the onPlayBackStopped/onPlayBackEnded events.
			# This causes the stream window not to reload.
			# Manually call the event in such a case.
			# Update: Maybe this has been solved. Check the comments in onPlayBackStarted().
			if not self.status == Player.StatusStopped and not self.status == Player.StatusEnded: self.onPlayBackStopped()

			# In case the playback failed or timed out without finishing naturally.
			# Only do this if not playing, otherwise this call can be sporadically triggered before the call from onPlayBackStopped(), and then the stream window is not reloaded.
			# Update: Maybe this has been solved. Check the comments in onPlayBackStarted().
			if not self.status == Player.StatusPlaying: self.playbackFinalize()

			return success
		except: tools.Logger.error()
		return False

	@classmethod
	def join(self, thread):
		# It seems that Kodi's player is only executed in a single thread.
		# That means, any blocking execution (eg: thread.join()) in this class, would block the Kodi's player code, preventing Kodi from firing events like onPlayBackStopped/onPlayBackEnded.
		# Only once the execution is unblocked, will these events fire.
		# Instead, use a loop with busy-wait to "join" threads.
		# This allows some idle/sleep time in between checks, which in turn allows Kodi's player code to execute and fire the right events.
		# This should probably only affect blocking joins started from the main thread (inside self.run()), but just do it for all threads here, in case it affects non-blocking joins within sub-threads.
		Pool.join(instance = thread, busy = True)

	def detailsRefresh(self):
		# If retry stream connection, stop the previous thread and restart.
		if self.detailsThreadMain:
			self.detailsThreadStop = True
			try: self.detailsThread.join()
			except: Logger.error()
			self.detailsThreadStop = False

		self.detailsSet(force = True)
		self.detailsUpdateSpeed()
		self.detailsNotification()

		# Sometimes the metadata is not set in the player.
		# This causes the title/plot/poster/etc not to show in the Kore app.
		# This typically happens if Gaia retries playback after failing to establish a stream connection.
		# This is probably caused by updateInfoTag() in detailsSet(), which only works if the player is currently playing.
		# Retry a few times. Hopefully the player has started by then.
		self.detailsThreadMain = Pool.thread(target = self._detailsRefresh, start = True)

	def _detailsRefresh(self):
		for i in range(30):
			tools.Time.sleep(2)
			if self.detailsThreadStop or self.detailsSet(force = True): break

	def detailsUpdate(self):
		try:
			if tools.Settings.getInteger('playback.details.description') > 0:
				if self.detailsThreadUpdate is None:
					self.detailsThreadUpdate = Pool.thread(target = self._detailsUpdate, start = True)
		except: tools.Logger.error()

	def _detailsUpdate(self):
		try:
			threads = []
			if tools.Settings.getInteger('playback.details.description.production') > 0:
				threads.append(Pool.thread(target = self._detailsUpdateProduction, start = True))
			if tools.Settings.getInteger('playback.details.description.service') > 0:
				threads.append(Pool.thread(target = self._detailsUpdateService, start = True))
			if tools.Settings.getInteger('playback.details.description.device') > 0:
				threads.append(Pool.thread(target = self._detailsUpdateDevice, start = True))
			if tools.Settings.getInteger('playback.details.description.server') > 0:
				threads.append(Pool.thread(target = self._detailsUpdateServer, start = True))
			if tools.Settings.getInteger('playback.details.description.name') > 0:
				threads.append(Pool.thread(target = self._detailsUpdateName, start = True))
			if tools.Settings.getInteger('playback.details.description.link') > 0:
				threads.append(Pool.thread(target = self._detailsUpdateLink, start = True))
			[self.join(thread) for thread in threads]
			self.detailsSet()
		except: tools.Logger.error()

	def _detailsUpdateProduction(self):
		try:
			setting = tools.Settings.getInteger('playback.details.description.production')
			details = {}

			if setting >= 1:
				details['director'] = self.metadata.get('director')
			if setting >= 2:
				details['writer'] = self.metadata.get('writer')
				details['creator'] = self.metadata.get('creator')
			if setting >= 3:
				details['network'] = self.metadata.get('network')
				details['studio'] = self.metadata.get('studio')

			if details:
				for k, v in details.items():
					if v: self.details[k] = interface.Format.iconJoin(v[:4])
		except: tools.Logger.error()

	def _detailsUpdateService(self):
		try:
			from lib.modules.network import Networker
			setting = tools.Settings.getInteger('playback.details.description.service')
			details = None
			if setting == 1: details = [self.service]
			elif setting == 2: details = [self.service, Networker.linkDomain(link = self.url, subdomain = False, topdomain = True, ip = True, scheme = False)]
			elif setting == 3: details = [self.service, Networker.linkDomain(link = self.url, subdomain = True, topdomain = True, ip = True, scheme = False)]
			if details: self.details['service'] = interface.Format.iconJoin([i for i in details if i])
		except: tools.Logger.error()

	def _detailsUpdateDevice(self):
		try:
			from lib.modules.network import Geolocator
			data = Geolocator.detectGlobal()
			if data:
				setting = tools.Settings.getInteger('playback.details.description.device')
				details = None
				if setting == 1: details = [data['location']['label']['short']['icon']]
				elif setting == 2: details = [data['location']['label']['long']['icon']]
				elif setting == 3: details = [data['location']['label']['long']['icon'], data['address']['ip']]
				if details: self.details['device'] = interface.Format.iconJoin(details)
		except: tools.Logger.error()

	def _detailsUpdateServer(self):
		try:
			from lib.modules.network import Geolocator
			data = Geolocator.detectExternal(domain = self.url)
			if data:
				setting = tools.Settings.getInteger('playback.details.description.server')
				details = None
				if setting == 1: details = [data['location']['label']['short']['icon']]
				elif setting == 2: details = [data['location']['label']['long']['icon']]
				elif setting == 3: details = [data['location']['label']['long']['icon'], data['address']['ip']]
				if details: self.details['server'] = interface.Format.iconJoin(details)
		except: tools.Logger.error()

	def _detailsUpdateName(self):
		try:
			from lib.modules.network import Networker
			name = Networker.linkName(link = self.url, extension = True)
			if name: self.details['name'] = tools.Tools.stringSplit(name, length = Player.DetailsSplit, join = ' ')
		except: tools.Logger.error()

	def _detailsUpdateLink(self):
		try:
			if self.url: self.details['link'] = tools.Tools.stringSplit(self.url, length = Player.DetailsSplit, join = ' ')
		except: tools.Logger.error()

	def detailsUpdateSpeed(self):
		try:
			if tools.Settings.getInteger('playback.details.description') > 0:
				if self.detailsThreadSpeed is None: # Do not start multiple threads when retrying stream connection.
					self.detailsThreadSpeed = Pool.thread(target = self._detailsUpdateSpeed, start = True)
		except: tools.Logger.error()

	def _detailsUpdateSpeed(self):
		try:
			setting = tools.Settings.getInteger('playback.details.description.speed')
			if setting > 0:
				setting -= 1 # Buffer setting does not have a "Disabled" value at 0.
				while self.isBusy():
					speed = self._bufferDetect(duration = 5, setting = setting)
					if not speed: break
					self.details['speed'] = speed
					self.detailsSet()
					tools.Time.sleep(15)
		except: tools.Logger.error()

	def detailsSet(self, force = False):
		try:
			if self.metadataCleaned:
				newline = interface.Format.newline()

				details = []

				if 'creator' in self.details: details.append((35685, self.details['creator']))
				if 'director' in self.details: details.append((35377, self.details['director']))
				if 'writer' in self.details: details.append((35684, self.details['writer']))
				if 'network' in self.details: details.append((33719, self.details['network']))
				if 'studio' in self.details: details.append((35811, self.details['studio']))

				if 'speed' in self.details: details.append((35418, self.details['speed']))
				if 'service' in self.details: details.append((35420, self.details['service']))
				if 'device' in self.details: details.append((35419, self.details['device']))
				if 'server' in self.details: details.append((35207, self.details['server']))
				if 'name' in self.details: details.append((35724, self.details['name']))
				if 'link' in self.details: details.append((33702, self.details['link']))

				details = newline.join([interface.Format.fontBold(interface.Translation.string(i[0]) + ': ') + i[1] for i in details])

				# There is a weird sporadic error in the Kore remote app.
				# After binging a few episodes, the Kore app suddenly says it is not connected to Kodi anymore. Restarting Kore does not help.
				# When keeping the Kore app open, there might be a second every then and now where it connects back to Kodi, but then loses connection immediately afterwards.
				# When stoping playback, Kore reconnect permanently and the error is gone.
				# Not sure if this is a Kodi or Kore bug.
				# Maybe it is caused by Gaia constantly setting updateInfoTag() and Kore getting confused or flooded.
				# Now we just set the info if the details actually changed.
				# If the speed setting was enabled, this problem might still remain, since the speed thread calls this function every 15 seconds.
				# Not sure if this will fix the problem.
				if force or not details == self.detailsPrevious:
					self.detailsPrevious = details
					metadata = tools.Tools.copy(self.metadataCleaned)
					if not 'plot' in metadata or not metadata['plot']: metadata['plot'] = ''
					metadata['plot'] = metadata['plot'].strip('\n').strip('\r')
					separator = (newline * 2) if metadata['plot'] else ''

					if tools.Settings.getInteger('playback.details.description') == 1: metadata['plot'] = details + separator + metadata['plot'] + newline
					else: metadata['plot'] = metadata['plot'] + separator + details + newline

					try:
						self.metatools.itemInfo(item = self.item, metadata = metadata)
						self.updateInfoTag(self.item)
						return True
					except: pass # Not yet playing.
		except: tools.Logger.error()
		return False

	def detailsNotification(self):
		try:
			if tools.Settings.getInteger('playback.details.notification') > 0:
				Pool.thread(target = self._detailsNotification, start = True)
		except: tools.Logger.error()

	def _detailsNotification(self):
		try:
			setting = tools.Settings.getInteger('playback.details.notification')
			title = None
			message = None
			if setting == 1:
				title = 35418
				message = self._bufferDetect(duration = 5, setting = 2)
			elif setting == 2:
				from lib.modules.network import Networker
				title = 35420
				message = [self.service, Networker.linkDomain(link = self.url, subdomain = False, topdomain = True, ip = True, scheme = False)]
			elif setting == 3:
				from lib.modules.network import Geolocator
				data = Geolocator.detectGlobal()
				title = 35419
				message = [data['location']['label']['long']['icon'], data['address']['ip']]
			elif setting == 4:
				from lib.modules.network import Geolocator
				data = Geolocator.detectExternal(domain = self.url)
				title = 35207
				message = [data['location']['label']['long']['icon'], data['address']['ip']]
			elif setting == 5:
				from lib.modules.network import Networker
				title = 35724
				message = Networker.linkName(link = self.url, extension = True)
			elif setting == 5:
				title = 33702
				message = self.url
			if tools.Tools.isArray(message): message = interface.Format.iconJoin([i for i in message if i])
			interface.Dialog.notification(title = title, message = message, icon = interface.Dialog.IconInformation, time = 10000)
		except: tools.Logger.error()

	def interact(self):
		try:
			self.interactLock.acquire() # Can be called multiple times simultaneously (_bingePlay and playbackFinalize).
			if not self.interacted and self.bingeSuppress <= 1:
				if self.playbackWatched:
					if self.interactSpecial and not self.interactBackground:
						self.interactBackground = True
						window.WindowBackground.show(metadata = self.metadata, logo = True)
						tools.Time.sleep(0.05) # Sometimes the background window shows on top of the rating window.

					self.interacted = True
					if self.core.propertySilent(): self.core.propertySilentSet(self.core.SilentInteract)

					stopped = self.bingeContinue is None and self.bingeTimeout is None

					# Only set this if the user did not manually select an option already.
					# That is, stopping playback (eg from Kore app) without clicking on a button in the binge dialog before.
					# Treat this as a timed-out non-action.
					# If the current episode was stopped too early (not finished watching), do not continue with binge.
					if stopped:
						if self.playbackWatched: # Stopped close to the end of playback.
							self.bingeContinue = tools.Binge.actionNone() == tools.Binge.ActionContinue
							self.bingeTimeout = True
						else: # Stopped somewhere 2/3 into playback.
							self.bingeContinue = False
							self.bingeTimeout = True

					observation = self._interactObserverEvaluate()
					binge = self.binge and self.bingeMetadata and (self.bingeContinue or (self.interactContinue and not stopped)) # Always allow if the continue dialog is enabled. Check self.bingeMetadata, in case of last episode.
					if not self.binge and observation: binge = True # For movies with an observer.

					result = self.playback.dialogAutorate(media = self.media, imdb = self.idImdb, tmdb = self.idTmdb, tvdb = self.idTvdb, trakt = self.idTrakt, season = self.season, episode = self.episode, binge = binge, automatic = bool(self.autoplay or self.autopack))
					if result is False: self.bingeContinue = False # Otherwise binging continues if the power button was used in the dialog.

					if result and binge and self.interactContinue and self.bingeMetadata:
						default = None
						fixed = False
						if not self.bingeTimeout:
							if self.interactPropagate > 0:
								action = window.WindowContinue.ActionContinue if self.bingeContinue else window.WindowContinue.ActionStop
								if self.interactPropagate == 1:
									default = action
								elif self.interactPropagate == 2:
									fixed = True
									result = {'action' : action, 'timeout' : False, 'interacted' : False}

						if observation: default = observation
						if not fixed:
							self._interactObserverNotify(observation)
							result = self.playback.dialogContinue(metadata = self.bingeMetadata, binge = True, default = default)

						if result:
							if result['action'] is window.WindowContinue.ActionNone:
								self.bingeTimeout = result['timeout']
								self.bingeContinue = tools.Binge.actionNone() == tools.Binge.ActionContinue
							else:
								self.bingeTimeout = result['timeout']
								self.bingeContinue = result['action'] == window.WindowContinue.ActionContinue
						else:
							self.bingeTimeout = False
							self.bingeContinue = False
					elif observation:
						self._interactObserverNotify(observation)
						self.playback.dialogContinue(metadata = self.metadata, binge = False, default = observation)
					else:
						window.WindowBackground.close()

		finally: self.interactLock.release()

	def _interactObserver(self, type):
		if not self.interactObserver == type:
			self.interactObserver = type
			tools.Observer.updatePlayback(type = type, imdb = self.idImdb, tmdb = self.idTmdb, tvdb = self.idTvdb, trakt = self.idTrakt, set = self.idSet, season = self.season, episode = self.episode)

	def _interactObserverStart(self):
		self._interactObserver(type = tools.Observer.TypeStart)

	def _interactObserverStop(self):
		self._interactObserver(type = tools.Observer.TypeStop)

	def _interactObserverEvaluate(self):
		self._interactObserverStop()
		return tools.Observer.evaluate(binge = bool(self.bingeMetadata) if self.mediaSerie else None, notify = False) # Notify AFTER the rating dialog.

	def _interactObserverNotify(self, observation):
		tools.Observer.notify(observation = observation)

	def _showStreams(self):
		if self.reload and (not self.binge or (self.binge and not self.bingeFinishedCheck)):
			if self.navigationStreamsSpecial and not self.autoplay:
				# Do not reload the streams window if playback failed and we are busy retrying playback.
				# Otherwise when trying playback, it mostly succeeds and then the Kodi player shows, and shortly after, the streams window is reloaded on top.
				if not self.retryBusy:
					# Only show the streams window when launched from Gaia.
					# Do not reload if this is launched from eg the local library.
					if tools.System.originGaia(quick = False):
						reload = False
						setting = tools.Settings.getInteger('interface.stream.interface.reload')
						if setting == 1:
							reload == self.status == Player.StatusPaused
						elif setting == 2:
							if self.status == Player.StatusPaused: reload = True
							elif self.status in [Player.StatusStopped, Player.StatusEnded]: reload = not self.playbackWatched
						elif setting == 3:
							if self.status == Player.StatusPaused: reload = True
							elif self.status in [Player.StatusStopped, Player.StatusEnded]: reload = True

						if reload:
							setting = tools.Settings.getInteger('interface.stream.interface.reload.mode')
							if setting > 0:
								if setting == 1: reload = interface.Dialog.option(title = 35545, message = 36459, labelConfirm = 33149, labelDeny = 33743, default = interface.Dialog.ChoiceNo, timeout = 15000)
								else: reload = not interface.Dialog.option(title = 35545, message = 36459, labelConfirm = 33743, labelDeny = 33149, default = interface.Dialog.ChoiceNo, timeout = 15000)

							if reload:
								# Reload streams in a separate process.
								# Otherwise we might end up in a long loop of play->reload->play->reload which might not clean up memory and increase the chance of running out of threads on low-end devices.
								#self.core.showStreams(filter = True, binge = self.binge, autoplay = self.autoplay)
								self.core.showStreamsExternal(filter = True, binge = self.binge, autoplay = self.autoplay, reload = True)
								return True
		return False

	def _debridClear(self):
		debrid.Debrid.deletePlayback(link = self.url, source = self.source)

	def _downloadStop(self):
		self._downloadClear(delete = False)
		if not self.download == None:
			from lib.modules import downloader
			self.download.stop(cacheOnly = True)

	def _downloadClear(self, delete = True):
		try: self.dialog.close()
		except: pass

		if delete:
			thread = Pool.thread(target = playerDelete, args = (self,))
			thread.start()

	def _downloadUpdateSize(self):
		try:
			from lib.modules import downloader

			# Try using the progress from the downloader, since the below code mostly returns 0.
			# Through Python, you can get the total file size (including the empty padded space).

			file = xbmcvfs.File(self.url) # The file must be opened each time this function is called, otherwise it does not refrehs with the new content/size.
			current = self.download.sizeCompleted()
			if current > 0:
				self.sizeCurrent = current
			else:
				file.seek(self.sizeCurrent, 0)
				data = file.read(self.DownloadChunk)
				try: length = len(data)
				except: length = 0
				while not data == self.DownloadNull and not length == 0:
					self.sizeCurrent += self.DownloadFuture
					file.seek(self.sizeCurrent, 0)
					data = file.read(self.DownloadChunk)
					try: length = len(data)
					except: length = 0
			self.sizeTotal = max(self.sizeTotal, file.size())
			file.close()
			if self.sizeTotal > 0: self.sizeProgress = self.sizeCurrent / float(self.sizeTotal)
		except:
			tools.Logger.error()
		return self.sizeProgress

	def _downloadUpdateTime(self):
		try: timeCurrent = max(self.timeCurrent, self.getTime())
		except: timeCurrent = 0
		try: timeTotal = max(self.timeTotal, self.getTotalTime())
		except: timeTotal = 0
		if timeTotal > 0: timeProgress = timeCurrent / float(timeTotal)
		else: timeProgress = 0
		return max(timeProgress, self.timeProgress)

	def _downloadProgressDifference(self):
		progressSize = self._downloadUpdateSize()
		progressTime = self._downloadUpdateTime()
		return max(0, progressSize - progressTime), progressSize

	def _downloadProgress(self):
		progress = ''
		if not self.download == None:
			from lib.modules import downloader
			progress = interface.Format.fontBold(interface.Translation.string(32403) + ': ')
			self.download.refresh()
			progress += self.download.progress()
			progress += ' - ' + self.download.speed() + interface.Format.newline()
		return progress

	def _downloadCheck(self):
		if self.download == None:
			return False

		# Ensures that only one process can access this function at a time. Otherwise this function is executed multiple times at the same time.
		if self.downloadCheck:
			return False

		# If the user constantly cancels the buffering dialog, the dialog will not be shown for the rest of the playback.
		if not self.downloadBufferShow:
			return False

		try:
			self.downloadCheck = True

			# Close all old and other dialogs.
			# Leave this for now. Seems to actually close the cache dialog below.
			#xbmc.executebuiltin('Dialog.Close(progressdialog,true)')
			#xbmc.executebuiltin('Dialog.Close(extendedprogressdialog,true)')
			#tools.Time.sleep(0.5) # Wait for the dialogs to close.

			# NB: The progress dialog pops up when the download is at 100%. Chack for the download progress (progressSize < 1).
			progressDifference, progressSize = self._downloadProgressDifference()
			if progressSize < 1 and progressDifference < self.DownloadThresholdStart or self.sizeCurrent < self.DownloadMinimum:
				paused = False
				try:
					if self.isPlaying():
						self.pause()
						paused = True
				except: pass

				title = interface.Translation.string(33368)
				message = interface.Translation.string(33369)
				interface.Core.create(type = interface.Core.TypeDownload, title = title, message = self._downloadProgress() + message, background = False)

				progressMinimum = progressDifference
				progressRange = self.DownloadThresholdStop - progressMinimum
				while progressSize < 1 and progressDifference < self.DownloadThresholdStop or self.sizeCurrent < self.DownloadMinimum:
					progress = max(1, int(((progressDifference - progressMinimum) / float(progressRange)) * 99))
					interface.Core.update(progress = progress, message = self._downloadProgress() + message)
					if interface.Core.canceled(): break
					tools.Time.sleep(1)
					if interface.Core.canceled(): break
					progressDifference, progressSize = self._downloadProgressDifference()

				canceled = interface.Core.canceled() # Will be reset after the dialog is closed below.
				interface.Core.update(progress = 100, message = message)
				interface.Core.close()
				tools.Time.sleep(0.2)

				if canceled:
					if self.isPlayback():
						self.downloadBufferCounter += 1
						if self.downloadBufferCounter % 3 == 0:
							if interface.Dialog.option(title = 33368, message = 33744):
								self.downloadBufferShow = False
					else:
						self._downloadStop()
						return False

				try:
					if paused:
						self.pause() # Unpause
				except: pass

			self.downloadCheck = False
			return True
		except:
			tools.Logger.error()
			self.downloadCheck = False
			return False

	def _bingeDelay(self):
		if self.bingeDelay is None:
			# If an outro chapter is available, sync the binge window accordingly.
			outro = None
			try:
				outro = Chapter.chapterOutro(single = True)
				if outro: self.bingeDelay = int(self.getTotalTime() - outro['time']['start'] + 1)
			except: tools.Logger.error()

			if not self.bingeDelay: self.bingeDelay = tools.Binge.delay()

			automatic = False
			duration = None
			try: duration = self.getTotalTime()
			except:
				try: duration = int(self.metadata['duration'])
				except: pass
			if self.bingeDelay == 0:
				automatic = True
				self.bingeDelay = int(duration / 50.0) if duration else 45
				self.bingeDelay = max(45, self.bingeDelay)
				if self.bingeDialogFull: self.bingeDelay = int(self.bingeDelay / 3.0)
				self.bingeDelay = min(90, self.bingeDelay)

			# Increase the time for the overlay dialog.
			# The dialog is shown hidden at this time and can be manually shown or wait for it to show automatically.
			# Using the following is sometimes too little if you want to skip ahead ealier. Just use a multiplier of 3 for all cases.
			#	self.bingeDelayBefore = int(self.bingeDelay * (3 if automatic and not outro else 2))
			# UPDATE: Using (self.bingeDelay * 3) is too little for some shows like "The Witcher" which can have 3-5 minutes of credits for 45-55 minutes play time.
			# UPDATE 2: For "Andor" this is a few seconds too little: max(3.0, (duration / 600.0) if duration else 4.0)
			if self.bingeDialogOverlay or self.bingeDialogButton:
				multiplier = max(3.0, (duration / 550.0) if duration else 4.0)
				self.bingeDelayBefore = int(self.bingeDelay * multiplier)

			self.bingeDelay = int(self.bingeDelay)
			self.bingeDelayBefore = int(self.bingeDelayBefore)

		return self.bingeDelay

	def _bingeCheck(self):
		try:
			if self.binge:
				remaining = self.timeTotal - self.timeCurrent
				# Do not start binge scraping before 5 minutes into playback, irrespective of the users binge time setting.
				# Firstly, it might interfere with the early-playback features, eg auto resume, auto audio/subtitle selection, etc.
				# Secondly, during the first few minutes the user might stop playback and select a different stream, due to buffering or video/audio problems, and we do not want to draw down the system during this time.
				if not self.bingeFinishedScrape and self.timeCurrent > 300 and remaining < tools.Binge.scrape():
					self.bingeFinishedScrape = True
					Pool.thread(target = self._bingeScrape, start = True)
				if not self.bingeFinishedCheck and self.bingeMetadata:
					if self.bingeDialogUpNext:
						if not self.bingeMetadata is None:
							# NB: AddonSignals cannot be called from a thread, otherwise the callback never fires.
							self.bingeFinishedCheck = True
							self._bingeUpNext()
					elif self.bingeDialogOverlay or self.bingeDialogButton:
						delay = self._bingeDelay()
						if self.bingeDelayBefore: delay = self.bingeDelayBefore
						if remaining <= delay:
							self.bingeFinishedCheck = True
							self._bingeShow()
		except: tools.Logger.error()

	def _bingeScrape(self):
		try:
			from lib.meta.manager import MetaManager
			self.bingeMetadata = MetaManager.instance().metadataEpisodeNext(title = self.metadata['tvshowtitle'], year = self.metadata['year'], imdb = self.metadata['imdb'], tmdb = self.metadata['tmdb'], tvdb = self.metadata['tvdb'], trakt = self.metadata['trakt'], season = self.metadata['season'], episode = self.metadata['episode'])
			if self.bingeMetadata:
				tools.System.executePlugin(action = 'scrape', parameters = {
					'silent' : True,
					'media' : self.media,
					'binge' : tools.Binge.ModeBackground,
					'title' : self.bingeMetadata['title'],
					'tvshowtitle' : self.bingeMetadata['tvshowtitle'],
					'year' : self.bingeMetadata['year'],
					'imdb' : self.bingeMetadata['imdb'],
					'tvdb' : self.bingeMetadata['tvdb'],
					'trakt' : self.bingeMetadata['trakt'],
					'season' : self.bingeMetadata['season'],
					'episode' : self.bingeMetadata['episode'],
					'premiered' : self.bingeMetadata['premiered'],
					'metadata' : tools.Converter.jsonTo(self.bingeMetadata),
					'autopack' : self.autopack,
				})
			elif self.bingeSuppress <= 1:
				if tools.Settings.getBoolean('activity.binge.notification'):
					interface.Dialog.notification(title = 35580, message = 35587, icon = interface.Dialog.IconInformation)
		except:
			tools.Logger.error()

	def _bingeUpNext(self):
		episodeCurrent = {
			'episodeid' : tools.Title.titleUniversal(metadata = self.metadata),
			'tvshowid' : self.metadata['imdb'] if 'imdb' in self.metadata else '',
			'title' : self.metadata['title'] if 'title' in self.metadata else '',
			'showtitle' : self.metadata['tvshowtitle'] if 'tvshowtitle' in self.metadata else '',
			'season' : int(self.metadata['season']) if 'season' in self.metadata else '',
			'episode' : int(self.metadata['episode']) if 'episode' in self.metadata else '',
			'playcount' : self.metadata['playcount'] if 'playcount' in self.metadata else 0,
			'plot' : self.metadata['plot'] if ('plot' in self.metadata and not self.metadata['plot'] is None) else '',
			'rating' : float(self.metadata['rating']) if 'rating' in self.metadata else 0,
			'firstaired' : self.metadata['premiered'] if 'premiered' in self.metadata else '',
			'art' : MetaImage.setUpNext(data = self.metadata),
		}

		episodeNext = {
			'episodeid' : tools.Title.titleUniversal(metadata = self.bingeMetadata),
			'tvshowid' : self.bingeMetadata['imdb'] if 'imdb' in self.bingeMetadata else '',
			'title' : self.bingeMetadata['title'] if 'title' in self.bingeMetadata else '',
			'showtitle' : self.bingeMetadata['tvshowtitle'] if 'tvshowtitle' in self.bingeMetadata else '',
			'season' : int(self.bingeMetadata['season']) if 'season' in self.bingeMetadata else '',
			'episode' : int(self.bingeMetadata['episode']) if 'episode' in self.bingeMetadata else '',
			'playcount' : self.bingeMetadata['playcount'] if 'playcount' in self.bingeMetadata else 0,
			'plot' : self.bingeMetadata['plot'] if ('plot' in self.bingeMetadata and not self.bingeMetadata['plot'] == '0') else '',
			'rating' : float(self.bingeMetadata['rating']) if ('rating' in self.bingeMetadata and not self.bingeMetadata['rating'] == '0') else 0,
			'firstaired' : self.bingeMetadata['premiered'] if ('premiered' in self.bingeMetadata and not self.bingeMetadata['premiered'] == '0') else '',
			'art' : MetaImage.setUpNext(data = self.bingeMetadata),
		}

		infoNext = {
			'current_episode': episodeCurrent,
			'next_episode': episodeNext,
			'play_info': {},
		}

		try:
			import AddonSignals
			AddonSignals.sendSignal('upnext_data', infoNext, source_id = tools.System.id())
			AddonSignals.registerSlot('upnextprovider', tools.System.id() + '_play_action', self._bingeShowUpNext)
		except: tools.Logger.error()

	def _bingeShowUpNext(self, data):
		self.bingeContinue = True
		self._bingeShow()

	def _bingeShow(self):
		# NB: Use a thread here.
		# The binge windows are blocking and _bingeShowDialog() will only finish if the user closed/continued the binging.
		# This in turn causes keepPlaybackAlive() to hang and not submit scrobble/watched status during the whole time the binge window is opened (including being hidden).
		if self.bingeThread is None or not self.bingeThread.alive():
			self.bingeThread = Pool.thread(target = self._bingeShowDialog, start = True)

	def _bingeShowDialog(self):
		try:
			if self.binge and self.bingeMetadata and not self.bingeFinishedShow:
				self.bingeFinishedShow = True
				if not self.bingeDialogUpNext:
					self.bingeContinue = None
					if self.bingeSuppress:
						Pool.thread(target = self._bingeSuppress, start = True)
					if self.bingeDialogNone:
						self.bingeContinue = True
					else:
						images = MetaImage.setEpisode(data = self.bingeMetadata, season = False, episode = False)

						background = None
						try: background = images['fanart']
						except: pass
						if not background:
							try: background = images['tvshow.fanart']
							except: pass
							if not background:
								try: background = images['tvshow.landscape']
								except: pass

						poster = None
						try: poster = images['poster']
						except: pass
						if not poster:
							try: poster = images['tvshow.poster']
							except: pass
							if not poster:
								try: poster = images['tvshow.keyart']
								except: pass

						bingeContinue = None
						if self.bingeDialogFull:
							delay = self._bingeDelay()
							bingeContinue = window.WindowBingeFull.show(title = self.bingeMetadata['tvshowtitle'], season = self.bingeMetadata['season'], episode = self.bingeMetadata['episode'], duration = self.bingeMetadata['duration'], background = background, poster = poster, delay = delay)
						elif self.bingeDialogOverlay:
							try: delay = int(self.getTotalTime() - self.getTime())
							except: delay = 0
							automatic = self._bingeDelay()
							if self.bingeDelayBefore:
								if delay < self.bingeDelayBefore: start = delay # If progress is manually skipped to the end, where there is less playback time left than the value of "automatic".
								else: start = self.bingeDelayBefore # Normal binge without playback skipping.
								automatic = max(0, start - automatic)
							bingeContinue = window.WindowBingeOverlay.show(title = self.bingeMetadata['tvshowtitle'], season = self.bingeMetadata['season'], episode = self.bingeMetadata['episode'], duration = self.bingeMetadata['duration'], background = background, poster = poster, delay = delay, automatic = automatic)
						elif self.bingeDialogButton:
							try: remaining = int(self.getTotalTime() - self.getTime())
							except: remaining = 0
							duration = self._bingeDelay()
							delay = 0
							if self.bingeDelayBefore:
								if remaining < self.bingeDelayBefore: start = remaining # If progress is manually skipped to the end, where there is less playback time left than the value of "automatic".
								else: start = self.bingeDelayBefore # Normal binge without playback skipping.
								delay = max(0, start - duration)
							duration = min(duration, remaining)
							bingeContinue = window.WindowBingeButton.show(delay = delay, duration = duration)

						if self.bingeTimeout is None: self.bingeContinue = bingeContinue # And set this if we did not already change the values from onPlayBackStopped() -> _bingeCancel().

				if self.bingeContinue is None and self.bingeTimeout is None:
					self.bingeTimeout = True
					self.bingeContinue = tools.Binge.actionNone() == tools.Binge.ActionContinue

				if self.bingeContinue:
					if self.status == Player.StatusStopped:
						self._bingePlay()
					elif tools.Binge.actionContinue() == tools.Binge.ActionInterrupt:
						self.stop()
						self._bingePlay()
					else:
						self.bingePlay = True
				elif tools.Binge.actionCancel() == tools.Binge.ActionInterrupt:
					self.stop()
		except: tools.Logger.error()

	def _bingePlay(self):
		try:
			if self.binge and not self.bingeFinishedPlay:
				self.bingeFinishedPlay = True

				self.interact() # Rate here, since the call from onPlayBackStopped() only fires after the executePlugin() below is executed.
				if not self.interactBackground and self.bingeContinue: interface.Loader.show()
				elif not self.bingeContinue: return self.core.propertySilentSet(self.core.SilentCancel) # Eg: Power button was clicked in the rating dialog.

				# If the background scraping has not finished yet, show the scraping dialog of the current scrape process.
				# This should not happen often, but can happen if the device is really slow, not able to finish the scrape in 10 minutes, or if the user skips to the end of the video (eg: 10 seconds before the end of the video).
				status = self.core.propertyStatus()
				if not status == self.core.StatusFinished and not not status == self.core.StatusFinalize:
					self.core.propertySilentSet(self.core.SilentInactive)
				else:
					self.core.propertySilentSet(self.core.SilentCancel)
					tools.System.executePlugin(action = 'scrape', parameters = {
						'media' : self.media,
						'binge' : tools.Binge.ModeContinue,
						'title' : self.bingeMetadata['title'],
						'tvshowtitle' : self.bingeMetadata['tvshowtitle'],
						'year' : self.bingeMetadata['year'],
						'imdb' : self.bingeMetadata['imdb'],
						'tvdb' : self.bingeMetadata['tvdb'],
						'trakt' : self.bingeMetadata['trakt'],
						'season' : self.bingeMetadata['season'],
						'episode' : self.bingeMetadata['episode'],
						'premiered' : self.bingeMetadata['premiered'],
						'metadata' : tools.Converter.jsonTo(self.bingeMetadata),
						'autopack' : self.autopack,
					})
					if not self.interactBackground and self.bingeContinue: interface.Loader.show()
		except: tools.Logger.error()

	def _bingeSuppress(self):
		count = 0
		while count < 100:
			id = window.Window.current()
			# Trakt addon crashes if it shows the rating dialog, but then gets closed forcefully by Gaia.
			# Trakt addon then has to be restarted manually (disabled and re-enabled), or Kodi has to be restarted.
			# The user either has to disable the rating dialog in Trakt's settings, or set Gaia's "activity.binge.suppress" setting to 0 or 1.
			if id > window.Window.IdMaximum and not window.Window.currentGaia() and (not self.bingeSuppress == 1 or not window.Window.currentTraktRating()):
				interface.Dialog.close(id)
				break
			count += 1
			tools.Time.sleep(0.1)

	def _bingeCancel(self):
		if self.binge:
			# Close not cancel.
			if self.bingeDialogFull: window.WindowBingeFull.close()
			elif self.bingeDialogOverlay: window.WindowBingeOverlay.close()
			elif self.bingeDialogButton: window.WindowBingeButton.close()

			# If we stop playback in the middle (while the background scrape of the next episode is already done), the stream window of the NEXT episode is shown on "reload".
			# By setting this status, the stream window of the current unfinished episode is shown instead.
			if not self.core.propertyStatus() == self.core.StatusCancel and self.timeProgress < self.playbackEnd and self.status == Player.StatusStopped: self.core.propertyStatusSet(self.core.StatusCancel)

	def _closeFailure(self):
		# Close Kodi's "Playback Failed" dialog.

		# Do not check if the dialog is open first, since other dialogs (eg: Gaia stream connection dialog) might pop up on top, and then Kodi shows that dialog ID as being opened.
		#if window.Window.currentDialog(id = window.Window.IdWindowOk):
		#	window.Window.close(id = window.Window.IdWindowOk)

		window.Window.close(id = window.Window.IdWindowOk)

	def _errorId(self, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, time = False):
		id = []
		if not imdb is None and not imdb == '' and not imdb == '0': id.append(imdb)
		elif not tmdb is None and not tmdb == '' and not tmdb == '0': id.append(tmdb)
		elif not tvdb is None and not tvdb == '' and not tvdb == '0': id.append(tvdb)
		elif not trakt is None and not trakt == '' and not trakt == '0': id.append(trakt)
		if season: id.append(season)
		if episode: id.append(episode)
		if time: id.append(tools.Time.timestamp())
		return tools.Hash.sha1('_'.join([str(i) for i in id]))

	def _errorLog(self, finish = False):
		try:
			if self._errorSeparator: tools.Logger.log(self._errorSeparator)
			if finish: return
		except: pass

		id = self._errorId(imdb = self.idImdb, tmdb = self.idTmdb, tvdb = self.idTvdb, trakt = self.idTrakt, season = self.season, episode = self.episode, time = True) # Add time to always make unique.
		start = '[PLAYBACK %s /]' % id
		end = '[/ PLAYBACK %s]' % id

		self._errorLast = None
		self._errorSeparator = end
		self._errorExpression = '%s(.*?)(?:$|%s)' % (start.replace('[', '\[').replace(']', '\]').replace(' ', '\s').replace('/', '\/'), end.replace('[', '\[').replace(']', '\]').replace(' ', '\s').replace('/', '\/'))

		tools.Logger.log(start)

	def _errorCheck(self, force = False):
		# Kodi's internal player CURL can fail (eg: HTTP timeouts, HTTP errors, Cloudflare, etc).
		# These errors are not detectable in Python. None of the player functions, or even onPlayBackError(), give any indication to these kinds of errors.
		# The only way to detect them seems to be to read/process the log file.
		#	ERROR <general>: OpenDemuxStream - Error creating demuxer
		#	INFO <general>: CVideoPlayer::OnExit()
		#	INFO <general>: CVideoPlayer::CloseFile()
		#	INFO <general>: VideoPlayer: waiting for threads to exit
		#	INFO <general>: VideoPlayer: finished waiting
		# Or:
		#	VideoPlayer::OpenFile: https://somelink.com
		#	ERROR <general>: CCurlFile::Stat - Failed: Timeout was reached(28) for https://somelink.com
		#	INFO <general>: Creating InputStream
		#	ERROR <general>: CCurlFile::FillBuffer - Failed: Timeout was reached(28)
		#	ERROR <general>: CCurlFile::Open failed with code 0 for https://somelink.com:
		#	ERROR <general>: CCurlFile::Exists - Failed: Timeout was reached(28) for https://somelink.com/VIDEO_TS.IFO
		#	ERROR <general>: CCurlFile::Exists - Failed: Timeout was reached(28) for https://somelink.com/VIDEO_TS/VIDEO_TS.IFO
		#	ERROR <general>: CCurlFile::FillBuffer - Failed: Timeout was reached(28)
		#	ERROR <general>: CCurlFile::Open failed with code 0 for https://somelink.com:
		#	ERROR <general>: CFileCache::Open - <https://somelink.com> failed to open
		#	ERROR <general>: CVideoPlayer::OpenInputStream - error opening [https://somelink.com]
		#	INFO <general>: CVideoPlayer::OnExit()
		#	WARNING <general>: CDVDMessageQueue(player)::Put MSGQ_NOT_INITIALIZED
		#	INFO <general>: CVideoPlayer::CloseFile()
		#	INFO <general>: VideoPlayer: waiting for threads to exit
		#	INFO <general>: VideoPlayer: finished waiting

		try:
			current = tools.Time.timestamp() # Only check every few seconds, otherwise there is too much disk I/O.
			if force or not self._errorLast or (current - self._errorLast) >= 5:
				self._errorLast = current

				data = tools.Logger.data()
				if data:
					data = tools.Regex.extract(data = data, expression = self._errorExpression, flags = tools.Regex.FlagAllLines)
					if data: return tools.Regex.match(data = data, expression = 'VideoPlayer::OnExit')

		except: tools.Logger.error()
		return False

	def isVisible(self):
		return window.Window.visible(window.Window.IdWindowPlayer) or window.Window.visible(window.Window.IdWindowPlayerFull)

	def isPlayback(self, started = False):
		# Kodi often starts playback where isPlaying() is true and isPlayingVideo() is false, since the video loading is still in progress, whereas the play is already started.
		try: return self.isPlaying() and self.isPlayingVideo() and self.getTime() >= 0 and (not started or self.statusStarted)
		except: False

	def isBusy(self):
		return self.isPlayingVideo() and not tools.System.aborted()

	def keepPlaybackWait(self, title, message, status, substatus1, substatus2, timeout):
		wasPlaying = False
		delay = 0.3
		iterations = int(timeout / delay)
		for i in range(0, iterations):
			self._closeFailure()

			if self.isPlaying(): wasPlaying = True
			elif wasPlaying: break # Was playing, but not anymore. This is when the video playback fails. Kodi for some reason does not trigger the onPlayBackError signal.

			if self.isPlayback() or self.error: break

			# Kodi player failed with its cURL timing out or not being able to resolve the domain of the URL.
			if self.status == Player.StatusStopped or self.status == Player.StatusEnded: break

			# Kodi sometimes does not fire the onPlayBackStopped/onPlayBackEnded events, causing the cleanup not to execute (eg: delete debrid file, reloading stream window, etc).
			# Seems to happen if the playback is manually stopped a few seconds after playback started.
			# This seems to be caused by deadlock (a Lock, from eg the Database class, was not released). This has been fixed, and this problem should not occur anymore.
			# UPDATE:
			#	The reason for these events not firing, is because the code in this file is continously executing, not giving Kodi a chance to execute its own code (aka calling the callback functions) in between.
			#	To test this hypothesis: If the sleep delay in this function is increased to something large (eg: 5 secs), allowing Kodi some time to execute, these events are fired correctly.
			#	The real solution seems to be not to use "thread.join()" for the thread calling this function, but instead using a busy-wait loop checking every few ms if the thread is still alive.
			#	To test these failing playback, try setting self.url at the start to an invalid domain name (quick fail), or play a Youtube video through RealDebrid which always seems to cause a cURL timeout (slow fail, since Kodi's player has a timeout of 30 seconds).
			# If the problem reoccurs in the future, maybe it is better to use the threading option below, but start the thread globally before calling keepPlaybackAlive(), rather than calling it in this function.
			# Using _errorCheck() is inefficient, constantly reading from file.
			'''if self._errorCheck():
				if not self.status == Player.StatusStopped and not self.status == Player.StatusEnded: self.onPlayBackStopped()
				break'''
			'''def keepPlaybackCheck():
				while True:
					if tools.System.aborted() or (self.status == Player.StatusPlaying and not self.isPlaying()) or (self.status == Player.StatusStopped or self.status == Player.StatusEnded):
						if not self.status == Player.StatusStopped and not self.status == Player.StatusEnded: self.onPlayBackStopped()
						break
					tools.Time.sleep(0.5)
			Pool.thread(target = keepPlaybackCheck,start = True)'''

			if self.download is None:
				if self.core.progressPlaybackCanceled(): break
				interface.Loader.hide() # Busy icons pops up again in Kodi 18.

				# Only 30% the progress, since the other 70% is from sources __init__.py.
				# Add 5% (70% to 75%) to show some progress from __init__.py.
				# Only increase up to 24% to have a max value of 99%.
				progress = 75 + int((i / float(iterations)) * 24)

				self.core.progressPlaybackUpdate(progress = progress, title = title, message = message, status = status, substatus1 = substatus1, substatus2 = substatus2, total = self.retryTotal, remaining = self.retryRemaining, force = True)
			else:
				self._downloadCheck()
			tools.Time.sleep(delay)

	def keepPlaybackProgress(self, initialize = False, update = False, progress = 75):
		title = interface.Translation.string(33451)
		status = interface.Translation.string(33460)
		substatus1 = interface.Translation.string(35474)
		substatus2 = interface.Translation.string(35303)
		message = self.retryMessage
		if not message == '':
			if interface.Core.background() and not self.core.progressPlaybackEnabled():
				message += ' - '
			else:
				message += '.' + interface.Format.newline()
		message += status

		if initialize: self.core.progressPlaybackInitialize(title = title, message = message, metadata = self.metadata)
		if update: self.core.progressPlaybackUpdate(progress = progress, title = title, message = message, status = status, substatus1 = substatus1, substatus2 = substatus2, total = None if initialize else self.retryTotal, remaining = None if initialize else self.retryRemaining, force = True)

		return title, status, substatus1, substatus2, message

	def keepPlaybackAlive(self):
		try:
			self._downloadCheck()

			title, status, substatus1, substatus2, message = self.keepPlaybackProgress()
			interface.Loader.hide()

			timeout = tools.Settings.getCustom('playback.time.wait')
			if not timeout: timeout = 300 # Technically unlimited.

			# Use a thread for Kodi 18, since the player freezes for a few seconds before starting playback.
			thread = Pool.thread(target = self.keepPlaybackWait, args = (title, message, status, substatus1, substatus2, timeout), start = True)

			# NB: Do not join(), but use a busy-wait instead.
			# Check the comment in keepPlaybackWait() for more info.
			#thread.join()
			self.join(thread)

			if self.core.progressPlaybackCanceled():
				self.core.progressPlaybackClose()
				self.stop()
				self._debridClear()
				return True

			# Only show the notification if the player is not able to load the file at all.
			if not self.isPlayback():
				self.core.progressPlaybackUpdate(progress = 100, title = title, message = message, status = status, substatus1 = substatus1, substatus2 = substatus2)
				if self.retryRemaining > 0: tools.Time.sleep(self.retryDelay)
				self.stop()
				self.core.progressPlaybackUpdate(progress = 100, message = '', status = None, force = True) # Must be set to 100 for background dialog, otherwise it shows up in a later dialog.
				return False

			if self.resumeTime: self.resume(self.resumeTime, offset = True)

			self.core.progressPlaybackUpdate(progress = 100, title = title, message = message, status = status, substatus1 = substatus1, substatus2 = substatus2)

			# Important to close here, otherwise the playback window stays open (although invisible), causing a dangling Python process.
			# We previously closed it in the Player destructor, but that interfered with the binge process, often canceling the next episode's playback.
			# Check the destructor for more details.
			# NB: Do not close immediately, otherwise if we resume playback, the WindowStreams shows briefly before the Kodi player window shows.
			# If Kodi playback starts, it will in any case show on top of the window, so there is no urgency in closing it.
			def _close():
				tools.Time.sleep(3)
				if self.isBusy(): self.core.progressPlaybackClose()
			Pool.thread(target = _close, start = True)

			addLibrary = tools.Settings.getBoolean('library.general.watched')

			streamsHas = False
			visibleWas = False

			if self.vpnMonitor: Vpn.killPlayback()

			self.detailsRefresh()

			while self.isBusy():
				self.timeTotal = self.getTotalTime()
				self.timeCurrent = self.getTime()
				try: self.timeProgress = self.timeCurrent / float(self.timeTotal)
				except: pass # self.timeTotal is 0.

				# On some hosters (eg: VidLox), if videos are taken down, they replace it with a short 404 video clip.
				# If the video clip is below 30 seconds, assume it is not a valid one, and do not mark progress, binge watch, etc.
				if self.timeTotal and self.timeTotal > 30:
					try:
						if self.timeProgress >= self.playbackEnd and not self.playbackWatched:
							try: orionoid.Orionoid().streamVote(idItem = self.source['stream'].idOrionItem(), idStream = self.source['stream'].idOrionStream(), vote = orionoid.Orionoid.VoteUp, automatic = True)
							except: pass
							self.playbackWatched = True
							if addLibrary: library.Library(media = self.media).add(title = self.title, year = self.year, imdb = self.idImdb, tmdb = self.idTmdb, tvdb = self.idTvdb, trakt = self.idTrakt, season = self.season, episode = self.episode, metadata = self.metadata)
							self._updateLibrary()
					except: tools.Logger.error()
					self.progressUpdate()
					self._bingeCheck()

				self.streamSubtitle()

				if self.navigationStreamsSpecial:
					for i in range(4):
						visible = self.isVisible()
						playback = self.isPlayback()
						if not visibleWas and visible: visibleWas = True
						if not streamsHas and playback and visibleWas and not visible:
							streamsHas = True
							if self.statusStarted and not self.error: self._showStreams() # Do not do this (eg reload stream window) if playback failed.
						elif streamsHas and visible:
							streamsHas = False
							interface.Dialog.closeAll()
						if not self.download is None: self._downloadCheck()
						if i % 2 == 0: self.streamSubtitle()
						tools.Time.sleep(1)
				else:
					if self.download is None:
						tools.Time.sleep(2)
					else:
						for i in range(4):
							self._downloadCheck()
							tools.Time.sleep(0.5)

			return True
		except:
			tools.Logger.error()
			return False

	def progressRetrieve(self):
		if self.metadata: # Do not do for exact searches.
			if self.playback.settingsHistoryEnabled() and self.playback.settingsHistoryProgressResume() > 0: self.progressThread = Pool.thread(target = self._progressRetrieve, start = True)
			else: self.progress = 0
		else: self.progress = 0

	def _progressRetrieve(self):
		# Use Playback.AdjustSettings. Check playback.py -> progress() for more info.
		self.progress = self.playback.progress(media = self.media, imdb = self.idImdb, tmdb = self.idTmdb, tvdb = self.idTvdb, trakt = self.idTrakt, season = self.season, episode = self.episode, adjust = self.playback.AdjustInternal)

	def progressUpdate(self, action = None):
		if self.metadata: # Do not do for exact searches.
			if self.progressInitialized and not self.progressBusy:
				if action is None:
					if self.status == Player.StatusPlaying:
						action = Playback.ActionStart
					elif self.status == Player.StatusPaused:
						action = Playback.ActionPause
					elif self.status == Player.StatusStopped or self.status == Player.StatusEnded:
						# NB: When a title is played for the first time and scrobble is stopped (aka the "stop" action is submitted to Trakt's API), the progress status can later be retrieved and playback resumed.
						# However, when a title was already watched, and the user watches it again, and then scrobble is stopped, the progress is not returned by "sync/playback".
						# When scrobble is paused instead of stopped, the correct progress can be retrieved through "sync/playback".
						# Hence, only stop scrobble if the playback actually finished, and not just when the user hits the stop button in Kodi's player.
						# This is not a huge issue, since the playback progress can still be retrieved from the local database, but it is still better to get the progress from Trakt, in case the user watched it on a different device.
						if self.playbackWatched: action = Playback.ActionStop
						else: action = Playback.ActionFinish

				# NB: Check the resume progress.
				# The following scenario:
				#	1. The user has a previous progress saved at 60%. A day later the user resumes playback.
				#	2. Right after resuming, scrobbeling is set at around 0-1% before Kodi actually changes the position and the new scrobbeling progress is submitted.
				#	3. If playback fails or the users stops playback BEFORE Kodi could fully resume, scrobbeling would have reset to 0% before being able to update it to the actual resume progress.
				# Hence, the progress will be lost in such a case. Instead wait for the playback to resume before updating the scrobbeling progress.
				if action and (not self.progress or self.progress < 0.5 or self.timeProgress > self.progress or self.timeCurrent > 5):
					self.playback.update(action = action, current = self.timeCurrent, duration = self.timeTotal, media = self.media, imdb = self.idImdb, tmdb = self.idTmdb, tvdb = self.idTvdb, trakt = self.idTrakt, season = self.season, episode = self.episode, metadata = self.metadata)

	def progressInitialize(self):
		locked = False
		try:
			try:
				if self.timeTotal == 0: self.timeTotal = self.getTotalTime()
				if self.timeCurrent == 0: self.timeCurrent = self.getTime()
			except:
				# When Kodi's player is not playing anything, it throws an exception when calling self.getTotalTime()
				return

			if not self.progressInitialized:
				self.progressInitialized = True
				self.progressBusy = True
				if self.progressThread:
					self.join(self.progressThread)
					self.progressThread = None

				if not self.resumeTime and self.progress > 0:
					if self.timeTotal > 0:
						paused = False
						seconds = self.progress * self.timeTotal
						if seconds > 0:
							if self.playback.settingsHistoryEnabled():
								resume = self.playback.settingsHistoryProgressResume()
								if resume == 4:
									if self.progress <= 0.02 or self.progress >= 0.98:
										resume = -1
										seconds = 0
									elif self.progress <= 0.1 or self.progress >= 0.9:
										resume = 3
									else:
										resume = -1

								if resume >= 2:
									paused = True
									timeMinutes, timeSeconds = divmod(float(seconds), 60)
									timeHours, timeMinutes = divmod(timeMinutes, 60)
									label = '%02d:%02d:%02d' % (timeHours, timeMinutes, timeSeconds)
									label = interface.Translation.string(32502) % label
									if resume == 3: label += ' ' + interface.Translation.string(34372)

									# Lock, so that the subtitle dialog/paause and the resume dialog/pause do not intefer while running in threads.
									self.playbackLock.acquire()
									locked = True

									Streamer.playerPause()
									choice = interface.Dialog.option(title = 32344, message = label, labelConfirm = 32501, labelDeny = 32503, timeout = 10000 if resume >= 3 else None)
									if choice: seconds = 0

						if seconds > 0:
							self.resume(seconds, offset = True)
						if paused:
							Streamer.playerUnpause()
							try:
								if locked: self.playbackLock.release()
							except: pass
							tools.Time.sleep(0.1) # Otherwise the onPlaybackResumed() can fire AFTER self.progressBusy is reset below.
						else:
							if locked:
								try:
									if locked: self.playbackLock.release()
								except: pass

				self.progressBusy = False

			self.progressUpdate()
		finally:
			try:
				if locked: self.playbackLock.release()
			except: pass

	def _bufferDetect(self, duration = 5, setting = None):
		# Do not start the threads immediately, since we want to start them as close together as possible, since we want to get readings from the same time interval.
		try:
			busy = self.bufferLock.locked()
			self.bufferLock.acquire()
			if not busy: # If this is called while the stats are still updating, just wait and return, and do not re-run the detection.
				self._bufferDetectAll(duration = duration)

				# Sometimes Kodi returns 0bps, mostly right at the start of playback or resume.
				# Try measuring the speeds a second time.
				# Only do this up to 10 times, since if there is a permanent failure reading a speed, we do not want to always delay the notification by running another detection.
				if self.bufferFailures < 10:
					self.bufferFailures += 1
					rerun = False
					bufferNetwork = self.bufferNetwork is not None and self.bufferNetwork == 0
					bufferKodi = self.bufferKodi is not None and self.bufferKodi == 0
					if setting == 0 or setting == 1: rerun = bufferNetwork and bufferKodi
					elif setting == 2: rerun = bufferNetwork or bufferKodi
					if rerun: self._bufferDetectAll(duration = duration)

			message = []
			if setting == 0:
				label = self._bufferLabelNetwork()
				if label: message.append(label)
				else: message.append(self._bufferLabelKodi())
			elif setting == 1:
				message.append(self._bufferLabelNeeded())
				label = self._bufferLabelNetwork()
				if label: message.append(label)
				else: message.append(self._bufferLabelKodi())
			elif setting == 2:
				message.append(self._bufferLabelNeeded())
				message.append(self._bufferLabelNetwork())
				message.append(self._bufferLabelKodi())
			return interface.Format.iconJoin([i for i in message if i])
		except:
			tools.Logger.error()
			return None
		finally:
			try: self.bufferLock.release()
			except: pass

	def _bufferDetectAll(self, duration = 5):
		self.bufferKodi = None
		self.bufferNetwork = None
		threadNetwork = Pool.thread(target = self._bufferDetectNetwork, kwargs = {'duration' : duration})
		threadKodi = Pool.thread(target = self._bufferDetectKodi, kwargs = {'duration' : duration})
		threadNetwork.start()
		threadKodi.start()
		self.join(threadNetwork)
		self.join(threadKodi)

	def _bufferDetectNetwork(self, duration = 5):
		try: self.bufferNetwork = tools.Hardware.detectNetwork(duration = duration)['download']
		except: tools.Logger.error()

	def _bufferDetectKodi(self, duration = 5):
		try:
			size = self.source['stream'].fileSize()
			if size:
				player = Streamer.player()

				# In case threads are interleaved, get the real elapsed time to also include sleep time.
				timer = tools.Time(mode = tools.Time.ModeSystem, start = True)

				startx = player.property('percentage')
				start = player.property('cachepercentage')
				tools.Time.sleep(duration)
				end = player.property('cachepercentage')

				duration = timer.elapsed(milliseconds = True) / 1000.0
				self.bufferKodi = max(0, (size * ((end - start) / 100.0)) / duration) # Can be less than 0 at the end of playback or changing position.
		except: tools.Logger.error()

	def _bufferBits(self, value):
		if not value: return None
		if value < 0: value = 0
		from lib.modules.convert import ConverterSpeed
		return ConverterSpeed(value, unit = ConverterSpeed.Bit).value(unit = ConverterSpeed.Byte)

	def _bufferLabel(self, label, value, byte = True):
		if value is None: return None
		if value < 0: value = 0
		from lib.modules.convert import ConverterSpeed
		value = ConverterSpeed(value, unit = ConverterSpeed.Byte if byte else ConverterSpeed.Bit).stringOptimal(unit = ConverterSpeed.Bit, notation = ConverterSpeed.SpeedLetter).title()
		return '%s: %s' % (interface.Translation.string(label), value)

	def _bufferLabelNeeded(self):
		return self._bufferLabel(label = 35417, value = self.bufferNeeded)

	def _bufferLabelNetwork(self):
		return self._bufferLabel(label = 33719, value = self.bufferNetwork)

	def _bufferLabelKodi(self):
		return self._bufferLabel(label = 33170, value = self.bufferKodi)

	def _bufferReset(self):
		self.bufferPrevious = 0
		self.bufferDuration = tools.Time.timestamp()

	def bufferMonitor(self):
		if self.bufferThread is None and tools.Settings.getBoolean('playback.buffer.monitor'):
			self.bufferThread = Pool.thread(target = self._bufferMonitor, start = True)

	def _bufferMonitor(self):
		# There are 3 methods to detect buffering:
		# 1. Detect the notification popup from Kodi that says "Source too slow".
		#	 The problems with this method:
		#		The notification only pops up close to the end of the buffering (+- 20 seconds after buffering started).
		#		There is not way to read the label from the notification using xbmcgui.Window(10107).getControl(401). The control is notr a ControlLabel, but instead a ControlFadeLabel, which does not have a getLabel() function.
		# 2. Check the Kodi log for certain statements:
		#		OutputPicture - timeout waiting for buffer
		#		CVideoPlayerAudio::Process - stream stalled
		#	 The problems with this method:
		#		Requires constant disk I/O which might cause problems on devices with a slow disk.
		#		When buffering happens right at the start of playback, sometimes (rare cases) none of the above statements are printed to the log. Subsequent buffering should be fine.
		# 3. Use the Kodi RPC or info label to get the "cachepercentage".
		#	 Kodi does not pause playback during buffering. So if the player is still in "play" state and the playback progress is not increasing, assume buffering is happening.
		#	 Checking these values is done every 1 second. This should be enough time for the "percentage" progress to increase.
		#	 This seems to always work. Not sure if there are exceptions.

		player = Streamer.player()

		previousCache = 0
		previousPlayback = 0
		previousBuffer = False

		progressCache = 0
		progressPlayback = 0

		settingsLevel = tools.Settings.getInteger('playback.buffer.monitor.notification')
		settingsDelay = tools.Settings.getCustom('playback.buffer.monitor.delay')

		self._bufferReset()
		self.buffer = False
		while self.isBusy():
			if self.status == Player.StatusPlaying:
				progressCache = player.property('cachepercentage')
				progressPlayback = player.property('percentage')
				if not progressCache == previousCache and progressPlayback == previousPlayback:
					# Sometimes right after playback starts, or right after changing the playback position, the percentage readings indicate that the player is buffering.
					# Although watching the video there does not seem to be any buffering and the video plays at a normal speed.
					# Wait a short while and take the readings again, trying to eliminate these false positives.
					# If these false positives still happen from time to time, maybe the delay should be increassed slightly, eg to 1-2 seconds.
					tools.Time.sleep(0.5)
					progressCache = player.property('cachepercentage')
					progressPlayback = player.property('percentage')
					if not progressCache == previousCache and progressPlayback == previousPlayback:
						self.buffer = True
						time = tools.Time.timestamp()
						if (not settingsDelay and not previousBuffer) or (settingsDelay and (time - self.bufferPrevious > settingsDelay)):
							self.bufferPrevious = time
							message = self._bufferDetect(setting = settingsLevel)
							if not message: break

							# Check status again. Playback might have resumed while measuring the speed.
							if self.status == Player.StatusPlaying:
								# During the first 30 seconds of playback or resume, only show the notification if the current speed is not 0bps and not greater than the needed speed.
								# After the first 30 seconds, always show the notification.
								bufferNeeded = self.bufferNeeded if self.bufferNeeded else 0
								bufferCurrent = 0
								if not self.bufferNetwork is None: bufferCurrent = self.bufferNetwork
								elif not self.bufferKodi is None: bufferCurrent = self.bufferKodi
								if not((tools.Time.timestamp() - self.bufferDuration) < 30 and (bufferCurrent == 0 or bufferCurrent > bufferNeeded)):
									interface.Dialog.notification(title = 33368, message = message, icon = interface.Dialog.IconWarning, duplicates = True, time = 8000)

						previousBuffer = True
					else:
						self.buffer = False
						previousBuffer = False
				else:
					self.buffer = False
					previousBuffer = False

				previousCache = progressCache
				previousPlayback = progressPlayback

			tools.Time.sleep(1)

	def _updateLibrary(self):
		if self.kodi and not self.libraryUpdated:
			try:
				self.libraryUpdated = True

				try: playcount = self.kodi['playcount'] + 1
				except: playcount = 1

				if self.mediaFilm: tools.System.executeJson(method = 'VideoLibrary.SetMovieDetails', parameters = {'movieid' : str(self.kodi['movieid']), 'playcount' : playcount})
				elif self.mediaSerie: tools.System.executeJson(method = 'VideoLibrary.SetEpisodeDetails', parameters = {'episodeid' : str(self.kodi['episodeid']), 'playcount' : playcount})

				interface.Directory.refresh()
			except:
				tools.Logger.error()

	def streamSelect(self):
		locked = False
		try:
			enabled = tools.Settings.getBoolean('playback.general.pause')
			if enabled:
				self.playbackLock.acquire()
				locked = True
				Streamer.playerPause()

			Audio.select(metadata = self.metadata) # Must be before subtitles, since the subtitles might need the current audio stream/language.
			thread = Subtitle.select(name = self.name, imdb = self.idImdb, tmdb = self.idTmdb, title = self.title, year = self.year, season = self.seasonString, episode = self.episodeString, source = self.source['stream'], lock = None if locked else self.playbackLock)

			if enabled:
				if thread: thread.join()
				Streamer.playerUnpause()
		finally:
			try:
				if locked: self.playbackLock.release()
			except: pass

	def streamSubtitle(self):
		Subtitle.internal(name = self.name, imdb = self.idImdb, tmdb = self.idTmdb, title = self.title, year = self.year, season = self.seasonString, episode = self.episodeString, source = self.source['stream'])

	def streamStop(self):
		Subtitle.stop()

	def resume(self, seconds, offset = False):
		self.resumedTime = max(0, seconds - (Player.ResumeTime if offset else 0))
		self.seekTime(self.resumedTime)

	def playbackInitialize(self):
		if not self.playbackInitialized:
			self.playbackInitialized = True
			for i in range(0, 1200):
				# Check "started" as well, otherwise the playback window is closed too quickly and the background menus are visible for a second.
				# It seems that Kodi fixed the issue that onAvStarted() was not called, should now be correctly executed.
				if self.isPlayback(started = True) or self.status == Player.StatusPaused: break
				tools.Time.sleep(0.05)
			interface.Dialog.closeAll()

			# Make sure progressInitialize() and streamSelect() are not executed at the same time.
			# Otherise the resume and subtitles dialog might pop up at the same time.
			#self.progressInitialize()
			#self.streamSelect()
			# Update: We now do these in threads. They use a lock to prevent the dialogs/pause/resume from these functions to intefer.
			# This is important for anime, where the dialog often starts in the 1st second of the video.
			# If selecting the subtitles takes too long (when executing sequentially), the first few sentences might be missed.
			# streamSelect() does pause playback until the subtitles were selected, but it might take too long before it is paused while the dialog already started.
			threads = [
				Pool.thread(target = self.streamSelect, start = True),
				Pool.thread(target = self.progressInitialize, start = True),
			]
			[thread.join() for thread in threads]

			# Only do this after the streamSelect() and progressInitialize().
			# Otherwise the Skip button might show over the resume/subtitle dialogs making them unclickable until the Skip button ius canceled.
			if self.mediaSerie: Chapter.select(resume = self.resumedTime)

			# Only start this AFTER the resume feature and subtitle dialogs, since they pause playback which is incorrectly detected as buffering.
			self.bufferMonitor()

	def playbackFinalize(self):
		if not self.playbackFinalized:
			self.playbackFinalized = True

			self.streamStop()

			# When the binge overlay window starts (either hidden or if shown and the user hides it mannually), without clicking the Continue/Cancel buttons.
			# If playback is stopped from the Kore app while the binge window is hidden, after playback finished, one can still pull down the binge window.
			# Forcefully close the window if playback stopped.
			if self.bingeDialogOverlay: window.WindowBingeOverlay.close()
			elif self.bingeDialogButton: window.WindowBingeButton.close()

			# Do not do this (eg reload stream window) if playback failed.
			if self.statusStarted and not self.error:
				self.progressUpdate()

				# Must be BEFORE _showStreams() and _bingePlay(), since we want to wait for the rating dialog to close before we continue.
				# Otherwise the rating dialog might be closed or hidden underneath the stream window.
				self.interact()

				continued = self._showStreams()
				if self.binge:
					if self.bingePlay:
						continued = True
						self._bingePlay()
					elif self.bingeDialogNone or self.bingeDialogFull:
						continued = True
						self._bingeShow()
					else:
						if not self.bingeContinue:
							self.core.propertyStatusSet(self.core.StatusCancel)
							self.core.propertySilentSet(self.core.SilentActive)
						elif self.core.propertySilent() == self.core.SilentInteract:
							# If playback was stopped without picking a binge continue/cancel option.
							self.core.propertySilentSet(self.core.SilentInactive)

				# Refresh the directory to show new progress or watched status.
				# Do not refresh if we are binging, otherwise the container refresh causes a loader to pop up for a short time.
				if not continued and not self.bingeContinue: interface.Directory.refresh(position = True, loader = False, wait = False)

				if not self.bingeContinue: window.WindowBackground.close()

	def onPlayBackStarted(self):
		# NB: It seems that Kodi only executes callbacks if the previous callback is done executing.
		# If within a callback, we execute a large function that itself relies on the status/data of another callback, it does not seem to work.
		# It then looks like the callbacks never get executed.
		# This might be the problem for various other parts of ther Player code, eg: the last few statements in run().
		# Starting a thread seems to solve the problem.
		self.status = Player.StatusPlaying
		tools.Logger.log('Playback Started')
		Pool.thread(target = self._onPlayBackStarted, start = True)

	def _onPlayBackStarted(self):
		interface.Loader.hide()
		self.statusDone = Player.StatusPlaying

	def onPlayBackPaused(self):
		self.status = Player.StatusPaused
		tools.Logger.log('Playback Paused')
		Pool.thread(target = self._onPlayBackPaused, start = True)

	def _onPlayBackPaused(self):
		self.progressUpdate()
		self.statusDone = Player.StatusPaused

	def onPlayBackResumed(self):
		self.status = Player.StatusPlaying
		tools.Logger.log('Playback Resumed')
		Pool.thread(target = self._onPlayBackResumed, start = True)

	def _onPlayBackResumed(self):
		self.progressUpdate()
		self.statusDone = Player.StatusPlaying

	def onPlayBackStopped(self):
		self.status = Player.StatusStopped
		tools.Logger.log('Playback Stopped')
		Pool.thread(target = self._onPlayBackStopped, start = True)

	def _onPlayBackStopped(self):
		# Show here already to reduce the period between playback end and a window popping up.
		# Also do this if rating/continue was disabled and there is no binging.
		# Only show if finished watching. Otherwise the window is shown if the cancel button was clicked in the playback window (that cancels the next episode before it even starts).
		if self.playbackWatched and not self.interactBackground and self.interactSpecial:
			special1 = self.interactRating or self.interactContinue
			special2 = self.core.navigationPlaybackSpecial and self.bingeContinue
			if special1 or special2:
				self.interactBackground = True
				window.WindowBackground.show(metadata = self.metadata, logo = True)

		self._interactObserverStop()
		self._bingeCancel()
		self._downloadStop()
		self._debridClear()
		self._downloadClear()

		# Only do this if the video actually played and did not stop because of failure or timeout.
		if self.statusStarted: self.playbackFinalize()
		self.statusDone = Player.StatusStopped

	def onPlayBackEnded(self):
		self.status = Player.StatusEnded
		tools.Logger.log('Playback Ended')
		Pool.thread(target = self._onPlayBackEnded, start = True)

	def _onPlayBackEnded(self):
		self.onPlayBackStopped()
		self.statusDone = Player.StatusEnded

	def onPlayBackError(self):
		tools.Logger.log('Playback Error')
		self.error = True
		#Pool.thread(target = self._onPlayBackError, start = True)

	def _onPlayBackError(self):
		pass

	def onAVStarted(self):
		self.statusStarted = True
		tools.Logger.log('Playback AV Started')
		Pool.thread(target = self._onAVStarted, start = True)

	def _onAVStarted(self):
		# Do this here and not in onPlayBackStarted(), since onPlayBackStarted() is called even if the video doess not play (eg: link times out).
		self.playbackInitialize()

	def onAVChange(self):
		tools.Logger.log('Playback AV Changed')
		#Pool.thread(target = self._onAVChange, start = True)

	def _onAVChange(self):
		pass

	def onPlayBackSeek(self, time, seekOffset):
		tools.Logger.log('Playback Seek')
		Pool.thread(target = self._onPlayBackSeek, start = True)

	def _onPlayBackSeek(self):
		self._bufferReset() # Show notification again if the playback position was changed, typically leading to some buffering.
		self.progressUpdate()

	def onPlayBackSeekChapter(self, chapter):
		tools.Logger.log('Playback Seek Chapter')
		Pool.thread(target = self._onPlayBackSeekChapter, start = True)

	def _onPlayBackSeekChapter(self):
		self._bufferReset() # Show notification again if the playback position was changed, typically leading to some buffering.
		self.progressUpdate()

class Streamer(object):

	Player = None
	Status = None
	Language = None

	# Must correspond with settings.xml.
	LanguageAutomatic = 0
	LanguageCustom = 1

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		Streamer.Player = None
		Streamer.Status = None
		if settings: Streamer.Language = None

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def id(self):
		return self.name().lower()

	@classmethod
	def name(self):
		return self.__name__

	@classmethod
	def player(self):
		if Streamer.Player is None: Streamer.Player = interface.Player()
		return Streamer.Player

	@classmethod
	def playerPause(self, wait = False):
		# NB: For some reasons, the callbacks from interface.Player are never executed in playerPause() and playerUnpause().
		# Use the status from player.py Player to solve the issue.
		#player = self.player()
		#if not player.status() == interface.Player.StatusPaused: player.pause()

		player = Player.instance()
		Streamer.Status = player.status

		#if not player.status == Player.StatusPaused:
		if not Streamer.Status == Player.StatusPaused:
			player.pause()
			Streamer.Status = Player.StatusPaused
			if wait: self.playerWait(status = Player.StatusPaused)

	@classmethod
	def playerUnpause(self, wait = False):
		# NB: For some reasons, the callbacks from interface.Player are never executed in playerPause() and playerUnpause().
		# Use the status from player.py Player to solve the issue.
		#player = self.player()
		#if player.status() == interface.Player.StatusPaused: player.pause()

		player = Player.instance()
		Streamer.Status = player.status

		#if player.status == Player.StatusPaused:
		if Streamer.Status == Player.StatusPaused:
			player.pause()
			Streamer.Status = Player.StatusPlaying
			if wait: self.playerWait(status = Player.StatusPlaying)

	@classmethod
	def playerStatus(self, status = None):
		if not status is None: Streamer.Status = status
		return Streamer.Status

	@classmethod
	def playerWait(self, status):
		# It can take a few 100 ms for Kodi to actually pause/unpause the playback and execute the callbacks that change the status.
		# Without waiting, there are sporadic errors where it is playing while the subtitles/resume dialog are showing, or it stays paused after these dialogs were closed.
		# Update: A better solution is to not wait (esepcially when pausing) and hold up the subtitle selection.
		# Instead, use an internal state here.
		# Note that this will only work if the functions of Styreamer are called directly. Calling pause() directly on the player will not update the status here.
		player = Player.instance()
		for i in range(100):
			if player.status == status: break
			tools.Time.sleep(0.01)

	@classmethod
	def streams(self, unknown = False):
		return self._streamRetrieve(retrieve = interface.Player.RetrieveAll, unknown = unknown)

	@classmethod
	def streamDefault(self, unknown = False):
		return self._streamRetrieve(retrieve = interface.Player.RetrieveDefault, unknown = unknown)

	@classmethod
	def streamCurrent(self, unknown = False):
		return self._streamRetrieve(retrieve = interface.Player.RetrieveCurrent, unknown = unknown)

	@classmethod
	def streamKnown(self, unknown = True, primary = True, secondary = True, tertiary = True):
		try:
			current = self.streamCurrent(unknown = unknown)
			if current:
				settings = self.settingsLanguage()
				if settings:
					languages = []
					if primary:
						try: languages.append(settings[0])
						except: pass
					if secondary:
						try: languages.append(settings[1])
						except: pass
					if tertiary:
						try: languages.append(settings[2])
						except: pass
					return current['language'][tools.Language.Code][tools.Language.CodeStream] in languages
		except: tools.Logger.error()
		return False

	@classmethod
	def _streamRetrieve(self, retrieve, unknown = False):
		return self._stream(player = self.player(), retrieve = retrieve, process = True, unknown = self.language() if unknown is True else unknown if unknown else None)

	@classmethod
	def log(self, message, stream = None):
		message = '[%s] %s' % (self.name().upper(), message)
		if stream:
			if tools.Tools.isArray(stream):
				if tools.Tools.isString(stream[0]): tools.Logger.log('%s: %s' % (message, ' | '.join([str(tools.Language.name(i)) for i in stream])))
				elif not 'language' in stream[0]: tools.Logger.log('%s: %s' % (message, ' | '.join([str(i[tools.Language.Name][tools.Language.NameDefault]) for i in stream])))
				else: tools.Logger.log('%s: %s' % (message, ' | '.join(['%s (%s)' % (str(i['language'][tools.Language.Name][tools.Language.NameDefault] if i['language'] else None), str(i['name'] if i['name'] else None)) for i in stream])))
			else:
				tools.Logger.log('%s: %s (%s)' % (message, str(stream['language'][tools.Language.Name][tools.Language.NameDefault] if stream['language'] else None), str(stream['name'] if stream['name'] else None)))
		else:
			if not stream is None: message + ': None'
			tools.Logger.log(message)

	@classmethod
	def language(self):
		return Streamer.Language

	@classmethod
	def languageSet(self, language):
		if language:
			if tools.Tools.isArray(language): language = language[0]
			Streamer.Language = tools.Language.language(language)

	@classmethod
	def settingsLanguage(self, code = tools.Language.CodeStream, log = False):
		result = []

		setting = 'playback.%s.language' % self.id()
		if tools.Settings.getInteger(setting) == Streamer.LanguageAutomatic: languages = tools.Language.settings()
		else: languages = tools.Language.settingsCustoms(id = setting, code = False)

		# OpenSubtitles has variations or some languages.
		# Eg: Simplified vs traditional vs bilingual Chinese.
		# Eg: Standard vs Brazilian Portuguese.
		variations = tools.Language.variations()
		for language in languages:
			result.append(language)
			for variation in variations:
				if language[tools.Language.Code][tools.Language.CodePrimary] == variation[tools.Language.Original]:
					result.append(variation)

		if log: self.log('Language preferences', [i[tools.Language.Name][tools.Language.NameDefault] for i in result])
		return [i[tools.Language.Code][code] for i in result]


class Audio(Streamer):

	# Must correspond with settings.xml.
	StreamDefault = 0
	StreamAutomatic = 1

	OriginalDisabled = 0
	OriginalLenient = 1
	OriginalStrict = 2

	@classmethod
	def _stream(self, player, retrieve, process, unknown):
		return player.audioStream(retrieve = retrieve, process = process, unknown = unknown)

	@classmethod
	def select(self, metadata = None, unknown = False):
		try:
			# In sporadic cases, the streams returned might be None.
			# This is probably because the player has not fully initialized.
			# Wait and try again.
			streams = None
			for i in range(20):
				streams = self.streams(unknown = unknown)
				if streams and streams[0]: break
				tools.Time.sleep(0.05)

			settings = self.settingsLanguage(log = not unknown)
			current = self.streamCurrent(unknown = unknown)

			if not unknown: self.log('Available streams', streams if streams else [])

			if tools.Settings.getInteger('playback.audio.stream') == Audio.StreamDefault:
				self.log('Using default stream', current)
			elif not streams:
				self.log('No audio streams detected.')
			else:
				original = None
				try:
					original = metadata['language']
					if original and not tools.Tools.isArray(original): original = [original]
					original = [tools.Language.code(i, code = tools.Language.CodeStream) for i in original]
					original = [i for i in original if i]
					self.log('Original audio language', original)
				except: pass

				originaled = None
				try:
					originaled = tools.Settings.getInteger('playback.audio.orginal')
					if not originaled:
						self.log('Ignoring original audio language', original)
						original = None
					else:
						exclude = tools.Language.settingsCustom(id = 'playback.audio.orginal.exclude', code = tools.Language.CodeStream)
						if exclude:
							try: original.remove(exclude)
							except: pass
							self.log('Excluding original audio language', [exclude])
				except: tools.Logger.error()

				best = None
				bestOriginal = False

				# First try to use the language the title was originally released in.
				# Pick any language that is in the user's settings, even if it is the secondary/tertiary language.
				# No user wants to watch dubbed content if the user can (to some extend) understand the original language.
				# Eg: If a movie is in French, but the file also contains an English audio stream: French should be used instead of English if the user has French in any of the language settings.
				if best is None and original:
					for code in original:
						if originaled == Audio.OriginalLenient or (originaled == Audio.OriginalStrict and code in settings):
							for stream in streams:
								if stream and code == stream['language'][tools.Language.Code][tools.Language.CodeStream]:
									if best is None:
										if stream['name']: # Ingore commentary audio.
											lower = stream['name'].lower()
											if not 'comment' in lower  and not 'director' in lower:
												best = stream
										else:
											best = stream
									else:
										better = False
										if stream['channels'] and best['channels']:
											if stream['channels'] > best['channels']: better = True
											elif stream['bitrate'] and best['bitrate'] and stream['channels'] == best['channels'] and stream['bitrate'] > best['bitrate']: better = True
											if better and stream['name']: # Ingore commentary audio.
												lower = stream['name'].lower()
												if 'comment' in lower or 'director' in lower: better = False
										if better: best = stream
							if best:
								bestOriginal = True
								break

				if best is None:
					for code in settings:
						for stream in streams:
							if stream and code == stream['language'][tools.Language.Code][tools.Language.CodeStream]:
								if best is None:
									if stream['name']: # Ingore commentary audio.
										lower = stream['name'].lower()
										if not 'comment' in lower  and not 'director' in lower:
											best = stream
									else:
										best = stream
								else:
									better = False
									if stream['channels'] and best['channels']:
										if stream['channels'] > best['channels']: better = True
										elif stream['bitrate'] and best['bitrate'] and stream['channels'] == best['channels'] and stream['bitrate'] > best['bitrate']: better = True
										if better and stream['name']: # Ingore commentary audio.
											lower = stream['name'].lower()
											if 'comment' in lower or 'director' in lower: better = False
									if better: best = stream
						if best: break

				if best:
					self.log('Using %s stream' % ('original' if bestOriginal else 'unknown' if unknown else 'preferred'), best)
					self.player().audioSelect(best)
				else:
					undefined = False
					if not unknown:
						for stream in streams:
							if stream['language'][tools.Language.Code][tools.Language.CodeDefault] == tools.Language.UniversalCode:
								undefined = True
								break
					if undefined:
						assumed = self.language()
						if assumed:
							self.log('Unknown stream detected. Assuming the language: ' + str(assumed[tools.Language.Name][tools.Language.NameDefault]))
							return self.select(unknown = True)

					self.log('No preferred stream detected. Falling back to default stream.')
					self.log('Using default stream', current)
		except: tools.Logger.error()


class Subtitle(Streamer):

	# Must correspond with settings.xml.
	StreamDisabled = 0
	StreamDefault = 1
	StreamForced = 2
	StreamAutomatic = 3
	StreamFixed = 4

	# Must correspond with settings.xml.
	SelectionManual = 0
	SelectionAutomatic = 1
	SelectionChoice = 2
	SelectionExact = 3

	# Must correspond with settings.xml.
	NotificationsDisabled = 0
	NotificationsStandard = 1
	NotificationsExtended = 2

	# Must correspond with settings.xml.
	DialogAutomatic = 0
	DialogPlain = 1
	DialogDetails = 2

	StatusCanceled = 'canceled'
	StatusLoaded = 'loaded'
	StatusFailed = 'failed'
	StatusError = 'error'
	StatusUnavailable = 'unavailable'
	StatusDisabled = 'disabled'
	StatusForced = 'forced'
	StatusDefault = 'default'
	StatusIntegrated = 'integrated'

	# Must correspond with the file names in script.gaia.resources.
	InternalDisable = 'GAIA Disable Subtitles'
	InternalSelect = 'GAIA Select Subtitles'
	InternalIntegrated = None
	InternalPrevious = None
	InternalValid = None
	InternalStop = None
	InternalInitial = None
	InternalExternal = None

	Lock = Lock()

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		Subtitle.InternalIntegrated = None
		Subtitle.InternalPrevious = None
		Subtitle.InternalValid = None
		Subtitle.InternalStop = None
		Subtitle.InternalInitial = None
		Subtitle.InternalExternal = None

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def _stream(self, player, retrieve, process, unknown):
		return player.subtitleStream(retrieve = retrieve, process = process, unknown = unknown)

	@classmethod
	def _notification(self, title, message, icon = interface.Dialog.IconInformation, essential = True):
		notifications = tools.Settings.getInteger('playback.subtitle.notifications')
		if notifications == Subtitle.NotificationsExtended or (notifications == Subtitle.NotificationsStandard and essential):
			interface.Dialog.notification(title = title, message = message, icon = icon)

	@classmethod
	def _load(self, subtitle):
		success = False

		if subtitle:
			if (subtitle.get('type') or {}).get('integrated'):
				self.player().subtitleSelect(id = subtitle.get('id'))
				success = True
				self.log('Integrated subtitles loaded: ' + subtitle.get('name'))
			else:
				# Issues with decoding the subtitles.
				# This means that the subtitles will not show at all, or show, but with a weird/incorrect encoding.
				decoded = 'decoded' in subtitle and subtitle['decoded'] is False

				if not 'path' in subtitle:
					from lib.modules.subtitle import Subtitle as Subtitler
					self.log('Downloading external subtitles.')
					subtitle = Subtitler.download(subtitle = subtitle)

				if subtitle:
					# Do not load if there were decoding problems.
					# Only do this the first time. If the user selects the subtitles a second time, just display them as is.
					if not decoded and 'decoded' in subtitle and subtitle['decoded'] is False:
						success = False
						self.log('Subtitles decoding failed.')
					elif 'path' in subtitle:
						self.player().subtitleSelect(path = subtitle['path'])
						success = True
						self.log('External subtitles loaded: ' + subtitle['name'])

		return success, subtitle

	@classmethod
	def stop(self):
		Subtitle.InternalStop = True

	@classmethod
	def internal(self, name, imdb, tmdb, title, year, season, episode, source):
		# The process of detecting, downloading, and selecting subtitles can take some time.
		# This can cause this function to be executed again before the previous execution is done, since it is called in a loop.
		# Only allow a single execution of the select function() at any give time.
		if Subtitle.Lock.locked(): return

		# Make sure internal() only executes AFTER the initial select() is called once playback starts.
		if not Subtitle.InternalInitial: return

		# Reduce the load by only executing if the subtitles changed.
		current = self.streamCurrent()
		if current and not Subtitle.InternalPrevious == current:
			Subtitle.InternalPrevious = current
			if current['name'].startswith(Subtitle.InternalSelect): # Note that Kodi formats the filename of the subtitles, removes language codes, symbols, etc.
				self.select(name = name, imdb = imdb, tmdb = tmdb, title = title, year = year, season = season, episode = episode, source = source, internal = True)
			else:
				Subtitle.InternalValid = current # Last valid subtitles that are not InternalSelect.

	@classmethod
	def select(self, name, imdb, tmdb, title, year, season, episode, source, wait = False, internal = False, lock = None):
		thread = Pool.thread(target = self._select, kwargs = {'name' : name, 'imdb' : imdb, 'tmdb' : tmdb, 'title' : title, 'year' : year, 'season' : season, 'episode' : episode, 'source' : source, 'internal' : internal, 'lock' : lock}, start = True)
		if wait: Player.join(thread)
		return thread

	@classmethod
	def _select(self, name, imdb, tmdb, title, year, season, episode, source, internal = False, lock = None):
		unpause = False
		try:
			if Subtitle.Lock.locked(): return None
			else: Subtitle.Lock.acquire()

			from lib.modules.subtitle import Subtitle as Subtitler

			settingsStream = tools.Settings.getInteger('playback.subtitle.stream')
			settingsSelection = tools.Settings.getInteger('playback.subtitle.selection')
			settingsDownload = tools.Settings.getBoolean('playback.subtitle.download')
			settingsNotifications = tools.Settings.getInteger('playback.subtitle.notifications')

			settingsDialog = tools.Settings.getInteger('playback.subtitle.dialog')
			if settingsDialog == Subtitle.DialogAutomatic: settingsDialog = Subtitle.DialogDetails if interface.Skin.supportDialogDetail() else Subtitle.DialogPlain

			settingsLanguage = self.settingsLanguage(log = True)
			if not settingsLanguage:
				assumed = tools.Language.language(tools.Language.EnglishCode)
				settingsLanguage = [assumed[tools.Language.Code][tools.Language.CodeStream]]
				self.log('No subtitle language preferences. Assuming the language: ' + str(assumed[tools.Language.Name][tools.Language.NameDefault]))

			# In sporadic cases, the streams returned might be None.
			# This is probably because the player has not fully initialized.
			# Wait and try again.
			streams = None
			for i in range(20):
				streams = self.streams()
				if streams and streams[0]: break
				tools.Time.sleep(0.05)

			player = self.player()
			current = self.streamCurrent()
			self.log('Available streams', streams if streams else [])

			pathDisable = tools.File.joinPath(tools.System.pathResources(), 'resources', 'media', 'subtitle', Subtitle.InternalDisable + '.srt')
			pathSelect = tools.File.joinPath(tools.System.pathResources(), 'resources', 'media', 'subtitle', Subtitle.InternalSelect + '.srt')
			if internal:
				settingsSelection = Subtitle.SelectionManual # Always manually select if the user opens the subtitle dialog again.
				player.subtitleSelect(path = pathDisable, enable = False)
				interface.Dialog.closeAll() # Close the Kodi subtitle dialog.
				tools.Time.sleep(0.1)
			else:
				# Use the cached integrated subtitles, otherwise newley downloaded subtitles will be listed as "integrated" in the dialog if opened again.
				if Subtitle.InternalIntegrated is None:
					if streams: Subtitle.InternalIntegrated = Subtitler.process(data = [i for i in streams if i], integrated = True)
					else: Subtitle.InternalIntegrated = False

				player.subtitleSelect(path = pathDisable, enable = False)
				player.subtitleSelect(path = pathSelect, enable = False)
				player.subtitleSelect(path = pathDisable, enable = False) # Add again to make sure the "select" subtitle is not enabled/selected by default.

				# Kodi needs some time until subtitles are loaded from file. Wait, otherwise any other subtitle loading or info retrieval might be wrong.
				# This often results in "pathSelect" to show up in the Kodi player subtitle dialog as the selected subtitles, although the code later on loads a different subtitle.
				# NB: Just wiatimh: tools.Time.sleep(0.5), is sometimes not enough. Sometimes everything loads in a few ms, but sometimes we need more time. Check the subs instead.
				for i in range(60):
					loaded = 0
					loadedStreams = self.streams()
					if loadedStreams:
						for stream in loadedStreams:
							if stream and stream['name'].startswith(Subtitle.InternalDisable) or stream['name'].startswith(Subtitle.InternalSelect):
								loaded += 1
								if loaded >= 2: break
						if loaded >= 2: break
					tools.Time.sleep(0.05)

				if current: player.subtitleSelect(id = current['id']) # Reset to default.

			if not internal:
				if settingsStream == Subtitle.StreamDisabled:
					player.subtitleDisable()
					self.log('Disabling subtitles.')
					return self._finish(status = Subtitle.StatusDisabled)
				elif settingsStream == Subtitle.StreamDefault:
					self.log('Leaving default subtitles.')
					return self._finish(status = Subtitle.StatusDefault, subtitle = current)
				elif settingsStream == Subtitle.StreamForced:
					if current and current['forced']:
						self.log('Leaving forced subtitles.')
						return self._finish(status = Subtitle.StatusForced, subtitle = current)
					else:
						player.subtitleDisable()
						self.log('Disabling subtitles.')
						return self._finish(status = Subtitle.StatusDisabled)
				elif settingsStream == Subtitle.StreamAutomatic:
					primary = True
					secondary = True
					tertiary = True
					if tools.Settings.getBoolean('playback.subtitle.force'):
						if tools.Settings.getBoolean('playback.subtitle.force.primary'): primary = False
						if tools.Settings.getBoolean('playback.subtitle.force.secondary'): secondary = False
						if tools.Settings.getBoolean('playback.subtitle.force.tertiary'): tertiary = False

					if Audio.streamKnown(primary = primary, secondary = secondary, tertiary = tertiary):
						if current and current['forced']:
							try: code = current['language'][tools.Language.Code][tools.Language.CodeStream]
							except: code = None

							# If the forced subtitles are in a language the user does not know and the audio stream is known, disable the subtitles.
							# If the language of the forced subtitles is unknown, leave them on.
							# Eg: Constellation (2024) series: The audio is 99% English, but there are occasional Swedish/Russian conversations. Leave the forced English subtitles on for that 1%.
							if code and not code == tools.Language.UniversalCode and settingsLanguage and not code in settingsLanguage:
								self.log('Audio stream known. Disabling forced subtitles.')
								player.subtitleDisable()
								return self._finish(status = Subtitle.StatusDisabled)
							else:
								self.log('Audio stream known. Leaving forced subtitles.')
								return self._finish(status = Subtitle.StatusForced, subtitle = current)
						else:
							self.log('Audio stream known. Disabling subtitles.')
							player.subtitleDisable()
							return self._finish(status = Subtitle.StatusDisabled)

				if settingsSelection == Subtitle.SelectionExact or settingsSelection == Subtitle.SelectionAutomatic:
					# Already do this here, so that we can avoid a call to OpenSubtitles if we in any case use the integrated subtitles.
					if Subtitle.InternalIntegrated:
						# If there are multiple valid subtitles, try to pick the best one.
						# Eg: We watch anime with Japanese audio (unknown to the user) and there are integrated French subtitles (known to the user).
						# There are two French subtitles (forced and full). We want the full subtitles, since the audio language is unknown.
						# Also do some other sorting. Eg: Rank available languages according to user preferences, try to avoid impaired subitles, etc.
						known = Audio.streamKnown(primary = primary, secondary = secondary, tertiary = tertiary)
						integrated = []
						for stream in Subtitle.InternalIntegrated:
							try:
								type = stream.get('type') or {}
								try: sort = 10 - settingsLanguage.index(stream['language'][tools.Language.Code][tools.Language.CodeStream])
								except: sort = None
								if not sort is None:
									if type.get('integrated'): sort += 0.001
									else: sort -= 0.001

									if stream.get('impaired'): sort -= 0.01
									else: sort += 0.01

									if known:
										if stream.get('default'): sort += 0.1
										else: sort -= 0.1
									else:
										if stream['name']:
											if tools.Regex.match(data = stream['name'], expression = '(full|complete)'): sort += 0.1
											elif tools.Regex.match(data = stream['name'], expression = '(force|foreign)'): sort -= 0.1

									stream['sort'] = sort
									integrated.append(stream)
							except: tools.Logger.error()
						integrated = tools.Tools.listSort(integrated, key = lambda i : i['sort'], reverse = True)
						for stream in integrated:
							success, _ = self._load(subtitle = stream)
							if success: return self._finish(status = Subtitle.StatusIntegrated, subtitle = stream)

			subtitles = []
			failure = False
			if Subtitle.InternalIntegrated: subtitles.extend(Subtitle.InternalIntegrated)
			if settingsDownload:
				# If external subtitles are loaded on the initial run, and reopened with InternalSelect, the dialog shows quickly, since the search results are cached.
				# However, if during the initital run integrated subtitles are selected and the user later selects InternalSelect, a new search is done which can take time.
				# Notify the user.
				if not Subtitle.InternalExternal and internal:
					if lock:
						lock.acquire()
						lock = None
					unpause = True
					self.playerPause()
					self._notification(title = 36127, message = 36128, icon = interface.Dialog.IconInformation)
				Subtitle.InternalExternal = True

				self.log('Searching external subtitles.')
				subsubtitles = Subtitler.search(language = settingsLanguage, imdb = imdb, tmdb = tmdb, title = title, year = year, season = season, episode = episode)
				if subsubtitles: subtitles.extend(subsubtitles)
				elif subsubtitles is None: failure = True
			if len(subtitles) == 0: return self._finish(status = Subtitle.StatusUnavailable, notification = not failure, unpause = unpause) # OpenSubntitles error already showing if there were server issues.

			filename = source.fileName()
			year = source.metaYear()
			filenameLower = filename.lower()
			extensions = tools.Video.extensions(list = True, dot = True)
			for i in range(len(subtitles)):
				subtitle = subtitles[i]
				type = subtitle.get('type') or {}
				name = subtitle.get('name')
				nameLower = name.lower()

				# Match ratio.
				if type.get('integrated'): match = 1.0
				elif filename and name:
					match = tools.Matcher.levenshtein(filename, name, ignoreCase = True, ignoreSpace = True, ignoreNumeric = False, ignoreSymbol = True)

					# Check if there is a perfect match with the extension removed.
					# Eg: "No.Time.to.Die.2021.720p.HDCAM.SLOTSLIGHTS" vs "No.Time.to.Die.2021.720p.HDCAM.SLOTSLIGHTS.mkv"
					if match < 1 and match > 0.75:
						filenameNew = filenameLower
						nameNew = nameLower

						for extension in extensions:
							if filenameNew.endswith(extension):
								filenameNew = tools.Tools.stringRemoveSuffix(filenameNew, extension)
								nameNew = tools.Tools.stringRemoveSuffix(nameNew, extension)
								matchNew = tools.Matcher.levenshtein(filenameNew, nameNew, ignoreCase = True, ignoreSpace = True, ignoreNumeric = False, ignoreSymbol = True)
								if matchNew >= 1: match = matchNew
								break

						# Some symbols that were replaced.
						# Eg: "No.Time.to.Die.1080p.AMZN.WEB-DL.DDP5.1.H.264-CMRG" vs "No Time to Die 1080p AMZN WEB-DL DDP5 1 H 264-CMRG"

						if match < 1 and match > 0.75:
							filenameNew = tools.Tools.replaceNotAlphaNumeric(data = filenameNew, replace = ' ')
							nameNew = tools.Tools.replaceNotAlphaNumeric(data = nameNew, replace = ' ')
							matchNew = tools.Matcher.levenshtein(filenameNew, nameNew, ignoreCase = True, ignoreSpace = True, ignoreNumeric = False, ignoreSymbol = True)
							if matchNew >= 1: match = matchNew

						# Sometimes the year is not included.
						# Eg: "No.Time.to.Die.1080p.AMZN.WEB-DL.DDP5.1.H.264-CMRG" vs "No Time to Die 2021 1080p AMZN WEB-DL DDP5 1 H 264-CMRG"
						if match < 1 and match > 0.75 and year:
							year = str(year)
							filenameNew = filenameNew.replace(year, '')
							nameNew = nameNew.replace(year, '')
							matchNew = tools.Matcher.levenshtein(filenameNew, nameNew, ignoreCase = True, ignoreSpace = True, ignoreNumeric = False, ignoreSymbol = True)
							if matchNew >= 1: match = matchNew

				else: match = 0.0
				subtitles[i]['match'] = match

				# Sort value.
				sort = match

				try:
					index = settingsLanguage.index(subtitle['language'][tools.Language.Code][tools.Language.CodeStream])
					if index >= 0: sort += (10 - index) * 1000
				except: pass

				if type.get('integrated'): sort += 100000 # Make sure integrated subtitles are always on top.
				elif match == 1: sort += 100 # Make sure perfect matches are always on top.

				if type.get('foreign'): sort += 0.15
				if type.get('default'): sort += 0.1
				if type.get('trusted'): sort += 0.05
				if type.get('impaired'): sort -= 0.05
				if type.get('ai'): sort -= 0.1
				if type.get('machine'): sort -= 0.2

				try: sort += subtitle['rating'] * 0.3
				except: pass
				try: sort += min(1, subtitle['download'] / 10000.0) * 0.2
				except: pass
				try: sort += min(1, subtitle['votes'] / 1000.0) * 0.1
				except: pass
				subtitles[i]['sort'] = sort

			success = False
			subtitles = tools.Tools.listSort(data = subtitles, key = lambda i : i['sort'], reverse = True)

			if settingsSelection == Subtitle.SelectionChoice:
				if lock:
					lock.acquire()
					lock = None
				self.playerPause()
				choice = interface.Dialog.options(title = 32353, message = 35144, labelConfirm = 33110, labelDeny = 33800, labelCustom = 33743)
				if choice == interface.Dialog.ChoiceCustom or choice == interface.Dialog.ChoiceCancelled:
					return self._finish(status = Subtitle.StatusCanceled, unpause = True)
				if choice == interface.Dialog.ChoiceYes:
					settingsSelection = Subtitle.SelectionManual
				elif choice == interface.Dialog.ChoiceNo:
					settingsSelection = Subtitle.SelectionAutomatic
					self.playerUnpause()

			if settingsSelection == Subtitle.SelectionExact:
				success = False
				for i in range(len(subtitles)):
					subtitle = subtitles[i]
					if subtitle['match'] >= 1 and subtitle['language'][tools.Language.Code][tools.Language.CodeStream] in settingsLanguage:
						success, subtitle = self._load(subtitle = subtitle)
						if success:
							subtitles[i] = subtitle
							break
				if not success: settingsSelection = Subtitle.SelectionManual

			if settingsSelection == Subtitle.SelectionAutomatic:
				success = False
				for subtitle in subtitles:
					success = self._load(subtitle = subtitle)
					if success: break
				if not success: # Try again with decode-failed subtitles.
					for i in range(len(subtitles)):
						subtitle = subtitles[i]
						if subtitle and 'decoded' in subtitle and subtitle['decoded'] is False:
							success, subtitle = self._load(subtitle = subtitle)
							if success:
								subtitles[i] = subtitle
								break

			if settingsSelection == Subtitle.SelectionManual:
				if lock:
					lock.acquire()
					lock = None
				details = settingsDialog == Subtitle.DialogDetails
				self.playerPause()
				while True:
					if Subtitle.InternalStop: break # Eg: User stopped the video before the subtitle dialog shows up.
					choice = interface.Dialog.select(title = 32353, items = self._items(subtitles = subtitles, details = details), details = details)
					if choice < 0: return self._finish(status = Subtitle.StatusCanceled, unpause = True)
					subtitle = subtitles[choice]
					success, subtitle = self._load(subtitle = subtitle)
					if subtitle: subtitles[choice] = subtitle
					if success: break
					elif subtitle and 'decoded' in subtitle and subtitle['decoded'] is False: self._notification(title = 35860, message = 35861, icon = interface.Dialog.IconWarning)

			return self._finish(status = Subtitle.StatusLoaded if success else Subtitle.StatusFailed, subtitle = subtitle, unpause = True)
		except:
			tools.Logger.error()
			return self._finish(status = Subtitle.StatusError, unpause = unpause)

	@classmethod
	def _items(self, subtitles, details):
		items = []
		directory = interface.Directory()
		gradient = interface.Format.colorGradientIncrease(count = 1000)

		iconDown = interface.Format.icon(icon = interface.Font.IconDown, bold = True)
		if details: supportIcon = interface.Skin.supportDialogDetailIcon(default = True)
		else: supportIcon = True

		for i in range(len(subtitles)):
			subtitle = subtitles[i]
			type = subtitle.get('type') or {}

			# Flag icon.
			icon = tools.Language.flag(subtitle['language'][tools.Language.Code][tools.Language.CodePrimary], quality = interface.Icon.QualityLarge if supportIcon else interface.Icon.QualitySmall, subtitle = not type.get('integrated'))

			# Label line 1.
			label = subtitle['name']
			defective = 'decoded' in subtitle and subtitle['decoded'] is False
			if not label: label = interface.Format.fontItalic(interface.Translation.string(35248))
			if defective: label = interface.Format.fontItalic(label)

			# Label line 2.
			info = []
			if type.get('integrated') and tools.Language.NameUniversal in subtitle['language'][tools.Language.Name]: language = subtitle['language'][tools.Language.Name][tools.Language.NameUniversal]
			else: language = subtitle['language'][tools.Language.Name][tools.Language.NameDefault]
			info.append(interface.Format.fontBold(language))
			if type.get('integrated'): info.append(interface.Format.fontColor(33336, color = interface.Format.colorExcellent()))
			if defective: info.append(interface.Format.fontColor(35360, color = interface.Format.colorBad()))
			match = subtitle['match']
			if match >= 1.0: matchLabel = 36107
			elif match >= 0.50: matchLabel = 36108
			elif match >= 0.30: matchLabel = 36109
			else: matchLabel = 36110
			info.append(interface.Format.fontColor('%s (%.0f%%)' % (interface.Translation.string(matchLabel), match * 100), color = interface.Format.colorGradientPick(value = match * 1000, gradient = gradient)))
			if type.get('machine'): info.append(interface.Format.fontColor(36251, color = interface.Format.colorBad()))
			if type.get('ai'): info.append(interface.Format.fontColor(35432, color = interface.Format.colorPoor()))
			if type.get('trusted'): info.append(interface.Format.fontColor(35531, color = interface.Format.colorAlternative()))
			if type.get('impaired'): info.append(interface.Format.fontColor(33922, color = interface.Format.colorSpecial()))
			if type.get('foreign'): info.append(interface.Format.fontColor(35414, color = interface.Format.colorSpecial()))
			if type.get('default'): info.append(interface.Format.fontColor(33564, color = interface.Format.colorSpecial()))
			if not subtitle.get('rating') is None:
				rating = interface.Format.iconRating(count = max(1, tools.Math.roundUp(subtitle.get('rating') * 5)), fixed = 5, color = interface.Format.colorGradientPick(value = subtitle.get('rating') * 100, gradient = gradient))
				if not type.get('integrated'): rating += ' (%s)' % tools.Math.thousand(subtitle.get('votes') or 0)
				info.append(rating)
			if not subtitle.get('download') is None:
				info.append(interface.Format.fontColor('%s%s' % (iconDown, tools.Math.thousand(subtitle.get('download'))), color = interface.Format.colorGradientPick(value = subtitle.get('download') / 6.0, gradient = gradient)))
			info = interface.Format.iconJoin(info, pad = '  ')

			if details:
				if (type.get('integrated') or subtitle['match'] >= 1): label = interface.Format.fontBold(label)
				label2 = info
			else:
				label = interface.Format.iconJoin([info, label])
				label2 = None

			items.append(directory.item(label = label, label2 = label2, icon = icon))

		return items

	@classmethod
	def _finish(self, status, subtitle = False, unpause = False, notification = True):
		# Only show notifications if the player is actually playing.
		# Otherwise, if there is a playback failure or if playback was manually canceled from WindowPlayback, the Subtitle.StatusFailed pops up.
		if notification and self.player().isPlayback():

			if not subtitle is False:
				if subtitle:
					name = subtitle['name']
					if not name: name = interface.Format.fontItalic(interface.Translation.string(35248))
					subtitle = interface.Format.iconJoin([interface.Format.fontBold(subtitle['language'][tools.Language.Name][tools.Language.NameDefault]), name])
				else: subtitle = 36122

			if status == Subtitle.StatusLoaded: self._notification(title = 35140, message = subtitle, icon = interface.Dialog.IconSuccess)
			elif status == Subtitle.StatusFailed: self._notification(title = 35145, message = 36117, icon = interface.Dialog.IconWarning)
			elif status == Subtitle.StatusUnavailable: self._notification(title = 35145, message = 35146, icon = interface.Dialog.IconWarning)
			elif status == Subtitle.StatusDisabled: self._notification(title = 36118, message = 36119, icon = interface.Dialog.IconInformation, essential = False)
			elif status == Subtitle.StatusForced: self._notification(title = 36120, message = subtitle, icon = interface.Dialog.IconInformation, essential = False)
			elif status == Subtitle.StatusDefault: self._notification(title = 36121, message = subtitle, icon = interface.Dialog.IconInformation, essential = False)
			elif status == Subtitle.StatusIntegrated: self._notification(title = 35549, message = subtitle, icon = interface.Dialog.IconInformation, essential = False)
			elif status == Subtitle.StatusError: self._notification(title = 36123, message = 36124, icon = interface.Dialog.IconError)

		# Reset to the previously selected subtitles before the user selected InternalSelect.
		if status == Subtitle.StatusCanceled:
			if Subtitle.InternalValid: self.player().subtitleSelect(id = Subtitle.InternalValid['id'])

		if unpause: self.playerUnpause()

		try: Subtitle.Lock.release()
		except: pass

		Subtitle.InternalInitial = True

		return status


class Chapter(Streamer):

	TypePromo = 'promo'
	TypeIntro = 'intro'
	TypeRecap = 'recap'
	TypeStory = 'story'
	TypeOutro = 'outro'
	TypeEnd = 'end' # Often there is an extra chapter to indicate the end of the chapter.
	TypeDefault = TypeStory
	TypesSkip = [TypePromo, TypeIntro, TypeRecap]
	TypesExpression = {
		TypePromo : '(promo)',
		TypeIntro : '(intro|start|theme|trailer)',
		TypeOutro : '(outro|credit|finish)',
		TypeRecap : '(recap|refresh)',
	}

	Chapters = []

	@classmethod
	def settingsSkip(self):
		return tools.Settings.getBoolean('activity.skip.enabled')

	@classmethod
	def chapterSkip(self):
		# Some videos has multiple short chapters at the start.
		# Eg: The Winter King S01E01 has 7 chapters that will be considered intro from the code above.
		# If there are that many chapters, it is difficult to determine which one is the actual intro and which are normal (short) chapters.
		# For 1 - 3 intro chapters: show Skip button for all of them.
		# For 4 intro chapters: only show Skip button for the first 3 chapters.
		# For 5 intro chapters: only show Skip button for the first 2 chapters.
		# For 5+ intro chapters: only show Skip button for the first chapter.

		valid = [chapter for chapter in Chapter.Chapters if chapter['skip'] and chapter['time']['duration'] >= 10]
		if len(valid) < 3: valid = [chapter for chapter in Chapter.Chapters if chapter['skip'] and chapter['time']['duration'] >= 7]

		skipped = 0
		total = len(valid)
		limit = 3 if total <= 4 else 2 if total == 5 else 1

		chapters = {}
		for chapter in valid:
			if skipped >= limit: break
			skipped += 1
			chapters[chapter['percent']['start']] = chapter

		return chapters

	@classmethod
	def chapterOutro(self, single = True):
		result = [chapter for chapter in Chapter.Chapters if chapter['type'] == Chapter.TypeOutro and chapter['time']['duration'] >= 5]
		if result: return result[-1] if single else result
		return None

	@classmethod
	def select(self, resume = None, wait = False):
		if self.settingsSkip():
			thread = Pool.thread(target = self._select, kwargs = {'resume' : resume}, start = True)
			if wait: Player.join(thread)
			return thread
		return None

	@classmethod
	def _select(self, resume = None):
		try:
			# There is currently no way to get the chapter names, not from the RPC, not from the info labels, and not from Python.
			# Often chapters are labeled as "Intro" or "Recap", which could be used to better determine which chapter is the intro.
			# We could do:
			#	tools.System.execute('ActivateWindow(videobookmarks)')
			#	list = xbmcgui.Window(xbmcgui.getCurrentWindowId()).getControl(11)
			#	item = list.getListItem(0).getLabel()
			# However, getListItem() always returns None for lists populated from the skin (C++).

			Chapter.Chapters = []

			try:
				from lib.modules.convert import ConverterDuration
				chapters = tools.System.infoLabel('Player.Chapters')
				if chapters:
					chapters = [float(i) for i in chapters.split(',')]
					if chapters:
						try: time = tools.Math.roundUp(self.player().getTotalTime() or 0)
						except: time = 0 # RuntimeError: Kodi is not playing any media file

						thresholdPromoPercent = 0.001
						thresholdPromoDuration = 0.1
						thresholdIntroPercent = 0.05 # House of Dragons: percent = 2.7%
						thresholdIntroDuration = 0.25
						thresholdOutroPercent = 0.05 # House of Dragons: percent = 2.4%
						thresholdOutroDuration = 0.97
						thresholdLastPercent = 0.08 # Similar to outro, but only if it is the last chapter. 6% just too little for Band of Brothers (6.02%).
						thresholdLastDuration = 0.92 # 94% just too little for Band of Brothers (93.97%).
						if time and time < 1800:
							# Short episodes with less than 30 minutes.
							# Heavenly Delusion: percent = 6.5%, end = 93.5%.
							# Heavenly Delusion S01E06: percent = 12.3%, end = 87.6%.
							thresholdLastPercent = 0.15
							thresholdLastDuration = 0.85

						chapters.append(100.0)
						last = len(chapters) - 1
						for i in range(last):
							next = i + 1
							name = 'Chapter %d' % (i + 1)

							start = chapters[i] / 100.0
							end = chapters[next] / 100.0
							startTime = int(start * time)
							endTime = int(end * time)
							if not startTime == endTime and i < next: endTime -= 1
							startFormat = ConverterDuration(value = startTime, unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatClockShort)
							endFormat = ConverterDuration(value = endTime, unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatClockShort)

							# In the future if we can get the chapter names, matching with regex will be better.
							type = None
							if start == end: type = Chapter.TypeEnd
							if not type:
								for t, e in Chapter.TypesExpression.items():
									if tools.Regex.match(data = name, expression = e):
										type = t
										break
								if not type:
									percent = end - start
									if percent < thresholdPromoPercent and start < thresholdPromoDuration: type = Chapter.TypePromo
									elif percent < thresholdIntroPercent and start < thresholdIntroDuration: type = Chapter.TypeIntro # House of Dragons: percent = 2.7%
									elif percent < thresholdOutroPercent and end >= thresholdOutroDuration: type = Chapter.TypeOutro # House of Dragons: percent = 2.4% | Heavenly Delusion: percent = 6.5%, end = 93%.
									elif next == last and percent < thresholdLastPercent and end >= thresholdLastDuration: type = Chapter.TypeOutro
									else: type = Chapter.TypeDefault

							Chapter.Chapters.append({
								'name' : name,
								'label' : '%s: %s (%s - %s)' % (name, type.title(), startFormat, endFormat),
								'type' : type,
								'skip' : type in Chapter.TypesSkip,
								'percent' : {
									'start' : start,
									'end' : end,
									'duration' : end - start,
								},
								'time' : {
									'start' : startTime,
									'end' : endTime,
									'duration' : endTime - startTime,
								},
							})

						self.log('Available chapters: ' + (' | '.join([i['label'] for i in Chapter.Chapters])))
			except: tools.Logger.error()

			self._update(resume = resume)
			return Chapter.Chapters
		except:
			tools.Logger.error()
			return []

	@classmethod
	def _update(self, resume = None):
		try:
			if Chapter.Chapters:
				chapters = self.chapterSkip()
				chapter = None
				player = self.player()
				timeTotal = float(player.getTotalTime())
				progressPrevious = 0
				second = 1 / timeTotal
				offset = 3

				# If playback is auto-resumed, the Kodi player needs some time to execute player.seekTime() and for player.getTime() to get updated.
				# This means if the intro chapter is right at the start of video, the Skip button pops up for a short time before being hidden again when player.getTime() changes.
				# To avoid this, use the passed in resume time instead.
				# Waiting here is technically not required, but it cannot hurt to get the actual time in the loop below.
				if resume:
					for i in range(6):
						try:
							if player.getTime() >= resume: break
						except: pass
						tools.Time.sleep(0.05)

				# Run this for the entire pl;ayback, in case the user changes progress to the start again.
				while True:
					if not player.isPlayingVideo() or tools.System.aborted():
						window.WindowButtonSkip.cancel()
						return

					# Only use the resume time once.
					# Yesterday the user fell asleep, woke up in the middle of the episode progress and stopped playback.
					# Next day the user starts playback again, it gets auto-resumed to th emiddle, but the user manually changes progress to 0% to start the episode from the beginning.
					# In this case "resume" will be higher that the actual getTime(). But we still want the Skip button to show.
					if resume:
						timeCurrent = max(resume, player.getTime())
						resume = None
					else:
						timeCurrent = player.getTime()
					progress = timeCurrent / timeTotal

					if progress < progressPrevious: chapters = self.chapterSkip()
					if chapter and (timeCurrent < chapter['time']['start'] - 1 or timeCurrent > chapter['time']['end'] + 1): window.WindowButtonSkip.cancel()
					progressPrevious = progress

					for percent in chapters.keys():
						# 5 secs is too little if the intro starts right at the start of the video (00:00). Eg: GoT S07E05.
						# Probably because the audio/subtitle and auto resume threads are still busy.
						if progress >= percent and progress <= percent + ((8 if percent < 0.01 else 5) * second):
							chapter = chapters[percent]
							del chapters[percent]

							seekTime = chapter['time']['end'] - offset
							seekDuration = chapter['time']['duration'] - offset

							window.WindowButtonSkip.show(duration = seekDuration, callback = lambda : player.seekTime(seekTime))
							break

					# Use longer sleeping time if the progress is closer to the end, in order to reduce processing.
					# Still keep monitoring, in case the user is at the end of the progress and seeks to the start of the video.
					tools.Time.sleep(0.5 if progress < 0.1 else 1 if progress < 0.2 else 1.5 if progress < 0.3 else 2 if progress < 0.5 else 5)
		except: tools.Logger.error()
