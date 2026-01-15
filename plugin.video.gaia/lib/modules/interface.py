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
import xbmcgui
import xbmcaddon
import xbmcplugin

import re

from lib.modules import tools
from lib.modules.concurrency import Pool

class Translation(object):

	@classmethod
	def string(self, id, utf8 = False, system = False):
		if tools.Tools.isInteger(id):
			# Needs ID when called from RunScript(vpn.py)
			if system: result = xbmc.getLocalizedString(id)
			else: result = xbmcaddon.Addon(tools.System.GaiaAddon).getLocalizedString(id)
		else:
			if tools.Tools.isString(id): result = id
			else: result = str(id)
		if utf8:
			try:
				if not '•' in result: result = tools.Converter.unicodeNormalize(string = result, umlaut = True)
			except:
				result = tools.Converter.unicodeNormalize(string = result, umlaut = True)
		return result


class Skin(object):

	Id = None

	TypeEstuary = 'skin.estuary'
	TypeEstouchy = 'skin.estouchy'
	TypeConfluence = 'skin.confluence'
	TypeXonfluence = 'skin.xonfluence'

	TypeArcticHorizon = 'skin.arctic.horizon'
	TypeArcticReloaded = 'skin.arctic.zephyr.mod'
	TypeArcticResurrection = 'skin.arctic.zephyr.2.resurrection.mod'

	TypeAeon = 'skin.aeon'
	TypeAeonNox = 'skin.aeon.nox'
	TypeAeonNoxSilvo = 'skin.aeon.nox.silvo'
	TypeAeonViper = 'skin.aeon.viper'
	TypeAeonViperK19 = 'skin.aeon.viper.k19'
	TypeAeonViperK20 = 'skin.aeon.viper.k20'

	TypeEminence = 'skin.eminence.2'
	TypeEminenceGaia = 'skin.eminence.gaia'

	SupportDialogDetail = {
		TypeEstouchy : True,
		TypeEstuary : True,
		TypeConfluence : True,
		TypeXonfluence : True,
		TypeArcticHorizon : True,
		TypeArcticReloaded : True,
		TypeArcticResurrection : True,
		TypeAeonNox : False, # Not sure, but at least the Silvo skin does not support it.
		TypeAeonNoxSilvo : False, # Shows a normal list dialog, just with the icon on the side. But does not show label2 on the 2nd line.
		TypeAeonViper : False,
		TypeAeonViperK19 : False,
		TypeAeonViperK20 : False,
		TypeEminence : True,
		TypeEminenceGaia : True,
	}

	SupportDialogDetailBold = {
		TypeEstouchy : True, # Seems to have been fixed and is working now (Kodi 19.4).
		TypeEstuary : True,
		TypeConfluence : False,
		TypeXonfluence : False,
		TypeArcticHorizon : True,
		TypeArcticReloaded : True,
		TypeArcticResurrection : True,
		TypeAeonNox : True,
		TypeAeonNoxSilvo : True,
		TypeAeonViper : True,
		TypeAeonViperK19 : True,
		TypeAeonViperK20 : True,
		TypeEminence : True,
		TypeEminenceGaia : True,
	}

	SupportDialogDetailIcon = {
		TypeEstouchy : False,
		TypeEstuary : False,
		TypeConfluence : False,
		TypeXonfluence : False,
		TypeArcticHorizon : True,
		TypeArcticReloaded : True,
		TypeArcticResurrection : True,
		TypeAeonNox : True,
		TypeAeonNoxSilvo : True,
		TypeAeonViper : True,
		TypeAeonViperK19 : True,
		TypeAeonViperK20 : True,
		TypeEminence : True,
		TypeEminenceGaia : True,
	}

	SupportLabelCustom = {
		TypeEstouchy : False,
		TypeEstuary : False,
		TypeConfluence : False,
		TypeXonfluence : False,
		TypeArcticHorizon : False,
		TypeArcticReloaded : False,
		TypeArcticResurrection : False,
		TypeAeonNox : False,
		TypeAeonNoxSilvo : False,
		TypeAeonViper : False,
		TypeAeonViperK19 : False,
		TypeAeonViperK20 : False,
		TypeEminence : False,
		TypeEminenceGaia : True,
	}

	@classmethod
	def _directory(self):
		return xbmc.getSkinDir()

	@classmethod
	def path(self):
		return tools.File.translatePath('special://skin')

	@classmethod
	def id(self):
		if Skin.Id is None: Skin.Id = self._directory()
		return Skin.Id

	@classmethod
	def isSkin(self, id):
		return id in self.id()

	@classmethod
	def isEstuary(self):
		return self.isSkin(Skin.TypeEstuary)

	@classmethod
	def isEstouchy(self):
		return self.isSkin(Skin.TypeEstouchy)

	@classmethod
	def isConfluence(self):
		return self.isSkin(Skin.TypeConfluence)

	@classmethod
	def isArcticHorizon(self):
		return self.isSkin(Skin.TypeArcticHorizon)

	# Any Aeon version.
	@classmethod
	def isAeon(self):
		return self.isSkin(Skin.TypeAeon)

	@classmethod
	def isAeonNox(self):
		return self.isSkin(Skin.TypeAeonNox)

	@classmethod
	def isAeonNoxSilvo(self):
		return self.isSkin(Skin.TypeAeonNoxSilvo)

	@classmethod
	def isAeonViper(self):
		return self.isSkin(Skin.TypeAeonViper)

	@classmethod
	def isEminence(self):
		return self.isSkin(Skin.TypeEminence)

	@classmethod
	def isEminenceGaia(self):
		return self.isSkin(Skin.TypeEminenceGaia)

	@classmethod
	def _support(self, definitions, default = None):
		id = self.id()
		for key, value in definitions.items():
			if self.isSkin(key): return value
		return default

	# Wether or not the skin supports a detailed list dialog.
	# Some skins have a detailed list dialog, but either the icons do not show, or they do not show the label2 on the 2nd line.
	# For instance, Aeon Nox Silvo's detailed list dialog is just the normal list dialog with the icon in the side-bar, but no label2.
	@classmethod
	def supportDialogDetail(self, default = None):
		return self._support(definitions = Skin.SupportDialogDetail, default = default)

	# Wether or not a bold label is supported in a detailed list dialog.
	# Some skins make the label by default bold, which means the label ends up being double bold (once from the skin, once from Gaia).
	# Kodi then strips the one bold opening tag, but leaves the closing tag there.
	# Then the label shows up as: "Some label that is bold[/B]".
	@classmethod
	def supportDialogDetailBold(self, default = None):
		return self._support(definitions = Skin.SupportDialogDetailBold, default = default)

	# Wether or not the detailed list dialog displays a large icon.
	# If yes, "large" icons should be used. If no, "small" icons should be used.
	@classmethod
	def supportDialogDetailIcon(self, default = None):
		return self._support(definitions = Skin.SupportDialogDetailIcon, default = default)

	# Wether or not the skin shows the ListItem's label in the menu and not the title/tvshowtitle.
	@classmethod
	def supportLabelCustom(self, default = None):
		return self._support(definitions = Skin.SupportLabelCustom, default = default)

	@classmethod
	def dependencies(self, detail = True):
		try:
			result = tools.System.addonDetails(id = self.id(), dependencies = True)['dependencies']
			if not detail: result = [i.get('addonid') for i in result]
			return result
		except: tools.Logger.error()
		return None

class Font(object):

	# Icon

	IconSeparator	= 'separator'
	IconEstimator	= 'estimator'
	IconRating		= 'rating'
	IconWatched		= 'watched'
	IconProgress	= 'progress'
	IconCalendar	= 'calendar'
	IconLeft		= 'left'
	IconRight		= 'right'
	IconUp			= 'up'
	IconDown		= 'down'

	IconKodi		= 'kodi'
	IconGaia		= 'gaia'
	IconOrion		= 'orion'
	IconTrakt		= 'trakt'
	IconClose		= 'close'
	IconBack		= 'back'
	IconSettings	= 'settings'
	IconPlay		= 'play'
	IconPlaylist	= 'playlist'
	IconExplore		= 'explore'
	IconSearch		= 'search'
	IconLibrary		= 'library'
	IconShortcut	= 'shortcut'
	IconActivity	= 'activity'
	IconInfo		= 'info'
	IconVideo		= 'video'
	IconRefresh		= 'refresh'
	IconBrowse		= 'browse'
	IconBinge		= 'binge'
	IconFilter		= 'filter'
	IconScrape		= 'scrape'
	IconFile		= 'file'
	IconLink		= 'link'
	IconDownload	= 'download'
	IconCache		= 'cache'

	IconDefault = {
		IconSeparator	: '•',
		IconEstimator	: '±',
		IconRating		: '★',
		IconWatched		: '⸙',
		IconProgress	: '¤',
		IconCalendar	: '※',
		IconLeft		: '←',
		IconRight		: '→',
		IconUp			: '↑',
		IconDown		: '↓',

		IconKodi		: '»',
		IconGaia		: '»',
		IconOrion		: '»',
		IconTrakt		: '»',
		IconClose		: '«',
		IconBack		: '«',
		IconSettings	: '»',
		IconPlay		: '»',
		IconPlaylist	: '»',
		IconExplore		: '»',
		IconSearch		: '»',
		IconLibrary		: '»',
		IconShortcut	: '»',
		IconActivity	: '»',
		IconInfo		: '»',
		IconVideo		: '»',
		IconRefresh		: '»',
		IconBrowse		: '»',
		IconBinge		: '»',
		IconFilter		: '»',
		IconScrape		: '»',
		IconFile		: '»',
		IconLink		: '»',
		IconDownload	: '»',
		IconCache		: '»',
	}

	IconAlternative = {
		IconSeparator	: '•',
		IconEstimator	: '±',
		IconRating		: '\uf005',
		IconWatched		: '\uf00c',
		IconProgress	: '\uf252',
		IconCalendar	: '\uf073',
		IconLeft		: '\uf060',
		IconRight		: '\uf061',
		IconUp			: '\uf062',
		IconDown		: '\uf063',

		IconKodi		: '\ueee0',
		IconGaia		: '\ueee1',
		IconOrion		: '\ueee2',
		IconTrakt		: '\ueee3',
		IconClose		: '\ue59b',
		IconBack		: '\uf355',
		IconSettings	: '\uf013',
		IconPlay		: '\uf04b ', # Add space, since the icon is narrow and doesn't align with other icons in the context menu.
		IconPlaylist	: '\ue1d0',
		IconExplore		: '\uf14e',
		IconSearch		: '\uf002',
		IconLibrary		: '\uf5db',
		IconShortcut	: '\uf364',
		IconActivity	: '\ue1a2',
		IconInfo		: '\uf05a',
		IconVideo		: '\uf8a9',
		IconRefresh		: '\uf2f1',
		IconBrowse		: '\uf07c',
		IconBinge		: '\ue1d2',
		IconFilter		: '\uf0b0',
		IconScrape		: '\uf713',
		IconFile		: '\uf15b ', # Add space, since the icon is narrow and doesn't align with other icons in the context menu.
		IconLink		: '\uf35d',
		IconDownload	: '\uf019',
		IconCache		: '\uf1c0',
	}

	IconData = None

	# Size
	SizeTiny		= 15
	SizeSmall		= 20
	SizeMedium		= 25
	SizeLarge		= 30
	SizeBig			= 35
	SizeHuge		= 45
	SizeMassive		= 80
	SizeColossal	= 120

	# Some skins have very large fonts.
	# Adjust the font selection by changing the requested size.
	# Eg: A value of 0.7 means a requested font of size 20 will instead use a size of 14 (20 * 0.7).
	SizeAdjust = {
		Skin.TypeEstouchy : 0.85,
		Skin.TypeConfluence : 0.65, # 0.7 is still too much for WindowOptimization.
	}

	FontData = None
	FontSelection = {}
	FontProperty = 'GaiaFonts'

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		if settings:
			Font.IconData = None
			Font.FontData = None

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def iconSettings(self, settings = False):
		def _help():
			Dialog.details(title = 36031, items = [
				{'type' : 'title', 'value' : 'Unicode Fonts', 'break' : 2},
				{'type' : 'text', 'value' : 'Icons are symbol characters from the font used by your Kodi skin. These symbols are used in labels or if only text is available and images cannot be used. Many fonts do no support most of the Unicode symbols available, but all of them support the standard Latin alphabet with common symbols. If your font does not support a specific character, it will show up as an empty or crossed-out rectangle, or not show up at all. In such a case, you can change the character used by the icon to a character that is supported by your font. ', 'break' : 2},

				{'type' : 'title', 'value' : 'Unicode Lookup', 'break' : 2},
				{'type' : 'text', 'value' : 'Icons can be provided as raw Unicode characters or by using the escaped Python Unicode notation in the format [B]\\uXXXX[/B], where [B]XXXX[/B] is the Unicode number (eg \\u2605). You can search Unicode characters at:', 'break' : 2},
				{'type' : 'link', 'value' : 'https://fileformat.info/info/unicode/char/search.htm', 'break' : 2},
				{'type' : 'text', 'value' : 'The fonts used by the Gaia Eminence skin also include symbols from the Noto [I]Symbols[/I], [I]Symbols2[/I], and [I]Math[/I]  fonts, which can be found here:', 'break' : 2},
				{'type' : 'link', 'value' : 'https://fonts.google.com/noto/fonts', 'break' : 2},
				{'type' : 'text', 'value' : 'Gaia Eminence also includes the solid FontAwesome symbols, which can be found here:', 'break' : 2},
				{'type' : 'link', 'value' : 'https://fontawesome.com/search?s=solid', 'break' : 2},
				{'type' : 'text', 'value' : 'The Unicode number can be found in the top-tight corner when clicking on an icon on FontAwesome. The Unicode number is given without the preceding \\u (eg f015).'},
			])

		def _default():
			tools.Settings.setData(id = 'theme.icon.configuration', value = self._iconDefault(), label = 33564)

		def _change(data, icon):
			default = self._iconDefault()
			value = Dialog.input(title = icon.capitalize(), default = data[icon])
			if not value: value = default[icon]
			data[icon] = value
			tools.Settings.setData(id = 'theme.icon.configuration', value = data, label = 33564 if data == default else 35233)

		def _create(data, entries):
			for i in range(len(entries)):
				entry = entries[i]
				entries[i] = {'title' : entry.capitalize(), 'value' : data[entry], 'parameters' : {'data' : data, 'icon' : entry}, 'action' : _change}
			return entries

		def _items():
			data = self._iconInitialize(clear = True)
			entriesGeneral = _create(data = data, entries = [
				Font.IconSeparator,
				Font.IconEstimator,
				Font.IconRating,
				Font.IconWatched,
				Font.IconProgress,
				Font.IconCalendar,
				Font.IconLeft,
				Font.IconRight,
				Font.IconUp,
				Font.IconDown,
			])
			entriesContext = _create(data = data, entries = [
				Font.IconGaia,
				Font.IconOrion,
				Font.IconTrakt,
				Font.IconClose,
				Font.IconBack,
				Font.IconSettings,
				Font.IconPlay,
				Font.IconPlaylist,
				Font.IconActivity,
				Font.IconExplore,
				Font.IconSearch,
				Font.IconLibrary,
				Font.IconShortcut,
				Font.IconInfo,
				Font.IconVideo,
				Font.IconRefresh,
				Font.IconBrowse,
				Font.IconBinge,
				Font.IconFilter,
				Font.IconScrape,
				Font.IconFile,
				Font.IconDownload,
				Font.IconCache,
			])
			return [
				{'title' : Dialog.prefixBack(33486), 'close' : True},
				{'title' : Dialog.prefixNext(33239), 'action' : _help},
				{'title' : Dialog.prefixNext(33564), 'action' : _default},
				{'title' : 32310, 'items' : entriesGeneral},
				{'title' : 35839, 'items' : entriesContext},
			]

		Dialog.information(title = 36031, items = _items(), refresh = _items, reselect = Dialog.ReselectMenu)

		if settings: tools.Settings.launchData(id = 'theme.icon.configuration')

	@classmethod
	def _iconInitialize(self, clear = False):
		if clear: Font.IconData = None
		if Font.IconData is None:
			default = tools.Tools.copy(self._iconDefault())
			if tools.Settings.getBoolean('theme.icon.enabled'):
				data = tools.Settings.getData('theme.icon.configuration')
				if data: default.update(data)
			Font.IconData = default
		return Font.IconData

	@classmethod
	def _iconDefault(self):
		return Font.IconAlternative if Skin.isEminenceGaia() else Font.IconDefault

	@classmethod
	def icon(self, icon):
		try: return self._iconInitialize()[icon]
		except: return None

	@classmethod
	def _fontXml(self, directory, scan = False):
		path = tools.File.joinPath(directory, 'Font.xml')
		if tools.File.exists(path): return path
		if scan:
			directories, files = tools.File.listDirectory(directory, absolute = True)
			for directory in directories:
				path = self._fontXml(directory = directory, scan = scan)
				if path: return path
		return None

	@classmethod
	def _fontPath(self):
		path = None
		skin = tools.File.translate('special://skin')
		directories, files = tools.File.listDirectory(path)

		# Try commonly used directory names.
		for directory in ['1080', '1080i', '1080p', '720', '720i', '720p', 'xml']:
			if directory in directories:
				path = self._fontXml(directory = tools.File.joinPath(skin, directory))
				if path: break

		# If not found, scan all subfolders.
		if not path: path = self._fontXml(directory = skin, scan = True)

		return path

	@classmethod
	def _fontDetect(self):
		if Font.FontData is None:
			data = tools.System.windowPropertyGet(property = Font.FontProperty)

			if data:
				Font.FontData = tools.Converter.jsonFrom(data)

				# If the skin changed, reset and detect again.
				if not Font.FontData or not 'id' in Font.FontData or not Font.FontData['id'] == Skin.id():
					tools.System.windowPropertyClear(property = Font.FontProperty)
					Font.FontData = None

			if Font.FontData is None:
				adjust = Skin._support(definitions = Font.SizeAdjust, default = 1)
				Font.FontData = []
				path = self._fontPath()

				if path:
					data = tools.File.readNow(path)
					fonts = tools.Regex.extract(data = data, expression = '<font>(.*?)<\/font>', group = None, all = True, flags = tools.Regex.FlagCaseInsensitive | tools.Regex.FlagAllLines)
					for font in fonts:
						name = tools.Regex.extract(data = font, expression = '<name>(.*?)<\/name>')
						file = tools.Regex.extract(data = font, expression = '<filename>(.*?)<\/filename>')

						size = tools.Regex.extract(data = font, expression = '<size>(.*?)<\/size>')
						if size: size = int(size)

						if size: dimension = int(size / adjust)
						else: dimension = size

						aspect = tools.Regex.extract(data = font, expression = '<aspect>(.*?)<\/aspect>')
						if aspect: aspect = float(aspect)

						spacing = tools.Regex.extract(data = font, expression = '<linespacing>(.*?)<\/linespacing>')
						if spacing: spacing = float(spacing)

						style = tools.Regex.extract(data = font, expression = '<style>(.*?)<\/style>')
						if not style: style = ''
						if name: style += ' ' + name
						if file: style += ' ' + file

						bold = tools.Regex.match(data = style, expression = 'bold')
						black = tools.Regex.match(data = style, expression = 'black')
						italic = tools.Regex.match(data = style, expression = 'italic')
						light = tools.Regex.match(data = style, expression = 'light')
						mono = tools.Regex.match(data = style, expression = 'mono')
						upper = tools.Regex.match(data = style, expression = 'upper')
						lower = tools.Regex.match(data = style, expression = 'lower')
						capital = tools.Regex.match(data = style, expression = 'capitalize')
						symbol = tools.Regex.match(data = style, expression = 'symbol')

						Font.FontData.append({
							'name' : name,
							'file' : file,
							'size' : size,
							'dimension' : dimension,
							'aspect' : aspect,
							'spacing' : spacing,

							'bold' : bold,
							'black' : black,
							'italic' : italic,
							'light' : light,
							'mono' : mono,
							'upper' : upper,
							'lower' : lower,
							'capital' : capital,
							'symbol' : symbol,
						})

				# If nothing found, add the default font (seems to be avilable in most skins).
				if not Font.FontData:
					Font.FontData.append({
						'name' : 'font13',
						'file' : None,
						'size' : None,
						'dimension' : None,
						'aspect' : None,
						'spacing' : None,

						'bold' : None,
						'italic' : None,
						'light' : None,
						'mono' : None,
						'upper' : None,
						'lower' : None,
						'capital' : None,
						'symbol' : None,
					})

				Font.FontData = {'id' : Skin.id(), 'fonts' : Font.FontData}
				tools.System.windowPropertySet(property = Font.FontProperty, value = tools.Converter.jsonTo(Font.FontData))

		return Font.FontData

	@classmethod
	def _fontMatch(self, font, value, key):
		return value is None or (value is True and font[key]) or (value is False and not font[key]) or font[key] == value

	@classmethod
	def _fontFind(self, size = 20, aspect = False, spacing = False, bold = None, italic = None, light = None, mono = None, upper = False, lower = False, capital = False, symbol = False):
		fonts = self._fontDetect()['fonts']

		if fonts:
			matches = [
				[aspect, 'aspect'],
				[spacing, 'spacing'],
				[bold, 'bold'],
				[bold, 'black'],
				[italic, 'italic'],
				[light, 'light'],
				[mono, 'mono'],
				[upper, 'upper'],
				[lower, 'lower'],
				[capital, 'capital'],
				[symbol, 'symbol'],
			]

			for font in fonts:
				if font['dimension'] == size: # Use adjusted size.
					matched = True
					for match in matches:
						if not self._fontMatch(font = font, value = match[0], key = match[1]):
							matched = False
							break
					if matched: return font

		return None

	'''
		Fonts in Kodi are selected based on the font name.
		Font names have no specific requirnment/format/name and can greatly vary between different skins.
		Many skins have the default font names like "font13", but some skins do not even have those (use different naming convetion), or use different font sizes for the same name.
		Detect all availbale fonts in the skin and select the best available one.

		size:
			The preferred font size.
		deviation:
			The deviation in font sizes if the given size is not available.
			Prefers closests deviation to the given size.
			1. False: Do not allow any deviation (aka fixed size).
			2. None: Decrease of 50% font size, increase of 25% font size.
			3. Integer: Increase/decrease deviation (eg: size = 5, deviation = 2 : [5, 4, 6, 3, 7])
			4. List: Separate decrease (index 0) and increase (index 1) deviations
		aspect/spacing/bold/italic/light/mono/upper/lower/capital/symbol:
			Select a font based on style attributes.
			1. None: Attribute can have any value or not be present.
			2. False: Attribute may not be present (eg: bold = False : do not select any bold fonts)
			3. True: Attribute must be present, but can have any value.
			4. Specific value: Attribute must be equal to a specific value (eg: aspect = 0.7)
		default:
			Return a default value if no font can be found with the given preferences.
	'''
	@classmethod
	def font(self, size = 20, deviation = None, aspect = False, spacing = False, bold = None, italic = None, light = None, mono = None, upper = False, lower = False, capital = False, symbol = False, default = True, full = False):
		# The default maximum deviation "int(size * 0.25)" is too little for the OSMC skin for FontTiny (OSMC's smallest font is 19). Increase to 0.5.
		if deviation is None: deviation = [int(size * 0.5), int(size * 0.5)]
		elif tools.Tools.isInteger(deviation): deviation = [deviation, deviation]
		key = (size, tuple(deviation), aspect, spacing, bold, italic, light, mono, upper, lower, capital, symbol, default)

		# Quickly return previously detected fonts.
		try: return Font.FontSelection[key] if full else Font.FontSelection[key]['name']
		except: pass

		# Preferred size.
		font = self._fontFind(size = size, aspect = aspect, spacing = spacing, bold = bold, italic = italic, light = light, mono = mono, upper = upper, lower = lower, capital = capital, symbol = symbol)

		# Deviated size.
		if not font and deviation:
			sizeMinimum = max(1, size - deviation[0])
			sizeMaximum = size + deviation[1]

			sizeDecrease = size - 1
			sizeIncrease = size + 1

			while True:
				allowed = False
				if sizeDecrease >= sizeMinimum:
					font = self._fontFind(size = sizeDecrease, aspect = aspect, spacing = spacing, bold = bold, italic = italic, light = light, mono = mono, upper = upper, lower = lower, capital = capital, symbol = symbol)
					if font: break
					sizeDecrease -= 1
					allowed = True
				if sizeIncrease <= sizeMaximum:
					font = self._fontFind(size = sizeIncrease, aspect = aspect, spacing = spacing, bold = bold, italic = italic, light = light, mono = mono, upper = upper, lower = lower, capital = capital, symbol = symbol)
					if font: break
					sizeIncrease += 1
					allowed = True
				if not allowed: break

		# Any other font.
		if not font and default:
			font = self.font(size = size, deviation = deviation, aspect = None, spacing = None, bold = bold, italic = italic, light = light, mono = mono, upper = upper, lower = lower, capital = capital, symbol = symbol, default = False)
			if not font:
				font = self.font(size = size, deviation = deviation, aspect = None, spacing = None, bold = None, italic = None, light = None, mono = None, upper = None, lower = None, capital = None, symbol = symbol, default = False)
				if not font:
					fonts = self._fontDetect()['fonts']
					if fonts: font = fonts[0]

		if not font: return font
		Font.FontSelection[key] = font
		return font if full else font['name']

	@classmethod
	def fontDefault(self, aspect = False, spacing = False, bold = None, italic = None, light = None, mono = None, upper = False, lower = False, capital = False, symbol = False, full = False):
		return self.fontMedium(aspect = aspect, spacing = spacing, bold = bold, italic = italic, light = light, mono = mono, upper = upper, lower = lower, capital = capital, symbol = symbol, full = full)

	@classmethod
	def fontTiny(self, aspect = False, spacing = False, bold = None, italic = None, light = None, mono = None, upper = False, lower = False, capital = False, symbol = False, full = False):
		return self.font(size = Font.SizeTiny, aspect = aspect, spacing = spacing, bold = bold, italic = italic, light = light, mono = mono, upper = upper, lower = lower, capital = capital, symbol = symbol, full = full)

	@classmethod
	def fontSmall(self, aspect = False, spacing = False, bold = None, italic = None, light = None, mono = None, upper = False, lower = False, capital = False, symbol = False, full = False):
		return self.font(size = Font.SizeSmall, aspect = aspect, spacing = spacing, bold = bold, italic = italic, light = light, mono = mono, upper = upper, lower = lower, capital = capital, symbol = symbol, full = full)

	@classmethod
	def fontMedium(self, aspect = False, spacing = False, bold = None, italic = None, light = None, mono = None, upper = False, lower = False, capital = False, symbol = False, full = False):
		return self.font(size = Font.SizeMedium, aspect = aspect, spacing = spacing, bold = bold, italic = italic, light = light, mono = mono, upper = upper, lower = lower, capital = capital, symbol = symbol, full = full)

	@classmethod
	def fontLarge(self, aspect = False, spacing = False, bold = None, italic = None, light = None, mono = None, upper = False, lower = False, capital = False, symbol = False, full = False):
		return self.font(size = Font.SizeLarge, aspect = aspect, spacing = spacing, bold = bold, italic = italic, light = light, mono = mono, upper = upper, lower = lower, capital = capital, symbol = symbol, full = full)

	@classmethod
	def fontBig(self, aspect = False, spacing = False, bold = None, italic = None, light = None, mono = None, upper = False, lower = False, capital = False, symbol = False, full = False):
		return self.font(size = Font.SizeBig, aspect = aspect, spacing = spacing, bold = bold, italic = italic, light = light, mono = mono, upper = upper, lower = lower, capital = capital, symbol = symbol, full = full)

	@classmethod
	def fontHuge(self, aspect = False, spacing = False, bold = None, italic = None, light = None, mono = None, upper = False, lower = False, capital = False, symbol = False, full = False):
		return self.font(size = Font.SizeHuge, aspect = aspect, spacing = spacing, bold = bold, italic = italic, light = light, mono = mono, upper = upper, lower = lower, capital = capital, symbol = symbol, full = full)

	@classmethod
	def fontMassive(self, aspect = False, spacing = False, bold = None, italic = None, light = None, mono = None, upper = False, lower = False, capital = False, symbol = False, full = False):
		return self.font(size = Font.SizeMassive, aspect = aspect, spacing = spacing, bold = bold, italic = italic, light = light, mono = mono, upper = upper, lower = lower, capital = capital, symbol = symbol, full = full)

	@classmethod
	def fontColossal(self, aspect = False, spacing = False, bold = None, italic = None, light = None, mono = None, upper = False, lower = False, capital = False, symbol = False, full = False):
		return self.font(size = Font.SizeColossal, aspect = aspect, spacing = spacing, bold = bold, italic = italic, light = light, mono = mono, upper = upper, lower = lower, capital = capital, symbol = symbol, full = full)

