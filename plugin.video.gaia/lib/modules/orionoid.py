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

try:
	from lib.modules.tools import System, Tools, Time, Settings, File, Extension, Regex, Converter, Logger
	from lib.modules.interface import Translation, Directory, Format, Dialog, Loader
	from lib.modules.network import Networker
	from lib.modules.stream import Stream
	from lib.modules.concurrency import Pool, Lock

	if not System.id() == System.id(None):
		raise Exception('lib')

	from orion import *

	class Orionoid(object):

		Id = Orion.Id
		Name = Orion.Name
		Scraper = 'oriscrapers'

		TypeMovie = Orion.TypeMovie
		TypeShow = Orion.TypeShow

		StreamTorrent = Orion.StreamTorrent
		StreamUsenet = Orion.StreamUsenet
		StreamHoster = Orion.StreamHoster

		VoteUp = Orion.VoteUp
		VoteDown = Orion.VoteDown

		DebridPremiumize = Orion.DebridPremiumize
		DebridOffcloud = Orion.DebridOffcloud
		DebridRealdebrid = Orion.DebridRealdebrid
		DebridAlldebrid = Orion.DebridAlldebrid
		DebridDebridlink = Orion.DebridDebridlink

		SettingsEnabled = 'premium.orion.enabled'
		SettingsAuthentication = 'premium.orion.authentication'
		SettingsFilters = 'premium.orion.filters'
		SettingsPromotion = 'premium.orion.promotion'
		SettingsFree = 'premium.orion.free'
		SettingsAddonInstallation = 'stream.orion.installation'
		SettingsAddonConnection = 'stream.orion.connection'
		SettingsAddonSettings = 'stream.orion.settings'

		SettingsAddonGeneral = Orion.SettingsAccount
		SettingsAddonAccount = Orion.SettingsAccount
		SettingsAddonFilters = Orion.SettingsFilters

		IgnoreDomains = ['furk', 'easynews']
		IgnoreHeaders = ['phpsessid', 'session.*', 'auth(?:orization|enticat(?:e|ion))?', 'x?.?(?:rapid)?.?api.?(?:key)?', 'token', 'key', 'user(?:name)?$', 'pass(?:word)?'] # Header or cookie keys.

		PropertyAuthentication = 'GaiaOrionAuthentication'

		ChunkLimit = 30

		Maps = None

		##############################################################################
		# CONSTRUCTOR
		##############################################################################

		def __init__(self, silent = False):
			self.mOrion = Orion(key = System.obfuscate(Settings.getString('internal.key.orion', raw = True)), silent = silent)
			self.mHashesQueue = []
			self.mHashesCompleted = {}
			self.mHashesThreads = []
			self.mHashesLock = Lock()
			self.mIdentifiersQueue = []
			self.mIdentifiersCompleted = {}
			self.mIdentifiersThreads = []
			self.mIdentifiersLock = Lock()

		##############################################################################
		# INITIALIZE
		##############################################################################

		def initialize(self, background = False, refresh = False, settings = False, external = False):
			if background:
				# Kodi caches addon settings.
				# If the Orion settings dialog is opened and a settings is cached (eg: enable/disable app-specific filters), the old cached settings are returned (eg: settingsFiltersGlobal).
				# Launch a new process so that the newest settings can be retrieved after the Orion settings dialog was closed.
				System.executePlugin(action = 'orionInitialize', parameters = {'settings' : settings})
			else:
				# Only (re-)enable the settings if not previously set (aka first launch).
				# If the user manually disables Orion in the settings, it shoulds stay disabled, and not automatically re-enable on next launch.
				if not Settings.getBoolean(Orionoid.SettingsEnabled) and Settings.getBoolean(Orionoid.SettingsAuthentication):
					pass # User has manually disabled Orion.
				else:
					valid = self.accountValid(external = external)
					if not external: Settings.set(Orionoid.SettingsEnabled, valid)
					if valid: Settings.setData(Orionoid.SettingsAuthentication, value = valid, label = Format.fontBold(self.accountLabel()))
					else: Settings.defaultData(Orionoid.SettingsAuthentication)
					Settings.set(Orionoid.SettingsFilters, Translation.string(33509 if self.mOrion.settingsFiltersGlobal() else 35233))

				if refresh: Directory.refresh() # When executed from the Tools menu, hide the entry if a an account was authenticated above.
				if settings: self.settingsLocal(settings)

		##############################################################################
		# UNINSTALL
		##############################################################################

		@classmethod
		def uninstall(self, setting = False):
			'''if Dialog.option(title = 35400, message = 35633):
				directory = System.path(id = Orionoid.Id)
				path = File.joinPath(directory, 'addon.xml')
				data = File.readNow(path)
				data = Regex.replace(data = data, expression = 'id="' + Orionoid.Id + '"\s*version="(.*?)"', replacement = 'id="' + Orionoid.Id + '" version="9.9.9"', all = True, flags = Regex.FlagAllLines)
				data = Regex.replace(data = data, expression = '\sname="Orion"', replacement = ' name="Orion Dummy"', all = True, flags = Regex.FlagAllLines)
				data = Regex.replace(data = data, expression = '<extension\s*point="xbmc\.python\.pluginsource".*?<\/extension>', replacement = '', all = True, flags = Regex.FlagAllLines)
				data = Regex.replace(data = data, expression = '<extension\s*point="xbmc\.python\.module".*?\/>', replacement = '', all = True, flags = Regex.FlagAllLines)
				data = Regex.replace(data = data, expression = '<extension\s*point="xbmc\.service".*?\/>', replacement = '', all = True, flags = Regex.FlagAllLines)
				File.writeNow(path, data)
				directories, files = File.listDirectory(directory, absolute = True)
				for i in directories: File.deleteDirectory(i)
				Dialog.notification(title = 35400, message = 35635, icon = Dialog.IconSuccess)'''

			if Dialog.option(title = 35400, message = 36240): self.addonDisable(refresh = True)
			if settings: self.settingsAddon()

		##############################################################################
		# STRUCTURE
		##############################################################################

		def structureOld(self):
			return not self.structureNew()

		def structureNew(self):
			try:
				import inspect
				inspect.signature(self.mOrion.streams).parameters['videoDepth']
				return True
			except:
				return False

		##############################################################################
		# LINK
		##############################################################################

		def link(self):
			return self.mOrion.link()

		##############################################################################
		# SILENT
		##############################################################################

		def silent(self):
			return self.mOrion.silent()

		def silentSet(self, silent = True):
			self.mOrion.silentSet(silent)

		##############################################################################
		# SETTINGS
		##############################################################################

		@classmethod
		def settingsAddon(self, settings = False):
			id = None
			if self.addonInstalled(): id = Orionoid.SettingsAddonSettings if settings else Orionoid.SettingsAddonConnection
			else: id = Orionoid.SettingsAddonInstallation
			Settings.launch(id)

		def settingsLocal(self, id = None):
			id = id if (id and not id is True and Settings.getBoolean(Orionoid.SettingsEnabled)) else Orionoid.SettingsEnabled
			if id == Orionoid.SettingsAuthentication: Settings.launchData(id)
			else: Settings.launch(id)

		def settingsLaunch(self, category = None, section = None, addon = None, app = None, wait = False):
			self.mOrion.settingsLaunch(category = category, section = section, addon = addon, app = app, wait = wait)

		def settingsFilters(self, settings = False, wait = None):
			if wait is None and settings is True: wait = True
			self.mOrion.settingsFilters(app = True, wait = wait)
			self.initialize(background = True, settings = Orionoid.SettingsFilters)

		def settingsScrapingTimeout(self):
			return self.mOrion.settingsScrapingTimeout()

		def settingsScrapingMode(self):
			return self.mOrion.settingsScrapingMode()

		def settingsScrapingCount(self):
			return self.mOrion.settingsScrapingCount()

		def settingsScrapingQuality(self):
			return self.mOrion.settingsScrapingQuality()

		##############################################################################
		# ADDON
		##############################################################################

		@classmethod
		def addonId(self):
			return Orionoid.Id

		@classmethod
		def addonLaunch(self):
			Extension.launch(id = Orionoid.Id)

		@classmethod
		def addonSettings(self, id = None, settings = False):
			Extension.settings(id = Orionoid.Id, setting = id, wait = True)
			if settings: self.settingsAddon(settings = settings)

		@classmethod
		def addonInstalled(self):
			return Extension.installed(id = Orionoid.Id)

		@classmethod
		def addonEnable(self, refresh = False, settings = False):
			result = Extension.enable(id = Orionoid.Id, refresh = refresh)
			if settings: self.settingsAddon()
			return result

		@classmethod
		def addonDisable(self, refresh = False):
			return Extension.disable(id = Orionoid.Id, refresh = refresh)

		def addonWebsite(self, open = False):
			link = self.link()
			if open: Networker.linkShow(link = link)
			return link

		##############################################################################
		# ACCOUNT
		##############################################################################

		def accountEnable(self, enable = True):
			Settings.set(Orionoid.SettingsEnabled, enable)

		def accountDisable(self, disable = True):
			Settings.set(Orionoid.SettingsEnabled, not disable)

		def accountEnabled(self, external = False):
			return (external or Settings.getBoolean(Orionoid.SettingsEnabled)) and self.mOrion.userEnabled()

		def accountValid(self, enabled = False, external = False, refresh = False):
			return (external or not enabled or self.accountEnabled(external = external)) and self.mOrion.userValid(refresh = refresh)

		def accountAvailable(self):
			return not Settings.getBoolean(Orionoid.SettingsAuthentication) and self.accountValid(external = True)

		def accountAllow(self):
			return self.accountValid() or self.accountEnabled() or self.accountEnabled() == 0

		def accountLabel(self):
			return self.mOrion.userLabel()

		def accountAnonymous(self):
			return self.mOrion.userAnonymous()

		def accountFree(self):
			return self.mOrion.userFree()

		def accountPremium(self):
			return self.mOrion.userPremium()

		def accountUser(self, refresh = False):
			return self.mOrion.user(refresh = refresh)

		def accountDialog(self):
			return self.mOrion.userDialog()

		def accountLogin(self):
			return self.mOrion.userLogin()

		def accountAuthenticate(self, settings = False, background = True):
			System.windowPropertySet(Orionoid.PropertyAuthentication, '1')
			Settings.set(Orionoid.SettingsEnabled, True)

			# First check if the account was authenticated in the Orion addon, but not yet in the Gaia addon.
			# In that case, just pull in the Orion account, instead of showing the authentication dialog and requiring the user to authenticate again.
			if self.accountAvailable():
				Loader.show()
				self.initialize(settings = Orionoid.SettingsAuthentication if settings is True else settings, background = background, external = True)
				result = self.accountVerify()
			else:
				result = self.accountLogin()
				Loader.show()
				self.initialize(settings = Orionoid.SettingsAuthentication if settings is True else settings, background = background, external = True)

			if not result: Settings.set(Orionoid.SettingsEnabled, False)
			System.windowPropertyClear(Orionoid.PropertyAuthentication)
			Loader.hide()
			return result

		@classmethod
		def accountAuthenticateBusy(self):
			try: return bool(System.windowPropertyGet(Orionoid.PropertyAuthentication))
			except: return False

		@classmethod
		def accountAuthenticateWait(self):
			while self.accountAuthenticateBusy():
				Time.sleep(0.1)

		def accountVerify(self):
			verify = self.accountValid(enabled = True, external = False, refresh = False) and self.accountValid(enabled = False, external = True, refresh = True)
			if self.mOrion.lastTypeConnection(): return None
			return verify

		def accountUpdate(self, key = None, input = False, loader = False):
			return self.mOrion.userUpdate(key = key, input = input, loader = loader)

		def accountPromotion(self, settings = False, background = True):
			if settings and self.accountAvailable():
				return self.accountAuthenticate(settings = settings, background = background)
			else:
				register = self.mOrion.userRegister()
				if register:
					self.accountEnable()
					self.initialize(settings = Orionoid.SettingsAuthentication if settings is True else settings, background = background, refresh = True)
				elif settings:
					self.settingsLocal(Orionoid.SettingsFree)
				Settings.set(Orionoid.SettingsPromotion, False)
				return register

		def accountPromotionEnabled(self):
			return not self.accountValid() and Settings.getBoolean(Orionoid.SettingsPromotion)

		##############################################################################
		# REQUESTS
		##############################################################################

		def requestsLimited(self):
			return self.mOrion.lastTypeSubscription()

		##############################################################################
		# SERVER
		##############################################################################

		def serverStats(self):
			return self.mOrion.serverStats()

		def serverTest(self):
			return self.mOrion.serverTest()

		##############################################################################
		# MAP
		##############################################################################

		@classmethod
		def map(self, value, category, attribute, mode = 'orion', default = None):
			if Orionoid.Maps is None:
				Orionoid.Maps = {
					'video' : {
						'quality' : {
							'orion' : {
								Orion.QualityHd8k : Stream.VideoQualityHd8k,
								Orion.QualityHd6k : Stream.VideoQualityHd6k,
								Orion.QualityHd4k : Stream.VideoQualityHd4k,
								Orion.QualityHd2k : Stream.VideoQualityHd2k,
								Orion.QualityHd1080 : Stream.VideoQualityHd1080,
								Orion.QualityHd720 : Stream.VideoQualityHd720,

								Orion.QualitySd : Stream.VideoQualitySd,

								Orion.QualityScr1080 : Stream.VideoQualityScr1080,
								Orion.QualityScr720 : Stream.VideoQualityScr720,
								Orion.QualityScr : Stream.VideoQualityScr480,

								Orion.QualityCam1080 : Stream.VideoQualityCam1080,
								Orion.QualityCam720 : Stream.VideoQualityCam720,
								Orion.QualityCam : Stream.VideoQualityCam480,
							},
							'gaia' : {
								Stream.VideoQualityHd : Orion.QualityHd720,
								Stream.VideoQualityHdUltra : Orion.QualityHd4k,
								Stream.VideoQualityHd16k : Orion.QualityHd8k,
								Stream.VideoQualityHd14k : Orion.QualityHd8k,
								Stream.VideoQualityHd12k : Orion.QualityHd8k,
								Stream.VideoQualityHd10k : Orion.QualityHd8k,
								Stream.VideoQualityHd8k : Orion.QualityHd8k,
								Stream.VideoQualityHd6k : Orion.QualityHd6k,
								Stream.VideoQualityHd4k : Orion.QualityHd4k,
								Stream.VideoQualityHd2k : Orion.QualityHd2k,
								Stream.VideoQualityHd1080 : Orion.QualityHd1080,
								Stream.VideoQualityHd720 : Orion.QualityHd720,

								Stream.VideoQualitySd : Orion.QualitySd,
								Stream.VideoQualitySd576 : Orion.QualitySd,
								Stream.VideoQualitySd540 : Orion.QualitySd,
								Stream.VideoQualitySd480 : Orion.QualitySd,
								Stream.VideoQualitySd360 : Orion.QualitySd,
								Stream.VideoQualitySd240 : Orion.QualitySd,
								Stream.VideoQualitySd144 : Orion.QualitySd,

								Stream.VideoQualityScr : Orion.QualityScr,
								Stream.VideoQualityScr4k : Orion.QualityScr1080,
								Stream.VideoQualityScr2k : Orion.QualityScr1080,
								Stream.VideoQualityScr1080 : Orion.QualityScr1080,
								Stream.VideoQualityScr720 : Orion.QualityScr720,
								Stream.VideoQualityScr576 : Orion.QualityScr,
								Stream.VideoQualityScr540 : Orion.QualityScr,
								Stream.VideoQualityScr480 : Orion.QualityScr,
								Stream.VideoQualityScr360 : Orion.QualityScr,
								Stream.VideoQualityScr240 : Orion.QualityScr,
								Stream.VideoQualityScr144 : Orion.QualityScr,

								Stream.VideoQualityCam : Orion.QualityCam,
								Stream.VideoQualityCam4k : Orion.QualityCam1080,
								Stream.VideoQualityCam2k : Orion.QualityCam1080,
								Stream.VideoQualityCam1080 : Orion.QualityCam1080,
								Stream.VideoQualityCam720 : Orion.QualityCam720,
								Stream.VideoQualityCam576 : Orion.QualityCam,
								Stream.VideoQualityCam540 : Orion.QualityCam,
								Stream.VideoQualityCam480 : Orion.QualityCam,
								Stream.VideoQualityCam360 : Orion.QualityCam,
								Stream.VideoQualityCam240 : Orion.QualityCam,
								Stream.VideoQualityCam144 : Orion.QualityCam,
							},
						},
						'codec' : {
							'orion' : {
								Orion.CodecH266 : Stream.VideoCodecH266,
								Orion.CodecH265 : Stream.VideoCodecH265,
								Orion.CodecH264 : Stream.VideoCodecH264,
								Orion.CodecH262 : Stream.VideoCodecH262,
								Orion.CodecH222 : Stream.VideoCodecH222,
								Orion.CodecAv1 : Stream.VideoCodecAv1,
								Orion.CodecVp10 : Stream.VideoCodecVp10,
								Orion.CodecVp9 : Stream.VideoCodecVp9,
								Orion.CodecVp8 : Stream.VideoCodecVp8,
								Orion.CodecDivx : Stream.VideoCodecDivx,
								Orion.CodecMpeg : Stream.VideoCodecMpeg,
								Orion.CodecWmv : Stream.VideoCodecWmv,
								Orion.CodecXvid : Stream.VideoCodecXvid,
							},
							'gaia' : {
								Stream.VideoCodecH266 : Orion.CodecH266,
								Stream.VideoCodecH265 : Orion.CodecH265,
								Stream.VideoCodecH264 : Orion.CodecH264,
								Stream.VideoCodecH262 : Orion.CodecH262,
								Stream.VideoCodecH222 : Orion.CodecH222,
								Stream.VideoCodecAv1 : Orion.CodecAv1,
								Stream.VideoCodecVp10 : Orion.CodecVp10,
								Stream.VideoCodecVp9 : Orion.CodecVp9,
								Stream.VideoCodecVp8 : Orion.CodecVp8,
								Stream.VideoCodecDivx : Orion.CodecDivx,
								Stream.VideoCodecMpeg : Orion.CodecMpeg,
								Stream.VideoCodecWmv : Orion.CodecWmv,
								Stream.VideoCodecXvid : Orion.CodecXvid,
							},
						},
						'3d' : {
							'orion' : {
								True : Stream.Video3d,
								False : Stream.Video3dNone,
							},
							'gaia' : {
								Stream.Video3d : True,
								Stream.Video3dStereo : True,
								Stream.Video3dMono : True,
								Stream.Video3dFsbs : True,
								Stream.Video3dHsbs : True,
								Stream.Video3dRsbs : True,
								Stream.Video3dFou : True,
								Stream.Video3dHou : True,
								Stream.Video3dRou : True,
								Stream.Video3dPou : True,
								Stream.Video3d180 : True,
								Stream.Video3d360 : True,
								Stream.Video3dRi : True,
								Stream.Video3dArc : True,
								Stream.Video3dAgm : True,
								Stream.Video3dNone : False,
							},
						},
					},

					'audio' : {
						'type' : {
							'orion' : {
								Orion.AudioStandard : Stream.AudioTypeOriginal,
								Orion.AudioDubbed : Stream.AudioTypeDubbed,
							},
							'gaia' : {
								Stream.AudioTypeOriginal : Orion.AudioStandard,
								Stream.AudioTypeLine : Orion.AudioDubbed,
								Stream.AudioTypeMic : Orion.AudioDubbed,
								Stream.AudioTypeDubbed : Orion.AudioDubbed,
								Stream.AudioTypeDubbedLine : Orion.AudioDubbed,
								Stream.AudioTypeDubbedMic : Orion.AudioDubbed,
								Stream.AudioTypeDubbedFan : Orion.AudioDubbed,
							},
						},
						'system' : {
							'orion' : {
								Orion.SystemDd : Stream.AudioSystemDolby,
								Orion.SystemDts : Stream.AudioSystemDts,
								Orion.SystemDig : Stream.AudioSystemDigirise,
								Orion.SystemMpeg : Stream.AudioSystemMpeg,
								Orion.SystemXiph : Stream.AudioSystemXiph,
								Orion.SystemWin : Stream.AudioSystemWindows,
								Orion.SystemApp : Stream.AudioSystemApple,
							},
							'gaia' : {
								Stream.AudioSystemDolby : Orion.SystemDd,
								Stream.AudioSystemDts : Orion.SystemDts,
								Stream.AudioSystemDigirise : Orion.SystemDig,
								Stream.AudioSystemMpeg : Orion.SystemMpeg,
								Stream.AudioSystemXiph : Orion.SystemXiph,
								Stream.AudioSystemWindows : Orion.SystemWin,
								Stream.AudioSystemApple : Orion.SystemApp,
							},
						},
						'codec' : {
							'orion' : {
								Orion.CodecAmsthd : Stream.AudioCodecThdams,
								Orion.CodecAmspls : Stream.AudioCodecPlsams,
								Orion.CodecAms : Stream.AudioCodecAms,
								Orion.CodecThd : Stream.AudioCodecThd,
								Orion.CodecPls : Stream.AudioCodecPls,
								Orion.CodecLve : Stream.AudioCodecLve,
								Orion.CodecSex : Stream.AudioCodecSex,
								Orion.CodecEx : Stream.AudioCodecEx,
								Orion.CodecAc3 : Stream.AudioCodecAc3,
								Orion.CodecAc4 : Stream.AudioCodecAc4,
								Orion.Codec70 : Stream.AudioCodec70,
								Orion.Codec9624 : Stream.AudioCodec9624,
								Orion.CodecEs : Stream.AudioCodecEsur,
								Orion.CodecNeo6 : Stream.AudioCodecNeo6,
								Orion.CodecNeox : Stream.AudioCodecNeox,
								Orion.CodecNeopc : Stream.AudioCodecNeopc,
								Orion.CodecNeo : Stream.AudioCodecNeo,
								Orion.CodecHdhra : Stream.AudioCodecHdhr,
								Orion.CodecHdma : Stream.AudioCodecHdma,
								Orion.CodecNx : Stream.AudioCodecNx,
								Orion.CodecHx : Stream.AudioCodecHx,
								Orion.CodecSs : Stream.AudioCodecSurs,
								Orion.CodecCon : Stream.AudioCodecCon,
								Orion.CodecIna : Stream.AudioCodecIna,
								Orion.CodecPyf: Stream.AudioCodecPyf,
								Orion.CodecX : Stream.AudioCodecX,
								Orion.CodecDra : Stream.AudioCodecDra,
								Orion.CodecAac : Stream.AudioCodecAac,
								Orion.CodecMp3 : Stream.AudioCodecMp3,
								Orion.CodecMp2 : Stream.AudioCodecMp2,
								Orion.CodecFlac : Stream.AudioCodecFlac,
								Orion.CodecWma : Stream.AudioCodecWma,
								Orion.CodecAlac : Stream.AudioCodecAlac,
								Orion.CodecPcm : Stream.AudioCodecPcm,
							},
							'gaia' : {
								Stream.AudioCodecThdams : Orion.CodecAmsthd,
								Stream.AudioCodecPlsams : Orion.CodecAmspls,
								Stream.AudioCodecAms : Orion.CodecAms,
								Stream.AudioCodecThd : Orion.CodecThd,
								Stream.AudioCodecPls : Orion.CodecPls,
								Stream.AudioCodecLve : Orion.CodecLve,
								Stream.AudioCodecSex : Orion.CodecSex,
								Stream.AudioCodecEx : Orion.CodecEx,
								Stream.AudioCodecAc3 : Orion.CodecAc3,
								Stream.AudioCodecAc4 : Orion.CodecAc4,
								Stream.AudioCodec70 : Orion.Codec70,
								Stream.AudioCodec9624 : Orion.Codec9624,
								Stream.AudioCodecEsur : Orion.CodecEs,
								Stream.AudioCodecNeo6 : Orion.CodecNeo6,
								Stream.AudioCodecNeox : Orion.CodecNeox,
								Stream.AudioCodecNeopc : Orion.CodecNeopc,
								Stream.AudioCodecNeo : Orion.CodecNeo,
								Stream.AudioCodecHdhr : Orion.CodecHdhra,
								Stream.AudioCodecHdma : Orion.CodecHdma,
								Stream.AudioCodecNx : Orion.CodecNx,
								Stream.AudioCodecHx : Orion.CodecHx,
								Stream.AudioCodecSurs : Orion.CodecSs,
								Stream.AudioCodecCon : Orion.CodecCon,
								Stream.AudioCodecIna : Orion.CodecIna,
								Stream.AudioCodecPyf : Orion.CodecPyf,
								Stream.AudioCodecX : Orion.CodecX,
								Stream.AudioCodecDra : Orion.CodecDra,
								Stream.AudioCodecAac : Orion.CodecAac,
								Stream.AudioCodecMp3 : Orion.CodecMp3,
								Stream.AudioCodecMp2 : Orion.CodecMp2,
								Stream.AudioCodecFlac : Orion.CodecFlac,
								Stream.AudioCodecWma : Orion.CodecWma,
								Stream.AudioCodecAlac : Orion.CodecAlac,
								Stream.AudioCodecPcm : Orion.CodecPcm,
							},
						},
					},

					'subtitle' : {
						'type' : {
							'orion' : {
								Orion.SubtitleSoft : Stream.SubtitleTypeSoft,
								Orion.SubtitleHard : Stream.SubtitleTypeHard,
							},
							'gaia' : {
								Stream.SubtitleTypeSoft : Orion.SubtitleSoft,
								Stream.SubtitleTypeHard : Orion.SubtitleHard,
							},
						},
					},

					'file' : {
						'pack' : {
							'orion' : {
								True : True,
								False : Stream.FilePackNone,
							},
							'gaia' : {
								Stream.FilePackShow : True,
								Stream.FilePackSeason : True,
								Stream.FilePackEpisode : True,
								Stream.FilePackCollection : True,
								Stream.FilePackNone : False,
							},
						},
					},

					'source' : {
						'type' : {
							'orion' : {
								Orion.StreamTorrent : Stream.SourceTypeTorrent,
								Orion.StreamUsenet : Stream.SourceTypeUsenet,
								Orion.StreamHoster : Stream.SourceTypeHoster,
							},
							'gaia' : {
								Stream.SourceTypeTorrent : Orion.StreamTorrent,
								Stream.SourceTypeUsenet : Orion.StreamUsenet,
								Stream.SourceTypeHoster : Orion.StreamHoster,
							},
						},
					},
				}

			try: return Orionoid.Maps[category][attribute][mode][value]
			except: return value if default == 'value' else default

		##############################################################################
		# STREAMS - UPDATE
		##############################################################################

		def _streamIgnore(self, stream):
			try:
				link = stream.linkPrimary()

				# Locally cached streams - already submitted on the previous run.
				# Still keep those marked as AccessCacheExpired, since all newley scraped links will have this value.
				# Only check timestamps.
				cache = stream.infoCache()
				if cache and not cache == Stream.AccessCacheExpired: return True

				# Exclude duplicates
				# Check if True, since the function can also return "orion".
				# "orion" duplicate links are marked as duplicate solely because there is another duplicate link that comes from Orion and should always have preference.
				# However, the locally retrieved duplicate link might contain additional info (eg: full filename, updated seeds/leeches, etc), andshould therefore still be submitted to Orion.
				if not stream.exclusionDuplicateHas(): return True # The stream was not completely processed (eg: scrape cancled).
				if stream.exclusionDuplicate() is True: return True

				# Keyword exclusions
				if not stream.exclusionKeywordHas(): return True # The stream was not completely processed (eg: scrape cancled).
				if stream.exclusionKeyword(): return True

				# Metadata exclusions
				if not stream.exclusionMetadataHas(): return True # The stream was not completely processed (eg: scrape cancled).
				if stream.exclusionMetadata(): return True

				# Format exclusions
				if not stream.exclusionFormatHas(): return True # The stream was not completely processed (eg: scrape cancled).
				if stream.exclusionFormat(): return True

				# Fake exclusions
				if not stream.exclusionFakeHas(): return True # The stream was not completely processed (eg: scrape cancled).
				if stream.exclusionFake(): return True

				# Blocked domains
				# Probably does not work. Many guarded links or text-paste services
				# Check core.py -> hostersBlocked()
				if not stream.exclusionBlockedHas(): return True # The stream was not completely processed (eg: scrape cancled).
				if stream.exclusionBlocked(): return True

				# Local streams
				if stream.sourceTypeLocal(): return True

				# Premium streams
				# Debrid, EasyNews, Emby/Jellyfin.
				if stream.sourceTypePremium(): return True

				# Not magnet, http, ftp
				if not Networker.linkIs(link = link, magnet = True): return True

				# Exact searches.
				if stream.infoExact(): return True

				# Custom added links.
				if stream.infoCustom(): return True

				# YouTube links (from Gaia's hoster provider) - too many incorrect results (correct file name, but contains eg reaction/fan videos)
				provider = stream.sourceProvider()
				if provider and provider.lower() == 'youtube': return True

				if not stream.sourceTypeTorrent():
					# Not FQDN or IP address (eg: http://localhost or http://downloads)
					if not '.' in Networker.linkDomain(link = link, subdomain = True, topdomain = True, ip = True): return True

					# Streams from member websites
					if Networker.linkDomain(link = link, subdomain = False, topdomain = False, ip = True).lower() in Orionoid.IgnoreDomains: return True

					# Streams with cookies
					cookies = Networker.linkHeaders(link = link)
					if cookies:
						for cookie in cookies.keys():
							for key in Orionoid.IgnoreHeaders:
								if Regex.match(data = cookie, expression = key): return True

					# Streams with headers
					headers = Networker.linkHeaders(link = link)
					if headers:
						for header in headers.keys():
							for key in Orionoid.IgnoreHeaders:
								if Regex.match(data = header, expression = key): return True

					# Links that will expire.
					#	https://vidembed.cc/embedplus?id=MzQwMA==&token=2rgps4mw7KV9j9oXn7zNkg&expires=1636728884
					parameters = Networker.linkParameters(link = link, decode = True)
					if 'expire' in parameters or 'expires' in parameters or 'expiration' in parameters: return True

					# Very long links, which are most likely invalid or contain cookie/session data
					if len(link) > 1024: return True
			except:
				Logger.error()
				return True
			return False

		def _streamUpdate(self, meta, streams):
			item = self._streamUpdateMeta(meta)
			item['filter'] = {'default' : Stream.thresholdNameDefault(), 'threshold' : Stream.thresholdName()}
			item['streams'] = []

			new = self.structureNew()

			for stream in streams:
				try:
					stream = stream['stream']
					if not self._streamIgnore(stream):
						if new: data = self._streamUpdateNew(stream)
						else: data = self._streamUpdateOld(stream)
						if data: item['streams'].append(data)
				except:
					Logger.error()

			if item['streams']: return OrionItem(data = item).update()
			return False

		def _streamUpdateOld(self, stream):
			try:
				data = {'links' : None, 'stream' : {}, 'access' : {}, 'file' : {}, 'meta' : {}, 'video' : {}, 'audio' : {}, 'subtitle' : {}}

				data['links'] = stream.linkPrimary()

				data['stream']['type'] = self.map(value = stream.sourceType(), category = 'source', attribute = 'type', mode = 'gaia')
				data['stream']['origin'] = stream.sourceOrigin()
				data['stream']['source'] = stream.sourceProvider()
				data['stream']['hoster'] = stream.sourceHoster()
				data['stream']['seeds'] = stream.sourceSeeds()
				data['stream']['time'] = stream.sourceTime(time = Stream.TimeNone, exact = Stream.ExactYes)

				data['access']['direct'] = stream.accessTypeDirect()
				data['access']['premiumize'] = stream.accessCachePremiumize(exact = Stream.ExactYes)
				data['access']['offcloud'] = stream.accessCacheOffcloud(exact = Stream.ExactYes)
				data['access']['realdebrid'] = stream.accessCacheRealdebrid(exact = Stream.ExactYes)
				data['access']['alldebrid'] = stream.accessCacheAlldebrid(exact = Stream.ExactYes)

				data['file']['hash'] = stream.hash()
				data['file']['name'] = stream.fileName()
				data['file']['pack'] = self.map(value = stream.filePack(), category = 'file', attribute = 'pack', mode = 'gaia')
				if stream.filePack():
					data['file']['size'] = {}
					size = stream.fileSize(estimate = True)
					if size: data['file']['size']['single'] = size
					size = stream.fileSize(estimate = False)
					if size: data['file']['size']['pack'] = size
				else:
					data['file']['size'] = stream.fileSize(estimate = True)

				data['meta']['release'] = stream.releaseType()
				data['meta']['uploader'] = stream.releaseGroup()[0] if stream.releaseGroup() else None
				data['meta']['edition'] = stream.releaseEdition()

				data['video']['quality'] = self.map(value = stream.videoQuality(), category = 'video', attribute = 'quality', mode = 'gaia', default = 'value')
				data['video']['codec'] = self.map(value = stream.videoCodec(), category = 'video', attribute = 'codec', mode = 'gaia', default = 'value')
				data['video']['3d'] = self.map(value = stream.video3d(), category = 'video', attribute = '3d', mode = 'gaia', default = False)

				data['audio']['type'] = self.map(value = stream.audioType(), category = 'audio', attribute = 'type', mode = 'gaia', default = 'value')
				data['audio']['channels'] = stream.audioChannels()
				data['audio']['system'] = self.map(value = stream.audioSystem(), category = 'audio', attribute = 'system', mode = 'gaia', default = 'value')
				data['audio']['codec'] = self.map(value = stream.audioCodec(), category = 'audio', attribute = 'codec', mode = 'gaia', default = 'value')
				data['audio']['languages'] = stream.audioLanguage()

				data['subtitle']['type'] = self.map(value = stream.subtitleType(), category = 'subtitle', attribute = 'type', mode = 'gaia', default = 'value')
				data['subtitle']['languages'] = stream.subtitleLanguage()

				if stream.idOrionHas():
					idData = Stream.idOrionDataGenerate(
						link				= data['links'],
						hash				= data['file']['hash'],

						videoQuality		= data['video']['quality'],
						videoCodec			= data['video']['codec'],
						video3d				= data['video']['3d'],

						audioType			= data['audio']['type'],
						audioSystem			= data['audio']['system'],
						audioCodec			= data['audio']['codec'],
						audioChannels		= data['audio']['channels'],
						audioLanguage		= data['audio']['languages'],

						subtitleType		= data['subtitle']['type'],
						subtitleLanguage	= data['subtitle']['languages'],

						fileName			= data['file']['name'],
						fileSize			= stream.fileSize(estimate = True), # Use the estimated size, to invalidate the Orion ID (force = True) if the new estimated pack size changed.
						filePack			= data['file']['pack'],

						releaseType			= data['meta']['release'],
						releaseEdition		= data['meta']['edition'],
						releaseGroup		= data['meta']['uploader'],

						sourceType			= data['stream']['type'],
						sourceTime			= data['stream']['time'],
						sourceSeeds			= data['stream']['seeds'],

						sourceOrigin		= data['stream']['origin'],
						sourceProvider		= data['stream']['source'],
						sourceHoster		= data['stream']['hoster'],
					)

					# If a stream has an Orion ID, Orion only submits the debrid cache status and ignores all other attributes.
					# In case the Orionoid provider extracts the metadata locally from filename again, the original metadata from Orion might be different to this newly extracted metadata.
					# In such a case, force Orion to submit the new metadata.
					if not idData == stream.idOrionData(): data['force'] = True

					data['id'] = stream.idOrionStream()

				result = {}
				for key1, value1 in data.items():
					if not value1 is None:
						if Tools.isDictionary(value1):
							result[key1] = {}
							for key2, value2 in value1.items():
								if not value2 is None:
									result[key1][key2] = value2
						else:
							result[key1] = value1

				return result
			except:
				Logger.error()
				return None

		# gaiaremove - update and test with new Orion structure change.
		def _streamUpdateNew(self, stream):
			try:
				result = stream.dataExport()
				del result['meta']
				del result['info']
				del result['stream']
				del result['provider']
				del result['segment']
				return result
			except:
				Logger.error()
				return None

		def _streamUpdateMeta(self, meta):
			item = {}
			item['type'] = type = Orionoid.TypeShow if 'tvshowtitle' in meta else Orionoid.TypeMovie

			if item['type'] == Orionoid.TypeMovie:
				item['movie'] = {}

				item['movie']['id'] = {}
				try: item['movie']['id']['imdb'] = meta['imdb'].replace('tt', '')
				except: pass
				try: item['movie']['id']['tmdb'] = meta['tmdb']
				except: pass

				item['movie']['meta'] = {}
				try: item['movie']['meta']['title'] = meta['title']
				except: pass
				try: item['movie']['meta']['year'] = int(meta['year'])
				except: pass
			elif item['type'] == Orionoid.TypeShow:
				item['show'] = {}
				item['episode'] = {}

				item['show']['id'] = {}
				try: item['show']['id']['imdb'] = meta['imdb'].replace('tt', '')
				except: pass
				try: item['show']['id']['tmdb'] = meta['tvdb']
				except: pass

				item['show']['meta'] = {}
				try: item['show']['meta']['title'] = meta['tvshowtitle']
				except:
					try: item['show']['meta']['title'] = meta['title']
					except: pass
				try: item['show']['meta']['year'] = int(meta['tvshowyear'])
				except:
					try: item['show']['meta']['title'] = meta['year']
					except: pass

				item['episode']['meta'] = {}
				try: item['episode']['meta']['title'] = meta['title']
				except:
					try: item['episode']['meta']['title'] = meta['tvshowtitle']
					except: pass
				try: item['episode']['meta']['year'] = int(meta['year'])
				except:
					try: item['episode']['meta']['title'] = meta['tvshowyear']
					except: pass

				item['episode']['number'] = {}
				season = Converter.unicode(meta['season']).lower().replace('season', '').replace(' ', '')
				try: item['episode']['number']['season'] = int(season)
				except:
					try: item['episode']['number']['season'] = Converter.roman(season)
					except: pass
				episode = Converter.unicode(meta['episode']).lower().replace('episode', '').replace(' ', '')
				try: item['episode']['number']['episode'] = int(episode)
				except:
					try: item['episode']['number']['episode'] = Converter.roman(episode)
					except: pass

			return item

		def streamUpdate(self, meta, streams, wait = False):
			if meta and streams:
				thread = Pool.thread(target = self._streamUpdate, args = (meta, streams))
				thread.start()
				if wait: thread.join()

		def streamRetrieve(self, type, idImdb = None, idTmdb = None, idTvdb = None, idTvrage = None, idTrakt = None, numberSeason = None, numberEpisode = None, title = None, year = None, query = None, verify = False):
			limit = 1 if verify else Orion.FilterSettings
			result = None
			if not query == None:
				result = self.mOrion.streams(type = type, query = query, limitCount = limit, limitRetry = limit, details = True)
			elif type == Orionoid.TypeMovie:
				if not idImdb is None:
					result = self.mOrion.streams(type = type, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTvrage = idTvrage, idTrakt = idTrakt, limitCount = limit, limitRetry = limit, details = True)
				elif not title is None:
					query = title
					if not year is None: query += ' ' + Converter.unicode(year)
					result = self.mOrion.streams(type = type, query = query, limitCount = limit, limitRetry = limit, details = True)
			elif type == Orionoid.TypeShow:
				if not numberSeason is None and not numberEpisode is None:
					if not idImdb is None:
						result = self.mOrion.streams(type = type, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTvrage = idTvrage, idTrakt = idTrakt, numberSeason = numberSeason, numberEpisode = numberEpisode, limitCount = limit, limitRetry = limit, details = True)
					elif not title == None:
						query = title + ' ' + Converter.unicode(numberSeason) + ' ' + Converter.unicode(numberEpisode)
						result = self.mOrion.streams(type = type, query = query, limitCount = limit, limitRetry = limit, details = True)
			return result

		def streamsCount(self, streams):
			return self.mOrion.streamsCount(streams = streams, quality = self.mOrion.FilterSettings)

		def streamVote(self, idItem, idStream, vote = VoteUp, notification = False):
			if idItem and idStream: self.mOrion.streamVote(idItem = idItem, idStream = idStream, vote = vote, notification = notification)

		def streamRemove(self, idItem, idStream, notification = False):
			if idItem and idStream: self.mOrion.streamRemove(idItem = idItem, idStream = idStream, notification = notification)

		##############################################################################
		# HASHES
		##############################################################################

		def hashes(self, links, chunked = False):
			self._hashesLock()
			for link in links:
				if not link in self.mHashesQueue and not link in self.mHashesCompleted:
					self.mHashesQueue.append(link)
			self._hashesUnlock()

			if (not chunked and len(self.mHashesQueue) > 0) or (chunked and len(self.mHashesQueue) >= Orionoid.ChunkLimit and not self._hashesRunning()):
				thread = Pool.thread(target = self._hashesRetrieve)
				self._hashesLock()
				self.mHashesThreads.append(thread)
				self._hashesUnlock()
				thread.start()
			if not chunked: self._hashesJoin()

			result = {}
			for link in links:
				if link in self.mHashesCompleted:
					result[link] = self.mHashesCompleted[link]
			return result

		def _hashesRetrieve(self):
			links = Tools.copy(self.mHashesQueue)
			self._hashesLock()
			self.mHashesQueue = []
			self._hashesUnlock()

			hashes = self.mOrion.containerHashes(links = links)
			self._hashesLock()
			self.mHashesCompleted.update(hashes)
			for link in links:
				if not link in self.mHashesCompleted:
					self.mHashesCompleted[link] = None
			self._hashesUnlock()

		def _hashesLock(self):
			self.mHashesLock.acquire()

		def _hashesUnlock(self):
			try: self.mHashesLock.release()
			except: pass

		def _hashesRunning(self):
			return any(thread.is_alive() for thread in self.mHashesThreads)

		def _hashesJoin(self):
			try: [thread.join() for thread in self.mHashesThreads]
			except: pass

		##############################################################################
		# IDENTIFIERS
		##############################################################################

		def identifiers(self, links, chunked = False):
			self._identifiersLock()
			for link in links:
				if not link in self.mIdentifiersQueue and not link in self.mIdentifiersCompleted:
					self.mIdentifiersQueue.append(link)
			self._identifiersUnlock()

			if (not chunked and len(self.mIdentifiersQueue) > 0) or (chunked and len(self.mIdentifiersQueue) >= Orionoid.ChunkLimit and not self._identifiersRunning()):
				thread = Pool.thread(target = self._identifiersRetrieve)
				self._identifiersLock()
				self.mIdentifiersThreads.append(thread)
				self._identifiersUnlock()
				thread.start()
			if not chunked: self._identifiersJoin()

			result = {}
			for link in links:
				if link in self.mIdentifiersCompleted:
					result[link] = self.mIdentifiersCompleted[link]
			return result

		def _identifiersRetrieve(self):
			links = Tools.copy(self.mIdentifiersQueue)
			self._identifiersLock()
			self.mIdentifiersQueue = []
			self._identifiersUnlock()

			identifiers = self.mOrion.containerIdentifiers(links = links)
			self._identifiersLock()
			self.mIdentifiersCompleted.update(identifiers)
			for link in links:
				if not link in self.mIdentifiersCompleted:
					self.mIdentifiersCompleted[link] = None
			self._identifiersUnlock()

		def _identifiersLock(self):
			self.mIdentifiersLock.acquire()

		def _identifiersUnlock(self):
			try: self.mIdentifiersLock.release()
			except: pass

		def _identifiersRunning(self):
			return any(thread.is_alive() for thread in self.mIdentifiersThreads)

		def _identifiersJoin(self):
			try: [thread.join() for thread in self.mIdentifiersThreads]
			except: pass

		##############################################################################
		# DEBRID
		##############################################################################

		def debridSupport(self, type = None, status = None):
			# Exclude RealDebrid status checking, since RealDebrid often says hosters are down (eg: NitroFlare, RuTube, etc), although they correctly resolve.
			# UPDATE: Seesm to be the same case with AllDebrid and dropapk.to/drop.download.
			# Just retrieve all services and ignore the status.
			# If a service is truely down, resolving will fail and the user will just have to select another debrid or link and try again.
			#if status is None: status = '-realdebrid'

			return self.mOrion.debridSupport(type = type, status = status, details = False)

		def debridLookup(self, item, type = None):
			return self.mOrion.debridLookup(item = item, type = type)

		def debridResolve(self, link = None, type = None, container = None, containerData = None, containerName = None, containerType = None, containerSize = None, file = Orion.FileOriginal, output = Orion.OutputList, details = True):
			# By default try to fully resolve the original file.
			# Some debrid services, like AllDebrid and DebridLink, can return a unique Orion link with data to further resolve the link (especially hoster links).
			# On AllDebrid, when accessing this Orion link, it will resolve hoster links and process them, which can take some time (AllDebrid has a "delayed" attribute).
			# Kodi's player's cURL has a default timeout of 30 seconds, which might not be enough to handle this final AllDebrid resolving. then the player times out and fails to play.
			# Instead, try to do this final resolving here already (while the playback loading window shows), in order to reduce the time needed when Kodi's cURL tries to establish the connection.
			return self.mOrion.debridResolve(link = link, type = type, container = container, containerData = containerData, containerName = containerName, containerType = containerType, containerSize = containerSize, file = file, output = output, details = details)

