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

# https://www.reddit.com/r/Piracy/wiki/megathread/all_purpose/
# https://torrends.to/proxy/
# https://myds.cloud/%E8%B5%84%E6%96%99/%E7%A3%81%E5%8A%9B%E6%90%9C%E7%B4%A2
# https://github.com/fmhy/FMHY/wiki/%F0%9F%8C%80-Torrenting

import os
import sys

from lib.modules.tools import Tools, Logger, System, Media, Time, Language, Converter, Settings, Regex, Math, Hardware, Platform
from lib.modules.interface import Format, Translation
from lib.modules.stream import Stream
from lib.modules.network import Networker, Container
from lib.modules.concurrency import Pool, Lock, Semaphore, Premaphore

class ProviderBase(object):

	# Supported languages by the provider structure.
	# When adding a new language, the following must be done:
	#	1. Add the language to the Languages list below.
	#	2. Add a new Mode enum and functions below.
	#	3. Add the language to tools.Language.Sets['providers'].
	#	4. Add query words to web.py -> ProviderWeb.
	#	5. Add show detection keywords for the language to stream.py -> Stream.
	Languages							= [
											Language.CodeUniversal,
											Language.CodeEnglish,
											Language.CodeFrench,
											Language.CodeGerman,
											Language.CodeDutch,
											Language.CodeSpanish,
											Language.CodePortuguese,
											Language.CodeItalian,
											Language.CodeRussian,
										]

	# Type - must have the same value as the directory name
	TypeUnknown							= None
	TypeSpecial							= 'special'
	TypeLocal							= 'local'
	TypePremium							= 'premium'
	TypeCenter							= 'center'
	TypeTorrent							= 'torrent'
	TypeUsenet							= 'usenet'
	TypeHoster							= 'hoster'
	TypeExternal						= 'external'
	Types								= [TypeSpecial, TypeLocal, TypePremium, TypeCenter, TypeTorrent, TypeUsenet, TypeHoster, TypeExternal]
	TypesData							= {
											TypeSpecial		: {'enabled' : True,	'label' : 35156},
											TypeLocal		: {'enabled' : True,	'label' : 35356},
											TypePremium		: {'enabled' : True,	'label' : 35357},
											TypeCenter		: {'enabled' : False,	'label' : 35387},
											TypeTorrent		: {'enabled' : True,	'label' : 35327},
											TypeUsenet		: {'enabled' : True,	'label' : 33044},
											TypeHoster		: {'enabled' : True,	'label' : 33263},
											TypeExternal	: {'enabled' : True,	'label' : 33045},
										}

	# Mode - must have the same value as the directory name
	ModeUnknown							= None
	ModeUniversal						= 'universal'
	ModeAnime							= 'anime'
	ModeEnglish							= 'english'
	ModeFrench							= 'french'
	ModeGerman							= 'german'
	ModeDutch							= 'dutch'
	ModeSpanish							= 'spanish'
	ModePortuguese						= 'portuguese'
	ModeItalian							= 'italian'
	ModeRussian							= 'russian'
	Modes								= [ModeUniversal, ModeAnime, ModeEnglish, ModeFrench, ModeGerman, ModeDutch, ModeSpanish, ModePortuguese, ModeItalian, ModeRussian]
	ModesData							= {
											ModeUniversal	: {'enabled' : True,	'label' : 35355},
											ModeAnime		: {'enabled' : True,	'label' : 35565},
											ModeEnglish		: {'enabled' : True,	'label' : 35801},
											ModeFrench		: {'enabled' : True,	'label' : 35033},
											ModeGerman		: {'enabled' : True,	'label' : 35797},
											ModeDutch		: {'enabled' : True,	'label' : 35798},
											ModeSpanish		: {'enabled' : True,	'label' : 35799},
											ModePortuguese	: {'enabled' : True,	'label' : 35800},
											ModeItalian		: {'enabled' : True,	'label' : 35389},
											ModeRussian		: {'enabled' : True,	'label' : 35353},
										}

	# Access - must have the same value as the directory name
	AccessUnknown						= None
	AccessOpen							= 'open'
	AccessMember						= 'member'
	AccessOffline						= 'offline'
	AccessDistributed					= 'distributed'
	Accesses							= [AccessOpen, AccessMember, AccessOffline, AccessDistributed]
	AccessesData						= {
											AccessOpen			: {'enabled' : True,	'label' : 33046},
											AccessMember		: {'enabled' : True,	'label' : 33047},
											AccessOffline		: {'enabled' : True,	'label' : 36355},
											AccessDistributed	: {'enabled' : True,	'label' : 33941},
										}

	# Media
	MediaUnknown						= None
	MediaMovie							= Media.Movie
	MediaShow							= Media.Show

	# Container
	ContainerSingular					= 'link'
	ContainerPlural						= 'links'
	ContainerTorrentSingular			= 'torrent'
	ContainerTorrentPlural				= 'torrents'
	ContainerUsenetSingular				= 'NZB'
	ContainerUsenetPlural				= 'NZBs'

	# Keyword
	# Must correspond with the indexes in settings.xml.
	KeywordNone							= 0
	KeywordQuick						= 1
	KeywordFull							= 2

	# Verify
	VerifySuccess						= 'success'
	VerifyFailure						= 'failure'
	VerifyLimited						= 'limited'
	VerifyOptional						= 'optional'

	VerifyConnection					= 'connection'
	VerifyRequest						= 'request'
	VerifyCloudflare					= 'cloudflare'
	VerifyCertificate					= 'certificate'

	VerifyType							= 'type'
	VerifyReason						= 'reason'
	VerifyError							= 'error'

	VerifyDomain						= 'domain'
	VerifyAccount						= 'account'
	VerifyScrape						= 'scrape'

	VerifyOrder							= [VerifyDomain, VerifyAccount, VerifyScrape]
	VerifyValues						= [VerifySuccess, VerifyLimited, VerifyFailure]
	VerifyLabels						= {VerifySuccess : 33025, VerifyLimited : 33024, VerifyFailure : 33023, VerifyOptional : 35323, VerifyConnection : 33404, VerifyRequest : 35261, VerifyCloudflare : 35689, VerifyCertificate : 35386, VerifyError : 35311, VerifyDomain : 33500, VerifyAccount : 33339, VerifyScrape : 35514}
	VerifyColors						= {VerifySuccess : 'colorExcellent', VerifyLimited : 'colorMedium', VerifyFailure : 'colorBad', VerifyOptional : 'colorSpecial'}

	# Time
	TimeDefault							= 60
	TimeFactorFull						= 1.00
	TimeFactorScrape					= 0.95			# Timeout factor for main outer scrape function.
	TimeFactorInternal					= 0.90			# Timeout factor for internal functions.
	TimeRequest							= 30			# The timeout of network requests. This is NOT the total time requests can take, but instead the time it takes for the server to respond on the intital request. Do not make this too high, otherwise requests might hang.

	# Concurrency
	ConcurrencyTotal					= 0				# How many providers are enabled.
	ConcurrencyTasks					= 0				# How many providers are allowed to run concurrently.
	ConcurrencyBinge					= None
	ConcurrencyLock						= None
	ConcurrencyData						= {}

	# Rank
	RankLimit							= 5
	RankMaximum							= 3				# Maximum rank when calulating the rank dynamically. Used by exterenal providers.
	RankMinimum							= 1				# Minimum rank when calulating the rank dynamically. Used by exterenal providers.
	RankDefault							= 2

	# Status
	StatusOperational					= 'operational'	# The provider works as expected.
	StatusCloudflare					= 'cloudflare'	# The provider is blocked by Cloudflare, typically when using a VPN.
	StatusImpaired						= 'impaired'	# The provider is impaired, excluding Cloudflare issues, inaccessible by some VPNs, or other restrictions. Impaired providers are show in a light font in the manager dialog.
	StatusDead							= 'dead'		# The provider is dead, such as having no working domain or the website has closed down. Dead providers are disabled by default and are show in an italic font in the manager dialog.
	StatusHidden						= 'hidden'		# The provider is completely ignored as if it does not exist. Hidden providers are not shown in the manager dialog at all.
	StatusDefault						= StatusOperational
	StatusLabels						= {StatusOperational : 33430, StatusCloudflare : 35689, StatusImpaired : 33431, StatusDead : 36357, StatusHidden : 36358}
	StatusDescriptions					= {StatusOperational : 36359, StatusCloudflare : 36806, StatusImpaired : 36360, StatusDead : 36361, StatusHidden : 36362}

	# Process
	ProcessRequest						= 'request'
	ProcessExtract						= 'extract'
	ProcessFixed						= 'fixed'
	ProcessValidate						= 'validate'
	ProcessFormat						= 'format'
	ProcessMode							= 'mode'
	ProcessAuthorization				= 'authorization'
	ProcessIterations					= 'iterations'

	# Request
	RequestMethod						= 'method'
	RequestMethodGet					= Networker.MethodGet
	RequestMethodPost					= Networker.MethodPost

	RequestType							= 'type'
	RequestTypeNone						= Networker.DataNone
	RequestTypePost						= Networker.DataPost
	RequestTypeJson						= Networker.DataJson
	RequestTypeForm						= Networker.DataForm
	RequestTypeMulti					= Networker.DataMulti

	RequestHeaderUserAgent				= Networker.HeaderUserAgent
	RequestHeaderRequestToken			= Networker.HeaderRequestToken
	RequestHeaderReferer				= Networker.HeaderReferer
	RequestHeaderLocation				= Networker.HeaderLocation

	RequestCurve						= 'curve'
	RequestCurvePrime256v1				= Networker.CurvePrime256v1
	RequestCurveSecp384r1				= Networker.CurveSecp384r1
	RequestCurveSecp512r1				= Networker.CurveSecp512r1

	RequestCookiePhp					= Networker.CookiePhp

	RequestLink							= 'link'
	RequestSubdomain					= 'subdomain'
	RequestPath							= 'path'
	RequestData							= 'data'
	RequestCookies						= 'cookies'
	RequestHeaders						= 'headers'

	# Account
	AccountOptional						= 'optional'

	AccountInputDialog					= 'dialog' # Shows an input dialog to ask the user for the account details.
	AccountInputCustom					= 'custom' # Calls a custom function to handle the authentication.

	AccountTypeUsername					= 'username'
	AccountTypeEmail					= 'email'
	AccountTypePassword					= 'password'
	AccountTypeKey						= 'key'
	AccountTypeOther					= 'other'

	AccountTypeOrder					= [AccountTypeOther, AccountTypeUsername, AccountTypeEmail, AccountTypePassword, AccountTypeKey]
	AccountTypeLabels					= {AccountTypeUsername : 33267, AccountTypeEmail : 32304, AccountTypePassword : 32307, AccountTypeKey : 33214, AccountTypeOther : 33493}

	# Setting - Category
	SettingsCategoryScrape				= 'scrape'
	SettingsCategoryCustom				= 'custom'

	# Setting - Attribute
	SettingsId							= 'id'
	SettingsLabel						= 'label'
	SettingsDefault						= 'default'
	SettingsType						= 'type'
	SettingsMode						= 'mode'
	SettingsFormat						= 'format'
	SettingsDescription					= 'description'
	SettingsRefresh						= 'refresh'

	# Setting - Value
	SettingsValueNone					= 'none'
	SettingsValueDefault				= 'default'
	SettingsValueGeneral				= 'general'
	SettingsValueCustom					= 'custom'
	SettingsValueUnlimited				= 'unlimited'
	SettingsValueAutomatic				= 'automatic'
	SettingsValueUnauthorized			= 'unauthorized'
	SettingsValueZero					= 'zero'

	# Setting - Type
	SettingsTypeCustom					= 'custom'
	SettingsTypeBoolean					= 'boolean'
	SettingsTypeNumber					= 'number'
	SettingsTypeString					= 'string'
	SettingsTypePath					= 'path'

	# Settings - Format
	SettingsFormatDuration				= 'duration'	# Assumes the user input is in number of seconds.
	SettingsFormatDays					= 'days'		# Assumes the user input is in number of days.
	SettingsFormatSeconds				= 'seconds'		# Assumes the user input is in number of seconds.
	SettingsFormatSize					= 'size'		# Assumes the user input is in MB.
	SettingsFormatPeers					= 'peers'
	SettingsFormatSeeds					= 'seeds'
	SettingsFormatLeeches				= 'leeches'
	SettingsFormatLinks					= 'links'
	SettingsFormatRank					= 'rank'
	SettingsFormatQuery					= 'query'
	SettingsFormatPage					= 'page'
	SettingsFormatRequest				= 'request'
	SettingsFormatVersion				= 'version'

	# Settings - Path
	SettingsPathFile					= 'file'		# Readable file path.
	SettingsPathRead					= 'read'		# Readable directory path.
	SettingsPathWrite					= 'write'		# Writable directory path.

	# Settings - Global

	SettingsGlobalLimitTime				= 'scrape.limit.time'
	SettingsGlobalLimitQuery			= 'scrape.limit.query'
	SettingsGlobalLimitPage				= 'scrape.limit.page'
	SettingsGlobalLimitRequest			= 'scrape.limit.request'

	SettingsGlobalSaveStream			= 'scrape.save.stream'
	SettingsGlobalSaveCache				= 'scrape.save.cache'
	SettingsGlobalSaveExpression		= 'scrape.save.expression'

	SettingsGlobalPackEnabled			= 'scrape.pack.enabled'
	SettingsGlobalPackMovie				= 'scrape.pack.movie'
	SettingsGlobalPackShow				= 'scrape.pack.show'
	SettingsGlobalPackSeason			= 'scrape.pack.season'

	SettingsGlobalMirrorEnabled			= 'provider.mirror.domain'
	SettingsGlobalMirrorLimit			= 'provider.mirror.domain.limit'

	SettingsGlobalUnblockEnabled		= 'provider.mirror.unblock'
	SettingsGlobalUnblockType			= 'provider.mirror.unblock.type'
	SettingsGlobalUnblockLink			= 'provider.mirror.unblock.link'
	SettingsGlobalUnblockFormat			= 'provider.mirror.unblock.format'

	SettingsGlobalTitleEnabled			= 'scrape.query.title'
	SettingsGlobalTitleCharacter		= 'scrape.query.title.character'
	SettingsGlobalTitleOriginal			= 'scrape.query.title.original'
	SettingsGlobalTitleNative			= 'scrape.query.title.native'
	SettingsGlobalTitleLocal			= 'scrape.query.title.local'
	SettingsGlobalTitleAlias			= 'scrape.query.title.alias'
	SettingsGlobalTitleLanguage			= 'scrape.query.title.language'

	SettingsGlobalKeywordEnabled		= 'scrape.query.keyword'
	SettingsGlobalKeywordEnglish		= 'scrape.query.keyword.english'
	SettingsGlobalKeywordOriginal		= 'scrape.query.keyword.original'
	SettingsGlobalKeywordNative			= 'scrape.query.keyword.native'
	SettingsGlobalKeywordCustom			= 'scrape.query.keyword.custom'
	SettingsGlobalKeywordLanguage		= 'scrape.query.keyword.language'

	SettingsGlobalYearEnabled			= 'scrape.query.year'

	# Scrape
	ScrapePriority						= 'priority'
	ScrapeTermination					= 'termination'
	ScrapeTime							= 'time'
	ScrapeQuery							= 'query'
	ScrapePage							= 'page'
	ScrapeRequest						= 'request'

	# Custom
	CustomVersion						= 'version'		# Scraper version.
	CustomSize							= 'size'		# Minimum file size.
	CustomTime							= 'time'		# Maximum age.
	CustomPeers							= 'peers'		# Minimum torrent peers.
	CustomSeeds							= 'seeds'		# Minimum torrent seeds.
	CustomLeeches						= 'leeches'		# Minimum torrent leeches.
	CustomSearch						= 'search'		# Search by ID or title.
	CustomCategory						= 'category'	# Separate or combined categories.
	CustomVerified						= 'verified'	# Uploaded by verified users.
	CustomSpam							= 'spam'		# Remove spam.
	CustomAdult							= 'adult'		# Remove adult content.
	CustomPassword						= 'password'	# Remove password protected files.
	CustomIncomplete					= 'incomplete'	# Remove incomplete files (missing NZB parts).

	CustomSearchId						= 'id'
	CustomSearchTitle					= 'title'

	# Version
	# Use strings instead of integers, since int dict keys get converted to strings during JSON conversion.
	Version1							= '1'
	Version2							= '2'
	Version3							= '3'
	Version4							= '4'
	Version5							= '5'
	Version6							= '6'
	Version7							= '7'
	Version8							= '8'
	Version9							= '9'
	VersionDefault						= '1'	# During provider intialization if settings were not yet initialized.
	VersionAutomatic					= '-'	# Special automatic version.
	VersionNone							= None	# No version specified.

	# Prepare
	PrepareFirst						= 0
	PrepareLast							= -1
	PrepareDefault						= None

	# Approval
	ApprovalExcellent					= 1.0
	ApprovalGood						= 0.8
	ApprovalMedium						= 0.6
	ApprovalPoor						= 0.4
	ApprovalBad							= 0.2
	ApprovalDefault						= 0.5

	# Performance
	# The following assignment should be used.
	# Add PerformanceStep if provider is really good. Subtract PerformanceStep if the provider has major problems.
	#	JSON:
	#		Single request (not multiple categories to search): PerformanceExcellent
	#		Single request + authentication request: PerformanceGood
	#		Multiple request (multiple categories to search, check that they are not joined into one catergory): PerformanceMedium
	#		Detailed request (requires details sub-requests): PerformanceBad
	#	HTML:
	#		Single request (not multiple categories to search): PerformanceGood
	#		Multiple request (multiple categories to search, check that they are not joined into one catergory): PerformancePoor
	#		Detailed request (requires details sub-requests): PerformanceBad

	Performance0						= 0.0
	Performance1						= 0.1
	Performance2						= 0.2
	Performance3						= 0.3
	Performance4						= 0.4
	Performance5						= 0.5
	Performance6						= 0.6
	Performance7						= 0.7
	Performance8						= 0.8
	Performance9						= 0.9
	Performance10						= 1.0

	PerformanceBad						= Performance1
	PerformancePoor						= Performance3
	PerformanceMedium					= Performance5
	PerformanceGood						= Performance7
	PerformanceExcellent				= Performance9

	PerformanceDefault					= Performance5
	PerformanceStep						= 0.1
	PerformanceHalf						= 0.05

	PerformanceLabels					= {PerformanceBad : 35244, PerformancePoor : 35243, PerformanceMedium : 33999, PerformanceGood : 35242, PerformanceExcellent : 35241}

	# Unblock
	UnblockTypeCustom					= 0
	UnblockTypeProxybitcasa				= 1
	UnblockTypeUnblockitapp				= 2
	UnblockTypeUnblockedpwgithubio		= 3
	UnblockTypeUnblockiteu				= 4
	UnblockTypeUnblockedis				= 5
	UnblockTypeUnblockninjacom			= 6

	UnblockFormat0						= 0	# Internal Gaia IDs.
	UnblockFormat1						= 1	# unblockninja.com
	UnblockFormat2						= 2 # unblockit.app / unblocked-pw.github.io
	UnblockFormat3						= 3 # unblockit.eu / unblocked.is
	UnblockFormat4						= 4 # proxybit.casa

	UnblockSettings						= None
	UnblockData							= {
											UnblockTypeProxybitcasa			: {'link' : 'https://proxybit.casa',			'format' : UnblockFormat4},
											UnblockTypeUnblockitapp			: {'link' : 'https://unblockit.app',			'format' : UnblockFormat2},
											UnblockTypeUnblockedpwgithubio	: {'link' : 'https://unblocked-pw.github.io',	'format' : UnblockFormat2},
											UnblockTypeUnblockiteu			: {'link' : 'https://unblockit.eu',				'format' : UnblockFormat3},
											UnblockTypeUnblockedis			: {'link' : 'https://unblocked.is',				'format' : UnblockFormat3},
											}

	# Result
	ResultLock							= {}
	ResultFound							= {}
	ResultStreams						= {}
	ResultCore							= None
	ResultFilters						= None

	# Scrape
	ScrapeCountQuery					= {}
	ScrapeCountPages					= {}
	ScrapeCountRequests					= {}

	# Settings
	SettingsDataBase 					= {
											'limit' : {
												ScrapeTime : None,
												ScrapeQuery : None,
												ScrapePage : None,
												ScrapeRequest : None,
											},
											'save' : {
												'stream' : None,
												'cache' : None,
												'expression' : None,
											},
											'pack' : {
												'enabled' : None,
												'movie' : None,
												'show' : None,
												'season' : None,
											},
											'mirror' : {
												'enabled' : None,
												'limit' : None,
											},
											'unblock' : {
												'enabled' : None,
												'type' : None,
												'link' : None,
												'format' : None,
											},
											'title' : {
												'enabled' : None,
												'time' : None,
												'character' : None,
												'original' : None,
												'native' : None,
												'local' : None,
												'alias' : None,
												'language' : None,
											},
											'keyword' : {
												'enabled' : None,
												'english' : None,
												'original' : None,
												'native' : None,
												'custom' : None,
												'language' : None,
											},
											'year' : {
												'enabled' : None,
											},
										}
	SettingsData						= Tools.copy(SettingsDataBase)

	# Priority
	PriorityEnabled						= True
	PriorityLocks						= {}
	PriorityLock						= Lock()
	PriorityDelay						= 0.1
	PriorityChunk						= [250, 100] # More details in priorityChunks().
	PriorityChunked						= None
	PriorityTimeout						= 60 # 1 minute.

	# Query
	QueryId								= {}
	QueryDone							= {}

	# Other
	Link								= {}
	Redirect							= {}
	Timer								= {}
	Times								= {}
	Stop								= {}
	Execution							= []
	Statistics							= {}
	Handlers							= {}

	Skip								= '[GAIASKIP]'
	Details								= '[GAIADETAILS]'
	Entries								= '[GAIAENTRIES]'

	ExpressionMagnet					= r'(magnet(?:\:|%3A).*)'
	ExpressionTorrent					= r'(\.torrent)'
	ExpressionProxy						= r'(proxy|unblock|bypass|immunicity|nocensor|prox\d|p4y)'
	ExpressionSha1						= r'([a-f0-9]{40})'
	ExpressionSha256					= r'([a-f0-9]{64})'
	ExpressionSha						= r'([a-f0-9]{40}|[a-f0-9]{64})'

	def __init__(self,
		id				= None,		# The ID of the provider. If not provided, the ID is determined from the file name.

		data			= None,		# The data.
		dataClear		= True,		# Clear/initialize the settings.

		settings		= None,		# The settings.
		settingsClear	= True,		# Clear/initialize the settings.

		initialize		= False,	# Immediately initialize the provider (note that the settings are not loaded yet if they were not passed to the constructor).
	):
		self.log = self._log
		self.logError = self._logError
		self.logMessage = self._logMessage

		self.mLock = Lock()

		self.mVerify = None
		self.mParameters = {}

		if dataClear: self.dataClear()
		if data: self.dataUpdate(data)
		else: self.initializeCore(id = id)

		if settingsClear: self.settingsDataClear()
		if settings: self.settingsDataUpdate(settings)

		if initialize: self.initialize()
		self.stopInitialize()

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self,
		name					= None,			# The interface name of the provider. If not provided, the ID is used as name.
		description				= None,			# An optional description to explain the provider and provide additional notes.
		link					= None,			# The list of default links used during scraping.
		mirror					= None,			# A link or list of links to pages that list mirror sites. This is displayed to the user in the help section.
		unblock					= None,			# A dictionary with UnblockFormatX keys and the subdomain aas value.
		resolver				= None,			# Whether or not the provider has a custom resolve() implementation.

		enabled					= None,			# Whether or not the provider is enabled by default.
		rank					= None,			# The star ranking (out of 5) indicating how good the provider is (speed, reliability, number of links, JSON vs HTML, etc).
		performance				= None,			# The overall performance of the provider between 0.0 (very slow, many sub-requests, delays, HTML, etc) and 1.0 (fast, no sub-requests, JSON, etc). The inverse (1.0 - performance) is used for provider optimization. For instance, a low-end device will only enable fast providers.
		optimization			= None,			# Whether or not to enable the provider during optimization. If True, the provider is always enabled, if False, it is always disabled, irrespective of the user's device or other parameters. If left at None, a ranking is calculated (based on the provider's performance and rank) which is used to enable/disable the provider.
		status					= None,			# The status of the provider, such as being fully operational, impaired, or dead.

		language				= None,			# The language of the provider. If not provided, the language is determined from the folder structure.
		developer				= None,			# Whether or not the provider is only availble for developers.

		addonId					= None,			# The internal ID of addon the provider originates from. If not provided, Gaia is assumed.
		addonName				= None,			# The name of addon the provider originates from. If not provided, Gaia is assumed.
		addonRank				= None,			# The star ranking  of addon the provider originates from.
		addonSettings			= None,			# Whether or not the addon has an external addon settings dialog.
		addonPrepare			= None,			# An integer priority for the order in which external providers are initialized. Check Manager.providersPrepare() for more info.
		addonModuleScraper		= None,			# The Kodi module ID of the addon the provider originates from. If not provided, Gaia is assumed.
		addonModuleParent		= None,			# The Kodi module ID of the parent addon the provider originates from. A script.module.xxx addon might have a parent plugin.video.xxx addon and might read settings from the parent addon (eg Oath).
		addonModuleSettings		= None,			# The Kodi module ID of the addon the has the settings dialog.

		supportNiche			= None,			# A list of niches supported by the provider. Eg: Media.Anime
		supportMovie			= None,			# Whether or not movie searches are supported.
		supportShow				= None,			# Whether or not show searches are supported.
		supportSpecial			= None,			# Whether or not special episode searches are supported.
		supportPack				= None,			# Whether or not pack searches are supported. Overarching parameter for all pack types.
		supportPackMovie		= None,			# Whether or not movie pack searches are supported.
		supportPackShow			= None,			# Whether or not show pack searches are supported.
		supportPackSeason		= None,			# Whether or not season pack searches are supported.

		# Each attribute can have one of the following values:
		#	None: Do not use the account attribute.
		#	True: Same as AccountInputDialog.
		#	AccountInputDialog: Ask the user for manual input which is stored in the provider settings.
		#	AccountInputCustom: Initiates a custom account process. Subclasses must implement accountCustomEnabled(), accountSettingsLabel(), and accountCustomDialog().
		#	String: A settings ID. The value is directly retrieved from and saved to the normal settings.
		accountOptional			= None,			# Set to True, so that the provider can be used with or without an account. For instance, adding an account can increase API rate limits.
		accountUsername			= None,			# Account username.
		accountEmail			= None,			# Account email.
		accountPassword			= None,			# Account password.
		accountKey				= None,			# Account API key.
		accountOther			= None,			# Other account authentication.

		scrapePriority			= None,			# The default priority that determines the order in which providers are scraped.
		scrapeTermination		= None,			# The default number of links after which the scraping process is terminated.
		scrapeTime				= None,			# The default scraping timeout. If None, the global scraping timeout is used.
		scrapeQuery				= False,		# The default maximum number of queries to scrape. If False, the provider does not support query limits. If None, the global query limit is used.
		scrapePage				= False,		# The default maximum number of pages to scrape. If False, the provider does not support page limits. If None, the global page limit is used.
		scrapeRequest			= False,		# The default maximum number of requests/queries to execute during scraping. If False, the provider does not support request limits. If None, the global request limit is used.

		# A list of custom settings for the provider.
		# Each setting is a dictionary with the following attributes:
		#	id (string): The ID to access the setting with.
		#	label (string): The label of the setting to display in the interface.
		#	type (enum/list): The data type (boolean, number, string) of the setting. If a list of values are provided, the user can choose an option from this list. The list can be a list of strings, or a list of dictionaries, where the dict-key is the internal value, and the dict-value is the label.
		#	default (mixed): The default value of the setting. If "type" is a string/int list, the default is the index. If "type" is a dict list, the default is the dict's key.
		#	format (string/dict): Optional formatting string to format the value before displaying it in the interface. Eg: use '%d Days' to change the value 123 to "123 Days". Or use one of the Format enums for special/advanced formatting.
		#		If it is a dictionary, the key is the custom setting's value, and the value is the label to display instead.
		#			If dict-key is SettingsValueGeneral: The default formatting to use for general values.
		#			If dict-key is SettingsValueNone: Special formatting to use for the None value.
		#			If dict-key is SettingsValueDefault: Special formatting to use for the default value.
		#			If dict-key any other: Special formatting to use for this specific value.
		#			If dict-value is SettingsValueNone: Show the italic keyword "None".
		#			If dict-value is SettingsValueDefault: Show the italic keyword "Default".
		#			If dict-value is SettingsValueCustom: Show the italic keyword "Custom".
		#			If dict-value is SettingsValueUnlimited: Show the italic keyword "Unlimited".
		#			If dict-value is SettingsValueAutomatic: Show the italic keyword "Automatic".
		#			If dict-value is Format enums: Show a specially/advanced formatted string according to the enum.
		#			If dict-value is string: Percentage escaped string is used for formatting. Eg: '%d Days'
		#			If dict-value is string-list: Same as string, but the first value is for singular, second value is for plural label. Eg: ['%d Day', '%d Days']
		#			If dict-value is integer: A label from strings.po. Can be percentage escaped for replacements. Eg: 34567
		#			If dict-value is integer-list: A label from strings.po. Same as integer, but the first value is for singular, second value is for plural label. Eg: [34567, 34568]
		#	description (string): A help label describing what the setting does.
		#	refresh (string/True): If the setting is changed, clear the settings and reinitialize the provider (eg: change version might require the links/domains to change accordingly). If True, clear all settings. If a string, clear a specific key in mSettings.
		custom					= None,
		customSize				= None,
		customTime				= None,
		customPeers				= None,
		customSeeds				= None,
		customLeeches			= None,
		customSearch			= None,
		customCategory			= None,
		customVerified			= None,
		customSpam				= None,
		customAdult				= None,
		customPassword			= None,
		customIncomplete		= None,

		# A list of different versions of the website. Versions can be given in the following formats.
		#	Dict: A "custom" dict like other custom settings. Does not require all attributes, only those that need to be overwritten.
		#	List of dicts: The dict-key is the value, the dict-value is the label to display.
		#	List of strings: The strings are considered the version ID and label. The first element is assumed to be the default.
		#	List of enums: The value are considered the ID (eg: Version1). The labels are "Version #". The first element is assumed to be the default.
		#	Integer: Generates a number of versions which will have the same format as list of integers. Eg: 5 will generate five versions, from 1 to 5.
		customVersion			= None,

		cacheTime				= None,
	):
		try:
			id = self.id()
			type = self.type()
			mode = self.mode()
			access = self.access()

			if not name and id: name = id.capitalize()
			if enabled is None: enabled = True
			if rank is None: rank = ProviderBase.RankDefault
			if performance is None: performance = ProviderBase.PerformanceDefault
			if status is None: status = ProviderBase.StatusDefault
			if status == ProviderBase.StatusDead: enabled = False
			if developer is None: developer = False

			# Assume Anime/Donghua support if it is an Anime provider.
			# Also include general Japanese/Chinese content, since Tokyotosho also has a "Drama" category for content that is not really anime (eg: "Kamen Rider").
			if supportNiche is None and mode == ProviderBase.ModeAnime: supportNiche = [Media.Anime, Media.Donghua, Media.Japanese, Media.Chinese]
			elif supportNiche and Tools.isString(supportNiche): supportNiche = [supportNiche]

			if supportMovie is None: supportMovie = True
			if supportShow is None: supportShow = True
			if supportSpecial is None: supportSpecial = True
			if supportPackMovie is None: supportPackMovie = True
			if supportPackShow is None: supportPackShow = True
			if supportPackSeason is None: supportPackSeason = True
			if supportPack is False:
				supportPackMovie = False
				supportPackShow = False
				supportPackSeason = False

			if mirror and not Tools.isArray(mirror): mirror = [mirror]

			if language is None: language = []
			elif not Tools.isArray(language): language = [language]

			gaia = self.addonGaiaName()
			if addonRank is None: addonRank = ProviderBase.RankDefault if addonId else ProviderBase.RankLimit
			addonId = addonId if addonId else self.addonGaiaId()
			addonName = addonName if addonName else gaia

			account = {}
			if accountOptional: account[ProviderBase.AccountOptional] = accountOptional
			if accountUsername: account[ProviderBase.AccountTypeUsername] = ProviderBase.AccountInputDialog if accountUsername is True else accountUsername
			if accountEmail: account[ProviderBase.AccountTypeEmail] = ProviderBase.AccountInputDialog if accountEmail is True else accountEmail
			if accountPassword: account[ProviderBase.AccountTypePassword] = ProviderBase.AccountInputDialog if accountPassword is True else accountPassword
			if accountKey: account[ProviderBase.AccountTypeKey] = ProviderBase.AccountInputDialog if accountKey is True else accountKey
			if accountOther: account[ProviderBase.AccountTypeOther] = ProviderBase.AccountInputDialog if accountOther is True else accountOther

			scrape = self.scrapeInitialize(priority = scrapePriority, termination = scrapeTermination, time = scrapeTime, query = scrapeQuery, pages = scrapePage, requests = scrapeRequest)
			custom = self.customInitialize(custom = custom, version = customVersion, size = customSize, time = customTime, peers = customPeers, seeds = customSeeds, leeches = customLeeches, search = customSearch, category = customCategory, verified = customVerified, spam = customSpam, adult = customAdult, password = customPassword, incomplete = customIncomplete)

			container = ProviderBase.ContainerSingular
			containers = ProviderBase.ContainerPlural
			if type == ProviderBase.TypeTorrent:
				container = ProviderBase.ContainerTorrentSingular
				containers = ProviderBase.ContainerTorrentPlural
			elif type == ProviderBase.TypeUsenet:
				container= ProviderBase.ContainerUsenetSingular
				containers = ProviderBase.ContainerUsenetPlural

			replacements = {'id' : id, 'name' : name, 'addon' : addonName, 'gaia' : gaia, 'type' : type, 'mode' : mode, 'access' : access, 'container' : container, 'containers' : containers}
			try: description = description.format(**replacements)
			except: pass
			if custom:
				for i in range(len(custom)):
					try: custom[i]['description'] = custom[i]['description'].format(**replacements)
					except: pass

			data = {
				'name' : name,
				'label' : name,
				'description' : description,

				'mirror' : mirror,
				'unblock' : unblock,
				'resolver' : resolver,

				'rank' : rank,
				'performance' : performance,
				'optimization' : optimization,
				'status' : status,
				'developer' : developer,

				'addon' : {
					'id' : addonId,
					'name' : addonName,
					'rank' : addonRank,
					'settings' : addonSettings,
					'prepare' : addonPrepare,
					'module' : {
						'scraper' : addonModuleScraper,
						'parent' : addonModuleParent,
						'settings' : addonModuleSettings,
					},
				},

				'enabled' : {
					'default' : enabled, # If the provider is enabled by default.
				},

				'support' : {
					'niche' : supportNiche,
					'movie' : supportMovie,
					'show' : supportShow,
					'special' : supportSpecial,
					'pack' : {
						'movie' : supportPackMovie,
						'show' : supportPackShow,
						'season' : supportPackSeason,
					},
				},

				'account' : account,
				'scrape' : scrape,
				'custom' : custom,

				'cache' : {
					ProviderBase.ScrapeTime : self.settingsGlobalSaveStream() if cacheTime is None else cacheTime,
				},
			}
			if language: data['language'] = language # Do not replace with None if it was set in initializeCore().

			self.dataUpdate(data)
			if link: self.linkSet(link = link, settings = False)
		except: self.logError()

	def initializeCore(self, id = None):
		if not id: id = self.__class__.__module__
		module = self.__class__.__module__
		path = os.path.normpath(sys.modules[module].__file__)
		path = os.path.splitext(path)[0] + '.py'
		parts = path.split(os.sep)

		self.mData['id'] = id

		self.mData['file']['id'] = module
		self.mData['file']['name'] = parts[-1]
		self.mData['file']['path'] = path
		self.mData['file']['directory'] = os.path.dirname(path)

		self.mData['category']['type'] = parts[-4]
		self.mData['category']['mode'] = parts[-3]
		self.mData['category']['access'] = parts[-2]
		self.mData['category']['external'] = self.mData['category']['type'] == 'external'

		if not self.mData['language']:
			language = Language.code(self.mData['category']['mode'])
			if not language: language = Language.UniversalCode
			self.mData['language'] = [language]

	def initializeSettings(self, type = None):
		self.settingsDataClear(type = type)
		self.initialize()

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		ProviderBase.ResultLock = {}
		ProviderBase.ResultFound = {}
		ProviderBase.ResultStreams = {}
		ProviderBase.ResultCore = None
		ProviderBase.ResultFilters = None

		ProviderBase.ScrapeCountQuery = {}
		ProviderBase.ScrapeCountPages = {}
		ProviderBase.ScrapeCountRequests = {}

		ProviderBase.PriorityLocks = {}

		ProviderBase.QueryId = {}
		ProviderBase.QueryDone = {}

		ProviderBase.Link = {}
		ProviderBase.Redirect = {}
		ProviderBase.Timer = {}
		ProviderBase.Times = {}
		ProviderBase.Stop = {}
		ProviderBase.Execution = []
		ProviderBase.Statistics = {}
		ProviderBase.Handlers = {}

		if settings:
			ProviderBase.SettingsData = Tools.copy(ProviderBase.SettingsDataBase)

	##############################################################################
	# LOCK
	##############################################################################

	def lock(self):
		try: self.mLock.acquire()
		except: pass

	def unlock(self):
		try: self.mLock.release()
		except: pass

	##############################################################################
	# COPY
	##############################################################################

	def copy(self, data = True, settings = True, parameters = True):
		instance = self.__class__()
		if data: instance.dataImport(self)
		if settings: instance.settingsDataImport(self)
		if parameters: instance.parametersImport(self)
		instance.initialize()
		return instance

	##############################################################################
	# DATA
	##############################################################################

	def data(self):
		return self.mData

	def dataHas(self):
		return Tools.hasVariable(self, 'mData')

	def dataClear(self):
		self.mData = {
			'id' : None,
			'name' : None,
			'label' : None,
			'description' : None,
			'language' : None,

			'link' : None,
			'mirror' : None,
			'unblock' : None,
			'resolver' : None,

			'rank' : None,
			'performance' : None,
			'optimization' : None,
			'status' : None,
			'developer' : None,

			'addon' : {
				'id' : None,
				'name' : None,
				'rank' : None,
				'settings' : None,
				'version' : None,
				'prepare' : None,
				'module' : {
					'scraper' : None,
					'parent' : None,
					'settings' : None,
				},
			},

			'file' : {
				'id' : None,
				'name' : None,
				'path' : None,
				'directory' : None,
			},

			'category' : {
				'type' : None,
				'mode' : None,
				'access' : None,
				'external' : None,
			},

			'enabled' : {
				'default' : None,		# If the provider is enabled by default.
				'failure' : True,		# If the provider is enabled based on previous failures.
				'preset' : True,		# If the provider is enabled in the preset.
				'developer' : True,		# If the provider is for developers only and the developer settings are enabled.
				'support' : True,		# If the provider is supported by the handlers/resolvers.
			},

			'support' : {
				'movie' : None,
				'show' : None,
				'pack' : None,
			},

			'scrape' : {
				ProviderBase.ScrapePriority : None,
				ProviderBase.ScrapeTermination : None,
				ProviderBase.ScrapeTime : None,
				ProviderBase.ScrapeQuery : None,
				ProviderBase.ScrapePage : None,
				ProviderBase.ScrapeRequest : None,
			},

			'account' : None,
			'custom' : None,

			'cache' : {
				ProviderBase.ScrapeTime : None,
			},
		}

	def dataUpdate(self, data):
		return Tools.update(self.mData, data)

	'''
		FUNCTION:
			Exports the provider as a Python object.
	'''
	def dataExport(self):
		return self.mData

	'''
		FUNCTION:
			Exports the provider to a JSON string.
	'''
	def dataJson(self):
		return Converter.jsonTo(self.dataExport())

	'''
		FUNCTION:
			Imports the provider from a JSON string or provider object.
	'''
	def dataImport(self, data):
		if Tools.isString(data): data = Converter.jsonFrom(data)
		elif Tools.isInstance(data, ProviderBase): data = Tools.copy(data.data())
		self.dataUpdate(data)

	'''
		FUNCTION:
			String operator overload.
	'''
	def __str__(self):
		return self.dataJson()

	'''
		FUNCTION:
			Key index operator overload.
	'''
	def __getitem__(self, key):
		return self.mData[key]

	'''
		FUNCTION:
			JSON serialization overload.
			Not a built-in operator, but called from tools.Converter.jsonTo().
	'''
	def __json__(self):
		return self.dataJson()

	##############################################################################
	# STOP
	##############################################################################

	# Use a global instead of a member variable, since web.py creates copies of the provider.
	def _stop(self):
		ProviderBase.Stop[self.id()] = True

	def stop(self):
		self._stop()

		# Kill processes, since they cannot access ProviderBase.Stop.
		for execution in ProviderBase.Execution:
			try: execution.terminate()
			except: pass

	def stopped(self):
		try: return ProviderBase.Stop[self.id()]
		except: return False

	def stopClear(self):
		ProviderBase.Stop = {}
		ProviderBase.Execution = []

	def stopInitialize(self):
		# Child threads in a process are NOT killed (only orphaned) when the parent process is terminated in the stop() function above.
		# Catch the process termination and then call stop() to make child threads exit.
		if self.concurrencyProcess():
			try:
				import signal
				signal.signal(signal.SIGTERM, lambda x, y : self._stop())
				signal.signal(signal.SIGKILL, lambda x, y : self._stop())
				signal.signal(signal.SIGINT, lambda x, y : self._stop())
			except: pass

	##############################################################################
	# ID
	##############################################################################

	def id(self):
		return self.mData['id']

	def idSet(self, id):
		self.mData['id'] = id

	def idGenerate(self, id = None):
		if id is None: id = self.id()
		if id is None: id = self.name()
		id = id.replace(' ', '').replace('-', '').replace('_', '').replace('.', '').lower()
		self.idSet(self.addonId()[:3] + '-' + id)

	# Returns a unique ID for the instance.
	def idInstance(self):
		return id(self)

	##############################################################################
	# NAME
	##############################################################################

	def name(self):
		return self.mData['name']

	def nameSet(self, name):
		self.mData['name'] = name

	##############################################################################
	# LABEL
	##############################################################################

	def label(self):
		return self.mData['label']

	def labelSet(self, label):
		self.mData['label'] = label

	def labelGenerate(self, name = None):
		if name is None: name = self.name()
		if name is None: name = self.id().capitalize()
		self.labelSet(self.addonName()[:3] + '-' + name)

	##############################################################################
	# DESCRIPTION
	##############################################################################

	def description(self):
		return self.mData['description']

	def descriptionSet(self, description):
		self.mData['description'] = description

	##############################################################################
	# MIRROR
	##############################################################################

	def mirror(self, index = 0):
		try: return self.mData['mirror'][index]
		except: return None

	def mirrors(self):
		 return self.mData['mirror']

	##############################################################################
	# UNBLOCK
	##############################################################################

	def unblock(self):
		return self.mData['unblock']

	def unblockHas(self):
		unblock = self.unblock()
		if unblock:
			try: return not unblock[self.unblockSettings()['format']] is None
			except: pass
		return False

	def unblockEnabled(self):
		return self.unblockSettings()['enabled']

	def unblockDomain(self):
		return Networker.linkDomain(link = self.unblockSettings()['link'], subdomain = False, topdomain = True, ip = True, scheme = False)

	def unblockSettings(self):
		if ProviderBase.UnblockSettings is None:
			enabled = self.settingsGlobalUnblockEnabled()
			type = None
			link = None
			format = None
			if enabled:
				type = self.settingsGlobalUnblockType()
				if type == ProviderBase.UnblockTypeCustom:
					link = self.settingsGlobalUnblockLink()
					format = self.settingsGlobalUnblockFormat()
				else:
					link = ProviderBase.UnblockData[type]['link']
					format = ProviderBase.UnblockData[type]['format']
			ProviderBase.UnblockSettings = {'enabled' : enabled, 'type' : type, 'link' : link, 'format' : format}
		return ProviderBase.UnblockSettings

	def unblockLink(self):
		settings = self.unblockSettings()

		format = settings['format']
		if format == ProviderBase.UnblockFormat0: id = self.id()
		else: id = self.unblock()[format]

		link = settings['link']
		scheme = Networker.linkScheme(link = link)
		if not scheme: scheme = 'https'
		domain = Networker.linkDomain(link = link, subdomain = False, topdomain = True, ip = True, scheme = False)

		return '%s://%s.%s' % (scheme, id, domain)

	##############################################################################
	# RANK
	##############################################################################

	def rank(self, label = False):
		if label: return self.rankIcon(self.mData['rank'])
		else: return self.mData['rank']

	def rankSet(self, rank):
		self.mData['rank'] = rank

	@classmethod
	def rankIcon(self, rank = 1, color = True):
		return Format.iconRating(count = rank, fixed = ProviderBase.RankLimit, color = color)

	def rankLabel(self, rank = None, icon = True, percent = True, description = True, color = True):
		try:
			from lib.modules.interface import Translation, Format
			if rank is None: rank = self.rank()

			result = ''

			if icon: result += self.rankIcon(rank = rank, color = color)
			if percent: result = Format.iconJoin([result, '%d%%' % Math.roundClosest((rank / 5.0) * 100.0)])
			if description: result += ' (%s)' % Translation.string(36363)

			if result: return result
		except: self.logError()
		return None

	##############################################################################
	# PERFORMANCE
	##############################################################################

	@classmethod
	def _performance(self, rank):
		if rank <= 1: return ProviderBase.PerformanceBad
		elif rank <= 2: return ProviderBase.PerformancePoor
		elif rank <= 3: return ProviderBase.PerformanceMedium
		elif rank <= 4: return ProviderBase.PerformanceGood
		elif rank <= 5: return ProviderBase.PerformanceExcellent
		else: return ProviderBase.PerformanceMedium

	def performance(self):
		return self.mData['performance']

	def performanceSet(self, performance = None, rank = None):
		if performance is None and not rank is None: performance = self._performance(rank = rank)
		self.mData['performance'] = performance

	def performanceLabel(self, performance = None, label = True, percent = True, description = True, color = True):
		try:
			from lib.modules.interface import Translation, Format
			if performance is None: performance = self.performance()

			result = ''

			if performance >= ProviderBase.PerformanceExcellent:
				type = ProviderBase.PerformanceExcellent
				if color: color = Format.colorExcellent()
			elif performance >= ProviderBase.PerformanceGood:
				type = ProviderBase.PerformanceGood
				if color: color = Format.colorGood()
			elif performance >= ProviderBase.PerformanceMedium:
				type = ProviderBase.PerformanceMedium
				if color: color = Format.colorMedium()
			elif performance >= ProviderBase.PerformancePoor:
				type = ProviderBase.PerformancePoor
				if color: color = Format.colorPoor()
			else:
				type = ProviderBase.PerformanceBad
				if color: color = Format.colorBad()

			if label:
				label = Translation.string(ProviderBase.PerformanceLabels[type])
				if color: label = Format.fontColor(label, color = color)
				result += label
			if percent: result = Format.iconJoin([result, '%d%%' % Math.roundClosest(performance * 100.0)])
			if description: result += ' (%s)' % Translation.string(36364)

			if result: return result
		except: self.logError()
		return None

	##############################################################################
	# ORDER
	##############################################################################

	def order(self, inverse = False):
		order = 1 + self.performance() + (self.rank() / float(ProviderBase.RankLimit))

		if self.typeLocal(): order += 0.20
		elif self.typeSpecial(): order += 0.15
		elif self.typeCenter(): order += 0.10
		elif self.typePremium(): order += 0.05

		if self.statusCloudflare(): order -= 0.25
		elif self.statusImpaired(): order -= 0.25
		elif self.statusDead(): order -= 0.60
		elif self.statusHidden(): order -= 0.50 if System.developer() else 99.0

		order = Math.scale(value = order, fromMinimum = 0, fromMaximum = 4.0, toMinimum = 0, toMaximum = 1)
		if inverse: order = 1 - order
		return order

	##############################################################################
	# OPTIMIZATION
	##############################################################################

	def optimization(self):
		return self.mData['optimization']

	def optimizationSet(self, optimization = None):
		self.mData['optimization'] = optimization

	def optimizationRating(self, performance = True, rank = True, status = True, language = None):
		rating = []
		if performance: rating.append(self.performance())
		if rank: rating.append(self.rank() / float(ProviderBase.RankLimit))
		rating = [i for i in rating if not i is None]

		if rating: rating = sum(rating) / float(len(rating))
		else: rating = 0.4

		if status and (self.statusCloudflare() or self.statusImpaired()): rating -= ProviderBase.PerformanceStep

		if language:
			languages = self.languages()
			if languages:
				if not Tools.isArray(language): language = [language]
				exclude = [Language.UniversalCode, Language.EnglishCode]

				found = False
				changeMatch = 0.45
				changeUnmatch = 0.2

				# Increase the rating if the user has set a non-English language in the settings that match the provider language.
				for lang in languages:
					if lang in language and not lang in exclude:
						found = True
						order = 1 + ((3 - language.index(lang)) / 10.0) # Given languages a higher weight if they are listed first (eg: primary language will increase the rating more than the secondary language).
						rating += changeMatch * order
						break

				# Decrease the rating of non-English providers if the user has not set the language in the settings.
				if not found and languages and len([i for i in languages if not i in exclude]) > 0:
					rating -= changeUnmatch

		if self.typeExternal(): rating *= 0.7

		return Math.round(min(1, max(0, rating)), places = 2)

	def optimize(self, performance = True, rank = True, niche = None, language = None, account = True, dead = True, default = True, support = True, optimization = True, internal = True):
		# If optimization is True, enable the provider. If set to False, disable the provider.
		if optimization:
			optimization = self.optimization()
			if not optimization is None: return optimization

		# Do not enable premium debrid scrapers, since most people will not use them in any case.
		# Plus they are often a bit slower, since they have to make a lot of API requests for subfolders.
		# And Premiumize links expire, so the scraper is executed again when the streams are reloaded a day later.
		if self.typePremium(): return False

		# Enable providers which have an active account.
		if account and self.accountHas():
			if self.accountOptional():
				# If no optional account was provided, continue with the other criteria below.
				if self.accountEnabled(): return True
			else:
				return self.accountEnabled()

		# Disable dead providers.
		if dead and self.statusDead(): return False

		# Disable providers that are by default disabled.
		# NB: Do not use this, otherwise a bunch of providers are always disabled (eg: external hosters).
		#if default and not self.enabledDefault(): return False

		# Disable providers that are not supported by the handlers/resolvers.
		if support and not self.enabledSupport(): return False

		# Disable providers that are internally disabled.
		if internal and not self.enabledInternal(): return False

		# Disable providers that have no supported handler.
		if self.typeTorrent() or self.typeUsenet():
			from lib.modules.handler import Handler
			type = self.type()
			try: handler = ProviderBase.Handlers[type]
			except: handler = ProviderBase.Handlers[type] = Handler(type = type)
			if not handler.supportedType(type = type): return False

		# Enable niche providers.
		# If there are too many niche (eg: anime) providers in the future, we might need to do this in optimizationRating() to not enable all of them.
		if niche:
			support = self.supportNiche()
			if support:
				if not Tools.isArray(niche): niche = [niche]
				if not Tools.isArray(support): support = [support]
				if any(i in niche for i in support): return True

		# Otherwise calculate a rating.
		return self.optimizationRating(performance = performance, rank = rank, language = language)

	##############################################################################
	# STATUS
	##############################################################################

	def status(self):
		return self.mData['status']

	def statusOperational(self):
		return self.status() == ProviderBase.StatusOperational

	def statusCloudflare(self):
		return self.status() == ProviderBase.StatusCloudflare

	def statusImpaired(self):
		return self.status() == ProviderBase.StatusImpaired

	def statusDead(self):
		return self.status() == ProviderBase.StatusDead

	def statusHidden(self):
		return self.status() == ProviderBase.StatusHidden

	def statusActive(self):
		return self.statusOperational() or self.statusCloudflare() or self.statusImpaired()

	def statusLabel(self, status = None, label = True, description = True, color = True):
		try:
			from lib.modules.interface import Translation, Format
			if status is None: status = self.status()

			result = ''

			if status == ProviderBase.StatusOperational: color = Format.colorExcellent()
			elif status == ProviderBase.StatusCloudflare: color = Format.colorMedium()
			elif status == ProviderBase.StatusImpaired: color = Format.colorPoor()
			elif status == ProviderBase.StatusDead: color = Format.colorBad()
			else: color = None

			if label:
				result += Translation.string(ProviderBase.StatusLabels[status])
				if color: result = Format.fontColor(result, color = color)
			if description: result += ' (%s)' % Translation.string(ProviderBase.StatusDescriptions[status])

			if result: return result
		except: self.logError()
		return None

	##############################################################################
	# LANGUAGE
	##############################################################################

	def language(self, index = 0, code = None):
		language = self.mData['language'][index]
		if not code is None: language = Language.code(language, code = code)
		return language

	def languagePrimary(self, index = 0):
		return self.language(index = index, code = Language.CodePrimary)

	def languageSecondary(self, index = 0):
		return self.language(index = index, code = Language.CodeSecondary)

	def languageTertiary(self, index = 0):
		return self.language(index = index, code = Language.CodeTertiary)

	def languages(self, copy = False, universal = True):
		if copy: languages = Tools.copy(self.mData['language'])
		else: languages = self.mData['language']
		if not universal: languages = [i for i in languages if not i == Language.CodeUniversal]
		return languages

	def languageSet(self, language):
		if not Tools.isArray(language): language = [language]
		self.mData['language'] = language

	##############################################################################
	# DEVELOPER
	##############################################################################

	def developer(self):
		return self.mData['developer']

	##############################################################################
	# ADDON
	##############################################################################

	@classmethod
	def addonGaiaId(self):
		return self.addonGaiaName().lower()

	@classmethod
	def addonGaiaName(self):
		return System.name()

	def addonId(self):
		return self.mData['addon']['id']

	def addonName(self):
		return self.mData['addon']['name']

	def addonRank(self, label = False):
		if label: return self.rankIcon(self.mData['addon']['rank'])
		else: return self.mData['addon']['rank']

	def addonSettings(self):
		return self.mData['addon']['settings']

	def addonPrepare(self):
		return self.mData['addon']['prepare']

	def addonVersion(self):
		return self.mData['addon']['version']

	def addonVersionSet(self, version):
		self.mData['addon']['version'] = version

	def addonModuleScraper(self):
		return self.mData['addon']['module']['scraper']

	def addonModuleParent(self):
		return self.mData['addon']['module']['parent']

	def addonModuleSettings(self, fallback = True):
		result = self.mData['addon']['module']['settings']
		if result: return result
		return self.addonModuleScraper() if self.addonSettings() else None

	def addonEnabled(self, scraper = True, parent = False, settings = False):
		if scraper:
			id = self.addonModuleScraper()
			if id and not System.enabled(id = id): return False
		if parent:
			id = self.addonModuleParent()
			if id and not System.enabled(id = id): return False
		if settings:
			id = self.addonModuleSettings()
			if id and not System.enabled(id = id): return False
		return scraper or parent or settings

	def addonInstalled(self, scraper = True, parent = False, settings = False):
		if scraper:
			id = self.addonModuleScraper()
			if id and not System.installed(id = id, deprecated = False): return False
		if parent:
			id = self.addonModuleParent()
			if id and not System.installed(id = id, deprecated = False): return False
		if settings:
			id = self.addonModuleSettings()
			if id and not System.installed(id = id, deprecated = False): return False
		return scraper or parent or settings

	def addonEnable(self, scraper = True, parent = False):
		from lib.modules.tools import Extension
		if scraper:
			id = self.addonModuleScraper()
			if id: Extension.enable(id)
		if parent:
			id = self.addonModuleParent()
			if id: Extension.enable(id)

	##############################################################################
	# LINK
	##############################################################################

	def link(self, path = None, settings = True, index = 0):
		try:
			link = self.links(settings = settings, deleted = False, flat = True)[index]
			if path: return Networker.linkJoin(link, path)
			else: return link
		except: return None

	def linkNext(self, link = None, path = None, settings = True):
		try:
			if link is None: return self.link(path = path, settings = settings)
			link = Networker.linkDomain(link = link, subdomain = True, topdomain = True, ip = True)
			links = self.links(settings = settings, deleted = False, flat = True)
			for i in range(len(links)):
				if Networker.linkDomain(link = links[i], subdomain = True, topdomain = True, ip = True) == link:
					if path: return Networker.linkJoin(links[i + 1], path)
					else: return links[i + 1]
		except: pass
		return None

	def linkCurrent(self, path = None, settings = True):
		try:
			link = self.linkRedirect()
			if not link:
				link = self.linkPrevious()
				if not link: link = self.link()
			link = Networker.linkDomain(link = link, subdomain = True, topdomain = True, ip = True)
			links = self.links(settings = settings, deleted = False, flat = True)
			for i in range(len(links)):
				if Networker.linkDomain(link = links[i], subdomain = True, topdomain = True, ip = True) == link:
					if path: return Networker.linkJoin(links[i], path)
					else: return links[i]
		except: pass
		return None

	def linkPrevious(self, redirect = True):
		if redirect:
			redirect = self.linkRedirect()
			if redirect: return redirect
		id = self.id()
		return ProviderBase.Link[id] if id in ProviderBase.Link else None

	def linkPreviousSet(self, link):
		ProviderBase.Link[self.id()] = link

	def linkRedirect(self):
		id = self.id()
		return ProviderBase.Redirect[id] if id in ProviderBase.Redirect else None

	def linkRedirectSet(self, link):
		ProviderBase.Redirect[self.id()] = link

	def linkPath(self, link = None, path = None):
		if link is None: return link
		link = Networker.linkDomain(link = link, subdomain = True, topdomain = True, ip = True, scheme = True)
		return Networker.linkJoin(link, path)

	def links(self, settings = True, deleted = False, custom = None, flat = True, unblock = True):
		result = None
		if settings: result = self.mSettings['link']
		if not result: result = self.mData['link']
		if not result: return result

		if not deleted: result = [link for link in result if not 'deleted' in link or not link['deleted']]

		if custom is True: result = [link for link in result if 'custom' in link and link['custom']]
		elif custom is False: result = [link for link in result if not 'custom' in link or not link['custom']]

		if unblock: self.linksUnblock(result, toggle = False)
		if flat: result = [link['link'] for link in result]

		return result

	def linksClean(self):
		try:
			# Update the settings with links in case the provider code was updated with new domains.
			# Maintain the old custom domains the user added before the update.
			# Also maintain the order if the user moved domains up/down.

			if self.linkHas():
				linksDefault = self.links(settings = False, deleted = True, flat = False)
				linksSettings = self.links(settings = True, deleted = True, flat = False)

				index = 0
				for i in range(len(linksSettings)):
					if not linksSettings[i]['custom']:
						index = i
						break

				for link1 in linksDefault:
					linkValue1 = link1['link']
					found = False
					for i in range(len(linksSettings)):
						linkValue2 = linksSettings[i]['link']
						if linkValue1 == linkValue2:
							linksSettings[i]['fixed'] = True
							found = True
							index = max(index, i + 1)
							break

					if not found:
						link1['fixed'] = True
						linksSettings.insert(index, link1)
						index += 1

				# Change the domain order if it changed in the new version.
				# Eg: A later alternative domain has now become the main domain is is moved to the front.
				try:
					# Try to keep the order as much as possible, if the user moved a custom domain to the front.
					customBefore = []
					customAfter = []
					custom = customBefore
					for link in linksSettings:
						if link['custom']: custom.append(link['link'])
						else: custom = customAfter
					order = customBefore + [link['link'] for link in linksDefault] + customAfter
					linksSettings = Tools.listSort(data = linksSettings, key = lambda i : order.index(i['link']) if i['link'] in order else 999999)
				except: self.logError()

				# Remove old domains if there are new domains.
				linksSettings = [link for link in linksSettings if link['custom'] or 'fixed' in link]
				for i in range(len(linksSettings)):
					try: del linksSettings[i]['fixed']
					except: pass

				# Filter out any duplicate links added by custom.
				try: linksSettings = Tools.listUnique(data = linksSettings, attribute = 'link')
				except: self.logError()

				self.linkSet(linksSettings, settings = True)
		except: self.logError()

	def linksUnblock(self, links, toggle = True):
		if links:
			if self.unblockHas() and self.unblockEnabled():
				domain = self.unblockDomain()
				found = False
				for i in range(len(links)):
					link = links[i]
					if 'unblock' in link and link['unblock']:
						if not domain in link['link']:
							del links[i]
							break
						elif 'deleted' in link and link['deleted']:
							if toggle: del links[i]['deleted']
							return True
						else:
							found = True
							break
				if not found:
					links.insert(1, {'link' : self.unblockLink(), 'custom' : False, 'unblock' : True})
					return True
			else:
				for i in range(len(links)):
					link = links[i]
					if 'unblock' in link and link['unblock']:
						del links[i]
						break
		return False

	def linkSet(self, link, settings = True):
		if link is None: link = []
		elif Tools.isArray(link): link = Tools.copy(link) # Create a copy, since lists are passed by reference, and the list might be edited afterwards.
		else: link = [link]
		if link and not Tools.isDictionary(link[0]): link = [{'link' : l, 'custom' : False} for l in link]
		if settings: self.mSettings['link'] = link
		else: self.mData['link'] = link

	def linkHas(self):
		return bool(self.mData['link'])

	def linkDomain(self, subdomain = True, settings = True, request = False, scheme = False):
		id = self.id()
		link = ProviderBase.Link[id] if (request and id in ProviderBase.Link and ProviderBase.Link[id]) else self.link(settings = settings)
		if link: return Networker.linkDomain(link = link, subdomain = subdomain, topdomain = True, ip = True, scheme = scheme)
		else: return None

	def linkDomains(self, subdomain = True, settings = True):
		return [Networker.linkDomain(link, subdomain = subdomain, topdomain = True, ip = True) for link in self.links(settings = settings, deleted = False, flat = True)]

	def linkVerifyConnection(self, networker, special = True):
		if networker:
			if networker.responseSuccess():
				return True, None
			else:
				# Ignore HTTP 4xx errors (eg 403 with TorrentApi). Server is up, just misformed request. Still detect Cloudflare 4xx errors.
				type = networker.responseErrorType()
				if special and networker.responseError4xx() and not type == Networker.ErrorCloudflare: return True, None
				else: return False, type
		return None, None

	# Can be overwritten by subclasses.
	# Can return True/False or one of the VerifyXYZ enums.
	def linkVerify(self):
		# For external providers.
		try:
			if self.linkHas():
				networker = Networker()

				counter = 0
				retries = 0

				enabled = self.settingsGlobalMirrorEnabled()
				limit = self.settingsGlobalMirrorLimit()

				link = self.linkPrevious()
				if link:
					link = self.linkPath(link = link)
				else:
					counter += 1
					link = self.linkNext(link = link)

				reason = None
				while link:
					networker.request(link = link)
					result, reason = self.linkVerifyConnection(networker)
					if result: break
					elif not enabled or counter > limit: break
					elif self.stopped(): break
					counter += 1
					retries += 1
					link = self.linkNext(link = link)

				if reason == Networker.ErrorConnection: return ProviderBase.VerifyFailure, reason
				elif retries > 0 or reason: return ProviderBase.VerifyLimited, reason
				else: return ProviderBase.VerifySuccess, reason
		except:
			self.logError()
		return None, None

	##############################################################################
	# FILE
	##############################################################################

	def fileId(self):
		return self.mData['file']['id']

	def fileName(self):
		return self.mData['file']['name']

	def filePath(self):
		return self.mData['file']['path']

	def fileDirectory(self):
		return self.mData['file']['directory']

	##############################################################################
	# TYPE
	##############################################################################

	def type(self):
		return self.mData['category']['type']

	def typeFixed(self):
		return self.typeTorrent() or self.typeUsenet() or self.typeHoster()

	def typeLocal(self):
		return self.type() == ProviderBase.TypeLocal

	def typeExternal(self):
		return self.type() == ProviderBase.TypeExternal

	def typePremium(self):
		return self.type() == ProviderBase.TypePremium

	def typeCenter(self):
		return self.type() == ProviderBase.TypeCenter

	def typeSpecial(self):
		return self.type() == ProviderBase.TypeSpecial

	def typeTorrent(self):
		return self.type() == ProviderBase.TypeTorrent

	def typeUsenet(self):
		return self.type() == ProviderBase.TypeUsenet

	def typeHoster(self):
		return self.type() == ProviderBase.TypeHoster

	##############################################################################
	# MODE
	##############################################################################

	def mode(self):
		return self.mData['category']['mode']

	def modeUniversal(self):
		return self.mode() == ProviderBase.ModeUniversal

	def modeAnime(self):
		return self.mode() == ProviderBase.ModeAnime

	def modeEnglish(self):
		return self.mode() == ProviderBase.ModeEnglish

	def modeFrench(self):
		return self.mode() == ProviderBase.ModeFrench

	def modeGerman(self):
		return self.mode() == ProviderBase.ModeGerman

	def modeDutch(self):
		return self.mode() == ProviderBase.ModeDutch

	def modeSpanish(self):
		return self.mode() == ProviderBase.ModeSpanish

	def modePortuguese(self):
		return self.mode() == ProviderBase.ModePortuguese

	def modeItalian(self):
		return self.mode() == ProviderBase.ModeItalian

	def modeRussian(self):
		return self.mode() == ProviderBase.ModeRussian

	##############################################################################
	# ACCESS
	##############################################################################

	def access(self):
		return self.mData['category']['access']

	def accessOpen(self):
		return self.access() == ProviderBase.AccessOpen

	def accessMember(self):
		return self.access() == ProviderBase.AccessMember

	def accessOffline(self):
		return self.access() == ProviderBase.AccessOffline

	def accessDistributed(self):
		return self.access() == ProviderBase.AccessDistributed

	##############################################################################
	# ENABLED
	##############################################################################

	def enabled(self):
		return self.enabledSettings() and self.enabledFailure() and self.enabledPreset() and self.enabledDeveloper() and self.enabledSupport() and self.enabledAccount() and self.enabledInternal() and self.enabledExternal()

	def enabledDefault(self):
		return self.mData['enabled']['default']

	def enableDefault(self, enable = True):
		self.mData['enabled']['default'] = enable

	def disableDefault(self, disable = True):
		self.enableDefault(enable = not disable)

	def enabledSettings(self, type = True, mode = True, access = True, addon = True, provider = True):
		return (not type or self.enabledSettingsType()) and (not mode or self.enabledSettingsMode()) and (not access or self.enabledSettingsAccess()) and (not addon or self.enabledSettingsAddon()) and (not provider or self.enabledSettingsProvider())

	def enabledSettingsType(self):
		return self.mSettings['enabled']['type']

	def enableSettingsType(self, enable = True):
		self.mSettings['enabled']['type'] = enable

	def disableSettingsType(self, disable = True):
		self.enableSettingsType(enable = not disable)

	def enabledSettingsMode(self):
		return self.mSettings['enabled']['mode']

	def enableSettingsMode(self, enable = True):
		self.mSettings['enabled']['mode'] = enable

	def disableSettingsMode(self, disable = True):
		self.enableSettingsMode(enable = not disable)

	def enabledSettingsAccess(self):
		return self.mSettings['enabled']['access']

	def enableSettingsAccess(self, enable = True):
		self.mSettings['enabled']['access'] = enable

	def disableSettingsAccess(self, disable = True):
		self.enableSettingsAccess(enable = not disable)

	def enabledSettingsAddon(self):
		return self.mSettings['enabled']['addon']

	def enableSettingsAddon(self, enable = True):
		self.mSettings['enabled']['addon'] = enable

	def disableSettingsAddon(self, disable = True):
		self.enableSettingsAddon(enable = not disable)

	def enabledSettingsProvider(self):
		return self.mSettings['enabled']['provider']

	def enableSettingsProvider(self, enable = True):
		self.mSettings['enabled']['provider'] = enable

	def disableSettingsProvider(self, disable = True):
		self.enableSettingsProvider(enable = not disable)

	def enabledFailure(self):
		return self.mData['enabled']['failure']

	def enableFailure(self, enable = True):
		self.mData['enabled']['failure'] = enable

	def disableFailure(self, disable = True):
		self.enableFailure(enable = not disable)

	def enabledPreset(self):
		return self.mData['enabled']['preset']

	def enablePreset(self, enable = True):
		self.mData['enabled']['preset'] = enable

	def disablePreset(self, disable = True):
		self.enablePreset(enable = not disable)

	def enabledDeveloper(self):
		return self.mData['enabled']['developer']

	def enableDeveloper(self, enable = True):
		self.mData['enabled']['developer'] = enable

	def disableDeveloper(self, disable = True):
		self.enableDeveloper(enable = not disable)

	def enabledSupport(self):
		return self.mData['enabled']['support']

	def enableSupport(self, enable = True):
		self.mData['enabled']['support'] = enable

	def disableSupport(self, disable = True):
		self.enableSupport(enable = not disable)

	def enabledAccount(self):
		return not self.accountHas() or self.accountEnabled(optional = True)

	def enabledInternal(self):
		return True

	def enabledExternal(self):
		return True

	##############################################################################
	# SUPPORT
	##############################################################################

	def supportMedia(self):
		result = []
		if self.mData['support']['movie']: result.append(Media.Movie)
		if self.mData['support']['show']: result.append(Media.Show)
		return result

	def supportNiche(self):
		return self.mData['support']['niche']

	def supportMovie(self):
		return self.mData['support']['movie']

	def supportShow(self):
		return self.mData['support']['show']

	def supportSpecial(self):
		return self.mData['support']['special']

	def supportPackMovie(self):
		return self.mData['support']['movie'] and self.mData['support']['pack']['movie']

	def supportPackShow(self):
		return self.mData['support']['show'] and self.mData['support']['pack']['show']

	def supportPackSeason(self):
		return self.mData['support']['show'] and self.mData['support']['pack']['season']

	##############################################################################
	# ACCOUNT
	##############################################################################

	def account(self, type = None):
		result = self.mSettings['account']
		if type:
			account = self.accountType(type = type)
			if not account:
				return None
			elif account == ProviderBase.AccountInputDialog:
				try: result = result[type]
				except: result = None
			elif not account == ProviderBase.AccountInputCustom:
				result = Settings.getString(account)
		return result

	def accountSet(self, value, type = None):
		if type:
			account = self.accountType(type = type)
			if account == ProviderBase.AccountInputDialog:
				if self.mSettings['account'] is None: self.mSettings['account'] = {}
				self.mSettings['account'][type] = value
			elif not account == ProviderBase.AccountInputCustom:
				Settings.set(account, value)
		else:
			self.mSettings['account'] = value

	def accountType(self, type = None):
		result = self.mData['account']
		if type:
			try: result = result[type]
			except: result = None
		return result

	def accountOptional(self):
		return self.accountType(type = ProviderBase.AccountOptional)

	def accountUsername(self):
		return self.account(type = ProviderBase.AccountTypeUsername)

	def accountEmail(self):
		return self.account(type = ProviderBase.AccountTypeEmail)

	def accountPassword(self):
		return self.account(type = ProviderBase.AccountTypePassword)

	def accountKey(self):
		return self.account(type = ProviderBase.AccountTypeKey)

	def accountOther(self):
		return self.account(type = ProviderBase.AccountTypeOther)

	def accountClear(self, type = None):
		if type: self.mSettings['account'][type] = None
		else: self.mSettings['account'] = None

	def accountHas(self, optional = None):
		try:
			if optional and self.accountOptional(): return True
			values = list(self.mData['account'].keys())
			return any(i in ProviderBase.AccountTypeOrder and self.mData['account'][i] for i in values)
		except: return False

	def accountEnabled(self, type = None, optional = None):
		if optional and self.accountOptional(): return True

		if type: items = {type : self.mData['account'][type]}
		else: items = self.mData['account']

		for type, account in items.items():
			if account == ProviderBase.AccountInputDialog:
				if type and (not self.mSettings['account'] or not type in self.mSettings['account'] or not self.mSettings['account'][type]):
					return False
			elif account == ProviderBase.AccountInputCustom:
				if not self.accountCustomEnabled():
					return False

		return True

	def accountAttributes(self):
		result = []
		for type in ProviderBase.AccountTypeOrder:
			account = self.accountType(type = type)
			if account:
				label = self.accountLabel(type = type)
				value = None
				format = None
				if self.accountEnabled(type = type, optional = True):
					value = self.account(type = type)
					if account == ProviderBase.AccountInputCustom:
						try: format = self.accountSettingsLabel(type = type)
						except: format = self.accountSettingsLabel()
					else:
						format = value
				format = self.accountFormat(type = type, value = format)
				result.append({'type' : type, 'label' : label, 'value' : value, 'format' : format, 'optional' : self.accountOptional()})
		return result

	def accountLabel(self, type):
		from lib.modules.interface import Translation
		try: return Translation.string(ProviderBase.AccountTypeLabels[type])
		except: return None

	def accountFormat(self, type = None, value = None):
		from lib.modules.interface import Format
		if not value:
			if type == ProviderBase.AccountTypeOther: return Format.fontItalic(35805)
			else: return Format.fontItalic(33112)
		if type == ProviderBase.AccountTypePassword or type == ProviderBase.AccountTypeKey:
			return Format.FontPassword
		return value

	def accountDialog(self, type):
		input = None
		account = self.accountType(type = type)

		if account == ProviderBase.AccountInputDialog:
			from lib.modules.interface import Dialog
			input = Dialog.input(title = self.accountLabel(type = type), default = self.account(type = type))
			self.accountSet(type = type, value = input)
		elif account == ProviderBase.AccountInputCustom:
			try:
				input = self.accountCustomDialog(type = type)
				if not input is None: self.accountSet(type = type, value = input)
			except:
				input = self.accountCustomDialog()
				if not input is None: self.accountSet(value = input)
		else:
			from lib.modules.interface import Dialog
			input = Dialog.input(title = self.accountLabel(type = type), default = self.account(type = type))
			self.accountSet(type = type, value = input)

	# Must be implemented by subclasses with AccountInputCustom mode.
	# Returns True/False if the account details were entered by the user.
	def accountCustomEnabled(self):
		return False

	# Must be implemented by subclasses with AccountInputCustom mode.
	# Returns the label that is displayed in the dialog.
	def accountSettingsLabel(self, type = None):
		from lib.modules.interface import Translation
		return Translation.string(33216)

	# Must be implemented by subclasses with AccountInputCustom mode.
	# Executes the authentication process and stores all necessary values.
	# If this function returns anything besides None, it will be saved to the settings.
	# If this function stores its own settings, it should return None.
	def accountCustomDialog(self, type = None):
		return None

	# Can be overwritten by subclasses.
	# Can return True/False or one of the VerifyXYZ enums.
	def accountVerify(self):
		return None

	##############################################################################
	# SETTINGS
	##############################################################################

	def settings(self, category, id = None, settings = True):
		result = None
		items = self.mData[category]

		if items:
			if id:
				for item in items:
					if self.settingsIdCompare(item[ProviderBase.SettingsId], id):
						if settings:
							try: result = self.mSettings[category][id]
							except: pass
						if result is None: result = item[ProviderBase.SettingsDefault]

						# Convert list index to the actual value.
						type = item[ProviderBase.SettingsType]
						if Tools.isArray(type) and not Tools.isDictionary(type[0]):
							try: result = type[result]
							except: result = type[0] # New version has removed options.

						break
			else:
				result = {}
				for item in items:
					value = None
					if settings:
						try: value = self.mSettings[category][item[ProviderBase.SettingsId]]
						except: value = None
					if value is None: value = item[ProviderBase.SettingsDefault]

					# Do not return the actual value, but the index. Used by manager to save/load setttings data.
					#type = item[ProviderBase.SettingsType]
					#if Tools.isArray(type) and not Tools.isDictionary(type[0]):
					#	try: value = type[value] # List index.
					#	except: value = type[0] # New version has removed options.

					result[item[ProviderBase.SettingsId]] = value
		return result

	def settingsSet(self, category, value, id = None, settings = True):
		if settings:
			if id:
				self.mSettings[category][id] = value
			elif value:
				for id, val in value.items():
					self.mSettings[category][id] = val
		elif self.mData[category]:
			if id:
				for i in range(len(self.mData[category])):
					if self.settingsIdCompare(self.mData[category][i][ProviderBase.SettingsId], id):
						self.mData[category][i] = value
						break
			elif value is None:
				for i in range(len(self.mData[category])):
					self.mData[category][i] = value
			elif value:
				for id, val in value.items():
					for i in range(len(self.mData[category])):
						if self.settingsIdCompare(self.mData[category][i][ProviderBase.SettingsId], id):
							self.mData[category][i] = val
							break

	def settingsId(self, category):
		try: return [i[ProviderBase.SettingsId] for i in self.mData[category]]
		except: return None

	@classmethod
	def settingsIdCompare(self, id1, id2):
		# Important to convert to string, since JSON conversion changes int keys to string keys.
		return str(id1) == str(id2)

	def settingsHas(self, category, id):
		for i in self.mData[category]:
			if i[ProviderBase.SettingsId] == id: return True
		return False

	def settingsCustomize(self, default, custom):
		if not custom is True: default.update(custom)
		return default

	def settingsAttributes(self, category):
		return self._settingsAttributes(category = category, data = self.mData, settings = self.mSettings)

	@classmethod
	def _settingsAttributes(self, category, data = None, settings = None):
		from lib.modules.interface import Translation
		result = []
		items = data[category]

		if items:
			for item in items:
				type = item[ProviderBase.SettingsType]
				try: value = settings[category][item[ProviderBase.SettingsId]]
				except: value = None
				try: default = item[ProviderBase.SettingsDefault]
				except: default = None

				# Assume it is the index for the list.
				# Try-except in case a future version removes the option that is saved in the settings. If the option is gone, usae the default.
				if Tools.isArray(type) and not Tools.isDictionary(type[0]):
					if not value is None:
						try: value = type[value]
						except:
							try: value = type[default]
							except: value = None
					if not default is None:
						try: default = type[default]
						except: default = None

				if value is None: value = default

				try: format = item[ProviderBase.SettingsFormat]
				except: format = None
				format = self.settingsFormat(type = item[ProviderBase.SettingsType], value = value, default = default, format = format)

				try: description = item[ProviderBase.SettingsDescription]
				except: description = None

				result.append({'id' : item[ProviderBase.SettingsId], 'type' : item[ProviderBase.SettingsType], 'label' : Translation.string(item[ProviderBase.SettingsLabel]), 'value' : value, 'format' : format, 'description' : description})

		return result

	@classmethod
	def settingsFormat(self, type, value, default = None, format = None):
		try:
			formatter = None

			if format:
				if formatter is None and value == default:
					try: formatter = format[ProviderBase.SettingsDefault]
					except: pass
				if formatter is None and value is None:
					try: formatter = format[ProviderBase.SettingsValueNone]
					except: pass
				if formatter is None and value == 0:
					try: formatter = format[ProviderBase.SettingsValueZero]
					except: pass
				if formatter is None:
					try: formatter = format[value]
					except: pass
				if formatter is None:
					try: formatter = format[ProviderBase.SettingsValueGeneral]
					except: pass

				if formatter:
					if formatter == ProviderBase.SettingsValueNone:
						value = Format.fontItalic(33112)
					elif formatter == ProviderBase.SettingsValueDefault:
						value = Format.fontItalic(33564)
					elif formatter == ProviderBase.SettingsValueCustom:
						value = Format.fontItalic(35233)
					elif formatter == ProviderBase.SettingsValueUnlimited:
						value = Format.fontItalic(35221)
					elif formatter == ProviderBase.SettingsValueAutomatic:
						value = Format.fontItalic(33800)
					elif formatter == ProviderBase.SettingsValueUnauthorized:
						value = Format.fontItalic(35805)
					elif formatter == ProviderBase.SettingsFormatDuration:
						from lib.modules.convert import ConverterDuration
						value = ConverterDuration(value, unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatAbbreviationShort, capitalize = True)
					elif formatter == ProviderBase.SettingsFormatDays:
						from lib.modules.convert import ConverterDuration
						value = ConverterDuration(value, unit = ConverterDuration.UnitDay).string(format = ConverterDuration.FormatWordFixed, unit = ConverterDuration.UnitDay, places = ConverterDuration.PlacesNone, capitalize = True)
					elif formatter == ProviderBase.SettingsFormatSeconds:
						from lib.modules.convert import ConverterDuration
						value = ConverterDuration(value, unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatWordFixed, unit = ConverterDuration.UnitSecond, places = ConverterDuration.PlacesNone, capitalize = True)
					elif formatter == ProviderBase.SettingsFormatSize:
						from lib.modules.convert import ConverterSize
						value = ConverterSize(value, unit = ConverterSize.ByteMega).stringOptimal()
					elif formatter == ProviderBase.SettingsFormatPeers:
						value = '%d %s' % (value, Translation.string(33190 if value == 1 else 33191))
					elif formatter == ProviderBase.SettingsFormatSeeds:
						value = '%d %s' % (value, Translation.string(35706 if value == 1 else 33204))
					elif formatter == ProviderBase.SettingsFormatLeeches:
						value = '%d %s' % (value, Translation.string(33125 if value == 1 else 33126))
					elif formatter == ProviderBase.SettingsFormatLinks:
						value = '%d %s' % (value, Translation.string(33381 if value == 1 else 35222))
					elif formatter == ProviderBase.SettingsFormatRank:
						value = '%d. %s' % (value, Translation.string(35011))
					elif formatter == ProviderBase.SettingsFormatQuery:
						value = '%d %s' % (value, Translation.string(33328 if value == 1 else 32035))
					elif formatter == ProviderBase.SettingsFormatPage:
						value = '%d %s' % (value, Translation.string(35809 if value == 1 else 35810))
					elif formatter == ProviderBase.SettingsFormatRequest:
						value = '%d %s' % (value, Translation.string(35807 if value == 1 else 35808))
					elif formatter == ProviderBase.SettingsFormatVersion:
						if value == ProviderBase.VersionAutomatic: value = Format.fontItalic(33800)
						elif value.isdigit(): value = '%s %s' % (Translation.string(36797), str(value)) # Use "Variant" label. Otherwise the user might think a higher "Version" is better (eg V2 is better than V1), which is not always the case.
					elif Tools.isString(formatter) or Tools.isInteger(formatter):
						if Tools.isInteger(formatter): formatter = Translation.string(formatter)
						try: value = formatter % value
						except: value = formatter
					elif Tools.isArray(formatter):
						if Tools.isInteger(formatter[0]): formatter = [Translation.string(i) for i in formatter]
						if value == 1:
							try: value = formatter[0] % value
							except: value = formatter[0]
						else:
							try: value = formatter[1] % value
							except: value = formatter[1]

			if not formatter:
				if Tools.isArray(type):
					if Tools.isDictionary(type[0]):
						for attribute in type:
							if self.settingsIdCompare(value, list(attribute.keys())[0]):
								value = list(attribute.values())[0]
								if Tools.isInteger(value) and value > 30000: value = Translation.string(value)
								else: value = str(value)
								break
					elif Tools.isInteger(value):
						value = Translation.string(value)
				elif type == ProviderBase.SettingsTypeBoolean:
					value = Translation.string(33341 if value else 33342)
				else:
					value = str(value)

		except: self.logError()
		return value

	def settingsDialog(self, category, id):
		from lib.modules.interface import Dialog, Translation

		if self.mData[category]:
			for i in range(len(self.mData[category])):
				if self.settingsIdCompare(self.mData[category][i][ProviderBase.SettingsId], id):
					item = self.mData[category][i]
					type = item[ProviderBase.SettingsType]
					try: value = self.mSettings[category][id]
					except: value = None
					try: default = item[ProviderBase.SettingsDefault]
					except: default = None
					try: format = item[ProviderBase.SettingsFormat]
					except: format = None
					try: refresh = item[ProviderBase.SettingsRefresh]
					except: refresh = None
					try: mode = item[ProviderBase.SettingsMode]
					except: mode = None

					# Assume it is the index for the list.
					# Try-except in case a future version removes the option that is saved in the settings. If the option is gone, usae the default.
					if Tools.isArray(type) and not Tools.isDictionary(type[0]):
						if not value is None:
							try: value = type[value]
							except:
								try: value = type[default]
								except: value = None
						if not default is None:
							try: default = type[default]
							except: default = None

					before = value
					if value is None: value = default

					if type == ProviderBase.SettingsTypeCustom:
						value = self.customExecute(id = id)
					elif type == ProviderBase.SettingsTypeBoolean:
						value = not value
					elif type == ProviderBase.SettingsTypeNumber:
						value = Dialog.input(title = item[ProviderBase.SettingsLabel], default = value, type = Dialog.InputNumeric)
						if not value is None: value = int(value)
					elif type == ProviderBase.SettingsTypeString:
						value = Dialog.input(title = item[ProviderBase.SettingsLabel], default = value, type = Dialog.InputAlphabetic)
					elif type == ProviderBase.SettingsTypePath:
						if mode == ProviderBase.SettingsPathRead: browse = Dialog.BrowseDirectoryRead
						elif mode == ProviderBase.SettingsPathWrite: browse = Dialog.BrowseDirectoryWrite
						else: browse = Dialog.BrowseFile
						if value and (mode == ProviderBase.SettingsPathRead or mode == ProviderBase.SettingsPathWrite):
							# If the directory does not exist yet (eg: first scrape), Kodi will not open at the dialog at the default location.
							# Do this for both read/write directories, and put it inn a try-catch in case the directory is not writeable.
							try:
								from lib.modules.tools import File
								File.makeDirectory(value)
							except: self.logError()
						value = Dialog.browse(title = item[ProviderBase.SettingsLabel], type = browse, default = value)
					elif Tools.isArray(type):
						if Tools.isDictionary(type[0]):
							selection = None
							items = []
							for j in range(len(type)):
								items.append(self.settingsFormat(type = type, value = list(type[j].keys())[0], default = default, format = format))
								if list(type[j].keys())[0] == value: selection = j
							value = Dialog.select(title = item[ProviderBase.SettingsLabel], selection = selection, items = items)
							if value >= 0: value = list(type[value].keys())[0]
							else: break
						else:
							try: selection = type.index(value)
							except: selection = None
							items = []
							for j in range(len(type)):
								items.append(self.settingsFormat(type = type, value = type[j], default = default, format = format))
							value = Dialog.select(title = item[ProviderBase.SettingsLabel], selection = selection, items = items)
							if value < 0: break

					self.mSettings[category][id] = value
					if refresh and not before == value: self.initializeSettings(type = refresh)
					break

	##############################################################################
	# SETTINGS - DATA
	##############################################################################

	def settingsData(self):
		return self.mSettings

	def settingsDataDefault(self):
		return {
			ProviderBase.SettingsCategoryScrape : {},
			ProviderBase.SettingsCategoryCustom : {},
			'link' : None,
			'account' : None,
			'enabled' : {
				'type' : None,
				'mode' : None,
				'access' : None,
				'addon' : None,
				'provider' : None,
			},
		}

	def settingsDataClear(self, type = None):
		settings = self.settingsDataDefault()
		if type and not type is True: self.mSettings[type] = settings[type]
		else: self.mSettings = settings

	def settingsDataEnabledClear(self, type = None):
		settings = self.settingsDataDefault()
		if type and not type is True: self.mSettings['enabled'][type] = settings['enabled'][type]
		else: self.mSettings['enabled'] = settings['enabled']

	def settingsDataUpdate(self, data):
		# Delete non-custom (default) links.
		# Otherwise when the hardcoded links in the provider Python code change on a new version, the old links are pulled in from the settings.
		# Ignore non-custom links, which will then use the new ones from the Python code.
		if data['link']: data['link'] = [i for i in data['link'] if i['custom']]

		return Tools.update(self.mSettings, data)

	def settingsDataImport(self, data):
		if Tools.isString(data): data = Converter.jsonFrom(data)
		elif Tools.isInstance(data, ProviderBase): data = Tools.copy(data.settingsData())
		self.settingsDataUpdate(data)

	def settingsDataExport(self, data):
		return Converter.jsonTo(self.mSettings)

	##############################################################################
	# SETTINGS - GLOBAL
	##############################################################################

	@classmethod
	def settingsGlobalLimitTime(self):
		result = ProviderBase.SettingsData['limit'][ProviderBase.ScrapeTime]
		if result is None: result = ProviderBase.SettingsData['limit'][ProviderBase.ScrapeTime] = Settings.getCustom(ProviderBase.SettingsGlobalLimitTime)
		return result

	@classmethod
	def settingsGlobalLimitTimeSet(self, value):
		Settings.setCustom(ProviderBase.SettingsGlobalLimitTime, value)
		ProviderBase.SettingsData['limit'][ProviderBase.ScrapeTime] = None

	@classmethod
	def settingsGlobalLimitTimeLabel(self, value = None):
		if value is None: value = self.settingsGlobalLimitTime()
		return Settings.customLabel(id = ProviderBase.SettingsGlobalLimitTime, value = value)

	@classmethod
	def settingsGlobalLimitQuery(self):
		result = ProviderBase.SettingsData['limit'][ProviderBase.ScrapeQuery]
		if result is None: result = ProviderBase.SettingsData['limit'][ProviderBase.ScrapeQuery] = Settings.getCustom(ProviderBase.SettingsGlobalLimitQuery)
		return result

	@classmethod
	def settingsGlobalLimitQuerySet(self, value):
		Settings.setCustom(ProviderBase.SettingsGlobalLimitQuery, value)
		ProviderBase.SettingsData['limit'][ProviderBase.ScrapeQuery] = None

	@classmethod
	def settingsGlobalLimitQueryLabel(self, value = None):
		if value is None: value = self.settingsGlobalLimitQuery()
		return Settings.customLabel(id = ProviderBase.SettingsGlobalLimitQuery, value = value)

	@classmethod
	def settingsGlobalLimitPage(self):
		result = ProviderBase.SettingsData['limit'][ProviderBase.ScrapePage]
		if result is None: result = ProviderBase.SettingsData['limit'][ProviderBase.ScrapePage] = Settings.getCustom(ProviderBase.SettingsGlobalLimitPage)
		return result

	@classmethod
	def settingsGlobalLimitPageSet(self, value, temporary = False):
		if temporary:
			ProviderBase.SettingsData['limit'][ProviderBase.ScrapePage] = value
		else:
			Settings.setCustom(ProviderBase.SettingsGlobalLimitPage, value)
			ProviderBase.SettingsData['limit'][ProviderBase.ScrapePage] = None

	@classmethod
	def settingsGlobalLimitPageLabel(self, value = None):
		if value is None: value = self.settingsGlobalLimitPage()
		return Settings.customLabel(id = ProviderBase.SettingsGlobalLimitPage, value = value)

	@classmethod
	def settingsGlobalLimitRequest(self):
		result = ProviderBase.SettingsData['limit'][ProviderBase.ScrapeRequest]
		if result is None: result = ProviderBase.SettingsData['limit'][ProviderBase.ScrapeRequest] = Settings.getCustom(ProviderBase.SettingsGlobalLimitRequest)
		return result

	@classmethod
	def settingsGlobalLimitRequestSet(self, value):
		Settings.setCustom(ProviderBase.SettingsGlobalLimitRequest, value)
		ProviderBase.SettingsData['limit'][ProviderBase.ScrapeRequest] = None

	@classmethod
	def settingsGlobalLimitRequestLabel(self, value = None):
		if value is None: value = self.settingsGlobalLimitRequest()
		return Settings.customLabel(id = ProviderBase.SettingsGlobalLimitRequest, value = value)

	@classmethod
	def settingsGlobalSaveStream(self):
		result = ProviderBase.SettingsData['save']['stream']
		if result is None: result = ProviderBase.SettingsData['save']['stream'] = Settings.getCustom(ProviderBase.SettingsGlobalSaveStream)
		return result

	@classmethod
	def settingsGlobalSaveStreamSet(self, value):
		Settings.setCustom(ProviderBase.SettingsGlobalSaveStream, value)
		ProviderBase.SettingsData['save']['stream'] = None

	@classmethod
	def settingsGlobalSaveStreamLabel(self, value = None):
		if value is None: value = self.settingsGlobalSaveStream()
		return Settings.customLabel(id = ProviderBase.SettingsGlobalSaveStream, value = value)

	@classmethod
	def settingsGlobalSaveCache(self):
		result = ProviderBase.SettingsData['save']['cache']
		if result is None: result = ProviderBase.SettingsData['save']['cache'] = Settings.getCustom(ProviderBase.SettingsGlobalSaveCache)
		return result

	@classmethod
	def settingsGlobalSaveCacheSet(self, value):
		Settings.setCustom(ProviderBase.SettingsGlobalSaveCache, value)
		ProviderBase.SettingsData['save']['cache'] = None

	@classmethod
	def settingsGlobalSaveCacheLabel(self, value = None):
		if value is None: value = self.settingsGlobalSaveCache()
		return Settings.customLabel(id = ProviderBase.SettingsGlobalSaveCache, value = value)

	@classmethod
	def settingsGlobalSaveExpression(self):
		result = ProviderBase.SettingsData['save']['expression']
		if result is None: result = ProviderBase.SettingsData['save']['expression'] = Settings.getInteger(ProviderBase.SettingsGlobalSaveExpression)
		return result

	@classmethod
	def settingsGlobalSaveExpressionSet(self, value):
		Settings.set(ProviderBase.SettingsGlobalSaveExpression, value)
		ProviderBase.SettingsData['save']['expression'] = None

	@classmethod
	def settingsGlobalPackEnabled(self):
		result = ProviderBase.SettingsData['pack']['enabled']
		if result is None: result = ProviderBase.SettingsData['pack']['enabled'] = Settings.getBoolean(ProviderBase.SettingsGlobalPackEnabled)
		return result

	@classmethod
	def settingsGlobalPackEnabledSet(self, value):
		Settings.set(ProviderBase.SettingsGlobalPackEnabled, value)
		ProviderBase.SettingsData['pack']['enabled'] = None

	@classmethod
	def settingsGlobalPackMovie(self):
		if self.settingsGlobalPackEnabled():
			result = ProviderBase.SettingsData['pack']['movie']
			if result is None: result = ProviderBase.SettingsData['pack']['movie'] = Settings.getBoolean(ProviderBase.SettingsGlobalPackMovie)
			return result
		return False

	@classmethod
	def settingsGlobalPackMovieSet(self, value):
		Settings.set(ProviderBase.SettingsGlobalPackMovie, value)
		ProviderBase.SettingsData['pack']['movie'] = None

	@classmethod
	def settingsGlobalPackShow(self):
		if self.settingsGlobalPackEnabled():
			result = ProviderBase.SettingsData['pack']['show']
			if result is None: result = ProviderBase.SettingsData['pack']['show'] = Settings.getBoolean(ProviderBase.SettingsGlobalPackShow)
			return result
		return False

	@classmethod
	def settingsGlobalPackShowSet(self, value):
		Settings.set(ProviderBase.SettingsGlobalPackShow, value)
		ProviderBase.SettingsData['pack']['show'] = None

	@classmethod
	def settingsGlobalPackSeason(self):
		if self.settingsGlobalPackEnabled():
			result = ProviderBase.SettingsData['pack']['season']
			if result is None: result = ProviderBase.SettingsData['pack']['season'] = Settings.getBoolean(ProviderBase.SettingsGlobalPackSeason)
			return result
		return False

	@classmethod
	def settingsGlobalPackSeasonSet(self, value):
		Settings.set(ProviderBase.SettingsGlobalPackSeason, value)
		ProviderBase.SettingsData['pack']['season'] = None

	@classmethod
	def settingsGlobalTitleEnabled(self):
		result = ProviderBase.SettingsData['title']['enabled']
		if result is None: result = ProviderBase.SettingsData['title']['enabled'] = Settings.getBoolean(ProviderBase.SettingsGlobalTitleEnabled)
		return result

	@classmethod
	def settingsGlobalTitleEnabledSet(self, value):
		Settings.set(ProviderBase.SettingsGlobalTitleEnabled, value)
		ProviderBase.SettingsData['title']['enabled'] = None

	@classmethod
	def settingsGlobalTitleCharacter(self):
		if self.settingsGlobalTitleEnabled():
			result = ProviderBase.SettingsData['title']['character']
			if result is None: result = ProviderBase.SettingsData['title']['character'] = Settings.getBoolean(ProviderBase.SettingsGlobalTitleCharacter)
			return result
		return False

	@classmethod
	def settingsGlobalTitleCharacterSet(self, value):
		Settings.set(ProviderBase.SettingsGlobalTitleCharacter, value)
		ProviderBase.SettingsData['title']['character'] = None

	@classmethod
	def settingsGlobalTitleOriginal(self):
		if self.settingsGlobalTitleEnabled():
			result = ProviderBase.SettingsData['title']['original']
			if result is None: result = ProviderBase.SettingsData['title']['original'] = Settings.getBoolean(ProviderBase.SettingsGlobalTitleOriginal)
			return result
		return False

	@classmethod
	def settingsGlobalTitleOriginalSet(self, value):
		Settings.set(ProviderBase.SettingsGlobalTitleOriginal, value)
		ProviderBase.SettingsData['title']['original'] = None

	@classmethod
	def settingsGlobalTitleNative(self):
		if self.settingsGlobalTitleEnabled():
			result = ProviderBase.SettingsData['title']['native']
			if result is None: result = ProviderBase.SettingsData['title']['native'] = Settings.getBoolean(ProviderBase.SettingsGlobalTitleNative)
			return result
		return False

	@classmethod
	def settingsGlobalTitleNativeSet(self, value):
		Settings.set(ProviderBase.SettingsGlobalTitleNative, value)
		ProviderBase.SettingsData['title']['native'] = None

	@classmethod
	def settingsGlobalTitleLocal(self):
		if self.settingsGlobalTitleEnabled():
			result = ProviderBase.SettingsData['title']['local']
			if result is None: result = ProviderBase.SettingsData['title']['local'] = Settings.getBoolean(ProviderBase.SettingsGlobalTitleLocal)
			return result
		return False

	@classmethod
	def settingsGlobalTitleLocalSet(self, value):
		Settings.set(ProviderBase.SettingsGlobalTitleLocal, value)
		ProviderBase.SettingsData['title']['local'] = None

	@classmethod
	def settingsGlobalTitleAlias(self):
		if self.settingsGlobalTitleEnabled():
			result = ProviderBase.SettingsData['title']['alias']
			if result is None: result = ProviderBase.SettingsData['title']['alias'] = Settings.getBoolean(ProviderBase.SettingsGlobalTitleAlias)
			return result
		return False

	@classmethod
	def settingsGlobalTitleAliasSet(self, value):
		Settings.set(ProviderBase.SettingsGlobalTitleAlias, value)
		ProviderBase.SettingsData['title']['alias'] = None

	@classmethod
	def settingsGlobalTitleLanguage(self):
		if self.settingsGlobalTitleEnabled():
			result = ProviderBase.SettingsData['title']['language']
			if result is None:
				language = Language.settingsCustom(ProviderBase.SettingsGlobalTitleLanguage, default = Language.Alternative)
				result = ProviderBase.SettingsData['title']['language'] = language
			return result
		return None

	@classmethod
	def settingsGlobalKeywordEnabled(self):
		result = ProviderBase.SettingsData['keyword']['enabled']
		if result is None: result = ProviderBase.SettingsData['keyword']['enabled'] = Settings.getBoolean(ProviderBase.SettingsGlobalKeywordEnabled)
		return result

	@classmethod
	def settingsGlobalKeywordEnabledSet(self, value):
		Settings.set(ProviderBase.SettingsGlobalKeywordEnabled, value)
		ProviderBase.SettingsData['keyword']['enabled'] = None

	@classmethod
	def settingsGlobalKeywordEnglish(self):
		if self.settingsGlobalKeywordEnabled():
			result = ProviderBase.SettingsData['keyword']['english']
			if result is None: result = ProviderBase.SettingsData['keyword']['english'] = Settings.getInteger(ProviderBase.SettingsGlobalKeywordEnglish)
			return result
		return None

	@classmethod
	def settingsGlobalKeywordEnglishSet(self, value):
		Settings.set(ProviderBase.SettingsGlobalKeywordEnglish, value)
		ProviderBase.SettingsData['keyword']['english'] = None

	@classmethod
	def settingsGlobalKeywordOriginal(self):
		if self.settingsGlobalKeywordEnabled():
			result = ProviderBase.SettingsData['keyword']['original']
			if result is None: result = ProviderBase.SettingsData['keyword']['original'] = Settings.getInteger(ProviderBase.SettingsGlobalKeywordOriginal)
			return result
		return None

	@classmethod
	def settingsGlobalKeywordOriginalSet(self, value):
		Settings.set(ProviderBase.SettingsGlobalKeywordOriginal, value)
		ProviderBase.SettingsData['keyword']['original'] = None

	@classmethod
	def settingsGlobalKeywordNative(self):
		if self.settingsGlobalKeywordEnabled():
			result = ProviderBase.SettingsData['keyword']['native']
			if result is None: result = ProviderBase.SettingsData['keyword']['native'] = Settings.getInteger(ProviderBase.SettingsGlobalKeywordNative)
			return result
		return None

	@classmethod
	def settingsGlobalKeywordNativeSet(self, value):
		Settings.set(ProviderBase.SettingsGlobalKeywordNative, value)
		ProviderBase.SettingsData['keyword']['native'] = None

	@classmethod
	def settingsGlobalKeywordCustom(self):
		if self.settingsGlobalKeywordEnabled():
			result = ProviderBase.SettingsData['keyword']['custom']
			if result is None: result = ProviderBase.SettingsData['keyword']['custom'] = Settings.getInteger(ProviderBase.SettingsGlobalKeywordCustom)
			return result
		return None

	@classmethod
	def settingsGlobalKeywordCustomSet(self, value):
		Settings.set(ProviderBase.SettingsGlobalKeywordCustom, value)
		ProviderBase.SettingsData['keyword']['custom'] = None

	@classmethod
	def settingsGlobalKeywordLanguage(self):
		if self.settingsGlobalKeywordEnabled():
			result = ProviderBase.SettingsData['keyword']['language']
			if result is None:
				language = Language.settingsCustom(ProviderBase.SettingsGlobalKeywordLanguage, default = Language.Alternative)
				result = ProviderBase.SettingsData['keyword']['language'] = language
			return result
		return None

	@classmethod
	def settingsGlobalYearEnabled(self):
		result = ProviderBase.SettingsData['year']['enabled']
		if result is None: result = ProviderBase.SettingsData['year']['enabled'] = Settings.getBoolean(ProviderBase.SettingsGlobalYearEnabled)
		return result

	@classmethod
	def settingsGlobalYearEnabledSet(self, value):
		Settings.set(ProviderBase.SettingsGlobalYearEnabled, value)
		ProviderBase.SettingsData['year']['enabled'] = None

	@classmethod
	def settingsGlobalMirrorEnabled(self):
		result = ProviderBase.SettingsData['mirror']['enabled']
		if result is None: result = ProviderBase.SettingsData['mirror']['enabled'] = Settings.getBoolean(ProviderBase.SettingsGlobalMirrorEnabled)
		return result

	@classmethod
	def settingsGlobalMirrorEnabledSet(self, value):
		Settings.set(ProviderBase.SettingsGlobalMirrorEnabled, value)
		ProviderBase.SettingsData['mirror']['enabled'] = None

	@classmethod
	def settingsGlobalMirrorLimit(self):
		if self.settingsGlobalMirrorEnabled():
			result = ProviderBase.SettingsData['mirror']['limit']
			if result is None: result = ProviderBase.SettingsData['mirror']['limit'] = Settings.getInteger(ProviderBase.SettingsGlobalMirrorLimit)
			return result
		return 0

	@classmethod
	def settingsGlobalMirrorLimitSet(self, value):
		Settings.set(ProviderBase.SettingsGlobalMirrorLimit, value)
		ProviderBase.SettingsData['mirror']['limit'] = None

	@classmethod
	def settingsGlobalUnblockEnabled(self):
		result = ProviderBase.SettingsData['unblock']['enabled']
		if result is None: result = ProviderBase.SettingsData['unblock']['enabled'] = Settings.getBoolean(ProviderBase.SettingsGlobalUnblockEnabled)
		return result

	@classmethod
	def settingsGlobalUnblockType(self):
		if self.settingsGlobalUnblockEnabled():
			result = ProviderBase.SettingsData['unblock']['type']
			if result is None: result = ProviderBase.SettingsData['unblock']['type'] = Settings.getInteger(ProviderBase.SettingsGlobalUnblockType)
			return result
		return 0

	@classmethod
	def settingsGlobalUnblockLink(self):
		if self.settingsGlobalUnblockEnabled():
			result = ProviderBase.SettingsData['unblock']['link']
			if result is None: result = ProviderBase.SettingsData['unblock']['link'] = Settings.getString(ProviderBase.SettingsGlobalUnblockLink)
			return result
		return ''

	@classmethod
	def settingsGlobalUnblockFormat(self):
		if self.settingsGlobalUnblockEnabled():
			result = ProviderBase.SettingsData['unblock']['format']
			if result is None: result = ProviderBase.SettingsData['unblock']['format'] = Settings.getInteger(ProviderBase.SettingsGlobalUnblockFormat)
			return result
		return 0

	##############################################################################
	# SCRAPE
	##############################################################################

	def scrape(self, id = None, settings = True):
		return self.settings(category = ProviderBase.SettingsCategoryScrape, id = id, settings = settings)

	def scrapeSet(self, value, id = None, settings = True):
		return self.settingsSet(category = ProviderBase.SettingsCategoryScrape, value = value, id = id, settings = settings)

	def scrapeId(self):
		return self.settingsId(category = ProviderBase.SettingsCategoryScrape)

	def scrapeHas(self, id):
		return self.settingsHas(category = ProviderBase.SettingsCategoryScrape, id = id)

	def scrapeAttributes(self):
		return self.settingsAttributes(category = ProviderBase.SettingsCategoryScrape)

	@classmethod
	def scrapeAttributesAll(self):
		return self._settingsAttributes(category = ProviderBase.SettingsCategoryScrape, data = {ProviderBase.SettingsCategoryScrape : self.scrapeInitialize()})

	def scrapeDialog(self, id = None):
		return self.settingsDialog(category = ProviderBase.SettingsCategoryScrape, id = id)

	@classmethod
	def scrapeInitialize(self, priority = None, termination = None, time = None, query = None, pages = None, requests = None):
		result = [
			self.scrapePriorityInitialize(default = priority),
			self.scrapeTerminationInitialize(default = termination),
			self.scrapeTimeInitialize(default = time),
			self.scrapeQueryInitialize(default = query),
			self.scrapePageInitialize(default = pages),
			self.scrapeRequestInitialize(default = requests),
		]
		result = [i for i in result if i]
		return result

	##############################################################################
	# SCRAPE - PRIORITY
	##############################################################################

	def scrapePriority(self, settings = True):
		return self.scrape(id = ProviderBase.ScrapePriority, settings = settings)

	def scrapePrioritySet(self, priority, settings = True):
		return self.scrapeSet(id = ProviderBase.ScrapePriority, settings = settings, value = priority)

	@classmethod
	def scrapePriorityInitialize(self, default = None):
		if default is False: return None
		return {
			ProviderBase.SettingsId				: ProviderBase.ScrapePriority,
			ProviderBase.SettingsLabel			: 33169,
			ProviderBase.SettingsDefault		: default,
			ProviderBase.SettingsType			: ProviderBase.SettingsTypeNumber,
			ProviderBase.SettingsFormat			: {ProviderBase.SettingsValueGeneral : ProviderBase.SettingsFormatRank, ProviderBase.SettingsValueNone : ProviderBase.SettingsDefault, ProviderBase.SettingsValueZero : ProviderBase.SettingsDefault},
			ProviderBase.SettingsDescription	: 34344,
		}

	##############################################################################
	# SCRAPE - TERMINATION
	##############################################################################

	def scrapeTermination(self, settings = True):
		return self.scrape(id = ProviderBase.ScrapeTermination, settings = settings)

	def scrapeTerminationSet(self, value, settings = True):
		return self.scrapeSet(id = ProviderBase.ScrapeTermination, settings = settings, value = value)

	@classmethod
	def scrapeTerminationInitialize(self, default = None):
		if default is False: return None
		return {
			ProviderBase.SettingsId				: ProviderBase.ScrapeTermination,
			ProviderBase.SettingsLabel			: 35812,
			ProviderBase.SettingsDefault		: default,
			ProviderBase.SettingsType			: ProviderBase.SettingsTypeNumber,
			ProviderBase.SettingsFormat			: {ProviderBase.SettingsValueGeneral : ProviderBase.SettingsFormatLinks, ProviderBase.SettingsValueNone : ProviderBase.SettingsDefault, ProviderBase.SettingsValueZero : ProviderBase.SettingsDefault},
			ProviderBase.SettingsDescription	: 34345,
		}

	##############################################################################
	# SCRAPE - TIME
	##############################################################################

	def scrapeTime(self, settings = True, default = False, factor = TimeFactorFull):
		result = self.scrape(id = ProviderBase.ScrapeTime, settings = settings)
		if default and result is None: result = self.settingsGlobalLimitTime()
		return (factor * result) if result else result

	def scrapeTimeSet(self, value, settings = True):
		return self.scrapeSet(id = ProviderBase.ScrapeTime, settings = settings, value = value)

	@classmethod
	def scrapeTimeInitialize(self, default = None):
		if default is False: return None
		return {
			ProviderBase.SettingsId				: ProviderBase.ScrapeTime,
			ProviderBase.SettingsLabel			: 32312,
			ProviderBase.SettingsDefault		: default,
			ProviderBase.SettingsType			: ProviderBase.SettingsTypeNumber,
			ProviderBase.SettingsFormat			: {ProviderBase.SettingsValueGeneral : ProviderBase.SettingsFormatDuration, ProviderBase.SettingsValueNone : ProviderBase.SettingsDefault, ProviderBase.SettingsValueZero : ProviderBase.SettingsDefault},
			ProviderBase.SettingsDescription	: 34377,
		}

	##############################################################################
	# SCRAPE - QUERY
	##############################################################################

	def scrapeQuery(self, settings = True, default = False):
		result = self.scrape(id = ProviderBase.ScrapeQuery, settings = settings)
		if default and result is None: result = self.settingsGlobalLimitQuery()
		return result

	def scrapeQuerySet(self, value, settings = True):
		return self.scrapeSet(id = ProviderBase.ScrapeQuery, settings = settings, value = value)

	def scrapeQueryHas(self):
		return self.scrapeHas(id = ProviderBase.ScrapeQuery)

	def scrapeQueryIncrease(self, value = 1):
		id = self.idInstance()
		if not id in ProviderBase.ScrapeCountQuery: ProviderBase.ScrapeCountQuery[id] = 0
		ProviderBase.ScrapeCountQuery[id] += value

	def scrapeQueryAllow(self, increase = False):
		if self.verifyBusy(): return True
		limit = self.scrapeQuery(settings = True, default = True)
		if not limit: return True
		id = self.idInstance() # Use the instance ID instead of the provider ID, since we want a page limit per query, and not a global limit over all instances of that provider, like the request limit.
		if not id in ProviderBase.ScrapeCountQuery: result = True
		else: result = ProviderBase.ScrapeCountQuery[id] < limit
		if increase: self.scrapeQueryIncrease()
		return result

	@classmethod
	def scrapeQueryInitialize(self, default = None):
		if default is False: return None
		return {
			ProviderBase.SettingsId				: ProviderBase.ScrapeQuery,
			ProviderBase.SettingsLabel			: 33329,
			ProviderBase.SettingsDefault		: default,
			ProviderBase.SettingsType			: ProviderBase.SettingsTypeNumber,
			ProviderBase.SettingsFormat			: {ProviderBase.SettingsValueGeneral : ProviderBase.SettingsFormatQuery, ProviderBase.SettingsValueNone : ProviderBase.SettingsDefault, ProviderBase.SettingsValueZero : ProviderBase.SettingsDefault},
			ProviderBase.SettingsDescription	: 34497,
		}

	##############################################################################
	# SCRAPE - PAGE
	##############################################################################

	def scrapePage(self, settings = True, default = False):
		result = self.scrape(id = ProviderBase.ScrapePage, settings = settings)
		if default and result is None: result = self.settingsGlobalLimitPage()
		return result

	def scrapePageSet(self, value, settings = True):
		return self.scrapeSet(id = ProviderBase.ScrapePage, settings = settings, value = value)

	def scrapePageHas(self):
		return self.scrapeHas(id = ProviderBase.ScrapePage)

	def scrapePageIncrease(self, value = 1):
		id = self.idInstance()
		if not id in ProviderBase.ScrapeCountPages: ProviderBase.ScrapeCountPages[id] = 0
		ProviderBase.ScrapeCountPages[id] += value

	def scrapePageAllow(self, increase = False):
		if self.verifyBusy(): return True
		limit = self.scrapePage(settings = True, default = True)
		if not limit: return True
		id = self.idInstance() # Use the instance ID instead of the provider ID, since we want a page limit per query, and not a global limit over all instances of that provider, like the request limit.
		if not id in ProviderBase.ScrapeCountPages: result = True
		else: result = ProviderBase.ScrapeCountPages[id] < limit
		if increase: self.scrapePageIncrease()
		return result

	@classmethod
	def scrapePageInitialize(self, default = None):
		if default is False: return None
		return {
			ProviderBase.SettingsId				: ProviderBase.ScrapePage,
			ProviderBase.SettingsLabel			: 35307,
			ProviderBase.SettingsDefault		: default,
			ProviderBase.SettingsType			: ProviderBase.SettingsTypeNumber,
			ProviderBase.SettingsFormat			: {ProviderBase.SettingsValueGeneral : ProviderBase.SettingsFormatPage, ProviderBase.SettingsValueNone : ProviderBase.SettingsDefault, ProviderBase.SettingsValueZero : ProviderBase.SettingsValueUnlimited},
			ProviderBase.SettingsDescription	: 34378,
		}

	##############################################################################
	# SCRAPE - REQUEST
	##############################################################################

	def scrapeRequest(self, settings = True, default = False):
		result = self.scrape(id = ProviderBase.ScrapeRequest, settings = settings)
		if default and result is None: result = self.settingsGlobalLimitRequest()
		return result

	def scrapeRequestSet(self, value, settings = True):
		return self.scrapeSet(id = ProviderBase.ScrapeRequest, settings = settings, value = value)

	def scrapeRequestHas(self):
		return self.scrapeHas(id = ProviderBase.ScrapeRequest)

	def scrapeRequestIncrease(self, value = 1):
		id = self.id()
		if not id in ProviderBase.ScrapeCountRequests: ProviderBase.ScrapeCountRequests[id] = 0
		ProviderBase.ScrapeCountRequests[id] += value

	def scrapeRequestAllow(self, increase = False):
		if self.verifyBusy(): return True
		limit = self.scrapeRequest(settings = True, default = True)
		if not limit: return True
		id = self.id()
		if not id in ProviderBase.ScrapeCountRequests: result = True
		else: result = ProviderBase.ScrapeCountRequests[id] < limit
		if increase: self.scrapeRequestIncrease()
		return result

	@classmethod
	def scrapeRequestInitialize(self, default = None):
		if default is False: return None
		return {
			ProviderBase.SettingsId				: ProviderBase.ScrapeRequest,
			ProviderBase.SettingsLabel			: 35806,
			ProviderBase.SettingsDefault		: default,
			ProviderBase.SettingsType			: ProviderBase.SettingsTypeNumber,
			ProviderBase.SettingsFormat			: {ProviderBase.SettingsValueGeneral : ProviderBase.SettingsFormatRequest, ProviderBase.SettingsValueNone : ProviderBase.SettingsDefault, ProviderBase.SettingsValueZero : ProviderBase.SettingsValueUnlimited},
			ProviderBase.SettingsDescription	: 34379,
		}

	##############################################################################
	# CUSTOM
	##############################################################################

	def custom(self, id = None, settings = True):
		return self.settings(category = ProviderBase.SettingsCategoryCustom, id = id, settings = settings)

	def customSet(self, value, id = None, settings = True):
		return self.settingsSet(category = ProviderBase.SettingsCategoryCustom, value = value, id = id, settings = settings)

	def customId(self):
		return self.settingsId(category = ProviderBase.SettingsCategoryCustom)

	def customHas(self, id):
		return self.settingsHas(category = ProviderBase.SettingsCategoryCustom, id = id)

	def customAttributes(self):
		return self.settingsAttributes(category = ProviderBase.SettingsCategoryCustom)

	def customDialog(self, id = None):
		return self.settingsDialog(category = ProviderBase.SettingsCategoryCustom, id = id)

	def customExecute(self, id):
		return None

	def customInitialize(self, custom = None, version = None, size = None, time = None, peers = None, seeds = None, leeches = None, search = None, category = None, verified = None, spam = None, adult = None, password = None, incomplete = None):
		extra = []
		if custom and Tools.isDictionary(custom): custom = [custom]

		# Order matters for the settingfs dialog. Showq important ones first.
		if version: extra.append(self.customVersionInitialize(version))

		if search: extra.append(self.customSearchInitialize(search))
		if category: extra.append(self.customCategoryInitialize(category))

		if verified: extra.append(self.customVerifiedInitialize(verified))
		if spam: extra.append(self.customSpamInitialize(spam))
		if adult: extra.append(self.customAdultInitialize(adult))
		if password: extra.append(self.customPasswordInitialize(password))
		if incomplete: extra.append(self.customIncompleteInitialize(incomplete))

		if size: extra.append(self.customSizeInitialize(size))
		if time: extra.append(self.customTimeInitialize(time))
		if peers: extra.append(self.customPeersInitialize(peers))
		if seeds: extra.append(self.customSeedsInitialize(seeds))
		if leeches: extra.append(self.customLeechesInitialize(leeches))

		extra = [i for i in extra if not i is None]
		if extra:
			if not custom: custom = []
			extra.extend(custom)
			custom = extra

		if custom:
			for i in range(len(custom)):
				custom[i]['settings'] = None
				if ProviderBase.SettingsFormat in custom[i]:
					customFormat = custom[i][ProviderBase.SettingsFormat]
					if customFormat and not Tools.isDictionary(customFormat):
						customFormat = {ProviderBase.SettingsValueGeneral : customFormat}
					if not ProviderBase.SettingsValueNone in customFormat:
						customFormat[ProviderBase.SettingsValueNone] = ProviderBase.SettingsValueNone
					if not ProviderBase.SettingsValueDefault in customFormat and not Tools.isArray(custom[i][ProviderBase.SettingsType]): # Do not add "default" for lists, otherwise the version shows "Default".
						customFormat[ProviderBase.SettingsDefault] = ProviderBase.SettingsDefault
					if custom[i][ProviderBase.SettingsType] == ProviderBase.SettingsTypeBoolean:
						if not True in customFormat: customFormat[True] = 32301
						if not False in customFormat: customFormat[False] = 32302
					custom[i][ProviderBase.SettingsFormat] = customFormat
				if Tools.isArray(custom[i][ProviderBase.SettingsType]) and not ProviderBase.SettingsDefault in custom[i]:
					if Tools.isDictionary(custom[i][ProviderBase.SettingsType][0]): custom[i][ProviderBase.SettingsDefault] = list(custom[i][ProviderBase.SettingsType][0].keys())[0]
					else: custom[i][ProviderBase.SettingsDefault] = 0

		return custom

	##############################################################################
	# CUSTOM - VERSION
	##############################################################################

	def customVersion(self, default = VersionDefault, settings = True):
		result = self.custom(id = ProviderBase.CustomVersion, settings = settings)
		if result is None and not default is None: result = default
		return result

	def customVersionSet(self, value, initialize = False, settings = True):
		self.customSet(id = ProviderBase.CustomVersion, value = value, settings = settings)
		if initialize: self.initializeSettings(type = 'link')

	def customVersionHas(self):
		return self.customHas(id = ProviderBase.CustomVersion)

	def customVersionInitialize(self, custom):
		if Tools.isInteger(custom): custom = [i for i in range(1, custom + 1)]
		if Tools.isArray(custom): custom = [str(i) for i in custom]

		try: default = list(custom[0].keys())[0]
		except: default = 0

		result = {
			ProviderBase.SettingsId				: ProviderBase.CustomVersion,
			ProviderBase.SettingsLabel			: 'Scraper Version',
			ProviderBase.SettingsRefresh		: 'link', # Clear the domains and reinitialize the provider.
			ProviderBase.SettingsDefault		: default,
			ProviderBase.SettingsType			: None,
			ProviderBase.SettingsFormat			: ProviderBase.SettingsFormatVersion,
			ProviderBase.SettingsDescription	: 'Use a specific version of the website or API. These versions have different structures or layouts that are incompatible with each other and require alternative code to be scraped. Some versions might contain inaccurate metadata or require requests to subpages which takes substantially longer to scrape.',
		}
		if Tools.isDictionary(custom): result = self.settingsCustomize(custom = custom, default = result)
		else: result[ProviderBase.SettingsType] = custom
		return result

	def customVersion1(self):
		return self.customVersion() == ProviderBase.Version1

	def customVersion2(self):
		return self.customVersion() == ProviderBase.Version2

	def customVersion3(self):
		return self.customVersion() == ProviderBase.Version3

	def customVersion4(self):
		return self.customVersion() == ProviderBase.Version4

	def customVersion5(self):
		return self.customVersion() == ProviderBase.Version5

	def customVersion6(self):
		return self.customVersion() == ProviderBase.Version6

	def customVersion7(self):
		return self.customVersion() == ProviderBase.Version7

	def customVersion8(self):
		return self.customVersion() == ProviderBase.Version8

	def customVersion9(self):
		return self.customVersion() == ProviderBase.Version9

	def customVersionAutomatic(self):
		return self.customVersion() == ProviderBase.VersionAutomatic

	def customVersionNone(self):
		return self.customVersion() is ProviderBase.VersionNone

	##############################################################################
	# CUSTOM - SIZE
	##############################################################################

	def customSize(self, bytes = True, settings = True):
		result = self.custom(id = ProviderBase.CustomSize, settings = settings)
		if bytes and result: result *= 1048576
		return result

	def customSizeSet(self, value, settings = True):
		self.customSet(id = ProviderBase.CustomSize, value = value, settings = settings)

	def customSizeHas(self):
		return self.customHas(id = ProviderBase.CustomSize)

	def customSizeInitialize(self, custom):
		return self.settingsCustomize(custom = custom, default = {
			ProviderBase.SettingsId				: ProviderBase.CustomSize,
			ProviderBase.SettingsLabel			: 'Minimum Size',
			ProviderBase.SettingsDefault		: None,
			ProviderBase.SettingsType			: ProviderBase.SettingsTypeNumber,
			ProviderBase.SettingsFormat			: {ProviderBase.SettingsValueGeneral : ProviderBase.SettingsFormatSize, ProviderBase.SettingsValueZero : ProviderBase.SettingsValueNone},
			ProviderBase.SettingsDescription	: 'Only retrieve {containers} that have a minimum file size.',
		})

	##############################################################################
	# CUSTOM - TIME
	##############################################################################

	def customTime(self, days = False, settings = True):
		result = self.custom(id = ProviderBase.CustomTime, settings = settings)
		if not days and result: result *= 86400 # Stored as days, returns seconds.
		return result

	def customTimeSet(self, value, settings = True):
		self.customSet(id = ProviderBase.CustomTime, value = value, settings = settings)

	def customTimeHas(self):
		return self.customHas(id = ProviderBase.CustomTime)

	def customTimeInitialize(self, custom):
		return self.settingsCustomize(custom = custom, default = {
			ProviderBase.SettingsId				: ProviderBase.CustomTime,
			ProviderBase.SettingsLabel			: 'Maximum Age',
			ProviderBase.SettingsDefault		: None,
			ProviderBase.SettingsType			: ProviderBase.SettingsTypeNumber,
			ProviderBase.SettingsFormat			: {ProviderBase.SettingsValueGeneral : ProviderBase.SettingsFormatDays, ProviderBase.SettingsValueZero : ProviderBase.SettingsValueNone},
			ProviderBase.SettingsDescription	: 'The maximum age of the {container} upload. Older {containers} will be discarded.',
		})

	##############################################################################
	# CUSTOM - PEERS
	##############################################################################

	def customPeers(self, settings = True):
		return self.custom(id = ProviderBase.CustomPeers, settings = settings)

	def customPeersSet(self, value, settings = True):
		self.customSet(id = ProviderBase.CustomPeers, value = value, settings = settings)

	def customPeersHas(self):
		return self.customHas(id = ProviderBase.CustomPeers)

	def customPeersInitialize(self, custom):
		return self.settingsCustomize(custom = custom, default = {
			ProviderBase.SettingsId				: ProviderBase.CustomPeers,
			ProviderBase.SettingsLabel			: 'Minimum Peers',
			ProviderBase.SettingsDefault		: None,
			ProviderBase.SettingsType			: ProviderBase.SettingsTypeNumber,
			ProviderBase.SettingsFormat			: {ProviderBase.SettingsValueGeneral : ProviderBase.SettingsFormatPeers, ProviderBase.SettingsValueZero : ProviderBase.SettingsValueNone},
			ProviderBase.SettingsDescription	: 'Only retrieve {containers} that have a minimum number of peers.',
		})

	##############################################################################
	# CUSTOM - SEEDS
	##############################################################################

	def customSeeds(self, settings = True):
		return self.custom(id = ProviderBase.CustomSeeds, settings = settings)

	def customSeedsSet(self, value, settings = True):
		self.customSet(id = ProviderBase.CustomSeeds, value = value, settings = settings)

	def customSeedsHas(self):
		return self.customHas(id = ProviderBase.CustomSeeds)

	def customSeedsInitialize(self, custom):
		return self.settingsCustomize(custom = custom, default = {
			ProviderBase.SettingsId				: ProviderBase.CustomSeeds,
			ProviderBase.SettingsLabel			: 'Minimum Seeds',
			ProviderBase.SettingsDefault		: None,
			ProviderBase.SettingsType			: ProviderBase.SettingsTypeNumber,
			ProviderBase.SettingsFormat			: {ProviderBase.SettingsValueGeneral : ProviderBase.SettingsFormatSeeds, ProviderBase.SettingsValueZero : ProviderBase.SettingsValueNone},
			ProviderBase.SettingsDescription	: 'Only retrieve {containers} that have a minimum number of seeds.',
		})

	##############################################################################
	# CUSTOM - LEECHES
	##############################################################################

	def customLeeches(self, settings = True):
		return self.custom(id = ProviderBase.CustomLeeches, settings = settings)

	def customLeechesSet(self, value, settings = True):
		self.customSet(id = ProviderBase.CustomLeeches, value = value, settings = settings)

	def customLeechesHas(self):
		return self.customHas(id = ProviderBase.CustomLeeches)

	def customLeechesInitialize(self, custom):
		return self.settingsCustomize(custom = custom, default = {
			ProviderBase.SettingsId				: ProviderBase.CustomLeeches,
			ProviderBase.SettingsLabel			: 'Minimum Leeches',
			ProviderBase.SettingsDefault		: None,
			ProviderBase.SettingsType			: ProviderBase.SettingsTypeNumber,
			ProviderBase.SettingsFormat			: {ProviderBase.SettingsValueGeneral : ProviderBase.SettingsFormatLeeches, ProviderBase.SettingsValueZero : ProviderBase.SettingsValueNone},
			ProviderBase.SettingsDescription	: 'Only retrieve {containers} that have a minimum number of leeches.',
		})

	##############################################################################
	# CUSTOM - SEARCH
	##############################################################################

	def customSearch(self, settings = True):
		return self.custom(id = ProviderBase.CustomSearch, settings = settings)

	def customSearchSet(self, value, settings = True):
		self.customSet(id = ProviderBase.CustomSearch, value = value, settings = settings)

	def customSearchHas(self):
		return self.customHas(id = ProviderBase.CustomSearch)

	def customSearchInitialize(self, custom):
		return self.settingsCustomize(custom = custom, default = {
			ProviderBase.SettingsId				: ProviderBase.CustomSearch,
			ProviderBase.SettingsLabel			: 'Search Mode',
			ProviderBase.SettingsDefault		: ProviderBase.CustomSearchId,
			ProviderBase.SettingsType			: [{ProviderBase.CustomSearchId : 'Search By ID'}, {ProviderBase.CustomSearchTitle : 'Search By Title'}],
			ProviderBase.SettingsDescription	: 'Search {name} using either title or the IMDb, TMDb, TVDB or Trakt ID. Not all files have an associated ID and searching by title might therefore return more results. Searching by title is slower and can return incorrect results. The title will be used if no ID is available.',
		})

	def customSearchId(self, settings = True):
		return self.customSearch(settings = settings) == ProviderBase.CustomSearchId

	def customSearchTitle(self, settings = True):
		return self.customSearch(settings = settings) == ProviderBase.CustomSearchTitle

	##############################################################################
	# CUSTOM - CATEGORY
	##############################################################################

	def customCategory(self, settings = True):
		return self.custom(id = ProviderBase.CustomCategory, settings = settings)

	def customCategorySet(self, value, settings = True):
		self.customSet(id = ProviderBase.CustomCategory, value = value, settings = settings)

	def customCategoryHas(self):
		return self.customHas(id = ProviderBase.CustomCategory)

	def customCategoryInitialize(self, custom):
		return self.settingsCustomize(custom = custom, default = {
			ProviderBase.SettingsId				: ProviderBase.CustomCategory,
			ProviderBase.SettingsLabel			: 'Separate Categories',
			ProviderBase.SettingsDefault		: False,
			ProviderBase.SettingsType			: ProviderBase.SettingsTypeBoolean,
			ProviderBase.SettingsDescription	: '{name} has subcategories that can be searched together with a single request or can be searched separately with multiple requests. Searching categories separately might return more results, but can also increase the scraping time.',
		})

	##############################################################################
	# CUSTOM - VERIFIED
	##############################################################################

	def customVerified(self, settings = True):
		return self.custom(id = ProviderBase.CustomVerified, settings = settings)

	def customVerifiedSet(self, value, settings = True):
		self.customSet(id = ProviderBase.CustomVerified, value = value, settings = settings)

	def customVerifiedHas(self):
		return self.customHas(id = ProviderBase.CustomVerified)

	def customVerifiedInitialize(self, custom):
		return self.settingsCustomize(custom = custom, default = {
			ProviderBase.SettingsId				: ProviderBase.CustomVerified,
			ProviderBase.SettingsLabel			: 'Verified Only',
			ProviderBase.SettingsDefault		: False,
			ProviderBase.SettingsType			: ProviderBase.SettingsTypeBoolean,
			ProviderBase.SettingsDescription	: 'Only include {containers} that are internally ranked or were uploaded by verified users. Less results might be returned, but they are more likely to be better quality releases.',
		})

	##############################################################################
	# CUSTOM - SPAM
	##############################################################################

	def customSpam(self, settings = True):
		return self.custom(id = ProviderBase.CustomSpam, settings = settings)

	def customSpamSet(self, value, settings = True):
		self.customSet(id = ProviderBase.CustomSpam, value = value, settings = settings)

	def customSpamHas(self):
		return self.customHas(id = ProviderBase.CustomSpam)

	def customSpamInitialize(self, custom):
		return self.settingsCustomize(custom = custom, default = {
			ProviderBase.SettingsId				: ProviderBase.CustomSpam,
			ProviderBase.SettingsLabel			: 'Spam Filter',
			ProviderBase.SettingsDefault		: False,
			ProviderBase.SettingsType			: ProviderBase.SettingsTypeBoolean,
			ProviderBase.SettingsDescription	: 'Filter out results that are considered spam.',
		})

	##############################################################################
	# CUSTOM - ADULT
	##############################################################################

	def customAdult(self, settings = True):
		return self.custom(id = ProviderBase.CustomAdult, settings = settings)

	def customAdultSet(self, value, settings = True):
		self.customSet(id = ProviderBase.CustomAdult, value = value, settings = settings)

	def customAdultHas(self):
		return self.customHas(id = ProviderBase.CustomAdult)

	def customAdultInitialize(self, custom):
		return self.settingsCustomize(custom = custom, default = {
			ProviderBase.SettingsId				: ProviderBase.CustomAdult,
			ProviderBase.SettingsLabel			: 'Adult Filter',
			ProviderBase.SettingsDefault		: True,
			ProviderBase.SettingsType			: ProviderBase.SettingsTypeBoolean,
			ProviderBase.SettingsDescription	: 'Filter out results that are considered adult content.',
		})

	##############################################################################
	# CUSTOM - PASSWORD
	##############################################################################

	def customPassword(self, settings = True):
		return self.custom(id = ProviderBase.CustomPassword, settings = settings)

	def customPasswordSet(self, value, settings = True):
		self.customSet(id = ProviderBase.CustomPassword, value = value, settings = settings)

	def customPasswordHas(self):
		return self.customHas(id = ProviderBase.CustomPassword)

	def customPasswordInitialize(self, custom):
		return self.settingsCustomize(custom = custom, default = {
			ProviderBase.SettingsId				: ProviderBase.CustomPassword,
			ProviderBase.SettingsLabel			: 'Password Filter',
			ProviderBase.SettingsDefault		: True,
			ProviderBase.SettingsType			: ProviderBase.SettingsTypeBoolean,
			ProviderBase.SettingsDescription	: 'Filter out results that are password protected.',
		})

	##############################################################################
	# CUSTOM - INCOMPLETE
	##############################################################################

	def customIncomplete(self, settings = True):
		return self.custom(id = ProviderBase.CustomIncomplete, settings = settings)

	def customIncompleteSet(self, value, settings = True):
		self.customSet(id = ProviderBase.CustomIncomplete, value = value, settings = settings)

	def customIncompleteHas(self):
		return self.customHas(id = ProviderBase.CustomIncomplete)

	def customIncompleteInitialize(self, custom):
		return self.settingsCustomize(custom = custom, default = {
			ProviderBase.SettingsId				: ProviderBase.CustomIncomplete,
			ProviderBase.SettingsLabel			: 'Incomplete Filter',
			ProviderBase.SettingsDefault		: True,
			ProviderBase.SettingsType			: ProviderBase.SettingsTypeBoolean,
			ProviderBase.SettingsDescription	: 'Filter out files that are incomplete or have missing parts.',
		})

	##############################################################################
	# CACHE
	##############################################################################

	def cacheTime(self):
		return self.mData['cache'][ProviderBase.ScrapeTime]

	##############################################################################
	# MATCH
	##############################################################################

	'''
		FUNCTION:
			Check if the provider matches a description.
		PARAMETERS:
			description (string): The provider ID, name, or file name.
			exact (boolean): If True, match the description exactly. If False, match the description leniently, eg szukajka vs szukajkatvself.
	'''
	def match(self, description, exact = True):
		lookups = [self.id(), self.name(), self.fileName()]
		lookups = [i.lower() for i in lookups]
		if exact: return description in lookups
		else: return any(i in description or description in i for i in lookups)

	##############################################################################
	# VERIFY
	##############################################################################

	def verify(self, domain = True, account = True, scrape = True):
		self.stopClear()

		domainType = None
		domainReason = None
		accountType = None
		accountReason = None
		scrapeType = None
		scrapeReason = None

		if not self.stopped() and domain:
			domainType, domainReason = self.verifyDomain(internal = True)
		if domainType is None or domainType == ProviderBase.VerifySuccess:
			if not self.stopped() and account:
				accountType, accountReason = self.verifyAccount(internal = True)
			if not self.stopped() and scrape:
				if accountType is None or accountType == ProviderBase.VerifySuccess or accountType == ProviderBase.VerifyOptional:
					scrapeType, scrapeReason = self.verifyScrape(internal = True)
				elif scrape:
					if self.accountHas() and not self.accountOptional():
						scrapeType = accountType
						scrapeReason = accountReason
					else:
						scrapeType = domainType
						scrapeReason = domainReason
		else:
			# Ignore accounts for open providers (eg: TorrentApi/Torrentz2k that uses accountless tokens).
			if account and self.accountHas() and not self.accountOptional() and not self.accessOpen():
				accountType = domainType
				accountReason = domainReason
			if scrape:
				scrapeType = domainType
				scrapeReason = domainReason

		return {
			ProviderBase.VerifyDomain : {
				ProviderBase.VerifyType : domainType,
				ProviderBase.VerifyReason : domainReason,
			},
			ProviderBase.VerifyAccount : {
				ProviderBase.VerifyType : accountType,
				ProviderBase.VerifyReason : accountReason,
			},
			ProviderBase.VerifyScrape : {
				ProviderBase.VerifyType : scrapeType,
				ProviderBase.VerifyReason : scrapeReason,
			},
		}

	def verifyBusy(self):
		return self.mVerify

	def verifyDomain(self, internal = False):
		if not internal: self.stopClear()
		self.timerStart()
		self.mVerify = True
		result, reason = self.linkVerify()
		if result is True: result = ProviderBase.VerifySuccess
		elif result is False: result = ProviderBase.VerifyFailure
		self.mVerify = False
		return result, reason

	def verifyAccount(self, internal = False):
		if not internal: self.stopClear()
		self.timerStart()
		self.mVerify = True
		result = self.accountVerify()
		if result is True: result = ProviderBase.VerifySuccess
		elif result is False: result = ProviderBase.VerifyFailure
		self.mVerify = False
		return result, None

	def verifyScrape(self, internal = False):
		def _verifyScrape(media, items, hostersAll, hostersPremium):
			for item in items:
				if self.stopped(): break # Otherwise the GUI becomes unresponsive on cancel, waiting for the threads.
				item['media'] = media
				item['niche'] = None
				item['silent'] = True
				item['cacheLoad'] = False
				item['cacheSave'] = False
				item['hostersAll'] = hostersAll
				item['hostersPremium'] = hostersPremium
				self.execute(**item)
				result, reason = self.verifyScrapeResult()
				if not result is None: return result, reason
			return ProviderBase.VerifyFailure, None

		if not internal: self.stopClear()
		self.concurrencyInitialize()
		self.settingsGlobalLimitPageSet(value = 1, temporary = True) # Only scrape the first page.
		self.mVerify = True
		result = ProviderBase.VerifyFailure
		reason = None

		movie = [
			{
				'titles'	: {'search':{'main':['Avatar'],'episode':[],'collection':[],'native':[]},'collection':None,'abbreviation':'Avatar','processed':{'all':['Avatar','Avatar - Aufbruch nach Pandora','Аватар','Afanda','Afaandaat','آواتار','阿凡达','阿凡達','アバタ','아바타'],'main':['Avatar','Avatar - Aufbruch nach Pandora','Аватар','Afanda','Afaandaat','آواتار','阿凡达','阿凡達','アバタ','아바타'],'episode':[],'collection':['Avatar']},'main':'Avatar','local':'Avatar','original':'Avatar'},
				'years'		: {'common' : 2009, 'original' : 2009, 'median' : 2009, 'all' : [2009]},
				'idImdb'	: 'tt0499549',
				'idTmdb'	: '19995',
				'idTvdb'	: '165',
			},
			{
				'titles'	: {'search':{'main':['Titanic'],'episode':[],'collection':[],'native':[]},'collection':None,'abbreviation':'Titanic','processed':{'all':['Titanic','Титаник','泰坦尼克号','Τιτανικός','鐵達尼號','타이타닉','Titanikas','טיטניק'],'main':['Titanic','Титаник','泰坦尼克号','Τιτανικός','鐵達尼號','타이타닉','Titanikas','טיטניק'],'episode':[],'collection':[]},'main':'Titanic','local':'Titanic','original':'Titanic'},
				'years'		: {'common' : 1997, 'original' : 1997, 'median' : 1997, 'all' : [1997]},
				'idImdb'	: 'tt0120338',
				'idTmdb'	: '597',
				'idTvdb'	: '231',
			},
			{
				'titles'	: {'search':{'main':['Harry Potter and the Chamber of Secrets'],'episode':[],'collection':['Harry Potter'],'native':[]},'collection':'Harry Potter','abbreviation':'Harry Potter and the Chamber of Secrets','processed':{'all':['Harry Potter and the Chamber of Secrets','哈利波特—消失的密室','哈利波特与密室','Harry Potter ja saladuste kamber','Harry Potter 2 - Chamber of Secrets','Harry Potter 2 Chambre des secrets - Harry Potter and the Chamber of Secrets - 2002 FR','Harry Potter 2','Harry Potter 2 - La Camera Dei Segreti','Harry Potter a tajemná komnata','2 Harry Potter a Tajemná komnata','Harry Potter y la cámara secreta','2. Harry Potter and the Chamber of Secrets - Ultimate Extended Edition','Harry Potter and the Chamber of Secrets - Ultimate Extended Edition','2. Harry Potter and the chamber of secrets','Harry Potter dan Kamar Rahasia','Harry Potter I La Cambra Secreta','Гарри Поттер и тайная комната','Гарри Поттер 2. Гарри Поттер и тайная комната','Garri Potter i Tainaya komnata','Harry Potter En De Geheime Kamer','2 - Harry Potter en de geheime kamer','Harry Potter E a Câmara dos Segredos','Harry Potter og mysteriekammeret','哈利波特：消失的密室','Harry Potter ve Sirlar Odasi','Haris Poteris ir paslapciu kambarys','Harry Potter si camera secretelor','Harry Potter og leyniklefinn','Harry Potter i Komnata Tajemnic','Harry Potter et la chambre des secrets','Harry Potter 2 - et la Chambre des Secrets','Harry Potter - 2 - La Chambre des Secrets','Harry Potter 2 et la Chambre des Secrets','Harry Potter 2 - Harry Potter et la Chambre des secrets','Хари Потър и стаята на тайните','Khari Potŭr i stayata na taĭnite','Harry Potter og hemmelighedernes kammer','Harry Potter 2 Hemmelighedernes Kammer','Harry Potter i Odaja tajni','Harry Potter und die Kammer des Schreckens','Harry Potter 2 - Die Kammer des Schreckens','Harry Potter II und die Kammer des Schreckens','Harry Potter 2 - und die Kammer des Schreckens','Harry Potter 2 - Harry Potter und die Kammer des Schreckens','ハリー・ポッターと秘密の部屋','Harii Pottâ to himitsu no heya','Harry Potter és a titkok kamrája','Harry Potter e a Câmara Secreta','Harry Potter 2 e a Câmara Secreta','Harry Potter ja salaisuuksien kammio','Ο Χάρι Πότερ και η κάμαρα με τα μυστικά','Ο Χάρι Πότερ Και Η Κάμαρα Με Τα Μυστικά','O Chári Póter kai i Kámara me ta Mystiká','Hari Poter i Dvorana tajni','Harry Potter II and the Chamber of Secrets','Harry Potter 2 - The Chamber of Secrets','Harry Potter II - The Chamber of Secrets','Harry Potter - 2 - The Chamber of Secrets','HP and the Chamber of Secrets','Harry Potter a tajomná komnata','해리 포터와 비밀의 방','해리포터와 비밀의 방','Harry Potter in dvorana skrivnosti','Harri Potter i tayemna kimnata','Harry Potter och hemligheternas kammare','הארי פוטר וחדר הסודות','Harry Potter a tajemna komnata','2 Harry Potter a Tajemna komnata','Harry Potter y la camara secreta','Harry Potter E a Camara dos Segredos','Khari Potur i stayata na tainite','Harii Potta to himitsu no heya','Harry Potter es a titkok kamraja','Harry Potter e a Camara Secreta','Harry Potter 2 e a Camara Secreta','O Chari Poter kai i Kamara me ta Mystika','Harry Potter a tajomna komnata','Harry Potter'],'main':['Harry Potter and the Chamber of Secrets','哈利波特—消失的密室','哈利波特与密室','Harry Potter ja saladuste kamber','Harry Potter 2 - Chamber of Secrets','Harry Potter 2 Chambre des secrets - Harry Potter and the Chamber of Secrets - 2002 FR','Harry Potter 2','Harry Potter 2 - La Camera Dei Segreti','Harry Potter a tajemná komnata','2 Harry Potter a Tajemná komnata','Harry Potter y la cámara secreta','2. Harry Potter and the Chamber of Secrets - Ultimate Extended Edition','Harry Potter and the Chamber of Secrets - Ultimate Extended Edition','2. Harry Potter and the chamber of secrets','Harry Potter dan Kamar Rahasia','Harry Potter I La Cambra Secreta','Гарри Поттер и тайная комната','Гарри Поттер 2. Гарри Поттер и тайная комната','Garri Potter i Tainaya komnata','Harry Potter En De Geheime Kamer','2 - Harry Potter en de geheime kamer','Harry Potter E a Câmara dos Segredos','Harry Potter og mysteriekammeret','哈利波特：消失的密室','Harry Potter ve Sirlar Odasi','Haris Poteris ir paslapciu kambarys','Harry Potter si camera secretelor','Harry Potter og leyniklefinn','Harry Potter i Komnata Tajemnic','Harry Potter et la chambre des secrets','Harry Potter 2 - et la Chambre des Secrets','Harry Potter - 2 - La Chambre des Secrets','Harry Potter 2 et la Chambre des Secrets','Harry Potter 2 - Harry Potter et la Chambre des secrets','Хари Потър и стаята на тайните','Khari Potŭr i stayata na taĭnite','Harry Potter og hemmelighedernes kammer','Harry Potter 2 Hemmelighedernes Kammer','Harry Potter i Odaja tajni','Harry Potter und die Kammer des Schreckens','Harry Potter 2 - Die Kammer des Schreckens','Harry Potter II und die Kammer des Schreckens','Harry Potter 2 - und die Kammer des Schreckens','Harry Potter 2 - Harry Potter und die Kammer des Schreckens','ハリー・ポッターと秘密の部屋','Harii Pottâ to himitsu no heya','Harry Potter és a titkok kamrája','Harry Potter e a Câmara Secreta','Harry Potter 2 e a Câmara Secreta','Harry Potter ja salaisuuksien kammio','Ο Χάρι Πότερ και η κάμαρα με τα μυστικά','Ο Χάρι Πότερ Και Η Κάμαρα Με Τα Μυστικά','O Chári Póter kai i Kámara me ta Mystiká','Hari Poter i Dvorana tajni','Harry Potter II and the Chamber of Secrets','Harry Potter 2 - The Chamber of Secrets','Harry Potter II - The Chamber of Secrets','Harry Potter - 2 - The Chamber of Secrets','HP and the Chamber of Secrets','Harry Potter a tajomná komnata','해리 포터와 비밀의 방','해리포터와 비밀의 방','Harry Potter in dvorana skrivnosti','Harri Potter i tayemna kimnata','Harry Potter och hemligheternas kammare','הארי פוטר וחדר הסודות','Harry Potter a tajemna komnata','2 Harry Potter a Tajemna komnata','Harry Potter y la camara secreta','Harry Potter E a Camara dos Segredos','Khari Potur i stayata na tainite','Harii Potta to himitsu no heya','Harry Potter es a titkok kamraja','Harry Potter e a Camara Secreta','Harry Potter 2 e a Camara Secreta','O Chari Poter kai i Kamara me ta Mystika','Harry Potter a tajomna komnata'],'episode':[],'collection':['Harry Potter']},'main':'Harry Potter and the Chamber of Secrets','local':'Harry Potter and the Chamber of Secrets','original':'Harry Potter and the Chamber of Secrets'},
				'years'		: {'common' : 2002, 'original' : 2002, 'median' : 2002, 'all' : [2002]},
				'idImdb'	: 'tt0295297',
				'idTmdb'	: '672',
				'idTvdb'	: '63',
			},
			{
				'titles'	: {'search':{'main':['Avengers Endgame'],'episode':[],'collection':['The Avengers'],'native':[]},'collection':'The Avengers','abbreviation':'Avengers: Endgame','processed':{'all':['Avengers: Endgame','Avengers : Endgame','复仇者联盟3：无尽之战(下)','复联4','Avengers.Endgame','复仇者联盟4：终局之战','Tasujad: Lõppmäng','المنتقمون: نهاية اللعبة','انتقام جوان: پایان بازی','Avengers: Hoi Ket','შურისმაძიებლები: თამაშის დასასრული','एवेंजर्स: एंडगेम','एवेंजर्स: खेल ख़त्म','Vengadores: La guerra del infinito - 2ª parte','VENGADORES: ENDGAME VERSION EXTENDIDA','Los Vengadores: Endgame','Εκδικητές: Η Τελευταία Πράξη','Мстители: Война бесконечности. Часть 2','Мстители: Финал','Vingadores: Endgame','Osvetnici: Kraj igre','復仇者聯盟：終局之戰','İntikamcılar: Sonsuzluk Savaşı - Bölüm 2','Yenilmezler : Sonsuzluk Savaşı - Bölüm 2','Yenilmezler 4 Son Oyun','ආගන්තුකයන්: Endgame','Keršytojai: Pabaiga','เวนเจอร์ส: ฤทธิ์','Razbunatorii: Sfarsitul jocului','The Avengers 4 - Endgame','Avengers: Koniec gry','Avengers, Endgame','Отмъстителите: Краят','Osvetnici: Završnica','Avengers: Endspiel','Avengers 4 - Endgame','Avengers - Endgame','Marvel\'s The Avengers 4 - Endgame','Marvel\'s The Avengers 4 Endgame','MCU-22 - Avengers 4 - Endgame','アベンジャーズ：エンドゲーム','Bosszúállók: Végjáték','Vingadores: Guerra Infinita - Parte 2','Vingadores 3','Vingadores 4','Vingadores: Ultimato','Os Vingadores 4 - Ultimato','Os Vingadores 4: Ultimato','Qasoskorlar: Final','Qasoskorlar 4','Qasoskorlar 4: Soʻngi Raund','MCU 22: Avengers: Endgame','Avengers 4','Avengers: Infinity War - Part II','The Avengers 3: Part 2','Avengers: Infinity Gauntlet','Avengers: End Game','Avengers - The End Game','Avengers: Untitled','Avengers: Annihilation','AVENGERS ENDGAME 3D','Avengers: Infinity War Part 2','Avengers 4: Endgame','Marvel Studios\' Avengers: Endgame','Avengers-Endgame','Avengers: Infinity War, Part 2','Avengers: Endgame 3D','The Avengers 4: Endgame','어벤져스 엔드게임','어벤져스 4','어벤져스-엔드게임','어벤져스: 엔드게임','마블 어벤져스, 엔드게임','Месники 3','Месники: Завершення','Tasujad: Loppmang','Vengadores: La guerra del infinito - 2a parte','Intikamclar: Sonsuzluk Savas - Bolum 2','Yenilmezler : Sonsuzluk Savas - Bolum 2','Kersytojai: Pabaiga','Osvetnici: Zavrsnica','Bosszuallok: Vegjatek','Qasoskorlar 4: Songi Raund','The Avengers'],'main':['Avengers: Endgame','Avengers : Endgame','复仇者联盟3：无尽之战(下)','复联4','Avengers.Endgame','复仇者联盟4：终局之战','Tasujad: Lõppmäng','المنتقمون: نهاية اللعبة','انتقام جوان: پایان بازی','Avengers: Hoi Ket','შურისმაძიებლები: თამაშის დასასრული','एवेंजर्स: एंडगेम','एवेंजर्स: खेल ख़त्म','Vengadores: La guerra del infinito - 2ª parte','VENGADORES: ENDGAME VERSION EXTENDIDA','Los Vengadores: Endgame','Εκδικητές: Η Τελευταία Πράξη','Мстители: Война бесконечности. Часть 2','Мстители: Финал','Vingadores: Endgame','Osvetnici: Kraj igre','復仇者聯盟：終局之戰','İntikamcılar: Sonsuzluk Savaşı - Bölüm 2','Yenilmezler : Sonsuzluk Savaşı - Bölüm 2','Yenilmezler 4 Son Oyun','ආගන්තුකයන්: Endgame','Keršytojai: Pabaiga','เวนเจอร์ส: ฤทธิ์','Razbunatorii: Sfarsitul jocului','The Avengers 4 - Endgame','Avengers: Koniec gry','Avengers, Endgame','Отмъстителите: Краят','Osvetnici: Završnica','Avengers: Endspiel','Avengers 4 - Endgame','Avengers - Endgame','Marvel\'s The Avengers 4 - Endgame','Marvel\'s The Avengers 4 Endgame','MCU-22 - Avengers 4 - Endgame','アベンジャーズ：エンドゲーム','Bosszúállók: Végjáték','Vingadores: Guerra Infinita - Parte 2','Vingadores 3','Vingadores 4','Vingadores: Ultimato','Os Vingadores 4 - Ultimato','Os Vingadores 4: Ultimato','Qasoskorlar: Final','Qasoskorlar 4','Qasoskorlar 4: Soʻngi Raund','MCU 22: Avengers: Endgame','Avengers 4','Avengers: Infinity War - Part II','The Avengers 3: Part 2','Avengers: Infinity Gauntlet','Avengers: End Game','Avengers - The End Game','Avengers: Untitled','Avengers: Annihilation','AVENGERS ENDGAME 3D','Avengers: Infinity War Part 2','Avengers 4: Endgame','Marvel Studios\' Avengers: Endgame','Avengers-Endgame','Avengers: Infinity War, Part 2','Avengers: Endgame 3D','The Avengers 4: Endgame','어벤져스 엔드게임','어벤져스 4','어벤져스-엔드게임','어벤져스: 엔드게임','마블 어벤져스, 엔드게임','Месники 3','Месники: Завершення','Tasujad: Loppmang','Vengadores: La guerra del infinito - 2a parte','Intikamclar: Sonsuzluk Savas - Bolum 2','Yenilmezler : Sonsuzluk Savas - Bolum 2','Kersytojai: Pabaiga','Osvetnici: Zavrsnica','Bosszuallok: Vegjatek','Qasoskorlar 4: Songi Raund'],'episode':[],'collection':['The Avengers']},'main':'Avengers: Endgame','local':'Avengers : Endgame','original':'Avengers: Endgame'},
				'years'		: {'common' : 2019, 'original' : 2019, 'median' : 2019, 'all' : [2019]},
				'idImdb'	: 'tt4154796',
				'idTmdb'	: '299534',
				'idTvdb'	: '148',
			},
		]

		show = [
			{
				'titles'		: {'search':{'main':['The Office'],'episode':['Pilot'],'collection':[],'native':[]},'episode':'Pilot','collection':None,'abbreviation':'The Office','processed':{'all':['The Office','The Office (US)','美版办公室','O Escritório','The Office (US) – Das Büro','The Office (U.S.)','Vida de Escritório','O Escritorio','The Office (US)  Das Buro','Vida de Escritorio','Pilot'],'main':['The Office','The Office (US)','美版办公室','O Escritório','The Office (US) – Das Büro','The Office (U.S.)','Vida de Escritório','O Escritorio','The Office (US)  Das Buro','Vida de Escritorio'],'episode':['Pilot'],'collection':[]},'main':'The Office','local':'The Office (US)','original':'The Office'},
				'years'			: {'common' : 2005, 'original' : 2005, 'median' : 2005, 'all' : [2005]},
				'time'			: 1111622400,
				'idImdb'		: 'tt0386676',
				'idTmdb'		: '2316',
				'idTvdb'		: '73244',
				'numberSeason'	: 1,
				'numberEpisode'	: 1,
			},
			{
				'titles'		: {'search':{'main':['The Big Bang Theory'],'episode':['The Conjugal Conjecture'],'collection':[],'native':[]},'episode':'The Conjugal Conjecture','collection':None,'abbreviation':'The Big Bang Theory','processed':{'all':['The Big Bang Theory','天才理论传','Suure Paugu teooria','Enfejare Bozorg','Big Bang Theory','Vu No Lon','Teorie velkého třesku','Teorie velkého tresku','Teorie velkeho tresku','La teoría del Big Bang','תאוריית המפץ הגדול','Hamapats hagadol','SONY','Big Bang','Cómo se lo comí a tu madre','La Teoria del Big Bang','TBBT','A Teoria do Big Bang','Štreberi','宅男行不行','Didžiojo sprogimo teorija','Didziojo sprogimo teorija','ビッグバン★セオリー/ギークなボクらの恋愛法則','Agymenők','Agymenok','Teoria vel\'keho tresku','빅뱅이론','빅뱅 이론','Теорія великого вибуху','Como se lo comi a tu madre','Streberi','The Conjugal Conjecture'],'main':['The Big Bang Theory','天才理论传','Suure Paugu teooria','Enfejare Bozorg','Big Bang Theory','Vu No Lon','Teorie velkého třesku','Teorie velkého tresku','Teorie velkeho tresku','La teoría del Big Bang','תאוריית המפץ הגדול','Hamapats hagadol','SONY','Big Bang','Cómo se lo comí a tu madre','La Teoria del Big Bang','TBBT','A Teoria do Big Bang','Štreberi','宅男行不行','Didžiojo sprogimo teorija','Didziojo sprogimo teorija','ビッグバン★セオリー/ギークなボクらの恋愛法則','Agymenők','Agymenok','Teoria vel\'keho tresku','빅뱅이론','빅뱅 이론','Теорія великого вибуху','Como se lo comi a tu madre','Streberi'],'episode':['The Conjugal Conjecture'],'collection':[]},'main':'The Big Bang Theory','local':'The Big Bang Theory','original':'The Big Bang Theory'},
				'years'			: {'common' : 2007, 'original' : 2007, 'median' : 2007, 'all' : [2007]},
				'time'			: 1474243200,
				'idImdb'		: 'tt0898266',
				'idTmdb'		: '1418',
				'idTvdb'		: '80379',
				'numberSeason'	: 10,
				'numberEpisode'	: 1,
			},
			{
				'titles'		: {'search':{'main':['Game of Thrones'],'episode':['Winterfell'],'collection':[],'native':[]},'episode':'Winterfell','collection':None,'abbreviation':'Game of Thrones','processed':{'all':['Game of Thrones','Το Παιχνίδι του θρόνου','Παιχνίδι Του Στέμματος','Il Trono di Spade','بازی تاج و تخت','სამეფო კარის თამაშები','அரியணை விளையாட்டு','Juego de Tronos','冰与火之歌','权利的游戏','Game of Thrones (2011)','A Guerra dos Tronos','冰與火之歌：權力遊戲','Taht Oyunları','Sostų žaidimas','มหาศึกชิงบัลลังก์','Urzeala Tronurilor','Le Trône de fer','Le Throne de fer','Igra prijestolja','Game of Thrones- Das Lied von Eis und Feuer','Game of Thrones - Das Lied von Eis und Feuer','Trónok harca','صراع العروش','Jogo dos Tronos','A Song of Ice and Fire','GoT','Taht Oyunlar','Sostu zaidimas','Le Trone de fer','Tronok harca','Winterfell'],'main':['Game of Thrones','Το Παιχνίδι του θρόνου','Παιχνίδι Του Στέμματος','Il Trono di Spade','بازی تاج و تخت','სამეფო კარის თამაშები','அரியணை விளையாட்டு','Juego de Tronos','冰与火之歌','权利的游戏','Game of Thrones (2011)','A Guerra dos Tronos','冰與火之歌：權力遊戲','Taht Oyunları','Sostų žaidimas','มหาศึกชิงบัลลังก์','Urzeala Tronurilor','Le Trône de fer','Le Throne de fer','Igra prijestolja','Game of Thrones- Das Lied von Eis und Feuer','Game of Thrones - Das Lied von Eis und Feuer','Trónok harca','صراع العروش','Jogo dos Tronos','A Song of Ice and Fire','GoT','Taht Oyunlar','Sostu zaidimas','Le Trone de fer','Tronok harca'],'episode':['Winterfell'],'collection':[]},'main':'Game of Thrones','local':'Game of Thrones','original':'Game of Thrones'},
				'years'			: {'common' : 2011, 'original' : 2011, 'median' : 2011, 'all' : [2011]},
				'time'			: 1555200000,
				'idImdb'		: 'tt0944947',
				'idTmdb'		: '1399',
				'idTvdb'		: '121361',
				'numberSeason'	: 8,
				'numberEpisode'	: 1,
			},
			{
				'titles'		: {'search':{'main':['Rick and Morty'],'episode':['Total Rickall'],'collection':[],'native':[]},'episode':'Total Rickall','collection':None,'abbreviation':'Rick and Morty','processed':{'all':['Rick and Morty','Rick et Morty','Rick a Morty','瑞克与莫蒂','Total Rickall'],'main':['Rick and Morty','Rick et Morty','Rick a Morty','瑞克与莫蒂'],'episode':['Total Rickall'],'collection':[]},'main':'Rick and Morty','local':'Rick and Morty','original':'Rick and Morty'},
				'years'			: {'common' : 2013, 'original' : 2013, 'median' : 2013, 'all' : [2013]},
				'time'			: 1439683200,
				'idImdb'		: 'tt2861424',
				'idTmdb'		: '60625',
				'idTvdb'		: '275274',
				'numberSeason'	: 2,
				'numberEpisode'	: 4,
			},
			{ # For NYAA.
				'titles'		: {'search':{'main':['Dragon Ball Z'],'episode':['The Arrival of Raditz'],'collection':[],'native':[]},'episode':'The Arrival of Raditz','collection':None,'abbreviation':'Dragon Ball Z','processed':{'all':['Dragon Ball Z', 'Dragonball Z', 'DBZ', 'ドラゴンボールZ', 'The Arrival of Raditz'],'main':['Dragon Ball Z', 'Dragonball Z', 'DBZ', 'ドラゴンボールZ'],'episode':['The Arrival of Raditz'],'collection':[]},'main':'Dragon Ball Z','local':'Dragon Ball Z','original':'Dragon Ball Z'},
				'years'			: {'common' : 2000, 'original' : 2000, 'median' : 2000, 'all' : [2000]},
				'time'			: 952214400,
				'idImdb'		: 'tt0214341',
				'idTmdb'		: '12971',
				'idTvdb'		: '81472',
				'numberSeason'	: 1,
				'numberEpisode'	: 1,
			},
		]

		from lib.modules.core import Core
		core = Core()
		hostersAll = core.hosters()
		hostersPremium = core.hostersPremium()

		if self.supportMovie() and not result == ProviderBase.VerifySuccess:
			result, reason = _verifyScrape(Media.Movie, movie, hostersAll, hostersPremium)

		if self.supportShow() and not result == ProviderBase.VerifySuccess:
			result, reason = _verifyScrape(Media.Show, show, hostersAll, hostersPremium)

		self.mVerify = False
		return result, reason

	def verifyScrapeResult(self):
		if self.resultCount() > 0: return ProviderBase.VerifySuccess, None
		else: return self.verifyScrapeStatus()

	def verifyScrapeStatus(self):
		return None, None

	##############################################################################
	# THREAD
	##############################################################################

	def thread(self, function, *args):
		# Do not create a thread object here already.
		# Only create the thread in threadExecute().
		#return Pool.thread(target = function, args = tuple(args))
		return {'target' : function, 'args' : tuple(args)}

	def threadExecute(self, threads, factor = TimeFactorInternal, limit = None, wait = True, optimize = True):
		if not threads: return False

		# If there is only 1 thread or multiple threads, but only 1 thread should be executed at a time.
		# Execute the target function directly without launching a new thread.
		# Saves the overhead of creating a thread and reduces the overall threads created.
		if optimize and wait and (len(threads) == 1 or limit == 1):
			for thread in threads:
				if Tools.isDictionary(thread): thread['target'](*thread['args'])
				else: thread.run()
		else:
			synchronizer = None
			if limit:
				if Tools.isInteger(limit): synchronizer = Premaphore(limit) # Only create the thread object once it is ready to execute, but not before while it is waiting.
				else: synchronizer = limit

			# NB: Do not store the thread object permanently, like in the "threads" list passed into this function.
			# Otherwise a reference to the thread object is kept until the end of execution, preventing the thread from being deleted the moment it is done, and only getting deleted by the garbage collector at the end of the process.
			# When not storing the thread object, it gets deleted immediately after it finishes, freeing up threads.
			# This is especially important for low-end devices which have a maximum thread-creation limit imposed by the system (often linked to the RAM available, and other OS factors).
			instances = [] # Gets cleared when this function runs out-of-scope.

			for thread in threads:
				if Tools.isDictionary(thread): thread = Pool.thread(target = thread['target'], args = thread['args'], synchronizer = synchronizer)
				instances.append(thread)
				thread.start()

			if wait: self.threadWait(threads = instances, factor = factor)

		return True

	def threadWait(self, threads, factor = TimeFactorInternal):
		if Tools.isList(threads): [thread.join(self.timerRemaining(factor = factor)) for thread in threads]
		else: threads.join(self.timerRemaining(factor = factor))

	##############################################################################
	# TIMER
	##############################################################################

	def timerStart(self):
		ProviderBase.Timer[self.id()] = Time(start = True)

	def timerRemaining(self, factor = TimeFactorInternal):
		id = self.id()
		if id in ProviderBase.Timer: return self.scrapeTime(default = True, factor = factor) - ProviderBase.Timer[id].elapsed()
		else: return None

	def timerAllow(self, factor = TimeFactorInternal):
		remaining = self.timerRemaining(factor = factor)
		if remaining is None: return True
		else: return remaining > 0

	def timerCheck(self, factor = TimeFactorInternal, limit = None):
		time = self.timerRemaining(factor = factor)
		if time is None:
			# Important for web.py -> request() if the timer was not started.
			# Eg: When playing a .torrent file.
			time = ProviderBase.TimeDefault
		elif time <= 0:
			if not self.id() in ProviderBase.Times: # Only print once if there are mutliple requests per provider.
				ProviderBase.Times[self.id()] = True
				Logger.log('Provider not finished due to scraping time limit: ' + self.name())
			return None
		if limit: time = min(limit, time)
		return time

	def timerRequest(self, factor = TimeFactorInternal):
		return self.timerCheck(factor = factor, limit = ProviderBase.TimeRequest)

	##############################################################################
	# PARAMETERS
	##############################################################################

	def parameters(self):
		return self.mParameters

	def parametersSet(self, query = None, media = None, niche = None, titles = None, years = None, time = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, numberSeason = None, numberEpisode = None, numberPack = None, language = None, country = None, network = None, studio = None, pack = None, duration = None, exact = None, silent = None):
		# Copy the years, since the dictionary gets edited.
		if language: language = Tools.copy(language) if Tools.isArray(language) else [language]
		if country: country = Tools.copy(country) if Tools.isArray(country) else [country]
		if network: network = Tools.copy(network) if Tools.isArray(network) else [network]
		if studio: studio = Tools.copy(studio) if Tools.isArray(studio) else [studio]

		# Sometimes English is not listed as a the first language, although it is the main spoken language.
		# Eg: Body of Lies: Language ['ar', 'en'] - Country ['gb', 'us']
		# Move English to the front.
		if country and language and len(language) > 1:
			if not language[0] == Language.EnglishCode and language[1] == Language.EnglishCode:
				origin = country[0] if Tools.isArray(country) else country
				if origin in ['us', 'uk', 'gb', 'au', 'nz'] or (origin == 'ca' and not language[0] == Language.CodeFrench):
					language.remove(Language.EnglishCode)
					language.insert(0, Language.EnglishCode)

		self.mParameters = {'query' : query, 'media' : media, 'niche' : niche, 'titles' : Tools.copy(titles), 'years' : Tools.copy(years), 'time' : time, 'idImdb' : idImdb, 'idTmdb' : idTmdb, 'idTvdb' : idTvdb, 'idTrakt' : idTrakt, 'numberSeason' : numberSeason, 'numberEpisode' : numberEpisode, 'numberPack' : numberPack, 'language' : language, 'country' : country, 'network' : network, 'studio' : studio, 'pack' : pack, 'duration' : duration, 'exact' : exact, 'silent' : silent}

	def parametersImport(self, data):
		if Tools.isString(data): data = Converter.jsonFrom(data)
		elif Tools.isInstance(data, ProviderBase): data = Tools.copy(data.parameters())
		Tools.update(self.mParameters, data)

	def parametersExport(self, data):
		return Converter.jsonTo(self.mParameters)

	def parameterQuery(self):
		try: return self.mParameters['query']
		except: return None

	def parameterQuerySearch(self):
		try: return self.parameterQuery()['query']
		except: return None

	def parameterQueryRaw(self):
		try: return self.parameterQuery()['raw']
		except: return None

	def parameterQuerySpecial(self):
		try: return self.parameterQuery()['special']
		except: return None

	def parameterQueryPack(self):
		try: return self.parameterQuery()['pack']
		except: return None

	def parameterQueryYear(self):
		try: return self.parameterQuery()['year']
		except: return None

	def parameterQueryTitle(self):
		try: return self.parameterQuery()['title']
		except: return None

	def parameterQueryTime(self):
		try: return self.parameterQuery()['time']
		except: return None

	def parameterQueryId(self):
		try: return self.parameterQuery()['id']
		except: return None

	def parameterQueryIdImdb(self):
		try: return self.parameterQueryId()['imdb']
		except: return None

	def parameterQueryIdTmdb(self):
		try: return self.parameterQueryId()['tmdb']
		except: return None

	def parameterQueryIdTvdb(self):
		try: return self.parameterQueryId()['tvdb']
		except: return None

	def parameterQueryIdTrakt(self):
		try: return self.parameterQueryId()['trakt']
		except: return None

	def parameterQueryNumber(self):
		try: return self.parameterQuery()['number']
		except: return None

	def parameterQueryNumberSeason(self):
		try: return self.parameterQueryNumber()['season']
		except: return None

	def parameterQueryNumberEpisode(self):
		try: return self.parameterQueryNumber()['episode']
		except: return None

	def parameterQueryNumberPack(self):
		try: return self.parameterQueryNumber()['pack']
		except: return None

	def parameterMedia(self):
		return self.mParameters['media']

	def parameterMediaMovie(self):
		return Media.isFilm(self.mParameters['media'])

	def parameterMediaShow(self):
		return Media.isSerie(self.mParameters['media'])

	def parameterNiche(self):
		return self.mParameters['niche']

	def parameterNicheAnime(self):
		return Media.isAnime(self.mParameters['niche'])

	def parameterNicheDonghua(self):
		return Media.isDonghua(self.mParameters['niche'])

	def parameterTitles(self):
		return self.mParameters['titles']

	def parameterYears(self):
		return self.mParameters['years']

	def parameterTime(self):
		return self.mParameters['time']

	def parameterIdImdb(self):
		return self.mParameters['idImdb']

	def parameterIdTmdb(self):
		return self.mParameters['idTmdb']

	def parameterIdTvdb(self):
		return self.mParameters['idTvdb']

	def parameterIdTrakt(self):
		return self.mParameters['idTrakt']

	def parameterNumberSeason(self):
		return self.mParameters['numberSeason']

	def parameterNumberEpisode(self):
		return self.mParameters['numberEpisode']

	def parameterNumberPack(self):
		return self.mParameters['numberPack']

	def parameterLanguage(self):
		return self.mParameters['language']

	def parameterCountry(self):
		return self.mParameters['country']

	def parameterNetwork(self):
		return self.mParameters['network']

	def parameterStudio(self):
		return self.mParameters['studio']

	def parameterPack(self):
		return self.mParameters['pack']

	def parameterDuration(self):
		return self.mParameters['duration']

	def parameterExact(self):
		return self.mParameters['exact']

	def parameterSilent(self):
		return self.mParameters['silent']

	##############################################################################
	# RESULT
	##############################################################################

	def result(self):
		try: return ProviderBase.ResultStreams[self.id()]
		except: return None

	def resultJson(self):
		return Converter.jsonTo(self.result())

	@classmethod
	def resultId(self, type = None, link = None, hash = None):
		id = [type]
		if link: id.append(link)
		elif hash: id.append(hash)
		else: return None
		id = [i for i in id if i]
		if id: return '_'.join(id)
		return None

	def resultCount(self):
		result = self.result()
		return len(result) if result else 0

	def resultClear(self):
		id = self.id()
		ProviderBase.ResultLock[id] = Lock()
		ProviderBase.ResultFound[id] = {} # Use a dictionary, since lookups are faster than lists.
		ProviderBase.ResultStreams[id] = []

		from lib.modules.core import Core
		from lib.modules.stream import Filters
		ProviderBase.ResultCore = Core()
		ProviderBase.ResultFilters = Filters.instance()

	def resultSet(self, streams):
		id = self.id()
		for stream in streams:
			ProviderBase.ResultStreams[id].append({'stream' : stream})
		self.statisticsUpdateSearch(stream = len(streams))

	def resultAdd(self, stream):
		try:
			stream = self.resultProcess(stream = stream)
			if not stream.exclusionLink(): # Only check if the link was set here, since processStream() can still set it.
				id = self.id()
				link = stream.linkPrimary()
				hash = stream.hash()
				type = stream.sourceType()
				idLink = self.resultId(type = type, link = link)
				idHash = self.resultId(type = type, hash = hash)

				# The ID will not be in the lock list if the scraping was aborted, but some provider threads are still running.
				if id in ProviderBase.ResultLock:
					ProviderBase.ResultLock[id].acquire()
					if stream.accessTypeOrion() or ((not idLink or not idLink in ProviderBase.ResultFound[id]) and (not idHash or not idHash in ProviderBase.ResultFound[id])):
						self.statisticsUpdateSearch(stream = True)

						if idLink: ProviderBase.ResultFound[id][idLink] = True
						if idHash: ProviderBase.ResultFound[id][idHash] = True

						stream.idGaiaGenerate()
						idGaia = stream.idGaiaStream()
						if idGaia and not idGaia in ProviderBase.ResultFound[id]:
							ProviderBase.ResultFound[id][idGaia] = True
							ProviderBase.ResultStreams[id].append({'stream' : stream}) # If this key is ever changed, make sure to update the local library provider.

							ProviderBase.ResultLock[id].release()
							return True
		except: Logger.error()

		try: ProviderBase.ResultLock[id].release()
		except: pass
		return False

	def resultContains(self, type = None, link = None, hash = None):
		id = self.id()

		if id in ProviderBase.ResultFound:
			idLink = self.resultId(type = type, link = link)
			if idLink: return idLink in ProviderBase.ResultFound[id]

			idHash = self.resultId(type = type, hash = hash)
			if idHash: return idHash in ProviderBase.ResultFound[id]

		return False

	def resultStream(self, **data):
		try:
			if not 'sourceOrigin' in data:
				try: data['sourceOrigin'] = self.addonName()
				except: data['sourceOrigin'] = self.addonGaiaName()

			if not 'sourceProvider' in data:
				data['sourceProvider'] = self.name()

			if not 'sourcePublisher' in data:
				# If the link is from a proxy or unblocking site, innclude the subdomain as well.
				# Otherwise "https://zooqle.unblock.app" will show up as "unblock.app".
				sourcePublisher = self.linkDomain(subdomain = False, request = True)
				if sourcePublisher and Regex.match(data = sourcePublisher, expression = ProviderBase.ExpressionProxy):
					sourcePublisher = self.linkDomain(subdomain = True, request = True)
				data['sourcePublisher'] = sourcePublisher

			stream = Stream.load(
				idImdb = self.parameterIdImdb(),
				idTmdb = self.parameterIdTmdb(),
				idTvdb = self.parameterIdTvdb(),
				idTrakt = self.parameterIdTrakt(),

				metaMedia = self.parameterMedia(),
				metaNiche = self.parameterNiche(),
				metaTitle = self.parameterTitles(),
				metaYear = self.parameterYears()['median'] if self.parameterYears() else None,
				metaTime = self.parameterTime(),
				metaSeason = self.parameterNumberSeason(),
				metaEpisode = self.parameterNumberEpisode(),
				metaNumber = self.parameterNumberPack(),
				metaLanguage = self.parameterLanguage(),
				metaCountry = self.parameterCountry(),
				metaNetwork = self.parameterNetwork(),
				metaStudio = self.parameterStudio(),
				metaDuration = self.parameterDuration(),
				metaPack = self.parameterPack(),

				infoQuery = self.parameterQuery(),
				infoExact = self.parameterExact(),
				infoLanguage = self.languages(copy = True),

				**data
			)
			if stream: stream.providerSet(self)
			return stream
		except:
			self.logError()
			return None

	def resultProcess(self, stream):
		# Generate the magnet link once the file name was generated (eg: YTS) in the stream.
		if not stream.link() and stream.sourceTypeTorrent():
			hashContainer = stream.hashContainer()
			if hashContainer:
				fileName = stream.fileName()
				link = Container(hashContainer).torrentMagnet(title = fileName if fileName else None)
				stream.linkSet(link)
		return stream

	##############################################################################
	# LOG
	##############################################################################

	@classmethod
	def log(self, message, developer = False):
		if not developer or self.logDeveloper(): Logger.log(self.logMessage(message))

	def _log(self, message, developer = False):
		if not developer or self.logDeveloper(): Logger.log(self.logMessage(message))

	@classmethod
	def logError(self, message = None, developer = False):
		if not developer or self.logDeveloper(): Logger.error(message = self.logMessage(message))

	def _logError(self, message = None, developer = False):
		if not developer or self.logDeveloper(): Logger.error(message = self.logMessage(message))

	@classmethod
	def logMessage(self, message):
		return message

	def _logMessage(self, message):
		try: message = '[%s - %s] %s' % (self.addonName(), self.name(), message)
		except: pass
		return message

	@classmethod
	def logDeveloper(self):
		return System.developer()

	##############################################################################
	# CACHE
	##############################################################################

	def cacheInitialize(self, query = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, numberSeason = None, numberEpisode = None):
		from lib.providers.core.manager import Manager
		Manager.streamsInsert(data = [], provider = self, query = query, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, numberSeason = numberSeason, numberEpisode = numberEpisode)

	def cacheRetrieve(self, cache = True, query = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, numberSeason = None, numberEpisode = None):
		if cache:
			from lib.providers.core.manager import Manager
			return Manager.streamsRetrieve(provider = self, query = query, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, numberSeason = numberSeason, numberEpisode = numberEpisode, time = self.cacheTime())
		else:
			return None

	##############################################################################
	# QUERY
	##############################################################################

	def queryId(self):
		id = self.id()
		if not id in ProviderBase.QueryId:
			value = ''
			try: value += sys.modules[self.__module__].__file__
			except: value += id
			try: value += self.instanceId()
			except: pass
			ProviderBase.QueryId[id] = value
		return ProviderBase.QueryId[id]

	def queryAllow(self, *args):
		# Check if query was already executed, in order to avoid duplicate queries for alternative titles.
		query = self.queryId()
		for arg in args:
			if not arg is None:
				try: arg = Converter.unicode(arg)
				except: pass
				query += '_' + arg
		if query in ProviderBase.QueryDone: return False
		ProviderBase.QueryDone[query] = True
		return True

	##############################################################################
	# EXECUTE
	##############################################################################

	@classmethod
	def concurrencyMode(self):
		return Pool.settingMode()

	@classmethod
	def concurrencyThread(self):
		return self.concurrencyMode() == Pool.ModeThread

	@classmethod
	def concurrencyProcess(self):
		return self.concurrencyMode() == Pool.ModeProcess

	# minimum/maximum should not be changed, except in rare cases, like with debrid providers.
	@classmethod
	def concurrencyTasks(self, level = None, minimum = 1, maximum = 10):
		if level is None or not ProviderBase.ConcurrencyTasks: return ProviderBase.ConcurrencyTasks

		id = str(level) + '_' + str(minimum) + '_' + str(maximum)
		if not id in ProviderBase.ConcurrencyData:
			tasks = 1

			concurrency = None
			if ProviderBase.ConcurrencyTasks <= 4: concurrency = Pool.LevelLow
			elif ProviderBase.ConcurrencyTasks <= 8: concurrency = Pool.LevelMedium
			elif ProviderBase.ConcurrencyTasks <= 12: concurrency = Pool.LevelHigh

			# If fewer providers are enabled, we can use higher tasks limits.
			# Otherwise scraping with very few providers is unnecessarily slow, because we restrict the concurrency too much, which is not needed by other providers.
			multipliers = [1.0, 1.0, 1.0]
			if ProviderBase.ConcurrencyTotal <= 5: multipliers = [2.0, 1.5, 1.2]
			elif ProviderBase.ConcurrencyTotal <= 10: multipliers = [1.7, 1.4, 1.1]
			elif ProviderBase.ConcurrencyTotal <= 15: multipliers = [1.5, 1.3, 1.0]

			# Number of queries running concurrently for the same provider.
			if level <= 1:
				if concurrency == Pool.LevelLow: tasks = 1
				elif concurrency == Pool.LevelMedium: tasks = 2
				elif concurrency == Pool.LevelHigh: tasks = 3
				else: tasks = 5
				tasks *= multipliers[0]

			# Number of streams to process concurrently from the results of a single query from a single provider.
			elif level == 2:
				if concurrency == Pool.LevelLow: tasks = 1
				elif concurrency == Pool.LevelMedium: tasks = 2
				elif concurrency == Pool.LevelHigh: tasks = 3
				else: tasks = 6
				tasks *= multipliers[1]

			# Number of sub-queries for each entry of a details page running concurrently.
			elif level == 3:
				if concurrency == Pool.LevelLow: tasks = 2
				elif concurrency == Pool.LevelMedium: tasks = 3
				elif concurrency == Pool.LevelHigh: tasks = 4
				else: tasks = 7
				tasks *= multipliers[2]

			ProviderBase.ConcurrencyData[id] = max(minimum, min(maximum, int(tasks)))

		return ProviderBase.ConcurrencyData[id]

	@classmethod
	def concurrencyTasksSet(self, total, tasks, binge = None):
		ProviderBase.ConcurrencyTotal = total
		ProviderBase.ConcurrencyTasks = tasks
		ProviderBase.ConcurrencyBinge = binge

	def concurrencyLock(self):
		ProviderBase.ConcurrencyLock.acquire()

	def concurrencyUnlock(self):
		try: ProviderBase.ConcurrencyLock.release()
		except: pass

	@classmethod
	def concurrencyInitialize(self, tasks = None, binge = False):
		limit = Pool.settingScrape(binge = binge)

		total = tasks or 1 # 1: When an invidual provider is verified.
		if tasks: tasks = [tasks]
		else: tasks = []
		if limit: tasks.append(limit)
		if tasks: self.concurrencyTasksSet(total = total, tasks = min(tasks), binge = binge)

		level1 = self.concurrencyTasks(level = 1) or 'Unlimited'
		level2 = self.concurrencyTasks(level = 2) or 'Unlimited'
		level3 = self.concurrencyTasks(level = 3) or 'Unlimited'
		Logger.log('Scraping Concurrency Limits: %s Scrape' % ('Binge' if binge else 'Normal'))
		Logger.log('   Maximum Concurrent Providers: %s' % (str(limit) if limit else 'Unlimited'))
		Logger.log('   Maximum Concurrent Tasks: %s (Level 1) | %s (Level 2) | %s (Level 3)' % (str(level1), str(level2), str(level3)))

		if ProviderBase.ConcurrencyLock is None: ProviderBase.ConcurrencyLock = Semaphore(limit if limit else 9999999)

	@classmethod
	def concurrencyPrepare(self):
		# When using multi-processing, 1 or 2 providers always hang and never finish.
		# It seems that web.py -> request() -> Networker.linkDomain() causes the problem.
		# These are sporadic errors, that sometimes don't occur, but 90% of the time do occur. They are also not specific to certain providers.
		# It seems that "from externals import tldextract" is causing the process to hang.
		# Not entirely sure why, but it could have something to do with the TLD domains being read from file (.tld_set_snapshot) and maybe too many processes trying to access the file.
		# The .tld_set_snapshot file in the tldextract module, seems to be only read once and then cached it in memory.
		# Doing this does not solve the issue 100% (sometimes it still hangs), but at least close to 99.9% of the time.

		# Placing the statement below inside concurrencyInitialize(), which is only called once, does not fix the problem. It must be called by each provider in their own thread.
		# Placing the statement below inside the process execution itself also does not seem to work. It must be placed in the outside thread BEFORE the process is created.
		#from lib.modules.external import Importer
		#Importer.moduleTldExtract()
		Networker.modulePrepare()

	##############################################################################
	# CLEAR
	##############################################################################

	def clear(self):
		self.concurrencyPrepare()
		self.stopClear()
		self.resultClear()
		self.timerStart()

	##############################################################################
	# EXECUTE
	##############################################################################

	def execute(self, media, niche, titles, years = None, time = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, numberSeason = None, numberEpisode = None, numberPack = None, language = None, country = None, network = None, studio = None, pack = None, duration = None, exact = False, silent = False, cacheLoad = True, cacheSave = True, hostersAll = None, hostersPremium = None):
		result = []

		self.clear()
		self.concurrencyLock()
		timer = self.statisticsTimer()
		if self.timerAllow() and not self.stopped():
			if self.concurrencyProcess(): self.executeProcess(media = media, niche = niche, titles = titles, years = years, time = time, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, numberSeason = numberSeason, numberEpisode = numberEpisode, numberPack = numberPack, language = language, country = country, network = network, studio = studio, pack = pack, duration = duration, exact = exact, silent = silent, cacheLoad = cacheLoad, cacheSave = cacheSave, hostersAll = hostersAll, hostersPremium = hostersPremium)
			else: self.executeThread(media = media, niche = niche, titles = titles, years = years, time = time, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, numberSeason = numberSeason, numberEpisode = numberEpisode, numberPack = numberPack, language = language, country = country, network = network, studio = studio, pack = pack, duration = duration, exact = exact, silent = silent, cacheLoad = cacheLoad, cacheSave = cacheSave, hostersAll = hostersAll, hostersPremium = hostersPremium)
		self.statisticsUpdate(duration = timer)
		self.concurrencyUnlock()

		return self.result()

	def executeThread(self, media, niche, titles, years = None, time = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, numberSeason = None, numberEpisode = None, numberPack = None, language = None, country = None, network = None, studio = None, pack = None, duration = None, exact = False, silent = False, cacheLoad = True, cacheSave = True, hostersAll = None, hostersPremium = None):
		self.executeSearch(media = media, niche = niche, titles = titles, years = years, time = time, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, numberSeason = numberSeason, numberEpisode = numberEpisode, numberPack = numberPack, language = language, country = country, network = network, studio = studio, pack = pack, duration = duration, exact = exact, silent = silent, cacheLoad = cacheLoad, cacheSave = cacheSave, hostersAll = hostersAll, hostersPremium = hostersPremium)

	def executeProcess(self, media, niche, titles, years = None, time = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, numberSeason = None, numberEpisode = None, numberPack = None, language = None, country = None, network = None, studio = None, pack = None, duration = None, exact = False, silent = False, cacheLoad = True, cacheSave = True, hostersAll = None, hostersPremium = None):
		result = Pool.processData()
		parameters = {'result' : result, 'media' : media, 'niche' : niche, 'titles' : titles, 'years' : years, 'time' : time, 'idImdb' : idImdb, 'idTmdb' : idTmdb, 'idTvdb' : idTvdb, 'idTrakt' : idTrakt, 'numberSeason' : numberSeason, 'numberEpisode' : numberEpisode, 'numberPack' : numberPack, 'language' : language, 'country' : country, 'network' : network, 'studio' : studio, 'pack' : pack, 'duration' : duration, 'exact' : exact, 'silent' : silent, 'cacheLoad' : cacheLoad, 'cacheSave' : cacheSave, 'hostersAll' : hostersAll, 'hostersPremium' : hostersPremium}

		process = Pool.process(target = self._executeProcess, kwargs = parameters)
		ProviderBase.Execution.append(process)
		process.start()
		process.join(self.timerRemaining())

		try: self.statisticsSet(result['statistics'])
		except: pass

		if not self.stopped():
			try:
				streams = Converter.jsonFrom(result['result'])
				self.resultSet([Stream.load(data = stream['stream']) for stream in streams])
			except: pass

	def _executeProcess(self, result, media, niche, titles, years = None, time = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, numberSeason = None, numberEpisode = None, numberPack = None, language = None, country = None, network = None, studio = None, pack = None, duration = None, exact = False, silent = False, cacheLoad = True, cacheSave = True, hostersAll = None, hostersPremium = None):
		# If the process is terminated (when calling stop() or when the timeout is reached with process.join(self.timerRemaining())), the "result" dictionary might be destroyed while the process is still running.
		# Updating the dictionary in such a case throws a broken pipe error which is written to the Kodi log: BrokenPipeError: [Errno 32] Broken pipe
		# Catch these errors to avoid filling up the log.
		try:
			# Use the locks and sempahores from the multiprocessing library.
			# Using these classes from the threading library might occasionally casue sporadic deadlocks in the provider process.
			# Every now and then, a few (1-3) providers might get stuck at the end of the scraping process and don't finish until the timeout in join() was reached.
			# The providers are different each time and get stuck in different parts of their code.
			# Not entirley sure why this happens, but it might be caused by deadlocks in mutal exclusion classes from the threading library.
			# Using these classes from the multiprocessing library seems to fix it.
			Pool.processIntiailize()

			result['result'] = None
			result['statistics'] = None
			self.executeSearch(media = media, niche = niche, titles = titles, years = years, time = time, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, numberSeason = numberSeason, numberEpisode = numberEpisode, numberPack = numberPack, language = language, country = country, network = network, studio = studio, pack = pack, duration = duration, exact = exact, silent = silent, cacheLoad = cacheLoad, cacheSave = cacheSave, hostersAll = hostersAll, hostersPremium = hostersPremium)
			result['result'] = self.resultJson()
			result['statistics'] = self.statistics()
		except BrokenPipeError: pass
		except: self.logError()

	# NB: This function is overwritten in ProviderWeb. Make sure to add any future updates in this function to ProviderWeb as well.
	def executeSearch(self, media, niche, titles, years = None, time = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, numberSeason = None, numberEpisode = None, numberPack = None, language = None, country = None, network = None, studio = None, pack = None, duration = None, exact = False, silent = False, cacheLoad = True, cacheSave = True, hostersAll = None, hostersPremium = None):
		try:
			timer = self.statisticsTimer()
			streams = self.cacheRetrieve(cache = cacheLoad, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, numberSeason = numberSeason, numberEpisode = numberEpisode)
			if streams is None:
				if cacheSave: self.cacheInitialize(idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, numberSeason = numberSeason, numberEpisode = numberEpisode)
				self.parametersSet(media = media, niche = niche, titles = titles, years = years, time = time, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, numberSeason = numberSeason, numberEpisode = numberEpisode, numberPack = numberPack, language = language, country = country, network = network, studio = studio, pack = pack, duration = duration, exact = exact, silent = silent)
				self.statisticsUpdateSearch(query = True)
				threads = [self.thread(self.search, media, niche, titles, years, time, idImdb, idTmdb, idTvdb, idTrakt, numberSeason, numberEpisode, numberPack, language, country, network, studio, pack, exact, silent, cacheLoad, cacheSave, hostersAll, hostersPremium)]
				self.threadExecute(threads = threads, factor = ProviderBase.TimeFactorScrape, limit = 1) # Outer code in core.py already started a thread per provider. Execute directly without threading.
			else:
				self.statisticsUpdateSearch(cache = True)
				self.resultSet(streams)
			self.statisticsUpdateSearch(duration = timer)
		except: Logger.error()

	##############################################################################
	# SEARCH
	##############################################################################

	# Can be implemented by subclasses.
	def search(self, media = None, niche = None, titles = None, years = None, time = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, numberSeason = None, numberEpisode = None, numberPack = None, language = None, country = None, network = None, studio = None, pack = None, exact = None, silent = False, cacheLoad = True, cacheSave = True, hostersAll = None, hostersPremium = None):
		pass

	def searchValid(self, data, validateTitle = True, validateYear = True, validateShow = True, validateSeason = True, validateEpisode = True, validateAdjust = None, deviation = True, title = None, titleCollection = None):
		return Stream.validName(
			data = data,

			media = self.parameterMedia(),
			niche = self.parameterNiche(),

			title = self.parameterTitles()['processed']['all'] if title is None else title,
			titleCollection = self.parameterTitles()['processed']['collection'] if titleCollection else titleCollection,
			year = self.parameterYears()['median'],

			season = self.parameterNumberSeason(),
			episode = self.parameterNumberEpisode(),
			number = self.parameterNumberPack(),

			validateAdjust = validateAdjust,
			validateTitle = validateTitle,
			validateYear = validateYear,
			validateShow = validateShow,
			validateSeason = validateSeason,
			validateEpisode = validateEpisode,

			deviation = deviation,
		)

	##############################################################################
	# RESOLVE
	##############################################################################

	def resolver(self):
		return self.mData['resolver']

	def resolverSet(self, resolver = None):
		self.mData['resolver'] = resolver

	def resolve(self, link, renew = False):
		# NB: Reset the scraping timeout.
		# Otherwise resolving can fail during binge scraping.
		# The provider is in idle state for a long time during binging, waiting for the current playback to finish.
		# Once the next episode is started, resolving can fail, because any network request in the provider (eg: accountRequest()) checks the scraping timeout.
		# Eg: YggTorrent.
		self.clear()

		return self.resolveLink(link = link, renew = renew)

	# Can be implemented by subclasses.
	# If headers/cookies have to be added to the resolved link:
	#	1. Either update the headers/cookies function parameters (passed by reference).
	#	2. Or add the headers/cookies to the link that is returned.
	def resolveLink(self, link, data = None, headers = None, cookies = None, renew = False):
		return link

	##############################################################################
	# PRIORITY
	##############################################################################

	def priority(self, settings = True, type = True, order = True):
		priority = [0, 0, 0]

		if settings:
			scrape = self.scrapePriority()
			if not scrape: priority[0] = 99999
			else: priority[0] = scrape

		if type:
			if self.typeLocal(): priority[1] = 1
			elif self.typeSpecial(): priority[1] = 2
			elif self.typeCenter(): priority[1] = 3
			elif self.typePremium(): priority[1] = 4
			else: priority[1] = 5

		if order:
			priority[2] = int(self.order(inverse = True) * 10000)

		return int(''.join([str(i).zfill(5) for i in priority]))

	# In modules/core.py we start the provider threads in order of priority.
	# However, if many providers all have the same scrapePriority(), they will be executing in parallel.
	# During execution, there is no more priority and Python can interleave/schedule the threads in any order.
	# The main part of each provider is the Stream creation/validation, which takes by far the longest.
	# Providers that retrieve a lot of links (eg Orion) might end up finishing last, although they were started first, since they need a lot of time for the Streams.
	# Alow these providers, and providers with a custom set priority, to execute their Stream code before others.
	# This will allow providers that started first to also finish earlier (depending on how many streams they have), since their threads gets priority and are interleaved more often.
	# These extra lockings should not increase scraping time too much, maybe 1-2 secs for 25 providers (this might just be some deviation and not actually increase the time).
	# This might actually save some time, since threads are interleaved less frequently, avoiding some overhead?

	def priorityStart(self, lock = None):
		if not ProviderBase.PriorityEnabled: return None

		id = self.id()
		priority = self.priority()
		locked = None
		locker = lock['lock'] if lock else None

		# Create a shallow copy to ignore new providers that enter here after the current provider has already started.
		locks = Tools.copy(ProviderBase.PriorityLocks, deep = False)

		# Get all providers with a lower (better) or same priority.
		# If the priority is the same, only use those locks that were added BEFORE the current lock, otherwise there seems to be a deadlock (but maybe only when using PriorityChunk == 100).
		temp = []
		for i in Tools.listSort(locks.keys()):
			if i < priority: temp.append(locks[i])
			elif i == priority:
				if locker:
					index = -1
					for j in range(len(locks[i])):
						if locks[i][j]['lock'] == locker:
							index = j
							break
					if index > 0: temp.append(locks[i][:j])
				else:
					temp.append(locks[i])
			else: break
		locks = Tools.listFlatten(temp)

		# Do not wait for locks by the same provider, such as multiple threads or searchConcurrency().
		# Otherwise sub-threads of the same provider might deadlock, because they wait for their parent thread to finish, and the parent thread does not finish, because the child threads are not done yet.
		locks = [i for i in locks if not i['id'] == id]

		# If we already created the lock in a previous iteration, sleep a little bit.
		# This forces Python to schedule another thread.
		# Without this, the same provider might regain the lock after each iteration of the outer chunk loop.
		# This will then process each of the chunks one after the other, without giving other providers a chance to execute.
		# When sleeping, we can allow another provider to finish its stream processing, so it can continue with the network request of the next page, or if finished, allow another provider to start.
		# Do not sleep if there are only a few providers left, otherwise we just waste time.
		if locker and len(locks) > 3: Time.sleep(ProviderBase.PriorityDelay)

		# Use own lock.
		# Must happen after the shallow copy, otherwise me wait for our own lock.
		if locker is None: locker = Lock()
		locker.acquire()
		if not priority in ProviderBase.PriorityLocks: ProviderBase.PriorityLocks[priority] = []
		ProviderBase.PriorityLocks[priority].append({'id' : id, 'lock' : locker})

		# Wait for all other prioviders with a lower (better) priority to finish.
		# Use a timeout, in case there is a catastrophic failure in a provider that never unlocks (should not really happen).
		# Using a timeout: in the best case we avoid deadlock. In the worst case, we just skip the locks and are back to more-or-less no priority, as if ProviderBase.PriorityEnabled=False.
		for i in locks:
			valid = i['lock'].acquire(timeout = ProviderBase.PriorityTimeout)
			if valid: i['lock'].release()
			else: locked = i['id']

		if locked:
			self.log('A provider (%s) priority lock timed out. This should not happen!' % locked)
			locked = False
		else:
			locked = True

		# In case multiple providers with the same priority all exit the loop above at the same time.
		# Only use this inner lock if we did not get a timeout from a lock above.
		# Since that catastrophic provider probably also holds this lock.
		if locked: ProviderBase.PriorityLock.acquire()

		return {'lock' : locker, 'locked' : locked}

	def priorityEnd(self, lock):
		if not ProviderBase.PriorityEnabled: return None

		# This function could be called multiple times, once for normal unlocking, once at the end of the try-catch statement.
		# Only unlock if the lock was found, that is, it was not unlocked previously.
		if lock:
			found = False
			priority = self.priority()
			if priority in ProviderBase.PriorityLocks:
				for i in ProviderBase.PriorityLocks[priority]:
					if i['lock'] == lock['lock']:
						ProviderBase.PriorityLocks[priority].remove(i)
						found = True
						break

			if found:
				if lock['locked']: ProviderBase.PriorityLock.release()
				lock['lock'].release()

	def priorityChunks(self, items):
		if not ProviderBase.PriorityEnabled: return [items]

		# Divide into chunks, to let other providers continue in between the chunks.
		# Otherwise if, eg Orion, returns 2000 links, it will block all other providers while it processed all 2000 streams, which can take a long time.
		# Use 250 and not 200 as chunk size. Some providers retrieve 250 items per page, and we want to process them all in a single chunk.

		# On slower devices, use a lower chunk size.
		# Processing a few 100 links from Orion on a slow device can take very long, causing these errors:
		#	A provider (orionoid) priority lock timed out. This should not happen!
		# Although these errors are not a big problem, still reduce the chunk size.
		# If 20 or 250, the chunk size does not seem to have a huge difference on the scraping time.

		if ProviderBase.PriorityChunked is None: # Only do once, since Hardware.performanceRating() can take 100ms.
			ProviderBase.PriorityChunked = ProviderBase.PriorityChunk[0 if Hardware.performanceRating() > 0.7 else 1]

		return [items[i : i + ProviderBase.PriorityChunked] for i in range(0, len(items), ProviderBase.PriorityChunked)]

	##############################################################################
	# STATISTICS
	##############################################################################

	def statistics(self):
		id = self.id()
		try:
			return ProviderBase.Statistics[id]
		except:
			ProviderBase.Statistics[id] = {'duration' : 0, 'stream' : 0, 'query' : 0, 'page' : 0, 'request' : 0, 'search' : {}}
			return ProviderBase.Statistics[id]

	def statisticsSet(self, data):
		self.statistics().update(data)

	def statisticsUpdate(self, duration):
		statistics = self.statistics()

		query = 0
		page = 0
		request = 0
		for key, entry in statistics['search'].items():
			query += entry['query']
			page += entry['page']
			request += entry['request']

		statistics['duration'] = self._statisticsDuration(duration)
		statistics['stream'] = self.resultCount()
		statistics['query'] = query
		statistics['page'] = page
		statistics['request'] = request

	def statisticsUpdateSearch(self, duration = None, query = None, page = None, request = None, stream = None, cache = None):
		search = self.parameterQueryRaw()
		statistics = self.statistics()

		try: entry = statistics['search'][search]
		except: entry = statistics['search'][search] = {'duration' : 0, 'stream' : 0, 'query' : 0, 'page' : 0, 'request' : 0, 'cache' : False}

		if not duration is None: entry['duration'] = max(entry['duration'], self._statisticsDuration(duration))
		if not query is None: entry['query'] += int(query)
		if not page is None: entry['page'] += int(page)
		if not request is None: entry['request'] += int(request)
		if not stream is None: entry['stream'] += int(stream)
		if not cache is None: entry['cache'] += cache

	def _statisticsDuration(self, duration):
		try: return duration.elapsed(milliseconds = True)
		except: return duration

	@classmethod
	def statisticsClear(self):
		ProviderBase.Statistics = {}

	@classmethod
	def statisticsTimer(self):
		# Measure only the time the provider is actively computing.
		# Otherwise time continues while the thread is asleep/idle/interleaved and does not represent the actual time it took.
		# ModeProcessor and ModeThread sometimes measure some providers as taking a few seconds longer than the entire scraping process.
		# ModeMonotonic seems to be mostly accurate.
		return Time(start = True, mode = Time.ModeMonotonic)
