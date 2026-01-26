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
from lib.modules.tools import System, Regex

class Provider(ProviderJson):

	_Link					= ['https://bitlordsearch.com']
	_Path					= {
								ProviderJson.Version1 : 'api/list/', # Must end in "/", otherwise some requests fail.
								ProviderJson.Version2 : 'get_list',
							}

	_LimitOffset			= 1000

	# BitLord is very slow in returning results.
	# Using multiple categories, each with its own request, makes scraping even slower.
	#	Multiple categories:	74 results (65 seconds)
	#	Single category:		63 results (25 seconds)
	#	No category:			85 results (25 seconds)
	# Instead, search all categories at once, which is substation ally faster and also returns a few more results.
	_CategoryMovie			= {
								#ProviderJson.Version1 : ['Movies+%26+Video', 'None'] # Do not split into "Movies" and "Video", since it is a single category and otherwise the requests fail.
								ProviderJson.Version1 : [''],
								ProviderJson.Version2 : '3',
							}
	_CategoryShow			= {
								#ProviderJson.Version1 : ['Series', 'None'],
								ProviderJson.Version1 : [''],
								ProviderJson.Version2 : '4',
							}

	_ParameterTrue			= 'true'
	_ParameterFalse			= 'false'
	_ParameterOffset		= 'offset'
	_ParameterLimit			= 'limit'

	_ParameterQuery1		= 'title'
	_ParameterSort1			= 'sort_seeds'
	_ParameterDescending1	= 'down'
	_ParameterCategory1		= 'category'
	_ParameterPorn1			= 'adult'
	_ParameterSpam1			= 'is_verified'

	_ParameterQuery2		= 'query'
	_ParameterDescending2	= 'desc'
	_ParameterSeeds2		= 'seeds'
	_ParameterAll2			= '4'
	_ParameterSort2			= 'filters[field]'
	_ParameterOrder2		= 'filters[sort]'
	_ParameterTime2			= 'filters[time]'
	_ParameterCategory2		= 'filters[category]'
	_ParameterPorn2			= 'filters[adult]'
	_ParameterSpam2			= 'filters[risky]'

	_AttributeList			= 'content'
	_AttributeSeeds			= 'seeds'
	_AttributeLeeches		= 'peers'

	_AttributId1			= '_id'
	_AttributeLink1			= 'magnet_link'
	_AttributeName1			= 'fulltext_index'
	_AttributeSize1			= 'size_in_byte'
	_AttributeTime1			= 'created_time'

	_AttributId2			= 'id'
	_AttributeLink2			= 'magnet'
	_AttributeName2			= 'name'
	_AttributeSize2			= 'size'
	_AttributeTime2			= 'age'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		version = self.customVersion()
		if version == ProviderJson.Version1:
			accountAuthentication	= {ProviderJson.ProcessMode : ProviderJson.AccountModeScrape}

			# The string-matching algorithm used by BitLord is horrible.
			# Plus-encoding "+" is used by default.
			# However, when using various encodings ("%20", "+", "-"), often few results are returned.
			# This becomes even worse when searching by "Title Year", often not returning any results.
			# When using a dot as separator, considrably more results are returned.
			# The dot-encoding also returns results with spaces. The query "Title.Year" returns results for both "Title.Year" and "Title Year".
			# Adding the year also removes a lot of valid results.
			# This is still not perfect. If there are symbols (eg ":") in the title, often no results are returned at all.
			# If this symbol is not included, no results are returned.
			# Eg:
			#	"avatar the way of water"			: 1 results
			#	"avatar the way of water 2022"		: 0 results
			#	"avatar.the.way.of.water"			: 1 results
			#	"avatar.the.way.of.water.2022"		: 0 results
			#	"avatar: the way of water"			: 6 results
			#	"avatar: the way of water 2022"		: 0 results
			#	"avatar:.the.way.of.water"			: 6 results
			#	"avatar:.the.way.of.water.2022"		: 0 results
			# On the other hand, if we use the original title:
			#	"Bosch: Legacy"						: 0 results
			#	"Bosch Legacy"						: many results
			#	"Bosch.Legacy"						: many results
			# Or:
			#	"Final: Destination Bloodlines"		: 0 results
			#	"Final Destination Bloodlines"		: 2 results
			#	"Final.Destination.Bloodlines"		: 2 results
			# Hence, search with raw vs processed titles each has its own problem.
			# Hopefully they fix their search algorithm in the future, so that is works better with the default queries.
			formatEncode			= ProviderJson.FormatEncodePlus

			searchQuery				= {
										ProviderJson.RequestPath : Provider._Path[version],
										ProviderJson.RequestData : {
											Provider._ParameterQuery1		: ProviderJson.TermQuery,
											Provider._ParameterCategory1	: ProviderJson.TermCategory,
											Provider._ParameterLimit		: Provider._LimitOffset,
											Provider._ParameterOffset		: ProviderJson.TermOffset,
											Provider._ParameterSort1		: Provider._ParameterDescending1,
											Provider._ParameterSpam1		: Provider._ParameterTrue if self.customSpam() else Provider._ParameterFalse,
											Provider._ParameterPorn1		: Provider._ParameterFalse if self.customAdult() else Provider._ParameterTrue,
										},
									}

			extractList				= None
			extractLink				= Provider._AttributeLink1,
			extractIdLocal			= Provider._AttributId1
			extractFileName			= Provider._AttributeName1
			extractFileSize			= Provider._AttributeSize1
			extractSourceTime		= Provider._AttributeTime1
			extractSourceSeeds		= Provider._AttributeSeeds
			extractSourceLeeches	= Provider._AttributeLeeches

		elif version == ProviderJson.Version2:
			accountAuthentication	= {
										ProviderJson.ProcessMode : ProviderJson.AccountModeScrape,
										ProviderJson.ProcessRequest : {
											ProviderJson.RequestMethod : ProviderJson.RequestMethodGet,
										},
										ProviderJson.ProcessExtract : {
											ProviderJson.RequestCookies : ProviderJson.RequestCookiePhp,
											ProviderJson.RequestHeaders : {
												ProviderJson.RequestHeaderRequestToken : [r'token\s*:\s*(.*?)(?:$|\s|,)', r'%s\s*\+?=\s*[\'"](.*?)[\'";]'],
											},
										},
										ProviderJson.ProcessValidate : {ProviderJson.RequestHeaders : {ProviderJson.RequestHeaderRequestToken : r'.{1,}'}},
									}

			formatEncode			= ProviderJson.FormatEncodeNone

			searchQuery				= {
										ProviderJson.RequestMethod : ProviderJson.RequestMethodPost,
										ProviderJson.RequestPath : Provider._Path[version],
										ProviderJson.RequestData : {
											Provider._ParameterQuery2		: ProviderJson.TermQuery,
											Provider._ParameterCategory2	: ProviderJson.TermCategory,
											Provider._ParameterOffset		: ProviderJson.TermOffset,
											Provider._ParameterLimit		: Provider._LimitOffset,
											Provider._ParameterSort2		: Provider._ParameterSeeds2,
											Provider._ParameterOrder2		: Provider._ParameterDescending2,
											Provider._ParameterTime2		: Provider._ParameterAll2,
											Provider._ParameterPorn2		: Provider._ParameterFalse,
											Provider._ParameterSpam2		: Provider._ParameterFalse if self.customSpam() else Provider._ParameterTrue,
										},
									}

			extractList				= Provider._AttributeList
			extractLink				= Provider._AttributeLink2
			extractIdLocal			= Provider._AttributId2
			extractFileName			= Provider._AttributeName2
			extractFileSize			= Provider._AttributeSize2
			extractSourceTime		= Provider._AttributeTime2
			extractSourceSeeds		= Provider._AttributeSeeds
			extractSourceLeeches	= Provider._AttributeLeeches

		ProviderJson.initialize(self,
			name					= 'BitLord',
			description				= '{name} is a {container} indexer that scrapes other sites. The site contains results in various languages, but most of them are in English. {name} can be slow and return few results, and has missing or inaccurate file sizes.',

			# Queries are slow, especially for shows which can take 60-90 secs.
			# And sometimes no links are returned, even though if one rescrapes, suddenly there are links. Maybe a caching issue on BitLord?
			# Update (2025-12): BitLord can be super slow. Reduce rank to not include the provider during provider optimization.
			#rank					= 4,
			rank					= 3,
			performance				= ProviderJson.PerformanceMedium,

			link					= Provider._Link,

			accountAuthentication	= accountAuthentication,

			customVersion			= 2,
			customSpam				= True,
			customAdult				= True,

			supportMovie			= True,
			supportShow				= True,
			supportPack				= True,

			offsetStart				= 0,
			offsetIncrease			= Provider._LimitOffset,

			formatEncode			= formatEncode,

			searchQuery				= searchQuery,
			searchCategoryMovie		= Provider._CategoryMovie[version],
			searchCategoryShow		= Provider._CategoryShow[version],

			extractList				= extractList,
			extractLink				= extractLink,
			extractIdLocal			= extractIdLocal,
			extractFileName			= extractFileName,
			extractFileSize			= extractFileSize,
			extractSourceTime		= extractSourceTime,
			extractSourceSeeds		= extractSourceSeeds,
			extractSourceLeeches	= extractSourceLeeches,
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def accountAuthenticate(self):
		if self.customVersion1():
			def _extract(data): return System.obfuscate(data = data)
			data = self.requestText(path = _extract('PT1BWnRWRGJNbFdPNlIyUldwM1l5VVVQ'))
			if data:
				x0 = Regex.extract(data = data, expression = _extract('PT13U1dCVGFLRkRkNG9FUnY5eVNEdDJMTGxHTnZCVk13a21TeE1YY2pGemQ1c2tiT05HVTV4bWNpMUdieloyUjRsSFpZaFhlYWhsVzVwRldOWkRVNWRXUA=='))
				x1 = Regex.extract(data = data, expression = _extract('TFpGTUxsVWFrSm1aREZsTlFsM1p3QlZldlYzU0VsRFpKbEdaaXRrYk9OR1VUQm5lWVJFT3dwMVZ4Z21ZcWhEZFlSMGJ2c0VTS3gyWXpVVlA='))
				x2 = Regex.extract(data = data, expression = _extract('TFpGTUxsVWFrSm1aREZsTlFsM1p3QlZldlYzU0VsRFpKbEdaaXRrYk9OR1VUQm5lWVJFT3dwRlNLWkhaNmhEZFlSMGJ2c0VTT3BYV1lGVVA='))
				if x1 and x2:
					data = self.requestJson(method = ProviderJson.RequestMethodPost, link = x0 or None, path = _extract('PT1BVHlVRGJoSlRPd3drTXNkWFdSMVRQ'), data = {_extract('YWRWTW9KbWJLeDJZelVWUA==') : x1, _extract('YWhrUzJSMk1PcFhXWUZVUA==') : x2})
					if data:
						x3 = data.get(_extract('PU0yTU94V1d5NEVh'))
						if x3:
							self.linkRedirectSet(link = x0)
							return {ProviderJson.RequestHeaders : self.accountAuthorization(type = ProviderJson.AccountAuthorizationBearer, value = x3)}
			return False
		else:
			return None

	def processOffset(self, data, items):
		if self.customVersion1():
			try:
				if not items or len(items) < Provider._LimitOffset: return ProviderJson.Skip
			except: self.logError()

	def processLink(self, value, item, details = None, entry = None):
		if value:
			# Often returns links like: https://thepiratebay.orgmagnet:?xt=urn:btih:....
			value = Regex.extract(data = value, expression = ProviderJson.ExpressionMagnet)
		return value if value else None

	def processFileSize(self, value, item, details = None, entry = None):
		# BitLord scrapes other torrent sites.
		# The file size is often missing or given in different units (MB vs GB).
		try:
			value = float(value)
			if value > 0:
				if value < 75: value = value * 1073741824
				elif value < 75000: value = value * 1048576
				return int(value)
		except: pass
		return None
