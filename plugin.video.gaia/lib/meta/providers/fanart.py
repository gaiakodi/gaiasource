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

from lib.modules.tools import Tools, Logger, Regex, Language
from lib.modules.network import Networker
from lib.modules.cache import Cache
from lib.modules.account import Fanart as Account
from lib.meta.image import MetaImage
from lib.meta.provider import MetaProvider

class MetaFanart(MetaProvider):

	TypeMovie	= 'movies'
	TypeShow	= 'tv'

	Link		= 'https://webservice.fanart.tv/v3/%s/%s'

	Index		= 99999999

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		MetaProvider.__init__(self, account = Account.instance())
		self.mHeaders = self.account().headers()

	##############################################################################
	# GENERAL
	##############################################################################

	def _retrieve(self, type = None, id = None, link = None, cache = None):
		if Tools.isArray(id):
			# Some Fanart items do not have an IMDb ID. In such a case try to use the TMDb ID.
			data = None
			for i in id:
				data = self._request(type = type, id = i, link = link, cache = cache)
				if data and not('error message' in data and data['error message'].lower() == 'not found'): return data
			return data
		else:
			return self._request(type = type, id = id, link = link, cache = cache)

	def _request(self, type = None, id = None, link = None, cache = None):
		if not link: link = MetaFanart.Link % (type, id)
		networker = Networker()
		headers = self.mHeaders
		if cache:
			if cache is True: timeout = Cache.TimeoutLong
			else: timeout = cache
			cache = Cache.instance()
			result = cache.cache(mode = None, timeout = timeout, refresh = None, function = networker.request, link = link, headers = headers)

			try: error = result['error']['type']
			except: error = None
			if error and error in Networker.ErrorServer: self._errorUpdate()

			if not result or (error and error in Networker.ErrorNetwork):
				# Delete the cache, otherwise the next call will return the previously failed request.
				cache.cacheDelete(networker.request, link = link, headers = headers)
				return False
		else:
			result = networker.request(link = link, headers = headers)

			try: error = result['error']['type']
			except: error = None
			if error and error in Networker.ErrorServer: self._errorUpdate()

			if not result or (error and error in Networker.ErrorNetwork): return False
		return Networker.dataJson(result['data'])

	##############################################################################
	# MOVIE
	##############################################################################

	def metadataMovie(self, imdb = None, tmdb = None, cache = False):
		try:
			if imdb or tmdb:
				id = []
				if imdb: id.append(imdb)
				if tmdb: id.append(tmdb)

				data = self._retrieve(type = MetaFanart.TypeMovie, id = id, cache = cache)
				if data is False: return False

				if data and ('name' in data or 'tmdb_id' in data or 'imdb_id' in data):
					images = {i : [] for i in MetaImage.Types}

					# https://medium.com/fanart-tv/what-are-fanart-tv-personal-api-keys-472f60222856
					entries = (
						(('movieposter',), None, MetaImage.TypePoster),
						(('moviethumb',), None, MetaImage.TypeThumb),
						(('moviebackground',), None, MetaImage.TypeFanart),
						(('moviethumb',), 'moviebackground', MetaImage.TypeLandscape),
						(('moviebanner',), None, MetaImage.TypeBanner),
						(('hdclearlogo', 'hdmovielogo', 'clearlogo', 'movielogo'), None, MetaImage.TypeClearlogo),
						(('hdclearart', 'hdmovieclearart', 'clearart', 'movieclearart'), None, MetaImage.TypeClearart),
						(('moviedisc',), None, MetaImage.TypeDiscart),
					)

					for entry in entries:
						try:
							values = None
							for i in entry[0]:
								if i in data:
									values = data[i]
									break
							if not values and entry[1] and entry[1] in data: values = data[entry[1]]
							if values:
								index = 0
								for i in values:
									index += 1
									images[entry[2]].append(self._imageCreate(data = i, index = index))
						except: Logger.error()

					if images: return images
		except: Logger.error()
		return None

	##############################################################################
	# SHOW
	##############################################################################

	# season: None (images for the show), True (images for all seasons), integer (images for a specific season).
	def metadataShow(self, tvdb = None, season = None, cache = False):
		try:
			if tvdb:
				data = self._retrieve(type = MetaFanart.TypeShow, id = tvdb, cache = cache)
				if data is False: return False

				if data and ('name' in data or 'thetvdb_id' in data):
					images = {i : [] for i in MetaImage.Types}
					imagesSeason = {}

					# https://medium.com/fanart-tv/what-are-fanart-tv-personal-api-keys-472f60222856
					seasoned = ['all', '', None] if (season is None or season is True) else [str(season), int(season)]
					entries = [
						(('tvposter',), None, MetaImage.TypePoster),
						(('tvthumb',), None, MetaImage.TypeThumb),
						(('tvbackground', 'showbackground'), None, MetaImage.TypeFanart),
						(('tvthumb',), 'showbackground', MetaImage.TypeLandscape),
						(('tvbanner',), None, MetaImage.TypeBanner),
						(('hdclearlogo', 'clearlogo', 'hdtvlogo', 'tvlogo'), None, MetaImage.TypeClearlogo),
						(('hdclearart', 'clearart'), None, MetaImage.TypeClearart),
						(('tvdisc', 'showdisc'), None, MetaImage.TypeDiscart),
					]

					if not season is None:
						entries.extend([
							(('seasonposter',), None, MetaImage.TypePoster),
							(('seasonthumb',), None, MetaImage.TypeThumb),
							(('tvbackground', 'showbackground'), None, MetaImage.TypeFanart),
							(('tvbackground', 'showbackground'), None, MetaImage.TypeLandscape),
							(('seasonbanner',), None, MetaImage.TypeBanner),
						])

					for entry in entries:
						try:
							values = None
							for i in entry[0]:
								if i in data:
									values = data[i]
									break
							if not values and entry[1] and entry[1] in data: values = data[entry[1]]
							if values:
								index = 0
								for i in values:
									if (
										(season is None and (not 'season' in i or ('season' in i and i['season'] in seasoned))) or # Show.
										(season is True and 'season' in i and not i['season'] in seasoned) or # All seasons.
										(not season is None and not season is True and 'season' in i and i['season'] in seasoned) # Specific season.
									):
										index += 1
										if season is True:
											number = int(i['season'])
											if not number in imagesSeason: imagesSeason[number] = Tools.copy(images)
											imagesSeason[number][entry[2]].append(self._imageCreate(data = i, index = index))
										else:
											images[entry[2]].append(self._imageCreate(data = i, index = index))
						except: Logger.error()

					if season is True:
						if imagesSeason:
							imagesSeason = self._imageSeason(images = imagesSeason)
							return imagesSeason
					elif images:
						return images
		except: Logger.error()
		return None

	##############################################################################
	# SET
	##############################################################################

	def metadataSet(self, imdb = None, tmdb = None, cache = False):
		return self.metadataMovie(imdb = imdb, tmdb = tmdb, cache = cache)

	###################################################################
	# IMAGE
	###################################################################

	def _imageCreate(self, data, index):
		index = MetaFanart.Index - index
		id = data.get('id')
		id = (MetaFanart.Index - int(id)) if id else 0
		vote = data.get('likes')
		vote = int(vote) if vote else 0
		sort = {
			MetaImage.SortIndex : index,
			MetaImage.SortId : id,
			MetaImage.SortVote : vote,
			MetaImage.SortVoteIndex : [vote, index],
			MetaImage.SortVoteId : [vote, id],
		}
		return MetaImage.create(link = data.get('url'), provider = MetaImage.ProviderFanart, language = data.get('lang'), theme = data.get('theme'), sort = sort)

	def _imageSeason(self, images):
		try:
			# Group season images based on a common theme.

			# Prefer metadata language setting, followed by general language setting, followed by no language (None), and all other images last.
			from lib.meta.tools import MetaTools
			exclude = (None, Language.CodeUniversal, Language.CodeNone, Language.CodeUnknown)
			settings = []
			setting = MetaImage.settingsLanguage()
			if setting: settings.append(setting)
			setting = MetaTools.instance().settingsLanguage()
			if setting: settings.append(setting)
			setting = Language.settingsCode()
			if setting: settings.extend(setting)
			settings.append(None)
			settings = Tools.listUnique(settings)
			settings = {settings[i] : (10 - i) for i in range(len(settings)) if not settings[i] in exclude}

			for type in MetaImage.Types:
				ids = {}
				votes = []
				total = len(images)
				threshold = total * 0.4 # The theme/group needs to cover at least 40% of the seasons.

				def _name(image):
					name = Networker.linkName(image.get('link'), extension = False)
					if name: name = Regex.extract(data = name, expression = r'.*\-+(.*)')
					return name

				def _id(name):
					return Regex.replace(data = name, expression = r'\-(\d+)(?:$|\-)', replacement = 'x', group = 1)

				def _add(id, vote, language):
					try:
						ids[id]['count'] += 1
						ids[id]['vote'] += vote
					except:
						ids[id] = {'count' : 1, 'vote' : vote, 'language' : language}

				for image in images.values():
					subids = {}
					voted = False
					for i in image[type]:
						name = _name(image = i)
						if name:
							try: vote = i['sort']['vote'][0] or 0
							except: vote = 0
							if not voted:
								votes.append(vote)
								voted = True

							id = name
							for k in range(len(name)):
								id = id[:-1]

								# Allow up to 3 characters.
								# Eg: GoT DE season posters start with 6060 and 6062.
								if len(id) < 3: break

								# Do not add twice for the same image group.
								# Otherwise shorter prefixes can be added multiple times and then having a larger count than longer prefixes.
								if not id in subids:
									subids[id] = True
									_add(id = id, vote = vote, language = i.get('language'))

				if ids:
					setting = MetaImage.settingsLanguage(media = MetaImage.MediaSeason, type = type)
					if setting and not setting in exclude: settings[100] = setting

					ids = {k : v for k, v in sorted(ids.items(), key = lambda i : (settings.get(i[1]['language'], 0), i[1]['count'], i[1]['vote'], len(i[0])), reverse = True)}
					id = next(iter(ids))

					# Add the theme/group index.
					keys = list(ids.keys())
					for number, image in images.items():
						for i in image[type]:
							name = name = _name(image = i)
							if name:
								for j in range(len(keys)):
									if name.startswith(keys[j]):
										i[MetaImage.AttributeTheme] = keys[j]
										i['sort'][MetaImage.SortTheme] = j
										break

					# Only do this if there are common images across at least "threshold"% of the seasons.
					# Otherwise keep the orignal order.
					if id and ids[id]['count'] >= threshold:
						for number, image in images.items():
							temp1 = []
							temp2 = []
							for i in image[type]:
								name = name = _name(image = i)
								if name:
									match = name.startswith(id)
									if match: temp1.append(i)
									else: temp2.append(i)
							if temp1 or temp2: images[number][type] = temp1 + temp2
		except: Logger.error()
		return images
