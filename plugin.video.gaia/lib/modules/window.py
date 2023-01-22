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

import xbmcgui
import re

from lib.modules import tools
from lib.modules import interface
from lib.modules.theme import Theme
from lib.modules.concurrency import Pool, Lock

class WindowBase(object):

	# Actions
	# https://codedocs.xyz/xbmc/xbmc/group__kodi__key__action__ids.html
	ActionAny = -1
	ActionMoveLeft = 1
	ActionMoveRight = 2
	ActionMoveUp = 3
	ActionMoveDown = 4
	ActionSelectItem = 7
	ActionBackSpace = 110
	ActionContextMenu = 117
	ActionPreviousMenu = 10
	ActionNavigationBack = 92
	ActionShowInfo = 11
	ActionItemNext = 14
	ActionItemPrevious = 15
	ActionsCancel = [ActionPreviousMenu, ActionNavigationBack, ActionBackSpace]

	def __init__(self, **arguments):
		self.mActions = []
		self.mControls = []
		self.mClicks = []
		self.mVisible = False

	def __del__(self):
		self.mVisible = False

	def show(self):
		self.mVisible = True
		self.mClosed = False
		xbmcgui.WindowDialog.show(self)

	def doModal(self):
		self.mVisible = True
		self.mClosed = False
		xbmcgui.WindowDialog.doModal(self)

	def close(self):
		xbmcgui.WindowDialog.close(self)
		self.mVisible = False

	def closed(self):
		return self.mClosed

	def visible(self):
		return self.mVisible

	def _onAction(self, action, callback):
		self.mActions.append((action, callback))

	def _onControl(self, x, y, callback):
		self.mControls.append((x, y, callback))

	def _onClick(self, control, callback):
		try: control = control.getId()
		except: pass
		self.mClicks.append((control, callback))

	def onAction(self, action):
		id = action.getId()
		if id in WindowBase.ActionsCancel: self.mVisible = False
		xbmcgui.WindowDialog.onAction(self, action)
		for i in self.mActions:
			if i[0] == WindowBase.ActionAny or i[0] == id:
				try: i[1](action = id)
				except: i[1]()

	def onControl(self, control):
		distances = []
		actions = []
		x = control.getX()
		y = control.getY()

		for i in self.mControls:
			distances.append(abs(x - i[0]) + abs(y - i[1]))
			actions.append(i[2])

		smallestIndex = -1
		smallestDistance = 999999
		for i in range(len(distances)):
			if distances[i] < smallestDistance:
				smallestDistance = distances[i]
				smallestIndex = i

		if smallestIndex >= 0:
			try: actions[smallestIndex](control = control)
			except: actions[smallestIndex]()

	def onClick(self, controlId):
		found = False
		for i in self.mClicks:
			if i[0] == controlId:
				found = True
				i[1]()

		# NB: The onControl() function should normally be called.
		# However, if a WindowXml is used and new controls are added dynamically via Python, it seems that onControl() is not called anymore.
		# Call onControl() manually here. Not sure if this somewhere causes onControl() to be called twice and result in weird behaviour.
		# If this is ever removed, make sure that WindowWizardPremium the navigation buttons at the buttom can be invoked/clicked/entered.
		# Only do this if "not found", otherwise when an authentication dialog (native Kodi dialog) is launched and "Cancel" is clicked in that dialog, the click propagates to underlying WindowWizard, also closing it.
		if not found: self.onControl(self.getControl(controlId))

class WindowCore(WindowBase, xbmcgui.WindowDialog):

	def __init__(self):
		super(WindowCore, self).__init__()

	def __del__(self):
		try: super(WindowCore, self).__del__()
		except: pass

class WindowXml(WindowBase, xbmcgui.WindowXMLDialog):

	def __init__(self, file, path, skin, resolution):
		# Using super() here with multiple inheritance does not work.
		WindowBase.__init__(self)
		xbmcgui.WindowXMLDialog.__init__(self, xmlFilename = file, scriptPath = path, defaultSkin = skin, defaultRes = resolution)

	def __del__(self):
		try: super(WindowXml, self).__del__()
		except: pass

class Window(object):

	Instance = None
	InstanceTypes = {}

	InitializeIterations = 100
	InitializeSleep = 0.1

	IdMinimum = 10000
	IdMaximum = 13000
	IdWindowHome = 10000
	IdWindowVideo = 10025
	IdWindowPlayer = 12901
	IdWindowPlayerFull = 12005
	IdWindowPlaylist = 10028
	IdWindowOk = 12002
	IdWindowInformation = 12003
	IdWindowNotification = 10107
	IdListControl = 52000

	PropertyType = 'GaiaType'
	PropertyAnimation = 'GaiaAnimation'

	# All Kodi windows have this fixed dimension.
	SizeWidth = 1280
	SizeHeight = 720

	# Size
	SizeLarge = 'large'
	SizeMedium = 'medium'
	SizeSmall = 'small'
	SizeMini = 'mini'

	# Replacements
	Replacements = {
		tools.Screen.Ratio4x3 : {
			'[GAIAPANELLEFT]' : '40',
			'[GAIAPOSTERTOP]' : '130',
			'[GAIAPOSTERWIDTH]' : '360',
			'[GAIAPOSTERHEIGHT]' : '400',
		},
		tools.Screen.Ratio16x9 : {
			'[GAIAPANELLEFT]' : '40',
			'[GAIAPOSTERTOP]' : '0',
			'[GAIAPOSTERWIDTH]' : '360',
			'[GAIAPOSTERHEIGHT]' : '530',
		},
		tools.Screen.Ratio20x9 : {
			'[GAIAPANELLEFT]' : '70',
			'[GAIAPOSTERTOP]' : '0',
			'[GAIAPOSTERWIDTH]' : '300',
			'[GAIAPOSTERHEIGHT]' : '530',
		},
	}

	# Type
	TypeNone = ''
	TypeStreamPlain = 'plain'
	TypeStreamBasic = 'basic'
	TypeStreamIcons = 'icons'
	TypeWizardSmall = 'small'
	TypeWizardLarge = 'large'
	TypeWizardScroll = 'scroll'
	TypeWizardStatic = 'static'
	TypeWizardQr = 'qr'
	TypeDefault = TypeNone
	Types = [TypeStreamPlain, TypeStreamBasic, TypeStreamIcons, TypeWizardSmall, TypeWizardLarge, TypeWizardScroll, TypeWizardStatic, TypeWizardQr]

	# Background
	BackgroundColorOpaque = 'FFFFFFFF'
	BackgroundColor1 = 'AA010101'
	BackgroundColor2 = '88010101'
	BackgroundColor3 = 'AA333333'
	BackgroundNone = 0
	BackgroundCombined = 1
	BackgroundSkin = 2
	BackgroundFanart = 3

	# Separator
	SeparatorLineWidth = 850
	SeparatorLineHeight = 3
	SeparatorLineNarrow = 650
	SeparatorLineWide = 1100
	SeparatorLinePadding = 25

	# Alignment
	AlignmentLeft = 0x00000000
	AlignmentRight = 0x00000001
	AlignmentTruncated = 0x00000008
	AlignmentJustified = 0x00000010
	AlignmentCenterX = 0x00000002
	AlignmentCenterY = 0x00000004
	AlignmentCenter = AlignmentCenterX | AlignmentCenterY
	AlignmentLeftCenter = AlignmentLeft | AlignmentCenterY
	AlignmentRightCenter = AlignmentRight | AlignmentCenterY
	AlignmentTruncatedCenter = AlignmentTruncated | AlignmentCenterY
	AlignmentJustifiedCenter = AlignmentJustified | AlignmentCenterY

	# Ratio
	RatioStretch = 0
	RatioScaleUp = 1
	RatioScaleDown = 2
	RatioDefault = RatioStretch

	# Button
	ButtonMedium = 'medium'
	ButtonLarge = 'large'

	# Select
	SelectNone = None
	SelectYes = True
	SelectNo = False
	SelectHide = 'hide'

	def __init__(self, backgroundType = None, backgroundPath = None, xml = None, xmlType = TypeDefault, xmlOffset = None, xmlReplacements = None, width = None, height = None):
		self.mId = 0
		self.mLock = Lock()
		self.mClose = False

		self.mEnd = False
		self.mControls = []
		self.mLabels = []
		self.mContexts = []
		self.mItems = []

		self.mBackgroundType = backgroundType
		self.mBackgroundPath = backgroundPath

		self.mScaleWidth = (Window.SizeWidth / float(Window.SizeHeight)) / (tools.Screen.width() / float(tools.Screen.height()))
		self.mScaleHeight = 1

		self.mWidth = Window.SizeWidth if width is None else width
		self.mHeight = Window.SizeHeight if height is None else height

		if xml:
			if xmlType and not tools.Tools.isArray(xmlType): xmlType = [xmlType]
			ratio = tools.Screen.ratio(closest = True)[0]
			xmlRatio = xml.replace('.xml', '') + (('.' + ('.'.join(xmlType))) if xmlType else '') + '.' + ratio + '.' + interface.Skin.id().lstrip('skin.').replace('.', '') + '.xml'
			if not '.' in xml: xml += '.xml'
			pathTemplate = self._pathTemplate()
			pathWindow = self._pathWindow(kodi = True)
			pathXml = tools.File.joinPath(pathTemplate, xml)
			pathRatio = tools.File.joinPath(pathWindow, xmlRatio)
			xml = xmlRatio

			if not tools.File.exists(pathRatio):
				tools.File.makeDirectory(pathWindow)
				data = tools.File.readNow(pathXml)

				for key, value in Window.Replacements[ratio].items():
					data = data.replace(key, value)

				types = tools.Tools.copy(Window.Types) # Copy, since we remove below.
				for type in xmlType:
					try: types.remove(type)
					except: pass

				flags = tools.Regex.FlagCaseInsensitive | tools.Regex.FlagAllLines

				# Replace "GAIATYPE..."
				data = self._replace(data = data, category = 'type', allow = xmlType, forbid = types)

				# Replace "GAIARATIO..."
				ratios = [i[0] for i in tools.Screen.Ratios]
				try: ratios.remove(ratio)
				except: pass
				data = self._replace(data = data, category = 'ratio', allow = [ratio], forbid = ratios)

				# Replace "GAIAFONT..."
				fonts = {
					'tiny' : interface.Font.fontTiny(),
					'small' : interface.Font.fontSmall(),
					'medium' : interface.Font.fontMedium(),
					'large' : interface.Font.fontLarge(),
					'huge' : interface.Font.fontHuge(),
					'big' : interface.Font.fontBig(),
					'massive' : interface.Font.fontMassive(),
					'colossal' : interface.Font.fontColossal(),
				}
				data = self._replace(data = data, category = 'font', single = fonts)

				data = self._replace(data = data, category = 'offset', single = xmlOffset if xmlOffset else 0)

				if xmlReplacements: data = self._replace(data = data, category = '', single = xmlReplacements)

				tools.File.writeNow(pathRatio, data)

			if not '.' in xml: xml += '.xml'
			self.mWindow = WindowXml(xml, self._pathWindow(kodi = False), 'default', '720p')
			self.mXml = True
		else:
			self.mWindow = WindowCore()
			self.mXml = False

	def __del__(self):
		self._remove()

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True, full = True):
		for type in Window.InstanceTypes.keys():
			try: globals()[type].Instance = None
			except: pass

		if full:
			WindowStreams.reset(settings = settings)
			WindowOptimization.reset(settings = settings)
			WindowWizard.reset(settings = settings)

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def instance(self):
		return self._instance()

	@classmethod
	def _instance(self, instance = None):
		# One instance per class.
		if not instance is None:
			globals()[self.__name__].Instance = instance
			Window.InstanceTypes[self.__name__] = True
		return globals()[self.__name__].Instance

	@classmethod
	def _instanceHas(self):
		return not globals()[self.__name__].Instance is None

	@classmethod
	def _instanceId(self):
		try: return globals()[self.__name__].Instance.mId
		except: return None

	@classmethod
	def _instanceDelete(self):
		try:
			del globals()[self.__name__].Instance
			globals()[self.__name__].Instance = None
		except: pass

	@classmethod
	def _replace(self, data, category, allow = None, forbid = None, single = None, custom = None):
		flags = tools.Regex.FlagCaseInsensitive | tools.Regex.FlagAllLines
		category = 'GAIA%s%%s' % category.upper()

		# IF (CURRENT TYPES)
		if allow:
			for type in allow:
				type = category % type.upper()
				expression = '(<!-- \[%s/\] -->(.*?)<!-- \[/%s\] -->)' % (type, type)
				matches = tools.Regex.extract(data = data, expression = expression, group = None, all = True, flags = flags)
				if matches:
					for match in matches:
						if not tools.Regex.match(data = match[0], expression = '\[/%s/\]' % type, flags = flags): # Ignore if-else.
							data = data.replace(match[0], match[1])

		# IF (OTHER TYPES)
		if forbid:
			for type in forbid:
				type = category % type.upper()
				expression = '<!-- \[%s/\] -->.*?<!-- \[/%s\] -->' % (type, type)
				matches = tools.Regex.extract(data = data, expression = expression, group = None, all = True, flags = flags)
				if matches:
					for match in matches:
						if not tools.Regex.match(data = match, expression = '\[/%s/\]' % type, flags = flags): # Ignore if-else.
							data = data.replace(match, '')

		# IF-ELSE (CURRENT TYPES)
		if allow:
			for type in allow:
				type = category % type.upper()
				expression = '<!-- \[%s/\] -->(.*?)<!-- \[/%s/\] -->.*?<!-- \[/%s\] -->' % (type, type, type)
				data = tools.Regex.replace(data = data, expression = expression, replacement = r'\1', group = None, all = True, flags = flags)

		# IF-ELSE (OTHER TYPES)
		if forbid:
			for type in forbid:
				type = category % type.upper()
				expression = '<!-- \[%s/\] -->.*?<!-- \[/%s/\] -->(.*?)<!-- \[/%s\] -->' % (type, type, type)
				data = tools.Regex.replace(data = data, expression = expression, replacement = r'\1', group = None, all = True, flags = flags)

		# SINGLE REPLACEMENTS
		if single:
			if not tools.Tools.isDictionary(single): single = {'' : single}
			for type, replacement in single.items():
				if tools.Tools.isFunction(replacement): replacement = replacement()
				type = category % type.upper()
				data = tools.Regex.replace(data = data, expression = '\[%s\]' % type, replacement = str(replacement), group = None, all = True, flags = flags)

		return data

	def _lock(self):
		self.mLock.acquire()

	def _unlock(self):
		self.mLock.release()

	def _locked(self):
		self.mLock.locked()

	def _initializeStart1(self):
		pass

	def _initializeStart2(self):
		self._addBackground(type = self.mBackgroundType, path = self.mBackgroundPath)

	def _initializeStart3(self):
		pass

	def _initializeEnd1(self):
		self.mEnd = True

	def _initializeEnd2(self):
		pass

	def _onAction(self, action, callback):
		if self.mWindow: self.mWindow._onAction(action, callback)

	def _onControl(self, x, y, callback):
		if self.mWindow: self.mWindow._onControl(x, y, callback)

	def _onClick(self, control, callback):
		if self.mWindow: self.mWindow._onClick(control, callback)

	@classmethod
	def _colorDefault(self):
		return interface.Format.colorWhite()

	@classmethod
	def _colorHighlight(self):
		return interface.Format.colorPrimary()

	@classmethod
	def _colorDiffuse(self):
		return interface.Format.colorDisabled()

	@classmethod
	def _colorSeparator(self):
		return interface.Format.colorSecondary()

	@classmethod
	def _end(self):
		try: return self._instance().mEnd
		except: pass

	@classmethod
	def _idPropertyName(self):
		return tools.System.name() + self.__name__

	@classmethod
	def _idProperty(self):
		id = self.propertyGlobal(self._idPropertyName())
		if id is None or id == '': return None
		else: return int(id)

	@classmethod
	def _idPropertySet(self, id):
		return self.propertyGlobalSet(self._idPropertyName(), id)

	@classmethod
	def _idPropertyClear(self):
		return self.propertyGlobalClear(self._idPropertyName())

	@classmethod
	def _initialize1(self, **arguments):
		try:
			window = self._instance(self(**arguments))
		except:
			try:
				try: del arguments['retry']
				except: pass
				window = self._instance(self(**arguments))
			except:
				tools.Logger.error()
				return None
		window.propertySet(Window.PropertyType, self.__name__)
		window._initializeStart1()
		window._initializeStart2()
		window._initializeControls(labels = False) # Initialize controls needed from the start (important for WindowStreams).
		window._initializeStart3()
		window.mWindow.doModal()
		window.close()

	@classmethod
	def _initialize2(self):
		try:
			count = 0
			instance = self._instance()
			while instance is None and count < Window.InitializeIterations and not tools.System.aborted():
				tools.Time.sleep(Window.InitializeSleep)
				count += 1
				instance = self._instance()
			if not instance is None:
				while not instance.visible() and count < Window.InitializeIterations and not tools.System.aborted():
					tools.Time.sleep(Window.InitializeSleep)
					count += 1
				id = self.current()
				instance.mId = id
				self._idPropertySet(instance.mId)
				instance._initializeEnd1()
				instance._initializeControls(labels = True) # Initialize remaining controls.
				instance._initializeAnimations()
				instance._initializeEnd2()
		except: tools.Logger.error()

	def _initializeControls(self, labels = True, lock = False):
		if lock: self._lock()

		# Add controls that were not added before.
		controls = []
		hidden = []
		animations = []
		for i in range(len(self.mControls)):
			if not self.mControls[i]['initialized']:
				self.mControls[i]['initialized'] = True
				controls.append(self.mControls[i]['control'])
				if not self.mControls[i]['visible']: hidden.append(self.mControls[i]['control'])
				if self.mControls[i]['animation']: animations.append((self.mControls[i]['control'], self.mControls[i]['animation']))

				# For button highlight animation.
				if 'components' in self.mControls[i]:
					components = self.mControls[i]['components']
					if 'animation' in components and ('control' in components or 'highlight' in components):
						animations.append((components['control'] if 'control' in components else components['highlight'], components['animation']))
		self.mWindow.addControls(controls)

		# Hide non-visible controls.
		# Cannot call setVisible(...) BEFORE the controls was added to the window.
		for control in hidden:
			control.setVisible(False)

		# Add animations.
		for control in animations:
			control[0].setAnimations(control[1])

		# Initialize the label text.
		if labels:
			for label in self.mLabels:
				self._setLabel(control = label['control'], text = label['text'], color = label['color'], size = label['size'], bold = label['bold'], italic = label['italic'], light = label['light'], uppercase = label['uppercase'], lowercase = label['lowercase'], capitalcase = label['capitalcase'])

		if lock: self._unlock()

	def _initializeAnimations(self):
		def _animate():
			# This time should corrsepond with the animation duration.
			# The animation should be stopped when it is at the end, not interrupted somwehere in the middle.
			# 5 seconds is a bit too long. 3 seconds allow buttons to blink twice.
			for i in range(30):
				if self.closed(): return # Important for consecutive rating dialogs.
				tools.Time.sleep(0.1)

			self.propertySet(Window.PropertyAnimation, 'false')
			for control in self.mControls:
				if 'components' in control and 'highlight' in control['components']:
					self._setButton(control = control, highlight = False)

		self.propertySet(Window.PropertyAnimation, 'true')
		Pool.thread(target = _animate, start = True)

	@classmethod
	def _show(self, **arguments):
		try:
			close = arguments['close']
			del arguments['close']
		except:
			close = False
		if self.visible() and not close:
			return False
		elif close:
			self.close()
			tools.Time.sleep(0.1)

		try:
			wait = arguments['wait']
			del arguments['wait']
		except:
			wait = True
		try:
			initialize = arguments['initialize']
			del arguments['initialize']
		except:
			initialize = True
		thread1 = Pool.thread(target = self._initialize1, kwargs = arguments)
		thread1.start()
		thread2 = Pool.thread(target = self._initialize2)
		thread2.start()
		if wait:
			thread1.join()
		elif initialize: # Wait until launched.
			count = 0
			while not self.visible() and count < Window.InitializeIterations and not tools.System.aborted():
				tools.Time.sleep(Window.InitializeSleep)
				count += 1
			while not self._end() and count < Window.InitializeIterations and not tools.System.aborted():
				tools.Time.sleep(Window.InitializeSleep)
				count += 1
		return True

	@classmethod
	def clean(self):
		tools.File.deleteDirectory(self._pathWindow())

	@classmethod
	def close(self, id = None, loader = False):
		try:
			# Instance might be lost if accessed in a subsequent execution (eg: applying filters).
			if id is None and not self._instanceHas(): id = self._idProperty()
			if id is None:
				instance = self._instance()
				if not instance.mClose: # In case this function is called multiple times.
					instance.mClose = True
					# Close the window BEFORE calling _remove().
					# This seems to solve the issue of Gaia labels remaining in the Kodi UI when the cancel button in scraping window is clicked.
					instance.mWindow.close()
					instance._remove()
					#instance.mWindow.close()
					if loader: interface.Loader.hide() # Sometimes is visible if canceling playback window.
					try: del instance.mWindow
					except: pass
					try: instance.mWindow = None
					except: pass
					self._instanceDelete()
			else:
				interface.Dialog.close(id)
			self._idPropertyClear()
			return True
		except:
			self._idPropertyClear()
			return False

	@classmethod
	def show(self, id):
		return tools.System.execute('ActivateWindow(%s)' % str(id))

	@classmethod
	def id(self):
		try: return self._instance().mId
		except: return None

	@classmethod
	def current(self, id = None):
		return self.currentDialog(id = id)

	@classmethod
	def currentWindow(self, id = None):
		result = xbmcgui.getCurrentWindowId()
		if id is None: return result
		else: return result == id

	@classmethod
	def currentWindowInstance(self):
		return xbmcgui.Window(self.currentWindow())

	@classmethod
	def currentDialog(self, id = None):
		result = xbmcgui.getCurrentWindowDialogId()
		if id is None: return result
		else: return result == id

	@classmethod
	def currentDialogInstance(self):
		# Do not use WindowDialog, since it seems that functions like getControl() does not work with it.
		#return xbmcgui.WindowDialog(self.currentDialog())
		return xbmcgui.Window(self.currentDialog())

	@classmethod
	def currentType(self, type = None):
		try:
			result = self.currentDialogInstance().getProperty(Window.PropertyType)
			if type is None:
				if result == '': return None
				else: return result
			else:
				try: type = type.__name__
				except: pass
				return result == type
		except: return None

	@classmethod
	def currentKodi(self, loader = True):
		id = self.currentDialog()
		if not loader and (id == interface.Dialog.IdDialogBusy or id == interface.Dialog.IdDialogBusyNoCancel): return False
		else: return id >= Window.IdMinimum and id < Window.IdMaximum

	@classmethod
	def currentGaia(self):
		return not self.currentType() is None

	@classmethod
	def currentTraktAuthentication(self):
		# Checks if the current window is the rating dialog of sscript.trakt.
		# Checking the controls seems to be the only way this can be achieved.

		if self.currentDialog() <= Window.IdMaximum: return False
		instance = self.currentDialogInstance()
		if not instance: return False

		controls = {
			203 : xbmcgui.ControlLabel,
			204 : xbmcgui.ControlLabel,
			205 : xbmcgui.ControlLabel,
			201 : xbmcgui.ControlButton,
			202 : xbmcgui.ControlButton,
		}

		for id, type in controls.items():
			try:
				if not tools.Tools.isInstance(instance.getControl(id), type): return False
			except: return False
		return True

	@classmethod
	def currentTraktRating(self):
		# Checks if the current window is the rating dialog of sscript.trakt.
		# Checking the controls seems to be the only way this can be achieved.

		if self.currentDialog() <= Window.IdMaximum: return False
		instance = self.currentDialogInstance()
		if not instance: return False

		controls = {
			10011 : xbmcgui.ControlLabel,
			10012 : xbmcgui.ControlLabel,
			10015 : xbmcgui.ControlGroup,
			11030 : xbmcgui.ControlButton,
			11031 : xbmcgui.ControlButton,
			11032 : xbmcgui.ControlButton,
			11033 : xbmcgui.ControlButton,
			11034 : xbmcgui.ControlButton,
			11035 : xbmcgui.ControlButton,
			11036 : xbmcgui.ControlButton,
			11037 : xbmcgui.ControlButton,
			11038 : xbmcgui.ControlButton,
			11039 : xbmcgui.ControlButton,
		}

		for id, type in controls.items():
			try:
				if not tools.Tools.isInstance(instance.getControl(id), type): return False
			except: return False
		return True

	@classmethod
	def visible(self, id = None):
		try:
			if id is None: return self._instance().mWindow.visible()
			else: return self.visibleWindow(id) or self.visibleDialog(id)
		except: return False

	@classmethod
	def visibleWindow(self, id):
		return self.currentWindow() == id

	@classmethod
	def visibleDialog(self, id):
		return self.currentDialog() == id

	@classmethod
	def visibleCustom(self, id = None):
		return self.currentWindow() >= Window.IdMaximum or self.currentDialog() >= Window.IdMaximum

	@classmethod
	def closed(self):
		try: return self._instance().mWindow.closed()
		except: return True

	@classmethod
	def _separator(self, values):
		return self.separator(values, color = self._colorSeparator(), bold = False)

	@classmethod
	def _highlight(self, value):
		return interface.Format.fontColor(str(value), self._colorHighlight())

	@classmethod
	def separator(self, items = None, bold = True, color = None):
		separator = interface.Format.iconSeparator(pad = '  ')
		if bold:
			separator = interface.Format.font(separator, bold = True, translate = False)
		if color:
			if color == True: color = self._colorDiffuse()
			separator = interface.Format.font(separator, color = color, translate = False)
		if items: return separator.join([i for i in items if not i is None and not i == ''])
		else: return separator

	@classmethod
	def focus(self, control = IdListControl, sleep = True):
		try:
			if tools.Tools.isInteger(control): result = self._instance().mWindow.setFocusId(control)
			else: result = self._instance().mWindow.setFocus(control)
			if sleep: tools.Time.sleep(0.01) # Otherwise the control is not yet focused when later code requires the focus somehow (eg: opening the context menu).
			return result
		except: pass

	@classmethod
	def itemClear(self, control = IdListControl):
		try: return self._instance().control(control).reset()
		except: pass

	@classmethod
	def itemAdd(self, item, context = None, control = IdListControl):
		try:
			instance = self._instance()
			if instance and item:
				if tools.Tools.isArray(item):
					if context: instance.mContexts.extend(context)
					instance.mItems.extend(item)
					return instance.control(control).addItems([i['item'] for i in item] if tools.Tools.isDictionary(item[0]) else item)
				else:
					if context: instance.mContexts.append(context)
					instance.mItems.append(item)
					return instance.control(control).addItem(item['item'] if tools.Tools.isDictionary(item) else item)
		except: tools.Logger.error()

	@classmethod
	def itemSelect(self, index, control = IdListControl):
		try: return self._instance().control(control).selectItem(index)
		except: pass

	@classmethod
	def itemSelected(self, control = IdListControl, index = True):
		if index:
			try: return self._instance().control(control).getSelectedPosition()
			except: pass
		else:
			try: return self._instance().control(control).getSelectedItem()
			except: pass

	@classmethod
	def property(self, property, id = None):
		try:
			if id is None: return self._instance().mWindow.getProperty(property)
			else: return xbmcgui.Window(id).getProperty(property)
		except: pass

	@classmethod
	def propertyClear(self, property, id = None):
		try:
			if id is None: return self._instance().mWindow.clearProperty(property)
			else: return xbmcgui.Window(id).clearProperty(property)
		except: pass

	@classmethod
	def propertySet(self, property, value, id = None):
		try:
			if tools.Tools.isStructure(value):
				value = tools.Converter.jsonTo(value)
			else:
				if value is None: value = ''
				elif tools.Tools.isBoolean(value): value = int(value)
				value = str(value)
			if id is None: return self._instance().mWindow.setProperty(property, value)
			else: return xbmcgui.Window(id).setProperty(property, value)
		except: pass

	@classmethod
	def propertyGlobal(self, property):
		return self.property(property = property, id = Window.IdWindowHome)

	@classmethod
	def propertyGlobalClear(self, property):
		return self.propertyClear(property = property, id = Window.IdWindowHome)

	@classmethod
	def propertyGlobalSet(self, property, value):
		return self.propertySet(property = property, value = value, id = Window.IdWindowHome)

	def control(self, id):
		try: return self.mWindow.getControl(id)
		except: return None

	def _window(self):
		return self.mWindow

	@classmethod
	def _theme(self):
		theme = Theme.skin()
		theme = theme.replace(' ', '').lower()
		index = theme.find('(')
		if index >= 0: theme = theme[:index]
		return theme

	@classmethod
	def _pathTemplate(self):
		return tools.File.joinPath(tools.System.pathResources(), 'resources', 'skins', 'default', '720p')

	@classmethod
	def _pathWindow(self, kodi = False):
		path = tools.File.joinPath(tools.System.profile(), 'Windows')
		if kodi: path = tools.File.joinPath(path, 'resources', 'skins', 'default', '720p')
		return path

	@classmethod
	def _pathInterface(self):
		return tools.File.joinPath(tools.System.pathResources(), 'resources', 'media', 'interface')

	@classmethod
	def _pathSkin(self):
		theme = self._theme()
		addon = tools.System.pathResources() if theme == 'default' or 'gaia1' in theme else tools.System.pathSkins()
		return tools.File.joinPath(addon, 'resources', 'media', 'skins', theme)

	@classmethod
	def _pathImage(self, image, interface = True):
		if tools.Tools.isArray(image): image = tools.File.joinPath(*image)
		if not '.' in image: image += '.png'
		path = tools.File.joinPath(self._pathSkin(), 'interface' if interface else '', image)
		if not tools.File.exists(path): path = tools.File.joinPath(self._pathInterface(), image)
		return path

	@classmethod
	def _pathIcon(self, icon, quality = None, type = None, special = interface.Icon.SpecialNone):
		if not '.' in icon: icon += '.png'
		return interface.Icon.path(icon, type = type if type else interface.Icon.themeIcon(), quality = quality, special = special)

	@classmethod
	def _pathLogo(self, size = SizeLarge):
		return tools.File.joinPath(tools.System.pathResources(), 'resources', 'media', 'logo', size)

	@classmethod
	def _background(self, type = None, path = None):
		result = []

		if type == Window.BackgroundFanart or type == Window.BackgroundCombined:
			result.append({'path' : path if path else self._pathImage('background.jpg', interface = False), 'color' : Window.BackgroundColorOpaque})
		elif type == Window.BackgroundSkin:
			result.append({'path' : self._pathImage('background.jpg', interface = False), 'color' : Window.BackgroundColorOpaque})

		if type == Window.BackgroundCombined:
			result.append({'path' : self._pathImage('background.jpg', interface = False), 'color' : Window.BackgroundColor3})
		else:
			if result and tools.System.GaiaResources in result[0]['path']: color = Window.BackgroundColor2
			else: color = Window.BackgroundColor1
			result.append({'path' : self._pathImage('pixel.png'), 'color' : color})

		return result

	def _scaleWidth(self, value):
		return int(self.mScaleWidth * value)

	def _scaleHeight(self, value):
		return int(self.mScaleHeight * value)

	def _scale(self, controls, width = None):
		middleOld = 0
		middleNew = 0
		offsetOld = 0
		if width:
			middleOld = self.mWidth / 2.0
			middleNew = self._scaleWidth(middleOld)
			offsetOld = (width - self._scaleWidth(width)) / 2.0

		for id in controls:
			if tools.Tools.isInteger(id): control = self.control(id)
			else: control = id
			widthOld = control.getWidth()
			widthNew = self._scaleWidth(widthOld)
			control.setWidth(widthNew)

			xOld = control.getX()
			xNew = xOld - int((widthNew - widthOld) / 2.0)

			# Reposition controls in scaled windows.
			# Controls on the left-side of the screen should be pushed towards the middle (in the right direction).
			# Controls on the right-side of the screen should be pushed towards the middle (in the left direction).
			offsetNew = offsetOld
			if width: # NB: This does NOT work perfectly.
				if xOld > middleOld:
					offsetNew *= -1 * (((xNew + (1.5 * widthOld)) / middleNew) - 1)
				else:
					offsetNew *= 1 - (xNew / middleNew)
					if xOld + widthOld > middleOld: offsetNew -= (widthOld - widthNew) / 2.5 # Wide items crossing from the left-side over the middle to the right-side.
					else: offsetNew -= (widthOld - widthNew) / 4.0 # Narrow items not crossing over the middle to the right-side.

				offsetNew = int(offsetNew + (offsetOld / 2.0))

			control.setPosition(xNew + int(offsetNew), control.getY())

	def _centerX(self, width = 0):
		return int((self.mWidth - width) / 2.0)

	def _centerY(self, height = 0):
		return int((self.mHeight - height) / 2.0)

	def _offsetX(self):
		return self.mDimensionX + self.mDimensionWidth

	def _offsetY(self):
		return self.mDimensionY + self.mDimensionHeight

	def _dimensionSeparator(self, width = None):
		if width is None: width = Window.SeparatorLineWidth
		elif width is True: width = Window.SeparatorLineWide
		return [width, Window.SeparatorLineHeight + Window.SeparatorLinePadding]

	def _dimensionButton(self, text = None, icon = None):
		return [(len(self._buttonText(text = text, icon = icon)) * 14) if text else self._scaleWidth(250), self._scaleHeight(50)]

	def _buttonText(self, text, icon = None):
		text = interface.Translation.string(text)
		if not icon is None: text = '       ' + text
		return text

	def _remove(self, controls = None, force = False):
		try:
			if controls is None:
				result = []
				remove = []
				for control in self.mControls[::-1]: # Iterate reverse, because there is a delay.
					if force or not control['fixed']: control['control'].setVisible(False)
				for control in self.mControls[::-1]: # Iterate reverse, because there is a delay.
					if not force and control['fixed']: result.append(control)
					else: remove.append(control['control'])
				self.mWindow.removeControls(remove)
				for control in remove: del control

				# Calling "del" on the controls above only reduces the reference counter, but does not delete it if there are still other refrences.
				# This causes Kodi to show error messages: "... has left several classes in memory that we couldn't clean up".
				# Remove to individual instance member variables (eg: mStatusControl), dictionaries (eg: mLabels), and lists (eg: mProgressInner).
				for i in range(len(self.mLabels)):
					if self.mLabels[i]['control'] in remove:
						self.mLabels[i]['control'] = None
				for name in vars(self).keys():
					variable = self.__dict__[name]
					if tools.Tools.isDictionary(variable):
						for key, value in variable.items():
							if value in remove:
								variable[key] = None
					elif tools.Tools.isArray(variable):

						for i in range(len(variable)):
							if variable[i] in remove:
								variable[i] = None
					elif variable in remove:
						self.__dict__[name] = None

				self.mControls = result
			else:
				if tools.Tools.isArray(controls): self.mWindow.removeControls(controls)
				else: self.mWindow.removeControl(controls)
				for control in controls: del control
		except: pass

	def _add(self, control, fixed = False, visible = True, animation = None, lock = False, initialize = False):
		# Adding controls individually to the window is slow, especially the progress bar icons.
		# Instead of adding each control individually, we queue them and add them all at once in _initializeControls() using window.addControls(...) which is a lot faster.
		# We also do not need locking here, which would also makes things slower, sincee append/extend on lists is thread safe.

		if lock: self._lock()
		if tools.Tools.isArray(control):
			self.mControls.extend([{
				'control' : c,
				'fixed' : fixed,
				'initialized' : initialize,
				'visible' : visible,
				'animation' : animation,
			} for c in control])
			if initialize: self.mWindow.addControls(control)
		else:
			self.mControls.append({
				'control' : control,
				'fixed' : fixed,
				'initialized' : initialize,
				'visible' : visible,
				'animation' : animation,
			})
			if initialize: self.mWindow.addControl(control)
		if lock: self._unlock()
		return control

	def _get(self, control):
		try: control = control[0].getId()
		except:
			try: control = control.getId()
			except: pass

		for i in self.mControls:
			if i['control'].getId() == control:
				return i

		return None

	def _components(self, control, components):
		for i in self.mControls:
			if i['control'] == control:
				i['components'] = components
				break

	@classmethod
	def _visible(self, control):
		try:
			if control:
				if tools.Tools.isArray(control):
					for i in control:
						try:
							if i.isVisible(): return True
						except: pass
				else:
					if control.isVisible(): return True
		except: tools.Logger.error()
		return False

	@classmethod
	def _visibleSet(self, control, visible = True):
		if tools.Tools.isDictionary(control):
			for i in control.items():
				self._visibleSet(control = i, visible = visible)
		elif tools.Tools.isArray(control):
			for i in control:
				self._visibleSet(control = i, visible = visible)
		else:
			try: control.setVisible(visible)
			except: pass

	def _addImage(self, path, x, y, width, height, ratio = RatioDefault, color = None, fixed = False, visible = True, animation = None):
		image = xbmcgui.ControlImage(x, y, width, height, path, ratio)
		if color: image.setColorDiffuse(color)
		self._add(control = image, fixed = fixed, visible = visible, animation = animation)
		return image

	def _addBackground(self, type = BackgroundCombined, path = None, fixed = False):
		if not type is None:
			images = self._background(type = type, path = path)
			ratio = Window.RatioDefault if self.mWidth == Window.SizeWidth and self.mHeight == Window.SizeHeight else Window.RatioScaleUp
			for image in images:
				self._addImage(path = image['path'], color = image['color'], x = 0, y = 0, width = self.mWidth, height = self.mHeight, ratio = ratio, fixed = fixed)

	def _addCurtains(self):
		if tools.Settings.getInteger('interface.scrape.interface') == 3 and tools.Settings.getBoolean('interface.scrape.interface.curtains'):
			path = tools.File.joinPath(tools.System.pathResources(), 'resources', 'media', 'cinema', 'curtains.png')
			return self._addImage(path = path, x = 0, y = 0, width = self.mWidth, height = self.mHeight)
		return None

	def _addButton(self, text = None, x = None, y = None, width = None, height = None, callback = None, icon = None, iconSize = None, select = SelectNone, highlight = None, bold = True, uppercase = True, alignment = AlignmentCenter, size = None, visible = True, type = ButtonMedium):
		dimension = self._dimensionButton(text = text, icon = icon)
		if width is None: width = dimension[0]
		if height is None: height = dimension[1]

		if size is None: size = interface.Font.fontLarge()

		if text:
			text = self._buttonText(text = text, icon = icon)
			if alignment in [Window.AlignmentLeftCenter, Window.AlignmentLeft]: text = '  ' + text
		else:
			text = ''

		components = {}

		pathNormal = self._pathImage(['button', type, 'unfocused'])
		pathFocus = self._pathImage(['button', type, 'focused'])

		control = self._add(xbmcgui.ControlButton(x, y, width, height, interface.Format.font(text, bold = bold, uppercase = uppercase), focusTexture = pathFocus, noFocusTexture = pathNormal, alignment = alignment, textColor = Window._colorDefault(), font = size), visible = visible)

		if not icon is None:
			sizeIcon = int(height * 0.8 * (iconSize if iconSize else 1))
			iconX = int(x + (width * 0.1))
			iconY = int(y + ((height - sizeIcon) / 2.0))
			controlIcon = self._addImage(path = self._pathIcon(icon = icon, quality = interface.Icon.QualityMini), x = iconX, y = iconY, width = sizeIcon, height = sizeIcon, visible = visible)
			components['icon'] = controlIcon
		else:
			controlIcon = None

		if highlight:
			if highlight is True: highlight = self._colorHighlight()
			controlHighlight = self._addImage(path = self._pathImage(['button', type, 'highlight']), x = x + 2, y = y + 2, width = width - 4, height = height - 4, visible = visible, color = highlight)
			components['highlight'] = controlHighlight
			components['animation'] = [('Conditional', 'effect=fade start=100 end=0 time=1000 pulse=true tween=linear condition=String.IsEqual(Window.Property(%s),true)' % Window.PropertyAnimation)]
		else:
			controlHighlight = None

		if not select is Window.SelectNone:
			sizeIcon = 32
			iconX = int(x - (sizeIcon / 3))
			iconY = int(y - (sizeIcon / 3))
			controlSelect = self._addImage(path = self._pathImage(['button', 'select', 'selected' if select == Window.SelectYes else 'unselected' if select == Window.SelectNo else '']), x = iconX, y = iconY, width = sizeIcon, height = sizeIcon, visible = visible)
			components['select'] = controlSelect
		else:
			controlSelect = None

		if components: self._components(control = control, components = components)

		if callback:
			def wrapper(control):
				try: callback(control = self._get(control = control))
				except: callback()
			self.mWindow._onControl(x, y, wrapper)

		return [control, controlIcon, controlSelect, controlHighlight]

	def _setButton(self, control, text = None, icon = None, highlight = None, bold = True, uppercase = True, size = None):
		# From _initializeAnimations().
		if tools.Tools.isDictionary(control):
			temp = [None, None, None, None]
			if 'control' in control: temp[0] = control['control']
			if 'components' in control:
				if 'icon' in control['components']: temp[1] = control['components']['icon']
				if 'select' in control['components']: temp[2] = control['components']['select']
				if 'highlight' in control['components']: temp[3] = control['components']['highlight']
			control = temp

		if text:
			if size is None: size = interface.Font.fontLarge()
			control[0].setLabel(interface.Format.font(self._buttonText(text = text, icon = icon), bold = bold, uppercase = uppercase), font = size)
			dimension = self._dimensionButton(text = text, icon = icon)
			control[0].setWidth(dimension[0])
		if icon and control[1]: control[1].setImage(self._pathIcon(icon = icon, quality = interface.Icon.QualityMini))
		if not highlight is None and control[3]: control[3].setVisible(highlight)

	def _selectButton(self, control, select = SelectYes):
		if tools.Tools.isArray(control): control = control[2]
		control.setImage(self._pathImage(['button', 'select', 'selected' if select == Window.SelectYes else 'unselected' if select == Window.SelectNo else '']))

	def _addSeparator(self, x = None, y = None, width = None, control = False):
		dimension = self._dimensionSeparator(width = width)
		height = self._scaleHeight(Window.SeparatorLineHeight)
		if x is None: x = self._centerX(dimension[0])
		if y is None: y = self._offsetY() + int((dimension[1] - height) / 2.0)
		image = self._addImage(self._pathImage('separator'), x = x, y = y, width = dimension[0], height = height)
		if control: return (image, dimension)
		else: return dimension

	def _addLabel(self, text, x, y, width, height, color = None, size = None, alignment = AlignmentLeft, bold = False, italic = False, light = False, uppercase = False, lowercase = False, capitalcase = False, animation = None):
		# NB: Fix suggested by NG.
		# Sometimes when the special window is closed, the text of the lables remain afterwards. The text is then shown in various places of the current Kodi native window and remain there until Kodi is restarted.
		# Create the label control, but only set the label text AFTER the window has been created.
		if color is None: color = self._colorDefault()
		if size is None: size = interface.Font.fontDefault()
		control = self._add(xbmcgui.ControlLabel(x, y, width, height, '', font = size, textColor = color, alignment = alignment), animation = animation)
		self.mLabels.append({'control' : control, 'text' : interface.Translation.string(text) if tools.Tools.isInteger(text) else text, 'color' : color, 'size' : size, 'bold' : bold, 'italic' : italic, 'light' : light, 'uppercase' : uppercase, 'lowercase' : lowercase, 'capitalcase' : capitalcase})
		return control

	def _setLabel(self, control, text, color = None, size = None, bold = False, italic = False, light = False, uppercase = False, lowercase = False, capitalcase = False, translate = False):
		if control: # Sometimes the control gets deleted during window close, while progress updates are called which updates the label with a now-deleted control.
			if color is None: color = self._colorDefault()
			if size is None: size = interface.Font.fontDefault()
			control.setLabel(interface.Format.font(text, bold = bold, italic = italic, light = light, uppercase = uppercase, lowercase = lowercase, capitalcase = capitalcase, translate = translate), font = size, textColor = color)

