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
from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlLink, HtmlDiv, HtmlButton
from lib.modules.tools import Regex

# 3 search modes:
#	1. Exact Search: HTML searches the local Torrentz database.
#	2. Full Search: API searches. Seems to just be a wrapper on ApiBay (URL, parameters and returned data is at least the same).
#	3. Multi Search: Returns too many incorrect results, especially when sorted.

class Provider(ProviderJson, ProviderHtml):

	_Link					= {
								ProviderHtml.Version1 : ['https://torrentz2k.xyz'], # Must have the wwX subdomain, otherwise it will fail. But the subdomain always changes (ww5, ww7, etc). Retrieve the subdomain through the authentication process.
								ProviderHtml.Version2 : ['https://torrentz2k.xyz'], # Does not require the wwX subdomain.
							}

	_Path					= {
								ProviderHtml.Version1 : 'find/%s/page/%s', # Just "find" can be used for the first page, but subsequent pages require the full path.
								ProviderHtml.Version2 : 'api.php?url=/q.php',
							}

	_CategoryMovie			= {
								ProviderHtml.Version1 : ['movies', 'anime'],
								ProviderHtml.Version2 : ['201', '202', '207', '209'], # 201 = Movies, 202 = Movies DVDR, 207 = HD Movies, 209 = 3D
							}
	_CategoryShow			= {
								ProviderHtml.Version1 : ['tv', 'anime'],
								ProviderHtml.Version2 : ['205', '208'], # 205 = TV Shows, 208 = HD TV Shows
							}

	_Query					= '%s?%s=%s%%26%s=%s' # URL-encode "&", since the URL is passed as a parameter, otherwise the category is ignored.

	_LimitOffset			= 100 # The maximum number of results returned by a query.

	_ParameterQuery			= 'q'
	_ParameterCategory		= 'cat'
	_ParameterSort			= 'sorter'
	_ParameterPage			= 'page'
	_ParameterSeeds			= 'seed'

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

	_ExpressionNext			= '(next)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		version = self.customVersion()
		id = self.customSearchId()
		category = self.customCategory()

		name			= 'Torrentz2K'
		description		= '{name} is one of newer {container} site similar to Torrentz. The site contains results in various languages, but most of them are in English. {name} changes their domain often and has missing metadata. Version %s uses the new website structure. Version %s uses an API which does not have its own data, but instead retrieves data from ApiBay.' % (ProviderHtml.Version1, ProviderHtml.Version2)
		rank			= 2
		performance		= ProviderHtml.PerformanceMedium - ProviderHtml.PerformanceStep
		status			= ProviderHtml.StatusDead # Now redirects to torrentify.buzz, which has a different structure. Update (2024-12): Still down.
		link			= Provider._Link[version]
		customVersion	= 2
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
														ProviderHtml.RequestHeaderLocation : 'https?://(w+\d*)\..*',
													},
												},
											},

				offsetStart					= 1,
				offsetIncrease				= 1,

				searchQuery					= {
												ProviderHtml.RequestMethod : ProviderHtml.RequestMethodPost,
												ProviderHtml.RequestSubdomain : ProviderHtml.TermAuthentication,
												ProviderHtml.RequestPath : Provider._Path[version] % (Provider.TermQuery, Provider.TermOffset),
												ProviderHtml.RequestData : {
													Provider._ParameterQuery		: ProviderHtml.TermQuery,
													#Provider._ParameterCategory	: ProviderHtml.TermCategory, # Do not search by category, since there is a "Packs" category that is not searchable through parameters. Filter out manually.
													Provider._ParameterPage		: ProviderHtml.TermOffset,
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
		elif version == ProviderHtml.Version2:
			ProviderJson.initialize(self,
				name					= name,
				description				= description,
				rank					= rank,
				performance				= performance,
				status					= status,

				link					= link,

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
				#								Provider._ParameterCategory	: ProviderJson.TermCategory,
				#							},
				#						},
				searchQuery				= [
											Provider._Query % (Provider._Path[version], Provider._ParameterQuery, Provider.TermIdImdb if id else Provider.TermQuery, Provider._ParameterCategory, ProviderJson.TermCategory),
											Provider._Query % (Provider._Path[version], Provider._ParameterQuery, Provider.TermQuery, Provider._ParameterCategory, ProviderJson.TermCategory),
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

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		if self.customVersion1():
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

	def processBefore(self, item):
		if self.customVersion1():
			category = self.extractHtml(item, [HtmlResult(index = 0, extract = Html.ParseTextNested)])
			if category:
				category = category.lower().strip()
				version = self.customVersion()
				categories = Provider._CategoryShow[version] if self.parameterMediaShow() else Provider._CategoryMovie[version]
				if not category in categories: return ProviderJson.Skip
			else: return ProviderJson.Skip
		elif self.customVersion2():
			expectedImdb = self.parameterIdImdb()
			if expectedImdb:
				try: currentImdb = item[Provider._AttributeImdb]
				except: currentImdb = None
				if currentImdb and not currentImdb == expectedImdb: return ProviderJson.Skip

	def processHash(self, value, item, details = None, entry = None):
		if self.customVersion2():
			# If no results are found, a single link with a 0s hash is returned. Skip it.
			if value  == '0000000000000000000000000000000000000000': return ProviderJson.Skip
		return value

	def processFileName(self, value, item, details = None, entry = None):
		if self.customVersion1():
			if value:
				# Remove prefix.
				#	Original Name: Luca 2021 2160p UHD BluRay x265-B0MBARDiERS
				value = Regex.remove(data = value, expression = '(^\s*original\s*name\s*:*\s*)', all = True)

				# Remove suffix.
				#	Original Name: 【更多高清电影访问 】夏日友晴天[简繁字幕] Luca 2021 1080p BluRay x264 [email protected] COM 9.94GB (description)
				#	Luca 2021 Hybrid 1080p BluRay REMUX AVC Atmos-EPSiLON [1o80p ReMuX] (description)
				value = Regex.remove(data = value, expression = '(\s*[\(\{\[](?:email\s*protect(?:ed)|description)[\)\}\]].*$)', all = True)
		return value

	def processSourceTimeInexact(self, value, item, details = None, entry = None):
		if self.customVersion1():
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
		if self.customVersion2():
			if self.customVerified():
				if not value == Provider._AttributeVip and not value == Provider._AttributeTrusted: return ProviderJson.Skip
			if value == Provider._AttributeVip: return ProviderJson.ApprovalExcellent
			elif value == Provider._AttributeTrusted: return ProviderJson.ApprovalGood
			elif value == Provider._AttributeMember: return ProviderJson.ApprovalBad
			else: return ProviderJson.ApprovalDefault
		return value
