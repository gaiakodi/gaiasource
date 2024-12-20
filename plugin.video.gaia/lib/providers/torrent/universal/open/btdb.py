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

from lib.providers.core.html import ProviderHtml, Html, HtmlLink, HtmlDiv, HtmlSpan, HtmlSmall, HtmlStrong, HtmlListUnordered, HtmlListItem

class Provider(ProviderHtml):

	_Link					= ['https://btdb.eu']
	_Unblock				= {ProviderHtml.UnblockFormat2 : 'btdb', ProviderHtml.UnblockFormat3 : 'btdb'}
	_Path					= 'search/%s/?sort=hits&page=%s'

	_LimitApproval			= 5

	_AttributeContent		= 'card-body'
	_AttributeMedia			= 'media'
	_AttributeMediaBody		= 'media-body'
	_AttributeMediaRight	= 'media-right'
	_AttributeName			= 'item-title'
	_AttributeInfo			= 'item-meta-info'
	_AttributeDownloads		= 'item-meta-info'
	_AttributePages			= 'pagination'
	_AttributeNext			= 'next'
	_AttributeDisabled		= 'disabled'

	_ExpressionDownloads	= '(downloads)'
	_ExpressionVoteUp		= '(up\s*votes)'
	_ExpressionVoteDown		= '(down\s*votes)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name						= 'BTDB',
			description					= '{name} is a less-known {container} site. The site contains results in various languages, but most of them are in English. {name} has many {containers}, but the seed and leech counters are often outdated. {name} has strong Cloudflare protection that might not be bypassable and cause scraping to fail.',
			rank						= 3,
			performance					= ProviderHtml.PerformanceGood,
			status						= ProviderHtml.StatusDead, # Domain redirects to a different website. Update (2024-12): Still down.

			link						= Provider._Link,
			unblock						= Provider._Unblock,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			offsetStart					= 1,
			offsetIncrease				= 1,

			formatEncode				= ProviderHtml.FormatEncodeQuote,

			searchQuery					= Provider._Path % (ProviderHtml.TermQuery, ProviderHtml.TermOffset),

			extractOptimizeData			= HtmlDiv(class_ = Provider._AttributeContent), # To detect the last page in processOffset().
			extractList					= [HtmlDiv(class_ = Provider._AttributeMedia)],
			extractLink					= [HtmlDiv(class_ = Provider._AttributeMediaRight), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
			extractFileName				= [HtmlDiv(class_ = Provider._AttributeMediaBody), HtmlDiv(class_ = Provider._AttributeName)],
			extractFileSize				= [HtmlDiv(class_ = Provider._AttributeMediaBody), HtmlDiv(class_ = Provider._AttributeInfo), HtmlSmall(index = 0), HtmlStrong()],
			extractSourceTimeInexact	= [HtmlDiv(class_ = Provider._AttributeMediaBody), HtmlDiv(class_ = Provider._AttributeInfo), HtmlSmall(index = 4), HtmlStrong()],
			extractSourceApproval		= [
											[HtmlDiv(class_ = Provider._AttributeMediaRight), HtmlSmall(title_ = Provider._ExpressionDownloads)],
											[HtmlDiv(class_ = Provider._AttributeMediaBody), HtmlDiv(class_ = Provider._AttributeInfo), HtmlSpan(title_ = Provider._ExpressionVoteUp)],
											[HtmlDiv(class_ = Provider._AttributeMediaBody), HtmlDiv(class_ = Provider._AttributeInfo), HtmlSpan(title_ = Provider._ExpressionVoteDown)],
										],
			extractSourceSeeds			= [HtmlDiv(class_ = Provider._AttributeMediaBody), HtmlDiv(class_ = Provider._AttributeInfo), HtmlSmall(index = 2), HtmlStrong(extract = [Html.ParseText, Html.ParseRemoveComma])],
			extractSourceLeeches		= [HtmlDiv(class_ = Provider._AttributeMediaBody), HtmlDiv(class_ = Provider._AttributeInfo), HtmlSmall(index = 3), HtmlStrong(extract = [Html.ParseText, Html.ParseRemoveComma])],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			next = self.extractHtml(data, [HtmlListUnordered(class_ = Provider._AttributePages), HtmlListItem(class_ = Provider._AttributeNext, extract = Html.AttributeClass)])
			if not next or Provider._AttributeDisabled in next: return ProviderHtml.Skip
		except: self.logError()

	def processSourceApproval(self, value, item, details = None, entry = None):
		result = ProviderHtml.ApprovalDefault
		remaining = 1 - ProviderHtml.ApprovalDefault
		ratio = (remaining * 0.6) if (value and value[0]) else remaining
		try: result += ((remaining * 0.4) * min(1, (float(value[0]) / Provider._LimitApproval)))
		except: pass
		votes = 0
		try: votes += float(value[1])
		except: pass
		try: votes -= float(value[2])
		except: pass
		result += ratio * max(-1, min(1, votes / Provider._LimitApproval))
		return result