class Icon(object):

	TypeIcon = 'icon'
	TypeThumb = 'thumb'
	TypePoster = 'poster'
	TypeBanner = 'banner'
	TypeDefault = TypeIcon

	QualityMini = 'mini'
	QualitySmall = 'small'
	QualityLarge = 'large'
	QualityLight = 'light'
	QualityDefault = QualityLarge

	SpecialNone = None
	SpecialQuality = 'quality'
	SpecialDonations = 'donations'
	SpecialNotifications = 'notifications'
	SpecialCountries = 'countries'
	SpecialLanguages = 'languages'
	SpecialAddons = 'addons'
	SpecialServices = 'services'
	SpecialHandlers = 'handlers'
	SpecialOracle = 'oracle'
	SpecialContent = 'content'
	SpecialExtensions = 'extensions'

	ThemeData = {}

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		if settings:
			Icon.ThemeData = {}

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def _initialize(self, special = SpecialNone):
		if not special in Icon.ThemeData:
			if special: theme = special
			else: theme = tools.Settings.getString('theme.general.icon').lower()

			if not theme in ['default', '-', '']:
				theme = theme.replace(' ', '').lower()
				if 'glass' in theme:
					theme = theme.replace('(', '').replace(')', '')
				else:
					index = theme.find('(')
					if index >= 0: theme = theme[:index]

				addon = tools.System.pathResources() if theme in ['white', Icon.SpecialQuality, Icon.SpecialDonations, Icon.SpecialNotifications, Icon.SpecialCountries, Icon.SpecialLanguages, Icon.SpecialAddons, Icon.SpecialServices, Icon.SpecialHandlers, Icon.SpecialOracle, Icon.SpecialContent, Icon.SpecialExtensions] else tools.System.pathIcons()
				themePath = tools.File.joinPath(addon, 'resources', 'media', 'icons', theme)
				quality = tools.Settings.getInteger('theme.general.icon.quality')
				if quality == 0:
					themeIcon = Icon.QualityLarge
					themeThumb = Icon.QualityLarge
					themePoster = Icon.QualityLarge
					themeBanner = Icon.QualityLarge
					themeNotification = Icon.QualitySmall
				elif quality == 1:
					themeIcon = Icon.QualitySmall
					themeThumb = Icon.QualitySmall
					themePoster = Icon.QualitySmall
					themeBanner = Icon.QualitySmall
					themeNotification = Icon.QualitySmall
				elif quality == 2:
					themeIcon = Icon.QualityLarge
					themeThumb = Icon.QualityLarge
					themePoster = Icon.QualityLarge
					themeBanner = Icon.QualityLarge
					themeNotification = Icon.QualityLarge
				else:
					themeIcon = Icon.QualityLarge
					themeThumb = Icon.QualityLarge
					themePoster = Icon.QualityLarge
					themeBanner = Icon.QualityLarge
					themeNotification = Icon.QualitySmall

				if Skin.isEminenceGaia(): themeNotification = Icon.QualityMini

				Icon.ThemeData[special] = {
					'path' : themePath,
					'icon' : themeIcon,
					'thumb' : themeThumb,
					'poster' : themePoster,
					'banner' : themeBanner,
					'notification' : themeNotification,
				}

	@classmethod
	def themePath(self, special = SpecialNone):
		self._initialize(special = special)
		return Icon.ThemeData[special]['path']

	@classmethod
	def themeIcon(self, special = SpecialNone):
		self._initialize(special = special)
		return Icon.ThemeData[special]['icon']

	@classmethod
	def themeThumb(self, special = SpecialNone):
		self._initialize(special = special)
		return Icon.ThemeData[special]['thumb']

	@classmethod
	def themePoster(self, special = SpecialNone):
		self._initialize(special = special)
		return Icon.ThemeData[special]['poster']

	@classmethod
	def themeBanner(self, special = SpecialNone):
		self._initialize(special = special)
		return Icon.ThemeData[special]['banner']

	@classmethod
	def themeNotification(self, special = SpecialNone):
		self._initialize(special = special)
		return Icon.ThemeData[special]['notification']

	@classmethod
	def exists(self, icon, type = TypeDefault, default = None, special = SpecialNone, quality = None):
		return tools.File.exists(self.path(icon = icon, type = type, default = default, special = special, quality = quality))

	@classmethod
	def path(self, icon, type = TypeDefault, default = None, special = SpecialNone, quality = None):
		if icon == None: return None
		path = self.themePath(special = special)
		if path is None:
			return default
		else:
			if quality is None:
				if type == Icon.TypeIcon and special == Icon.SpecialNotifications: type = self.themeNotification(special = special)
				elif type == Icon.TypeIcon: type = self.themeIcon(special = special)
				elif type == Icon.TypeThumb: type = self.themeThumb(special = special)
				elif type == Icon.TypePoster: type = self.themePoster(special = special)
				elif type == Icon.TypeBanner: type = self.themeBanner(special = special)
				else: type = self.themeIcon(special = special)
			else:
				type = quality
			if not icon.endswith('.png'): icon += '.png'
			return tools.File.joinPath(path, type, icon)

	@classmethod
	def pathAll(self, icon, default = None, special = SpecialNone):
		return (
			self.pathIcon(icon = icon, default = default, special = special),
			self.pathThumb(icon = icon, default = default, special = special),
			self.pathPoster(icon = icon, default = default, special = special),
			self.pathBanner(icon = icon, default = default, special = special)
		)

	@classmethod
	def pathIcon(self, icon, default = None, special = SpecialNone):
		return self.path(icon = icon, type = Icon.TypeIcon, default = default, special = special)

	@classmethod
	def pathThumb(self, icon, default = None, special = SpecialNone):
		return self.path(icon = icon, type = Icon.TypeThumb, default = default, special = special)

	@classmethod
	def pathPoster(self, icon, default = None, special = SpecialNone):
		return self.path(icon = icon, type = Icon.TypePoster, default = default, special = special)

	@classmethod
	def pathBanner(self, icon, default = None, special = SpecialNone):
		return self.path(icon = icon, type = Icon.TypeBanner, default = default, special = special)

	@classmethod
	def settings(self):
		id = tools.Extension.IdGaiaIcons
		items = ['Default', 'White']
		getMore = Format.fontBold(Translation.string(33739))
		if tools.Extension.installed(id):
			# Removed old icon packs, since the ZIP file is becoming too large.
			#items.extend(['Black', 'Glass (Light)', 'Glass (Dark)', 'Shadow (Grey)', 'Fossil (Grey)', 'Navy (Blue)', 'Cerulean (Blue)', 'Sky (Blue)', 'Pine (Green)', 'Lime (Green)', 'Ruby (Red)', 'Candy (Red)', 'Tiger (Orange)', 'Pineapple (Yellow)', 'Violet (Purple)', 'Magenta (Pink)', 'Amber (Brown)'])
			items.extend(['Black', 'Glass (Light)', 'Glass (Dark)', 'Shadow (Grey)', 'Fossil (Grey)', 'Navy (Blue)', 'Sky (Blue)', 'Ruby (Red)', 'Tiger (Orange)', 'Pineapple (Yellow)', 'Violet (Purple)', 'Magenta (Pink)'])
		else:
			items.extend([getMore])
		choice = Dialog.select(title = 33338, items = items)
		if choice >= 0:
			if items[choice] == getMore:
				choice = Dialog.option(title = 33338, message = 33741, labelConfirm = 33736, labelDeny = 33743)
				if choice: tools.Extension.enable(id = id)
			else:
				tools.Settings.set('theme.general.icon', items[choice])
				Icon.ThemeData = {}
				Directory.refresh() # Does not reload new icons, probably because images are cached?

class Detail(object):

	MenuGeneric				= 'generic'
	MenuQuick				= 'quick'
	MenuProgress			= 'progress'
	MenuArrival				= 'arrival'

	TypeLabel				= 'label'
	TypeTagline				= 'tagline'
	TypePlot				= 'plot'

	ModeEnabled				= 'enabled'
	ModeDisabled			= 'disabled'
	ModePartial				= 'partial'
	Modes					= [ModeEnabled, ModeDisabled]
	ModesPartial			= [ModeEnabled, ModePartial, ModeDisabled] # Place partial before disabled.

	Placement				= 'placement'
	PlacementPrepend		= 'prepend'
	PlacementAppend			= 'append'
	Placements				= [PlacementPrepend, PlacementAppend]

	Separator				= 'separator'
	SeparatorNone			= 'none'
	SeparatorDash			= 'dash'
	SeparatorDot			= 'dot'
	SeparatorBar			= 'bar'
	SeparatorSlash			= 'slash'
	SeparatorSpace			= 'space'
	SeparatorLine			= 'line'
	SeparatorGap			= 'gap'
	Separators				= [SeparatorNone, SeparatorDash, SeparatorDot, SeparatorBar, SeparatorSlash, SeparatorSpace, SeparatorLine, SeparatorGap]

	Bracket					= 'bracket'
	BracketNone				= 'none'
	BracketRound			= 'round'
	BracketSquare			= 'square'
	BracketCurly			= 'curly'
	Brackets				= [BracketNone, BracketRound, BracketSquare, BracketCurly]

	Decoration				= 'decoration'
	DecorationNone			= 'none'
	DecorationIcon			= 'icon'
	DecorationAbbreviate	= 'abbreviate'
	DecorationComplete		= 'complete'
	Decorations				= [DecorationNone, DecorationIcon, DecorationAbbreviate, DecorationComplete]

	Style					= 'style'
	StyleNone				= 'none'
	StyleBold				= 'bold'
	StyleItalic				= 'italic'
	StyleLight				= 'light'
	Styles					= [StyleNone, StyleBold, StyleItalic, StyleLight]

	Color					= 'color'
	ColorNone				= 'none'
	ColorPalette			= 'palette'
	ColorPrimary			= 'primary'
	ColorSecondary			= 'secondary'
	ColorTertiary			= 'tertiary'
	ColorDisabled			= 'disabled'
	Colors					= [ColorNone, ColorPalette, ColorPrimary, ColorSecondary, ColorTertiary, ColorDisabled]

	Format					= 'format'

	SettingMediaMenu		= 'label.detail.media.menu'
	SettingMediaFormat		= 'label.detail.media.format'
	SettingActivityMenu		= 'label.detail.activity.menu'
	SettingActivityFormat	= 'label.detail.activity.format'
	SettingActivityPlay		= 'label.detail.activity.play.media'
	SettingActivityProgress	= 'label.detail.activity.progress.media'
	SettingActivityRating	= 'label.detail.activity.rating.media'
	SettingActivityAir		= 'label.detail.activity.air.media'

	@classmethod
	def format(self, data, format, color = True):
		try: format = format[Detail.Format]
		except: pass
		return Format.font(data, bold = format.get(Detail.StyleBold), italic = format.get(Detail.StyleItalic), light = format.get(Detail.StyleLight), color = format.get(Detail.Color) if color is True else color)

	# Color for brackets and join icons.
	@classmethod
	def color(self, format):
		color = format[Detail.Color]
		if color == Detail.ColorPalette or color == Detail.ColorDisabled: return Format.colorDisabled()
		else: return False

	@classmethod
	def _join(self, detail, prepend = False):
		result = []
		for i in detail:
			value = i[0]
			format = i[1]

			bracket = format[Detail.Bracket]
			if bracket and not bracket == Detail.BracketNone:
				bracket = self._bracket(format = format)
				value = bracket[0] + value.strip() + bracket[1]

			separator = format[Detail.Format][Detail.Separator]
			value = tools.Tools.stringRemoveSuffix(value, remove = separator.strip())
			if prepend: result.append(tools.Tools.stringRemoveSpace(value + separator))
			else: result.append(tools.Tools.stringRemoveSpace(separator + value))

		separator = format[Detail.Separator]
		if separator == Detail.SeparatorLine or separator == Detail.SeparatorGap: divide = ''
		else: divide = ' '

		return tools.Tools.stringRemoveSpace(' '.join(result)), divide

	@classmethod
	def joinBefore(self, data, detail):
		if not detail: return data
		result, divide = self._join(detail = detail, prepend = True)
		if data: result = result.rstrip() + divide + data.lstrip()
		return result

	@classmethod
	def joinAfter(self, data, detail):
		if not detail: return data
		result, divide = self._join(detail = detail)
		if data: result = data.rstrip() + divide + result.lstrip()
		return result

	@classmethod
	def _bracket(self, format, color = None):
		bracket = format[Detail.Format][Detail.Bracket]
		if color is None:
			if format[Detail.Color] in (Detail.ColorPalette, Detail.ColorDisabled): color = Format.colorDisabled()
			elif not Detail.Decoration in format: color = format[Detail.Format][Detail.Color] # Only for media details.
		return self.format(data = bracket[0], format = format, color = color), self.format(data = bracket[1], format = format, color = color)

	@classmethod
	def _label(self, value, color = True):
		if value == Detail.ModeEnabled: return Format.fontColor(32301, Format.colorExcellent()) if color else 32301
		elif value == Detail.ModeDisabled: return Format.fontColor(32302, Format.colorBad()) if color else 32302
		elif value == Detail.ModePartial: return Format.fontColor(33165, Format.colorMedium()) if color else 33165

		elif value == Detail.MenuGeneric: return 35540
		elif value == Detail.MenuQuick: return 36016
		elif value == Detail.MenuProgress: return 36017
		elif value == Detail.MenuArrival: return 36018

		elif value == tools.Media.Mixed: return 36052
		elif value == tools.Media.Movie: return 32001
		elif value == tools.Media.Set: return 33527
		elif value == tools.Media.Show: return 32002
		elif value == tools.Media.Season: return 32054
		elif value == tools.Media.Episode: return 32326
		elif value == tools.Media.Extra: return 36758

		elif value == Detail.TypeLabel: return 36129
		elif value == Detail.TypeTagline: return 36757
		elif value == Detail.TypePlot: return 33463

		elif value: return Translation.string(value).capitalize()

		return None

	@classmethod
	def _settingsMenu(self, id):
		data = tools.Settings.getData(id = id)
		if not data: data = self._settingsMenuDefault(id = id)
		return data

	@classmethod
	def _settingsMenuDefault(self, id):
		if id == Detail.SettingActivityMenu:
			return {
				Detail.MenuGeneric : {
					tools.Media.Mixed	: {Detail.TypeLabel : Detail.ModeEnabled,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeDisabled},
					tools.Media.Movie	: {Detail.TypeLabel : Detail.ModeEnabled,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeDisabled},
					tools.Media.Set		: {Detail.TypeLabel : Detail.ModeEnabled,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeDisabled},
					tools.Media.Show	: {Detail.TypeLabel : Detail.ModeEnabled,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeDisabled},
					tools.Media.Season	: {Detail.TypeLabel : Detail.ModeDisabled,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeDisabled},
					tools.Media.Episode	: {Detail.TypeLabel : Detail.ModeEnabled,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeDisabled},
					tools.Media.Extra	: {Detail.TypeLabel : Detail.ModeDisabled,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeDisabled},
				},
				Detail.MenuQuick : {
					tools.Media.Mixed	: {Detail.TypeLabel : Detail.ModeDisabled,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeDisabled},
					tools.Media.Movie	: {Detail.TypeLabel : Detail.ModeDisabled,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeDisabled},
					tools.Media.Show	: {Detail.TypeLabel : Detail.ModeDisabled,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeDisabled},
				},
				Detail.MenuProgress : {
					tools.Media.Mixed	: {Detail.TypeLabel : Detail.ModeDisabled,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeDisabled},
					tools.Media.Movie	: {Detail.TypeLabel : Detail.ModeEnabled,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeDisabled},
					tools.Media.Show	: {Detail.TypeLabel : Detail.ModeDisabled,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeDisabled},
				},
				Detail.MenuArrival : {
					tools.Media.Mixed	: {Detail.TypeLabel : Detail.ModeDisabled,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeDisabled},
					tools.Media.Movie	: {Detail.TypeLabel : Detail.ModeEnabled,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeDisabled},
					tools.Media.Show	: {Detail.TypeLabel : Detail.ModeEnabled,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeDisabled},
				},
			}
		else:
			return {
				Detail.MenuGeneric : {
					tools.Media.Mixed	: {Detail.TypeLabel : Detail.ModeEnabled,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeEnabled},
					tools.Media.Movie	: {Detail.TypeLabel : Detail.ModePartial,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeEnabled},
					tools.Media.Set		: {Detail.TypeLabel : Detail.ModePartial,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeEnabled},
					tools.Media.Show	: {Detail.TypeLabel : Detail.ModePartial,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeEnabled},
					tools.Media.Season	: {Detail.TypeLabel : Detail.ModePartial,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeDisabled},
					tools.Media.Episode	: {Detail.TypeLabel : Detail.ModePartial,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeEnabled},
					tools.Media.Extra	: {Detail.TypeLabel : Detail.ModePartial,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeEnabled},
				},
				Detail.MenuQuick : {
					tools.Media.Mixed	: {Detail.TypeLabel : Detail.ModeEnabled,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeEnabled},
					tools.Media.Movie	: {Detail.TypeLabel : Detail.ModePartial,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeEnabled},
					tools.Media.Show	: {Detail.TypeLabel : Detail.ModePartial,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeEnabled},
				},
				Detail.MenuProgress : {
					tools.Media.Mixed	: {Detail.TypeLabel : Detail.ModeEnabled,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeEnabled},
					tools.Media.Movie	: {Detail.TypeLabel : Detail.ModePartial,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeEnabled},
					tools.Media.Show	: {Detail.TypeLabel : Detail.ModePartial,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeEnabled},
				},
				Detail.MenuArrival : {
					tools.Media.Mixed	: {Detail.TypeLabel : Detail.ModeEnabled,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeEnabled},
					tools.Media.Movie	: {Detail.TypeLabel : Detail.ModePartial,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeEnabled},
					tools.Media.Show	: {Detail.TypeLabel : Detail.ModePartial,	Detail.TypeTagline : Detail.ModeDisabled,	Detail.TypePlot : Detail.ModeEnabled},
				},
			}

	@classmethod
	def _settingsMenuUpdate(self, id, partial = False, settings = False):
		self.tData = self._settingsMenu(id = id)
		self.tMenu = None
		self.tMedia = None

		def _default(menu = None, media = None):
			data = self._settingsMenuDefault(id = id)
			if menu: self.tData[menu][media] = data[menu][media]
			else: self.tData = data

		def _back():
			self.tMenu = None
			self.tMedia = None

		def _select(menu, media):
			self.tMenu = menu
			self.tMedia = media

		def _toggle(menu, media, type):
			modes = Detail.ModesPartial if partial else Detail.Modes
			value = self.tData[menu][media][type]
			index = modes.index(value)
			try: value = modes[index + 1]
			except: value = modes[0]
			self.tData[menu][media][type] = value

		def _items():
			if self.tMenu is None:
				items = [
					{'title' : Dialog.prefixBack(33486), 'bold' : True, 'color' : True, 'close' : True},
					{'title' : Dialog.prefixNext(33564), 'bold' : True, 'color' : True, 'action' : _default},
				]
				for k1, v1 in self.tData.items():
					item = []
					for k2, v2 in v1.items():
						value = v2.values()
						if Detail.ModePartial in value or list(value).count(Detail.ModeDisabled) == 2: value = Detail.ModePartial
						elif Detail.ModeEnabled in value: value = Detail.ModeEnabled
						else: value = Detail.ModeDisabled
						item.append({'title' : self._label(k2), 'value' : self._label(value), 'action' : _select, 'parameters' : {'menu' : k1, 'media' : k2}})
					items.append({'title' : self._label(k1), 'items' : item})
			else:
				item = []
				for k, v in self.tData[self.tMenu][self.tMedia].items():
					item.append({'title' : self._label(k), 'value' : self._label(v), 'action' : _toggle, 'parameters' : {'menu' : self.tMenu, 'media' : self.tMedia, 'type' : k}})
				items = [
					{'title' : Dialog.prefixBack(35374), 'bold' : True, 'color' : True, 'back' : True, 'action' : _back},
					{'title' : Dialog.prefixNext(33564), 'bold' : True, 'color' : True, 'action' : _default, 'parameters' : {'menu' : self.tMenu, 'media' : self.tMedia}},
					{'title' : self._label(Detail.Placement), 'items' : item},
				]

			return items

		Dialog.information(title = 35456, items = _items(), refresh = _items, reselect = Dialog.ReselectMenu)

		tools.Settings.setData(id = id, value = self.tData, label = Translation.string(33564 if self.tData == self._settingsMenuDefault(id = id) else 35233))
		if settings: tools.Settings.launchData(id = id)

	@classmethod
	def settingsMediaMenu(self):
		return self._settingsMenu(id = Detail.SettingMediaMenu)

	@classmethod
	def settingsMediaMenuUpdate(self, settings = False):
		return self._settingsMenuUpdate(id = Detail.SettingMediaMenu, partial = True, settings = settings)

	@classmethod
	def settingsActivityMenu(self):
		return self._settingsMenu(id = Detail.SettingActivityMenu)

	@classmethod
	def settingsActivityMenuUpdate(self, settings = False):
		return self._settingsMenuUpdate(id = Detail.SettingActivityMenu, settings = settings)

	@classmethod
	def _settingsFormat(self, id, prepare = False):
		data = tools.Settings.getData(id = id)
		if not data: data = self._settingsFormatDefault(id = id)

		if prepare:
			for k, v in data.items():
				format = {}

				separator = v[Detail.Separator]
				if separator == Detail.SeparatorDash: separator = ' - '
				elif separator == Detail.SeparatorDot: separator = Format.iconSeparator(pad = True, color = True)
				elif separator == Detail.SeparatorBar: separator = ' | '
				elif separator == Detail.SeparatorSlash: separator = ' / '
				elif separator == Detail.SeparatorSpace: separator = ' '
				elif separator == Detail.SeparatorLine: separator = Format.newline()
				elif separator == Detail.SeparatorGap: separator = Format.newline() * 2
				else: separator = ''
				format[Detail.Separator] = separator

				bracket = v[Detail.Bracket]
				if bracket == Detail.BracketRound: bracket = ('(', ')')
				elif bracket == Detail.BracketSquare: bracket = ('[', ']')
				elif bracket == Detail.BracketCurly: bracket = ('{', '}')
				else: bracket = ('', '')
				format[Detail.Bracket] = bracket

				style = v[Detail.Style]
				if style == Detail.StyleBold: format[Detail.StyleBold] = True
				elif style == Detail.StyleItalic: format[Detail.StyleItalic] = True
				elif style == Detail.StyleLight: format[Detail.StyleLight] = True

				color = v[Detail.Color]
				if color == Detail.ColorPrimary: color = Format.colorPrimary()
				elif color == Detail.ColorSecondary: color = Format.colorSecondary()
				elif color == Detail.ColorTertiary: color = Format.colorTertiary()
				elif color == Detail.ColorDisabled: color = Format.colorDisabled()
				else: color = None
				format[Detail.Color] = color

				v[Detail.Format] = format

		return data

	@classmethod
	def _settingsFormatDefault(self, id):
		if id == Detail.SettingActivityFormat:
			return {
				Detail.TypeLabel : {
					Detail.Placement	: Detail.PlacementPrepend,
					Detail.Decoration	: Detail.DecorationNone,
					Detail.Separator	: Detail.SeparatorSpace,
					Detail.Bracket		: Detail.BracketSquare,
					Detail.Style		: Detail.StyleBold,
					Detail.Color		: Detail.ColorPalette,
				},
				Detail.TypeTagline : {
					Detail.Placement	: Detail.PlacementPrepend,
					Detail.Decoration	: Detail.DecorationNone,
					Detail.Separator	: Detail.SeparatorSpace,
					Detail.Bracket		: Detail.BracketSquare,
					Detail.Style		: Detail.StyleBold,
					Detail.Color		: Detail.ColorPalette,
				},
				Detail.TypePlot : {
					Detail.Placement	: Detail.PlacementPrepend,
					Detail.Decoration	: Detail.DecorationNone,
					Detail.Separator	: Detail.SeparatorSpace,
					Detail.Bracket		: Detail.BracketSquare,
					Detail.Style		: Detail.StyleBold,
					Detail.Color		: Detail.ColorPalette,
				},
			}
		else:
			return {
				Detail.TypeLabel : {
					Detail.Placement	: Detail.PlacementAppend,
					Detail.Separator	: Detail.SeparatorDash,
					Detail.Bracket		: Detail.BracketNone,
					Detail.Style		: Detail.StyleItalic,
					Detail.Color		: Detail.ColorNone,
				},
				Detail.TypeTagline : {
					Detail.Placement	: Detail.PlacementAppend,
					Detail.Separator	: Detail.SeparatorDash,
					Detail.Bracket		: Detail.BracketNone,
					Detail.Style		: Detail.StyleBold,
					Detail.Color		: Detail.ColorNone,
				},
				Detail.TypePlot : {
					Detail.Placement	: Detail.PlacementPrepend,
					Detail.Separator	: Detail.SeparatorGap,
					Detail.Bracket		: Detail.BracketNone,
					Detail.Style		: Detail.StyleBold,
					Detail.Color		: Detail.ColorNone,
				},
			}

	@classmethod
	def _settingsFormatUpdate(self, id, decoration = False, palette = False, settings = False):
		self.tData = self._settingsFormat(id = id)

		def _default():
			self.tData = self._settingsFormatDefault(id = id)

		def _toggle(type, option):
			value = self.tData[type][option]

			if option == Detail.Placement: options = Detail.Placements
			elif option == Detail.Decoration: options = Detail.Decorations
			elif option == Detail.Separator: options = Detail.Separators
			elif option == Detail.Bracket: options = Detail.Brackets
			elif option == Detail.Style: options = Detail.Styles
			elif option == Detail.Color: options = Detail.Colors if palette else [i for i in Detail.Colors if not i == Detail.ColorPalette]

			index = options.index(value)
			try: value = options[index + 1]
			except: value = options[0]

			self.tData[type][option] = value

		def _items():
			items = [
				{'title' : Dialog.prefixBack(33486), 'bold' : True, 'color' : True, 'close' : True},
				{'title' : Dialog.prefixNext(33564), 'bold' : True, 'color' : True, 'action' : _default},
			]
			for k1, v1 in self.tData.items():
				item = []
				for k2, v2 in v1.items():
					if not decoration and k2 == Detail.Decoration: continue
					item.append({'title' : self._label(k2), 'value' : self._label(v2, color = False), 'action' : _toggle, 'parameters' : {'type' : k1, 'option' : k2}})
				items.append({'title' : self._label(k1), 'items' : item})
			return items

		Dialog.information(title = 32358, items = _items(), refresh = _items, reselect = Dialog.ReselectMenu)

		tools.Settings.setData(id = id, value = self.tData, label = Translation.string(33564 if self.tData == self._settingsFormatDefault(id = id) else 35233))
		if settings: tools.Settings.launchData(id = id)

	@classmethod
	def settingsMediaFormat(self, prepare = False):
		return self._settingsFormat(id = Detail.SettingMediaFormat, prepare = prepare)

	@classmethod
	def settingsMediaFormatUpdate(self, settings = False):
		return self._settingsFormatUpdate(id = Detail.SettingMediaFormat, decoration = False, palette = False, settings = settings)

	@classmethod
	def settingsActivityFormat(self, prepare = False):
		return self._settingsFormat(id = Detail.SettingActivityFormat, prepare = prepare)

	@classmethod
	def settingsActivityFormatUpdate(self, settings = False):
		return self._settingsFormatUpdate(id = Detail.SettingActivityFormat, decoration = True, palette = True, settings = settings)

	@classmethod
	def _settingsMedia(self, id):
		data = tools.Settings.getData(id = id)
		if not data: data = self._settingsMediaDefault(id = id)
		return data

	@classmethod
	def _settingsMediaDefault(self, id):
		return {
			tools.Media.Mixed	: Detail.ModeEnabled,
			tools.Media.Movie	: Detail.ModeEnabled,
			tools.Media.Set		: Detail.ModeEnabled,
			tools.Media.Show	: Detail.ModeEnabled,
			tools.Media.Season	: Detail.ModeEnabled,
			tools.Media.Episode	: Detail.ModeEnabled,
		}

	@classmethod
	def _settingsMediaUpdate(self, id, film = True, serie = True, settings = False):
		self.tData = self._settingsMedia(id = id)

		def _default(media = None):
			self.tData = self._settingsMediaDefault(id = id)

		def _toggle(media):
			value = self.tData[media]
			index = Detail.Modes.index(value)
			try: value = Detail.Modes[index + 1]
			except: value = Detail.Modes[0]
			self.tData[media] = value

		def _items():
			items = [
				{'title' : Dialog.prefixBack(33486), 'bold' : True, 'color' : True, 'close' : True},
				{'title' : Dialog.prefixNext(33564), 'bold' : True, 'color' : True, 'action' : _default},
			]
			item = []
			for k, v in self.tData.items():
				if not film and (tools.Media.isMixed(k) or tools.Media.isMovie(k) or tools.Media.isSet(k)): continue
				if not serie and (tools.Media.isMixed(k) or tools.Media.isSerie(k)): continue
				item.append({'title' : self._label(k), 'value' : self._label(v), 'action' : _toggle, 'parameters' : {'media' : k}})
			items.append({'title' : 35235, 'items' : item})
			return items

		Dialog.information(title = 36729, items = _items(), refresh = _items, reselect = Dialog.ReselectMenu)

		tools.Settings.setData(id = id, value = self.tData, label = Translation.string(33564 if self.tData == self._settingsMediaDefault(id = id) else 35233))
		if settings: tools.Settings.launchData(id = id)

	@classmethod
	def settingsActivityPlay(self):
		return self._settingsMedia(id = Detail.SettingActivityPlay)

	@classmethod
	def settingsActivityPlayUpdate(self, settings = False):
		return self._settingsMediaUpdate(id = Detail.SettingActivityPlay, settings = settings)

	@classmethod
	def settingsActivityProgress(self):
		return self._settingsMedia(id = Detail.SettingActivityProgress)

	@classmethod
	def settingsActivityProgressUpdate(self, settings = False):
		return self._settingsMediaUpdate(id = Detail.SettingActivityProgress, settings = settings)

	@classmethod
	def settingsActivityRating(self):
		return self._settingsMedia(id = Detail.SettingActivityRating)

	@classmethod
	def settingsActivityRatingUpdate(self, settings = False):
		return self._settingsMediaUpdate(id = Detail.SettingActivityRating, settings = settings)

	@classmethod
	def settingsActivityAir(self):
		return self._settingsMedia(id = Detail.SettingActivityAir)

	@classmethod
	def settingsActivityAirUpdate(self, settings = False):
		return self._settingsMediaUpdate(id = Detail.SettingActivityAir, film = False, settings = settings)

