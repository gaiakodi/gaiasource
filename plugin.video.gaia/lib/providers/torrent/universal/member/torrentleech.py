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
from lib.modules.network import Networker

class Provider(ProviderJson):

	# Important to add the "www" subdomain, otherwise the authentication cookie does not work.
	_Link					= ['https://www.torrentleech.org', 'https://www.torrentleech.cc', 'https://www.torrentleech.me', 'https://www.tleechreload.org', 'https://www.tlgetin.cc']
	_Mirror					= ['https://forums.torrentleech.org/t/issues-connecting-to-the-website/17734/2']

	_PathSearch				= 'torrents/browse/list/categories/%s/query/%s/orderby/seeders/order/desc/page/%s'
	_PathDownload			= 'download/%s/%s'
	_PathLogin				= 'user/account/login/'

	_LimitApproval			= 1000

	_CategoryMovie			= ['8', '9', '11', '12', '13', '14', '15', '29', '37', '43', '47'] # 8 = Cam, 9 = TS/TC, 11 = DVDRip/DVDScr, 12 = DVD-R, 13 = Bluray 14 = BlurayRip, 15 = Boxsets, 29 = Documentaries, 37 = WebRip, 43 = HDRip, 47 = 4K
	_CategoryShow			= ['26', '27', '32'] # 26 = Episodes, 27 = Boxsets, 32 = Episodes HD

	_CustomFreeleech		= 'freeleech'
	_CustomAnonymous		= 'anonymous'
	_CustomRar				= 'rar'

	_ParameterUsername		= 'username'
	_ParameterPassword		= 'password'

	_AttributeList			= 'torrentList'
	_AttributeId			= 'fid'
	_AttributeName			= 'name'
	_AttributeFile			= 'filename'
	_AttributeSize			= 'size'
	_AttributeTime			= 'addedTimestamp'
	_AttributeDownloads		= 'completed'
	_AttributeUploader		= 'uploader'
	_AttributeSeeds			= 'seeders'
	_AttributeLeeches		= 'leechers'
	_AttributeImdb			= 'imdbID'
	_AttributeTags			= 'tags'
	_AttributePageNumber	= 'page'
	_AttributePageFound		= 'numFound'
	_AttributePageCount		= 'perPage'

	_AttributeFreeleech		= 'freeleech'
	_AttributeNonscene		= 'nonscene'
	_AttributeRar			= 'rar'

	_ExpressionLogout		= r'(logout)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderJson.initialize(self,
			name					= 'TorrentLeech',
			description				= '{name} is a private torrent tracker and indexer. An account is required to use the provider, but registration is free. {name} has a required seeding ratio, but also has a free leeching option that does not count towards your download ratio. {name} does not contain torrent hashes and can therefore not be checked against debird caches. They also impose IP restrictions and some debrid services might not be able to download the torrents.',
			rank					= 5,
			performance				= ProviderJson.PerformanceExcellent,

			link					= Provider._Link,
			mirror					= Provider._Mirror,

			accountUsername			= True,
			accountPassword			= True,
			accountAuthentication	= {
										ProviderJson.ProcessMode : ProviderJson.AccountModeAll,
										ProviderJson.ProcessRequest : {
											ProviderJson.RequestMethod : ProviderJson.RequestMethodPost,
											ProviderJson.RequestPath : Provider._PathLogin,
											ProviderJson.RequestData : {
												Provider._ParameterUsername : ProviderJson.TermAuthenticationUsername,
												Provider._ParameterPassword : ProviderJson.TermAuthenticationPassword,
											},
										},
										ProviderJson.ProcessExtract : {
											ProviderJson.RequestCookies : ProviderJson.RequestCookiePhp,
										},
										ProviderJson.ProcessValidate : { # TorrentLeech always returns a PHP session cookie, even if not logged in. Manually check if the login was successful.
											ProviderJson.RequestData : Provider._ExpressionLogout,
										},
									},

			custom					= [
										{
											ProviderJson.SettingsId				: Provider._CustomFreeleech,
											ProviderJson.SettingsLabel			: 'Freeleech Only',
											ProviderJson.SettingsDefault		: False,
											ProviderJson.SettingsType			: ProviderJson.SettingsTypeBoolean,
											ProviderJson.SettingsDescription	: 'Only retrieve freelech torrents which will not count towards your downloaded data amount. If you download a torrent your ratio will not be negatively affected. Seeding, however, will accrue the normal amount of data.',
										},
										{
											ProviderJson.SettingsId				: Provider._CustomRar,
											ProviderJson.SettingsLabel			: 'Exclude RAR',
											ProviderJson.SettingsDefault		: False,
											ProviderJson.SettingsType			: ProviderJson.SettingsTypeBoolean,
											ProviderJson.SettingsDescription	: 'Exclude RAR archives. Some debrid services might not be able to extract RAR archives, causing streaming to fail.',
										},
										{
											ProviderJson.SettingsId				: Provider._CustomAnonymous,
											ProviderJson.SettingsLabel			: 'Exclude Anonymous',
											ProviderJson.SettingsDefault		: False,
											ProviderJson.SettingsType			: ProviderJson.SettingsTypeBoolean,
											ProviderJson.SettingsDescription	: 'Exclude torrents that were uploaded by anonymous users.',
										},
									],
			customVerified			= True,

			supportMovie			= True,
			supportShow				= True,
			supportPack				= True,

			offsetStart				= 1,
			offsetIncrease			= 1,

			formatEncode			= ProviderJson.FormatEncodeQuote,

			searchQuery				= Provider._PathSearch % (ProviderJson.TermCategory, ProviderJson.TermQuery, ProviderJson.TermOffset),
			searchCategoryMovie		= ','.join(Provider._CategoryMovie),
			searchCategoryShow		= ','.join(Provider._CategoryShow),

			extractList				= Provider._AttributeList,
			extractLink				= [[Provider._AttributeId], [Provider._AttributeFile]],
			extractFileName			= Provider._AttributeName,
			extractFileSize			= Provider._AttributeSize,
			extractReleaseUploader	= Provider._AttributeUploader,
			extractSourceTime		= Provider._AttributeTime,
			extractSourceApproval	= Provider._AttributeDownloads,
			extractSourceSeeds		= Provider._AttributeSeeds,
			extractSourceLeeches	= Provider._AttributeLeeches,
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			number = data[Provider._AttributePageNumber]
			found = data[Provider._AttributePageFound]
			count = data[Provider._AttributePageCount]
			if (number * count) >= found: return ProviderJson.Skip
		except: self.logError()

	def processBefore(self, item):
		try: currentImdb = item[Provider._AttributeImdb]
		except: currentImdb = None
		if currentImdb and not currentImdb == 'tt': # Some results just have "tt" as the ID.
			expectedImdb = self.parameterIdImdb()
			if expectedImdb and not expectedImdb == currentImdb: return ProviderJson.Skip

		try:
			verified = self.customVerified()
			rar = self.custom(id = Provider._CustomRar)
			freeleech = self.custom(id = Provider._CustomFreeleech)
			if verified or rar or freeleech:
				tags = [i.lower() for i in item[Provider._AttributeTags]]
				if freeleech and not Provider._AttributeFreeleech in tags: return ProviderJson.Skip
				elif verified and Provider._AttributeNonscene in tags: return ProviderJson.Skip
				elif rar and Provider._AttributeRar in tags: return ProviderJson.Skip
		except: pass

	def processLink(self, value, item, details = None, entry = None):
		return Networker.linkJoin(self.linkCurrent(), Provider._PathDownload % (value[0], value[1]))

	def processReleaseUploader(self, value, item, details = None, entry = None):
		if self.custom(id = Provider._CustomAnonymous) and not value: return ProviderJson.Skip
		return value

	def processSourceApproval(self, value, item, details = None, entry = None):
		try:
			value = float(value) / Provider._LimitApproval
			return min(ProviderJson.ApprovalExcellent, value)
		except:
			return ProviderJson.ApprovalDefault
