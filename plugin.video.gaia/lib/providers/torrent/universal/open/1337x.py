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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlLink, HtmlListUnordered, HtmlListItem, HtmlDiv, HtmlSmall
from lib.modules.tools import Regex, Time

class Provider(ProviderHtml):

	_Link					= ['https://1337x.to', 'https://1337x.so', 'https://1337x.st', 'https://x1337x.ws', 'https://x1337x.eu', 'https://x1337x.se']
	_Mirror					= ['https://1337x.to/about', 'https://torrends.to/proxy/1337x']
	_Unblock				= {ProviderHtml.UnblockFormat1 : '1337x', ProviderHtml.UnblockFormat2 : '1337x', ProviderHtml.UnblockFormat3 : '1337x2', ProviderHtml.UnblockFormat4 : '1337x'}
	_Path					= 'sort-category-search/%s/%s/seeders/desc/%s/'

	_CategoryMovie			= 'Movies'
	_CategoryShow			= 'TV'

	_AttributeBox			= 'box-info-detail'
	_AttributeTable			= 'table-list'
	_AttributeName			= 'name'
	_AttributeSize			= 'size'
	_AttributeDate			= 'coll-date'
	_AttributeSeeds			= 'seeds'
	_AttributeLeeches		= 'leeches'
	_AttributeUploader		= 'uploader'
	_AttributePages			= 'pagination'
	_AttributeLast			= 'last'
	_AttributeDetails		= 'torrent-detail-page'
	_AttributeList			= 'list'
	_AttributeInfo			= 'box-info'
	_AttributeFiles			= 'head'

	# Admin = Black, Moderator = Green, VIP = Blue, Uploader = Orange, Trial Uploader = Red, Member = Grey
	_ExpressionAdmin		= '(?:^|\s)(admin)(?:$|\s)'
	_ExpressionModerator	= '(?:^|\s)(moderator)(?:$|\s)'
	_ExpressionVip			= '(?:^|\s)(vip)(?:$|\s)'
	_ExpressionUploader		= '(?:^|\s)(uploader)(?:$|\s)'
	_ExpressionTrial		= '(?:^|\s)(trial)(?:$|\s|-|_)'
	_ExpressionMember		= '(?:^|\s)(member)(?:$|\s)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name					= '1337X',
			description				= '{name} is one of the oldest and most well-known {container} sites. The site contains results in various languages, but most of them are in English. The search page of {name} does not contain all the metadata. A subpage must therefore be retrieved for each result in order to extract the magnet link, which substantially increases scraping time.',
			rank					= 4,
			performance				= ProviderHtml.PerformanceBad,

			link					= Provider._Link,
			mirror					= Provider._Mirror,
			unblock					= Provider._Unblock,

			customVerified			= True,

			supportMovie			= True,
			supportShow				= True,
			supportPack				= True,

			offsetStart				= 1,
			offsetIncrease			= 1,

			formatEncode			= ProviderHtml.FormatEncodePlus,

			searchQuery				= Provider._Path % (ProviderHtml.TermQuery, ProviderHtml.TermCategory, ProviderHtml.TermOffset),
			searchCategoryMovie		= Provider._CategoryMovie,
			searchCategoryShow		= Provider._CategoryShow,

			extractOptimizeData		= HtmlDiv(class_ = Provider._AttributeBox), # To detect the last page in processOffset().
			extractOptimizeDetails	= HtmlDiv(class_ = Provider._AttributeInfo),
			extractList				= [HtmlResults(class_ = Provider._AttributeTable)],
			extractDetails			= [HtmlResult(class_ = Provider._AttributeName), HtmlLink(index = 1, extract = Html.AttributeHref)],
			extractLink				= [ProviderHtml.Details, Html(class_ = Provider._AttributeDetails), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
			extractFileName			= [HtmlResult(class_ = Provider._AttributeName), HtmlLink(index = 1)], # Very long titles are cut off (...), but on the main and details page, there is not perfect/reliable way to get the full title. Let Stream extract it from the magnet.
			extractFileSize			= [HtmlResult(class_ = Provider._AttributeSize, extract = Html.ParseTextUnnested)],
			extractReleaseUploader	= [HtmlResult(class_ = Provider._AttributeUploader)],
			extractSourceTime		= [HtmlResult(class_ = Provider._AttributeDate)],
			extractSourceApproval	= [ProviderHtml.Details, Html(class_ = Provider._AttributeDetails), HtmlListUnordered(class_ = Provider._AttributeList), HtmlListItem(index = 4), HtmlSmall(extract = Html.AttributeClass)],
			extractSourceSeeds		= [HtmlResult(class_ = Provider._AttributeSeeds)],
			extractSourceLeeches	= [HtmlResult(class_ = Provider._AttributeLeeches)],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			last = self.extractHtml(data, [Html(class_ = Provider._AttributePages), Html(class_ = Provider._AttributeLast)])
			if not last: return ProviderHtml.Skip
		except: self.logError()

	def processSourceTime(self, value, item, details = None, entry = None):
		# Dates are given in different formats:
		#	New uploads: (eg: 5:47am)
		#	Recent uploads: (eg: 7am Nov. 9th)
		#	Old uploads: (eg: Apr. 12th '20)
		if value:
			result = ''

			year = Regex.extract(data = value, expression = '(\d{4})')
			if not year:
				year = Regex.extract(data = value, expression = '\'(\d{2})')
				if year: year = int('20' + year)
			if not year: year = Time.year()
			month = Regex.extract(data = value, expression = '([a-z]{3})\.')
			day = Regex.extract(data = value, expression = '\.\s(\d{1,2})[a-z]')
			if year and month and day: result += '%s %s %s' % (day, month, year)
			else: result += Time.format(format = Time.FormatDate)

			hour = Regex.extract(data = value, expression = '(\d{1,2})(?::\d{2})?am')
			if not hour:
				hour = Regex.extract(data = value, expression = '(\d{1,2})(?::\d{2})?pm')
				if hour: hour = str(int(hour) + 12)
			if hour:
				minute = Regex.extract(data = value, expression = ':(\d{2})')
				if not minute: minute = '00'
				if minute: result += ' %s:%s:%s' % (hour, minute, '00')

			return result
		return value

	def processSourceApproval(self, value, item, details = None, entry = None):
		if value:
			value = ' '.join(value)

			match = Regex.match(data = value, expression = Provider._ExpressionAdmin)
			if match: return ProviderHtml.ApprovalExcellent

			match = Regex.match(data = value, expression = Provider._ExpressionModerator)
			if match: return ProviderHtml.ApprovalExcellent

			match = Regex.match(data = value, expression = Provider._ExpressionVip)
			if match: return ProviderHtml.ApprovalExcellent

			match = Regex.match(data = value, expression = Provider._ExpressionUploader)
			if match: return ProviderHtml.ApprovalGood

			if self.customVerified(): return ProviderHtml.Skip

			match = Regex.match(data = value, expression = Provider._ExpressionTrial)
			if match: return ProviderHtml.ApprovalBad

			return ProviderHtml.ApprovalDefault
		else:
			return None # Extract on second iteration when the details page has been extracted.
