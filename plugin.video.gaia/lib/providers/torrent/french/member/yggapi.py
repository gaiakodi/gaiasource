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
from lib.modules.tools import Regex
from lib.modules.network import Networker

class Provider(ProviderJson):

	_Link					= ['https://yggapi.eu']

	_TrackerDomain			= ['tracker.p2p-world.net', 'connect.maxp2p.org'] # https://yggapi.eu/docs#
	_TrackerCustom			= 'tracker'

	_PathSearch				= 'torrents'
	_PathDetails			= 'torrent/%s'
	_PathDownload			= 'torrent/%s/download'

	_LimitOffset			= 100 # The maximum number of results returned by a query.
	_LimitApproval			= 500

	_CategoryMovie			= [2183, 2181, 2178] # 2183 = Movie, 2181 = Documentary, 2178 = Animation
	_CategoryShow			= [2185, 2184, 2182, 2179] # 2185 = Show, 2184 = TV Show, 2182 = TV Program, 2179 = Animation Series

	_ParameterQuery			= 'q'
	_ParameterCategory		= 'category_id'
	_ParameterSort			= 'order_by'
	_ParameterSeeds			= 'seeders'
	_ParameterLimit			= 'per_page'
	_ParameterOffset		= 'page'
	_ParameterSeason		= 'season'
	_ParameterEpisode		= 'episode'
	_ParameterKey			= 'passkey'
	_ParameterTracker		= 'tracker_domain'

	_AttributeId			= 'id'
	_AttributeName			= 'title'
	_AttributeSeeds			= 'seeders'
	_AttributeLeeches		= 'leechers'
	_AttributeDownloads		= 'downloads'
	_AttributeSize			= 'size'
	_AttributeCategory		= 'category_id'
	_AttributeTime			= 'uploaded_at'
	_AttributeLink			= 'link'
	_AttributeHash			= 'hash'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		tracker = self.custom(id = Provider._TrackerCustom)
		ProviderJson.initialize(self,
			name					= 'YggApi',
			description				= '{name} is a new API wrapping around the original YggTorrent. {name} allows to bypass Cloudflare and can therefore be used with a VPN. {name} might not always return all the results from YggTorrent.',
			rank					= 4,
			performance				= ProviderJson.PerformanceBad,

			link					= Provider._Link,

			accountKey				= True,
			accountAuthentication	= {
										ProviderJson.ProcessMode : ProviderJson.AccountModeResolve,
										ProviderJson.ProcessFixed : {
											ProviderJson.RequestData : {
												Provider._ParameterKey : ProviderJson.TermAuthenticationKey,
												Provider._ParameterTracker : tracker,
											},
										},
									},

			# The tracker passkey cannot really be verified.
			# If the key is invalid, the .torrent file will still be created, just with an invalid/non-working key.
			# The only thing that can be verified is to make a dummy call to the download endpoint with the given key.
			# If the key is too short or not in the correct format, an error is returned and the verification fails.
			# Hence, the key format can be verified, but not wether the key is actually valid or not.
			accountVerification		= {
										ProviderJson.ProcessRequest : {
											ProviderJson.RequestPath : Provider._PathDownload % '0', # Some invalid torrent ID.
										},
										ProviderJson.ProcessValidate : {
											ProviderJson.RequestData : '^(?!{"detail".*"passkey")', # Not a JSON key-error response.
										},
									},

			custom					= {
										ProviderJson.SettingsId				: Provider._TrackerCustom,
										ProviderJson.SettingsLabel			: 'Torrent Tracker',
										ProviderJson.SettingsDefault		: 0,
										ProviderJson.SettingsType			: Provider._TrackerDomain,
										ProviderJson.SettingsDescription	: 'Use a specific torrent tracker for downloads.',
									},

			supportMovie			= True,
			supportShow				= True,
			supportPack				= True,

			offsetStart				= 1,
			offsetIncrease			= 1,

			# Searching these also finds others:
			#	saison: saisons
			#	integrale: intégrale
			#	integral: intégral
			#	trilogy: trilogie
			#	complete: complet
			queryYear				= False, # Many movies do not contain the year.

			formatEncode			= ProviderJson.FormatEncodeQuote,

			searchQuery				= {
										ProviderJson.RequestPath : Provider._PathSearch,
										ProviderJson.RequestData : {
											Provider._ParameterQuery	: ProviderJson.TermQuery,

											# Ignore these parameters. Add the season/episode numbers to the query string.
											#Provider._ParameterSeason	: ,
											#Provider._ParameterEpisode	: ,

											# Do not add a category. Search all categories and then filter in processItem().
											#Provider._ParameterCategory	: ProviderJson.TermCategory,

											Provider._ParameterSort		: Provider._ParameterSeeds,
											Provider._ParameterOffset	: ProviderJson.TermOffset,
											Provider._ParameterLimit	: Provider._LimitOffset,
										},
									},

			#searchCategoryMovie	= Provider._CategoryMovie,
			#searchCategoryShow		= Provider._CategoryShow,

			extractHash				= [ProviderJson.Details, Provider._AttributeHash],
			extractLink				= Provider._AttributeId,
			extractFileName			= Provider._AttributeName,
			extractFileSize			= Provider._AttributeSize,
			extractSourceTime		= Provider._AttributeTime,
			extractSourceApproval	= Provider._AttributeDownloads,
			extractSourceSeeds		= Provider._AttributeSeeds,
			extractSourceLeeches	= Provider._AttributeLeeches,
			extractIdItem			= Provider._AttributeId,
		)

	##############################################################################
	# EXTRACT
	##############################################################################

	def extractDetails(self, item):
		if item:
			id = item.get(Provider._AttributeId)
			if id: return Provider._PathDetails % id
		return ProviderJson.Skip

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			if len(items) < Provider._LimitOffset: return ProviderJson.Skip
		except: pass

	def processItem(self, item):
		if item:
			category = item.get(Provider._AttributeCategory)
			categories = Provider._CategoryShow if self.parameterMediaShow() else Provider._CategoryMovie
			if not category or not category in categories: return ProviderJson.Skip
		return item

	def processLink(self, value, item, details = None, entry = None):
		return Networker.linkJoin(self.linkCurrent(), Provider._PathDownload % value)

	def processSourceTime(self, value, item, details = None, entry = None):
		if value: return Regex.extract(data = value, expression = r'(\d{4}\-\d{2}\-\d{2}T\d{2}\:\d{2}\:\d{2})', cache = True)
		return value

	def processSourceApproval(self, value, item, details = None, entry = None):
		try:
			value = float(value) / Provider._LimitApproval
			return min(ProviderJson.ApprovalExcellent, value)
		except:
			return ProviderJson.ApprovalDefault