class Format(object):

	# Do not read setting or format colors according to the settings here.
	# Otherwise this code will execute every time the file is included, aka every time the user navigates between menus.
	# This would add about half a second extra to loading time.
	#ColorCustom = tools.Settings.getBoolean('theme.color.enabled')
	ColorCustom = None
	ColorQuality = {}
	ColorStep = 0.01

	ColorNone = None
	ColorDefault = 'default'
	ColorAutomatic = 'automatic'
	ColorPrimary = 'FFA0C12C'
	ColorSecondary = 'FF3C7DBF'
	ColorTertiary = 'FF777777'
	ColorRating = 'FFD4AF37'
	ColorMain = 'FF2396FF'
	ColorAlternative = 'FF004F98'
	ColorSpecial = 'FF6C3483'
	ColorUltra = 'FF00A177'
	ColorExcellent = 'FF1E8449'
	ColorGood = 'FF668D2E'
	ColorMedium = 'FFB7950B'
	ColorPoor = 'FFBA4A00'
	ColorBad = 'FF922B21'
	ColorGaia1 = 'FFA0C12C'
	ColorGaia2 = 'FF3C7DBF'
	ColorWhite = 'FFFFFFFF'
	ColorBlack = 'FF000000'
	ColorDisabled = 'FF888888'
	ColorTransparent = '88'

	Gradients = {}

	FontNewline = '[CR]'
	FontPassword = '•••••••••••••••'
	FontSplitInterval = 50

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		if settings:
			Format.ColorCustom = None
			Format.ColorQuality = {}

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def colorExtract(self, color):
		result = tools.Regex.extract(data = color, expression = '\\[.*?\\]([0-9A-F]{8}|[0-9A-F]{6})\\[.*?\\]')
		if not result: result = tools.Regex.extract(data = color, expression = '([0-9A-F]{8}|[0-9A-F]{6})')
		return result

	@classmethod
	def colorIsHex(self, color):
		return tools.Regex.match(data = color, expression = '^([0-9A-F]{1,8})$')

	@classmethod
	def colorToRgb(self, hex, alpha = False):
		hex = hex.replace('#', '')
		if len(hex) == 6: hex = 'FF' + hex
		if alpha: return [int(hex[i : i + 2], 16) for i in range(0, 8, 2)]
		else: return [int(hex[i : i + 2], 16) for i in range(2, 8, 2)]

	@classmethod
	def colorToHex(self, rgb):
		rgb = [int(i) for i in rgb]
		hex = ''.join(['0{0:x}'.format(i) if i < 16 else '{0:x}'.format(i) for i in rgb]).upper()
		if len(hex) == 6: hex = 'FF' + hex
		return hex

	@classmethod
	def colorGradient(self, startHex, endHex, count = 10):
		key = '%s_%s_%s' % (str(startHex), str(endHex), str(count))
		if not key in Format.Gradients:
			# http://bsou.io/posts/color-gradients-with-python
			start = self.colorToRgb(startHex)
			end = self.colorToRgb(endHex)
			colors = [start]
			for i in range(1, count):
				vector = [int(start[j] + (float(i) / (count - 1)) * (end[j] - start[j])) for j in range(3)]
				colors.append(vector)
			Format.Gradients[key] = [self.colorToHex(i) for i in colors]
		return Format.Gradients[key]

	@classmethod
	def colorGradientDiscrete(self, colors, count = 10):
		subcount = tools.Math.roundUp(count / float(len(colors) - 1))
		gradient = []
		for i in range(1, len(colors)):
			gradient.extend(self.colorGradient(startHex = colors[i - 1], endHex = colors[i], count = subcount))
		return gradient

	@classmethod
	def colorGradientIncrease(self, count = 10, discrete = True):
		if discrete:
			colors = [Format.colorBad(), Format.colorPoor(), Format.colorMedium(), Format.colorGood(), Format.colorExcellent()]
			return self.colorGradientDiscrete(colors = colors, count = count)
		else:
			return self.colorGradient(Format.colorBad(), Format.colorExcellent(), count)

	@classmethod
	def colorGradientDecrease(self, count = 10, discrete = True):
		if discrete:
			colors = [Format.colorExcellent(), Format.colorGood(), Format.colorMedium(), Format.colorPoor(), Format.colorBad()]
			return self.colorGradientDiscrete(colors = colors, count = count)
		else:
			return self.colorGradient(Format.colorExcellent(), Format.colorBad(), count)

	@classmethod
	def colorGradientPick(self, value, gradient):
		return gradient[max(0, min(len(gradient) - 1, int(value)))]

	@classmethod
	def colorMix(self, color1, color2, ratio = 0.5):
		ratio1 = ratio
		ratio2 = 1.0 - ratio
		color = []
		rgb = tools.Tools.isArray(color1)
		if not rgb:
			color1 = self.colorToRgb(color1, alpha = True)
			color2 = self.colorToRgb(color2, alpha = True)
		for i in range(len(color1)):
			color.append(min(255, max(0, int((color1[i] * ratio1) + (color2[i] * ratio2)))))
		return color if rgb else self.colorToHex(color)

	@classmethod
	def colorChange(self, color, change = 10):
		if color:
			if change > -1 and change < 1: change = int(round(255 * change))
			color = self.colorToRgb(color)
			color = [min(255, max(0, i + change)) for i in color]
			return self.colorToHex(color)
		else:
			return None

	@classmethod
	def colorLighter(self, color, change = 10):
		return self.colorChange(color, change)

	@classmethod
	def colorDarker(self, color, change = 10):
		return self.colorChange(color, -change)

	@classmethod
	def colorLightness(self, color):
		color = self.colorToRgb(hex = color, alpha = False)
		return sum(color) / 765.0

	@classmethod
	def colorDarkness(self, color):
		return 1.0 - self.colorLightness(color = color)

	@classmethod
	def colorAlpha(self, color, alpha):
		if len(color) == 8: color = color[2:]
		return alpha + color

	@classmethod
	def _colorSettings(self, custom, type, default):
		color = None
		if custom: color = tools.Settings.getCustom('theme.color.' + type)
		if not color: color = default
		return color

	@classmethod
	def _colorIninitialize(self):
		if Format.ColorCustom is None:
			Format.ColorCustom = tools.Settings.getBoolean('theme.color.enabled')
			Format.ColorPrimary = self._colorSettings(Format.ColorCustom, 'primary', Format.ColorPrimary)
			Format.ColorSecondary = self._colorSettings(Format.ColorCustom, 'secondary', Format.ColorSecondary)
			Format.ColorTertiary = self._colorSettings(Format.ColorCustom, 'tertiary', Format.ColorTertiary)
			Format.ColorRating = self._colorSettings(Format.ColorCustom, 'rating', Format.ColorRating)
			Format.ColorMain = self._colorSettings(Format.ColorCustom, 'main', Format.ColorMain)
			Format.ColorAlternative = self._colorSettings(Format.ColorCustom, 'alternative', Format.ColorAlternative)
			Format.ColorSpecial = self._colorSettings(Format.ColorCustom, 'special', Format.ColorSpecial)
			Format.ColorUltra = self._colorSettings(Format.ColorCustom, 'ultra', Format.ColorUltra)
			Format.ColorExcellent = self._colorSettings(Format.ColorCustom, 'excellent', Format.ColorExcellent)
			Format.ColorGood = self._colorSettings(Format.ColorCustom, 'good', Format.ColorGood)
			Format.ColorMedium = self._colorSettings(Format.ColorCustom, 'medium', Format.ColorMedium)
			Format.ColorPoor = self._colorSettings(Format.ColorCustom, 'poor', Format.ColorPoor)
			Format.ColorBad = self._colorSettings(Format.ColorCustom, 'bad', Format.ColorBad)
			Format.ColorDisabled = self._colorSettings(Format.ColorCustom, 'disabled', Format.ColorDisabled)

			try: Format.ColorTransparent = self.colorToHex([((100.0 - tools.Settings.getInteger('theme.color.transparent')) / 100.0) * 255.0])
			except: tools.Logger.error()

	@classmethod
	def colorQuality(self, quality):
		if not quality in Format.ColorQuality:
			from lib.modules.stream import Stream
			color = None
			quality = quality.lower()
			if quality.startswith(Stream.VideoQualityHd):
				color = self.colorUltra()
				index = 0
				if quality == Stream.VideoQualityHd4k: index = 1
				elif quality == Stream.VideoQualityHd6k: index = 2
				elif quality == Stream.VideoQualityHd8k: index = 3
				elif quality == Stream.VideoQualityHd10k: index = 4
				elif quality == Stream.VideoQualityHd12k: index = 5
				elif quality == Stream.VideoQualityHd14k: index = 6
				elif quality == Stream.VideoQualityHd16k: index = 7
				elif quality == Stream.VideoQualityHdUltra: index = 8
				elif quality == Stream.VideoQualityHd1080: color = self.colorExcellent()
				elif quality == Stream.VideoQualityHd720: color = self.colorGood()
				elif quality == Stream.VideoQualityHd: color = self.colorExcellent()
				if index > 0: color = self.colorDarker(color = color, change = (index * Format.ColorStep))
			elif quality.startswith(Stream.VideoQualitySd):
				color = self.colorMedium()
				index = 0
				if quality == Stream.VideoQualitySd240: index = 1
				elif quality == Stream.VideoQualitySd360: index = 2
				elif quality == Stream.VideoQualitySd480: index = 3
				elif quality == Stream.VideoQualitySd540: index = 4
				elif quality == Stream.VideoQualitySd576: index = 5
				elif quality == Stream.VideoQualitySd: index = 3
				if index > 0: color = self.colorLighter(color = color, change = (index * Format.ColorStep))
			elif quality.startswith(Stream.VideoQualityScr):
				color = self.colorPoor()
				index = 0
				if quality == Stream.VideoQualityScr240: index = 1
				elif quality == Stream.VideoQualityScr360: index = 2
				elif quality == Stream.VideoQualityScr480: index = 3
				elif quality == Stream.VideoQualityScr540: index = 4
				elif quality == Stream.VideoQualityScr576: index = 5
				elif quality == Stream.VideoQualityScr720: index = 6
				elif quality == Stream.VideoQualityScr1080: index = 7
				elif quality == Stream.VideoQualityScr: index = 3
				if index > 0: color = self.colorLighter(color = color, change = (index * Format.ColorStep))
			elif quality.startswith(Stream.VideoQualityCam):
				color = self.colorBad()
				index = 0
				if quality == Stream.VideoQualityCam240: index = 1
				elif quality == Stream.VideoQualityCam360: index = 2
				elif quality == Stream.VideoQualityCam480: index = 3
				elif quality == Stream.VideoQualityCam540: index = 4
				elif quality == Stream.VideoQualityCam576: index = 5
				elif quality == Stream.VideoQualityCam720: index = 6
				elif quality == Stream.VideoQualityCam1080: index = 7
				elif quality == Stream.VideoQualityCam: index = 3
				if index > 0: color = self.colorLighter(color = color, change = (index * Format.ColorStep))
			Format.ColorQuality[quality] = color
		return Format.ColorQuality[quality]

	@classmethod
	def colorPrimary(self):
		self._colorIninitialize()
		return Format.ColorPrimary

	@classmethod
	def colorSecondary(self):
		self._colorIninitialize()
		return Format.ColorSecondary

	@classmethod
	def colorTertiary(self):
		self._colorIninitialize()
		return Format.ColorTertiary

	@classmethod
	def colorRating(self):
		self._colorIninitialize()
		return Format.ColorRating

	@classmethod
	def colorMain(self):
		self._colorIninitialize()
		return Format.ColorMain

	@classmethod
	def colorAlternative(self):
		self._colorIninitialize()
		return Format.ColorAlternative

	@classmethod
	def colorSpecial(self):
		self._colorIninitialize()
		return Format.ColorSpecial

	@classmethod
	def colorUltra(self):
		self._colorIninitialize()
		return Format.ColorUltra

	@classmethod
	def colorExcellent(self):
		self._colorIninitialize()
		return Format.ColorExcellent

	@classmethod
	def colorGood(self):
		self._colorIninitialize()
		return Format.ColorGood

	@classmethod
	def colorMedium(self):
		self._colorIninitialize()
		return Format.ColorMedium

	@classmethod
	def colorPoor(self):
		self._colorIninitialize()
		return Format.ColorPoor

	@classmethod
	def colorBad(self):
		self._colorIninitialize()
		return Format.ColorBad

	@classmethod
	def colorGaia1(self):
		return Format.ColorGaia1

	@classmethod
	def colorGaia2(self):
		return Format.ColorGaia2

	@classmethod
	def colorWhite(self):
		return Format.ColorWhite

	@classmethod
	def colorBlack(self):
		return Format.ColorBlack

	@classmethod
	def colorDisabled(self):
		self._colorIninitialize()
		return Format.ColorDisabled

	@classmethod
	def colorTransparent(self):
		self._colorIninitialize()
		return Format.ColorTransparent

	@classmethod
	def _iconFormat(self, icon, color = False, bold = False, pad = True, padLeft = False, padRight = False, padding = ' '):
		# Color

		if color == Format.ColorDefault or color is True: color = self.colorDisabled()
		if color: icon = self.fontColor(icon, color = color)

		# Bold

		if bold: icon = self.fontBold(icon)

		# Pad

		if pad is True: padLeft = padRight = padding
		elif pad: padLeft = padRight = pad

		if padLeft is True: padLeft = padding
		if padRight is True: padRight = padding

		if padLeft: icon = padLeft + icon
		if padRight: icon = icon + padRight

		# Result

		return icon

	@classmethod
	def icon(self, icon, color = False, bold = False, pad = False, padLeft = False, padRight = False):
		return self._iconFormat(icon = Font.icon(icon), color = color, bold = bold, pad = pad, padLeft = padLeft, padRight = padRight)

	@classmethod
	def iconSeparator(self, color = False, bold = False, pad = False, padLeft = False, padRight = False):
		return self.icon(icon = Font.IconSeparator, color = color, bold = bold, pad = pad, padLeft = padLeft, padRight = padRight)

	@classmethod
	def iconBullet(self, color = False, bold = False, pad = False, padLeft = False, padRight = '  '):
		return self.iconSeparator(color = color, bold = bold, pad = pad, padLeft = padLeft, padRight = padRight)

	@classmethod
	def iconJoin(self, values, color = True, bold = False, pad = True, padLeft = False, padRight = False):
		if not tools.Tools.isArray(values): values = [values]
		values = [Translation.string(i) if tools.Tools.isInteger(i) else i for i in values]
		return self.iconSeparator(color = color, bold = bold, pad = pad, padLeft = padLeft, padRight = padRight).join(values)

	@classmethod
	def iconRating(self, count = None, fixed = None, color = False, bold = False, pad = False, padLeft = False, padRight = False):
		icon = Font.icon(Font.IconRating)

		if color == Format.ColorDefault or color is True:
			color = Format.colorRating()
		elif color == Format.ColorAutomatic:
			if count <= 1: color = Format.colorBad()
			elif count == 2: color = Format.colorPoor()
			elif count == 3: color = Format.colorMedium()
			elif count == 4: color = Format.colorGood()
			elif count >= 5: color = Format.colorExcellent()

		if count is None: iconEnabled = icon
		else: iconEnabled = icon * count

		if fixed is None: iconDisabled = ''
		else:
			if fixed is True: fixed = 5
			iconDisabled = icon * (fixed - count)

		label = self.fontColor(iconEnabled, color = color)
		if iconDisabled: label += self.fontColor(iconDisabled, color = self.colorDisabled())
		return self._iconFormat(icon = label, color = self.colorDisabled(), bold = bold, pad = pad, padLeft = padLeft, padRight = padRight)

	@classmethod
	def __translate(self, label, utf8 = False):
		return Translation.string(label, utf8 = utf8)

	@classmethod
	def font(self, label, color = None, bold = None, italic = None, light = None, uppercase = None, lowercase = None, capitalcase = None, newline = None, translate = True):
		if label == None: return label
		if translate: label = self.__translate(label)
		if label:
			if color:
				label = self.fontColor(label, color, translate = False)
			if bold:
				label = self.fontBold(label, translate = False)
			if italic:
				label = self.fontItalic(label, translate = False)
			if light:
				label = self.fontLight(label, translate = False)
			if uppercase:
				label = self.fontUppercase(label, translate = False)
			elif lowercase:
				label = self.fontLowercase(label, translate = False)
			elif capitalcase:
				label = self.fontCapitalcase(label, translate = False)
			if newline:
				label += self.fontNewline(translate = False)
			return label
		else:
			return ''

	@classmethod
	def fontColor(self, label, color, translate = True):
		if color == None: return label
		if len(color) == 6: color = 'FF' + color
		if translate: label = self.__translate(label)
		return '[COLOR ' + color + ']' + label + '[/COLOR]'

	@classmethod
	def fontBold(self, label, translate = True):
		if translate: label = self.__translate(label)
		return '[B]' + label + '[/B]'

	@classmethod
	def fontItalic(self, label, translate = True):
		if translate: label = self.__translate(label)
		return '[I]' + label + '[/I]'

	@classmethod
	def fontLight(self, label, translate = True):
		if translate: label = self.__translate(label)
		return '[LIGHT]' + label + '[/LIGHT]'

	@classmethod
	def fontUppercase(self, label, translate = True):
		if translate: label = self.__translate(label)
		return '[UPPERCASE]' + label + '[/UPPERCASE]'

	@classmethod
	def fontLowercase(self, label, translate = True):
		if translate: label = self.__translate(label)
		return '[LOWERCASE]' + label + '[/LOWERCASE]'

	@classmethod
	def fontCapitalcase(self, label, translate = True):
		if translate: label = self.__translate(label)
		return '[CAPITALIZE]' + label + '[/CAPITALIZE]'

	@classmethod
	def fontNewline(self):
		return Format.FontNewline

	@classmethod
	def fontSplit(self, label, interval = None, type = None):
		if not interval: interval = Format.FontSplitInterval
		if not type: type = Format.FontNewline
		return re.sub('(.{' + str(interval) + '})', '\\1' + type, label, 0, re.DOTALL)

	# Synonyms

	@classmethod
	def color(self, label, color):
		return self.fontColor(label, color)

	@classmethod
	def bold(self, label):
		return self.fontBold(label)

	@classmethod
	def italic(self, label):
		return self.fontItalic(label)

	@classmethod
	def light(self, label):
		return self.fontLight(label)

	@classmethod
	def uppercase(self, label):
		return self.fontUppercase(label)

	@classmethod
	def lowercase(self, label):
		return self.fontLowercase(label)

	@classmethod
	def capitalcase(self, label):
		return self.fontCapitalcase(label)

	@classmethod
	def newline(self):
		return self.fontNewline()

	@classmethod
	def split(self, label, interval = None, type = None):
		return self.fontSplit(label = label, interval = interval, type = type)

	@classmethod
	def clean(self, label):
		label = tools.Regex.remove(data = label, expression = '(\[.*?\])', all = True)
		label = tools.Regex.remove(data = label, expression = '(\[\/.*?\])', all = True)
		return label


class Core(object):

	TypeScrape = 'interface.scrape.interface'
	TypePlayback = 'interface.playback.interface'
	TypeDownload = 'download.manual.progress'

	Intance = None

	def __init__(self):
		self.mType = None
		self.mDialog = None
		self.mTitle = None
		self.mTitleBold = None
		self.mMessage = None
		self.mProgress = None
		self.mBackground = False
		self.mClosed = True

		self.mThread = None
		self.mRunning = False
		self.mDots = False
		self.mSuffix = ''

	def __del__(self):
		# If Intance runs out of scope, close the dialog.
		self.close()

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		Core.Intance = None

	##############################################################################
	# GENERAL
	##############################################################################

	def _dots(self):
		dots = ' '
		self.mRunning = True
		while self.mDots and self.visible():
			dots += '.'
			if len(dots) > 4: dots = ' '
			self.mSuffix = Format.fontBold(dots)
			self._update()
			tools.Time.sleep(0.5)
		self.mRunning = False

	def _set(self, type = None, dialog = None, title = None, message = None, progress = None, background = None, dots = None):
		if not type is None: self.mType = type
		if not dots is None: self.mDots = dots
		if not dialog is None: self.mDialog = dialog

		if not title is None: self.mTitle = title
		if self.mTitle is None: self.mTitle = 35302
		self.mTitleBold = Format.fontBold(self.mTitle)

		if not message is None: self.mMessage = message
		if self.mMessage is None: self.mMessage = 35302

		if not progress is None: self.mProgress = progress
		if self.mProgress is None: self.mProgress = 0

		if not background is None: self.mBackground = background
		else: self.mBackground = self.backgroundSetting()

	@classmethod
	def instance(self):
		if Core.Intance is None: Core.Intance = Core()
		return Core.Intance

	@classmethod
	def instanceHas(self):
		return Core.Intance is None

	@classmethod
	def dialog(self):
		return self.instance().mDialog

	@classmethod
	def background(self):
		return self.instance().mBackground

	@classmethod
	def backgroundSetting(self):
		type = self.instance().mType
		if type == Core.TypeDownload: index = 3
		else: index = 2
		return tools.Settings.getInteger(type) == index

	@classmethod
	def canceled(self):
		try: return self.dialog().iscanceled()
		except: return False

	@classmethod
	def visible(self):
		return not self.instance().mClosed and not self.canceled()

	@classmethod
	def create(self, type = None, title = None, message = None, progress = None, background = None, close = None, dots = True):
		try:
			core = self.instance()

			if close is None:
				# Background dialog has a lot more problems. Always close.
				# Foreground dialog is more robust as does not need it.
				# This ensures the the foreground dialog stays open, instead of popping up and closing all the time.

				# NB: Currently seems fine with background dialogs as well. In case the interleaving flickering between messages starts again, enable this.
				close = False
				#if background == None: close = core.mBackground
				#else: close = background

			if close or not core.mDialog:
				self.close()

			core._set(type = type, title = title, message = message, progress = progress, background = background, dots = dots)

			if core.mClosed or not core.mDialog:
				# If launched for the first time, close all other progress dialogs.
				if not core.mDialog:
					Dialog.closeAllProgress()
					tools.Time.sleep(0.1)
				try: del core.mDialog
				except: pass
				core.mDialog = Dialog.progress(background = core.mBackground, title = core.mTitle, message = core.mMessage)

			core.mClosed = False
			core._update()

			if core.mDots and (not core.mThread or not core.mRunning):
				core.mThread = Pool.thread(target = core._dots)
				core.mThread.start()

			return core.mDialog
		except:
			tools.Logger.error()

	def _update(self):
		if self.mBackground:
			try: self.mDialog.update(self.mProgress, self.mTitleBold, self.mMessage % self.mSuffix)
			except: self.mDialog.update(self.mProgress, self.mTitleBold, self.mMessage)
		else:
			try: self.mDialog.update(self.mProgress, self.mMessage % self.mSuffix)
			except: self.mDialog.update(self.mProgress, self.mMessage)

	@classmethod
	def update(self, title = None, message = None, progress = None, background = None, dots = None):
		try:
			core = self.instance()
			if core.mDialog == None or not self.visible():
				if dots == None: return self.create(title = title, message = message, progress = progress, background = background)
				else: return self.create(title = title, message = message, progress = progress, background = background, dots = dots)
			else:
				core._set(title = title, message = message, progress = progress, dots = dots)
				core._update()
				return core.mDialog
		except: pass

	@classmethod
	def close(self, delay = 0):
		try:
			# NB: Checking DialogCoreClosed is very important.
			# Do not rely on the try-catch statement.
			# Kodi crashes instead of throwing an exception.
			core = self.instance()
			if not core.mClosed:
				core.mClosed = True
				if core.mDialog:
					# Must be set to 100, otherwise it shows up in a later dialog.
					#if core.mBackground: core.mDialog.update(100, ' ', ' ')
					#else: core.mDialog.update(100, ' ')
					core.mProgress = 100
					core._update()

					core.mDialog.close()
					try:
						del core.mDialog
						core.mDialog = None
					except: pass
				if delay > 0: tools.Time.sleep(delay)
		except: pass


