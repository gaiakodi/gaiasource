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

from lib.modules.tools import Media, Logger, Regex
from lib.modules.account import Tmdb
from lib.modules.network import Networker

class MetaTmdb(object):

	LinkMovie		= 'https://themoviedb.org/movie/%s'
	LinkShow		= 'https://themoviedb.org/tv/%s'
	LinkSeason		= 'https://themoviedb.org/tv/%s/season/%d'
	LinkEpisode		= 'https://themoviedb.org/tv/%s/season/%d/episode/%d'

	LinkSearchMovie	= 'https://api.themoviedb.org/3/search/movie'
	LinkSearchShow	= 'https://api.themoviedb.org/3/search/tv'

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
	# SEARCH
	##############################################################################

	@classmethod
	def searchMovie(self, query = None, page = 1, link = None):
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

			data = self.request(method = Networker.MethodGet, link = MetaTmdb.LinkSearchMovie, data = {'query' : query, 'page' : page})
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
	def searchShow(self, query = None, page = 1, link = None):
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

			data = self.request(method = Networker.MethodGet, link = MetaTmdb.LinkSearchShow, data = {'query' : query, 'page' : page})
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
