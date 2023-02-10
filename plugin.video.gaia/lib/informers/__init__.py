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

import sys
from lib.modules.tools import Media, System, Time, File, Tools, Settings, Extension
from lib.modules.interface import Player, Loader, Dialog, Directory
from lib.modules.window import Window

class Informer(object):

	TypeMovie		= Media.TypeMovie
	TypeSet			= Media.TypeSet
	TypeShow		= Media.TypeShow
	TypeSeason		= Media.TypeSeason
	TypeEpisode		= Media.TypeEpisode
	TypePerson		= Media.TypePerson
	TypeTrailer		= 'trailer' # Play the trailer.
	TypeSelection	= 'selection' # Current selected item in the GUI.

	# Indexes must correspond with the order in settings.xml.
	# Order from best to worst (excluding Kodi).
	IdAutomatic		= None
	IdKodi			= 'kodi'
	Ids				= {0 : IdAutomatic, 1 : IdKodi, 2 : 'extendedinfo', 3 : 'embuaryinfo', 4 : 'diamondinfo'}

	# Wait a total of 30 seconds with an interval of 0.1 seconds.
	WaitIterations	= 300
	WaitInterval	= 0.1

	# Sort
	SortName		= 'name'
	SortBest		= 'best'
	SortNone		= None
	SortDefault		= SortBest

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, name, addon = None, id = None):
		self.mId = id if id else self._id()
		self.mName = name
		self.mAddon = addon

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def instance(self, id = None, sort = SortDefault):
		try:
			if not id: id = self.informer()
			if id == Informer.IdAutomatic:
				for module in self.instanceModules(kodi = False, sort = sort):
					instance = self.instanceImport(module)
					if instance and instance.installed(): return instance
				return self.instanceImport(Informer.IdKodi)
			else:
				return self.instanceImport(id)
		except: return None

	@classmethod
	def instances(self, kodi = True, sort = SortDefault):
		result = []
		for module in self.instanceModules(kodi = kodi, sort = sort):
			instance = self.instanceImport(module)
			if instance: result.append(instance)
		return result

	@classmethod
	def instanceModules(self, kodi = True, sort = SortDefault):
		result = []

		path = File.directory(__file__)
		directories, files = File.listDirectory(path, absolute = False)
		for directory in directories:
			if not directory.startswith('_') and (kodi or not directory == Informer.IdKodi):
				result.append(directory)

		if sort == Informer.SortName:
			result = Tools.listSort(result)
		elif sort == Informer.SortBest:
			order = {v : k for k, v in Informer.Ids.items()}
			result = Tools.listSort(result, key = order.get)

		return result

	@classmethod
	def instanceImport(self, id):
		try: return Tools.getInstance('lib.informers.' + id, self.__name__)
		except: return None

	##############################################################################
	# GENERAL
	##############################################################################

	def id(self):
		return self.mId

	def _id(self):
		return File.directoryName(sys.modules[self.__module__].__file__)

	def name(self):
		return self.mName

	def addon(self):
		return self.mAddon

	##############################################################################
	# ADDON
	##############################################################################

	def settings(self):
		if self.mAddon: Extension.settings(id = self.mAddon)

	def launch(self):
		if self.mAddon: Extension.launch(id = self.mAddon)

	def installed(self):
		if self.mAddon: return Extension.installed(id = self.mAddon)
		else: return True

	def enable(self, refresh = False):
		from lib.modules import tools
		if self.mAddon: return Extension.enable(id = self.mAddon, refresh = refresh)

	def disable(self, refresh = False):
		if self.mAddon: return Extension.disable(id = self.mAddon, refresh = refresh)

	def execute(self, parameters = None):
		System.executeScript(self.mAddon, parameters = parameters)

	##############################################################################
	# INFORMER
	##############################################################################

	@classmethod
	def informer(self):
		informer = Settings.getInteger('interface.context.informer')
		if informer: return Informer.Ids[informer]
		else: return None

	@classmethod
	def informerKodi(self, automatic = True):
		id = self.informer()
		if automatic and id == Informer.IdAutomatic:
			for module in self.instanceModules(kodi = False):
				instance = self.instanceImport(module)
				if instance and instance.installed(): return False
		else:
			return id == Informer.IdKodi

	##############################################################################
	# PARAMETERS
	##############################################################################

	def parameters(self, type, imdb = None, tmdb = None, tvdb = None, title = None, year = None, season = None, episode = None):
		return None

	##############################################################################
	# DIALOG
	##############################################################################

	def dialog(self, type = None, imdb = None, tmdb = None, tvdb = None, title = None, year = None, season = None, episode = None, metadata = None, wait = True):
		if wait: Loader.show()
		supported = self._dialog(type = type, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year, season = season, episode = episode, metadata = metadata, wait = wait)
		if not supported: Dialog.notification(title = self.name(), message = 35818, icon = Dialog.IconWarning)
		if wait: Loader.hide()
		return supported

	def _dialog(self, type = None, imdb = None, tmdb = None, tvdb = None, title = None, year = None, season = None, episode = None, metadata = None, wait = True):
		if type == Informer.TypeSelection or not(imdb or tmdb or tvdb or title):
			if metadata:
				try: type = metadata['mediatype']
				except: type = None
				if type == 'tvshow': type = Informer.TypeShow
				elif type == 'season': type = Informer.TypeSeason
				elif type == 'episode': type = Informer.TypeEpisode
				elif type == 'person': type = Informer.TypePerson
				elif type == 'set': type = Informer.TypeSet
				else: type = Informer.TypeMovie

				try:
					imdb = metadata['imdb_id']
					if imdb == '': imdb = None
				except: imdb = None
				try:
					tmdb = metadata['tmdb_id']
					if tmdb == '': tmdb = None
				except: tmdb = None
				try:
					tvdb = metadata['tvdb_id']
					if tvdb == '': tvdb = None
				except: tvdb = None

				try:
					title = metadata['tvshowtitle']
					if title == '': title = None
				except: title = None
				if not title:
					try:
						title = metadata['title']
						if title == '': title = None
					except: title = None

				try:
					year = metadata['year']
					if year == '': year = None
				except: year = None
				try:
					season = metadata['season']
					if season == '': season = None
				except: season = None
				try:
					episode = metadata['episode']
					if episode == '': episode = None
				except: episode = None
			else:
				type = System.infoLabel('ListItem.DBTYPE')
				if type == 'tvshow': type = Informer.TypeShow
				elif type == 'season': type = Informer.TypeSeason
				elif type == 'episode': type = Informer.TypeEpisode
				elif type == 'person': type = Informer.TypePerson
				elif type == 'set': type = Informer.TypeSet
				else: type = Informer.TypeMovie

				tmdb = None
				tvdb = None
				imdb = System.infoLabel('ListItem.IMDBNumber')
				if imdb == '': imdb = None
				title = System.infoLabel('ListItem.TVShowTitle')
				if title == '': title = None
				if not title:
					title = System.infoLabel('ListItem.Title')
					if title == '': title = None
				year = System.infoLabel('ListItem.Year')
				if year == '': year = None
				season = System.infoLabel('ListItem.Season')
				if season == '': season = None
				episode = System.infoLabel('ListItem.Episode')
				if episode == '': episode = None

		parameters = self.parameters(type = type, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year, season = season, episode = episode)
		if parameters is None: return False

		self.execute(parameters = parameters)

		if wait:
			if type == Informer.TypeTrailer: function = Player().isPlaying
			else: function = Window.visibleCustom
			for i in range(Informer.WaitIterations):
				if function(): break
				Time.sleep(Informer.WaitInterval)

		return True

	##############################################################################
	# SHOW
	##############################################################################

	@classmethod
	def show(self, id = None, type = None, imdb = None, tmdb = None, tvdb = None, title = None, year = None, season = None, episode = None, metadata = None, wait = True):
		if wait: Loader.show()

		if not id: id = self.informer()
		instance = None
		supported = False

		if id:
			try:
				instance = self.instanceImport(id)
				installed = instance.installed()
			except: installed = False
			if installed:
				supported = instance._dialog(type = type, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year, season = season, episode = episode, metadata = metadata, wait = wait)
				if not supported: Dialog.notification(title = instance.name(), message = 35818, icon = Dialog.IconWarning)
			else:
				if not supported: Dialog.notification(title = instance.name() if instance else 35817, message = 35821, icon = Dialog.IconError)
		else:
			for module in self.instanceModules(kodi = False):
				instance = self.instanceImport(module)
				if instance.installed():
					supported = instance._dialog(type = type, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year, season = season, episode = episode, metadata = metadata, wait = wait)
					if supported:
						break
			if not supported:
				instance = self.instanceImport(Informer.IdKodi)
				supported = instance._dialog(type = type, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year, season = season, episode = episode, metadata = metadata, wait = wait)
				if not supported: Dialog.notification(title = 35817, message = 35818, icon = Dialog.IconWarning)

		if wait: Loader.hide()
		return supported

	##############################################################################
	# NAVIGATOR
	##############################################################################

	@classmethod
	def navigators(self, id = None):
		directory = Directory()
		for instance in self.instances(kodi = False):
			id = instance.id()
			directory.add(label = instance.name(), action = 'informerNavigator', parameters = {'id' : id}, folder = True, icon = id, iconDefault = 'DefaultAddonProgram.png')
		directory.finish()

	def navigator(self):
		id = self.id()
		directory = Directory()
		if self.installed():
			directory.add(label = 33256, action = 'informerLaunch', parameters = {'id' : id}, folder = False, icon = id + 'launch.png', iconDefault = 'DefaultAddonProgram.png')
			directory.add(label = 33011, action = 'informerSettings', parameters = {'id' : id}, folder = False, icon = id + 'settings.png', iconDefault = 'DefaultAddonProgram.png')
		else:
			directory.add(label = 33474, action = 'informerInstall', parameters = {'id' : id, 'refresh' : True}, folder = False, icon = id + 'install.png', iconDefault = 'DefaultAddonProgram.png')
		directory.finish()
