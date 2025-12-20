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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlLink, HtmlDiv, HtmlImage
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	_Link					= ['https://skytorrents.to', 'https://skytorrents.in', 'https://skytorrents.org', 'https://skytorrents.net', 'https://skytorrents.lol']
	_Mirror					= ['https://torrends.to/site/skytorrents']

	_LimitApproval			= 5

	_ParameterSearch		= 'search'
	_ParameterPage			= 'page'
	_ParameterSort			= 'sort'
	_ParameterSeeds			= 'seeders'

	_AttributeTable			= 'table'
	_AttributeLabel			= 'label'

	_ExpressionMovie		= '(movie|video)'
	_ExpressionShow			= '(show|video)'
	_ExpressionVerified		= '(verified)'
	_ExpressionVoteUp		= '.*>\s*([\-\d]+)\s*<.+?thumb_upm'
	_ExpressionVoteDown		= '.*>\s*([\-\d]+)\s*<.+?thumb_downm'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name						= 'SkyTorrents',
			description					= '{name} is a less-known {container} site. The site contains results in various languages, but most of them are in English. {name} has many and high-quality results with good metadata, but also has strong Cloudflare protection that might not be bypassable and cause scraping to fail.',
			rank						= 4,
			performance					= ProviderHtml.PerformanceGood,
			status						= ProviderHtml.StatusDead, # Domain redirects to a different website. Update (2025-06): Still down.

			link						= Provider._Link,
			mirror						= Provider._Mirror,

			customVerified				= True,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			offsetStart					= 1,
			offsetIncrease				= 1,

			formatEncode				= ProviderHtml.FormatEncodeQuote,

			searchQuery					= {
											ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
											ProviderHtml.RequestData : {
												Provider._ParameterSearch	: ProviderHtml.TermQuery,
												Provider._ParameterPage		: ProviderHtml.TermOffset,
												Provider._ParameterSort		: Provider._ParameterSeeds,
											},
										},

			extractParser				= ProviderHtml.ParserHtml5, # Has a div and style element in the table body.
			extractList					= [HtmlResults(class_ = Provider._AttributeTable)],
			extractLink					= [HtmlResult(index = 0), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
			extractFileName				= [HtmlResult(index = 0), HtmlLink(index = 0)],
			extractFileSize				= [HtmlResult(index = 1)],
			extractSourceTimeInexact	= [HtmlResult(index = 3)],
			extractSourceSeeds			= [HtmlResult(index = 4)],
			extractSourceLeeches		= [HtmlResult(index = 5)],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processBefore(self, item):
		info = self.extractHtml(item, [HtmlResult(index = 0)])

		# Check category labels.
		category = Provider._ExpressionMovie if self.parameterMediaMovie() else Provider._ExpressionShow
		labels = self.extractHtml(info, [HtmlLink(class_ = Provider._AttributeLabel)])
		if labels: # Some do not have any labels.
			found = False
			for label in labels:
				if Regex.match(data = label.text, expression = category):
					found = True
					break
			if not found: return ProviderHtml.Skip

		# Check verified label.
		if self.customVerified():
			verified = self.extractHtml(info, [HtmlImage(title_ = Provider._ExpressionVerified)])
			if not verified: return ProviderHtml.Skip

	def processSourceApproval(self, value, item, details = None, entry = None):
		info = self.extractHtml(item, [HtmlResult(index = 0, extract = Html.ParseCode)])

		try: up = float(Regex.extract(data = info, expression = Provider._ExpressionVoteUp))
		except: up = 0
		try: down = float(Regex.extract(data = info, expression = Provider._ExpressionVoteDown))
		except: down = 0

		rating = min(1, max(-1, (up + down) / Provider._LimitApproval))
		return ProviderHtml.ApprovalDefault + ((1 - ProviderHtml.ApprovalDefault) * rating)
