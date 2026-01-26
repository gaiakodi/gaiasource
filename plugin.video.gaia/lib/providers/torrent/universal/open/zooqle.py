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

from lib.providers.core.html import ProviderHtml, Html, HtmlBody, HtmlResults, HtmlResultsDiv, HtmlResult, HtmlResultDiv, HtmlLink, HtmlDiv, HtmlSpan, HtmlTable
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	_Link				= {
							ProviderHtml.Version1 : ['https://zooqle.io', 'https://zooqle.pro', 'https://zooqlemovies.com'], # https://zooqle.movie has a different layout.
							ProviderHtml.Version2 : 'https://zooqle.com',
						}

	_Path				= {
							ProviderHtml.Version1 : None,
							ProviderHtml.Version2 : 'search?q=%s+category%%3A%s&pg=%s&v=t&s=ns&sd=d', # s=ns: sort by seeds, sd=d: sort descending.
						}

	_Mirror				= ['https://zoogleproxy.com', 'https://torrends.to/proxy/zooqle']
	_Unblock			= {ProviderHtml.UnblockFormat1 : 'zooqle', ProviderHtml.UnblockFormat2 : 'zooqle', ProviderHtml.UnblockFormat3 : 'zooqle2', ProviderHtml.UnblockFormat4 : 'zooqle'}

	_CategoryMovie		= 'Movies'
	_CategoryShow		= 'TV'
	_CategoryAnime		= 'Anime'

	_ParameterQuery		= 'keyword'

	_AttributeMain		= 'zq-small'
	_AttributeTable		= 'table-torrents'
	_AttributeLong		= 'long'
	_AttributePages		= 'pagination'
	_AttributeContent	= 'tvHot'
	_AttributeRow		= 'row'
	_AttributeCell		= 'cell'
	_AttributeDetails	= 'table-torrents'

	_ExpressionSeeds	= r'seed.*?([\d,]+)'
	_ExpressionLeeches	= r'leech.*?([\d,]+)'
	_ExpressionStandard	= r'(std)'
	_ExpressionAudio	= r'(audio)'
	_ExpressionLanguage	= r'(language)'
	_ExpressionNext		= r'(next)'
	_ExpressionMute		= r'(mute)'
	_ExpressionExclude	= r'(med|low)'
	_ExpressionChannels	= r'(?:(?:audio.?)(?:format|channels?))'
	_ExpressionLanguages= r'(?:(?:detected.?)languages?)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		version = self.customVersion()

		name			= 'Zooqle'
		description		= '{name} has a very large database of {containers} and metadata. The site contains results in various languages, but most of them are in Russian or English. Version %s only contains movies, but no shows, and has a small database with missing metadata.' % ProviderHtml.Version1
		#rank			= 5
		rank			= 2 # Only returns movies for v1, and only very few links.
		performance		= ProviderHtml.PerformanceGood

		# Update (2022-06): Website hass been down. From Reddit is seems to be down from April 2022.
		# Update (2024-12): Still down.
		# Update (2025-06): Still down - Cloudflare 520 error.
		# Only the old .com domain is down.
		#status			= ProviderHtml.StatusDead
		status			= ProviderHtml.StatusOperational

		if version == ProviderHtml.Version1:
			ProviderHtml.initialize(self,
				name						= name,
				description					= description,
				rank						= rank,
				performance					= performance,
				status						= status,

				link						= Provider._Link[version],
				mirror						= Provider._Mirror,
				unblock						= Provider._Unblock,

				# Only supports movies.
				supportMovie				= True,
				supportShow					= False,
				supportPack					= False,

				searchQuery					= {
												ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
												ProviderHtml.RequestData : {
													Provider._ParameterQuery	: ProviderHtml.TermIdImdb, # Can search my IMDb ID.
												},
											},

				extractOptimizeData			= HtmlDiv(id_ = Provider._AttributeContent),
				extractOptimizeDetails		= HtmlBody(),
				extractOptimizeEntries		= False,
				extractList					= [HtmlResultsDiv(class_ = Provider._AttributeRow)],
				extractDetails				= [HtmlResultDiv(), HtmlLink(extract = Html.AttributeHref)],
				extractEntries				= [ProviderHtml.Details, HtmlResults(class_ = Provider._AttributeDetails)],
				extractHash					= [ProviderHtml.Entries, HtmlResult(index = 1), HtmlLink(extract = ProviderHtml.ExpressionSha)],
				extractFileNameInexact		= [ProviderHtml.Entries, HtmlResult(index = 1), HtmlLink(extract = Html.ParseTextNested)],
				extractFileSize				= [ProviderHtml.Entries, HtmlResult(index = 2, extract = Html.ParseTextNested)],
				extractAudioChannels		= [ProviderHtml.Entries, HtmlResult(index = 1), HtmlSpan(title_ = Provider._ExpressionChannels, extract = Html.ParseTextNested)],
				extractAudioLanguage		= [ProviderHtml.Entries, HtmlResult(index = 1), HtmlSpan(title_ = Provider._ExpressionLanguages, extract = Html.ParseTextNested)],
				extractSourceTimeInexact	= [ProviderHtml.Entries, HtmlResult(index = 3, extract = Html.ParseTextNested)],
				extractSourceSeedsInexact	= [ProviderHtml.Entries, HtmlResult(index = 4), HtmlDiv(), HtmlDiv(index = 0, extract = Html.ParseTextNested)],
				extractSourceLeechesInexact	= [ProviderHtml.Entries, HtmlResult(index = 4), HtmlDiv(), HtmlDiv(index = 1, extract = Html.ParseTextNested)],
			)

		elif version == ProviderHtml.Version2:
			ProviderHtml.initialize(self,
				name						= name,
				description					= description,
				rank						= rank,
				performance					= performance,
				status						= status,

				link						= Provider._Link[version],
				mirror						= Provider._Mirror,
				unblock						= Provider._Unblock,

				supportMovie				= True,
				supportShow					= True,
				supportPack					= True,

				offsetStart					= 1,
				offsetIncrease				= 1,

				formatEncode				= ProviderHtml.FormatEncodePlus,

				searchQuery					= Provider._Path[version] % (ProviderHtml.TermQuery, ProviderHtml.TermCategory, ProviderHtml.TermOffset),
				searchCategoryMovie			= ','.join([Provider._CategoryMovie, Provider._CategoryAnime]),
				searchCategoryShow			= ','.join([Provider._CategoryShow, Provider._CategoryAnime]),

				extractOptimizeData			= HtmlDiv(class_ = Provider._AttributeMain), # To detect the last page in processOffset().
				extractList					= [HtmlResults(class_ = Provider._AttributeTable)],
				extractLink					= [HtmlResult(index = 2), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
				extractFileName				= [HtmlResult(index = 1), HtmlLink()],
				extractFileSize				= [HtmlResult(index = 3)],
				extractFileExtra			= [HtmlResult(index = 1), HtmlDiv()], # Extract this as fileNameExtra, instead of individual values, since the filename might contain more specific details (eg: the div contains "3D", but the filename contains "3D SBS").
				extractSourceTimeInexact	= [HtmlResult(index = 4)],
				extractSourceSeeds			= [HtmlResult(index = 5), HtmlDiv(extract = [Html.AttributeTitle, Provider._ExpressionSeeds])],
				extractSourceLeeches		= [HtmlResult(index = 5), HtmlDiv(extract = [Html.AttributeTitle, Provider._ExpressionLeeches])],
			)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			if self.customVersion2():
				last = self.extractHtml(data, [Html(class_ = Provider._AttributePages), HtmlLink(attribute = {Html.AttributeAriaLabel : Provider._ExpressionNext, Html.AttributeClass : Provider._ExpressionMute})])
				if last: return ProviderHtml.Skip
		except: self.logError()

	def processFileExtra(self, value, item, details = None, entry = None):
		if self.customVersion2():
			try: value = Regex.remove(data = value, expression = Provider._ExpressionExclude, all = True).strip()
			except: pass
			return value
		else:
			return value if value else None

	def processSourceTimeInexact(self, value, item, details = None, entry = None):
		if self.customVersion2():
			if value and Provider._AttributeLong in value: return None
		return value
