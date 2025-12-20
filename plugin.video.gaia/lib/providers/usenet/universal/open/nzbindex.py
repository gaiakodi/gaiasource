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

from lib.providers.core.usenet import ProviderUsenetJson

class Provider(ProviderUsenetJson):

	_Link				= ['https://nzbindex.com', 'https://nzbindex.nl']

	_PathSearch			= {
							ProviderUsenetJson.Version1 : 'api/search',
							ProviderUsenetJson.Version2 : 'search/json',
						}
	_PathDownload		= {
							ProviderUsenetJson.Version1 : 'download/%s.nzb',
							ProviderUsenetJson.Version2 : 'download/%s',
						}

	_LimitOffset		= {
							ProviderUsenetJson.Version1 : 100,
							ProviderUsenetJson.Version2 : 250,
						}

	_ParameterQuery		= 'q'
	_ParameterPage1		= 'page'
	_ParameterPage2		= 'p'
	_ParameterLimit		= 'max'
	_ParameterSort		= 'sort'
	_ParameterSortAge	= 'agedesc'
	_ParameterAge		= 'maxage'
	_ParameterSize		= 'minsize'
	_ParameterSpam		= 'hidespam'
	_ParameterComplete	= 'complete'
	_ParameterPassword	= 'hidepassword'

	_AttributeResults	= 'results'
	_AttributeData		= 'data'
	_AttributeContent	= 'content'
	_AttributeId		= 'id'
	_AttributeName		= 'name'
	_AttributeSize		= 'size'
	_AttributeTime		= 'posted'
	_AttributeUploader	= 'poster'

	_ParameterStats		= 'stats'
	_ParameterCurrent1	= 'number'
	_ParameterCurrent2	= 'current_page'
	_ParameterPages1	= 'number'
	_ParameterPages2	= 'max_page'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		version = self.customVersion()

		name			= 'NZBIndex'
		description		= '{name} is one of the most well-known and oldest open usenet indexers. The site contains many English titles, but is also a great source for other European languages. {name} has several {containers} containing executables or other unplaybale files.'
		rank			= 4
		performance		= ProviderUsenetJson.PerformanceGood # Do not make Excellent, since it reurns many invalid links (eg PC games) that are only removed during full title validation.
		customVersion	= 2

		query = {
			Provider._ParameterQuery	: ProviderUsenetJson.TermQuery,
			Provider._ParameterLimit	: Provider._LimitOffset[version],
			Provider._ParameterSort		: Provider._ParameterSortAge,
		}

		age = self.customTime(days = True)
		if age: query[Provider._ParameterAge] = age
		size = self.customSize()
		if size: query[Provider._ParameterSize] = size
		spam = self.customSpam()
		if spam: query[Provider._ParameterSpam] = int(spam) # Not in new API anymore, or at least not listed on the website.
		password = self.customPassword()
		if password: query[Provider._ParameterPassword] = int(password) # Not in new API anymore, or at least not listed on the website.
		if self.customIncomplete(): query[Provider._ParameterComplete] = 1

		# New API (post 2025-12).
		if version == ProviderUsenetJson.Version1:
			query[Provider._ParameterPage1] = ProviderUsenetJson.TermOffset

			ProviderUsenetJson.initialize(self,
				name					= name,
				description				= description,
				rank					= rank,
				performance				= performance,

				link					= Provider._Link,

				customVersion			= customVersion,
				customSpam				= True,
				customPassword			= True,
				customIncomplete		= True,

				supportMovie			= True,
				supportShow				= True,
				supportPack				= True,

				offsetStart				= 0,
				offsetIncrease			= 1,

				searchQuery				= {
											ProviderUsenetJson.RequestMethod : ProviderUsenetJson.RequestMethodGet,
											ProviderUsenetJson.RequestPath : Provider._PathSearch[version],
											ProviderUsenetJson.RequestData : query,
										},

				extractList				= [Provider._AttributeData, Provider._AttributeContent],
				extractLink				= Provider._AttributeId,
				extractIdLocal			= Provider._AttributeId,
				extractFileName			= Provider._AttributeName,
				extractFileSize			= Provider._AttributeSize,
				extractSourceTime		= Provider._AttributeTime,
				extractReleaseUploader	= Provider._AttributeUploader,
			)

		# Old API (pre 2025).
		elif version == ProviderUsenetJson.Version2:
			query[Provider._ParameterPage2] = ProviderUsenetJson.TermOffset

			ProviderUsenetJson.initialize(self,
				name					= name,
				description				= description,
				rank					= rank,
				performance				= performance,

				link					= Provider._Link,

				customVersion			= customVersion,
				customSpam				= True,
				customPassword			= True,
				customIncomplete		= True,

				supportMovie			= True,
				supportShow				= True,
				supportPack				= True,

				offsetStart				= 0,
				offsetIncrease			= 1,

				searchQuery				= {
											ProviderUsenetJson.RequestMethod : ProviderUsenetJson.RequestMethodGet,
											ProviderUsenetJson.RequestPath : Provider._PathSearch[version],
											ProviderUsenetJson.RequestData : query,
										},

				extractList				= Provider._AttributeResults,
				extractLink				= Provider._AttributeId,
				extractIdLocal			= Provider._AttributeId,
				extractFileName			= Provider._AttributeName,
				extractFileSize			= Provider._AttributeSize,
				extractSourceTime		= Provider._AttributeTime,
				extractReleaseUploader	= Provider._AttributeUploader,
			)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			version = self.customVersion()
			if version == ProviderUsenetJson.Version1:
				stats = data[Provider._AttributeData][Provider._ParameterPage1]
				if int(stats[Provider._ParameterCurrent1]) >= (int(stats[Provider._ParameterPages1]) - 1): return ProviderUsenetJson.Skip # Current page starts at 0.
			elif version == ProviderUsenetJson.Version2:
				stats = data[Provider._ParameterStats]
				if int(stats[Provider._ParameterCurrent2]) >= int(stats[Provider._ParameterPages2]): return ProviderUsenetJson.Skip
		except: pass

	def processLink(self, value, item, details = None, entry = None):
		if not value: return ProviderUsenetJson.Skip
		return self.linkCurrent(path = Provider._PathDownload[self.customVersion()] % value)
