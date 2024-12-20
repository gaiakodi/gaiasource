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

from lib.modules.tools import Tools, Logger
from lib.modules.network import Networker
from lib.modules.cache import Cache
from lib.modules.concurrency import Lock
from lib.modules.account import Fanart as Account
from lib.meta.image import MetaImage

class MetaFanart(object):

	TypeMovie	= 'movies'
	TypeShow	= 'tv'

	Link		= 'https://webservice.fanart.tv/v3/%s/%s'

	Index		= 99999999

	Lock		= Lock()
	Account		= None
	Headers		= None

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		if settings:
			MetaFanart.Account = None
			MetaFanart.Headers = None

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def retrieve(self, type = None, id = None, link = None, cache = None):
		if Tools.isArray(id):
			# Some Fanart items do not have an IMDb ID. In such a case try to use the TMDb ID.
			data = None
			for i in id:
				data = self._retrieve(type = type, id = i, link = link, cache = cache)
				if data and not('error message' in data and data['error message'].lower() == 'not found'): return data
			return data
		else:
			return self._retrieve(type = type, id = id, link = link, cache = cache)

	@classmethod
	def _retrieve(self, type = None, id = None, link = None, cache = None):
		if not link: link = MetaFanart.Link % (type, id)
		networker = Networker()
		headers = self.headers()
		if cache:
			if cache is True: timeout = Cache.TimeoutLong
			else: timeout = cache
			cache = Cache.instance()
			result = cache.cache(mode = None, timeout = timeout, refresh = None, function = networker.request, link = link, headers = headers)
			if not result or result['error']['type'] in Networker.ErrorNetwork:
				# Delete the cache, otherwise the next call will return the previously failed request.
				cache.cacheDelete(networker.request, link = link, headers = headers)
				return False
		else:
			result = networker.request(link = link, headers = headers)
			if not result or result['error']['type'] in Networker.ErrorNetwork: return False
		return Networker.dataJson(result['data'])

	@classmethod
	def headers(self):
		self.account() # Initialize sccount and headers.
		return MetaFanart.Headers

	@classmethod
	def account(self):
		if MetaFanart.Account is None:
			MetaFanart.Lock.acquire()
			if MetaFanart.Account is None:
				MetaFanart.Account = Account.instance()
				MetaFanart.Headers = MetaFanart.Account.headers()
			MetaFanart.Lock.release()
		return MetaFanart.Account

	@classmethod
	def _process(self, data, index):
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
		return MetaImage.create(link = data.get('url'), provider = MetaImage.ProviderFanart, language = data.get('lang'), sort = sort)

	##############################################################################
	# MOVIE
	##############################################################################

	@classmethod
	def movie(self, imdb = None, tmdb = None, cache = False):
		try:
			if imdb or tmdb:
				id = []
				if imdb: id.append(imdb)
				if tmdb: id.append(tmdb)

				data = self.retrieve(type = MetaFanart.TypeMovie, id = id, cache = cache)
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
									images[entry[2]].append(self._process(data = i, index = index))
						except: Logger.error()

					if images: return images
		except: Logger.error()
		return None

	##############################################################################
	# SHOW
	##############################################################################

	# season: None (images for the show), True (images for all seasons), integer (images for a specific season).
	@classmethod
	def show(self, tvdb = None, season = None, cache = False):
		try:
			if tvdb:
				data = self.retrieve(type = MetaFanart.TypeShow, id = tvdb, cache = cache)
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
											imagesSeason[number][entry[2]].append(self._process(data = i, index = index))
										else:
											images[entry[2]].append(self._process(data = i, index = index))
						except: Logger.error()

					if season is True:
						if imagesSeason: return imagesSeason
					elif images:
						return images
		except: Logger.error()
		return None

	##############################################################################
	# SET
	##############################################################################

	@classmethod
	def set(self, imdb = None, tmdb = None, cache = False):
		return self.movie(imdb = imdb, tmdb = tmdb, cache = cache)
