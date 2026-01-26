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
from lib.providers.core.html import ProviderHtml, Html, HtmlBody, HtmlResults, HtmlResult, HtmlTable, HtmlLink, HtmlDiv, HtmlSpan, HtmlButton, HtmlParagraph, HtmlDescriptionList, HtmlDescriptionName, HtmlDescriptionValue
from lib.modules.tools import Regex, Time

class Provider(ProviderJson, ProviderHtml):

	_Link					= {
								# Update (2024-12): .st domain is the only one still working.
								ProviderHtml.Version1 : ['https://extratorrent.st'],
								ProviderHtml.Version2 : ['https://extratorrent.si'],
								ProviderHtml.Version3 : ['https://extratorrents.it', 'https://extratorrent.ag'],
								ProviderHtml.Version4 : ['https://extratorrent.cyou'], # Must have the wwX subdomain, otherwise it will fail. But the subdomain always changes (ww5, ww7, etc). Retrieve the subdomain through the authentication process.
								ProviderHtml.Version5 : ['https://extratorrent.cyou'], # Does not require the wwX subdomain.
							}

	# Both down.
	#_Mirror				= ['https://www.elitetricks.net/extratorrent-proxy/', 'https://traqq.com/blog/2020-top-proxies-for-extratorrent-absolutely-working/']
	_Mirror					= None

	_Unblock				= {
								ProviderHtml.Version1 : None,
								ProviderHtml.Version2 : None,
								ProviderHtml.Version3 : {ProviderHtml.UnblockFormat1 : 'extratorrent2', ProviderHtml.UnblockFormat2 : 'extratorrent', ProviderHtml.UnblockFormat3 : 'extratorrent', ProviderHtml.UnblockFormat4 : 'extratorrent'},
								ProviderHtml.Version4 : None,
								ProviderHtml.Version5 : None,
							}

	_Path					= {
								ProviderHtml.Version1 : 'search/', # Must end with a slash.
								ProviderHtml.Version2 : 'search/', # Must end with a slash.
								ProviderHtml.Version3 : 'search/', # Must end with a slash.
								ProviderHtml.Version4 : 'find/%s/page/%s', # Just "find" can be used for the first page, but subsequent pages require the full path.
								ProviderHtml.Version5 : 'api.php?url=/q.php',
							}

	_CategoryMovie			= {
								ProviderHtml.Version1 : '1',
								ProviderHtml.Version2 : '4',
								ProviderHtml.Version3 : '4',
								ProviderHtml.Version4 : ['movies', 'anime'],
								ProviderHtml.Version5 : ['201', '202', '207', '209'], # 201 = Movies, 202 = Movies DVDR, 207 = HD Movies, 209 = 3D
							}
	_CategoryShow			= {
								ProviderHtml.Version1 : '2',
								ProviderHtml.Version2 : '8',
								ProviderHtml.Version3 : '8',
								ProviderHtml.Version4 : ['tv', 'anime'],
								ProviderHtml.Version5 : ['205', '208'], # 205 = TV Shows, 208 = HD TV Shows
							}

	_Query					= '%s?%s=%s%%26%s=%s' # URL-encode "&", since the URL is passed as a parameter, otherwise the category is ignored.

	_LimitOffset			= 100 # The maximum number of results returned by a query.

	_ParameterSearch		= 'search'
	_ParameterQuery1		= 'q'
	_ParameterQuery2		= 'f'
	_ParameterCategory1		= 'cat'
	_ParameterCategory2		= 's_cat'
	_ParameterPage1			= 'page'
	_ParameterPage2			= 'page'
	_ParameterSort1			= 'sorter'
	_ParameterSort2			= 'srt'
	_ParameterSeeds1		= 'seed'
	_ParameterSeeds2		= 'seeds'
	_ParameterOrder			= 'order'
	_ParameterDescending	= 'desc'
	_ParameterSafe			= 'safe'
	_ParameterYes			= '1'
	_ParameterNo			= '0'

	_AttributeContent		= 'results'
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
	_AttributeTable			= 'tl'
	_AttributeUploader1		= 'username'
	_AttributeUploader2		= 'usr'
	_AttributePage			= 'pager_link'
	_AttributeDisabled		= 'pager_no_link'

	_ExpressionVideo		= r'(video|anime)'
	_ExpressionMovie		= r'(movie)'
	_ExpressionShow			= r'(tv)'
	_ExpressionExclude		= r'(book|tutorial|adult|porn|software|picture|music|game)'

	_ExpressionNext1		= r'(next)'
	_ExpressionNext2		= r'(>|&gt;)'
	_ExpressionToday		= r'(today\-*(?:\d{4})?)'
	_ExpressionYesterday	= r'(y[\-\s]*day\-*(?:\d{4})?)'
	_ExpressionHash			= r'\/([a-z0-9]{32,})(?:[\/\?\&]|$)'
	_ExpressionVideo		= r'(video)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		version = self.customVersion()
		id = self.customSearchId()
		category = self.customCategory()

		name			= 'ExtraTorrent'
		description		= '{name} is one of the oldest and most well-known {container} sites. The site contains results in various languages, but most of them are in English. There are different versions of {name} with version %s having some missing metadata. {name} has strong Cloudflare protection that might not be bypassable and cause scraping to fail.'  % ProviderHtml.Version3
		rank			= 4
		performance		= ProviderHtml.PerformancePoor
		status			= ProviderHtml.StatusCloudflare # Update (2024-12): The only working .st domain has heavy Cloudflare protection.
		link			= Provider._Link[version]
		mirror			= Provider._Mirror
		unblock			= Provider._Unblock
		customVersion	= 5
		supportMovie	= True
		supportShow		= True
		supportPack		= True

		if version == ProviderHtml.Version4:
			ProviderHtml.initialize(self,
				name						= name,
				description					= description,
				rank						= rank,
				performance					= performance,

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
												ProviderHtml.RequestPath : Provider._Path[version] % (Provider.TermQuery, Provider.TermOffset),
												ProviderHtml.RequestData : {
													Provider._ParameterQuery1		: ProviderHtml.TermQuery,
													#Provider._ParameterCategory1	: ProviderHtml.TermCategory, # Do not search by category, since there is a "Packs" category that is not searchable through parameters. Filter out manually.
													Provider._ParameterPage1		: ProviderHtml.TermOffset,
													Provider._ParameterSort1		: Provider._ParameterSeeds1,
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
		elif version == ProviderHtml.Version5:
			ProviderJson.initialize(self,
				name					= name,
				description				= description,
				rank					= rank,
				performance				= performance,

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
											Provider._Query % (Provider._Path[version], Provider._ParameterQuery1, Provider.TermIdImdb if id else Provider.TermQuery, Provider._ParameterCategory1, ProviderJson.TermCategory),
											Provider._Query % (Provider._Path[version], Provider._ParameterQuery1, Provider.TermQuery, Provider._ParameterCategory1, ProviderJson.TermCategory),
										],

				searchCategoryMovie		= Provider._CategoryMovie[version] if category else ','.join(Provider._CategoryMovie[version]),
				searchCategoryShow		= Provider._CategoryShow[version] if category else ','.join(Provider._CategoryShow[version]),

				extractHash				= Provider._AttributeHash,
				extractReleaseUploader	= Provider._AttributeUploader1,
				extractFileName			= Provider._AttributeName,
				extractFileSize			= Provider._AttributeSize,
				extractSourceTime		= Provider._AttributeTime,
				extractSourceApproval	= Provider._AttributeStatus,
				extractSourceSeeds		= Provider._AttributeSeeds,
				extractSourceLeeches	= Provider._AttributeLeeches,
			)
		else:
			if version == ProviderHtml.Version1:
				extractFileName				= [HtmlResult(index = 1), HtmlLink()]
				extractFileSize				= [HtmlResult(index = 3)]
				extractReleaseUploader		= [HtmlResult(index = 1), HtmlDiv(class_ = Provider._AttributeUploader2)]
				extractSourceTime			= None
				extractSourceTimeInexact	= [HtmlResult(index = 2)]
				extractSourceSeeds			= [HtmlResult(index = 4)]
				extractSourceLeeches		= [HtmlResult(index = 5)]
			elif version == ProviderHtml.Version2:
				extractFileName				= [HtmlResult(index = 2), HtmlLink()]
				extractFileSize				= [HtmlResult(index = 4)]
				extractReleaseUploader		= [HtmlResult(index = 2), HtmlDiv(class_ = Provider._AttributeUploader2)]
				extractSourceTime			= [HtmlResult(index = 3)]
				extractSourceTimeInexact	= None
				extractSourceSeeds			= [HtmlResult(index = 6)]
				extractSourceLeeches		= [HtmlResult(index = 7)]
			elif version == ProviderHtml.Version3:
				extractFileName				= [HtmlResult(index = 2), HtmlLink()]
				extractFileSize				= [HtmlResult(index = 4)]
				extractReleaseUploader		= [HtmlResult(index = 2), HtmlDiv(class_ = Provider._AttributeUploader2)]
				extractSourceTime			= None
				extractSourceTimeInexact	= [HtmlResult(index = 3)] # Old torrents are inaccurate (eg: 3 years).
				extractSourceSeeds			= [HtmlResult(index = 6)]
				extractSourceLeeches		= [HtmlResult(index = 7)]

			ProviderHtml.initialize(self,
				name						= name,
				description					= description,
				rank						= rank,
				performance					= performance,
				status						= status,

				link						= link,
				mirror						= mirror,
				unblock						= unblock,

				customVersion				= customVersion,

				streamTime					= '%m-%d-%Y', # Has US date format (month first). Pass custom format in and do not use the built-in formats that place the day first.

				supportMovie				= supportMovie,
				supportShow					= supportShow,
				supportPack					= supportPack,

				offsetStart					= 1,
				offsetIncrease				= 1,

				formatEncode				= ProviderHtml.FormatEncodeQuote,

				searchQuery					= {
												ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
												ProviderHtml.RequestPath : Provider._Path[version],
												ProviderHtml.RequestData : {
													Provider._ParameterSearch		: ProviderHtml.TermQuery,
													Provider._ParameterCategory2	: ProviderHtml.TermCategory,
													Provider._ParameterPage2		: ProviderHtml.TermOffset,
													Provider._ParameterSort2		: Provider._ParameterSeeds2,
													Provider._ParameterOrder		: Provider._ParameterDescending,
												},
											},
				searchCategoryMovie			= Provider._CategoryMovie[version],
				searchCategoryShow			= Provider._CategoryShow[version],

				extractOptimizeData			= HtmlBody(), # To detect the last page in processOffset().
				extractList					= [HtmlResults(class_ = Provider._AttributeTable)],
				extractLink					= [HtmlResult(index = 0), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
				extractFileName				= extractFileName,
				extractFileSize				= extractFileSize,
				extractReleaseUploader		= extractReleaseUploader,
				extractSourceTime			= extractSourceTime,
				extractSourceTimeInexact	= extractSourceTimeInexact,
				extractSourceSeeds			= extractSourceSeeds,
				extractSourceLeeches		= extractSourceLeeches,
			)

	##############################################################################
	# PROCESS
	##############################################################################

	def processData(self, data):
		version = self.customVersion()
		if version == ProviderHtml.Version1:
			# There is somewhere a huge HTML syntax error in the code, preventing Beautifulsoup from extracting it in:
			#	extractList = [HtmlResults(class_ = Provider._AttributeTable)]
			# Even this does not work:
			#	extractParser = ProviderHtml.ParserHtml5
			# Use regex to extract and then parse.
			data = Regex.extract(data = str(data), expression = r'(<table\s*class="tl".*?<\/table>)', flags = Regex.FlagCaseInsensitive | Regex.FlagAllLines)
			if data: data = self.parseHtml(data = data)
		return data

	def processOffset(self, data, items):
		try:
			version = self.customVersion()
			if version == ProviderHtml.Version4:
				next = False
				buttons = self.extractHtml(data, [HtmlButton()])
				if buttons:
					for button in buttons:
						if Regex.match(data = button.text, expression = Provider._ExpressionNext1):
							next = True
							break
				if not next: return ProviderHtml.Skip
			elif version == ProviderHtml.Version2:
				last = self.extractHtml(data, [HtmlTable(), Html(class_ = Provider._AttributePage, index = -1, extract = Html.ParseText)])
				if last:
					last = int(last)
					next = self.extractHtml(data, [HtmlTable(), Html(class_ = Provider._AttributeDisabled, index = -1, extract = Html.ParseText)])
					if next:
						next = int(next)
						if next > last: return ProviderHtml.Skip
			elif version == ProviderHtml.Version1 or version == ProviderHtml.Version3:
				# Seems that subsequent pages contain the same results as page 1.
				last = self.extractHtml(data, [HtmlTable(), Html(class_ = Provider._AttributePage, index = -1, extract = Html.ParseText)])
				if last and not Regex.match(data = last, expression = Provider._ExpressionNext2):
					return ProviderHtml.Skip
		except: self.logError()

	def processBefore(self, item):
		version = self.customVersion()
		if version == ProviderHtml.Version4:
			category = self.extractHtml(item, [HtmlResult(index = 0, extract = Html.ParseTextNested)])
			if category:
				category = category.lower().strip()
				categories = Provider._CategoryShow[version] if self.parameterMediaShow() else Provider._CategoryMovie[version]
				if not category in categories: return ProviderJson.Skip
			else: return ProviderJson.Skip
		elif version == ProviderHtml.Version5:
			expectedImdb = self.parameterIdImdb()
			if expectedImdb:
				try: currentImdb = item[Provider._AttributeImdb]
				except: currentImdb = None
				if currentImdb and not currentImdb == expectedImdb: return ProviderJson.Skip
		elif version == ProviderHtml.Version1 or version == ProviderHtml.Version2 or version == ProviderHtml.Version3:
			# Seems that the category query parameter does not have an affect.
			# Filter the category manually.
			category = self.extractHtml(item, [HtmlResult(index = 1), HtmlLink(extract = Html.AttributeTitle)])
			if category:
				if version == ProviderHtml.Version2:
					target = Provider._ExpressionMovie if self.parameterMediaMovie() else Provider._ExpressionShow
					if not (Regex.match(data = category, expression = target) or Regex.match(data = category, expression = Provider._ExpressionVideo)):
						return ProviderHtml.Skip
				elif version == ProviderHtml.Version1 or version == ProviderHtml.Version3:
					# There can be too many subcategories to check. Rather just check some exclude categories.
					# https://extratorrents.it/category/4/Movies+Torrents.html
					if Regex.match(data = category, expression = Provider._ExpressionExclude):
						return ProviderHtml.Skip

	def processHash(self, value, item, details = None, entry = None):
		if self.customVersion5():
			# If no results are found, a single link with a 0s hash is returned. Skip it.
			if value  == '0000000000000000000000000000000000000000': return ProviderJson.Skip
		return value

	def processFileName(self, value, item, details = None, entry = None):
		if self.customVersion4():
			if value:
				# Remove prefix.
				#	Original Name: Luca 2021 2160p UHD BluRay x265-B0MBARDiERS
				value = Regex.remove(data = value, expression = r'(^\s*original\s*name\s*:*\s*)', all = True)

				# Remove suffix.
				#	Original Name: 【更多高清电影访问 】夏日友晴天[简繁字幕] Luca 2021 1080p BluRay x264 [email protected] COM 9.94GB (description)
				#	Luca 2021 Hybrid 1080p BluRay REMUX AVC Atmos-EPSiLON [1o80p ReMuX] (description)
				value = Regex.remove(data = value, expression = r'(\s*[\(\{\[](?:email\s*protect(?:ed)|description)[\)\}\]].*$)', all = True)
		return value

	def processSourceTime(self, value, item, details = None, entry = None):
		version = self.customVersion()
		if version == ProviderHtml.Version2:
			# Y-day-2021
			# Today-13:10
			# 03-29-2019
			if Regex.match(data = value, expression = Provider._ExpressionToday):
				value = Regex.replace(data = value, expression = Provider._ExpressionToday, replacement = Time.format(format = Time.FormatDate) + ' ', all = True)
			elif Regex.match(data = value, expression = Provider._ExpressionYesterday):
				value = Regex.replace(data = value, expression = Provider._ExpressionYesterday, replacement = Time.past(days = 1, format = Time.FormatDate) + ' ', all = True)
		return value

	def processSourceTimeInexact(self, value, item, details = None, entry = None):
		if self.customVersion4():
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
		if self.customVersion5():
			if self.customVerified():
				if not value == Provider._AttributeVip and not value == Provider._AttributeTrusted: return ProviderJson.Skip
			if value == Provider._AttributeVip: return ProviderJson.ApprovalExcellent
			elif value == Provider._AttributeTrusted: return ProviderJson.ApprovalGood
			elif value == Provider._AttributeMember: return ProviderJson.ApprovalBad
			else: return ProviderJson.ApprovalDefault
		return value
