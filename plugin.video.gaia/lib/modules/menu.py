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

from lib.modules.tools import System, Tools, Settings, Media, Logger
from lib.meta.menu import MetaMenu

class Menu(object):

	Action				= 'menu'

	MenuSearch			= 'search'
	MenuTool			= 'tool'

	ContentSetting		= 'setting'
	ContentService		= 'service'
	ContentNetwork		= 'network'
	ContentDownload		= 'download'
	ContentLibrary		= 'library'
	ContentVerification	= 'verification'
	ContentExtension	= 'extension'
	ContentMetadata		= 'metadata'
	ContentUtility		= 'utility'

	ParameterMenu		= 'menu'
	ParameterContent	= 'content'
	ParameterCategory	= 'category'
	ParameterLabel		= 'label'
	ParameterImage		= 'image'
	ParameterAction		= 'action'
	ParameterCommand	= 'command'
	ParameterFolder		= 'folder'
	ParameterExtra		= 'extra'

	ServiceOrion		= 'orion'
	ServicePremiumize	= 'premiumize'
	ServiceOffcloud		= 'offcloud'
	ServiceRealdebrid	= 'realdebrid'
	ServiceEasynews		= 'easynews'
	ServiceEmby			= 'emby'
	ServiceJellyfin		= 'jellyfin'
	ServiceCrescrapers	= 'crescrapers'
	ServiceOpescrapers	= 'opescrapers'
	ServiceFenscrapers	= 'fenscrapers'
	ServiceOatscrapers	= 'oatscrapers'
	ServiceLamscrapers	= 'lamscrapers'
	ServiceCivscrapers	= 'civscrapers'
	ServiceGloscrapers	= 'gloscrapers'
	ServiceUniscrapers	= 'uniscrapers'
	ServiceNanscrapers	= 'nanscrapers'
	ServiceResolveurl	= 'resolveurl'
	ServiceUrlresolver	= 'urlresolver'
	ServiceElementum	= 'elementum'
	ServiceQuasar		= 'quasar'
	ServiceYoutube		= 'youtube'
	ServiceUpnext		= 'upnext'
	ServiceTmdbhelper	= 'tmdbhelper'
	ServiceVpnmanager	= 'vpnmanager'

	CategoryError		= 'error'
	CategoryBackup		= 'backup'
	CategoryPremium		= 'premium'
	CategoryScraper		= 'scraper'
	CategoryResolver	= 'resolver'
	CategoryInformer	= 'informer'
	CategoryDownloader	= 'downloader'
	CategoryUtility		= 'utility'
	CategoryDownloads	= 'downloads'
	CategoryInstant		= 'instant'
	CategoryCloud		= 'cloud'
	CategorySpeed		= 'speed'
	CategoryVpn			= 'vpn'
	CategoryManual		= 'manual'
	CategoryCache		= 'cache'
	CategoryBrowse		= 'browse'
	CategoryList		= 'list'
	CategoryClear		= 'clear'
	CategoryLocal		= 'local'
	CategoryAvailable	= 'available'
	CategoryInstalled	= 'installed'
	CategoryLog			= 'log'
	CategorySystem		= 'system'
	CategoryInformation	= 'information'

	Instance			= None

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		pass

	@classmethod
	def instance(self,):
		if Menu.Instance is None: Menu.Instance = self()
		return Menu.Instance

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		if settings: Menu.Instance = None

	##############################################################################
	# MENU
	##############################################################################

	# Add "action" parameter, so that it is not included in "parameters" when called from addon.py. Important for the "search" endpoint.
	def menu(self, action = None, menu = None, content = None, media = None, niche = None, **parameters):
		if menu == Menu.MenuTool:
			return self._menuTool(content = content, **parameters)
		else:
			instance = MetaMenu.instance(media = media, niche = niche)
			if menu == Menu.MenuSearch: return instance.search(**parameters)
			else: return instance.menu(menu = menu, content = content, **parameters)

	def _menuTool(self, content = None, category = None, **parameters):
		if category and not Tools.isArray(category): category = [category]
		if content == Menu.ContentSetting: items = self._menuSetting(category = category, **parameters)
		elif content == Menu.ContentService: items = self._menuService(category = category, **parameters)
		elif content == Menu.ContentNetwork: items = self._menuNetwork(category = category, **parameters)
		elif content == Menu.ContentDownload: items = self._menuDownload(category = category, **parameters)
		elif content == Menu.ContentLibrary: items = self._menuLibrary(category = category, **parameters)
		elif content == Menu.ContentVerification: items = self._menuVerification(category = category, **parameters)
		elif content == Menu.ContentExtension: items = self._menuExtension(category = category, **parameters)
		elif content == Menu.ContentMetadata: items = self._menuMetadata(category = category, **parameters)
		elif content == Menu.ContentUtility: items = self._menuUtility(category = category, **parameters)
		else: items = self._menuMain(**parameters)
		if items: self._build(items = items)

	def _menuMain(self, **parameters):
		from lib.modules.api import Api
		from lib.modules.shortcut import Shortcut
		from lib.modules.interface import Format, Icon

		donation = Format.color(33505, 'FFB700')
		items = [
			self._item(label = 33011,		image = 'settings',		content = Menu.ContentSetting),
			self._item(label = 33502,		image = 'services',		content = Menu.ContentService),
			self._item(label = 33719,		image = 'network',		content = Menu.ContentNetwork),
			self._item(label = 32009,		image = 'downloads',	content = Menu.ContentDownload),
			self._item(label = 35170,		image = 'library',		content = Menu.ContentLibrary),
			self._item(label = 33017,		image = 'verification',	content = Menu.ContentVerification),
			self._item(label = 33720,		image = 'extensions',	content = Menu.ContentExtension),
			self._item(label = 33015,		image = 'metadata',		content = Menu.ContentMetadata),
			self._item(label = 33989,		image = 'clean',		action = 'cleanup'),
			self._item(label = 35330,		image = 'utility',		content = Menu.ContentUtility),
			self._item(label = donation,	image = 'donations',	action = 'donations',				icon = Icon.SpecialDonations),
		]

		if Api.lotteryValid(): items.insert(0, self._item(label = 33876, image = 'tickets', action = 'lotteryVoucher'))

		shortcut = MetaMenu.instance()._menuShortcut(location = Shortcut.LocationTool)
		if shortcut: items.insert(0, shortcut)

		return items

	def _menuSetting(self, category = None, **parameters):
		items = []

		if category is None:
			items = [
				self._item(label = 33894,	image = 'settingsadvanced',		action = 'settingsAdvanced'),
				self._item(label = 33893,	image = 'settingswizard',		action = 'settingsWizard'),
				self._item(label = 35269,	image = 'settingsoptimization',	action = 'settingsOptimization'),
				self._item(label = 33773,	image = 'settingsbackup',		content = Menu.ContentSetting,		category = Menu.CategoryBackup),
			]
		elif Menu.CategoryBackup in category:
			items = [
				self._item(label = 33800,	image = 'backupautomatic',		action = 'backupAutomatic'),
				self._item(label = 33774,	image = 'backupimport',			action = 'backupImport'),
				self._item(label = 35212,	image = 'backupexport',			action = 'backupExport'),
			]
		return items

	def _menuService(self, category = None, **parameters):
		items = []

		if not category:
			items = [
				self._item(label = 35400,	image = 'orion',			content = Menu.ContentService,		category = Menu.ServiceOrion),
				self._item(label = 33768,	image = 'premium',			content = Menu.ContentService,		category = Menu.CategoryPremium),
				self._item(label = 33749,	image = 'scraper',			content = Menu.ContentService,		category = Menu.CategoryScraper),
				self._item(label = 35328,	image = 'change',			content = Menu.ContentService,		category = Menu.CategoryResolver),
				self._item(label = 35822,	image = 'informer',			content = Menu.ContentService,		category = Menu.CategoryInformer),
				self._item(label = 35329,	image = 'downloads',		content = Menu.ContentService,		category = Menu.CategoryDownloader),
				self._item(label = 35330,	image = 'utility',			content = Menu.ContentService,		category = Menu.CategoryUtility),
			]

		elif Menu.CategoryPremium in category:
			items = [
				self._item(label = 33566,	image = 'premiumize',		content = Menu.ContentService,		category = Menu.ServicePremiumize),
				self._item(label = 35200,	image = 'offcloud',			content = Menu.ContentService,		category = Menu.ServiceOffcloud),
				self._item(label = 33567,	image = 'realdebrid',		content = Menu.ContentService,		category = Menu.ServiceRealdebrid),
				self._item(label = 33794,	image = 'easynews',			content = Menu.ContentService,		category = Menu.ServiceEasynews),
				self._item(label = 35551,	image = 'emby',				content = Menu.ContentService,		category = Menu.ServiceEmby),
				self._item(label = 35682,	image = 'jellyfin',			content = Menu.ContentService,		category = Menu.ServiceJellyfin),
			]

		elif Menu.CategoryScraper in category:
			if len(category) == 1:
				items = [
					self._item(label = 36086,	image = 'crescrapers',		content = Menu.ContentService,		category = [Menu.CategoryScraper, Menu.ServiceCrescrapers]),
					self._item(label = 35548,	image = 'opescrapers',		content = Menu.ContentService,		category = [Menu.CategoryScraper, Menu.ServiceOpescrapers]),
					self._item(label = 33318,	image = 'fenscrapers',		content = Menu.ContentService,		category = [Menu.CategoryScraper, Menu.ServiceFenscrapers]),
					self._item(label = 33321,	image = 'oatscrapers',		content = Menu.ContentService,		category = [Menu.CategoryScraper, Menu.ServiceOatscrapers]),
					self._item(label = 35431,	image = 'lamscrapers',		content = Menu.ContentService,		category = [Menu.CategoryScraper, Menu.ServiceLamscrapers]),
					self._item(label = 35504,	image = 'civscrapers',		content = Menu.ContentService,		category = [Menu.CategoryScraper, Menu.ServiceCivscrapers]),
					self._item(label = 35530,	image = 'gloscrapers',		content = Menu.ContentService,		category = [Menu.CategoryScraper, Menu.ServiceGloscrapers]),
					self._item(label = 35359,	image = 'uniscrapers',		content = Menu.ContentService,		category = [Menu.CategoryScraper, Menu.ServiceUniscrapers]),
					self._item(label = 35349,	image = 'nanscrapers',		content = Menu.ContentService,		category = [Menu.CategoryScraper, Menu.ServiceNanscrapers]),
				]
			else:
				from lib.modules import tools

				module = None
				service = category[-1]

				if service == Menu.ServiceCrescrapers: module = tools.CreScrapers
				elif service == Menu.ServiceOpescrapers: module = tools.OpeScrapers
				elif service == Menu.ServiceFenscrapers: module = tools.FenScrapers
				elif service == Menu.ServiceOatscrapers: module = tools.OatScrapers
				elif service == Menu.ServiceLamscrapers: module = tools.LamScrapers
				elif service == Menu.ServiceCivscrapers: module = tools.CivScrapers
				elif service == Menu.ServiceGloscrapers: module = tools.GloScrapers
				elif service == Menu.ServiceUniscrapers: module = tools.UniScrapers
				elif service == Menu.ServiceNanscrapers: module = tools.NanScrapers

				if module and module.installed(): items.append(self._item(label = 33011, image = '%ssettings' % service, action = '%sSettings' % service))
				else: items.append(self._item(label = 33474, image = '%sinstall' % service, action = '%sInstall' % service))

		elif Menu.CategoryResolver in category:
			if len(category) == 1:
				items = [
					self._item(label = 35310,	image = 'resolveurl',		content = Menu.ContentService,		category = [Menu.CategoryResolver, Menu.ServiceResolveurl]),
					self._item(label = 33747,	image = 'urlresolver',		content = Menu.ContentService,		category = [Menu.CategoryResolver, Menu.ServiceUrlresolver]),
				]
			else:
				from lib.modules import tools

				module = None
				service = category[-1]

				if service == Menu.ServiceResolveurl: module = tools.ResolveUrl
				elif service == Menu.ServiceUrlresolver: module = tools.UrlResolver

				if module and module.installed(): items.append(self._item(label = 33011, image = '%ssettings' % service, action = '%sSettings' % service))
				else: items.append(self._item(label = 33474, image = '%sinstall' % service, action = '%sInstall' % service))

		elif Menu.CategoryInformer in category:
			from lib.informers import Informer
			if len(category) == 1:
				for instance in Informer.instances(kodi = False):
					id = instance.id()
					items.append(self._item(label = instance.name(), image = id, content = Menu.ContentService, category = [Menu.CategoryInformer, id]))
			else:
				service = category[-1]
				informer = Informer.instance(id = service)

				if informer and informer.installed():
					items.extend([
						self._item(label = 33256,	image = '%slaunch' % service,		action = 'informerLaunch',		id = service),
						self._item(label = 33011,	image = '%ssettings' % service,		action = 'informerSettings',	id = service),
					])
				else:
					items.append(self._item(label = 33474, image = '%sinstall' % service, action = 'informerInstall', id = service))

		elif Menu.CategoryDownloader in category:
			if len(category) == 1:
				items = [
					self._item(label = 35316,	image = 'elementum',		content = Menu.ContentService,		category = [Menu.CategoryDownloader, Menu.ServiceElementum]),
					self._item(label = 33570,	image = 'quasar',			content = Menu.ContentService,		category = [Menu.CategoryDownloader, Menu.ServiceQuasar]),
				]
			else:
				from lib.modules import tools

				module = None
				service = category[-1]

				if service == Menu.ServiceElementum: module = tools.Elementum
				elif service == Menu.ServiceQuasar: module = tools.Quasar

				if module and module.installed():
					items.extend([
						self._item(label = 33256, image = '%slaunch' % service, action = '%sLaunch' % service),
						self._item(label = 33477, image = '%sweb' % service, action = '%sInterface' % service),
						self._item(label = 33011, image = '%ssettings' % service, action = '%sSettings' % service),
					])
				else:
					items.append(self._item(label = 33474, image = '%sinstall' % service, action = '%sInstall' % service))

		elif Menu.CategoryUtility in category:
			items = [
				self._item(label = 35296,	image = 'youtube',		content = Menu.ContentService,		category = Menu.ServiceYoutube),
				self._item(label = 33322,	image = 'upnext',		content = Menu.ContentService,		category = Menu.ServiceUpnext),
				self._item(label = 36382,	image = 'tmdbhelper',	content = Menu.ContentService,		category = Menu.ServiceTmdbhelper),
				self._item(label = 33709,	image = 'vpnmanager',	content = Menu.ContentService,		category = Menu.ServiceVpnmanager),
			]

		elif Menu.ServiceOrion in category:
			from lib.modules.orionoid import Orionoid
			orion = Orionoid()
			if orion.addonInstalled():
				items.append(self._item(label = 33256, image = 'orionlaunch', action = 'orionLaunch'))
				try:
					if orion.accountPromotionEnabled() or not orion.accountValid(): items.append(self._item(label = 35428, image = 'orion', action = 'orionPromotion'))
					if orion.accountValid(): items.append(self._item(label = 33339, image = 'orionaccount', action = 'orionAccount'))
					if orion.accountFree(): items.append(self._item(label = 33768, image = 'orionpremium', action = 'orionWebsite'))
				except: pass
				items.append(self._item(label = 33011,	image = 'orionsettings',	action = 'orionSettings'))
				items.append(self._item(label = 33354,	image = 'orionpremium',		action = 'orionWebsite'))
				items.append(self._item(label = 35636,	image = 'orionuninstall',	action = 'orionUninstall'))
			else:
				items.append(self._item(label = 33736,	image = 'orioninstall',		action = 'orionInstall'))

		elif Menu.ServicePremiumize in category:
			from lib.debrid.premiumize import Core
			valid = Core().accountValid()
			if Menu.CategoryDownloads in category:
				if valid:
					items.extend([
						self._item(label = 33297,	image = 'downloadslist',		action = 'premiumizeList',			folder = True),
						self._item(label = 35069,	image = 'downloadsadd',			action = 'premiumizeAdd'),
						self._item(label = 33013,	image = 'downloadsclean',		action = 'premiumizeClear'),
						self._item(label = 33344,	image = 'downloadsinformation',	action = 'premiumizeInformation'),
					])
				items.append(self._item(label = 33011,	image = 'downloadssettings',	action = 'premiumizeSettings'))
			else:
				if valid:
					items.extend([
						self._item(label = 32009,	image = 'premiumizedownloads',	content = Menu.ContentService,	category = [Menu.ServicePremiumize, Menu.CategoryDownloads]),
						self._item(label = 33339,	image = 'premiumizeaccount',	action = 'premiumizeAccount'),
						self._item(label = 33030,	image = 'premiumizespeed',		action = 'speedtestPremiumize'),
					])
				items.extend([
					self._item(label = 33011,	image = 'premiumizesettings',	action = 'premiumizeSettings'),
					self._item(label = 33354,	image = 'premiumizeweb',		action = 'premiumizeWebsite'),
				])

		elif Menu.ServiceOffcloud in category:
			from lib.debrid.offcloud import Core
			valid = Core().accountValid()
			if Menu.CategoryDownloads in category:
				download = None
				if Menu.CategoryInstant in category: download = Menu.CategoryInstant
				elif Menu.CategoryCloud in category: download = Menu.CategoryCloud
				if download is None:
					if valid:
						items.extend([
							self._item(label = 35205,	image = 'downloadsinstant',		content = Menu.ContentService,	category = [Menu.ServiceOffcloud, Menu.CategoryDownloads, Menu.CategoryInstant]),
							self._item(label = 35206,	image = 'downloadscloud',		content = Menu.ContentService,	category = [Menu.ServiceOffcloud, Menu.CategoryDownloads, Menu.CategoryCloud]),
							self._item(label = 35069,	image = 'downloadsadd',			action = 'offcloudAdd'),
							self._item(label = 33013,	image = 'downloadsclean',		action = 'offcloudClear'),
							self._item(label = 33344,	image = 'downloadsinformation',	action = 'offcloudInformation'),
						])
					items.append(self._item(label = 33011,	image = 'downloadssettings',	action = 'offcloudSettings'))
				else:
					if valid:
						items.extend([
							self._item(label = 33297,	image = 'downloadslist',		action = 'offcloudList',		category = download,	folder = True),
							self._item(label = 35069,	image = 'downloadsadd',			action = 'offcloudAdd',			category = download),
							self._item(label = 33013,	image = 'downloadsclean',		action = 'offcloudClear',		category = download),
							self._item(label = 33344,	image = 'downloadsinformation',	action = 'offcloudInformation',	category = download),
						])
			else:
				if valid:
					items.extend([
						self._item(label = 32009,	image = 'offclouddownloads',	content = Menu.ContentService,	category = [Menu.ServiceOffcloud, Menu.CategoryDownloads]),
						self._item(label = 33339,	image = 'offcloudaccount',		action = 'offcloudAccount'),
						self._item(label = 33030,	image = 'offcloudspeed',		action = 'speedtestOffCloud'),
					])
				items.extend([
					self._item(label = 33011,	image = 'offcloudsettings',	action = 'offcloudSettings'),
					self._item(label = 33354,	image = 'offcloudweb',		action = 'offcloudWebsite'),
				])

		elif Menu.ServiceRealdebrid in category:
			from lib.debrid.realdebrid import Core
			valid = Core().accountValid()
			if Menu.CategoryDownloads in category:
				if valid:
					items.extend([
						self._item(label = 33297,	image = 'downloadslist',		action = 'realdebridList',			folder = True),
						self._item(label = 35069,	image = 'downloadsadd',			action = 'realdebridAdd'),
						self._item(label = 33013,	image = 'downloadsclean',		action = 'realdebridClear'),
						self._item(label = 33344,	image = 'downloadsinformation',	action = 'realdebridInformation'),
					])
				items.append(self._item(label = 33011,	image = 'downloadssettings',	action = 'realdebridSettings'))
			else:
				if valid:
					items.extend([
						self._item(label = 32009,	image = 'realdebriddownloads',	content = Menu.ContentService,	category = [Menu.ServiceRealdebrid, Menu.CategoryDownloads]),
						self._item(label = 33339,	image = 'realdebridaccount',	action = 'realdebridAccount'),
						self._item(label = 33030,	image = 'realdebridspeed',		action = 'speedtestRealDebrid'),
					])
				items.extend([
					self._item(label = 33011,	image = 'realdebridsettings',	action = 'realdebridSettings'),
					self._item(label = 33354,	image = 'realdebridweb',		action = 'realdebridWebsite'),
				])

		elif Menu.ServiceEasynews in category:
			from lib.debrid.easynews import Core
			valid = Core().accountValid()
			if valid:
				items.extend([
					self._item(label = 33339,	image = 'easynewsaccount',	action = 'easynewsAccount'),
					self._item(label = 33030,	image = 'easynewsspeed',	action = 'speedtestEasyNews'),
				])
			items.extend([
				self._item(label = 33011,	image = 'easynewssettings',	action = 'easynewsSettings'),
				self._item(label = 33354,	image = 'easynewsweb',		action = 'easynewsWebsite'),
			])

		elif Menu.ServiceEmby in category:
			items = [
				self._item(label = 33011,	image = 'embysettings',	action = 'embySettings'),
				self._item(label = 33354,	image = 'embyweb',		action = 'embyWebsite'),
			]

		elif Menu.ServiceJellyfin in category:
			items = [
				self._item(label = 33011,	image = 'jellyfinsettings',	action = 'jellyfinSettings'),
				self._item(label = 33354,	image = 'jellyfinweb',		action = 'jellyfinWebsite'),
			]

		elif Menu.ServiceYoutube in category:
			from lib.modules.tools import YouTube
			if YouTube.installed():
				items.extend([
					self._item(label = 33256,	image = 'youtubelaunch',	action = 'youtubeLaunch'),
					self._item(label = 33011,	image = 'youtubesettings',	action = 'youtubeSettings'),
				])
			else:
				items.append(self._item(label = 33474, image = 'youtubeinstall', action = 'youtubeInstall'))
			items.append(self._item(label = 33354, image = 'youtubeweb', action = 'youtubeWebsite'))

		elif Menu.ServiceUpnext in category:
			from lib.modules.tools import UpNext
			if UpNext.installed(): items.append(self._item(label = 33011, image = 'upnextsettings', action = 'upnextSettings'))
			else: items.append(self._item(label = 33474, image = 'upnextinstall', action = 'upnextInstall'))

		elif Menu.ServiceTmdbhelper in category:
			from lib.modules.tools import TmdbHelper
			if TmdbHelper.installed():
				items.extend([
					self._item(label = 33256,	image = 'tmdbhelperlaunch',		action = 'tmdbhelperLaunch'),
					self._item(label = 33011,	image = 'tmdbhelpersettings',	action = 'tmdbhelperSettings'),
					self._item(label = 36384,	image = 'tmdbhelperintegrate',	action = 'tmdbhelperIntegrate'),
				])
			else:
				items.append(self._item(label = 33474, image = 'tmdbhelperinstall', action = 'tmdbhelperInstall'))

		elif Menu.ServiceVpnmanager in category:
			from lib.modules.tools import VpnManager
			if VpnManager.installed():
				items.extend([
					self._item(label = 33256,	image = 'vpnmanagerlaunch',		action = 'vpnmanagerLaunch'),
					self._item(label = 33011,	image = 'vpnmanagersettings',	action = 'vpnmanagerSettings'),
				])
			else:
				items.append(self._item(label = 33474, image = 'vpnmanagerinstall', action = 'vpnmanagerInstall'))

		return items

	def _menuNetwork(self, category = None, **parameters):
		items = []

		if not category:
			items = [
				self._item(label = 33030,	image = 'networkspeed',			content = Menu.ContentNetwork,		category = Menu.CategorySpeed),
				self._item(label = 33344,	image = 'networkinformation',	action = 'networkInformation'),
				self._item(label = 33801,	image = 'networkvpn',			content = Menu.ContentNetwork,		category = Menu.CategoryVpn),
			]

		elif Menu.CategorySpeed in category:
			items = [
				self._item(label = 33509,	image = 'speedglobal',		action = 'speedtestGlobal'),
				self._item(label = 33566,	image = 'speedpremiumize',	action = 'speedtestPremiumize'),
				self._item(label = 35200,	image = 'speedoffcloud',	action = 'speedtestOffCloud'),
				self._item(label = 33567,	image = 'speedrealdebrid',	action = 'speedtestRealDebrid'),
				self._item(label = 33794,	image = 'speedeasynews',	action = 'speedtestEasyNews'),
				self._item(label = 33851,	image = 'speedcomparison',	action = 'speedtestComparison'),
			]

		elif Menu.CategoryVpn in category:
			from lib.modules.tools import VpnManager
			from lib.debrid.premiumize import Core as Premiumize
			from lib.debrid.easynews import Core as Easynews

			items = [
				self._item(label = 33389,	image = 'vpnverification',	action = 'vpnVerify'),
				self._item(label = 33802,	image = 'vpnconfiguration',	action = 'vpnConfigure'),
				self._item(label = 33011,	image = 'vpnsettings',		action = 'vpnSettings'),
			]
			if VpnManager.installed(): items.append(self._item(label = 33709, image = 'vpnvpnmanager', action = 'vpnmanagerLaunch'))
			if Premiumize().accountValid(): items.append(self._item(label = 33566, image = 'vpnpremiumize', action = 'premiumizeVpn'))
			if Easynews().accountValid(): items.append(self._item(label = 33794, image = 'vpneasynews', action = 'easynewsVpn'))

		return items

	def _menuDownload(self, category = None, **parameters):
		from lib.modules.tools import File
		from lib.modules.downloader import Downloader

		items = []

		if not category:
			items = [
				self._item(label = 33290,	image = 'downloadsmanual',			content = Menu.ContentDownload,		category = Menu.CategoryManual),
				self._item(label = 33016,	image = 'downloadscache',			content = Menu.ContentDownload,		category = Menu.CategoryCache),
				self._item(label = 33566,	image = 'downloadspremiumize',		content = Menu.ContentService,		category = [Menu.ServicePremiumize, Menu.CategoryDownloads]),
				self._item(label = 35200,	image = 'downloadsoffcloud',		content = Menu.ContentService,		category = [Menu.ServiceOffcloud, Menu.CategoryDownloads]),
				self._item(label = 33567,	image = 'downloadsrealdebrid',		content = Menu.ContentService,		category = [Menu.ServiceRealdebrid, Menu.CategoryDownloads]),
				self._item(label = 35316,	image = 'downloadselementum',		content = Menu.ContentService,		category = [Menu.CategoryDownloader, Menu.ServiceElementum]),
				self._item(label = 33570,	image = 'downloadsquasar',			content = Menu.ContentService,		category = [Menu.CategoryDownloader, Menu.ServiceQuasar]),
				self._item(label = 33011,	image = 'downloadssettings',		action = 'downloadsSettings'),
			]

		elif (Menu.CategoryManual in category or Menu.CategoryCache in category) and len(category) == 1:
			type = category[-1]
			if Downloader(type).enabled(notification = True): # Do not use full check, since the download directory might be temporarley down (eg: network), and you still want to access the downloads.
				error = False
				if not error and Settings.getInteger('download.%s.location.selection' % type) == 0:
					path = Settings.path('download.%s.location.combined' % type)
					if not File.existsDirectory(path): error = True

				items.append(self._item(label = 33297,	image = 'downloadslist', content = Menu.ContentDownload, category = [Menu.CategoryList, type]))

				if error: items.append(self._item(label = 33003, image = 'downloadsbrowse', content = Menu.ContentDownload, category = [Menu.CategoryBrowse, type, Menu.CategoryError], folder = False))
				else: items.append(self._item(label = 33003, image = 'downloadsbrowse', content = Menu.ContentDownload, category = [Menu.CategoryBrowse, type]))

				items.extend([
					self._item(label = 33013,	image = 'downloadsclean',		content = Menu.ContentDownload,		category = [Menu.CategoryClear, type]),
					self._item(label = 33011,	image = 'downloadssettings',	action = 'downloadsSettings',		downloadType = type),
				])

		elif Menu.CategoryList in category:
			type = category[-1]
			items = [
				self._item(label = 33029,	image = 'downloadslist',		action = 'downloadsList',		downloadType = type,	downloadStatus = Downloader.StatusAll,			folder = True),
				self._item(label = 33291,	image = 'downloadsbusy',		action = 'downloadsList',		downloadType = type,	downloadStatus = Downloader.StatusBusy,			folder = True),
				self._item(label = 33292,	image = 'downloadspaused',		action = 'downloadsList',		downloadType = type,	downloadStatus = Downloader.StatusPaused,		folder = True),
				self._item(label = 33294,	image = 'downloadscompleted',	action = 'downloadsList',		downloadType = type,	downloadStatus = Downloader.StatusCompleted,	folder = True),
				self._item(label = 33295,	image = 'downloadsfailed',		action = 'downloadsList',		downloadType = type,	downloadStatus = Downloader.StatusFailed,		folder = True),
			]

		elif Menu.CategoryBrowse in category:
			error = False
			type = category[-1]
			if type == Menu.CategoryError:
				error = True
				type = category[-2]

			if not error and Settings.getInteger('download.%s.location.selection' % type) == 0:
				path = Settings.path('download.%s.location.combined' % type)
				if not File.existsDirectory(path): error = True

			downloader = Downloader(type)
			if error:
				downloader.notificationLocation()
				return None
			else:
				for item in [(Downloader.MediaMovie, 'movies', 32001), (Downloader.MediaShow, 'shows', 32002), (Downloader.MediaOther, 'other', 35149)]:
					path = downloader._location(item[0])
					if File.existsDirectory(path): items.append(self._item(label = item[2], image = 'downloads' + item[1], command = path, folder = True))
					else: items.append(self._item(label = item[2], image = 'downloads' + item[1], content = Menu.ContentDownload, category = [Menu.CategoryBrowse, type, Menu.CategoryError],	folder = False))

		elif Menu.CategoryClear in category:
			type = category[-1]
			items = [
				self._item(label = 33029,	image = 'cleanlist',		action = 'downloadsClear',		downloadType = type,	downloadStatus = Downloader.StatusAll),
				self._item(label = 33291,	image = 'cleanplay',		action = 'downloadsClear',		downloadType = type,	downloadStatus = Downloader.StatusBusy),
				self._item(label = 33292,	image = 'cleanpaused',		action = 'downloadsClear',		downloadType = type,	downloadStatus = Downloader.StatusPaused),
				self._item(label = 33294,	image = 'cleancompleted',	action = 'downloadsClear',		downloadType = type,	downloadStatus = Downloader.StatusCompleted),
				self._item(label = 33295,	image = 'cleanfailed',		action = 'downloadsClear',		downloadType = type,	downloadStatus = Downloader.StatusFailed),
			]

		return items

	def _menuLibrary(self, category = None, **parameters):
		items = []
		if not category:
			items = [
				self._item(label = 35183,	image = 'libraryupdate',		action = 'libraryUpdate',			force = True),
				self._item(label = 33468,	image = 'libraryclean',			action = 'libraryClean'),
				self._item(label = 32314,	image = 'librarylocal',			content = Menu.ContentLibrary,		category = Menu.CategoryLocal),
				self._item(label = 33003,	image = 'librarybrowse',		content = Menu.ContentLibrary,		category = Menu.CategoryBrowse),
				self._item(label = 33011,	image = 'librarysettings',		action = 'librarySettings'),
			]
		elif Menu.CategoryLocal in category:
			items = [
				self._item(label = 32001,	image = 'librarymovies',		action = 'libraryLocal',			media = Media.Movie),
				self._item(label = 32002,	image = 'libraryshows',			action = 'libraryLocal',			media = Media.Show),
			]

		elif Menu.CategoryBrowse in category:
			from lib.modules.tools import File
			from lib.modules.library import Library

			error = False
			media = category[-1]
			if media == Menu.CategoryError:
				error = True
				media = category[-2]

			if error:
				Library(media = media).notificationLocation()
			else:
				for item in [(Media.Movie, 'movies', 32001), (Media.Show, 'shows', 32002)]:
					path = Library(media = item[0]).location()
					if File.existsDirectory(path): items.append(self._item(label = item[2], image = 'library' + item[1], command = path, folder = True))
					else: items.append(self._item(label = item[2], image = 'library' + item[1], content = Menu.ContentLibrary, category = [Menu.CategoryBrowse, item[0], Menu.CategoryError], folder = False))

		return items

	def _menuVerification(self, category = None, **parameters):
		items = []
		if not category:
			items = [
				self._item(label = 32346,	image = 'verificationaccount',		action = 'accountsVerify'),
				self._item(label = 33014,	image = 'verificationprovider',		action = 'providersVerify'),
				self._item(label = 35689,	image = 'verificationcloudflare',	action = 'cloudflareVerify'),
			]
		return items

	def _menuExtension(self, category = None, **parameters):
		items = []

		if not category:
			items = [
				self._item(label = 33239,	image = 'extensionshelp',			action = 'extensionsHelp'),
				self._item(label = 33721,	image = 'extensionsavailable',		content = Menu.ContentExtension,		category = Menu.CategoryAvailable),
				self._item(label = 33722,	image = 'extensionsinstalled',		content = Menu.ContentExtension,		category = Menu.CategoryInstalled),
			]

		else:
			from lib.modules.tools import Extension
			installed = Menu.CategoryInstalled in category
			for extension in Extension.list():
				if (installed and extension['installed']) or (not installed and not extension['installed']):
					items.append(self._item(label = extension['name'], image = extension['icon'], action = 'extensions', id = extension['id']))

		return items

	def _menuMetadata(self, category = None, **parameters):
		items = []

		if not category:
			from lib.meta.providers.imdb import MetaImdb
			items = [
				self._item(label = 36840,	image = 'metadatadetail',	action = 'metadataDetail'),
				self._item(label = 33552,	image = 'metadatapreload',	action = 'metadataPreload'),
				self._item(label = 36880,	image = 'metadataimdb',		action = 'metadataBulk',	settings = not MetaImdb.bulkEnabled(),	selection = True),
				self._item(label = 33011,	image = 'metadatasettings',	action = 'metadataSettings'),
			]

		return items

	def _menuUtility(self, category = None, **parameters):
		items = []

		if not category:
			items = [
				self._item(label = 33239,	image = 'help',					action = 'supportMenu', 		folder = True),
				self._item(label = 32062,	image = 'log',					content = Menu.ContentUtility,	category = Menu.CategoryLog),
				self._item(label = 33467,	image = 'system',				content = Menu.ContentUtility,	category = Menu.CategorySystem),
				self._item(label = 35442,	image = 'promotion',			action = 'promotionsMenu',		folder = True,		force = True),
				self._item(label = 33344,	image = 'information',			content = Menu.ContentUtility,	category = Menu.CategoryInformation),
			]

		elif Menu.CategoryLog in category:
			items = [
				self._item(label = 32064,	image = 'logkodi',				action = 'logKodi'),
				self._item(label = 32063,	image = 'logscrape',			action = 'logScrape'),
			]

		elif Menu.CategorySystem in category:
			items = [
				self._item(label = 33344,	image = 'systeminformation',	action = 'systemInformation'),
				self._item(label = 33719,	image = 'systemnetwork',		action = 'networkInformation'),
				self._item(label = 33472,	image = 'systemmanager',		action = 'systemManager'),
				self._item(label = 32008,	image = 'systemtools',			action = 'systemPower'),
				self._item(label = 35789,	image = 'systembenchmark',		action = 'systemBenchmark'),
			]

		elif Menu.CategoryInformation in category:
			items = [
				self._item(label = 33354,	image = 'network',				action = 'qr',	link = Settings.getString('internal.link.website', raw = True)),
				self._item(label = 33412,	image = 'cache',				action = 'qr',	link = Settings.getString('internal.link.repository', raw = True)),
				self._item(label = 35201,	image = 'announcements',		action = 'informationAnnouncement'),
				self._item(label = 33503,	image = 'change',				action = 'informationChangelog'),
				self._item(label = 33935,	image = 'attribution',			action = 'informationAttribution'),
				self._item(label = 35109,	image = 'legal',				action = 'informationDisclaimer'),
				self._item(label = 33358,	image = 'information',			action = 'informationAbout'),
			]

		return items

	##############################################################################
	# BUILD
	##############################################################################

	def _item(self, label = None, image = None, menu = None, content = None, action = None, command = None, folder = None, icon = None, **parameters):
		item = {}

		if not label is None: item[Menu.ParameterLabel] = label
		if not image is None: item[Menu.ParameterImage] = image

		item[Menu.ParameterMenu] = menu or Menu.MenuTool
		if not content is None: item[Menu.ParameterContent] = content

		if not action is None: item[Menu.ParameterAction] = action
		if not command is None: item[Menu.ParameterCommand] = command
		if not folder is None: item[Menu.ParameterFolder] = folder

		if icon: item['icon'] = icon
		if parameters: item[Menu.ParameterExtra] = parameters

		return item

	def _build(self, items):
		from lib.meta.image import MetaImage
		from lib.modules.theme import Theme
		from lib.modules.shortcut import Shortcut
		from lib.modules.interface import Translation, Directory, Context, Icon

		directory = Directory(content = Directory.ContentSettings, cache = True, lock = False)

		for i in range(len(items)):
			parameters = items[i]
			item = directory.item()

			# Label
			label = Translation.string(parameters.get(Menu.ParameterLabel))
			item.setLabel(label)

			# Images
			image = parameters.get(Menu.ParameterImage)
			fanart = Theme.fanart()
			special = parameters.get('icon')
			icon, thumb, poster, banner = Icon.pathAll(icon = image, special = special)
			Directory.decorate(item = item, icon = image, iconSpecial = special) # For Gaia Eminence.
			MetaImage.set(item = item, images = {
				MetaImage.TypePoster : poster,
				MetaImage.TypeThumb : thumb,
				MetaImage.TypeFanart : fanart,
				MetaImage.TypeLandscape : fanart,
				MetaImage.TypeBanner : banner,
				MetaImage.TypeClearlogo : icon,
				MetaImage.TypeClearart : icon,
				MetaImage.TypeDiscart : poster,
				MetaImage.TypeIcon : icon,
			})

			# Item
			data = {
				'title'	: label,
				'plot'	: System.navigationDescription(name = label),
			}
			try: tag = item.getVideoInfoTag()
			except: tag = None
			if tag: # Kodi 20+
				tag.setTitle(data['title'])
				tag.setPlot(data['plot'])
			else: # Kodi 19
				item.setInfo(type = 'video', infoLabels = data)

			# Command
			command = parameters.get(Menu.ParameterCommand)
			action = parameters.get(Menu.ParameterAction)
			folder = not command and not action
			if command is None:
				data = {System.NavigationParameter : System.navigation(name = label)}
				for j in [Menu.ParameterMenu, Menu.ParameterContent, Menu.ParameterCategory]:
					value = parameters.get(j)
					if not value is None: data[j] = value

				extra = parameters.get(Menu.ParameterExtra)
				if extra: data.update(extra)

				command = System.command(action = action or Menu.Action, parameters = data)

			# Folder
			folder = parameters.get(Menu.ParameterFolder) or folder
			if folder is None: folder = True

			# Context
			shortcut = parameters.get(Shortcut.Parameter)
			if shortcut: shortcut = Shortcut.item(id = shortcut, label = label, create = False, delete = True) # The context menu from a shortcut item itself.
			else: shortcut = Shortcut.item(label = label, folder = True, create = True, delete = False)
			context = Context(mode = Context.ModeGeneric, link = command, shortcut = shortcut)
			item.addContextMenuItems(context.menu(full = True))

			items[i] = [command, item, folder]

		directory.addItems(items = items)
		directory.finish()
