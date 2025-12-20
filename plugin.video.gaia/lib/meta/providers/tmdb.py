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

from lib.modules.tools import Media, Logger, Regex, Time, Tools, Converter, Language, Country, Math
from lib.modules.compression import Compressor
from lib.modules.network import Networker
from lib.modules.concurrency import Pool
from lib.modules.cache import Cache

from lib.modules.account import Tmdb as Account

from lib.meta.provider import MetaProvider
from lib.meta.tools import MetaTools
from lib.meta.image import MetaImage

class MetaTmdb(MetaProvider):

	LinkMovie				= 'https://themoviedb.org/movie/%s'
	LinkSet					= 'https://themoviedb.org/collection/%s'
	LinkShow				= 'https://themoviedb.org/tv/%s'
	LinkSeason				= 'https://themoviedb.org/tv/%s/season/%d'
	LinkEpisode				= 'https://themoviedb.org/tv/%s/season/%d/episode/%d'

	LinkFindMovie			= 'https://themoviedb.org/search/movie?query=%s'
	LinkFindSet				= 'https://themoviedb.org/search/collection?query=%s'
	LinkFindShow			= 'https://themoviedb.org/search/tv?query=%s'

	LinkList				= 'https://api.themoviedb.org/3/list/%s'

	LinkSearchMovie			= 'https://api.themoviedb.org/3/search/movie'
	LinkSearchSet			= 'https://api.themoviedb.org/3/search/collection'
	LinkSearchShow			= 'https://api.themoviedb.org/3/search/tv'

	LinkDiscoverMovie		= 'https://api.themoviedb.org/3/discover/movie'
	LinkDiscoverShow		= 'https://api.themoviedb.org/3/discover/tv'

	LinkRatedMovie			= 'https://api.themoviedb.org/3/movie/top_rated'
	LinkRatedShow			= 'https://api.themoviedb.org/3/tv/top_rated'

	LinkDetailMovie			= 'https://api.themoviedb.org/3/movie/%s'
	LinkDetailMovieImage	= 'https://api.themoviedb.org/3/movie/%s/images'
	LinkDetailSet			= 'https://api.themoviedb.org/3/collection/%s'
	LinkDetailSetImage		= 'https://api.themoviedb.org/3/collection/%s/images'
	LinkDetailShow			= 'https://api.themoviedb.org/3/tv/%s'
	LinkDetailShowImage		= 'https://api.themoviedb.org/3/tv/%s/images'
	LinkDetailSeason		= 'https://api.themoviedb.org/3/tv/%s/season/%d'

	LinkId					= 'https://api.themoviedb.org/3/find/%s'
	LinkIdSet				= 'https://files.tmdb.org/p/exports/collection_ids_%s.json.gz'

	LinkImage				= 'https://image.tmdb.org/t/p/%s%s'

	# https://developers.themoviedb.org/3/movies/get-movie-release-dates
	ReleasePremiere			= 1
	ReleaseLimited			= 2
	ReleaseTheatre			= 3
	ReleaseDigital			= 4
	ReleasePhysical			= 5
	ReleaseTelevision		= 6
	ReleaseLaunch			= [ReleasePhysical, ReleaseDigital, ReleaseTelevision, ReleaseTheatre, ReleaseLimited] # Order matters.
	ReleaseCinema			= [ReleaseTheatre, ReleaseLimited] # Order matters.
	ReleaseHome				= [ReleasePhysical, ReleaseDigital, ReleaseTelevision] # Order matters.
	ReleaseNew				= [ReleasePhysical, ReleaseDigital, ReleaseTelevision, ReleaseTheatre, ReleaseLimited, ReleasePremiere] # Order matters.

	# https://www.themoviedb.org/talk/5e1a60f7459ad6001435e0ae
	SerieDocu				= 0
	SerieNews				= 1
	SerieMini				= 2
	SerieReality			= 3
	SerieScript				= 4
	SerieTalk				= 5
	SerieVideo				= 6
	SerieGeneral			= [SerieScript, SerieMini, SerieDocu, SerieVideo]

	# https://developers.themoviedb.org/3/genres/get-movie-list
	GenreAction				= 28		# Movie: 28 - "Action"
	GenreAdventure			= 12		# Movie: 12 - "Adventure"
	GenreActionAdventure	= 10759		# Show: 10759 - "Action & Adventure"
	GenreAnimation			= 16		# Movie + Show: 16 - "Animation"
	GenreChildren			= 10762		# Show: 10762 - "Kids"
	GenreComedy				= 35		# Movie+Show: 35 - "Comedy"
	GenreCrime				= 80		# Movie+Show: 80 - "Crime"
	GenreDocumentary		= 99		# Movie+Show: 99 - "Documentary"
	GenreDrama				= 18		# Movie+Show: 18 - "Drama"
	GenreFamily				= 10751		# Movie+Show: 10751 - "Family"
	GenreScifi				= 878		# Movie: 878 - "Science Fiction"
	GenreFantasy			= 14		# Movie: 14 - "Fantasy"
	GenreScifiFantasy		= 10765		# Show: 10765 - "Sci-Fi & Fantasy"
	GenreHistory			= 36		# Movie: 36 - "History"
	GenreHorror				= 27		# Movie: 27 - "Horror"
	GenreMusic				= 10402		# Movie: 10402 - "Music"
	GenreMystery			= 9648		# Movie+Show: 9648 - "Mystery"
	GenreRomance			= 10749		# Movie: 10749 - "Romance"
	GenreThriller			= 53		# Movie: 53 - "Thriller"
	GenreWar				= 10752		# Movie: 10752 - "War"
	GenreWarPolitics		= 10768		# Show: 10768 - "War & Politics"
	GenreWestern			= 37		# Movie+Show: 37 - "Western"
	GenreNews				= 10763		# Show: 10763 - "News"
	GenreTalk				= 10767		# Show: 10767 - "Talk"
	GenreReality			= 10764		# Show: 10764 - "Reality"
	GenreSoap				= 10766		# Show: 10766 - "Soap"
	GenreTelevision			= 10770		# Movie: 10770 - "TV Movie"

	Genres					= {
		MetaTools.GenreAction								: GenreAction,
		MetaTools.GenreAdventure							: GenreAdventure,
		(MetaTools.GenreAction, MetaTools.GenreAdventure)	: GenreActionAdventure,
		MetaTools.GenreAnimation							: GenreAnimation,
		MetaTools.GenreChildren								: GenreChildren,
		MetaTools.GenreComedy								: GenreComedy,
		MetaTools.GenreCrime								: GenreCrime,
		MetaTools.GenreDocumentary							: GenreDocumentary,
		MetaTools.GenreDrama								: GenreDrama,
		MetaTools.GenreFamily								: GenreFamily,
		MetaTools.GenreScifi								: GenreScifi,
		MetaTools.GenreFantasy								: GenreFantasy,
		(MetaTools.GenreScifi, MetaTools.GenreFantasy)		: GenreScifiFantasy,
		MetaTools.GenreHistory								: GenreHistory,
		MetaTools.GenreHorror								: GenreHorror,
		MetaTools.GenreMusic								: GenreMusic,
		MetaTools.GenreMystery								: GenreMystery,
		MetaTools.GenreRomance								: GenreRomance,
		MetaTools.GenreThriller								: GenreThriller,
		MetaTools.GenreWar									: GenreWar,
		(MetaTools.GenreWar, MetaTools.GenrePolitics)		: GenreWarPolitics,
		MetaTools.GenreWestern								: GenreWestern,
		MetaTools.GenreNews									: GenreNews,
		MetaTools.GenreTalk									: GenreTalk,
		MetaTools.GenreReality								: GenreReality,
		MetaTools.GenreSoap									: GenreSoap,
		MetaTools.GenreTelevision							: GenreTelevision,
	}
	GenresMulti				= {
		MetaTools.GenreAction								: GenreActionAdventure,
		MetaTools.GenreAdventure							: GenreActionAdventure,
		MetaTools.GenreScifi								: GenreScifiFantasy,
		MetaTools.GenreFantasy								: GenreScifiFantasy,
		MetaTools.GenreWar									: GenreWarPolitics,
		MetaTools.GenrePolitics								: GenreWarPolitics,
	}

	StatusRumored			= 'Rumored'
	StatusPlanned			= 'Planned'
	StatusProduction		= 'In Production'
	StatusPostproduction	= 'Post Production'
	StatusReleased			= 'Released'
	StatusPiloted			= 'Pilot'
	StatusReturning			= 'Returning Series'
	StatusEnded				= 'Ended'
	StatusCanceled			= 'Canceled'

	Status					= {
		MetaTools.StatusRumored			: StatusRumored,
		MetaTools.StatusPlanned			: StatusPlanned,
		MetaTools.StatusProduction		: StatusProduction,
		MetaTools.StatusPostproduction	: StatusPostproduction,
		MetaTools.StatusReleased		: StatusReleased,
		MetaTools.StatusPiloted			: StatusPiloted,
		MetaTools.StatusReturning		: StatusReturning,
		MetaTools.StatusEnded			: StatusEnded,
		MetaTools.StatusCanceled		: StatusCanceled,
	}

	SortRelease				= 'primary_release_date'
	SortTitle				= 'original_title'
	SortPopularity			= 'popularity'
	SortRating				= 'vote_average'
	SortVotes				= 'vote_count'
	SortRevenue				= 'revenue'

	OrderAscending			= 'asc'
	OrderDescending			= 'desc'
	OrderDefault			= {
		SortRelease			: OrderDescending,
		SortTitle			: OrderAscending,
		SortPopularity		: OrderDescending,
		SortRating			: OrderDescending,
		SortVotes			: OrderDescending,
		SortRevenue			: OrderDescending,
	}

	# TMDb does not allow one to specify the number of items to retrieve (eg: in discover()).
	# TMDb uses a fixed limit and then requires paging.
	LimitFixed				= 20

	# If too many appends are added, TMDb returns: "Too many append to response objects: The maximum number of remote calls is 20."
	LimitAppend				= 20

	# USAGE
	# TMDb does not have fixed limits anymore.
	# But they still have soft limits of about 50 requests/sec and 20 connections/IP.
	# https://www.themoviedb.org/talk/6422345a6a34480112ba52fd
	# https://developer.themoviedb.org/docs/rate-limiting
	UsageAuthenticatedRequest		= 50
	UsageAuthenticatedDuration		= 1
	UsageUnauthenticatedRequest		= 50
	UsageUnauthenticatedDuration	= 1

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		MetaProvider.__init__(self, account = Account.instance())

	##############################################################################
	# LINK
	##############################################################################

	@classmethod
	def link(self, media = None, id = None, title = None, year = None, season = None, episode = None, metadata = None, search = False):
		try:
			if metadata:
				if not media:
					if 'tvshowtitle' in metadata:
						if 'episode' in metadata: media = Media.Episode
						elif 'season' in metadata: media = Media.Season
						else: media = Media.Show
					elif 'set' in metadata and not 'collection' in metadata:
						media = Media.Set
					else:
						media = Media.Movie
				if media == Media.Set:
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

			if media == Media.Show:
				episode = None
				season = None
			elif media == Media.Season:
				episode = None

			if id:
				if Media.isSerie(media):
					if not episode is None: return MetaTmdb.LinkEpisode % (id, season, episode)
					elif not season is None: return MetaTmdb.LinkSeason % (id, season)
					else: return MetaTmdb.LinkShow % id
				elif media == Media.Set:
					return MetaTmdb.LinkSet % id
				else:
					return MetaTmdb.LinkMovie % id
			elif search and title:
				query = title
				if year and media == Media.Movie: query += ' ' + str(year)
				link = MetaTmdb.LinkFindShow if Media.isSerie(media) else MetaTmdb.LinkFindSet if media == Media.Set else MetaTmdb.LinkFindMovie
				return link % Networker.linkQuote(data = query, plus = False)
		except: Logger.error()
		return None

	def linkEncode(self, link, query = None, page = None, data = None, increment = True):
		parameters = Networker.linkParameters(link = link)
		link = Networker.linkClean(link = link, parametersStrip = True, headersStrip = True)

		if (page is None or page == 1) and 'page' in parameters and parameters['page']: page = int(parameters['page'])
		if not page is None and increment: page += 1
		if data and 'total_pages' in data and data['total_pages'] < page: return None

		if not query is None: parameters['query'] = query
		if not page is None: parameters['page'] = page

		return Networker.linkCreate(link = link, parameters = parameters, duplicates = False)

	def linkDecode(self, link):
		if link: return Networker.linkParameters(link = link)
		else: return None

	def linkData(self, link = None, query = None, page = None, language = None):
		if link: data = self.linkDecode(link = link)
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

	def _retrieve(self, link, linkExtra = None, query = None, media = None, page = 1, language = None, data = None):
		results = None
		try:
			if not linkExtra: linkExtra = link
			parameters = self.linkData(link = linkExtra, query = query, page = page, language = language)
			if data:
				if not parameters: parameters = {}
				parameters.update(data)
			data = self._request(method = Networker.MethodGet, link = link, data = parameters)
			if data: results = self.items(media = media, data = data, link = linkExtra, query = query, page = page)
		except: Logger.error()
		return results

	def _request(self, link, data = None, method = None, cache = None, lock = False):
		try:
			if lock: self._lock(limit = lock)
			if cache is None: return self._requestData(link = link, data = data, method = method)
			else: return self._cache(timeout = cache, function = self._requestData, link = link, data = data, method = method)
		finally:
			if lock: self._unlock(limit = lock)

	def _requestData(self, link, data = None, method = None):
		if not data: data = {}
		if method is None: method = Networker.MethodGet

		data = {k : v for k, v in data.items() if not v is None}
		data['api_key'] = self.account().key()

		values = data.get('append_to_response')
		if Tools.isArray(values): data['append_to_response'] = ','.join(values)

		values = data.get('include_image_language')
		if Tools.isArray(values): data['include_image_language'] = ','.join(values)

		self._usageUpdate()
		networker = Networker()
		result = networker.requestJson(method = method, link = link, data = data)

		error = networker.responseErrorType()
		if error and error in Networker.ErrorServer: self._errorUpdate()

		return result

	##############################################################################
	# ITEM
	##############################################################################

	def item(self, media, item):
		if not item: return None
		result = {}

		result['media'] = media

		ids = {}
		tmdb = item.get('id')
		if tmdb: result['tmdb'] = ids['tmdb'] = str(tmdb)
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
				year = Regex.extract(data = premiered, expression = '(\d{4})-', group = 1)
				if year: result['year'] = int(year)

				result['premiered'] = premiered
				result['time'] = {MetaTools.TimePremiere : Time.timestamp(premiered, format = Time.FormatDate, utc = True)}

		status = item.get('status')
		if status:
			status = self._convertStatus(status = status, inverse = True)
			if status: result['status'] = status

		genre = item.get('genre_ids')
		if not genre:
			genre = item.get('genres')
			if genre: genre = [i.get('id') for i in genre]
		if genre:
			genre = self._convertGenre(genre = genre, inverse = True)
			if genre: result['genre'] = genre

		language = item.get('original_language')
		if language: result['language'] = Language.codes([language])

		country = item.get('origin_country')
		if country:
			if not Tools.isArray(country): country = [country]
			result['country'] = Country.codes(country)

		rating = item.get('vote_average')
		votes = item.get('vote_count')
		if not rating is None or not votes is None:
			value = {}
			if not rating is None:
				if not 'voting' in value: value['voting'] = {}
				result['rating'] = value['voting']['rating'] = rating
			if not votes is None:
				if not 'voting' in value: value['voting'] = {}
				result['votes'] = value['voting']['votes'] = votes
			result.update({'temp' : {'tmdb' : value}})

		return result

	def items(self, media = None, items = None, data = None, link = None, query = None, page = None, increment = True):
		if items is None and data:
			for i in ['results', 'items', 'movie_results', 'tv_results', 'tv_season_results', 'tv_episode_results']:
				if i in data:
					items = data[i]
					break
		if not items: return None

		result = []
		for item in items:
			try:
				item = self.item(media = media, item = item)
				if item: result.append(item)
			except: Logger.error()

		return result

	##############################################################################
	# ID
	##############################################################################

	def _id(self, media, imdb = None, tvdb = None):
		source = None
		link = MetaTmdb.LinkId

		if imdb:
			link = link % imdb
			source = 'imdb_id'
		elif tvdb and Media.isSerie(media):
			link = link % tvdb
			source = 'tvdb_id'
		else:
			return None

		data = self._request(method = Networker.MethodGet, link = link, data = {'external_source' : source})
		if data:
			if media == Media.Show: result = 'tv_results'
			elif media == Media.Season: result = 'tv_season_results'
			elif media == Media.Episode: result = 'tv_episode_results'
			else: result = 'movie_results'
			try: return data[result][0].get('id')
			except: pass

		return None

	def _idMovie(self, imdb = None, tvdb = None):
		return self._id(media = Media.Movie, imdb = imdb, tvdb = tvdb)

	def _idShow(self, imdb = None, tvdb = None):
		return self._id(media = Media.Show, imdb = imdb, tvdb = tvdb)

	def _idSeason(self, tvdb = None):
		return self._id(media = Media.Season, imdb = imdb, tvdb = tvdb)

	def _idEpisode(self, imdb = None, tvdb = None):
		return self._id(media = Media.Episode, imdb = imdb, tvdb = tvdb)

	##############################################################################
	# EXTRACT
	##############################################################################

	def _extractType(self, item):
		# It seems that TMDb recently added the "episode_type" attribute.
		# But it is not documented and the forums do not really list the different values, except for "finale".
		# Add these, since for future episodes, TMDb has the type, while Trakt has not, since they probably have not scraped TMDb yet.

		try:
			type = item.get('episode_type')
			if type:
				if Tools.isArray(type): type = ' '.join(type)
				type = type.lower()

				result = []

				if 'premiere' in type: result.append(Media.Premiere)
				elif 'finale' in type: result.append(Media.Finale)
				elif 'standard' in type: result.append(Media.Standard)

				if 'mid' in type: result.append(Media.Middle)
				elif 'season' in type: result.append(Media.Inner)
				elif 'serie' in type or 'show' in type: result.append(Media.Outer)

				if result: return self.mMetatools.mergeType(values = result, season = item.get('season_number'), episode = item.get('episode_number'))
		except: Logger.error()
		return None

	##############################################################################
	# LIMIT
	##############################################################################

	@classmethod
	def limit(self, pages = None):
		if pages: return pages * MetaTmdb.LimitFixed
		else: return MetaTmdb.LimitFixed

	##############################################################################
	# LIST
	##############################################################################

	def list(self, id = None, language = None, link = None):
		if not link: link = MetaTmdb.LinkList % id
		return self._retrieve(link = link, linkExtra = link, language = language)

	##############################################################################
	# SEARCH
	##############################################################################

	def search(self, media, query = None, page = 1, language = None):
		if Media.isMovie(media): return self.searchMovie(query = query, page = page, language = language)
		elif Media.isSet(media): return self.searchSet(query = query, page = page, language = language)
		elif Media.isSerie(media): return self.searchShow(query = query, page = page, language = language)
		else: return None

	def searchMovie(self, query = None, page = 1, language = None):
		return self._retrieve(media = Media.Movie, link = MetaTmdb.LinkSearchMovie, query = query, page = page, language = language)

	def searchSet(self, query = None, page = 1, language = None):
		return self._retrieve(media = Media.Set, link = MetaTmdb.LinkSearchSet, query = query, page = page, language = language)

	def searchShow(self, query = None, page = 1, language = None, link = None):
		return self._retrieve(media = Media.Show, link = MetaTmdb.LinkSearchShow, query = query, page = page, language = language)

	##############################################################################
	# DISCOVER
	##############################################################################

	# niche: not supported yet, only here for MetaManager.arrivals() compatibility.
	# year: integer = single year
	# date: integer = single minimum timestamp | tuple = range of timestamps (from and to) | tuple = if one value is None, ignore that and only use upper or lower date.
	# rating: integer = single minimum rating | tuple = range of rating (from and to) | tuple = if one value is None, ignore that and only use upper or lower rating.
	# votes: integer = single minimum vote | tuple = range of votes (from and to) | tuple = if one value is None, ignore that and only use upper or lower votes.
	def discover(self, media, niche = None, release = None, serie = None, year = None, date = None, genre = None, language = None, country = None, rating = None, votes = None, sort = None, order = None, page = None, limit = None, threaded = None):
		if limit and limit > MetaTmdb.LimitFixed:
			def _discover(result, page, **parameters):
				data = self.discover(page = page, **parameters)
				if data: result[page - 1] = data

			pages = Math.roundUp(limit / float(MetaTmdb.LimitFixed))
			result = [None] * pages

			execution = []
			for i in range(pages):
				execution.append({
					'result' : result,
					'page' : i + 1,
					'media' : media,
					'niche' : niche,
					'release' : release,
					'serie' : serie,
					'year' : year,
					'date' : date,
					'genre' : genre,
					'country' : country,
					'language' : language,
					'rating' : rating,
					'votes' : votes,
					'sort' : sort,
					'order' : order,
				})

			if threaded:
				threads = [Pool.thread(target = _discover, kwargs = i, start = True) for i in execution]
				[thread.join() for thread in threads]
			else:
				[_discover(**i) for i in execution]

			result = Tools.listFlatten([i for i in result if i])
			return result if result else None

		data = {}
		if page is None: page = 1
		movie = Media.isFilm(media)
		show = Media.isSerie(media)

		if movie and release:
			if Tools.isArray(release): release = '|'.join([str(i) for i in release])
			data['with_release_type'] = release

		if show and serie:
			if serie is True: serie = MetaTmdb.SerieGeneral
			if Tools.isArray(serie): serie = '|'.join([str(i) for i in serie])
			data['with_type'] = serie

		if year:
			if Tools.isArray(year):
				if movie:
					# Retrieving home releases often returns decad old movies.
					# This is because those old movies get a new 4k/BluRay release, which gives them a new "release_date".
					# Also add "primary_release_date" which is applied to the oldest date of the movie, to filter out those old movies.
					# https://www.themoviedb.org/talk/5a87b514c3a3682dbf04eca7
					data['primary_release_date.gte'] = '%d-01-01' % year[0]
					data['primary_release_date.lte'] = '%d-12-31' % year[1]
			else:
				data['first_air_date_year' if show else 'year'] = year

		if date:
			# NB: Use "primary_release_date" instead of "release_date".
			# Otherwise when returning the latests digital/physical releases, old items are returned (sometimes 20+ years old).
			# Update: Maybe this was only a temporary TMDb issue. When using "primary_release_date", the digital/physical release date is ignored, that is, titles released later than "primary_release_date.lte" are still returned.
			# Update (2025-03): Check the new primary_release_date above in "year".
			dateStart = None
			dateEnd = None
			if Tools.isArray(date):
				dateStart = date[0]
				dateEnd = date[1]
			else:
				dateStart = date
			if dateStart and Tools.isInteger(dateStart): dateStart = Time.format(dateStart, format = Time.FormatDate)
			if dateEnd and Tools.isInteger(dateEnd): dateEnd = Time.format(dateEnd, format = Time.FormatDate)

			if movie:
				if dateStart: data['release_date.gte'] = dateStart
				if dateEnd: data['release_date.lte'] = dateEnd
			elif show:
				if dateStart: data['first_air_date.gte'] = dateStart
				if dateEnd: data['first_air_date.lte'] = dateEnd
				data['include_null_first_air_dates'] = 'false'

		if genre:
			if not Tools.isArray(genre): genre = [genre]
			genreInclude = []
			genreExclude = []
			for i in genre:
				if Tools.isString(i):
					i = MetaTmdb.GenresMulti.get(i, i)
					if Tools.isString(i): i = self._convertGenre(genre = i)
				if i < 0: genreExclude.append(str(-1 * i))
				else: genreInclude.append(str(i))
			if genreInclude: data['with_genres'] = ','.join(genreInclude)
			if genreExclude: data['without_genres'] = ','.join(genreExclude)

		if language:
			if not Tools.isArray(language): language = [language]
			if not Language.EnglishCode in language: language.insert(0, Language.EnglishCode)
			data['with_original_language'] = '|'.join(language)

		if country or release: # Always add if release was added.
			# NB: Add a region, otherwise the API call returns titles that were only theatrically released and were not digitially/physically released yet.
			if not country: country = ['US', 'GB', 'CA', 'DE', 'FR', 'NL', 'PL', 'SE', 'NO', 'FI', 'ES', 'PT', 'IT', 'JP', 'KO', 'AU', 'NZ', 'ZA', 'BR', 'MX']
			if Tools.isArray(country): country = '|'.join([str(i) for i in country])
			data['country'] = country

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

		if sort:
			if not order: order = MetaTmdb.OrderDefault[sort]
			data['sort_by'] = sort + '.' + order

		return self._retrieve(media = media, link = MetaTmdb.LinkDiscoverShow if Media.isSerie(media) else MetaTmdb.LinkDiscoverMovie, data = data, page = page, language = language)

	def discoverMovie(self, release = None, year = None, date = None, genre = None, language = None, country = None, rating = None, votes = None, sort = None, order = None, page = None, limit = None, threaded = None):
		return self.discover(media = Media.Movie, release = release, year = year, date = date, genre = genre, language = language, country = country, rating = rating, votes = votes, sort = sort, order = order, page = page, limit = limit, threaded = threaded)

	def discoverShow(self, release = None, year = None, date = None, genre = None, language = None, country = None, rating = None, votes = None, sort = None, order = None, link = None):
		return self.discover(media = Media.Show, release = release, year = year, date = date, genre = genre, language = language, country = country, rating = rating, votes = votes, sort = sort, order = order, page = page, limit = limit, threaded = threaded)

	def discoverSet(self):
		result = None
		try:
			link = MetaTmdb.LinkIdSet % Time.past(days = 1, format = '%m_%d_%Y')
			data = Networker().requestData(link = link)
			if data:
				data = Compressor.gzipDecompress(data = data)
				if data:
					data = Converter.unicode(data)
					if data:
						data = data.strip()
						data = data.replace('\n', ',\n')
						data = data.strip('\n').strip(',').strip('\n')
						data = Converter.jsonFrom('[' + data + ']')
						if data:
							result = [{
								'media' : Media.Set,
								'id'	: {'tmdb' : i.get('id')},
								'tmdb' : i.get('id'),
								'title' : i.get('name'),
							} for i in data]
		except: Logger.error()
		return result

	##############################################################################
	# RATED
	##############################################################################

	def ratedMovie(self, page = 1, language = None, link = None):
		return self._retrieve(link = MetaTmdb.LinkRatedMovie, linkExtra = link, page = page, language = language)

	def ratedShow(self, page = 1, language = None, link = None):
		return self._retrieve(link = MetaTmdb.LinkRatedShow, linkExtra = link, page = page, language = language)

	##############################################################################
	# METADATA
	##############################################################################

	# quick = True: make less requests by combining subrequests, but less accurate images might be returned.
	def metadataMovie(self, id = None, tmdb = None, imdb = None, language = None, quick = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			if not id: id = tmdb or imdb
			if id:
				requests = []
				if quick:
					requests.append({'id' : 'movie', 'parameters' : {'link' : MetaTmdb.LinkDetailMovie % id, 'data' : {'append_to_response' : ['credits', 'release_dates', 'external_ids', 'images'], 'language' : language, 'include_image_language' : self._metadataImageLanguage(language = language)}, 'cache' : cache}})
				else:
					# Images could be retrieved using "append_to_response", but they are filtered according to the "language" parameter used for the metadata.
					# One could add the "include_image_language" parameter (eg: include_image_language=en,fr,null), but there is no wildcard to return images for all languages.
					# Even if we append all language codes to the request, TMDb seems to only use the first 4 ones and ignore the rest.
					# So currently the only option is to retrieve images in a separate request.
					#	https://developer.themoviedb.org/docs/image-languages
					#	https://www.themoviedb.org/talk/5aa948870e0a263dc10354db

					requests.append({'id' : 'movie', 'parameters' : {'link' : MetaTmdb.LinkDetailMovie % id, 'data' : {'append_to_response' : ['credits', 'release_dates', 'external_ids'], 'language' : language}, 'cache' : cache}})

					# Update: Sometimes there are no images in English or Null, only in another language.
					# Therefore do not add the language to the image requests, but instead retrieve images in all languages.
					#	https://www.themoviedb.org/movie/1369241-el-salto/images/posters
					#requests.append({'id' : 'image', 'parameters' : {'link' : MetaTmdb.LinkDetailMovieImage % id, 'data' : {'include_image_language' : self._metadataImageLanguage(language = language)}, 'cache' : cache}})
					requests.append({'id' : 'image', 'parameters' : {'link' : MetaTmdb.LinkDetailMovieImage % id, 'cache' : cache}})
				data = self._execute(requests = requests, threaded = threaded)

				if data:
					dataMovie = data.get('movie')
					dataImage = data.get('image') or (dataMovie or {}).get('images')
					if dataMovie is False or dataImage is False: complete = False

					if dataMovie or dataImage:
						result = {}

						if 'title' in dataMovie and 'id' in dataMovie:
							result['media'] = Media.Movie

							ids = {}
							external = dataMovie.get('external_ids') or {}
							tmdb = dataMovie.get('id')
							if tmdb: ids['tmdb'] = str(tmdb)
							imdb = dataMovie.get('imdb_id')
							if imdb: ids['imdb'] = str(imdb)
							else:
								imdb = external.get('imdb_id')
								if imdb: ids['imdb'] = str(imdb)
							tvdb = external.get('tvdb_id')
							if tvdb: ids['tvdb'] = str(tvdb)
							if ids: result['id'] = ids

							title = dataMovie.get('title')
							if title: result['title'] = Networker.htmlDecode(title)

							originaltitle = dataMovie.get('original_title')
							if originaltitle: result['originaltitle'] = Networker.htmlDecode(originaltitle)

							tagline = dataMovie.get('tagline')
							if tagline: result['tagline'] = Networker.htmlDecode(tagline)

							plot = dataMovie.get('overview')
							if plot: result['plot'] = Networker.htmlDecode(plot)

							premiered = dataMovie.get('release_date')
							if premiered:
								premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
								if premiered:
									result['premiered'] = premiered
									year = Regex.extract(data = premiered, expression = '(\d{4})-', group = 1)
									if year: result['year'] = int(year)

							genre = dataMovie.get('genres')
							if genre: result['genre'] = MetaTmdb._convertGenre(genre = [i['id'] for i in genre], inverse = True)

							rating = dataMovie.get('vote_average')
							if not rating is None: result['rating'] = rating

							votes = dataMovie.get('vote_count')
							if not votes is None: result['votes'] = votes

							duration = dataMovie.get('runtime')
							if not duration is None: result['duration'] = duration * 60

							status = dataMovie.get('status')
							if status: result['status'] = MetaTmdb._convertStatus(status = status, inverse = True)

							studio = dataMovie.get('production_companies')
							if studio: result['studio'] = [i['name'] for i in studio]

							country = dataMovie.get('production_countries')
							if country: result['country'] = Country.codes([i['iso_3166_1'].lower() for i in country])

							languages = dataMovie.get('spoken_languages')
							if languages: result['language'] = Language.codes([i['iso_639_1'].lower() for i in languages])
							languages = dataMovie.get('original_language')
							if languages:
								# TMDb does not have a valid order for spoken_languages.
								# Eg: GoodFellas (1990): spoken_languages = ['it', 'en'], original_language = 'en'
								languages = Language.codes([languages])
								if languages:
									if 'language' in result: result['language'] = Tools.listUnique(languages + result['language'])
									else: result['language'] = Tools.listUnique(languages)

							country = dataMovie.get('origin_country')
							if country:
								if not Tools.isArray(country): country = [country]
								result['country'] = Country.codes(country)

							homepage = dataMovie.get('homepage')
							if homepage: result['homepage'] = homepage

							finance = {}
							budget = dataMovie.get('budget')
							if budget: finance['budget'] = budget
							revenue = dataMovie.get('revenue')
							if revenue: finance['revenue'] = revenue
							if finance:
								if 'budget' in finance and 'revenue' in finance: finance['profit'] = finance['revenue'] - finance['budget']
								result['finance'] = finance

							dataCollection = dataMovie.get('belongs_to_collection')
							if dataCollection:
								collection = {}
								collectionId = dataCollection.get('id')
								if collectionId:
									collectionId = str(collectionId)
									collection['tmdb'] = collectionId
									collection['id'] = {'tmdb' : collectionId}
								collectionTitle = dataCollection.get('name')
								if collectionTitle: collection['title'] = Regex.replace(data = Networker.htmlDecode(collectionTitle), expression = '\s+', replacement = ' ', all = True) # Sometimes TMDb has 2 spaces between the title and the "Collection" part.

								if collection:
									collectionImage = {}
									collectionPoster = dataCollection.get('poster_path')
									if collectionPoster: collectionImage[MetaImage.TypePoster] = [self._metadataImage(type = MetaImage.TypePoster, path = collectionPoster)]
									collectionFanart = dataCollection.get('backdrop_path')
									if collectionFanart: collectionImage[MetaImage.TypeFanart] = [self._metadataImage(type = MetaImage.TypeFanart, path = collectionFanart)]

									collection[MetaImage.Attribute] = collectionImage
									result['collection'] = collection

									# For Kodi.
									#if collection['id']: result['setid'] = collection['id'] # This seems to be the local DB ID for the set (in the Kodi info dialog there is a special button that redirects to the local library set menu).
									if collection['title']: result['set'] = collection['title']

						try:
							if 'credits' in dataMovie:
								dataPeople = dataMovie['credits']
								if dataPeople:
									if 'crew' in dataPeople:
										dataCrew = dataPeople['crew']
										if dataCrew:
											director = self._metadataDirector(data = dataCrew)
											if director: result['director'] = director

											writer = self._metadataWriter(data = dataCrew)
											if writer: result['writer'] = writer

									if 'cast' in dataPeople:
										dataCast = dataPeople['cast']
										if dataCast:
											cast = []
											for i in dataCast:
												if 'character' in i and i['character']: character = i['character']
												else: character = None
												if 'order' in i: order = i['order']
												else: order = None
												if 'profile_path' in i and i['profile_path']: thumbnail = self._metadataImage(type = MetaImage.TypePhoto, path = i['profile_path'])
												else: thumbnail = None
												cast.append({'name' : i['name'], 'role' : character, 'order' : order, 'thumbnail' : thumbnail})
											if cast: result['cast'] = cast
						except: Logger.error()

						try:
							if dataImage or dataMovie:
								images = {i : [] for i in MetaImage.Types}
								poster = [[], []]
								keyart = [[], []]
								fanart = [[], []]
								landscape = [[], []]

								if dataImage:
									entries = (
										('posters', MetaImage.TypePoster),
										('backdrops', MetaImage.TypeFanart),
										('logos', MetaImage.TypeClearlogo),
									)
									for entry in entries:
										try:
											if entry[0] in dataImage:
												indexed = 0
												for i in dataImage[entry[0]]:
													indexed += 1
													index = 99999999 - indexed
													vote = i.get('vote_average')
													vote = float(vote) if vote else 0
													sort = {
														MetaImage.SortIndex : index,
														MetaImage.SortVote : vote,
														MetaImage.SortVoteIndex : [vote, index],
													}
													image = MetaImage.create(link = self._metadataImage(type = entry[1], path = i.get('file_path')), provider = MetaImage.ProviderTmdb, language = i.get('iso_639_1'), sort = sort)
													if image:
														if entry[1] == MetaImage.TypePoster:
															if image[MetaImage.AttributeLanguage]:
																poster[0].append(image)
																keyart[1].append(image)
															else:
																poster[1].append(image)
																keyart[0].append(image)
														elif entry[1] == MetaImage.TypeFanart:
															if image[MetaImage.AttributeLanguage]:
																landscape[0].append(image)
																fanart[1].append(image)
															else:
																landscape[1].append(image)
																fanart[0].append(image)
														else:
															images[entry[1]].append(image)
										except: Logger.error()

								# Update (2025-09): Not sure if this is a new change to the API, a temporary issues, or always was there.
								# For some seasons, the "images" dict returned by TMDb does not contain any images.
								# However, there might still be a single image stored as a separate path attribute. Use these images as a fallback.
								# This has only been observed with the season metadata, but also do this here, in case some movies have the same problem.
								if dataMovie:
									entries = (
										('poster_path', MetaImage.TypePoster),
										('backdrop_path', MetaImage.TypeFanart),
										('logo_path', MetaImage.TypeClearlogo),
										('still_path', MetaImage.TypeThumb),
									)
									for entry in entries:
										try:
											if entry[0] in dataMovie:
												image = MetaImage.create(link = self._metadataImage(type = entry[1], path = dataMovie[entry[0]]), provider = MetaImage.ProviderTmdb)
												if image:
													if entry[1] == MetaImage.TypePoster:
														if image[MetaImage.AttributeLanguage]:
															if not poster[0] and not poster[1]: poster[0].append(image)
															if not keyart[0] and not keyart[1]: keyart[1].append(image)
														else:
															if not poster[0] and not poster[1]: poster[1].append(image)
															if not keyart[0] and not keyart[1]: keyart[0].append(image)
													elif entry[1] == MetaImage.TypeFanart:
														if image[MetaImage.AttributeLanguage]:
															if not landscape[0] and not landscape[1]: landscape[0].append(image)
															if not fanart[0] and not fanart[1]: fanart[1].append(image)
														else:
															if not landscape[0] and not landscape[1]: landscape[1].append(image)
															if not fanart[0] and not fanart[1]: fanart[0].append(image)
													else:
														if not images[entry[1]]: images[entry[1]].append(image)
										except: Logger.error()

								images[MetaImage.TypePoster] = poster[0] + poster[1]
								images[MetaImage.TypeKeyart] = keyart[0] + keyart[1]
								images[MetaImage.TypeFanart] = fanart[0] + fanart[1]
								images[MetaImage.TypeLandscape] = landscape[0] + landscape[1]
								if images: result[MetaImage.Attribute] = images
						except: Logger.error()

						try:
							# NB: Make sure the order and approach is the same as for Trakt release dates.
							if 'release_dates' in dataMovie:
								dataRelease = dataMovie['release_dates']
								try: dataRelease = dataRelease['results']
								except: pass
								if dataRelease:
									release = []
									types = {
										1 : MetaTools.TimePremiere,
										2 : MetaTools.TimeLimited,
										3 : MetaTools.TimeTheatrical,
										4 : MetaTools.TimeDigital,
										5 : MetaTools.TimePhysical,
										6 : MetaTools.TimeTelevision,
									}
									for i in dataRelease:
										releaseDate = i.get('release_dates')
										if releaseDate:
											releaseCountry = i.get('iso_3166_1')
											releaseCountry = releaseCountry.lower() if releaseCountry else None
											for j in releaseDate:
												releaseLanguage = j.get('iso_639_1')
												releaseLanguage = releaseLanguage.lower() if releaseLanguage else None
												release.append({
													'type'			: types.get(j.get('type')) or MetaTools.TimeUnknown,
													'time'			: Time.timestamp(fixedTime = j.get('release_date'), iso = True),
													'country'		: releaseCountry,
													'language'		: releaseLanguage,
													'certificate'	: data.get('certification') or None,
													'desription'	: data.get('note') or None,
												})
									if release:
										result['time'] = self.mMetatools.timeGenerate(release = release, metadata = result)
										if not 'temp' in result: result['temp'] = {}
										if not 'tmdb' in result['temp']: result['temp']['tmdb'] = {}
										result['temp']['tmdb']['release'] = release
						except: Logger.error()
		except: Logger.error()
		return {'provider' : self.id(), 'complete' : complete, 'data' : result} if detail else result

	# quick = True: make less requests by combining subrequests, but less accurate images might be returned.
	def metadataSet(self, id = None, tmdb = None, imdb = None, language = None, quick = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			if not id: id = tmdb or imdb
			if id:
				requests = []
				if quick:
					requests.append({'id' : 'set', 'parameters' : {'link' : MetaTmdb.LinkDetailSet % id, 'data' : {'append_to_response' : ['images'], 'language' : language, 'include_image_language' : self._metadataImageLanguage(language = language)}, 'cache' : cache}})
				else:
					requests.append({'id' : 'set', 'parameters' : {'link' : MetaTmdb.LinkDetailSet % id, 'data' : {'language' : language}, 'cache' : cache}})
					requests.append({'id' : 'image', 'parameters' : {'link' : MetaTmdb.LinkDetailSetImage % id, 'cache' : cache}})
				data = self._execute(requests = requests, threaded = threaded)

				if data:
					dataSet = data.get('set')
					dataImage = data.get('image') or (dataSet or {}).get('images')
					dataParts = dataSet['parts'] if dataSet and 'parts' in dataSet else None
					if dataSet is False or dataImage is False or not dataParts: complete = False

					if dataSet or dataImage:
						result = {}

						if 'name' in dataSet and 'id' in dataSet:
							result['media'] = Media.Movie

							ids = {}
							tmdb = dataSet.get('id')
							if tmdb: result['tmdb'] = ids['tmdb'] = str(tmdb)
							if ids: result['id'] = ids

							title = dataSet.get('name')
							if title:
								title = Networker.htmlDecode(title)
								result['set'] = result['title'] = result['originaltitle'] = title

							plot = dataSet.get('overview')
							if plot: result['plot'] = result['setoverview'] = Networker.htmlDecode(plot)

							parts = []
							for part in dataParts:
								resultPart = {'media' : Media.Movie}

								ids = {}
								tmdb = part.get('id')
								if tmdb: ids['tmdb'] = resultPart['tmdb'] = str(tmdb)
								if ids: resultPart['id'] = ids

								title = part.get('title')
								if title: resultPart['title'] = Networker.htmlDecode(title)

								originaltitle = part.get('original_title')
								if originaltitle: resultPart['originaltitle'] = Networker.htmlDecode(originaltitle)

								plot = part.get('overview')
								if plot: resultPart['plot'] = Networker.htmlDecode(plot)

								premiered = part.get('release_date')
								if premiered:
									premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1, cache = True)
									if premiered:
										year = Regex.extract(data = premiered, expression = '(\d{4})-', group = 1, cache = True)
										if year: resultPart['year'] = int(year)
										resultPart['premiered'] = premiered
										resultPart['time'] = {MetaTools.TimePremiere : Time.timestamp(premiered, format = Time.FormatDate, utc = True)}

								genre = part.get('genre_ids')
								if not genre:
									genre = part.get('genres')
									if genre: genre = [i.get('id') for i in genre]
								if genre:
									genre = self._convertGenre(genre = genre, inverse = True)
									if genre: resultPart['genre'] = genre

								rating = part.get('vote_average')
								if not rating is None: resultPart['rating'] = rating

								votes = part.get('vote_count')
								if not votes is None: resultPart['votes'] = votes

								languages = part.get('spoken_languages')
								if languages: resultPart['language'] = Language.codes([i['iso_639_1'].lower() for i in languages])
								languages = part.get('original_language')
								if languages:
									languages = Language.codes([languages])
									if languages:
										if 'language' in resultPart: resultPart['language'] = Tools.listUnique(languages + resultPart['language'])
										else: resultPart['language'] = Tools.listUnique(languages)

								country = part.get('origin_country')
								if country:
									if not Tools.isArray(country): country = [country]
									resultPart['country'] = Country.codes(country)

								resultPart['adult'] = part.get('adult')

								parts.append(resultPart)
							parts = Tools.listSort(parts, key = lambda i : (i.get('time') or {}).get(MetaTools.TimePremiere, 9999999999))

							values = [i.get('year') for i in parts]
							if values:
								values = [i for i in values if i]
								if values:
									year = min(values)
									if year: result['year'] = year

							values = [i.get('premiered') for i in parts]
							if values:
								values = [i for i in values if i]
								if values:
									premiered = min(values, key = lambda i : Time.integer(i))
									if premiered: result['premiered'] = premiered

							values = []
							for i in parts:
								genre = i.get('genre')
								if genre: values.extend(genre)
							if values:
								genre = Tools.listUnique([i for i in values if i])
								if values: result['genre'] = genre

							voting = self.mMetatools.votingAverageWeighted(metadata = parts, maximum = True)
							if voting:
								result['rating'] = Math.round(voting['rating'], places = 3) # Round to save storage space in the cache.
								result['votes'] = voting['votes']

							values = []
							for i in parts:
								language = i.get('language')
								if language: values.extend(language)
							if values:
								language = Tools.listUnique([i for i in values if i])
								if values: result['language'] = language

							values = []
							for i in parts:
								country = i.get('country')
								if country: values.extend(country)
							if values:
								country = Tools.listUnique([i for i in values if i])
								if values: result['country'] = country

							adult = False
							for part in dataParts:
								if part.get('adult'):
									adult = True
									break
							result['adult'] = adult

							result['part'] = parts

						try:
							if dataImage or dataSet:
								images = {i : [] for i in MetaImage.Types}
								poster = [[], []]
								keyart = [[], []]
								fanart = [[], []]
								landscape = [[], []]

								if dataImage:
									entries = (
										('posters', MetaImage.TypePoster),
										('backdrops', MetaImage.TypeFanart),
										('logos', MetaImage.TypeClearlogo),
									)
									for entry in entries:
										try:
											if entry[0] in dataImage:
												indexed = 0
												for i in dataImage[entry[0]]:
													indexed += 1
													index = 99999999 - indexed
													vote = i.get('vote_average')
													vote = float(vote) if vote else 0
													sort = {
														MetaImage.SortIndex : index,
														MetaImage.SortVote : vote,
														MetaImage.SortVoteIndex : [vote, index],
													}
													image = MetaImage.create(link = self._metadataImage(type = entry[1], path = i.get('file_path')), provider = MetaImage.ProviderTmdb, language = i.get('iso_639_1'), sort = sort)
													if image:
														if entry[1] == MetaImage.TypePoster:
															if image[MetaImage.AttributeLanguage]:
																poster[0].append(image)
																keyart[1].append(image)
															else:
																poster[1].append(image)
																keyart[0].append(image)
														elif entry[1] == MetaImage.TypeFanart:
															if image[MetaImage.AttributeLanguage]:
																landscape[0].append(image)
																fanart[1].append(image)
															else:
																landscape[1].append(image)
																fanart[0].append(image)
														else:
															images[entry[1]].append(image)
										except: Logger.error()

								# Update (2025-09): Not sure if this is a new change to the API, a temporary issues, or always was there.
								# For some seasons, the "images" dict returned by TMDb does not contain any images.
								# However, there might still be a single image stored as a separate path attribute. Use these images as a fallback.
								# This has only been observed with the season metadata, but also do this here, in case some sets have the same problem.
								if dataSet:
									entries = (
										('poster_path', MetaImage.TypePoster),
										('backdrop_path', MetaImage.TypeFanart),
										('logo_path', MetaImage.TypeClearlogo),
										('still_path', MetaImage.TypeThumb),
									)
									for entry in entries:
										try:
											if entry[0] in dataSet:
												image = MetaImage.create(link = self._metadataImage(type = entry[1], path = dataSet[entry[0]]), provider = MetaImage.ProviderTmdb)
												if image:
													if entry[1] == MetaImage.TypePoster:
														if image[MetaImage.AttributeLanguage]:
															if not poster[0] and not poster[1]: poster[0].append(image)
															if not keyart[0] and not keyart[1]: keyart[1].append(image)
														else:
															if not poster[0] and not poster[1]: poster[1].append(image)
															if not keyart[0] and not keyart[1]: keyart[0].append(image)
													elif entry[1] == MetaImage.TypeFanart:
														if image[MetaImage.AttributeLanguage]:
															if not landscape[0] and not landscape[1]: landscape[0].append(image)
															if not fanart[0] and not fanart[1]: fanart[1].append(image)
														else:
															if not landscape[0] and not landscape[1]: landscape[1].append(image)
															if not fanart[0] and not fanart[1]: fanart[0].append(image)
													else:
														if not images[entry[1]]: images[entry[1]].append(image)
										except: Logger.error()

								images[MetaImage.TypePoster] = poster[0] + poster[1]
								images[MetaImage.TypeKeyart] = keyart[0] + keyart[1]
								images[MetaImage.TypeFanart] = fanart[0] + fanart[1]
								images[MetaImage.TypeLandscape] = landscape[0] + landscape[1]
								if images: result[MetaImage.Attribute] = images
						except: Logger.error()
		except: Logger.error()
		return {'provider' : self.id(), 'complete' : complete, 'data' : result} if detail else result

	def metadataShow(self, id = None, tmdb = None, language = None, quick = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			if not id: id = tmdb
			if id: # Shows do not work with IMDb IDs like movies do.
				requests = []
				if quick:
					requests.append({'id' : 'show', 'parameters' : {'link' : MetaTmdb.LinkDetailShow % id, 'data' : {'id' : id, 'append_to_response' : ['external_ids', 'aggregate_credits', 'images'], 'language' : language, 'include_image_language' : self._metadataImageLanguage(language = language)}, 'cache' : cache}})
				else:
					# Images could be retrieved using "append_to_response", but they are filtered according to the "language" parameter used for the metadata.
					# One could add the "include_image_language" parameter (eg: include_image_language=en,fr,null), but there is no wildcard to return images for all languages.
					# Even if we append all language codes to the request, TMDb seems to only use the first 4 ones and ignore the rest.
					# So currently the only option is to retrieve images in a separate request.
					#	https://developer.themoviedb.org/docs/image-languages
					#	https://www.themoviedb.org/talk/5aa948870e0a263dc10354db
					requests.append({'id' : 'show', 'parameters' : {'link' : MetaTmdb.LinkDetailShow % id, 'data' : {'id' : id, 'append_to_response' : ['external_ids', 'aggregate_credits'], 'language' : language}, 'cache' : cache}})

					# Update: Sometimes there are no images in English or Null, only in another language.
					# Therefore do not add the language to the image requests, but instead retrieve images in all languages.
					#	https://www.themoviedb.org/tv/231452-angela/images/posters
					# read more under metadataMovie().
					# Make a second requests for images, since sometimes Trakt does not have the IMDb and TVDb IDs (or has the wrong IDs), especially for new releases.
					# Then no images might show in the Arrivals menu, or some other fallback image like a banner or fanart.
					#requests.append({'id' : 'image', 'parameters' : {'link' : MetaTmdb.LinkDetailShowImage % id, 'data' : {'include_image_language' : self._metadataImageLanguage(language = language)}, 'cache' : cache}})
					requests.append({'id' : 'image', 'parameters' : {'link' : MetaTmdb.LinkDetailShowImage % id, 'cache' : cache}})
				data = self._execute(requests = requests, threaded = threaded)

				if data:
					dataShow = data['show']
					dataImage = data.get('image') or (dataShow or {}).get('images')
					if dataShow is False or dataImage is False: complete = False

					if dataShow:
						result = {}

						if 'name' in dataShow and 'id' in dataShow:
							result['media'] = Media.Show

							mini = False
							type = dataShow.get('type')
							if type and Tools.isString(type) and Regex.match(data = type, expression = 'mini\-?serie'):
								mini = True
							else:
								try:
									season = dataShow.get('seasons')
									if season:
										season = season[0].get('name')
										if season and Regex.match(data = season, expression = 'mini\-?serie'): mini = True
								except: Logger.error()
							if mini: result['niche'] = [Media.Mini]

							ids = {}
							external = dataShow.get('external_ids') or {}
							tmdb = dataShow.get('id')
							if tmdb: ids['tmdb'] = str(tmdb)
							imdb = dataShow.get('imdb_id')
							if imdb: ids['imdb'] = str(imdb)
							else:
								imdb = external.get('imdb_id')
								if imdb: ids['imdb'] = str(imdb)
							tvdb = external.get('tvdb_id')
							if tvdb: ids['tvdb'] = str(tvdb)
							tvrage = external.get('tvrage_id')
							if tvrage: ids['tvrage'] = str(tvrage)
							if ids: result['id'] = ids

							title = dataShow.get('name')
							if title: result['title'] = Networker.htmlDecode(title)

							originaltitle = dataShow.get('original_name')
							if originaltitle: result['originaltitle'] = Networker.htmlDecode(originaltitle)

							tagline = dataShow.get('tagline')
							if tagline: result['tagline'] = Networker.htmlDecode(tagline)

							plot = dataShow.get('overview')
							if plot: result['plot'] = Networker.htmlDecode(plot)

							premiered = dataShow.get('first_air_date')
							if premiered:
								premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
								if premiered:
									result['premiered'] = premiered
									result['aired'] = premiered
									year = Regex.extract(data = premiered, expression = '(\d{4})-', group = 1)
									if year: result['year'] = int(year)

							genre = dataShow.get('genres')
							if genre: result['genre'] = MetaTmdb._convertGenre(genre = [i['id'] for i in genre], inverse = True)
							if mini:
								if not result.get('genre'): result['genre'] = []
								result['genre'].append(MetaTools.GenreMini)

							rating = dataShow.get('vote_average')
							if not rating is None: result['rating'] = rating

							votes = dataShow.get('vote_count')
							if not votes is None: result['votes'] = votes

							duration = dataShow.get('episode_run_time')
							if duration:
								duration = duration[0] * 60
								result['duration'] = duration

							status = dataShow.get('status')
							if status: result['status'] = MetaTmdb._convertStatus(status = status, inverse = True)

							network = dataShow.get('networks')
							if network: result['network'] = [i['name'] for i in network]

							studio = dataShow.get('production_companies')
							if studio: result['studio'] = [i['name'] for i in studio]

							# Sometimes alternative ISO codes are returned that are not an official code.
							# Eg: tt0806901 - [{'iso_3166_1': 'DE', 'name': 'Germany'}, {'iso_3166_1': 'XG', 'name': 'East Germany'}]
							country = dataShow.get('production_countries')
							if country: result['country'] = Country.codes([i['iso_3166_1'].lower() for i in country])

							languages = dataShow.get('spoken_languages')
							if languages: result['language'] = Language.codes([i['iso_639_1'].lower() for i in languages])
							languages = dataShow.get('original_language')
							if languages:
								languages = Language.codes([languages])
								if languages:
									if 'language' in result: result['language'] = Tools.listUnique(languages + result['language'])
									else: result['language'] = Tools.listUnique(languages)

							country = dataShow.get('origin_country')
							if country:
								if not Tools.isArray(country): country = [country]
								result['country'] = Country.codes(country)

							homepage = dataShow.get('homepage')
							if homepage: result['homepage'] = homepage

							# Create basic pack data in case the full pack metadata has not been retrieved yet.
							# Is used by some skins (eg Aeon Nox) to display episode counts for show menus.
							try:
								from lib.meta.pack import MetaPack

								seasonReleased = None
								seasonSpecial = None
								episodeSpecial = None
								seasonOfficial = dataShow.get('number_of_seasons')
								episodeOfficial = dataShow.get('number_of_episodes')
								seasons = dataShow.get('seasons')
								if seasons:
									for i in seasons:
										if i.get('season_number') == 0:
											seasonSpecial = 1
											episodeSpecial = i.get('episode_count')
											break

								lastEpisode = dataShow.get('last_episode_to_air')
								if lastEpisode: seasonReleased = lastEpisode.get('season_number')

								count = {}
								if not seasonOfficial is None or not seasonReleased is None or not seasonSpecial is None:
									count['season'] = {}
									if not seasonOfficial is None: count['season']['total'] = seasonOfficial
									if not seasonReleased is None: count['season']['released'] = seasonReleased
									if not seasonOfficial is None and not seasonReleased is None: count['season']['unreleased'] = seasonOfficial - seasonReleased
									if not seasonSpecial is None: count['season']['special'] = seasonSpecial
								if not episodeOfficial is None or not episodeSpecial is None:
									count['episode'] = {}
									if not episodeOfficial is None: count['episode']['total'] = episodeOfficial
									if not episodeSpecial is None: count['episode']['special'] = episodeSpecial
								if count: result['count'] = count

								pack = MetaPack.reduceBase(seasonOfficial = seasonOfficial, seasonSpecial = seasonSpecial, episodeOfficial = episodeOfficial, episodeSpecial = episodeSpecial, duration = duration)
								if pack: result['packed'] = pack
							except: Logger.error()
						try:
							if 'aggregate_credits' in dataShow:
								dataPeople = dataShow['aggregate_credits']
								if dataPeople:
									if 'crew' in dataPeople:
										dataCrew = dataPeople['crew']
										if dataCrew:
											director = self._metadataDirector(data = dataCrew)
											if director: result['director'] = director

											writer = self._metadataWriter(data = dataCrew)
											if writer: result['writer'] = writer

									if 'cast' in dataPeople:
										dataCast = dataPeople['cast']
										if dataCast:
											cast = []
											for i in dataCast:
												if 'character' in i and i['character']: character = i['character']
												else: character = None
												if not character and 'roles' in i and i['roles']: character = i['roles'][0]['character']
												if 'order' in i: order = i['order']
												else: order = None
												if 'profile_path' in i and i['profile_path']: thumbnail = self._metadataImage(type = MetaImage.TypePhoto, path = i['profile_path'])
												else: thumbnail = None
												cast.append({'name' : i['name'], 'role' : character, 'order' : order, 'thumbnail' : thumbnail})
											if cast: result['cast'] = cast
						except: Logger.error()

						try:
							if dataImage or dataShow:
								images = {i : [] for i in MetaImage.Types}
								poster = [[], []]
								keyart = [[], []]
								fanart = [[], []]
								landscape = [[], []]

								if dataImage:
									entries = (
										('posters', MetaImage.TypePoster),
										('backdrops', MetaImage.TypeFanart),
										('logos', MetaImage.TypeClearlogo),
									)
									for entry in entries:
										try:
											if entry[0] in dataImage:
												indexed = 0
												for i in dataImage[entry[0]]:
													indexed += 1
													index = 99999999 - indexed
													vote = i.get('vote_average')
													vote = float(vote) if vote else 0
													sort = {
														MetaImage.SortIndex : index,
														MetaImage.SortVote : vote,
														MetaImage.SortVoteIndex : [vote, index],
													}
													image = MetaImage.create(link = self._metadataImage(type = entry[1], path = i.get('file_path')), provider = MetaImage.ProviderTmdb, language = i.get('iso_639_1'), sort = sort)
													if image:
														if entry[1] == MetaImage.TypePoster:
															if image[MetaImage.AttributeLanguage]:
																poster[0].append(image)
																keyart[1].append(image)
															else:
																poster[1].append(image)
																keyart[0].append(image)
														elif entry[1] == MetaImage.TypeFanart:
															if image[MetaImage.AttributeLanguage]:
																landscape[0].append(image)
																fanart[1].append(image)
															else:
																landscape[1].append(image)
																fanart[0].append(image)
														else:
															images[entry[1]].append(image)
										except: Logger.error()

								# Update (2025-09): Not sure if this is a new change to the API, a temporary issues, or always was there.
								# For some seasons, the "images" dict returned by TMDb does not contain any images.
								# However, there might still be a single image stored as a separate path attribute. Use these images as a fallback.
								# This has only been observed with the season metadata, but also do this here, in case some shows have the same problem.
								if dataShow:
									entries = (
										('poster_path', MetaImage.TypePoster),
										('backdrop_path', MetaImage.TypeFanart),
										('logo_path', MetaImage.TypeClearlogo),
										('still_path', MetaImage.TypeThumb),
									)
									for entry in entries:
										try:
											if entry[0] in dataShow:
												image = MetaImage.create(link = self._metadataImage(type = entry[1], path = dataShow[entry[0]]), provider = MetaImage.ProviderTmdb)
												if image:
													if entry[1] == MetaImage.TypePoster:
														if image[MetaImage.AttributeLanguage]:
															if not poster[0] and not poster[1]: poster[0].append(image)
															if not keyart[0] and not keyart[1]: keyart[1].append(image)
														else:
															if not poster[0] and not poster[1]: poster[1].append(image)
															if not keyart[0] and not keyart[1]: keyart[0].append(image)
													elif entry[1] == MetaImage.TypeFanart:
														if image[MetaImage.AttributeLanguage]:
															if not landscape[0] and not landscape[1]: landscape[0].append(image)
															if not fanart[0] and not fanart[1]: fanart[1].append(image)
														else:
															if not landscape[0] and not landscape[1]: landscape[1].append(image)
															if not fanart[0] and not fanart[1]: fanart[0].append(image)
													else:
														if not images[entry[1]]: images[entry[1]].append(image)
										except: Logger.error()

								images[MetaImage.TypePoster] = poster[0] + poster[1]
								images[MetaImage.TypeKeyart] = keyart[0] + keyart[1]
								images[MetaImage.TypeFanart] = fanart[0] + fanart[1]
								images[MetaImage.TypeLandscape] = landscape[0] + landscape[1]

								if images: result[MetaImage.Attribute] = images
						except: Logger.error()
		except: Logger.error()
		return {'provider' : self.id(), 'complete' : complete, 'data' : result} if detail else result

	# quick = True: make less requests by combining subrequests.
	def metadataSeason(self, id = None, tmdb = None, language = None, quick = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			if not id: id = tmdb
			if id:
				idShow = id
				if quick is None: quick = True

				requests = [{'id' : 'show', 'parameters' : {'link' : MetaTmdb.LinkDetailShow % id, 'data' : {'language' : language}, 'cache' : cache}}]
				data = self._execute(requests = requests, threaded = threaded)

				if data:
					dataShow = data['show']
					if dataShow is False: complete = False

					if dataShow and 'name' in dataShow and 'id' in dataShow:
						result = []

						numbers = []
						idSeasons = {}
						idImages = {}
						idPeople = {}
						for i in dataShow.get('seasons'):
							number = i.get('season_number')
							if not number is None:
								numbers.append(number)
								idSeasons[number] = 'season/%d' % number
								idImages[number] = 'season/%d/images' % number
								idPeople[number] = 'season/%d/aggregate_credits' % number

						# Check metadataShow() for more info on the images.
						# Do not get the external_ids for seasons, since they are for the show, not the season.
						# Currently there does not seem to be any difference between the metadata returned by quick vs not quick. So stick to quick for now.
						requests = []
						if quick:
							# If too many appends are added, TMDb returns: "Too many append to response objects: The maximum number of remote calls is 20."
							# Split them over multiple requests.
							append = list(idSeasons.values()) + list(idImages.values()) + list(idPeople.values())
							append = [append[i : i + MetaTmdb.LimitAppend] for i in range(0, len(append), MetaTmdb.LimitAppend)]

							# It is more efficient to use a single (or grouped) request with "append_to_response", instead of retrieving each season with a separate request.
							for i in range(len(append)):
								requests.append({'id' : 'season' + str(i), 'parameters' : {'link' : MetaTmdb.LinkDetailShow % id, 'data' : {'append_to_response' : append[i], 'language' : language, 'include_image_language' : self._metadataImageLanguage(language = language)}, 'cache' : cache}})
						else:
							for i in numbers:
								requests.append({'id' : 'season' + str(i), 'parameters' : {'link' : MetaTmdb.LinkDetailSeason % (id, i), 'data' : {'append_to_response' : ['aggregate_credits', 'images'], 'language' : language, 'include_image_language' : self._metadataImageLanguage(language = language)}, 'cache' : cache}})
						data = self._execute(requests = requests, threaded = threaded)

						if data:
							# Combined the split requests.
							if quick:
								dataAll = {}
								for i in data.values():
									if i is False or i is None: complete = False
									else: dataAll.update(i)

							for number in numbers:
								dataSeason = None
								dataImage = None
								dataPeople = None
								if quick:
									dataSeason = dataAll.get(idSeasons.get(number))
									dataImage = dataAll.get(idImages.get(number))
									dataPeople = dataAll.get(idPeople.get(number))
								else:
									dataSeason = data.get('season' + str(number))
									if dataSeason is False or dataSeason is None: complete = False
									else:
										dataImage = dataSeason.get('images')
										dataPeople = dataSeason.get('aggregate_credits')

								if dataSeason:
									resultSeason = {}
									resultSeason['media'] = Media.Season
									resultSeason['season'] = dataSeason.get('season_number')

									resultSeason['id'] = {}
									if idShow: resultSeason['id']['tmdb'] = str(idShow)
									tmdb = dataSeason.get('id')
									if id: resultSeason['id']['season'] = {'tmdb' : str(tmdb)}

									title = dataSeason.get('name')
									if title: resultSeason['title'] = Networker.htmlDecode(title)

									plot = dataSeason.get('overview')
									if plot: resultSeason['plot'] = Networker.htmlDecode(plot)

									premiered = dataSeason.get('air_date')
									if premiered:
										premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
										if premiered:
											resultSeason['premiered'] = premiered
											resultSeason['aired'] = premiered

									# TMDb does not have ratings for seasons, only for shows and episodes.
									# Calculate the average vote over al episodes in the season.
									# Limit the vote count to the maximum of the episodes, assuming that the same people vote for different episodes.
									rating = []
									votes = []
									episodes = dataSeason.get('episodes')
									if episodes:
										for episode in episodes:
											if episode:
												ratingEpisode = episode.get('vote_average')

												# NB: Do not include 0.0 ratings, which are typical for unaired episodes.
												if ratingEpisode: rating.append(ratingEpisode)

												votesEpisode = episode.get('vote_count')
												if not votesEpisode is None: votes.append(votesEpisode)
									if rating: resultSeason['rating'] = sum(rating) / float(len(rating))
									if votes: resultSeason['votes'] = max(votes)

									try:
										if dataPeople:
											if 'crew' in dataPeople:
												dataCrew = dataPeople['crew']
												if dataCrew:
													director = self._metadataDirector(data = dataCrew)
													if director: resultSeason['director'] = director

													writer = self._metadataWriter(data = dataCrew)
													if writer: resultSeason['writer'] = writer

											if 'cast' in dataPeople:
												dataCast = dataPeople['cast']
												if dataCast:
													cast = []
													for i in dataCast:
														if 'character' in i and i['character']: character = i['character']
														else: character = None
														if not character and 'roles' in i and i['roles']: character = i['roles'][0]['character']
														if 'order' in i: order = i['order']
														else: order = None
														if 'profile_path' in i and i['profile_path']: thumbnail = self._metadataImage(type = MetaImage.TypePhoto, path = i['profile_path'])
														else: thumbnail = None
														cast.append({'name' : i['name'], 'role' : character, 'order' : order, 'thumbnail' : thumbnail})
													if cast: resultSeason['cast'] = cast
									except: Logger.error()

									try:
										# Seasons only seem to have posters on TMDb, but no fanart, landscape, etc.
										if dataImage or dataSeason:
											images = {i : [] for i in MetaImage.Types}
											poster = [[], []]
											keyart = [[], []]
											fanart = [[], []]
											landscape = [[], []]

											if dataImage:
												entries = (
													('posters', MetaImage.TypePoster),
													('backdrops', MetaImage.TypeFanart),
													('logos', MetaImage.TypeClearlogo),
												)
												for entry in entries:
													try:
														if entry[0] in dataImage:
															indexed = 0
															for i in dataImage[entry[0]]:
																indexed += 1
																index = 99999999 - indexed
																vote = i.get('vote_average')
																vote = float(vote) if vote else 0
																sort = {
																	MetaImage.SortIndex : index,
																	MetaImage.SortVote : vote,
																	MetaImage.SortVoteIndex : [vote, index],
																}
																image = MetaImage.create(link = self._metadataImage(type = entry[1], path = i.get('file_path')), provider = MetaImage.ProviderTmdb, language = i.get('iso_639_1'), sort = sort)
																if image:
																	if entry[1] == MetaImage.TypePoster:
																		if image[MetaImage.AttributeLanguage]:
																			poster[0].append(image)
																			keyart[1].append(image)
																		else:
																			poster[1].append(image)
																			keyart[0].append(image)
																	elif entry[1] == MetaImage.TypeFanart:
																		if image[MetaImage.AttributeLanguage]:
																			landscape[0].append(image)
																			fanart[1].append(image)
																		else:
																			landscape[1].append(image)
																			fanart[0].append(image)
																	else:
																		images[entry[1]].append(image)
													except: Logger.error()

											# Update (2025-09): Not sure if this is a new change to the API, a temporary issues, or always was there.
											# For some seasons, the "images" dict returned by TMDb does not contain any images.
											# However, there might still be a single image stored as a separate path attribute. Use these images as a fallback.
											# Eg: Good times, bad times (when retrieving with "quick=True").
											if dataSeason:
												entries = (
													('poster_path', MetaImage.TypePoster),
													('backdrop_path', MetaImage.TypeFanart),
													('logo_path', MetaImage.TypeClearlogo),
													('still_path', MetaImage.TypeThumb),
												)
												for entry in entries:
													try:
														if entry[0] in dataSeason:
															image = MetaImage.create(link = self._metadataImage(type = entry[1], path = dataSeason[entry[0]]), provider = MetaImage.ProviderTmdb)
															if image:
																if entry[1] == MetaImage.TypePoster:
																	if image[MetaImage.AttributeLanguage]:
																		if not poster[0] and not poster[1]: poster[0].append(image)
																		if not keyart[0] and not keyart[1]: keyart[1].append(image)
																	else:
																		if not poster[0] and not poster[1]: poster[1].append(image)
																		if not keyart[0] and not keyart[1]: keyart[0].append(image)
																elif entry[1] == MetaImage.TypeFanart:
																	if image[MetaImage.AttributeLanguage]:
																		if not landscape[0] and not landscape[1]: landscape[0].append(image)
																		if not fanart[0] and not fanart[1]: fanart[1].append(image)
																	else:
																		if not landscape[0] and not landscape[1]: landscape[1].append(image)
																		if not fanart[0] and not fanart[1]: fanart[0].append(image)
																else:
																	if not images[entry[1]]: images[entry[1]].append(image)
													except: Logger.error()

											images[MetaImage.TypePoster] = poster[0] + poster[1]
											images[MetaImage.TypeKeyart] = keyart[0] + keyart[1]
											images[MetaImage.TypeFanart] = fanart[0] + fanart[1]
											images[MetaImage.TypeLandscape] = landscape[0] + landscape[1]

											if images: resultSeason[MetaImage.Attribute] = images
									except: Logger.error()

									if resultSeason: result.append(resultSeason)
		except: Logger.error()

		if not result: result = None
		return {'provider' : self.id(), 'complete' : complete, 'data' : result} if detail else result

	def metadataEpisode(self, id = None, tmdb = None, season = None, language = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			if not id: id = tmdb
			if id:
				requests = [{'id' : 'season', 'parameters' : {'link' : MetaTmdb.LinkDetailSeason % (id, season), 'data' : {'language' : language}, 'cache' : cache}}]
				data = self._execute(requests = requests, threaded = threaded)

				if data:
					dataSeason = data['season']
					if dataSeason is False or (dataSeason and not 'episodes' in dataSeason):
						# If the season does not exist on TMDb.
						# {'success': False, 'status_code': 34, 'status_message': 'The resource you requested could not be found.'}
						# Eg: 62715 S02
						#if season and season > 1 and dataSeason and dataSeason.get('status_code') == 34: pass
						#else: complete = False

						# Leave for now and ignore 34 errors, since we cannot determine if the season does not exist on TMDb at all, or if does not exist yet, but will be added at a later stage.
						# If we check errors here, do the same for MetaTrakt which will also not have the season.
						complete = False

					if dataSeason and 'episodes' in dataSeason:
						result = []

						try: idSeason = str(dataSeason['id'])
						except: idSeason = None

						for episode in dataSeason['episodes']:
							resultEpisode = {}
							resultEpisode['media'] = Media.Episode

							ids = {}
							id = episode.get('show_id')
							if id: ids['tmdb'] = str(id)
							if idSeason: ids['season'] = {'tmdb' : idSeason}
							id = episode.get('id')
							if id: ids['episode'] = {'tmdb' : str(id)}
							if ids: resultEpisode['id'] = ids

							resultEpisode['season'] = episode.get('season_number')
							resultEpisode['episode'] = episode.get('episode_number')

							title = episode.get('name')
							if title: resultEpisode['title'] = Networker.htmlDecode(title)

							plot = episode.get('overview')
							if plot: resultEpisode['plot'] = Networker.htmlDecode(plot)

							premiered = episode.get('air_date')
							if premiered:
								premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
								if premiered:
									resultEpisode['premiered'] = premiered
									resultEpisode['aired'] = premiered

							rating = episode.get('vote_average')
							if not rating is None: resultEpisode['rating'] = rating

							votes = episode.get('vote_count')
							if not votes is None: resultEpisode['votes'] = votes

							duration = episode.get('runtime')
							if duration: resultEpisode['duration'] = duration * 60

							type = self._extractType(item = episode)
							if type: resultEpisode['type'] = type

							try:
								if 'crew' in episode:
									dataCrew = episode['crew']
									if dataCrew:
										director = self._metadataDirector(data = dataCrew)
										if director: resultEpisode['director'] = director

										writer = self._metadataWriter(data = dataCrew)
										if writer: resultEpisode['writer'] = writer

								if 'guest_stars' in episode:
									dataCast = episode['guest_stars']
									if dataCast:
										cast = []
										for i in dataCast:
											if 'name' in i and i['name']:
												if 'character' in i and i['character']: character = i['character']
												else: character = None
												if 'order' in i: order = i['order']
												else: order = None
												if 'profile_path' in i and i['profile_path']: thumbnail = self._metadataImage(type = MetaImage.TypePhoto, path = i['profile_path'])
												else: thumbnail = None
												cast.append({'name' : i['name'], 'role' : character, 'order' : order, 'thumbnail' : thumbnail})
										if cast: resultEpisode['cast'] = cast
							except: Logger.error()

							try:
								thumb = episode.get('still_path')
								if thumb:
									image = MetaImage.create(link = self._metadataImage(type = MetaImage.TypeThumb, path = thumb), provider = MetaImage.ProviderTmdb)
									if image: resultEpisode[MetaImage.Attribute] = {MetaImage.TypeThumb : [image]}
							except: Logger.error()

							result.append(resultEpisode)
		except: Logger.error()

		if not result: result = None
		return {'provider' : self.id(), 'complete' : complete, 'data' : result} if detail else result

	def _metadataPerson(self, data, department, job):
		people = []
		if data:
			for i in data:
				if department == (i.get('department') or '').lower():
					jobs = []

					# "credits"
					values = i.get('job')
					if values:
						if Tools.isArray(values): jobs.extend(values)
						else: jobs.append(values)

					# "aggregate_credits"
					values = i.get('jobs')
					if values:
						if Tools.isArray(values): jobs.extend(values)
						else: jobs.append(values)

					jobs = [j.get('job') if Tools.isDictionary(j) else j for j in jobs]
					jobs = [j.lower() for j in jobs if j]

					if any(j in job for j in jobs):
						name = i.get('name')
						if name and 'job': people.append(name)
		return Tools.listUnique(people)

	def _metadataDirector(self, data):
		# https://api.themoviedb.org/3/configuration/jobs?api_key=xxx
		return self._metadataPerson(data = data, department = 'directing', job = ['director', 'co-director', 'series director'])

	def _metadataWriter(self, data):
		# https://api.themoviedb.org/3/configuration/jobs?api_key=xxx
		return self._metadataPerson(data = data, department = 'writing', job = ['writer', 'screenplay', 'author', 'co-writer', 'original film writer', 'original story', 'story', 'teleplay'])

	def _metadataImage(self, type, path):
		# https://www.themoviedb.org/talk/53c11d4ec3a3684cf4006400
		if path is None: return None
		size = {MetaImage.TypePoster : 780, MetaImage.TypeFanart : 1280, MetaImage.TypeClearlogo : 500, MetaImage.TypePhoto : 185}
		size = size.get(type)
		if size: size = 'w%d' % size
		else: size = 'original'
		return MetaTmdb.LinkImage % (size, path)

	def _metadataImageLanguage(self, language):
		languages = ['en', 'null']
		if language and not language in languages: languages.insert(0, language)
		return languages

	##############################################################################
	# PACK
	##############################################################################

	# quick = True: Only retrieve the full metadata for some seasons, and automatically calculate the numbers for the remainder of the seasons without retrieving their full metadata.
	def metadataPack(self, id = None, tmdb = None, data = None, quick = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			if not id: id = tmdb
			if data or id:
				from lib.meta.pack import MetaPack

				seasons = []
				if not data and id:
					# All episode metadata cannot be retrieved/appended, only a single season.
					#	https://www.themoviedb.org/talk/59d2898cc3a36830800048f2
					# Update: it is possible to retrieve all seasons/episodes in one go:
					#	https://www.themoviedb.org/talk/64ecd07106f98400ca56ea68
					# This is fine, since we create the episode numbers automatically for all seasons, and then have detailed metadsata for season 1.
					# For shows with a single absolute season (eg: Dragon Ball Super), this is all we need.
					# For detailed metadata for the remainder of the seasons, we just use the data from TVDb/Trakt.
					# Although the detailed episode data is not absolutely required, since it will probably the same as Trakt, it might still be a good idea to add it, in case Trakt goes down and then the TVDb-only data will cause havoc to the numbering in packs.
					#data = self._request(link = MetaTmdb.LinkDetailShow % id, data = {'append_to_response' : 'season/1,external_ids'}, cache = cache)
					if quick:
						data = self._request(link = MetaTmdb.LinkDetailShow % id, data = {'append_to_response' : ['external_ids', 'season/0', 'season/1', 'season/2']}, cache = cache)
					else:
						data = self._request(link = MetaTmdb.LinkDetailShow % id, cache = cache)
						if data:
							dataSeasons = data.get('seasons')
							if dataSeasons:
								# "append_to_response=translations" only returns the show translations, but not the episode translations.
								# And there does not seem to be any effort to add a feature like this: https://www.themoviedb.org/talk/63e602a59512e100b2b188b0
								# If Trakt does not have the TVDb IDs for episodes, it becomes difficult to match the episodes by title in MetaPack.
								# Eg: Good times, bad times:
								#	Trakt: default titles (eg "Episode 8") and German aliases.
								#	TVDb: German titles
								#	TMDb: default titles (eg "Episode 8")
								# If such default titles are used, add the original language of the show to the parameters, so that episode titles for that language are returned.
								language = None
								last = data.get('last_episode_to_air')
								if last and (not last.get('name') or Regex.match(data = last.get('name'), expression = '^episode\s*\d+')): language = data.get('original_language')

								seasons = [i.get('season_number') for i in dataSeasons]
								seasons = ['season/%d' % i for i in seasons if not i is None]

								# If too many appends are added, TMDb returns: "Too many append to response objects: The maximum number of remote calls is 20."
								# Split them over multiple requests.
								limit = MetaTmdb.LimitAppend - 1
								append = [seasons[i : i + limit] for i in range(0, len(seasons), limit)]

								requests = []
								for i in append:
									parameters = {'append_to_response' : ['external_ids'] + i}
									if language: parameters['language'] = language
									requests.append({'id' : 'season' + str(i), 'parameters' : {'link' : MetaTmdb.LinkDetailShow % id, 'data' : parameters, 'cache' : cache}})
								data = self._execute(requests = requests, threaded = threaded)

								# Combined the split requests.
								all = {}
								for i in data.values():
									if i is False or i is None: complete = False
									else: all.update(i)
								data = all

				if data:
					dataSeasons = data.get('seasons')

					if not seasons and dataSeasons:
						seasons = [i.get('season_number') for i in dataSeasons]
						seasons = ['season/%d' % i for i in seasons if not i is None]

					dataEpisodes = {}
					for i in seasons:
						season = data.get(i)
						if season:
							episodes = season.get('episodes')
							if episodes: dataEpisodes[season.get('season_number')] = episodes

					sequential = 0
					seasons = {}
					if dataSeasons:
						# Add custom episode numbers if absolute numbers are used.
						# Eg: One Piece
						custom1 = False
						try:
							for season in dataSeasons:
								numberSeason = season.get('season_number')
								if numberSeason and numberSeason > 1:
									values = dataEpisodes.get(numberSeason)
									if values:
										if min([j.get('episode_number') for j in values]) >= 3:
											custom1 = True
											break
						except: Logger.error()

						for season in dataSeasons:
							numberSeason = season.get('season_number')
							if not numberSeason is None:
								episodes = []

								values = dataEpisodes.get(numberSeason)
								if values:
									counter = 0
									previous = 0
									custom2 = True
									try:
										numbers = [j.get('episode_number') for j in values]
										if not len(values) == (max(numbers) - min(numbers) + 1): custom2 = False
									except:
										custom2 = False
										Logger.error()

									for j in values:
										numberEpisode = j.get('episode_number')
										item = {'number' : {MetaPack.NumberStandard : [numberSeason, numberEpisode], MetaPack.NumberSequential : [1, sequential if numberSeason > 0 else 0]}}

										if custom1 and custom2 and numberSeason > 0:
											counter += 1

											# Sometimes TMDb has a missing episode.
											# Increase the counter, so that the custom episode still matches with the standard episode number.
											# Eg: The Tonight Show Starring Jimmy Fallon S01E174 (missing on both Trakt and TMDb).
											# Only do this up to 3 missing episodes, since Trakt/TMDb can sometimes have entire blocks of episodes missing.
											if previous:
												difference = abs(previous - numberEpisode)
												if difference > 1 and difference <= 3: counter += (difference - 1)

											# Add this for shows where TMDb uses season-numbering for seasons, but within each season, episodes are numbered absolutely.
											# Eg: One Piece
											# Do this in case a few new unaired episodes were added to TMDb, but are not on Trakt yet.
											# Otherwise the last episodes on TMDb will not be added to the pack.
											# Eg: One Piece S22E1136+S22E1137 are on TMDb already, but Trakt only goes to S22E1135 at that point.
											item['number'][MetaPack.NumberCustom] = [numberSeason, counter]

											previous = numberEpisode

										id = j.get('id')
										if id: item['id'] = {'tmdb' : str(id)}

										title = j.get('name')
										if title: item['title'] = [title]

										date = j.get('air_date')
										if date:
											time = Time.timestamp(fixedTime = date, format = Time.FormatDate, utc = True)
											item['year'] = Time.year(timestamp = time) if time else j.get('year')
											item['date'] = date
											item['time'] = time

										duration = j.get('runtime')
										if duration: item['duration'] = duration * 60

										type = self._extractType(item = j)
										if type: item['serie'] = type

										episodes.append(item)

								# Do not add this, since some seasons on TMDb have missing episodes, which makes these assumed numbers incorrect.
								# Eg: The Tonight Show Starring Jimmy Fallon S03E13-59 are missing.
								# Missing TMDb numbers are now interpolated in MetaPack from the Trakt numbers.
								'''else:
									count = season.get('episode_count') or 0
									if count:
										for i in range(1, count + 1):
											if numberSeason > 0: sequential += 1
											item = {'number' : {MetaPack.NumberStandard : [numberSeason, i], MetaPack.NumberSequential : [1, sequential if numberSeason > 0 else 0]}}
											episodes.append(item)
								'''

								title = season.get('name')
								title = [title] if title else None

								time = None
								date = season.get('air_date')
								if date: time = Time.timestamp(fixedTime = date, format = Time.FormatDate, utc = True)
								elif episodes:
									time = episodes[0].get('time') # Some seasons do not have an air_date. Eg: One Piece S02+.
									date = episodes[0].get('date')

								seasons[numberSeason] = {
									'id'		: {'tmdb' : str(season.get('id'))},
									'title'		: title,
									'number'	: {MetaPack.NumberStandard : numberSeason, MetaPack.NumberSequential : 1 if numberSeason else 0},
									'year'		: Time.year(timestamp = time) if time else None,
									'date'		: date,
									'time'		: time,
									'episodes'	: episodes,
								}

					seasons = [seasons[i] for i in sorted(seasons.keys())]

					external = data.get('external_ids') or {}
					tmdb = data.get('id')
					if tmdb: tmdb = str(tmdb)
					imdb = external.get('imdb_id')
					if imdb: imdb = str(imdb)
					tvdb = external.get('tvdb_id')
					if tvdb: tvdb = str(tvdb)

					title = data.get('name')
					title = [title] if title else None

					time = None
					date = data.get('first_air_date')
					if date: time = Time.timestamp(fixedTime = date, format = Time.FormatDate, utc = True)

					status = data.get('status')
					if status: status = MetaTools.statusExtract(status)

					duration = []
					if dataEpisodes:
						for episodes in dataEpisodes.values():
							for episode in episodes:
								if not episode.get('season_number') == 0:
									temp = episode.get('runtime')
									if temp: duration.append(temp * 60)
					temp = (data.get('last_episode_to_air') or {}).get('runtime')
					if temp: duration.append(temp * 60)
					duration = int(sum(duration) / float(len(duration))) if duration else None

					language = []
					temp = data.get('original_language')
					if temp: language.extend(temp) if Tools.isArray(temp) else language.append(temp)
					temp = data.get('languages')
					if temp: language.extend(temp) if Tools.isArray(temp) else language.append(temp)
					temp = data.get('spoken_languages')
					if temp: language.extend([i.get('iso_639_1') for i in temp])
					language = Tools.listUnique(Language.codes([i.lower() for i in language if i])) if language else None

					country = None
					value = data.get('origin_country')
					if value:
						if not Tools.isArray(value): value = [value]
						country = Tools.listUnique(Country.codes(value))

					result = {
						'id' : {
							'imdb'	: imdb,
							'tmdb'	: tmdb,
							'tvdb'	: tvdb,
						},
						'title'		: title,
						'year'		: data.get('year') or (Time.year(timestamp = time) if time else None),
						'date'		: date,
						'time'		: time,
						'status'	: status,
						'duration'	: duration,
						'language'	: language,
						'country'	: country,
						'seasons'	: seasons,
					}
				else: complete = False
			else:
				complete = False # No TMDb ID for this show yet.
		except: Logger.error()
		return {'provider' : self.id(), 'complete' : complete, 'data' : result} if detail else result
