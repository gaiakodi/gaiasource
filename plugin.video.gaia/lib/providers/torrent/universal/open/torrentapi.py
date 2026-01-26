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

from lib.providers.core.json import ProviderJson
from lib.modules.tools import System

# https://torrentapi.org/apidocs_v2.txt?&app_id=rarbg

'''
	TorrentAPI returns two type of errors:
	1.  {"error":"No results found","error_code":20}
		These errors occur sporadically.
		In many cases it just means there are simply no results for the given IMDb ID or search query.
		In some cases it is some internal TorrentAPI problem. When executing the exact same query (same search and API token) again, it suddenly returns results.
	2.  "" (empty result)
		This seems to happen if the 1req/2sec API limit was not kept.

	There are two ways of scraping TorrentAPI:
	1. Proper (Slow):
		a. Scraping time: 30+ secs (when packs are also scraped).
		b. Request delay of 2 secs (or more for retries).
		c. Make retry requests for error #1.
		d. Very low probability that results are not found (aka retry requests did also not return anything). But it still happens every now and then.
	2. Quick (Fast):
		a. Scraping time: 10 secs or less (when packs are also scraped).
		b. No request delay (or minimal). Essentially continuously spamming the API with requests until they return results.
		c. Make retry requests for error #1 and #2.
		d. Low probability that results are not found (aka retry requests did also not return anything). Seems to happen slightly more than with the proper way.

'''

