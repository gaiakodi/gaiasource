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

# There is not official name for this library and website layout.
# But there are HTML/CSS IDs and classes named "nzbreader" in the website HTML and download links.
# NZB links redirect to nzbreader.com.

from lib.providers.core.usenet import ProviderUsenetHtml
from lib.providers.core.html import Html, HtmlResults, HtmlResult, HtmlTable, HtmlLink, HtmlDiv, HtmlBold
from lib.modules.tools import Regex
from lib.modules.network import Networker

class ProviderNzbreader(ProviderUsenetHtml):

	Fork1					= 1		# findnzb.com, nzbid.net
	Fork2					= 2		# nzbfriends.com
	ForkDefault				= Fork1

	_Fork					= 'NZBReader'

	_PathDownload			= 'nzb/?getnzb_transparent=1&collection=%s&uuid=%s'

	_LimitOffset			= 100

	_ParameterQuery			= 'q'
	_ParameterPage			= 'page'
	_ParameterLimit			= 'limit'
	_ParameterSize			= 'min'
	_ParameterAge			= 'age'
	_ParameterSort			= 'sort'
	_ParameterRelevance		= 'relevance'
	_ParameterType			= 'type'
	_ParameterSubject		= 'subject'

	_AttributeContainer		= 'height'
	_AttributeTable			= 'results'
	_AttributeNext			= 'paging_next'

	_ExpressionCollection	= 'collection\/(.*?)(?:$|\/)'
	_ExpressionUuid			= 'nzbreader\/(.*?)(?:$|\/)'
	_ExpressionGet			= '(\/get\/collection\/)'
	_ExpressionUploader		= '(?:&|&amp;)q=(.*?)(?:$|&)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self,
		fork		= ForkDefault,

		description	= None,

		# Because subrequests are required to get the NZB link and has very few results.
		rank		= 2,
		performance	= ProviderUsenetHtml.PerformanceBad,

		**kwargs
	):
		self.mCollection = None

		self.forkSet(fork = fork)
		if fork == ProviderNzbreader.Fork1:
			extractDetails				= [[HtmlResult(index = 0), HtmlLink(href_ = ProviderNzbreader._ExpressionCollection, extract = [Html.AttributeHref, ProviderNzbreader._ExpressionCollection])], [HtmlResult(index = 0), HtmlLink(href_ = ProviderNzbreader._ExpressionUuid, extract = [Html.AttributeHref, ProviderNzbreader._ExpressionUuid])]]
			extractLink					= [ProviderUsenetHtml.Details, HtmlLink(href_ = ProviderNzbreader._ExpressionGet, extract = Html.AttributeHref)]
			extractIdUniversal			= [HtmlResult(index = 0), HtmlLink(href_ = ProviderNzbreader._ExpressionUuid, extract = [Html.AttributeHref, ProviderNzbreader._ExpressionUuid])]
			extractIdCollection			= [HtmlResult(index = 0), HtmlLink(href_ = ProviderNzbreader._ExpressionCollection, extract = [Html.AttributeHref, ProviderNzbreader._ExpressionCollection])]
			extractSourceTimeInexact	= [HtmlResult(index = 4)]
			extractReleaseUploader		= [HtmlResult(index = 2), HtmlLink(href_ = ProviderNzbreader._ExpressionUploader, extract = [Html.AttributeHref, ProviderNzbreader._ExpressionUploader])] # Use the link instead of the inner text, since the inner text sometimes cuts off characteres from the name.
		elif fork == ProviderNzbreader.Fork2:
			extractDetails				= [HtmlResult(index = 0), HtmlLink(href_ = ProviderNzbreader._ExpressionCollection, extract = Html.AttributeHref)]
			extractLink					= [ProviderUsenetHtml.Details, HtmlLink(href_ = ProviderNzbreader._ExpressionUuid, extract = [Html.AttributeHref, ProviderNzbreader._ExpressionUuid])]
			extractIdUniversal			= [ProviderUsenetHtml.Details, HtmlLink(href_ = ProviderNzbreader._ExpressionUuid, extract = [Html.AttributeHref, ProviderNzbreader._ExpressionUuid])]
			extractIdCollection			= None
			extractSourceTimeInexact	= [HtmlResult(index = 3)]
			extractReleaseUploader	 	= [HtmlResult(index = 0), HtmlDiv(index = 1), HtmlLink(extract = [Html.AttributeHref, ProviderNzbreader._ExpressionUploader])] # Use the link instead of the inner text, since the inner text sometimes cuts off characteres from the name.

		if not description: description = '{name} is a usenet indexer based on {fork}. The site contains many English titles, but is also a great source for other European languages. Subpages have to be requested to extract the {container} link which substantially increases scraping time. {name} returns few results and often has incomplete metadata.'
		description = description.replace('{fork}', ProviderNzbreader._Fork)

		query = {
			ProviderNzbreader._ParameterQuery	: ProviderUsenetHtml.TermQuery,
			ProviderNzbreader._ParameterPage	: ProviderUsenetHtml.TermOffset,
			ProviderNzbreader._ParameterLimit	: ProviderNzbreader._LimitOffset,
			ProviderNzbreader._ParameterType	: ProviderNzbreader._ParameterSubject,
			ProviderNzbreader._ParameterSort	: ProviderNzbreader._ParameterRelevance,
		}

		age = self.customTime(days = True)
		if age: query[ProviderNzbreader._ParameterAge] = age
		size = self.customSize()
		if size: query[ProviderNzbreader._ParameterSize] = size

		ProviderUsenetHtml.initialize(self,
			description					= description,
			rank						= rank,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			offsetStart					= 1,
			offsetIncrease				= 1,

			formatEncode				= ProviderUsenetHtml.FormatEncodePlus,

			searchQuery					= {
											ProviderUsenetHtml.RequestMethod : ProviderUsenetHtml.RequestMethodGet,
											ProviderUsenetHtml.RequestData : query,
										},

			extractOptimizeData			= HtmlTable(class_ = ProviderNzbreader._AttributeContainer), # To detect the last page in processOffset().
			extractDetails				= extractDetails,
			extractList					= [HtmlResults(class_ = ProviderNzbreader._AttributeTable, index = -1, start = 1)], # index = -1: Can be multiple results table on Fork 2. start = 1: table header.
			extractLink					= extractLink,
			extractIdUniversal			= extractIdUniversal,
			extractIdCollection			= extractIdCollection,
			extractFileName				= [HtmlResult(index = 0), HtmlLink()],
			extractFileSize				= [HtmlResult(index = 1), HtmlBold()],
			extractSourceTimeInexact	= extractSourceTimeInexact,
			extractReleaseUploader		= extractReleaseUploader,

			**kwargs
		)

	##############################################################################
	# FORK
	##############################################################################

	def fork(self):
		return self.mFork

	def fork1(self):
		return self.mFork == ProviderNzbreader.Fork1

	def fork2(self):
		return self.mFork == ProviderNzbreader.Fork2

	def forkSet(self, fork):
		self.mFork = fork

	##############################################################################
	# LINK
	##############################################################################

	def linkDownload(self, collection, uuid):
		if collection and uuid: return Networker.linkJoin(self.linkCurrent(), ProviderNzbreader._PathDownload % (collection, uuid))
		else: return ProviderUsenetHtml.Skip

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		next = self.extractHtml(data, [HtmlLink(class_ = ProviderNzbreader._AttributeNext)])
		if not next: return ProviderUsenetHtml.Skip

	def processDetails(self, value, item):
		if self.fork1():
			try: return self.linkDownload(collection = value[0], uuid = value[1])
			except: return ProviderUsenetHtml.Skip
		else:
			self.mCollection = Regex.extract(data = value, expression = ProviderNzbreader._ExpressionCollection)
		return value

	def processLink(self, value, item, details = None, entry = None):
		if self.fork2() and details: return self.linkDownload(collection = self.mCollection, uuid = value)
		return value

	def processIdCollection(self, value, item, details = None, entry = None):
		if self.fork2(): return self.mCollection
		return value

##############################################################################
# FORKS
##############################################################################

class ProviderNzbreader1(ProviderNzbreader):

	def initialize(self, **kwargs):
		ProviderNzbreader.initialize(self, fork = ProviderNzbreader.Fork1, **kwargs)

class ProviderNzbreader2(ProviderNzbreader):

	def initialize(self, **kwargs):
		ProviderNzbreader.initialize(self, fork = ProviderNzbreader.Fork2, **kwargs)