class WindowBackground(Window):

	def __init__(self, backgroundType, backgroundPath, observeWindow = None, observeDialog = None):
		super(WindowBackground, self).__init__(backgroundType = backgroundType, backgroundPath = backgroundPath)
		if observeWindow or observeDialog: Pool.thread(self._observe, kwargs = {'window' : observeWindow, 'dialog' : observeDialog}, start = True)

	# observeWindow/observeDialog: only show the background while a specific window/dialog is visible.
	@classmethod
	def show(self, background = None, backgroundType = None, wait = False, initialize = True, close = False, observeWindow = None, observeDialog = None):
		return super(WindowBackground, self)._show(backgroundType = tools.Settings.getInteger('interface.stream.interface.background') if backgroundType is None else backgroundType, backgroundPath = background, wait = wait, initialize = initialize, close = close, observeWindow = observeWindow, observeDialog = observeDialog)

	@classmethod
	def _observe(self, window = None, dialog = None):
		id = None
		function = None
		if window:
			id = window
			function = self.currentWindow
		elif dialog:
			id = dialog
			function = self.currentDialog
		else:
			return

		# Wait for the window to show.
		for i in range(50): # 5 seconds.
			if function() == id: break
			tools.Time.sleep(0.1)

		# Wait for the window to close.
		while self.visible() and not tools.System.aborted():
			if not function() == id: break
			tools.Time.sleep(0.1)

		self.close()

class WindowCinema(Window):

	LogoWidth = 300
	LogoHeight = 218

	def __init__(self, backgroundType, backgroundPath):
		super(WindowCinema, self).__init__(backgroundType = backgroundType, backgroundPath = backgroundPath)

	@classmethod
	def show(self, background = None, wait = False, initialize = True, close = False):
		return super(WindowCinema, self)._show(backgroundType = tools.Settings.getInteger('interface.scrape.interface.background'), backgroundPath = background, wait = wait, initialize = initialize, close = close)

	def _initializeStart1(self):
		super(WindowCinema, self)._initializeStart1()

	def _initializeStart2(self):
		super(WindowCinema, self)._initializeStart2()
		self._addCurtains()
		loader = tools.Settings.getInteger('interface.scrape.interface.loader')
		if loader >= 2: self._addLogo(name = loader == 3)

	def _addLogo(self, name = False):
		if name:
			width = self._scaleWidth(WindowCinema.LogoWidth)
			height = self._scaleHeight(WindowCinema.LogoHeight)
			path = tools.File.joinPath(tools.System.pathResources(), 'resources', 'media', 'cinema', 'logo.png')
			self._addImage(path = path, x = self._centerX(width), y = self._centerY(height), width = width, height = height)
		else:
			width = self._scaleWidth(128)
			height = self._scaleHeight(128)
			path = tools.File.joinPath(tools.System.pathResources(), 'resources', 'media', 'logo', 'small', 'iconcolor.png')
			self._addImage(path = path, x = self._centerX(width), y = self._centerY(height), width = width, height = height)

class WindowQr(Window):

	LogoWidth = 300
	LogoHeight = 218

	IdImageBorder = 50011
	IdImageBackground = 50012
	IdImageOverlay = 50013
	IdImageSeparator1 = 50014
	IdImageSeparator2 = 50015
	IdImageLogo = 50016

	IdButtonColor = 50101
	IdButtonDetails = 50102
	IdButtonClose = 50103
	IdButtonCopy = 50104
	IdButtonBrowser = 50105

	IdLabelDescription = 52001
	IdLabelName = 52002
	IdLabelData1 = 52101
	IdLabelData2 = 52102
	IdLabelData3 = 52201
	IdLabelData4 = 52202
	IdLabelData5 = 52301
	IdLabelData6 = 52302
	IdLabelCode1 = 52401
	IdLabelCode2 = 52402

	IdQrCode = 51001
	IdQrBorder = 51002
	IdQrCircle = 51003
	IdQrIcon1 = 51004
	IdQrIcon2 = 51005
	IdQrButton = 51006

	def __init__(self, qr, thread, data, link = None, code = None, name = None, hash = None, wallet = None, payment = None, symbol = None, description = None, donations = None, icon = None, color = None, permanent = False, overlay = True, **kwargs):
		super(WindowQr, self).__init__(xml = 'qr', **kwargs)
		self.mQrColor = qr['path']
		self.mQrPlain = None
		self.mQrMode = True
		self.mQrChanged = False
		self.mQrThread = thread
		self.mQrTruncated = qr['truncated']
		self.mQrPermanent = permanent

		self.mData = data
		self.mDataPlain = wallet if wallet else data

		self.mLink = link
		self.mCode = code
		self.mName = name
		self.mHash = hash
		self.mWallet = wallet
		self.mPayment = payment
		self.mDescription = description
		self.mDonations = donations
		self.mColor = color

		self.mIcon = None
		if icon:
			icon = tools.Tools.copy(icon)
			if tools.Tools.isString(icon):
				if '.' in icon: self.mIcon = {'path' : icon}
				else: self.mIcon = {'icon' : icon}
			elif tools.Tools.isDictionary(icon):
				self.mIcon = icon
			if 'icon' in self.mIcon and not 'path' in self.mIcon: self.mIcon['path'] = self._pathIcon(icon = self.mIcon['icon'], quality = interface.Icon.QualitySmall, special = interface.Icon.SpecialServices)

		from lib.modules.network import Networker
		if self.mLink and Networker.linkIs(link = self.mLink, magnet = False): self.mLabel = 33381
		elif self.mLink and Networker.linkIs(link = self.mLink, magnet = True): self.mLabel = 35076
		elif self.mWallet: self.mLabel = 33507
		elif self.mName: self.mLabel = 35724
		elif self.mHash: self.mLabel = 35725
		else: self.mLabel = 36264

		self.mOverlay = overlay

		self.mOptions = []
		options = [
			{'value' : self.mLink, 'label' : 33381},
			{'value' : self.mCode, 'label' : 33206},
			{'value' : self.mWallet, 'label' : 33507},
			{'value' : self.mPayment, 'label' : 36269},
			{'value' : self.mName, 'label' : 33390},
			{'value' : self.mHash, 'label' : 36274},
		]
		limit = 65
		for option in options:
			if option['value']:
				option['copy'] = '%s %s' % (interface.Translation.string(36271), interface.Format.bold(option['label']))
				option['split'] = interface.Format.newline().join([option['value'][i : i + limit] for i in range(0, len(option['value']), limit)]) # Text dialog does not scroll long labels. Split over multiple lines.
				self.mOptions.append(option)

		self.mNavigationIndex = None
		self.mNavigationButtons = []

	@classmethod
	def show(self, data = None, link = None, code = None, name = None, hash = None, wallet = None, payment = None, symbol = None, description = None, donations = None, icon = None, color = None, copy = True, permanent = False, overlay = True, wait = False, **kwargs):
		interface.Loader.show()
		colorQr = color

		if donations:
			donations = tools.Tools.copy(donations)
			donation = self._donation(id = symbol if symbol else name, donations = donations)
			if donation:
				donation['selected'] = True
				from lib.modules.network import Networker
				if not symbol: symbol = donation['symbol']
				if not color: color = colorQr = donation['color']
				if not icon:
					icon = self._pathIcon(icon = donation['symbol'], quality = interface.Icon.QualitySmall, special = interface.Icon.SpecialDonations)
					if not tools.File.exists(icon): icon = self._pathIcon(icon = 'donations', quality = interface.Icon.QualitySmall, special = interface.Icon.SpecialDonations)
				if not link and Networker.linkIs(donation['address']): wallet = link = donation['address']
				elif not wallet: wallet = donation['address']
				if not payment: payment = donation['payment']
				if not donation['type'] == 'crypto': # Otherwise multiple options are shown when copying to clipboard.
					wallet = None
					payment = None

		if symbol == 'gaia':
			colorQr = True
			color = None
			 # Use a special logo, since it has the exact resolution (no resampling needed) and many of the transparent pixels were removed to reduce the black-ish resampling borders.
			icon = tools.File.joinPath(self._pathLogo(Window.SizeMini), 'iconqr.png')
		elif symbol in ['pp', 'tvdb', 'tmdb', 'imdb']:
			icon = {'path' : icon, 'small' : True}

		if hash: hash = hash.upper()

		if data is None:
			if payment: data = payment
			elif wallet: data = wallet
			elif link: data = link
			elif name: data = name
			elif hash: data = hash

		if copy:
			from lib.modules.clipboard import Clipboard
			if copy is True:
				if code: copy = code
				elif wallet: copy = wallet
				elif link: copy = link
				elif name: copy = name
				elif hash: copy = hash
			Clipboard.copy(value = copy, notify = False)

		colorQr = colorQr if colorQr is True else [interface.Format.colorDarker(color = colorQr, change = 70), colorQr] if colorQr else None
		qr = self._qrGenerate(data = data, color = colorQr, loaderHide = False, permanent = permanent)
		thread = Pool.thread(target = self._qrGeneratePlain, kwargs = {'data' : data, 'loaderShow' : False, 'loaderHide' : False, 'permanent' : permanent}, start = True)

		super(WindowQr, self)._show(qr = qr, thread = thread, data = data, link = link, code = code, name = name, hash = hash, wallet = wallet, payment = payment, symbol = symbol, description = description, donations = donations, icon = icon, color = color, permanent = permanent, overlay = overlay, wait = wait, **kwargs)
		return self._instance()

	def _initializeEnd1(self):
		super(WindowQr, self)._initializeEnd1()

		from lib.modules.network import Networker

	 	# Resize for  wide screens.
		controls = [
			WindowQr.IdImageBorder,
			WindowQr.IdImageBackground,
			WindowQr.IdImageOverlay,
			WindowQr.IdImageSeparator1,
			WindowQr.IdImageSeparator2,
			WindowQr.IdImageLogo,

			WindowQr.IdLabelDescription,
			WindowQr.IdLabelName,
			WindowQr.IdLabelData1,
			WindowQr.IdLabelData2,
			WindowQr.IdLabelData3,
			WindowQr.IdLabelData4,
			WindowQr.IdLabelData5,
			WindowQr.IdLabelData6,
			WindowQr.IdLabelCode1,
			WindowQr.IdLabelCode2,

			WindowQr.IdQrCode,
			WindowQr.IdQrBorder,
			WindowQr.IdQrCircle,
			WindowQr.IdQrIcon1,
			WindowQr.IdQrIcon2,
			WindowQr.IdQrButton,
		]
		self._scale(controls)

		dialogWidth = self._scaleWidth(400)
		dialogCenter = self._centerX(0)

		buttonColor = self.control(WindowQr.IdButtonColor)
		buttonDetails = self.control(WindowQr.IdButtonDetails)
		buttonClose = self.control(WindowQr.IdButtonClose)
		buttonCopy = self.control(WindowQr.IdButtonCopy)
		buttonBrowser = self.control(WindowQr.IdButtonBrowser)
		self.mNavigationButtons = [buttonColor, buttonDetails, buttonClose, buttonCopy, buttonBrowser]
		self._scale(self.mNavigationButtons)

		buttonOffset = self._scaleWidth(30)
		buttonWidth = buttonColor.getWidth() + self._scaleWidth(6)
		buttonStart = int(dialogCenter - (dialogWidth / 2.0) + buttonOffset)
		buttonColor.setPosition(buttonStart, buttonColor.getY())
		buttonDetails.setPosition(buttonStart + buttonWidth, buttonDetails.getY())
		buttonClose.setPosition(buttonStart + (buttonWidth * 2), buttonClose.getY())
		buttonCopy.setPosition(buttonStart + (buttonWidth * 3), buttonCopy.getY())
		buttonBrowser.setPosition(buttonStart + (buttonWidth * 4), buttonBrowser.getY())

		self._onClick(self.control(WindowQr.IdQrButton), self._actionColor)

		self._onClick(buttonColor, self._actionColor)
		self._onClick(buttonDetails, self._actionDetails)
		self._onClick(buttonBrowser, self._actionBrowser)
		self._onClick(buttonCopy, self._actionCopy)
		self._onClick(buttonClose, self.close)

		self._onAction(WindowBase.ActionMoveLeft, self._actionFocus)
		self._onAction(WindowBase.ActionMoveRight, self._actionFocus)
		self._onAction(WindowBase.ActionMoveUp, self._actionFocus)
		self._onAction(WindowBase.ActionMoveDown, self._actionFocus)
		self._actionFocus()

		colorPrimary = interface.Format.colorPrimary()
		colorSecondary = interface.Format.colorSecondary()
		color = self.mColor if self.mColor else colorPrimary

		if self.mColor:
			colorBorder = interface.Format.colorDarker(color = self.mColor, change = 50)
		else:
			colorBorder = interface.Format.colorGradient(colorSecondary, colorPrimary, count = 10)
			colorBorder = colorBorder[3]

		if self.mDonations:
			paypal = self._donationName(id = 'paypal', donations = self.mDonations, enabled = True)
			bitcoin = self._donationName(id = 'bitcoin', donations = self.mDonations, enabled = True)
			ethereum = self._donationName(id = 'ethereum', donations = self.mDonations, enabled = True)

		logo = tools.File.joinPath(self._pathLogo(Window.SizeSmall), 'iconcolor.png')
		self.propertySet('GaiaLogo', logo)
		if self.mIcon:
			if 'small' in self.mIcon and self.mIcon['small']: self.propertySet('GaiaIconSmall', self.mIcon['path'])
			else: self.propertySet('GaiaIconLarge', self.mIcon['path'])
		else:
			self.propertySet('GaiaIconLarge', logo)
		self.propertySet('GaiaBackground', self._pathImage('background.jpg', interface = False))
		self.propertySet('GaiaColor', colorBorder)
		self.propertySet('GaiaColorButton', colorPrimary)
		self.propertySet('GaiaOverlay', int(self.mOverlay))

		label = self.mDescription
		if label is None:
			if self.mCode: label = 36257
			elif self.mLink and Networker.linkIs(link = self.mLink, magnet = False): label = 36258
			elif self.mLink and Networker.linkIs(link = self.mLink, magnet = True): label = 36259
			elif self.mWallet:
				if paypal: label = interface.Translation.string(36262) % (paypal, bitcoin, ethereum)
				else: label = interface.Translation.string(36263) % (bitcoin, ethereum)
			elif self.mName: label = 36260
			elif self.mHash: label = 36275
			elif self.mData: label = 36261
		if label: self.propertySet('GaiaDescription', interface.Format.font(label, bold = True, color = interface.Format.ColorWhite)) # Set white, because some skins (eg: Arctic Horizon) have a dark color as default.

		if self.mWallet:
			label = [self._donationName(donations = self.mDonations), self._donationSymbol(donations = self.mDonations)]
			label = interface.Format.iconJoin([i for i in label if i])
			self.propertySet('GaiaNameValue', interface.Format.font(label, bold = True, color = color))

		if label: self.propertySet('GaiaDataLabel', interface.Format.font(self.mLabel, bold = True, color = colorPrimary))
		self.propertySet('GaiaDataValue', interface.Format.font(self.mDataPlain, bold = True, color = interface.Format.ColorWhite))

		if self.mCode:
			self.propertySet('GaiaCodeLabel', interface.Format.font(33206, bold = True, color = colorPrimary))
			self.propertySet('GaiaCodeValue', interface.Format.font(self.mCode, bold = True, color = interface.Format.ColorWhite))

		self._actionColor(initial = True)
		self.propertySet('GaiaInitialized', 1)

		if self.mQrTruncated:
			interface.Dialog.notification(title = 36272, message = 36273, icon = interface.Dialog.IconInformation)
			Pool.thread(target = self._actionColor, kwargs = {'delay' : True}, start = True) # Automatically switch to the plain QR code after some time for large data.

	def _initializeEnd2(self):
		super(WindowQr, self)._initializeEnd2()
		interface.Loader.hide()

	def _actionFocus(self, action = None):
		maximum = len(self.mNavigationButtons) - 1

		if self.mNavigationIndex is None: self.mNavigationIndex = int(maximum / 2.0)
		elif action == WindowBase.ActionMoveLeft or action == WindowBase.ActionMoveUp: self.mNavigationIndex -= 1
		elif action == WindowBase.ActionMoveRight or action == WindowBase.ActionMoveDown: self.mNavigationIndex += 1

		if self.mNavigationIndex < 0: self.mNavigationIndex = maximum
		elif self.mNavigationIndex > maximum: self.mNavigationIndex = 0

		self.focus(self.mNavigationButtons[self.mNavigationIndex])

	def _actionColor(self, initial = False, delay = False):
		if delay:
			tools.Time.sleep(20)
			if self.mQrChanged: return

		if self.mQrMode:
			path = self.mQrColor
			plain = 0
		else:
			try: self.mQrThread.join()
			except: pass
			self.mQrPlain = self._qrGeneratePlain(data = self.mData, permanent = self.mQrPermanent)['path']
			path = self.mQrPlain
			plain = 1

		self.propertySet('GaiaQr', path)
		self.propertySet('GaiaPlain', plain)
		self.mQrMode = not self.mQrMode
		if not initial: self.mQrChanged = True

	def _actionDetails(self):
		items = []
		for option in self.mOptions:
			items.append({'type' : 'title', 'value' : option['label'], 'break' : 1})
			items.append({'type' : 'text', 'value' : option['split'], 'break' : 2})
		items.append({'type' : 'break', 'break' : 2})
		interface.Dialog.details(title = 33379, items = items)

	def _actionBrowser(self):
		from lib.modules.network import Networker
		Networker.linkOpen(link = self.mData, label = self.mLabel)

	def _actionCopy(self):
		choice = 0
		if len(self.mOptions) == 2:
			choice = interface.Dialog.option(title = 36271, message = 36270, labelConfirm = self.mOptions[1]['copy'], labelDeny = self.mOptions[0]['copy'])
			if choice: choice = 1
			else: choice = 0
		elif len(self.mOptions) == 3:
			choice = interface.Dialog.options(title = 36271, message = 36270, labelConfirm = self.mOptions[1]['copy'], labelDeny = self.mOptions[0]['copy'], labelCustom = self.mOptions[2]['copy'])
			if choice == interface.Dialog.ChoiceYes: choice = 1
			elif choice == interface.Dialog.ChoiceNo: choice = 0
			else: choice = 2

		from lib.modules.clipboard import Clipboard
		Clipboard.copy(value = self.mOptions[choice]['value'], notify = True, type = self.mOptions[choice]['label'])

	@classmethod
	def _donation(self, donations, id = None, enabled = True):
		if id: id = id.lower()
		for donation in donations:
			if (not id and 'selected' in donation and donation['selected']) or (donation['symbol'].lower() == id or donation['name'].lower() == id):
				if enabled and donation['enabled']: return donation
				else: break
		return None

	@classmethod
	def _donationColor(self, value, color, adjust = None):
		if adjust is None:
			darkness = interface.Format.colorDarkness(color)
			if darkness > 0.9: darkness = 80
			elif darkness > 0.8: darkness = 70
			elif darkness > 0.7: darkness = 60
			else: darkness = 0
			if darkness: color = interface.Format.colorLighter(color = color, change = darkness)
		elif adjust is False:
			color = None
		return interface.Format.font(value, color = color)

	@classmethod
	def _donationSymbol(self, donations, id = None, enabled = True, color = None):
		donation = self._donation(id = id, donations = donations, enabled = enabled)
		if donation and not donation['symbol'] in ['gaia', 'pp']: return self._donationColor(value = donation['symbol'].upper(), color = donation['color'], adjust = color)
		else: return None

	@classmethod
	def _donationName(self, donations, id = None, enabled = True, color = None):
		donation = self._donation(id = id, donations = donations, enabled = enabled)
		if donation: return self._donationColor(value = donation['name'], color = donation['color'], adjust = color)
		else: return None

	@classmethod
	def _qrGenerate(self, data, color = None, loaderShow = True, loaderHide = True, truncate = True, permanent = False):
		if loaderShow: interface.Loader.show()
		from lib.modules.qr import Qr
		if color is True: color = Qr.ColorGaia
		if not color: color = Qr.ColorGaia
		qr = Qr.generate(data = data, colorFront = color, extended = True, truncate = True, cache = Qr.CachePermanent if permanent else Qr.CacheTemporary)
		if loaderHide: interface.Loader.hide()
		return qr

	@classmethod
	def _qrGeneratePlain(self, data, loaderShow = False, loaderHide = False, permanent = False):
		return self._qrGenerate(data = data, color = 'FF333333', loaderShow = loaderShow, loaderHide = loaderHide, permanent = permanent)

