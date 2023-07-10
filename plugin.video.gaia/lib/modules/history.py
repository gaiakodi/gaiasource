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
from lib.modules.tools import Media, Selection, Hash, Converter, Tools, Time

class History(Database):

	Name = 'history' # The name of the file. Update version number of the database structure changes.

	Duration = 15778800 # 6 months. For how long to keep history entries, after which they get deleted to save some storage space.

	def __init__(self):
		Database.__init__(self, History.Name)

	def _initialize(self):
		self._createAll('''
			CREATE TABLE IF NOT EXISTS %s
			(
				id TEXT PRIMARY KEY,
				kids INTEGER,
				time INTEGER,
				link TEXT,
				metadata TEXT,
				source TEXT
			);
			''',
			[Media.TypeMovie, Media.TypeShow, Media.TypeDocumentary, Media.TypeShort]
		)

	def _id(self, media, link, metadata):
		# Allow the same link to be inserted multiple times for movie or show/season packs.
		id = []
		if Media.typeTelevision(media):
			try: id.append(metadata['imdb'] if 'imdb' in metadata and metadata['imdb'] else metadata['tvdb'])
			except: pass
			try: id.append(metadata['season'])
			except: pass
			try: id.append(metadata['episode'])
			except: pass
		else:
			try: id.append(metadata['imdb'] if 'imdb' in metadata and metadata['imdb'] else metadata['tmdb'])
			except: pass
		id.append(link)
		return Hash.sha1('_'.join([str(i) for i in id]))

	def _media(self, media):
		if Media.typeTelevision(media): return Media.TypeShow
		else: return media

	def _prepare(self, data):
		if data is None: return self._null()
		elif not Tools.isString(data): data = Converter.jsonTo(data)
		return '"%s"' % data.replace('"', '""')

	# The database can get very large over time (100MB+) due to all the show metadata stored.
	# Clean to reduce the size.
	def clean(self, time = None):
		if time is None: time = Time.timestamp() - History.Duration
		self._deleteAll('DELETE FROM `%s` WHERE time < ?;', parameters = (time,), compress = True)

	def insert(self, media, link, metadata, source, kids = Selection.TypeUndefined):
		media = self._media(media = media)
		id = self._id(media = media, link = link, metadata = metadata)
		existing = self._select('SELECT id FROM %s WHERE id = "%s";' % (media, id))

		if existing:
			self.update(media, id)
		else:
			self._insert('''
				INSERT INTO %s
				(id, kids, time, link, metadata, source)
				VALUES
				("%s", %d, %d, "%s", %s, %s);
				'''
				% (media, id, kids, Time.timestamp(), link, self._prepare(metadata), self._prepare(source))
			)

	def insertMovie(self, link, metadata, source, kids = Selection.TypeUndefined):
		self.insert(media = Media.TypeMovie, kids = kids, link = link, metadata = metadata, source = source)

	def insertShow(self, link, metadata, source, kids = Selection.TypeUndefined):
		self.insert(media = Media.TypeShow, kids = kids, link = link, metadata = metadata, source = source)

	def insertDocumentary(self, link, metadata, source, kids = Selection.TypeUndefined):
		self.insert(media = Media.TypeDocumentary, kids = kids, link = link, metadata = metadata, source = source)

	def insertShort(self, link, metadata, source, kids = Selection.TypeUndefined):
		self.insert(media = Media.TypeShort, kids = kids, link = link, metadata = metadata, source = source)

	def update(self, media, id):
		media = self._media(media)
		self._update('UPDATE %s SET time = %d WHERE id = "%s";' % (media, Time.timestamp(), id))

	def updateMovie(self, id):
		self.update(media = Media.TypeMovie, id = id)

	def updateShow(self, id):
		self.update(media = Media.TypeShow, id = id)

	def updateDocumentary(self, id):
		self.update(media = Media.TypeDocumentary, id = id)

	def updateShort(self, id):
		self.update(media = Media.TypeShort, id = id)

	def retrieve(self, media, count = 30, kids = Selection.TypeUndefined):
		media = self._media(media)
		if media is None:
			return self.retrieveAll(count = count, kids = kids)
		else:
			if kids == Selection.TypeUndefined: kids = ''
			else: kids = 'WHERE kids IS %d' % kids
			return self._select('SELECT "%s" as media, kids, time, link, metadata, source FROM %s %s ORDER BY time DESC LIMIT %d;' % (media, media, kids, count))

	def retrieveAll(self, count = 30, kids = Selection.TypeUndefined):
		if kids == Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT media, kids, time, link, metadata, source FROM
			(
				SELECT time, kids, time, link, metadata, source, "%s" as media FROM %s
				UNION ALL
				SELECT time, kids, time, link, metadata, source, "%s" as media FROM %s
				UNION ALL
				SELECT time, kids, time, link, metadata, source, "%s" as media FROM %s
				UNION ALL
				SELECT time, kids, time, link, metadata, source, "%s" as media FROM %s
			)
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (Media.TypeMovie, Media.TypeMovie, Media.TypeShow, Media.TypeShow, Media.TypeDocumentary, Media.TypeDocumentary, Media.TypeShort, Media.TypeShort, kids, count))

	def retrieveMovie(self, count = 30, kids = Selection.TypeUndefined):
		if kids == Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT "%s" as media, kids, time, link, metadata, source FROM %s
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (Media.TypeMovie, Media.TypeMovie, kids, count))

	def retrieveShow(self, count = 30, kids = Selection.TypeUndefined):
		if kids == Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT "%s" as media, kids, time, link, metadata, source FROM %s
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (Media.TypeShow, Media.TypeShow, kids, count))

	def retrieveDocumentary(self, count = 30, kids = Selection.TypeUndefined):
		if kids == Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT "%s" as media, kids, time, link, metadata, source FROM %s
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (Media.TypeDocumentary, Media.TypeDocumentary, kids, count))

	def retrieveShort(self, count = 30, kids = Selection.TypeUndefined):
		if kids == Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT "%s" as media, kids, time, link, metadata, source FROM %s
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (Media.TypeShort, Media.TypeShort, kids, count))