except ImportError:

	class Orionoid(object):

		Id = 'script.module.orion'
		Name = 'Orion'
		Scraper = 'oriscrapers'

		SettingsAddonInstallation = 'stream.orion.installation'
		SettingsAddonConnection = 'stream.orion.connection'
		SettingsAddonSettings = 'stream.orion.settings'

		PropertyAuthentication = 'GaiaOrionAuthentication'

		##############################################################################
		# INITIALIZE
		##############################################################################

		def initialize(self, background = False, refresh = False, settings = False, external = False):
			pass

		##############################################################################
		# UNINSTALL
		##############################################################################

		@classmethod
		def uninstall(self, settings = False):
			from lib.modules.interface import Dialog
			Dialog.confirm(title = 35400, message = 35634)
			if settings: self.settingsAddon()

		##############################################################################
		# SETTINGS
		##############################################################################

		@classmethod
		def settingsAddon(self, settings = False):
			id = None
			if self.addonInstalled(): id = Orionoid.SettingsAddonSettings if settings else Orionoid.SettingsAddonConnection
			else: id = Orionoid.SettingsAddonInstallation
			Settings.launch(id)

		##############################################################################
		# ADDON
		##############################################################################

		@classmethod
		def addonId(self):
			return Orionoid.Id

		@classmethod
		def addonInstalled(self):
			return Extension.installed(id = Orionoid.Id)

		@classmethod
		def addonEnable(self, refresh = False, settings = False):
			result = Extension.enable(id = Orionoid.Id, refresh = refresh)
			if settings: self.settingsAddon()
			return result

		@classmethod
		def addonDisable(self, refresh = False):
			return Extension.disable(id = Orionoid.Id, refresh = refresh)

		##############################################################################
		# ACCOUNT
		##############################################################################

		def accountEnabled(self, external = False):
			return False

		def accountValid(self, enabled = False, external = False):
			return False

		def accountAvailable(self):
			return False

		def accountAllow(self):
			return False

		@classmethod
		def accountAuthenticateBusy(self):
			try: return bool(System.windowPropertyGet(Orionoid.PropertyAuthentication))
			except: return False

		@classmethod
		def accountAuthenticateWait(self):
			while self.accountAuthenticateBusy():
				Time.sleep(0.1)

	from lib.modules.tools import Logger
	Logger.log('Orion addon not installed or enabled', type = Logger.TypeDebug)

except Exception as error:

	class Orionoid(object):
		Id = 'script.module.orion'
		Name = 'Orion'
		Scraper = 'oriscrapers'

	if not str(error) == 'lib':
		from lib.modules.tools import Logger
		Logger.error()