class WindowRating(Window):

	IconStar = 'star'
	IconHeart = 'heart'
	IconSettings = [IconStar, IconHeart]

	IdDialog = 50000

	IdImageBorder = 50011
	IdImageBackground = 50012
	IdImageOverlay = 50013
	IdImageSeparator = 50014
	IdImageLogo = 50015
	IdImagePoster = 51001

	IdButtonClose = 50101
	IdButtonQr = 50102
	IdButtons = [52001, 52101, 52201, 52301, 52401, 52501, 52601, 52701, 52801, 52901]

	IdLabelTitle = 51011
	IdLabelHighlight = 51012
	IdLabelDescription1 = 51003
	IdLabelDescription2 = 51004
	IdLabelDescription3 = 51005
	IdLabelDescription4 = 51006

	IdImageGlobal = 51201
	IdImageTrakt = 51311
	IdImageImdb = 51321
	IdImageTmdb = 51331

	IdGroupRater = 51100
	IdGroupGlobal = 51200
	IdGroupService = 51300

	Rating = None

	def __init__(self, metadata, rating, icon, animation, **kwargs):
		xmlReplacements = {
			'valuegap' : lambda: self._scaleWidth(60),
		}
		super(WindowRating, self).__init__(xml = 'rating', xmlReplacements = xmlReplacements, **kwargs)

		self.mMetadata = metadata
		self.mMedia = tools.Media.TypeMovie
		if 'tvshowtitle' in self.mMetadata and self.mMetadata['tvshowtitle']:
			if 'episode' in self.mMetadata and not self.mMetadata['episode'] is None: self.mMedia = tools.Media.TypeEpisode
			elif 'season' in self.mMetadata and not self.mMetadata['season'] is None: self.mMedia = tools.Media.TypeSeason
			else: self.mMedia = tools.Media.TypeShow

		self.mRating = rating
		self.mIcon = icon
		self.mAnimation = animation

		self.mLabel = self._label()
		self.mHighlight = self._label(partial = True)
		self.mLink = self._link()

	@classmethod
	def show(self, metadata, rating = None, icon = None, animation = False, wait = True, initialize = True, close = False):
		interface.Loader.show()

		from lib.meta.image import MetaImage
		backgroundType = tools.Settings.getInteger('interface.rating.interface.background')
		backgroundPath = MetaImage.getFanart(data = metadata, default = None)
		backgroundPath = backgroundPath[0] if backgroundPath else None

		if not icon: icon = WindowRating.IconSettings[tools.Settings.getInteger('interface.rating.interface.icon')]

		WindowRating.Rating = None
		super(WindowRating, self)._show(metadata = metadata, rating = rating, backgroundType = backgroundType, backgroundPath = backgroundPath, icon = icon, animation = animation, wait = wait, initialize = initialize, close = close)
		return WindowRating.Rating

	def _initializeEnd1(self):
		super(WindowRating, self)._initializeEnd1()
		interface.Loader.show()

		from lib.meta.tools import MetaTools
		from lib.meta.image import MetaImage
		from lib.modules.playback import Playback

	 	# Resize for  wide screens.
		controls = [
			WindowRating.IdImageBorder,
			WindowRating.IdImageBackground,
			WindowRating.IdImageOverlay,
			WindowRating.IdImageSeparator,
			WindowRating.IdImageLogo,
			WindowRating.IdImagePoster,

			WindowRating.IdButtonClose,
			WindowRating.IdButtonQr,

			WindowRating.IdLabelTitle,
			WindowRating.IdLabelHighlight,
			WindowRating.IdLabelDescription1,
			WindowRating.IdLabelDescription2,
			WindowRating.IdLabelDescription3,
			WindowRating.IdLabelDescription4,

			WindowRating.IdGroupRater,

			WindowRating.IdImageGlobal,
			WindowRating.IdImageTrakt,
			WindowRating.IdImageImdb,
			WindowRating.IdImageTmdb,
		]

		# Rating buttons.
		for i in range(0, 10):
			for j in range(0, 5):
				controls.append(int('52%d0%d' % (i, j)))

		self._scale(controls)

		width = 800
		dialogWidth = self._scaleWidth(width)
		dialogCenter = self._centerX(0)
		dialogLeft = dialogCenter - int(dialogWidth / 2.0)
		dialogRight = dialogCenter + int(dialogWidth / 2.0)

		offset = int((60 - self._scaleWidth(60)) / 2.0)
		offset2 = int(offset / 2.0)
		offset3 = int(offset2 / 4.0)
		controls = [
			{'id' : WindowRating.IdImagePoster, 'side' : 0, 'offset' : 20},
			{'id' : WindowRating.IdImageLogo, 'side' : 0, 'offset' : 20},

			{'id' : WindowRating.IdButtonClose, 'side' : 1, 'offset' : 70},
			{'id' : WindowRating.IdButtonQr, 'side' : 1, 'offset' : 124},

			{'id' : WindowRating.IdLabelTitle, 'side' : 0, 'offset' : 186},
			{'id' : WindowRating.IdLabelHighlight, 'side' : 0, 'offset' : 186},
			{'id' : WindowRating.IdLabelDescription1, 'side' : 1, 'offset' : 220},
			{'id' : WindowRating.IdLabelDescription2, 'side' : 1, 'offset' : 220},
			{'id' : WindowRating.IdLabelDescription3, 'side' : 1, 'offset' : 220},
			{'id' : WindowRating.IdLabelDescription4, 'side' : 1, 'offset' : 220},

			{'id' : WindowRating.IdGroupRater, 'side' : 0, 'offset' : 186 - offset},
			{'id' : WindowRating.IdGroupGlobal, 'side' : 0, 'offset' : 186 - offset2},
			{'id' : WindowRating.IdGroupService, 'side' : 0, 'offset' : 192 - offset3},
		]
		for i in controls:
			control = self.control(i['id'])
			offset = self._scaleWidth(i['offset'])
			if i['side']: offset = dialogRight - offset
			else: offset = dialogLeft + offset
			control.setPosition(offset, control.getY())

		self._onClick(WindowRating.IdButtonClose, self._cancel)
		self._onClick(WindowRating.IdButtonQr, self._qr)
		for button in WindowRating.IdButtons:
			self._onClick(button, self._rate)

		colorPrimary = interface.Format.colorPrimary()
		colorSecondary = interface.Format.colorSecondary()

		self.propertySet('GaiaIcon', self.mIcon)
		self.propertySet('GaiaLogo', tools.File.joinPath(self._pathLogo(Window.SizeSmall), 'iconcolor.png'))
		self.propertySet('GaiaBackground', self._pathImage('background.jpg', interface = False))
		self.propertySet('GaiaColorButton', colorPrimary)
		self.propertySet('GaiaColorPrimary', colorPrimary)
		self.propertySet('GaiaColorSecondary', colorSecondary)
		self.propertySet('GaiaColorRating', interface.Format.colorRating())
		self.propertySet('GaiaSeparator', interface.Format.iconSeparator(pad = True, color = True))
		self.propertySet('GaiaIndicator', int(self.mAnimation)) # Do not use "GaiaAnimation", since the parent Window class already has that attribute.

		poster = MetaImage.getPoster(data = self.mMetadata)
		if poster: self.propertySet('GaiaPoster', poster[0])
		self.propertySet('GaiaLabel', self.mLabel)
		self.propertySet('GaiaHighlight', self.mHighlight)
		self.propertySet('GaiaLink', self.mLink)

		default = 5
		MetaTools.instance().voting(self.mMetadata)
		for i in ['global', 'trakt', 'imdb', 'tmdb']:
			rating = ''
			try:
				value = self.mMetadata['rating'] if i == 'global' else self.mMetadata['voting']['rating'][i]
				if value:
					if i == 'global': default = value
					rating += interface.Format.fontBold('%.1f' % value)
					value = self.mMetadata['votes'] if i == 'global' else self.mMetadata['voting']['votes'][i]
					rating += ' (%s)' % tools.Math.thousand(value if value else 0)
			except: pass
			if rating: self.propertySet('GaiaRating' + i.capitalize(), rating + ' ') # Add space, otherwise the last rating (TMDb) is sometimes cut off.

		if self.mRating and 'rating' in self.mRating and self.mRating['rating']:
			default = self.mRating['rating']
			self.propertySet('GaiaPreviousRating', int(default))
			if 'time' in self.mRating and self.mRating['time']: self.propertySet('GaiaPreviousTime', tools.Time.format(self.mRating['time'], format = tools.Time.FormatDate))
			self.propertySet('GaiaPreviousLabel', interface.Translation.string(33168))

		default = int(tools.Math.roundDown(default))
		self.propertySet('GaiaRatingDefault', default)
		self.focus(WindowRating.IdButtons[default - 1])

		self.propertySet('GaiaInitialized', 1)

	def _initializeEnd2(self):
		super(WindowRating, self)._initializeEnd2()
		interface.Loader.hide()

	def _label(self, partial = False):
		label = []

		if 'tvshowtitle' in self.mMetadata and self.mMetadata['tvshowtitle']:
			label.append(self.mMetadata['tvshowtitle'])
		elif 'title' in self.mMetadata and self.mMetadata['title']:
			label.append(self.mMetadata['title'])
			if 'year' in self.mMetadata and self.mMetadata['year']:
				label.append(str(self.mMetadata['year']))

		if 'episode' in self.mMetadata and not self.mMetadata['episode'] is None:
			label.append(interface.Translation.string(33028) + ' ' + tools.Media.number(season = self.mMetadata['season'], episode = self.mMetadata['episode']))
		elif 'season' in self.mMetadata and not self.mMetadata['season'] is None:
			label.append(interface.Translation.string(32055) + ' ' + str(self.mMetadata['season']))
		elif 'tvshowtitle' in self.mMetadata and self.mMetadata['tvshowtitle'] and self.mAnimation:
			label.append(interface.Translation.string(32005))

		if partial and len(label) > 1:
			labelBefore = label[1]
			labelAfter = interface.Format.fontColor(label[1], color = interface.Format.colorPrimary())
			label = interface.Format.iconJoin(label, color = False)
			label = label.replace(labelBefore, '')
			label = interface.Format.fontColor(label, color = '00FFFFFF')
			label += labelAfter
			return label
		else:
			return interface.Format.iconJoin(label)

	def _link(self):
		link = None
		if link is None:
			try:
				slug = self.mMetadata['id']['slug']
				if slug:
					from lib.modules import trakt as Trakt
					try: season = self.mMetadata['season']
					except: season = None
					try: episode = self.mMetadata['episode']
					except: episode = None
					link = Trakt.link(media = self.mMedia, slug = slug, season = season, episode = episode)
			except: tools.Logger.error()
		if link is None:
			from lib.meta.processors.imdb import MetaImdb
			link = MetaImdb.link(metadata = self.mMetadata)
		if link is None:
			try: link = self.mMetadata['homepage']
			except: pass
		return link

	def _qr(self):
		if self.mLink:
			dialog = self.control(WindowRating.IdDialog)
			dialog.setVisible(False)
			WindowQr.show(link = self.mLink, overlay = False, wait = True)
			dialog.setVisible(True)

	def _rate(self):
		try: WindowRating.Rating = int(self.property('GaiaRatingValue'))
		except: pass
		self.close()

	def _cancel(self):
		WindowRating.Rating = None
		self.close()

class WindowProgress(Window):

	# Logo
	LogoNone = None
	LogoIcon = 'icon'
	LogoName = 'name'

	LogoIconWidth = 128
	LogoIconHeight = 128
	LogoNameWidth = 197
	LogoNameHeight = 100
	LogoOffsetY = 0.24

	ProgressPercentage = 'GaiaProgressPercentage'
	ProgressFinished = 'GaiaProgressFinished'
	ProgressCount = 10
	ProgressSize = 24
	ProgressPaddingX = 8
	ProgressPaddingY = 20
	ProgressInterval = 1

	def __init__(self, backgroundType, backgroundPath, logo = None, progress = None, status = None, statusUpper = True, xml = None, xmlType = Window.TypeDefault, xmlOffset = None, width = None, height = None):
		super(WindowProgress, self).__init__(backgroundType = backgroundType, backgroundPath = backgroundPath, xml = xml, xmlType = xmlType, xmlOffset = xmlOffset, width = width, height = height)

		self.mLogo = logo

		self.mProgress = progress if progress else 0
		self.mProgressThread = None
		self.mProgressFinished = False
		self.mProgressInner = []
		self.mProgressOuter = []
		self.mProgressFill = []
		self.mProgressUpdate = None
		self.mProgressPrevious = [None, None, None]
		self.mProgressColors = interface.Format.colorGradient(self._colorProgressEmpty(), self._colorProgressFull(), int(100 / WindowProgress.ProgressCount))
		self.propertySet(WindowProgress.ProgressPercentage, self.mProgress)
		self.propertySet(WindowProgress.ProgressFinished, False)

		self.mStatus = status
		self.mStatusUpper = statusUpper
		self.mStatusControl = None

	# For some reason WindowIntro throws the following error on destrucution:
	#	ERROR: Exception
	#	ERROR: TypeError
	#	ERROR: :
	#	ERROR: "'NoneType' object is not callable"
	#	ERROR:  in
	#	ERROR: <bound method WindowIntro.__del__ of <lib.modules.window.WindowIntro object at 0x7f2c3861add0>>
	#	ERROR:  ignored
	# If the desctructors are removed, this error disappears.
	# Since the desctructors don't do anything but call the pareent desctructor, this should not be a problem.
	# All desctructors of other Window classes were aslo removed.
	#def __del__(self):
	#	super(WindowProgress, self).__del__()

	def _initializeStart1(self, progress = True, status = True):
		super(WindowProgress, self)._initializeStart1()

		self.mDimensionWidth = 0
		self.mDimensionHeight = 0

		if self.mLogo: self._dimensionUpdate(self._dimensionLogo(self.mLogo))
		if progress: self._dimensionUpdate(self._dimensionProgress())
		if status and not self.mStatus is False and not self.mStatus is None:
			self._dimensionUpdate(self._dimensionSpace())
			self._dimensionUpdate(self._dimensionLine())
			self._dimensionUpdate(self._dimensionSpace())

	def _initializeStart2(self, progress = True, status = True):
		super(WindowProgress, self)._initializeStart2()

		if self.mLogo: self.mDimensionHeight += self._offsetLogo(self._dimensionLogo(self.mLogo)[1])

		self.mDimensionX = self._centerX(self.mDimensionWidth)
		self.mDimensionY = self._centerY(self.mDimensionHeight)

		self.mDimensionWidth = 0
		self.mDimensionHeight = 0
		if self.mLogo: self._dimensionUpdate(self._addLogo(self.mLogo))
		if progress: self._dimensionUpdate(self._addProgress())
		if status and not self.mStatus is False and not self.mStatus is None:
			self._dimensionUpdate(self._dimensionSpace())
			self._dimensionUpdate(self._addStatus())
			self._dimensionUpdate(self._dimensionSpace())

	def _initializeEnd1(self):
		super(WindowProgress, self)._initializeEnd1()
		if self.mProgress: self.update(progress = self.mProgress, status = self.mStatus) # Do not do this if the status has a value, like in _initializeEnd2(), otherwise WindowStreams gets messed up.

	def _initializeEnd2(self):
		super(WindowProgress, self)._initializeEnd2()
		if self.mProgress or self.mStatus: self.update(progress = self.mProgress, status = self.mStatus)

	@classmethod
	def show(self, backgroundType = None, backgroundPath = None, logo = LogoIcon, progress = None, status = None, wait = False, initialize = True, close = False, retry = False, **kwargs):
		if tools.Tools.isInteger(wait):
			thread = Pool.thread(target = self._refresh, args = (wait,))
			thread.start()
			wait = True
		return super(WindowProgress, self)._show(backgroundType = backgroundType, backgroundPath = backgroundPath, logo = logo, progress = progress, status = status, wait = wait, initialize = initialize, close = close, retry = retry, **kwargs)

	@classmethod
	def _refresh(self, duration):
		steps = int(duration / WindowProgress.ProgressInterval)

		for i in range(steps):
			if self.visible(): break
			tools.Time.sleep(WindowProgress.ProgressInterval)

		progress = 0
		increase = 100 / steps
		for i in range(steps):
			if not self.visible(): break
			progress += increase
			self.update(progress = progress)
			tools.Time.sleep(WindowProgress.ProgressInterval)

		self.close()

	@classmethod
	def update(self, progress = None, finished = None, status = None, force = False, wait = False):
		instance = self._instance()
		if not instance or not instance.visible(): return None

		current = (progress, finished, status)

		# Updating the visible GUI is an expensive task, probably due to Kodi's GUI lock.
		# Try to update the progress as seldom as possible, to reduce overhead.
		# Also update the progress in a thread, to not make it block the actual tasks we keep track of.
		# Add progress update values to a queue and only pick the last value in the thread.
		# This reduces the number of times the GUI is updated, if multiple updaates come in while the thread is still busy with a previous update.
		if not progress is None:
			if progress < 1: progress *= 100
			progress = int(progress)

			# NB: Do not update the progress too often.
			# In some situations the progress increment can be fractionally small, causing the progress bar to update too often.
			# Eg: 2000 streams have been found, and now the progress is incremented by 0.05, each time calling the WindowProgress.update() function.
			# The actions below are processing-intensive (eg: setColorDiffuse) which can take very long when called 2000 times.
			if instance.mProgressPrevious[0] == progress: progress = None

			# Reduce even further. Only update the semi-opaque progress block every 5% instead of every 1%.
			# Only do this if the new progress is less than 5% from the previous progress, otherwise huge progress jumps are not immediatly shown.
			elif not instance.mProgressPrevious[0] is None and not progress % 5 == 0 and (instance.mProgressPrevious[0] is None or (progress - instance.mProgressPrevious[0]) < 5): progress = None

		if not status is None and instance.mProgressPrevious[2] == status: status = None

		instance.mProgressPrevious = current

		if not progress is None or not finished is None or not status is None:
			instance.mProgressUpdate = (progress, finished, status)
			if not instance._locked(): instance.mProgressThread = Pool.thread(target = instance._update, kwargs = {'force' : force}, start = True)
			if wait and instance.mProgressThread: instance.mProgressThread.join()

		return instance

	def _update(self, force = False):
		self._lock()

		while self.mProgressUpdate and not tools.System.aborted():
			if not self.visible() or self.mProgressFinished: break # Closed.

			progress, finished, status = self.mProgressUpdate
			self.mProgressUpdate = None
			if finished is True: progress = 100

			self._progressUpdate(progressNew = progress, progressCurrent = self.mProgress, controlFill = self.mProgressFill, controlIcon = self.mProgressInner, force = force)

			if not finished is None:
				self.mProgressFinished = finished
				self.propertySet(WindowProgress.ProgressFinished, finished)

			if not status is None:
				self.mStatus = status
				self._setLabel(control = self.mStatusControl, text = interface.Format.fontColor(self.mStatus, self._colorHighlight()), size = interface.Font.fontLarge(), bold = True, uppercase = self.mStatusUpper)

		self._unlock()

	@classmethod
	def _colorProgressEmpty(self):
		return interface.Format.colorSecondary()

	@classmethod
	def _colorProgressFull(self):
		return interface.Format.colorPrimary()

	def _logoSize(self, dimension):
		width = dimension[0]
		height = dimension[1]
		# Use < and not <=. If the logo is 128px, it will use the 256px image.
		# Due to dynamic resizing, the image with the actual size looks poor, rather use the larger image.
		if width < 64 and height < 64: return Window.SizeMini
		elif width < 128 and height < 128: return Window.SizeSmall
		elif width < 256 and height < 256: return Window.SizeMedium
		else: return Window.SizeLarge

	def _logoName(self, force = False, dimension = None):
		theme = self._theme()
		size = self._logoSize(dimension)
		return tools.File.joinPath(self._pathLogo(size), 'namecolor.png' if force or theme == 'default' or 'gaia' in theme  else 'nameglass.png')

	def _logoIcon(self, force = False, dimension = None):
		theme = self._theme()
		size = self._logoSize(dimension)
		return tools.File.joinPath(self._pathLogo(size), 'iconcolor.png' if force or theme == 'default' or 'gaia' in theme else 'iconglass.png')

	def _progress(self, progress):
		return int(tools.Math.roundDown(progress / float(WindowProgress.ProgressCount)))

	def _progressSub(self, progress):
		return int(progress % float(WindowProgress.ProgressCount))

	def _progressUpdate(self, progressNew, progressCurrent, controlFill, controlIcon, force = False):
		if not progressNew is None:
			self.mProgress = progressNew
			reduced = progressNew < progressCurrent
			progress = self._progress(progressNew)

			# setColorDiffuse is an expensive task. Only set if not set before.
			# Probably due to GUI locks that Kodi uses for updating items in the visible GUI.
			try:
				for i in range(progress):
					if not controlFill[i] is True:
						controlFill[i] = True
						controlIcon[i].setColorDiffuse(self._colorProgressFull())
				try:
					controlFill[i] = None
					controlIcon[progress].setColorDiffuse(self.mProgressColors[self._progressSub(progressNew)])
				except: pass
				if reduced or force:
					for i in range(progress, WindowProgress.ProgressCount):
						if not controlFill[i] is False:
							controlFill[i] = False
							controlIcon[i].setColorDiffuse(self._colorProgressEmpty())
			except:
				# Sometimes the icons are None and setColorDiffuse() fails.
				tools.Logger.error()

	def _progressClear(self, controlFill, controlIcon):
		self._progressUpdate(progressNew = -1, progressCurrent = 0, controlFill = controlFill, controlIcon = controlIcon)

	def _offsetLogo(self, y):
		return int(y * WindowProgress.LogoOffsetY)

	def _dimensionUpdate(self, size):
		self.mDimensionWidth = max(self.mDimensionWidth, size[0])
		self.mDimensionHeight += size[1]

	def _dimensionLine(self):
		return [1200, 30]

	def _dimensionSpace(self):
		return [1, 10]

	def _dimensionLogo(self, logo):
		if logo == WindowProgress.LogoIcon: return [self._scaleWidth(WindowProgress.LogoIconWidth), self._scaleHeight(WindowProgress.LogoIconHeight)]
		elif logo == WindowProgress.LogoName: return [self._scaleWidth(WindowProgress.LogoNameWidth), self._scaleHeight(WindowProgress.LogoNameHeight)]
		else: return [0, 0]

	def _dimensionProgress(self):
		width = (WindowProgress.ProgressCount * self._scaleWidth(WindowProgress.ProgressSize)) + ((WindowProgress.ProgressCount - 1) * self._scaleWidth(WindowProgress.ProgressPaddingX))
		height = self._scaleHeight(WindowProgress.ProgressSize + (0 if self.mStatus is False or self.mStatus is None else WindowProgress.ProgressPaddingY))
		return [width, height]

	def _addLogo(self, logo):
		dimension = self._dimensionLogo(logo)
		if logo == WindowProgress.LogoIcon: path = self._logoIcon(force = True, dimension = dimension)
		elif logo == WindowProgress.LogoName: path = self._logoName(force = True, dimension = dimension)
		self._addImage(path = path, x = self._centerX(dimension[0]), y = self._offsetY(), width = dimension[0], height = dimension[1])
		if logo == WindowProgress.LogoName: dimension[1] += self._offsetLogo(dimension[1]) # Add padding below.
		return dimension

	def _addProgress(self, animation = None):
		dimension, self.mProgressInner, self.mProgressOuter, self.mProgressFill = self._addProgressBar(animation = animation)
		return dimension

	def _addProgressBar(self, x = None, y = None, animation = None):
		pathInner = self._pathImage('progressinner')
		pathOuter = self._pathImage('progressouter')
		padding = self._scaleWidth(WindowProgress.ProgressPaddingX)
		dimension = self._dimensionProgress()
		width = self._scaleWidth(WindowProgress.ProgressSize)
		height = self._scaleHeight(WindowProgress.ProgressSize)
		if x is None: x = self._centerX(dimension[0])
		if y is None: y = self._offsetY()

		inner = [None] * WindowProgress.ProgressCount
		outer = [None] * WindowProgress.ProgressCount
		fill = [False] * WindowProgress.ProgressCount
		for i in range(WindowProgress.ProgressCount):
			self._addProgressIcon(inner = inner, outer = outer, index = i, pathInner = pathInner, pathOuter = pathOuter, x = x, y = y, width = width, height = height, animation = animation)
			x += width + padding

		return dimension, inner, outer, fill

	def _addProgressIcon(self, inner, outer, index, pathInner, pathOuter, x, y, width, height, animation = None):
		inner[index] = self._addImage(path = pathInner, x = x, y = y, width = width, height = height, color = self._colorProgressEmpty(), animation = animation)
		outer[index] = self._addImage(path = pathOuter, x = x, y = y, width = width, height = height, animation = animation)

	def _addLine(self, text = '', color = None, size = None, alignment = Window.AlignmentCenter, bold = True, uppercase = True, animation = None, dimension = None):
		if color is None: color = self._colorDefault()
		if size is None: size = interface.Font.fontLarge()
		if dimension is None: dimension = self._dimensionLine()
		control = self._addLabel(text = text, x = self._centerX(dimension[0]), y = self._offsetY(), width = dimension[0], height = dimension[1], color = color, size = size, alignment = alignment, bold = bold, uppercase = uppercase, animation = animation)
		return control, dimension

	def _addStatus(self, text = None, animation = None):
		if text is None: text = self.mStatus
		if tools.Tools.isBoolean(text): text = ''
		self.mStatusControl, dimension = self._addLine(text = text, color = self._colorHighlight(), animation = animation, uppercase = self.mStatusUpper)
		return dimension


