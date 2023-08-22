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

	# Make sure to add new ones to _cleanSettingsDatabases().
	NameCache = 'cache'
	NameHistory = 'history'
	NameLibrary = 'library'
	NamePlayback = 'playback'
	NameProviders = 'providers'
	NameStreams = 'streams'
	NameMetadata = 'metadata'
	NameSearches = 'searches'
	NameShortcuts = 'shortcuts'
	NameTrailers = 'trailers'
	NameDownloads = 'downloads'
	NameSettings = 'settings'

	LimitSetting = 'general.database.limit'
	LimitFree = 0.8

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
	def pathStreams(self):
		return self.path(name = Database.NameStreams)

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
		self._execute(query, parameters = parameters, commit = commit, compress = compress)
		try: return self._mDatabase.rowcount # Number of rows deleted.
		except: return 0

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

	##############################################################################
	# CLEAN
	##############################################################################

	# time: delete everything before this time.
	# size: delete until the size is lower than this.
	def clean(self, time = None, size = None, force = False):
		result = False
		try:
			if size:
				if not force: size = max(size, 5242880) # 5 MB

				sizeBefore = self._size()
				if sizeBefore > size:
					# Compress before checking the size for the first time.
					# For large databases (300MB+) this can take 5secs+ on an SSD.
					# Update: This can take long for large databases. Only makes sense to compress if we just removed rows from the database.
					#self._compress()

					if sizeBefore > size:
						# We want to delete more rows in one go, since every deletion + compression can take a long time.
						# A better way would be to count the rows. However, SQLite is very slow with COUNT(*).
						count = max(10, min(100, int(sizeBefore / 5242880.0)))

						sizeChanged = 0

						for i in range(100000 if force else 1000):
							timed = self._cleanTime(count = count)
							if not timed: break
							timed = self._cleanAdjust(time = timed, force = force)

							if self._clean(time = timed, commit = False, compress = False):
								self._commit()
								self._compress()
								sizeAfter = self._size()

								# Sometimes deleting a few rows from a small database does not change the file size, even after compressing.
								# Check a few iterations before breaking out of the loop.
								if sizeBefore == sizeAfter:
									sizeChanged += 1
									if sizeChanged >= 2: break
								else:
									sizeChanged = 0

								result = True
								if sizeAfter < size: break
								sizeBefore = sizeAfter
							else:
								break # No rows deleted.
			if time:
				if self._clean(time = self._cleanAdjust(time = time, force = force), commit = False, compress = False):
					self._compress(commit = True)
				result = True
		except:
			from lib.modules.tools import Logger
			Logger.error()
		return result

	def cleanCompress(self):
		self._compress()

	def cleanReduce(self):
		self.clean(size = self._cleanSettings(name = self._mName))

	@classmethod
	def cleanAutomatic(self, wait = False):
		if wait:
			self._cleanAutomatic()
		else:
			from lib.modules.concurrency import Pool
			Pool.thread(target = self._cleanAutomatic, start = True)

	@classmethod
	def _cleanAutomatic(self):
		settings = self._cleanSettings()
		databases = self._cleanSettingsDatabases()

		# Initialize with the recommended values.
		if not settings:
			for database in databases:
				if database['type'] == 'automatic':
					self._cleanSettingsUpdate(database = database, value = database['recommended'], validate = False)
			settings = self._cleanSettings()

		for database in databases:
			if database['type'] == 'automatic':
				name = database['name']
				limit = settings[name] if name in settings else 0
				if limit: database['instance']().clean(size = limit)

	@classmethod
	def cleanSettings(self, settings = False):
		from lib.modules.tools import Settings
		from lib.modules.interface import Dialog

		self.tCanceled = False
		Dialog.information(title = 36036, refresh = self._cleanSettingsItems, reselect = Dialog.ReselectYes)

		if settings: Settings.launchData(id = Database.LimitSetting)

	@classmethod
	def _cleanSettings(self, name = None):
		from lib.modules.tools import Settings
		settings = Settings.getDataObject(Database.LimitSetting)
		if not settings: settings = {}
		if name: return settings[name] if name in settings else None
		return settings

	@classmethod
	def _cleanSettingsDatabases(self):
		from lib.meta.cache import MetaCache
		from lib.providers.core.manager import Manager
		from lib.modules.history import History
		from lib.modules.cache import Cache
		from lib.modules.playback import Playback
		from lib.modules.search import Search
		from lib.modules.video import Trailer

		return [
			{
				'name'			: Database.NameMetadata,
				'instance'		: MetaCache.instance,
				'type'			: 'automatic',
				'precent'		: 0.20,
				'minimum'		: 52428800,				# 50MB
				'maximum'		: 4294967296,			# 4GB
				'recommended'	: 1073741824,			# 1GB
			},
			{
				'name'			: Database.NameStreams,
				'instance'		: Manager.streamsDatabaseInstance,
				'type'			: 'automatic',
				'precent'		: 0.45,
				'minimum'		: 52428800,				# 50MB
				'maximum'		: 4294967296,			# 4GB
				'recommended'	: 1073741824,			# 1GB
			},
			{
				'name'			: Database.NameHistory,
				'instance'		: History,
				'type'			: 'automatic',
				'precent'		: 0.19,
				'minimum'		: 52428800,				# 50MB
				'maximum'		: 4294967296,			# 4GB
				'recommended'	: 1073741824,			# 1GB
			},
			{
				'name'			: Database.NameCache,
				'instance'		: Cache.instance,
				'type'			: 'automatic',
				'precent'		: 0.10,
				'minimum'		: 52428800,				# 50MB
				'maximum'		: 2147483648,			# 2GB
				'recommended'	: 262144000,			# 250MB
			},
			{
				'name'			: Database.NamePlayback,
				'instance'		: Playback.instance,
				'type'			: 'automatic',
				'precent'		: 0.02,
				'minimum'		: 10485760,				# 10MB
				'maximum'		: 1073741824,			# 1GB
				'recommended'	: 104857600,			# 100MB
			},
			{
				'name'			: Database.NameSearches,
				'instance'		: Search,
				'type'			: 'automatic',
				'precent'		: 0.02,
				'minimum'		: 10485760,				# 10MB
				'maximum'		: 1073741824,			# 1GB
				'recommended'	: 104857600,			# 100MB
			},
			{
				'name'			: Database.NameTrailers,
				'instance'		: Trailer,
				'type'			: 'automatic',
				'precent'		: 0.02,
				'minimum'		: 10485760,				# 10MB
				'maximum'		: 1073741824,			# 1GB
				'recommended'	: 104857600,			# 100MB
			},
			{
				'name'			: Database.NameLibrary,
				'type'			: 'manual',
				'precent'		: 0.0,
				'minimum'		: 0,					# Unlimited
				'maximum'		: 0,					# Unlimited
				'recommended'	: 0,					# Unlimited
			},
			{
				'name'			: Database.NameShortcuts,
				'type'			: 'manual',
				'precent'		: 0.0,
				'minimum'		: 0,					# Unlimited
				'maximum'		: 0,					# Unlimited
				'recommended'	: 0,					# Unlimited
			},
			{
				'name'			: Database.NameDownloads,
				'type'			: 'manual',
				'precent'		: 0.0,
				'minimum'		: 0,					# Unlimited
				'maximum'		: 0,					# Unlimited
				'recommended'	: 0,					# Unlimited
			},
			{
				'name'			: Database.NameProviders,
				'type'			: 'fixed',
				'precent'		: 0.0,
				'minimum'		: 0,					# Unlimited
				'maximum'		: 0,					# Unlimited
				'recommended'	: 0,					# Unlimited
			},
			{
				'name'			: Database.NameSettings,
				'type'			: 'fixed',
				'precent'		: 0.0,
				'minimum'		: 0,					# Unlimited
				'maximum'		: 0,					# Unlimited
				'recommended'	: 0,					# Unlimited
			},
		]

	@classmethod
	def _cleanSettingsItems(self):
		if self.tCanceled: return None

		from lib.modules.interface import Loader, Dialog, Translation
		from lib.modules.convert import ConverterSize
		from lib.modules.tools import Hardware

		Loader.show()

		settings = self._cleanSettings()
		of = Translation.string(33073)
		unlimited = Translation.string(35221)

		totalSize = 0
		totalLimit = 0
		totalUnlimited = False
		free = Hardware.storageUsageFreeBytes(refresh = True)
		usable = int(free * Database.LimitFree)

		limits = []
		for database in self._cleanSettingsDatabases():
			name = database['name']

			size = Database(name = name, connect = False)._size()
			totalSize += size

			limit = settings[name] if name in settings else 0
			totalLimit += limit

			if database['type'] == 'automatic' and not limit: totalUnlimited = True

			database['optimized'] = max(database['minimum'], min(database['maximum'], int(database['precent'] * usable) - size))

			label = '%s %s %s' % (ConverterSize(size, unit = ConverterSize.Byte).stringOptimal(), of, ConverterSize(limit, unit = ConverterSize.Byte).stringOptimal() if limit else unlimited)
			limits.append({'title' : name.capitalize(), 'value' : label, 'prefix' : True, 'action' : self._cleanSettingsSelect, 'parameters' : {'database' : database}})

		statistics = [
			{'title' : 36435, 'value' : ConverterSize(free, unit = ConverterSize.Byte).stringOptimal()},
			{'title' : 36436, 'value' : ConverterSize(totalSize, unit = ConverterSize.Byte).stringOptimal()},
			{'title' : 36439, 'value' : ConverterSize(totalLimit, unit = ConverterSize.Byte).stringOptimal() if totalLimit and not totalUnlimited else unlimited},
		]

		items = [
			{'title' : Dialog.prefixBack(33486), 'close' : True},
			{'title' : Dialog.prefixNext(33239), 'action' : self._cleanSettingsHelp},
			{'title' : Dialog.prefixNext(36447), 'action' : self._cleanSettingsCompress},
			{'title' : Dialog.prefixNext(35269), 'action' : self._cleanSettingsOptimize},
			{'title' : 36437, 'items' : statistics},
			{'title' : 35220, 'items' : limits},
		]

		Loader.hide()
		return items

	@classmethod
	def _cleanSettingsHelp(self):
		from lib.modules.interface import Dialog
		Dialog.details(title = 36036, items = [
			{'type' : 'title', 'value' : 'Overview', 'break' : 2},
			{'type' : 'text', 'value' : 'Multiple databases are created by Gaia on the device\'s local disk. Some databases can grow very large over time. You can specify database file size limits if you have little storage space available. When Gaia is launched, these limits will be applied and old entries are deleted from the databases in order to reduce the file size. Note that this is only a best effort and there is no guarantee that the exact limits will always be maintained. Also note that these limits only apply to Gaia databases. Other files created by Gaia, other addons, or Kodi are not included.', 'break' : 2},
			{'type' : 'title', 'value' : 'Limits', 'break' : 2},
			{'type' : 'text', 'value' : 'Gaia should work well with at least [B]250MB[/B] of free disk space for all databases combined. Although Gaia might still work with less storage space, certain features might stop working after some time. To get the best performance out of Gaia, you should have [B]1GB[/B] or more free disk space.', 'break' : 2},
			{'type' : 'text', 'value' : 'Take the following into account when choosing limits:', 'break' : 2},
			{'type' : 'list', 'value' : [
				{'title' : 'Low Limits', 'value' : 'If limits are too low (typically below 50MB per database), you might free up storage space, however there might be performance implications for the addon. If entries are constantly deleted from the databases in order to adhere to the file size limits, this data has to be retrieved again in the future, putting a burden on external servers and your internet connection. This in turn might slow down menu loading and various other features in the addon.'},
				{'title' : 'High Limits', 'value' : 'If limits are too high (typically above 2GB per database), there should generally not be any issues. However, the larger a database becomes, the slower access to the database becomes. This slowdown should be marginal and will probably not be noticed while using the addon. It is typically better to keep a larger than a smaller database.'},
			], 'number' : False},
			{'type' : 'title', 'value' : 'Databases', 'break' : 2},
			{'type' : 'text', 'value' : 'The following databases are utilized:', 'break' : 2},
			{'type' : 'list', 'value' : [
				{'title' : 'Metadata', 'value' : 'This stores all the movie and show metadata used by menus and other features. This database can grow large over time, but should generally not be limited too much, since it will slow down menus.'},
				{'title' : 'Streams', 'value' : 'This stores all the streams returned by providers during scraping. Streams are stored locally so that they can be quickly reloaded without having to go through the scraping process again. For instance, during binging the next episode is scraped, but you might not want to watch it now. If you want to watch the episode a few days later, the streams can just be retrieved from disk instead of starting the scraping process again. This database can grow very large over time and should be limited to avoid performance implications during scraping. This database is also cleaned up automatically by the [I]Save Streams[/I]  settings under the [I]Scraping[/I]  tab, which automatically deletes old streams after a few days, instead of limiting it by size.'},
				{'title' : 'History', 'value' : 'This stores the streams you played in the past, allowing you to quickly resume playback of the stream in the future. It is similar to the [I]Streams[/I]  database, except that it only stores the streams that you actually played. This database can grow large over time and should be limited to avoid performance implications.'},
				{'title' : 'Cache', 'value' : 'This stores all the temporary network requests so that if a request is executed again in the near future, the results can be quickly retrieved from disk. This database should stay relatively small and should generally not be limited too much, since it will slow down most of the functionality.'},
				{'title' : 'Playback', 'value' : 'This stores your playback progress, watched status, and various other playback attributes. Most of the data is also synchronized to Trakt if you have an account authenticated. This database should stay relatively small and should generally not be impacted a lot from strict limits.'},
				{'title' : 'Searches', 'value' : 'This stores all the searches you made in the past, including chats with the Oracle. This database should stay relatively small and should generally not be impacted a lot from strict limits.'},
				{'title' : 'Trailers', 'value' : 'This stores all the trailers you played in the past. This database should stay relatively small and should generally not be impacted a lot from strict limits.'},
				{'title' : 'Library', 'value' : 'his stores data when using the addon in combination with Kodi\'s local library. Depending on how you use it, the size could grow large over time. This database is not controlled by any limits, since it does not contain historic data, but rather data manually added by you. You should manage this database yourself if you utilize the features.'},
				{'title' : 'Shortcuts', 'value' : 'This stores shortcuts you manually create in the addon menus. This database will always stay small. This database is not controlled by any limits, since it does not contain historic data, but rather data manually added by you. You should manage this database yourself if you utilize the features.'},
				{'title' : 'Downloads', 'value' : 'This stores information for the integrated download manager. This database will always stay small. This database is not controlled by any limits, since it does not contain historic data, but rather data manually added by you. You should manage this database yourself if you utilize the features.'},
				{'title' : 'Providers', 'value' : 'This stores information about the providers in the addon. This database will always stay small. This database is not controlled by any limits, since it does not contain historic data.'},
				{'title' : 'Settings', 'value' : 'This stores detailed settings that are too large to store in the normal Kodi addon settings. This database will always stay small. This database is not controlled by any limits, since it does not contain historic data.'},
			], 'number' : False},
		])

	@classmethod
	def _cleanSettingsCompress(self, database = None):
		from lib.modules.interface import Dialog, Loader

		choice = Dialog.options(title = 36036, message = 36448, labelConfirm = 32532, labelDeny = 36447, labelCustom = 33743)
		if choice == Dialog.ChoiceCustom: return False

		Loader.show()
		try:
			databases = [database] if database else self._cleanSettingsDatabases()
			for database in databases:
				if database['type'] == 'automatic':
					instance = database['instance']()
					if choice == Dialog.ChoiceYes: instance.cleanReduce()
					elif choice == Dialog.ChoiceNo: instance.cleanCompress()
		except:
			from lib.modules.tools import Logger
			Logger.error()
		Loader.hide()
		return True

	@classmethod
	def _cleanSettingsOptimize(self):
		from lib.modules.tools import Hardware
		from lib.modules.interface import Dialog, Translation
		from lib.modules.convert import ConverterSize

		choice = Dialog.options(title = 36036, message = 36449, labelConfirm = 35233, labelDeny = 33348, labelCustom = 33743)
		if choice == Dialog.ChoiceCustom: return False

		size = 0
		free = Hardware.storageUsageFreeBytes(refresh = True)
		databases = self._cleanSettingsDatabases()

		if choice == Dialog.ChoiceYes:
			for database in databases:
				size += database['recommended']
			size = ConverterSize(size, unit = ConverterSize.Byte).value(unit = ConverterSize.ByteMega, places = ConverterSize.PlacesNone)
			size = Dialog.input(title = 36036, type = Dialog.InputNumeric, default = size)
			if not size: return False
			size = ConverterSize(size, unit = ConverterSize.ByteMega).value(unit = ConverterSize.Byte, places = ConverterSize.PlacesNone)
		elif choice == Dialog.ChoiceNo:
			precent = Dialog.input(title = 36036, type = Dialog.InputNumeric, default = 50)
			if not precent: return False
			size = int(free * (precent / 100.0))

		if size:
			labelFree = ConverterSize(free, unit = ConverterSize.Byte).stringOptimal()
			labelSize = ConverterSize(size, unit = ConverterSize.Byte).stringOptimal()
			if Dialog.option(title = 36036, message = Translation.string(36450) % (labelFree, labelSize)):
				for database in databases:
					if database['type'] == 'automatic':
						self._cleanSettingsUpdate(database = database, value = database['precent'] * size, validate = False)
				return True
		return False

	@classmethod
	def _cleanSettingsSelect(self, database):
		from lib.modules.interface import Dialog
		from lib.modules.tools import Tools

		if database['type'] == 'automatic':
			choice = Dialog.information(title = 36036, refresh = lambda : self._cleanSettingsSelectItems(database), reselect = Dialog.ReselectYes)
			if Tools.isInteger(choice) and choice < 0: self.tCanceled = True
		else:
			Dialog.confirm(title = 36036, message = 36445 if database['type'] == 'fixed' else 36446)

	@classmethod
	def _cleanSettingsSelectItems(self, database):
		from lib.modules.interface import Dialog, Translation
		from lib.modules.tools import Hardware
		from lib.modules.convert import ConverterSize

		unlimited = Translation.string(35221)

		# Recalculate these, in case we use the "Compress" action.
		name = database['name']
		free = Hardware.storageUsageFreeBytes(refresh = True)
		usable = int(free * Database.LimitFree)
		size = Database(name = name, connect = False)._size()
		settings = self._cleanSettings()
		limit = settings[name] if name in settings else 0

		return [
			{'title' : Dialog.prefixBack(35374), 'close' : True},
			{'title' : Dialog.prefixNext(33239), 'action' : self._cleanSettingsHelp},
			{'title' : Dialog.prefixNext(36447), 'action' : self._cleanSettingsCompress, 'parameters' : {'database' : database}},
			{'title' : 36437, 'items' : [
				{'title' : 33026, 'value' : database['name'].capitalize()},
				{'title' : 36435, 'value' : ConverterSize(free, unit = ConverterSize.Byte).stringOptimal()},
				{'title' : 36429, 'value' : ConverterSize(size, unit = ConverterSize.Byte).stringOptimal()},
				{'title' : 36438, 'value' : ConverterSize(limit, unit = ConverterSize.Byte).stringOptimal() if limit else unlimited},
			]},
			{'title' : 35220, 'items' : [
				{'title' : 36430, 'prefix' : True, 'close' : True, 'value' : ConverterSize(database['minimum'], unit = ConverterSize.Byte).stringOptimal(), 'action' : self._cleanSettingsUpdate, 'parameters' : {'database' : database, 'limit' : limit, 'free' : free, 'usable' : usable, 'value' : database['minimum']}},
				{'title' : 36431, 'prefix' : True, 'close' : True, 'value' : ConverterSize(database['maximum'], unit = ConverterSize.Byte).stringOptimal(), 'action' : self._cleanSettingsUpdate, 'parameters' : {'database' : database, 'limit' : limit, 'free' : free, 'usable' : usable, 'value' : database['maximum']}},
				{'title' : 36432, 'prefix' : True, 'close' : True, 'value' : ConverterSize(database['recommended'], unit = ConverterSize.Byte).stringOptimal(), 'action' : self._cleanSettingsUpdate, 'parameters' : {'database' : database, 'limit' : limit, 'free' : free, 'usable' : usable, 'value' : database['recommended']}},
				{'title' : 36433, 'prefix' : True, 'close' : True, 'value' : ConverterSize(database['optimized'], unit = ConverterSize.Byte).stringOptimal(), 'action' : self._cleanSettingsUpdate, 'parameters' : {'database' : database, 'limit' : limit, 'free' : free, 'usable' : usable, 'value' : database['optimized']}},
				{'title' : 36440, 'prefix' : True, 'close' : True, 'value' : unlimited, 'action' : self._cleanSettingsUpdate, 'parameters' : {'database' : database, 'limit' : limit, 'free' : free, 'usable' : usable, 'value' : 0}},
				{'title' : 36434, 'prefix' : True, 'close' : True, 'value' : 35233, 'action' : self._cleanSettingsUpdate, 'parameters' : {'database' : database, 'limit' : limit, 'free' : free, 'usable' : usable, 'value' : None}},
			]},
		]

	@classmethod
	def _cleanSettingsUpdate(self, database, limit = None, free = None, usable = None, value = None, validate = True):
		from lib.modules.tools import Settings
		from lib.modules.interface import Dialog, Translation
		from lib.modules.convert import ConverterSize

		if validate:
			if value is None:
				value = ConverterSize(limit or database['recommended'], unit = ConverterSize.Byte).value(unit = ConverterSize.ByteMega, places = ConverterSize.PlacesNone)
				value = Dialog.input(title = 36036, type = Dialog.InputNumeric, default = value)
				value = ConverterSize(value, unit = ConverterSize.ByteMega).value(unit = ConverterSize.Byte, places = ConverterSize.PlacesNone)

			if value == 0:
				choice = Dialog.options(title = 36036, message = 36443, labelConfirm = 33925, labelDeny = 33633, labelCustom = 33743)
				if choice == Dialog.ChoiceYes: value = database['maximum']
				elif choice == Dialog.ChoiceCustom: return False

			if value > 0 and value < database['minimum']:
				choice = Dialog.options(title = 36036, message = 36441, labelConfirm = 33925, labelDeny = 33633, labelCustom = 33743)
				if choice == Dialog.ChoiceYes: value = database['minimum']
				elif choice == Dialog.ChoiceCustom: return False

			if value > 0 and value > database['maximum']:
				choice = Dialog.options(title = 36036, message = 36442, labelConfirm = 33925, labelDeny = 33633, labelCustom = 33743)
				if choice == Dialog.ChoiceYes: value = database['maximum']
				elif choice == Dialog.ChoiceCustom: return False

			if value > usable:
				choice = Dialog.options(title = 36036, message = 36444, labelConfirm = 33925, labelDeny = 33633, labelCustom = 33743)
				if choice == Dialog.ChoiceYes: value = database['optimized']
				elif choice == Dialog.ChoiceCustom: return False

		settings = self._cleanSettings()
		settings[database['name']] = value

		label = 0
		for database in self._cleanSettingsDatabases():
			if database['type'] == 'automatic':
				name = database['name']
				if name in settings:
					if settings[name] == 0:
						label = 0
						break
					else:
						label += settings[name]
		if label == 0: label = Translation.string(35221)
		else: label = ConverterSize(label, unit = ConverterSize.Byte).stringOptimal()

		Settings.setData(id = Database.LimitSetting, value = settings, label = label)

		return True

	def _cleanAdjust(self, time, force = False):
		# Ignore if the given time is within the past 30 hours.
		# Otherwise entries are constantly deleted and filled up again immediately.
		if not force:
			from lib.modules.tools import Time
			time = min(time, Time.past(hours = 30))
		return time

	# Should be overwritten by subclasses to clear older entries and reduce disk storage space.
	def _clean(self, time, commit = True, compress = True):
		return None

	# Should be overwritten by subclasses.
	# Takes in a number of rows to delete.
	# Returns a singel timestamp for all tables in the database, which can be used to remove all old rows before the timestamp.
	def _cleanTime(self, count):
		return None


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
