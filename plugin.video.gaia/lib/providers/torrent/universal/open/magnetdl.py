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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlDiv, HtmlLink, HtmlTableRow
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	# The .com domain is old version 2, while .co is the new version 1.
	# The new version is basically a bad rip-off from TorrentQuest.
	# The .co domain changed again using a details page, which is now the new version 1.
	_Link					= {
								ProviderHtml.Version1 : 'https://magnetdl.co',
								ProviderHtml.Version2 : 'https://magnetdl.co',
								ProviderHtml.Version3 : 'https://magnetdl.com',
							}

	_Path					= {
								ProviderHtml.Version1 : 'data.php',
								ProviderHtml.Version2 : 'search',
								ProviderHtml.Version3 : '%s/%s/se/desc/%s/',
							}

	_CategoryMovie			= {
								ProviderHtml.Version1 : ['movies', 'video', '3d', 'other'],
								ProviderHtml.Version2 : ['movies', 'video', '3d'],
								ProviderHtml.Version3 : ['movie'],
							}
	_CategoryShow			= {
								ProviderHtml.Version1 : ['tv', 'movies', 'video', '3d', 'other'], # Many of the shows are listed under "movies".
								ProviderHtml.Version2 : ['tv', 'video'],
								ProviderHtml.Version3 : ['tv'],
							}

	_ParameterQuery			= 'q'
	_ParameterPage			= 'page'
	_ParameterSort			= 'order'
	_ParameterSeeds			= 'seeders'
	_ParameterOrder			= 'orderby'
	_ParameterDescending	= 'DESC'

	_AttributeTable			= 'download'
	_AttributeNext			= 'next'
	_AttributeContent		= 'content'
	_AttributeHeader		= 'header-content'
	_AttributeFill			= 'fill-content'

	_ExpressionHash			= 'hash\s*:\s*' + ProviderHtml.ExpressionSha
	_ExpressionTime			= 'uploaded\s*:\s*([\d\-\:\.\s]+)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		version			= self.customVersion()

		name			= 'MagnetDL'
		description		= '{name} has a very large and reliable database of {containers}. The site contains results in various languages, but most of them are in Russian or English. {name} can only search with the Latin alphabet. Titles that purely consist of numbers, symbols, or other alphabets will not be found. {name} has strong Cloudflare protection that might not be bypassable and cause scraping to fail.'

		# New details page for version 3 reduces rating and performance.
		#rank			= 4
		#performance	= ProviderHtml.PerformanceGood - ProviderHtml.PerformanceStep
		#status			= ProviderHtml.StatusCloudflare
		rank			= 3
		performance		= ProviderHtml.PerformanceBad

		# Update (2025-12): Seems to not be blocked by Cloudflare anymore.
		#status			= ProviderHtml.StatusCloudflare
		status			= ProviderHtml.StatusOperational

		link			= Provider._Link[version]
		unblock			= {ProviderHtml.UnblockFormat1 : 'magnetdl', ProviderHtml.UnblockFormat2 : 'magnetdl', ProviderHtml.UnblockFormat4 : 'magnetdl'}

		customVersion	= 3

		supportMovie	= True
		supportShow		= True
		supportPack		= True

		offsetStart		= 1
		offsetIncrease	= 1

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

				offsetStart					= offsetStart,
				offsetIncrease				= offsetIncrease,

				formatEncode				= ProviderHtml.FormatEncodeQuote,

				searchQuery					= {
												ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
												ProviderHtml.RequestPath : Provider._Path[version],
												ProviderHtml.RequestData : {
													Provider._ParameterQuery	: ProviderHtml.TermQuery,
													Provider._ParameterPage		: ProviderHtml.TermOffset,
													Provider._ParameterSort		: Provider._ParameterSeeds,
													Provider._ParameterOrder	: Provider._ParameterDescending,
												},
											},

				extractOptimizeDetails		= HtmlDiv(id_ = Provider._AttributeContent),
				extractDetails				= [HtmlResult(index = 0), HtmlLink(extract = Html.AttributeHref)],
				extractList					= [HtmlTableRow()],
				extractHash					= [ProviderHtml.Details, Html(class_ = Provider._AttributeFill, extract = Html.ParseTextNested)],
				extractFileName				= [ProviderHtml.Details, Html(class_ = Provider._AttributeHeader, extract = Html.ParseTextNested)], # File name on the main page can be cut off (..).
				#extractReleaseUploader		= [ProviderHtml.Details, Html(class_ = Provider._AttributeFill, extract = Html.ParseTextNested)], # Do not ewxtract the uploader, since they are all "eztv". If this is ever enabled again, add a custom processReleaseUploader() below.
				extractFileSize				= [HtmlResult(index = 4)],
				extractSourceTimeInexact	= [ProviderHtml.Details, Html(class_ = Provider._AttributeFill, extract = Html.ParseTextNested)], # These do not seem to be the actual torrent date, but rather the scraping date. Eg Avatar has most links within the past 2 years.
				extractSourceSeeds			= [HtmlResult(index = 5)],
				extractSourceLeeches		= [HtmlResult(index = 6)],
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

				offsetStart					= offsetStart,
				offsetIncrease				= offsetIncrease,

				formatEncode				= ProviderHtml.FormatEncodePlus,

				searchQuery					= {
												ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
												ProviderHtml.RequestPath : Provider._Path[version],
												ProviderHtml.RequestData : {
													Provider._ParameterQuery	: ProviderHtml.TermQuery,
													Provider._ParameterPage		: ProviderHtml.TermOffset,
													Provider._ParameterSort		: Provider._ParameterSeeds,
													Provider._ParameterOrder	: Provider._ParameterDescending,
												},
											},

				extractList					= [HtmlResults(class_ = Provider._AttributeTable)],
				extractLink					= [HtmlResult(index = 0), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
				extractFileName				= [HtmlResult(index = 1), HtmlLink(extract = Html.AttributeTitle)], # File name from inner text can be cut off (..).
				extractFileSize				= [HtmlResult(index = 4)],
				extractSourceTimeInexact	= [HtmlResult(index = 2)],
				extractSourceSeeds			= [HtmlResult(index = 5)],
				extractSourceLeeches		= [HtmlResult(index = 6)],
			)
		elif version == ProviderHtml.Version3:
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

				offsetStart					= offsetStart,
				offsetIncrease				= offsetIncrease,

				formatEncode				= ProviderHtml.FormatEncodeMinus,
				formatCase					= ProviderHtml.FormatCaseLower,
				formatInclude				= ProviderHtml.FormatIncludeEncode,

				searchQuery					= Provider._Path[version] % (ProviderHtml.TermLetter, ProviderHtml.TermQuery, ProviderHtml.TermOffset),

				extractList					= [HtmlResults(class_ = Provider._AttributeTable, skip = 1)],
				extractLink					= [HtmlResult(index = 0), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
				extractFileName				= [HtmlResult(index = 1), HtmlLink(extract = Html.AttributeTitle)], # File name from inner text can be cut off (..).
				extractFileSize				= [HtmlResult(index = 5)],
				extractSourceTimeInexact	= [HtmlResult(index = 2)],
				extractSourceSeeds			= [HtmlResult(index = 6)],
				extractSourceLeeches		= [HtmlResult(index = 7)],
			)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		if self.customVersion3():
			if not Regex.match(data = str(items[-1]), expression = Provider._AttributeNext): return ProviderHtml.Skip

	def processBefore(self, item):
		try:
			if self.customVersion1():
				# Validate to only retrieve sub-pages that are valid.
				# The file name on the main page can be cut off (...), therefore extract the full name from the details page.
				name = self.extractHtml(item, [HtmlResult(index = 1, extract = Html.ParseTextNested)])
				if not name or not self.searchValid(data = name, validateShow = False): return ProviderHtml.Skip
		except: self.logError()

	def processItem(self, item):
		category = Provider._CategoryShow if self.parameterMediaShow() else Provider._CategoryMovie
		category = category[self.customVersion()]
		type = self.extractHtml(item, HtmlResult(index = 3, extract = Html.ParseText))
		if not type or not type.lower() in category: return ProviderHtml.Skip
		return item

	def processHash(self, value, item, details = None, entry = None):
		if self.customVersion1():
			if value: return Regex.extract(data = value, expression = Provider._ExpressionHash)
		return value if value else None

	def processSourceTimeInexact(self, value, item, details = None, entry = None):
		if self.customVersion1():
			if value: return Regex.extract(data = value, expression = Provider._ExpressionTime)
		return value