class Dialog(object):

	TypeText = 'text'
	TypeConfirm = 'confirm'
	TypeOption = 'option'
	TypeOptions = 'options'
	TypeInput = 'input'
	TypeNotification = 'notification'
	TypeDetails = 'details'

	IconPlain = 'logo'
	IconInformation = 'information'
	IconWarning = 'warning'
	IconError = 'error'
	IconSuccess = 'success'

	IconNativeLogo = 'nativelogo'
	IconNativeInformation = 'nativeinformation'
	IconNativeWarning = 'nativewarning'
	IconNativeError = 'nativeerror'

	InputAlphabetic = xbmcgui.INPUT_ALPHANUM # Standard keyboard
	InputNumeric = xbmcgui.INPUT_NUMERIC # Format: #
	InputDate = xbmcgui.INPUT_DATE # Format: DD/MM/YYYY
	InputTime = xbmcgui.INPUT_TIME # Format: HH:MM
	InputIp = xbmcgui.INPUT_IPADDRESS # Format: #.#.#.#
	InputPassword = xbmcgui.INPUT_PASSWORD # Returns MD55 hash of input and the input is masked.

	# Numbers/values must correspond with Kodi
	BrowseFile = 1
	BrowseImage = 2
	BrowseDirectoryRead = 0
	BrowseDirectoryWrite = 3
	BrowseDefault = BrowseFile

	PrefixBack = '« '
	PrefixNext = '» '

	IdNone = 9999
	IdHome = 10000
	IdDialogText = 10147
	IdDialogProgress = 10101
	IdDialogOk = 12002
	IdDialogNotification = 10107
	IdDialogBusy = 10138
	IdDialogBusyNoCancel = 10160
	IdDialogKeyboard = 10103
	IdDialogYesNo = 10100
	IdDialogAddonSettings = 10140
	IdDialogSelect = 12000
	IdDialogCustom = 13000

	ToggleEnable = 'enable'
	ToggleDisable = 'disable'
	ToggleApply = 'apply'
	ToggleBack = 'back'
	ToggleCancel = 'cancel'
	ToggleDefault = 'default'
	ToggleInverse = 'inverse'

	ReselectYes = True
	ReselectNo = False
	ReselectMenu = 'menu' # Keep track of submenu selection and reselect on a submenu basis.

	ChoiceCanceled = -1
	ChoiceNo = 0
	ChoiceYes = 1
	ChoiceCustom = 2

	EmptyLine = ''

	Notifications = {}

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		Dialog.Notifications = {}

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def prefix(self, text, prefix, color = None, bold = True):
		if color is None: color = Format.colorPrimary()
		return Format.font(prefix, color = color, bold = bold, translate = False) + Translation.string(text)

	@classmethod
	def prefixBack(self, text, color = None, bold = None):
		if color is None: color = Format.colorPrimary()
		return self.prefix(text = text, prefix = Dialog.PrefixBack, color = color, bold = bold)

	@classmethod
	def prefixNext(self, text, color = None, bold = None):
		if color is None: color = Format.colorPrimary()
		return self.prefix(text = text, prefix = Dialog.PrefixNext, color = color, bold = bold)

	@classmethod
	def prefixContains(self, text):
		try: return Dialog.PrefixBack in text or Dialog.PrefixNext in text
		except: return False

	@classmethod
	def close(self, id, sleep = None):
		xbmc.executebuiltin('Dialog.Close(%s,true)' % str(id))
		if sleep: tools.Time.sleep(sleep)

	@classmethod
	def closeConfirm(self, sleep = None):
		self.close(id = self.IdDialogOk, sleep = sleep)

	@classmethod
	def closeOption(self, sleep = None):
		self.close(id = self.IdDialogYesNo, sleep = sleep)

	@classmethod
	def closeNotification(self, sleep = None):
		self.close(id = self.IdDialogNotification, sleep = sleep)

	@classmethod
	def closeText(self, sleep = None):
		self.close(id = self.IdDialogText, sleep = sleep)

	# Close all open dialog.
	# Sometimes if you open a dialog right after this, it also clauses. Might need some sleep to prevent this. sleep in ms.
	@classmethod
	def closeAll(self, sleep = None):
		xbmc.executebuiltin('Dialog.Close(all,true)')
		if sleep: tools.Time.sleep(sleep)

	@classmethod
	def closeAllProgress(self, sleep = None):
		xbmc.executebuiltin('Dialog.Close(progressdialog,true)')
		xbmc.executebuiltin('Dialog.Close(extendedprogressdialog,true)')
		if sleep: tools.Time.sleep(sleep)

	@classmethod
	def closeAllNative(self, sleep = None):
		xbmc.executebuiltin('Dialog.Close(virtualkeyboard,true)')
		xbmc.executebuiltin('Dialog.Close(yesnodialog,true)')
		xbmc.executebuiltin('Dialog.Close(progressdialog,true)')
		xbmc.executebuiltin('Dialog.Close(extendedprogressdialog,true)')
		xbmc.executebuiltin('Dialog.Close(sliderdialog,true)')
		xbmc.executebuiltin('Dialog.Close(okdialog,true)')
		xbmc.executebuiltin('Dialog.Close(selectdialog,true)')
		if sleep: tools.Time.sleep(sleep)

	@classmethod
	def aborted(self):
		return tools.System.aborted()

	# Current window ID
	@classmethod
	def windowId(self):
		return xbmcgui.getCurrentWindowId()

	# Check if certain window is currently showing.
	@classmethod
	def windowVisible(self, id):
		return self.windowId() == id

	@classmethod
	def windowVisibleHome(self):
		return self.windowId() == Dialog.IdHome

	# Current dialog ID
	@classmethod
	def dialogId(self, window = False):
		id = xbmcgui.getCurrentWindowDialogId()
		if window and not id: id = xbmcgui.getCurrentWindowId()
		return id

	# Check if certain dialog is currently showing.
	@classmethod
	def dialogVisible(self, id = None, loader = None, window = False):
		dialog = self.dialogId(window = window)
		if dialog and dialog <= Dialog.IdNone:
			dialog = None
		elif not loader and (dialog == Dialog.IdDialogBusy or dialog == Dialog.IdDialogBusyNoCancel):
			if loader is None:
				# Wait if loader is showing, in case a different dialog is shown after the loader.
				for i in range(5):
					dialog = self.dialogId(window = window)
					if dialog and dialog <= Dialog.IdNone:
						dialog = None
						break
					elif dialog == Dialog.IdDialogBusy or dialog == Dialog.IdDialogBusyNoCancel:
						dialog = None
						tools.Time.sleep(0.1)
					else:
						break
			else:
				dialog = None
		return bool(dialog) if id is None else id == dialog

	@classmethod
	def dialogProgressVisible(self):
		return self.dialogVisible(Dialog.IdDialogProgress)

	@classmethod
	def dialogConfirmVisible(self):
		return self.dialogVisible(Dialog.IdDialogYesNo)

	@classmethod
	def dialogNotificationVisible(self):
		return tools.System.visible('Window.IsActive(notification)')

	# Get a control from a dialog.
	# Control IDs: https://kodi.wiki/view/List_of_Built_In_Controls#DialogNotification.xml
	@classmethod
	def dialogControl(self, id, control):
		try: return xbmcgui.Window(id).getControl(control)
		except: return None

	# Wait/sleep for all dialogs (or a specific dialog) to close.
	@classmethod
	def dialogWait(self, id = None, open = True, close = True, loader = None, window = True):
		interval = 0.25

		# Wait for the dialog to open.
		# Do not wait forever, in case something goes wrong and the dialog never opens.
		if open:
			for i in range(20 if open is True else int(open * interval)):
				if self.dialogVisible(id = id, loader = loader, window = window): break
				else: tools.Time.sleep(interval)

		# Wait for the dialog to close.
		if close:
			for i in range(100000 if close is True else int(close * interval)):
				if self.dialogVisible(id = id, loader = loader, window = window): tools.Time.sleep(interval)
				else: break

	@classmethod
	def keyboard(self, default = '', hidden = False, show = True, title = None):
		keyboard = xbmc.Keyboard(default, self.title(title), hidden)
		if show:
			keyboard.doModal()
			return keyboard.getText() if keyboard.isConfirmed() else None
		else:
			return keyboard

	@classmethod
	def link(self, link, color = True, italic = True, bold = False, identation = True, offset = False):
		if color is True: color = Format.colorSecondary()
		elif not color: color = None

		if identation is True: identation = '     '
		elif not identation: identation = ''

		if offset is True: offset = 1
		if offset: offset = Format.newline() * offset
		else: offset = ''

		return offset + identation + Format.font(link, italic = italic, bold = bold, color = color)

	@classmethod
	def show(self, type, **kwargs):
		if type == Dialog.TypeText: return self.text(**kwargs)
		elif type == Dialog.TypeConfirm: return self.confirm(**kwargs)
		elif type == Dialog.TypeOption: return self.option(**kwargs)
		elif type == Dialog.TypeOptions: return self.options(**kwargs)
		elif type == Dialog.TypeInput: return self.input(**kwargs)
		elif type == Dialog.TypeNotification: return self.notification(**kwargs)
		elif type == Dialog.TypeDetails: return self.details(**kwargs)
		return None

	@classmethod
	def confirm(self, message, title = None, wait = True):
		if wait: return xbmcgui.Dialog().ok(self.title(title), self.__translate(message))
		else: Pool.thread(target = self.confirm, kwargs = {'title' : title, 'message' : message}).start()

	@classmethod
	def text(self, message, mono = False, help = True, title = None):
		message = self.__translate(message)
		if help:
			newline = Format.newline()
			while message.endswith(newline): message = message[:-len(newline)]
			message = message + (newline * 2) + Format.font('[%s]' % self.__translate(36096), italic = True, light = True) + Format.newline()
		return xbmcgui.Dialog().textviewer(self.title(title), message, mono)

	# Shows a text dialog with formatting.
	# items is a list of values with one of the following formats:
	#	Add a new line break:
	#		{'type' : 'break'}
	#	Add a bold and colored heading with a default break afterwards:
	#		{'type' : 'title', 'value' : 'Heading Text', 'break' : False <True if not provided, or integer with the number of breaks>}
	#	Add a bold and secondary colored heading with a default break afterwards:
	#		{'type' : 'subtitle', 'value' : 'Heading Text', 'break' : False <True if not provided, or integer with the number of breaks>}
	#	Add a body of text without formatting:
	#		{'type' : 'text', 'value' : 'Some description text', 'break' : False <True if not provided, or integer with the number of breaks>}
	#	Add a formatted and indented link.
	#		{'type' : 'link', 'value' : 'xyz', 'break' : False <True if not provided>, 'identation' : False <True if not provided>}
	#	Add a list of items, with a bold and colored heading, and text without formatting.
	#		{'type' : 'list', 'value' : [{'title' : 'List item heading', 'value' : 'Some text', 'link' : '<optional>'}], 'break' : False <True if not provided>, 'number' : True <False if not provided, shows either bullet points or numbering>}
	#	Each item can have {'color' : True/False} or {'bold' : True/False} to disable color/bold formatting. By default both are True.
	@classmethod
	def details(self, items, mono = False, title = None, text = True):
		message = ''
		colorPrimary = Format.colorPrimary()
		colorSecondary = Format.colorSecondary()
		separator = Format.iconSeparator(color = colorPrimary, pad = True)
		colon = ': '
		newline = Format.FontNewline * (2 if text else 1)
		newlineSpace = ' ' + Format.FontNewline

		titles = False
		for item in items:
			if item and item['type'] == 'title':
				titles = True
				break
		colorTitle = colorSecondary if titles else colorPrimary

		for item in items:
			if item:
				if item['type'] == 'break':
					try: message += newlineSpace if item['break'] is True else '' if item['break'] is False else (newlineSpace * item['break'])
					except: message += newlineSpace
				else:
					try: color = item['color']
					except: color = True
					try: bold = item['bold']
					except: bold = True

					if item['type'] == 'title':
						message += Format.font(item['value'], bold = bold, color = colorPrimary if color else None, uppercase = True)
					if item['type'] == 'subtitle':
						message += Format.font(item['value'], bold = bold, color = colorSecondary if color else None, uppercase = False)
					elif item['type'] == 'text':
						message += Translation.string(item['value'])
					elif item['type'] == 'link':
						try: identation = item['identation']
						except: identation = True
						message += self.link(item['value'], color = colorSecondary if color else None, italic = True, bold = False, identation = identation)
					elif item['type'] == 'list':
						for entry in item['value']:
							if 'link' in entry:
								value = self.link(entry['link'], color = colorSecondary if color else None, italic = True, bold = False, identation = False)
								if 'value' in entry and entry['value']: value = '%s (%s )' % (entry['value'], value)
								entry['value'] = value

						try: number = item['number']
						except: number = False
						if number: message += Format.FontNewline.join([Format.fontColor(' %d. ' % (i + 1), color = colorSecondary if color else None) + (Format.font(Translation.string(item['value'][i]['title']) + colon, color = colorTitle if color else None) if 'title' in item['value'][i] else ' ') + Translation.string(item['value'][i]['value']) for i in range(len(item['value']))])
						else: message += Format.FontNewline.join([separator + (Format.font(Translation.string(i['title']) + colon, bold = bold, color = colorTitle if color else None) if 'title' in i else ' ') + Translation.string(i['value']) for i in item['value']])

					try: message += newline if item['break'] is True else '' if item['break'] is False else (Format.FontNewline * item['break'])
					except: message += newline

		if text: self.text(title = title, message = message, mono = mono)
		else: self.confirm(title = title, message = message)

	@classmethod
	def select(self, items, multiple = False, selection = None, details = False, fix = True, title = None):
		# Some Kodi skins (eg: Confluence and Estouchy) make labels bold by default.
		# This causes nested bold labels (one from Gaia and one from the skin).
		# When displayed, there is always a trailing "[/B]" in the label. Eg: "Some label in the dialog [/B]".
		# Adding a newline seems to fix it.
		if details and fix:
			try:
				for i in range(len(items)):
					label = items[i].getLabel()
					if '[B]' in label: items[i].setLabel(label + Format.FontNewline)
					label = items[i].getLabel2()
					if '[B]' in label: items[i].setLabel2(label + Format.FontNewline)
			except: tools.Logger.error()

		if multiple:
			try: return xbmcgui.Dialog().multiselect(self.title(title), items, preselect = selection, useDetails = details)
			except: return xbmcgui.Dialog().multiselect(self.title(title), items, useDetails = details)
		else:
			if tools.Tools.isString(selection): selection = items.index(selection)
			try: return xbmcgui.Dialog().select(self.title(title), items, preselect = selection, useDetails = details)
			except: return xbmcgui.Dialog().select(self.title(title), items, useDetails = details)

	@classmethod
	def option(self, message, labelConfirm = None, labelDeny = None, default = None, timeout = None, title = None):
		if not labelConfirm is None: labelConfirm = self.__translate(labelConfirm)
		if not labelDeny is None: labelDeny = self.__translate(labelDeny)

		# Only supported since Kodi 20.
		if not default is None:
			if tools.System.versionKodiMinimum(20.0):
				if default == Dialog.ChoiceYes: default = xbmcgui.DLG_YESNO_YES_BTN
				elif default == Dialog.ChoiceNo: default = xbmcgui.DLG_YESNO_NO_BTN
				else: default = None
			else: default = None

		if not default is None and not timeout is None:	return xbmcgui.Dialog().yesno(self.title(title), self.__translate(message), yeslabel = labelConfirm, nolabel = labelDeny, autoclose = timeout, defaultbutton = default)
		elif not default is None: return xbmcgui.Dialog().yesno(self.title(title), self.__translate(message), yeslabel = labelConfirm, nolabel = labelDeny, defaultbutton = default)
		elif not timeout is None: return xbmcgui.Dialog().yesno(self.title(title), self.__translate(message), yeslabel = labelConfirm, nolabel = labelDeny, autoclose = timeout)
		else: return xbmcgui.Dialog().yesno(self.title(title), self.__translate(message), yeslabel = labelConfirm, nolabel = labelDeny)

	@classmethod
	def options(self, message, labelConfirm = None, labelDeny = None, labelCustom = None, default = None, timeout = None, title = None):
		if not labelConfirm is None: labelConfirm = self.__translate(labelConfirm)
		if not labelDeny is None: labelDeny = self.__translate(labelDeny)
		if not labelCustom is None: labelCustom = self.__translate(labelCustom)

		# Only supported since Kodi 20.
		if not default is None:
			if tools.System.versionKodiMinimum(20.0):
				if default == Dialog.ChoiceYes: default = xbmcgui.DLG_YESNO_YES_BTN
				elif default == Dialog.ChoiceNo: default = xbmcgui.DLG_YESNO_NO_BTN
				elif default == Dialog.ChoiceCustom: default = xbmcgui.DLG_YESNO_CUSTOM_BTN
				else: default = None
			else: default = None

		if not default is None and not timeout is None: return xbmcgui.Dialog().yesnocustom(self.title(title), self.__translate(message), yeslabel = labelConfirm, nolabel = labelDeny, customlabel = labelCustom, autoclose = timeout, defaultbutton = default)
		elif not default is None: return xbmcgui.Dialog().yesnocustom(self.title(title), self.__translate(message), yeslabel = labelConfirm, nolabel = labelDeny, customlabel = labelCustom, defaultbutton = default)
		elif not timeout is None: return xbmcgui.Dialog().yesnocustom(self.title(title), self.__translate(message), yeslabel = labelConfirm, nolabel = labelDeny, customlabel = labelCustom, autoclose = timeout)
		else: return xbmcgui.Dialog().yesnocustom(self.title(title), self.__translate(message), yeslabel = labelConfirm, nolabel = labelDeny, customlabel = labelCustom)

	# icon: icon or path to image file.
	# wait: wait if other notifications to finish before showing this one. Otherwise Kodi preempts the previous notification and immediately shows the next one.
	# titleless: Without Gaia at the front of the title.
	@classmethod
	def notification(self, message, icon = None, time = 4000, sound = None, wait = True, duplicates = False, title = None, titleless = False):
		if icon and not (icon.startswith('http') or icon.startswith('ftp') or tools.File.exists(icon)):
			icon = icon.lower()
			if icon == Dialog.IconNativeInformation: icon = xbmcgui.NOTIFICATION_INFO
			elif icon == Dialog.IconNativeWarning: icon = xbmcgui.NOTIFICATION_WARNING
			elif icon == Dialog.IconNativeError: icon = xbmcgui.NOTIFICATION_ERROR
			else:
				if icon == Dialog.IconPlain or icon == Dialog.IconNativeLogo: icon = 'plain'
				elif icon == Dialog.IconWarning: icon = 'warning'
				elif icon == Dialog.IconError: icon = 'error'
				elif icon == Dialog.IconSuccess: icon = 'success'
				else: icon = 'information'
				icon = Icon.pathIcon(icon = icon, special = Icon.SpecialNotifications)

		title = self.title(title, titleless = titleless)
		message = self.__translate(message)

		from lib.modules import window
		propertyTime = 'GaiaNotificationTime'
		propertyLabels = 'GaiaNotificationLabels'
		timeNow = timeWait = tools.Time.timestamp()

		waiting = None
		if wait:
			waiting = True
			try:
				timeWait = float(window.Window.propertyGlobal(propertyTime))
				if timeWait <= timeNow: waiting = False
			except: waiting = False

		# Do not show the message if it was already shown during this execution.
		# Prevents duplicate messages, like the "account limit reached" from Newznab providers when multiple queries are executed in parallel.
		if wait and not duplicates:
			id = ''
			try: id += title
			except: pass
			try: id += message
			except: pass
			if id and id in Dialog.Notifications and timeNow - Dialog.Notifications[id] < 60: return # Allow duplicates if older than 60 seconds.
			Dialog.Notifications[id] = timeNow

		if sound is None and tools.Sound.nativeNotify(): sound = True
		def _sound(time):
			tools.Sound.executeNotifyStart()
			if tools.Sound.enabledNotifyFinish(): Pool.thread(target = _soundFinish, kwargs = {'time' : time}, start = True)
		def _soundFinish(time):
			tools.Time.sleep(time / 1000.0)
			tools.Sound.executeNotifyFinish()

		window.Window.propertyGlobalSet(propertyTime, max(timeNow, timeWait) + (time / 1000.0))
		if waiting:
			def _notification(title, message, icon, time, sound):
				tools.Time.sleep(timeWait - timeNow)
				if sound is None: _sound(time = time)
				xbmcgui.Dialog().notification(title, message, icon, time, sound = sound is True)
			Pool.thread(target = _notification, args = (title, message, icon, time, sound), start = True)
		else:
			if sound is None: _sound(time = time)
			xbmcgui.Dialog().notification(title, message, icon, time, sound = sound is True)

	# items = [(label1,callback1),(label2,callback2),...]
	# or labels = [label1,label2,...]
	@classmethod
	def context(self, items = None, labels = None):
		if items:
			labels = [i[0] for i in items]
			choice = xbmcgui.Dialog().contextmenu(labels)
			if choice >= 0: return items[choice][1]()
			else: return False
		else:
			return xbmcgui.Dialog().contextmenu(labels)

	@classmethod
	def progress(self, message = None, background = False, percent = 0, title = None):
		if background: dialog = xbmcgui.DialogProgressBG()
		else: dialog = xbmcgui.DialogProgress()
		if not message: message = ''
		else: message = self.__translate(message)
		title = self.title(title)
		dialog.create(title, message)
		if background: dialog.update(percent, title, message)
		else: dialog.update(percent, message)
		return dialog

	# verify: Existing MD5 password string to compare against.
	# confirm: Confirm password. Must be entered twice
	# hidden: Hides alphabetic input.
	# default: Default set input.
	@classmethod
	def input(self, type = InputAlphabetic, verify = False, confirm = False, hidden = False, default = None, timeout = None, title = None):
		default = '' if default == None else default
		if verify:
			option = xbmcgui.PASSWORD_VERIFY
			if tools.Tools.isString(verify):
				default = verify
		elif confirm:
			option = 0
		elif hidden:
			option = xbmcgui.ALPHANUM_HIDE_INPUT
		else:
			option = None

		timeout = (timeout * 1000) if timeout else 0 # Milliseconds.

		# NB: Although the default parameter is given in the docs, it seems that the parameter is not actually called "default". Hence, pass it in as an unnamed parameter.
		if option is None: result = xbmcgui.Dialog().input(self.title(title), str(default), type = type, autoclose = timeout)
		else: result = xbmcgui.Dialog().input(self.title(title), str(default), type = type, autoclose = timeout, option = option)

		# When moving between day/month/year, Kodi can insert a space (eg: "1/ 1/2012").
		if type == Dialog.InputDate and result: result = result.replace(' ', '')

		if verify:
			return not result == ''
		elif type == Dialog.InputNumeric:
			if result == '': return None
			else: return float(result)
		else:
			return result

	@classmethod
	def inputPassword(self, verify = False, confirm = False, title = None):
		return self.input(title = title, type = Dialog.InputPassword, verify = verify, confirm = confirm)

	@classmethod
	def browse(self, type = BrowseDefault, default = None, multiple = False, mask = [], title = None):
		if default is None: default = tools.File.joinPath(tools.System.pathHome(), '') # Needs to end with a slash
		if mask is None: mask = []
		elif tools.Tools.isString(mask): mask = [mask]
		for i in range(len(mask)):
			mask[i] = mask[i].lower()
			if not mask[i].startswith('.'):
				mask[i] = '.' + mask[i]
		mask = '|'.join(mask)
		return xbmcgui.Dialog().browse(type, self.title(title), 'files', mask, True, False, default, multiple)

	@classmethod
	def info(self, item):
		return xbmcgui.Dialog().info(item)

	# Creates an information dialog.
	# Either a list of item categories, or a list of items.
	# Without actions:
	#	[
	#		{'title' : 'Category 1', 'items' : [{'title' : 'Name 1', 'value' : 'Value 1', 'link' : True}, {'title' : 'Name 2', 'value' : 'Value 2'}]},
	#		{'title' : 'Category 2', 'items' : [{'title' : 'Name 3', 'value' : 'Value 3', 'link' : False}, {'title' : 'Name 4', 'value' : 'Value 4'}]},
	#	]
	# With actions:
	#	[
	#		{'title' : 'Category 1', 'items' : [{'title' : 'Name 1', 'value' : 'Value 1', 'link' : True, 'action' : function, 'parameters' : {}, 'close' : True, 'return' : 'return value', 'back' : <True/False wether or not it is a back button - used for reselection>}, {'title' : 'Name 2', 'value' : 'Value 2', 'action' : function, 'close' : True}]},
	#		{'title' : 'Category 2', 'items' : [{'title' : 'Name 3', 'value' : 'Value 3', 'link' : False, 'action' : function, 'close' : True, 'return' : 'return value'}, {'title' : 'Name 4', 'value' : 'Value 4', 'action' : function, 'close' : True}]},
	#	]
	# Pick the item with a 'selection' attribute (if no 'selection' parameter was provided to the function):
	#	[
	#		{'title' : 'Category 1', 'items' : [{'title' : 'Name 1', 'value' : 'Value 1', 'selection' : True}]},
	#	]
	@classmethod
	def information(self, items = None, title = None, refresh = None, reselect = ReselectNo, selection = None, offset = None, details = False, id = None, copy = False):
		if items is None or len(items) == 0:
			if refresh: items = refresh()
			if items is None or len(items) == 0: return False

		def decorate(item):
			label = item['title'] if 'title' in item else ''
			if 'prefix' in item:
				if item['prefix'] is True: label = self.prefixNext(Translation.string(label))
				else: label = item['prefix'] + Translation.string(label)

			value = item['value'] if 'value' in item else None
			bold = item['bold'] if 'bold' in item else True
			color = item['color'] if 'color' in item else True
			prefix = Dialog.prefixContains(label)
			if not prefix: label = self.__translate(label)
			if value is None:
				heading = value or 'items' in item
				label = Format.font(label, bold = bold, uppercase = heading, color = Format.colorPrimary() if heading and color else None, translate = False if prefix else True)
			else:
				if not label == '':
					if not value is None:
						label += ': '
					label = Format.font(label, bold = bold, color = Format.colorSecondary() if color else None)
				if not value is None:
					label += Format.font(self.__translate(item['value']), italic = ('link' in item and item['link']))

			return label

		def undecorate(label):
			if tools.Tools.isString(label): label = Format.clean(label)
			return label

		def create(items):
			if not items: return None, None, None, None, None, None, None
			labels = []
			copies = []
			actions = []
			parameters = []
			closes = []
			returns = []
			selection = None

			index = -1
			total = len(items)
			end = total - 1

			for i in range(total):
				item = items[i]
				if not item is None and not(item == Dialog.EmptyLine and i == end): # Exclude empty separator if it is the last element
					if 'items' in item:
						if not len(labels) == 0:
							index += 1
							labels.append('')
							copies.append(None)
							actions.append(None)
							parameters.append(None)
							closes.append(None)
							returns.append(None)

						index += 1
						labels.append(decorate(item))
						copies.append(undecorate(item['value']) if 'value' in item else None)
						actions.append(item['action'] if 'action' in item else None)
						parameters.append(item['parameters'] if 'parameters' in item else None)
						closes.append(item['close'] if 'close' in item else False)
						returns.append(item['return'] if 'return' in item else None)
						if 'selection' in item and item['selection'] and selection is None: selection = index

						for it in item['items']:
							if not it is None:
								index += 1
								labels.append(decorate(it))
								copies.append(undecorate(it['value']) if 'value' in it else None)
								actions.append(it['action'] if 'action' in it else None)
								parameters.append(it['parameters'] if 'parameters' in it else None)
								closes.append(it['close'] if 'close' in it else False)
								returns.append(it['return'] if 'return' in it else None)
								if 'selection' in it and it['selection'] and selection is None: selection = index
					else:
						index += 1
						labels.append(decorate(item))
						copies.append(undecorate(item['value']) if 'value' in item else None)
						actions.append(item['action'] if 'action' in item else None)
						parameters.append(item['parameters'] if 'parameters' in item else None)
						closes.append(item['close'] if 'close' in item else False)
						returns.append(item['return'] if 'return' in item else None)
						if 'selection' in item and item['selection'] and selection is None: selection = index

			return labels, copies, actions, parameters, closes, returns, selection

		def menuId(items, generate = True):
			# Create the id only with the title attributes, since the value attributes might get a different value.
			result = []
			if tools.Tools.isDictionary(items):
				for key, value in items.items():
					if key == 'title': result.append(value)
					elif key == 'items': result.extend(menuId(value, generate = False))
			elif tools.Tools.isArray(items):
				for item in items:
					result.extend(menuId(item, generate = False))
			if generate: return tools.Hash.hash(tools.Converter.jsonTo(result))
			else: return result

		labels, copies, actions, parameters, closes, returns, selected = create(items)
		if selection is None: selection = selected

		choiceId = None
		choices = {}

		if labels:
			if any(i for i in actions):
				choice = selection
				while labels:

					if reselect == Dialog.ReselectMenu:
						reselection = True
						if id:
							if tools.Tools.isFunction(id): choiceId = id()
							else: choiceId = id
						else: choiceId = menuId(items)
						try: choice = choices[choiceId] # Allow different selections for submenus.
						except: choice = None
					elif tools.Tools.isNumber(value = reselect, bool = False):
						choice = reselect

					if tools.Tools.isFunction(reselect):
						reselection = reselect()
					else:
						reselection = reselect

					if offset and not choice is None: choice += offset()

					if reselection: choice = self.select(items = labels, title = title, selection = choice, details = details)
					else: choice = self.select(items = labels, title = title, details = details)
					if choiceId:
						try: remember = items[choice]['remember'] # Exclude items marked asa not to remember.
						except: remember = True
						if remember: choices[choiceId] = choice

					if copy:
						from lib.modules.clipboard import Clipboard
						try: Clipboard.copy(copies[choice])
						except: pass

					if choice < 0: break
					if actions[choice]:
						if parameters[choice]: actions[choice](**parameters[choice])
						else: actions[choice]()
					if closes[choice]: return returns[choice]
					elif refresh:
						items = refresh()
						labels, copies, actions, parameters, closes, returns, selected = create(items)

				return choice
			elif any(i for i in returns):
				choice = self.select(labels, title = title, selection = selection, details = details)
				if copy:
					from lib.modules.clipboard import Clipboard
					try: Clipboard.copy(copies[choice])
					except: pass
				if choice < 0: return None
				return returns[choice]
			else:
				choice = self.select(labels, title = title, selection = selection, details = details)
				if copy:
					from lib.modules.clipboard import Clipboard
					try: Clipboard.copy(copies[choice])
					except: pass
				return choice

	# Creates an enabled/disable dialog.
	# items = [{
	#	label : label to display,
	#	id : optional key/id to use for the results, otherwise use the label as id,
	#	value : enabled/disabled (bool),
	#	prefix : optional prefix added with square brackets to the start,
	#	suffix : optional suffix added with round brackets to the end,
	#	bold : wethter or not to make the label bold (bool),
	# }, ...]
	# options = [
	#	Dialog.ToggleApply : adds an option to accept the current selection.
	#	Dialog.ToggleBack : adds an option to accept the current selection.
	#	Dialog.ToggleCancel : adds an option to cancel the current selection, not accepting it, and returning the original values.
	#	Dialog.ToggleEnable : adds an option to enable all items.
	#	Dialog.ToggleDisable : adds an option to disable all items.
	#	Dialog.ToggleInverse : adds an option to inverse the values of all items.
	#	Dialog.ToggleDefault : adds an option to reset all items to a default value.
	#		If "Dialog.ToggleDefault", will use ther original values from the items parameter.
	#		If "(Dialog.ToggleDefault, True)", will reset all to True.
	#		If "(Dialog.ToggleDefault, False)", will reset all to False.
	#		If "(Dialog.ToggleDefault, {key1 : value1, key2 : value2})", will reset to the values specified in the dictionary.
	#	Custom options can be passed in as "('Label', function)". The function takes the items list as parameter. If the function returns True, the dialog wiill be closed accepting the changes. If the function returns False, the dialog wiill be closed without accepting the changes.
	# ]
	# bold: Make all labels bold.
	@classmethod
	def toggle(self, items = None, options = None, bold = None, title = None, cancel = True):
		enabled = Format.fontColor(32301, Format.colorExcellent())
		disabled = Format.fontColor(32302, Format.colorBad())

		def _toggleItems(items, actions):
			return [action if action else '' for action in actions] + [_toggleLabel(item) for item in items]

		def _toggleLabel(item):
			prefix = ''
			if 'prefix' in item:
				prefix = self.__translate(item['prefix'])
				if prefix.upper() in ['B', 'I', 'CR']: prefix = '[%s\1] ' % prefix # Kodi label formatting (eg: [CR] aka Crunchyroll will be seen as line break).
				else: prefix = Format.fontBold('[%s] ' % prefix)
			label = prefix + self.__translate(item['label']) + ((' (%s)' % self.__translate(item['suffix'])) if 'suffix' in item else '')
			if bold or 'bold' in item and item['bold']: label = Format.fontBold(label)
			return '%s: %s' % (label, enabled if item['value'] else disabled)

		def _toggleApply(items):
			return True

		def _toggleBack(items):
			return True

		def _toggleCancel(items):
			return False

		def _toggleEnable(items):
			for i in range(len(items)):
				items[i]['value'] = True

		def _toggleDisable(items):
			for i in range(len(items)):
				items[i]['value'] = False

		def _toggleInverse(items):
			for i in range(len(items)):
				items[i]['value'] = not items[i]['value']

		def _toggleDefault(items):
			for i in range(len(items)):
				items[i]['value'] = defaults[items[i]['id' if 'id' in items[i] else 'label']]

		offset = 0
		functions = []
		actions = []
		defaults = None
		original = {item['id'] if 'id' in item else item['label'] : item['value'] for item in items}

		if options:
			offset = len(options) + 1

			for option in options:
				if tools.Tools.isArray(option):
					if option[0] == Dialog.ToggleDefault:
						actions.append(self.prefixNext(Format.fontBold(33564), bold = True))
						if option[1] is True:
							functions.append(_toggleEnable)
						elif option[1] is False:
							functions.append(_toggleDisable)
						else:
							functions.append(_toggleDefault)
							defaults = option[1]
					else:
						actions.append(self.prefixNext(Format.fontBold(option[0]), bold = True))
						functions.append(option[1])
				elif option == Dialog.ToggleDefault:
					actions.append(self.prefixNext(Format.fontBold(33564), bold = True))
					functions.append(_toggleDefault)
					defaults = {item['id' if 'id' in item else 'label'] : item['value'] for item in items}
				elif option == Dialog.ToggleApply:
					actions.append(self.prefixNext(Format.fontBold(35478), bold = True))
					functions.append(_toggleApply)
				elif option == Dialog.ToggleBack:
					actions.append(self.prefixBack(Format.fontBold(35374), bold = True))
					functions.append(_toggleBack)
				elif option == Dialog.ToggleCancel:
					actions.append(self.prefixBack(Format.fontBold(33743), bold = True))
					functions.append(_toggleCancel)
				elif option == Dialog.ToggleEnable:
					actions.append(self.prefixNext(Format.fontBold(35435), bold = True))
					functions.append(_toggleEnable)
				elif option == Dialog.ToggleDisable:
					actions.append(self.prefixNext(Format.fontBold(35436), bold = True))
					functions.append(_toggleDisable)
				elif option == Dialog.ToggleInverse:
					actions.append(self.prefixNext(Format.fontBold(35163), bold = True))
					functions.append(_toggleInverse)

			actions.append(None)

		entries = _toggleItems(items, actions)
		choice = None
		while True:
			choice = self.select(title = title, items = entries, selection = choice)
			if choice < 0:
				if cancel: return original
				else: break
			elif choice < offset:
				try:
					result = functions[choice](items)
					if result is True: break
					elif result is False: return original
					entries = _toggleItems(items, actions)
				except: pass
			else:
				index = choice - offset
				items[index]['value'] = not items[index]['value']
				entries[choice] = _toggleLabel(items[index])

		return {item['id'] if 'id' in item else item['label'] : item['value'] for item in items}

	@classmethod
	def __translate(self, string):
		return Translation.string(string)

	@classmethod
	def title(self, extension = None, bold = True, titleless = False):
		title = '' if titleless else tools.System.name()
		if not extension == None:
			if not titleless:
				title += Format.iconSeparator(color = True, pad = True)
			title += self.__translate(extension)
		if bold:
			title = Format.fontBold(title)
		return title


