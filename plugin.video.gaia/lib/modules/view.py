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

from lib.modules.tools import System, Time, File, Regex, Logger, Settings, Media
from lib.modules.interface import Directory, Translation, Format, Dialog, Loader, Skin
from lib.modules.concurrency import Pool

class View(object):

	ModeDefault = 0
	ModeFixed = 1
	ModeCustom = 2

	SelectionNone = 0
	SelectionUnselected = 1
	SelectionAlways = 2

	Fixed = {
		'skin.estuary' : {
			Directory.ContentGeneral : 55, # WideList
			Directory.ContentMovies : 51, # Poster
			Directory.ContentSets : 51, # Poster
			Directory.ContentShows : 51, # Poster
			Directory.ContentSeasons : 50, # List
			Directory.ContentEpisodes : 55, # WideList
		},
		'skin.estouchy' : {
			Directory.ContentGeneral : 9000, # Unknown
			Directory.ContentMovies : 50, # Unknown
			Directory.ContentSets : 50, # Unknown
			Directory.ContentShows : 50, # Unknown
			Directory.ContentSeasons : 50, # Unknown
			Directory.ContentEpisodes : 50, # Unknown
		},
		'skin.confluence' : {
			Directory.ContentGeneral : 500, # Thumbnail
			Directory.ContentMovies : 515, # MediaInfo3
			Directory.ContentSets : 515, # MediaInfo3
			Directory.ContentShows : 515, # MediaInfo3
			Directory.ContentSeasons : 2, # MediaInfo2
			Directory.ContentEpisodes : 2, # MediaInfo2
		},
		'skin.aeon.nox.silvo' : {
			Directory.ContentGeneral : 50, # List
			Directory.ContentMovies : 501, # LowList
			Directory.ContentSets : 501, # LowList
			Directory.ContentShows : 501, # LowList
			Directory.ContentSeasons : 501, # LowList
			Directory.ContentEpisodes : 501, # LowList
		},
		'skin.arctic.horizon' : {
			Directory.ContentGeneral : 500, # SquareList
			Directory.ContentMovies : 52, # PosterRow
			Directory.ContentSets : 52, # PosterRow
			Directory.ContentShows : 52, # PosterRow
			Directory.ContentSeasons : 53, # LandscapeIntegrated
			Directory.ContentEpisodes : 53, # LandscapeIntegrated
		},
	}

	@classmethod
	def add(self, media):
		try:
			skinId = Skin.id()
			skinPath = Skin.path()

			xml = File.joinPath(skinPath, 'addon.xml')
			data = File.readNow(xml).replace('\n', '')
			source = Regex.extract(data = data, expression = r'defaultresolution\s*=\s*[\\\'\\"](.+?)[\\\'\\"]')
			if not source: source = Regex.extract(data = data, expression = r'<\s*res.+?folder\s*=\s*[\\\'\\"](.+?)[\\\'\\"]')
			source = File.joinPath(skinPath, source, 'MyVideoNav.xml')

			data = File.readNow(source).replace('\n', '')
			views = Regex.extract(data = data, expression = r'<views>(.+?)</views>')
			views = [int(x) for x in views.split(',')]

			Loader.hide() # NB: Loader must be hidden, otherwise the info label below will not work.
			Time.sleep(0.1)
			viewId = int(System.infoLabel('System.CurrentControlID'))
			if viewId is None: return False
			viewName = System.infoLabel('Container.Viewmode')
			Loader.show()

			return {'id' : viewId, 'name' : viewName, 'skin' : skinId, 'layout' : self.settingsLayoutGet(media = media)}
		except:
			Logger.error()
			return False

	@classmethod
	def _wait(self, id, path, container, layout):
		'''
			The goal is to wait for the container to finish loading before setting the view and/or position.
			Setting the view/position before the container has finished loading does not work and the container remains unchanged afterwards.
			The problem is that there is no way, either through Python or through the built-in functions and InfoLabels, to determine when the container has finished loading.
			It still takes a few 100 ms after xbmcplugin.endOfDirectory() for Kodi to finish loading the menu.

			Trying to access the Container, ControlList, and ListItem through Python also does not work.
			Although it is possible to get the Container and ControlList through Python, the ControlList is always empty.
			This has been reported on ther Kodi forums multiple times since 2012, and is therefore unlikley to be fixed.
			Getting the size, position, current item, etc from the ControlList is therefore not possible in Python.
			Strangely enough, it is still possible to call setters on the ControlList (eg ControlList.selectItem() does change the selected position, even when size() == 0).

			One possibility is to add a unique ID to a menu/container and check if that ID has changed when navigating from one menu to the next.
				1. Calling xbmcplugin.setProperty() is useless, since that value is set (and retrievable) before the container finished loading.
				2. The only reliable way to determine if the container finished loading is to check if the ListItems in ther container have been initialized/loaded.
				   As already mentioned, trying to access the ControlList/ListItem from Python does not work, since the list is always returned empty.
				   The only possiblity is to use the InfoLabels to get the values from the container/list.
				   	a. Using Container.FolderPath sometimes works, but in most cases this value has changed before the container finished loading. Plus Container.FolderPath does not work when navigating back on cached menus, since they do not update this value.
				   	b. The best option seems to be to set a custom property on the first ListItem. The problem is that it is impossible to access custom properties using InfoLabels.
					   It is only possible by skins and custom XML that have direct access to the ListItem.Property(...). Custom properties cannot be accessed through Container(id).ListItem(offset).Property.
					c. Another option is to use an unused info label set in Python by ListItem.setInfo() which is accessible from Container(id).ListItem(offset).Info.
					   The problem here is that we might use an info label that might be used/displayed elsewhere, like the Kodi info Dialog.
					   Setting an unknown/custom label with ListItem.setInfo(), throws a warning in the Kodi log.
					   Additionally, it can take a few seconds (not ms) to access info labels through Container(id).ListItem(offset), which causes a delay while setting the view/position.
					d. The final solution is to read the the core attributes from Container(id).ListItem(offset), which seem to be fast and don't have the delay of c. above.
							cid).ListItem(offset).Label
							Container(id).ListItem(offset).Icon
					   Use both these, since it is unlikley that the first item of a submenu has the same label AND icon.
					   It is however possible for the first submenu item to have the same icon, and in a few cases maybe the same label, but not both.
					   So if the label+icon of the first item changed, we can assume that the list finished loading.

			Update 1:
				It seems that setting an custom property on ListItem is accessible from the InfoLabels.
				Note that there are different ways of getting the ListItem:
					Container(...).ListItem(...)
					Container(...).ListItemPosition(...)
					Container(...).ListItemNoWrap(...)
					Container(...).ListItemAbsolute(...)
				The first 3 can be off if the menu is reloaded and Kodi automatically selects the previously selected item.
					Eg: Container(...).ListItem(0)
				Might not select the 1st item, but the 1st item visible after Kodi automatically selects the item.
				Use Container(...).ListItemAbsolute(...) instead.

			Update 2:
				There is one small problem with the implementation below.
				If we currently have some Gaia menu opened and hit Backspace twice realy quickly, Kodi exits the addon and goes to the main menu (this seems to be standard Kodi behaviour).
				However, once Backspace is hit the first time, Kodi starts navigating to the parent menu, which in turn will call this function.
				When Backspace is hit the second time shortly after, Kodi interprets this as exiting the current addon, and initiates the exit protocol.
				However, since this function was initiated from the first Backspace hit, the loop below is still running while Kodi waits for the Python interpreter to stop.
				After 5 seconds of Kodi waiting, Kodi kills the interpreter (while the loop below is still running):
					ERROR <general>: CPythonInvoker(289, .kodi/addons/plugin.video.gaia/addon.py): script didn't stop in 5 seconds - let's kill it
					ERROR <general>: GetDirectory - Error getting plugin://plugin.video.gaia/?action=moviesLists&type=movie
					ERROR <general>: CGUIMediaWindow::GetDirectory(plugin://plugin.video.gaia/?action=moviesLists&type=movie) failed
				System.aborted() is False during this, which is probably a bug in Kodi.
				Trying to retrieve any value with System.infoLabel(InfoLabel) or System.visible(BooleanCondition) does not help, since nothing indicates we are exiting the addon.
				It seems the only way is to let Kodi kill the addon after 5 secs, which will then causes a "System Exit" exception with current xbmc calls, mostly in Time.sleep().
				That is why the sleep() call is wrapped in its own try-catch, with the catch part returning False.
				Also note that hitting Backspace twice is not the same as hitting Esc.

			Update 3 (2024-09-01):
				Using the following InfoLabel:
					System.infoLabel('Container.ListItemAbsolute(0).Property(%s)' % Directory.PropertyId)
				causes occasional sporadic crashes, at least for Kodi 21.
				Maybe this is a bug in Kodi, that if the items are not finished loading and one calls an InfoLabel on it, Kodi has some internal error and crashes.
				Next attempt is to try using boolean conditions, xbmc.getCondVisibility(...), instead of InfoLabels. Update: no useful conditions that could help.
		'''

		# When background processes load a Gaia menu, do not wait here (eg: Widgets).
		if not System.originGaia(): return False

		try:
			# Do not wait more than 10 secs, in order not to hold up any processes.
			# In most cases (at least on a fast device), basic menus (parent menus with basic icons) are ready in 0.05 secs, and movie/show menus (with posters, fanart, etc) are ready in 0.2-0.5 secs.
			# Even if it times out, None is returned, which will still attempt to set the view/position.
			interations = 60 # 200 is probably overkill. 60 = 3secs.
			interval = 0.05

			# Wait for the Oracle window to close, otherwise the 1st item is not selected, since getting the ListItem will get the list from Oracle window and not the menu.
			# If the WindowOracleResults is shown for longer than 10 secs, this problem happens.
			# Wait for WindowOracleResults to close before determining which item to select.
			from lib.modules.window import WindowOracle
			if WindowOracle.visible():
				for i in range(0, interations * 30):
					if not WindowOracle.visible(): break
					Time.sleep(interval)

			if id:
				# NB: Kodi (v21, but probably ealier versions as well, altough this was not noticed in earlier development versions), sometimes randomly crashes when executing the following statement:
				#	System.infoLabel(command1, wait = False)
				# This is a very sporadic crash that only happens once in a while when navigating through the menus.
				# The first thought was that maybe the command itself caused the problem (eg: ListItemAbsolute or Property), but changing that to other InfoLabels either did not return the wanted results, or also crashed.
				# The problem probably is trying to get an item or property from a Kodi container that is still busy loading, and Kodi does not handle the InfoLabel very well, resulting in the crash.
				# Adding a sleep-delay or trying to use a different InfoLabel does not fix the issue.
				# Update: Using the JSON RPC instead of System.infoLabel() seems to have fixed th eissue. There is probably some bug in Kodi's Python code, which is present in the RPC.

				# NB: When the Back entry (..) is hidden, the 1st item has an index of 0 instead of 1.
				# Gaia Eminence hides the back button on first install.
				# Check 1st and 2nd item.
				command1 = 'Container.ListItemAbsolute(0).Property(%s)' % Directory.PropertyId
				command2 = 'Container.ListItemAbsolute(1).Property(%s)' % Directory.PropertyId

				method = 'XBMC.GetInfoLabels'
				parameters1 = {'labels' : [command1]}
				parameters2 = {'labels' : [command2]}

				for i in range(0, interations):
					# This causes sporadic Kodi crashes. Do not use!!
					#if id == System.infoLabel(command1, wait = False): return True
					#if id == System.infoLabel(command2, wait = False): return True

					# Use the RPC instead, which does not seem to cause the crashes.
					if id == System.executeJson(method = method, parameters = parameters1).get('result', {}).get(command1): return True
					if id == System.executeJson(method = method, parameters = parameters2).get('result', {}).get(command2): return True

					if System.aborted(): return False
					try: Time.sleep(interval)
					except: return False # Read Update 2 above.
			elif layout:
				for i in range(0, interations):
					# Do not wait if ContentGeneral, which will end up with Container.Content(), which always returns False.
					if System.visible(container): return True
					if System.aborted(): return False
					try: Time.sleep(interval)
					except: return False # Read Update 2 above.
			else:
				return True # This should never execute.
		except: Logger.error()
		return None

	@classmethod
	def set(self, media, content = None, id = None, path = None, views = None, select = None, thread = True):
		if thread: Pool.thread(target = self._setView, kwargs = {'media' : media, 'content' : content, 'id' : id, 'path' : path, 'views' : views, 'select' : select}, start = True)
		else: self._setView(media = media, content = content, id = id, path = path, views = views)

	@classmethod
	def _setView(self, media, content = None, id = None, path = None, views = None, select = None):
		try:
			skin = Skin.id()
			if not content: content = self.convert(media)
			layout = self.settingsLayoutGet(media = media)
			container = 'Container.Content(%s)' % layout

			view = None
			if views:
				try: view = views[skin]
				except: pass
			if not view:
				mode = self.settingsGet(media = media)
				if mode == View.ModeCustom:
					try:
						view = self.settingsTypeGet(media = media)
						if not view is None:
							view = view[skin]
							if content in view: view = view[content]['id']
							else: view = view[Directory.ContentDefault]['id'] # When the View Layout is set to Default.
					except:
						view = None
						Logger.error()
				elif mode == View.ModeFixed:
					try:
						view = View.Fixed[skin]
						if content in view: view = view[content]
						else: view = view[Directory.ContentDefault] # When the View Layout is set to Default.
					except:
						view = None
						Logger.error()

			if view:
				command = 'Container.SetViewMode(%s)' % str(view)

				# Previous should always be set, so this should never be executed.
				# Wait here, because the if-statement in the loop will immediately set loaded = True.
				if not id and not layout: Time.sleep(0.5)

				if self._wait(id = id, path = path, container = container, layout = layout) is False:
					return False
				else:
					System.execute(command)
					self._setSelection(index = select)
					return True
			elif not self.settingsSelection() == View.SelectionNone: # Avoid waiting if the setting was disabled.
				if self._wait(id = id, path = path, container = container, layout = layout) is False:
					return False
				else:
					self._setSelection(index = select)
					return None
			return None
		except:
			Logger.error()
			return False

	@classmethod
	def _setSelection(self, index = None):
		try:
			selection = self.settingsSelection(episode = False)
			if not index is None:
				selectionEpisode = self.settingsSelection(episode = True)
				if selectionEpisode == View.SelectionNone: index = None
				else: selection = selectionEpisode

			if not selection == View.SelectionNone:
				# Only change the position if the default position is 0, aka the back navigation.
				# If menus are cached, Kodi will remember the previous position.
				# Hence, when a menu is reloaded, Kodi automatically selects the previous item.
				# In such a case, do not change the position.
				# This can be tested by opening a movie menu, make sure a specific movie is selected, then hit the Backspace key, and then reload the same menu.
				# In contrast to opening a movie menu, selecting some movie, then going to the top/first entry (which is the back ".." item), and then reloading the same menu.
				current = None if selection == View.SelectionAlways else System.infoLabel('Container.CurrentItem')
				try: currentValue = int(current) # ValueError: invalid literal for int() with base 10
				except: currentValue = -1
				if selection == View.SelectionAlways or (not current is None and currentValue == 0):
					import xbmcgui
					try: id = int(System.infoLabel('System.CurrentControlID')) # Sometimes this returns nothing.
					except: id = None
					if not id is None:
						window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
						try: list = window.getControl(id)
						except: list = None # Sometimes cannot get the control.
						if list:
							if index is None: index = 1
							else: index += 1 # Index 0 is the back navigation.
							list.selectItem(index)
		except:
			# This error message might show often if a keyboard/mouse is use, since moving the mouse might change focus to another control.
			# Eg: System.CurrentControlID might return None.
			# Eg: window.getControl(id) might return another control (eg button) instead of a list.
			Logger.error()

	@classmethod
	def settings(self, media = None, content = None, previous = None, settings = False):
		try:
			if content:
				Loader.show()
				id = 'view.style.%s.type' % media

				view = self.add(media = media)
				if view: self.settingsTypeSet(media = media, view = view)

				# Actions, like System.execute('Action(Back)') do not work, probably because Container.Update() was called from settings.xml.
				# This is the best we can do to reload the menu that was visible before the views menu.
				if previous:
					# Reaplce container, otherwise when loading the previous command into the container, it still shows the old view, probably because it is cached.
					# This might make the user think that the settings update did not work.
					System.executeContainer(command = previous, replace = True)

					# Wait for the container to load, otherwise it will only update if the settings dialog is closed.
					# 1 second is too little.
					Time.sleep(2.5)

				Loader.hide()
				if view: Dialog.notification(title = 33586, message = Translation.string(33587) % Format.fontBold(view['name']), icon = Dialog.IconSuccess)
				if settings: self.settingsLaunch(media = media)
			else:
				title = Translation.string(32059)
				content = self.convert(media)
				previous = System.infoLabel('Container.FolderPath')
				link = System.command(action = 'settingsView', parameters = {'media' : media, 'content' : content, 'previous' : previous, 'settings' : settings})

				Loader.hide()
				Time.sleep(0.5) # 0.2 is too short.

				# Hide the Kodi left-hand sliding window if views was launched from there (through the settings dialog).
				# This is very unreliable and will only work if the language is English and the label is "Add-on settings".
				control = System.infoLabel('System.CurrentControl')
				if control and control.lower() == 'add-on settings': System.execute('Action(Menu)')

				directory = Directory(content = Directory.ContentSettings, media = media, cache = False, lock = False)
				for i in range(10):
					directory.add(label = title, link = link, info = ('video', {'title' : title}), icon = 'viewssave.png', iconDefault = 'DefaultProgram.png', fanart = True, folder = False)
				directory.finish()

				Dialog.confirm(title = 33012, message = 36201)
		except:
			Logger.error()

	@classmethod
	def settingsLaunch(self, media):
		Settings.launchData(self.settingsTypeId(media = media))

	@classmethod
	def settingsInitialize(self):
		# In case the skin was changed, change the view name/label in the settings.
		for media in [Directory.ContentGeneral, Media.Movie, Media.Set, Media.Show, Media.Season, Media.Episode]:
			settings = self.settingsTypeGet(media = media)
			try:
				view = settings[Skin.id()][self.settingsLayoutGet(media = media)]['name']
				self.settingsTypeSet(media = media, label = view)
			except:
				self.settingsTypeSet(media = media, label = False)

	@classmethod
	def settingsSelection(self, episode = False):
		return Settings.getInteger('view.general.selection' + ('.episode' if episode else ''))

	@classmethod
	def settingsId(self, media):
		return 'view.style.%s' % media

	@classmethod
	def settingsGet(self, media):
		return Settings.getInteger(id = self.settingsId(media = media))

	@classmethod
	def settingsLayoutId(self, media):
		return 'view.style.%s.layout' % (media if media and not media == Directory.ContentGeneral else Directory.ContentGeneral)

	@classmethod
	def settingsLayoutGet(self, media = None, fallback = False):
		# Must be the same index-order as in settings.xml.
		if fallback:
			default = self.convert(media = media)
			if default == Directory.ContentGeneral: fallback = False

		order = [
			default if fallback else Directory.ContentDefault,
			Directory.ContentAddons,
			Directory.ContentFiles,
			Directory.ContentGames,
			Directory.ContentVideos,
			Directory.ContentMovies,
			Directory.ContentSets,
			Directory.ContentShows,
			Directory.ContentSeasons,
			Directory.ContentEpisodes,
		]

		try: return order[0 if self.settingsGet(media = media) == View.ModeFixed else Settings.getInteger(self.settingsLayoutId(media = media))]
		except: return Directory.ContentDefault

	@classmethod
	def settingsTypeId(self, media):
		return 'view.style.%s.type' % media

	@classmethod
	def settingsTypeGet(self, media):
		return Settings.getData(id = self.settingsTypeId(media = media))

	@classmethod
	def settingsTypeSet(self, media, data = None, view = None, label = None):
		if label:
			Settings.setLabel(id = self.settingsTypeId(media = media), value = label)
		elif label is False:
			Settings.defaultData(id = self.settingsTypeId(media = media))
		else:
			if data is None: data = self.settingsTypeGet(media = media)
			if not data: data = {}
			if not view['skin'] in data: data[view['skin']] = {}
			data[view['skin']][self.convert(media = media) if view['layout'] is None else view['layout']] = {'id' : view['id'], 'name' : view['name']}
			Settings.setData(id = self.settingsTypeId(media = media), value = data, label = view['name'])

	@classmethod
	def convert(self, media):
		if media:
			if media.startswith('movie') or media.startswith('docu') or media.startswith('short'): return Directory.ContentMovies
			elif media.startswith('set'): return Directory.ContentSets
			elif media.startswith('tvshow') or media.startswith('show'): return Directory.ContentShows
			elif media.startswith('season'): return Directory.ContentSeasons
			elif media.startswith('episode'): return Directory.ContentEpisodes
			elif media.startswith('mixed'): return Directory.ContentShows
		return Directory.ContentGeneral