class WindowIntro(WindowProgress):

	Parts = 7

	TimeAnimation = 1000
	TimeDelay = 200

	LogoWidth = 700
	LogoHeight = 303

	AnimationType = 'WindowOpen'
	AnimationValues = 'effect=fade start=0 end=100 time=%d delay=%d'

	def __init__(self, backgroundType, backgroundPath, progress = False, status = True, slogan = True, alternative = False, **kwargs):
		super(WindowIntro, self).__init__(backgroundType = backgroundType, backgroundPath = backgroundPath, status = status, **kwargs)
		self.mTime = tools.Time.timestamp()
		self.mProgressEnabled = progress
		self.mSlogan = slogan
		self.mAlternative = alternative

	def _initializeStart1(self):
		super(WindowIntro, self)._initializeStart1(progress = False, status = False)
		self._dimensionUpdate(self._dimensionLogo())
		if self.mProgressEnabled:
			self._dimensionUpdate(self._dimensionSpace())
			self._dimensionUpdate(self._dimensionSpace())
			self._dimensionUpdate(self._dimensionProgress())
		if not self.mStatus is False and not self.mStatus is None:
			self._dimensionUpdate(self._dimensionLine())
			self._dimensionUpdate(self._dimensionSpace())

	def _initializeStart2(self):
		super(WindowIntro, self)._initializeStart2(progress = False, status = False)
		self._dimensionUpdate(self._addLogo())
		delay = (WindowIntro.Parts - 1) * WindowIntro.TimeDelay
		if self.mProgressEnabled:
			self._dimensionUpdate(self._dimensionSpace())
			self._dimensionUpdate(self._dimensionSpace())
			self._dimensionUpdate(self._addProgress(animation = self._animation(delay = delay)))
		if not self.mStatus is False and not self.mStatus is None:
			self._dimensionUpdate(self._addStatus(animation = self._animation(delay = delay)))
			self._dimensionUpdate(self._dimensionSpace())

	def _initializeEnd1(self):
		super(WindowIntro, self)._initializeEnd1()
		if not self.mProgressEnabled: self.close(wait = True)

	@classmethod
	def show(self, status = True, wait = False, initialize = True, close = False, progress = True, slogan = True, alternative = False):
		return super(WindowIntro, self)._show(backgroundType = self.BackgroundCombined, backgroundPath = None, status = status, wait = wait, initialize = initialize, close = close, progress = progress, slogan = slogan, alternative = alternative)

	@classmethod
	def close(self, id = None, loader = True, wait = False):
		if wait:
			start = self.instance().mTime
			total = ((2 * WindowIntro.TimeAnimation) + ((WindowIntro.Parts + 1) * WindowIntro.TimeDelay)) / 1000.0
			current = tools.Time.timestamp()
			while current - start < total and not tools.System.aborted():
				tools.Time.sleep(0.5)
				current += 0.5
		return super(WindowIntro, self).close(id = id, loader = loader)

	@classmethod
	def duration(self, seconds = True):
		result = WindowIntro.TimeAnimation + WindowIntro.TimeDelay
		if seconds: result = result / 1000.0
		return result

	@classmethod
	def _animation(self, duration = None, delay = None):
		return [(WindowIntro.AnimationType, WindowIntro.AnimationValues % (duration if duration else WindowIntro.TimeAnimation, delay if delay else WindowIntro.TimeDelay))]

	def _logoPath(self, part):
		file = 'gaia%d.png' % part
		path = tools.File.joinPath(tools.System.pathResources(), 'resources', 'media', 'logo', 'splash')
		if self.mAlternative:
			pathAlternative = tools.File.joinPath(path, 'alternative', file)
			if tools.File.exists(pathAlternative): return pathAlternative
		return tools.File.joinPath(path, file)

	def _dimensionLogo(self, offset = True):
		extra = 0
		if offset:
			extra -= 20
			if not self.mSlogan: extra += 80
		return [self._scaleWidth(WindowIntro.LogoWidth), self._scaleHeight(WindowIntro.LogoHeight) + extra]

	def _addLogo(self):
		dimension = self._dimensionLogo(offset = False)
		width = dimension[0]
		height = dimension[1]
		x = self._centerX(width)
		y = self._offsetY()

		if not self.mSlogan: y += 80

		delay = WindowIntro.TimeDelay
		for i in range(1, WindowIntro.Parts + (1 if self.mSlogan else 0)):
			logo = self._addImage(path = self._logoPath(i), x = x, y = y, width = width, height = height, animation = self._animation(delay = delay))
			if i < WindowIntro.Parts - 1: delay += WindowIntro.TimeDelay

		return dimension


class WindowScrape(WindowProgress):

	StatisticsEssential	= 0
	StatisticsStandard	= 1
	StatisticsAdvanced	= 2
	StatisticsExtended	= 3

	def __init__(self, backgroundType, backgroundPath, logo, status, **kwargs):
		super(WindowScrape, self).__init__(backgroundType = backgroundType, backgroundPath = backgroundPath, logo = logo, status = status, **kwargs)

		self.mSkip = False
		self.mTime = None
		self.mStreamsTotal = 0
		self.mStreamsHdUltra = 0
		self.mStreamsHd1080 = 0
		self.mStreamsHd720 = 0
		self.mStreamsSd = 0
		self.mStreamsLd = 0
		self.mStreamsTorrent = 0
		self.mStreamsUsenet = 0
		self.mStreamsHoster = 0
		self.mStreamsCached = 0
		self.mStreamsDebrid = 0
		self.mStreamsDirect = 0
		self.mStreamsPremium = 0
		self.mStreamsLocal = 0
		self.mStreamsFinished = 0
		self.mStreamsBusy = 0
		self.mProvidersFinished = 0
		self.mProvidersBusy = 0
		self.mProvidersLabels = None
		self.mProvidersStarted = None

		self.mControlDetails = None
		self.mControlStreams1 = None
		self.mControlStreams2 = None
		self.mControlStreams3 = None
		self.mControlStreams4 = None
		self.mControlProcessed = None
		self.mControlProviders = None
		self.mControlSkip = None
		self.mControlCancel = None

		self.mStatistics = tools.Settings.getInteger('interface.scrape.interface.statistics')

		self._onAction(WindowBase.ActionMoveLeft, self._actionFocus)
		self._onAction(WindowBase.ActionMoveRight, self._actionFocus)
		self._onAction(WindowBase.ActionMoveUp, self._actionFocus)
		self._onAction(WindowBase.ActionMoveDown, self._actionFocus)
		self._onAction(WindowBase.ActionItemNext, self._actionFocus)
		self._onAction(WindowBase.ActionItemPrevious, self._actionFocus)
		self._onAction(WindowBase.ActionSelectItem, self._actionFocus)

	def _initializeStart1(self):
		super(WindowScrape, self)._initializeStart1()
		self._dimensionUpdate(self._dimensionSeparator())
		self._dimensionUpdate(self._dimensionLine())
		if self.mStatistics >= WindowScrape.StatisticsStandard:
			self._dimensionUpdate(self._dimensionSeparator())
			self._dimensionUpdate(self._dimensionLine())
			self._dimensionUpdate(self._dimensionLine())
		if self.mStatistics >= WindowScrape.StatisticsAdvanced:
			self._dimensionUpdate(self._dimensionLine())
		if self.mStatistics >= WindowScrape.StatisticsExtended:
			self._dimensionUpdate(self._dimensionLine())
		if self.mStatistics >= WindowScrape.StatisticsAdvanced:
			self._dimensionUpdate(self._dimensionSeparator())
			self._dimensionUpdate(self._dimensionLine())
			if tools.Settings.getBoolean('interface.scrape.interface.providers'): self._dimensionUpdate(self._dimensionLine())
		self._dimensionUpdate(self._dimensionSeparator())
		self._dimensionUpdate(self._dimensionButtons())

	def _initializeStart2(self):
		super(WindowScrape, self)._initializeStart2()
		width = Window.SeparatorLineNarrow if self.mStatistics <= WindowScrape.StatisticsStandard else None
		self._dimensionUpdate(self._addSeparator(width = width))
		self._dimensionUpdate(self._addDetails())
		if self.mStatistics >= WindowScrape.StatisticsStandard:
			self._dimensionUpdate(self._addSeparator(width = width))
			self._dimensionUpdate(self._addStreams1())
			self._dimensionUpdate(self._addStreams2())
		if self.mStatistics >= WindowScrape.StatisticsAdvanced:
			self._dimensionUpdate(self._addStreams3())
		if self.mStatistics >= WindowScrape.StatisticsExtended:
			self._dimensionUpdate(self._addStreams4())
		if self.mStatistics >= WindowScrape.StatisticsAdvanced:
			self._dimensionUpdate(self._addSeparator(width = width))
			self._dimensionUpdate(self._addProcessed())
			if tools.Settings.getBoolean('interface.scrape.interface.providers'): self._dimensionUpdate(self._addProviders())
		self._dimensionUpdate(self._addSeparator(width = width))
		self._dimensionUpdate(self._addButtons())
		self._addCurtains()

	@classmethod
	def show(self, background = None, status = True, wait = False, initialize = True, close = False):
		return super(WindowScrape, self).show(backgroundType = tools.Settings.getInteger('interface.scrape.interface.background'), backgroundPath = background, logo = WindowProgress.LogoIcon, status = status, wait = wait, initialize = initialize, close = close)

	@classmethod
	def update(self, progress = None, finished = None, status = None, time = None, streamsTotal = None, streamsHdUltra = None, streamsHd1080 = None, streamsHd720 = None, streamsSd = None, streamsLd = None, streamsTorrent = None, streamsUsenet = None, streamsHoster = None, streamsCached = None, streamsDebrid = None, streamsDirect = None, streamsPremium = None, streamsLocal = None, streamsFinished = None, streamsBusy = None, providersFinished = None, providersBusy = None, providersLabels = None, skip = False):
		instance = super(WindowScrape, self).update(progress = progress, finished = finished, status = status)
		if instance is None: return instance
		instance._lock()

		if not time is None: instance.mTime = time
		if not streamsTotal is None: instance.mStreamsTotal = streamsTotal
		if not streamsHdUltra is None: instance.mStreamsHdUltra = streamsHdUltra
		if not streamsHd1080 is None: instance.mStreamsHd1080 = streamsHd1080
		if not streamsHd720 is None: instance.mStreamsHd720 = streamsHd720
		if not streamsSd is None: instance.mStreamsSd = streamsSd
		if not streamsLd is None: instance.mStreamsLd = streamsLd
		if not streamsTorrent is None: instance.mStreamsTorrent = streamsTorrent
		if not streamsUsenet is None: instance.mStreamsUsenet = streamsUsenet
		if not streamsHoster is None: instance.mStreamsHoster = streamsHoster
		if not streamsCached is None: instance.mStreamsCached = streamsCached
		if not streamsDebrid is None: instance.mStreamsDebrid = streamsDebrid
		if not streamsDirect is None: instance.mStreamsDirect = streamsDirect
		if not streamsPremium is None: instance.mStreamsPremium = streamsPremium
		if not streamsLocal is None: instance.mStreamsLocal = streamsLocal
		if not streamsFinished is None: instance.mStreamsFinished = streamsFinished
		if not streamsBusy is None: instance.mStreamsBusy = streamsBusy
		if not providersFinished is None: instance.mProvidersFinished = providersFinished
		if not providersBusy is None: instance.mProvidersBusy = providersBusy
		try: instance.mProvidersLabels = providersLabels[:3]
		except: instance.mProvidersLabels = providersLabels

		if not instance.mSkip == skip:
			if skip:
				[i.setVisible(not skip) for i in instance.mControlCancel if i]
				[i.setVisible(skip) for i in instance.mControlSkip if i]
			else:
				[i.setVisible(skip) for i in instance.mControlSkip if i]
				[i.setVisible(not skip) for i in instance.mControlCancel if i]
			instance.mSkip = skip

		size = interface.Font.fontLarge()

		if not progress is None or not time is None:
			labels = []
			labels.append('%s: %s %%' % (interface.Translation.string(32037), instance._highlight(instance.mProgress)))
			labels.append('%s: %s %s' % (interface.Translation.string(35029), instance._highlight(instance.mTime), interface.Translation.string(32405)))
			if instance.mStatistics == WindowScrape.StatisticsEssential:
				labels.append('%s: %s' % (interface.Translation.string(33481), instance._highlight(instance.mStreamsTotal)))
			instance._setLabel(control = instance.mControlDetails, text = self._separator(labels), size = size, bold = True, uppercase = True)

		if instance.mStatistics == WindowScrape.StatisticsStandard:
			if not streamsTotal is None:
				labels = []
				labels.append('TOTAL: ' + instance._highlight(instance.mStreamsTotal))
				labels.append('INSTANT: ' + instance._highlight(instance.mStreamsCached + instance.mStreamsPremium + instance.mStreamsLocal + instance.mStreamsDirect))
				instance._setLabel(control = instance.mControlStreams1, text = self._separator(labels), size = size, bold = True, uppercase = True)

			if not streamsHdUltra is None or not streamsHd1080 is None or not streamsHd720 is None or not streamsSd is None or not streamsLd is None:
				labels = []
				labels.append('ULTRA: ' + instance._highlight(instance.mStreamsHdUltra))
				labels.append('HD: ' + instance._highlight(instance.mStreamsHd1080 + instance.mStreamsHd720))
				labels.append('SD: ' + instance._highlight(instance.mStreamsSd + instance.mStreamsLd))
				instance._setLabel(control = instance.mControlStreams2, text = self._separator(labels), size = size, bold = True, uppercase = True)
		elif instance.mStatistics == WindowScrape.StatisticsAdvanced:
			if not streamsTotal is None:
				label = 'TOTAL: ' + instance._highlight(instance.mStreamsTotal)
				instance._setLabel(control = instance.mControlStreams1, text = label, size = size, bold = True, uppercase = True)

			if not streamsHdUltra is None or not streamsHd1080 is None or not streamsHd720 is None or not streamsSd is None or not streamsLd is None:
				labels = []
				labels.append('ULTRA: ' + instance._highlight(instance.mStreamsHdUltra))
				labels.append('HD: ' + instance._highlight(instance.mStreamsHd1080 + instance.mStreamsHd720))
				labels.append('SD: ' + instance._highlight(instance.mStreamsSd + instance.mStreamsLd))
				instance._setLabel(control = instance.mControlStreams2, text = self._separator(labels), size = size, bold = True, uppercase = True)

			if not streamsCached is None or not streamsDebrid is None or not streamsDirect is None or not streamsPremium is None or not streamsLocal is None:
				labels = []
				labels.append('CACHED: ' + instance._highlight(instance.mStreamsCached))
				labels.append('INSTANT: ' + instance._highlight(instance.mStreamsPremium + instance.mStreamsDirect + instance.mStreamsLocal))
				labels.append('DEBRID: ' + instance._highlight(instance.mStreamsDebrid))
				instance._setLabel(control = instance.mControlStreams3, text = self._separator(labels), size = size, bold = True, uppercase = True)
		elif instance.mStatistics == WindowScrape.StatisticsExtended:
			if not streamsTotal is None:
				label = 'STREAMS FOUND: ' + instance._highlight(instance.mStreamsTotal)
				instance._setLabel(control = instance.mControlStreams1, text = label, size = size, bold = True, uppercase = True)

			if not streamsTorrent is None or not streamsUsenet is None or not streamsHoster is None:
				labels = []
				labels.append('TORRENT: ' + instance._highlight(instance.mStreamsTorrent))
				labels.append('USENET: ' + instance._highlight(instance.mStreamsUsenet))
				labels.append('HOSTER: ' + instance._highlight(instance.mStreamsHoster))
				instance._setLabel(control = instance.mControlStreams2, text = self._separator(labels), size = size, bold = True, uppercase = True)

			if not streamsHdUltra is None or not streamsHd1080 is None or not streamsHd720 is None or not streamsSd is None or not streamsLd is None:
				labels = []
				labels.append('HDULTRA: ' + instance._highlight(instance.mStreamsHdUltra))
				labels.append('HD1080: ' + instance._highlight(instance.mStreamsHd1080))
				labels.append('HD720: ' + instance._highlight(instance.mStreamsHd720))
				labels.append('SD: ' + instance._highlight(instance.mStreamsSd))
				labels.append('LD: ' + instance._highlight(instance.mStreamsLd))
				instance._setLabel(control = instance.mControlStreams3, text = self._separator(labels), size = size, bold = True, uppercase = True)

			if not streamsCached is None or not streamsDebrid is None or not streamsDirect is None or not streamsPremium is None or not streamsLocal is None:
				labels = []
				labels.append('CACHED: ' + instance._highlight(instance.mStreamsCached))
				labels.append('DEBRID: ' + instance._highlight(instance.mStreamsDebrid))
				labels.append('DIRECT: ' + instance._highlight(instance.mStreamsDirect))
				labels.append('PREMIUM: ' + instance._highlight(instance.mStreamsPremium))
				labels.append('LOCAL: ' + instance._highlight(instance.mStreamsLocal))
				instance._setLabel(control = instance.mControlStreams4, text = self._separator(labels), size = size, bold = True, uppercase = True)

		if instance.mStatistics >= WindowScrape.StatisticsAdvanced:
			if instance.mStreamsFinished > 0 or instance.mStreamsBusy > 0:
				labels = []
				labels.append('FINISHED STREAMS: ' + instance._highlight(instance.mStreamsFinished))
				labels.append('BUSY STREAMS: ' + instance._highlight(instance.mStreamsBusy))
				instance._setLabel(control = instance.mControlProcessed, text = self._separator(labels), size = size, bold = True, uppercase = True)
			elif not providersFinished is None or not providersBusy is None:
				labels = []
				labels.append('BUSY PROVIDERS: ' + instance._highlight(instance.mProvidersBusy))
				labels.append('FINISHED PROVIDERS: ' + instance._highlight(instance.mProvidersFinished))
				instance._setLabel(control = instance.mControlProcessed, text = self._separator(labels), size = size, bold = True, uppercase = True)

			if not instance.mControlProviders is None:
				try:
					if not instance.mProvidersStarted and instance.mProvidersLabels is None: label = 'PROVIDERS STARTED'
					elif not instance.mProvidersLabels or len(instance.mProvidersLabels) == 0: label = 'PROVIDERS FINISHED'
					else:
						instance.mProvidersStarted = True
						label = self._separator(instance.mProvidersLabels)
					instance._setLabel(control = instance.mControlProviders, text = label, size = size, bold = True, uppercase = True)
				except:
					tools.Logger.error()

		instance._unlock()
		return instance

	@classmethod
	def enabled(self):
		return tools.Settings.getInteger('interface.scrape.interface') == 0

	@classmethod
	def skip(self):
		interface.Loader.show()
		self.close()

	def _actionFocus(self):
		try:
			if self.mControlSkip[0].isVisible():
				self.focus(self.mControlSkip[0])
			else:
				self.focus(self.mControlCancel[0])
		except:
			# For Kodi 17 that does not have the isVisible() function.
			try:
				if self.mSkip: self.focus(self.mControlSkip[0])
				else: self.focus(self.mControlCancel[0])
			except: pass

	def _dimensionButtons(self, text = None):
		return self._dimensionButton(text = text, icon = True)

	def _addDetails(self):
		self.mControlDetails, dimension = self._addLine()
		return dimension

	def _addStreams1(self):
		self.mControlStreams1, dimension = self._addLine()
		return dimension

	def _addStreams2(self):
		self.mControlStreams2, dimension = self._addLine()
		return dimension

	def _addStreams3(self):
		self.mControlStreams3, dimension = self._addLine()
		return dimension

	def _addStreams4(self):
		self.mControlStreams4, dimension = self._addLine()
		return dimension

	def _addProcessed(self):
		self.mControlProcessed, dimension = self._addLine()
		return dimension

	def _addProviders(self):
		self.mControlProviders, dimension = self._addLine()
		return dimension

	def _addButtons(self):
		dimension = self._dimensionButtons(text = 33897)
		x = self._centerX(dimension[0])
		y = self._offsetY() + 20
		self.mControlSkip = self._addButton(text = 33897, x = x, y = y, callback = self.skip, icon = 'change', visible = False)

		dimension = self._dimensionButtons(text = 33743)
		x = self._centerX(dimension[0])
		y = self._offsetY() + 20
		self.mControlCancel = self._addButton(text = 33743, x = x, y = y, callback = self.close, icon = 'error')

		return dimension


class WindowPlayback(WindowProgress):

	def __init__(self, backgroundType, backgroundPath, logo, status, retry, **kwargs):
		super(WindowPlayback, self).__init__(backgroundType = backgroundType, backgroundPath = backgroundPath, logo = logo, status = status, **kwargs)
		self.mRetry = retry
		self.mRetryCount = None
		self.mControlSeparator1 = None
		self.mControlSeparator2 = None
		self.mControlSubstatus = None
		self.mControlRetries = None
		self.mControlCancel = None

		self._onAction(WindowBase.ActionMoveLeft, self._actionFocus)
		self._onAction(WindowBase.ActionMoveRight, self._actionFocus)
		self._onAction(WindowBase.ActionMoveUp, self._actionFocus)
		self._onAction(WindowBase.ActionMoveDown, self._actionFocus)
		self._onAction(WindowBase.ActionItemNext, self._actionFocus)
		self._onAction(WindowBase.ActionItemPrevious, self._actionFocus)
		self._onAction(WindowBase.ActionSelectItem, self._actionFocus)
		self._onAction(WindowBase.ActionNavigationBack, self._actionCancel)

	def _initializeStart1(self, retry = False):
		super(WindowPlayback, self)._initializeStart1()
		if self.mRetry:
			self._dimensionUpdate(self._dimensionSeparator())
			self._dimensionUpdate(self._dimensionLine())
			self._dimensionUpdate(self._dimensionLine())
			self._dimensionUpdate(self._dimensionSeparator())
		self._dimensionUpdate(self._dimensionCancel())

	def _initializeStart2(self, retry = False):
		super(WindowPlayback, self)._initializeStart2()
		if self.mRetry:
			self._dimensionUpdate(self._addSeparator1())
			self._dimensionUpdate(self._addSubstatus())
			self._dimensionUpdate(self._addRetries())
			self._dimensionUpdate(self._addSeparator2())
		self._dimensionUpdate(self._addCancel())
		self._addCurtains()

	@classmethod
	def show(self, background = None, status = True, wait = False, initialize = True, close = False, retry = False):
		if interface.Player.canceled(): return False
		return super(WindowPlayback, self).show(backgroundType = tools.Settings.getInteger('interface.playback.interface.background'), backgroundPath = background, logo = WindowProgress.LogoIcon, status = status, wait = wait, initialize = initialize, close = close, retry = retry)

	@classmethod
	def close(self, id = None, loader = True, stop = False, cancel = False):
		if cancel: interface.Player.canceledSet()

		if stop:
			# If the playback has started but Kodi cannot connect and/or start streaming (stuck at "Establishing Stream Connection").
			from lib.modules.interface import Player
			Player().stop()

		# Sometimes the loader is visible if canceling playback window. loader parameter True by default.
		loader = False # This problem seems to be gone, and we do not want to hide the loader when reloading the stream window from player.py, otherwise there is a short time where neither the loader not the stream loading window is visible.
		return super(WindowPlayback, self).close(id = id, loader = loader)

	@classmethod
	def update(self, progress = None, finished = None, status = None, substatus1 = None, substatus2 = None, total = None, remaining = None):
		if interface.Player.canceled(): return False

		instance = super(WindowPlayback, self).update(progress = progress, finished = finished, status = status)
		if instance is None: return instance
		instance._lock()

		try:
			remaining += 1 # Otherwise it shows "0 of 2" after the first retry. Just looks better as "1 of 2".
			retry = not((total - remaining) == 0)
		except: retry = False

		if retry and not remaining == instance.mRetryCount:
			background = instance.mBackgroundPath
			instance._unlock()

			interface.Loader.show()
			instance.close(loader = False, stop = True)
			self.show(background = background, status = True, retry = True)

			instance = super(WindowPlayback, self).update(progress = progress, finished = finished, status = status)
			interface.Loader.hide()
			if instance is None: return instance

			instance._lock()
			instance.mRetryCount = remaining

		if retry:
			size = interface.Font.fontLarge()

			if not substatus1 is None or not substatus2 is None:
				labels = []
				labels.append(substatus1)
				labels.append(substatus2)
				instance._setLabel(control = instance.mControlSubstatus, text = self._separator(labels), size = size, bold = True, uppercase = True)

			if not total is None or not remaining is None:
				labels = []
				labels.append('%s: %s' % (interface.Translation.string(35476), instance._highlight(total)))
				labels.append('%s: %s' % (interface.Translation.string(35475), instance._highlight(remaining)))
				instance._setLabel(control = instance.mControlRetries, text = self._separator(labels), size = size, bold = True, uppercase = True)

		instance._unlock()
		return instance

	@classmethod
	def enabled(self):
		return tools.Settings.getInteger('interface.playback.interface') == 0

	def _actionFocus(self):
		try: self.focus(self.mControlCancel[0])
		except: pass

	def _actionCancel(self):
		self.close(stop = True, cancel = True)

	def _dimensionCancel(self):
		return self._dimensionButton(text = 33743, icon = True)

	def _addSeparator1(self):
		self.mControlSeparator1, dimension = self._addSeparator(control = True)
		return dimension

	def _addSeparator2(self):
		self.mControlSeparator2, dimension = self._addSeparator(control = True)
		return dimension

	def _addSubstatus(self):
		self.mControlSubstatus, dimension = self._addLine()
		return dimension

	def _addRetries(self):
		self.mControlRetries, dimension = self._addLine()
		return dimension

	def _addCancel(self):
		dimension = self._dimensionCancel()
		x = self._centerX(dimension[0])
		y = self._offsetY() + 20
		self.mControlCancel = self._addButton(text = 33743, x = x, y = y, callback = self._actionCancel, icon = 'error')
		return dimension


class WindowStreams(WindowProgress):

	ProgressThread = None
	ProgressData = {}

	def __init__(self, backgroundType, backgroundPath, logo, status, metadata, items, xmlType, **kwargs):
		super(WindowStreams, self).__init__(backgroundType = backgroundType, backgroundPath = backgroundPath, logo = logo, status = status, xml = 'streams', xmlType = xmlType, **kwargs)

		self.mMetadata = metadata
		self.mItems = items

		self._onAction(WindowBase.ActionContextMenu, self._actionContext)
		self._onAction(WindowBase.ActionShowInfo, self._actionInformation)
		self._onAction(WindowBase.ActionAny, self._actionList)
		self._onClick(Window.IdListControl, self._actionSelect)

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True, full = True):
		WindowStreams.ProgressThread = None
		WindowStreams.ProgressData = {}

	##############################################################################
	# GENERAL
	##############################################################################

	def _initializeStart2(self):
		# Create the main background.
		self._addBackground(type = self.mBackgroundType, path = self.mBackgroundPath, fixed = True)

	def _initializeEnd1(self):
		# The XML interface is only created during doModal().
		# In order to create the loader on top of the XML, it must be added AFTER the window has been shown.
		super(WindowStreams, self)._initializeStart2()
		super(WindowStreams, self)._initializeEnd1()

	@classmethod
	def show(self, background = None, status = True, metadata = None, items = None, wait = False, initialize = True, close = False):
		self.reset()

		backgroundType = tools.Settings.getInteger('interface.stream.interface.background')
		decorations = tools.Settings.getInteger('interface.stream.interface.decorations')
		if decorations == 0: decorations = self.TypeStreamPlain
		elif decorations == 1: decorations = self.TypeStreamBasic
		elif decorations == 2: decorations = self.TypeStreamIcons
		else: decorations = self.TypeStreamPlain
		return super(WindowStreams, self)._show(xmlType = decorations, backgroundType = backgroundType, backgroundPath = background, logo = WindowProgress.LogoIcon, status = status, metadata = metadata, items = items, wait = wait, initialize = initialize, close = close)

	@classmethod
	def update(self, progress = None, finished = None, status = None):
		# Just updating the progress in this window can slow down loading of the stream list (from core.py -> _showStreams) by 2 seconds for every 500 links.
		# Let the progress update run in a background thread.

		'''instance = super(WindowStreams, self).update(progress = progress, finished = finished, status = status)
		try:
			if finished: instance._remove()
		except: pass'''

		if WindowStreams.ProgressThread is None: WindowStreams.ProgressThread = Pool.thread(target = self._updateObserve, start = True)
		WindowStreams.ProgressData['progress'] = progress
		WindowStreams.ProgressData['finished'] = finished
		WindowStreams.ProgressData['status'] = status

	@classmethod
	def _updateObserve(self):
		while not tools.System.aborted():
			if WindowStreams.ProgressData:
				if WindowStreams.ProgressData['finished']:
					# Wait for the final progress update to complete, otherwise _remove() might be called before the update thread finishes, causing the stream list in WindowStream not to show once loading is done (sporadic error).
					instance = super(WindowStreams, self).update(wait = True, **WindowStreams.ProgressData)
					try: instance._remove()
					except: pass
					break
				else:
					instance = super(WindowStreams, self).update(**WindowStreams.ProgressData)
			if not self.visible(): break
			tools.Time.sleep(0.1)

	@classmethod
	def enabled(self):
		return tools.Settings.getInteger('interface.stream.interface') == 0

	@classmethod
	def itemReselect(self):
		id = self.propertyGlobal('GaiaIndexId')
		position = self.propertyGlobal('GaiaIndex' + id)
		if position: self.itemSelect(int(position))

	def _actionSelect(self):
		path = self.control(Window.IdListControl).getSelectedItem().getProperty('GaiaAction')
		tools.System.executePlugin(command = path)

	def _actionInformation(self):
		try: item = self.mItems[self.itemSelected()]
		except: item = None

		# If the item was selected, show stream info.
		# Otherwise fall back to the movie/episode info (eg: no item selected from the list).
		if item:
			tools.System.executePlugin(action = 'streamsInformation', parameters = {'source' : item, 'metadata' : self.mMetadata})
		else:
			# This only works if the user has opened the information dialog on the normal movie/episode menu before.
			# This adds the metadata to memory and when the window is opened from here, it will correctly display the metadata.
			# But if the information was not displayed before, this window stays empty.
			# Use the ExtendedInfo dialog instead.
			#Window.show(self.IdWindowInformation)

			from lib.informers import Informer
			Informer.show(metadata = self.mMetadata)

	def _actionContext(self):
		index = self.control(Window.IdListControl).getSelectedPosition()
		if index >= 0:
			self.focus(50000)
			self.mContexts[index].show()

	def _actionList(self):
		try:
			id = self.propertyGlobal('GaiaIndexId')
			if id: self.propertyGlobalSet('GaiaIndex' + id, self.control(Window.IdListControl).getSelectedPosition())
		except: pass


