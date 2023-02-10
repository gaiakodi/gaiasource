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
from lib.modules.tools import Selection, Time, Tools

class Searches(Database):

	Name = 'searches' # The name of the file. Update version number of the database structure changes.

	TypeMovies = 'movies'
	TypeSets = 'sets'
	TypeShows = 'shows'
	TypeDocumentaries = 'documentaries'
	TypeShorts = 'shorts'
	TypePeople = 'people'

	def __init__(self):
		Database.__init__(self, Searches.Name)

	def _initialize(self):
		self._createAll('CREATE TABLE IF NOT EXISTS %s (terms TEXT PRIMARY KEY, time INTEGER, kids INTEGER);', [Searches.TypeMovies, Searches.TypeSets, Searches.TypeShows, Searches.TypeDocumentaries, Searches.TypeShorts, Searches.TypePeople])

	def insert(self, searchType, searchTerms, searchKids = Selection.TypeUndefined):
		searchTerms = searchTerms.strip()
		if searchTerms and len(searchTerms) > 0:
			existing = self._select('SELECT terms FROM %s WHERE terms = "%s";' % (searchType, searchTerms))
			if existing:
				self.update(searchType, searchTerms)
			else:
				self._insert('INSERT INTO %s (terms, time, kids) VALUES ("%s", %d, %d);' % (searchType, searchTerms, Time.timestamp(), searchKids))

	def insertMovies(self, searchTerms, searchKids = Selection.TypeUndefined):
		self.insert(Searches.TypeMovies, searchTerms, searchKids)

	def insertSets(self, searchTerms, searchKids = Selection.TypeUndefined):
		self.insert(Searches.TypeSets, searchTerms, searchKids)

	def insertShows(self, searchTerms, searchKids = Selection.TypeUndefined):
		self.insert(Searches.TypeShows, searchTerms, searchKids)

	def insertDocumentaries(self, searchTerms, searchKids = Selection.TypeUndefined):
		self.insert(Searches.TypeDocumentaries, searchTerms, searchKids)

	def insertShorts(self, searchTerms, searchKids = Selection.TypeUndefined):
		self.insert(Searches.TypeShorts, searchTerms, searchKids)

	def insertPeople(self, searchTerms, searchKids = Selection.TypeUndefined):
		self.insert(Searches.TypePeople, searchTerms, searchKids)

	def update(self, searchType, searchTerms):
		searchTerms = searchTerms.strip()
		self._update('UPDATE %s SET time = %d WHERE terms = "%s";' % (searchType, Time.timestamp(), searchTerms))

	def updateMovies(self, searchTerms):
		self.update(Searches.TypeMovies, searchTerms)

	def updateSets(self, searchTerms):
		self.update(Searches.TypeSets, searchTerms)

	def updateShows(self, searchTerms):
		self.update(Searches.TypeShows, searchTerms)

	def updateDocumentaries(self, searchTerms):
		self.update(Searches.TypeDocumentaries, searchTerms)

	def updateShorts(self, searchTerms):
		self.update(Searches.TypeShorts, searchTerms)

	def updatePeople(self, searchTerms):
		self.update(Searches.TypePeople, searchTerms)

	def retrieve(self, searchType, count = 30, kids = Selection.TypeUndefined):
		if kids == Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('SELECT terms, kids FROM %s %s ORDER BY time DESC LIMIT %d;' % (searchType, kids, count))

	def retrieveAll(self, count = 30, kids = Selection.TypeUndefined, type = None):
		if kids == Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids

		if type is None: type = [Searches.TypeMovies, Searches.TypeSets, Searches.TypeShows, Searches.TypeDocumentaries, Searches.TypeShorts, Searches.TypePeople]
		elif not Tools.isArray(type): type = [type]

		parameters = []
		for i in type: parameters.extend([i, i])
		parameters.extend([kids, count])

		return self._select(('''
			SELECT type, terms, kids FROM
			(''' + (' UNION ALL '.join(['SELECT time, terms, kids, "%s" as type FROM %s' for i in range(len(type))])) + ''')
			%s
			ORDER BY time DESC LIMIT %d;
		''') % tuple(parameters))

	def retrieveMovies(self, count = 30, kids = Selection.TypeUndefined):
		if kids == Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT terms, kids, "%s" as type FROM %s
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (Searches.TypeMovies, Searches.TypeMovies, kids, count))

	def retrieveSets(self, count = 30, kids = Selection.TypeUndefined):
		if kids == Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT terms, kids, "%s" as type FROM %s
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (Searches.TypeSets, Searches.TypeSets, kids, count))

	def retrieveShows(self, count = 30, kids = Selection.TypeUndefined):
		if kids == Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT terms, kids, "%s" as type FROM %s
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (Searches.TypeShows, Searches.TypeShows, kids, count))

	def retrieveDocumentaries(self, count = 30, kids = Selection.TypeUndefined):
		if kids == Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT terms, kids, "%s" as type FROM %s
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (Searches.TypeDocumentaries, Searches.TypeDocumentaries, kids, count))

	def retrieveShorts(self, count = 30, kids = Selection.TypeUndefined):
		if kids == Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT terms, kids, "%s" as type FROM %s
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (Searches.TypeShorts, Searches.TypeShorts, kids, count))

	def retrievePeople(self, count = 30, kids = Selection.TypeUndefined):
		if kids == Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT terms, kids, "%s" as type FROM %s
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (Searches.TypePeople, Searches.TypePeople, kids, count))
