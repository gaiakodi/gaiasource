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
from lib.modules.tools import Logger, Converter, Tools, Regex

from lib.meta.tools import MetaTools

class MetaImdb(object):

	Debug			= False # Disable debugging, since many smaller movies have many missing attributes.

	LinkTitle		= 'https://imdb.com/title/%s'
	LinkSeason		= 'https://imdb.com/title/%s/episodes?season=%d'

	CacheDetails	= Cache.TimeoutWeek1
	CacheList		= Cache.TimeoutWeek1
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
	def link(self, id = None, season = None, metadata = None):
		if metadata:
			try:
				id = metadata['id']['episode']['imdb']
				if id: return MetaImdb.LinkTitle % id
			except: pass
			try:
				id = metadata['id']['imdb']
				season = metadata['season']
			except: pass

		if id:
			if season: return MetaImdb.LinkSeason % (id, season)
			else: return MetaImdb.LinkTitle % id

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
	def _fatal(self, id = None):
		Logger.log('IMDB DATA%s: The structure of the IMDb data has changed and cannot be processed anymore. Please contact the Gaia developer if you see this message.' % (' [%s]' % id) if id else '', type = Logger.TypeFatal)
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
	def _extract(self, result, data, attribute, keys, function = None, id = None, log = True):
		for i in data:
			try:
				value = Tools.dictionaryGet(dictionary = i, keys = keys)
				if not value is None:
					if function: value = function(value)
					result[attribute] = value
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
					try: result.append(item['credits'][0]['name']['nameText']['text'])
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
		except: return self._fatal(id = id)

		data = []
		try: data.append(datas['mainColumnData'])
		except: pass
		try: data.append(datas['aboveTheFoldData'])
		except: pass
		if not data: return self._fatal(id = id)

		result = {}
		finance = {}
		tempImdb = {}
		tempMetacritic = {}

		self._extract(id = id, result = result, data = data, attribute = 'imdb', keys = ['id'])
		if 'imdb' in result:
			id = result['imdb']
			result['id'] = {'imdb' : result['imdb']}
		else: return self._fatal(id = id)

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
		if data is None:
			if link is None and id:
				if season == 0: return None
				link = self.link(id = id, season = season)
			if link: data = self.retrieve(link = link, timeout = MetaImdb.CacheDetails if cache else MetaImdb.CacheNone)
		if not data: return None

		result = []
		try:
			from lib.modules.convert import ConverterTime
			months = {'Jan' : '01', 'Feb' : '02', 'Mar' : '03', 'Apr' : '04', 'May' : '05', 'Jun' : '06', 'Jul' : '07', 'Aug' : '8', 'Sep' : '09', 'Oct' : '10', 'Nov' : '11', 'Dec' : '12'}

			parser = Parser(data = data, parser = Parser.ParserHtml)
			episodes = parser.find('div', {'class' : 'eplist'})

			# Some shows have no listed episodes.
			# Eg: https://www.imdb.com/title/tt21871318/
			if not episodes: return None

			episodes = episodes.find_all('div', {'class' : 'list_item'})
			if not episodes: return self._fatal(id = id)

			try:
				show = parser.find('div', {'class' : 'subpage_title_block'}).find('a', {'itemprop' : 'url'})
				showId = Regex.extract(data = show['href'], expression = '(tt\d+)[^\d]')
				showTitle = show.text
			except:
				showId = None
				showTitle = None

			for episode in episodes:
				resultEpisode = {}
				resultTemp = {}

				if showId: resultEpisode['id'] = {'imdb' : showId}
				if showTitle: resultEpisode['tvshowtitle'] = showTitle

				name = episode.find('a', {'itemprop' : 'name'})
				if name:
					idEpisode = Regex.extract(data = name['href'], expression = '(tt\d+)[^\d]')
					if idEpisode:
						if not resultEpisode['id']: resultEpisode['id'] = {}
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
			return self._fatal(id = id)