class WindowBinge(WindowProgress):

	ModeFull = True
	ModeOverlay = False

	def __init__(self, mode, backgroundType, backgroundPath, poster, logo, status, width = None, height = None, inverse = False, **kwargs):
		super(WindowBinge, self).__init__(backgroundType = backgroundType, backgroundPath = backgroundPath, logo = logo, status = status, width = width, height = height, **kwargs)

		self.mMode = mode

		self.mControlTitle = None
		self.mControlEpisode = None
		self.mControlTime = None
		self.mControlCancel = None
		self.mControlContinue = None

		self.mPoster = poster
		self.mTime = None
		self.mFocus = None
		self.mAction = tools.Binge.actionNone()
		self.mContinue = self.mAction == tools.Binge.ActionContinue
		self.mFontSize = interface.Font.fontMedium() if self.mMode == WindowBinge.ModeOverlay else interface.Font.fontLarge()

		for action in [WindowBase.ActionMoveLeft, WindowBase.ActionMoveRight, WindowBase.ActionMoveUp, WindowBase.ActionMoveDown, WindowBase.ActionItemNext, WindowBase.ActionItemPrevious, WindowBase.ActionSelectItem]:
			self._onAction(action, self._actionFocus)

	@classmethod
	def show(self, background = None, poster = None, wait = False, initialize = True, close = False, title = None, season = None, episode = None, duration = None, delay = None):
		next = False
		result = super(WindowBinge, self)._show(backgroundType = tools.Settings.getInteger('interface.playback.interface.background'), backgroundPath = background, poster = poster, logo = WindowProgress.LogoIcon, status = interface.Translation.string(35582), wait = wait, initialize = initialize, close = close)
		if result:
			instance = self._instance()

			# Focus the Continue button so that it only takes one click to go to the next episode.
			instance._actionFocus()

			instance._setLabel(control = instance.mControlTitle, text = title, size = instance.mFontSize, bold = True, uppercase = True)
			instance._setLabel(control = instance.mControlEpisode, text = self._separator(['%s %s' % (interface.Translation.string(32055), self._highlight(season)), '%s %s' % (interface.Translation.string(33028), self._highlight(episode))]), size = instance.mFontSize, bold = True, uppercase = True)

			if duration:
				end = interface.Translation.string(33331) + ' ' + self._highlight(tools.Time.future(seconds = duration, format = tools.Time.FormatTimeShort, local = True).replace(':', interface.Format.fontColor(':', color = self._colorDefault())))
				duration = int(tools.Math.roundDown(float(duration) / 60.0))
				hours = int(tools.Math.roundDown(duration / 60.0))
				minutes = duration % 60
				duration = []
				if hours > 0: duration.append('%s %s' % (self._highlight(hours), interface.Translation.string(35617 if hours == 1 else 35618)))
				if minutes > 0: duration.append('%s %s' % (self._highlight(minutes), interface.Translation.string(35619 if minutes == 1 else 35620)))
				duration = ' '.join(duration)
				duration = self._separator([duration, end])
			else:
				duration = interface.Translation.string(33237)
			instance._setLabel(control = instance.mControlTime, text = duration, size = instance.mFontSize, bold = True, uppercase = True)

			if delay:
				delay = (delay * 1000) - 1000 # Subtract a little bit, since the window takes some time to show.
				self.update(progress = 0, time = int(delay / 1000.0))
				timer = tools.Time()
				timer.start()
				elapsed = 0
				while (delay - elapsed) > 1000 and instance.visible() and not tools.System.aborted():
					elapsed = timer.elapsed(milliseconds = True)
					self.update(progress = int((elapsed + 1000) / float(delay) * 100), time = int((delay - elapsed) / 1000.0))
					tools.Time.sleep(0.2)
				self.update(progress = 100, time = 0, finished = True)
				next = instance.mContinue
				instance.close()
		return result and next

	@classmethod
	def update(self, progress = None, finished = None, status = None, time = None):
		instance = super(WindowBinge, self).update(progress = progress, finished = finished, status = status)
		if instance is None: return instance
		instance._lock()

		if not time is None: instance.mTime = time

		if instance.mTime is None:
			instance.mStatus = ''
		else:
			label = 35582 if instance.mAction == tools.Binge.ActionContinue else 35629
			unit = 35630 if instance.mTime == 1 else 32405
			instance.mStatus = '%s %s %s' % (interface.Translation.string(label), self._highlight(instance.mTime), interface.Translation.string(unit))
		instance._setLabel(control = instance.mStatusControl, text = instance.mStatus, size = instance.mFontSize, bold = True, uppercase = True)

		instance._unlock()
		return instance

	@classmethod
	def cancel(self):
		try: self._instance()._actionCancel()
		except: pass

	def _actionFocus(self):
		if self.mMode == WindowBinge.ModeOverlay:
			if self.mFocus is True: self._actionFocusCancel()
			else: self._actionFocusContinue()
		else:
			if self.mFocus is False: self._actionFocusContinue()
			else: self._actionFocusCancel()

	def _actionFocusCancel(self):
		self.mFocus = False
		try: self.focus(self.mControlCancel[0])
		except: pass

	def _actionFocusContinue(self):
		self.mFocus = True
		try: self.focus(self.mControlContinue[0])
		except: pass

	def _actionCancel(self):
		self.mContinue = False
		self.close()

	def _actionContinue(self):
		self.mContinue = True
		self.close()

	def _addStatus(self, text = None):
		if text is None: text = self.mStatus
		if tools.Tools.isBoolean(text): text = ''
		self.mStatusControl, dimension = self._addLine(text = text, size = self.mFontSize)
		return dimension


class WindowBingeFull(WindowBinge):

	Padding = 30

	def __init__(self, backgroundType, backgroundPath, poster, logo, status):
		super(WindowBingeFull, self).__init__(mode = WindowBinge.ModeFull, backgroundType = backgroundType, backgroundPath = backgroundPath, poster = poster, logo = logo, status = status)

	def _initializeStart1(self):
		super(WindowBingeFull, self)._initializeStart1()
		self._dimensionUpdate(self._dimensionSeparator())
		self._dimensionUpdate(self._dimensionLine())
		self._dimensionUpdate(self._dimensionLine())
		self._dimensionUpdate(self._dimensionLine())
		self._dimensionUpdate(self._dimensionSeparator())
		self._dimensionUpdate(self._dimensionControls())

	def _initializeStart2(self):
		super(WindowBingeFull, self)._initializeStart2()
		self._dimensionUpdate(self._addSeparator1())
		self._dimensionUpdate(self._addTitle())
		self._dimensionUpdate(self._addEpisode())
		self._dimensionUpdate(self._addTime())
		self._dimensionUpdate(self._addSeparator2())
		self._dimensionUpdate(self._addControls())
		self._addCurtains()

	def _dimensionControls(self):
		dimensionCancel = self._dimensionCancel()
		dimensionContinue = self._dimensionContinue()
		return (WindowBingeFull.Padding + dimensionCancel[0] + dimensionContinue[0], max(dimensionCancel[1], dimensionContinue[1]))

	def _dimensionCancel(self):
		return self._dimensionButton(text = 33743, icon = True)

	def _dimensionContinue(self):
		return self._dimensionButton(text = 33821, icon = True)

	def _addSeparator1(self):
		control, dimension = self._addSeparator(control = True)
		return dimension

	def _addSeparator2(self):
		control, dimension = self._addSeparator(control = True)
		return dimension

	def _addTitle(self):
		self.mControlTitle, dimension = self._addLine()
		return dimension

	def _addEpisode(self):
		self.mControlEpisode, dimension = self._addLine()
		return dimension

	def _addTime(self):
		self.mControlTime, dimension = self._addLine()
		return dimension

	def _addControls(self):
		dimension = self._dimensionControls()
		y = self._offsetY() + 20
		x = self._centerX(dimension[0])
		self.mControlCancel = self._addButton(text = 33743, x = x, y = y, callback = self._actionCancel, icon = 'error')
		x += self._dimensionCancel()[0] + WindowBingeFull.Padding
		self.mControlContinue = self._addButton(text = 33821, x = x, y = y, callback = self._actionContinue, icon = 'play')
		return dimension


class WindowBingeOverlay(WindowBinge):

	SizeHeight = 110

	ButtonWidth = 150
	ButtonHeight = 40

	LogoIconWidth = 48
	LogoIconHeight = 48

	PosterWidth = 61
	PosterHeight = 90

	Padding = 10

	def __init__(self, backgroundType, backgroundPath, poster, logo, status):
		super(WindowBingeOverlay, self).__init__(mode = WindowBinge.ModeOverlay, backgroundType = backgroundType, backgroundPath = backgroundPath, poster = poster, logo = logo, status = status, height = WindowBingeOverlay.SizeHeight, inverse = True)

	def _initializeStart1(self):
		super(WindowBingeOverlay, self)._initializeStart1()
		self.mDimensionHeight += WindowBingeOverlay.Padding

	def _initializeStart2(self):
		super(WindowBingeOverlay, self)._initializeStart2()
		self._addSeparator()
		self._addPoster()
		self._addDetails()
		self._addControls()

	def _dimensionSpace(self):
		return [0, 0]

	def _dimensionLine(self):
		return [1200, 1]

	def _dimensionLogo(self, logo):
		if logo == WindowProgress.LogoIcon: return [self._scaleWidth(WindowBingeOverlay.LogoIconWidth), self._scaleHeight(WindowBingeOverlay.LogoIconHeight)]
		else: return [0, 0]

	def _dimensionButton(self, text = None, icon = None):
		width = len(self._buttonText(text = text, icon = icon)) * 10
		return [max(width, self._scaleWidth(WindowBingeOverlay.ButtonWidth)), self._scaleHeight(WindowBingeOverlay.ButtonHeight)]

	def _dimensionPoster(self, text = None, icon = None):
		return [self._scaleWidth(WindowBingeOverlay.PosterWidth), self._scaleHeight(WindowBingeOverlay.PosterHeight)]

	def _dimensionDetail(self):
		return [self._scaleWidth((self.mWidth / 2) - (3 * WindowBingeOverlay.Padding) - WindowBingeOverlay.PosterWidth), self._scaleHeight(20)]

	def _addSeparator(self):
		return self._addImage(self._pathImage('separator'), x = -5, y = self.mHeight, width = self.mWidth + 10, height = Window.SeparatorLineHeight)

	def _addPoster(self):
		if self.mPoster:
			dimension = self._dimensionPoster()
			self._addImage(path = self.mPoster, x = WindowBingeOverlay.Padding, y = WindowBingeOverlay.Padding, width = dimension[0], height = dimension[1])

	def _addDetails(self):
		x = (self._dimensionPoster()[0] + (2 * WindowBingeOverlay.Padding)) if self.mPoster else WindowBingeOverlay.Padding
		y = int(1.5 * WindowBingeOverlay.Padding)
		self.mControlTitle, dimension = self._addDetail(x = x, y = y)
		y += WindowBingeOverlay.Padding + dimension[1]
		self.mControlEpisode, dimension = self._addDetail(x = x, y = y)
		y += WindowBingeOverlay.Padding + dimension[1]
		self.mControlTime, dimension = self._addDetail(x = x, y = y)

	def _addDetail(self, x, y, text = ''):
		dimension = self._dimensionDetail()
		control = self._addLabel(text = text, x = x, y = y, width = dimension[0], height = dimension[1], color = self._colorDefault(), alignment = Window.AlignmentLeftCenter, bold = True, uppercase = True)
		return control, dimension

	def _addControls(self):
		dimensionContinue = self._dimensionButton(text = 33821, icon = 'play')
		dimensionCancel = self._dimensionButton(text = 33821, icon = 'play')
		width = max(dimensionContinue[0], dimensionCancel[0])
		height = max(dimensionContinue[1], dimensionCancel[1])
		x = self.mWidth - width - WindowBingeOverlay.Padding
		y = WindowBingeOverlay.Padding
		self.mControlContinue = self._addButton(text = 33821, x = x, y = y, width = width, height = height, callback = self._actionContinue, icon = 'play', size = interface.Font.fontMedium())
		y += height + WindowBingeOverlay.Padding
		self.mControlCancel = self._addButton(text = 33743, x = x, y = y, width = width, height = height, callback = self._actionCancel, icon = 'error', size = interface.Font.fontMedium())


class WindowStep(WindowProgress):

	ActionBack = None
	ActionBacked = None
	ActionClosed = None

	def __init__(self, backgroundType, backgroundPath, logo, stepper = True, helper = False, title = None, description = None, navigationCancel = True, navigationHelp = True, navigationBack = True, navigationNext = True, callbackClose = None, callbackCancel = None, callbackHelp = None, callbackBack = None, callbackNext = None, xml = False, xmlType = None, xmlOffset = None, **kwargs):
		super(WindowStep, self).__init__(backgroundType = backgroundType, backgroundPath = backgroundPath, logo = logo, xml = 'wizard' if xml is True else xml, xmlType = xmlType, xmlOffset = xmlOffset, **kwargs)

		if xml: self.mDirectory = interface.Directory(content = interface.Directory.ContentFiles, view = False, cache = True, lock = False)

		self.mStepper = stepper
		self.mHelper = helper
		self.mTitle = title
		self.mDescription = description

		self.mSeparator1 = None
		self.mSeparator2 = None

		self.mNavigation = None
		self.mNavigationIndex = None
		self.mNavigationRow = None
		self.mNavigationCount = None

		self.mNavigationCancel = navigationCancel
		self.mNavigationHelp = navigationHelp
		self.mNavigationBack = navigationBack
		self.mNavigationNext = navigationNext

		self.mCallbackClose = callbackClose
		self.mCallbackCancel = callbackCancel
		self.mCallbackHelp = callbackHelp
		self.mCallbackBack = callbackBack
		self.mCallbackNext = callbackNext

		self._onAction(WindowBase.ActionMoveLeft, self._actionFocus)
		self._onAction(WindowBase.ActionMoveRight, self._actionFocus)
		self._onAction(WindowBase.ActionMoveUp, self._actionFocus)
		self._onAction(WindowBase.ActionMoveDown, self._actionFocus)

		self._onAction(WindowBase.ActionContextMenu, self._actionHelp)
		self._onAction(WindowBase.ActionShowInfo, self._actionHelp)

		# All these actions make Kodi close the window by default.
		# ESC == ACTION_PREVIOUS_MENU
		# BACKSPACE == ACTION_NAV_BACK
		self._onAction(WindowBase.ActionNavigationBack, self.actionClose)
		self._onAction(WindowBase.ActionBackSpace, self.actionClose)
		self._onAction(WindowBase.ActionPreviousMenu, self.actionClose)

		if xml: self._onClick(Window.IdListControl, self.actionItem)

	def _initializeStart1(self, retry = False):
		super(WindowStep, self)._initializeStart1(progress = self.mStepper, status = self.mStepper)
		self._dimensionUpdate(self._dimensionSeparator(width = True))
		self._dimensionUpdate(self._dimensionContent())
		self._dimensionUpdate(self._dimensionSeparator(width = True))
		self._dimensionUpdate(self._dimensionNavigation())

	def _initializeStart2(self, retry = False):
		super(WindowStep, self)._initializeStart2(progress = self.mStepper, status = self.mStepper)
		self._dimensionUpdate(self._addSeparator1())
		self._dimensionUpdate(self._addContent())
		self._dimensionUpdate(self._addSeparator2())
		self._dimensionUpdate(self._addNavigation())

		if self.mTitle: self.propertySet(property = 'GaiaTitle', value = interface.Format.font(self.mTitle, color = interface.Format.colorSecondary(), bold = True, uppercase = True))
		if self.mDescription: self.propertySet(property = 'GaiaDescription%d' % (1 if len(interface.Translation.string(self.mDescription)) < 100 else 2), value = interface.Format.font(self.mDescription, bold = True))

	def _initializeEnd1(self):
		super(WindowStep, self)._initializeEnd1()
		self._addItems()

	def _initializeEnd2(self):
		super(WindowStep, self)._initializeEnd2()
		self._actionDefault()

	@classmethod
	def show(self, stepper = True, helper = False, navigationCancel = True, navigationHelp = True, navigationBack = True, navigationNext = True, callbackClose = None, callbackCancel = None, callbackHelp = None, callbackBack = None, callbackNext = None, **kwargs):
		return super(WindowStep, self).show(backgroundType = tools.Settings.getInteger('interface.playback.interface.background'), logo = WindowProgress.LogoIcon, stepper = stepper, helper = helper, navigationCancel = navigationCancel, navigationHelp = navigationHelp, navigationBack = navigationBack, navigationNext = navigationNext, callbackClose = callbackClose, callbackCancel = callbackCancel, callbackHelp = callbackHelp, callbackBack = callbackBack, callbackNext = callbackNext, **kwargs)

	def _actionDefault(self, focus = True):
		self.mNavigation = []
		if self.mNavigationCancel: self.mNavigation.append(self.mNavigationCancel)
		if self.mNavigationHelp: self.mNavigation.append(self.mNavigationHelp)
		if self.mNavigationBack: self.mNavigation.append(self.mNavigationBack)
		if self.mNavigationNext: self.mNavigation.append(self.mNavigationNext)
		if focus: self._actionFocus()

	def _actionFocus(self, action = None, multiple = False):
		if self._actionFocusBack(): return

		if self.mXml:
			if self.mNavigationRow is None: self.mNavigationRow = 0
			elif action == WindowBase.ActionMoveUp: self.mNavigationRow -= 1
			elif action == WindowBase.ActionMoveDown: self.mNavigationRow += 1

			if self.mNavigationRow < 0: self.mNavigationRow = 1
			elif self.mNavigationRow > 1: self.mNavigationRow = 0

			if self.mNavigationRow == 0:
				self.focus()
				return

		count = self.mNavigationCount
		if not count: count = 0

		try: navigation = [i for i in self.mNavigation if self._visible(i)]
		except: navigation = None
		if not navigation: return None

		self.mNavigationCount = len(navigation)
		maximum = self.mNavigationCount - 1

		if self.mNavigationIndex is None:
			self.mNavigationIndex = maximum
		elif self.mXml and (action == WindowBase.ActionMoveUp or action == WindowBase.ActionMoveDown): # Default to the Continue button for windows with a list.
			self.mNavigationIndex = maximum
		else:
			#self.mNavigationIndex += (self.mNavigationCount - count)
			if action == WindowBase.ActionMoveLeft: self.mNavigationIndex -= 1
			elif action == WindowBase.ActionMoveRight: self.mNavigationIndex += 1
			elif not multiple:
				if action == WindowBase.ActionMoveUp: self.mNavigationIndex -= 1
				elif action == WindowBase.ActionMoveDown: self.mNavigationIndex += 1

		if self.mNavigationIndex < 0: self.mNavigationIndex = maximum
		if self.mNavigationIndex > maximum: self.mNavigationIndex = 0

		self.focus(navigation[self.mNavigationIndex][0])

	def _actionRefocus(self):
		self.mNavigationIndex = None
		self._actionFocus()

	def _actionFocusBack(self, backed = False):
		# Ensure that when going back, the previous window's button is also focused on the "Back" button, instead of focusing the default control.
		if (not backed and WindowStep.ActionBack is True) or (backed and (WindowStep.ActionBack is True or WindowStep.ActionBacked is True)):
			WindowStep.ActionBack = None
			if backed: WindowStep.ActionBacked = None
			else: WindowStep.ActionBacked = True

			if self.mNavigationBack:
				self.mNavigationRow = 1
				try: self.mNavigationIndex = len([i for i in self.mNavigation if self._visible(i)]) - 2
				except: pass
				self.focus(self.mNavigationBack[0])
				return True

		return False

	# Virtual
	def _actionClose(self):
		if self.mCallbackClose: self.mCallbackClose()
		self.close()
		WindowStep.ActionClosed = True

	# Virtual
	def _actionCancel(self):
		self._actionClose()

	# Virtual
	def _actionHelp(self):
		pass

	# Virtual
	def _actionBack(self):
		pass

	# Virtual
	def _actionNext(self):
		return True

	def actionClose(self, control = None):
		self._actionClose()

	def actionCancel(self, control = None):
		if self.mCallbackCancel:
			if not self.mCallbackCancel(): return False
		self._actionCancel()
		return True

	def actionHelp(self, control = None):
		if self.mCallbackHelp: self.mCallbackHelp()
		self._actionHelp()

	def actionBack(self, control = None):
		WindowStep.ActionBack = True
		if self.mCallbackBack: self.mCallbackBack()
		self._actionBack()
		self._actionRefocus()

	def actionNext(self, control = None):
		WindowStep.ActionBack = None
		WindowStep.ActionBacked = None
		if self._actionNext():
			if self.mCallbackNext: self.mCallbackNext()
			self._actionRefocus()

	def actionItem(self):
		item = self.mItems[self.itemSelected()]
		if 'callback' in item and item['callback']: item['callback']()

	def _help(self, items, title = None):
		interface.Dialog.details(title = title if title else 36232, items = items)

	def _center(self):
		dimension = self._dimensionContent()
		x = int((Window.SizeWidth - dimension[0]) / 2.0)
		y = self._offsetY() + int(dimension[1] / 2.0)
		y += 5
		return x, y

	def _dimensionContent(self):
		return [self._scaleWidth(1200), 400]

	def _dimensionNavigation(self):
		return [self._scaleWidth(1200), 80]

	def _addSeparator1(self):
		self.mSeparator1, dimension = self._addSeparator(control = True, width = True, y = self._offsetY() + (25 if self.mStepper else 10))
		return dimension

	def _addSeparator2(self):
		self.mSeparator2, dimension = self._addSeparator(control = True, width = True, y = Window.SizeHeight - self._dimensionNavigation()[1] - self._dimensionSeparator()[1])
		return dimension

	def _addItems(self):
		pass

	def _addContent(self):
		return self._dimensionContent()

	def _addNavigation(self):
		dimension = self._dimensionNavigation()
		y = self._scaleHeight(Window.SizeHeight - dimension[1])
		window = Window.SizeWidth
		offset = self._scaleWidth(window) - dimension[0] + 40

		if self.mNavigationCancel: self.mNavigationCancel = self._addButton(text = 33743, x = offset, y = y, callback = self.actionCancel, icon = 'error')
		else: self.mNavigationCancel = None

		if self.mNavigationHelp: self.mNavigationHelp = self._addButton(text = 33239, x = offset + ((20 + self.mNavigationCancel[0].getWidth()) if self.mNavigationCancel else 0), y = y, callback = self.actionHelp, icon = 'help', highlight = self.mHelper)
		else: self.mNavigationHelp = None

		if self.mNavigationNext:
			label = 33821
			icon = 'next'
			if tools.Tools.isDictionary(self.mNavigationNext):
				if 'label' in self.mNavigationNext: label = self.mNavigationNext['label']
				if 'icon' in self.mNavigationNext: icon = self.mNavigationNext['icon']
			elif tools.Tools.isInteger(self.mNavigationNext):
				label = self.mNavigationNext
			dimensionNext = self._dimensionButton(text = label, icon = icon)
			self.mNavigationNext = self._addButton(text = label, x = window - offset - dimensionNext[0], y = y, callback = self.actionNext, icon = icon)
		else:
			self.mNavigationNext = None
			dimensionNext = [0, 0]

		if self.mNavigationBack:
			label = 36051
			icon = 'previous'
			if tools.Tools.isDictionary(self.mNavigationBack):
				if 'label' in self.mNavigationBack: label = self.mNavigationBack['label']
				if 'icon' in self.mNavigationBack: icon = self.mNavigationBack['icon']
			elif tools.Tools.isInteger(self.mNavigationBack):
				label = self.mNavigationBack
			dimensionBack = self._dimensionButton(text = label, icon = icon)
			self.mNavigationBack = self._addButton(text = label, x = window - offset - 20 - dimensionNext[0] - dimensionBack[0], y = y, callback = self.actionBack, icon = icon)
		else:
			self.mNavigationBack = None

		return dimension

	def _addItem(self, label = None, label1 = None, label2 = None, label3 = None, label4 = None, icon = None, selected = None, offset = None, callback = None):
		label = interface.Translation.string(label)
		item = self.mDirectory.item(label = label, label2 = label) if label else None
		item.setProperties({
			'GaiaIcon' : self._pathIcon(icon = icon, quality = interface.Icon.QualityLarge, special = interface.Icon.SpecialServices) if icon and not '.' in icon else icon,
			'GaiaSelected' : '' if selected is None else int(selected),
			'GaiaOffset' : offset if offset else 0,
			'GaiaLabel' : label,
			'GaiaLabel1' : interface.Translation.string(label1) if label1 else None,
			'GaiaLabel2' : interface.Translation.string(label2) if label2 else None,
			'GaiaLabel3' : interface.Translation.string(label3) if label3 else None,
			'GaiaLabel4' : interface.Translation.string(label4) if label4 else None,
		})
		return {'item' : item, 'callback' : callback}

	def _selectItem(self, index = None, item = None, selected = True):
		if item is None: item = self.mItems[index]['item']
		item.setProperty('GaiaSelected', '' if selected is None else str(int(selected)))


class WindowStepScroll(WindowStep):

	ScrollNone = None
	ScrollAuto = 'auto'	# Scroll permanently, even if the user selected an item from the list.
	ScrollOnce = 'once'	# Scroll until the user selected an item from the list.
	ScrollDefault = ScrollOnce

	FocusNone = None # Do not focus any control.
	FocusList = 'list' # Focus the list control.
	FocusNext = 'next' # Focus the Next button.
	FocusDefault = FocusList

	# Delay in seconds before autoscrolling starts.
	DelayShort = 2
	DelayLong = 5
	DelayDefault = DelayLong

	def __init__(self, scrollMode = ScrollDefault, scrollDelay = DelayDefault, scrollFocus = FocusDefault, xmlType = None, **kwargs):
		if scrollMode:
			if not xmlType: xmlType = []
			elif xmlType and not tools.Tools.isArray(xmlType): xmlType = [xmlType]
			if not Window.TypeWizardScroll in xmlType: xmlType.append(Window.TypeWizardScroll)

		super(WindowStepScroll, self).__init__(xmlType = xmlType, **kwargs)

		self.mScrollMode = scrollMode
		self.mScrollDelay = scrollDelay
		self.mScrollFocus = scrollFocus
		self.mScrollAction = False

	def _initializeEnd1(self):
		super(WindowStepScroll, self)._initializeEnd1()
		if self.mScrollMode == WindowStepScroll.ScrollOnce: Pool.thread(target = self._scroll, start = True)

	def _scroll(self):
		try:
			if self.mScrollDelay:
				self.propertySet(property = 'GaiaScroll', value = 0)
				tools.Time.sleep(self.mScrollDelay)
				self.propertySet(property = 'GaiaScroll', value = 1)

			while self.visible() and not tools.System.aborted():
				#if tools.System.visible('Control.HasFocus(%d)' % Window.IdListControl):
				if self.mScrollAction:
					self.propertySet(property = 'GaiaScroll', value = 0)
					break
				tools.Time.sleep(0.2)
		except: tools.Logger.error()

	def _actionDefault(self, focus = True):
		super(WindowStepScroll, self)._actionDefault(focus = False)
		if focus:
			if self._actionFocusBack(backed = True):
				return
			elif self.mScrollFocus == WindowStepScroll.FocusList:
				self.mNavigationRow = 0
				self.focus()
			elif self.mScrollFocus == WindowStepScroll.FocusNext:
				self.mNavigationRow = 1
				super(WindowStepScroll, self)._actionFocus()

	def _actionFocus(self, action = None, multiple = False):
		self.mScrollAction = True
		super(WindowStepScroll, self)._actionFocus(action = action, multiple = multiple)

	def actionItem(self):
		self.mScrollAction = True
		super(WindowStepScroll, self).actionItem()


class WindowStepQr(WindowStepScroll):

	Thread = None

	def __init__(self, data, title = None, description = None, **kwargs):
		super(WindowStepQr, self).__init__(title = title, description = description, xml = True, xmlType = [Window.TypeWizardLarge, Window.TypeWizardQr], **kwargs)
		self.mData = data

	@classmethod
	def show(self, data = None, stepper = False, navigationCancel = False, navigationBack = False, navigationNext = None, callbackNext = None, **kwargs):
		data = self.prepare(data = data, loader = True)
		if navigationNext is None: navigationNext = {'label' : 33486, 'icon' : 'error'}
		if callbackNext is None: callbackNext = self.close
		return super(WindowStepQr, self).show(data = data, stepper = stepper, navigationCancel = navigationCancel, navigationBack = navigationBack, navigationNext = navigationNext, callbackNext = callbackNext, **kwargs)

	@classmethod
	def prepare(self, data = None, loader = False, wait = True):
		# Use self.Thread to use a different variable for each subclass.
		if self.Thread: # Still busy from a previous call to prepare().
			self.Thread.join()
			self.Thread = None

		if wait:
			return self._prepare(data = data, loader = loader)
		else:
			self.Thread = Pool.thread(target = self._prepare, kwargs = {'data' : None, 'loader' : loader}, start = True)
			return self.Thread

	@classmethod
	def _prepare(self, data = None, loader = False):
		if loader: interface.Loader.show()
		if data is None: data = self._prepareRetrieve(data = data)
		self._qrGenerate(data = self._prepareSelect(data = data))
		if loader: interface.Loader.hide()
		return data

	@classmethod
	def _prepareRetrieve(self, data = None):
		return data

	@classmethod
	def _prepareSelect(self, data = None):
		return data

	def _actionItem(self, link = None, symbol = None, color = None, icon = None):
		donations = self.mData if self.mData and 'payment' in self.mData[0] else None
		WindowQr.show(link = link, symbol = symbol, color = color, icon = icon, donations = donations, permanent = True)

	def _addItems(self):
		items = []
		datas = self._prepareSelect(data = self.mData)
		if datas:
			for data in datas:
				items.append(self._addQr(data = data))
		self.itemAdd(item = items)

	def _addQr(self, data):
		from lib.modules.network import Networker

		try: link = data['link']
		except: link = None
		try: name = data['name']
		except: name = None
		try: symbol = data['symbol']
		except: symbol = None
		try: wallet = data['address']
		except: wallet = None
		try: payment = data['payment']
		except: payment = None
		try: color = data['color']
		except: color = None

		label = WindowQr._donationColor(value = name, color = color)

		label1 = link if link else wallet
		if Networker.linkIs(label1) and not Networker.linkPath(label1) and not Networker.linkParameters(label1):
			label1 = Networker.linkDomain(label1)
		label1 = WindowQr._donationColor(value = label1, color = color)

		if symbol == 'gaia':
			icon = tools.File.joinPath(self._pathLogo(size = interface.Icon.QualitySmall), 'iconcolor.png')
			color = None
		else:
			icon = self._pathIcon(icon = symbol, quality = interface.Icon.QualitySmall, special = interface.Icon.SpecialDonations if wallet else interface.Icon.SpecialServices)

		qr = self._qrGenerate(data = link if link else payment, color = color)

		item = self._addItem(label = label, label1 = label1, icon = icon, callback = lambda : self._actionItem(link = link, symbol = symbol, color = color, icon = icon))
		item['item'].setProperties({
			'GaiaIconSmall' : icon,
			'GaiaQr' : qr,
		})
		return item

	@classmethod
	def _qrGenerate(self, data = None, color = None, permanent = True):
		from lib.modules.qr import Qr
		cache = Qr.CachePermanent if permanent else Qr.CacheTemporary
		if tools.Tools.isArray(data):
			data = [{'data' : i['payment'] if 'payment' in i else i['link'], 'colorFront' : [interface.Format.colorDarker(color = i['color'], change = 70), i['color']], 'truncate' : False, 'cache' : cache} for i in data]
			Qr.generate(*data)
		else:
			if color: color = [interface.Format.colorDarker(color = color, change = 70), color]
			else: color = Qr.ColorGaia
			qr = Qr.generate(data = data, colorFront = color, truncate = False, cache = cache)
			return qr