class Splash(xbmcgui.WindowDialog):

	# Types
	TypeMini = 'mini'
	TypeName = 'name'
	TypeIcon = 'icon'
	TypeAbout = 'about'
	TypeMessage = 'message'

	# Actions
	ActionSelectItem = 7
	ActionPreviousMenu = 10
	ActionNavigationBack = 92
	ActionMoveRight = 2
	ActionMoveLeft = 1
	ActionsCancel = [ActionPreviousMenu, ActionNavigationBack, ActionMoveRight]
	ActionsMaximum = 100 # Mouse other unwanted actions.

	# Duration
	Duration = 2

	# All Kodi windows have this fixed dimension.
	SizeWidth = 1280
	SizeHeight = 720

	# Size
	SizeLarge = 'large'
	SizeMedium = 'medium'
	SizeSmall = 'small'

	# Format
	FormatWhite = '0xFFFFFFFF'
	FormatCenter = 0x00000002 | 0x00000004
	FormatJustified = 0x00000010 | 0x00000004

	Instance = None

	def __init__(self, type, message = None):
		Loader.show()

		self.mType = type

		self.mScaleWidthExtra = 1
		self.mScaleHeightExtra = 1
		self.mScaleWidth = tools.Screen.height() / float(Splash.SizeHeight)
		self.mScaleHeight = tools.Screen.width() / float(Splash.SizeWidth)
		if self.mScaleWidth > self.mScaleHeight:
			self.mScaleWidth = self.mScaleWidth / self.mScaleHeight
			self.mScaleHeight = 1
			self.mScaleWidthExtra = self.mScaleHeightExtra = self.mScaleHeight / self.mScaleWidth
		elif self.mScaleWidth < self.mScaleHeight:
			self.mScaleHeight = self.mScaleHeight / self.mScaleWidth
			self.mScaleWidth = 1
			self.mScaleWidthExtra = self.mScaleHeightExtra = self.mScaleWidth / self.mScaleHeight

		# If the screen size is exactly the same ratio as the Kodi fixed resolution (Splash.SizeWidth and Splash.SizeHeight).
		# Otheriwse the splash fills the entire window.
		if self.mScaleWidthExtra == 1 and self.mScaleHeightExtra == 1:
			self.mScaleWidthExtra *= 0.75
			self.mScaleHeightExtra *= 0.75

		self.mWidth = Splash.SizeWidth
		self.mHeight = Splash.SizeHeight

		self.mButtonPremiumize = None
		self.mButtonOffCloud = None
		self.mButtonRealDebrid = None
		self.mButtonEasyNews = None
		self.mButtonFreeHosters = None
		self.mButtonClose = None

		try:
			if type == Splash.TypeMini:
				widthTotal, heightTotal = self.__window(False, True)
			elif type == Splash.TypeName:
				width = self.__scaleWidth(379)
				height = self.__scaleHeight(192)
				x = self.__centerX(width)
				y = self.__centerY(height)
				self.addControl(xbmcgui.ControlImage(x, y, width, height, self.__name(True)))
			elif type == Splash.TypeIcon:
				width = self.__scaleWidth(381)
				height = self.__scaleHeight(384)
				x = self.__centerX(width)
				y = self.__centerY(height)
				self.addControl(xbmcgui.ControlImage(x, y, width, height, self.__icon(True, Splash.SizeLarge)))
			elif type == Splash.TypeAbout:
				widthTotal, heightTotal = self.__window(True, True)

				width = widthTotal
				height = heightTotal
				x = self.__centerX(widthTotal)
				y = self.__centerY(heightTotal) - self.__scaleHeight(30)
				label = Format.fontBold(Translation.string(33359) + ' ' + tools.System.version())
				label += Format.newline() + Format.fontBold(tools.Settings.getString('internal.link.website', raw = True))
				self.addControl(xbmcgui.ControlLabel(x, y, width, height, label, textColor = Splash.FormatWhite, alignment = Splash.FormatCenter))

				width = widthTotal - self.__scaleWidth(165)
				height = self.__scaleHeight(150)
				x = self.__centerX(widthTotal) + self.__scaleWidth(83)
				y = self.__centerY(heightTotal) + self.__scaleHeight(285)
				label = tools.System.disclaimer()
				self.__textbox(x, y, width, height, label)

				self.mButtonClose = self.__button(
					buttonLabel = '       Close',
					buttonX = self.__centerX(widthTotal) + self.__scaleWidth(375),
					buttonY = self.__centerY(heightTotal) + self.__scaleHeight(450),
					buttonWidth = self.__scaleWidth(150),
					buttonHeight = self.__scaleHeight(53),

					iconPath = Icon.path('error.png', type = Icon.themeIcon()),
					iconX = self.__centerX(widthTotal) + self.__scaleWidth(379),
					iconY = self.__centerY(heightTotal) + self.__scaleHeight(450),
					iconWidth = self.__scaleWidth(53),
					iconHeight = self.__scaleHeight(53),
				)

			elif type == Splash.TypeMessage:
				widthTotal, heightTotal = self.__window(True, True)

				width = widthTotal - self.__scaleWidth(165)
				height = self.__scaleHeight(210)
				x = self.__centerX(widthTotal) + self.__scaleWidth(83)
				y = self.__centerY(heightTotal) + self.__scaleHeight(225)
				self.__textbox(x, y, width, height, message, font = Font.fontLarge())

				self.mButtonClose = self.__button(
					buttonLabel = '       Close',
					buttonX = self.__centerX(widthTotal) + self.__scaleWidth(375),
					buttonY = self.__centerY(heightTotal) + self.__scaleHeight(450),
					buttonWidth = self.__scaleWidth(150),
					buttonHeight = self.__scaleHeight(53),

					iconPath = Icon.path('error.png', type = Icon.themeIcon()),
					iconX = self.__centerX(widthTotal) + self.__scaleWidth(379),
					iconY = self.__centerY(heightTotal) + self.__scaleHeight(450),
					iconWidth = self.__scaleWidth(53),
					iconHeight = self.__scaleHeight(53),
				)
		except: tools.Logger.error()
		Loader.hide()

	def __theme(self):
		from lib.modules.theme import Theme
		theme = Theme.skin()
		theme = theme.replace(' ', '').lower()
		index = theme.find('(')
		if index >= 0: theme = theme[:index]
		return theme

	def __logo(self, size = SizeMedium):
		return tools.File.joinPath(tools.System.pathResources(), 'resources', 'media', 'logo', size)

	def __name(self, force = False, size = SizeMedium):
		theme = self.__theme()
		return tools.File.joinPath(self.__logo(size), 'namecolor.png' if force or theme == 'default' or 'gaia' in theme  else 'nameglass.png')

	def __icon(self, force = False, size = SizeMedium):
		theme = self.__theme()
		return tools.File.joinPath(self.__logo(size), 'iconcolor.png' if force or theme == 'default' or 'gaia' in theme else 'iconglass.png')

	def __interface(self):
		return tools.File.joinPath(tools.System.pathResources(), 'resources', 'media', 'interface')

	def __skin(self):
		theme = self.__theme()
		addon = tools.System.pathResources() if theme == 'default' or 'gaia' in theme else tools.System.pathSkins()
		return tools.File.joinPath(addon, 'resources', 'media', 'skins', theme)

	def __scaleWidth(self, value):
		return int(self.mScaleWidth * self.mScaleWidthExtra * value)

	def __scaleHeight(self, value):
		return int(self.mScaleHeight * self.mScaleHeightExtra * value)

	def __window(self, full = True, logo = True):
		if full:
			name = 'splashfull.png'
			width = self.__scaleWidth(900)
			height = self.__scaleHeight(563)
			logoWidth = self.__scaleWidth(263)
			logoHeight = self.__scaleHeight(133)
			logoX = self.__scaleWidth(319)
			logoY = self.__scaleHeight(75)
		else:
			name = 'splashmini.png'
			width = self.__scaleWidth(525)
			height = self.__scaleHeight(315)
			logoWidth = self.__scaleWidth(370)
			logoHeight = self.__scaleHeight(188)
			logoX = self.__scaleWidth(77)
			logoY = self.__scaleHeight(64)

		x = self.__centerX(width)
		y = self.__centerY(height)

		path = tools.File.joinPath(self.__skin(), 'interface', name)
		if tools.File.exists(path):
			self.addControl(xbmcgui.ControlImage(x, y, width, height, path))

		path = tools.File.joinPath(self.__interface(), name)
		self.addControl(xbmcgui.ControlImage(x, y, width, height, path))

		if logo:
			logoX = self.__centerX(width) + logoX
			logoY = self.__centerY(height) + logoY
			path = self.__name()
			self.addControl(xbmcgui.ControlImage(logoX, logoY, logoWidth, logoHeight, path))

		return (width, height)

	def __button(self, buttonLabel, buttonX, buttonY, buttonWidth, buttonHeight, iconPath = None, iconX = None, iconY = None, iconWidth = None, iconHeight = None, infoLabel = None, infoX = None, infoY = None, infoWidth = None, infoHeight = None):
		pathNormal = pathFocus = tools.File.joinPath(self.__interface(), 'button', 'medium', 'outer.png')

		buttonLabel = Format.fontBold(buttonLabel)
		self.addControl(xbmcgui.ControlButton(buttonX, buttonY, buttonWidth, buttonHeight, buttonLabel, focusTexture = pathFocus, noFocusTexture = pathNormal, alignment = Splash.FormatCenter, textColor = Splash.FormatWhite, font = Font.fontLarge()))

		if not iconPath == None:
			self.addControl(xbmcgui.ControlImage(iconX, iconY, iconWidth, iconHeight, iconPath))

		if not infoLabel == None:
			# Do not use named parameters, since it causes a crash.
			info = xbmcgui.ControlFadeLabel(infoX, infoY, infoWidth, infoHeight, Font.fontSmall(), Splash.FormatWhite, Splash.FormatCenter)
			self.addControl(info)
			info.addLabel(infoLabel)

		return (buttonX, buttonY)

	def __textbox(self, x, y, width, height, label, delay = 3000, time = 4000, repeat = True, font = None):
		if font is None: font = Font.fontMedium()
		box = xbmcgui.ControlTextBox(x, y, width, height, textColor = Splash.FormatWhite, font = font)
		self.addControl(box)
		box.autoScroll(delay, time, repeat)
		box.setText(label)

	def __centerX(self, width):
		return int((self.mWidth - width) / 2)

	def __centerY(self, height):
		return int((self.mHeight - height) / 2)

	def __referalPremiumize(self):
		from lib.debrid import premiumize
		premiumize.Core.website(open = True)
		self.close()

	def __referalOffCloud(self):
		from lib.debrid import offcloud
		offcloud.Core.website(open = True)
		self.close()

	def __referalRealDebrid(self):
		from lib.debrid import realdebrid
		realdebrid.Core.website(open = True)
		self.close()

	def __referalEasyNews(self):
		from lib.debrid import easynews
		easynews.Core.website(open = True)
		self.close()

	def __continue(self):
		self.close()

	def onControl(self, control):
		distances = []
		actions = []
		if self.mButtonPremiumize:
			distances.append(abs(control.getX() - self.mButtonPremiumize[0]) + abs(control.getY() - self.mButtonPremiumize[1]))
			actions.append(self.__referalPremiumize)
		if self.mButtonOffCloud:
			distances.append(abs(control.getX() - self.mButtonOffCloud[0]) + abs(control.getY() - self.mButtonOffCloud[1]))
			actions.append(self.__referalOffCloud)
		if self.mButtonRealDebrid:
			distances.append(abs(control.getX() - self.mButtonRealDebrid[0]) + abs(control.getY() - self.mButtonRealDebrid[1]))
			actions.append(self.__referalRealDebrid)
		if self.mButtonEasyNews:
			distances.append(abs(control.getX() - self.mButtonEasyNews[0]) + abs(control.getY() - self.mButtonEasyNews[1]))
			actions.append(self.__referalEasyNews)
		if self.mButtonFreeHosters:
			distances.append(abs(control.getX() - self.mButtonFreeHosters[0]) + abs(control.getY() - self.mButtonFreeHosters[1]))
			actions.append(self.__continue)
		if self.mButtonClose:
			distances.append(abs(control.getX() - self.mButtonClose[0]) + abs(control.getY() - self.mButtonClose[1]))
			actions.append(self.__continue)

		smallestIndex = -1
		smallestDistance = 999999
		for i in range(len(distances)):
			if distances[i] < smallestDistance:
				smallestDistance = distances[i]
				smallestIndex = i

		if smallestIndex < 0:
			self.__continue()
		else:
			actions[smallestIndex]()

	def onAction(self, action):
		action = action.getId()
		if action < Splash.ActionsMaximum:
			if self.mButtonClose == None:
				if action in Splash.ActionsCancel:
					self.__continue()
				else:
					from lib.modules.network import Networker
					Networker.linkShow(link = tools.Settings.getString('internal.link.website', raw = True))
			else:
				self.__continue()

	def close(self):
		super(Splash, self).close()
		#self.popupClose()

	@classmethod
	def visible(self):
		try: return Splash.Instance.visible()
		except: return not Splash.Instance is None

	@classmethod
	def type(self):
		type = tools.Settings.getString('general.launch.splash')
		try: return int(type)
		except: return None

	@classmethod
	def loader(self):
		type = self.type()
		return not type is None or type > 0

	@classmethod
	def popup(self, time = Duration, wait = True, slogan = False, alternative = False):
		try:
			type = self.type()
			if type is None or type == 4:
				from lib.modules import window
				window.WindowIntro.show(wait = wait, slogan = slogan, alternative = alternative)
				Splash.Instance = window.WindowIntro.instance()
			elif type == 1: self.popupIcon(time = time)
			elif type == 2: self.popupName(time = time)
			elif type == 3: self.popupMini(time = time)
		except:
			pass
		return Splash.Instance

	@classmethod
	def popupClose(self):
		try: Splash.Instance.close(wait = True) # WindowIntro
		except:
			try: Splash.Instance.close()
			except: pass
		Splash.Instance = None

	@classmethod
	def popupMini(self, time = Duration, wait = False):
		try:
			# So that the interface can load in the background while the splash loads.
			thread = Pool.thread(target = self.__popupMini, args = (time,))
			thread.start()
			if wait: thread.join()
		except:
			pass

	@classmethod
	def popupName(self, time = Duration, wait = False):
		try:
			# So that the interface can load in the background while the splash loads.
			thread = Pool.thread(target = self.__popupName, args = (time,))
			thread.start()
			if wait: thread.join()
		except:
			pass

	@classmethod
	def popupIcon(self, time = Duration, wait = False):
		try:
			# So that the interface can load in the background while the splash loads.
			thread = Pool.thread(target = self.__popupIcon, args = (time,))
			thread.start()
			if wait: thread.join()
		except:
			pass

	@classmethod
	def popupAbout(self, wait = False):
		try:
			# So that the interface can load in the background while the splash loads.
			thread = Pool.thread(target = self.__popupAbout)
			thread.start()
			if wait: thread.join()
		except:
			pass

	@classmethod
	def popupMessage(self, message, wait = False):
		try:
			# So that the interface can load in the background while the splash loads.
			thread = Pool.thread(target = self.__popupMessage, args = (message,))
			thread.start()
			if wait: thread.join()
		except:
			pass

	@classmethod
	def __popupMini(self, time = Duration):
		try:
			Splash.Instance = Splash(Splash.TypeMini)
			if time:
				Splash.Instance.show()
				tools.Time.sleep(time)
				Splash.Instance.close()
				Splash.Instance = None
			else:
				Splash.Instance.doModal()
		except:
			pass

	@classmethod
	def __popupName(self, time = Duration):
		try:
			Splash.Instance = Splash(Splash.TypeName)
			if time:
				Splash.Instance.show()
				tools.Time.sleep(time)
				Splash.Instance.close()
				Splash.Instance = None
			else:
				Splash.Instance.doModal()
		except:
			pass

	@classmethod
	def __popupIcon(self, time = Duration):
		try:
			Splash.Instance = Splash(Splash.TypeIcon)
			if time:
				Splash.Instance.show()
				tools.Time.sleep(time)
				Splash.Instance.close()
				Splash.Instance = None
			else:
				Splash.Instance.doModal()
		except:
			pass

	@classmethod
	def __popupAbout(self):
		try:
			Splash.Instance = Splash(Splash.TypeAbout)
			Splash.Instance.doModal()
		except:
			pass

	@classmethod
	def __popupMessage(self, message):
		try:
			Splash.Instance = Splash(Splash.TypeMessage, message = message)
			Splash.Instance.doModal()
		except:
			pass


# Spinner loading bar
class Loader(object):

	Id = 'busydialognocancel'
	IdCancel = 'busydialog'
	Enabled = True

	@classmethod
	def show(self):
		if Loader.Enabled: tools.System.execute('ActivateWindow(%s)' % Loader.Id)

	@classmethod
	def hide(self, wait = False, delay = None):
		if delay: tools.Time.sleep(delay)
		tools.System.execute('Dialog.Close(%s)' % Loader.Id)
		tools.System.execute('Dialog.Close(%s)' % Loader.IdCancel)
		if wait:
			while self.visible(): tools.Time.sleep(0.1)

	# Important to check for busydialog aas well for HandlerElemetum if the torrent fails to be started.
	@classmethod
	def visible(self):
		return tools.System.visible('Window.IsActive(%s)' % Loader.Id) or tools.System.visible('Window.IsActive(%s)' % Loader.IdCancel)

	@classmethod
	def enable(self, enable = True):
		Loader.Enabled = enable

	@classmethod
	def disable(self, disable = True):
		Loader.Enabled = not disable


class Item(xbmcgui.ListItem):

	pass


# Kodi Directory Interface
class Directory(object):

	# https://alwinesch.github.io/group__python__xbmcgui__window__xml.html#gaa30572d1e5d9d589e1cd3bfc1e2318d6
	ContentAddons = 'addons'
	ContentFiles = 'files'
	ContentVideos = 'videos'
	ContentImages = 'images'
	ContentMovies = 'movies'
	ContentShows = 'tvshows'
	ContentSeasons = 'seasons'
	ContentEpisodes = 'episodes'
	ContentSets = 'sets'
	ContentAlbums = 'albums'
	ContentSongs = 'songs'
	ContentMusicVideos = 'musicvideos'
	ContentArtists = 'artists'
	ContentActors = 'actors'
	ContentDirectors = 'directors'
	ContentStudios = 'studios'
	ContentCountries = 'countries'
	ContentGames = 'games'
	ContentTags = 'tags'
	ContentYears = 'years'
	ContentGenres = 'genres'
	ContentPlaylists = 'playlists'
	ContentMixed = 'mixed'

	ContentNone = ''
	ContentSettings = 'settings'
	ContentGeneral = 'general'
	ContentDefault = ContentNone
	ContentMedia = [ContentMovies, ContentShows, ContentSeasons, ContentEpisodes, ContentSets, ContentMixed]

	PropertyId = 'GaiaMenuId'

	def __init__(self, content = ContentDefault, media = ContentGeneral, category = None, view = True, cache = True, update = False, lock = False):
		self.mHandle = tools.System.handle()
		self.mMedia = tools.Media.Movie if tools.Media.isFilm(media) else media

		self.mContent = content
		if content == Directory.ContentSettings:
			from lib.modules.view import View
			self.mContent = View.settingsLayoutGet(media = media, fallback = True)

		self.mView = view
		self.mCache = cache
		self.mUpdate = update
		self.mLock = lock
		self.mId = None

		# The description on main menu items is accomplished with: item.setInfo(type = 'video', infoLabels = {'plot' : '...'})
		# Some skins add additional decorations if setInfo() is called with 'video' (eg Aeon Nox adds a yellow star in 'Icons' view).
		# Disable descriptions for Aeon Nox (and  maybe other skins in the future).
		self.mDescription = not Skin.isAeon()

		self.mCategory = category

	@classmethod
	def back(self):
		tools.System.execute('Action(Back)')

	@classmethod
	def decorate(self, item, icon = None, iconDefault = None, iconSpecial = None):
		# For Gaia Eminence.
		item.setProperty('GaiaIconLarge', Icon.path(icon = icon, type = Icon.TypeIcon, quality = Icon.QualityLarge, default = iconDefault, special = iconSpecial))
		item.setProperty('GaiaIconSmall', Icon.path(icon = icon, type = Icon.TypeIcon, quality = Icon.QualitySmall, default = iconDefault, special = iconSpecial))
		item.setProperty('GaiaIconMini', Icon.path(icon = icon, type = Icon.TypeIcon, quality = Icon.QualityMini, default = iconDefault, special = iconSpecial))

	# context = [{'label', 'action', 'parameters'}]
	# info = (type, label-dict)
	# Optional 'command' parameter to specify a custom command instead of construction one from action and parameters.
	def add(self, label, link = None, description = None, action = None, parameters = None, context = None, info = None, folder = False, icon = None, iconDefault = None, iconSpecial = None, fanart = None, lock = None):
		item = self.item(label = Translation.string(label), lock = lock)

		if context and len(context) > 0:
			if tools.Tools.isDictionary(context[0]):
				contextMenu = []
				for c in context:
					contextLabel = Translation.string(c['label'])
					if 'command' in c:
						command = c['command']
					else:
						contextAction = c['action'] if 'action' in c else None
						contextParameters = c['parameters'] if 'parameters' in c else None
						command = tools.System.commandPlugin(action = contextAction, parameters = contextParameters)
					contextMenu.append((contextLabel, command))
			else:
				contextMenu = context
			item.addContextMenuItems(contextMenu)

		iconIcon, iconThumb, iconPoster, iconBanner = Icon.pathAll(icon = icon, default = iconDefault, special = iconSpecial)
		item.setArt({'icon': iconIcon, 'thumb': iconThumb, 'poster': iconPoster, 'banner': iconBanner})
		self.decorate(item = item, icon = icon, iconDefault = iconDefault, iconSpecial = iconSpecial)

		if not fanart is False:
			if fanart is True:
				from lib.modules.theme import Theme
				fanart = Theme.fanart()
			item.setProperty('Fanart_Image', fanart)

		infoType = 'video'
		infoLabels = {}
		if info:
			infoType = info[0]
			infoLabels = info[1]
		if description and self.mDescription:
			infoLabels['plot'] = Translation.string(description)
		if infoLabels:
			from lib.meta.tools import MetaTools
			MetaTools.instance().itemInfo(item = item, metadata = infoLabels, type = infoType)

		if link is None: link = tools.System.commandPlugin(action = action, parameters = parameters, call = False)
		self.addItem(link = link, item = item, folder = folder)

	def addItem(self, link, item, folder = False):
		self._id(item = item)
		xbmcplugin.addDirectoryItem(handle = self.mHandle, url = link, listitem = item, isFolder = folder)

	def addItems(self, items):
		if items: self._id(item = items[0][1])
		xbmcplugin.addDirectoryItems(handle = self.mHandle, items = items)

	def _id(self, item):
		# Used by view.py to determine if the menu was finished loading.
		if item and self.mId is None:
			self.mId = str(tools.Time.timestamp()) # Must be string for comparison.
			item.setProperty(Directory.PropertyId, self.mId)

	def finish(self, content = None, cache = None, update = None, view = None, loader = False, select = None):
		# Manually set sorting method, otherwise Kodi's default skin shows a "Sort by Date" label, although it is not always sorted by date.
		sorting = ['SORT_METHOD_UNSORTED']
		if self.mMedia == tools.Media.Movie or self.mMedia == tools.Media.Set or self.mMedia == tools.Media.Show or self.mMedia == tools.Media.Season or self.mMedia == tools.Media.Episode:
			tools.System.pluginPropertySet(property = 'GaiaMenuMedia', value = self.mMedia) # For Gaia Eminence.
			sorting.extend([
				'SORT_METHOD_LABEL',
				'SORT_METHOD_TITLE',
				'SORT_METHOD_TITLE_IGNORE_THE',
				'SORT_METHOD_VIDEO_ORIGINAL_TITLE', # AttributeError: module 'xbmcplugin' has no attribute 'SORT_METHOD_VIDEO_ORIGINAL_TITLE'
				'SORT_METHOD_VIDEO_ORIGINAL_TITLE_IGNORE_THE', # AttributeError: module 'xbmcplugin' has no attribute 'SORT_METHOD_VIDEO_ORIGINAL_TITLE_IGNORE_THE'

				#'SORT_METHOD_DATE', # Seems Kodi always adds a sort-by-date option to the start, and this just adds a duplicate entry for date. Also doesn't actually work. Does not sort by premiered/aired date, but some other date (maybe last accessed). Note the info label "date" probably has to be set for ListItems.
				'SORT_METHOD_DATEADDED', # SORT_METHOD_DATE is broken (just Google). SORT_METHOD_DATEADDED works, so use that instead. Note the info label "dateadded" has to be set for ListItems.
				'SORT_METHOD_YEAR', # AttributeError: module 'xbmcplugin' has no attribute 'SORT_METHOD_YEAR'
				'SORT_METHOD_VIDEO_YEAR',

				'SORT_METHOD_DURATION',
				'SORT_METHOD_VIDEO_RUNTIME',

				'SORT_METHOD_COUNTRY',
				'SORT_METHOD_GENRE',
				'SORT_METHOD_MPAA_RATING',

				'SORT_METHOD_VIDEO_RATING',
				'SORT_METHOD_VIDEO_USER_RATING',

				'SORT_METHOD_STUDIO',
				'SORT_METHOD_STUDIO_IGNORE_THE',

				'SORT_METHOD_LASTPLAYED',
				'SORT_METHOD_PLAYCOUNT',
			])
			if self.mMedia == tools.Media.Season:
				sorting.extend(['SORT_METHOD_SEASON'])
			elif self.mMedia == tools.Media.Episode:
				sorting.extend(['SORT_METHOD_EPISODE'])
		else:
			tools.System.pluginPropertySet(property = 'GaiaMenuMedia', value = 'general') # For Gaia Eminence.
		for sort in sorting:
			# Put in a try-catch, since otherwise execution fails if a certain enum was removed and can not be set anymore.
			try: xbmcplugin.addSortMethod(self.mHandle, tools.Tools.getVariable(xbmcplugin, sort))
			except: pass

		# For Gaia Eminence.
		tools.System.pluginPropertySet(property = 'GaiaIconBackLarge', value = Icon.path(icon = 'previous', type = Icon.TypeIcon, quality = Icon.QualityLarge))
		tools.System.pluginPropertySet(property = 'GaiaIconBackSmall', value = Icon.path(icon = 'previous', type = Icon.TypeIcon, quality = Icon.QualitySmall))
		tools.System.pluginPropertySet(property = 'GaiaIconBackMini', value = Icon.path(icon = 'previous', type = Icon.TypeIcon, quality = Icon.QualityMini))
		# NB: Use the global icon, otherwise when navigating back, the container is unloaded, making the back poster temporarily empty while the loader is shown.
		tools.System.windowPropertySet(property = 'GaiaIconBackLarge', value = Icon.path(icon = 'previous', type = Icon.TypeIcon, quality = Icon.QualityLarge))
		tools.System.windowPropertySet(property = 'GaiaIconBackSmall', value = Icon.path(icon = 'previous', type = Icon.TypeIcon, quality = Icon.QualitySmall))
		tools.System.windowPropertySet(property = 'GaiaIconBackMini', value = Icon.path(icon = 'previous', type = Icon.TypeIcon, quality = Icon.QualityMini))

		contented = self.mContent if content is None or self.mContent == Directory.ContentGeneral else content

		# Shows a category path in the title bar of certain skins (eg: Estuary).
		try:
			category = self.mCategory
			if not category:
				name = tools.System.name()
				category = []
				try: category.extend(tools.System.navigation())
				except: pass
				category = tools.Tools.listUnique(category)
				if contented:
					try: category.remove(name)
					except: pass
					if len(category) >= 3:
						for i in [32001, 32002]:
							try: category.remove(Translation.string(i))
							except: pass
					category = [category[-1]] if category else []
				else:
					category = [name, category[-1]] if category else [name]
				category = tools.Tools.listUnique(category)
				category = ' / '.join(category)
			xbmcplugin.setPluginCategory(self.mHandle, category)
		except: tools.Logger.error()

		# cacheToDisc does not seem to work anymore.
		# Every time we go back on a cached menu, Kodi calls addon.py again in a new Python invoker to repopulate the menu, without using the cached results.
		#	https://forum.kodi.tv/showthread.php?tid=351108
		# It seems that they iternally now have different values (0/False = No caching, 1/True = caching if slow, 2 = always cache)
		#	https://github.com/xbmc/xbmc/blob/master/xbmc/FileItemList.h
		# Also note that caching only applies to the window stack. Hence, only if we go back does it cache. Going foward by opening a menu that was previously opened will not use the cache.
		# Not sure if we always want to cache. For instance, if we open a episode menu, mark all episodes as watched, navigate back, the season still shows as unwatched (no checkmark). Only if we go back one step further, then reopening the seasons menu, does the new status show.
		# For now, only cache non-media menus.
		if cache is None: cache = self.mCache
		if cache is True: cache = 1 if contented in Directory.ContentMedia else 2

		update = self.mUpdate if update is None else update

		path = tools.System.infoLabel('Container.FolderPath', wait = False) # Must be called before xbmcplugin.endOfDirectory().

		xbmcplugin.setContent(self.mHandle, contented)
		try: xbmcplugin.endOfDirectory(self.mHandle, cacheToDisc = cache, updateListing = update)
		except: xbmcplugin.endOfDirectory(self.mHandle, cacheToDisc = bool(cache), updateListing = update) # For older Kodi versions where it might not allow passing in cacheToDisc as an integer.

		if loader: Loader.hide()

		# Do not do this for external addons or widgets.
		if tools.System.originGaia():
			if view is None: view = self.mView
			if view:
				from lib.modules.view import View
				View.set(media = view if not view is True else self.mMedia if self.mMedia else self.mContent, content = self.mContent, id = self.mId, path = path, select = select)

	# clear: Clear the path history. Can also be a path to reset to.
	# position: After refresh, go to the previously selected position, becuase Kodi always jumps back to the top after refresh. Not perfect, since the list can become unfocused, or the user moves the mosue over another item before this code is executed.
	@classmethod
	def refresh(self, id = None, clear = False, position = False, force = False, wait = True, loader = False):
		# Do no refresh if we are in an invoker that did a scrape.
		# Otherwise, when calling Container.Refresh, Kodi will execute the scrape command again.
		if not force and tools.System.commandIsScrape(): return

		if wait: self._refresh(id = id, clear = clear, position = position, loader = loader)
		else: Pool.thread(target = self._refresh, kwargs = {'id' : 'id', 'clear' : clear, 'position' : position, 'loader' : loader}, start = True)

	@classmethod
	def _refresh(self, id = None, clear = False, position = False, loader = False):
		container = 'Container'

		# The idea here is to refresh the container the command got called from, ibstead of the "current" container.
		# This allows the context menu to refresh the menu/list container inside widgets.
		# However, Container(id).Refresh is not implemented and does not actually reload the widget container.
		# Leave here, in case Kodi ever implements this, we could re-add it to work for "refreshMenu" and "refreshMetadata" int he context menu.
		# https://forum.kodi.tv/showthread.php?tid=335235
		# https://forum.kodi.tv/showthread.php?tid=348712
		#if id: container += '(%s)' % str(id)

		# wait: NB: it seems that Kodi never finishes when executing Container.Refresh and wait=True.
		index = -1
		if position:
			try: index = int(tools.System.infoLabel(container + '.CurrentItem'))
			except: pass

		tools.System.execute(container + '.Refresh', wait = False)
		if clear: tools.System.execute(container + '.Update(%s,replace)' % (clear if tools.Tools.isString(clear) else ''), wait = False)

		if position and index >= 0:
			try:
				# Refreshing takes some time. Wait until done.
				count = 0
				while count < 15:
					count += 1
					if not Loader.visible(): break
					tools.Time.sleep(0.2)
				# For some reason Kodi freezes when executing the below statements in a single line of code.
				# Kepp each statement separate.
				window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
				list = window.getFocus()
				list.selectItem(index)
			except: pass

		if loader: Loader.hide()

	# Creates a new list item.
	# lock:
	#	By default Kodi acquires a GUI lock everytime you call any function on the item (eg: setProperty, setArt, etc).
	#	This drastically increases the execution time every time the directory is changed, or when list items are displayed in other places (eg: stream window).
	#	Since Kodi 18, an "offscreen" parameter was added that reduces locking and is way faster.
	#	The parameter is not documented, but from forum discussions, it seems that one can set the parameter to True if the item is currently NOT being displayed in the GUI, that is adding the item to the directory aand later on calling functions on it.
	#	However, if the item is created, all functions called on it, and afterwards being added to the directory/GUI, the offscreen parameter can be set to True (lock = False) to speed up the process.
	#	If you plan on calling functions on the item after it was added, make sure to set the lock parameter to True.
	# 	https://forum.kodi.tv/showthread.php?tid=307394
	def item(self, label = None, label2 = None, path = None, icon = None, lock = None):
		try: item = xbmcgui.ListItem(label = label, label2 = label2, path = path, offscreen = not (self.mLock if lock is None else lock)) # Kodi 18+.
		except: item = xbmcgui.ListItem(label = label, label2 = label2, path = path) # Old Kodi versions.
		if icon:
			if not '/' in icon and not '\\' in icon: icon = Icon.pathIcon(icon)
			item.setArt({'icon': icon, 'thumb': icon})
		return item