class Provider(ProviderJson):

	_Link					= ['https://torrentapi.org']
	_Path					= 'pubapi_v2.php'

	_LimitOffset			= 100	# Maximum number of links returned per request.
	_LimitDelay				= 2		# Maximum of 1 requests per 2 seconds.
	_LimitMinimal			= 0.01

	_CustomSpeed			= 'speed'
	_CustomRetry			= 'retry'
	_CustomFast				= 'fast'
	_CustomSlow				= 'slow'

	_CategoryMovie			= ['14', '17', '42', '44', '45', '46', '47', '48', '50', '51', '52', '54'] # 14 = Movies/XVID, 17 = Movies/x264, 42 = Movies/Full BD, 44 = Movies/x264/1080, 45 = Movies/x264/720, 46 = Movies/BD Remux, 47 = Movies/x264/3D, 48 = Movies/XVID/720, 50 = Movies/x264/4k, 51 = Movies/x265/4k, 52 = Movs/x265/4k/HDR, 54 = Movies/x265/1080
	_CategoryShow			= ['18', '41', '49'] # 18 = TV Episodes, 41 = TV HD Episodes, 49 = TV UHD Episodes

	_ParameterApp			= 'app_id'
	_ParameterJson			= 'json_extended'
	_ParameterToken			= 'token'
	_ParameterTokenGet		= 'get_token'
	_ParameterSearch		= 'search'
	_ParameterSearchImdb	= 'search_imdb'
	_ParameterSearchTvdb	= 'search_tvdb'
	_ParameterSearchTmdb	= 'search_themoviedb'
	_ParameterSearchString	= 'search_string'
	_ParameterMode			= 'mode'
	_ParameterCategory		= 'category'
	_ParameterSort			= 'sort'
	_ParameterFormat		= 'format'
	_ParameterRanked		= 'ranked'
	_ParameterLimit			= 'limit'

	_AttributeList			= 'torrent_results'
	_AttributeLink			= 'download'
	_AttributeName			= 'title'
	_AttributeSize			= 'size'
	_AttributeHash			= 'info_hash'
	_AttributeTime			= 'pubdate'
	_AttributeSeeds			= 'seeders'
	_AttributeLeeches		= 'leechers'
	_AttributeInfo			= 'episode_info'
	_AttributeImdb			= 'imdb'
	_AttributeTmdb			= 'themoviedb'
	_AttributeTvdb			= 'tvdb'
	_AttributeSeason		= 'seasonnum'
	_AttributeEpisode		= 'epnum'

	_ExpressionError		= r'(no\s*results?\s*found|"error_code"\s*:\s*20[,\}])' # No results are returned. This might be because there are no results, or because of a TorrentApi error that sometimes does not return results although there are some.
	_ExpressionLimit		= r'(^$)' # Empty data returned. This seems to be caused by exceeding the request limit.

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		category = self.customCategory()
		verified = self.customVerified()
		speed = self.custom(id = Provider._CustomSpeed)
		speedFast = speed == Provider._CustomFast
		retry = self.custom(id = Provider._CustomRetry)
		retryDelay = Provider._LimitDelay * 0.2 # These delays are added on top of the default requestDelay.

		if self.customSearchId():
			searchType = Provider._ParameterSearchImdb
			searchValue = Provider.TermIdImdb
			searchImdbType = Provider._ParameterSearchImdb
			searchImdbValue = ProviderJson.TermIdImdb
			searchTvdbType = Provider._ParameterSearchTvdb
			searchTvdbValue = ProviderJson.TermIdTvdb
			searchTmdbType = Provider._ParameterSearchTmdb
			searchTmdbValue = ProviderJson.TermIdTmdb
		else:
			searchType = Provider._ParameterSearchString
			searchValue = Provider.TermQuery
			searchImdbType = None
			searchImdbValue = None
			searchTvdbType = None
			searchTvdbValue = None
			searchTmdbType = None
			searchTmdbValue = None

		ProviderJson.initialize(self,
			name					= 'TorrentAPI',
			description				= '{name} is the backend {container} API used by RarBg. The API contains results in various languages, but most of them are in English. Searches are conducted using the IMDb ID. The API is fast and reliable, but queries are limited to %d results without paging support and will therefore not always return all the results that are available. The API has a 1 request per %d seconds limit and scraping might therefore take longer when searching packs or foreign titles.' % (Provider._LimitOffset, Provider._LimitDelay),
			rank					= 5,
			performance				= ProviderJson.PerformanceExcellent - ProviderJson.PerformanceStep,
			status					= ProviderJson.StatusDead, # RarBG shut down. Cloudflare cannot connect to the TorrentAPI server anymore. Is probably due to the same reasons.

			link					= Provider._Link,

			requestDelay			= Provider._LimitMinimal if speedFast else Provider._LimitDelay,

			# For some reason TorrentApi sometimes returns: {"error":"No results found","error_code":20}.
			# If the same request is executed again right afterwards, it suddenly returns results (same auth token and same parameters).
			# This error seems to be sporadic, sometimes it happens frequently, sometimes not at all.
			# And it seems this happeens waay more often with query searches than with ID searches, although it does happen with ID once in a while as well.
			# This also does not seem to be related to the request limit. This error occurs even if requests are spaced 30 seconds apart.
			# Maybe it has to do with server load. If too many (total) requests come into TorrentApi's server at once, some requests are just dropped. Not sure about this.
			# Retry once, and if no results are returned again, then bad luck. Sometimes 3 - 5 retries are needed to finally get results.
			retryCount				= [6, retry] if speedFast else retry,
			retryDelay				= [Provider._LimitMinimal, retryDelay] if speedFast else retryDelay,
			retryExpression			= [Provider._ExpressionLimit, Provider._ExpressionError] if speedFast else Provider._ExpressionError,

			accountAuthentication	= {
										ProviderJson.ProcessMode : ProviderJson.AccountModeScrape,
										ProviderJson.ProcessRequest : {
											ProviderJson.RequestPath : Provider._Path,
											ProviderJson.RequestData : {
												Provider._ParameterTokenGet	: Provider._ParameterTokenGet,
												Provider._ParameterFormat	: Provider._ParameterJson,
											},
										},
										ProviderJson.ProcessFixed : {
											ProviderJson.RequestData : {
												Provider._ParameterApp : System.name(),
											},
										},
										ProviderJson.ProcessExtract : Provider._ParameterToken,
										ProviderJson.ProcessValidate : {Provider._ParameterToken : '^[a-z0-9]{8,32}$'},
									},

			custom					= [
										{
											ProviderJson.SettingsId				: Provider._CustomSpeed,
											ProviderJson.SettingsLabel			: 'Scrape Speed',
											ProviderJson.SettingsDefault		: Provider._CustomFast,
											ProviderJson.SettingsType			: [{Provider._CustomFast : 33998}, {Provider._CustomSlow : 33997}],
											ProviderJson.SettingsDescription	: '{name} restricts the how frequently requests can be made to the API. This limit slows down scraping, especially when searching packs or multiple alternative titles and keywords. [I]Slow[/I]  scraping will strictly adhere to the request limit, which increases scraping time, but generally returns all available results. [I]Fast[/I]  scraping will apply the request limit moderately, therefore reducing scraping time, but also slightly increasing the chance that a few results might go undetected.',
										},
										{
											ProviderJson.SettingsId				: Provider._CustomRetry,
											ProviderJson.SettingsLabel			: 'Failure Retries',
											ProviderJson.SettingsDefault		: 1,
											ProviderJson.SettingsType			: ProviderJson.SettingsTypeNumber,
											ProviderJson.SettingsDescription	: 'Sometimes requests to {name} fail for an unknown reason. Retry the request a number of times before giving up. Set the value to 0 to not retry any request. More retries increases the scraping time.',
										},
									],
			customSearch			= True,
			customCategory			= {
										# Do not make the default True, since there is a request limit and requests are executed sequentially.
										ProviderJson.SettingsDescription	: '{name} returns a maximum of %d results per request. {name} has subcategories that can be searched together with a single request or can be searched separately with multiple requests. Since a 1 request per %d seconds limit is imposed, separate category searching will greatly increase the scraping time and not return more results most of the time.' % (Provider._LimitOffset, Provider._LimitDelay),
									},
			customVerified			= True,

			supportMovie			= True,
			supportShow				= True,
			supportPack				= True,

			# It seems that everything on TorrentApi has an IMDb ID.
			# Use a fallback query if the IMDb ID is not availble, for exact searches, or if the custom setting was set to search by title.
			searchQuery				= [
										{
											ProviderJson.RequestPath : Provider._Path,
											ProviderJson.RequestData : {
												Provider._ParameterFormat			: Provider._ParameterJson,
												Provider._ParameterToken			: ProviderJson.TermAuthentication,
												Provider._ParameterMode				: Provider._ParameterSearch,
												Provider._ParameterCategory			: ProviderJson.TermCategory,
												Provider._ParameterLimit			: Provider._LimitOffset,
												Provider._ParameterSort				: Provider._AttributeSeeds,
												Provider._ParameterRanked			: verified,
												searchType							: searchValue,
											},
										},
										{
											ProviderJson.RequestPath : Provider._Path,
											ProviderJson.RequestData : {
												Provider._ParameterFormat		: Provider._ParameterJson,
												Provider._ParameterToken		: ProviderJson.TermAuthentication,
												Provider._ParameterMode			: Provider._ParameterSearch,
												Provider._ParameterCategory		: ProviderJson.TermCategory,
												Provider._ParameterLimit		: Provider._LimitOffset,
												Provider._ParameterSort			: Provider._AttributeSeeds,
												Provider._ParameterRanked		: verified,
												searchImdbType					: searchImdbValue,
											},
										},
										{
											ProviderJson.RequestPath : Provider._Path,
											ProviderJson.RequestData : {
												Provider._ParameterFormat		: Provider._ParameterJson,
												Provider._ParameterToken		: ProviderJson.TermAuthentication,
												Provider._ParameterMode			: Provider._ParameterSearch,
												Provider._ParameterCategory		: ProviderJson.TermCategory,
												Provider._ParameterLimit		: Provider._LimitOffset,
												Provider._ParameterSort			: Provider._AttributeSeeds,
												Provider._ParameterRanked		: verified,
												searchTvdbType					: searchTvdbValue,
											},
										},
										{
											ProviderJson.RequestPath : Provider._Path,
											ProviderJson.RequestData : {
												Provider._ParameterFormat		: Provider._ParameterJson,
												Provider._ParameterToken		: ProviderJson.TermAuthentication,
												Provider._ParameterMode			: Provider._ParameterSearch,
												Provider._ParameterCategory		: ProviderJson.TermCategory,
												Provider._ParameterLimit		: Provider._LimitOffset,
												Provider._ParameterSort			: Provider._AttributeSeeds,
												Provider._ParameterRanked		: verified,
												searchTmdbType					: searchTmdbValue,
											},
										},
										{
											ProviderJson.RequestPath : Provider._Path,
											ProviderJson.RequestData : {
												Provider._ParameterFormat		: Provider._ParameterJson,
												Provider._ParameterToken		: ProviderJson.TermAuthentication,
												Provider._ParameterMode			: Provider._ParameterSearch,
												Provider._ParameterCategory		: ProviderJson.TermCategory,
												Provider._ParameterLimit		: Provider._LimitOffset,
												Provider._ParameterSort			: Provider._AttributeSeeds,
												Provider._ParameterRanked		: verified,
												Provider._ParameterSearchString	: ProviderJson.TermQuery,
											},
										},
									],

			# TorrentApi allows a maximum of 100 results per request and they do not support paging.
			# The best way would be to search each category, but since there is a request limit, requests are made sequentially and are therefore slow.
			# Do not search all categories, since it would take too long. Search the main category and then a few HD ones.
			# It seems that TorrentApi has very few torrents per title, so there is no real benefit to search individual categories as well.
			# Do not use the "movies" and "tv" categories, since they return less results than the concatenated integer categories.
			searchCategoryMovie		= Provider._CategoryMovie if category else ';'.join(Provider._CategoryMovie),
			searchCategoryShow		= Provider._CategoryShow if category else ';'.join(Provider._CategoryShow),

			extractList				= Provider._AttributeList,
			extractLink				= Provider._AttributeLink,
			extractHash				= Provider._AttributeHash,
			extractFileName			= Provider._AttributeName,
			extractFileSize			= Provider._AttributeSize,
			extractSourceTime		= Provider._AttributeTime,
			extractSourceApproval	= Provider._ParameterRanked,
			extractSourceSeeds		= Provider._AttributeSeeds,
			extractSourceLeeches	= Provider._AttributeLeeches,
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processBefore(self, item):
		info = item[Provider._AttributeInfo] # Even for movies.
		id = False

		# Do not do this for packs, since the ID can be from a different movie in the pack (typically the first movie in the series).
		if not self.parameterQueryPack():
			try: currentImdb = info[Provider._AttributeImdb]
			except: currentImdb = None
			if currentImdb:
				expectedImdb = self.parameterIdImdb()
				if expectedImdb:
					if expectedImdb == currentImdb: id = True
					else: return ProviderJson.Skip

			if not id:
				try: currentTmdb = info[Provider._AttributeTmdb]
				except: currentTmdb = None
				if currentTmdb:
					expectedTmdb = self.parameterIdTmdb()
					if expectedTmdb:
						if expectedTmdb == currentTmdb: id = True
						else: return ProviderJson.Skip

			if not id:
				try: currentTvdb = info[Provider._AttributeTvdb]
				except: currentTvdb = None
				if currentTvdb:
					expectedTvdb = self.parameterIdTvdb()
					if expectedTvdb:
						if expectedTvdb == currentTvdb: id = True
						else: return ProviderJson.Skip

		expectedSeason = self.parameterNumberSeason()
		if expectedSeason:
			try: currentSeason = int(info[Provider._AttributeSeason])
			except: currentSeason = None
			if not currentSeason is None and currentSeason == expectedSeason:
				try: currentEpisode = int(info[Provider._AttributeEpisode])
				except: currentEpisode = None
				if not currentEpisode is None and currentEpisode < 100000: # Packs have a 1000000 episode number.
					if not currentEpisode == self.parameterNumberEpisode(): return ProviderJson.Skip
			else:
				return ProviderJson.Skip
