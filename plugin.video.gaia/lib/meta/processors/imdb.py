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

from lib.modules.network import Networker
from lib.modules.cache import Cache
from lib.modules.parser import Parser
from lib.modules.tools import Logger, Converter, Tools, Regex, Media

from lib.meta.tools import MetaTools

class MetaImdb(object):

	Debug			= False # Disable debugging, since many smaller movies have many missing attributes.

	LinkTitle		= 'https://imdb.com/title/%s'
	LinkSeason		= 'https://imdb.com/title/%s/episodes?season=%d'
	LinkAward		= 'https://imdb.com/title/%s/awards'
	LinkSearch		= 'https://imdb.com/find/?q=%s'

	CacheDetails	= Cache.TimeoutWeek1
	CacheList		= [Cache.TimeoutRefresh, Cache.TimeoutDay3]
	CacheDefault	= Cache.TimeoutLong
	CacheNone		= None

	##############################################################################
	# GENERAL
	##############################################################################

	# NB: timeout = CacheNone: do not cache the data by default, since IMDb pages can be 1MB+ in size and quickly fill up disk space.
	# Even though the data is returned as GZIP from IMDB (+-200KB), it is stored decompressed in the cache database.
	# Therefore, do not cache, except if specifically requested, and let the extracted/summarized data be cached by MetaCache.
	@classmethod
	def retrieve(self, link, timeout = CacheNone, full = False):
		networker = Networker()
		if timeout is MetaImdb.CacheNone: result = networker.requestText(link = link, headers = self.headers())
		elif Tools.isArray(timeout): result = Cache.instance().cache(None, timeout[0], timeout[1], networker.requestText, link = link, headers = self.headers())
		else: result = Cache.instance().cache(None, timeout, None, networker.requestText, link = link, headers = self.headers())
		return networker if full else result

	@classmethod
	def headers(self):
		# IMDb returns the website in the language specified in the headers (if supported).
		# In order to get (some) metadata and the poster in a specific language, set the Accept-Language header.
		headers = MetaTools.instance().headerLanguage()

		# A raw IMDb page is arround 1MB+ in size (eg: "Accept-Encoding: identity").
		# A GZIP-ped IMDb page is under 200KB in size.
		# The data returned by Python's Requests will always have the text data size at +-1MB, because Requests already decompresses the data for us.
		# To get the actual uncompressed size, use:
		#	session.request(stream = True, method = 'GET', ...)
		#	size = len(response.raw.read()))
		# It seems that by default IMDb are returned with GZIP. Not sure if Requests does this, or if IMDb pages are always returned with GZIP by default (if no other Accept-Encoding header was set).
		# Just force the Accept-Encoding header to GZIP to  make sure we get lower-sized data.
		headers[Networker.HeaderAcceptEncoding] = 'gzip, deflate, br'

		return headers

	@classmethod
	def link(self, media = None, id = None, title = None, year = None, season = None, metadata = None, award = False, search = False):
		try:
			if metadata:
				if not media:
					if 'tvshowtitle' in metadata:
						if 'episode' in metadata: media = Media.TypeEpisode
						elif 'season' in metadata: media = Media.TypeSeason
						else: media = Media.TypeShow
					else:
						media = Media.TypeMovie
				if id is None and media == Media.TypeEpisode:
					try: id = metadata['id']['episode']['imdb']
					except: pass
				if id is None:
					try: id = metadata['id']['imdb']
					except: pass
				try: title = metadata['tvshowtitle'] if metadata['tvshowtitle'] else metadata['title']
				except: pass
				try: year = metadata['year']
				except: pass
				try: season = metadata['season']
				except: pass

			if media == Media.TypeShow:
				episode = None
				season = None
			elif media == Media.TypeSeason:
				episode = None

			if id:
				if award: return MetaImdb.LinkAward % id
				elif season and media == Media.TypeSeason: return MetaImdb.LinkSeason % (id, season)
				else: return MetaImdb.LinkTitle % id
			elif search and title:
				query = title
				if year and Media.typeMovie(media): query += ' ' + str(year)
				return MetaImdb.LinkSearch % Networker.linkQuote(data = query, plus = False)
		except: Logger.error()
		return None

	@classmethod
	def image(self, link, size = 780, crop = False):
		expression = '((?:_SX|_SY|_UX|_UY|_CR|_AL|_V)(?:\d+|_).+?\.)'

		# Keep the cropped coordinates for people images, otherwise there might be differently sized images in the menu.
		# Eg: https://m.media-amazon.com/images/M/MV5BMzIzMTE4NzcyMl5BMl5BanBnXkFtZTgwODA2NTQyNTM@._V1_UY209_CR87,0,140,209_AL_.jpg
		# Eg: https://m.media-amazon.com/images/M/MV5BYjQ5MDkyMGEtYmI0OS00MmM2LWE0MmEtZmQ2NjA5MzYyYTFjXkEyXkFqcGdeQXVyNjIwMTQzOTU@._V1_UY209_CR37,0,140,209_AL_.jpg
		if crop:
			try:
				pixel = Regex.extract(data = link, expression = '_CR([\d\,]+)')
				if pixel:
					pixel = [int(i) for i in pixel.split(',')]
					if pixel:
						ratio = size / float(pixel[3])
						pixel = [int(i * ratio) for i in pixel]

						# Either scale vertically or horizontally.
						# Use the same scaling as in the original link (some links contain _UX, some _UY).
						# Otherwise some images might have top-bottom or left-right white bars.
						width = pixel[2]
						height = pixel[3]
						if Regex.extract(data = link, expression = '((?:_UX)(?:\d+|_).+?\.)'):
							scaler = '_UX'
							size = width
						else:
							scaler = '_UY'
							size = height

						pixel = [str(i) for i in pixel]
						return Regex.replace(data = link, expression = expression, replacement = '%s%d_CR%s.' % (scaler, size, ','.join(pixel)), group = 1)
			except: Logger.error()

		# Eg: https://m.media-amazon.com/images/M/MV5BNjA3NGExZDktNDlhZC00NjYyLTgwNmUtZWUzMDYwMTZjZWUyXkEyXkFqcGdeQXVyMTU1MDM3NDk0._V1_.jpg
		# Eg: https://m.media-amazon.com/images/M/MV5BMzA4Njc3ODYtMTYwOS00Y2NiLWFkNmEtOThhZmU0MGQxM2Y5XkEyXkFqcGdeQXVyMTYzMDM0NTU@._V1_QL75_UX190_CR0,0,190,281_.jpg
		return Regex.replace(data = link, expression = expression, replacement = '_SX%d.' % size, group = 1)

	##############################################################################
	# LOGGING
	##############################################################################

	@classmethod
	def _fatal(self, id = None, code = None):
		details = ''
		if id and code: details = ' [%s - %s]' % (id, code)
		elif id: details = ' [%s]' % id
		elif code: details = ' [%s]' % code
		Logger.log('IMDB DATA%s: The structure of the IMDb data has changed and cannot be processed anymore. Please contact the Gaia developer if you see this message.' % details, type = Logger.TypeFatal)
		return None

	@classmethod
	def _error(self, id = None, message = None, attribute = None):
		if MetaImdb.Debug:
			if not message: message = ''
			if attribute: message += (' ' if message else '') + ('The "%s" attribute cannot be extracted.' % attribute)
			Logger.log('IMDB DATA%s: %s' % ((' [%s]' % id) if id else '', message), type = Logger.TypeError)
		return None

	##############################################################################
	# EXTRACT
	##############################################################################

	@classmethod
	def _extract(self, data, keys, result = None, attribute = None, function = None, id = None, log = True):
		if Tools.isDictionary(data): data = [data]
		for i in data:
			try:
				value = Tools.dictionaryGet(dictionary = i, keys = keys)
				if not value is None:
					if function: value = function(value)
					if not result is None: result[attribute] = value
					return value
			except: pass
		if log: self._error(id = id, attribute = attribute)
		return None

	@classmethod
	def _extractIdList(self, data):
		try:
			if data: return [item['id'] for item in data]
		except: Logger.error()
		return None

	@classmethod
	def _extractIdListLower(self, data):
		try:
			if data: return [item['id'].lower() for item in data]
		except: Logger.error()
		return None

	@classmethod
	def _extractPremiered(self, data):
		try:
			if data and data['year'] and data['month'] and data['month']:
				return '%d-%d-%d' % (data['year'], data['month'], data['month'])
		except: Logger.error()
		return None

	@classmethod
	def _extractStudio(self, data):
		try:
			if data:
				result = []
				for item in data:
					try: result.append(item['node']['company']['companyText']['text'])
					except: Logger.error()
				if result: return result
		except: Logger.error()
		return None

	@classmethod
	def _extractHomepage(self, data):
		try:
			if data:
				result = []
				for item in data:
					rank = 2
					type = item['node']['label'].lower()
					if 'official site' in type: rank = 0
					elif 'official' in type: rank = 1
					result.append((rank, item['node']['url']))
				if result: return sorted(result, key = lambda i : i[0])[0][1]
		except: Logger.error()
		return None

	@classmethod
	def _extractCast(self, data):
		try:
			if data:
				result = []
				order = 0
				for item in data:
					cast = {}
					try: cast['name'] = item['node']['name']['nameText']['text']
					except: Logger.error()
					try: cast['thumbnail'] = self.image(item['node']['name']['primaryImage']['url'])
					except: pass
					try: cast['role'] = ' / '.join([i['name'] for i in item['node']['characters']])
					except: pass
					if cast:
						cast['order'] = order
						result.append(cast)
						order += 1
				if result: return result
		except: Logger.error()
		return None

	@classmethod
	def _extractCrew(self, data):
		try:
			if data:
				result = []
				for item in data:
					try:
						if item['credits']: result.append(item['credits'][0]['name']['nameText']['text'])
					except: Logger.error()
				if result: return result
		except: Logger.error()
		return None

	@classmethod
	def _extractAward(self, data):
		try:
			if data:
				award = {}
				try: award['id'] = Tools.replaceNotAlphaNumeric(data['award']['text'].lower())
				except: Logger.error()
				try: award['name'] = data['award']['text']
				except: Logger.error()
				try: award['wins'] = data['wins']
				except: pass
				try: award['nominations'] = data['nominations']
				except: pass
				if award: return [award]
		except: Logger.error()
		return None

	@classmethod
	def _extractMetacritic(self, data):
		try:
			if data: return data / 10.0
		except: Logger.error()
		return None

	##############################################################################
	# DETAILS
	##############################################################################

	# Provide either id/link/data
	# NB: cache = False: do not cache the data by default. Read the comment at retrieve().
	@classmethod
	def details(self, id = None, link = None, data = None, cache = False):
		if data is None:
			if link is None and id: link = self.link(id = id)
			if link: data = self.retrieve(link = link, timeout = MetaImdb.CacheDetails if cache else MetaImdb.CacheNone)
		if not data: return None

		# IMDb has JSON data stored inside the HTML.
		# There is a JSON object at the start of the HTML with only basic metadata.
		# But somewhere in the middle of the HTML there is a full JSON metadata object.
		# It is easier and more reliable to use the JSON data instead of extracting values from HTML.

		# Parser.ParserHtml is faster than Parser.ParserHtml5.
		parser = Parser(data = data, parser = Parser.ParserHtml)
		datas = parser.find_all('script', {'type' : 'application/json'})

		data = None
		for i in datas:
			try:
				i = Converter.jsonFrom(i.string)
				if 'props' in i:
					data = i
					break
			except: pass

		try: datas = data['props']['pageProps']
		except: return self._fatal(id = id, code = 'details-a')

		data = []
		try: data.append(datas['mainColumnData'])
		except: pass
		try: data.append(datas['aboveTheFoldData'])
		except: pass
		if not data: return self._fatal(id = id, code = 'details-b')

		result = {}
		finance = {}
		tempImdb = {}
		tempMetacritic = {}

		self._extract(id = id, result = result, data = data, attribute = 'imdb', keys = ['id'])
		if 'imdb' in result:
			id = result['imdb']
			result['id'] = {'imdb' : result['imdb']}
		else: return self._fatal(id = id, code = 'details-c')

		self._extract(id = id, result = result, data = data, attribute = 'title', keys = ['titleText', 'text'])
		self._extract(id = id, result = result, data = data, attribute = 'originaltitle', keys = ['originalTitleText', 'text'])
		self._extract(id = id, result = result, data = data, attribute = 'plot', keys = ['plot', 'plotText', 'plainText'])
		self._extract(id = id, result = result, data = data, attribute = 'year', keys = ['releaseYear', 'year'])
		self._extract(id = id, result = result, data = data, attribute = 'premiered', keys = ['releaseDate'], function = self._extractPremiered)
		self._extract(id = id, result = result, data = data, attribute = 'genres', keys = ['genres', 'genres'], function = self._extractIdList)
		self._extract(id = id, result = result, data = data, attribute = 'mpaa', keys = ['certificate', 'rating'])
		self._extract(id = id, result = result, data = data, attribute = 'duration', keys = ['runtime', 'seconds'])
		self._extract(id = id, result = result, data = data, attribute = 'status', keys = ['productionStatus', 'currentProductionStage', 'text'])
		self._extract(id = id, result = result, data = data, attribute = 'studio', keys = ['production', 'edges'], function = self._extractStudio)
		self._extract(id = id, result = result, data = data, attribute = 'country', keys = ['countriesOfOrigin', 'countries'], function = self._extractIdListLower)
		self._extract(id = id, result = result, data = data, attribute = 'language', keys = ['spokenLanguages', 'spokenLanguages'], function = self._extractIdListLower)
		self._extract(id = id, result = result, data = data, attribute = 'homepage', keys = ['detailsExternalLinks', 'edges'], function = self._extractHomepage)

		self._extract(id = id, result = result, data = data, attribute = 'cast', keys = ['cast', 'edges'], function = self._extractCast)
		self._extract(id = id, result = result, data = data, attribute = 'director', keys = ['directors'], function = self._extractCrew)
		self._extract(id = id, result = result, data = data, attribute = 'writer', keys = ['writers'], function = self._extractCrew)

		self._extract(id = id, result = result, data = data, attribute = 'award', keys = ['prestigiousAwardSummary'], function = self._extractAward)

		self._extract(id = id, result = finance, data = data, attribute = 'budget', keys = ['productionBudget', 'budget', 'amount'])
		self._extract(id = id, result = finance, data = data, attribute = 'revenue', keys = ['worldwideGross', 'total', 'amount'])
		self._extract(id = id, result = finance, data = data, attribute = 'opening', keys = ['openingWeekendGross', 'gross', 'total', 'amount'])
		if finance:
			try: finance['profit'] = finance['revenue'] - finance['budget']
			except: pass
			result['finance'] = finance

		self._extract(id = id, result = tempImdb, data = data, attribute = 'poster', keys = ['primaryImage', 'url'], function = self.image)
		self._extract(id = id, result = tempImdb, data = data, attribute = 'rating', keys = ['ratingsSummary', 'aggregateRating'])
		self._extract(id = id, result = tempImdb, data = data, attribute = 'votes', keys = ['ratingsSummary', 'voteCount'])
		self._extract(id = id, result = tempMetacritic, data = data, attribute = 'rating', keys = ['metacritic', 'metascore', 'score'], function = self._extractMetacritic, log = False)
		result['temp'] = {}
		if tempImdb: result['temp']['imdb'] = tempImdb
		if tempMetacritic: result['temp']['metacritic'] = tempMetacritic

		return result

	# Provide either id/link/data
	# NB: cache = False: do not cache the data by default. Read the comment at retrieve().
	@classmethod
	def detailsSeason(self, id = None, season = None, link = None, data = None, cache = False):
		try:
			if data is None:
				if link is None and id:
					if season == 0: return None
					link = self.link(media = Media.TypeSeason, id = id, season = season)
				if link: data = self.retrieve(link = link, timeout = MetaImdb.CacheDetails if cache else MetaImdb.CacheNone)
			if not data: return None

			# IMDb only sometimes returns the page with JSON. Other times it just returns the pure already formatted HTML.
			# Especially if many IMDb pages are requested in a short period of time, IMDb more often returns pure HTML than JSON.
			# When it returns JSON, it is the new styled IMDb episode page.
			# When it does not return JSON, it is the old styled IMDb episode page.

			# Parser.ParserHtml is faster than Parser.ParserHtml5.
			parser = Parser(data = data, parser = Parser.ParserHtml)

			result = self._detailsSeasonNew(parser = parser)
			if not result: result = self._detailsSeasonOld(parser = parser)
			return result
		except:
			Logger.error()
			return self._fatal(id = id, code = 'details-season-z')

	@classmethod
	def _detailsSeasonOld(self, parser):
		try:
			from lib.modules.convert import ConverterTime
			months = {'Jan' : '01', 'Feb' : '02', 'Mar' : '03', 'Apr' : '04', 'May' : '05', 'Jun' : '06', 'Jul' : '07', 'Aug' : '8', 'Sep' : '09', 'Oct' : '10', 'Nov' : '11', 'Dec' : '12'}

			episodes = parser.find('div', {'class' : 'eplist'})

			# Some shows have no listed episodes.
			# Eg: https://www.imdb.com/title/tt21871318/
			if not episodes: return None

			episodes = episodes.find_all('div', {'class' : 'list_item'})
			if not episodes: return self._fatal(id = id, code = 'details-season-old-a')

			try:
				show = parser.find('div', {'class' : 'subpage_title_block'}).find('a', {'itemprop' : 'url'})
				showId = Regex.extract(data = show['href'], expression = '(tt\d+)[^\d]')
				showTitle = show.text
			except:
				showId = None
				showTitle = None

			result = []
			for episode in episodes:
				resultEpisode = {}
				resultTemp = {}

				if showId: resultEpisode['id'] = {'imdb' : showId}
				if showTitle: resultEpisode['tvshowtitle'] = showTitle

				name = episode.find('a', {'itemprop' : 'name'})
				if name:
					idEpisode = Regex.extract(data = name['href'], expression = '(tt\d+)[^\d]')
					if idEpisode:
						if not 'id' in resultEpisode or not resultEpisode['id']: resultEpisode['id'] = {}
						resultEpisode['id']['episode'] = {'imdb' : idEpisode}

					resultEpisode['title'] = Networker.htmlDecode(name.text)

				plot = episode.find('div', {'itemprop' : 'description'})
				if plot: resultEpisode['plot'] = Networker.htmlDecode(plot.text.strip().replace('\n', ' '))

				ratings = episode.find('div', {'class' : 'ipl-rating-widget'})
				if ratings:
					rating = ratings.find('span', {'class' : 'ipl-rating-star__rating'})
					if rating: resultTemp['rating'] = float(rating.text)

					votes = ratings.find('span', {'class' : 'ipl-rating-star__total-votes'})
					if votes: resultTemp['votes'] = int(votes.text.replace(',', '').replace('(', '').replace(')', ''))

				premiered = episode.find('div', {'class' : 'airdate'})
				if premiered:
					date = None
					premiered = premiered.text
					for month, number in months.items():
						if month in premiered:
							try:
								number = '-%s-' % number
								premiered = premiered.replace(' %s. ' % month, number).replace(' %s ' % month, number)

								# Some episodes just have a month and year, but no day (eg: " May 2004").
								# Note that these dates have preceeding spaces or newlines, so strip below.
								# Just assume the 1st of the month.
								# https://www.imdb.com/title/tt0434706/episodes?season=1
								if premiered.strip().startswith('-'): premiered = '01' + premiered.strip()

								date = ConverterTime(premiered, format = '%d-%m-%Y').string(format = '%Y-%m-%d')
								break
							except: Logger.error()
					if date:
						resultEpisode['premiered'] = date
						resultEpisode['aired'] = date
						resultEpisode['year'] = int(Regex.extract(data = date, expression = '(\d{4})'))

				thumbnail = episode.find('div', {'class' : 'image'})
				if thumbnail:
					number = thumbnail.text
					if number:
						number = Regex.extract(data = number, expression = 's(\d+).*?ep?(\d+)', group = None, all = True)
						if number:
							resultEpisode['season'] = int(number[0][0])
							resultEpisode['episode'] = int(number[0][1])

					thumbnail = thumbnail.find('img')
					if thumbnail:
						thumbnail = thumbnail['src']
						if thumbnail:
							resultTemp['thumbnail'] = self.image(thumbnail)

				if resultTemp: resultEpisode['temp'] = {'imdb' : resultTemp}
				if resultEpisode: result.append(resultEpisode)

			return {'episodes' : result}
		except:
			Logger.error()
			return self._fatal(id = id, code = 'details-season-old-z')

	@classmethod
	def _detailsSeasonNew(self, parser):
		try:
			from lib.modules.convert import ConverterTime

			data = None
			datas = parser.find_all('script', {'type' : 'application/json'})
			for i in datas:
				try:
					i = Converter.jsonFrom(i.string)
					if 'props' in i:
						data = i
						break
				except: pass
			if not data: return None

			try: data = data['props']['pageProps']['contentData']
			except: return self._fatal(id = id, code = 'details-season-new-a')

			try: show = data['entityMetadata']
			except: return self._fatal(id = id, code = 'details-season-new-b')
			showId = self._extract(id = id, data = show, keys = ['id'])
			showTitle = self._extract(id = id, data = show, keys = ['titleText', 'text'])

			try: episodes = data['section']['episodes']['items']
			except: return self._fatal(id = id, code = 'details-season-new-c')

			result = []
			for episode in episodes:
				resultEpisode = {}
				resultTemp = {}

				if showId: resultEpisode['id'] = {'imdb' : showId}
				if showTitle: resultEpisode['tvshowtitle'] = showTitle

				idEpisode = self._extract(id = id, data = episode, keys = ['id'])
				if idEpisode:
					if not 'id' in resultEpisode or not resultEpisode['id']: resultEpisode['id'] = {}
					resultEpisode['id']['episode'] = {'imdb' : idEpisode}

				self._extract(id = id, result = resultEpisode, data = episode, attribute = 'season', keys = ['season'], function = int)
				self._extract(id = id, result = resultEpisode, data = episode, attribute = 'episode', keys = ['episode'], function = int)
				self._extract(id = id, result = resultEpisode, data = episode, attribute = 'title', keys = ['titleText'])
				self._extract(id = id, result = resultEpisode, data = episode, attribute = 'plot', keys = ['plot'])

				self._extract(id = id, result = resultEpisode, data = episode, attribute = 'year', keys = ['releaseYear'], function = int)
				premiered = self._extract(id = id, data = episode, keys = ['releaseDate'])
				if premiered:
					premiered = ConverterTime(premiered, format = ConverterTime.FormatDateAmerican).string(format = ConverterTime.FormatDate)
					if premiered:
						resultEpisode['premiered'] = premiered
						resultEpisode['aired'] = premiered
						resultEpisode['year'] = int(Regex.extract(data = premiered, expression = '(\d{4})'))

				self._extract(id = id, result = resultEpisode, data = episode, attribute = 'rating', keys = ['aggregateRating'], function = float)
				self._extract(id = id, result = resultEpisode, data = episode, attribute = 'votes', keys = ['voteCount'], function = int)
				if 'rating' in resultEpisode: resultTemp['rating'] = resultEpisode['rating']
				if 'votes' in resultEpisode: resultTemp['votes'] = resultEpisode['votes']

				self._extract(id = id, result = resultTemp, data = episode, attribute = 'thumbnail', keys = ['image', 'url'], function = self.image)

				if resultTemp: resultEpisode['temp'] = {'imdb' : resultTemp}
				if resultEpisode: result.append(resultEpisode)

			return {'episodes' : result}
		except:
			Logger.error()
			return self._fatal(id = id, code = 'details-season-new-z')

	#gaiaremove
	# Provide either id/link/data
	# NB: This does not fully work. IMDb hides a lot of awards (including big ones like Academy Awards and Primetime Emmies), which requires additional requests to their Graphql API (eg: GoT).
	# TMDb wants to add a new feature in the API. Maybe use that: https://trello.com/c/zLTMoZhb/109-add-awards-nominations
	# Or just extract the the summary award info from the main IMDb page.
	@classmethod
	def detailsAward(self, id = None, link = None, data = None, cache = False):
		if data is None:
			if link is None and id: link = self.link(id = id, award = True)
			if link: data = self.retrieve(link = link, timeout = MetaImdb.CacheDetails if cache else MetaImdb.CacheNone)
		if not data: return None

		try:
			# Parser.ParserHtml is faster than Parser.ParserHtml5.
			parser = Parser(data = data, parser = Parser.ParserHtml)
			datas = parser.find_all('script', {'type' : 'application/json'})

			data = None
			for i in datas:
				try:
					i = Converter.jsonFrom(i.string)
					if 'props' in i:
						data = i
						break
				except: pass

			try: data = data['props']['pageProps']['contentData']
			except: return self._fatal(id = id, code = 'details-awards-a')

			countries = {
				# Academy Awards
				# Golden Globe Awards
				# Los Angeles Film Critics' Association
				# National Board of Review
				# National Society of Film Critics
				# New York Film Critics' Circle
				# Annie Awards
				# Golden Raspberry Awards
				# Sundance Film Festival
				# Screen Actors Guild Awards
				# Hollywood Film Awards
				# Directors Guild of America Awards
				# Tony Awards
				# Pulitzer Prize
				# MTV
				# Satellite Awards
				# AFI Awards
				# Critics Choice Awards
				# Black Reel Awards
				# AARP Movies for Grownups Awards
				# North Carolina Film Critics Association
				# Columbus Film Critics Association
				# Austin Film Critics Association
				# Allywood Film Critics Association Awards
				# Music City Film Critics' Association Awards
				# San Diego Film Critics Society Awards
				# Set Decorators Society of America, USA
				# Critics Association of Central Florida Awards
				# Hawaii Film Critics Society
				# Georgia Film Critics Association (GAFCA)
				# Portland Critics Association Awards
				# Chicago Indie Critics Awards (CIC)
				# North Dakota Film Society
				# Seattle Film Critics Society
				# Denver Film Critics Society
				# Motion Picture Sound Editors
				# Houston Film Critics Society Awards
				# PGA Awards
				# Cinema Audio Society
				# Costume Designers Guild Awards
				# Casting Society of America
				# Gold Derby Awards
				# Visual Effects Society Awards
				# Kids' Choice Awards
				# Grammy Awards
				'us' : '([\s\,\.\-\(\[]+(usa?)[\s\.\)\]]?|united\s*states|america|los\s*angeles|new\s*york|carolina|florida|hawaii|dakota|denver|columbus|austin|san\s*diego|portland|chicago|seattle|houston|hollywood|allywood|academy\s*award|oscar|golden\s*globe|emm(?:y|ie)\s|national\s*board.*review|national\s*society.*critic|annie\s|raspberr|sundance|screen.*actor.*guild|tony\s*award|pulitzer|mtv|satellite\s*ward|afi\s*ward|critics\s*choice|black\s*reel|aarp|music\s*city|gafca|georgia\s*film\s*critics|motion \s*picture\s*sound\s*editors|pga\s*award|cinema\s*audio\s*society|costume\s*designers\s*guild|golden\s*derby|visual\s*effects\s*society|kid.*choice|grammy)',

				# BAFTA Film Awards
				'uk' : '([\s\,\.\-\(\[]+(uk|gb)[\s\.\)\]]?|great\s*britain|united\s*kingdom|london|liverpool|bafta)',

				# Golden Screen Award
				'ca' : '(canada|canadian|golden\s*screen\s*award)',

				# AACTA International Awards
				'au' : '(australia|sydney|perthaacta)',

				# Palme d’Or – The Cannes International Film Festival
				# César Awards
				# Méliès d’Or
				# Cartoon d’Or
				'fr' : '(france|french|paris|d(?:\'|’)or|palme.*or|cannes|c(?:é|e)sar)',

				# The Golden Bear – The Berlin International Film Festival
				'de' : '(german|deutsch|golden(?:er)?\s*b(?:ea|ä)r|berlin|m(?:u|ue|ü)nchen)',

				# The Golden Leopard
				'ch' : '(golden(?:er)?\s*leopard)',

				# National Film Awards
				# FilmFare Awards
				'in' : '(india|hindi|national\s*film\s*award|film\s*fare)',
			}

			result = {
				'count' : {
					'total' : None,
					'wins' : None,
					'losses' : None,
					'nominations' : None,
				},
				'awards' : [],
			}

			self._extract(id = id, data = data, keys = ['winsCount'], result = result['count'], attribute = 'wins')
			self._extract(id = id, data = data, keys = ['nominationsCount'], result = result['count'], attribute = 'nominations')

			try: data = data['categories']
			except:
				self._fatal(id = id, code = 'details-awards-b')
				return result

			for item in data:
				try:
					entry = {
						'name' : None,
						'country' : None,
						'awards' : [],
					}

					name = self._extract(id = id, data = item, keys = ['name'])

					for country, expression in countries.items():
						if Regex.match(data = name, expression = expression):
							entry['country'] = country
							break

					entry['name'] = Regex.remove(data = name, expression = '([\s\,\.\-\(\[]*(usa?|uk|gb|de)[\s\.\)\]]*$)')

					if 'section' in item:
						item = item['section']
						if 'items' in item:
							item = item['items']
							if item:
								for subitem in item:
									subentry = {
										'award' : None,
										'type' : None,
										'year' : None,
										'category' : None,
										'subcategory' : None,
										'people' : [],
									}

									type = self._extract(id = id, data = subitem, keys = ['rowTitle'])

									year = Regex.extract(data = type, expression = '((?:19|2[01])\d{2})')
									if year: subentry['year'] = int(year)

									if Regex.match(data = type, expression = '(winner)'): subentry['type'] = 'winner'
									elif Regex.match(data = type, expression = '(nominee)'): subentry['type'] = 'nominee'

									self._extract(id = id, data = subitem, keys = ['rowSubTitle'], result = subentry, attribute = 'award')
									if 'listContent' in subitem:
										content = subitem['listContent']
										if content:
											expression = '\s*(?:[\(\[]|[\,\-]\s)\s*(.*?)[\s\)\]]*$'
											for i in content:
												if i and 'className' in i and i['className'] == 'awardCategoryName':
													category = self._extract(id = id, data = i, keys = ['text'])
													if category:
														subcategory = Regex.extract(data = category, expression = expression)
														if subcategory:
															subentry['category'] = Regex.remove(data = category, expression = expression)
															subentry['subcategory'] = subcategory
														else:
															subentry['category'] = category
														break
									if 'subListContent' in subitem:
										content = subitem['subListContent']
										if content:
											for i in content:
												i = self._extract(id = id, data = i, keys = ['text'])
												if i: subentry['people'].append(i)
									entry['awards'].append(subentry)
					result['awards'].append(entry)
				except:
					Logger.error()
					self._fatal(id = id, code = 'details-awards-c')

			return result
		except:
			Logger.error()
			return self._fatal(id = id, code = 'details-awards-z')
