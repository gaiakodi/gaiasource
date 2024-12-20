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
from lib.modules.concurrency import Pool, Lock
from lib.modules.tools import Media, Time, Tools, Language, Country, Converter, Logger, File, System, Settings
from lib.modules.compression import Compression
from lib.meta.tools import MetaTools

class MetaCache(Database):

	Name				= Database.NameMetadata

	Attribute			= 'cache'
	AttributeRefresh	= 'refresh'
	AttributeStatus		= 'status'
	AttributeTime		= 'time'
	AttributeSettings	= 'settings'
	AttributePart		= 'part'
	AttributeFail		= 'fail'

	TypeMovie			= Media.Movie
	TypeSet				= Media.Set
	TypeShow			= Media.Show
	TypeSeason			= Media.Season
	TypeEpisode			= Media.Episode
	TypePack			= Media.Pack
	Types				= [TypeMovie, TypeSet, TypeShow, TypeSeason, TypeEpisode, TypePack]

	RefreshNone			= None
	RefreshForeground	= 'foreground'
	RefreshBackground	= 'background'

	StatusCurrent		= 'current'		# Available in database and is still new.
	StatusOutdated		= 'outdated'	# Available in database, but is outdated and needs a background refresh.
	StatusObsolete		= 'obsolete'	# Available in database, but is outdated and needs a foreground refresh.
	StatusSettings		= 'settings'	# Available in database, but with a different settings configuration.
	StatusIncomplete	= 'incomplete'	# Available in database, but is partial data and needs a background refresh.
	StatusExternal		= 'external'	# Available in external preprocessed database, but might be outdated or not according to the user's settings and therefore needs a background refresh.
	StatusInvalid		= 'invalid'		# Not in database at all.
	StatusMemory		= 'memory'		# Available from memory from a previous call. Can be retrieved without database access, but is only available during the same Python process.
	StatusValid			= [StatusCurrent, StatusMemory, StatusOutdated, StatusObsolete]

	# When the data outdated and should be refreshed in the background while the old cached data is still returned and displayed.
	TimeOutdated		= 2678400		# 1 Month.
	TimeOutdatedMovie	= TimeOutdated
	TimeOutdatedSet		= TimeOutdated
	TimeOutdatedShow	= TimeOutdated
	TimeOutdatedSeason	= TimeOutdated
	TimeOutdatedEpisode	= TimeOutdated
	TimeOutdatedPack	= TimeOutdated

	# When the data should be forcefully refreshed even if there is old cached data, since the metadata is too outdated to still be considered valid.
	# Keep this at a very long time, since one can always show the new data by reloading the menu after it was refreshed in the background.
	TimeObsolete		= 31556952		# 1 Year.
	TimeObsoleteMovie	= TimeObsolete
	TimeObsoleteSet		= TimeObsolete
	TimeObsoleteShow	= TimeObsolete
	TimeObsoleteSeason	= TimeObsolete
	TimeObsoleteEpisode	= TimeObsolete
	TimeObsoletePack	= TimeObsolete

	# Minimum age before re-retrieving incomplete metadata
	TimeRedo			= 3600			# 10 minutes. Do not make too high, otherwise incomplete metadata is refreshed too often when reloading the same menu in a short time. Do not make too large, otherwise temporary errors (eg: Trakt API rate limit) are not redone quickly.
	TimeRedoMovie		= TimeRedo
	TimeRedoSet			= TimeRedo
	TimeRedoShow		= TimeRedo
	TimeRedoSeason		= TimeRedo
	TimeRedoEpisode		= TimeRedo
	TimeRedoPack		= TimeRedo

	# Recentley released titles should be refreshed more often, since they might have outdated metadata or ratings with a low vote count.
	# These often also lack the TMDb digital/physical release dates, which might only be added at a later stage.
	# Values are given as {age-of-release : outdate-time} pairs.
	# Eg: {259200 : 43200} = If the title was released in the past 3 days, force refresh the data in the background if its last metadata update was more than 12 hours ago.
	# Be conservative as we do not want to update the metadata too often.
	TimeRelease			= {
							None		: 7200,		# Unreleased (release date in the future) : 2 hours.
							-63113904	: 259200,	# Missing data (release date far into the past, but missing digital/physical release date) : 3 days.
							86400		: 10800,	# 1 day : 3 hours.
							172800		: 21600,	# 2 days : 6 hours.
							345600		: 43200,	# 4 days : 12 hours.
							604800		: 86400,	# 7 days : 1 day.
							1209600		: 172800,	# 14 days : 2 days.
							1814400		: 259200,	# 21 days : 3 days.
						}
	TimeReleaseMovie	= TimeRelease
	TimeReleaseSet		= TimeRelease
	TimeReleaseShow		= TimeRelease
	TimeReleaseSeason	= TimeRelease
	TimeReleaseEpisode	= TimeRelease
	TimeReleasePack		= TimeRelease

	# Compress the external database using LZMA.
	# It has the best compression ratio so that more metadata can be stored in the addon.
	# LZMA might be slower at decompression than ZLIB, but this will only be done once. After that the metadata will be in the local cache.
	# LZMA should be part of the standard library from Python 3.3, so we are pretty sure it should be available.
	# If not, then the external metadata can simply not be used. Would be the same problem with other compression algorithms.
	# Note that more data can be added if no compression is used and we only compress the entire database with ZIP during release.
	# This is probably because of all the image URls that have similar parts and can be compressed better if all the data is compressed as one in the ZIP, instead of every row individually.
	# When uncompressed, we can add about 15% more movies or shows, but 50% LESS packs.
	# We could just compress the pack table and leave the other tables. But this would complicate the entire process.
	# Just enable compression, even if we can add a little bit less. Plus this also saves disc space.
	ExternalCompression	= Compression.TypeLzma
	ExternalName		= 'external'

	# How often to re-retrieve incomplete metadata until giving up.
	# Do not make this number too high, otherwise if eg a server is temporarily down or IMDb does not have a rating for a title yet, it will make too many requests with the same incomplete data.
	# Once given up, the metadata can still be refreshed normally using the various times above.
	Redo				= 5

	Instance			= {}
	External			= None
	Settings			= None
	Lock				= Lock()

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, generate = False):
		if generate: Database.__init__(self, name = MetaCache.ExternalName, compression = MetaCache.ExternalCompression)
		else: Database.__init__(self, name = MetaCache.Name)
		self.mExternal = not generate
		self.mMemory = {}

	@classmethod
	def instance(self, generate = False):
		if not generate in MetaCache.Instance:
			MetaCache.Lock.acquire()
			if not generate in MetaCache.Instance: MetaCache.Instance[generate] = MetaCache(generate = generate)
			MetaCache.Lock.release()
		return MetaCache.Instance[generate]

	def _initialize(self):
		self._create('''
			CREATE TABLE IF NOT EXISTS `%s`
			(
				time INTEGER,
				settings TEXT,

				idImdb TEXT,
				idTmdb TEXT,
				idTvdb TEXT,
				idTrakt TEXT,
				idSlug TEXT,

				part TEXT,
				data TEXT,

				PRIMARY KEY(settings, idImdb, idTmdb, idTrakt)
			);
			''' % MetaCache.TypeMovie,
		)
		self._create('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idImdb);' % (MetaCache.TypeMovie, MetaCache.TypeMovie))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_2 ON `%s`(idTmdb);' % (MetaCache.TypeMovie, MetaCache.TypeMovie))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_3 ON `%s`(idTvdb);' % (MetaCache.TypeMovie, MetaCache.TypeMovie))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_4 ON `%s`(idTrakt);' % (MetaCache.TypeMovie, MetaCache.TypeMovie))

		self._create('''
			CREATE TABLE IF NOT EXISTS `%s`
			(
				time INTEGER,
				settings TEXT,

				idImdb TEXT,
				idTmdb TEXT,
				idTvdb TEXT,
				idTrakt TEXT,
				idSlug TEXT,

				part TEXT,
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
				settings TEXT,

				idImdb TEXT,
				idTmdb TEXT,
				idTvdb TEXT,
				idTrakt TEXT,
				idSlug TEXT,

				part TEXT,
				data TEXT,

				PRIMARY KEY(settings, idImdb, idTvdb, idTrakt)
			);
			''' % MetaCache.TypeShow,
		)
		self._create('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idImdb);' % (MetaCache.TypeShow, MetaCache.TypeShow))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_2 ON `%s`(idTmdb);' % (MetaCache.TypeShow, MetaCache.TypeShow))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_3 ON `%s`(idTvdb);' % (MetaCache.TypeShow, MetaCache.TypeShow))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_4 ON `%s`(idTrakt);' % (MetaCache.TypeShow, MetaCache.TypeShow))

		self._create('''
			CREATE TABLE IF NOT EXISTS `%s`
			(
				time INTEGER,
				settings TEXT,

				idImdb TEXT,
				idTmdb TEXT,
				idTvdb TEXT,
				idTrakt TEXT,
				idSlug TEXT,

				part TEXT,
				data TEXT,

				PRIMARY KEY(settings, idImdb, idTvdb, idTrakt)
			);
			''' % MetaCache.TypeSeason,
		)
		self._create('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idImdb);' % (MetaCache.TypeSeason, MetaCache.TypeSeason))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_2 ON `%s`(idTmdb);' % (MetaCache.TypeSeason, MetaCache.TypeSeason))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_3 ON `%s`(idTvdb);' % (MetaCache.TypeSeason, MetaCache.TypeSeason))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_4 ON `%s`(idTrakt);' % (MetaCache.TypeSeason, MetaCache.TypeSeason))

		self._create('''
			CREATE TABLE IF NOT EXISTS `%s`
			(
				time INTEGER,
				settings TEXT,

				idImdb TEXT,
				idTmdb TEXT,
				idTvdb TEXT,
				idTrakt TEXT,
				idSlug TEXT,

				season INTEGER,

				part TEXT,
				data TEXT,

				PRIMARY KEY(settings, idImdb, idTvdb, idTrakt, season)
			);
			''' % MetaCache.TypeEpisode,
		)
		self._create('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idImdb, season);' % (MetaCache.TypeEpisode, MetaCache.TypeEpisode))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_2 ON `%s`(idTmdb, season);' % (MetaCache.TypeEpisode, MetaCache.TypeEpisode))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_3 ON `%s`(idTvdb, season);' % (MetaCache.TypeEpisode, MetaCache.TypeEpisode))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_4 ON `%s`(idTrakt, season);' % (MetaCache.TypeEpisode, MetaCache.TypeEpisode))

		self._create('''
			CREATE TABLE IF NOT EXISTS `%s`
			(
				time INTEGER,
				settings TEXT,

				idImdb TEXT,
				idTmdb TEXT,
				idTvdb TEXT,
				idTrakt TEXT,
				idSlug TEXT,

				part TEXT,
				data TEXT,

				PRIMARY KEY(settings, idImdb, idTvdb, idTrakt)
			);
			''' % MetaCache.TypePack,
		)
		self._create('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idImdb);' % (MetaCache.TypePack, MetaCache.TypePack))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_2 ON `%s`(idTmdb);' % (MetaCache.TypePack, MetaCache.TypePack))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_3 ON `%s`(idTvdb);' % (MetaCache.TypePack, MetaCache.TypePack))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_4 ON `%s`(idTrakt);' % (MetaCache.TypePack, MetaCache.TypePack))

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		# Important for self.mMemory to be reset.
		# We do not want to carry over the memory metadata to the next process, since the metadata might be outdated.
		MetaCache.Instance = {}

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
				# This should not be needed anymore. The metadata stored in MetaCache should not contain any user-specific data anymore, such as the user's Trakt rating, unlike Gaia v6 and prior.
				# Only do this for Fanart, since Fanart returns more and more-recent images if a user API key is provided, compared to making "anonymous" calls without a user key. Molre info in account.py.
				#from lib.modules.account import Imdb, Tmdb, Tvdb, Trakt, Fanart
				#values.extend([Imdb.instance().dataId(), Tmdb.instance().key(), Tvdb.instance().pin(), Trakt.instance().dataUsername(), Fanart.instance().dataKey()])
				from lib.modules.account import Fanart
				values.extend([Fanart.instance().dataKey()])

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
		typePack = False
		if type == MetaCache.TypeMovie: typeMovie = True
		elif type == MetaCache.TypeSet: typeSet = True
		elif type == MetaCache.TypeShow: typeShow = True
		elif type == MetaCache.TypeSeason: typeSeason = True
		elif type == MetaCache.TypeEpisode: typeEpisode = True
		elif type == MetaCache.TypePack: typePack = True
		return typeMovie, typeSet, typeShow, typeSeason, typeEpisode, typePack

	@classmethod
	def _timeOutdated(self, type):
		if type == MetaCache.TypeMovie: return MetaCache.TimeOutdatedMovie
		elif type == MetaCache.TypeSet: return MetaCache.TimeOutdatedSet
		elif type == MetaCache.TypeShow: return MetaCache.TimeOutdatedShow
		elif type == MetaCache.TypeSeason: return MetaCache.TimeOutdatedSeason
		elif type == MetaCache.TypeEpisode: return MetaCache.TimeOutdatedEpisode
		elif type == MetaCache.TypePack: return MetaCache.TimeOutdatedPack

	@classmethod
	def _timeObsolete(self, type):
		if type == MetaCache.TypeMovie: return MetaCache.TimeObsoleteMovie
		elif type == MetaCache.TypeSet: return MetaCache.TimeObsoleteSet
		elif type == MetaCache.TypeShow: return MetaCache.TimeObsoleteShow
		elif type == MetaCache.TypeSeason: return MetaCache.TimeObsoleteSeason
		elif type == MetaCache.TypeEpisode: return MetaCache.TimeObsoleteEpisode
		elif type == MetaCache.TypePack: return MetaCache.TimeObsoletePack

	@classmethod
	def _timeRedo(self, type):
		if type == MetaCache.TypeMovie: return MetaCache.TimeRedoMovie
		elif type == MetaCache.TypeSet: return MetaCache.TimeRedoSet
		elif type == MetaCache.TypeShow: return MetaCache.TimeRedoShow
		elif type == MetaCache.TypeSeason: return MetaCache.TimeRedoSeason
		elif type == MetaCache.TypeEpisode: return MetaCache.TimeRedoEpisode
		elif type == MetaCache.TypePack: return MetaCache.TimeRedoPack

	@classmethod
	def _timeRelease(self, type, release = None, metadata = None, time = None):
		if not release and metadata: release = self._timeExtract(type = type, metadata = metadata, time = time)
		if release:
			if type == MetaCache.TypeMovie: values = MetaCache.TimeReleaseMovie
			elif type == MetaCache.TypeSet: values = MetaCache.TimeReleaseSet
			elif type == MetaCache.TypeShow: values = MetaCache.TimeReleaseShow
			elif type == MetaCache.TypeSeason: values = MetaCache.TimeReleaseSeason
			elif type == MetaCache.TypeEpisode: values = MetaCache.TimeReleaseEpisode
			elif type == MetaCache.TypePack: values = MetaCache.TimeReleasePack
			else: values = None
			if values:
				if Tools.isString(release): release = Time.timestamp(fixedTime = release, format = Time.FormatDate)
				if not time: time = Time.timestamp()
				if release:
					for timeReleased, timeOutdated in values.items():
						if timeReleased is None: # Also do this for not-yet released episodes that have a later date than the current date.
							if release > time: return timeOutdated
						elif timeReleased < 0: # If the digital/physical release date is missing.
							if release >= (time - abs(timeReleased)):
								times = metadata.get('time')
								if times:
									for i in [MetaTools.TimeDigital, MetaTools.TimePhysical]:
										if not times.get(i): return timeOutdated
						else:
							if release >= (time - timeReleased): return timeOutdated
		return None

	@classmethod
	def _timeExtract(self, metadata, type = None, time = None):
		release = None
		try:
			if type == MetaCache.TypePack:
				# For packs, use the most recently released episode date.
				from lib.meta.pack import MetaPack
				times = MetaPack.instance(metadata).timeValuesStandard()
				if times:
					if not time: time = Time.timestamp()
					release = min(times, key = lambda x : abs(x - time))
			else:
				# Try to get physical/digital/etc release dates for movies.
				# Metadata, ratings, and votes might change when a new release comes out.
				# NB: Exclude times that are irrelevant (eg "updated" might be in "times", which is when it was updated by the user on Trakt).
				try: release = max([v for k, v in metadata['time'].items() if k in MetaTools.TimesRelease and not v is None])
				except: pass

				if not release:
					try: release = metadata['premiered']
					except: pass
					if not release:
						try: release = metadata['aired']
						except: pass

						# For season/episode metadata, extract the latests release date.
						if not release:
							values = []
							for type in ['seasons', 'episodes']:
								if type in metadata and Tools.isArray(metadata[type]):
									for i in metadata[type]:
										value = None
										try: value = i['premiered']
										except: pass
										if not value:
											try: value = i['aired']
											except: pass
										if value: values.append(value)
									break
							values = {Time.integer(i) : i for i in values}
							if values: release = values[max(values, key = values.get)]
		except: Logger.error()
		return release

	@classmethod
	def _id(self, item):
		idImdb = None
		idTmdb = None
		idTvdb = None
		idTrakt = None
		idSlug = None

		id = item.get('id')
		if id:
			idImdb = id.get('imdb')
			idTmdb = id.get('tmdb')
			idTvdb = id.get('tvdb')
			idTrakt = id.get('trakt')
			idSlug = id.get('slug')

		if not idImdb: idImdb = item.get('imdb')
		if not idTmdb: idTmdb = item.get('tmdb')
		if not idTvdb: idTvdb = item.get('tvdb')
		if not idTrakt: idTrakt = item.get('trakt')
		if not idSlug: idSlug = item.get('slug')

		return idImdb, idTmdb, idTvdb, idTrakt, idSlug

	@classmethod
	def _season(self, item):
		try:
			season = item['season']
			if not season is None: season = int(season)
		except: season = None
		return season

	##############################################################################
	# EXTERNAL
	##############################################################################

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

	@classmethod
	def externalGenerate(self, input = None, output = None):
		if input is None:
			input = MetaCache.instance(generate = True)._mPath
		if output is None:
			output = System.temporary(directory = 'metadata', gaia = True, make = True, clear = True)
			output = File.joinPath(output, 'metadata.db')
		File.copy(pathFrom = input, pathTo = output, overwrite = True)

		queries = []
		database = Database(path = output)
		for i in database._tables():
			primary = ''
			extra1 = ''
			extra2 = ''
			extra3 = ''
			if i == MetaCache.TypeMovie:
				primary = 'idImdb, idTmdb, idTrakt'
			elif i == MetaCache.TypeSet:
				primary = 'idTmdb'
			elif i == MetaCache.TypeShow or i == MetaCache.TypeSeason:
				primary = 'idImdb, idTvdb, idTrakt'
			elif i == MetaCache.TypeEpisode:
				extra1 = 'season INTEGER, '
				extra2 = 'season, '
				extra3 = ', season'
				primary = 'idImdb, idTvdb, idTrakt, season'
			elif i == MetaCache.TypePack:
				primary = 'idImdb, idTvdb, idTrakt'

			# Old SQLite does not have "DROP COLUMN", copy the table instead.
			#queries.append('DELETE FROM `%s` WHERE complete != 1;' % i) # Many specials have incomplete metadata. Keep them. We now copy this value below.
			queries.append('CREATE TABLE `temp_%s` (idImdb TEXT, idTmdb TEXT, idTvdb TEXT, idTrakt TEXT, %sdata TEXT, PRIMARY KEY(%s));' % (i, extra1, primary))

			queries.append('INSERT INTO `temp_%s` SELECT idImdb, idTmdb, idTvdb, idTrakt, %sdata FROM `%s`;' % (i, extra2, i))
			queries.append('DROP TABLE `%s`;' % i)
			queries.append('ALTER TABLE `temp_%s` RENAME TO `%s`;' % (i, i))

			# Do not add too many extra indices, since it can substantially increase the database size.
			if i == MetaCache.TypeSet:
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idTmdb);' % (i, i))
			elif i == MetaCache.TypeEpisode:
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idImdb, season);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_2 ON `%s`(idTmdb, season);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_3 ON `%s`(idTvdb, season);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_4 ON `%s`(idTrakt, season);' % (i, i))
			else:
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idImdb);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_2 ON `%s`(idTmdb);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_3 ON `%s`(idTvdb);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_4 ON `%s`(idTrakt);' % (i, i))

		for query in queries: database._execute(query = query, commit = True, compact = False)
		database._commit()
		database._compact()

		return output

	##############################################################################
	# MEMORY
	##############################################################################

	# These functions store previously retrieved/select() and updated/insert() metadata in memory until the end of the Python process execution.
	# This can substantially improve overall performance when the same metadata is retrieved multiple times during the same execution.
	# This is especially important for pack metadata retrieval, which can easily take 100-200+ ms for most packs, but even longer for larger packs.
	# In MetaManager.metadataEpisode(), the pack is retrieved multiple times through _metadataPackLookup() and _metadataPackAggregate(), and we do not always want to use disk I/O, decoding the JSON, and initializing MetaPack every time we access it.

	def _memory(self, type, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, season = None):
		for id in self._memoryId(type = type, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, season = season):
			item = self.mMemory.get(id)
			if item:
				# Copy here again, since we do not want to send out the dictionary that we might later access/copy again.
				# This should be fast and not cause too much delay.
				item = self._memoryCopy(type = type, item = item)
				return item
		return None

	def _memoryUpdate(self, item, type, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, season = None):
		item = self._memoryCopy(type = type, item = item)
		for id in self._memoryId(type = type, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, season = season):
			self.mMemory[id] = item

	def _memoryId(self, type, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, season = None):
		ids = []

		base = str(type) + '_%s_%s'
		if not season is None: base += '_' + str(season)

		if idTrakt: ids.append(base % (MetaTools.ProviderTrakt, idTrakt))
		if idImdb: ids.append(base % (MetaTools.ProviderImdb, idImdb))
		if idTmdb: ids.append(base % (MetaTools.ProviderTmdb, idTmdb))
		if idTvdb: ids.append(base % (MetaTools.ProviderTvdb, idTvdb))

		return ids

	def _memoryCopy(self, type, item):
		# NB: If item is None, it probably means the compression algorithm used for the local metadata.db is different to the one currently used for decompression.
		# Eg: the user imported and old database, but the new system uses different compression algorithm, or has differnt benchmarks for the algorithms.
		# This should not happen.
		#if not item is None:
		if True:

			# Important to copy here when called from select(), since the returned dict can be updated.

			# NB: This DEEP copy can be very slow, and ends up defeating the purpose of "faster" memory access.
			# This can take 100-200 ms for an episode list with 20+ episodes, and even longer if there are 100s of episodes in the season.
			# When loading the episode Progress menu, mutiple episode lists have to be loaded for each entry, and if many have 20+ episodes, it can cause a multiple-second delay in the menu loading.
			# Not sure if a deep copy is really necessary for some code?
			# Instead, do a semi-deep-shallow copy. Aka only copy the outer dict structure, the seasons/episodes outer list structure and the outer dict for each of the season/episode in the list.
			# Also deep-copy the "number" dict which is edited later on, and if not copied, causes issues when the same episode is retrieved during the same execution with different number types, eg: Core._scrapeNumber().
			# The semi-deep-shallow copy only takes 2-5ms, even for 20+ episodes.
			# NB: We might need to add additional nested attributes to deep-copy if we at some point discover bugs with edited dicts.
			#item = Tools.copy(item)

			# Do not do this for packs, since they should not change between calls, and can take very long to copy (eg: One Piece 150-250ms).
			if not type == MetaCache.TypePack:
				item = Tools.copy(item, deep = False)

				if type == MetaCache.TypeSeason or type == MetaCache.TypeEpisode:
					lookup = 'seasons' if type == MetaCache.TypeSeason else 'episodes'
					values = item.get(lookup)
					if values:
						temp = []
						for i in values:
							value = Tools.copy(i, deep = False)

							# Important to copy, since we update the dictionary, and its internal lists.
							# Otherwise the same episode lookup, but with different number types might cause inconsistencies with the nested "number" dictionary.
							number = i.get('number')
							if number: value['number'] = Tools.copy(number, deep = True) # Deep copy.

							temp.append(value)
						item[lookup] = temp

		return item

	##############################################################################
	# QUERY
	##############################################################################

	def _query(self, type, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, season = None, best = False, full = False):
		values = []
		parameters = []

		values1 = {}
		values2 = {}
		if type == MetaCache.TypeMovie:
			values1 = {'idImdb' : idImdb, 'idTmdb' : idTmdb, 'idTrakt' : idTrakt}
			values2 = {'idTvdb' : idTvdb}
		elif type == MetaCache.TypeSet:
			values1 = {'idTmdb' : idTmdb}
		elif type == MetaCache.TypeShow or type == MetaCache.TypeSeason or type == MetaCache.TypeEpisode:
			values1 = {'idImdb' : idImdb, 'idTvdb' : idTvdb, 'idTrakt' : idTrakt}
			values2 = {'idTmdb' : idTmdb}
		elif type == MetaCache.TypePack:
			values1 = {'idImdb' : idImdb, 'idTvdb' : idTvdb, 'idTrakt' : idTrakt}
			values2 = {'idTmdb' : idTmdb}

		for k, v in values1.items():
			if v:
				values.append(k)
				parameters.append(v)
		if not values or full:
			for k, v in values2.items():
				if v:
					values.append(k)
					parameters.append(v)

		if values:
			if best: base = Tools.copy(parameters)

			# Check the comment below on why to use AND for delete queries.
			operator = ' AND ' if full else ' OR '

			query = '(%s)' % operator.join(['%s = ?' % i for i in values])
			if not season is None:
				query = '(%s AND season = ?)' % query
				parameters.append(season)

			# Sometimes there is a mismatch between IDs on the different platforms.
			# In these cases, Trakt often adds 2 (technically identical) shows to their database, one pointing to the TMDb show, and one to the TVDb show.
			# 	Eg: The Vikings (2015)
			#		IMDb: -				TMDb: 204558	TVDb: 313970	Trakt: 108936 (the-vikings-2015)
			#		IMDb: tt19401686	TMDb: 204558	TVDb: -			Trakt: 248534 (the-vikings-2015-248534)
			# This has also been observed with other shows, which have been "fixed" on Trakt by now.
			#	Eg:
			#		{"trakt":100814,"slug":"tvf-pitchers-2015","tvdb":298807,"imdb":"tt4742876","tmdb":63180}
			#		{"trakt":185757,"slug":"tvf-pitchers-2015-185757","tvdb":298868,"imdb":"tt4742876","tmdb":63180}
			# When searching for "Vikings" under the shows search menu, and we then reopen the cached menu again and again, all titles are cached, except this one, which is always re-retrieved in the foreground, making the menu take a short while to load.
			# The issue is the DELETE statement which deletes if ANY of the IDs match (in this case TMDb), even if the other IDs do no match.
			# If the menu is opened once, it retrieves the 1st show. If opened again, it deletes the first show (since the TMDb matches), and then inserts the 2nd show.
			# If the menu is opened again, it deletes the 2nd show (since the TMDb matches) and inserts the 1st show. This cycle continues forever and the menu is never fully cached, since this title has to be retrieved in the foreground again and again.
			# We basically want to SELECT and DELETE based on the MOST ID matches instead of ANY matches.
			# We could have multiple queries, first trying to find a row with all IDs matching, if nothing is found try to find with one less ID, and so on. But this would require multiple queries and would slow down things.
			# Instead we count the number of ID matches using the IFF clause below and do the following:
			#	SELECT queries: match any ID, but sort based on how many IDs match, and then pick the one with most ID matches.
			#	DELETE queries: delete a row only if all IDs match. If one or more IDs do not match, do not delete, and insert the item a second time with the alternative IDs. This should not happen very often and therefore not waste too much extra disk space.
			if best:
				parameters += base
				query = (query, '(%s)' % ' + '.join(['IIF(%s = ?, 1, 0)' % i for i in values]))

			return query, parameters

		return None, None

	##############################################################################
	# DETAILS
	##############################################################################

	def details(self):
		count = {}
		for media in [Media.Movie, Media.Set, Media.Show, Media.Pack, Media.Season, Media.Episode]:
			count[media] = self._selectValue(query = 'SELECT COUNT(*) FROM `%s`' % media)
		return {
			'time'	: Time.timestamp(),
			'size'	: File.size(self._mPath), # Som etimes this returns 0 if a new database is created. Restart Kodi after having created the file to get the size.
			'count'	: count,
		}

	##############################################################################
	# INSERT
	##############################################################################

	def insert(self, type, items, time = None, wait = None):
		if not items: return None

		# Make a copy of the items.
		# Even for large lists, this should only take a few milliseconds.
		# This is needed, since we delete the "temp" attribute in _insertItems() before inserting the item into the database.
		# This "temp" attribute is still needed outside this function, and we do not want to delete it there as well, because lists/dicts are passed by reference. Deleting the attribute here, deletes it everywhere this dict reference is used.
		# Technically we could only make a shallow copy of each item individually: [Tools.copy(i, deep = False) for i in items], since we only remove an attribute on the first dict level, which only requires a shallow copy.
		# However, since the database insert below can run in a thread, other code, like from MetaTools, could manipulate the dict, which we might not want for the database insert. So rather do a deep copy.
		# Also, do the deep copy here, and not in the thread. Since we do not want other code, which might possibly edit the dict, to continue before the thread gets a chance to do the copy.
		items = Tools.copy(items, deep = True)

		if wait is None: wait = len(items) <= 1 # Do not use threads for small tasks.
		if wait: return self._insertItems(type = type, items = items, time = time)
		else: return Pool.thread(target = self._insertItems, kwargs = {'type' : type, 'items' : items, 'time' : time}, start = True)

	def _insertItems(self, type, items, memory = True, time = None): # _insert() already used in database.py.
		try:
			result = True
			settings = self.settingsId()
			typeMovie, typeSet, typeShow, typeSeason, typeEpisode, typePack = self._type(type)

			if time is None: time = Time.timestamp()

			# Sometimes the IDs are incorrect.
			# Especially Trakt sometimes returns the incorrect IMDb/TMDb/TVDb ID, specfically for less-known titles or newley/not-yet released titles.
			# First lookup with all available IDs and if not found, try to use individual IDs if order of importance.
			# Update: Some shows only appear on Trakt/TMDb, but not on IMDb/TVDb (eg: AVASTARS - Trakt:180301 - TMDb:125266).
			# Update: The cache ID lookups have been simplified. Any ID can now match.
			if typeEpisode: queryInsert = 'INSERT INTO `%s` (time, settings, idImdb, idTmdb, idTvdb, idTrakt, idSlug, season, part, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);' % type
			else: queryInsert = 'INSERT INTO `%s` (time, settings, idImdb, idTmdb, idTvdb, idTrakt, idSlug, part, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);' % type
			queryDelete = 'DELETE FROM `%s` WHERE settings = ? AND %s;' % (type, '%s')

			if not Tools.isArray(items): items = [items]
			for item in items:
				try:
					if item:
						idImdb, idTmdb, idTvdb, idTrakt, idSlug = self._id(item)

						# Too many times the requests return incomplete metadata.
						# Give up and mark the data as complete.
						# Clear the part BLOB to save some disk space.
						# The data can still be refreshed in the normal way.
						try:
							part = item[MetaCache.Attribute][MetaCache.AttributePart]
							if part and part.get(MetaCache.AttributeFail, 0) >= MetaCache.Redo: part = None
						except: part = None

						try: del item[MetaCache.Attribute]
						except: pass
						try: del item['temp']
						except: pass
						for i in ['seasons', 'episodes']:
							values = item.get(i)
							if values:
								for j in values:
									try: del j['temp']
									except: pass

						season = None
						insert = []

						if typeEpisode:
							season = self._season(item)
							insert.append(season)

						if memory: self._memoryUpdate(item = item, type = type, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, season = season)

						# Check _query() for more info on the use of "full".
						query, parameters = self._query(type = type, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, season = season, full = True)
						if query and parameters:
							self._delete(query = queryDelete % query, commit = False, parameters = [settings] + parameters)

						query, parameters = self._query(type = type, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, season = season)
						if query and parameters: # At least one of the IDs has been set.
							compressedPart = self._compress(Converter.jsonTo(part)) if part else None
							compressedData = self._compress(Converter.jsonTo(item)) if item else None
							self._insert(query = queryInsert, commit = False, parameters = [time, settings, idImdb, idTmdb, idTvdb, idTrakt, idSlug] + insert + [compressedPart, compressedData])
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

	def select(self, type, items, memory = True):
		try:
			settings = self.settingsId()
			typeMovie, typeSet, typeShow, typeSeason, typeEpisode, typePack = self._type(type)

			timeCurrent = Time.timestamp()
			timeObsolete = self._timeObsolete(type)
			timeOutdated = self._timeOutdated(type)
			timeRedo = self._timeRedo(type)

			# Sometimes the IDs are incorrect.
			# Especially Trakt sometimes returns the incorrect IMDb/TMDb/TVDb ID, specfically for less-known titles or newley/not-yet released titles.
			# First lookup with all available IDs and if not found, try to use individual IDs if order of importance.
			querySelect = 'SELECT time, settings, part, data FROM `%s` WHERE %s ORDER BY %s DESC, time DESC;' % (type, '%s', '%s')

			for i in range(len(items)):
				try:
					items[i][MetaCache.Attribute] = {MetaCache.AttributeRefresh : MetaCache.RefreshForeground, MetaCache.AttributeStatus : MetaCache.StatusInvalid, MetaCache.AttributeTime : None, MetaCache.AttributeSettings : None, MetaCache.AttributePart : None}
					idImdb, idTmdb, idTvdb, idTrakt, idSlug = self._id(items[i])

					season = self._season(items[i]) if typeEpisode else None

					if memory:
						metadata = self._memory(type = type, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, season = season)
						if metadata:
							refresh = MetaCache.RefreshNone
							status = MetaCache.StatusMemory

							items[i][MetaCache.Attribute][MetaCache.AttributeRefresh] = refresh
							items[i][MetaCache.Attribute][MetaCache.AttributeStatus] = status
							items[i][MetaCache.Attribute][MetaCache.AttributeTime] = timeCurrent

							Tools.update(items[i], metadata, none = False, lists = True, unique = True, inverse = True)
							continue
					# Check _query() for more info on the use of "best".
					query, parameters = self._query(type = type, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, season = season, best = True)

					if query and parameters:
						query = querySelect % query
						datas = self._select(query = query, parameters = parameters)

						# Check the external preprocessed database.
						external = False
						if not datas and self.mExternal:
							externaled = self._external()
							if externaled:
								datas = externaled._select(query = query.replace('time, settings, part,', '').replace(', time DESC', ''), parameters = parameters)
								if datas:
									for j in range(len(datas)):
										datas[j] = [timeCurrent, None, None, datas[j][0]]
									external = True

						if datas:
							selection = None

							# First try to pick the one with the same settings.
							for data in datas:
								if data[1] == settings:
									selection = data
									break

							# Otherwise pick the one with different settings.
							# Note that query returns the values in order of time, so picking the first is picking the newest.
							if not selection: selection = datas[0]
							time = selection[0]
							setting = selection[1]
							part = selection[2]
							timeDifference = timeCurrent - time

							metadata = Converter.jsonFrom(self._decompress(selection[3], type = MetaCache.ExternalCompression if external else None))
							if not(external and metadata is None): # Cannot decompress the external metadata, due to an unsupported compression algorithm.
								# If the release date of the title is recent, reduce the refresh time to update the metadata more often.
								# For recently released movies, the rating is often higher than it should be, since the early ratings cast by people are often higher than the average rating after a few days/weeks with more votes.
								# For newley released seasons/episodes, besides the rating, there might be other outdated metadata, like the plot, cast, episode title, or release date. For many new episodes there are no ratings within the first day or so of release.

								timeCheck = self._timeRelease(type = type, metadata = metadata, time = timeCurrent) or timeOutdated

								# Data comes from the external preprocessed database.
								# Always force a refresh, since external data might be outdated or not according to the users settings.
								if setting is None:
									refresh = MetaCache.RefreshBackground
									status = MetaCache.StatusExternal

								# Always refresh obsolete data, even when they are from differnt settings.
								elif timeDifference > timeObsolete:
									refresh = MetaCache.RefreshForeground
									status = MetaCache.StatusObsolete

								# Data available, but with different settings.
								# Refresh in the background and return the old data.
								elif not setting == settings:
									refresh = MetaCache.RefreshBackground
									status = MetaCache.StatusSettings

								# Data outdated and needs a fresh update.
								# Refresh in the background.
								elif timeDifference > timeCheck:
									refresh = MetaCache.RefreshBackground
									status = MetaCache.StatusOutdated

								# Data is available, but the data is incomplete.
								# Refresh in the background.
								# Do this AFTER checking "timeDifference > timeCheck" above, since incompelete refreshs should only be done for newer data.
								# Do this a maximum of once an hour, to avoid constant refreshes if the menu is reloaded in a short period of time.
								elif part and timeDifference > timeRedo:
									refresh = MetaCache.RefreshBackground
									status = MetaCache.StatusIncomplete

								else:
									refresh = MetaCache.RefreshNone
									status = MetaCache.StatusCurrent

								items[i][MetaCache.Attribute][MetaCache.AttributeRefresh] = refresh
								items[i][MetaCache.Attribute][MetaCache.AttributeStatus] = status
								items[i][MetaCache.Attribute][MetaCache.AttributeTime] = time
								items[i][MetaCache.Attribute][MetaCache.AttributeSettings] = setting
								if part: items[i][MetaCache.Attribute][MetaCache.AttributePart] = Converter.jsonFrom(self._decompress(part))

								if memory and not external and refresh == MetaCache.RefreshNone: self._memoryUpdate(item = metadata, type = type, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, season = season)

								# Do not just update(), otherwise some nested dictionaries will be replaced.
								# Eg: If from movies progress, items are passed, the metadata should be added into nested dictionaries.
								# Eg: {'time' : {'watched' : 123}}
								# With just update(), the entire 'time' dictionary will be replaced with the one from metadata.
								# With Tools.update(), the 'time' dictionary gets the new values from metadata, but still keeps the old 'watched' time.
								# Also important for IMDb. Searching IMDb by genre, IMDb lists and Advanced Search only returns 1-3 genres, although the searched genre might only be 4th or 5th.
								# TMDb/Trakt often also has different genres. The searched genre is therefore manually added in MetaImdb, but might not be available from detailed metadata retrieval.
								# Hence, the basic dictionary passed into this function might contain some metadata that is not available in the cache. Do not replace it, but extend the dictionary.
								#items[i].update(metadata)
								# Update: Important to use "inverse = True".
								# This will merge lists as: metadata+items[i], instead of items[i]+metadata.
								# Otherwise if a barebone item (eg: from Discover or Search) is passed in, in can already have lists with values, but those might be incomplete or less-relevant.
								# For instance, a Trakt search returns "Vikings" with network=['Amazon'], but the detailed metadata has ['History Canada', 'History', 'Amazon', 'Prime Video'].
								# Without inverse=True, the list will be merged with 'Amazon' first in the list, but it should rather be added to the end.
								# NB: if this call is changed, also change for the memory call above.
								Tools.update(items[i], metadata, none = False, lists = True, unique = True, inverse = True)
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
	# CLEAN
	##############################################################################

	def _clean(self, time, commit = True, compact = True):
		if time:
			count = 0
			query = 'DELETE FROM `%s` WHERE time <= ?;'
			for type in MetaCache.Types:
				count += self._delete(query = query % type, parameters = [time], commit = commit, compact = compact)
			return count
		return False

	def _cleanTime(self, count):
		if count:
			times = []
			query = 'SELECT time FROM `%s` ORDER BY time ASC LIMIT ?;'
			for type in MetaCache.Types:
				time = self._selectValues(query = query % type, parameters = [count])
				if time: times.extend(time)
			if times: return Tools.listSort(times)[:count][-1]
		return None

	##############################################################################
	# IMPORT
	##############################################################################

	def importData(self, path, type = None):
		database = Database(path = path)

		if type is None: type = MetaCache.Types
		elif not Tools.isArray(type): type = [type]

		for i in type:
			episode = i == MetaCache.TypeEpisode
			values = database._select(query = 'SELECT time, settings, idImdb, idTmdb, idTvdb, idTrakt, idSlug%s, part, data FROM `%s`;' % (', season' if episode else '', i))
			for value in values:
				query = 'INSERT INTO `%s` (time, settings, idImdb, idTmdb, idTvdb, idTrakt, idSlug%s, part, data) VALUES (?, ?, ?, ?, ?, ?, ?%s, ?, ?);' % (i, ', season' if episode else '', ', ?' if episode else '')
				self._insert(query = query, commit = False, parameters = value)

		self._commit()
		self._compact()
