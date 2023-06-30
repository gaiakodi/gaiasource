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

# No Gaia imports, because it does not work during script execution of downloader.py.

import os
import hashlib
import xbmc
import xbmcvfs
import xbmcgui
import xbmcaddon
from threading import Lock

try: import sqlite3 as database
except:
	try: from sqlite3 import dbapi2 as database
	except: from pysqlite2 import dbapi2 as database

DatabaseInstances = {}
DatabaseLock = Lock()
DatabaseLocks = {}
DatabaseLocksCustom = {}

class Database(object):

	Timeout = 20

	Extension = '.db'

	NameCache = 'cache'
	NameHistory = 'history'
	NameLibrary = 'library'
	NamePlayback = 'playback'
	NameProviders = 'providers'
	NameMetadata = 'metadata'
	NameSearches = 'searches'
	NameShortcuts = 'shortcuts'
	NameTrailers = 'trailers'
	NameDownloads = 'downloads'
	NameSettings = 'settings'

	def __init__(self, name = None, addon = None, default = None, path = None, label = False, connect = True):
		try:
			if name is None and path: name = hashlib.sha256(path.encode('utf-8')).hexdigest().upper()

			# NB: Use an underscore for member variables, since subclasses might specifiy their own variables with the same name, which will cause the parent variables to be overwritten.
			# Eg: Playback has its own self.mLock.
			self._mName = name
			self._mAddon = addon
			self._mDatabase = None
			self._mConnection = None
			self._mLabel = label

			# Locks are required to query the database from multiple threads.
			# Otherwise errors like these occur: ProgrammingError -> Recursive use of cursors not allowed.
			global DatabaseLocks
			global DatabaseLocksCustom
			if not name in DatabaseLocks:
				global DatabaseLock
				DatabaseLock.acquire()
				if not name in DatabaseLocks:
					DatabaseLocks[name] = Lock()
					DatabaseLocksCustom[name] = Lock()
				DatabaseLock.release()
			self._mLock = DatabaseLocks[name]
			self._mLockCustom = DatabaseLocksCustom[name]

			if path is None:
				self._mPath = self.path(name = name)
				if default and not xbmcvfs.exists(self._mPath): xbmcvfs.copy(os.path.join(default, name), self._mPath)
			else:
				if not path.endswith(Database.Extension): path += Database.Extension
				self._mPath = path
			if connect: self._connect()
		except Exception as error:
			xbmc.log('GAIA ERROR [Database Initialization - %s]: %s' % (self._mName, str(error)), xbmc.LOGERROR)

	def __del__(self):
		self._close()

	@classmethod
	def instance(self, name, default = None, create = None):
		global DatabaseInstances
		if not name in DatabaseInstances:
			DatabaseInstances[name] = Database(name = name, default = default)
			if not create is None: DatabaseInstances[name]._create(create)
		return DatabaseInstances[name]

	@classmethod
	def path(self, name, id = None, info = 'profile', path = []):
		try:
			if not name.endswith(Database.Extension): name += Database.Extension
			return os.path.join(xbmcvfs.translatePath((xbmcaddon.Addon(id) if id else xbmcaddon.Addon()).getAddonInfo(info)), *path, name)
		except:
			return None

	@classmethod
	def pathCache(self):
		return self.path(name = Database.NameCache)

	@classmethod
	def pathPlayback(self):
		return self.path(name = Database.NamePlayback)

	@classmethod
	def pathProviders(self):
		return self.path(name = Database.NameProviders)

	@classmethod
	def pathMetadata(self):
		return self.path(name = Database.NameMetadata)

	def _lock(self):
		self._mLockCustom.acquire()

	def _unlock(self):
		try: self._mLockCustom.release()
		except: pass

	def __lock(self):
		self._mLock.acquire()

	def __unlock(self):
		try: self._mLock.release()
		except: pass

	def _connect(self):
		try:
			# When the addon is launched for the first time after installation, an error occurs, since the addon userdata directory does not exist yet and the database file is written to that directory.
			# If the directory does not exist yet, create it.
			xbmcvfs.mkdirs(os.path.dirname(os.path.abspath(self._mPath)))

			# SQLite does not allow database objects to be used from multiple threads. Explicitly allow multi threading.
			self.__lock()
			try: self._mConnection = database.connect(self._mPath, check_same_thread = False, timeout = Database.Timeout)
			except: self._mConnection = database.connect(self._mPath, timeout = Database.Timeout)

			if self._mLabel: self._mConnection.row_factory = database.Row # SELECT rows as a dictionary instead of a list.
			self._mDatabase = self._mConnection.cursor()

			self.__unlock()

			self._initialize()
			return True
		except Exception as error:
			xbmc.log('GAIA ERROR [Database Connection - %s]: %s (%s)' % (self._mName, str(error), self._mPath), xbmc.LOGERROR)
			return False
		finally:
			self.__unlock()

	def _addon(self):
		if self._mAddon: return xbmcaddon.Addon(self._mAddon)
		else: return xbmcaddon.Addon()

	def _initialize(self):
		pass

	def _list(self, items):
		if not type(items) in [list, tuple]: items = [items]
		return items

	def _close(self):
		try: self._mDatabase.close()
		except: pass
		try: self._mConnection.close()
		except: pass

	def _null(self):
		return 'NULL'

	def _commit(self):
		try:
			self._mConnection.commit()
			return True
		except:
			return False

	def _compress(self, commit = True, lock = True, unlock = True, log = True):
		return self._execute('vacuum', commit = commit, lock = lock, unlock = unlock, log = log) # Reduce the file size.

	def _size(self):
		return xbmcvfs.File(self._mPath).size()

	def _execute(self, query, parameters = None, commit = True, compress = False, lock = True, unlock = True, log = True):
		try:
			if lock: self.__lock()
			try: query = query % self._mName
			except: pass
			if parameters is None: self._mDatabase.execute(query)
			else: self._mDatabase.execute(query, parameters)

			# There is a bug in SQLite for Python 3.6: cannot VACUUM from within a transaction
			# Try to compress and if unsuccessful, try again after commit.
			# https://github.com/ghaering/pysqlite/issues/109
			'''if compress: compressed = self._compress(commit = False, lock = False, unlock = False, log = False)
			if commit: self._commit()
			if compress and not compressed: self._compress(commit = True, lock = False, unlock = False)'''

			# Update: does it not make sense to compress AFTER the commit?
			# https://stackoverflow.com/questions/2250462/should-i-run-vacuum-in-transaction-or-after
			if commit: self._commit()
			if compress: self._compress(commit = True, lock = False, unlock = False)

			return True
		except Exception as error:
			if log:
				# Limit query printed to file, since some queries are very big (eg: providers), filling up the log file.
				xbmc.log('GAIA ERROR [Database Query - %s]: %s -- %s' % (self._mName, str(error), str(query[:2000])), xbmc.LOGERROR)

				# Database file lock errors. Notify the user to restart Kodi.
				if 'is locked' in str(error):
					import time
					timestamp = int(time.time())
					last = xbmcgui.Window(10000).getProperty('GaiaDatabaseLock')
					if not last or timestamp - int(last) >= 180: # Only show every 3 minutes.
						xbmcgui.Window(10000).setProperty('GaiaDatabaseLock', str(timestamp))
						addon = self._addon()
						xbmcgui.Dialog().notification('%s - %s' % (addon.getAddonInfo('name'), addon.getLocalizedString(33949)), addon.getLocalizedString(33950), xbmcgui.NOTIFICATION_ERROR, 10000, True)
				return False
		finally:
			if unlock: self.__unlock()

	# query must contain %s for table name.
	# tables can be None, table name, or list of tables names.
	# If tables is None, will retrieve all tables in the database.
	def _executeAll(self, query, tables = None, parameters = None, commit = True, compress = True, lock = True, unlock = True):
		try:
			if lock: self.__lock()
			result = True
			if tables is None: tables = self._tables(lock = False, unlock = False)
			tables = self._list(tables)
			for table in tables:
				result = result and self._execute(query % table, parameters = parameters, commit = False, compress = False, lock = False, unlock = False)

			# There is a bug in SQLite for Python 3.6: cannot VACUUM from within a transaction
			# Try to compress and if unsuccessful, try again after commit.
			# https://github.com/ghaering/pysqlite/issues/109
			'''if compress: compressed = self._compress(commit = False, lock = False, unlock = False, log = False)
			if commit: self._commit()
			if compress and not compressed: self._compress(commit = True, lock = False, unlock = False)'''

			if commit: self._commit()
			if compress: self._compress(commit = True, lock = False, unlock = False)

			return result
		finally:
			if unlock: self.__unlock()

	def _tables(self, lock = True, unlock = True):
		return self._selectValues('SELECT name FROM sqlite_master WHERE type IS "table"', lock = lock, unlock = unlock)

	def _create(self, query, parameters = None, commit = True):
		return self._execute(query, parameters = parameters, commit = commit)

	def _createAll(self, query, tables, parameters = None, commit = True):
		return self._executeAll(query, tables, parameters = parameters, commit = commit)

	# Retrieves a list of rows.
	# Each row is a tuple with all the return values.
	# Eg: [(row1value1, row1value2), (row2value1, row2value2)]
	def _select(self, query, parameters = None, lock = True, unlock = True):
		try:
			self._execute(query, parameters = parameters, commit = False, lock = lock, unlock = False)
			result = self._mDatabase.fetchall()
			if self._mLabel and result: result = [dict(i) for i in result]
			return result
		finally:
			if unlock: self.__unlock()

	# Retrieves a single row.
	# Each row is a tuple with all the return values.
	# Eg: (row1value1, row1value2)
	def _selectSingle(self, query, parameters = None, lock = True, unlock = True):
		try:
			self._execute(query, parameters = parameters, commit = False, lock = lock, unlock = False)
			result = self._mDatabase.fetchone()
			if self._mLabel and result: result = dict(result)
			return result
		finally:
			if unlock: self.__unlock()

	# Retrieves a list of single values from rows.
	# Eg: [row1value1, row1value2]
	def _selectValues(self, query, parameters = None, lock = True, unlock = True):
		try:
			result = self._select(query, parameters = parameters, lock = lock, unlock = unlock)
			if self._mLabel: return [list(i.values())[0] for i in result]
			else: return [i[0] for i in result]
		except:
			return []

	# Retrieves a single value from a single row.
	# Eg: row1value1
	def _selectValue(self, query, parameters = None, lock = True, unlock = True):
		try: return self._selectSingle(query, parameters = parameters, lock = lock, unlock = unlock)[0]
		except: return None

	# Checks if the value exists, such as an ID.
	def _exists(self, query, parameters = None):
		return len(self._select(query, parameters = parameters)) > 0

	def _insert(self, query, parameters = None, commit = True):
		return self._execute(query, parameters = parameters, commit = commit)

	def _update(self, query, parameters = None, commit = True):
		return self._execute(query, parameters = parameters, commit = commit)

	# Deletes specific row in table.
	# If table is none, assumes it was already set in the query
	def _delete(self, query, table = None, parameters = None, commit = True, compress = False):
		if not table is None: query = query % table
		return self._execute(query, parameters = parameters, commit = commit, compress = compress)

	# Deletes all rows in table.
	# tables can be None, table name, or list of tables names.
	# If tables is None, deletes all rows in all tables.
	def _deleteAll(self, query = None, tables = None, parameters = None, commit = True, compress = True):
		if query is None: query = 'DELETE FROM `%s`;'
		return self._executeAll(query, tables, parameters = parameters, commit = commit, compress = compress)

	def _deleteFile(self):
		from lib.modules import tools
		return tools.File.delete(self._mPath)

	# Drops single table.
	def _drop(self, table, parameters = None, commit = True, compress = True):
		return self._execute('DROP TABLE IF EXISTS `%s`;' % table, parameters = parameters, commit = commit, compress = compress)

	# Drops all tables.
	def _dropAll(self, parameters = None, commit = True, compress = True):
		return self._executeAll('DROP TABLE IF EXISTS `%s`;', parameters = parameters, commit = commit, compress = compress)

	# tables can be None, table name, or list of tables names.
	# If tables is provided, only clears the specific table(s), otherwise clears all tables.
	def clear(self, tables = None, confirm = False):
		title = self._addon().getAddonInfo('name') + ' - ' + self._addon().getLocalizedString(33013)
		message = self._addon().getLocalizedString(33042)
		if not confirm or xbmcgui.Dialog().yesno(title, message):
			self._deleteAll(tables = tables)
			if confirm:
				message = self._addon().getLocalizedString(33043)

				icon = xbmcaddon.Addon('script.gaia.resources').getAddonInfo('path')
				icon = self._addon().getAddonInfo('profile')
				icon = xbmcvfs.translatePath(self._mPath)

				icon = os.path.join(icon, 'resources', 'media', 'notifications', 'information.png')
				xbmcgui.Dialog().notification(title, message, icon = icon)


class Dummy(Database):

	Name = 'dummy'

	def __init__(self):
		Database.__init__(self, Dummy.Name)

	def _initialize(self):
		self._createAll('CREATE TABLE IF NOT EXISTS `%s` (value INTEGER);', [Dummy.Name])

	def _result(self, result):
		self._deleteFile()
		return result

	def test(self):
		if not xbmcvfs.exists(self._mPath): return self._result(False)
		value = 9
		self._insert('INSERT INTO `%s` (value) VALUES (?);', parameters = (value,))
		result = self._selectValue('SELECT value FROM `%s`;')
		return self._result(result == value)
