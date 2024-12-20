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
from lib.modules.tools import Media, Time, Tools, Converter, Hash
from lib.modules.interface import Translation

class Search(Database):

	Name			= 'searches' # The name of the file. Update version number of the database structure changes.

	TypeTitle		= 'title'
	TypeAdvanced	= 'advanced'
	TypeSet			= 'set'
	TypeList		= 'list'
	TypePerson		= 'person'
	TypeOracle		= 'oracle'
	TypeExact		= 'exact'

	Limit			= 30
	Instance		= None

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		Database.__init__(self, Search.Name)

	def _initialize(self):
		self._create('CREATE TABLE IF NOT EXISTS `%s` (id TEXT PRIMARY KEY, type TEXT, media TEXT, niche TEXT, time INTEGER, label TEXT, query TEXT);')

	@classmethod
	def instance(self):
		if Search.Instance is None: Search.Instance = self()
		return Search.Instance

	@classmethod
	def reset(self, settings = True):
		Search.Instance = None

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def _title(self):
		return Translation.string(32010)

	@classmethod
	def _id(self, type = None, media = None, niche = None, query = None, label = None):
		data = query if query else self._label(query = query, label = label)
		if not Tools.isString(data): data = Converter.jsonTo(data)
		return Hash.hashPersistent('%s_%s_%s_%s' % (type or '', media or '', niche or '', data))

	@classmethod
	def _label(self, query = None, label = None):
		if not label:
			if query:
				for i in ['query', 'title', 'label', 'keyword', 'keywords']:
					try:
						label = query[i]
						if label: break
					except: pass
			if not label: label = '%s %s' % (self._title(), Time.format(Time.FormatDateTime))
			elif Tools.isArray(label): label = ' '.join(label)
		return label.strip()

	##############################################################################
	# INSERT
	##############################################################################

	def insert(self, type = None, media = None, niche = None, query = None, label = None):
		id = self._id(type = type, media = media, niche = niche, query = query, label = label)
		if self._select('SELECT id FROM `%s` WHERE id = ?;', [id]): return self.update(type = type, media = media, niche = niche, query = query, label = label)
		else: return self._insert('INSERT INTO `%s` (id, type, media, niche, time, label, query) VALUES (?, ?, ?, ?, ?, ?, ?);', (id, type, media or None, Media.stringTo(niche) or None, Time.timestamp(), self._label(query = query, label = label), Converter.jsonTo(query) if query else None))

	##############################################################################
	# UPDATE
	##############################################################################

	def update(self, type = None, media = None, niche = None, query = None, label = None):
		id = self._id(type = type, media = media, niche = niche, query = query, label = label)
		return self._update('UPDATE `%s` SET time = ?, label = ?, query = ? WHERE id = ?;', (Time.timestamp(), self._label(query = query, label = label), Converter.jsonTo(query) if query else None, id))

	##############################################################################
	# RETRIEVE
	##############################################################################

	def retrieve(self, type = None, media = None, niche = None, mixed = None, limit = None, page = None, offset = None):
		query = []
		parameters = []
		if type:
			query.append('type = ?')
			parameters.append(type)
		if media:
			if mixed is True or (mixed is None and (Media.isMovie(media) or Media.isShow(media) or Media.isMixed(media))):
				query.append('(media IS NULL OR media = ? OR media = ?)')
				parameters.append(media)
				parameters.append(Media.Mixed)
			else:
				query.append('media = ?')
				parameters.append(media)
		if niche:
			niche = self._niche(niche = niche)
			if niche: query.append(niche)
		if query: query = 'WHERE ' + ' AND '.join(query)

		if not limit: limit = Search.Limit
		parameters.append(limit)

		if not page is None: parameters.append(limit * (page - 1))
		elif not offset is None: parameters.append(offset)
		else: parameters.append(0)

		data = self._select('SELECT id, type, media, niche, time, label, query FROM `%s` ' + query + ' ORDER BY time DESC LIMIT ? OFFSET ?;', parameters)

		if data:
			return [{
				'id'	: i[0],
				'type'	: i[1],
				'media'	: i[2],
				'niche'	: i[3],
				'time'	: i[4],
				'label'	: i[5],
				'query'	: Converter.jsonFrom(i[6]),
			} for i in data]
		return None

	##############################################################################
	# CLEAN
	##############################################################################

	def _clean(self, time, commit = True, compact = True):
		if time: return self._delete(query = 'DELETE FROM `%s` WHERE time <= ?;', parameters = [time], commit = commit, compact = compact)
		return False

	def _cleanTime(self, count):
		if count:
			times = []
			time = self._selectValues('SELECT time FROM `%s` ORDER BY time ASC LIMIT ?;', parameters = [count])
			if time: times.extend(time)
			if times: return Tools.listSort(times)[:count][-1]
		return None
