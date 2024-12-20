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
from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlLink

# https://eztv.re/api/

# The API is currently very limited, and therefore the HTML version is the default:
#	1. The API does not always return all the results that aare available. Eg: Game of Thrones S01E01 has 1 result in the API, but 3 results on the website.
#	2. There is no way to filter by seaason/episode number in the API. The API returns all the episode for a given show. If the wanted link is on page 5, but the user only scrapes up to page 3, nothing will be found.
#	3. The API cannot do exact searches.

# Update (2024-12): The new site now does not show the magnets on the first page anymore and requires a button click.
# This just sends some form-data to make the magnets visible without much effort.
# But use the API as default for now.

class Provider(ProviderJson, ProviderHtml):

	_Link				= ['https://eztvx.to', 'https://eztv.ag', 'https://eztv.it', 'https://eztv.ch', 'https://eztv.li', 'https://eztv.wf', 'https://eztv.tf', 'https://eztv.yt', 'https://eztv.re']
	_Mirror				= ['https://eztvstatus.com']
	_Unblock			= {ProviderHtml.UnblockFormat1 : 'eztv', ProviderHtml.UnblockFormat2 : 'eztv', ProviderHtml.UnblockFormat3 : 'eztv2', ProviderHtml.UnblockFormat4 : 'eztv'}
	_Path				= {
							ProviderHtml.Version1 : 'api/get-torrents?imdb_id=%s&page=%s&limit=%d',
							ProviderHtml.Version2 : 'search/%s',
						}

	_LimitOffset		= 100	# The maximum number of results returned by a query.
	_LimitIncorrect		= 5		# The maximum number of different shows appearing on the same result page, at which it is considered that nothing was found (EZTV then shows a page of latests uploads).

	_AttributeTorrents	= 'torrents'
	_AttributeImdb		= 'imdb_id'
	_AttributeLink		= 'magnet_url'
	_AttributeName		= 'filename'
	_AttributeSize		= 'size_bytes'
	_AttributeHash		= 'hash'
	_AttributeTime		= 'date_released_unix'
	_AttributeSeeds		= 'seeds'
	_AttributeLeeches	= 'peers'

	_AttributeSeason	= 'season'
	_AttributeEpisode	= 'episode'
	_AttributeCount		= 'torrents_count'
	_AttributeLimit		= 'limit'
	_AttributePage		= 'page'

	_AttributeTable		= 'forum_header_border'

	_AttributeLayout	= 'layout'
	_AttributeLinks		= 'def_wlinks'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		version = self.customVersion()
		if version == ProviderHtml.Version1:
			provider					= ProviderJson
			supportPack					= False
			offsetStart					= 1
			offsetIncrease				= 1
			formatEncode				= ProviderHtml.FormatEncodeDefault
			formatCase					= ProviderHtml.FormatCaseDefault
			searchQuery					= Provider._Path[version] % (ProviderJson.TermIdImdbNumber, ProviderJson.TermOffset, Provider._LimitOffset)

			extractList					= Provider._AttributeTorrents
			extractLink					= Provider._AttributeLink
			extractFileName				= Provider._AttributeName
			extractHash					= Provider._AttributeHash
			extractFileSize				= Provider._AttributeSize
			extractSourceTime			= Provider._AttributeTime
			extractSourceTimeInexact	= None
			extractSourceSeeds			= Provider._AttributeSeeds
			extractSourceLeeches		= Provider._AttributeLeeches
		elif version == ProviderHtml.Version2:
			provider					= ProviderHtml
			supportPack					= True
			offsetStart					= None # Only "latests releases" has page numbers. Result pages list all links on one page.
			offsetIncrease				= None
			formatEncode				= ProviderHtml.FormatEncodeMinus
			formatCase					= ProviderHtml.FormatCaseLower
			searchQuery					= {
											ProviderHtml.RequestMethod : ProviderHtml.RequestMethodPost,
											ProviderHtml.RequestPath : Provider._Path[version] % ProviderJson.TermQuery,

											# The new website hides the magnet buttons.
											# But when POSTing this parameter, the links are made visible.
											ProviderHtml.RequestData : {Provider._AttributeLayout : Provider._AttributeLinks},
										},

			extractList					= HtmlResults(class_ = Provider._AttributeTable, index = -1, start = 2)
			extractLink					= [HtmlResult(index = 2), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)]
			extractFileName				= HtmlResult(index = 1)
			extractHash					= None
			extractFileSize				= HtmlResult(index = 3)
			extractSourceTime			= None
			extractSourceTimeInexact	= HtmlResult(index = 4)
			extractSourceSeeds			= HtmlResult(index = 5)
			extractSourceLeeches		= None

		provider.initialize(self,
			name						= 'EZTV',
			description					= '{name} is one of the oldest and most well-known {container} sites. The site contains results in various languages, but most of them are in English. {name} only indexes shows and has few results. {name} has two versions of the provider. Version %s uses the {name} API. Although the API is fast, its functionality is very limited, often not returning all the available results. Version %s scrapes the website and has incomplete metadata.' % (ProviderHtml.Version1, ProviderHtml.Version2),
			rank						= 4,
			performance					= ProviderHtml.PerformanceGood,

			link						= Provider._Link,
			mirror						= Provider._Mirror,
			unblock						= Provider._Unblock,

			customVersion				= 2,

			supportMovie				= False,
			supportShow					= True,
			supportPack					= supportPack,

			offsetStart					= offsetStart,
			offsetIncrease				= offsetIncrease,

			formatEncode				= formatEncode,
			formatCase					= formatCase,

			searchQuery					= searchQuery,

			extractList					= extractList,
			extractLink					= extractLink,
			extractHash					= extractHash,
			extractFileName				= extractFileName,
			extractFileSize				= extractFileSize,
			extractSourceTime			= extractSourceTime,
			extractSourceTimeInexact	= extractSourceTimeInexact,
			extractSourceSeeds			= extractSourceSeeds,
			extractSourceLeeches		= extractSourceLeeches,
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processFileName(self, value, item, details = None, entry = None):
		return value if value else None

	def processData(self, data):
		if self.customVersion1():
			# EZTV currently only supports searching by IMDb ID, and not by title.
			# If no results are found, instead of returning nothing, a list of latests releases is returned.
			# If results are found, the root element contains a IMDb ID attribute.
			if not Provider._AttributeImdb in data:	return ProviderJson.Skip
		return data

	def processItems(self, items):
		if self.customVersion2():
			# If nothing is found for the query, EZTV returns a table of latest uploads, instead of an empty table.
			# There seems to be nothing that would distinguish  a fake table like this from a table with actual results.
			# Just check the number of different shows that appear on the page, and if it exceeds a threshold, assume the page returned nothing.
			shows = [self.extractHtml(item = item, keys = [HtmlResult(index = 0), HtmlLink(extract = Html.AttributeTitle)]) for item in items]
			shows = list(set(shows))
			if len(shows) > Provider._LimitIncorrect: return ProviderJson.Skip
		return items

	def processOffset(self, data, items):
		if self.customVersion1():
			count = data[Provider._AttributeCount]
			limit = data[Provider._AttributeLimit]
			page = data[Provider._AttributePage]
			if count <= (limit * page): return ProviderJson.Skip

	def processBefore(self, item):
		if self.customVersion1():
			season = item[Provider._AttributeSeason]
			try: season = int(season)
			except: season = 0
			if not season == 0 and not season == self.parameterNumberSeason(): return ProviderJson.Skip

			episode = item[Provider._AttributeEpisode]
			try: episode = int(episode) # Season packs have "0" as the episode number.
			except: episode = 0
			if not episode == 0 and not episode == self.parameterNumberEpisode(): return ProviderJson.Skip
