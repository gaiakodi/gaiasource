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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlLink, HtmlImage
from lib.modules.tools import Regex, Time

# https://thepiratebay.org uses ApiBay and is therefore excluded.

class Provider(ProviderHtml):

	_Link					= {
								ProviderHtml.Version1 : ['https://thepiratebay.zone', 'https://pirateproxy.live', 'https://thepiratebay10.org', 'https://tpb.party', 'https://thehiddenbay.com'],
								ProviderHtml.Version2 : ['https://piratebay.party', 'https://thepiratebay.party'],
								ProviderHtml.Version3 : ['https://thepìratebay.com', 'https://thepìratebay.se', 'https://thepiratebay3.to'],
							}
	_Mirror					= {
								ProviderHtml.Version1 : ['https://heypirateproxy.com'],
								ProviderHtml.Version2 : None,
								ProviderHtml.Version3 : ['https://thepiratebays.com'],
							}
	_Unblock				= {
								ProviderHtml.Version1 : {ProviderHtml.UnblockFormat1 : 'thepiratebay'},
								ProviderHtml.Version2 : None,
								ProviderHtml.Version3 : None,
							}
	_Path					= {
								ProviderHtml.Version1 : 'search/%s/%s/7/%s/', # 7 = sort by seeds
								ProviderHtml.Version2 : 'search/%s/%s/7/%s/', # 7 = sort by seeds
								ProviderHtml.Version3 : 's/0/5/0/page/%s/?q=%s&category=%s', # 5 = sort by seeds
							}

	_CategoryMovie			= ['201', '202', '207', '209'] # 201 = Movies, 202 = Movies DVDR, 207 = HD Movies, 209 = 3D
	_CategoryShow			= ['205', '208'] # 205 = TV Shows, 208 = HD TV Shows

	_AttributeResults		= 'searchResult'
	_AttributeName			= 'detName'
	_AttributeDescription	= 'detDesc'

	_ExpressionVerified		= r'(vip|trusted)'
	_ExpressionSize			= r'size\s*(.*?)[,$]'
	_ExpressionTime			= r'uploaded\s*(.*?)[,$]'
	_ExpressionNext			= r'alt\s*=\s*"next"'
	_ExpressionVip 			= r'vip'
	_ExpressionTrusted		= r'trust'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		version = self.customVersion()
		category = self.customCategory()

		if version == ProviderHtml.Version1:
			parameters				= (ProviderHtml.TermQuery, ProviderHtml.TermOffset, ProviderHtml.TermCategory)
			extractLink				= [HtmlResult(index = 1), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)]
			extractFileName			= [HtmlResult(index = 1), Html(class_ = Provider._AttributeName), HtmlLink()]
			extractFileSize			= [HtmlResult(index = 1), Html(class_ = Provider._AttributeDescription, extract = Provider._ExpressionSize)]
			extractReleaseUploader	= [HtmlResult(index = 1), Html(class_ = Provider._AttributeDescription), HtmlLink()]
			extractSourceTime		= [HtmlResult(index = 1), Html(class_ = Provider._AttributeDescription, extract = Provider._ExpressionTime)]
			extractSourceApproval	= [HtmlResult(index = 1), HtmlImage(title_ = Provider._ExpressionVerified, extract = Html.AttributeTitle)]
			extractSourceSeeds		= [HtmlResult(index = 2)]
			extractSourceLeeches	= [HtmlResult(index = 3)]
		elif version == ProviderHtml.Version2 or version == ProviderHtml.Version3:
			extractLink				= [HtmlResult(index = 3), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)]
			extractFileName			= [HtmlResult(index = 1)]
			extractFileSize			= [HtmlResult(index = 4)]
			extractReleaseUploader	= [HtmlResult(index = 7)]
			extractSourceTime		= [HtmlResult(index = 2)]
			extractSourceSeeds		= [HtmlResult(index = 5)]
			extractSourceLeeches	= [HtmlResult(index = 6)]
			if version == ProviderHtml.Version2:
				parameters				= (ProviderHtml.TermQuery, ProviderHtml.TermOffset, ProviderHtml.TermCategory)
				extractSourceApproval	= [HtmlResult(index = 3), HtmlImage(title_ = Provider._ExpressionVerified, extract = Html.AttributeTitle)]
			else:
				parameters				= (ProviderHtml.TermOffset, ProviderHtml.TermQuery, ProviderHtml.TermCategory)
				extractSourceApproval = None

		ProviderHtml.initialize(self,
			name					= 'ThePirateBay',
			description				= '{name} is one of the oldest and most well-known {container} sites. The site contains results in various languages, but most of them are in English. Modern {name} sites use an API which is implemented by the ApiBay provider, whereas this provider offers legacy support for old {name} sites. There are different versions of {name} on different mirror sites which are incompatible with each other. Version %s and %s are faster than version %s.'  % (ProviderHtml.Version1, ProviderHtml.Version2, ProviderHtml.Version3),
			rank					= 5,
			performance				= ProviderHtml.PerformanceGood,

			link					= Provider._Link[version],
			mirror					= Provider._Mirror[version],
			unblock					= Provider._Unblock[version],

			customVersion			= 3,
			customCategory			= True,
			customVerified			= True,

			supportMovie			= True,
			supportShow				= True,
			supportPack				= True,

			offsetStart				= 1,
			offsetIncrease			= 1,

			formatEncode			= ProviderHtml.FormatEncodeQuote,

			searchQuery				= Provider._Path[version] % parameters,
			searchCategoryMovie		= Provider._CategoryMovie if category else ','.join(Provider._CategoryMovie),
			searchCategoryShow		= Provider._CategoryShow if category else ','.join(Provider._CategoryShow),

			extractList				= [HtmlResults(id_ = Provider._AttributeResults)],
			extractLink				= extractLink,
			extractFileName			= extractFileName,
			extractFileSize			= extractFileSize,
			extractReleaseUploader	= extractReleaseUploader,
			extractSourceTime		= extractSourceTime,
			extractSourceApproval	= extractSourceApproval,
			extractSourceSeeds		= extractSourceSeeds,
			extractSourceLeeches	= extractSourceLeeches,
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		if not Regex.match(data = str(items[-1]), expression = Provider._ExpressionNext): return ProviderHtml.Skip

	def processSourceTime(self, value, item, details = None, entry = None):
		# Dates are given in different formats:
		#	Very new uploads: MM ago
		#	New uploads: Today/Y-day HH:MM
		#	Recent uploads: MM-DD HH:MM
		#	Old uploads: MM-DD YYYY
		#	Some values on version 3: YYYY-MM-DD HH:MM
		if value:
			result = ''
			if Regex.match(data = value, expression = r'\d{4}-\d{2}-\d{2}'):
				return value
			elif Regex.match(data = value, expression = r'ago'):
				return value
			elif Regex.match(data = value, expression = r'today'):
				result += Time.format(format = Time.FormatDate)
			elif Regex.match(data = value, expression = r'y[\-\s]*day'):
				result += Time.past(days = 1, format = Time.FormatDate)
			else:
				year = Regex.extract(data = value, expression = r'(\d{4})')
				if not year: year = Time.year()
				month = Regex.extract(data = value, expression = r'(\d{2})-')
				day = Regex.extract(data = value, expression = r'-(\d{2})')
				if year and month and day: result += '%s-%s-%s' % (year, month, day)

			hour = Regex.extract(data = value, expression = r'(\d{2}):')
			minute = Regex.extract(data = value, expression = r':(\d{2})')
			if hour and minute: result += ' %s:%s:%s' % (hour, minute, '00')

			return result
		return value

	def processSourceApproval(self, value, item, details = None, entry = None):
		if value:
			vip = Regex.match(data = value, expression = Provider._ExpressionVip)
			trusted = Regex.match(data = value, expression = Provider._ExpressionTrusted)
		else:
			vip = False
			trusted = False
		if self.customVerified():
			if not vip and not trusted: return ProviderHtml.Skip
		if vip: return ProviderHtml.ApprovalExcellent
		elif trusted: return ProviderHtml.ApprovalGood
		else: return ProviderHtml.ApprovalDefault
