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

from lib.modules.tools import System, Settings, File
from lib.modules.cache import Memory

class Theme(object):

	IdThumbnail		= 'ThemeThumbnail'
	IdPoster		= 'ThemePoster'
	IdBanner		= 'ThemeBanner'
	IdFanart		= 'ThemeFanart'
	IdNextPoster	= 'ThemeNextPoster'
	IdNextBanner	= 'ThemeNextBanner'

	@classmethod
	def skin(self):
		return Settings.getString('theme.general.skin').lower()

	@classmethod
	def skinPath(self):
		skin = self.skin()
		skin = skin.replace(' ', '').lower()
		index = skin.find('(')
		if index >= 0: skin = skin[:index]
		addon = System.pathResources() if skin == 'default' or 'gaia1' in skin else System.pathSkins()
		return File.joinPath(addon, 'resources', 'media', 'skins', skin)

	@classmethod
	def skinSettings(self, reset = True):
		from lib.modules.tools import Extension
		from lib.modules.interface import Translation, Format, Dialog

		id = Extension.IdGaiaSkins
		items = ['Default', 'Gaia 1 (Color)']
		getMore = Format.fontBold(Translation.string(33740))
		if Extension.installed(id):
			items.extend(['Gaia 2 (Color)', 'Gaia 3 (Color)', 'Gaia 4 (Color)', 'Bubbles 1 (Blue)', 'Bubbles 2 (Color)', 'Minimalism (Grey)', 'Universe (Color)', 'Glass (Transparent)', 'Cinema 1 (Blue)', 'Cinema 2 (Blue)', 'Cinema 3 (Orange)', 'Cinema 4 (Red)', 'Home 1 (Color)', 'Home 2 (Blue)', 'Home 3 (Red)', 'Home 4 (White)', 'Home 5 (Black)', 'Home 6 (Blue)'])
		else:
			items.extend([getMore])
		choice = Dialog.select(title = 33337, items = items)
		if choice >= 0:
			if items[choice] == getMore:
				choice = Dialog.option(title = 33337, message = 33742, labelConfirm = 33736, labelDeny = 33743)
				if choice: Extension.enable(id = id)
			else:
				Settings.set('theme.general.skin', items[choice])
				if reset: self.clear()
				System.execute('Container.Refresh')

	@classmethod
	def clear(self):
		self.posterClear()
		self.thumbnailClear()
		self.bannerClear()
		self.fanartClear()
		self.nextPosterClear()
		self.nextBannerClear()

		# Make sure the global properties are reloaded.
		# Otherwise the theme does not change if the settings are changed.
		self.poster()
		self.thumbnail()
		self.banner()
		self.fanart()
		self.nextPoster()
		self.nextBanner()

	@classmethod
	def icon(self):
		return System.info('icon')

	@classmethod
	def artwork(self):
		return Settings.getBoolean('theme.image.artwork')

	@classmethod
	def thumbnail(self):
		# This function is called often during menu navigation.
		# Save it in memory cache to speed up retrieving the value.

		result = Memory.get(id = Theme.IdThumbnail, uncached = True, local = True, kodi = True)
		if Memory.cached(result): return result

		result = False
		type = Settings.getInteger('theme.image.poster')
		if type == 0:
			result = None
		else:
			if self.skin() in ['default', '-', '']:
				result = 'DefaultFolder.png'
			else:
				path = self.skinPath()
				if not path is None:
					name = None
					if type == 1: name = 'plain'
					elif type == 2: name = 'artwork'
					elif type == 3: name = 'discbox'
					if name is None:
						result = None
					else:
						path = File.joinPath(path, 'posters', name)
						for i in ['.png', '.jpg']:
							if File.exists(path + i):
								result = path + i
								break

		if result is False: result = System.info('icon')
		return Memory.set(id = Theme.IdThumbnail, value = result, local = True, kodi = True)

	@classmethod
	def thumbnailClear(self):
		Memory.clear(id = Theme.IdThumbnail, local = True, kodi = True)

	@classmethod
	def poster(self):
		# This function is called often during menu navigation.
		# Save it in memory cache to speed up retrieving the value.

		result = Memory.get(id = Theme.IdPoster, uncached = True, local = True, kodi = True)
		if Memory.cached(result): return result

		result = False
		type = Settings.getInteger('theme.image.poster')
		if type == 0:
			result = None
		else:
			if self.skin() in ['default', '-', '']:
				result = 'DefaultFolder.png'
			else:
				path = self.skinPath()
				if not path is None:
					name = None
					if type == 1: name = 'plain'
					elif type == 2: name = 'artwork'
					elif type == 3: name = 'discbox'
					if name is None:
						result = None
					else:
						path = File.joinPath(path, 'posters', name)
						for i in ['.png', '.jpg']:
							if File.exists(path + i):
								result = path + i
								break

		if result is False: result = System.info('icon')
		return Memory.set(id = Theme.IdPoster, value = result, local = True, kodi = True)

	@classmethod
	def posterClear(self):
		Memory.clear(id = Theme.IdPoster, local = True, kodi = True)

	@classmethod
	def banner(self):
		# This function is called often during menu navigation.
		# Save it in memory cache to speed up retrieving the value.

		result = Memory.get(id = Theme.IdBanner, uncached = True, local = True, kodi = True)
		if Memory.cached(result): return result

		result = False
		type = Settings.getInteger('theme.image.banner')
		if type == 0:
			result = None
		else:
			if self.skin() in ['default', '-', '']:
				result = 'DefaultVideo.png'
			else:
				path = self.skinPath()
				if not path is None:
					name = None
					if type == 1: name = 'plain'
					elif type == 2: name = 'artwork'
					if name is None:
						result = None
					else:
						path = File.joinPath(path, 'banners', name)
						for i in ['.png', '.jpg']:
							if File.exists(path + i):
								result = path + i
								break

		if result is False: result = System.info('icon')
		return Memory.set(id = Theme.IdBanner, value = result, local = True, kodi = True)

	@classmethod
	def bannerClear(self):
		Memory.clear(id = Theme.IdBanner, local = True, kodi = True)

	@classmethod
	def fanart(self):
		# This function is called often during menu navigation.
		# Save it in memory cache to speed up retrieving the value.

		result = Memory.get(id = Theme.IdFanart, uncached = True, local = True, kodi = True)
		if Memory.cached(result): return result

		result = None
		if Settings.getBoolean('theme.image.background'):
			path = self.skinPath()
			if not path is None:
				path = File.joinPath(path, 'background')
				for i in ['.png', '.jpg']:
					if File.exists(path + i):
						result = path + i
						break

		return Memory.set(id = Theme.IdFanart, value = result, local = True, kodi = True)

	@classmethod
	def fanartClear(self):
		Memory.clear(id = Theme.IdFanart, local = True, kodi = True)

	@classmethod
	def nextBanner(self):
		# This function is called often during menu navigation.
		# Save it in memory cache to speed up retrieving the value.

		result = Memory.get(id = Theme.IdNextBanner, uncached = True, local = True, kodi = True)
		if Memory.cached(result): return result

		result = False
		type = Settings.getInteger('theme.image.banner')
		if type == 0:
			result = None
		else:
			if self.skin() in ['default', '-', '']:
				result = 'DefaultVideo.png'
			else:
				path = self.skinPath()
				if not path is None:
					name = None
					if type == 1: name = 'plain'
					elif type == 2: name = 'artwork'
					if name is None:
						result = None
					else:
						path = File.joinPath(path, 'next', 'banners', name)
						for i in ['.png', '.jpg']:
							if File.exists(path + i):
								result = path + i
								break

		if result is False: result = System.info('icon')
		return Memory.set(id = Theme.IdNextBanner, value = result, local = True, kodi = True)

	@classmethod
	def nextBannerClear(self):
		Memory.clear(id = Theme.IdNextBanner, local = True, kodi = True)

	@classmethod
	def nextPoster(self):
		# This function is called often during menu navigation.
		# Save it in memory cache to speed up retrieving the value.

		result = Memory.get(id = Theme.IdNextPoster, uncached = True, local = True, kodi = True)
		if Memory.cached(result): return result

		result = False
		type = Settings.getInteger('theme.image.poster')
		if type == 0:
			result = None
		else:
			if self.skin() in ['default', '-', '']:
				result = 'DefaultVideo.png'
			else:
				path = self.skinPath()
				if not path is None:
					name = None
					if type == 1: name = 'plain'
					elif type == 2: name = 'artwork'
					if name is None:
						result = None
					else:
						path = File.joinPath(path, 'next', 'poster', name)
						for i in ['.png', '.jpg']:
							if File.exists(path + i):
								result = path + i
								break

		if result is False: result = System.info('icon')
		return Memory.set(id = Theme.IdNextPoster, value = result, local = True, kodi = True)

	@classmethod
	def nextPosterClear(self):
		Memory.clear(id = Theme.IdNextPoster, local = True, kodi = True)
