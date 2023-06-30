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
from lib.modules.tools import Selection, Time, Tools, Converter, Media

class Search(Database):

	Name = 'searches' # The name of the file. Update version number of the database structure changes.

	TypeMovie = Media.TypeMovie
	TypeSet = Media.TypeSet
	TypeShow = Media.TypeShow
	TypeDocumentary = Media.TypeDocumentary
	TypeShort = Media.TypeShort
	TypePerson = Media.TypePerson
	TypeOracle = 'oracle'

	def __init__(self):
		Database.__init__(self, Search.Name)

	def _initialize(self):
		self._createAll('CREATE TABLE IF NOT EXISTS `%s` (terms TEXT PRIMARY KEY, time INTEGER, kids INTEGER, data TEXT);', [Search.TypeMovie, Search.TypeSet, Search.TypeShow, Search.TypeDocumentary, Search.TypeShort, Search.TypePerson, Search.TypeOracle])

	def insert(self, searchType, searchTerms, searchKids = Selection.TypeUndefined, searchData = None):
		searchTerms = searchTerms.strip()
		if searchTerms and len(searchTerms) > 0:
			existing = self._select('SELECT terms FROM `%s` WHERE terms = "%s";' % (searchType, searchTerms))
			if existing:
				self.update(searchType, searchTerms)
			else:
				self._insert('INSERT INTO `%s` (terms, time, kids, data) VALUES (?, ?, ?, ?);' % searchType, (searchTerms, Time.timestamp(), searchKids, Converter.jsonTo(searchData) if searchData else searchData))

	def insertMovie(self, searchTerms, searchKids = Selection.TypeUndefined, searchData = None):
		self.insert(Search.TypeMovie, searchTerms, searchKids, searchData)

	def insertSet(self, searchTerms, searchKids = Selection.TypeUndefined, searchData = None):
		self.insert(Search.TypeSet, searchTerms, searchKids, searchData)

	def insertShow(self, searchTerms, searchKids = Selection.TypeUndefined, searchData = None):
		self.insert(Search.TypeShow, searchTerms, searchKids, searchData)

	def insertDocumentary(self, searchTerms, searchKids = Selection.TypeUndefined, searchData = None):
		self.insert(Search.TypeDocumentary, searchTerms, searchKids, searchData)

	def insertShort(self, searchTerms, searchKids = Selection.TypeUndefined, searchData = None):
		self.insert(Search.TypeShort, searchTerms, searchKids, searchData)

	def insertPerson(self, searchTerms, searchKids = Selection.TypeUndefined, searchData = None):
		self.insert(Search.TypePerson, searchTerms, searchKids, searchData)

	def insertOracle(self, searchTerms, searchKids = Selection.TypeUndefined, searchData = None):
		self.insert(Search.TypeOracle, searchTerms, searchKids, searchData)

	def update(self, searchType, searchTerms, searchData = None):
		searchTerms = searchTerms.strip()
		if searchData: self._update('UPDATE `%s` SET time = ?, data = ? WHERE terms = ?;' % searchType, (Time.timestamp(), Converter.jsonTo(searchData), searchTerms))
		else: self._update('UPDATE `%s` SET time = %d WHERE terms = "%s";' % (searchType, Time.timestamp(), searchTerms))

	def updateMovie(self, searchTerms, searchData = None):
		self.update(Search.TypeMovie, searchTerms, searchData = searchData)

	def updateSet(self, searchTerms, searchData = None):
		self.update(Search.TypeSet, searchTerms, searchData = searchData)

	def updateShow(self, searchTerms, searchData = None):
		self.update(Search.TypeShow, searchTerms, searchData = searchData)

	def updateDocumentary(self, searchTerms, searchData = None):
		self.update(Search.TypeDocumentary, searchTerms, searchData = searchData)

	def updateShort(self, searchTerms, searchData = None):
		self.update(Search.TypeShort, searchTerms, searchData = searchData)

	def updatePerson(self, searchTerms, searchData = None):
		self.update(Search.TypePerson, searchTerms, searchData = searchData)

	def updateOracle(self, searchTerms, searchData = None):
		self.update(Search.TypeOracle, searchTerms, searchData = searchData)

	def retrieve(self, searchType, count = 30, kids = Selection.TypeUndefined):
		if kids == Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('SELECT terms, kids, data, "%s" as type FROM `%s` %s ORDER BY time DESC LIMIT %d;' % (searchType, searchType, kids, count))

	def retrieveAll(self, count = 30, kids = Selection.TypeUndefined, type = None):
		if kids == Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids

		typeFixed = None
		if type is None:
			type = [Search.TypeMovie, Search.TypeSet, Search.TypeShow, Search.TypeDocumentary, Search.TypeShort, Search.TypePerson, Search.TypeOracle]
		elif not Tools.isArray(type):
			type = [type]
			typeFixed = type
		else:
			typeFixed = type

		parameters = []
		for i in type: parameters.extend([i, i])
		parameters.extend([kids, count])

		result = self._select(('''
			SELECT terms, kids, data, type FROM
			(''' + (' UNION ALL '.join(['SELECT time, terms, kids, data, "%s" as type FROM `%s`' for i in range(len(type))])) + ''')
			%s
			ORDER BY time DESC LIMIT %d;
		''') % tuple(parameters))

		if result and typeFixed:
			temp = []
			for i in result:
				if i[3] == Search.TypeOracle:
					if Converter.jsonFrom(i[2])['media'] in typeFixed: temp.append(i)
				else:
					temp.append(i)
			result = temp

		return result

	def retrieveMovie(self, count = 30, kids = Selection.TypeUndefined):
		if kids == Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT terms, kids, data, "%s" as type FROM `%s`
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (Search.TypeMovie, Search.TypeMovie, kids, count))

	def retrieveSet(self, count = 30, kids = Selection.TypeUndefined):
		if kids == Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT terms, kids, data, "%s" as type FROM `%s`
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (Search.TypeSet, Search.TypeSet, kids, count))

	def retrieveShow(self, count = 30, kids = Selection.TypeUndefined):
		if kids == Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT terms, kids, data, "%s" as type FROM `%s`
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (Search.TypeShow, Search.TypeShow, kids, count))

	def retrieveDocumentary(self, count = 30, kids = Selection.TypeUndefined):
		if kids == Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT terms, kids, data, "%s" as type FROM `%s`
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (Search.TypeDocumentary, Search.TypeDocumentary, kids, count))

	def retrieveShort(self, count = 30, kids = Selection.TypeUndefined):
		if kids == Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT terms, kids, data, "%s" as type FROM `%s`
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (Search.TypeShort, Search.TypeShort, kids, count))

	def retrievePerson(self, count = 30, kids = Selection.TypeUndefined):
		if kids == Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT terms, kids, data, "%s" as type FROM `%s`
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (Search.TypePerson, Search.TypePerson, kids, count))

	def retrieveOracle(self, count = 30, kids = Selection.TypeUndefined, type = None):
		if kids == Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		result = self._select('''
			SELECT terms, kids, data, "%s" as type FROM `%s`
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (Search.TypeOracle, Search.TypeOracle, kids, count))

		if result and type:
			if not Tools.isArray(type): type = [type]
			result = [i for i in result if Converter.jsonFrom(i[2])['media'] in type]

		return result