class WindowAttribution(WindowStepQr):

	def __init__(self, **kwargs):
		super(WindowAttribution, self).__init__(description = 33986, scrollDelay = WindowStepScroll.DelayShort, **kwargs)

	@classmethod
	def _prepareRetrieve(self, data = None):
		if data is None:
			data = [
				{'symbol' : 'tvdb', 'name' : 35668, 'link' : 'https://thetvdb.com', 'color' : 'FF1C7E3E'},
				{'symbol' : 'tmdb', 'name' : 33508, 'link' : 'https://themoviedb.org', 'color' : 'FF44C0C5'},
				{'symbol' : 'trakt', 'name' : 32315, 'link' : 'https://trakt.tv', 'color' : 'FFED1C24'},
				{'symbol' : 'imdb', 'name' : 32034, 'link' : 'https://imdb.com', 'color' : 'FFF6C700'},
				{'symbol' : 'tvmaze', 'name' : 35669, 'link' : 'https://tvmaze.com', 'color' : 'FF3D948B'},
				{'symbol' : 'fanart', 'name' : 35260, 'link' : 'https://fanart.tv', 'color' : 'FF21B6E1'},
				{'symbol' : 'opensubtitles', 'name' : 35683, 'link' : 'https://opensubtitles.org', 'color' : 'FFC1DC14'},
			]
		return data

	def _actionHelp(self):
		self._help(items = [
			{'type' : 'title', 'value' : 'Attributions', 'break' : 2},
			{'type' : 'text', 'value' : 'Gaia uses metadata, images, and subtitles from a variety of projects which offer their services for free. Consider supporting these projects by donating to them, getting a premium subscription, or by helping to add new information to their databases.', 'break' : 2},
			{'type' : 'text', 'value' : 'Certain services, including TMDb, TVDb, TVmaze, and Fanart, can be used in Gaia without an account. However, you can still authenticate a custom account for these services in the settings.', 'break' : 2},
		])


class WindowDonation(WindowStepQr):

	# Do not use too many, otherwise QR generation takes too long.
	Order = ['gaia', 'btc', 'bch', 'eth', 'ada', 'ltc', 'xrp', 'doge', 'shib', 'xmr', 'pp']

	def __init__(self, stepper, **kwargs):
		super(WindowDonation, self).__init__(title = None if stepper else 36279, description = 33974, stepper = stepper, **kwargs)

	@classmethod
	def _prepareRetrieve(self, data = None):
		if data is None:
			from lib.modules.api import Api
			data = Api.donation(cache = True)
		return data

	@classmethod
	def _prepareSelect(self, data = None):
		result = []
		if data:
			for choice in WindowDonation.Order:
				for item in data:
					if 'symbol' in item and choice == item['symbol']:
						if item['enabled']: result.append(item)
						break
		return result

	def _actionHelp(self):
		color = interface.Format.colorSecondary()
		donation = interface.Format.fontColor('We prefer cryptocurrencies above PayPal donations.', color = color)
		bitcoin = interface.Format.fontColor('Bitcoin', color = color)
		ethereum = interface.Format.fontColor('Ethereum', color = color)
		self._help(items = [
			{'type' : 'title', 'value' : 'Donations', 'break' : 2},
			{'type' : 'text', 'value' : 'Developing and maintaining Gaia is an enormous task. Gaia is open-source and will always be free. Please consider donating to keep the project going. Even a few bucks can greatly help to cover the basic costs of maintaining the addon.', 'break' : 2},
			{'type' : 'text', 'value' : '%s Due to the nature of the project, donations through PayPal are not reliable and much of the money is lost due PayPal fees and policies.' % donation, 'break' : 2},
			{'type' : 'text', 'value' : 'Donations are used to pay for Gaia\'s website, domain, and server, subscribe to debrid and other premium services used during development and testing, implementing new features, and donating to other open-source projects that Gaia relies on.', 'break' : 2},
			{'type' : 'text', 'value' : 'Donating to Gaia does not entitle you to special treatment. However, if you have a feature request, it will be moved to the top of our To-Do list if it is accompanied by a donation.', 'break' : 2},
			{'type' : 'title', 'value' : 'Crypto', 'break' : 2},
			{'type' : 'text', 'value' : 'Getting your hands on some crypto coins is easy these days. We prefer %s or %s, but all coins are welcome.' % (bitcoin, ethereum), 'break' : 2},
			{'type' : 'text', 'value' : 'Some apps, like [B]CashApp[/B] for the US and UK, are an all-in-one solution for purchasing and storing your crypto.', 'break' : 2},
			{'type' : 'link', 'value' : 'https://cash.app', 'break' : 2},
			{'type' : 'text', 'value' : 'Another approach is to buy crypto from an exchange. There are many crypto exchanges worldwide. Some are only available in certain countries. Some exchanges require ID verification before being able to purchase crypto, while others, like [B]Binance[/B], allow you to anonymously buy small amounts of crypto without the need to verify your ID.', 'break' : 2},
			{'type' : 'link', 'value' : 'https://binance.com', 'break' : 1},
			{'type' : 'link', 'value' : 'https://coinbase.com', 'break' : 1},
			{'type' : 'link', 'value' : 'https://ftx.com', 'break' : 1},
			{'type' : 'link', 'value' : 'https://kraken.com', 'break' : 1},
			{'type' : 'link', 'value' : 'https://kucoin.com', 'break' : 2},
			{'type' : 'text', 'value' : 'You can leave your crypto on the exchange\'s wallet, especially small amounts. However, exchanges sometimes get hacked and it is better to transfer your crypto out of the exchange into a personal wallet. [B]Exodus[/B] is an easy-to-use wallet, available on most operating systems, and supports hundreds of different coins.', 'break' : 2},
			{'type' : 'link', 'value' : 'https://exodus.com', 'break' : 1},
		])


class WindowOptimization(WindowStep):

	SizeIcon = 128
	SizeRating = 200

	CategoryScrape = 'scrape'
	CategoryProvider = 'provider'

	# Must be thew same as manager.py.
	TradeoffSpeed = 'speed'
	TradeoffResult = 'result'
	TradeoffMixed = 'mixed'

	StepIntroduction = 'introduction'
	StepDiagnostics = 'diagnostics'
	StepRating = 'rating'
	StepPreferences = 'preferences'

	# This allows us to go back a single step in the setup wizard to the tradoff, instead of going back to the introduction and having to redo the diagnosis.
	DiagnoseData = None
	DiagnoseScrape = None
	DiagnoseProvider = None

	def __init__(self, navigationCategory, callbackDiagnose, callbackTradeoff, **kwargs):
		super(WindowOptimization, self).__init__(**kwargs)

		self.mIntroduction = None

		self.mDiagnoseProgress = 0
		self.mDiagnoseProgressInner = None
		self.mDiagnoseProgressOuter = None
		self.mDiagnoseProgressFill = None
		self.mDiagnoseProgressLabel = None

		self.mRatingDevice = None
		self.mRatingProcessor = None
		self.mRatingMemory = None
		self.mRatingStorage = None
		self.mRatingConnection = None
		self.mRatingHeading = None
		self.mRatingLabel = None

		self.mCategory = []
		self.mCategoryEnabled = navigationCategory
		self.mCategoryOptions = None
		self.mCategoryScrape = None
		self.mCategoryProvider = None
		self.mCategoryHeading = None
		self.mCategoryLabel = None

		self.mTradeoffOptions = None
		self.mTradeoffSpeed = None
		self.mTradeoffMixed = None
		self.mTradeoffResult = None
		self.mTradeoffHeading = None
		self.mTradeoffLabel = None

		self.mPreferencesHeading = None
		self.mPreferencesLabel = None
		self.mPreferencesSeparator1 = None
		self.mPreferencesSeparator2 = None

		self.mNavigationRow = None

		self.mStep = WindowOptimization.StepIntroduction
		self.mCallbackDiagnose = callbackDiagnose
		self.mCallbackTradeoff = callbackTradeoff

		self.mDataDiagnose = None
		self.mDataSettings = None

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		WindowOptimization.DiagnoseData = None
		WindowOptimization.DiagnoseScrape = None
		WindowOptimization.DiagnoseProvider = None

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def show(self, wait = False, stepper = False, navigationCancel = True, navigationHelp = True, navigationBack = True, navigationNext = True, navigationCategory = True, callbackClose = None, callbackCancel = None, callbackHelp = None, callbackBack = None, callbackNext = None, callbackDiagnose = None, callbackTradeoff = None, **kwargs):
		return super(WindowOptimization, self).show(wait = wait, stepper = stepper, navigationCancel = navigationCancel, navigationHelp = navigationHelp, navigationBack = navigationBack, navigationNext = navigationNext, navigationCategory = navigationCategory, callbackClose = callbackClose, callbackCancel = callbackCancel, callbackHelp = callbackHelp, callbackBack = callbackBack, callbackNext = callbackNext, callbackDiagnose = callbackDiagnose, callbackTradeoff = callbackTradeoff, **kwargs)

	@classmethod
	def update(self, progress = None, finished = None, status = None, diagnoseProgress = None, diagnoseStatus = None, diagnoseData = None, diagnoseScrape = True, diagnoseProvider = True, internal = False):
		instance = self._updateProgress(progress = progress, finished = finished, status = status)
		if diagnoseStatus:
			instance._setLabel(control = instance.mDiagnoseProgressLabel, text = diagnoseStatus, uppercase = True, bold = True)
		if diagnoseProgress:
			instance._progressUpdate(progressNew = diagnoseProgress, progressCurrent = instance.mDiagnoseProgress, controlFill = instance.mDiagnoseProgressFill, controlIcon = instance.mDiagnoseProgressInner)
			instance.mDiagnoseProgress = diagnoseProgress
		if diagnoseData:
			instance.mDataDiagnose = diagnoseData
			instance._actionDiagnostics(internal = internal)
			instance.mCategory = [] # Important for navigating back and redoing the diagnostics. Otherwise the settings labels are not populated.
			if diagnoseScrape: instance._actionCategory(control = instance.mCategoryScrape)
			if diagnoseProvider: instance._actionCategory(control = instance.mCategoryProvider)
			instance._actionTradeoff(control = instance.mTradeoffMixed)

			WindowOptimization.DiagnoseData = diagnoseData
			WindowOptimization.DiagnoseScrape = diagnoseScrape
			WindowOptimization.DiagnoseProvider = diagnoseProvider

	@classmethod
	def _updateProgress(self, progress = None, finished = None, status = None, force = False):
		return super(WindowOptimization, self).update(progress = progress, finished = finished, status = status, force = force)

	@classmethod
	def data(self, clear = True):
		data = WindowOptimization.DiagnoseData
		WindowOptimization.DiagnoseData = None
		return data

	def _initializeStart2(self):
		super(WindowOptimization, self)._initializeStart2()
		self._toggleDiagnostics(visible = False)
		self._toggleRating(visible = False)
		self._togglePreferences(visible = False)
		self._toggleIntroduction(visible = not bool(WindowOptimization.DiagnoseData))

	def _initializeEnd2(self):
		super(WindowOptimization, self)._initializeEnd2()
		self.mCategoryOptions = [self.mCategoryScrape, self.mCategoryProvider]
		self.mTradeoffOptions = [self.mTradeoffSpeed, self.mTradeoffMixed, self.mTradeoffResult]
		if WindowOptimization.DiagnoseData:
			self.update(diagnoseData = WindowOptimization.DiagnoseData, diagnoseScrape = WindowOptimization.DiagnoseScrape, diagnoseProvider = WindowOptimization.DiagnoseProvider, internal = True)
			self.mStep = WindowOptimization.StepPreferences
			self._toggleIntroduction(visible = False)
			self._toggleDiagnostics(visible = False)
			self._toggleRating(visible = False)
			self._togglePreferences(visible = True)

	def _actionFocus(self, action = None):
		if self.mStep == WindowOptimization.StepPreferences:
			if self.mNavigationRow is None: self.mNavigationRow = 2

			if action == WindowBase.ActionMoveUp: self.mNavigationRow -= 1
			elif action == WindowBase.ActionMoveDown: self.mNavigationRow += 1

			if self.mNavigationRow < 0: self.mNavigationRow = 2
			elif self.mNavigationRow > 2: self.mNavigationRow = 0

			if not self.mCategoryEnabled and self.mNavigationRow == 0:
				if action == WindowBase.ActionMoveUp: self.mNavigationRow = 2
				elif action == WindowBase.ActionMoveDown: self.mNavigationRow = 1

			if self.mNavigationRow == 2:
				super(WindowOptimization, self)._actionFocus(action = action, multiple = True)
			elif self.mNavigationRow == 1:
				maximum = len(self.mTradeoffOptions) - 1

				if self.mNavigationIndex is None: self.mNavigationIndex = maximum
				elif action == WindowBase.ActionMoveLeft: self.mNavigationIndex -= 1
				elif action == WindowBase.ActionMoveRight: self.mNavigationIndex += 1

				if self.mNavigationIndex < 0:
					if action in [WindowBase.ActionMoveUp, WindowBase.ActionMoveDown]: self.mNavigationIndex = 0
					else: self.mNavigationIndex = maximum
				if self.mNavigationIndex > maximum:
					if action in [WindowBase.ActionMoveUp, WindowBase.ActionMoveDown]: self.mNavigationIndex = maximum
					else: self.mNavigationIndex = 0

				self.focus(self.mTradeoffOptions[self.mNavigationIndex][0])
			elif self.mNavigationRow == 0:
				maximum = len(self.mCategoryOptions) - 1

				if self.mNavigationIndex is None: self.mNavigationIndex = maximum
				elif action == WindowBase.ActionMoveLeft: self.mNavigationIndex -= 1
				elif action == WindowBase.ActionMoveRight: self.mNavigationIndex += 1

				if self.mNavigationIndex < 0:
					if action in [WindowBase.ActionMoveUp, WindowBase.ActionMoveDown]: self.mNavigationIndex = 0
					else: self.mNavigationIndex = maximum
				if self.mNavigationIndex > maximum:
					if action in [WindowBase.ActionMoveUp, WindowBase.ActionMoveDown]: self.mNavigationIndex = maximum
					else: self.mNavigationIndex = 0

				self.focus(self.mCategoryOptions[self.mNavigationIndex][0])
		else:
			super(WindowOptimization, self)._actionFocus(action = action)

	def actionBack(self):
		WindowStep.ActionBack = True
		if self.mStep == WindowOptimization.StepIntroduction:
			if self.mCallbackBack: return  self.mCallbackBack()
		elif self.mStep == WindowOptimization.StepRating:
			self.mStep = WindowOptimization.StepIntroduction
			self._toggleRating(visible = False)
			self._toggleIntroduction(visible = True)
		elif self.mStep == WindowOptimization.StepPreferences:
			self.mStep = WindowOptimization.StepRating
			self._togglePreferences(visible = False)
			self._toggleRating(visible = True)
		self._actionRefocus()

	def actionNext(self):
		self._actionNext()
		if not self.mStep in [WindowOptimization.StepDiagnostics, WindowOptimization.StepPreferences]: self._actionRefocus()

	def _actionNext(self):
		if self.mStep == WindowOptimization.StepIntroduction:
			self.mStep = WindowOptimization.StepDiagnostics
			self._toggleIntroduction(visible = False)
			self._toggleDiagnostics(visible = True)
			self._progressClear(controlFill = self.mDiagnoseProgressFill, controlIcon = self.mDiagnoseProgressInner)
			self.mCallbackDiagnose()
		elif self.mStep == WindowOptimization.StepRating:
			self.mStep = WindowOptimization.StepPreferences
			self._toggleRating(visible = False)
			self._togglePreferences(visible = True)
		elif self.mStep == WindowOptimization.StepPreferences:
			if self.mCallbackNext:
				updateScrape = WindowOptimization.CategoryScrape in self.mCategory
				updateProvider =  WindowOptimization.CategoryProvider in self.mCategory
				self.mCallbackNext(data = self.mDataSettings, updateScrape = updateScrape, updateProvider = updateProvider)
			self.close()

	def _actionCategory(self, control):
		if not tools.Tools.isDictionary(control): control = self._get(control = control)
		try: control = control['control']
		except: pass

		if control == self.mCategoryScrape[0]:
			if WindowOptimization.CategoryScrape in self.mCategory:
				self._selectButton(control = self.mCategoryScrape, select = Window.SelectHide)
				self.mCategory.remove(WindowOptimization.CategoryScrape)
			else:
				self._selectButton(control = self.mCategoryScrape, select = Window.SelectYes)
				self.mCategory.append(WindowOptimization.CategoryScrape)
		elif control == self.mCategoryProvider[0]:
			if WindowOptimization.CategoryProvider in self.mCategory:
				self._selectButton(control = self.mCategoryProvider, select = Window.SelectHide)
				self.mCategory.remove(WindowOptimization.CategoryProvider)
			else:
				self._selectButton(control = self.mCategoryProvider, select = Window.SelectYes)
				self.mCategory.append(WindowOptimization.CategoryProvider)

		if WindowOptimization.CategoryScrape in self.mCategory and WindowOptimization.CategoryProvider in self.mCategory: label = 36145
		elif WindowOptimization.CategoryScrape in self.mCategory: label = 36143
		elif WindowOptimization.CategoryProvider in self.mCategory: label = 36144
		else: label = 36146
		self._setLabel(control = self.mCategoryLabel, text = interface.Translation.string(label), bold = True)

		self._actionTradeoff() # Update the settings labels.

	def _actionTradeoff(self, control = None):
		try:
			if control:
				label = None
				tradeoff = None

				if not tools.Tools.isDictionary(control): control = self._get(control = control)
				try: control = control['control']
				except: pass

				if control == self.mTradeoffSpeed[0]:
					label = 36053
					tradeoff = WindowOptimization.TradeoffSpeed
					self._selectButton(control = self.mTradeoffSpeed, select = Window.SelectYes)
				else:
					self._selectButton(control = self.mTradeoffSpeed, select = Window.SelectHide)

				if control == self.mTradeoffMixed[0]:
					label = 36055
					tradeoff = WindowOptimization.TradeoffMixed
					self._selectButton(control = self.mTradeoffMixed, select = Window.SelectYes)
				else:
					self._selectButton(control = self.mTradeoffMixed, select = Window.SelectHide)

				if control == self.mTradeoffResult[0]:
					label = 36054
					tradeoff = WindowOptimization.TradeoffResult
					self._selectButton(control = self.mTradeoffResult, select = Window.SelectYes)
				else:
					self._selectButton(control = self.mTradeoffResult, select = Window.SelectHide)

				self._setLabel(control = self.mTradeoffLabel, text = interface.Translation.string(label), bold = True)

				if not tradeoff: tradeoff = WindowOptimization.TradeoffMixed
				self.mDataSettings = self.mCallbackTradeoff(data = self.mDataDiagnose, tradeoff = tradeoff)

			if self.mDataSettings:
				label1 = []
				label2 = []
				if WindowOptimization.CategoryProvider in self.mCategory:
					label1.extend([(32345, self.mDataSettings['label']['providers'])])
				if WindowOptimization.CategoryScrape in self.mCategory:
					label1.extend([
						(33273, self.mDataSettings['label']['time']),
						(32035, self.mDataSettings['label']['query']),
						(35810, self.mDataSettings['label']['page']),
						#(36042, self.mDataSettings['label']['concurrency']),
					])
					label2.extend([
						(33167, self.mDataSettings['label']['pack']),
						(33881, self.mDataSettings['label']['title']),
						(35484, self.mDataSettings['label']['keyword']),
						(35830, self.mDataSettings['label']['mirror']),
					])
				label = ''
				if label1: label += self._labelDetails(label1)
				if label1 and label2: label += interface.Format.newline()
				if label2: label += self._labelDetails(label2)
				self._setLabel(control = self.mPreferencesLabel, text = label, bold = True)
		except: tools.Logger.error()

	def _actionDiagnostics(self, internal = False):
		label = [(36046, self.mDataDiagnose['performance']['processor']['label']['device']), (35004, self.mDataDiagnose['performance']['memory']['label']['device']), (33350, self.mDataDiagnose['performance']['storage']['label']['device']), (33404, self.mDataDiagnose['performance']['connection']['label']['device'])]
		self._setLabel(control = self.mRatingLabel, text = self._labelDetails(label), bold = True)

		font = interface.Font.fontMassive(full = True)
		self._setLabel(control = self.mRatingDevice['middle'], text = self._labelRating(self.mDataDiagnose['performance']['label']['rating']), bold = not font['bold'])
		self._setLabel(control = self.mRatingDevice['bottom'], text = self._labelPerformance(self.mDataDiagnose['performance']['label']['performance']), bold = True)
		self._setLabel(control = self.mRatingProcessor['middle'], text = self._labelRating(self.mDataDiagnose['performance']['processor']['label']['rating']), bold = not font['bold'])
		self._setLabel(control = self.mRatingProcessor['bottom'], text = self._labelPerformance(self.mDataDiagnose['performance']['processor']['label']['performance']), bold = True)
		self._setLabel(control = self.mRatingMemory['middle'], text = self._labelRating(self.mDataDiagnose['performance']['memory']['label']['rating']), bold = not font['bold'])
		self._setLabel(control = self.mRatingMemory['bottom'], text = self._labelPerformance(self.mDataDiagnose['performance']['memory']['label']['performance']), bold = True)
		self._setLabel(control = self.mRatingStorage['middle'], text = self._labelRating(self.mDataDiagnose['performance']['storage']['label']['rating']), bold = not font['bold'])
		self._setLabel(control = self.mRatingStorage['bottom'], text = self._labelPerformance(self.mDataDiagnose['performance']['storage']['label']['performance']), bold = True)
		self._setLabel(control = self.mRatingConnection['middle'], text = self._labelRating(self.mDataDiagnose['performance']['connection']['label']['rating']), bold = not font['bold'])
		self._setLabel(control = self.mRatingConnection['bottom'], text = self._labelPerformance(self.mDataDiagnose['performance']['connection']['label']['performance']), bold = True)

		self._setButton(control = self.mNavigationNext, text = 33821, icon = 'next')

		self.mStep = WindowOptimization.StepRating
		if not internal:
			self._toggleDiagnostics(visible = False)
			self._toggleRating(visible = True)

	def _toggleIntroduction(self, visible):
		self._visibleSet(control = self.mIntroduction, visible = visible)
		self._visibleSet(control = self.mNavigationBack, visible = self.mStepper)
		if visible:
			if self.mStepper: self._updateProgress(progress = WindowWizard.ProgressOptimization['introduction'], force = True)
			else: self._setButton(control = self.mNavigationNext, text = 36138, icon = 'diagnostic')

	def _toggleDiagnostics(self, visible):
		self._visibleSet(control = self.mNavigationBack, visible = not visible)
		self._visibleSet(control = self.mNavigationNext, visible = not visible)
		self._visibleSet(control = self.mDiagnoseProgressInner, visible = visible)
		self._visibleSet(control = self.mDiagnoseProgressOuter, visible = visible)
		self._visibleSet(control = self.mDiagnoseProgressLabel, visible = visible)
		if visible and self.mStepper: self._updateProgress(progress = WindowWizard.ProgressOptimization['diagnostics'], force = True)

	def _toggleRating(self, visible):
		self._visibleSet(control = self.mRatingDevice, visible = visible)
		self._visibleSet(control = self.mRatingProcessor, visible = visible)
		self._visibleSet(control = self.mRatingMemory, visible = visible)
		self._visibleSet(control = self.mRatingStorage, visible = visible)
		self._visibleSet(control = self.mRatingConnection, visible = visible)
		self._visibleSet(control = self.mRatingHeading, visible = visible)
		self._visibleSet(control = self.mRatingLabel, visible = visible)
		if visible:
			if self.mStepper: self._updateProgress(progress = WindowWizard.ProgressOptimization['rating'], force = True)
			else: self._setButton(control = self.mNavigationNext, text = 33821, icon = 'next')

	def _togglePreferences(self, visible):
		visibleCategory = visible and self.mCategoryEnabled

		self._visibleSet(control = self.mPreferencesSeparator1, visible = visibleCategory)
		self._visibleSet(control = self.mPreferencesSeparator2, visible = visible)
		self._visibleSet(control = self.mPreferencesHeading, visible = visible)
		self._visibleSet(control = self.mPreferencesLabel, visible = visible)

		self._visibleSet(control = self.mCategoryScrape, visible = visibleCategory)
		self._visibleSet(control = self.mCategoryProvider, visible = visibleCategory)
		self._visibleSet(control = self.mCategoryHeading, visible = visibleCategory)
		self._visibleSet(control = self.mCategoryLabel, visible = visibleCategory)

		self._visibleSet(control = self.mTradeoffSpeed, visible = visible)
		self._visibleSet(control = self.mTradeoffMixed, visible = visible)
		self._visibleSet(control = self.mTradeoffResult, visible = visible)
		self._visibleSet(control = self.mTradeoffHeading, visible = visible)
		self._visibleSet(control = self.mTradeoffLabel, visible = visible)

		if visible:
			if self.mStepper: self._updateProgress(progress = WindowWizard.ProgressOptimization['preferences'], force = True)
			else: self._setButton(control = self.mNavigationNext, text = 35269, icon = 'speed')

	def _labelRating(self, value):
		return value if value else '0%'

	def _labelPerformance(self, value):
		return value if value else interface.Translation.string(33387)

	def _labelDetails(self, values):
		return interface.Format.iconJoin(['%s %s' % (interface.Translation.string(i[0]) + ':', interface.Format.fontColor(self._labelPerformance(i[1]), color = interface.Format.colorPrimary())) for i in values])

	def _dimensionTradeoff(self):
		return [1200, 200]

	def _addContent(self):
		dimension = super(WindowOptimization, self)._addContent()
		self._addIntroduction(dimension = dimension)
		self._addDiagnostics(dimension = dimension)
		self._addRating(dimension = dimension)
		self._addPreferences(dimension = dimension)
		return dimension

	def _addIntroduction(self, dimension):
		height = 200
		x, y = self._center()
		self.mIntroduction = self._addLabel(text = interface.Translation.string(35005), x = x, y = y - int(height / 2.0) + 10, width = dimension[0], height = height, alignment = Window.AlignmentCenter, size = interface.Font.fontLarge(), bold = True)

	def _addDiagnostics(self, dimension):
		height = 20
		x, y = self._center()
		_, self.mDiagnoseProgressInner, self.mDiagnoseProgressOuter, self.mDiagnoseProgressFill = self._addProgressBar(y = y - height)
		self.mDiagnoseProgressLabel = self._addLabel(text = '', x = x, y = y + height, width = dimension[0], height = height, alignment = Window.AlignmentCenter, size = interface.Font.fontLarge(), color = self._colorHighlight(), uppercase = True, bold = True)

	def _addRating(self, dimension):
		width = WindowOptimization.SizeRating
		pad = 20
		offsetX = (1 - self.mScaleWidth) * 80

		x, y = self._center()
		spacing = 160

		self.mRatingHeading = self._addLabel(text = interface.Translation.string(36140), x = x, y = y - spacing, width = dimension[0], height = 20, alignment = Window.AlignmentCenter, size = interface.Font.fontBig(), color = interface.Format.colorSecondary(), bold = True, uppercase = True)
		self._visibleSet(control = self.mRatingHeading, visible = False)

		offset = 0 if self.mStepper else 20
		self.mRatingDevice = self._addRatingSection(type = 'device', label = 35012, offsetX = offsetX -((width / 2.0) + (pad / 2.0)), offsetY = -(WindowOptimization.SizeIcon - offset))
		self.mRatingProcessor = self._addRatingSection(type = 'processor', label = 36046, offsetX = offsetX -(2 * (width + pad)))
		self.mRatingMemory = self._addRatingSection(type = 'memory', label = 35004, offsetX = offsetX -(width + (pad / 2.0)))
		self.mRatingStorage = self._addRatingSection(type = 'storage', label = 33350, offsetX = offsetX + (pad / 2.0))
		self.mRatingConnection = self._addRatingSection(type = 'connection', label = 33404, offsetX = offsetX + (width + pad))

		self.mRatingLabel = self._addLabel(text = '', x = x, y = y + spacing, width = dimension[0], height = 20, alignment = Window.AlignmentCenter, size = interface.Font.fontSmall(), bold = True)

	def _addRatingSection(self, type, label, offsetX = 0, offsetY = 0, large = False):
		widthIcon = self._scaleWidth(WindowOptimization.SizeIcon)
		heightIcon = self._scaleHeight(WindowOptimization.SizeIcon)

		offsetX = int(offsetX)
		offsetY = int(offsetY)

		x, y = self._center()
		x = self._centerX(0) + offsetX
		y += offsetY

		if self.mStepper: y += 15

		controlIcon = self._addImage(path = self._pathIcon(type, quality = interface.Icon.QualityLarge), x = x, y = y, width = widthIcon, height = heightIcon)

		x += widthIcon - int(WindowOptimization.SizeIcon * 0.1)
		y += Window.SeparatorLinePadding
		width = WindowOptimization.SizeRating

		font = interface.Font.fontMassive(full = True)
		try: offset = (70 - font['dimension']) # Try to accomodate different font sizes that have different label heights.
		except: offset = 0

		yNew = y + int(heightIcon * 0.0) + offset
		height = int(heightIcon * 0.15)
		controlTop = self._addLabel(text = interface.Translation.string(label), x = x, y = yNew, width = width, height = height, size = interface.Font.fontSmall(), bold = True, color = interface.Format.colorSecondary())

		yNew = y + int(heightIcon * 0.07) + offset
		height = int(heightIcon * 0.5)
		controlMiddle = self._addLabel(text = '', x = x - 1, y = yNew, width = width, height = height, size = font['name'], bold = not font['bold'])

		yNew = y + height - int(heightIcon * 0.05)
		height = int(heightIcon * 0.15)
		controlBottom = self._addLabel(text = '', x = x, y = yNew, width = width, height = height, size = interface.Font.fontSmall(), bold = True, color = interface.Format.colorPrimary())

		return {'icon' : controlIcon, 'top' : controlTop, 'middle' : controlMiddle, 'bottom' : controlBottom}

	def _addPreferences(self, dimension):
		x, y = self._center()
		self._addCategory(dimension = dimension)
		self.mPreferencesSeparator1, _ = self._addSeparator(y = y - (47 if self.mStepper else 50), control = True)
		self._addTradeoff(dimension = dimension)
		self.mPreferencesSeparator2, _ = self._addSeparator(y = y + (115 if self.mStepper else 125) - (0 if self.mCategoryEnabled else 75), control = True)
		self._addSettings(dimension = dimension)

	def _addCategory(self, dimension):
		x, y = self._center()

		y -= 202
		if self.mStepper: y += 10
		self.mCategoryHeading = self._addLabel(text = interface.Translation.string(36142), x = x, y = y, width = dimension[0], height = 20, alignment = Window.AlignmentCenter, size = interface.Font.fontLarge(), color = interface.Format.colorSecondary(), bold = True, uppercase = True)

		xCenter = self._centerX(0)
		y += 50
		self.mCategoryScrape = self._addButton(text = 35514, x = xCenter - 230, y = y, icon = 'scraper', select = Window.SelectHide, callback = self._actionCategory)
		self.mCategoryProvider = self._addButton(text = 32345, x = xCenter + 10, y = y, icon = 'provider', select = Window.SelectHide, callback = self._actionCategory)

		y += self._dimensionButton()[1] + 15
		self.mCategoryLabel = self._addLabel(text = '', x = x, y = y, width = dimension[0], height = 20, alignment = Window.AlignmentCenter, size = interface.Font.fontSmall(), color = interface.Format.colorPrimary(), bold = True)

	def _addTradeoff(self, dimension):
		x, y = self._center()

		y -= 30
		if not self.mCategoryEnabled: y -= 140
		self.mTradeoffHeading = self._addLabel(text = interface.Translation.string(36141), x = x, y = y, width = dimension[0], height = 20, alignment = Window.AlignmentCenter, size = interface.Font.fontLarge(), color = interface.Format.colorSecondary(), bold = True, uppercase = True)

		xCenter = self._centerX(0)
		y += 50
		if not self.mCategoryEnabled: y += 20
		self.mTradeoffSpeed = self._addButton(text = 36050, x = xCenter - 310, y = y, icon = 'speed', select = Window.SelectHide, callback = self._actionTradeoff)
		self.mTradeoffMixed = self._addButton(text = 36052, x = xCenter - 83, y = y, icon = 'changelog', select = Window.SelectHide, callback = self._actionTradeoff)
		self.mTradeoffResult = self._addButton(text = 35815, x = xCenter + 145, y = y, icon = 'lists', select = Window.SelectHide, callback = self._actionTradeoff)

		y += self._dimensionButton()[1] + 15
		if not self.mCategoryEnabled: y += 15
		self.mTradeoffLabel = self._addLabel(text = '', x = x, y = y, width = dimension[0], height = 20, alignment = Window.AlignmentCenter, size = interface.Font.fontSmall(), color = interface.Format.colorPrimary(), bold = True)

	def _addSettings(self, dimension):
		x, y = self._center()

		y += 145
		if self.mStepper: y -= 15
		if not self.mCategoryEnabled: y -= 50
		self.mPreferencesHeading = self._addLabel(text = interface.Translation.string(36147), x = x, y = y, width = dimension[0], height = 20, alignment = Window.AlignmentCenter, size = interface.Font.fontLarge(), color = interface.Format.colorSecondary(), bold = True, uppercase = True)

		y += 30
		if not self.mCategoryEnabled: y += 25
		self.mPreferencesLabel = self._addLabel(text = '', x = x, y = y, width = dimension[0], height = 50, alignment = Window.AlignmentCenter, size = interface.Font.fontMedium(), bold = True)


