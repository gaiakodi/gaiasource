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

from lib.modules.tools import Media, Logger, Regex, Time, Tools, Converter, Language, Archive
from lib.modules.account import Tmdb
from lib.modules.network import Networker
from lib.modules.cache import Cache
from lib.modules.concurrency import Lock

class MetaTmdb(object):

	LinkMovie			= 'https://themoviedb.org/movie/%s'
	LinkSet				= 'https://themoviedb.org/collection/%s'
	LinkShow			= 'https://themoviedb.org/tv/%s'
	LinkSeason			= 'https://themoviedb.org/tv/%s/season/%d'
	LinkEpisode			= 'https://themoviedb.org/tv/%s/season/%d/episode/%d'

	LinkFindMovie		= 'https://themoviedb.org/search/movie?query=%s'
	LinkFindSet			= 'https://themoviedb.org/search/collection?query=%s'
	LinkFindShow		= 'https://themoviedb.org/search/tv?query=%s'

	LinkList			= 'https://api.themoviedb.org/3/list/%s'

	LinkSearchMovie		= 'https://api.themoviedb.org/3/search/movie'
	LinkSearchSet		= 'https://api.themoviedb.org/3/search/collection'
	LinkSearchShow		= 'https://api.themoviedb.org/3/search/tv'

	LinkDiscoverMovie	= 'https://api.themoviedb.org/3/discover/movie'
	LinkDiscoverShow	= 'https://api.themoviedb.org/3/discover/tv'

	LinkRatedMovie		= 'https://api.themoviedb.org/3/movie/top_rated'
	LinkRatedShow		= 'https://api.themoviedb.org/3/tv/top_rated'

	LinkId				= 'https://api.themoviedb.org/3/find/%s'

	LinkSetIds			= 'https://files.tmdb.org/p/exports/collection_ids_%s.json.gz'
	LinkSetDetails		= 'https://api.themoviedb.org/3/collection/%s'
	LinkSetImages		= 'https://api.themoviedb.org/3/collection/%s/images'

	LinkGenreMovie		= 'https://api.themoviedb.org/3/genre/movie/list'
	LinkGenreShow		= 'https://api.themoviedb.org/3/genre/tv/list'

	# https://developers.themoviedb.org/3/movies/get-movie-release-dates
	ReleasePremiere		= 1
	ReleaseLimited		= 2
	ReleaseTheatre		= 3
	ReleaseDigital		= 4
	ReleasePhysical		= 5
	ReleaseTelevision	= 6

	# https://developers.themoviedb.org/3/genres/get-movie-list
	GenreDocumentary	= 99

	SortRelease			= 'primary_release_date'
	SortTitle			= 'original_title'
	SortPopularity		= 'popularity'
	SortRating			= 'vote_average'
	SortVotes			= 'vote_count'
	SortRevenue			= 'revenue'

	OrderAscending		= 'asc'
	OrderDescending		= 'desc'
	OrderDefault		= {
		SortRelease		: OrderDescending,
		SortTitle		: OrderAscending,
		SortPopularity	: OrderDescending,
		SortRating		: OrderDescending,
		SortVotes		: OrderDescending,
		SortRevenue		: OrderDescending,
	}

	# TMDb does not allow one to specify the number of items to retrieve (eg: in discover()).
	# TMDb uses a fixed limit and then requirrs paging.
	LimitFixed			= 20

	Lock				= Lock()

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def link(self, media = None, id = None, title = None, year = None, season = None, episode = None, metadata = None, search = False):
		try:
			if metadata:
				if not media:
					if 'tvshowtitle' in metadata:
						if 'episode' in metadata: media = Media.TypeEpisode
						elif 'season' in metadata: media = Media.TypeSeason
						else: media = Media.TypeShow
					elif 'set' in metadata and not 'collection' in metadata:
						media = Media.TypeSet
					else:
						media = Media.TypeMovie
				if media == Media.TypeSet:
					try: id = metadata['collection']['id']
					except: pass
				if not id:
					try: id = metadata['id']['tmdb']
					except: pass
				try: title = metadata['tvshowtitle'] if metadata['tvshowtitle'] else metadata['title']
				except: pass
				try: year = metadata['year']
				except: pass
				try: season = metadata['season']
				except: pass
				try: episode = metadata['episode']
				except: pass

			if media == Media.TypeShow:
				episode = None
				season = None
			elif media == Media.TypeSeason:
				episode = None

			if id:
				if Media.typeTelevision(media):
					if not episode is None: return MetaTmdb.LinkEpisode % (id, season, episode)
					elif not season is None: return MetaTmdb.LinkSeason % (id, season)
					else: return MetaTmdb.LinkShow % id
				elif media == Media.TypeSet:
					return MetaTmdb.LinkSet % id
				else:
					return MetaTmdb.LinkMovie % id
			elif search and title:
				query = title
				if year and Media.typeMovie(media): query += ' ' + str(year)
				link = MetaImdb.LinkFindShow if Media.typeTelevision(media) else MetaImdb.LinkFindSet if media == Media.TypeSet else MetaImdb.LinkFindMovie
				return link % Networker.linkQuote(data = query, plus = False)
		except: Logger.error()
		return None

	@classmethod
	def linkEncode(self, link, query = None, page = None, data = None, increment = True):
		parameters = Networker.linkParameters(link = link)
		link = Networker.linkClean(link = link, parametersStrip = True, headersStrip = True)

		if (page is None or page == 1) and 'page' in parameters and parameters['page']: page = int(parameters['page'])
		if not page is None and increment: page += 1
		if data and 'total_pages' in data and data['total_pages'] < page: return None

		if not query is None: parameters['query'] = query
		if not page is None: parameters['page'] = page

		return Networker.linkCreate(link = link, parameters = parameters, duplicates = False)

	@classmethod
	def linkDencode(self, link):
		if link: return Networker.linkParameters(link = link)
		else: return None

	@classmethod
	def linkData(self, link = None, query = None, page = None, language = None):
		if link: data = self.linkDencode(link = link)
		else: data = {}

		if not query is None and not 'query' in data: data['query'] = query
		if not page is None and not 'page' in data: data['page'] = page
		if not language is None and not 'language' in data: data['language'] = language[0] if Tools.isArray(language) else language
		if not 'include_adult' in data: data['include_adult'] = False
		if not 'include_video' in data: data['include_video'] = False # https://www.themoviedb.org/talk/5f2d3257cdbaff0035a40753

		return data

	##############################################################################
	# REQUEST
	##############################################################################

	@classmethod
	def retrieve(self, link, linkExtra = None, query = None, page = 1, language = None, data = None, next = None):
		results = None
		try:
			if not linkExtra: linkExtra = link
			parameters = self.linkData(link = linkExtra, query = query, page = page, language = language)
			if data:
				if not parameters: parameters = {}
				parameters.update(data)
			data = self.request(method = Networker.MethodGet, link = link, data = parameters)
			if data: results = self.items(data = data, link = linkExtra, query = query, page = page, next = next)
		except: Logger.error()
		return results

	@classmethod
	def request(self, link, data = None, method = None, cache = None, lock = False):
		try:
			if lock: MetaTmdb.Lock.acquire()
			if cache is None: return self._request(link = link, data = data, method = method)
			else: return Cache.instance().cacheSeconds(timeout = cache, function = self._request, link = link, data = data, method = method)
		finally:
			if lock: MetaTmdb.Lock.release()

	@classmethod
	def _request(self, link, data = None, method = None):
		if not data: data = {}
		data['api_key'] = Tmdb().key()
		if method is None: method = Networker.MethodGet
		return Networker().requestJson(method = method, link = link, data = data)

	##############################################################################
	# ITEM
	##############################################################################

	@classmethod
	def item(self, item, next = None):
		if not item: return None
		result = {}

		ids = {}
		idTmdb = item.get('id')
		if idTmdb: result['tmdb'] = ids['tmdb'] = str(idTmdb)
		if ids: result['id'] = ids

		title = item.get('title')
		if not title: title = item.get('name')
		if title: result['title'] = Networker.htmlDecode(title)

		originaltitle = item.get('original_title')
		if not originaltitle: originaltitle = item.get('original_name')
		if originaltitle: result['originaltitle'] = Networker.htmlDecode(originaltitle)

		plot = item.get('overview')
		if plot: result['plot'] = Networker.htmlDecode(plot)

		premiered = item.get('release_date')
		if not premiered: premiered = item.get('first_air_date')
		if premiered:
			premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
			if premiered:
				result['premiered'] = premiered
				year = Regex.extract(data = premiered, expression = '(\d{4})-', group = 1)
				if year: result['year'] = int(year)

		rating = item.get('vote_average')
		votes = item.get('vote_count')
		if not rating is None or not votes is None:
			value = {}
			if not rating is None: value['rating'] = rating
			if not votes is None: value['votes'] = votes
			result.update({'temp' : {'tmdb' : value}})

		if next: result['next'] = next

		return result

	@classmethod
	def items(self, items = None, next = None, data = None, link = None, query = None, page = None, increment = True):
		if items is None and data:
			for i in ['results', 'items', 'movie_results', 'tv_results', 'tv_season_results', 'tv_episode_results']:
				if i in data:
					items = data[i]
					break
		if not items: return None

		if next is None and not page is None: next = self.linkEncode(link = link, query = query, page = page, data = data, increment = increment)

		result = []
		for item in items:
			try:
				item = self.item(item = item, next = next)
				if item: result.append(item)
			except: Logger.error()

		return result

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
	# LIST
	##############################################################################

	@classmethod
	def list(self, id = None, language = None, link = None):
		if not link: link = MetaTmdb.LinkList % id
		return self.retrieve(link = link, linkExtra = link, language = language, next = False)

	##############################################################################
	# SEARCH
	##############################################################################

	@classmethod
	def searchMovie(self, query = None, page = 1, language = None, link = None):
		return self.retrieve(link = MetaTmdb.LinkSearchMovie, linkExtra = link, query = query, page = page, language = language)

	@classmethod
	def searchSet(self, query = None, page = 1, language = None, link = None):
		return self.retrieve(link = MetaTmdb.LinkSearchSet, linkExtra = link, query = query, page = page, language = language)

	@classmethod
	def searchShow(self, query = None, page = 1, language = None, link = None):
		return self.retrieve(link = MetaTmdb.LinkSearchShow, linkExtra = link, query = query, page = page, language = language)

	##############################################################################
	# DISCOVER
	##############################################################################

	# year: integer = single year
	# release: integer = single minimum timestamp | tuple = range of timestamps (from and to) | tuple = if one value is None, ignore that and only use upper or lower date.
	# rating: integer = single minimum rating | tuple = range of rating (from and to) | tuple = if one value is None, ignore that and only use upper or lower rating.
	# votes: integer = single minimum vote | tuple = range of votes (from and to) | tuple = if one value is None, ignore that and only use upper or lower votes.
	@classmethod
	def discover(self, media, page = 1, language = None, sort = None, order = None, type = None, region = None, release = None, year = None, genre = None, rating = None, votes = None, link = None):
		if link:
			data = self.linkDencode(link = link)
			if data:
				if 'page' in data:
					page = int(data['page'])
					del data['page']
				if 'language' in data:
					language = data['language']
					del data['language']
				if 'sort' in data:
					sort = data['sort']
					del data['sort']
				if 'order' in data:
					order = data['order']
					del data['order']
				if 'year' in data:
					year = int(data['year'])
					del data['year']
				if 'type' in data:
					type = data['type']
					if '|' in type: type = [int(i) if Tools.isNumeric(i) else i for i in type.split('|')]
					elif Tools.isNumeric(type): type = int(type)
					del data['type']
				if 'release' in data:
					release = data['release']
					if ',' in release: release = [int(i) if Tools.isNumeric(i) else i for i in release.split(',')]
					elif Tools.isNumeric(release): release = int(release)
					del data['release']
				if 'genre' in data:
					if genre is None: genre = []
					genres = data['genre']
					if ',' in genres: genre.extend([int(i) if Tools.isNumeric(i) else i for i in genres.split(',')])
					elif Tools.isNumeric(genres): genre.append(int(genres))
					del data['genre']
				if 'rating' in data:
					rating = data['rating']
					if ',' in rating: rating = [float(i) for i in rating.split(',')]
					else: rating = float(rating)
					del data['rating']
				if 'votes' in data:
					votes = data['votes']
					if ',' in votes: votes = [int(i) for i in votes.split(',')]
					else: votes = int(votes)
					del data['votes']
		else:
			data = None

		if not data: data = {}

		if sort:
			if not order: order = MetaTmdb.OrderDefault[sort]
			data['sort_by'] = sort + '.' + order

		if type:
			if Tools.isArray(type): type = '|'.join([str(i) for i in type])
			data['with_release_type'] = type

		if region or type: # Always add if type was added.
			# NB: Add a region, otherwise the API call returns titles that were only theatrically released and were not digitially/physically released yet.
			# Eg: Mission Impossible 7 is returned, although still in theaters.
			# When getting the realease dates: https://api.themoviedb.org/3/movie/575264/release_dates?api_key=...
			# The digital/physical release dates are correct. So without using region, it probably checks the wrong dates (eg theater dates).
			# Do not add DE as region, because for some reason it still returns Mission Impossible 7.
			if not region: region = ['US', 'GB', 'CA', 'FR', 'NL', 'PL', 'SE', 'NO', 'FI', 'ES', 'PT', 'IT', 'JP', 'AU', 'NZ', 'ZA', 'BR', 'MX']
			if Tools.isArray(region): region = '|'.join([str(i) for i in region])
			data['region'] = region

		if release:
			# NB: Use "primary_release_date" instead of "release_date".
			# Otherwise when returning the latests digital/physical releases, old items are returned (sometimes 20+ years old).
			releaseStart = None
			releaseEnd = None
			if Tools.isArray(release):
				releaseStart = release[0]
				releaseEnd = release[1]
			else:
				releaseStart = release
			if releaseStart:
				if Tools.isInteger(releaseStart): releaseStart = Time.format(releaseStart, format = Time.FormatDate)
				data['primary_release_date.gte'] = releaseStart
			if releaseEnd:
				if Tools.isInteger(releaseEnd): releaseEnd = Time.format(releaseEnd, format = Time.FormatDate)
				data['primary_release_date.lte'] = releaseEnd

		if year: data['year'] = year

		if genre:
			if not Tools.isArray(genre): genre = [genre]
			genreInclude = []
			genreExclude = []
			for i in genre:
				if i < 0: genreExclude.append(str(-1 * i))
				else: genreInclude.append(str(i))
			if genreInclude: data['with_genres'] = ','.join(genreInclude)
			if genreExclude: data['without_genres'] = ','.join(genreExclude)

		if not rating is None:
			ratingStart = None
			ratingEnd = None
			if Tools.isArray(rating):
				ratingStart = rating[0]
				ratingEnd = rating[1]
			else:
				ratingStart = rating
			if ratingStart: data['vote_average.gte'] = ratingStart
			if ratingEnd: data['vote_average.lte'] = ratingEnd

		if not votes is None:
			votesStart = None
			votesEnd = None
			if Tools.isArray(votes):
				votesStart = votes[0]
				votesEnd = votes[1]
			else:
				votesStart = votes
			if votesStart: data['vote_count.gte'] = votesStart
			if votesEnd: data['vote_count.lte'] = votesEnd

		if language:
			if not Tools.isArray(language): language = [language]
			if not Language.EnglishCode in language: language.insert(0, Language.EnglishCode)
			data['with_original_language'] = '|'.join(language)

		link = Networker.linkClean(link = link, parametersStrip = True, headersStrip = True)
		link = Networker.linkCreate(link = link, parameters = data, duplicates = False)

		return self.retrieve(link = MetaTmdb.LinkDiscoverShow if Media.typeTelevision(media) else MetaTmdb.LinkDiscoverMovie, linkExtra = link, page = page, language = language, data = data)

	@classmethod
	def discoverMovie(self, page = 1, language = None, sort = None, order = None, type = None, release = None, year = None, genre = None, rating = None, votes = None, link = None):
		return self.discover(media = Media.TypeMovie, page = page, language = language, sort = sort, order = order, type = type, release = release, year = year, genre = genre, rating = rating, votes = votes, link = link)

	@classmethod
	def discoverShow(self, page = 1, language = None, sort = None, order = None, rtype = None, elease = None, year = None, genre = None, rating = None, votes = None, link = None):
		return self.discover(media = Media.TypeShow, page = page, language = language, sort = sort, order = order, type = type, release = release, year = year, genre = genre, rating = rating, votes = votes, link = link)

	##############################################################################
	# RATED
	##############################################################################

	@classmethod
	def ratedMovie(self, page = 1, language = None, link = None):
		return self.retrieve(link = MetaTmdb.LinkRatedMovie, linkExtra = link, page = page, language = language)

	@classmethod
	def ratedShow(self, page = 1, language = None, link = None):
		return self.retrieve(link = MetaTmdb.LinkRatedShow, linkExtra = link, page = page, language = language)

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
				data = Archive.gzipDecompress(data = data)
				if data:
					data = Converter.unicode(data)
					if data:
						data = data.strip()
						data = data.replace('\n', ',\n')
						data = data.strip('\n').strip(',').strip('\n')
						data = Converter.jsonFrom('[' + data + ']')
						if data: result = data
		except: Logger.error()
		return result

	@classmethod
	def set(self, id, language = None):
		data = {'language' : language} if language else None
		data = self.request(method = Networker.MethodGet, link = MetaTmdb.LinkSetDetails % id, data = data)
		return data

	@classmethod
	def setImages(self, id, language = None):
		data = {'language' : language} if language else None
		data = self.request(method = Networker.MethodGet, link = MetaTmdb.LinkSetImages % id, data = data)
		return data

	##############################################################################
	# GENRE
	##############################################################################

	@classmethod
	def generes(self, media = None, language = None, cache = True):
		link = MetaTmdb.LinkGenreShow if Media.typeTelevision(media) else MetaTmdb.LinkGenreMovie
		data = {'language' : language} if language else None
		data = self.request(method = Networker.MethodGet, link = link, data = data, cache = Cache.TimeoutLong if cache else None, lock = cache)
		if data: data = {i['id'] : i['name'] for i in data['genres']}
		return data

	@classmethod
	def generesMovie(self, language = None, cache = True):
		return self.generes(media = Media.TypeMovie, language = language, cache = cache)

	@classmethod
	def generesShow(self, language = None, cache = True):
		return self.generes(media = Media.TypeShow, language = language, cache = cache)

	@classmethod
	def genere(self, id, media = None, language = None, cache = True):
		genres = self.generes(media = media, language = language, cache = cache)
		try: return generes[id]
		except: return None

	@classmethod
	def genereMovie(self, id, language = None, cache = True):
		return self.genere(id =  id, media = Media.TypeMovie, language = language, cache = cache)

	@classmethod
	def genereShow(self, id, language = None, cache = True):
		return self.genere(id =  id, media = Media.TypeShow, language = language, cache = cache)
