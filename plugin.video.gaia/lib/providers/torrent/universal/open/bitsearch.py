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

# This is the exact same site as SolidTorrents, just with a different domain.
# Both use the same API and website layout.
# BitSearch and SolidTorrents could be different domains pointing to the same server.
# However, sometimes one site is accessible while the other is not. The inaccessbile site typically has a Cloudflare configuration error.
# This could be because of different servers or because of a Cloudflare issue.

from lib.providers.core.json import ProviderJson
from lib.providers.core.html import ProviderHtml, Html, HtmlMain, HtmlLink, HtmlDiv, HtmlSpan, HtmlNav, HtmlHeading5, HtmlHeading3, HtmlListItem, HtmlResultsDiv
from lib.modules.tools import Regex, Time

class Provider(ProviderJson, ProviderHtml):

	_Link					= ['https://bitsearch.to']
	_Path					= {
								ProviderHtml.Version1 : 'api/v1/search', # https://bitsearch.to/api
								ProviderHtml.Version2 : 'search',
							}

	_LimitOffset1			= 20 # Old API.
	_LimitOffset2			= 100 # New API. Default: 20, Maximum: 100.

	_LimitApproval			= {
								ProviderHtml.Version1 : 2000,
								ProviderHtml.Version2 : 5000,
							}

	# NB: There are a lot of titles listed under Other/Video.
	_CategoryMovie			= [2, 4, 1] # 2 = Movies, 4 = Anime, 1 = Other
	_CategoryShow			= [3, 4, 1] # 3 = TV, 4 = Anime, 1 = Other
	_CategoryVideo			= 'Video'
	_CategoryUnknown		= 'Unknown'

	_HeaderKey				= 'x-api-key'
	_HeaderLimit			= 'x-ratelimit-limit'

	_ParameterQuery			= 'q'
	_ParameterOffset		= 'skip'
	_ParameterPage			= 'page'
	_ParameterCategory		= 'category'
	_ParameterSort1			= 'sort'
	_ParameterSort2			= 'sortBy'
	_ParameterSeeds			= 'seeders'
	_ParameterSafety		= 'safety' # Does not seem to work at the moment.
	_ParameterSpam			= 'fuv'
	_ParameterYes			= 'yes'
	_ParameterNo			= 'no'
	_ParameterOrder			= 'order'
	_ParameterDescending	= 'desc'
	_ParameterLimit			= 'limit'
	_ParameterDummy			= 'dummy'

	_AttributeContainer1	= 'container'
	_AttributeContainer2	= 'mx-auto'
	_AttributeResult1		= 'search-result'
	_AttributeResult2		= 'space-y-4'
	_AttributeInfo1			= 'info'
	_AttributeInfo2			= 'flex'
	_AttributeInfo3			= 'flex-1'
	_AttributeInfo4			= 'flex-wrap'
	_AttributeInfo5			= 'flex-col'
	_AttributeInfo6			= 'inline-flex'
	_AttributeLinks			= 'links'
	_AttributeStats			= 'stats'
	_AttributeTitle1		= 'title'
	_AttributeTitle2		= 'text-base'
	_AttributePages			= 'pagination'
	_AttributeDisabled1		= 'disabled'
	_AttributeDisabled2		= 'cursor-not-allowed'

	_AttributList			= 'results'
	_AttributId1			= '_id'
	_AttributId2			= 'id'
	_AttributeLink			= 'magnet'
	_AttributeHash			= 'infohash'
	_AttributeName			= 'title'
	_AttributeSize			= 'size'
	_AttributeTime1			= 'imported'
	_AttributeTime2			= 'createdAt'
	_AttributeSwarm			= 'swarm'
	_AttributeSeeds			= 'seeders'
	_AttributeLeeches		= 'leechers'
	_AttributeVerified		= 'verified'
	_AttributeDownloads		= 'downloads'
	_AttributePage			= 'page'
	_AttributeTotal			= 'totalPages'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		name					= 'BitSearch'
		description				= '{name} is a {container} site and API. The site contains results in various languages, but most of them are in English. {name} is fast and has many {containers} with good metadata, but is often inaccessible.'

		# Down too often.
		rank					= 4
		performance				= ProviderHtml.PerformanceGood

		# Down very often with "Too many requests, please try again later." errors or occasional Cloudflare 520 errors.
		# Update (2025-12): Seems to be online again most of the time. Sometimes a Cloudflare 520 error, but typically disappears within 10 mins.
		#status					= ProviderHtml.StatusImpaired,
		status					= ProviderHtml.StatusOperational

		customVersion			= 2

		version = self.customVersion()
		if version == ProviderHtml.Version1:
			# Old API.
			'''category = ','.join([Provider._CategoryVideo, Provider._CategoryUnknown])
			ProviderJson.initialize(self,
				name					= name,
				description				= description,
				rank					= rank,
				performance				= performance,
				status					= status,

				link					= Provider._Link,

				customVersion			= customVersion,
				customSpam				= True,
				customVerified			= True,

				supportMovie			= True,
				supportShow				= True,
				supportPack				= True,

				offsetStart				= 0,
				offsetIncrease			= Provider._LimitOffset1,

				formatEncode			= ProviderJson.FormatEncodePlus,

				searchQuery				= {
											ProviderJson.RequestMethod : ProviderJson.RequestMethodGet,
											ProviderJson.RequestPath : Provider._Path[version],
											ProviderJson.RequestData : {
												Provider._ParameterQuery	: ProviderJson.TermQuery,
												Provider._ParameterCategory	: ProviderJson.TermCategory,
												Provider._ParameterOffset	: ProviderJson.TermOffset,
												Provider._ParameterSort1	: Provider._ParameterSeeds,
												Provider._ParameterSpam		: Provider._ParameterYes if self.customSpam() else Provider._ParameterNo,
											},
										},

				searchCategoryMovie		= category,
				searchCategoryShow		= category,

				extractList				= Provider._AttributList,
				extractLink				= Provider._AttributeLink,
				extractIdLocal			= Provider._AttributId1,
				extractFileName			= Provider._AttributeName,
				extractFileSize			= Provider._AttributeSize,
				extractSourceTime		= Provider._AttributeTime1,
				extractSourceApproval	= [Provider._AttributeSwarm, Provider._AttributeDownloads],
				extractSourceSeeds		= [Provider._AttributeSwarm, Provider._AttributeSeeds],
				extractSourceLeeches	= [Provider._AttributeSwarm, Provider._AttributeLeeches],
			)'''

			ProviderJson.initialize(self,
				name						= name,
				description					= description,
				rank						= rank,
				performance					= performance,
				status						= status,

				link						= Provider._Link,

				accountOptional				= True, # With API key: 1000 req/day. Without API key: 200 req/day.
				accountKey					= True,
				accountAuthentication		= {
												ProviderJson.ProcessMode : ProviderJson.AccountModeScrape,
												ProviderJson.ProcessFixed : {
													ProviderJson.RequestHeaders : {
														Provider._HeaderKey : ProviderJson.TermAuthenticationKey,
													},
												},
											},
				accountVerification			= {
												ProviderJson.ProcessRequest : {
													ProviderJson.RequestMethod : ProviderJson.RequestMethodGet,
													ProviderJson.RequestPath : Provider._Path[version],
													ProviderJson.RequestData : {
														Provider._ParameterQuery : 'ubuntu',
														Provider._ParameterLimit : 1,

														# Either BitSearch or Cloudflare is caching the results of a request based on the GET parameters.
														# Hence, verifying without an account, and then verifying with an account, returns the results of the first unverified call.
														# Add a random parameter to ensure that no cached results are returned.
														Provider._ParameterDummy : Time.timestamp(),
													},
												},
												ProviderJson.ProcessExtract : {
													ProviderJson.RequestHeaders : True,
												},
												ProviderJson.ProcessValidate : {
													ProviderJson.RequestHeaders : {Provider._HeaderLimit : '\d{4,}'}, # "x-ratelimit-tier: free" is only added if there is no API key. Check that the total limit is 1000 or greater.
												},
											},

				customVersion				= customVersion,
				customVerified				= True,

				supportMovie				= True,
				supportShow					= True,
				supportPack					= True,

				offsetStart					= 1,
				offsetIncrease				= 1,

				formatEncode				= ProviderJson.FormatEncodePlus,

				searchQuery					= {
												ProviderJson.RequestMethod : ProviderJson.RequestMethodGet,
												ProviderJson.RequestPath : Provider._Path[version],
												ProviderJson.RequestData : {
													Provider._ParameterQuery	: ProviderJson.TermQuery,
													Provider._ParameterCategory	: ProviderJson.TermCategory,
													Provider._ParameterPage		: ProviderJson.TermOffset,
													Provider._ParameterSort1	: Provider._ParameterSeeds,
													Provider._ParameterOrder	: Provider._ParameterDescending,
													Provider._ParameterLimit	: Provider._LimitOffset2,
												},
											},

				searchCategoryMovie			= Provider._CategoryMovie,
				searchCategoryShow			= Provider._CategoryShow,

				extractList					= Provider._AttributList,
				extractLink					= Provider._AttributeLink,
				extractHash					= Provider._AttributeHash,
				extractIdLocal				= Provider._AttributId2,
				extractFileName				= Provider._AttributeName,
				extractFileSize				= Provider._AttributeSize,

				# Only a few have this attribute and it seems to always be time it was added to the database and not the time the torrent was created.
				# Update: These seem to actually be the upload date, but only a few have them in the API, while the website shows dates for almost all torrents.
				# In the API at lot of the dates are from 2025, so this might not be the actual upload date. Hence, only set it as an inaccurate time.
				extractSourceTimeInexact	= Provider._AttributeTime2,

				extractSourceApproval		= Provider._AttributeDownloads,
				extractSourceSeeds			= Provider._AttributeSeeds,
				extractSourceLeeches		= Provider._AttributeLeeches,
			)

		elif version == ProviderHtml.Version2:
			# Old website.
			'''ProviderHtml.initialize(self,
				name						= name,
				description					= description,
				rank						= rank,
				performance					= performance,
				status						= status,

				link						= Provider._Link,

				customVersion				= customVersion,

				supportMovie				= True,
				supportShow					= True,
				supportPack					= True,

				offsetStart					= 1,
				offsetIncrease				= 1,

				formatEncode				= ProviderHtml.FormatEncodePlus,

				searchQuery					= {
												ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
												ProviderHtml.RequestPath : Provider._Path[version],
												ProviderHtml.RequestData : {
													Provider._ParameterQuery	: ProviderHtml.TermQuery,
													Provider._ParameterCategory	: ProviderHtml.TermCategory,
													Provider._ParameterPage		: ProviderHtml.TermOffset,
													Provider._ParameterSort		: Provider._ParameterSeeds,
												},
											},
				searchCategoryMovie			= Provider._CategoryMovie,
				searchCategoryShow			= Provider._CategoryShow,

				extractOptimizeData			= [HtmlMain(), HtmlDiv(class_ = Provider._AttributeContainer1, index = -1)], # Get the last container, since a new container was added to the top to download the mobile app.
				extractList					= HtmlListItem(class_ = Provider._AttributeResult1),
				extractLink					= [HtmlDiv(class_ = Provider._AttributeLinks), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
				extractFileName				= [HtmlDiv(class_ = Provider._AttributeInfo1), HtmlHeading5(class_ = Provider._AttributeTitle1), HtmlLink()], # Extract the link, since there can be a checkmark icon next to the file name.
				extractFileSize				= [HtmlDiv(class_ = Provider._AttributeInfo1), HtmlDiv(class_ = Provider._AttributeStats), HtmlDiv(index = 1)],
				extractSourceTime			= [HtmlDiv(class_ = Provider._AttributeInfo1), HtmlDiv(class_ = Provider._AttributeStats), HtmlDiv(index = 4)],
				extractSourceSeeds			= [HtmlDiv(class_ = Provider._AttributeInfo1), HtmlDiv(class_ = Provider._AttributeStats), HtmlDiv(index = 2)],
				extractSourceLeeches		= [HtmlDiv(class_ = Provider._AttributeInfo1), HtmlDiv(class_ = Provider._AttributeStats), HtmlDiv(index = 3)],
				extractSourceApproval		= [HtmlDiv(class_ = Provider._AttributeInfo1), HtmlDiv(class_ = Provider._AttributeStats), HtmlDiv(index = 0)],
			)'''

			# New website.
			ProviderHtml.initialize(self,
				name						= name,
				description					= description,
				rank						= rank,
				performance					= performance,
				status						= status,

				link						= Provider._Link,

				customVersion				= customVersion,

				supportMovie				= True,
				supportShow					= True,
				supportPack					= True,

				offsetStart					= 1,
				offsetIncrease				= 1,

				formatEncode				= ProviderHtml.FormatEncodePlus,

				searchQuery					= {
												ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
												ProviderHtml.RequestPath : Provider._Path[version],
												ProviderHtml.RequestData : {
													Provider._ParameterQuery	: ProviderHtml.TermQuery,
													Provider._ParameterCategory	: ProviderHtml.TermCategory,
													Provider._ParameterPage		: ProviderHtml.TermOffset,
													Provider._ParameterSort2	: Provider._ParameterSeeds,
													Provider._ParameterOrder	: Provider._ParameterDescending,
												},
											},
				searchCategoryMovie			= Provider._CategoryMovie,
				searchCategoryShow			= Provider._CategoryShow,

				extractParser				= ProviderHtml.ParserHtml5, # Has some issues in the HTML.
				extractOptimizeData			= [HtmlMain(class_ = Provider._AttributeContainer2, index = 0)], # Get the last container, since a new container was added to the top to download the mobile app.
				extractList					= HtmlResultsDiv(class_ = Provider._AttributeResult2),
				extractLink					= [HtmlDiv(class_ = Provider._AttributeInfo5), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
				extractFileName				= [HtmlDiv(class_ = Provider._AttributeInfo3), HtmlHeading3(class_ = Provider._AttributeTitle2), HtmlLink()], # Extract the link, since there can be a checkmark icon next to the file name.
				extractFileSize				= [HtmlDiv(class_ = Provider._AttributeInfo3), HtmlDiv(class_ = Provider._AttributeInfo4, index = 0), HtmlSpan(class_ = Provider._AttributeInfo6, index = 1)],
				extractSourceTimeInexact	= [HtmlDiv(class_ = Provider._AttributeInfo3), HtmlDiv(class_ = Provider._AttributeInfo4, index = 0), HtmlSpan(class_ = Provider._AttributeInfo6, index = 2)], # Inexact, because a lot of the dates seem to incorrect (rather the database time instead of the uplaod time).
				extractSourceSeeds			= [HtmlDiv(class_ = Provider._AttributeInfo3), HtmlDiv(class_ = Provider._AttributeInfo4, index = 1), HtmlSpan(class_ = Provider._AttributeInfo6, index = 0), HtmlSpan(index = 0)],
				extractSourceLeeches		= [HtmlDiv(class_ = Provider._AttributeInfo3), HtmlDiv(class_ = Provider._AttributeInfo4, index = 1), HtmlSpan(class_ = Provider._AttributeInfo6, index = 1), HtmlSpan(index = 0)],
				extractSourceApproval		= [HtmlDiv(class_ = Provider._AttributeInfo3), HtmlDiv(class_ = Provider._AttributeInfo4, index = 1), HtmlSpan(class_ = Provider._AttributeInfo6, index = 2), HtmlSpan(index = 0)],
			)

	##############################################################################
	# PROCESS
	##############################################################################

	def processBefore(self, item):
		try:
			if self.customVerified():
				version = self.customVersion()
				if version == ProviderHtml.Version1:
					# New API.
					if not item.get(Provider._AttributeVerified): return ProviderJson.Skip

					# Old API.
					elif not (item.get(Provider._AttributeSwarm) or {}).get(Provider._AttributeVerified): return ProviderJson.Skip
				elif version == ProviderHtml.Version2:
					verified = self.extractHtml(item, [HtmlDiv(class_ = Provider._AttributeInfo3), HtmlDiv(class_ = Provider._AttributeInfo2), HtmlSpan(class_ = Provider._AttributeInfo6, extract = Html.ParseTextNested)])
					if not verified or not verified.lower() == Provider._AttributeVerified: return ProviderJson.Skip
		except: self.logError()

	def processOffset(self, data, items):
		version = self.customVersion()
		if version == ProviderHtml.Version1:
			# Only for the new API.
			try:
				pagination = data.get(Provider._AttributePages)
				if pagination and pagination[Provider._AttributePage] == pagination[Provider._AttributeTotal]: return ProviderHtml.Skip
			except: self.logError()
		elif version == ProviderHtml.Version2:
			try:
				# Old website.
				next1 = self.extractHtml(data, [HtmlDiv(class_ = Provider._AttributePages), HtmlLink(index = -1, extract = Html.AttributeClass)])

				# New website.
				next2 = self.extractHtml(data, [HtmlNav(class_ = Provider._AttributeInfo2), HtmlSpan(index = -1, extract = Html.AttributeClass)])

				if (not next1 and not next2) or (next1 and Provider._AttributeDisabled1 in next1) or (next2 and Provider._AttributeDisabled2 in next2): return ProviderHtml.Skip
			except: self.logError()

	def processSourceTime(self, value, item, details = None, entry = None):
		if self.customVersion2():
			if value: value = Time.timestamp(value, format = '%m/%d/%Y')
		return value

	def processSourceApproval(self, value, item, details = None, entry = None):
		version = self.customVersion()
		if version == ProviderHtml.Version1:
			result = ProviderJson.ApprovalDefault
			try: result += (1 - result) * (float(value) / Provider._LimitApproval[version])
			except: pass
			return result
		elif version == ProviderHtml.Version2:
			result = ProviderHtml.ApprovalDefault
			try:
				if value:
					# Old website.
					# New website has downloads in full-digit integers.
					value = value.lower()
					multiplier = 1
					if 'b' in value: multiplier = 1000000000
					elif 'm' in value: multiplier = 1000000
					elif 'k' in value: multiplier = 1000
					value = Regex.extract(data = value, expression = '(\d+(?:\.\d+)?)')
					value = float(value) * multiplier

					result += (1 - result) * max(0, min(1, (float(value) / Provider._LimitApproval[version])))
			except: self.logError()
			return result
		return value
