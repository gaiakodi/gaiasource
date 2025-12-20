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
from lib.modules.tools import Media, Converter, Tools, Time
from lib.modules.stream import Stream

class History(Database):

	Name = Database.NameHistory

	TableHistory = Database.NameHistory
	TableStreams = Database.NameStreams

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		Database.__init__(self, History.Name)

	def _initialize(self):
		self._create('''
			CREATE TABLE IF NOT EXISTS %s
			(
				idGaia TEXT,
				idImdb TEXT,
				idTmdb TEXT,
				idTvdb TEXT,
				idTrakt TEXT,
				idSet TEXT,

				numberSeason INTEGER,
				numberEpisode INTEGER,

				timeAdded INTEGER,
				timeUpdated INTEGER,

				media TEXT,
				niche TEXT,
				count INTEGER,

				PRIMARY KEY(idGaia, idImdb, idTmdb, idTvdb, idTrakt, idSet, numberSeason, numberEpisode)
			);
			''' % History.TableHistory)

		# NB: Do not use the IDs as primary key, since they can be different for movie sets (will have the same idSet, but different idImdb, etc).
		self._create('''
			CREATE TABLE IF NOT EXISTS %s
			(
				idGaia TEXT,
				idImdb TEXT,
				idTmdb TEXT,
				idTvdb TEXT,
				idTrakt TEXT,
				idSet TEXT,

				numberSeason INTEGER,
				numberEpisode INTEGER,
				numberSet INTEGER,

				timeAdded INTEGER,
				timeUpdated INTEGER,

				media TEXT,
				niche TEXT,
				count INTEGER,

				data TEXT,

				PRIMARY KEY(idGaia)
			);
		''' % History.TableStreams)

		for table in [History.TableHistory, History.TableStreams]:
			self._create('CREATE INDEX IF NOT EXISTS %s_index_1 ON %s(idGaia);' % (table, table))
			self._create('CREATE INDEX IF NOT EXISTS %s_index_2 ON %s(idImdb);' % (table, table))
			self._create('CREATE INDEX IF NOT EXISTS %s_index_3 ON %s(idTmdb);' % (table, table))
			self._create('CREATE INDEX IF NOT EXISTS %s_index_4 ON %s(idTvdb);' % (table, table))
			self._create('CREATE INDEX IF NOT EXISTS %s_index_5 ON %s(idTrakt);' % (table, table))
			self._create('CREATE INDEX IF NOT EXISTS %s_index_6 ON %s(idSet);' % (table, table))
			self._create('CREATE INDEX IF NOT EXISTS %s_index_7 ON %s(numberSeason);' % (table, table))
			self._create('CREATE INDEX IF NOT EXISTS %s_index_8 ON %s(numberEpisode);' % (table, table))

	##############################################################################
	# INTERNAL
	##############################################################################

	def _id(self, stream):
		# Do not use idGaiaStream(), since that contains provider info.
		# Otherwise during binge, the season pack during the next episode scrape might come from a different provider, but we still want to use it.
		return stream.idGaiaItem() if stream else None

	def _media(self, media):
		if Media.isSerie(media): return Media.Show
		else: return media

	def _number(self, season = None, episode = None, set = None, stream = None, default = None):
		if stream:
			pack = stream.filePack()

			if pack == Stream.FilePackShow:
				season = default
				episode = default
			elif pack == Stream.FilePackSeason:
				episode = default
			elif pack == Stream.FilePackEpisode:
				episode = default

			if pack == Stream.FilePackCollection:
				set = stream.numberCollection()
				set = max(set) if set else default
			else:
				set = default
		return season, episode, set

	def _extract(self, media, niche = None, imdb = None, tmdb = None, tvdb = None, trakt = None, set = None, season = None, episode = None, metadata = None):
		media = self._media(media = media)
		if metadata:
			if niche is None: niche = metadata.get('niche')
			if imdb is None: imdb = metadata.get('imdb')
			if tmdb is None: tmdb = metadata.get('tmdb')
			if tvdb is None: tvdb = metadata.get('tvdb')
			if trakt is None: trakt = metadata.get('trakt')
			if set is None:
				try:
					set = metadata['collection']['id'] # Old metadata stored the TMDb ID in "id".
					set = set['tmdb'] # New metadata stores the IDs as a dictionary.
				except: pass
			if season is None: season = metadata.get('season')
			if episode is None: episode = metadata.get('episode')
		return media, niche, imdb, tmdb, tvdb, trakt, set, season, episode

	def _query(self, media = None, niche = None, gaia = None, imdb = None, tmdb = None, tvdb = None, trakt = None, set = None, season = None, episode = None, pack = False, prefix = None):
		query = []
		prefix = ('%s.' % prefix) if prefix else ''

		query.append('%smedia = "%s"' % (prefix, Media.Movie if media == Media.Set else media))

		if niche:
			niche = Media.stringFrom(niche)
			subquery = ['%sniche LIKE "%%%s%%"' % (prefix, i) for i in niche]
			query.append('(%s)' % (' AND '.join(subquery)))

		if media == Media.Set:
			query.append('NOT(%sidSet IS NULL OR %sidSet = "")' % (prefix, prefix))
		else:
			id = []
			if imdb: id.append('%sidImdb = "%s"' % (prefix, str(imdb)))
			if tmdb: id.append('%sidTmdb = "%s"' % (prefix, str(tmdb)))
			if tvdb: id.append('%sidTvdb = "%s"' % (prefix, str(tvdb)))
			if trakt: id.append('%sidTrakt = "%s"' % (prefix, str(trakt)))
			if set and pack: id.append('%sidSet = "%s"' % (prefix, str(set)))
			if id: query.append('(%s)' % ' OR '.join(id))

			if gaia is False: query.append('(%sidGaia IS NULL OR %sidGaia = "")' % (prefix, prefix))
			elif gaia: query.append('%sidGaia = "%s"' % (prefix, str(gaia))) # Should be "AND".

			if set is False: query.append('(%sidSet IS NULL OR %sidSet = "")' % (prefix, prefix))
			elif set and not pack: query.append('%sidSet = "%s"' % (prefix, str(set)))

			if Media.isSerie(media):
				number = []
				if pack:
					if not season is None and not season == '': number.append('%snumberSeason = %s' % (prefix, int(season)))
					if not episode is None and not episode == '': number.append('%snumberEpisode = %s' % (prefix, int(episode)))
					number = ['(%s)' % ' AND '.join(number)]
					if not season is None and not season == '': number.append('(%snumberSeason = %s AND (%snumberEpisode IS NULL OR %snumberEpisode = ""))' % (prefix, int(season), prefix, prefix))
					number.append('(%snumberSeason IS NULL OR %snumberSeason = "")' % (prefix, prefix))
					query.append('(%s)' % ' OR '.join(number))
				else:
					if season is False: number.append('(%snumberSeason IS NULL OR %snumberSeason = "")' % (prefix, prefix))
					elif not season is None and not season == '': number.append('%snumberSeason = %s' % (prefix, int(season)))
					if episode is False: number.append('(%snumberEpisode IS NULL OR %snumberEpisode = "")' % (prefix, prefix))
					elif not episode is None and not episode == '': number.append('%snumberEpisode = %s' % (prefix, int(episode)))
					if number: query.append('(%s)' % ' AND '.join(number))

		if query: return ' WHERE ' + (' AND '.join(query))
		else: return ''

	def _dataTo(self, data):
		if data is None: return None
		return self._compress(Converter.jsonTo(data))

	def _dataFrom(self, data):
		if data is None: return None
		return Converter.jsonFrom(self._decompress(data))

	##############################################################################
	# ADD
	##############################################################################

	def add(self, media, niche = None, imdb = None, tmdb = None, tvdb = None, trakt = None, set = None, season = None, episode = None, metadata = None, stream = None):
		# NB: "INSERT OR IGNORE" only ignores duplicate entries if the primary key does not contain NULL.
		# SQLite sees two NULLs as different values.
		# This means that "INSERT OR IGNORE" will insert duplicate rows if any of its primary key is NULL, which is always the case since either idTmdb or idTvdb will be NULL.
		# Instead of inserting NULL, insert an empty value to insure that the combined primary key is always unique.
		# https://stackoverflow.com/questions/43827629/why-does-sqlite-insert-duplicate-composite-primary-keys

		time = Time.timestamp()
		media, niche, imdb, tmdb, tvdb, trakt, set, season, episode = self._extract(media = media, niche = niche, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, set = set, season = season, episode = episode, metadata = metadata)
		if niche is None: niche = ''
		else: niche = Media.stringTo(niche)
		if imdb is None: imdb = ''
		if tmdb is None: tmdb = ''
		if tvdb is None: tvdb = ''
		if trakt is None: trakt = ''
		if set is None: set = ''
		if season is None: season = ''
		if episode is None: episode = ''
		if set is None: set = ''

		if stream:
			gaia = self._id(stream = stream)
			data = self._dataTo(data = stream)
		else:
			gaia = ''
			data = None

		self._insert('''
			INSERT OR IGNORE INTO %s (idGaia, idImdb, idTmdb, idTvdb, idTrakt, idSet, numberSeason, numberEpisode, timeAdded, media, niche, count)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
		''' % History.TableHistory, [gaia, imdb, tmdb, tvdb, trakt, set, season, episode, time, media, niche, 0])

		if stream:
			seasonNew, episodeNew, setNew = self._number(season = season, episode = episode, set = set, stream = stream, default = '')
			self._insert('''
				INSERT OR IGNORE INTO %s (idGaia, idImdb, idTmdb, idTvdb, idTrakt, idSet, numberSeason, numberEpisode, numberSet, timeAdded, media, niche, count, data)
				VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
			''' % History.TableStreams, [gaia, imdb, tmdb, tvdb, trakt, set if setNew else '', seasonNew, episodeNew, setNew, time, media, niche, 0, data])

		self.update(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, set = set, season = season, episode = episode, metadata = metadata, stream = stream, time = time)

	def addMovie(self, niche = None, imdb = None, tmdb = None, tvdb = None, trakt = None, set = None, metadata = None, stream = None):
		self.add(media = Media.Movie, niche = niche, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, set = set, metadata = metadata, stream = stream)

	def addShow(self, niche = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, metadata = None, stream = None):
		self.add(media = Media.Show, niche = niche, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, metadata = metadata, stream = stream)

	##############################################################################
	# UPDATE
	##############################################################################

	def update(self, media, imdb = None, tmdb = None, tvdb = None, trakt = None, set = None, season = None, episode = None, metadata = None, stream = None, time = None):
		if not time: time = Time.timestamp()
		media, niche, imdb, tmdb, tvdb, trakt, set, season, episode = self._extract(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, set = set, season = season, episode = episode, metadata = metadata)

		gaia = self._id(stream = stream)

		query = self._query(media = media, gaia = gaia, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, set = set, season = season, episode = episode)
		self._update('''
			UPDATE %s SET
				timeUpdated = ?,
				count = (count + 1)
			%s;
		''' % (History.TableHistory, query), [time])

		if stream:
			query = self._query(media = media, gaia = gaia)
			self._update('''
				UPDATE %s SET
					timeUpdated = ?,
					count = (count + 1)
				%s;
			''' % (History.TableStreams, query), [time])

	def updateMovie(self, imdb = None, tmdb = None, tvdb = None, trakt = None, set = None, metadata = None, stream = None, time = None):
		return self.update(media = Media.Movie, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, set = set, metadata = metadata, stream = stream, time = time)

	def updateShow(self, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, metadata = None, stream = None, time = None):
		return self.update(media = Media.Show, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, metadata = metadata, stream = stream, time = time)

	##############################################################################
	# RETRIEVE
	##############################################################################

	# load: retrieve the metadata. Either True/False, or Media. Eg: load=Media.Show will load all episodes as season metadata.
	def retrieve(self, media = None, niche = None, imdb = None, tmdb = None, tvdb = None, trakt = None, set = None, season = None, episode = None, metadata = None, limit = None, page = None, unique = None, pack = False, stream = False, load = False):
		result = []
		media, niche, imdb, tmdb, tvdb, trakt, set, season, episode = self._extract(media = media, niche = niche, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, set = set, season = season, episode = episode, metadata = metadata)

		if limit is True: limit = 1
		elif limit is None: limit = 100 # Otherwise too many items are retrieved and decompressed.

		if page: page = ' OFFSET %d' % (limit * (page - 1))
		else: page = ''

		if stream:
			extra1 = ', b.timeUpdated, b.count, b.data'
			extra2 = 'INNER JOIN %s AS b ON a.idGaia = b.idGaia' % History.TableStreams
		else:
			extra1 = ''
			extra2 = ''
			if unique is None: unique = True

		if unique:
			extra3 = 'AND (a.idImdb, a.idTmdb, a.idTvdb, a.idTrakt, a.idSet, a.numberSeason, a.numberEpisode, a.timeUpdated) IN (SELECT c.idImdb, c.idTmdb, c.idTvdb, c.idTrakt, c.idSet, c.numberSeason, c.numberEpisode, MAX(c.timeUpdated) FROM %s AS c GROUP BY c.idImdb, c.idTmdb, c.idTvdb, c.idTrakt, c.idSet, c.numberSeason, c.numberEpisode)' % History.TableHistory
		else:
			extra3 = ''

		query = self._query(prefix = 'a', media = media, niche = niche, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, set = set, season = season, episode = episode, pack = pack)
		items = self._select('''
			SELECT
				a.idGaia,
				a.idImdb,
				a.idTmdb,
				a.idTvdb,
				a.idTrakt,
				a.idSet,

				a.numberSeason,
				a.numberEpisode,

				a.timeAdded,
				a.timeUpdated,

				a.media,
				a.count
				%s
			FROM %s AS a
			%s %s %s
			ORDER BY a.timeUpdated DESC, a.count DESC
			LIMIT %d%s;
		''' % (extra1, History.TableHistory, extra2, query, extra3, limit, page))

		if items:
			for i in range(len(items)):
				item = items[i]
				entry = {
					'media' : item[10],
					'count' : item[11],
					'id' : {
						'gaia' : item[0] or None,
						'imdb' : item[1] or None,
						'tmdb' : item[2] or None,
						'tvdb' : item[3] or None,
						'trakt' : item[4] or None,
						'set' : item[5] or None,
					},
					'time' : {
						'added' : item[8],
						'updated' : item[9],
					},
				}
				if Media.isSerie(item[10]):
					entry['number'] = {
						'season' : item[6] or None,
						'episode' : item[7] or None,
					}

				if stream:
					entry['count'] = {'media' : item[11], 'stream' : item[13]}
					entry['time']['stream'] = item[12]
					entry['stream'] = self._dataFrom(item[14] or None)
				items[i] = entry

			if load:
				if Tools.isString(load): items = self.load(items = items, media = load, unique = unique, metadata = False)
				else: items = self.load(items = items, unique = unique, metadata = True)
			result = items

		if limit == 1: return result[0] if result else None
		else: return result

	def retrieveMovie(self, niche = None, imdb = None, tmdb = None, tvdb = None, trakt = None, set = None, metadata = None, limit = None, unique = None, pack = False, stream = False, load = False):
		return self.retrieve(media = Media.Movie, niche = niche, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, set = set, metadata = metadata, limit = limit, unique = unique, pack = pack, stream = stream, load = load)

	def retrieveShow(self, niche = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, metadata = None, limit = None, unique = None, pack = False, stream = False, load = False):
		return self.retrieve(media = Media.Show, niche = niche, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, metadata = metadata, limit = limit, unique = unique, pack = pack, stream = stream, load = load)

	##############################################################################
	# LOAD
	##############################################################################

	def load(self, items, media = None, unique = None, metadata = None):
		lookup = []
		lookupSeason = []
		lookupEpisode = []

		for item in items:
			item['metadata'] = {
				'media' : media or item['media'],

				'imdb' : item['id']['imdb'],
				'tmdb' : item['id']['tmdb'],
				'tvdb' : item['id']['tvdb'],
				'trakt' : item['id']['trakt'],
			}
			if Media.isSerie(item['media']):
				if media == Media.Show:
					lookup.append(item['metadata'])
				elif media == Media.Season:
					item['metadata']['season'] = item['number']['season']
					lookupSeason.append(item['metadata'])
				else:
					item['metadata']['season'] = item['number']['season']
					item['metadata']['episode'] = item['number']['episode']
					lookupEpisode.append(item['metadata'])
			elif media == Media.Set:
				try:
					item['metadata']['tmdb'] = item['id']['set']
					lookup.append(item['metadata'])
				except: pass
			else:
				lookup.append(item['metadata'])

		if unique:
			from lib.meta.tools import MetaTools
			items = MetaTools.instance().filterDuplicate(items = items, id = True, title = False, number = True, key = 'metadata')

		if metadata:
			from lib.meta.manager import MetaManager
			manager = MetaManager.instance()

			if lookup:
				manager.metadata(items = lookup, pack = False)

			if lookupSeason:
				lookupSeason = manager.metadata(items = lookupSeason, pack = False)
				for item in lookupSeason:
					if 'seasons' in item:
						numberSeason = item['season']
						for season in item['seasons']:
							if season['season'] == numberSeason:
								item.update(season)
								del item['seasons']
								break

			if lookupEpisode:
				lookupEpisode = manager.metadata(items = lookupEpisode, pack = False)
				for item in lookupEpisode:
					if 'episodes' in item:
						numberSeason = item['season']
						numberEpisode = item['episode']
						for episode in item['episodes']:
							if episode['season'] == numberSeason and episode['episode'] == numberEpisode:
								item.update(episode)
								del item['episodes']
								break

		if Tools.isString(media): items = [item['metadata'] for item in items]
		return items

	##############################################################################
	# CLEAN
	##############################################################################

	def _clean(self, time, commit = True, compact = True):
		if time:
			id = self._selectValues('SELECT idGaia FROM `%s` WHERE timeUpdated <= ?;' % History.TableStreams, parameters = [time])
			if id: return self._cleanId(id = id, commit = commit, compact = compact)
		return False

	def _cleanTime(self, count):
		if count:
			times = []
			time = self._selectValues('SELECT timeUpdated FROM `%s` ORDER BY timeUpdated ASC LIMIT ?;' % History.TableStreams, parameters = [count])
			if time: times.extend(time)
			if times: return Tools.listSort(times)[:count][-1]
		return None

	def _cleanId(self, id, commit = True, compact = True):
		if not Tools.isArray(id): id = [id]

		parameters = []
		query = []
		for i in id:
			parameters.append(i)
			query.append('idGaia = ?')

		query = ' OR '.join(query)
		query = 'DELETE FROM `%s` WHERE %s;' % ('%s', query)

		count = self._delete(query = query % History.TableStreams, parameters = parameters, commit = False, compact = False)
		self._delete(query = query % History.TableHistory, parameters = parameters, commit = False, compact = False)
		if commit: self._commit()
		if compact: self._compact()
		return count
