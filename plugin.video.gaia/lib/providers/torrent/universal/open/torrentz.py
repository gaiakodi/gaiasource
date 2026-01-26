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
from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlLink, HtmlTable, HtmlDiv, HtmlSpan, HtmlButton, HtmlParagraph, HtmlDescriptionList, HtmlDescriptionName, HtmlDescriptionValue
from lib.modules.tools import Regex

# Torrentz seems to be permanently  down (torrentz2.eu).
# The onion domain (tzwealmisr.onion) still worked, but it is also down now, probably due to new onion v3 domains.
# A new domain has popped up (torrentz2.cyou), which has 3 search modes:
#	1. Exact Search: HTML searches the local Torrentz database.
#	2. Full Search: API searches. Seems to just be a wrapper on ApiBay (URL, parameters and returned data is at least the same).
#	3. Multi Search: Returns too many incorrect results, especially when sorted.
# Update: torrentz2.nz now seems to be a copy of BitSearch/SolidTorrents. Both those sites also have a link poiting to this domain.

class Provider(ProviderJson, ProviderHtml):

	_Link					= {
								# Update (2025-06): The torrentz2.nz domain still works, but the website behind it only loads partially.
								# New domains exist, bu their search results are poiting to other torrents sites (torrentz2.io, torrentz.eu.com, thetorrentz.com).
								# https://fastestvpn.com/blogs/torrentz2-proxy-and-alternatives/
								# https://www.techworm.net/2020/06/torrentz2-eu-alternatives.html
								ProviderHtml.Version1 : ['https://torrentz2.nz'],
								ProviderHtml.Version2 : ['https://torrentz2.cyou'], # Must have the wwX subdomain, otherwise it will fail. But the subdomain always changes (ww5, ww7, etc). Retrieve the subdomain through the authentication process.
								ProviderHtml.Version3 : ['https://torrentz2.cyou'], # Does not require the wwX subdomain.
								ProviderHtml.Version4 : ['https://torrentzwealmisr.onion.ly'], # torrentz2.eu is down, torrentz2.pl and torrentz2.is return Cloudflare errors.
							}

	_Mirror					= {
								ProviderHtml.Version1 : None,
								ProviderHtml.Version2 : None,
								ProviderHtml.Version3 : None,
								ProviderHtml.Version4 : None, # Down: https://torrentsmirror.com
							}

	_Unblock				= {
								ProviderHtml.Version1 : None,
								ProviderHtml.Version2 : None,
								ProviderHtml.Version3 : None,
								ProviderHtml.Version4 : {ProviderHtml.UnblockFormat1 : 'torrentz2', ProviderHtml.UnblockFormat2 : 'torrentz', ProviderHtml.UnblockFormat3 : 'torrentz'},
							}

	_PathUnverified			= {
								ProviderHtml.Version1 : 'search',
								ProviderHtml.Version2 : 'find/%s/page/%s', # Just "find" can be used for the first page, but subsequent pages require the full path.
								ProviderHtml.Version3 : 'api.php?url=/q.php',
								ProviderHtml.Version4 : 'search', # Ordered by peers.
							}
	_PathVerified			= {
								ProviderHtml.Version1 : None,
								ProviderHtml.Version2 : None,
								ProviderHtml.Version3 : None,
								ProviderHtml.Version4 : 'verifiedP'	# Ordered by peers.
							}

	_CategoryMovie			= {
								ProviderHtml.Version1 : None,
								ProviderHtml.Version2 : ['movies', 'anime'],
								ProviderHtml.Version3 : ['201', '202', '207', '209'], # 201 = Movies, 202 = Movies DVDR, 207 = HD Movies, 209 = 3D
								ProviderHtml.Version4 : None,
							}
	_CategoryShow			= {
								ProviderHtml.Version1 : None,
								ProviderHtml.Version2 : ['tv', 'anime'],
								ProviderHtml.Version3 : ['205', '208'], # 205 = TV Shows, 208 = HD TV Shows
								ProviderHtml.Version4 : None,
							}

	_Query					= '%s?%s=%s%%26%s=%s' # URL-encode "&", since the URL is passed as a parameter, otherwise the category is ignored.

	_LimitOffset			= 100 # The maximum number of results returned by a query.

	_ParameterQuery1		= 'q'
	_ParameterQuery2		= 'f'
	_ParameterCategory1		= 'cat'
	_ParameterCategory2		= 'sortcat'
	_ParameterSort			= 'sorter'
	_ParameterPage1			= 'page'
	_ParameterPage2			= 'p'
	_ParameterSeeds			= 'seed'
	_ParameterSafe			= 'safe'
	_ParameterYes			= '1'
	_ParameterNo			= '0'

	_AttributeContent		= 'results'
	_AttributeUploader		= 'username'
	_AttributeName			= 'name'
	_AttributeSize			= 'size'
	_AttributeHash			= 'info_hash'
	_AttributeTime			= 'added'
	_AttributeStatus		= 'status'
	_AttributeSeeds			= 'seeders'
	_AttributeLeeches		= 'leechers'
	_AttributeImdb			= 'imdb'
	_AttributeVip			= 'vip'
	_AttributeTrusted		= 'trusted'
	_AttributeMember		= 'member'
	_AttributeResults		= 'results'
	_AttributePages			= 'pagination'
	_AttributeDisabled		= 'disabled'

	_ExpressionHash			= r'\/([a-z0-9]{32,})(?:[\/\?\&]|$)'
	_ExpressionVideo		= r'(video)'
	_ExpressionNext			= r'(next)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		version = self.customVersion()
		id = self.customSearchId()
		category = self.customCategory()

		name			= 'Torrentz'
		description		= '{name} is one of the oldest and most well-known {container} sites. The site contains results in various languages, but most of them are in English. {name} changes their domain often and has missing metadata. {name} has strong Cloudflare protection that might not be bypassable and cause scraping to fail. Version %s uses the new website structure. Version %s uses an API which does not have its own data, but instead retrieves data from ApiBay. Version %s uses the old website structure.' % (ProviderHtml.Version2, ProviderHtml.Version3, ProviderHtml.Version4)

		# Update (2024-12): New version 1 seems to better.
		# Update (2025-06): Domain is still up, but website is barebone without any functionality.
		#rank			= 2
		#performance	= ProviderHtml.PerformanceMedium - ProviderHtml.PerformanceStep
		#status			= ProviderHtml.StatusCloudflare # Cloudflare.
		rank			= 3
		performance		= ProviderHtml.PerformanceGood
		status			= ProviderHtml.StatusDead

		link			= Provider._Link[version]
		unblock			= Provider._Unblock[version]
		customVersion	= 4
		supportMovie	= True
		supportShow		= True
		supportPack		= True

		if version == ProviderHtml.Version1:
			ProviderHtml.initialize(self,
				name						= name,
				description					= description,
				rank						= rank,
				performance					= performance,
				status						= status,

				link						= link,
				unblock						= unblock,

				customVersion				= customVersion,

				supportMovie				= supportMovie,
				supportShow					= supportShow,
				supportPack					= supportPack,

				offsetStart					= 1,
				offsetIncrease				= 1,

				formatEncode				= ProviderHtml.FormatEncodePlus,

				searchQuery					= {
												ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
												ProviderHtml.RequestPath : Provider._PathUnverified[version],
												ProviderHtml.RequestData : {
													Provider._ParameterQuery1	: ProviderHtml.TermQuery,
													Provider._ParameterPage1	: ProviderHtml.TermOffset,
												},
											},

				extractOptimizeData			= HtmlDiv(class_ = Provider._AttributeContent), # To detect the last page in processOffset().
				extractList					= [HtmlDescriptionList()],
				extractLink					= [HtmlDescriptionValue(), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
				extractFileName				= [HtmlDescriptionName(), HtmlLink()],
				extractFileSize				= [HtmlDescriptionValue(), HtmlSpan(index = 2)],
				extractSourceTimeInexact	= [HtmlDescriptionValue(), HtmlSpan(index = 1)], # The "title" attribute has all the same fixed timestamp.
				extractSourceSeeds			= [HtmlDescriptionValue(), HtmlSpan(index = 3)],
				extractSourceLeeches		= [HtmlDescriptionValue(), HtmlSpan(index = 4)],
			)
		elif version == ProviderHtml.Version2:
			ProviderHtml.initialize(self,
				name						= name,
				description					= description,
				rank						= rank,
				performance					= performance,
				status						= status,

				link						= link,
				unblock						= unblock,

				customVersion				= customVersion,

				supportMovie				= supportMovie,
				supportShow					= supportShow,
				supportPack					= supportPack,

				accountAuthentication		= {
												ProviderHtml.ProcessMode : ProviderHtml.AccountModeScrape,
												ProviderHtml.ProcessRequest : {
													ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
												},
												ProviderHtml.ProcessExtract : {
													ProviderHtml.RequestHeaders : {
														ProviderHtml.RequestHeaderLocation : r'https?://(w+\d*)\..*',
													},
												},
											},

				offsetStart					= 1,
				offsetIncrease				= 1,

				searchQuery					= {
												ProviderHtml.RequestMethod : ProviderHtml.RequestMethodPost,
												ProviderHtml.RequestSubdomain : ProviderHtml.TermAuthentication,
												ProviderHtml.RequestPath : Provider._PathUnverified[version] % (Provider.TermQuery, Provider.TermOffset),
												ProviderHtml.RequestData : {
													Provider._ParameterQuery1		: ProviderHtml.TermQuery,
													#Provider._ParameterCategory1	: ProviderHtml.TermCategory, # Do not search by category, since there is a "Packs" category that is not searchable through parameters. Filter out manually.
													Provider._ParameterPage1		: ProviderHtml.TermOffset,
													Provider._ParameterSort			: Provider._ParameterSeeds,
												},
											},

				extractOptimizeData			= HtmlDiv(class_ = Provider._AttributeResults),
				extractList					= [HtmlResults()],
				extractLink					= [HtmlResult(index = 2), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
				extractReleaseUploader		= [HtmlResult(index = 7)],
				extractFileName				= [HtmlResult(index = 1), HtmlLink(index = 0)],
				extractFileSize				= [HtmlResult(index = 4)],
				extractSourceTimeInexact	= [HtmlResult(index = 3)],
				extractSourceSeeds			= [HtmlResult(index = 5)],
				extractSourceLeeches		= [HtmlResult(index = 6)],
			)
		elif version == ProviderHtml.Version3:
			ProviderJson.initialize(self,
				name					= name,
				description				= description,
				rank					= rank,
				performance				= performance,
				status					= status,

				link					= link,
				unblock					= unblock,

				customVersion			= customVersion,
				customSearch			= {
											ProviderJson.SettingsDefault		: ProviderJson.CustomSearchTitle,
											ProviderJson.SettingsDescription	: 'Search {name} using the title or the IMDb ID. Not all files have an associated ID and searching by title might therefore return more results. Searching by title is slower and can return incorrect results. The title will be used if no ID is available.',
										},
				customCategory			= {
											ProviderJson.SettingsDefault		: True,
											ProviderJson.SettingsDescription	: '{name} returns a maximum of %d results per request. {name} has subcategories that can be searched together with a single request or can be searched separately with multiple requests. Searching categories separately might return more results, but can also increase the scraping time.' % Provider._LimitOffset,
										},
				customVerified			= True,

				supportMovie			= supportMovie,
				supportShow				= supportShow,
				supportPack				= supportPack,

				# Important to manually create the GET URL for version 4.
				# Since version 4 already has a ? in the URL, Networker will append the GET parameters with a &.
				#searchQuery				= {
				#							ProviderJson.RequestPath : path,
				#							ProviderJson.RequestData : {
				#								Provider._ParameterQuery	: Provider.TermIdImdb if id else Provider.TermQuery,
				#								Provider._ParameterCategory1	: ProviderJson.TermCategory,
				#							},
				#						},
				searchQuery				= [
											Provider._Query % (Provider._PathUnverified[version], Provider._ParameterQuery1, Provider.TermIdImdb if id else Provider.TermQuery, Provider._ParameterCategory1, ProviderJson.TermCategory),
											Provider._Query % (Provider._PathUnverified[version], Provider._ParameterQuery1, Provider.TermQuery, Provider._ParameterCategory1, ProviderJson.TermCategory),
										],

				searchCategoryMovie		= Provider._CategoryMovie[version] if category else ','.join(Provider._CategoryMovie[version]),
				searchCategoryShow		= Provider._CategoryShow[version] if category else ','.join(Provider._CategoryShow[version]),

				extractHash				= Provider._AttributeHash,
				extractReleaseUploader	= Provider._AttributeUploader,
				extractFileName			= Provider._AttributeName,
				extractFileSize			= Provider._AttributeSize,
				extractSourceTime		= Provider._AttributeTime,
				extractSourceApproval	= Provider._AttributeStatus,
				extractSourceSeeds		= Provider._AttributeSeeds,
				extractSourceLeeches	= Provider._AttributeLeeches,
			)
		elif version == ProviderHtml.Version4:
			ProviderHtml.initialize(self,
				name					= name,
				description				= description,
				rank					= rank,
				performance				= performance,
				status					= status,

				link					= link,
				unblock					= unblock,

				customVersion			= customVersion,
				customVerified			= True,
				customAdult				= True,

				supportMovie			= supportMovie,
				supportShow				= supportShow,
				supportPack				= supportPack,

				offsetStart				= 0,
				offsetIncrease			= 1,

				formatEncode			= ProviderHtml.FormatEncodeQuote,

				searchQuery				= {
											ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
											ProviderHtml.RequestPath : Provider._PathVerified[version] if self.customVerified() else Provider._PathUnverified[version],
											ProviderHtml.RequestData : {
												Provider._ParameterQuery2	: ProviderHtml.TermQuery,
												Provider._ParameterPage2	: ProviderHtml.TermOffset,
												Provider._ParameterSafe		: Provider._ParameterYes if self.customAdult() else Provider._ParameterNo,
											},
										},

				extractOptimizeData		= HtmlDiv(class_ = Provider._AttributeContent), # To detect the last page in processOffset().
				extractList				= [HtmlDescriptionList()],
				extractHash				= [HtmlDescriptionName(), HtmlLink(extract = [Html.AttributeHref, Provider._ExpressionHash])],
				extractFileName			= [HtmlDescriptionName(), HtmlLink()],
				extractFileSize			= [HtmlDescriptionValue(), HtmlSpan(index = 2)],
				extractSourceTime		= [HtmlDescriptionValue(), HtmlSpan(index = 1, extract = Html.AttributeTitle)],
				extractSourceSeeds		= [HtmlDescriptionValue(), HtmlSpan(index = 3)],
				extractSourceLeeches	= [HtmlDescriptionValue(), HtmlSpan(index = 4)],
			)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		if self.customVersion1():
			next = self.extractHtml(data, [HtmlDiv(class_ = Provider._AttributePages), HtmlLink(index = -1, extract = Html.AttributeClass)])
			if next and Provider._AttributeDisabled in next: return ProviderHtml.Skip
		elif self.customVersion2():
			try:
				next = False
				buttons = self.extractHtml(data, [HtmlButton()])
				if buttons:
					for button in buttons:
						if Regex.match(data = button.text, expression = Provider._ExpressionNext):
							next = True
							break
				if not next: return ProviderHtml.Skip
			except: self.logError()
		elif self.customVersion4():
			try:
				pages = str(self.extractHtml(data, [HtmlParagraph(index = -1), HtmlLink()]))
				if not pages or not Regex.match(data = pages, expression = Provider._ExpressionNext): return ProviderHtml.Skip
			except: self.logError()

	def processBefore(self, item):
		if self.customVersion2():
			category = self.extractHtml(item, [HtmlResult(index = 0, extract = Html.ParseTextNested)])
			if category:
				category = category.lower().strip()
				version = self.customVersion()
				categories = Provider._CategoryShow[version] if self.parameterMediaShow() else Provider._CategoryMovie[version]
				if not category in categories: return ProviderJson.Skip
			else: return ProviderJson.Skip
		elif self.customVersion3():
			expectedImdb = self.parameterIdImdb()
			if expectedImdb:
				try: currentImdb = item[Provider._AttributeImdb]
				except: currentImdb = None
				if currentImdb and not currentImdb == expectedImdb: return ProviderJson.Skip
		elif self.customVersion4():
			category = str(self.extractHtml(item, [HtmlDescriptionName(extract = Html.ParseTextUnnested)]))
			if category and not Regex.match(data = category, expression = Provider._ExpressionVideo): return ProviderHtml.Skip

	def processHash(self, value, item, details = None, entry = None):
		if self.customVersion3():
			# If no results are found, a single link with a 0s hash is returned. Skip it.
			if value  == '0000000000000000000000000000000000000000': return ProviderJson.Skip
		return value

	def processFileName(self, value, item, details = None, entry = None):
		if self.customVersion2():
			if value:
				# Remove prefix.
				#	Original Name: Luca 2021 2160p UHD BluRay x265-B0MBARDiERS
				value = Regex.remove(data = value, expression = r'(^\s*original\s*name\s*:*\s*)', all = True)

				# Remove suffix.
				#	Original Name: 【更多高清电影访问 】夏日友晴天[简繁字幕] Luca 2021 1080p BluRay x264 [email protected] COM 9.94GB (description)
				#	Luca 2021 Hybrid 1080p BluRay REMUX AVC Atmos-EPSiLON [1o80p ReMuX] (description)
				value = Regex.remove(data = value, expression = r'(\s*[\(\{\[](?:email\s*protect(?:ed)|description)[\)\}\]].*$)', all = True)
		return value

	def processSourceTimeInexact(self, value, item, details = None, entry = None):
		if self.customVersion2():
			if value:
				# 3 Hrs
				# 1 Day / 2 Days
				# 4 Wks
				# 1 Mon / 4 Mons
				# 2 Yrs
				value = value.lower()
				value = value.replace('mn', 'minute').replace('min', 'minute').replace('hr', 'hour').replace('wk', 'week').replace('mon', 'month').replace('yr', 'year')
		return value

	def processSourceApproval(self, value, item, details = None, entry = None):
		if self.customVersion3():
			if self.customVerified():
				if not value == Provider._AttributeVip and not value == Provider._AttributeTrusted: return ProviderJson.Skip
			if value == Provider._AttributeVip: return ProviderJson.ApprovalExcellent
			elif value == Provider._AttributeTrusted: return ProviderJson.ApprovalGood
			elif value == Provider._AttributeMember: return ProviderJson.ApprovalBad
			else: return ProviderJson.ApprovalDefault
		return value
