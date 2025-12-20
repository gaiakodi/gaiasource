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

from lib.providers.core.json import ProviderJson

class Provider(ProviderJson):

	# The .hair domain returns an empty page.
	# Not sure if the .homes domain is the official replacement.
	# But the .homes domain works out of the box, if the "zSearch" option is enabled on the website.
	# The "xSearch" option does not return any results.
	# The "mSearch" option works, but does not have magnets/hashes on the main page.
	_Link					= ['https://magnetdl.homes'] # Old (pre 2025): https://magnetdl.hair

	_Path					= 'api.php?url=/q.php'

	_CategoryMovie			= ['201', '202', '207', '209'] # 201 = Movies, 202 = Movies DVDR, 207 = HD Movies, 209 = 3D
	_CategoryShow			= ['205', '208'] # 205 = TV Shows, 208 = HD TV Shows

	_Query					= '%s?%s=%s&%s=%s' # Do not URL-encode "&" (%26), otherwise no results are returned.

	_LimitOffset			= 100 # The maximum number of results returned by a query.

	_ParameterQuery			= 'q'
	_ParameterCategory		= 'cat'

	_AttributeUploader		= 'username'
	_AttributeName			= 'name'
	_AttributeSize			= 'size'
	_AttributeHash			= 'info_hash'
	_AttributeTime			= 'added'
	_AttributeStatus		= 'status'
	_AttributeSeeds			= 'seeders'
	_AttributeLeeches		= 'leechers'
	_AttributeImdb			= 'imdb'
	_AttributeVip			= 'vip'
	_AttributeTrusted		= 'trusted'
	_AttributeMember		= 'member'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		id = self.customSearchId()
		category = self.customCategory()
		ProviderJson.initialize(self,
			name					= 'MagnetDlAlt',
			description				= '{name} has a very large database of {containers}. The site contains results in various languages, but most of them are in English. {name} does not support paging and sorting and might therefore have few results. Although it shares a name with MagnetDL, it is a completely different site.',
			rank					= 3,
			performance				= ProviderJson.PerformanceMedium,

			link					= Provider._Link,

			customSearch			= {
										ProviderJson.SettingsDefault		: ProviderJson.CustomSearchTitle,
										ProviderJson.SettingsDescription	: 'Search {name} using the title or the IMDb ID. Not all files have an associated ID and searching by title might therefore return more results. Searching by title is slower and can return incorrect results. The title will be used if no ID is available.',
									},
			customCategory			= {
										ProviderJson.SettingsDefault		: True,
										ProviderJson.SettingsDescription	: '{name} returns a maximum of %d results per request. {name} has subcategories that can be searched together with a single request or can be searched separately with multiple requests. Searching categories separately might return more results, but can also increase the scraping time.' % Provider._LimitOffset,
									},
			customVerified			= True,

			supportMovie			= True,
			supportShow				= True,
			supportPack				= True,

			# Important to manually create the GET URL for version 4.
			# Since version 4 already has a ? in the URL, Networker will append the GET parameters with a &.
			#searchQuery				= {
			#							ProviderJson.RequestPath : path,
			#							ProviderJson.RequestData : {
			#								Provider._ParameterQuery	: Provider.TermIdImdb if id else Provider.TermQuery,
			#								Provider._ParameterCategory	: ProviderJson.TermCategory,
			#							},
			#						},
			searchQuery				= [
										Provider._Query % (Provider._Path, Provider._ParameterQuery, Provider.TermIdImdb if id else Provider.TermQuery, Provider._ParameterCategory, ProviderJson.TermCategory),
										Provider._Query % (Provider._Path, Provider._ParameterQuery, Provider.TermQuery, Provider._ParameterCategory, ProviderJson.TermCategory),
									],

			searchCategoryMovie		= Provider._CategoryMovie if category else ','.join(Provider._CategoryMovie),
			searchCategoryShow		= Provider._CategoryShow if category else ','.join(Provider._CategoryShow),

			extractHash				= Provider._AttributeHash,
			extractReleaseUploader	= Provider._AttributeUploader,
			extractFileName			= Provider._AttributeName,
			extractFileSize			= Provider._AttributeSize,
			extractSourceTime		= Provider._AttributeTime,
			extractSourceApproval	= Provider._AttributeStatus,
			extractSourceSeeds		= Provider._AttributeSeeds,
			extractSourceLeeches	= Provider._AttributeLeeches,
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processBefore(self, item):
		expectedImdb = self.parameterIdImdb()
		if expectedImdb:
			try: currentImdb = item[Provider._AttributeImdb]
			except: currentImdb = None
			if currentImdb and not currentImdb == expectedImdb: return ProviderJson.Skip

	def processHash(self, value, item, details = None, entry = None):
		# If no results are found, a single link with a 0s hash is returned. Skip it.
		if value  == '0000000000000000000000000000000000000000': return ProviderJson.Skip
		return value

	def processSourceApproval(self, value, item, details = None, entry = None):
		if self.customVerified():
			if not value == Provider._AttributeVip and not value == Provider._AttributeTrusted: return ProviderJson.Skip
		if value == Provider._AttributeVip: return ProviderJson.ApprovalExcellent
		elif value == Provider._AttributeTrusted: return ProviderJson.ApprovalGood
		elif value == Provider._AttributeMember: return ProviderJson.ApprovalBad
		else: return ProviderJson.ApprovalDefault
