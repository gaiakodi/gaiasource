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

from lib.providers.core.html import ProviderHtml, Html, HtmlBody, HtmlLink, HtmlDiv, HtmlSpan

class Provider(ProviderHtml):

	_Link					= ['https://btdig.com']
	_Unblock				= {ProviderHtml.UnblockFormat2 : 'btdigg', ProviderHtml.UnblockFormat3 : 'btdigg'}

	_Path					= 'search'

	_ParameterQuery			= 'q'
	_ParameterOffset		= 'p'
	_ParameterSort			= 'order'
	_ParameterRelevance		= '0'

	_AttributeItem			= 'one_result'
	_AttributeLink			= 'torrent_magnet'
	_AttributeName			= 'torrent_name'
	_AttributeSize			= 'torrent_size'
	_AttributeTime			= 'torrent_age'

	_ExpressionTime			= 'found\s*(.*)'
	_ExpressionDownloads	= 'downloaded\s*(\d+)\s*time'
	_ExpressionNext			= '(>|&gt;){1,}'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name						= 'BTDigg',
			description					= '{name} is an old but long-lasting {container} site. The site contains results in various languages, but most of them are in English. {name} is unreliable and has inaccurate or missing metadata, such as the peer count, and should therefore only be used if no other {container} provider works. {name} has strong Cloudflare protection that might not be bypassable and cause scraping to fail.',
			rank						= 1,
			performance					= ProviderHtml.PerformanceGood - ProviderHtml.PerformanceStep,
			status						= ProviderHtml.StatusCloudflare, # Cloudflare. Even when Cloudflare is not present, there is still a custom reCaptcha on the site.

			link						= Provider._Link,
			unblock						= Provider._Unblock,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			offsetStart					= 1,
			offsetIncrease				= 1,

			formatEncode				= ProviderHtml.FormatEncodePlus,

			searchQuery					= {
											ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
											ProviderHtml.RequestPath : Provider._Path,
											ProviderHtml.RequestData : {
												Provider._ParameterQuery	: ProviderHtml.TermQuery,
												Provider._ParameterOffset	: ProviderHtml.TermOffset,
												Provider._ParameterSort		: Provider._ParameterRelevance,
											},
										},

			extractOptimizeData			= HtmlBody(),
			extractList					= [HtmlDiv(class_ = Provider._AttributeItem)],
			extractLink					= [HtmlDiv(class_ =  Provider._AttributeLink), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
			extractFileName				= [HtmlDiv(class_ =  Provider._AttributeName)],
			extractFileSize				= [HtmlSpan(class_ =  Provider._AttributeSize)],
			extractSourceTimeInexact	= [HtmlSpan(class_ =  Provider._AttributeTime, extract = [Html.ParseText, Provider._ExpressionTime])],
		)