class WindowMetaDetail(WindowStep):

	DetailNone		= 0
	DetailPartial	= 1
	DetailComplete	= 2

	def __init__(self, stepper = False, **kwargs):
		super(WindowMetaDetail, self).__init__(title = 33161, xml = True, xmlType = Window.TypeWizardStatic, xmlOffset = None, stepper = stepper, **kwargs)

		from lib.meta.tools import MetaTools
		self.mDetail = MetaTools.instance().settingsDetail()

		self.mSources = {
			tools.Media.TypeMovie : {},
			tools.Media.TypeShow : {},
		}

		self.mLevels = {
			tools.Media.TypeMovie : {
				MetaTools.DetailEssential : {
					MetaTools.ProviderImdb		: WindowMetaDetail.DetailPartial,
					MetaTools.ProviderTrakt		: WindowMetaDetail.DetailPartial,
					MetaTools.ProviderTmdb		: WindowMetaDetail.DetailComplete,
					MetaTools.ProviderTvdb		: WindowMetaDetail.DetailNone,
					MetaTools.ProviderFanart	: WindowMetaDetail.DetailNone,
				},
				MetaTools.DetailStandard : {
					MetaTools.ProviderImdb		: WindowMetaDetail.DetailPartial,
					MetaTools.ProviderTrakt		: WindowMetaDetail.DetailComplete,
					MetaTools.ProviderTmdb		: WindowMetaDetail.DetailComplete,
					MetaTools.ProviderTvdb		: WindowMetaDetail.DetailNone,
					MetaTools.ProviderFanart	: WindowMetaDetail.DetailComplete,
				},
				MetaTools.DetailExtended : {
					MetaTools.ProviderImdb		: WindowMetaDetail.DetailComplete,
					MetaTools.ProviderTrakt		: WindowMetaDetail.DetailComplete,
					MetaTools.ProviderTmdb		: WindowMetaDetail.DetailComplete,
					MetaTools.ProviderTvdb		: WindowMetaDetail.DetailNone,
					MetaTools.ProviderFanart	: WindowMetaDetail.DetailComplete,
				},
			},
			tools.Media.TypeShow : {
				MetaTools.DetailEssential : {
					MetaTools.ProviderImdb		: WindowMetaDetail.DetailPartial,
					MetaTools.ProviderTrakt		: WindowMetaDetail.DetailPartial,
					MetaTools.ProviderTmdb		: WindowMetaDetail.DetailNone,
					MetaTools.ProviderTvdb		: WindowMetaDetail.DetailComplete,
					MetaTools.ProviderFanart	: WindowMetaDetail.DetailNone,
				},
				MetaTools.DetailStandard : {
					MetaTools.ProviderImdb		: WindowMetaDetail.DetailPartial,
					MetaTools.ProviderTrakt		: WindowMetaDetail.DetailComplete,
					MetaTools.ProviderTmdb		: WindowMetaDetail.DetailNone,
					MetaTools.ProviderTvdb		: WindowMetaDetail.DetailComplete,
					MetaTools.ProviderFanart	: WindowMetaDetail.DetailComplete,
				},
				MetaTools.DetailExtended : {
					MetaTools.ProviderImdb		: WindowMetaDetail.DetailComplete,
					MetaTools.ProviderTrakt		: WindowMetaDetail.DetailComplete,
					MetaTools.ProviderTmdb		: WindowMetaDetail.DetailPartial,
					MetaTools.ProviderTvdb		: WindowMetaDetail.DetailComplete,
					MetaTools.ProviderFanart	: WindowMetaDetail.DetailComplete,
				},
			},
		}

	def _initializeEnd2(self):
		super(WindowMetaDetail, self)._initializeEnd2()
		self._setMetadata()

	@classmethod
	def show(self, wait = False, stepper = False, helper = False, navigationCancel = True, navigationHelp = True, navigationBack = True, navigationNext = True, callbackClose = None, callbackCancel = None, callbackHelp = None, callbackBack = None, callbackNext = None, **kwargs):
		callbackNexter = callbackNext # Otherwise lambda below has problems with callbackNext being the lambda function and the parameter inside the lambda function.
		if stepper:
			callbackNext = lambda : self._actionApply(close = False, callback = callbackNexter)
		else:
			navigationBack = False
			navigationNext = {'label' : 33832, 'icon' : 'check'}
			callbackNext = lambda : self._actionApply(close = True, callback = callbackNexter)

		return super(WindowMetaDetail, self).show(wait = wait, stepper = stepper, helper = helper, navigationCancel = navigationCancel, navigationHelp = navigationHelp, navigationBack = navigationBack, navigationNext = navigationNext, callbackClose = callbackClose, callbackCancel = callbackCancel, callbackHelp = callbackHelp, callbackBack = callbackBack, callbackNext = callbackNext, **kwargs)

	def _actionHelp(self):
		self._help(items = [
			{'type' : 'title', 'value' : 'Metadata Detail', 'break' : 2},
			{'type' : 'text', 'value' : 'Metadata and images can be retrieved from a variety of sources. Certain sources might have some missing metadata, ratings, or images. Combining the data from different sources can therefore be useful for filling in missing values and making menus and dialogs aesthetically more pleasing.', 'break' : 2},
			{'type' : 'text', 'value' : 'Different levels of metadata detail and image varieties can be retrieved. The more metadata is retrieved, the more requests have to be made to different servers, and the longer menus take to load. [B]Note that this only applies to the first time a previously unseen movie or show is loaded. Once the metadata and images were retrieved, the data is cached locally and can be accessed without delay on subsequent retrievals.[/B] When a menu is opened for the very first time, it can take a long time to load. For movie menus this might take up to a minute, and show menus up to two minutes, depending on the level of metadata detail, the number of items in the list, the speed of your internet connection, and the load on the servers. Once the menu is cached locally, it will only take a second to load.', 'break' : 2},

			{'type' : 'title', 'value' : 'Metadata Levels', 'break' : 2},
			{'type' : 'text', 'value' : 'The following metadata detail levels are available:', 'break' : 2},

			{'type' : 'subtitle', 'value' : 'Essential Metadata', 'break' : 2},
			{'type' : 'text', 'value' : 'Retrieve only the most crucial metadata and images from as few providers as possible. This option has the fastest loading times and is recommended for users who prefer speed above everything else or users who have a slow internet connection.', 'break' : 2},
			{'type' : 'list', 'value' : [
				{'title' : 'Metadata', 'value' : 'Basic information is retrieved from IMDb or Trakt. Detailed information comes from TMDb for movies, and from TVDb for shows. Most metadata should be available with a few occasional missing values.'},
				{'title' : 'Ratings', 'value' : 'Ratings and vote counts might be incomplete. Movies always have a TMDb rating in addition to either an IMDb or Trakt rating. Shows have either an IMDb or Trakt rating.'},
				{'title' : 'Images', 'value' : 'Images are available for most view layouts, but more advanced views using banners, clear or disc art, might have some missing artwork. '},
			]},

			{'type' : 'subtitle', 'value' : 'Standard Metadata', 'break' : 2},
			{'type' : 'text', 'value' : 'Retrieve detailed metadata and additional images from as many providers as necessary without going overboard. This option has average loading times and is recommended for the majority users, since all metadata and images are available without making any unnecessary requests.', 'break' : 2},
			{'type' : 'list', 'value' : [
				{'title' : 'Metadata', 'value' : 'Basic information is retrieved from IMDb. Detailed information comes from TMDb and Trakt for movies, and from TVDb and Trakt for shows. All metadata should be available without any missing values.'},
				{'title' : 'Ratings', 'value' : 'Movies always have a TMDb and Trakt rating, in addition to an IMDb rating for some lists. Shows always have a Trakt rating, in addition to an IMDb rating for some lists.'},
				{'title' : 'Images', 'value' : 'Images are available for all view layouts. Images not available on TMDb or TVDb are retrieved from Fanart.'},
			]},

			{'type' : 'subtitle', 'value' : 'Extended Metadata', 'break' : 2},
			{'type' : 'text', 'value' : 'Retrieve all metadata and images from all available providers. This option has the longest loading times and is recommended for those users who have a good internet connection and prefer a good-looking interface above speed. [B]Note that retrieving extended metadata for some lists might take twice as long as standard metadata.[/B]', 'break' : 2},
			{'type' : 'list', 'value' : [
				{'title' : 'Metadata', 'value' : 'Basic information is retrieved from IMDb. Detailed information comes from TMDb and Trakt for movies, and from TVDb and Trakt for shows. All metadata should be available without any missing values.'},
				{'title' : 'Ratings', 'value' : 'Additional requests are made to IMDb for movies and shows, and to TMDb for shows, in order to retrieve supplementary ratings and vote counts. Movies and shows always have an IMDb, TMDb, and Trakt rating.'},
				{'title' : 'Images', 'value' : 'Images are available for all view layouts. Images not available on TMDb or TVDb are retrieved from Fanart.'},
			]},

			{'type' : 'title', 'value' : 'Metadata Sources', 'break' : 2},
			{'type' : 'text', 'value' : 'Metadata and images can be retrieved from the following sources:', 'break' : 2},

			{'type' : 'subtitle', 'value' : 'TMDb', 'break' : 2},
			{'type' : 'list', 'value' : [
				{'title' : 'Metadata', 'value' : 'Detailed metadata for movies with no missing values.'},
				{'title' : 'Ratings', 'value' : 'User ratings and vote counts for movies and shows.'},
				{'title' : 'Images', 'value' : 'Rudimentary images for movies, sufficient for most view layouts. This includes posters, fanart, logos, and cast photos.'},
			]},

			{'type' : 'subtitle', 'value' : 'TVDb', 'break' : 2},
			{'type' : 'list', 'value' : [
				{'title' : 'Metadata', 'value' : 'Detailed metadata for shows with no missing values.'},
				{'title' : 'Ratings', 'value' : 'No user ratings or vote counts at all.'},
				{'title' : 'Images', 'value' : 'Comprehensive images for shows, sufficient for almost all view layouts. This includes posters, fanart, banners, thumbnails, logos, clear art, and cast photos.'},
			]},

			{'type' : 'subtitle', 'value' : 'Trakt', 'break' : 2},
			{'type' : 'list', 'value' : [
				{'title' : 'Metadata', 'value' : 'Detailed metadata for movies and shows with only a few missing values.'},
				{'title' : 'Ratings', 'value' : 'User ratings and vote counts for movies and shows.'},
				{'title' : 'Images', 'value' : 'No images at all.'},
			]},

			{'type' : 'subtitle', 'value' : 'IMDb', 'break' : 2},
			{'type' : 'list', 'value' : [
				{'title' : 'Metadata', 'value' : 'Basic metadata for movies and shows with many missing values.'},
				{'title' : 'Ratings', 'value' : 'User ratings and vote counts for movies and shows.'},
				{'title' : 'Images', 'value' : 'Only posters for movies and shows, but no other artwork. Posters are mostly cluttered with text and other decorations.'},
			]},

			{'type' : 'subtitle', 'value' : 'Fanart', 'break' : 2},
			{'type' : 'list', 'value' : [
				{'title' : 'Metadata', 'value' : 'No metadata at all.'},
				{'title' : 'Ratings', 'value' : 'No user ratings or vote counts at all.'},
				{'title' : 'Images', 'value' : 'Comprehensive images for movies and shows, fully supporting all view layouts. This includes posters, fanart, banners, thumbnails, logos, clear art, disc art, and cast photos.'},
			]},
		])

	@classmethod
	def _actionApply(self, close = False, callback = None):
		from lib.meta.tools import MetaTools

		instance = self.instance()
		apply = True

		def _apply():
			if close: instance.close()
			if callback: callback()

		if instance.mDetail == MetaTools.DetailExtended:
			apply = interface.Dialog.option(title = 33161, message = 33839, labelConfirm = 33821, labelDeny = 32532)
			if not apply: instance._selectMetadata(detail = MetaTools.DetailStandard)
		if apply: _apply()

	def _addItems(self):
		self.itemAdd(item = self._addItem(label = 33015, callback = self._selectMetadata))
		self._addSources()

	def _addSources(self):
		x = 155
		y = 530
		offsetX = 200
		for item in [('tmdb', 33508), ('tvdb', 35668), ('trakt', 32315), ('imdb', 32034), ('fanart', 35260)]:
			self._addSource(x = x, y = y, type = item[0], label = item[1])
			x += offsetX

	def _addSource(self, x, y, type, label):
		width = 150
		height = 20
		size = 48
		offsetX = size + 8
		font = interface.Font.fontSmall()

		path = self._pathIcon(icon = type, quality = interface.Icon.QualityMini, special = interface.Icon.SpecialServices)
		self._addImage(path = path, x = x, y = y, width = size, height = size)

		self._addLabel(text = label, x = x + offsetX, y = y - 7, width = width, height = height, size = interface.Font.fontLarge(), bold = True)

		self.mSources[tools.Media.TypeMovie][type] = self._addLabel(text = '', x = x + offsetX, y = y + 18, width = width, height = height, size = font)
		self.mSources[tools.Media.TypeShow][type] = self._addLabel(text = '', x = x + offsetX, y = y + 33, width = width, height = height, size = font)

	def _setMetadata(self):
		from lib.meta.tools import MetaTools
		if self.mDetail == MetaTools.DetailEssential:
			label = 33162
			level = 1
		elif self.mDetail == MetaTools.DetailStandard:
			label = 33163
			level = 2
		elif self.mDetail == MetaTools.DetailExtended:
			label = 33164
			level = 3
		self.mItems[0]['item'].setProperty('GaiaIcon', self._pathImage(['level', 'level%d' % level]))
		self.mItems[0]['item'].setProperty('GaiaLabel', interface.Translation.string(label))

		lables = {
			WindowMetaDetail.DetailNone : interface.Format.font(33112, color = interface.Format.colorBad(), bold = True),
			WindowMetaDetail.DetailPartial : interface.Format.font(33165, color = interface.Format.colorMedium(), bold = True),
			WindowMetaDetail.DetailComplete : interface.Format.font(33166, color = interface.Format.colorGood(), bold = True),
		}
		for media in self.mSources.keys():
			for provider in self.mSources[media].keys():
				label = interface.Translation.string(32001 if media == tools.Media.TypeMovie else 32002)
				label = interface.Format.font(label + ': ', bold = True) + lables[self.mLevels[media][self.mDetail][provider]]
				self._setLabel(control = self.mSources[media][provider], text = label)

	def _selectMetadata(self, detail = None):
		from lib.meta.tools import MetaTools

		if detail is None: index = MetaTools.Details.index(self.mDetail) + 1
		else: index = MetaTools.Details.index(detail)

		if index >= len(MetaTools.Details): index = 0
		self.mDetail = MetaTools.Details[index]
		MetaTools.settingsDetailSet(self.mDetail)
		self._setMetadata()


class WindowMetaExternal(WindowStep):

	Statistics = None

	SizeDownload = 104857600 # 100 MB
	SizeStorage = 629145600 # 600 MB
	SizeMinimum = 262144000 # 250 MB
	SizeRecommended = 524288000 # 500 MB

	def __init__(self, stepper = False, **kwargs):
		super(WindowMetaExternal, self).__init__(title = 33301, xml = True, xmlType = Window.TypeWizardStatic, xmlOffset = None, stepper = stepper, **kwargs)

		self.mControlDescription = None

		from lib.meta.tools import MetaTools
		metatools = MetaTools.instance()

		self.mEnabled = metatools.settingsExternal() if metatools.settingsExternalHas() else None
		self.mInstalled = tools.Extension.installed(id = tools.Extension.IdGaiaMetadata, enabled = False)
		self.mSize = tools.Extension.size(id = tools.Extension.IdGaiaMetadata)

	def _initializeEnd2(self):
		super(WindowMetaExternal, self)._initializeEnd2()
		self._setMetadata()

	@classmethod
	def show(self, wait = False, stepper = False, helper = False, navigationCancel = True, navigationHelp = True, navigationBack = True, navigationNext = True, callbackClose = None, callbackCancel = None, callbackHelp = None, callbackBack = None, callbackNext = None, **kwargs):
		self.prepare()

		callbackNexter = callbackNext # Otherwise lambda below has problems with callbackNext being the lambda function and the parameter inside the lambda function.
		if stepper:
			callbackNext = lambda : self._actionApply(close = False, callback = callbackNexter)
		else:
			navigationBack = False
			navigationNext = {'label' : 33832, 'icon' : 'check'}
			callbackNext = lambda : self._actionApply(close = True, callback = callbackNexter)

		return super(WindowMetaExternal, self).show(wait = wait, stepper = stepper, helper = helper, navigationCancel = navigationCancel, navigationHelp = navigationHelp, navigationBack = navigationBack, navigationNext = navigationNext, callbackClose = callbackClose, callbackCancel = callbackCancel, callbackHelp = callbackHelp, callbackBack = callbackBack, callbackNext = callbackNext, **kwargs)

	@classmethod
	def prepare(self, update = True, wait = False):
		if WindowMetaExternal.Statistics is None:
			thread = Pool.thread(target = self._prepare, kwargs = {'update' : update}, start = True)
			if wait: thread.join()

	@classmethod
	def _prepare(self, update = True):
		if WindowMetaExternal.Statistics is None:
			#WindowMetaExternal.Statistics = {"version":"6.1.0~beta1","time":1673445472,"size":{"compressed":91867561,"uncompressed":559236897},"data":{"count":{"movie":21140,"set":0,"show":10497,"season":16155,"episode":45133},"size":{"movie":149786624,"set":4096,"show":158257152,"season":75292672,"episode":171491328}}}
			WindowMetaExternal.Statistics = tools.Extension.statistics(id = tools.Extension.IdGaiaMetadata)
			if update:
				try: self.instance()._setMetadata()
				except: pass

	@classmethod
	def _storage(self):
		return tools.Hardware.storage()

	def _actionHelp(self):
		self._help(items = [
			{'type' : 'title', 'value' : 'Preprocessed Metadata', 'break' : 2},
			{'type' : 'text', 'value' : 'Menus containing movies or shows can take a long time to load the first time they are opened, since a lot of metadata has to be retrieved in the background. Especially if you have [I]Extended Detail[/I]  enabled, metadata has to be retrieved from a range of different providers, which can result in 100s or sometimes even 1000s of requests per menu page. For some show or episode menus this can take upwards of a few minutes on some devices. Once the menu was loaded, all metadata is cached locally, and menus can then be reloaded in only a few seconds or less.', 'break' : 2},
			{'type' : 'text', 'value' : 'To mitigate the long initial menu loading times, you can install the [I]Gaia Metadata[/I]  addon. This addon contains a large database or preprocessed [I]Extended[/I]  metadata in [I]English[/I]. If you have this addon installed and a menu is opened for the first time, Gaia will first check your local metadata database, and if the items cannot be found there, it will use the preprocessed database instead. This allows for substantially faster menu loading, if and only if the movies or shows in the menu are present in the preprocessed database. Newer or less-known movies or shows might not be in the preprocessed database and will still require longer loading times. If data is retrieved from the preprocessed database, Gaia will still make a background request to retrieve updated metadata according to your language and country settings. The newly retrieved metadata is stored it in the local database and used the next time you open the menu. This metadata refreshing happens in the background in order not to hold up the menu loading.', 'break' : 2},
			{'type' : 'text', 'value' : 'The preprocessed database is only a fallback. Gaia will functional fully, even if the [I]Gaia Metadata[/I]  addon is not installed. In this case, Gaia will only use the locally generated metadata, which might result in longer loading times if the metadata is not yet cached.', 'break' : 2},
			{'type' : 'text', 'value' : 'Note that the [I]Gaia Metadata[/I]  addon requires a substantial amount of free disk space. If you have previously installed the addon and want to uninstall it to free up space, it is not enough to just disable the option in Gaia\'s settings. You will also have to manually uninstall the addon using the dependency manager under Kodi\'s system settings.', 'break' : 2},
		])

	@classmethod
	def _actionApply(self, close = False, callback = None):
		from lib.meta.tools import MetaTools
		from lib.modules.convert import ConverterSize

		instance = self.instance()
		apply = True
		title = 33301

		def _apply():
			if close: instance.close()
			if callback: callback()

		try:
			storage = self._storage()
			storageRemaining = storage['usage']['free']['bytes'] - WindowMetaExternal.Statistics['size']['uncompressed']
			storageFree = interface.Format.fontBold(ConverterSize(storage['usage']['free']['bytes']).stringOptimal())
			storageRequired = interface.Format.fontBold(ConverterSize(WindowMetaExternal.Statistics['size']['uncompressed']).stringOptimal())
		except:
			storageRemaining = 0
			storageFree = interface.Format.fontBold(33387)
			storageRequired = interface.Format.fontBold(33387)

		try:
			if instance.mEnabled:
				if not instance.mInstalled:
					message = None
					if storageRemaining <= 0: message = 33556
					elif storageRemaining <= WindowMetaExternal.SizeMinimum: message = 33557
					elif storageRemaining <= WindowMetaExternal.SizeRecommended: message = 33558
					if message:
						message = interface.Translation.string(message) % (storageFree, storageRequired)
						apply = interface.Dialog.option(title = title, message = message, labelConfirm = 33821, labelDeny = 33743)
			else:
				if instance.mInstalled:
					message = interface.Translation.string(33560) % (interface.Format.fontItalic(tools.Extension.IdGaiaMetadata), storageRequired)
					interface.Dialog.confirm(title = title, message = message)
				elif storageRemaining > WindowMetaExternal.SizeRecommended:
					message = interface.Translation.string(33559) % storageFree
					if interface.Dialog.option(title = title, message = message, labelConfirm = 33821, labelDeny = 33743): return _apply()
					else: apply = False
		except: tools.Logger.error()

		if apply:
			if tools.Extension.installed(id = tools.Extension.IdGaiaMetadata, enabled = True): _apply()
			else: tools.Extension.enable(id = tools.Extension.IdGaiaMetadata, confirm = tools.Extension.ConfirmDisabled, notification = True, action = _apply, wait = True)
			instance._selectMetadata(change = False)
		else:
			instance._selectMetadata()

	def _addItems(self):
		self.itemAdd(item = self._addItem(label = 33015, callback = self._selectMetadata))

	def _setMetadata(self):
		try:
			storage = self._storage()
			storageRemaining = storage['usage']['free']['bytes'] - WindowMetaExternal.Statistics['size']['uncompressed']
		except:
			storage = None
			storageRemaining = -1

		# If the user has not enabled/disabled this setting yet, use the free disk space value to determine the default value.
		if self.mEnabled is None and storageRemaining > 0: self.mEnabled = storageRemaining > WindowMetaExternal.SizeRecommended

		if self.mEnabled:
			from lib.modules.convert import ConverterSize

			icon = 'checked'
			label = 32301
			labels = [
				[interface.Translation.string(33542) % self._highlight(interface.Translation.string(33553)), interface.Translation.string(33541) % (self._highlight(interface.Translation.string(33547)), self._highlight(interface.Translation.string(33548)))],
				[],
				[],
				[],
			]

			if self.mInstalled:
				labels[2].append(33545)
				labels[2].append(interface.Translation.string(33546) % self._highlight(ConverterSize(self.mSize).stringOptimal()) if self.mSize else interface.Translation.string(33387))
			else:
				try: sizeDownload = WindowMetaExternal.Statistics['size']['compressed']
				except: sizeDownload = WindowMetaExternal.SizeDownload
				sizeDownload = ConverterSize(sizeDownload).stringOptimal()
				try: sizeStorage = WindowMetaExternal.Statistics['size']['uncompressed']
				except: sizeStorage = WindowMetaExternal.SizeStorage
				sizeStorage = ConverterSize(sizeStorage).stringOptimal()

				labels[2].append(interface.Translation.string(33543) % self._highlight(sizeDownload))
				labels[2].append(interface.Translation.string(33544) % self._highlight(sizeStorage))

			for i in [(tools.Media.TypeMovie, 32001), (tools.Media.TypeSet, 33527), (tools.Media.TypeShow, 32002), (tools.Media.TypeSeason, 32054), (tools.Media.TypeEpisode, 32326)]:
				try:
					if WindowMetaExternal.Statistics['data']['count'][i[0]] > 0:
						labels[1].append('%s %s' % (self._highlight(tools.Math.thousand(WindowMetaExternal.Statistics['data']['count'][i[0]])), interface.Translation.string(i[1])))
				except: pass

			try:
				storageTotal = self._highlight(storage['usage']['total']['label'])
				storageFree = storage['usage']['free']['label']

				if WindowMetaExternal.Statistics:
					if storageRemaining <= 0: storageFree = interface.Format.color(storageFree, color = interface.Format.colorBad())
					elif storageRemaining <= WindowMetaExternal.SizeMinimum: storageFree = interface.Format.color(storageFree, color = interface.Format.colorPoor())
					elif storageRemaining <= WindowMetaExternal.SizeRecommended: storageFree = interface.Format.color(storageFree, color = interface.Format.colorMedium())
					else: storageFree = self._highlight(storageFree)
				else: storageFree = self._highlight(storageFree)

				labels[3] = (interface.Translation.string(33555).replace('%s', '*').title().replace('*', '%s') % (storageFree, storageTotal)) + ' ' + interface.Translation.string(33350)
			except:
				tools.Logger.error()
		else:
			icon = 'unchecked'
			label = 32302
			labels = [
				[interface.Translation.string(33542) % self._highlight(interface.Translation.string(33554)), interface.Translation.string(33549) % self._highlight(interface.Translation.string(33548))],
				[interface.Translation.string(33550) % self._highlight(interface.Translation.string(33342))],
				[interface.Translation.string(33551) % self._highlight(interface.Translation.string(33342))],
				[interface.Translation.string(33552) % self._highlight(interface.Translation.string(33342))],
			]

		item = self.mItems[0]['item']
		item.setProperty('GaiaIcon', self._pathImage(['check', icon]))
		item.setProperty('GaiaLabel', interface.Translation.string(label))

		counter = 0
		for i in labels:
			if i:
				counter += 1
				item.setProperty('GaiaLabel%d' % counter, interface.Format.iconJoin(i))
		for i in range(counter + 1, 5): item.setProperty('GaiaLabel%d' % i, '')

	def _selectMetadata(self, change = True):
		from lib.meta.tools import MetaTools
		if change: self.mEnabled = not self.mEnabled
		MetaTools.settingsExternalSet(self.mEnabled)
		if change: self._setMetadata()


