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

from lib.modules.tools import Media, Logger, Regex, Time, Tools, Converter
from lib.modules.account import Tmdb
from lib.modules.network import Networker

class MetaTmdb(object):

	LinkMovie		= 'https://themoviedb.org/movie/%s'
	LinkShow		= 'https://themoviedb.org/tv/%s'
	LinkSeason		= 'https://themoviedb.org/tv/%s/season/%d'
	LinkEpisode		= 'https://themoviedb.org/tv/%s/season/%d/episode/%d'

	LinkSearchMovie	= 'https://api.themoviedb.org/3/search/movie'
	LinkSearchShow	= 'https://api.themoviedb.org/3/search/tv'

	LinkId			= 'https://api.themoviedb.org/3/find/%s'

	LinkSetIds		= 'https://files.tmdb.org/p/exports/collection_ids_%s.json.gz'
	LinkSetDetails	= 'https://api.themoviedb.org/3/collection/%s'

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def link(self, media = None, id = None, season = None, episode = None, metadata = None):
		if metadata:
			try:
				media = Media.TypeShow if 'tvshowtitle' in metadata or 'season' in metadata else Media.TypeMovie
				id = metadata['id']['tmdb']
				season = metadata['season']
				episode = metadata['episode']
			except: pass

		if id:
			if Media.typeTelevision(media):
				if not episode is None: return MetaTmdb.LinkEpisode % (id, season, episode)
				elif not season is None: return MetaTmdb.LinkSeason % (id, season)
				else: return MetaTmdb.LinkShow % id
			else:
				return MetaTmdb.LinkMovie % id

		return None

	##############################################################################
	# REQUEST
	##############################################################################

	@classmethod
	def request(self, link, data = None, method = None):
		if not data: data = {}
		data['api_key'] = Tmdb().key()
		if method is None: method = Networker.MethodGet
		return Networker().requestJson(method = method, link = link, data = data)

	##############################################################################
	# ID
	##############################################################################

	@classmethod
	def id(self, media, idImdb = None, idTvdb = None):
		source = None
		link = MetaTmdb.LinkId

		if idImdb:
			link = link % idImdb
			source = 'imdb_id'
		elif idTvdb and Media.typeTelevision(media):
			link = link % idTvdb
			source = 'tvdb_id'
		else:
			return None

		data = self.request(method = Networker.MethodGet, link = link, data = {'external_source' : source})
		if data:
			if media == Media.TypeShow: result = 'tv_results'
			elif media == Media.TypeSeason: result = 'tv_season_results'
			elif media == Media.TypeEpisode: result = 'tv_episode_results'
			else: result = 'movie_results'
			try: return data[result][0].get('id')
			except: pass

		return None

	@classmethod
	def idMovie(self, idImdb = None, idTvdb = None):
		return self.id(media = Media.TypeMovie, idImdb = idImdb, idTvdb = idTvdb)

	@classmethod
	def idShow(self, idImdb = None, idTvdb = None):
		return self.id(media = Media.TypeShow, idImdb = idImdb, idTvdb = idTvdb)

	@classmethod
	def idSeason(self, idTvdb = None):
		return self.id(media = Media.TypeSeason, idImdb = idImdb, idTvdb = idTvdb)

	@classmethod
	def idEpisode(self, idImdb = None, idTvdb = None):
		return self.id(media = Media.TypeEpisode, idImdb = idImdb, idTvdb = idTvdb)

	##############################################################################
	# SEARCH
	##############################################################################

	@classmethod
	def searchMovie(self, query = None, page = 1, link = None, language = None):
		results = None
		try:
			if link:
				parts = Networker.linkParts(link = link)
				try:
					query = Networker.linkUnquote(parts[-2])
					page = int(parts[-1])
				except:
					Logger.error()
					return results

			data = {'query' : query, 'page' : page}
			if language: data['language'] = language

			data = self.request(method = Networker.MethodGet, link = MetaTmdb.LinkSearchMovie, data = data)
			if data:
				page +=1
				next = None
				if 'total_pages' in data and data['total_pages'] >= page:
					next = '%s/%s/%s' % (MetaTmdb.LinkSearchMovie, Networker.linkQuote(query), page)

				results = []
				for item in data['results']:
					try:
						result = {}

						ids = {}
						idTmdb = item.get('id')
						if idTmdb: result['tmdb'] = ids['tmdb'] = str(idTmdb)
						if ids: result['id'] = ids

						title = item.get('title')
						if title: result['title'] = Networker.htmlDecode(title)

						originaltitle = item.get('original_title')
						if originaltitle: result['originaltitle'] = Networker.htmlDecode(originaltitle)

						plot = item.get('overview')
						if plot: result['plot'] = Networker.htmlDecode(plot)

						premiered = item.get('release_date')
						if premiered:
							premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
							if premiered:
								result['premiered'] = premiered
								year = Regex.extract(data = premiered, expression = '(\d{4})-', group = 1)
								if year: result['year'] = int(year)

						if next: result['next'] = next

						if result: results.append(result)
					except: Logger.error()
		except: Logger.error()

		return results

	@classmethod
	def searchShow(self, query = None, page = 1, link = None, language = None):
		results = None
		try:
			if link:
				parts = Networker.linkParts(link = link)
				try:
					query = Networker.linkUnquote(parts[-2])
					page = int(parts[-1])
				except:
					Logger.error()
					return results

			data = {'query' : query, 'page' : page}
			if language: data['language'] = language

			data = self.request(method = Networker.MethodGet, link = MetaTmdb.LinkSearchShow, data = data)
			if data:
				page +=1
				next = None
				if 'total_pages' in data and data['total_pages'] >= page:
					next = '%s/%s/%s' % (MetaTmdb.LinkSearchShow, Networker.linkQuote(query), page)

				results = []
				for item in data['results']:
					try:
						result = {}

						ids = {}
						idTmdb = item.get('id')
						if idTmdb: result['tmdb'] = ids['tmdb'] = str(idTmdb)
						if ids: result['id'] = ids

						title = item.get('name')
						if title: result['title'] = Networker.htmlDecode(title)

						originaltitle = item.get('original_name')
						if originaltitle: result['originaltitle'] = Networker.htmlDecode(originaltitle)

						plot = item.get('overview')
						if plot: result['plot'] = Networker.htmlDecode(plot)

						premiered = item.get('first_air_date')
						if premiered:
							premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
							if premiered:
								result['premiered'] = premiered
								year = Regex.extract(data = premiered, expression = '(\d{4})-', group = 1)
								if year: result['year'] = int(year)

						if next: result['next'] = next

						if result: results.append(result)
					except: Logger.error()
		except: Logger.error()

		return results

	##############################################################################
	# SET
	##############################################################################

	@classmethod
	def sets(self):
		result = None
		try:
			link = MetaTmdb.LinkSetIds % Time.past(days = 1, format = '%m_%d_%Y')
			data = Networker().requestData(link = link)
			if data:
				data = Tools.gzUncompress(data = data)
				if data:
					data = Converter.unicode(data)
					if data:
						data = data.strip()
						data = data.replace('\n', ',\n')
						data = data.strip('\n').strip(',').strip('\n')
						data = Converter.jsonFrom('[' + data + ']')
						if data: result = [{'tmdb' : i['id'], 'title' : i['name']} for i in data]
		except: Logger.error()
		return result

	@classmethod
	def set(self, id, language = None):
		data = {'language' : language} if language else None
		data = self.request(method = Networker.MethodGet, link = MetaTmdb.LinkSetDetails % id, data = data)
		return data