class Player(xbmc.Player):

	EventNone = None
	EventAvChange = 1
	EventAvStarted = 2
	EventPlaybackEnded = 3
	EventPlaybackError = 4
	EventPlaybackPaused = 5
	EventPlaybackResumed = 6
	EventPlaybackSeek = 7
	EventPlaybackSeekChapter = 8
	EventPlaybackSpeedChanged = 9
	EventPlaybackStarted = 10
	EventPlaybackStopped = 11
	EventQueueNext = 12

	StatusStarted = 'started'
	StatusPlaying = 'playing'
	StatusPaused = 'paused'
	StatusStopped = 'stopped'
	StatusEnded = 'ended'
	StatusError = 'error'
	StatusUnknown = None
	StatusFinished = [StatusStopped, StatusEnded, StatusError]

	RetrieveAll = 0 # Get all available streams.
	RetrieveDefault = 1 # Get the stream that is marked as default.
	RetrieveCurrent = 2 # Get the stream that is currently selected in the player.

	PropertyCanceled = 'GaiaPlaybackCanceled'

	def __init__ (self):
		xbmc.Player.__init__(self)
		self.mId = None
		self.mCallbacks = {}
		self.mStatus = Player.StatusUnknown

	def __del__(self):
		try: xbmc.Player.__del__(self)
		except: pass

	##############################################################################
	# GENERAL
	##############################################################################

	def id(self, wait = True):
		if self.mId is None:
			# Sometimes a takes some time for the ID to become available.
			for i in range(10):
				try: self.mId = tools.System.executeJson(method = 'Player.GetActivePlayers')['result'][0]['playerid']
				except: pass
				if not wait or not self.mId is None: break
				tools.Time.sleep(0.1)
		return self.mId

	def property(self, property):
		try:
			single = not tools.Tools.isArray(property)
			if single: property = [property]
			result = tools.System.executeJson(method = 'Player.GetProperties', parameters = {'playerid' : self.id(), 'properties' : property})
			result = result['result']
			if single: result = result[property[0]]
			return result
		except:
			return None

	##############################################################################
	# CANCELED
	##############################################################################

	# The playback process (resolving and Kodi player's callbacks) can occur from different threads and processes.
	# Also notable when playing an STRM file from the local library.
	# Using a global python variable to indicate if the playback was cancled therefore does not always work.
	# Use a global Kodi variable instead.

	@classmethod
	def canceled(self):
		return bool(tools.System.windowPropertyGet(property = Player.PropertyCanceled))

	@classmethod
	def canceledSet(self):
		tools.System.windowPropertySet(property = Player.PropertyCanceled, value = True)

	@classmethod
	def canceledClear(self):
		tools.System.windowPropertyClear(property = Player.PropertyCanceled)

	##############################################################################
	# STATUS
	##############################################################################

	def status(self):
		return self.mStatus

	def statusFinished(self):
		return self.mStatus in Player.StatusFinished

	##############################################################################
	# PLAY
	##############################################################################

	@classmethod
	def playNow(self, link, item = None):
		Player().play(link, item)

	def play(self, link, item = None):
		self.mStatus = Player.StatusStarted
		return xbmc.Player.play(self, link, item)

	def isPlayback(self):
		# Kodi often starts playback where isPlaying() is true and isPlayingVideo() is false, since the video loading is still in progress, whereas the play is already started.
		try: return self.isPlaying() and self.isPlayingVideo() and self.getTime() >= 0
		except: False

	##############################################################################
	# STOP
	##############################################################################

	def stop(self, rpc = False):
		if rpc: return tools.System.executeJson(method = 'Player.Stop', parameters = {'playerid' : self.id()})
		else: return xbmc.Player.stop(self)

	##############################################################################
	# CALLBACK
	##############################################################################

	def callbacksClear(self, event = EventNone):
		try:
			if event == Player.EventNone: self.mCallbacks = {}
			else: del self.mCallbacks[event]
		except: pass

	def callback(self, event, function):
		if not event in self.mCallbacks: self.mCallbacks[event] = []
		self.mCallbacks[event].append(function)

	def _callback(self, event, *arguments):
		try:
			for callback in self.mCallbacks[event]:
				try: callback(*arguments)
				except: callback()
		except: pass

	def onAVChange(self):
		self._callback(Player.EventAvChange)

	def onAVStarted(self):
		self._callback(Player.EventAvStarted)

	def onPlayBackEnded(self):
		self.mStatus = Player.StatusEnded
		self._callback(Player.EventPlaybackEnded)

	def onPlayBackError(self):
		self.mStatus = Player.StatusError
		self._callback(Player.EventPlaybackError)

	def onPlayBackPaused(self):
		self.mStatus = Player.StatusPaused
		self._callback(Player.EventPlaybackPaused)

	def onPlayBackResumed(self):
		self.mStatus = Player.StatusPlaying
		self._callback(Player.EventPlaybackResumed)

	def onPlayBackSeek(self, time, seekOffset):
		self._callback(Player.EventPlaybackSeek, time, seekOffset)

	def onPlayBackSeekChapter(self, chapter):
		self._callback(Player.EventPlaybackSeekChapter, chapter)

	def onPlayBackSpeedChanged(self, speed):
		self._callback(Player.EventPlaybackSpeedChanged, speed)

	def onPlayBackStarted(self):
		self.mStatus = Player.StatusPlaying
		self._callback(Player.EventPlaybackStarted)

	def onPlayBackStopped(self):
		self.mStatus = Player.StatusStopped
		self._callback(Player.EventPlaybackStopped)

	def onQueueNextItem(self):
		self._callback(Player.EventQueueNext)

	##############################################################################
	# AUDIO
	##############################################################################

	# Kodi's Python module has primitive functions. Some info is limited (eg: not able to get stream name), other info is not avialable at all (eg: current audio stream).
	# Use the JSON RPC instead.

	def _audioStream(self, data, process = False, unknown = None):
		if not data: return None
		elif tools.Tools.isArray(data): return [self._audioStream(data = i, process = process, unknown = unknown) for i in data]

		if process:
			language = tools.Language.language(data['language'], variation = True)
			if not language and unknown: language = tools.Language.language(unknown, variation = True) if tools.Tools.isString(unknown) else unknown
			if not tools.Tools.isDictionary(language): language = tools.Language.universal()
		else:
			language = data['language']
			if not language and unknown: language = unknown if tools.Tools.isString(unknown) else unknown[tools.Language.Code][tools.Language.CodeStream]

		return {
			'id' : data['index'],
			'name' : data['name'],
			'language' : language,
			'default' : data['isdefault'],
			'channels' : data['channels'],
			'bitrate' : data['bitrate'],
			'codec' : data['codec'],
		}

	def audioStream(self, retrieve = RetrieveAll, process = False, unknown = None):
		if retrieve == Player.RetrieveCurrent:
			return self._audioStream(data = self.property(property = 'currentaudiostream'), process = process, unknown = unknown)
		else:
			result = self._audioStream(data = self.property(property = 'audiostreams'), process = process, unknown = unknown)
			if not result: return None
			if retrieve == Player.RetrieveDefault:
				for i in result:
					if i['default']: return i
				return result[0]
			return result

	def audioSelect(self, id):
		if tools.Tools.isDictionary(id): id = id['id']

		try: current = self.audioStream(retrieve = Player.RetrieveCurrent)['id']
		except: current = None

		# Sometimes the playback restarts if changing the audio stream.
		# Only change the audio stream if it is not currently selected one.
		if not id == current: self.setAudioStream(id)

	##############################################################################
	# SUBTITLE
	##############################################################################

	def _subtitleStream(self, data, process = False, unknown = None):
		if not data: return None
		elif tools.Tools.isArray(data): return [self._subtitleStream(data = i, process = process, unknown = unknown) for i in data]

		if process:
			language = tools.Language.language(data['language'], variation = True)
			if not language and unknown: language = tools.Language.language(unknown, variation = True) if tools.Tools.isString(unknown) else unknown
			if not tools.Tools.isDictionary(language): language = tools.Language.universal()
		else:
			language = data['language']
			if not language and unknown: language = unknown if tools.Tools.isString(unknown) else unknown[tools.Language.Code][tools.Language.CodeStream]

		return {
			'id' : data['index'],
			'name' : data['name'],
			'language' : language,
			'default' : data['isdefault'],
			'impaired' : data['isimpaired'],
			'forced' : data['isforced'],
		}

	def subtitleStream(self, retrieve = RetrieveAll, process = False, unknown = None):
		if retrieve == Player.RetrieveCurrent:
			return self._subtitleStream(data = self.property(property = 'currentsubtitle'), process = process, unknown = unknown)
		else:
			result = self._subtitleStream(data = self.property(property = 'subtitles'), process = process, unknown = unknown)
			if not result: return None
			if retrieve == Player.RetrieveDefault:
				for i in result:
					if i['default']: return i
				return result[0]
			return result

	def subtitleEnable(self, enable = True):
		if not enable is None: self.showSubtitles(enable)

	def subtitleDisable(self, disable = True):
		self.subtitleEnable(enable = (not disable))

	def subtitleEnabled(self):
		return self.property(property = 'subtitleenabled')

	def subtitleDisabled(self):
		return not self.subtitleEnabled()

	def subtitleSelect(self, id = None, path = None, enable = True):
		if not enable: enable = self.subtitleEnabled() # Reset the state afterwards, since setSubtitles() automatically enables.
		if id is None:
			self.setSubtitles(path)
		else:
			if tools.Tools.isDictionary(id): id = id['id']
			self.setSubtitleStream(id)
		self.subtitleEnable(enable = enable)