class WindowWizardIntro(WindowStep):

	def __init__(self, **kwargs):
		super(WindowWizardIntro, self).__init__(**kwargs)

	@classmethod
	def show(self, **kwargs):
		return super(WindowWizardIntro, self).show(navigationBack = False, **kwargs)

	def _addContent(self):
		dimension = super(WindowWizardIntro, self)._addContent()
		height = 350
		x, y = self._center()
		description = interface.Translation.string(36206)
		self._addLabel(text = interface.Translation.string(36205), x = x, y = y - 260, width = dimension[0], height = height, alignment = Window.AlignmentCenter, size = interface.Font.fontHuge(), bold = True, uppercase = True, color = self._colorHighlight())
		self._addLabel(text = description, x = x, y = y - 130, width = dimension[0], height = height, alignment = Window.AlignmentCenter, size = interface.Font.fontLarge(), bold = True)
		return dimension

	def _actionHelp(self):
		items = [
			{'type' : 'title', 'value' : 'Setup Wizard', 'break' : 2},
			{'type' : 'text', 'value' : 'The setup wizard can be used to easily configure the principal settings of the addon. The settings adjusted by the wizard are crucial for making the addon function as intended. Other settings can be configured through the standard settings dialog. Use the [B]UP[/B], [B]DOWN[/B], [B]LEFT[/B], [B]RIGHT[/B], and [B]OK/SELECT[/B] keys to navigate through the setup wizard.', 'break' : 2},
			{'type' : 'title', 'value' : 'Legal Disclaimer', 'break' : 2},
			{'type' : 'text', 'value' : 'By continuing the setup wizard and using Gaia you agree to the disclaimer below.[CR][CR]' + tools.Disclaimer.message(), 'break' : 2},
		]
		items.extend(WindowWizard._helpMenu())
		self._help(items = items)


class WindowWizardOutro(WindowStep):

	def __init__(self, **kwargs):
		super(WindowWizardOutro, self).__init__(**kwargs)

	@classmethod
	def show(self, **kwargs):
		return super(WindowWizardOutro, self).show(navigationNext = {'label' : 33832, 'icon' : 'check'}, **kwargs)

	def _addContent(self):
		dimension = super(WindowWizardOutro, self)._addContent()
		height = 350
		x, y = self._center()
		description = interface.Translation.string(36278)
		self._addLabel(text = interface.Translation.string(33506), x = x, y = y - 265, width = dimension[0], height = height, alignment = Window.AlignmentCenter, size = interface.Font.fontHuge(), bold = True, uppercase = True, color = self._colorHighlight())
		self._addLabel(text = description, x = x, y = y - 130, width = dimension[0], height = height, alignment = Window.AlignmentCenter, size = interface.Font.fontLarge(), bold = True)
		return dimension

	def _actionHelp(self):
		items = [
			{'type' : 'title', 'value' : 'Setup Wizard', 'break' : 2},
			{'type' : 'text', 'value' : 'The most crucial settings were configured and you are ready to start streaming. Other settings can be configured in the standard settings dialog.', 'break' : 2},
		]
		items.extend(WindowWizard._helpMenu())
		self._help(items = items)


class WindowWizardLanguage(WindowStep):

	def __init__(self, **kwargs):
		super(WindowWizardLanguage, self).__init__(title = 36207, xml = True, xmlType = Window.TypeWizardSmall, **kwargs)

	def _initializeEnd2(self):
		super(WindowWizardLanguage, self)._initializeEnd2()
		self._setLanguagePrimary()
		self._setLanguageSecondary()
		self._setLanguageTertiary()

	@classmethod
	def show(self, wait = False, stepper = False, helper = False, navigationCancel = True, navigationHelp = True, navigationBack = True, navigationNext = True, callbackClose = None, callbackCancel = None, callbackHelp = None, callbackBack = None, callbackNext = None, **kwargs):
		return super(WindowWizardLanguage, self).show(wait = wait, stepper = stepper, helper = helper, navigationCancel = navigationCancel, navigationHelp = navigationHelp, navigationBack = navigationBack, navigationNext = navigationNext, callbackClose = callbackClose, callbackCancel = callbackCancel, callbackHelp = callbackHelp, callbackBack = callbackBack, callbackNext = callbackNext, **kwargs)

	def _actionHelp(self):
		self._help(items = [
			{'type' : 'title', 'value' : 'Language Preferences', 'break' : 2},
			{'type' : 'text', 'value' : 'Specify up to three languages that are used throughout the addon. Select the languages in order of proficiency, starting with the primary, followed by the secondary and tertiary languages. These preferences are global and used for various features, but languages can also be specified on a per-feature basis in the standard settings dialog.', 'break' : 2},
			{'type' : 'text', 'value' : 'The languages are used in the following way:', 'break' : 1},
			{'type' : 'list', 'value' : [
				{'title' : 'Metadata', 'value' : 'Use titles, names, plots, and tag lines from a specific language where available.'},
				{'title' : 'Artwork', 'value' : 'Use posters, fanart, and other artwork from a specific language where available.'},
				{'title' : 'Interface', 'value' : 'Show labels in your preferred language where available.'},
				{'title' : 'Scraping', 'value' : 'Search additional queries constructed from titles and keywords in your preferred language in order to find more streams.'},
				{'title' : 'Providers', 'value' : 'Use additional providers from countries with your preferred language in order to find more streams.'},
				{'title' : 'Audio', 'value' : 'Automatically select an audio language stream when playback starts.'},
				{'title' : 'Subtitles', 'value' : 'Automatically select a subtitle language stream when playback starts. Additional subtitles can be downloaded from OpenSubtitles when native subtitles are unavailable.'},
			]},
		])

	def _addItems(self):
		items = []
		items.append(self._addLanguage(label = 32356, callback = self._selectLanguagePrimary))
		items.append(self._addLanguage(label = 32357, callback = self._selectLanguageSecondary))
		items.append(self._addLanguage(label = 35036, callback = self._selectLanguageTertiary))
		self.itemAdd(item = items)

	def _addLanguage(self, label, callback):
		return self._addItem(label = label, callback = callback)

	def _setLanguage(self, index):
		color = interface.Format.colorPrimary()
		language = tools.Language.settings(raw = True)[index]
		if language:
			code = language[tools.Language.Code][tools.Language.CodePrimary]
			name = [language[tools.Language.Name][tools.Language.NameEnglish], language[tools.Language.Name][tools.Language.NameNative]]
			name = tools.Tools.listUnique([i for i in name if i])
		else:
			code = tools.Language.CodeNone
			name = [interface.Translation.string(33112)]

		self.mItems[index]['item'].setProperty('GaiaIcon', tools.Language.flag(language = code, quality = interface.Icon.QualityLarge))
		self.mItems[index]['item'].setProperty('GaiaLabel1', interface.Format.iconJoin([interface.Format.font(i, color = color) for i in name]))

	def _setLanguagePrimary(self):
		self._setLanguage(index = 0)

	def _setLanguageSecondary(self):
		self._setLanguage(index = 1)

	def _setLanguageTertiary(self):
		self._setLanguage(index = 2)

	def _selectLanguagePrimary(self):
		tools.Language.settingsSelectPrimary()
		self._setLanguagePrimary()

	def _selectLanguageSecondary(self):
		tools.Language.settingsSelectSecondary()
		self._setLanguageSecondary()

	def _selectLanguageTertiary(self):
		tools.Language.settingsSelectTertiary()
		self._setLanguageTertiary()


class WindowWizardAccount(WindowStepScroll):

	def __init__(self, **kwargs):
		super(WindowWizardAccount, self).__init__(title = 36227, xml = True, xmlType = Window.TypeWizardLarge, **kwargs)

	@classmethod
	def prepare(self, wait = True):
		if wait: self._prepare()
		else: Pool.thread(target = self._prepare, start = True)

	@classmethod
	def _prepare(self):
		functions = [self._authenticateTrakt, self._authenticateImdb, self._authenticateYoutube, self._authenticateOpensubtitles, self._authenticateOrion]
		for function in functions:
			function(authenticate = None)

	@classmethod
	def show(self, helper = False, **kwargs):
		return super(WindowWizardAccount, self).show(helper = helper, **kwargs)

	def _actionHelp(self):
		self._help(items = [
			{'type' : 'title', 'value' : 'Utility Accounts', 'break' : 2},
			{'type' : 'text', 'value' : 'Utility accounts provide additional functionality throughout the addon. All features of these accounts can be fully utilized with just a free subscription. Consider getting a paid subscription to support these services. It is highly recommended to authenticate at least a [B]Trakt[/B] and [B]YouTube[/B] account, since they provide essential features.', 'break' : 2},
			{'type' : 'text', 'value' : 'The accounts are used for the following:', 'break' : 1},
			{'type' : 'list', 'value' : [
				{'title' : 'Trakt', 'value' : 'Keep track of watched titles and scrobble the progress to resume playback at a later stage. Create, access, and manage your watchlist and other lists. Rate titles after playback finishes. Retrieve extended metadata for movies and shows.'},
				{'title' : 'IMDb', 'value' : 'Access your watchlist and other lists. Since IMDb does not have a public API, lists can only be accessed, but not created or managed. The privacy status of lists must be set to [I]public[/I]  on IMDb\'s website to make them retrievable.'},
				#{'title' : 'TMDb', 'value' : 'Retrieve extended metadata and additional images for movies. A personal TMDb account is not required for the addon to function correctly. However, TMDb has API rate limits based on the public IP address. If you use the addon a lot or have a VPN server that other TMDb users might also utilize, the rate limit might kick in sooner and it might be advisable to get a custom TMDb API key.'},
				#{'title' : 'TVDb', 'value' : 'Retrieve extended metadata and additional images for shows. A personal TVDb account is not required for the addon to function correctly. But a premium account is appropriate if you want to support TVDb.'},
				{'title' : 'Fanart', 'value' : 'Retrieve additional images for movies and shows. A personal Fanart account is not required for the addon to function correctly. However, Fanart limits the images returned by the API based on the account type. Without a Fanart account, only images older than 7 days are accessible. With a free Fanart account, this is reduced to 2 days. With a premium Fanart account, images can be accessed instantly.'},
				{'title' : 'YouTube', 'value' : 'Play trailers, season recaps, and various other video extras. The [I]Cinematic Experience[/I]  feature plays random trailers while scraping is in progress. YouTube is also used for a provider that scrapes the occasional title released on the platform. Note that Gaia only searches the YouTube API, but the resolving and playback of the videos are handled by the external [B]YouTube[/B] addon.'},
				{'title' : 'OpenSubtitles', 'value' : 'Load additional subtitles in various languages. Many new releases already contain integrated subtitles. But if the video does not have any subtitles or not any in your preferred language, OpenSubtitles can be used to automatically download extra subtitles.'},
				{'title' : 'Orion', 'value' : 'Retrieve torrent, usenet, and hoster links. Orion acts as another provider during scraping, but retrieves a lot of links more quickly than most other native Gaia providers. Orion also provides debrid cache lookups, resolving, and streaming features for Premiumize, OffCloud, RealDebrid, DebridLink, and AllDebrid. Since DebridLink and AllDebrid are not natively supported in Gaia, Orion can be used for additional functionality, such as cache lookups and selecting a specific file from a file pack.'},
			]},
		])

	def _actionNext(self):
		from lib.modules.account import Trakt, Youtube
		if not Trakt().authenticated() or not Youtube().authenticated():
			return interface.Dialog.option(title = 36227, message = 36233, labelConfirm = 33821, labelDeny = 32512)
		return True

	def _addItems(self):
		items = []

		items.append(self._addAccount(
			callback = self._authenticateTrakt,
			icon = 'trakt', label = 32315,
			recommend = True, free = True, paid = 2.50,
			support = [35139, 36229, 36228],
		))
		items.append(self._addAccount(
			callback = self._authenticateImdb,
			icon = 'imdb', label = 32034,
			recommend = False, free = True, paid = 12.50,
			support = [36229],
		))

		# If these are ever re-enabled, make sure to update the "index" attributes in the various def _authenticateXXX() functions
		'''items.append(self._addAccount(
			callback = self._authenticateTmdb,
			icon = 'tmdb', label = 33508,
			recommend = False, free = True, paid = False,
			support = [36228, 36249],
		))
		items.append(self._addAccount(
			callback = self._authenticateTvdb,
			icon = 'tvdb', label = 35668,
			recommend = False, free = True, paid = 1.00,
			support = [36228, 36249],
		))'''

		items.append(self._addAccount(
			callback = self._authenticateFanart,
			icon = 'fanart', label = 35260,
			recommend = False, free = True, paid = 1.50,
			support = [36249],
		))
		items.append(self._addAccount(
			callback = self._authenticateYoutube,
			icon = 'youtube', label = 35296,
			recommend = True, free = True, paid = 12.00,
			support = [35566, 36230, 36209],
		))
		items.append(self._addAccount(
			callback = self._authenticateOpensubtitles,
			icon = 'opensubtitles', label = 35683,
			recommend = False, free = True, paid = 1.00,
			support = [36210],
		))
		items.append(self._addAccount(
			callback = self._authenticateOrion,
			icon = 'orion', label = 35400,
			recommend = True, free = True, paid = 0.50,
			support = [36211, 36224, 36212],
		))

		self.itemAdd(item = items)

	def _addAccount(self, callback, icon, label, free = False, paid = False, recommend = False, support = None, offset = 0):
		label = interface.Translation.string(label)

		label1 = []
		if recommend: recommend = interface.Format.font(33662, color = interface.Format.colorExcellent())
		else: recommend = interface.Format.font(35323, color = interface.Format.colorPoor())
		label1.append('%s %s' % (recommend, interface.Translation.string(36159)))
		label1 = interface.Format.iconJoin(label1)

		label2 = []
		subscription = interface.Translation.string(36226)
		if free: label2.append('%s %s' % (interface.Format.font(33334, color = interface.Format.colorExcellent()), subscription))
		if paid: label2.append('%s %s %s' % (interface.Format.font(36208, color = interface.Format.colorPoor()), subscription, interface.Translation.string(33849) % interface.Format.font('$%.2f' % paid, color = interface.Format.colorPoor())))
		label2 = interface.Format.iconJoin(label2)

		label3 = interface.Format.iconJoin([interface.Translation.string(i) for i in support])
		return self._addItem(label = label, label1 = label1, label2 = label2, label3 = label3, icon = icon, offset = offset, callback = callback, selected = callback(authenticate = None))

	@classmethod
	def _authenticate(self, index, account, authenticate = True):
		if authenticate: account.authenticate(settings = False)
		authenticated = account.authenticated()
		if not authenticate is None: self.instance()._selectItem(index = index, selected = authenticated)
		return authenticated

	@classmethod
	def _authenticateTrakt(self, authenticate = True):
		from lib.modules.account import Trakt
		return self._authenticate(index = 0, account = Trakt(), authenticate = authenticate)

	@classmethod
	def _authenticateImdb(self, authenticate = True):
		from lib.modules.account import Imdb
		return self._authenticate(index = 1, account = Imdb(), authenticate = authenticate)

	@classmethod
	def _authenticateTmdb(self, authenticate = True):
		from lib.modules.account import Tmdb
		return self._authenticate(index = 2, account = Tmdb(), authenticate = authenticate)

	@classmethod
	def _authenticateTvdb(self, authenticate = True):
		from lib.modules.account import Tvdb
		return self._authenticate(index = 3, account = Tvdb(), authenticate = authenticate)

	@classmethod
	def _authenticateFanart(self, authenticate = True):
		from lib.modules.account import Fanart
		return self._authenticate(index = 2, account = Fanart(), authenticate = authenticate)

	@classmethod
	def _authenticateYoutube(self, authenticate = True):
		from lib.modules.account import Youtube
		return self._authenticate(index = 3, account = Youtube(), authenticate = authenticate)

	@classmethod
	def _authenticateOpensubtitles(self, authenticate = True):
		from lib.modules.account import Opensubtitles
		return self._authenticate(index = 4, account = Opensubtitles(), authenticate = authenticate)

	@classmethod
	def _authenticateOrion(self, authenticate = True):
		from lib.modules.account import Orion
		return self._authenticate(index = 5, account = Orion(), authenticate = authenticate)


class WindowWizardPremium(WindowStepScroll):

	def __init__(self, **kwargs):
		super(WindowWizardPremium, self).__init__(title = 36239, xml = True, xmlType = Window.TypeWizardLarge, **kwargs)

	@classmethod
	def prepare(self, wait = True):
		if wait: self._prepare()
		else: Pool.thread(target = self._prepare, start = True)

	@classmethod
	def _prepare(self):
		from lib.debrid.debrid import Debrid
		for service in Debrid.providers():
			self._authenticate(id = service['id'], authenticate = None)

	@classmethod
	def show(self, helper = False, **kwargs):
		return super(WindowWizardPremium, self).show(helper = helper, **kwargs)

	def _actionHelp(self):
		from lib.debrid.debrid import Debrid
		Debrid.help(title = 36232)

	def _actionNext(self):
		for item in self.mItems:
			if item['callback'](authenticate = False): return True
		return interface.Dialog.option(title = 36239, message = 36234, labelConfirm = 33821, labelDeny = 32512)

	def _addItems(self):
		try:
			from lib.debrid.debrid import Debrid

			items = []
			for service in Debrid.providers():
				items.append(self._addAccount(service))

			self.itemAdd(item = items)
		except:
			tools.Logger.error()

	def _addAccount(self, item):
		try:
			label = interface.Translation.string(item['name'])

			label1 = []
			if item['general']['recommend'] == 1: value = interface.Format.font(35486, color = interface.Format.colorExcellent())
			elif item['general']['recommend'] == 2: value = interface.Format.font(35487, color = interface.Format.colorMedium())
			elif item['general']['recommend'] == 3: value = interface.Format.font(35334, color = interface.Format.colorPoor())
			label1.append('%s %s' % (value, interface.Translation.string(36256)))
			if item['general']['native']: value = interface.Format.font(36253, color = interface.Format.colorExcellent())
			elif item['general']['limit']: value = interface.Format.font(36255, color = interface.Format.colorPoor())
			else: value = interface.Format.font(36254, color = interface.Format.colorMedium())
			label1.append('%s %s' % (value, interface.Translation.string(33921)))
			label1 = interface.Format.iconJoin(label1)

			label2 = []
			subscription = interface.Translation.string(36226)
			if item['subscription']['fee']: label2.append('%s %s %s' % (interface.Format.font(36208, color = interface.Format.colorPoor()), subscription, interface.Translation.string(33849) % interface.Format.font('$%.2f' % item['subscription']['fee'], color = interface.Format.colorPoor())))
			label2 = interface.Format.iconJoin(label2)

			label3 = []
			if item['network']['support']['torrent']: label3.append(36242)
			if item['network']['support']['usenet']: label3.append(33200)
			if item['network']['support']['hoster']: label3.append(36243)
			label3 = interface.Format.iconJoin(['%s %s' % (interface.Translation.string(i), interface.Translation.string(33921)) for i in label3])

			label4 = []
			if any(item['stream']['support'].values()): label4.append(36223)
			if any(item['cache']['support'].values()): label4.append(36224)
			if any(item['select']['support'].values()): label4.append(35542)
			if any(item['extra']['support'].values()): label4.append(36225)
			label4 = interface.Format.iconJoin([interface.Translation.string(i) for i in label4])

			offset = None
			if item['id'] == 'premiumize': offset = 1

			return self._addItem(label = label, label1 = label1, label2 = label2, label3 = label3, label4 = label4, icon = item['id'], offset = offset, callback = lambda authenticate = True: self._authenticate(id = item['id'], authenticate = authenticate), selected = self._authenticate(id = item['id'], authenticate = None))
		except: tools.Logger.error()

	@classmethod
	def _authenticate(self, id, authenticate = True):
		from lib.debrid.debrid import Debrid

		account = tools.Tools.getInstance('lib.modules.account', id.capitalize())
		if authenticate: account.authenticate(help = False, settings = False)
		authenticated = account.authenticated()
		if authenticate is None: return authenticated

		index = next((i for (i, provider) in enumerate(Debrid.providers()) if provider['id'] == id), None)
		self.instance()._selectItem(index = index, selected = authenticated)

		return authenticated


class WindowWizard(object):

	StatusUncompleted = 0
	StatusInitiated = 1
	StatusCanceled = 2
	StatusCompleted = 3

	ActionClosed = None

	# Also used by WindowOptimization.
	ProgressOptimization = {'introduction' : 70, 'diagnostics' : 73, 'rating' : 76, 'preferences' : 78}

	PropertyInitial = 'internal.initial.wizard'

	Window = None

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		WindowWizard.ActionClosed = None
		WindowWizard.Window = None

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def _helpMenu(self):
		return [
			{'type' : 'title', 'value' : 'Menu Performance', 'break' : 2},
			{'type' : 'text', 'value' : 'Note that menus containing movies, shows, or episodes, might take a long time to load when opened for the first time. The metadata and images are retrieved, processed, and stored in the local cache. Subsequent loading of the menus should be considerably faster, since the metadata and images are fetched from the local cache. The metadata will occasionally be refreshed in the background.', 'break' : 2},
			{'type' : 'title', 'value' : 'Scraping Performance', 'break' : 2},
			{'type' : 'text', 'value' : 'Scraping might be slow, especially on low-end devices. Shows generally need more time to scrape than movies. There are various ways in which scarping time can be reduced. Disabling unnecessary providers is a good starting point, since most providers have mostly the same links. Changing various scraping settings will also improve performance, including reducing the number of pages and queries, disabling pack queries, or reducing additional titles and keywords used during scraping.', 'break' : 2},
			{'type' : 'title', 'value' : 'Gaia Performance', 'break' : 2},
			{'type' : 'text', 'value' : 'A detailed discussion of various performance aspects of Gaia can be found in the online FAQ.', 'break' : 2},
			{'type' : 'link', 'value' : tools.Settings.getString('internal.link.support', raw = True), 'break' : 2},
		]

	@classmethod
	def cancel(self):
		cancel = True
		status = tools.Settings.getInteger(WindowWizard.PropertyInitial)
		if not status == WindowWizard.StatusCompleted: cancel = interface.Dialog.option(title = 33893, message = 35288)
		if cancel: self.close()
		return cancel

	@classmethod
	def close(self):
		WindowWizard.ActionClosed = True
		if tools.Settings.getInteger(WindowWizard.PropertyInitial) <= WindowWizard.StatusInitiated:
			tools.Settings.set(WindowWizard.PropertyInitial, WindowWizard.StatusCanceled)

	@classmethod
	def show(self, initial = False, wait = False):
		interface.Loader.show()

		if initial:
			# Only return if the wizard was canceled or completed.
			# Kodi can sometimes freeze during the wizard (eg: external Trakt addon authentication).
			# If the user then restarts Kodi, the status is still WindowWizard.PropertyInitial and the wizard should pop up again.
			status = tools.Settings.getInteger(WindowWizard.PropertyInitial)
			if status == WindowWizard.StatusCanceled or status == WindowWizard.StatusCompleted:
				interface.Loader.hide()
				return False
			elif not status:
				tools.Settings.set(WindowWizard.PropertyInitial, WindowWizard.StatusInitiated)

		# In some cases when opening the wizard, the wizard does not load. Or it loads, but the WindowWizardAccount window is empty.
		# When closing the window, nothing else in the addon works anymore and requires a Kodi restart.
		# Not sure why this is, but when importing Networker.moduleCaseInsensitiveDict() called from WindowWizardAccount.prepare() and WindowWizardPremium.prepare(), the problem is gone.
		# Just import all modules in Networker and hope that it solves the problem.
		# Maybe it is some threading, locking, or mutual exclusion issue.
		from lib.modules.network import Networker
		Networker.modulePrepare()

		# Create the QR codes in the background, so that they are hopefully ready once we get to those windows.
		WindowAttribution.prepare(wait = False)
		WindowDonation.prepare(wait = False)

		# Get statistics for metadata addon, so that they are hopefully ready once we get to those windows.
		WindowMetaExternal.prepare(wait = False)

		# Some of the accounts take long to initialize (create an instance), since they import external modules or addons (eg: YouTube and Orion).
		# This takes a few 100 ms and when the window is loaded, for a fraction of a second the window is empty while all the imports happen.
		# Prepare will import all the modules, making subsequent window loading faster.
		WindowWizardAccount.prepare(wait = False)
		WindowWizardPremium.prepare(wait = False)

		self.showIntro()
		WindowIntro.close()
		interface.Loader.hide()

		if wait:
			while not tools.System.aborted():
				if WindowWizard.ActionClosed or WindowStep.ActionClosed: break
				tools.Time.sleep(0.1)

		return True

	@classmethod
	def showIntro(self):
		WindowWizard.Window = WindowWizardIntro
		WindowWizardIntro.show(progress = 10, helper = True, stepper = True, callbackClose = self.close, callbackCancel = self.cancel, callbackNext = self.showLanguage)
		WindowWizardLanguage.close()

	@classmethod
	def showLanguage(self):
		WindowWizard.Window = WindowWizardLanguage
		WindowWizardLanguage.show(progress = 20, stepper = True, callbackClose = self.close, callbackCancel = self.cancel, callbackBack = self.showIntro, callbackNext = self.showMetaDetail)
		WindowWizardIntro.close()
		WindowMetaDetail.close()
		tools.Disclaimer.agree()

	@classmethod
	def showMetaDetail(self):
		WindowWizard.Window = WindowMetaDetail
		WindowMetaDetail.show(progress = 30, stepper = True, callbackClose = self.close, callbackCancel = self.cancel, callbackBack = self.showLanguage, callbackNext = self.showMetaExternal)
		WindowWizardLanguage.close()
		WindowMetaExternal.close()

	@classmethod
	def showMetaExternal(self):
		WindowWizard.Window = WindowMetaExternal
		WindowMetaExternal.show(progress = 40, stepper = True, callbackClose = self.close, callbackCancel = self.cancel, callbackBack = self.showMetaDetail, callbackNext = self.showAccount)
		WindowMetaDetail.close()
		WindowWizardAccount.close()

	@classmethod
	def showAccount(self):
		WindowWizard.Window = WindowWizardAccount
		WindowWizardAccount.show(progress = 50, stepper = True, callbackClose = self.close, callbackCancel = self.cancel, callbackBack = self.showMetaExternal, callbackNext = self.showPremium)
		WindowMetaExternal.close()
		WindowWizardPremium.close()

	@classmethod
	def showPremium(self):
		WindowWizard.Window = WindowWizardPremium
		WindowWizardPremium.show(progress = 60, stepper = True, callbackClose = self.close, callbackCancel = self.cancel, callbackBack = self.showAccount, callbackNext = self.showOptimization)
		WindowWizardAccount.close()
		WindowOptimization.close()

	@classmethod
	def showOptimization(self):
		from lib.providers.core.manager import Manager
		WindowWizard.Window = WindowOptimization
		Manager.optimizeShow(stepper = True, category = False, navigationNext = {'label' : 33821, 'icon' : 'next'}, callbackClose = self.close, callbackCancel = self.cancel, callbackBack = self.showPremium, callbackNext = self.showAttribution)
		WindowWizardPremium.close()
		WindowAttribution.close()

	@classmethod
	def showAttribution(self):
		WindowWizard.Window = WindowAttribution
		WindowAttribution.show(progress = 80, stepper = True, navigationCancel = True, navigationBack = True, navigationNext = True, callbackClose = self.close, callbackCancel = self.cancel, callbackBack = self.showOptimization, callbackNext = self.showDonation)
		WindowOptimization.close()
		WindowDonation.close()
		tools.Settings.set(WindowWizard.PropertyInitial, WindowWizard.StatusCompleted) # The remainder of the steps do not configure anything.

	@classmethod
	def showDonation(self):
		WindowWizard.Window = WindowDonation
		WindowDonation.show(progress = 90, stepper = True, navigationCancel = True, navigationBack = True, navigationNext = True, callbackClose = self.close, callbackCancel = self.cancel, callbackBack = self.showAttribution, callbackNext = self.showOutro)
		WindowAttribution.close()
		WindowWizardOutro.close()

	@classmethod
	def showOutro(self):
		WindowWizard.Window = WindowWizardOutro
		WindowWizardOutro.show(progress = 100, stepper = True, callbackClose = self.close, callbackCancel = self.cancel, callbackBack = self.showDonation, callbackNext = self.showFinal)
		WindowDonation.close()

	@classmethod
	def showFinal(self):
		WindowWizardOutro.close()
		self.close()
