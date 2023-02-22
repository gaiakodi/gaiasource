# -*- coding: utf-8 -*-

'''
	Gaia Add-on
	Copyright (C) 2016 Gaia

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from lib.modules.database import Database
from lib.modules.concurrency import Lock
from lib.modules.tools import Media, Time, Tools, Language, Country, Converter, Logger, File, System, Settings
from lib.meta.tools import MetaTools

class MetaCache(Database):

	Name				= 'metadata'

	Attribute			= 'cache'
	AttributeRefresh	= 'refresh'
	AttributeStatus		= 'status'
	AttributeTime		= 'time'
	AttributeSettings	= 'settings'
	AttributeComplete	= 'complete'

	TypeMovie			= Media.TypeMovie
	TypeSet				= Media.TypeSet
	TypeShow			= Media.TypeShow
	TypeSeason			= Media.TypeSeason
	TypeEpisode			= Media.TypeEpisode
	Types				= [TypeMovie, TypeSet, TypeShow, TypeSeason, TypeEpisode]

	RefreshNone			= None
	RefreshForeground	= 'foreground'
	RefreshBackground	= 'background'

	StatusCurrent		= 'current'		# Available in database and is still new.
	StatusOutdated		= 'outdated'	# Available in database, but is outdated and needs a background refresh.
	StatusObsolete		= 'obsolete'	# Available in database, but is outdated and needs a foreground refresh.
	StatusSettings		= 'settings'	# Available in database, but with a different settings configuration.
	StatusIncomplete	= 'incompelte'	# Available in database, but is partial data and needs a background refresh.
	StatusExternal		= 'external'	# Available in external preprocessed database, but might be outdated or not according to the user's settings and therefore needs a background refresh.
	StatusInvalid		= 'invalid'		# Not in database at all.

	# When the data outdated and should be refreshed in the background while the old cached data is still returned and displayed.
	TimeOutdated		= 2678400		# 1 Month.
	TimeOutdatedMovie	= TimeOutdated
	TimeOutdatedSet		= TimeOutdated
	TimeOutdatedShow	= TimeOutdated
	TimeOutdatedSeason	= TimeOutdated
	TimeOutdatedEpisode	= TimeOutdated

	# When the data should be forefully refreshed even if there is old cached data, since the metadata is too outdated to still be considered valid.
	# Keep this at a very long time, since one can always show the new data by reloading the menu after it wass refreshed in the background.
	TimeObsolete		= 31556952		# 1 Year.
	TimeObsoleteMovie	= TimeObsolete
	TimeObsoleteSet		= TimeObsolete
	TimeObsoleteShow	= TimeObsolete
	TimeObsoleteSeason	= TimeObsolete
	TimeObsoleteEpisode	= TimeObsolete

	Instance			= None
	External			= None
	Settings			= None
	Lock				= Lock()

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		Database.__init__(self, name = MetaCache.Name)

	@classmethod
	def instance(self):
		if MetaCache.Instance is None:
			MetaCache.Lock.acquire()
			if MetaCache.Instance is None: MetaCache.Instance = MetaCache()
			MetaCache.Lock.release()
		return MetaCache.Instance

	def _initialize(self):
		self._create('''
			CREATE TABLE IF NOT EXISTS `%s`
			(
				time INTEGER,
				complete BOOLEAN,
				settings TEXT,

				idImdb TEXT,
				idTmdb TEXT,
				idTvdb TEXT,
				idTrakt TEXT,
				idTvmaze TEXT,
				idSlug TEXT,

				data TEXT,

				PRIMARY KEY(settings, idImdb, idTmdb)
			);
			''' % MetaCache.TypeMovie,
		)
		self._create('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idImdb, idTmdb);' % (MetaCache.TypeMovie, MetaCache.TypeMovie))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_2 ON `%s`(idImdb);' % (MetaCache.TypeMovie, MetaCache.TypeMovie))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_3 ON `%s`(idTmdb);' % (MetaCache.TypeMovie, MetaCache.TypeMovie))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_4 ON `%s`(idTrakt);' % (MetaCache.TypeMovie, MetaCache.TypeMovie))

		self._create('''
			CREATE TABLE IF NOT EXISTS `%s`
			(
				time INTEGER,
				complete BOOLEAN,
				settings TEXT,

				idImdb TEXT,
				idTmdb TEXT,
				idTvdb TEXT,
				idTrakt TEXT,
				idTvmaze TEXT,
				idSlug TEXT,

				data TEXT,

				PRIMARY KEY(settings, idTmdb)
			);
			''' % MetaCache.TypeSet,
		)
		self._create('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idTmdb);' % (MetaCache.TypeSet, MetaCache.TypeSet))

		self._create('''
			CREATE TABLE IF NOT EXISTS `%s`
			(
				time INTEGER,
				complete BOOLEAN,
				settings TEXT,

				idImdb TEXT,
				idTmdb TEXT,
				idTvdb TEXT,
				idTrakt TEXT,
				idTvmaze TEXT,
				idSlug TEXT,

				data TEXT,

				PRIMARY KEY(settings, idImdb, idTvdb)
			);
			''' % MetaCache.TypeShow,
		)
		self._create('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idImdb, idTvdb);' % (MetaCache.TypeShow, MetaCache.TypeShow))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_2 ON `%s`(idImdb);' % (MetaCache.TypeShow, MetaCache.TypeShow))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_3 ON `%s`(idTvdb);' % (MetaCache.TypeShow, MetaCache.TypeShow))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_4 ON `%s`(idTrakt);' % (MetaCache.TypeShow, MetaCache.TypeShow))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_5 ON `%s`(idTvmaze);' % (MetaCache.TypeShow, MetaCache.TypeShow))

		self._create('''
			CREATE TABLE IF NOT EXISTS `%s`
			(
				time INTEGER,
				complete BOOLEAN,
				settings TEXT,

				idImdb TEXT,
				idTmdb TEXT,
				idTvdb TEXT,
				idTrakt TEXT,
				idTvmaze TEXT,
				idSlug TEXT,

				data TEXT,

				PRIMARY KEY(settings, idImdb, idTvdb)
			);
			''' % MetaCache.TypeSeason,
		)
		self._create('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idImdb, idTvdb);' % (MetaCache.TypeSeason, MetaCache.TypeSeason))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_2 ON `%s`(idImdb);' % (MetaCache.TypeSeason, MetaCache.TypeSeason))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_3 ON `%s`(idTvdb);' % (MetaCache.TypeSeason, MetaCache.TypeSeason))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_4 ON `%s`(idTrakt);' % (MetaCache.TypeSeason, MetaCache.TypeSeason))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_5 ON `%s`(idTvmaze);' % (MetaCache.TypeSeason, MetaCache.TypeSeason))

		self._create('''
			CREATE TABLE IF NOT EXISTS `%s`
			(
				time INTEGER,
				complete BOOLEAN,
				settings TEXT,

				idImdb TEXT,
				idTmdb TEXT,
				idTvdb TEXT,
				idTrakt TEXT,
				idTvmaze TEXT,
				idSlug TEXT,

				season INTEGER,

				data TEXT,

				PRIMARY KEY(settings, idImdb, idTvdb, season)
			);
			''' % MetaCache.TypeEpisode,
		)
		self._create('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idImdb, idTvdb, season);' % (MetaCache.TypeEpisode, MetaCache.TypeEpisode))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_2 ON `%s`(idImdb, season);' % (MetaCache.TypeEpisode, MetaCache.TypeEpisode))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_3 ON `%s`(idTvdb, season);' % (MetaCache.TypeEpisode, MetaCache.TypeEpisode))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_4 ON `%s`(idTrakt, season);' % (MetaCache.TypeEpisode, MetaCache.TypeEpisode))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_5 ON `%s`(idTvmaze, season);' % (MetaCache.TypeEpisode, MetaCache.TypeEpisode))

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		if settings:
			MetaCache.Settings = None
			MetaCache.External = None

	##############################################################################
	# SETTINGS
	##############################################################################

	@classmethod
	def settingsId(self):
		if MetaCache.Settings is None:
			MetaCache.Lock.acquire()
			if MetaCache.Settings is None:
				# This should include all values and settings that change the metadata before it is saved to the database.
				# If any of these settings change, the value  will not be retrieved from the database and force a refresh of the metadata.
				# This is better than clearing the cache and metadata databases everytime the user changes the settings.
				# NB: Do not add the rating settings here. More info under meta -> tools.py -> cleanVoting().

				from lib.modules.account import Imdb, Tmdb, Tvdb, Trakt, Fanart
				from lib.modules.tools import Hash
				from lib.meta.image import MetaImage
				from lib.meta.tools import MetaTools

				values = []

				# Metadata
				tools = MetaTools.instance()
				values.append(tools.settingsLanguage())
				values.append(tools.settingsCountry())
				values.append(tools.settingsDetail())

				# Images
				values.append(Converter.jsonTo(MetaImage.settingsInternal()))

				# Accounts
				values.extend([Imdb().dataId(), Tmdb().key(), Tvdb().pin(), Trakt().dataUsername(), Fanart().dataKey()])

				MetaCache.Settings = Hash.sha256('_'.join([i if i else ' ' for i in values]))
			MetaCache.Lock.release()

		return MetaCache.Settings

	##############################################################################
	# INTERNAL
	##############################################################################

	@classmethod
	def _type(self, type):
		typeMovie = False
		typeSet = False
		typeShow = False
		typeSeason = False
		typeEpisode = False
		if type == MetaCache.TypeMovie: typeMovie = True
		elif type == MetaCache.TypeSet: typeSet = True
		elif type == MetaCache.TypeShow: typeShow = True
		elif type == MetaCache.TypeSeason: typeSeason = True
		elif type == MetaCache.TypeEpisode: typeEpisode = True
		return typeMovie, typeSet, typeShow, typeSeason, typeEpisode

	@classmethod
	def _timeOutdated(self, type):
		if type == MetaCache.TypeMovie: return MetaCache.TimeOutdatedMovie
		elif type == MetaCache.TypeSet: return MetaCache.TimeOutdatedSet
		elif type == MetaCache.TypeShow: return MetaCache.TimeOutdatedShow
		elif type == MetaCache.TypeSeason: return MetaCache.TimeOutdatedSeason
		elif type == MetaCache.TypeEpisode: return MetaCache.TimeOutdatedEpisode

	@classmethod
	def _timeObsolete(self, type):
		if type == MetaCache.TypeMovie: return MetaCache.TimeObsoleteMovie
		elif type == MetaCache.TypeSet: return MetaCache.TimeObsoleteSet
		elif type == MetaCache.TypeShow: return MetaCache.TimeObsoleteShow
		elif type == MetaCache.TypeSeason: return MetaCache.TimeObsoleteSeason
		elif type == MetaCache.TypeEpisode: return MetaCache.TimeObsoleteEpisode

	@classmethod
	def _id(self, item):
		try:
			idImdb = item['imdb']
			if not idImdb or idImdb == '0' or idImdb == 'tt': idImdb = None
		except: idImdb = None

		try:
			idTmdb = item['tmdb']
			if not idTmdb or idTmdb == '0': idTmdb = None
		except: idTmdb = None

		try:
			idTvdb = item['tvdb']
			if not idTvdb or idTvdb == '0': idTvdb = None
		except: idTvdb = None

		try:
			idTrakt = item['trakt']
			if not idTrakt or idTrakt == '0': idTrakt = None
		except: idTrakt = None

		try:
			idTvmaze = item['tvmaze']
			if not idTvmaze or idTvmaze == '0': idTvmaze = None
		except: idTvmaze = None

		try:
			idSlug = item['slug']
			if not idSlug or idSlug == '0': idSlug = None
		except: idSlug = None

		return idImdb, idTmdb, idTvdb, idTrakt, idTvmaze, idSlug

	@classmethod
	def _season(self, item):
		try:
			season = item['season']
			if not season is None: season = int(season)
		except: season = None
		return season

	@classmethod
	def _external(self):
		if MetaCache.External is None:
			MetaCache.Lock.acquire()
			if MetaCache.External is None:
				try:
					path = System.pathMetadata()
					if path:
						path = File.joinPath(path, 'resources', 'data', 'metadata.db')
						if File.exists(path):
							if MetaTools.instance().settingsExternal():
								MetaCache.External = Database(path = path)
							else:
								Logger.log('Preprocessed Metadata setting disabled although the Gaia Metadata addon is installed. Menus might load faster if you enable the Preprocessed Metadata setting.')
								MetaCache.External = False
						else:
							MetaCache.External = False
					else:
						MetaCache.External = False
				except:
					Logger.error()
					MetaCache.External = False
			MetaCache.Lock.release()
		return MetaCache.External

	@classmethod
	def _externalEnable(self):
		MetaCache.External = None

	@classmethod
	def _externalDisable(self):
		MetaCache.External = False

	##############################################################################
	# INSERT
	##############################################################################

	def insert(self, type, items):
		try:
			result = True
			time = Time.timestamp()
			settings = self.settingsId()
			typeMovie, typeSet, typeShow, typeSeason, typeEpisode = self._type(type)

			# Sometimes the IDs are incorrect.
			# Especially Trakt sometimes returns the incorrect IMDb/TMDb/TVDb ID, specfically for less-known titles or newley/not-yet released titles.
			# First lookup with all available IDs and if not found, try to use individual IDs if order of importance.
			if typeMovie:
				queryInsert = 'INSERT INTO `%s` (time, complete, settings, idImdb, idTmdb, idTvdb, idTrakt, idTvmaze, idSlug, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);' % type
				queryDelete1 = 'DELETE FROM `%s` WHERE settings = ? AND idImdb = ? AND idTmdb = ?;' % type
				queryDelete2 = 'DELETE FROM `%s` WHERE settings = ? AND idImdb = ? AND idTmdb IS NULL;' % type
				queryDelete3 = 'DELETE FROM `%s` WHERE settings = ? AND idImdb IS NULL AND idTmdb = ?;' % type
				queryDelete4 = 'DELETE FROM `%s` WHERE settings = ? AND idImdb IS NULL AND idTmdb IS NULL AND idTvmaze = ?;' % type
			elif typeSet:
				queryInsert = 'INSERT INTO `%s` (time, complete, settings, idImdb, idTmdb, idTvdb, idTrakt, idTvmaze, idSlug, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);' % type
				queryDelete1 = 'DELETE FROM `%s` WHERE settings = ? AND idTmdb = ?;' % type
			elif typeShow:
				queryInsert = 'INSERT INTO `%s` (time, complete, settings, idImdb, idTmdb, idTvdb, idTrakt, idTvmaze, idSlug, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);' % type
				queryDelete1 = 'DELETE FROM `%s` WHERE settings = ? AND idImdb = ? AND idTvdb = ?;' % type
				queryDelete2 = 'DELETE FROM `%s` WHERE settings = ? AND idImdb = ? AND idTvdb IS NULL;' % type
				queryDelete3 = 'DELETE FROM `%s` WHERE settings = ? AND idImdb IS NULL AND idTvdb = ?;' % type
				queryDelete4 = 'DELETE FROM `%s` WHERE settings = ? AND idImdb IS NULL AND idTvdb IS NULL AND idTvmaze = ?;' % type
			elif typeSeason:
				queryInsert = 'INSERT INTO `%s` (time, complete, settings, idImdb, idTmdb, idTvdb, idTrakt, idTvmaze, idSlug, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);' % type
				queryDelete1 = 'DELETE FROM `%s` WHERE settings = ? AND idImdb = ? AND idTvdb = ?;' % type
				queryDelete2 = 'DELETE FROM `%s` WHERE settings = ? AND idImdb = ? AND idTvdb IS NULL;' % type
				queryDelete3 = 'DELETE FROM `%s` WHERE settings = ? AND idImdb IS NULL AND idTvdb = ?;' % type
				queryDelete4 = 'DELETE FROM `%s` WHERE settings = ? AND idImdb IS NULL AND idTvdb IS NULL AND idTvmaze = ?;' % type
			elif typeEpisode:
				queryInsert = 'INSERT INTO `%s` (time, complete, settings, idImdb, idTmdb, idTvdb, idTrakt, idTvmaze, idSlug, season, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);' % type
				queryDelete1 = 'DELETE FROM `%s` WHERE settings = ? AND idImdb = ? AND idTvdb = ? AND season = ?;' % type
				queryDelete2 = 'DELETE FROM `%s` WHERE settings = ? AND idImdb = ? AND idTvdb IS NULL AND season = ?;' % type
				queryDelete3 = 'DELETE FROM `%s` WHERE settings = ? AND idImdb IS NULL AND idTvdb = ? AND season = ?;' % type
				queryDelete4 = 'DELETE FROM `%s` WHERE settings = ? AND idImdb IS NULL AND idTvdb IS NULL AND idTvmaze = ? AND season = ?;' % type

			if not Tools.isArray(items): items = [items]
			for item in items:
				try:
					if item:
						idImdb, idTmdb, idTvdb, idTrakt, idTvmaze, idSlug = self._id(item)

						try: complete = item[MetaCache.Attribute][MetaCache.AttributeComplete]
						except:
							complete = True
							Logger.log('METACACHE: Missing "complete" attribute')

						try: del item[MetaCache.Attribute]
						except: pass
						try: del item['temp']
						except: pass

						queryDelete = None
						parametersDelete = None
						parametersInsert = None

						if typeMovie:
							if idImdb or idTmdb or idTvmaze:
								parametersInsert = []
								if idImdb and idTmdb:
									queryDelete = queryDelete1
									parametersDelete = [idImdb, idTmdb]
								elif idImdb:
									queryDelete = queryDelete2
									parametersDelete = [idImdb]
								elif idTmdb:
									queryDelete = queryDelete3
									parametersDelete = [idTmdb]
								elif idTvmaze:
									queryDelete = queryDelete4
									parametersDelete = [idTvmaze]
						elif typeSet:
							if idTmdb:
								parametersInsert = []
								if idTmdb:
									queryDelete = queryDelete1
									parametersDelete = [idTmdb]
						else:
							if idImdb or idTvdb or idTvmaze:
								parametersInsert = []
								if idImdb and idTvdb:
									queryDelete = queryDelete1
									parametersDelete = [idImdb, idTvdb]
								elif idImdb:
									queryDelete = queryDelete2
									parametersDelete = [idImdb]
								elif idTvdb:
									queryDelete = queryDelete3
									parametersDelete = [idTvdb]
								elif idTvmaze:
									queryDelete = queryDelete4
									parametersDelete = [idTvmaze]
								if typeEpisode:
									season = self._season(item)
									parametersDelete.append(season)
									parametersInsert.append(season)

						if not parametersDelete is None: self._delete(query = queryDelete, commit = False, parameters = [settings] + parametersDelete)
						if not parametersInsert is None: self._insert(query = queryInsert, commit = False, parameters = [time, complete, settings, idImdb, idTmdb, idTvdb, idTrakt, idTvmaze, idSlug] + parametersInsert + [Converter.jsonTo(item)])
				except:
					Logger.error()
					result = False

			self._commit()
			return result
		except:
			Logger.error()
			return False

	##############################################################################
	# SELECT
	##############################################################################

	def select(self, type, items):
		try:
			settings = self.settingsId()
			typeMovie, typeSet, typeShow, typeSeason, typeEpisode = self._type(type)

			timeCurrent = Time.timestamp()
			timeObsolete = self._timeObsolete(type)
			timeOutdated = self._timeOutdated(type)

			# Sometimes the IDs are incorrect.
			# Especially Trakt sometimes returns the incorrect IMDb/TMDb/TVDb ID, specfically for less-known titles or newley/not-yet released titles.
			# First lookup with all available IDs and if not found, try to use individual IDs if order of importance.

			# NB: Also lookup by TVmaze ID, since some shows/episodes retrieved from TVmaze do not have a IMDb/TVDb ID.
			# Otherwise detailed metadata is always re-retrieved for some episodes from TVmaze lists that only have a TVmaze ID, although the data is actually in the cache.

			if typeMovie:
				querySelect1 = 'SELECT time, complete, settings, data FROM `%s` WHERE idImdb = ? AND idTmdb = ? ORDER BY time DESC;' % type
				querySelect2 = 'SELECT time, complete, settings, data FROM `%s` WHERE idImdb = ? ORDER BY time DESC;' % type
				querySelect3 = 'SELECT time, complete, settings, data FROM `%s` WHERE idTmdb = ? ORDER BY time DESC;' % type
				querySelect4 = 'SELECT time, complete, settings, data FROM `%s` WHERE idTrakt = ? ORDER BY time DESC;' % type
				querySelect5 = 'SELECT time, complete, settings, data FROM `%s` WHERE idTvdb = ? ORDER BY time DESC;' % type
			elif typeSet:
				querySelect1 = 'SELECT time, complete, settings, data FROM `%s` WHERE idTmdb = ? ORDER BY time DESC;' % type
			elif typeShow:
				querySelect1 = 'SELECT time, complete, settings, data FROM `%s` WHERE idImdb = ? AND idTvdb = ? ORDER BY time DESC;' % type
				querySelect2 = 'SELECT time, complete, settings, data FROM `%s` WHERE idImdb = ? ORDER BY time DESC;' % type
				querySelect3 = 'SELECT time, complete, settings, data FROM `%s` WHERE idTvdb = ? ORDER BY time DESC;' % type
				querySelect4 = 'SELECT time, complete, settings, data FROM `%s` WHERE idTrakt = ? ORDER BY time DESC;' % type
				querySelect5 = 'SELECT time, complete, settings, data FROM `%s` WHERE idTvmaze = ? ORDER BY time DESC;' % type
				querySelect6 = 'SELECT time, complete, settings, data FROM `%s` WHERE idTmdb = ? ORDER BY time DESC;' % type
			elif typeSeason:
				querySelect1 = 'SELECT time, complete, settings, data FROM `%s` WHERE idImdb = ? AND idTvdb = ? ORDER BY time DESC;' % type
				querySelect2 = 'SELECT time, complete, settings, data FROM `%s` WHERE idImdb = ? ORDER BY time DESC;' % type
				querySelect3 = 'SELECT time, complete, settings, data FROM `%s` WHERE idTvdb = ? ORDER BY time DESC;' % type
				querySelect4 = 'SELECT time, complete, settings, data FROM `%s` WHERE idTrakt = ? ORDER BY time DESC;' % type
				querySelect5 = 'SELECT time, complete, settings, data FROM `%s` WHERE idTvmaze = ? ORDER BY time DESC;' % type
				querySelect6 = 'SELECT time, complete, settings, data FROM `%s` WHERE idTmdb = ? ORDER BY time DESC;' % type
			elif typeEpisode:
				querySelect1 = 'SELECT time, complete, settings, data FROM `%s` WHERE idImdb = ? AND idTvdb = ? AND season = ? ORDER BY time DESC;' % type
				querySelect2 = 'SELECT time, complete, settings, data FROM `%s` WHERE idImdb = ? AND season = ? ORDER BY time DESC;' % type
				querySelect3 = 'SELECT time, complete, settings, data FROM `%s` WHERE idTvdb = ? AND season = ? ORDER BY time DESC;' % type
				querySelect4 = 'SELECT time, complete, settings, data FROM `%s` WHERE idTrakt = ? AND season = ? ORDER BY time DESC;' % type
				querySelect5 = 'SELECT time, complete, settings, data FROM `%s` WHERE idTvmaze = ? AND season = ? ORDER BY time DESC;' % type
				querySelect6 = 'SELECT time, complete, settings, data FROM `%s` WHERE idTmdb = ? AND season = ? ORDER BY time DESC;' % type

			for i in range(len(items)):
				try:
					items[i][MetaCache.Attribute] = {MetaCache.AttributeRefresh : MetaCache.RefreshForeground, MetaCache.AttributeStatus : MetaCache.StatusInvalid, MetaCache.AttributeTime : None, MetaCache.AttributeSettings : None}
					idImdb, idTmdb, idTvdb, idTrakt, idTvmaze, idSlug = self._id(items[i])

					query = None
					parameters = None

					if typeMovie:
						if idImdb or idTmdb or idTrakt or idTvdb:
							parameters = []
							if idImdb and idTmdb:
								query = querySelect1
								parameters = [idImdb, idTmdb]
							elif idImdb:
								query = querySelect2
								parameters = [idImdb]
							elif idTmdb:
								query = querySelect3
								parameters = [idTmdb]
							elif idTrakt:
								query = querySelect4
								parameters = [idTrakt]
							elif idTvdb:
								query = querySelect5
								parameters = [idTvdb]
					elif typeSet:
						if idTmdb:
							parameters = []
							if idTmdb:
								query = querySelect1
								parameters = [idTmdb]
					else:
						if idImdb or idTvdb or idTrakt or idTvmaze or idTmdb:
							parameters = []
							if idImdb and idTvdb:
								query = querySelect1
								parameters = [idImdb, idTvdb]
							elif idImdb:
								query = querySelect2
								parameters = [idImdb]
							elif idTvdb:
								query = querySelect3
								parameters = [idTvdb]
							elif idTrakt:
								query = querySelect4
								parameters = [idTrakt]
							elif idTvmaze:
								query = querySelect5
								parameters = [idTvmaze]
							elif idTmdb:
								query = querySelect6
								parameters = [idTmdb]
							if typeEpisode:
								season = self._season(items[i])
								parameters.append(season)

					if not parameters is None:
						datas = self._select(query = query, parameters = parameters)

						# Check the external preprocessed database.
						if not datas:
							external = self._external()
							if external:
								datas = external._select(query = query.replace('time, complete, settings,', '').replace(' ORDER BY time DESC', ''), parameters = parameters)
								if datas:
									for j in range(len(datas)):
										datas[j] = [timeCurrent, True, None, datas[j][0]]

						if datas:
							selection = None

							# First try to pick the one with the same settings.
							for data in datas:
								if data[2] == settings:
									selection = data
									break

							# Otherwise pick the one with different settings.
							# Note that query returns the values in order of time, so picking the first is picking the newest.
							if not selection: selection = datas[0]
							time = selection[0]

							# Data comes from the external preprocessed database.
							# Always force a refresh, since external data might be outdated or not according to the users settings.
							if selection[2] is None:
								refresh = MetaCache.RefreshBackground
								status = MetaCache.StatusExternal

							# Data is available, but the data is incomplete.
							# Refresh in the background.
							# This shouldn't create too much extra network requests, since the partial data that was successfully retrieved, should still be available from the normal cache.
							elif not selection[1]:
								refresh = MetaCache.RefreshBackground
								status = MetaCache.StatusIncomplete

							# Always refresh obsolete data, even when they are from differnt settings.
							elif (timeCurrent - time) > timeObsolete:
								refresh = MetaCache.RefreshForeground
								status = MetaCache.StatusObsolete

							# Data available, but with different settings.
							# Refresh in the background and return the old data.
							elif not selection[2] == settings:
								refresh = MetaCache.RefreshBackground
								status = MetaCache.StatusSettings

							elif (timeCurrent - time) > timeOutdated:
								refresh = MetaCache.RefreshBackground
								status = MetaCache.StatusOutdated

							else:
								refresh = MetaCache.RefreshNone
								status = MetaCache.StatusCurrent

							items[i][MetaCache.Attribute][MetaCache.AttributeRefresh] = refresh
							items[i][MetaCache.Attribute][MetaCache.AttributeStatus] = status
							items[i][MetaCache.Attribute][MetaCache.AttributeTime] = time
							items[i][MetaCache.Attribute][MetaCache.AttributeSettings] = selection[2]

							items[i].update(Converter.jsonFrom(selection[3]))
				except: Logger.error()
		except: Logger.error()
		return items

	##############################################################################
	# DELETE
	##############################################################################

	def delete(self, type, setting):
		query = 'DELETE FROM `%s` WHERE setting = ?;' % type
		return self._delete(query = query, parameters = [setting])

	##############################################################################
	# IMPORT
	##############################################################################

	def importData(self, path, type = None):
		database = Database(path = path)

		if type is None: type = MetaCache.Types
		elif not Tools.isArray(type): type = [type]

		for i in type:
			episode = i == MetaCache.TypeEpisode
			values = database._select(query = 'SELECT time, complete, settings, idImdb, idTmdb, idTvdb, idTrakt, idTvmaze, idSlug%s, data FROM `%s`;' % (', season' if episode else '', i))
			for value in values:
				query = 'INSERT INTO `%s` (time, complete, settings, idImdb, idTmdb, idTvdb, idTrakt, idTvmaze, idSlug%s, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?%s, ?);' % (i, ', season' if episode else '', ', ?' if episode else '')
				self._insert(query = query, commit = False, parameters = value)

		self._commit()
		self._compress()
