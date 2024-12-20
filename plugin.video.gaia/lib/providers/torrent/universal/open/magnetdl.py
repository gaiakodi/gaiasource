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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlLink
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	# The .com domain is old version 2, while .co is the new version 1.
	# The new version is basically a bad rip-off from TorrentQuest.
	_Link			= {
						ProviderHtml.Version1 : 'https://magnetdl.co',
						ProviderHtml.Version2 : 'https://magnetdl.com',
					}

	_Path			= {
						ProviderHtml.Version1 : 'search',
						ProviderHtml.Version2 : '%s/%s/se/desc/%s/',
					}

	_CategoryMovie	= {
						ProviderHtml.Version1 : ['movies', 'video', '3d'],
						ProviderHtml.Version2 : ['movie'],
					}
	_CategoryShow	= {
						ProviderHtml.Version1 : ['tv', 'video'],
						ProviderHtml.Version2 : ['tv'],
					}

	_ParameterQuery	= 'q'
	_ParameterPage	= 'page'
	_ParameterSort	= 'order'
	_ParameterSeeds	= 'seeders'
	_ParameterOrder	= 'orderby'
	_ParameterAsc	= 'ASC'

	_AttributeTable	= 'download'
	_AttributeNext	= 'next'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		name		= 'MagnetDL'
		description	= '{name} has a very large and reliable database of {containers}. The site contains results in various languages, but most of them are in Russian or English. {name} can only search with the Latin alphabet. Titles that purely consist of numbers, symbols, or other alphabets will not be found. {name} has strong Cloudflare protection that might not be bypassable and cause scraping to fail.'
		rank		= 4
		performance	= ProviderHtml.PerformanceGood - ProviderHtml.PerformanceStep
		status		= ProviderHtml.StatusImpaired

		version = self.customVersion()
		if version == ProviderHtml.Version1:
			ProviderHtml.initialize(self,
				name						= name,
				description					= description,
				rank						= rank,
				performance					= performance,
				status						= status,

				link						= Provider._Link[version],
				unblock						= {ProviderHtml.UnblockFormat1 : 'magnetdl', ProviderHtml.UnblockFormat2 : 'magnetdl', ProviderHtml.UnblockFormat4 : 'magnetdl'},

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
													Provider._ParameterPage		: ProviderHtml.TermOffset,
													Provider._ParameterSort		: Provider._ParameterSeeds,
													Provider._ParameterOrder	: Provider._ParameterAsc,
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
		elif version == ProviderHtml.Version2:
			ProviderHtml.initialize(self,
				name						= name,
				description					= description,
				rank						= rank,
				performance					= performance,
				status						= status,

				link						= Provider._Link[version],
				unblock						= {ProviderHtml.UnblockFormat1 : 'magnetdl', ProviderHtml.UnblockFormat2 : 'magnetdl', ProviderHtml.UnblockFormat4 : 'magnetdl'},

				supportMovie				= True,
				supportShow					= True,
				supportPack					= True,

				offsetStart					= 1,
				offsetIncrease				= 1,

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
		if self.customVersion2():
			if not Regex.match(data = str(items[-1]), expression = Provider._AttributeNext): return ProviderHtml.Skip

	def processItem(self, item):
		category = Provider._CategoryShow if self.parameterMediaShow() else Provider._CategoryMovie
		category = category[self.customVersion()]
		type = self.extractHtml(item, HtmlResult(index = 3, extract = Html.ParseText))
		if not type or not type.lower() in category: return ProviderHtml.Skip
		return item
