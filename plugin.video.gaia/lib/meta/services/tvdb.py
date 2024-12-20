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

# https://thetvdb.github.io/v4-api

from lib.meta.data import MetaData
from lib.meta.service import MetaService

from lib.modules.tools import Converter, Settings, System, Language, Country, Tools, Regex, Logger, Media
from lib.modules.network import Networker
from lib.modules.account import Tvdb as Account
from lib.modules.cache import Cache
from lib.modules.concurrency import Lock

class MetaTvdb(MetaService):

	# Provider

	Provider				= 'tvdb'

	# Link

	LinkApi					= 'https://api4.thetvdb.com/v4'
	LinkImage				= 'https://artworks.thetvdb.com'
	LinkSearch				= 'https://thetvdb.com/search?query=%s'

	LinkMovieId				= 'https://thetvdb.com/dereferrer/movie/%s'
	LinkMovieTitle			= 'https://thetvdb.com/movies/%s'
	LinkShowId				= 'https://thetvdb.com/dereferrer/series/%s'
	LinkShowTitle			= 'https://thetvdb.com/series/%s'
	LinkSeasonId			= 'https://thetvdb.com/dereferrer/season/%s'
	LinkSeasonTitle			= 'https://thetvdb.com/series/%s/seasons/official/%s'
	LinkEpisodeId			= 'https://thetvdb.com/dereferrer/episode/%s'
	LinkEpisodeTitle		= 'https://thetvdb.com/series/%s/episodes/%s'

	# Cache

	CacheToken				= Cache.TimeoutMonth1 # Tokens are valid for 1 month according to API documentation.
	CacheTypes				= Cache.TimeoutMonth3

	# Status

	StatusSuccess			= 'success'
	StatusError				= 'failure'

	# Parameter

	ParameterLogin			= 'login'
	ParameterSearch			= 'search'
	ParameterMovies			= 'movies'
	ParameterSeries			= 'series'
	ParameterSeasons		= 'seasons'
	ParameterEpisodes		= 'episodes'
	ParameterPeople			= 'people'
	ParameterCharacters		= 'characters'
	ParameterCompanies		= 'companies'
	ParameterLanguages		= 'languages'
	ParameterArtwork		= 'artwork'
	ParameterGenres			= 'genres'
	ParameterSources		= 'sources'
	ParameterPeople			= 'people'
	ParameterCompanies		= 'companies'
	ParameterType			= 'type'
	ParameterTypes			= 'types'
	ParameterExtended		= 'extended'
	ParameterMeta			= 'meta'
	ParameterTranslations	= 'translations'
	ParameterQuery			= 'query'
	ParameterRemoteId		= 'remote_id'
	ParameterYear			= 'year'
	ParameterLimit			= 'limit'
	ParameterOffset			= 'offset'
	ParameterContent		= 'content'
	ParameterRatings		= 'ratings'
	ParameterStatuses		= 'statuses'

	# Origin

	OriginOfficial			= 'official'
	OriginUnofficial		= 'unofficial'
	OriginFanmade			= 'fanmade'
	OriginNone				= None

	# Vote

	VoteNone				= 0
	VoteMain				= 1
	VoteWorst				= -1
	VoteMaximum				= 99999

	# Special
	# Cannot find these in the API.
	# https://thetvdb.com/taxonomy
	Special					= {
		277					: MetaData.SpecialImportant,
		278					: MetaData.SpecialUnimportant,
		4447				: MetaData.SpecialBehind,
		4448				: MetaData.SpecialBlooper,
		4449				: MetaData.SpecialInterview,
		4450				: MetaData.SpecialCrossover,
		4451				: MetaData.SpecialMaking,
		4452				: MetaData.SpecialOriginal,
		4453				: MetaData.SpecialPilot,
		4454				: MetaData.SpecialRecap,
		4455				: MetaData.SpecialMovie,
		4456				: MetaData.SpecialShort,
		4458				: MetaData.SpecialDeleted,
		4459				: MetaData.SpecialExtended,
		4460				: MetaData.SpecialEpisode,
	}

	# Lock

	AuthenticationLock		= Lock()
	AuthenticationHeader	= None

	# Data

	DataProvider			= None
	DataSeason				= None
	DataPerson				= None
	DataCompany				= None
	DataImage				= None
	DataGenre				= None
	DataCertificate			= None
	DataStatusMovie			= None
	DataStatusShow			= None

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		if settings:
			MetaTvdb.AuthenticationHeader = None

	###################################################################
	# LOG
	###################################################################

	@classmethod
	def _log(self, message, data1 = None, data2 = None, data3 = None, type = Logger.TypeError):
		if data1 and Tools.isStructure(data1): data1 = Converter.jsonTo(data1)
		if data2 and Tools.isStructure(data2): data2 = Converter.jsonTo(data2)
		if data3 and Tools.isStructure(data3): data3 = Converter.jsonTo(data3)
		Logger.log('TVDb %s: ' % message, data1, data2, data3, type = type)

	@classmethod
	def _error(self):
		Logger.error()

	###################################################################
	# REQUEST
	###################################################################

	@classmethod
	def _request(self, parts, data = None, method = None, authentication = True, cache = None):
		link = Networker.linkJoin(MetaTvdb.LinkApi, parts)

		headers = None
		if authentication: headers = self._authenticationHeader()

		# For the series endpoint: meta=translations,episodes
		if data:
			for key, value in data.items():
				if Tools.isArray(value):
					data[key] = ','.join(value)

		result = self._requestJson(link = link, headers = headers, data = data, method = method if method else Networker.MethodGet, type = Networker.DataJson, cache = cache)

		# Do not check the status, since company requests returns a 500 error, although the (partial) data is returned.
		# Might be a temporary problem.
		#if result and result['status'] == MetaTvdb.StatusSuccess:
		if result and 'data' in result:
			result = result['data']
			return result if result else None
		else:
			self._log('Request Failure', link, data, result)
			return None

	###################################################################
	# RETRIEVE
	###################################################################

	@classmethod
	def _retrieve(self, media, type, extended = False, translations = False, episodes = False, show = None, season = None, id = None, level = None):
		if id:
			parts = [type, id]
			if extended and level >= MetaService.Level2: parts.append(MetaTvdb.ParameterExtended)

			data = {}
			if translations or episodes:
				data[MetaTvdb.ParameterMeta] = []
				if translations and level >= MetaService.Level3: data[MetaTvdb.ParameterMeta].append(MetaTvdb.ParameterTranslations)

				# Only do this for exactly Level4 and not above Level4.
				# Since Level5 and higher will in any case make separate requests for episodes and this would only return unnecessary data.
				if episodes and level == MetaService.Level4: data[MetaTvdb.ParameterMeta].append(MetaTvdb.ParameterEpisodes)

			data = self._request(parts = parts, data = data)
			return self._process(media = media, data = data, show = show, season = season)
		return None

	###################################################################
	# AUTHENTICATION
	###################################################################

	@classmethod
	def authenticationVerify(self, pin = None):
		return bool(self._authenticationToken(pin = pin))

	@classmethod
	def _authenticationKey(self):
		return System.obfuscate(Settings.raw('internal.key.tvdb'))

	@classmethod
	def _authenticationPin(self):
		return Account.instance().dataPin()

	@classmethod
	def _authenticationToken(self, key = None, pin = None):
		if key is None: key = self._authenticationKey()
		if pin is None: pin = self._authenticationPin()
		data = self._request(cache = MetaTvdb.CacheToken, parts = MetaTvdb.ParameterLogin, data = {'apikey' : key, 'pin' : pin}, method = Networker.MethodPost, authentication = False)
		try: return data['token']
		except: return None

	@classmethod
	def _authenticationHeader(self, token = None):
		if MetaTvdb.AuthenticationHeader is None:
			MetaTvdb.AuthenticationLock.acquire()
			if MetaTvdb.AuthenticationHeader is None:
				if token is None: token = self._authenticationToken()
				MetaTvdb.AuthenticationHeader = Account.headerBearer(token = token)
			MetaTvdb.AuthenticationLock.release()
		return MetaTvdb.AuthenticationHeader

	###################################################################
	# EXTRACT
	###################################################################

	@classmethod
	def _extract(self, data, type, attribute = False):
		if not Tools.isArray(type): type = [type]
		for i in type:
			try:
				if Tools.isArray(i):
					result = data
					for j in i:
						result = result[j]
				else:
					result = data[i]
				if not result is None:
					if attribute: return result, i
					else: return result
			except: pass
		if attribute: return None, None
		else: return None

	@classmethod
	def _extractContains(self, data, type):
		if not Tools.isArray(type): type = [type]
		for i in type:
			if Tools.isArray(i):
				for j in i:
					if not j in data:
						return False
				return True
			elif i in data:
				return True
		return False

	@classmethod
	def _extractMedia(self, data):
		result = self._extract(data = data, type = [
			'type',			# Search
			'recordType',	# Image
		])
		if result:
			result = MetaData.mediaExtract(result)
			if result: return result

		if self._extractContains(data = data, type = ['companyType', 'primaryCompanyType']): return MetaData.MediaCompany
		elif self._extractContains(data = data, type = ['birth', 'death', 'birthPlace', 'gender', 'races', 'personImgURL']): return MetaData.MediaPerson
		elif self._extractContains(data = data, type = ['peopleId', 'peopleType', 'personName']): return MetaData.MediaCharacter
		elif self._extractContains(data = data, type = ['boxOffice', 'budget', 'personName', 'releases']): return MetaData.MediaMovie
		elif self._extractContains(data = data, type = ['firstAired', 'lastAired', 'airsTime', 'airsDays']): return MetaData.MediaShow
		elif self._extractContains(data = data, type = [['number', 'seasonNumber']]): return MetaData.MediaEpisode
		elif self._extractContains(data = data, type = [['number', 'seriesId']]): return MetaData.MediaSeason # Check after episode.

		return None

	@classmethod
	def _extractId(self, data, media = None, all = True):
		if media is None:
			if all:
				ids = self._extract(data = data, type = [
					'remoteIds',
					'remote_ids',	# Search
				])
				if ids:
					result = {}
					for i in ids:
						try:
							try: provider = self._typeProvider(id = i['type'])
							except: provider = None

							# Search results have "type : 0".
							if not provider:
								name = self._extract(data = i, type = [
									'sourceName',
									'name',
								])
								if name: provider = MetaData.providerExtract(name)

							if provider:
								id = i['id']

								# TVDb sometimes has the TMDb as a slug, instead of the integer ID.
								# Eg: {"id": "105248-cyberpunk-edgerunners","type": 12,"sourceName": "TheMovieDB.com"}
								# Eg: {"id": "202297-fire-country","type": 12,"sourceName": "TheMovieDB.com"}
								if provider == MetaData.ProviderTmdb:
									try: int(id)
									except:
										try: id = Regex.extract(data = id, expression = '^\s*(\d+)\-')
										except: id = None

								if id: result[provider] = id
						except: pass
					return result
			else:
				result = self._extract(data = data, type = [
					'tvdb_id',	# Search - must be first, since it also has an "id" attribute
					'id',
				])
				if result: return result
		elif media == MetaData.MediaMovie:
			return self._extract(data = data, type = ['movieId'])
		elif media == MetaData.MediaShow:
			return self._extract(data = data, type = ['seriesId'])
		elif media == MetaData.MediaSeason:
			result = self._extract(data = data, type = ['seasonId'])
			if result:
				return result
			elif self._extractMedia(data = data) == MetaData.MediaEpisode: # Do not extract for shows.
				seasons = self._extract(data = data, type = ['seasons'])
				if seasons:
					for i in [self._typeSeasonPrimary(), self._typeSeasonSecondary()]:
						for j in seasons:
							type = self._extract(data = j, type = [['type', 'id']])
							if type == i: return self._extract(data = j, type = ['id'])
					return self._extract(data = seasons[0], type = ['id'])
		elif media == MetaData.MediaEpisode:
			return self._extract(data = data, type = ['episodeId'])
		elif media == MetaData.MediaPerson:
			return self._extract(data = data, type = ['peopleId', 'seriesPeopleId'])

		return None

	@classmethod
	def _extractTranslation(self, data, type, translation, aliases = None, language = None, extra = None, unknown = False):
		result = {}

		if language is None: language = self._extractLanguage(data = data, language = MetaData.LanguageOriginal, single = True)

		original = [[], [], []]
		try: original[0].append(data[type])
		except: pass
		result[MetaData.LanguageUniversal] = original

		# In Search, aliases is a list of foreign title strings.
		# This will fail (since they are no dictionaries), and it should, since we do not want to add them if we do not know the language.
		# Only allow non-language aliases for characters, persons, and companies.
		try:
			for i in data[aliases]:
				if Tools.isDictionary(i):
					try: code = Language.code(i['language'])
					except: pass
					i = i['name']
				if not code:
					if unknown: code = MetaData.LanguageUniversal
					else: continue
				if not code in result: result[code] = [[], [], []]
				result[code][2].append(i)
		except: pass

		try:
			for i in self._extract(data = data, type = [['translations', translation]]):
				code = Language.code(i['language'])
				if code:
					value = i[type]
					primary = self._extract(data = i, type = ['isPrimary', 'IsPrimary'])
					alias = self._extract(data = i, type = ['isAlias', 'IsAlias'])
					aliasAssumed = False

					# Some languages have multiple names, where the first name is the same as the original name.
					# Prefer the non-original name, except if it is the original language.
					# Example:
					#	French = ["Game of Thrones", "Le Trône de fer"]
					#	English = ["Game of Thrones", "GOT"]
					# Some are also not marked as IsPrimary, but still contains IsAlias titles.
					# Example (we rather want to pick Liaison above Bonding):
					#	{"name": "Liaison", "language": "fra", "isPrimary": true}
					#	{"name": "Liaison", "language": "eng"}
					#	{"name": "Bonding", "isAlias": true, "language": "eng"}
					if not alias:
						if value in original[0] or value in original[1] or value in original[2]:
							if not code == language:
								if code == Language.CodeEnglish and not primary: aliasAssumed = True
								else: alias = True

					if not code in result: result[code] = [[], [], []]
					if primary: result[code][0].append(value)
					elif aliasAssumed and not alias: result[code][1].append(value)
					elif alias: result[code][2].append(value)
					else: result[code][1].append(value)
					try:
						value = i[aliases]
						if Tools.isDictionary(value):
							try:
								code = Language.code(value['language'])
								if not code in result: result[code] = [[], [], []]
							except: pass
							value = value['name']
						result[code][2].extend(value)
					except: pass
		except: pass

		# Search
		try:
			for key, value in self._extract(data = data, type = [extra]).items():
				code = Language.code(key)
				if code:
					if not code in result: result[code] = [[], [], []]
					try: result[code][2].append(value)
					except: pass
		except: pass

		if result:
			if language:
				if not language in result: result[language] = [[], [], []]
				result[language][0].extend(original[0])
				result[language][1].extend(original[1])
				result[language][2].extend(original[2])

			for key, value in result.items():
				value = value[0] + value[1] + value[2]
				value = [i for i in value if i]
				value = Tools.listUnique(value)
				result[key] = value

			filtered = {}
			for key, value in result.items():
				if value:
					# TVDb seems to have a bug.
					# If a season is retrieved and the season name is null, when retrieving the same season but with "extended", the name is sometimes the season type name.
					# Eg: https://api4.thetvdb.com/v4/seasons/567215/extended returns the season name as "Aired Order".
					# Remove these names.
					value = [i for i in value if not Regex.match(data = i, expression = '^(?:aired|dvd|absolute|alternate(?:\s*dvd)?|regional)\s*order$', cache = True)]
					if value: filtered[key] = value
			return filtered

		return None

	@classmethod
	def _extractTitle(self, data):
		return self._extractTranslation(data = data, type = 'name', translation = 'nameTranslations', aliases = 'aliases')

	@classmethod
	def _extractOverview(self, data):
		return self._extractTranslation(data = data, type = 'overview', translation = 'overviewTranslations', extra = 'overviews')

	@classmethod
	def _extractName(self, data, person = False):
		if person and 'personName' in data:
			type = 'personName'
			translation = None
			aliases = None
		else:
			type = 'name'
			translation = 'nameTranslations'
			aliases = 'aliases'
		return self._extractTranslation(data = data, type = type, translation = translation, extra = 'translations', aliases = aliases, unknown = True)

	@classmethod
	def _extractSlug(self, data):
		return self._extract(data = data, type = ['slug'])

	@classmethod
	def _extractNumber(self, data, media = None, number = None):
		if number:
			if media:
				if number == MetaData.NumberStandard: return self._extract(data = data, type = ['number'])
				elif number == MetaData.NumberAbsolute: return self._extract(data = data, type = ['number' if media == MetaData.MediaSeason else 'absoluteNumber'])
			else:
				type = self._typeSeason(number = number)
				if not type is None:
					seasons = self._extract(data = data, type = ['seasons'])
					if seasons:
						for season in seasons:
							try:
								if self._extract(data = season, type = [['type', 'id']]) == type:
									return self._extract(data = season, type = ['number'])
							except: Logger.error()
		else:
			return self._extract(data = data, type = ['seasonNumber' if media == MetaData.MediaSeason else 'number'])
		return None

	@classmethod
	def _extractLanguage(self, data, language = None, single = False):
		result = []

		if language == MetaData.LanguageOriginal:
			result.append(self._extract(data = data, type = ['originalLanguage']))
			result.append(self._extract(data = data, type = ['language']))
			result.append(self._extract(data = data, type = ['primary_language'])) # Search
		elif language == MetaData.LanguageAudio:
			result.append(self._extract(data = data, type = ['audioLanguages']))
			result.append(self._extract(data = data, type = ['spokenLanguages']))
			result.append(self._extract(data = data, type = ['spoken_languages']))
		elif language == MetaData.LanguageSubtitle:
			result.append(self._extract(data = data, type = ['subtitleLanguages']))

		if result:
			result = Tools.listFlatten(result)
			result = [Language.code(i) for i in result]
			result = [i for i in result if i]
			result = Tools.listUnique(result)
			if result: return result[0] if single else result

		return None

	@classmethod
	def _extractImage(self, data, person = False):
		result = []

		type = [
			'image',
			'image_url', # Search
		]

		media = self._extractMedia(data = data)

		# The character object can contain 2 images.
		# "image" is the character photo (photo from the show).
		# "personImgURL" is the actor photo (generic photo).
		if person: type.insert(0, 'personImgURL') # Makes sure it is before the character "image".

		link, attribute = self._extract(data = data, type = type, attribute = True)
		if link:
			link = self._linkImage(link = link)

			#gaiaremove
			# The latests TVDb update now has a bug that many of the season images from the series API call have the wrong image type (eg: image type is given as banner, although it is a poster).
			# Even when removing "self._extract(data = data, type = 'imageType')", there is another problem that sometimes TVDb returns the correct image type, but returns some other image.
			# For instance, GoT S04 returns the season fanart instead of the poster in the series API call for "Aired Order", and the German poster for "DVD Order", although the other seasons have the correct poster.
			# Check if this is fixed by TVDb in the future. Otherwise, maybe use the show poster for all seasons the first time the menu is loaded with the "quick loading" setting.
			# Maybe this is releated to the update here: https://github.com/thetvdb/v4-api/issues/224
			# Maybe now the highest res/vote image is returned for each season, irrespective of the image type.
			image = self._extractImageType(link = link, attribute = attribute, type = self._extract(data = data, type = 'imageType'))

			image['vote'] = MetaTvdb.VoteMain # Prefer the main image over others from "artworks" with a vote of 0.
			result.append(image)

			link = self._extract(data = data, type = [
				'thumbnail',
				'thumbnail_url',
			])
			if link:
				link = self._linkImage(link = link)
				image = Tools.copy(image)
				image.update({
					'link' : link,
					'quality' : MetaData.ImageQualityLow,
				})
				result.append(image)

		artworks = self._extract(data = data, type = [
			'artworks',
			'artwork',	# Season
		])
		if artworks:
			sortId = len(artworks)
			for i in range(len(artworks)): artworks[i]['index'] = sortId - i # For index-based sorting, before we sort by ID below.

			# TVDb previously returned the artwork in the same order as on the website. With a recent update this changed.
			# Sorting by ID seems to have the same order as on the website for season images.
			# Sorting by ID and vote (which is GroupingDefault in image.py) seems to have the same order for show images on the main show page.
			# Update: The order seems to be based on additional API parameters. The two calls have different artwork orders:
			#	seasons/473271/extended
			#	seasons/473271/extended?meta=translations
			artworks = sorted(artworks, key = lambda i : self._extract(data = i, type = 'id'))

			for artwork in artworks:
				sortId -= 1
				link = self._extract(data = artwork, type = 'image')
				if link:
					link = self._linkImage(link = link)
					image = self._extractImageType(link = link, type = self._extract(data = artwork, type = 'type'), data = artwork)

					# Some images have null as the language.
					# These are not English/Universal, but some other languages (eg: Avatar).
					# Set to unknown to only use if no English/Universal images are available.
					# Update: If no language should be assumed as Universal (eg: select fanart without any title), this does not work, since most plain/title-less fanart are still being marked as English (eg Rick & Morty).
					language = Language.code(self._extract(data = artwork, type = 'language'))
					if not language: language = MetaData.LanguageUnknown
					image['language'] = language

					vote = self._extract(data = artwork, type = 'score')
					if vote:
						try: vote = max(vote, image['vote'])
						except: pass
						image['vote'] = vote
					else:
						vote = 0

					# Orders are constructed from an array of values.
					#	[[media], [index, ID, origin, vote]]
					# Always make "better" values have a higher sort value, since they are sorted in descending order.
					# The first list is hardcoded. The second list can be changed in ascending or descending mode.
					# Give shows a higher order than seasons, and seasons a higher order than episodes.
					# Otherwise when sorting the posters for a show, it might pick a season poster, since the season poster order will be on the same level as show posters.
					# This is because TVDb returns both show and season (and sometimes a few episode) images from the main show API request.

					sortIndex = artwork['index']

					sortOrigin = 0
					if image['set'] == MetaTvdb.OriginOfficial: sortOrigin = 3
					elif image['set'] == MetaTvdb.OriginUnofficial: sortOrigin = 2
					elif image['set'] == MetaTvdb.OriginFanmade: sortOrigin = 1

					sortMedia = 0
					mediaItem = image['media']
					if not mediaItem: mediaItem = media
					if mediaItem == MetaData.MediaEpisode: sortMedia = 1
					elif mediaItem == MetaData.MediaSeason: sortMedia = 2
					elif mediaItem == MetaData.MediaShow: sortMedia = 3

					image['sort'] = {
						MetaData.SortNone :				[[sortMedia], [0]],
						MetaData.SortIndex :			[[sortMedia], [sortIndex]],
						MetaData.SortId :				[[sortMedia], [sortId]],

						MetaData.SortVote :				[[sortMedia], [vote]],
						MetaData.SortVoteIndex :		[[sortMedia], [vote, sortIndex]],
						MetaData.SortVoteId :			[[sortMedia], [vote, sortId]],
						MetaData.SortVoteOrigin :		[[sortMedia], [vote, sortOrigin]],
						MetaData.SortVoteOriginIndex :	[[sortMedia], [vote, sortOrigin, sortIndex]],
						MetaData.SortVoteOriginId :		[[sortMedia], [vote, sortOrigin, sortId]],

						MetaData.SortOrigin :			[[sortMedia], [sortOrigin]],
						MetaData.SortOriginIndex :		[[sortMedia], [sortOrigin, sortIndex]],
						MetaData.SortOriginId :			[[sortMedia], [sortOrigin, sortId]],
						MetaData.SortOriginVote :		[[sortMedia], [sortOrigin, vote]],
						MetaData.SortOriginVoteIndex :	[[sortMedia], [sortOrigin, vote, sortIndex]],
						MetaData.SortOriginVoteId :		[[sortMedia], [sortOrigin, vote, sortId]],
					}

					try:
						id = self._extractId(data = artwork, media = image['media'])
						if id: image['id'] = id
					except: pass

					result.append(image)

					link = self._extract(data = artwork, type = ['thumbnail'])
					if link:
						link = self._linkImage(link = link)
						image = Tools.copy(image)
						image.update({
							'link' : link,
							'quality' : MetaData.ImageQualityLow,
						})
						result.append(image)

		# Do not extract season images from the 'seasons' sub-dictionary when retrieving episodes.
		# Otherwise the eg season poster is seen as the episode poster.
		# Some views/skins might then display this poster instead of using the poster from a higher level (eg: tvshow.poster).
		'''if media == MetaData.MediaEpisode:
			seasons = self._extract(data = data, type = 'seasons')
			if seasons:
				primary = self._typeSeasonPrimary()
				for season in seasons:
					link = self._extract(data = season, type = 'image')
					if link:
						link = self._linkImage(link = link)
						image = self._extractImageType(link = link, type = self._extract(data = season, type = 'type'), data = season)

						vote = 0
						if not self._extract(data = season, type = [['type', 'id']]) == primary: vote = MetaTvdb.VoteWorst
						if vote:
							try: image['vote'] = max(vote, image['vote'])
							except: image['vote'] = vote

						try:
							id = self._extractId(data = season, media = image['media'])
							if id: image['id'] = id
						except: pass

						result.append(image)

						link = self._extract(data = season, type = ['thumbnail'])
						if link:
							link = self._linkImage(link = link)
							image = Tools.copy(image)
							image.update({
								'link' : link,
								'quality' : MetaData.ImageQualityLow,
							})
							result.append(image)'''

		if result:
			# If there are duplicate entries (eg: main image might also be in the "artworks" array).
			# The main image might somtimes have the incorrect image type (eg: The Boys S01 has a banner set as poster).
			# Update earlier image entries with the data of later ones.
			images = {}
			for image in result:
				if image and image['link']:
					if image['link'] in images: Tools.dictionaryMerge(images[image['link']], image, copy = False, none = False)
					else: images[image['link']] = image
			images = list(images.values())

			return images
		return None

	@classmethod
	def _extractImageType(self, link, attribute = None, type = None, data = None):
		id = None
		descriptor = None
		media = None
		vote = None
		sort = None

		# To avoid incorrect classification (art and banner).
		path = Networker.linkPath(link = link, parameters = True)
		path = Tools.stringRemovePrefix(path, 'banners')

		if data: id = self._extract(data = data, type = 'id')

		match = Regex.extract(data = path, expression = '\/?([a-z]+)(?<!posters)\/', cache = True)
		if match: media = MetaData.mediaExtract(match)

		match = Regex.extract(data = path, expression = '\/([a-z\d\-\_]+)\.[a-z]{3,4}$', cache = True)
		if match: descriptor = match

		'''
			There is not way to determine which season posters belong together as a set.
			Even if a method is found to group posters, it will only work for some shows and not others.
			If changes are made, always check the shows:
				Game Of Thrones
				Rick & Morty
				Breaking Bad
				Peaky Blinders
			NOTE: When loading a season menu for the firt time, the default posters are shown. Only after reloading the mneu, the detailed/extended info posters are loaded.

			Images on the website have an upload username, which is not available through the API (even with the extended artwork endpoint).
			Even with the username, it is not always reliable, because a user can upload multiple sets.

			Often just using the first image is a good method, but there are exceptions.
			For instance, poster sets often have not associated poster for specials (season 0). Eg: Game of Thrones.
			Some users also upload a posters from a sset for seasons already released. But later if a new season comes out, the user might not upload new posters. Eg: Peaky Blinders (last season).

			There seems to be 3 types of season posters:
				Type 1:
					These are generally good posters. Probably official posters, or uploaded by admins/mods.
						series/<Show ID>/seasons/<Season ID>/posters/<Poster ID - numeric>.jpg
				Type 2:
					These are generally good posters. Probably official posters, or uploaded by admins/mods.
						seasons/<Poster ID - alphanumeric>.jpg
				Type 3:
					These are generally language-specific, fanmade, and/or user uploaded.
					There is no consistent way to group them.
					For instance, not all posters without an index belong together.
					Even those with the same index do not always belong together.
					It seems the first user to upload a poster is assigned the ID without an index, and every subsequent upload gets the index incremented.
						seasons/<Show ID>-<Season Number>.jpg
						seasons/<Show ID>-<Season Number>-<Index/Count Number>.jpg

			GAME OF THRONES
				SET 1
					Show:		ID: XXXXXXXX	Link:
					Season 0:	ID: 62035582	Link: https://artworks.thetvdb.com/banners/series/121361/seasons/137481/posters/62035582.jpg
					Season 1:	ID: 62035572	Link: https://artworks.thetvdb.com/banners/series/121361/seasons/364731/posters/62035572.jpg
					Season 2:	ID: 62035574	Link: https://artworks.thetvdb.com/banners/series/121361/seasons/473271/posters/62035574.jpg
					Season 3:	ID: 62035576	Link: https://artworks.thetvdb.com/banners/series/121361/seasons/488434/posters/62035576.jpg
					Season 4:	ID: 62035577	Link: https://artworks.thetvdb.com/banners/series/121361/seasons/568657/posters/62035577.jpg
					Season 5:	ID: 62035578	Link: https://artworks.thetvdb.com/banners/series/121361/seasons/607490/posters/62035578.jpg
					Season 6:	ID: 62035579	Link: https://artworks.thetvdb.com/banners/series/121361/seasons/651357/posters/62035579.jpg
					Season 7:	ID: 62035580	Link: https://artworks.thetvdb.com/banners/series/121361/seasons/703353/posters/62035580.jpg
					Season 8:	ID: 62035581	Link: https://artworks.thetvdb.com/banners/series/121361/seasons/793782/posters/62035581.jpg
				SET 2
					Show:		ID: 1352023		Link: https://artworks.thetvdb.com/banners/posters/5ca4ff0dea43a.jpg	(multiple alternative posters by same user starting with '5c7' or '5ca')
					Season 0:	ID: 61100621	Link: https://artworks.thetvdb.com/banners/seasons/5cc751ad03661.jpg
					Season 1:	ID: 61100636	Link: https://artworks.thetvdb.com/banners/seasons/5cc751cfeb87d.jpg
					Season 2:	ID: 61100664	Link: https://artworks.thetvdb.com/banners/seasons/5cc751f2f3b33.jpg
					Season 3:	ID: XXXXXXXX	Link: https://artworks.thetvdb.com/banners/seasons/5cc752208d21c.jpg
					Season 4:	ID: XXXXXXXX	Link: https://artworks.thetvdb.com/banners/seasons/5cc7524ff0bab.jpg
					Season 5:	ID: XXXXXXXX	Link: https://artworks.thetvdb.com/banners/seasons/5cc75288f1efc.jpg
					Season 6:	ID: XXXXXXXX	Link: https://artworks.thetvdb.com/banners/seasons/5cc752a358f31.jpg
					Season 7:	ID: XXXXXXXX	Link: https://artworks.thetvdb.com/banners/seasons/5cc75340ed474.jpg
					Season 8:	ID: XXXXXXXX	Link: https://artworks.thetvdb.com/banners/seasons/5cc753658f055.jpg
				SET 3
					Show:		ID: XXXXXXXX	Link:
					Season 0:	ID: XXXXXXXX	Link:
					Season 1:	ID: 62035564	Link: https://artworks.thetvdb.com/banners/series/121361/seasons/364731/posters/62035563.jpg
					Season 2:	ID: 62035564	Link: https://artworks.thetvdb.com/banners/series/121361/seasons/473271/posters/62035564.jpg
					Season 3:	ID: 62035566	Link: https://artworks.thetvdb.com/banners/series/121361/seasons/488434/posters/62035566.jpg
					Season 4:	ID: 62035567	Link: https://artworks.thetvdb.com/banners/series/121361/seasons/568657/posters/62035567.jpg
					Season 5:	ID: 62035568	Link: https://artworks.thetvdb.com/banners/series/121361/seasons/607490/posters/62035568.jpg
					Season 6:	ID: 62035569	Link: https://artworks.thetvdb.com/banners/series/121361/seasons/651357/posters/62035569.jpg
					Season 7:	ID: 62035570	Link: https://artworks.thetvdb.com/banners/series/121361/seasons/703353/posters/62035570.jpg
					Season 8:	ID: 62035571	Link: https://artworks.thetvdb.com/banners/series/121361/seasons/793782/posters/62035571.jpg
				SET 4
					Show:		ID: XXXXXXXX	Link:
					Season 0:	ID: 61100594	Link: https://artworks.thetvdb.com/banners/seasons/121361-0-2.jpg
					Season 1:	ID: 61100626	Link: https://artworks.thetvdb.com/banners/seasons/121361-1-6.jpg
					Season 2:	ID: 61100650	Link: https://artworks.thetvdb.com/banners/seasons/121361-2.jpg
					Season 3:	ID: XXXXXXXX	Link: https://artworks.thetvdb.com/banners/seasons/121361-3.jpg
					Season 4:	ID: XXXXXXXX	Link: https://artworks.thetvdb.com/banners/seasons/121361-4.jpg
					Season 5:	ID: XXXXXXXX	Link: https://artworks.thetvdb.com/banners/seasons/121361-5-2.jpg
					Season 6:	ID: XXXXXXXX	Link: https://artworks.thetvdb.com/banners/seasons/121361-6.jpg
					Season 7:	ID: XXXXXXXX	Link: https://artworks.thetvdb.com/banners/seasons/121361-7-5.jpg
					Season 8:	ID: XXXXXXXX	Link: https://artworks.thetvdb.com/banners/seasons/5cb693e7d5443.jpg	(uploaded by a differnt user - admin)
		'''

		# Make sure the expressions work for both show and season images.
		extension = '\.[a-z]{3,4}$'
		set = MetaTvdb.OriginNone
		if Regex.match(data = path, expression = '(?:seasons|series)\/\d+\/posters\/\d+' + extension, cache = True): set = MetaTvdb.OriginOfficial
		elif Regex.match(data = path, expression = '(?:seasons|posters)\/[a-z\d]+' + extension, cache = True): set = MetaTvdb.OriginUnofficial
		elif Regex.match(data = path, expression = 'seasons\/[\d\-]+' + extension, cache = True): set = MetaTvdb.OriginFanmade

		result = {
			'id' : id,
			'descriptor' : descriptor,
			'set' : set,
			'link' : link,
			'vote' : vote,
			'sort' : sort,
			'language' : MetaData.LanguageUnknown,
			'media' : media if media else MetaData.mediaExtract(path),
			'type' : MetaData.imageTypeExtract(data = path),
			'quality' : MetaData.imageQualityExtract(data = path),
			'opacity' : MetaData.imageOpacityExtract(data = path),
		}

		# Some photos might seem like an actor photo instead of a person photo.
		# Eg: "personImgURL": "/banners/v4/actor/247926/photo/615513ba07bf7.jpg"
		if attribute == 'personImgURL':
			result['media'] = MetaData.MediaPerson

		if not type is None:
			type = self._typeImage(id = type)
			if type: result.update(type)

		result['decor'] = MetaData.imageDecorExtract(data = path, type = result['type'])

		return result

	@classmethod
	def _extractYear(self, data):
		result = self._extractReleaseFirst(data = data)
		if not result: result = self._extractReleaseDate(data = data) # Movie
		if not result: result = self._extract(data = data, type = ['birth']) # Person
		if result:
			result = MetaData.yearExtract(result)
			if result: return result
		return None

	@classmethod
	def _extractGenre(self, data):
		try:
			result = []
			for i in data['genres']:
				genre = None
				if Tools.isString(i): genre = MetaData.genreExtract(i) # Search
				else:
					genre = self._typeGenre(id = i['id'])
					if not genre: genre = MetaData.genreExtract(i['name'])
				if genre: result.append(genre)
			if result: return result
		except: pass
		return None

	@classmethod
	def _extractDuration(self, data):
		result = self._extract(data = data, type = [
			'runtime',
			'averageRuntime',
		])
		if not result is None: return int(result)
		return None

	@classmethod
	def _extractBudget(self, data):
		result = self._extract(data = data, type = ['budget'])
		if result: return float(result)
		return None

	@classmethod
	def _extractIncome(self, data):
		result = self._extract(data = data, type = ['boxOffice'])
		if result: return float(result)
		return None

	@classmethod
	def _extractVote(self, data):
		result = self._extract(data = data, type = ['score'])
		if not result is None: return float(result)

		result = self._extract(data = data, type = ['sort']) # Character
		if not result is None:
			result = int(result)
			if result == 0: return result # None-sorted items have a value of 0.
			return MetaTvdb.VoteMaximum - int(result) # Sorted items start from 1 and lower values should be placed first, therefore subtract from VoteMaximum.

		return None

	@classmethod
	def _extractStatus(self, data, media):
		try:
			id = data['status']['id']
			if media == MetaData.MediaMovie: return self._typeStatusMovie(id = id)
			elif media == MetaData.MediaShow: return self._typeStatusShow(id = id)
		except: return None

	@classmethod
	def _extractSpecial(self, data, media, show = None, season = None):
		try:
			special = []

			if 'tagOptions' in data and data['tagOptions']:
				for i in data['tagOptions']:
					try: special.append(MetaTvdb.Special[i['id']])
					except: pass

			if 'isMovie' in data and data['isMovie']: special.append(MetaData.SpecialMovie)

			if 'name' in data and data['name']:
				# Maybe not absolutely necessary to exclude show titles from detection, but it might be useful in rare cases where these keywords appear in the title.
				exclude = None
				if show:
					try:
						titles = show.title(language = True, selection = MetaData.SelectionList)
						exclude = []
						for key, value in titles.items():
							exclude.extend(value)
						exclude = Tools.listUnique(exclude)
					except: pass

				extracted = MetaData.specialExtract(data = data['name'], exclude = exclude)
				if extracted: special.extend(extracted)

			before = {}
			season = data.get('airsBeforeSeason')
			if not season is None: before['season'] = season
			episode = data.get('airsBeforeEpisode')
			if not episode is None: before['episode'] = episode

			after = {}
			season = data.get('airsAfterSeason')
			if not season is None: after['season'] = season
			episode = data.get('airsAfterEpisode')
			if not episode is None: after['episode'] = episode

			return {
				'type' : Tools.listUnique(special) if special else None,
				'before' : before if before else None,
				'after' : after if after else None,
			}
		except:
			Logger.error()
			return None

	@classmethod
	def _extractReleaseCountry(self, data):
		result = self._extract(data = data, type = [
			'originalCountry',	# Movie and Show
			'country',			# Search
		])
		if result: return MetaData.releaseCountryExtract(result)
		return None

	@classmethod
	def _extractReleaseZone(self, data):
		country = self._extractReleaseCountry(data = data)
		if country: return Country.zone(country)
		return None

	@classmethod
	def _extractReleaseTime(self, data):
		result = self._extract(data = data, type = ['airsTime'])
		if result:
			return {'time' : result, 'zone' : None}
		else:
			result = self._extract(data = data, type = ['airsTimeUTC'])
			if result: return {'time' : result, 'zone' : MetaData.AirZoneUtc}
		return None

	@classmethod
	def _extractReleaseDate(self, data):
		try:
			for i in ['global', 'usa', self._extractReleaseCountry(data = data)]:
				for j in data['releases']:
					try:
						if j['country'] == i:
							result = j['date']
							if result: return result
					except: pass
			result = data['releases'][0]['date']
			if result: return result
		except: pass
		return None

	@classmethod
	def _extractReleaseFirst(self, data):
		return self._extract(data = data, type = [
			'firstAired',
			'first_air_time',	# Search
			'aired',			# Episode
		])

	@classmethod
	def _extractReleaseLast(self, data):
		return self._extract(data = data, type = ['lastAired'])

	@classmethod
	def _extractReleaseNext(self, data):
		return self._extract(data = data, type = ['nextAired'])

	@classmethod
	def _extractReleaseDay(self, data):
		result = self._extract(data = data, type = ['airsDays'])
		if result:
			result = [MetaData.releaseDayExtract(k) for k, v in result.items() if v]
			return [i for i in result if i]
		return None

	@classmethod
	def _extractCertificate(self, data):
		result = self._extract(data = data, type = ['contentRatings'])
		if result:
			result = [self._typeCertificate(i['id']) for i in result]
			return [i for i in result if i]
		return None

	###################################################################
	# PROCESS
	###################################################################

	@classmethod
	def _process(self, media, data, show = None, season = None):
		try:
			if data:
				if media is MetaData.MediaDefault: media = self._extractMedia(data = data)
				metadata = MetaData(media = media)

				if metadata.mediaContent(): self._processContent(metadata = metadata, data = data, show = show, season = season)
				elif metadata.mediaPerson(): self._processPerson(metadata = metadata, data = data)
				elif metadata.mediaCharacter(): self._processCharacter(metadata = metadata, data = data, single = True)
				elif metadata.mediaCompany(): self._processCompany(metadata = metadata, data = data)

				return metadata
		except: self._error()
		return None

	@classmethod
	def _processContent(self, metadata, data, show = None, season = None):
		self._processShow(metadata = metadata, data = data)
		self._processSeason(metadata = metadata, data = data)
		self._processEpisode(metadata = metadata, data = data)

		self._processId(metadata = metadata, data = data)
		self._processSlug(metadata = metadata, data = data)
		self._processNumber(metadata = metadata, data = data)

		# Do first, since other functions require these values.
		self._processLanguage(metadata = metadata, data = data) # Needed by title, overview, etc.
		self._processRelease(metadata = metadata, data = data) # Needed by air date and time (time zones).

		self._processTitle(metadata = metadata, data = data)
		self._processOverview(metadata = metadata, data = data)
		self._processYear(metadata = metadata, data = data)

		self._processGenre(metadata = metadata, data = data)

		self._processCharacter(metadata = metadata, data = data)
		self._processCompany(metadata = metadata, data = data)

		self._processVote(metadata = metadata, data = data)
		self._processStatus(metadata = metadata, data = data)
		self._processSpecial(metadata = metadata, data = data, show = show)
		self._processDuration(metadata = metadata, data = data)
		self._processMoney(metadata = metadata, data = data)
		self._processCertificate(metadata = metadata, data = data)

		# Do last, since some images are added to the characters.
		self._processImage(metadata = metadata, data = data)

	@classmethod
	def _processShow(self, metadata, data):
		try:
			if metadata.mediaSeason() or metadata.mediaEpisode():
				metadata.showSet(value = MetaData(media = MetaData.MediaShow))
		except: self._error()

	@classmethod
	def _processSeason(self, metadata, data):
		try:
			if 'seasons' in data and data['seasons']:
				primary = self._typeSeasonPrimary()
				if metadata.mediaShow():
					type = None
					for i in data['seasons']:
						if i['type']['id'] == primary:
							type = i['type']['id']
							break
					if type is None:
						secondary = self._typeSeasonSecondary()
						for i in data['seasons']:
							if i['type']['id'] == secondary:
								type = i['type']['id']
								break
						if type is None:
							type = data['seasons'][0]['type']['id']
					if type:
						seasons = []
						for i in data['seasons']:
							if i['type']['id'] == type:
								season = self._process(media = MetaData.MediaSeason, data = i)
								if season: seasons.append(season)
						if seasons: metadata.seasonSet(value = seasons)
				elif metadata.mediaEpisode():
					season = None
					for i in data['seasons']:
						if i['type']['id'] == primary:
							season = i
							break
					if season is None:
						try: season = data['seasons'][0]
						except: pass
					if not season is None:
						season = self._process(media = MetaData.MediaSeason, data = season)
						if season: metadata.seasonSet(value = season)
		except: self._error()

	@classmethod
	def _processEpisode(self, metadata, data):
		try:
			if 'episodes' in data and data['episodes']:
				if metadata.mediaShow() or metadata.mediaSeason():
					episodes = []
					for i in data['episodes']:
						episode = self._process(media = MetaData.MediaEpisode, data = i)
						if episode: episodes.append(episode)
					if episodes: metadata.episodeSet(value = episodes)
		except: self._error()

	@classmethod
	def _processPerson(self, metadata, data):
		try:
			self._processId(metadata = metadata, data = data)

			# The character structure contains both the person and the character attributes.
			# Only do this for the person structure.
			if self._extractMedia(data = data) == MetaData.MediaPerson:
				self._processImage(metadata = metadata, data = data, person = True)
				self._processVote(metadata = metadata, data = data)

			self._processName(metadata = metadata, data = data)
			self._processCharacter(metadata = metadata, data = data)
		except:	pass

	@classmethod
	def _processCharacter(self, metadata, data, single = False):
		try:
			if 'characters' in data:
				if data['characters']: # Sometimes null.
					characters = []
					for i in data['characters']:
						character = self._process(media = MetaData.MediaCharacter, data = i)
						if character: characters.append(character)
					metadata.characterSet(value = characters)
			elif single:
				self._processId(metadata = metadata, data = data)
				self._processSlug(metadata = metadata, data = data)
				self._processName(metadata = metadata, data = data)
				self._processImage(metadata = metadata, data = data)

				try:
					person = self._typePerson(id = data['type'])
					metadata.typeSet(value = person['type'])
					metadata.roleSet(value = person['role'])
				except: pass

				person = self._process(media = MetaData.MediaPerson, data = data)
				if person: metadata.personSet(person)

				self._processVote(metadata = metadata, data = data)

			if 'director' in data: # Search
				person = self._process(media = MetaData.MediaCharacter, data = {'name' : data['director']})
				if person: metadata.personSet(person)
		except: Logger.error()

	@classmethod
	def _processCompany(self, metadata, data):
		try:
			if 'companies' in data:
				if data['companies']: # Sometimes null.
					# List the original network first in the array.
					# We use this fot showing the studio icons in the menus.
					# And we prefer the original network above networks that simply buy the rights later on or produce the last season of the show.
					try: original = data['originalNetwork']['id']
					except: original = False

					if Tools.isDictionary(data['companies']): data = Tools.listFlatten(data['companies'].values())
					else: data = data['companies']
					companies = []
					for i in data:
						company = self._process(media = MetaData.MediaCompany, data = i)
						if company:
							if i.get('id') == original: companies.insert(0, company)
							else: companies.append(company)
					metadata.companySet(value = companies)
			elif self._extractMedia(data = data) == MetaData.MediaCompany:
				self._processId(metadata = metadata, data = data)
				self._processSlug(metadata = metadata, data = data)
				self._processName(metadata = metadata, data = data)
				self._processImage(metadata = metadata, data = data)

				# Use the primaryCompanyType first, since they might indicate "studio", while companyTypeId might indicate "producer" ("Production Company").
				# But not all "Production Company" listed are studios. They might be visual effects, special effects, etc.
				type = None
				if not type:
					try: type = self._typeCompany(id = data['primaryCompanyType'])
					except: pass
				if not type:
					try: type = self._typeCompany(id = data['companyType']['companyTypeId'])
					except: pass

				if type: metadata.typeSet(value = type)
			else: # Search
				companies = []
				types = {
					MetaData.CompanyTypeNetwork : ['network', 'networks'],
					MetaData.CompanyTypeStudio : ['studio', 'studios'],
					MetaData.CompanyTypeProducer : ['production_company', 'production_companies', 'productioncompany', 'productioncompanies'],
					MetaData.CompanyTypeDistributor : ['distributor', 'distributors'],
					MetaData.CompanyTypeEffects : ['special_effect', 'special_effects', 'specialeffect', 'specialeffects'],
				}
				for key, value in types.items():
					try:
						names = None
						for v in value:
							try:
								names = data[v]
								break
							except: pass
						if names:
							if not Tools.isArray(names): names = [names]
							for i in names:
								company = MetaData(media = MetaData.MediaCompany)
								company.typeSet(value = MetaData.CompanyTypeNetwork)
								company.nameSet(value = i)
								companies.append(company)
					except: pass
				metadata.companySet(value = companies)
		except: Logger.error()

	@classmethod
	def _processId(self, metadata, data):
		metadata.idTvdbSet(value = self._extractId(data = data, all = False))

		metadata.idSet(value = self._extractId(data = data, all = True))

		if not metadata.mediaPerson(): # Do not extract if a person is extracted from character data.
			metadata.idMovieTvdbSet(value = self._extractId(data = data, media = MetaData.MediaMovie))
			metadata.idShowTvdbSet(value = self._extractId(data = data, media = MetaData.MediaShow))
			metadata.idSeasonTvdbSet(value = self._extractId(data = data, media = MetaData.MediaSeason))
			metadata.idEpisodeTvdbSet(value = self._extractId(data = data, media = MetaData.MediaEpisode))

		metadata.idPersonTvdbSet(value = self._extractId(data = data, media = MetaData.MediaPerson))

	@classmethod
	def _processSlug(self, metadata, data):
		metadata.slugSet(value = self._extractSlug(data = data))

	@classmethod
	def _processNumber(self, metadata, data):
		isSeason = metadata.mediaSeason()
		isEpisode = metadata.mediaEpisode()

		if isSeason or isEpisode:
			for number in MetaData.Numbers:
				value = self._extractNumber(data = data, number = number)
				if not value is None: metadata.numberSeasonSet(value = value, number = number)

		numberBase = self._extractNumber(data = data)
		metadata.numberSet(value = numberBase)

		numberParent = self._extractNumber(data = data, media = MetaData.MediaSeason)
		metadata.numberSeasonSet(value = numberParent)

		# TVDb only has absolute numbers for some shows (eg: Game of Thrones), but not others (eg: Foundation).
		# If not available, the absolute number is 0 (eg: Foundation). But it might also be null for others, not sure?
		# Only add the absolute number if not 0.
		if numberParent or (isSeason and numberBase):
			if isEpisode:
				number = self._extractNumber(data = data, media = MetaData.MediaEpisode, number = MetaData.NumberAbsolute)
				if number: metadata.numberSet(value = number, number = MetaData.NumberAbsolute)
			if isSeason or isEpisode: metadata.numberSeasonSet(value = 1, number = MetaData.NumberAbsolute)
		else: # Specials (S00).
			# Do not use the special number as absolute number.
			# The absolute number should mean where the episodes is placed inside S01.
			# And in rare cases, a special can theoretically be part of the storyline and be added as an absolute episode.
			#if isEpisode and numberBase: metadata.numberSet(value = numberBase, number = MetaData.NumberAbsolute)
			if isEpisode:
				number = self._extractNumber(data = data, media = MetaData.MediaEpisode, number = MetaData.NumberAbsolute)
				if number: metadata.numberSet(value = number, number = MetaData.NumberAbsolute)
			if isSeason or isEpisode: metadata.numberSeasonSet(value = 0, number = MetaData.NumberAbsolute)

	@classmethod
	def _processLanguage(self, metadata, data):
		for i in [MetaData.LanguageOriginal, MetaData.LanguageAudio, MetaData.LanguageSubtitle]:
			metadata.languageSet(value = self._extractLanguage(data = data, language = i), language = i)

	@classmethod
	def _processTitle(self, metadata, data):
		metadata.titleSet(value = self._extractTitle(data = data))

	@classmethod
	def _processOverview(self, metadata, data):
		metadata.overviewSet(value = self._extractOverview(data = data))

	@classmethod
	def _processYear(self, metadata, data):
		metadata.yearSet(value = self._extractYear(data = data))

	@classmethod
	def _processImage(self, metadata, data, person = False):
		images = self._extractImage(data = data, person = person)
		entity = metadata.mediaEntity()
		if images:
			# Set all images in one go to reduce processing time.
			metadata.imageSet(value = images, provider = MetaData.ProviderTvdb)

	@classmethod
	def _processGenre(self, metadata, data):
		metadata.genreSet(value = self._extractGenre(data = data))

	@classmethod
	def _processName(self, metadata, data):
		metadata.nameSet(value = self._extractName(data = data, person = metadata.mediaPerson()))

	@classmethod
	def _processVote(self, metadata, data):
		# Seems that movies have an absolute score [0,inf], while shows have a rating [0,10].
		# Update: It seems that TVDb has removed the rating/votes attributes, both from the API and from the website.
		# Those [0,10] ratings that were still available for some time, were from the old website/API and seem to be all gone now.
		# One can still "Favourite" a show/episode, but those values are not available through the API (the Favourited value on the website does not match the 'score' attribute from the API).
		# https://forums.thetvdb.com/viewtopic.php?t=65652

		vote = self._extractVote(data = data)
		#if metadata.mediaShow(): metadata.voteRatingSet(value = vote)
		#else: metadata.voteAbsoluteSet(value = vote)
		metadata.voteAbsoluteSet(value = vote)

	@classmethod
	def _processStatus(self, metadata, data):
		metadata.statusSet(value = self._extractStatus(data = data, media = metadata.media()))

	@classmethod
	def _processSpecial(self, metadata, data, show = None):
		metadata.specialSet(value = self._extractSpecial(data = data, media = metadata.media(), show = show))

	@classmethod
	def _processDuration(self, metadata, data):
		metadata.durationMinutesSet(value = self._extractDuration(data = data))

	@classmethod
	def _processRelease(self, metadata, data):
		country = self._extractReleaseCountry(data = data)
		metadata.releaseCountrySet(value = country)

		zone = self._extractReleaseZone(data = data)
		metadata.releaseZoneSet(value = zone)

		if metadata.mediaTelevision():
			# Used by date functions below.
			time = self._extractReleaseTime(data = data)
			if time: metadata.releaseTimeSet(value = time['time'], zone = time['zone'])

			metadata.releaseDateFirstSet(value = self._extractReleaseFirst(data = data), zone = zone)
			metadata.releaseDateLastSet(value = self._extractReleaseLast(data = data), zone = zone)
			metadata.releaseDateNextSet(value = self._extractReleaseNext(data = data), zone = zone)

			metadata.releaseDaySet(value = self._extractReleaseDay(data = data))
		else:
			metadata.releaseDateSet(value = self._extractReleaseDate(data = data), zone = zone)

	@classmethod
	def _processMoney(self, metadata, data):
		metadata.moneyBudgetSet(value = self._extractBudget(data = data))
		metadata.moneyIncomeSet(value = self._extractIncome(data = data))

	@classmethod
	def _processCertificate(self, metadata, data):
		metadata.certificateSet(value = self._extractCertificate(data = data))

	###################################################################
	# TYPE
	###################################################################

	@classmethod
	def _typeRequest(self, type, sub = True):
		parts = [type]
		if sub is True: parts.append(MetaTvdb.ParameterTypes)
		elif sub: parts.append(sub)
		return self._request(parts = parts, cache = MetaTvdb.CacheTypes)

	@classmethod
	def _typeProvider(self, id = None):
		try:
			if MetaTvdb.DataProvider is None:
				data = self._typeRequest(type = MetaTvdb.ParameterSources)
				if data:
					MetaTvdb.DataProvider = {}
					for item in data:
						provider = MetaData.providerExtract(item['name'])
						if provider: MetaTvdb.DataProvider[item['id']] = provider
		except: self._error()

		if id is None:
			return MetaTvdb.DataProvider
		else:
			try: return MetaTvdb.DataProvider[id]
			except: return None

	@classmethod
	def _typeSeason(self, number = None, index = None):
		try:
			if MetaTvdb.DataSeason is None:
				data = self._typeRequest(type = MetaTvdb.ParameterSeasons)
				if data:
					MetaTvdb.DataSeason = {}

					for item in data:
						type = None

						if Regex.match(data = item['type'], expression = '(?:official|air|release)', cache = True): type = MetaData.NumberStandard
						elif Regex.match(data = item['type'], expression = '(?:absolute)', cache = True): type = MetaData.NumberAbsolute
						elif Regex.match(data = item['type'], expression = '(?:region)', cache = True): type = MetaData.NumberRegional
						elif Regex.match(data = item['type'], expression = '(?<!alt)(?<!alternate)(?<!alternative)(?:dvd|blu.?ray|dis[ck])', cache = True): type = MetaData.NumberDisc
						elif Regex.match(data = item['type'], expression = '(?:alt(?:ernat(?:e|ive))?)', cache = True): type = MetaData.NumberAlternative
						elif Regex.match(data = item['type'], expression = '(?<!alt)(?<!alternate)(?<!alternative)(?:dvd|blu.?ray|dis[ck])', cache = True): type = MetaData.NumberAlternativeDisc

						if type: MetaTvdb.DataSeason[type] = item['id']

					order = []
					for i in [MetaData.NumberStandard, MetaData.NumberDisc, MetaData.NumberAlternative, MetaData.NumberAlternativeDisc, MetaData.NumberRegional, MetaData.NumberAbsolute]:
						try: order.append(MetaTvdb.DataSeason[i])
						except: pass
					MetaTvdb.DataSeason['order'] = order
		except: self._error()

		if not number is None:
			try: return MetaTvdb.DataSeason[number]
			except: return None
		elif not index is None:
			try: return MetaTvdb.DataSeason['order'][index]
			except: return None
		else:
			return MetaTvdb.DataSeason

	@classmethod
	def _typeSeasonPrimary(self):
		return self._typeSeason(index = 0)

	@classmethod
	def _typeSeasonSecondary(self):
		return self._typeSeason(index = 1)

	@classmethod
	def _typePerson(self, id = None):
		try:
			if MetaTvdb.DataPerson is None:
				data = self._typeRequest(type = MetaTvdb.ParameterPeople)
				if data:
					MetaTvdb.DataPerson = {}
					for item in data:
						person = MetaData.characterExtract(item['name'])
						if person: MetaTvdb.DataPerson[item['id']] = person
		except: self._error()

		if id is None:
			return MetaTvdb.DataPerson
		else:
			try: return MetaTvdb.DataPerson[id]
			except: return None

	@classmethod
	def _typeCompany(self, id = None):
		try:
			if MetaTvdb.DataCompany is None:
				data = self._typeRequest(type = MetaTvdb.ParameterCompanies)
				if data:
					MetaTvdb.DataCompany = {}
					for item in data:
						try: name = item['companyTypeName']
						except: name = item['name']
						company = MetaData.companyExtract(name)
						if company:
							try: type = item['companyTypeId']
							except: type = item['id']
							MetaTvdb.DataCompany[type] = company
		except: self._error()

		if id is None:
			return MetaTvdb.DataCompany
		else:
			try: return MetaTvdb.DataCompany[id]
			except: return None

	@classmethod
	def _typeImage(self, id = None):
		try:
			if MetaTvdb.DataImage is None:
				data = self._typeRequest(type = MetaTvdb.ParameterArtwork)
				if data:
					MetaTvdb.DataImage = {}
					for item in data:
						type = MetaData.imageTypeExtract(item['name'])
						if type:
							media = self._extractMedia(data = item)
							quality = MetaData.imageQualityExtract(item['name'])
							opacity = MetaData.imageOpacityExtract(item['name'])
							MetaTvdb.DataImage[item['id']] = {'media' : media, 'type' : type, 'quality' : quality, 'opacity' : opacity}
						else: self._log('Unknown Image Type', item)
		except: self._error()

		# Make a copy, since the dictionary might be reused by different images.
		try: return Tools.copy(MetaTvdb.DataImage[id])
		except: return None

	@classmethod
	def _typeGenre(self, id = None):
		try:
			if MetaTvdb.DataGenre is None:
				data = self._typeRequest(type = MetaTvdb.ParameterGenres, sub = False)
				if data:
					MetaTvdb.DataGenre = {}
					for item in data:
						genre = MetaData.genreExtract(item['name'])
						if genre: MetaTvdb.DataGenre[item['id']] = genre
						else: self._log('Unknown Genre Type', item)
		except: self._error()

		if id is None:
			return MetaTvdb.DataGenre
		else:
			try: return MetaTvdb.DataGenre[id]
			except: return None

	@classmethod
	def _typeCertificate(self, id = None):
		try:
			if MetaTvdb.DataCertificate is None:
				data = self._typeRequest(type = MetaTvdb.ParameterContent, sub = MetaTvdb.ParameterRatings)
				if data:
					MetaTvdb.DataCertificate = {}
					for item in data:
						MetaTvdb.DataCertificate[item['id']] = {
							'code' : item['name'],
							'name' : item['fullname'],
							'description' : item['description'],
							'media' : MetaData.mediaExtract(item['contentType']),
							'country' : Country.code(item['country']),
						}
		except: self._error()

		if id is None:
			return MetaTvdb.DataCertificate
		else:
			try: return MetaTvdb.DataCertificate[id]
			except: return None

	@classmethod
	def _typeStatusMovie(self, id = None):
		try:
			if MetaTvdb.DataStatusMovie is None:
				data = self._typeRequest(type = MetaTvdb.ParameterMovies, sub = MetaTvdb.ParameterStatuses)
				if data:
					MetaTvdb.DataStatusMovie = {}
					for item in data:
						status = MetaData.statusExtract(item['name'])
						if status: MetaTvdb.DataStatusMovie[item['id']] = status
						else: self._log('Unknown Movie Status Type', item)
		except: self._error()

		if id is None:
			return MetaTvdb.DataStatusMovie
		else:
			try: return MetaTvdb.DataStatusMovie[id]
			except: return None

	@classmethod
	def _typeStatusShow(self, id = None):
		try:
			if MetaTvdb.DataStatusShow is None:
				data = self._typeRequest(type = MetaTvdb.ParameterSeries, sub = MetaTvdb.ParameterStatuses)
				if data:
					MetaTvdb.DataStatusShow = {}
					for item in data:
						status = MetaData.statusExtract(item['name'])
						if status: MetaTvdb.DataStatusShow[item['id']] = status
						else: self._log('Unknown Show Status Type', item)
		except: self._error()

		if id is None:
			return MetaTvdb.DataStatusShow
		else:
			try: return MetaTvdb.DataStatusShow[id]
			except: return None

	###################################################################
	# LANGUAGE
	###################################################################

	@classmethod
	def _language(self):
		try:
			result = []
			data = self._request(parts = MetaTvdb.ParameterLanguages)
			if data:
				for item in data:
					item = Language.code(item['id'])
					if item: result.append(item)
			return result
		except: self._error()
		return None

	###################################################################
	# LINK
	###################################################################

	@classmethod
	def link(self, media = None, id = None, slug = None, title = None, year = None, season = None, metadata = None, search = False, test = False):
		link = None
		try:
			if metadata:
				if not media:
					if 'tvshowtitle' in metadata:
						if 'episode' in metadata: media = Media.Episode
						elif 'season' in metadata: media = Media.Season
						else: media = Media.Show
					else:
						media = Media.Movie
				if media == Media.Episode and 'id' in metadata and 'episode' in metadata['id'] and 'tvdb' in metadata['id']['episode']: id = metadata['id']['episode']['tvdb']
				elif media == Media.Season and 'id' in metadata and 'season' in metadata['id'] and 'tvdb' in metadata['id']['season']: id = metadata['id']['season']['tvdb']
				elif 'id' in metadata and 'tvdb' in metadata['id']: id = metadata['id']['tvdb']
				try: title = metadata['tvshowtitle'] if 'tvshowtitle' in metadata else metadata['title']
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
				if media == MetaData.MediaMovie: return MetaTvdb.LinkMovieId % id
				elif media == MetaData.MediaShow: return MetaTvdb.LinkShowId % id
				elif media == MetaData.MediaSeason: return MetaTvdb.LinkSeasonId % id
				elif media == MetaData.MediaEpisode: return MetaTvdb.LinkEpisodeId % id
			elif title:
				from lib.meta.tools import MetaTools
				link = None

				slug1 = MetaTools.slug(title = title, year = year, separator = '-', symbol = None, lower = True)
				slug2 = MetaTools.slug(title = title, separator = '-', symbol = None, lower = True)

				if test:
					slugged = slug if slug else slug1
					if media == MetaData.MediaMovie: link = MetaTvdb.LinkMovieTitle % slugged
					elif media == MetaData.MediaShow: link = MetaTvdb.LinkShowTitle % slugged
					elif media == MetaData.MediaSeason and not season is None: link = MetaTvdb.LinkSeasonTitle % (slugged, season)
					elif media == MetaData.MediaEpisode and not id is None: link = MetaTvdb.LinkEpisodeTitle % (slugged, id)
					else: link = None
					if link:
						if not Networker().requestSuccess(link = link):
							if year:
								slugged = slug2 if not slug2 == slugged else slug1 if not slug1 == slugged else None
								if slugged:
									if media == MetaData.MediaMovie: link = MetaTvdb.LinkMovieTitle % slugged
									elif media == MetaData.MediaShow: link = MetaTvdb.LinkShowTitle % slugged
									elif media == MetaData.MediaSeason and not season is None: link = MetaTvdb.LinkSeasonTitle % (slugged, season)
									elif media == MetaData.MediaEpisode and not id is None: link = MetaTvdb.LinkEpisodeTitle % (slugged, id)
									else: link = None
									if link and not Networker().requestSuccess(link = link): link = None
								else:
									link = None
							else:
								link = None
				else:
					slugged = slug if slug else slug2 # Without the year - more likley to be the correct one.
					if media == MetaData.MediaMovie: link = MetaTvdb.LinkMovieTitle % slugged
					elif media == MetaData.MediaShow: link = MetaTvdb.LinkShowTitle % slugged
					elif media == MetaData.MediaSeason and not season is None: link = MetaTvdb.LinkSeasonTitle % (slugged, season)
					elif media == MetaData.MediaEpisode and not id is None: link = MetaTvdb.LinkEpisodeTitle % (slugged, id)

			if not link and title:
				link = MetaTvdb.LinkSearch % Networker.linkQuote(data = title, plus = False) + '&menu%5Btype%5D='
				if Media.isSerie(media): link += 'series'
				else: link += 'movie'
				if year: link += '&menu%5Byear%5D=' + str(year)
		except: Logger.error()

		return link

	@classmethod
	def _link(self, link, domain):
		if link and not Networker.linkIs(link): link = Networker.linkJoin(domain, link)
		return link

	@classmethod
	def _linkImage(self, link):
		# Some links do not contain the domain, but only the path (eg: /banners/movies/xxx/backgrounds/xxx.jpg).
		return self._link(link = link, domain = MetaTvdb.LinkImage)

	###################################################################
	# SEARCH
	###################################################################

	# Supported searches:
	#	Movie: Movie ID (idImdb/idTmdb/idTvdb) or Movie Title (query with optional year)
	#	Collection: No
	#	Show: Show ID (idImdb/idTmdb/idTvdb) or Show Title (query with optional year)
	#	Season: Show ID (idImdb/idTmdb/idTvdb) or Show Title (query with optional year) together with numberSeason
	#	Episode: Show ID (idImdb/idTmdb/idTvdb) or Show Title (query with optional year) together with numberSeason and numberEpisode
	#	Character: No
	#	Person: Person ID (idImdb/idTmdb/idTvdb) or Person Name (query)
	#	Company: Company ID (idImdb/idTmdb/idTvdb) or Company Name (query)
	@classmethod
	def _search(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, numberSeason = None, numberEpisode = None, media = None, limit = None, offset = None, page = None, level = None):
		data = {}
		result = []
		id = idImdb if idImdb else idTmdb if idTmdb else None # TVDb does not support Trakt.

		if query:
			data[MetaTvdb.ParameterQuery] = query
		elif id:
			data[MetaTvdb.ParameterRemoteId] = id
			if not query: data[MetaTvdb.ParameterQuery] = id
		elif idTvdb:
			data[MetaTvdb.ParameterQuery] = idTvdb
		else:
			return None if limit == 1 else result

		if limit: data[MetaTvdb.ParameterLimit] = limit
		if offset: data[MetaTvdb.ParameterOffset] = offset
		if year: data[MetaTvdb.ParameterYear] = year

		if not media:
			if not numberEpisode is None: media = MetaData.MediaEpisode
			elif not numberSeason is None: media = MetaData.MediaSeason
		if media:
			type = None
			if media == MetaData.MediaMovie: type = 'movie'
			elif media == MetaData.MediaPerson: type = 'person'
			elif media == MetaData.MediaCompany: type = 'company'
			elif media in MetaData.MediaTelevision: type = 'series'
			if type: data[MetaTvdb.ParameterType] = type

		data = self._request(parts = MetaTvdb.ParameterSearch, data = data)
		if data:
			try:
				for item in data:
					item = self._process(media = MetaData.MediaDefault, data = item)
					if item: result.append(item)
			except: Logger.error()

			if media in [MetaData.MediaSeason, MetaData.MediaEpisode]:
				# Reset so that the correct item from "result" is returned below (for limit == 1).
				id = None
				idTvdb = None
				query = True

				show = [i.idShowTvdb() for i in result]
				show = [i for i in show if i]
				show = self.show(idTvdb = show, level = level if level >= MetaService.Level4 else MetaService.Level4)
				result = []
				if media == MetaData.MediaSeason: result = [i.season(numberSeason = numberSeason) for i in show]
				elif media == MetaData.MediaEpisode: result = [i.episode(numberSeason = numberSeason, numberEpisode = numberEpisode) for i in show]
				result = [i for i in result if i]

		if limit == 1:
			if idImdb and id == idImdb:
				for i in result:
					if i.idImdb() == idImdb: return i
			elif idTmdb and id == idTmdb:
				for i in result:
					if i.idTmdb() == idTmdb: return i
			elif idTvdb:
				for i in result:
					if i.idTvdb() == idTvdb: return i
			elif query and result:
				return result[0]
			return None
		return result

	###################################################################
	# ID
	###################################################################

	@classmethod
	def _id(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, numberSeason = None, numberEpisode = None, media = None, level = None):
		result = self.search(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, limit = 1, level = level)
		try: return result.id()
		except: return None

	###################################################################
	# MOVIE
	###################################################################

	@classmethod
	def _movie(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, level = None):
		return self._retrieve(media = MetaData.MediaMovie, type = MetaTvdb.ParameterMovies, extended = True, translations = True, id = id, level = level)

	###################################################################
	# SHOW
	###################################################################

	@classmethod
	def _show(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, level = None):
		return self._retrieve(media = MetaData.MediaShow, type = MetaTvdb.ParameterSeries, extended = True, translations = True, episodes = True, id = id, level = level)

	###################################################################
	# SEASON
	###################################################################

	@classmethod
	def _season(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, numberSeason = None, show = None, level = None):
		return self._retrieve(media = MetaData.MediaSeason, type = MetaTvdb.ParameterSeasons, extended = True, translations = True, id = id, show = show, level = level)

	###################################################################
	# EPISODE
	###################################################################

	@classmethod
	def _episode(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, numberSeason = None, numberEpisode = None, show = None, season = None, level = None):
		return self._retrieve(media = MetaData.MediaEpisode, type = MetaTvdb.ParameterEpisodes, extended = True, translations = True, id = id, show = show, season = season, level = level)

	###################################################################
	# CHARACTER
	###################################################################

	@classmethod
	def _character(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, level = None):
		return self._retrieve(media = MetaData.MediaCharacter, type = MetaTvdb.ParameterCharacters, id = id, level = level)

	###################################################################
	# PERSON
	###################################################################

	@classmethod
	def _person(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, level = None):
		return self._retrieve(media = MetaData.MediaPerson, type = MetaTvdb.ParameterPeople, extended = True, translations = True, id = id, level = level)

	###################################################################
	# COMPANY
	###################################################################

	@classmethod
	def _company(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, level = None):
		return self._retrieve(media = MetaData.MediaCompany, type = MetaTvdb.ParameterCompanies, id = id, level = level)

	###################################################################
	# TRANSLATION
	###################################################################

	@classmethod
	def _translation(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, numberSeason = None, numberEpisode = None, media = None, translation = None, level = None):
		level = MetaService.Level3
		if media == MetaData.MediaMovie: result = self.movie(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, level = level)
		elif media == MetaData.MediaShow: result = self.show(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, level = level)
		elif media == MetaData.MediaSeason: result = self.season(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, numberSeason = numberSeason, level = level)
		elif media == MetaData.MediaEpisode: result = self.episode(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, numberSeason = numberSeason, numberEpisode = numberEpisode, level = level)
		if result:
			if translation == MetaService.TranslationTitle: return result.title(language = True)
			elif translation == MetaService.TranslationOverview: return result.overview(language = True)
		return None