class Context(object):

	ModeNone = None
	ModeGeneric = 'generic'
	ModeItem = 'item'
	ModeStream = 'stream'
	ModeVideo = 'video'

	PrefixNext = None
	PrefixBack = None

	Labels = {}
	LabelMenu = None
	LabelBack = None
	LabelClose = None

	EnabledSkin = None
	EnabledTrakt = None
	EnabledOrion = None
	EnabledYoutube = None
	EnabledLibrary = None
	EnabledPresets = None
	EnabledAutoplay = None
	EnabledBinge = None
	EnabledVideoContext = None
	EnabledVideoTrailer = None
	EnabledVideoRecap = None
	EnabledVideoReview = None
	EnabledVideoReaction = None
	EnabledVideoBonus = None
	EnabledVideoDeleted = None
	EnabledVideoProduction = None
	EnabledVideoDirection = None
	EnabledVideoInterview = None
	EnabledVideoExplanation = None
	EnabledVideoAlternation = None
	EnabledDownloadCloud = None
	EnabledDownloadManual = None
	EnabledDownloadCache = None
	EnabledManagerManual = None
	EnabledManagerCache = None
	EnabledVpnManager = None
	EnabledBluetooth = None
	EnabledOracle = None

	SettingsInformer = False
	SettingsEnabled = False
	SettingsEnabledGaia = False
	SettingsEnabledAddon = False
	SettingsEnabledWidget = False
	SettingsEnabledPlaylist = False
	SettingsLayout = False
	SettingsLayoutPrefix = False
	SettingsLayoutBold = False
	SettingsLayoutColor = False

	# Must correspond with addon.xml.
	PropertyContextBusy = 'GaiaContextBusy'
	PropertyContextLabel = 'GaiaContextLabel'
	PropertyContextEnabled = 'GaiaContextEnabled'
	PropertyContextAddon = 'GaiaContextAddon'
	PropertyContextWidget = 'GaiaContextWidget'
	PropertyContextPlaylist = 'GaiaContextPlaylist'

	Id = 'Context'
	Window = 10106
	Query = None

	def __init__(self,
		mode = ModeNone,
		items = None,

		media = None,
		niche = None,

		imdb = None,
		tmdb = None,
		tvdb = None,
		trakt = None,
		slug = None,
		season = None,
		episode = None,
		title = None,
		year = None,
		set = None,
		plays = None,
		rating = None,
		progress = None,

		query = None,
		link = None,
		provider = None,
		library = None,
		playlist = None,
		mixed = None,

		video = None,
		source = None,
		metadata = None,
		orion = None,
		shortcut = None,

		loader = False
	):
		if loader: Loader.show()
		if not mode == self.ModeNone: self._load(mode = mode, items = items, media = media, niche = niche, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, slug = slug, season = season, episode = episode, title = title, year = year, set = set, plays = plays, rating = rating, progress = progress, query = query, link = link, provider = provider, library = library, playlist = playlist, mixed = mixed, video = video, source = source, metadata = metadata, orion = orion, shortcut = shortcut)

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		Context.Query = None
		if settings:
			Context.LabelMenu = None
			from lib.modules.cache import Memory
			Memory.clear(id = Context.Id, local = True, kodi = True)

	##############################################################################
	# GENERAL
	##############################################################################

	def _load(self, mode = ModeNone, items = None, media = None, niche = None, imdb = None, tmdb = None, tvdb = None, trakt = None, slug = None, season = None, episode = None, title = None, year = None, set = None, plays = None, rating = None, progress = None, query = None, link = None, provider = None, library = None, playlist = None, mixed = None, video = None, source = None, metadata = None, orion = None, shortcut = None):
		try:
			from lib.modules.shortcut import Shortcut
			from lib.meta.tools import MetaTools

			self.mData = None

			self.mMode = mode
			self.mItems = items if items else []

			self.mMedia = media
			self.mNiche = niche
			self.mVideo = video

			# Get the command/query that initiated the creation of the context.
			# Is useful if we want to do something with the original command, like refreshing the metadata.
			# Using "Container.FolderPath" does the job from within Gaia, but does not work from widgets.
			# This is not the command of the item the context is opened on, which is self.mLink, but rather the command of the parent container the item is in.
			if query is None and Context.Query is None: Context.Query = tools.System.query(parse = True)
			self.mQuery = query or Context.Query

			self.mLink = link
			self.mProvider = provider
			self.mLibrary = link if library is True else library
			self.mPlaylist = playlist
			self.mMixed = mixed

			#gaiaremove - in a future version we have to get rid of self.mSource.
			#gaiaremove - it is too large and slows down stream window loading, since each item in the window has to JSON+URL/BASE64 encode a large source object, just for the context menu.
			#gaiaremove - add some cache with a source ID. Only pass the source ID to the context, and when the source is actually needed when an action is executed in the context, use the ID to lookup the actual data.
			self.mSource = source
			self.mOrion = orion

			self.mShortcut = shortcut
			self.mShortcutId = None
			self.mShortcutLabel = None
			self.mShortcutCommand = None
			self.mShortcutFolder = None
			self.mShortcutCreate = None
			self.mShortcutDelete = None
			if shortcut:
				self.mShortcutId = shortcut.get(Shortcut.ParameterId)
				self.mShortcutLabel = shortcut.get(Shortcut.ParameterLabel)
				self.mShortcutCommand = shortcut.get(Shortcut.ParameterCommand)
				self.mShortcutFolder = shortcut.get(Shortcut.ParameterFolder)
				self.mShortcutCreate = shortcut.get(Shortcut.ParameterCreate)
				self.mShortcutDelete = shortcut.get(Shortcut.ParameterDelete)
			if not self.mShortcutCommand: self.mShortcutCommand = self.mLink

			self.mName = None
			self.mHash = None
			if source:
				stream = source['stream']
				if stream:
					self.mName = stream.fileName()
					self.mHash = stream.hash()

			self.mTitle = title
			self.mYear = year
			self.mSeason = season
			self.mEpisode = episode
			self.mImdb = imdb
			self.mTmdb = tmdb
			self.mTvdb = tvdb
			self.mTrakt = trakt
			self.mSlug = slug

			self.mSet = set
			self.mPlays = plays
			self.mRating = rating
			self.mProgress = progress

			# Do not store the metadata object for the context menu, since most of the attributes are not used anyways.
			# This just drastically increases menu loading times, since the metadata has to be encoded/decoded with JSON and URL/Base64.
			# Especially for menus with tons of episodes, and stream windows with 100s of streams, this has to be done for every item, which adds up quickly.
			if metadata:
				if not self.mMedia:
					try: self.mMedia = metadata['media']
					except: pass
				if not self.mNiche:
					try: self.mNiche = metadata['niche']
					except: pass

				if 'query' in metadata:
					self.mTitle = metadata['query'] # Season Extras.
				else:
					for i in ['tvshowtitle', 'originaltitle', 'title', 'name', 'label']:
						if i in metadata and metadata[i]:
							self.mTitle = metadata[i]
							break

				try: self.mYear = metadata.get('tvshowyear') or metadata.get('year')
				except: pass

				try: self.mSeason = metadata['season']
				except: pass
				try: self.mEpisode = metadata['episode']
				except: pass

				try: self.mImdb = metadata['imdb']
				except: pass
				try: self.mTmdb = metadata['tmdb']
				except: pass
				try: self.mTvdb = metadata['tvdb']
				except: pass
				try: self.mTrakt = metadata['trakt']
				except: pass
				try: self.mSlug = metadata['slug']
				except: pass

				try: self.mSet = metadata['collection']['id']
				except: pass

				try: self.mPlays = metadata['playcount']
				except: pass
				if not self.mPlays: # Partially watched shows/seasons.
					try: self.mPlays = metadata['count']['episode']['watched']
					except: pass

				try: self.mRating = metadata['userrating']
				except: pass

				try: self.mProgress = metadata['progress']
				except: pass

				# "Series" menu under the season directory.
				if self.mMedia == tools.Media.Season and self.mSeason is None: self.mMedia = tools.Media.Show

				if self.mShortcut and self.mShortcutLabel is None:
					if self.mMedia == tools.Media.Person:
						self.mShortcutLabel = self.mTitle
					elif tools.Media.isSerie(self.mMedia):
						self.mShortcutLabel = tools.Title.title(media = tools.Media.Show, title = self.mTitle, year = self.mYear)
						if (self.mMedia == tools.Media.Season or self.mMedia == tools.Media.Episode) and not self.mSeason is None: # Check the season for the Series menu.
							self.mShortcutLabel += ' - ' + tools.Title.title(media = self.mMedia, season = self.mSeason, episode = self.mEpisode, special = True)
					else:
						self.mShortcutLabel = tools.Title.title(media = self.mMedia, title = self.mTitle, year = self.mYear)
					self.mShortcut[Shortcut.ParameterLabel] = self.mShortcutLabel

			self.initialize()
			if len(self.mItems) == 0:
				if self.mMode == Context.ModeGeneric: self.addGeneric()
				elif self.mMode == Context.ModeItem: self.addItem()
				elif self.mMode == Context.ModeStream: self.addStream()
				elif self.mMode == Context.ModeVideo: self.addVideo()
		except:
			tools.Logger.error()

	@classmethod
	def initialize(self, force = False, wait = True):
		if wait: self._initialize(force = force)
		else: Pool.thread(target = self._initialize, kwargs = {'force' : force}, start = True)

	@classmethod
	def _initialize(self, force = False):
		if Context.LabelMenu is None or force:
			from lib.modules.cache import Memory

			thread = Pool.thread(target = self._initializeRefresh, start = True)
			data = Memory.get(id = Context.Id, local = True, kodi = True)
			if not data or force:
				thread.join()
				data = Memory.get(id = Context.Id, local = True, kodi = True)

			Context.LabelMenu = data['label']['menu']
			Context.LabelBack = data['label']['back']
			Context.LabelClose = data['label']['close']

			Context.EnabledSkin = data['enabled']['skin']
			Context.EnabledOrion = data['enabled']['orion']
			Context.EnabledTrakt = data['enabled']['trakt']
			Context.EnabledYoutube = data['enabled']['youtube']
			Context.EnabledLibrary = data['enabled']['library']
			Context.EnabledPresets = data['enabled']['presets']
			Context.EnabledAutoplay = data['enabled']['autoplay']
			Context.EnabledBinge = data['enabled']['binge']

			Context.EnabledVideoContext = data['enabled']['video']['context']
			Context.EnabledVideoTrailer = data['enabled']['video']['trailer']
			Context.EnabledVideoRecap = data['enabled']['video']['recap']
			Context.EnabledVideoReview = data['enabled']['video']['review']
			Context.EnabledVideoReaction = data['enabled']['video']['reaction']
			Context.EnabledVideoBonus = data['enabled']['video']['bonus']
			Context.EnabledVideoDeleted = data['enabled']['video']['deleted']
			Context.EnabledVideoProduction = data['enabled']['video']['production']
			Context.EnabledVideoDirection = data['enabled']['video']['direction']
			Context.EnabledVideoInterview = data['enabled']['video']['interview']
			Context.EnabledVideoExplanation = data['enabled']['video']['explanation']
			Context.EnabledVideoAlternation = data['enabled']['video']['alternation']

			Context.EnabledDownloadCloud = data['enabled']['download']['cloud']
			Context.EnabledDownloadManual = data['enabled']['download']['manual']
			Context.EnabledDownloadCache = data['enabled']['download']['cache']
			Context.EnabledManagerManual = data['enabled']['download']['manager']['manual']
			Context.EnabledManagerCache = data['enabled']['download']['manager']['cache']

			Context.EnabledVpnManager = data['enabled']['vpn']['manager']
			Context.EnabledBluetooth = data['enabled']['bluetooth']
			Context.EnabledOracle = data['enabled']['oracle']

			Context.SettingsInformer = data['settings']['informer']
			Context.SettingsEnabled = data['settings']['enabled']['global']
			Context.SettingsEnabledGaia = data['settings']['enabled']['gaia']
			Context.SettingsEnabledAddon = data['settings']['enabled']['addon']
			Context.SettingsEnabledWidget = data['settings']['enabled']['widget']
			Context.SettingsEnabledPlaylist = data['settings']['enabled']['playlist']
			Context.SettingsLayout = data['settings']['layout']['global']
			Context.SettingsLayoutPrefix = data['settings']['layout']['prefix']
			Context.SettingsLayoutBold = data['settings']['layout']['bold']
			Context.SettingsLayoutColor = data['settings']['layout']['color']

	@classmethod
	def _initializeRefresh(self):
		from lib.modules.cache import Memory
		from lib.debrid import Debrid
		from lib.providers.core.manager import Manager
		from lib.modules.window import Window
		from lib.informers import Informer
		from lib.modules.library import Library
		from lib.modules.bluetooth import Bluetooth
		from lib.modules import trakt as Trakt
		from lib.modules import video
		from lib.oracle import Oracle

		label = self._labelIcon(tools.System.name(), icon = Font.IconGaia, color = True)

		enabledGlobal = tools.Settings.getBoolean('interface.context.enabled')
		enabledGaia = tools.Settings.getBoolean('interface.context.enabled.gaia')
		enabledAddon = tools.Settings.getBoolean('interface.context.enabled.addon')
		enabledWidget = tools.Settings.getBoolean('interface.context.enabled.widget')
		enabledPlaylist = tools.Settings.getBoolean('interface.context.enabled.playlist')

		enabledDownloadManual = tools.Settings.getBoolean('download.manual.enabled')
		enabledDownloadCache = tools.Settings.getBoolean('download.cache.enabled')

		try:
			from lib.modules import orionoid
			orion = orionoid.Orionoid().accountEnabled()
		except:
			orion = False

		data = {
			'enabled' : {
				'skin' : Skin.isEminenceGaia(),
				'orion' : orion,
				'trakt' : Trakt.authenticated(),
				'youtube' : tools.YouTube.installed(),
				'library' : Library.enabled(),
				'presets' : Manager.presetsEnabled(),
				'autoplay' : tools.Settings.getBoolean('playback.autoplay.enabled'),
				'binge' : tools.Binge.enabled(),

				'video' : {
					'context' : video.Video.settingContext(),
					'trailer' : video.Trailer.enabled(),
					'recap' : video.Recap.enabled(),
					'review' : video.Review.enabled(),
					'reaction' : video.Reaction.enabled(),
					'bonus' : video.Bonus.enabled(),
					'deleted' : video.Deleted.enabled(),
					'production' : video.Production.enabled(),
					'direction' : video.Direction.enabled(),
					'interview' : video.Interview.enabled(),
					'explanation' : video.Explanation.enabled(),
					'alternation' : video.Alternation.enabled(),
				},

				'download' : {
					'cloud' : Debrid.enabled(),
					'manual' : enabledDownloadManual,
					'cache' : enabledDownloadCache,
					'manager' : {
						'manual' : enabledDownloadManual,
						'cache' : enabledDownloadCache,
					},
				},

				'vpn' : {
					'manager' : tools.VpnManager.installed(),
				},

				'bluetooth' : Bluetooth.supported(),
				'oracle' : Oracle.instance().settingsEnabled(),
			},

			'label' : {
				'menu' : label,
				'back' : self._labelBack(),
				'close' : self._labelClose(),
			},

			'settings' : {
				'informer' : Informer.informerKodi(),

				'enabled' : {
					'global' : enabledGlobal,
					'gaia' : enabledGaia,
					'addon' : enabledAddon,
					'widget' : enabledWidget,
					'playlist' : enabledPlaylist,
				},

				'layout' : {
					'global' : tools.Settings.getBoolean('interface.context.layout'),
					'prefix' : tools.Settings.getBoolean('interface.context.layout.prefix'),
					'bold' : tools.Settings.getBoolean('interface.context.layout.bold'),
					'color' : tools.Settings.getBoolean('interface.context.layout.color'),
				},
			}
		}

		# Set a single dictionary instead of each value as a separate variable, since this is considerably faster.
		Memory.set(id = Context.Id, value = data, local = True, kodi = True)

		# Set these as well, since they are used in addon.xml.
		Window.propertyGlobalSet(Context.PropertyContextLabel, label)
		Window.propertyGlobalSet(Context.PropertyContextEnabled, enabledGlobal)
		Window.propertyGlobalSet(Context.PropertyContextAddon, enabledAddon)
		Window.propertyGlobalSet(Context.PropertyContextWidget, enabledWidget)
		Window.propertyGlobalSet(Context.PropertyContextPlaylist, enabledPlaylist)

	@classmethod
	def _translate(self, label, replace = None):
		if tools.Tools.isString(label):
			result = label
		else:
			if not label in Context.Labels: Context.Labels[label] = Translation.string(label)
			result = Context.Labels[label]
		if not replace is None: result = result % self._translate(replace)
		return result

	@classmethod
	def _label(self, label, color, next = False, icon = None):
		if color is True: color = Format.colorPrimary() if not Context.SettingsLayout or Context.SettingsLayoutColor else None
		elif color is False: color = None
		bold = not Context.SettingsLayout or Context.SettingsLayoutBold
		prefix = ''
		if not Context.SettingsLayout or Context.SettingsLayoutPrefix:
			if icon:
				prefix = Format.font(Font.icon(icon), color = Format.colorPrimary(), bold = bold and not Context.EnabledSkin, translate = False) + '  '
			elif next:
				if Context.PrefixNext is None: Context.PrefixNext = Format.font(Dialog.PrefixNext, color = Format.colorPrimary(), bold = bold, translate = False)
				prefix = Context.PrefixNext
			else:
				if Context.PrefixBack is None: Context.PrefixBack = Format.font(Dialog.PrefixBack, color = Format.colorPrimary(), bold = bold, translate = False)
				prefix = Context.PrefixBack
		return prefix + Format.font(label, bold = bold, color = color)

	@classmethod
	def _labelNext(self, label):
		return self._label(label = label, next = True, color = False)

	@classmethod
	def _labelBack(self):
		return self._label(label = 35374, icon = Font.IconBack, color = True)

	@classmethod
	def _labelClose(self):
		return self._label(label = 33486, icon = Font.IconClose, color = True)

	@classmethod
	def _labelIcon(self, label, icon, color = False):
		return self._label(label = label, icon = icon, color = color)

	def _labelItem(self, stream = True):
		label = tools.Title.title(media = self.mMedia, title = self.mTitle, year = self.mYear, season = self.mSeason, episode = self.mEpisode)
		if stream and self.mMode == Context.ModeStream: label = '[%s] %s' % (Translation.string(33071), label)
		return label

	@classmethod
	def _close(self):
		from lib.modules import window
		window.WindowStreams.close()

	@classmethod
	def _container(self):
		# The idea is to get the current container the list/menu was loaded in, so we can refresh/reload that container.
		# This is useful if the container is not an internal Gaia menu, but loaded externally through a widget.
		# So if the context menu is opened on a widget and we call the metadata refresh command, the widget should be refreshed, not whatever the "current" container is.
		# However, calling Container(id).Refresh with an ID does not work (yet). Check Directory.refresh() for more info.
		# Do not wait for System.originContainer(), since it sometimes does not return a value, and just prolongs the context execution time.
		# This happens especially when using a mouse to navigate the widget, instead of a keyboard/remote.
		# The mouse probably moves the focus elsewhere and Kodi gets confused about the container.
		# Since this value cannot be used at the moment, it does not make sense to wait very long for the ID to return.
		return tools.System.originContainer(wait = False)

	def _command(self, parameters = {}, full = True):
		if full:
			if not self.mMedia is None and not 'media' in parameters: parameters['media'] = self.mMedia
			if not self.mNiche is None and not 'niche' in parameters: parameters['niche'] = self.mNiche

			if 'niche' in parameters:
				niche = parameters['niche']
				if niche: parameters['niche'] = tools.Media.stringTo(niche)
				else: del parameters['niche']

		return dict((key, value) for key, value in parameters.items() if not value is None)

	def _commandPlugin(self, action = None, parameters = {}, command = None, id = None, full = True):
		return tools.System.commandPlugin(action = action, parameters = self._command(parameters, full = full), command = command)

	def _commandMenu(self, action = None, parameters = {}, command = None, id = None, replace = False, parent = None, full = True):
		# Calling Container.Update() externally, especially from widgets, might not work.
		# If we for instance execute the "Browse" context menu option on a widget, there is not video addon or any other menu opened, and therefore the container cannot be updated.
		# We have to first launch the addon and then update the container.
		# This can be done in one go using ActivateWindow(...).
		if tools.System.originMenu(): return self._commandContainer(action = action, parameters = parameters, command = command, id = id, replace = replace, full = full)
		else: return self._commandWindow(action = action, parameters = parameters, command = command, id = id, parent = parent, full = full)

	# Rather use _commandMenu().
	def _commandContainer(self, action = None, parameters = {}, command = None, id = None, replace = False, full = True):
		return tools.System.commandContainer(action = action, parameters = self._command(parameters, full = full), command = command, replace = replace)

	# Rather use _commandMenu().
	def _commandWindow(self, action = None, parameters = {}, command = None, id = None, parent = None, full = True):
		return tools.System.commandWindow(action = action, parameters = self._command(parameters, full = full), command = command, parent = parent)

	def dataTo(self, force = False):
		# NB: Do not create full commands for each action in the context menu.
		# NB: If multiple actions contain the source/metadata attribute, the context menu JSON can become very large and can take very long to generate.
		# NB: Instead, create a barebone context menu and append all parameters ONCE. The plugin commands are then dynamically created ONLY if they are called.
		if force or self.mData is None:
			self.mData = {
				'mode' : self.mMode,
				'items' : self.mItems,

				'media' : self.mMedia,
				'niche' : self.mNiche,

				'title' : self.mTitle,
				'year' : self.mYear,
				'season' : self.mSeason,
				'episode' : self.mEpisode,
				'imdb' : self.mImdb,
				'tmdb' : self.mTmdb,
				'tvdb' : self.mTvdb,
				'trakt' : self.mTrakt,
				'slug' : self.mSlug,

				'set' : self.mSet,
				'plays' : self.mPlays,
				'rating' : self.mRating,
				'progress' : self.mProgress,

				'query' : self.mQuery,
				'link' : self.mLink,
				'provider' : self.mProvider,
				'library' : self.mLibrary,
				'playlist' : self.mPlaylist,
				'mixed' : self.mMixed,

				'video' : self.mVideo,
				'source' : self.mSource,
				'orion' : self.mOrion,
				'shortcut' : self.mShortcut,
			}
			self.mData = self._command(self.mData)
		return self.mData

	def dataFrom(self, data):
		if tools.Tools.isString(data): data = tools.Converter.jsonFrom(data)
		self._load(**data)

	@classmethod
	def enabled(self, gaia = True):
		self.initialize()
		result = Context.SettingsEnabled
		if gaia: result = result and Context.SettingsEnabledGaia
		return result

	@classmethod
	def create(self):
		# This function is called from the context menu of external Kodi widgets (context.py).

		import sys
		from lib.modules.network import Networker

		def extract(value, default, parameters, metadata):
			result = default
			if not result:
				try: result = parameters[value]
				except: pass
			if not result:
				try: result = metadata[value]
				except: pass
			return None if tools.Tools.isInteger(result) and result < 0 else result

		Loader.show()

		item = sys.listitem
		info = item.getVideoInfoTag()
		type = info.getMediaType()

		path = item.getPath()
		parameters = Networker.linkDecode(path)

		metadata = parameters.get('metadata')
		if not metadata is None: metadata = tools.Converter.dictionary(metadata)

		media = parameters.get('media') or type
		niche = parameters.get('niche')

		code = item.getProperty('code')
		imdb = info.getIMDBNumber()
		if not imdb and code and code.startswith('tt'): imdb = code
		imdb = extract('imdb', imdb, parameters, metadata)

		tmdb = extract('tmdb', None, parameters, metadata)
		tvdb = extract('tvdb', None, parameters, metadata)
		trakt = extract('trakt', None, parameters, metadata)
		title = extract('title', info.getTitle(), parameters, metadata)
		tvshowtitle = extract('tvshowtitle', info.getTVShowTitle(), parameters, metadata)
		year = extract('year', info.getYear(), parameters, metadata)
		tvshowyear = extract('tvshowyear', info.getYear(), parameters, metadata)
		season = extract('season', info.getSeason(), parameters, metadata)
		episode = extract('episode', info.getEpisode(), parameters, metadata)

		from lib.meta.meny import MetaMenu
		context = MetaMenu(media = media, niche = niche).buildContext(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = tvshowtitle or title, year = tvshowyear or year, season = season, episode = episode)

		context.show()
		Loader.hide()

	def menu(self, full = False):
		result = (Context.LabelMenu, self._commandPlugin(action = 'contextShow', parameters = {'context' : self.dataTo()}))
		if full: result = [result]
		return result

	def commandInformation(self):
		return self._commandPlugin(action = 'informerDialog', parameters = {'media' : self.mMedia, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'title' : self.mTitle, 'year' : self.mYear, 'season' : self.mSeason, 'episode' : self.mEpisode})

	def commandInformationStream(self):
		return self._commandPlugin(action = 'streamsInformation', parameters = {'media' : self.mMedia, 'source' : self.mSource})

	def commandInformationPerson(self):
		return self._commandPlugin(action = 'informerDialog', parameters = {'media' : tools.Media.Person, 'title' : self.mTitle})

	def commandInformationMovie(self):
		return self._commandPlugin(action = 'informerDialog', parameters = {'media' : tools.Media.Movie, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'title' : self.mTitle, 'year' : self.mYear})

	def commandInformationSet(self):
		trakt = None
		tmdb = None
		if self.mSet:
			if tools.Tools.isDictionary(self.mSet):
				trakt = self.mSet.get('trakt')
				tmdb = self.mSet.get('tmdb')
			elif tools.Tools.isString(self.mSet) or tools.Tools.isInteger(self.mSet): # Deprecated. Previously the TMDb ID was stored directly under the metadata['collection']['id'] attribute. Now the IDs are stored as a dictionary.
				tmdb = self.mSet
		elif tools.Media.isSet(self.mMedia):
			trakt = self.mTrakt
			tmdb = self.mTmdb
		if trakt or tmdb: return self._commandPlugin(action = 'informerDialog', parameters = {'media' : tools.Media.Set, 'trakt' : trakt, 'tmdb' : tmdb})

	def commandInformationShow(self):
		return self._commandPlugin(action = 'informerDialog', parameters = {'media' : tools.Media.Show, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'title' : self.mTitle, 'year' : self.mYear})

	def commandInformationSeason(self):
		return self._commandPlugin(action = 'informerDialog', parameters = {'media' : tools.Media.Season, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'title' : self.mTitle, 'year' : self.mYear, 'season' : self.mSeason})

	def commandInformationEpisode(self):
		return self._commandPlugin(action = 'informerDialog', parameters = {'media' : tools.Media.Episode, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'title' : self.mTitle, 'year' : self.mYear, 'season' : self.mSeason, 'episode' : self.mEpisode})

	def commandFilters(self):
		return self._commandPlugin(action = 'streamsFilters')

	def commandActivityWatch(self):
		return self._commandPlugin(action = 'playbackWatch', parameters = {'media' : self.mMedia, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'episode' : self.mEpisode})

	def commandActivityUnwatch(self):
		return self._commandPlugin(action = 'playbackUnwatch', parameters = {'media' : self.mMedia, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'episode' : self.mEpisode})

	def commandActivityRate(self):
		return self._commandPlugin(action = 'playbackRate', parameters = {'media' : self.mMedia, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'episode' : self.mEpisode})

	def commandActivityUnrate(self):
		return self._commandPlugin(action = 'playbackUnrate', parameters = {'media' : self.mMedia, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'episode' : self.mEpisode})

	def commandActivityRefresh(self):
		return self._commandPlugin(action = 'playbackRefresh', parameters = {'media' : self.mMedia})

	def commandActivityReset(self):
		return self._commandPlugin(action = 'playbackReset', parameters = {'media' : self.mMedia, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'episode' : self.mEpisode})

	def commandActivityTrakt(self):
		return self._commandPlugin(action = 'traktManager', parameters = {'media' : self.mMedia, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'episode' : self.mEpisode})

	def commandScrapeAgain(self):
		return self._commandPlugin(action = 'scrapeAgain', parameters = {'link' : self.mLink})

	def commandScrapeManual(self):
		return self._commandPlugin(action = 'scrapeManual', parameters = {'link' : self.mLink})

	def commandScrapeAutomatic(self):
		return self._commandPlugin(action = 'scrapeAutomatic', parameters = {'link' : self.mLink})

	def commandScrapePresetManual(self):
		return self._commandPlugin(action = 'scrapePresetManual', parameters = {'link' : self.mLink})

	def commandScrapePresetAutomatic(self):
		return self._commandPlugin(action = 'scrapePresetAutomatic', parameters = {'link' : self.mLink})

	def commandScrapeSingle(self):
		return self._commandPlugin(action = 'scrapeSingle', parameters = {'link' : self.mLink})

	def commandScrapeBinge(self):
		return self._commandPlugin(action = 'scrapeBinge', parameters = {'link' : self.mLink})

	def commandBinge(self):
		return self._commandPlugin(action = 'binge', parameters = {'media' : self.mMedia, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'episode' : self.mEpisode})

	def commandPlaylistShow(self):
		return self._commandPlugin(action = 'playlistShow')

	def commandPlaylistClear(self):
		return self._commandPlugin(action = 'playlistClear')

	def commandPlaylistAdd(self):
		return self._commandPlugin(action = 'playlistAdd', parameters = {'media' : self.mMedia, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'episode' : self.mEpisode, 'link' : self.mLink, 'label' : self._labelItem(), 'context' : self.dataTo()})

	def commandPlaylistRemove(self):
		return self._commandPlugin(action = 'playlistRemove', parameters = {'label' : self._labelItem()})

	def commandVideo(self, video = None):
		return self._commandPlugin(action = 'streamsVideo', parameters = {'video' : video, 'media' : self.mMedia, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'title' : self.mTitle, 'year' : self.mYear})

	def commandVideoDirect(self, video = None):
		from lib.modules.video import Video
		return self._commandPlugin(action = 'streamsVideo', parameters = {'video' : video or self.mVideo, 'selection' : Video.ModeDirect, 'media' : self.mMedia, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'title' : self.mTitle, 'year' : self.mYear})

	def commandVideoManual(self, video = None):
		from lib.modules.video import Video
		return self._commandPlugin(action = 'streamsVideo', parameters = {'video' : video or self.mVideo, 'selection' : Video.ModeManual, 'media' : self.mMedia, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'title' : self.mTitle, 'year' : self.mYear})

	def commandVideoAutomatic(self, video = None):
		from lib.modules.video import Video
		return self._commandPlugin(action = 'streamsVideo', parameters = {'video' : video or self.mVideo, 'selection' : Video.ModeAutomatic, 'media' : self.mMedia, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'title' : self.mTitle, 'year' : self.mYear})

	def commandBrowse(self, season = False):
		# Important for "parameters=False" to avoid pulling int he parameters of the current menu.
		# Eg: If executed from a progress submenu, do not add the eg episode number from the submenu.
		from lib.meta.menu import MetaMenu
		return self._commandMenu(parameters = MetaMenu.instance().commandCreateMenu(media = tools.Media.Episode if season else tools.Media.Season, imdb = self.mImdb, tmdb = self.mTmdb, tvdb = self.mTvdb, trakt = self.mTrakt, season = self.mSeason if season else None, parameters = False))

	def commandDownloadCloud(self):
		return self._commandPlugin(action = 'downloadCloud', parameters = {'source' : self.mSource})

	def commandManualDefault(self):
		from lib.modules.handler import Handler
		from lib.modules.downloader import Downloader
		return self._commandPlugin(action = 'download', parameters = {'media' : self.mMedia, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'episode' : self.mEpisode, 'downloadType' : Downloader.TypeManual, 'handleMode' : Handler.ModeDefault, 'source' : self.mSource})

	def commandManualSelection(self):
		from lib.modules.handler import Handler
		from lib.modules.downloader import Downloader
		return self._commandPlugin(action = 'download', parameters = {'media' : self.mMedia, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'episode' : self.mEpisode, 'downloadType' : Downloader.TypeManual, 'handleMode' : Handler.ModeSelection, 'source' : self.mSource})

	def commandManualFile(self):
		from lib.modules.handler import Handler
		from lib.modules.downloader import Downloader
		return self._commandPlugin(action = 'download', parameters = {'media' : self.mMedia, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'episode' : self.mEpisode, 'downloadType' : Downloader.TypeManual, 'handleMode' : Handler.ModeFile, 'source' : self.mSource})

	def commandManualManager(self):
		from lib.modules.downloader import Downloader
		tools.System.launchAddon() # Important when called from outside Gaia.
		return self._commandMenu(action = 'downloadsManager', parameters = {'downloadType' : Downloader.TypeManual})

	def commandCacheDefault(self):
		from lib.modules.handler import Handler
		return self._commandPlugin(action = 'playCache', parameters = {'media' : self.mMedia, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'episode' : self.mEpisode, 'handleMode' : Handler.ModeDefault, 'source' : self.mSource})

	def commandCacheSelection(self):
		from lib.modules.handler import Handler
		return self._commandPlugin(action = 'playCache', parameters = {'media' : self.mMedia, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'episode' : self.mEpisode, 'handleMode' : Handler.ModeSelection, 'source' : self.mSource})

	def commandCacheFile(self):
		from lib.modules.handler import Handler
		return self._commandPlugin(action = 'playCache', parameters = {'media' : self.mMedia, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'episode' : self.mEpisode, 'handleMode' : Handler.ModeFile, 'source' : self.mSource})

	def commandCacheManager(self):
		from lib.modules.downloader import Downloader
		tools.System.launchAddon() # Important when called from outside Gaia.
		return self._commandMenu(action = 'downloadsManager', parameters = {'downloadType' : Downloader.TypeCache})

	def commandPlayDefault(self):
		from lib.modules.handler import Handler
		return self._commandPlugin(action = 'play', parameters = {'media' : self.mMedia, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'episode' : self.mEpisode, 'handleMode' : Handler.ModeDefault, 'reload' : not self.mMixed, 'source' : self.mSource})

	def commandPlaySelection(self):
		from lib.modules.handler import Handler
		return self._commandPlugin(action = 'play', parameters = {'media' : self.mMedia, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'episode' : self.mEpisode, 'handleMode' : Handler.ModeSelection, 'reload' : not self.mMixed, 'source' : self.mSource})

	def commandPlayFile(self):
		from lib.modules.handler import Handler
		return self._commandPlugin(action = 'play', parameters = {'media' : self.mMedia, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'episode' : self.mEpisode, 'handleMode' : Handler.ModeFile, 'reload' : not self.mMixed, 'source' : self.mSource})

	def commandFileAdd(self):
		return self._commandPlugin(action = 'fileAdd')

	def commandFileLink(self, mode):
		return self._commandPlugin(action = 'fileLink', parameters = {'source' : self.mSource, 'mode' : mode})

	def commandFileName(self):
		return self._commandPlugin(action = 'fileName', parameters = {'name' : self.mName})

	def commandFileHash(self):
		return self._commandPlugin(action = 'fileHash', parameters = {'hash' : self.mHash})

	def commandLink(self, media = None):
		return self._commandPlugin(action = 'qr', parameters = {'media' : media, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'episode' : self.mEpisode})

	def commandShortcutCreate(self):
		return self._commandPlugin(action = 'shortcutShow', parameters = {'label' : self.mShortcutLabel, 'command' : self.mShortcutCommand, 'folder' : self.mShortcutFolder, 'create' : True})

	def commandShortcutDelete(self):
		return self._commandPlugin(action = 'shortcutShow', parameters = {'id' : self.mShortcutId, 'delete' : True})

	def commandOrionVoteUp(self):
		return self._commandPlugin(action = 'orionVoteUp', parameters = {'idItem' : self.mOrion['item'], 'idStream' : self.mOrion['stream']})

	def commandOrionVoteDown(self):
		return self._commandPlugin(action = 'orionVoteDown', parameters = {'idItem' : self.mOrion['item'], 'idStream' : self.mOrion['stream']})

	def commandOrionRemove(self):
		return self._commandPlugin(action = 'orionRemove', parameters = {'idItem' : self.mOrion['item'], 'idStream' : self.mOrion['stream']})

	def commandRefreshMovie(self, level = None):
		return self._commandPlugin(action = 'refreshMetadata', parameters = {'media' : tools.Media.Movie, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'level' : level, 'container' : self._container(), 'notification' : True})

	def commandRefreshSet(self, level = None):
		return self._commandPlugin(action = 'refreshMetadata', parameters = {'media' : tools.Media.Set, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'level' : level, 'container' : self._container(), 'notification' : True})

	def commandRefreshShow(self):
		return self._commandPlugin(action = 'refreshMetadata', parameters = {'media' : tools.Media.Show, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'container' : self._container(), 'notification' : True})

	def commandRefreshSeason(self):
		return self._commandPlugin(action = 'refreshMetadata', parameters = {'media' : tools.Media.Season, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'container' : self._container(), 'notification' : True})

	def commandRefreshEpisode(self):
		return self._commandPlugin(action = 'refreshMetadata', parameters = {'media' : tools.Media.Episode, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'episode' : self.mEpisode, 'container' : self._container(), 'notification' : True})

	def commandRefreshPack(self):
		return self._commandPlugin(action = 'refreshMetadata', parameters = {'media' : tools.Media.Pack, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'container' : self._container(), 'notification' : True})

	def commandRefreshSerie(self, level = None):
		return self._commandPlugin(action = 'refreshMetadata', parameters = {'media' : tools.Media.Show, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'level' : level, 'container' : self._container(), 'notification' : True})

	def commandRefreshMenu(self):
		from lib.meta.menu import MetaMenu
		if MetaMenu.instance().notification(content = 'refresh', type = 'menu', background = False):
			Dialog.notification(title = 33060, message = 36784, icon = Dialog.IconInformation, time = 7000)
			return self._commandPlugin(action = 'refreshMenu', parameters = {'media' : self.mMedia, 'playback' : True, 'container' : self._container()})
		return None

	def commandRefreshList(self):
		# There are different ways we can reload the directory:
		#	1. Container.Update(path): Works, but just appends a new directory to the navigation. When navigating back it will show the previous unrefreshed list.
		#	2. Container.Update(path,replace): Works and replaces the directory, which 1. did not do. When navigating back it will go to the main menu, instead of the movie direcotry (seems to replace the entire history, not just the previous menu).
		#	3. ReplaceWindow(videos,path): Works, but replaces the entire menu history. Also shows and empty window while the new metadata is retrieved.
		#	4. _commandPlugin(): As if this was just a standard command. Refreshing metadata works, but when recreating the menu with interface.Directory, it complaints that the handle is invalid/-1, since the command was launched from the context instead of the normal directory navigation.
		#	5. _commandPlugin(): Execute the command to refresh the metadata, but do not create as menu with interface.Directory. Instead, just call Container.Refresh to let Kodi update the directory with the latests metadata.

		from lib.meta.menu import MetaMenu
		if MetaMenu.instance().notification(content = 'refresh', type = 'list', background = False):
			Dialog.notification(title = 33526, message = 36785, icon = Dialog.IconInformation, time = 7000)

			# If the query is encoded, decode it first before calling MetaMenu.commandCreateRefresh().
			# This is the case if we use the context menu -> Browse -> Browse Show -> then in the show menu open the context menu on a season -> Refresh -> Refresh Menu Metadata.
			if tools.Tools.isDictionary(self.mQuery): query = tools.System.commandResolve(self.mQuery)
			else: query = self.mQuery

			# NB: "full=False". Otherwise it this is called from the context of a movie entry, it will add the movie's niche to the refresh command to refresh the menu with, which is not what we want.
			return self._commandPlugin(parameters = MetaMenu.commandCreateRefresh(container = self._container(), parameters = query), full = False)
		return None

	def commandProvider(self, provider = None):
		if provider:
			from lib.meta.menu import MetaMenu
			return self._commandMenu(parameters = MetaMenu.commandCreateProvider(provider = provider, command = self.mLink))
		else:
			return self._commandMenu(command = self.mLink)

	def commandLibraryAddDirect(self):
		return self._commandPlugin(action = 'libraryAdd', parameters = {'media' : self.mMedia, 'link' : self.mLibrary})

	def commandLibraryAddStream(self):
		return self._commandPlugin(action = 'libraryAdd', parameters = {'media' : self.mMedia, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'episode' : self.mEpisode, 'link' : self.mLink})

	def commandLibraryAddMovie(self):
		return self._commandPlugin(action = 'libraryAdd', parameters = {'media' : tools.Media.Movie, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt})

	def commandLibraryAddEpisode(self):
		return self._commandPlugin(action = 'libraryAdd', parameters = {'media' : tools.Media.Episode, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason, 'episode' : self.mEpisode})

	def commandLibraryAddSeason(self):
		return self._commandPlugin(action = 'libraryAdd', parameters = {'media' : tools.Media.Season, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt, 'season' : self.mSeason})

	def commandLibraryAddShow(self):
		return self._commandPlugin(action = 'libraryAdd', parameters = {'media' : tools.Media.Show, 'imdb' : self.mImdb, 'tmdb' : self.mTmdb, 'tvdb' : self.mTvdb, 'trakt' : self.mTrakt})

	def commandLibraryUpdate(self):
		return self._commandPlugin(action = 'libraryUpdate', parameters = {'force' : True})

	def commandLibraryClean(self):
		return self._commandPlugin(action = 'libraryClean')

	def commandSettingsGaia(self):
		return self._commandPlugin(action = 'settingsAdvanced')

	def _commandSettingsClose(self):
		from lib.modules.window import WindowStreams
		if WindowStreams.visible():
			WindowStreams.close()
			tools.Time.sleep(0.01)

	def commandSettingsSkin(self):
		self._commandSettingsClose()
		return 'ActivateWindow(skinsettings)'

	def commandSettingsKodi(self):
		self._commandSettingsClose()
		return 'ActivateWindow(settings)'

	def commandNetworkInfo(self):
		return self._commandPlugin(action = 'networkInformation')

	def commandNetworkTest(self):
		return self._commandPlugin(action = 'speedtestGlobal')

	def commandVpnChange(self):
		return self._commandPlugin(action = 'vpnChange', parameters = {'dialog' : True})

	def commandVpnDisconnect(self):
		return self._commandPlugin(action = 'vpnDisconnect')

	def commandVpnStatus(self):
		return self._commandPlugin(action = 'vpnStatus')

	def commandVpnSettings(self):
		return self._commandPlugin(action = 'vpnSettings', parameters = {'external' : True})

	def commandBluetoothConnect(self):
		return self._commandPlugin(action = 'bluetoothConnect')

	def commandBluetoothDisconnect(self):
		return self._commandPlugin(action = 'bluetoothDisconnect')

	def commandBluetoothDevices(self):
		return self._commandPlugin(action = 'bluetoothDialog')

	def commandSystemInformation(self):
		return self._commandPlugin(action = 'systemInformation')

	def commandSystemManager(self):
		return self._commandPlugin(action = 'systemManager')

	def commandSystemPower(self):
		return self._commandPlugin(action = 'systemPower')

	def commandSystemCleanup(self):
		return self._commandPlugin(action = 'cleanup')

	def commandLogScrape(self):
		return self._commandPlugin(action = 'logScrape')

	def commandLogKodi(self):
		return self._commandPlugin(action = 'logKodi')

	def commandLogExport(self):
		return self._commandPlugin(action = 'supportReport')

	def commandOracleGeneric(self):
		return self._commandPlugin(action = 'oracle', parameters = {'media' : None, 'full' : True}) # Always show the full window process when launched from the context menu. So if the user has disabled certain steps in the settings, the full mode & search mode can still be launched from the context.

	def commandOracleMovie(self):
		return self._commandPlugin(action = 'oracle', parameters = {'media' : tools.Media.Movie, 'full' : True})

	def commandOracleShow(self):
		return self._commandPlugin(action = 'oracle', parameters = {'media' : tools.Media.Show, 'full' : True})

	def commandOracleSet(self):
		return self._commandPlugin(action = 'oracle', parameters = {'media' : tools.Media.Set, 'full' : True})

	def add(self, label, icon = None, action = None, command = None, parameters = None, condition = None, dynamic = None, close = None, loader = None, items = None):
		try:
			item = {'label' : self._translate(label)}
			if icon: item['icon'] = icon
			if action: item['action'] = action
			if command: item['command'] = command
			if parameters: item['parameters'] = parameters
			if condition: item['condition'] = condition
			if dynamic: item['dynamic'] = dynamic
			if close: item['close'] = close
			if loader: item['loader'] = loader
			if items:
				item['items'] = [i for i in items if i]
				if icon:
					for i in item['items']:
						if not 'icon' in i: i['icon'] = icon
						if 'items' in i:
							for j in i['items']:
								if not 'icon' in j: j['icon'] = icon
								if 'items' in j:
									for k in j['items']:
										if not 'icon' in k: k['icon'] = icon
			self.mItems.append(item)
		except: tools.Logger.error()

	def addGeneric(self):
		try:
			self.addProvider()
			self.addLibrary()
			self.addPlaylist()
			self.addShortcut()
			self.addTrakt()
			self.addTools()
		except: tools.Logger.error()

	def addItem(self):
		try:
			self.addInformation()
			if self.mMedia == tools.Media.Set:
				self.addVideos()
				self.addLink()
			elif not self.mMedia == tools.Media.Person:
				self.addVideos()
				self.addBrowse()
				self.addBinge()
				self.addScrape()
				self.addLink()
				self.addActivity()
				self.addLibrary()
				self.addPlaylist()
			self.addShortcut()
			self.addDownloads()
			self.addRefresh()
			self.addTools()
		except: tools.Logger.error()

	def addStream(self):
		try:
			self.addPlay()
			self.addCache()
			self.addInformation()
			self.addFile()
			self.addFilters()
			self.addActivity()
			self.addOrion()
			self.addLibrary()
			self.addPlaylist()
			self.addShortcut()
			self.addManual()
			self.addTools()
		except: tools.Logger.error()

	def addVideo(self):
		try:
			self.addSelection()
			self.addInformation()
			self.addVideos()
			self.addBrowse()
			self.addBinge()
			self.addScrape()
			self.addLink()
			self.addActivity()
			self.addLibrary()
			self.addPlaylist()
			self.addShortcut()
			self.addDownloads()
			self.addRefresh()
			self.addTools()
		except: tools.Logger.error()

	def addInformation(self):
		items = []

		# Kodi can only show the dialog for the currently selected ListItem in the GUI.
		# Update: This seems to be solved in Kodi 21, probably also Kodi 20.
		if Context.SettingsInformer and tools.System.versionKodiMaximum(version = 19):
			label = 33419
			if self.mMode == Context.ModeStream: label = 35506 if self.mEpisode is None else 35509
			items.insert(0, {'label' : label, 'command' : 'commandInformation', 'loader' : True})
		else:
			if self.mMedia == tools.Media.Person: items.insert(0, {'label' : 35819, 'command' : 'commandInformationPerson', 'loader' : True})
			if tools.Media.isSerie(self.mMedia) or tools.Media.isBonus(self.mMedia):
				if not self.mEpisode is None: items.insert(0, {'label' : 35509, 'command' : 'commandInformationEpisode', 'loader' : True})
				if not self.mSeason is None: items.insert(0, {'label' : 35508, 'command' : 'commandInformationSeason', 'loader' : True})
				if self.mImdb or self.mTmdb or self.mTvdb or self.mTrakt: items.insert(0, {'label' : 35507, 'command' : 'commandInformationShow', 'loader' : True})
			elif tools.Media.isFilm(self.mMedia):
				if self.mSet: items.insert(0, {'label' : 36400, 'command' : 'commandInformationSet', 'loader' : True})
				if (self.mImdb or self.mTmdb or self.mTvdb or self.mTrakt) and self.mSeason is None and self.mEpisode is None: items.insert(0, {'label' : 35506, 'command' : 'commandInformationMovie', 'loader' : True})
			elif tools.Media.isSet(self.mMedia):
				items.insert(0, {'label' : 36400, 'command' : 'commandInformationSet', 'loader' : True})

		if self.mMode == Context.ModeStream: items.insert(0, {'label' : 33415, 'command' : 'commandInformationStream', 'loader' : True})

		if items:
			if len(items) == 1:
				item = items[0]
				item['label'] = 33419
				item['icon'] = Font.IconInfo
				self.add(**item)
			else:
				self.add(label = 33419, icon = Font.IconInfo, items = items)

	def addFilters(self):
		self.add(label = 35477, icon = Font.IconFilter, command = 'commandFilters', loader = True)

	def addActivity(self):
		items = []

		items.append({'label' : 33651, 'command' : 'commandActivityWatch', 'loader' : True})
		if self.mPlays: items.append({'label' : 33652, 'command' : 'commandActivityUnwatch', 'loader' : True})

		items.append({'label' : 33653, 'command' : 'commandActivityRate', 'loader' : True})
		if self.mRating: items.append({'label' : 33654, 'command' : 'commandActivityUnrate', 'loader' : True})

		if self.mProgress: items.append({'label' : 33979, 'command' : 'commandActivityReset', 'loader' : True})
		items.append({'label' : 33678, 'command' : 'commandActivityRefresh', 'loader' : True})

		if Context.EnabledTrakt: items.append({'label' : 32070, 'command' : 'commandActivityTrakt', 'loader' : True})

		self.add(label = 35051, icon = Font.IconActivity, items = items)

	def addTrakt(self):
		self.add(label = 32315, icon = Font.IconTrakt, command = 'commandActivityTrakt', loader = True)

	def addScrape(self):
		if self.mTvdb is None or not self.mEpisode is None:
			serie = tools.Media.isSerie(self.mMedia)
			self.add(label = 35514, icon = Font.IconScrape, items = [
				{'label' : 33353, 'command' : 'commandScrapeAgain', 'loader' : True},
				{'label' : 35522, 'command' : 'commandScrapeManual', 'loader' : True},
				{'label' : 35523, 'command' : 'commandScrapeAutomatic', 'loader' : True},
				{'label' : 35524, 'condition' : 'Context.EnabledPresets', 'items' : [
					{'label' : 35522, 'command' : 'commandScrapePresetManual', 'loader' : True},
					{'label' : 35523, 'command' : 'commandScrapePresetAutomatic', 'loader' : True},
				]},
				{'label' : 35585, 'command' : 'commandScrapeSingle', 'condition' : 'Context.EnabledBinge', 'loader' : True} if serie else None,
				{'label' : 35586, 'command' : 'commandScrapeBinge', 'condition' : 'not Context.EnabledBinge', 'loader' : True} if serie else None,
			])

	def addBinge(self):
		if tools.Media.isSerie(self.mMedia):
			self.add(label = 35580, icon = Font.IconBinge, command = 'commandBinge', loader = True)

	def addPlaylist(self):
		# NB: Do not add the custom context menu to items in the playlist.
		# NB: This requires additional JSON and URL encodings and the entire context menu must be added as a parameter to the main context menu, increasing the size of the plugin command.
		# NB: More importantly, it drastically increases the time in takes to generate context menus, epsecially for lists with a lot of streams.
		# NB: Bad luck, playlist items have to work without a context menu.
		label = self._labelItem() if self.mPlaylist else None
		self.add(label = 35515, icon = Font.IconPlaylist, items = [
			{'label' : 35517, 'command' : 'commandPlaylistShow', 'close' : True},
			{'label' : 35516, 'command' : 'commandPlaylistClear', 'condition' : 'not tools.Playlist.empty()'},
			{'label' : 32065, 'command' : 'commandPlaylistAdd', 'condition' : 'not tools.Playlist.contains("%s")' % label} if self.mPlaylist else None,
			{'label' : 35518, 'command' : 'commandPlaylistRemove', 'condition' : 'tools.Playlist.contains("%s")' % label} if self.mPlaylist else None,
		])

	def addVideos(self):
		if Context.EnabledVideoContext:
			from lib.modules import video
			spoilers = ' (%s)' % Translation.string(35533)
			spoilers = '' # Remove the spoilers label for now.
			if Context.EnabledVideoContext == 1: command = 'commandVideoDirect'
			elif Context.EnabledVideoContext == 2: command = 'commandVideoAutomatic'
			elif Context.EnabledVideoContext == 3: command = 'commandVideoManual'
			else: command = 'commandVideo'
			self.add(label = 35351, icon = Font.IconVideo, items = [
				{'label' : Translation.string(video.Trailer.Label), 'command' : command, 'parameters' : video.Trailer.Id, 'close' : True, 'loader' : True} if Context.EnabledVideoTrailer or not tools.Media.isSerie(self.mMedia) else None,
				{'label' : Translation.string(video.Recap.Label) + spoilers, 'command' : command, 'parameters' : video.Recap.Id, 'close' : True, 'loader' : True} if Context.EnabledVideoRecap else None,
				{'label' : Translation.string(video.Review.Label) + spoilers, 'command' : command, 'parameters' : video.Review.Id, 'close' : True, 'loader' : True} if Context.EnabledVideoReview else None,
				{'label' : Translation.string(video.Reaction.Label) + spoilers, 'command' : command, 'parameters' : video.Reaction.Id, 'close' : True, 'loader' : True} if Context.EnabledVideoReaction else None,
				{'label' : Translation.string(video.Bonus.Label) + spoilers, 'command' : command, 'parameters' : video.Bonus.Id, 'close' : True, 'loader' : True} if Context.EnabledVideoBonus else None,
				{'label' : Translation.string(video.Deleted.Label) + spoilers, 'command' : command, 'parameters' : video.Deleted.Id, 'close' : True, 'loader' : True} if Context.EnabledVideoDeleted else None,
				{'label' : Translation.string(video.Production.Label) + spoilers, 'command' : command, 'parameters' : video.Production.Id, 'close' : True, 'loader' : True} if Context.EnabledVideoProduction else None,
				{'label' : Translation.string(video.Direction.Label) + spoilers, 'command' : command, 'parameters' : video.Direction.Id, 'close' : True, 'loader' : True} if Context.EnabledVideoDirection else None,
				{'label' : Translation.string(video.Interview.Label) + spoilers, 'command' : command, 'parameters' : video.Interview.Id, 'close' : True, 'loader' : True} if Context.EnabledVideoInterview else None,
				{'label' : Translation.string(video.Explanation.Label) + spoilers, 'command' : command, 'parameters' : video.Explanation.Id, 'close' : True, 'loader' : True} if Context.EnabledVideoExplanation else None,
				{'label' : Translation.string(video.Alternation.Label) + spoilers, 'command' : command, 'parameters' : video.Alternation.Id, 'close' : True, 'loader' : True} if Context.EnabledVideoAlternation else None,
			])

	def addSelection(self):
		self.add(label = 35143, icon = Font.IconVideo, items = [
			{'label' : 35646, 'command' : 'commandVideoManual', 'close' : True, 'loader' : True},
			{'label' : 35647, 'command' : 'commandVideoAutomatic', 'close' : True, 'loader' : True},
		])

	def addRefresh(self):
		items = [
			{'label' : 33526, 'command' : 'commandRefreshList', 'loader' : True},
			{'label' : 33060, 'command' : 'commandRefreshMenu', 'loader' : True},
		]
		if tools.Media.isFilm(self.mMedia):
			items.append({'label' : 33522, 'command' : 'commandRefreshMovie', 'parameters' : 0, 'loader' : True})
			if self.mSet:
				items.append({'label' : 36773, 'command' : 'commandRefreshMovie', 'parameters' : 1, 'loader' : True})
				items.append({'label' : 36771, 'command' : 'commandRefreshMovie', 'parameters' : 2, 'loader' : True})
		elif tools.Media.isSet(self.mMedia):
			items.append({'label' : 36773, 'command' : 'commandRefreshSet', 'parameters' : 0, 'loader' : True})
			items.append({'label' : 33522, 'command' : 'commandRefreshSet', 'parameters' : 1, 'loader' : True})
			items.append({'label' : 36771, 'command' : 'commandRefreshSet', 'parameters' : 2, 'loader' : True})
		elif tools.Media.isSerie(self.mMedia) or tools.Media.isBonus(self.mMedia):
			items.append({'label' : 33523, 'command' : 'commandRefreshShow', 'loader' : True})
			items.append({'label' : 33524, 'command' : 'commandRefreshSeason', 'loader' : True})
			if not self.mSeason is None: items.append({'label' : 33525, 'command' : 'commandRefreshEpisode', 'loader' : True})
			items.append({'label' : 36774, 'command' : 'commandRefreshPack', 'loader' : True})
			items.append({'label' : 36772, 'command' : 'commandRefreshSerie', 'parameters' : 1, 'loader' : True})
			items.append({'label' : 36771, 'command' : 'commandRefreshSerie', 'parameters' : 2, 'loader' : True})

		self.add(label = 32072, icon = Font.IconRefresh, items = items, loader = True)

	def addBrowse(self):
		if tools.Media.isSerie(self.mMedia) or tools.Media.isBonus(self.mMedia):
			if self.mSeason is None:
				self.add(label = 32071, icon = Font.IconBrowse, command = 'commandBrowse')
			else:
				self.add(label = 32071, icon = Font.IconBrowse, items = [
					{'label' : 36397, 'command' : 'commandBrowse', 'parameters' : False},
					{'label' : 36398, 'command' : 'commandBrowse', 'parameters' : True},
				])

	def addDownloads(self):
		self.add(label = 32009, icon = Font.IconDownload, items = [
			{'label' : 33585, 'command' : 'commandManualManager', 'close' : True, 'condition' : 'Context.EnabledDownloadManual and Context.EnabledManagerManual'},
			{'label' : 35499, 'command' : 'commandCacheManager', 'close' : True, 'condition' : 'Context.EnabledDownloadCache and Context.EnabledManagerCache'},
		])

	def addManual(self):
		self.add(label = 33051, icon = Font.IconDownload, items = [
			{'label' : 35472, 'command' : 'commandManualDefault', 'condition' : 'Context.EnabledDownloadManual'},
			{'label' : 33562, 'command' : 'commandManualSelection', 'condition' : 'Context.EnabledDownloadManual'},
			{'label' : 35161, 'command' : 'commandManualFile', 'condition' : 'Context.EnabledDownloadManual'},
			{'label' : 33585, 'command' : 'commandManualManager', 'close' : True, 'condition' : 'Context.EnabledDownloadManual and Context.EnabledManagerManual', 'loader' : True},
			{'label' : 33229, 'command' : 'commandDownloadCloud', 'condition' : 'Context.EnabledDownloadCloud'},
		])

	def addCache(self):
		self.add(label = 33016, icon = Font.IconCache, items = [
			{'label' : 35471, 'command' : 'commandCacheDefault', 'condition' : 'Context.EnabledDownloadCache'},
			{'label' : 33563, 'command' : 'commandCacheSelection', 'condition' : 'Context.EnabledDownloadCache'},
			{'label' : 35544, 'command' : 'commandCacheFile', 'condition' : 'Context.EnabledDownloadCache'},
			{'label' : 35499, 'command' : 'commandCacheManager', 'close' : True, 'condition' : 'Context.EnabledDownloadCache and Context.EnabledManagerCache', 'loader' : True},
		])

	def addPlay(self):
		self.add(label = 35470, icon = Font.IconPlay, items = [
			{'label' : 35378, 'command' : 'commandPlayDefault'},
			{'label' : 33561, 'command' : 'commandPlaySelection'},
			{'label' : 35543, 'command' : 'commandPlayFile'},
		])

	def addFile(self):
		links = [
			{'label' : 35332, 'command' : 'commandFileLink', 'parameters' : 'original', 'loader' : True},
			{'label' : 35688, 'command' : 'commandFileLink', 'parameters' : 'resolved', 'loader' : True},
			{'label' : 35460, 'command' : 'commandFileLink', 'parameters' : 'stream', 'loader' : True},
		]
		if (tools.Media.isSerie(self.mMedia) or tools.Media.isBonus(self.mMedia)) and not self.mSeason is None:
			sublinks = [{'label' : 36482, 'command' : 'commandLink', 'parameters' : tools.Media.Show, 'loader' : True}]
			if not self.mSeason is None: sublinks.append({'label' : 36483, 'command' : 'commandLink', 'parameters' : tools.Media.Season, 'loader' : True})
			if not self.mEpisode is None: sublinks.append({'label' : 36484, 'command' : 'commandLink', 'parameters' : tools.Media.Episode, 'loader' : True})
			links.append({'label' : 36481, 'command' : 'commandLink', 'loader' : True, 'items' : sublinks})
		elif self.mSet:
			links.append({'label' : 36481, 'command' : 'commandLink', 'loader' : True, 'items' : [
				{'label' : 36485, 'command' : 'commandLink', 'parameters' : tools.Media.Movie, 'loader' : True},
				{'label' : 36486, 'command' : 'commandLink', 'parameters' : tools.Media.Set, 'loader' : True}
			]})
		elif self.mMedia:
			links.append({'label' : 36481, 'command' : 'commandLink', 'parameters' : self.mMedia, 'loader' : True})
		else:
			links.append({'label' : 36481, 'command' : 'commandLink', 'loader' : True})

		self.add(label = 33380, icon = Font.IconFile, items = [
			{'label' : 35434, 'command' : 'commandFileAdd'},
			{'label' : 33031, 'items' : links},
			{'label' : 33036, 'command' : 'commandFileName', 'loader' : True} if self.mName else None,
			{'label' : 33494, 'command' : 'commandFileHash', 'loader' : True} if self.mHash else None,
		])

	def addLink(self):
		if (tools.Media.isSerie(self.mMedia) or tools.Media.isBonus(self.mMedia)) and not self.mSeason is None:
			links = [{'label' : 36482, 'command' : 'commandLink', 'parameters' : tools.Media.Show, 'loader' : True}]
			if not self.mSeason is None: links.append({'label' : 36483, 'command' : 'commandLink', 'parameters' : tools.Media.Season, 'loader' : True})
			if not self.mEpisode is None: links.append({'label' : 36484, 'command' : 'commandLink', 'parameters' : tools.Media.Episode, 'loader' : True})
			self.add(label = 33381, icon = Font.IconLink, items = links)
		elif self.mSet:
			self.add(label = 33381, icon = Font.IconLink, items = [
				{'label' : 36485, 'command' : 'commandLink', 'parameters' : tools.Media.Movie, 'loader' : True},
				{'label' : 36486, 'command' : 'commandLink', 'parameters' : tools.Media.Set, 'loader' : True}
			])
		elif self.mMedia:
			self.add(label = 33381, icon = Font.IconLink, command = 'commandLink', parameters = self.mMedia, loader = True)
		else:
			self.add(label = 33381, icon = Font.IconLink, command = 'commandLink', loader = True)

	def addShortcut(self):
		from lib.modules.shortcut import Shortcut
		if Shortcut.enabled():
			if self.mShortcutCreate: self.add(label = 35119, icon = Font.IconShortcut, command = 'commandShortcutCreate', loader = True)
			elif self.mShortcutDelete: self.add(label = 35119, icon = Font.IconShortcut, command = 'commandShortcutDelete', loader = True)

	def addOrion(self):
		if Context.EnabledOrion and self.mOrion:
			self.add(label = 35400, icon = Font.IconOrion, items = [
				{'label' : 35527, 'command' : 'commandOrionVoteUp'},
				{'label' : 35528, 'command' : 'commandOrionVoteDown'},
				{'label' : 35529, 'command' : 'commandOrionRemove'},
			])

	def addProvider(self):
		if self.mProvider:
			from lib.meta.menu import MetaMenu
			from lib.meta.manager import MetaManager
			items = []
			search = MetaMenu.commandIsSearch(command = self.mLink)
			manager = MetaManager.instance()
			label = Translation.string(36335 if search else 33573)
			items.append({'label' : 36334 if search else 33572, 'command' : 'commandProvider', 'parameters' : None})
			for i in self.mProvider: items.append({'label' : label % manager.providerName(i), 'command' : 'commandProvider', 'parameters' : i})
			self.add(label = 32010 if search else 33537, icon = Font.IconSearch if search else Font.IconExplore, items = items)

	def addLibrary(self):
		items = []
		if not self.mLibrary is None:
			items.append({'label' : self._translate(35495, 32515), 'command' : 'commandLibraryAddDirect', 'condition' : 'Context.EnabledLibrary'})
		elif self.mMode == Context.ModeStream and not self.mLink is None:
			items.append({'label' : self._translate(35495, 33071), 'command' : 'commandLibraryAddStream', 'condition' : 'Context.EnabledLibrary'})
		if tools.Media.isFilm(self.mMedia) and (not self.mImdb == None or not self.mTmdb is None):
			items.append({'label' : self._translate(35495, 35496), 'command' : 'commandLibraryAddMovie', 'condition' : 'Context.EnabledLibrary'})
		if (tools.Media.isSerie(self.mMedia) or tools.Media.isBonus(self.mMedia)) and (not self.mImdb is None or not self.mTvdb is None):
			if not self.mSeason is None and not self.mEpisode is None:
				items.append({'label' : self._translate(35495, 33028), 'command' : 'commandLibraryAddEpisode', 'condition' : 'Context.EnabledLibrary'})
			if not self.mSeason is None:
				items.append({'label' : self._translate(35495, 32055), 'command' : 'commandLibraryAddSeason', 'condition' : 'Context.EnabledLibrary'})
			items.append({'label' : self._translate(35495, 35498), 'command' : 'commandLibraryAddShow', 'condition' : 'Context.EnabledLibrary'})
		items.append({'label' : self._translate(35493), 'command' : 'commandLibraryUpdate', 'condition' : 'Context.EnabledLibrary'})
		items.append({'label' : self._translate(35674), 'command' : 'commandLibraryClean', 'condition' : 'Context.EnabledLibrary'})
		self.add(label = 35170, icon = Font.IconLibrary, items = items)

	def addTools(self):
		self.add(label = 32008, icon = Font.IconSettings, items = [
			{'label' : 33011, 'icon' : Font.IconSettings, 'items' : [
				{'label' : 32341, 'icon' : Font.IconSettings, 'command' : 'commandSettingsGaia'},
				{'label' : 32342, 'icon' : Font.IconSettings, 'command' : 'commandSettingsSkin'},
				{'label' : 32343, 'icon' : Font.IconSettings, 'command' : 'commandSettingsKodi'},
			]},
			{'label' : 33719, 'icon' : Font.IconSettings, 'items' : [
				{'label' : 33037, 'icon' : Font.IconSettings, 'command' : 'commandNetworkInfo'},
				{'label' : 33030, 'icon' : Font.IconSettings, 'command' : 'commandNetworkTest'},
			]},
			{'label' : 33801, 'icon' : Font.IconSettings, 'condition' : 'Context.EnabledVpnManager', 'items' : [
				{'label' : 33150, 'icon' : Font.IconSettings, 'command' : 'commandVpnChange'},
				{'label' : 33811, 'icon' : Font.IconSettings, 'command' : 'commandVpnDisconnect'},
				{'label' : 33812, 'icon' : Font.IconSettings, 'command' : 'commandVpnStatus'},
				{'label' : 33813, 'icon' : Font.IconSettings, 'command' : 'commandVpnSettings'},
			]} if Context.EnabledVpnManager else None,
			{'label' : 33529, 'icon' : Font.IconSettings, 'items' : [
				{'label' : 33530, 'icon' : Font.IconSettings, 'command' : 'commandBluetoothConnect'},
				{'label' : 33531, 'icon' : Font.IconSettings, 'command' : 'commandBluetoothDisconnect'},
				{'label' : 33532, 'icon' : Font.IconSettings, 'command' : 'commandBluetoothDevices'},
			]} if Context.EnabledBluetooth else None,
			{'label' : 33467, 'icon' : Font.IconSettings, 'items' : [
				{'label' : 33478, 'icon' : Font.IconSettings, 'command' : 'commandSystemInformation'},
				{'label' : 33479, 'icon' : Font.IconSettings, 'command' : 'commandSystemManager'},
				{'label' : 33476, 'icon' : Font.IconSettings, 'command' : 'commandSystemPower'},
				{'label' : 33495, 'icon' : Font.IconSettings, 'command' : 'commandSystemCleanup'},
			]},
			{'label' : 32062, 'icon' : Font.IconSettings, 'items' : [
				{'label' : 32063, 'icon' : Font.IconSettings, 'command' : 'commandLogScrape'},
				{'label' : 32064, 'icon' : Font.IconSettings, 'command' : 'commandLogKodi'},
				{'label' : 33151, 'icon' : Font.IconSettings, 'command' : 'commandLogExport'},
			]},
			{'label' : 33675, 'icon' : Font.IconSettings, 'items' : [
				{'label' : 36331, 'icon' : Font.IconSettings, 'command' : 'commandOracleGeneric'},
				{'label' : 36332, 'icon' : Font.IconSettings, 'command' : 'commandOracleMovie'},
				{'label' : 36333, 'icon' : Font.IconSettings, 'command' : 'commandOracleShow'},
				{'label' : 36336, 'icon' : Font.IconSettings, 'command' : 'commandOracleSet'},
			]},
		])

	def show(self, wait = False):
		# Sometimes a sporadic issue occurs where it seems that the Gaia context menu is populated twice (or more) with the same context menu items.
		# This makes the context menu unusable, since all the menu indexes are now wrong and selecting from submenus does not work anymore.
		# The only solution is to restart Kodi.
		# Not sure if this is caused by using threads below, so that multiple threads might be started at the same time, both populating the global context menu.
		# A possible solution is to use Context.PropertyContextBusy and only start a thread if the flag was not set.
		# Not sure if this actually solves the problem. If this does not happen again in the future, then we assume this does solve it.

		Loader.show()
		from lib.modules.window import Window
		if not Window.propertyGlobal(Context.PropertyContextBusy):
			Window.propertyGlobalSet(Context.PropertyContextBusy, True)

			# Start in a background thread, so that the underlying window/dialog can be closed and reopened.
			# The context menu is therefore not depended on the parent window.
			thread = Pool.thread(target = self._show, start = True)
			if wait: thread.join()
		else:
			Loader.hide()

	def _condition(self, item):
		if 'condition' in item:
			exec('result = ' + item['condition'], globals(), locals())
			return locals()['result']
		else:
			return True

	def _filter(self, items):
		items = [i for i in items if self._condition(i)]
		items = [i for i in items if not 'items' in i or len(self._filter(i['items'])) > 0]
		return items

	def _show(self):
		try:
			Loader.hide()
			items = [i for i in self.mItems if i]
			choices = []
			while True:
				index = len(choices)
				sub = index > 0

				item = items
				item = self._filter(item)
				for i in choices: item = item[i]['items']
				item = self._filter(item)

				labels = [self._labelIcon(label = i['label'], icon = i['icon'] if 'icon' in i else None) for i in item]
				if sub: labels.insert(0, Context.LabelBack)
				else: labels.insert(0, Context.LabelClose)
				choice = Dialog.context(labels = labels)

				if choice < 0 or (not sub and choice == 0):
					break
				elif sub and choice == 0:
					choices = choices[:-1]
					continue
				else:
					choice -= 1
					menu = item[choice]
					if 'dynamic' in menu and not 'items' in menu:
						Loader.show()
						exec('dynamic = ' + menu['dynamic'] + '()', globals(), locals())
						dynamic = locals()['dynamic']
						items[choice]['items'] = dynamic
						menu['items'] = dynamic
						Loader.hide()

					if 'items' in menu:
						choices.append(choice)
						continue
					else:
						if 'command' in menu and menu['command']:
							if 'loader' in menu and menu['loader']: Loader.show()
							if 'parameters' in menu and menu['parameters']: tools.System.execute(getattr(self, menu['command'])(menu['parameters']))
							else: tools.System.execute(getattr(self, menu['command'])())
						if 'close' in menu and menu['close']: self._close()
						break
		except:
			tools.Logger.error()
		finally:
			from lib.modules.window import Window
			Window.propertyGlobalClear(Context.PropertyContextBusy)
