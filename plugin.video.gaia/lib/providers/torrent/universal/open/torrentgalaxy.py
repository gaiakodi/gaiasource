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
from lib.providers.core.html import ProviderHtml, Html, HtmlResultsDiv, HtmlResultDiv, HtmlLink, HtmlDiv, HtmlFont, HtmlBold, HtmlListUnordered, HtmlListItem
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	_Link					= {
								ProviderHtml.Version1 : ['https://torrentgalaxy.one', 'https://torrentgalaxy.info'],
								ProviderHtml.Version2 : ['https://torrentgalaxy.to', 'https://torrentgalaxy.mx', 'https://torrentgalaxy.su'],
							}
	_Mirror					= ['https://proxygalaxy.pw', 'https://proxygalaxy.me', 'https://www.techworm.net/2024/03/torrentgalaxy-proxy-list-mirrors.html']
	_Unblock				= {ProviderHtml.UnblockFormat1 : 'torrentgalaxy', ProviderHtml.UnblockFormat2 : 'torrentgalaxy', ProviderHtml.UnblockFormat3 : 'torrentgalaxy', ProviderHtml.UnblockFormat4 : 'torrentgalaxy'}
	_Path					= {
								ProviderHtml.Version1 : 'get-posts/keywords:%s%s%s',
								ProviderHtml.Version2 : 'torrents.php',
							}


	_LimitApproval			= 1000

	# Subcategories
	#_CategoryMovie			= ['c1', 'c3', 'c4', 'c42', 'c45', 'c46'] # c1 = Movies SD, c3 = Movies 4K, c4 = Movies Packs, c42 = Movies HD, c45 = Movies CAM/TS, c46 = Movies Bollywood
	#_CategoryShow			= ['c5', 'c6', 'c41'] # c5 = Shows SD, c6 = Shows Packs, c41 = Shows HD
	_CategoryMovie			= {
								ProviderHtml.Version1 : ':category:Movies:category:Anime',
								ProviderHtml.Version2 : 'Movies',
							}
	_CategoryShow			= {
								ProviderHtml.Version1 : ':category:TV:category:Anime',
								ProviderHtml.Version2 : 'TV',
							}

	_ParameterQuery			= 'search'
	_ParameterCategory		= 'parent_cat'
	_ParameterPage			= 'page'
	_ParameterSort			= 'sort'
	_ParameterSeeds			= 'seeders'
	_ParameterOrder			= 'order'
	_ParameterDescending	= 'desc'
	_ParameterPorn			= 'nox'
	_ParameterAdult			= ':ncategory:XXX'

	_AttributeMain			= 'main'
	_AttributeTable			= 'tgxtable'
	_AttributeLink			= 'txlight'
	_AttributePages			= 'pager'
	_AttributePage			= 'page-item'
	_AttributeDetails		= 'gluewrapper'
	_AttributeDetail		= 'torrentpagetable'

	_ExpressionHash			= '(?:info\s*)?hash\s*\:\s*' + ProviderHtml.ExpressionSha
	_ExpressionTime			= '(?:added|date)\s*\:\s*(.*?)\.\s'
	_ExpressionActive		= '(active)'
	_ExpressionDisabled		= '(disabled)'
	_ExpressionVerified		= '(verified\s*by)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		version = self.customVersion()

		name			= 'TorrentGalaxy'
		description		= '{name} is a well-known {container} site. The site contains results in various languages, but most of them are in English. {name} has many high-quality results with good metadata.'
		customVersion	= 2

		if version == ProviderHtml.Version1:
			ProviderHtml.initialize(self,
				name						= name,
				description					= description,
				rank						= 3,
				performance					= ProviderHtml.PerformanceBad,

				link						= Provider._Link[version],
				mirror						= Provider._Mirror,
				unblock						= Provider._Unblock,

				customVersion				= customVersion,
				customAdult					= True,

				supportMovie				= True,
				supportShow					= True,
				supportPack					= True,

				offsetStart					= 1,
				offsetIncrease				= 1,

				formatEncode				= ProviderHtml.FormatEncodeQuote,

				searchQuery					= {
												ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
												ProviderHtml.RequestPath : Provider._Path[version] % (ProviderHtml.TermQuery, ProviderHtml.TermCategory, Provider._ParameterAdult if self.customAdult() else ''),
												ProviderHtml.RequestData : {
													Provider._ParameterPage		: ProviderHtml.TermOffset,
													Provider._ParameterSort		: Provider._ParameterSeeds,
													Provider._ParameterOrder	: Provider._ParameterDescending,
												},
											},
				searchCategoryMovie			= Provider._CategoryMovie[version],
				searchCategoryShow			= Provider._CategoryShow[version],

				extractOptimizeData			= HtmlDiv(id_ = Provider._AttributeMain), # To detect the last page in processOffset().
				extractOptimizeDetails		= HtmlDiv(class_ = Provider._AttributeDetails),
				extractList					= [HtmlResultsDiv(class_ = Provider._AttributeTable, start = 1)],
				extractDetails				= [HtmlResultDiv(index = 3), HtmlLink(class_ = Provider._AttributeLink, extract = Html.AttributeHref)],
				extractLink					= [ProviderHtml.Details, HtmlDiv(class_ = Provider._AttributeDetail, index = 0), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
				extractHash					= [ProviderHtml.Details, HtmlDiv(class_ = Provider._AttributeDetail, index = 1), Html(extract = [Html.ParseTextNested, Provider._ExpressionHash])], # In case the magnet link is later removed.
				extractFileName				= [HtmlResultDiv(index = 3), HtmlLink(class_ = Provider._AttributeLink, extract = Html.AttributeTitle)],
				extractFileSize				= [HtmlResultDiv(index = 7)],
				extractReleaseUploader		= [HtmlResultDiv(index = 6)],

				# More accurate on the details page.
				# These dates are mostly not correct, and are probably when the site indexed the torrent, instead of the torrent age.
				# Update: Do not use the date on the details page, since there are too many inconsistencies with the formatting.
				#	1. Longer month names are abbriviated (eg: Jan.). Shorter ones are given in full length (eg: June).
				#	2. Sometimes no time is given, just a string (eg: "midnight").
				#	3. Sometimes the time is given in full (eg: 8:15 p.m.) and sometimes in short (eg: 8 p.m.)
				#extractSourceTimeInexact	= [ProviderHtml.Details, HtmlDiv(class_ = Provider._AttributeDetail, index = 1), Html(extract = [Html.ParseTextNested, Provider._ExpressionTime])],
				extractSourceTimeInexact	= [HtmlResultDiv(index = 11, extract = Html.ParseTextUnnested)],

				extractSourceSeeds			= [HtmlResultDiv(index = 10), HtmlBold(index = 0)],
				extractSourceLeeches		= [HtmlResultDiv(index = 10), HtmlBold(index = 1)],
				extractSourceApproval		= [HtmlResultDiv(index = 9)],
			)
		elif version == ProviderHtml.Version2:
			ProviderHtml.initialize(self,
				name						= name,
				description					= description,
				rank						= 5,
				performance					= ProviderHtml.PerformanceGood,

				link						= Provider._Link[version],
				mirror						= Provider._Mirror,
				unblock						= Provider._Unblock,

				customVersion				= customVersion,
				customVerified				= True,

				supportMovie				= True,
				supportShow					= True,
				supportPack					= True,

				offsetStart					= 0,
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
													Provider._ParameterOrder	: Provider._ParameterDescending,
													Provider._ParameterPorn		: 1,
												},
											},
				searchCategoryMovie			= Provider._CategoryMovie[version],
				searchCategoryShow			= Provider._CategoryShow[version],

				extractOptimizeData			= HtmlDiv(id_ = Provider._AttributeMain), # To detect the last page in processOffset().
				extractList					= [HtmlResultsDiv(class_ = Provider._AttributeTable, start = 1)],
				extractLink					= [HtmlResultDiv(index = 4), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
				extractFileName				= [HtmlResultDiv(index = 3), HtmlLink(extract = Html.AttributeTitle)], # File name from inner text can be cut off (...).
				extractFileSize				= [HtmlResultDiv(index = 7)],
				extractReleaseUploader		= [HtmlResultDiv(index = 6)],
				extractSourceTime			= [HtmlResultDiv(index = 11)],
				extractSourceSeeds			= [HtmlResultDiv(index = 10), HtmlFont(index = 0)],
				extractSourceLeeches		= [HtmlResultDiv(index = 10), HtmlFont(index = 1)],
				extractSourceApproval		= [HtmlResultDiv(index = 9)],
			)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			next = str(self.extractHtml(data, [HtmlListUnordered(id_ = Provider._AttributePages), HtmlListItem(class_ = Provider._AttributePage, index = -1, extract = Html.AttributeClass)]))
			if self.customVersion1():
				# All pages are marked as disabled all the time. If the last item is "active", then we are on the last page.
				if Regex.match(data = next, expression = Provider._ExpressionActive): return ProviderHtml.Skip
			else:
				if Regex.match(data = next, expression = Provider._ExpressionDisabled): return ProviderHtml.Skip
		except: self.logError()

	def processBefore(self, item):
		if self.customVersion2():
			if self.customVerified():
				try:
					verified = self.extractHtml(item, [HtmlResultDiv(index = 1, extract = Provider._ExpressionVerified)])
					if not verified: return ProviderHtml.Skip
				except: self.logError()

	def processSourceApproval(self, value, item, details = None, entry = None):
		result = ProviderHtml.ApprovalDefault
		try:
			value = float(value.replace(',', ''))
			result += ((1 - result) * (value / Provider._LimitApproval))
		except: pass
		return result
