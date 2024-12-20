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

# https://knaben.eu/rss/
# NB: Do not use the API/RSS-feed, because:
#	1. Some missing attrributes (eg seeds/leeches)
#	2. Results limited to 400 links without paging.
#	3. Returned data is XML with inner CDATA, HTML, and text. Makes it more difficult to process.
# Update: Use the API now. Data is good enough to be used.

from lib.providers.core.json import ProviderJson
from lib.providers.core.html import ProviderHtml, Html, HtmlLink, HtmlDiv, HtmlResultsTable, HtmlResult
from lib.modules.tools import Regex, Converter

class Provider(ProviderJson, ProviderHtml):

	# Knaben now has an API, but the API cannot do a live search.
	# On the other hand, the live search is SUPER slow. Especially when many queries/pages are retrieved, Knaben ends up the last provider in the scrape.
	# So rather use the API with non-live cached results. Might return fewer results for new releases, but other providers have more up-to-date results.

	_Link					= ['https://knaben.eu', 'https://knaben.xyz', 'https://knaben.cc', 'https://knaben.org']
	_Api					= 'api'

	_Path					= {
								ProviderHtml.Version1 : 'v1',
								ProviderHtml.Version2 : 'search/%s/%s/%s/%s',
							}


	_LimitOffset			= 300 # The maximum number of results returned by an API query.

	_CategoryMovie			= ['3000000', '6000000'] # Movies = 3000000, Anime = 6000000
	_CategoryShow			= ['2000000', '6000000'] # TV = 2000000, Anime = 6000000

	_ParameterType			= 'search_type'
	_ParameterField			= 'search_field'
	_ParameterQuery			= 'query'
	_ParameterSort			= 'order_by'
	_ParameterOrder			= 'order_direction'
	_ParameterCategory		= 'categories'
	_ParameterOffset		= 'from'
	_ParameterLimit			= 'size'
	_ParameterUnsafe		= 'hide_unsafe'
	_ParameterAdult			= 'hide_xxx'

	_ParameterSeeds			= 'seeders'
	_ParameterDescending	= 'desc'
	_ParameterScore			= 'score'
	_ParameterPerfect		= '100%'
	_ParameterTitle			= 'title'

	_CookieFilter			= 'filter'
	_CookieSearch			= 'search'
	_CookieFast				= 'fast'
	_CookieLive				= 'live'
	_CookieUnsafe			= 'unsafe'
	_CookieAdult			= 'hideXXX'

	_AttributeMain			= 'invisdiv'
	_AttributeTable			= 'caption-top'
	_AttributePages			= 'pageNumbers'

	_AttributeHits			= 'hits'
	_AttributeSize			= 'bytes'
	_AttributeTime			= 'date'
	_AttributeName			= 'title'
	_AttributeHash			= 'hash'
	_AttributeMagnet		= 'magnetUrl'
	_AttributeSeeds			= 'seeders'
	_AttributeLeeches		= 'peers'
	_AttributePublisher		= 'cachedOrigin'
	_AttributeDownloads		= 'grabs'

	_ExpressionType			= '(?:^|\s|\-|:|>|\/)\s*(video|movie|tv|show|episode|hd|4k|3d|hdr|x264|x265|other|foreign)'
	_ExpressionSize			= '(\d+)\s'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		name			= 'Knaben'
		description		= '{name} is a less-known {container} site that indexes other {container} sites. The site contains results in various languages, but most of them are in English. {name} has many links that are unusable and are therefore excluded from the results. Version %s uses an API which is fast, but uses cached search and might return fewer results for newer releases. Version %s uses the website which is slow, since it conducts a live search, but might return more results for newer releases.' % (ProviderJson.Version1, ProviderJson.Version2)
		customVersion	= 2

		version = self.customVersion()

		if version == ProviderJson.Version1:
			ProviderJson.initialize(self,
				name					= name,
				description				= description,

				# Too many links returned from 1337x and other sources that are not magnets and cannot be used.
				rank					= 4,
				performance				= ProviderJson.PerformanceGood,

				link					= Provider._Link,

				customVersion			= customVersion,
				customVerified			= True,
				customAdult				= True,

				supportMovie			= True,
				supportShow				= True,
				supportPack				= True,

				offsetStart				= 0,
				offsetIncrease			= Provider._LimitOffset,

				searchQuery				= {
											ProviderJson.RequestMethod		: ProviderJson.RequestMethodPost,
											ProviderJson.RequestType		: ProviderJson.RequestTypeJson,
											ProviderJson.RequestSubdomain	: Provider._Api,
											ProviderJson.RequestPath		: Provider._Path[version],
											ProviderJson.RequestData		: {
												# NB: Do not use _ParameterScore, otherwise random results are returned.
												# _ParameterScore can be used if sorting is not specified, so that the results are sorted by score instead.
												# This works and returns the correct results. But down the list there are other incorrect links. Eg: same show, but different episode numbers.
												# Using "100%" seems to be the best option at the moment.
												Provider._ParameterType		: Provider._ParameterPerfect,

												Provider._ParameterField	: Provider._ParameterTitle,
												Provider._ParameterCategory	: ProviderJson.TermCategory,
												Provider._ParameterQuery	: ProviderJson.TermQuery,
												Provider._ParameterOffset	: ProviderJson.TermOffset,
												Provider._ParameterLimit	: Provider._LimitOffset,
												Provider._ParameterSort		: Provider._ParameterSeeds,
												Provider._ParameterOrder	: Provider._ParameterDescending,
												Provider._ParameterUnsafe	: bool(self.customVerified()),
												Provider._ParameterAdult	: bool(self.customAdult()),
											},
										},

				searchCategoryMovie		= [[int(i) for i in Provider._CategoryMovie]], # Nested array, otherwise only a single cateogty is passed as an int, instead of a list.
				searchCategoryShow		= [[int(i) for i in Provider._CategoryShow]], # Nested array, otherwise only a single cateogty is passed as an int, instead of a list.

				extractList				= Provider._AttributeHits,
				extractHash				= Provider._AttributeHash,
				extractLink				= Provider._AttributeMagnet,
				extractFileName			= Provider._AttributeName,
				extractFileSize			= Provider._AttributeSize,
				extractSourceTime		= Provider._AttributeTime,
				extractSourceSeeds		= Provider._AttributeSeeds,
				extractSourceLeeches	= Provider._AttributeLeeches,
				extractSourcePublisher	= Provider._AttributePublisher,
				extractSourceApproval	= Provider._AttributeDownloads,
			)

		elif version == ProviderJson.Version2:
			# Live search is slower, but returns more links, especially for newer content.
			#cookies = {Provider._CookieSearch : Provider._CookieFast}
			cookies = {Provider._CookieSearch : Provider._CookieLive}

			if not self.customVerified(): cookies[Provider._CookieUnsafe] = True
			if self.customAdult(): cookies[Provider._CookieAdult] = True
			cookies = Converter.quoteTo(Converter.jsonTo(cookies))

			ProviderHtml.initialize(self,
				name						= name,
				description					= description,
				rank						= 3,
				performance					= ProviderHtml.PerformanceGood,

				link						= Provider._Link,

				customVersion				= customVersion,
				customVerified				= True,
				customAdult					= True,

				supportMovie				= True,
				supportShow					= True,
				supportPack					= True,

				offsetStart					= 1,
				offsetIncrease				= 1,

				formatEncode				= ProviderHtml.FormatEncodeQuote,

				searchQuery					= {
												ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
												ProviderHtml.RequestPath : Provider._Path[version] % (ProviderHtml.TermQuery, ProviderHtml.TermCategory, ProviderHtml.TermOffset, Provider._ParameterSeeds),
												ProviderHtml.RequestCookies : {Provider._CookieFilter : cookies},
											},
				searchCategoryMovie			= Provider._CategoryMovie,
				searchCategoryShow			= Provider._CategoryShow,

				#extractOptimizeData			= HtmlDiv(id_ = Provider._AttributeMain), # Layout was changed. No parent div can be uniquely identified anymore.
				extractList					= HtmlResultsTable(class_ = Provider._AttributeTable),
				extractLink					= [HtmlResult(index = 1), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
				extractFileName				= [HtmlResult(index = 1), HtmlLink(extract = Html.ParseTextNested)],
				extractFileSize				= [HtmlResult(index = 2, extract = [Html.AttributeTitle, Provider._ExpressionSize])],
				extractSourceTime			= [HtmlResult(index = 3, extract = Html.AttributeTitle)],
				extractSourceSeeds			= [HtmlResult(index = 4, extract = Html.ParseTextNested)],
				extractSourceLeeches		= [HtmlResult(index = 5, extract = Html.ParseTextNested)],
			)

	##############################################################################
	# PROCESS
	##############################################################################

	# No way to detect the last page anymore.
	'''def processOffset(self, data, items):
		try:
			next = self.extractHtml(data, [HtmlDiv(class_ = Provider._AttributePages), HtmlLink(index = -1, extract = Html.AttributeHref)])
			if not next: return ProviderHtml.Skip
		except: self.logError()'''

	def processBefore(self, item):
		if self.customVersion2():
			type = self.extractHtml(item, [HtmlResult(index = 0, extract = Html.ParseTextNested)])
			if not type or not Regex.match(data = type, expression = Provider._ExpressionType, cache = True): return ProviderHtml.Skip

	def processLink(self, value, item, details = None, entry = None):
		# A lot of the entries (eg 1337x, RuTracker, etc) do not have a magnet, but a HTTP link that resolves to a magnet.
		if value and Regex.match(data = value, expression = Provider.ExpressionMagnet, cache = True): return value
		else: return ProviderHtml.Skip

	def processSourceTime(self, value, item, details = None, entry = None):
		if self.customVersion1() and value: return Regex.extract(data = value, expression = '(\d{4}\-\d{2}\-\d{2}T\d{2}\:\d{2}\:\d{2})', cache = True)
		return value
