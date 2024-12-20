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

from lib.modules.database import Database
from lib.modules.tools import Settings, Time, System, Media
from lib.modules.interface import Format, Translation, Dialog, Loader, Directory

class Shortcut(Database):

	Name				= 'shortcuts' # The name of the file. Update version number of the database structure changes.

	Parameter			= 'shortcut'
	ParameterId			= 'id'
	ParameterTime		= 'time'
	ParameterCount		= 'count'
	ParameterMedia		= 'media'
	ParameterLocation	= 'location'
	ParameterLabel		= 'label'
	ParameterCommand	= 'command'
	ParameterFolder		= 'folder'
	ParameterCreate		= 'create'
	ParameterDelete		= 'delete'

	LocationDialog		= 'dialog'
	LocationMenu		= 'menu'
	LocationTool		= 'tool'
	LocationFavorite	= 'favorite'

	Instance			= None

	def __init__(self):
		Database.__init__(self, Shortcut.Name)

	@classmethod
	def instance(self):
		if Shortcut.Instance is None: Shortcut.Instance = self()
		return Shortcut.Instance

	@classmethod
	def reset(self, settings = True):
		Shortcut.Instance = None

	@classmethod
	def enabled(self):
		return Settings.getBoolean('menu.general.shortcut')

	@classmethod
	def item(self, id = None, label = None, command = None, folder = None, create = None, delete = None):
		item = {}
		if not id is None: item[Shortcut.ParameterId] = id
		if not label is None: item[Shortcut.ParameterLabel] = label
		if not command is None: item[Shortcut.ParameterCommand] = command
		if not folder is None: item[Shortcut.ParameterFolder] = folder
		if not create is None: item[Shortcut.ParameterCreate] = create
		if not delete is None: item[Shortcut.ParameterDelete] = delete
		return item or None

	@classmethod
	def process(self, parameters):
		if self.enabled():
			id = parameters.get(Shortcut.Parameter)
			if not id is None: self.instance().update(id = id)

	def _initialize(self):
		self._create('''
			CREATE TABLE IF NOT EXISTS %s
			(
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				time INTEGER,
				count INTEGER,

				media TEXT,
				location TEXT,

				label TEXT,
				command TEXT,
				folder BOOL
			);
		''')

	def insert(self, media, location, label, command, folder):
		self._insert(
			'INSERT INTO %s (time, count, media, location, label, command, folder) VALUES (?, 0, ?, ?, ?, ?, ?);',
			parameters = (Time.timestamp(), media, location, label, command, folder)
		)

	def update(self, id):
		self._update('UPDATE %s SET count = count + 1 WHERE id = ?;', parameters = [id])

	def delete(self, id):
		self._delete('DELETE FROM %s WHERE id = ?;', parameters = [id])

	def retrieve(self, id = None, location = None, media = None):
		result = None
		if not id is None:
			data = self._selectSingle('SELECT id, time, count, media, location, label, command, folder FROM %s WHERE id = ?;', parameters = [id])
			if data: result = self._retrieve(data)
		elif location:
			if media: data = self._select('SELECT id, time, count, media, location, label, command, folder FROM %s WHERE media = ? AND location = ? ORDER BY count DESC;', parameters = [media, location])
			else: data = self._select('SELECT id, time, count, media, location, label, command, folder FROM %s WHERE media IS NULL AND location = ? ORDER BY count DESC;', parameters = [location])
			if data: result = [self._retrieve(i) for i in data]
		return result

	def _retrieve(self, data):
		return {
			Shortcut.ParameterId : data[0],
			Shortcut.ParameterTime : data[1],
			Shortcut.ParameterCount : data[2],
			Shortcut.ParameterMedia : data[3],
			Shortcut.ParameterLocation : data[4],
			Shortcut.ParameterLabel : data[5],
			Shortcut.ParameterCommand : data[6],
			Shortcut.ParameterFolder : data[7],
		}

	def open(self, id):
		self.update(id = id)
		data = self.retrieve(id = id)
		if data:
			command = data.get('command')
			folder = data.get('folder')
			if folder:
				if System.originMenu(): System.executeContainer(command = command)
				else: System.executeWindow(command = command)
			else:
				System.executePlugin(command = command)

	def show(self, id = None, label = None, command = None, folder = None, create = False, delete = False):
		items = [Format.bold(35135)]
		if create: items.append(Format.bold(35120))
		if delete: items.append(Format.bold(35134))

		Loader.hide()
		choice = Dialog.select(title = 35119, items = items)
		if choice >= 0:
			if choice == 0: self.showOpen()
			elif choice == 1:
				if create: self.showCreate(label = label, command = command, folder = folder)
				else: self.showDelete(id = id)

	def showCreate(self, label = None, command = None, folder = None, refresh = False):
		items = [
			Format.bold(35525),
			Format.bold(35121),
			Format.bold(35137),
			Format.bold(35122),
			Format.bold(35123),
			Format.bold(35124),
			Format.bold(35125),
		]
		choice = Dialog.select(title = 35130, items = items)

		if choice >= 0:
			if choice == 0: location = (Media.Unknown, Shortcut.LocationDialog)
			elif choice == 1: location = (Media.Unknown, Shortcut.LocationMenu)
			elif choice == 2: location = (Media.Unknown, Shortcut.LocationTool)
			elif choice == 3: location = (Media.Movie, Shortcut.LocationMenu)
			elif choice == 4: location = (Media.Movie, Shortcut.LocationFavorite)
			elif choice == 5: location = (Media.Show, Shortcut.LocationMenu)
			elif choice == 6: location = (Media.Show, Shortcut.LocationFavorite)

			if not label or label == '': label = Translation.string(35131)
			label = Dialog.input(title = 35132, type = Dialog.InputAlphabetic, default = label)
			if not label: return False

			self.insert(media = location[0], location = location[1], label = label, command = command, folder = folder)
			if refresh: Directory.refresh()
			Dialog.notification(title = 35119, message = Translation.string(35133) % items[choice], icon = Dialog.IconSuccess)
			return True

		return False

	def showDelete(self, id, refresh = True):
		self.delete(id = id)
		if refresh: Directory.refresh()
		Dialog.notification(title = 35119, message = Translation.string(35136), icon = Dialog.IconSuccess)

	def showOpen(self):
		location = [
			(35525, Media.Unknown, Shortcut.LocationDialog),
			(35121, Media.Unknown, Shortcut.LocationMenu),
			(35137, Media.Unknown, Shortcut.LocationTool),
			(35122, Media.Movie, Shortcut.LocationMenu),
			(35123, Media.Movie, Shortcut.LocationFavorite),
			(35125, Media.Show, Shortcut.LocationMenu),
			(35124, Media.Show, Shortcut.LocationFavorite),
		]

		ids = []
		items = []
		for i in location:
			entries = self.retrieve(media = i[1], location = i[2])
			if entries:
				label = Format.bold(Translation.string(i[0]) + ': ')
				for entry in entries:
					ids.append(entry.get('id'))
					items.append(label + entry.get('label'))

		choice = Dialog.select(title = 35130, items = items)
		if choice >= 0: self.open(id = ids[choice])
