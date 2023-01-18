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

from lib.providers.core.premium import ProviderPremium
from lib.providers.core.json import ProviderJson
from lib.debrid.easynews import Core
from lib.modules.stream import Stream
from lib.modules.network import Networker
from lib.modules.convert import ConverterDuration
from lib.modules.tools import Tools

'''
	Version 2:
		{"sid":"xxxxxxxxxxxxxxxxxxx","results":275,"perPage":"100","numPages":3,"dlFarm":"auto","dlPort":443,"baseURL":"https://members.easynews.com","downURL":"https://members.easynews.com/dl","thumbURL":"https://th.easynews.com/thumbnails-","page":1,"groups":[{"alt.binaries.boneless":94},{"alt.binaries.movies.divx":37}],"data":[{"0":"fc3f66c37e1b1ac254c1194f198eee47071797ea0","1":"","2":".avi","3":"80 x 34","4":"708.8 MB","5":"01-20-2010 01:37:50","6":"!!!!malin partage- &quot;Avatar.2009.FRENCH.REPACK.1CD.TS.MD.XViD.By.Hadopix.[emule-island.com].part13.rar&quot; yEnc (01/94) (Avatar.2009.FRENCH.REPACK.1CD.TS.MD.XViD.By.Hadopix.[emule-island.com].avi AutoUnRAR)","7":"Yenc@power-post.org (Yenc-PP-A&amp;A-FR)","8":"<autorar-wfmdnfm3pbkqx8vWnZ2dnUVZ7sYAAAAA@powerusenet.com-9b8dd54c>","9":"alt.binaries.movies.divx.french","10":"Avatar.2009.FRENCH.REPACK.1CD.TS.MD.XViD.By.Hadopix.[emule-island.com]","11":".avi","12":"XVID","13":"1","14":"2h:33m:48s","15":634,"16":48000,"17":25,"18":"MP3","19":"e6d01cc707cece713f0a7790a3f846f7","20":"&#8734;","35":"1cd8","type":"VIDEO","height":"272","width":"640","theight":34,"twidth":80,"fullres":"640 x 272","alangs":null,"slangs":null,"passwd":false,"virus":false,"expires":"&#8734;","nfo":"","ts":1263951470,"rawSize":743220278,"volume":false,"sc":false,"primaryURL":"//members.easynews.com","fallbackURL":"//members.easynews.com","sb":1},{"0":"75c3cfa9cadcb822755ab686d57b4c260d9d87515","1":"","2":".mkv","3":"160 x 90","4":"10.3 GB","5":"02-10-2019 19:14:49","6":"&quot;140d77ffb54624d092deed34dd.a56a&quot; yEnc (01/95) (Avatar.2009.720p.BluRay.DD5.1.x264-playHD.mkv AutoUnRAR)","7":"Bob &lt;bob@home.me&gt;","8":"<autorar-9I.9aKcrxpjQ.4WOFxkklz$ZftioIIbhlOB@8rtQY8dWx.05ZHk3-47c55247>","9":"alt.binaries.flowed","10":"Avatar.2009.720p.BluRay.DD5.1.x264-playHD","11":".mkv","12":"H264","13":"1","14":"2h:58m:9s","15":8286,"16":48000,"17":23.98,"18":"AC3","19":"51e4c71774a819b434be369bbaf119bb","20":"&#8734;","35":"8c20","type":"VIDEO","height":"720","width":"1280","theight":90,"twidth":160,"fullres":"1280 x 720","alangs":["eng"],"slangs":["eng","rum"],"passwd":false,"virus":false,"expires":"&#8734;","nfo":"","ts":1549826089,"rawSize":11072206783,"volume":false,"sc":false,"primaryURL":"//members.easynews.com","fallbackURL":"//members.easynews.com","sb":1}],"returned":81,"unfilteredResults":100,"hidden":19,"classicThumbs":"0","fields":{"2":"Extension","3":"Resolution","4":"Size","5":"Post Date","6":"Subject","7":"Poster","9":"Group","10":"Filename","12":"Video Codec","14":"Runtime","15":"BPS","16":"Sample Rate","17":"FPS","18":"Audio Codec","20":"Expire Date","FullThumb":"Full Thumb"},"hthm":0,"hInfo":0,"st":"adv","sS":"3","stemmed":"true","largeThumb":"0","largeThumbSize":"268x206","gsColumns":[{"num":6,"name":"subject"},{"num":4,"name":"size"},{"num":9,"name":"group"},{"num":5,"name":"time"},{"num":7,"name":"poster"},{"num":-1,"name":"set"}]}

	Version 3:
		{"sid":"xxxxxxxxxxxxxxxxxxx","groups":{"alt.binaries.boneless":22,"alt.binaries.mom":18},"data":[{"groups":"alt.binaries.movies.divx.french","mid":"<autorar-wfmdnfm3pbkqx8vWnZ2dnUVZ7sYAAAAA@powerusenet.com-9b8dd54c>","id":"1cd8","poster":"Yenc@power-post.org (Yenc-PP-A&amp;A-FR)","subject":"!!!!malin partage- &quot;Avatar.2009.FRENCH.REPACK.1CD.TS.MD.XViD.By.Hadopix.[emule-island.com].part13.rar&quot; yEnc (01/94) (Avatar.2009.FRENCH.REPACK.1CD.TS.MD.XViD.By.Hadopix.[emule-island.com].avi AutoUnRAR)","sig":"1263951470-1cd80b4f659c69fdf19b6375cac1300e","expires":"&#8734;","extension":".avi","filename":"Avatar.2009.FRENCH.REPACK.1CD.TS.MD.XViD.By.Hadopix.[emule-island.com]","type":"VIDEO","hash":"fc3f66c37e1b1ac254c1194f198eee47071797ea0","date":"2010-01-20 01:37:50","timestamp":1263951470,"size":"708.8 MB","bytes":743220278,"set":"e6d01cc707cece713f0a7790a3f846f7","colid":"dc5d12f667761e76954663a5b4800870","width":640,"height":272,"acodec":"MP3","vcodec":"XVID","bitrate":634,"bps":634584,"framerate":25,"hz":48000,"runtime":"2h:33m:48s","time":9228,"disposition":"1"},{"groups":"alt.binaries.flowed","mid":"<autorar-9I.9aKcrxpjQ.4WOFxkklz$ZftioIIbhlOB@8rtQY8dWx.05ZHk3-47c55247>","id":"8c20","poster":"Bob &lt;bob@home.me&gt;","subject":"&quot;140d77ffb54624d092deed34dd.a56a&quot; yEnc (01/95) (Avatar.2009.720p.BluRay.DD5.1.x264-playHD.mkv AutoUnRAR)","sig":"1549826089-8c20b8a35d5bf45724321e238cc509cf","expires":"&#8734;","extension":".mkv","filename":"Avatar.2009.720p.BluRay.DD5.1.x264-playHD","type":"VIDEO","hash":"75c3cfa9cadcb822755ab686d57b4c260d9d87515","date":"2019-02-10 19:14:49","timestamp":1549826089,"size":"10.3 GB","bytes":11072206783,"set":"51e4c71774a819b434be369bbaf119bb","colid":"852a6a2d0acd66b99436256de58c152c","width":1280,"height":720,"alang":["eng"],"slang":["eng","rum"],"acodec":"AC3","vcodec":"H264","bitrate":8286,"bps":8286438,"framerate":23.98,"hz":48000,"runtime":"2h:58m:9s","time":10689,"disposition":"1"}],"results":218,"numPages":3,"page":1,"returned":100,"fields":{"1":"Extension","2":"Resolution","3":"Size","4":"Post Date","5":"Subject","6":"Poster","7":"Group","8":"Filename","9":"Video Codec","10":"Runtime","11":"BPS","12":"Sample Rate","13":"FPS","14":"Audio Codec","16":"Expire Date","17":"set","FullThumb":"Full Thumb"},"stemmed":"true","ColOrder":[{"num":20,"name":"thumb"},{"num":8,"name":"filename"},{"num":4,"name":"date posted"},{"num":3,"name":"size"},{"num":6,"name":"poster"},{"num":7,"name":"group"}],"Groups":[]}
'''

class Provider(ProviderPremium, ProviderJson):

	_Link						= {
									ProviderJson.Version2 : ['https://members.easynews.com'],
									ProviderJson.Version3 : ['https://members-beta.easynews.com'],
								}
	_Path						= {
									ProviderJson.Version2 : '2.0/search/solr-search',
									ProviderJson.Version3 : '3.0/api/search',
								}
	_Download					= {
									ProviderJson.Version2 : '%s/dl/%s',
									ProviderJson.Version3 : '%s/os/3.0/auto/443/%s',
								}
	_File						= {
									ProviderJson.Version2 : '%s%s/%s%s',
									ProviderJson.Version3 : '%s%s/%s?sid=%s&sig=%s',
								}
	_Curve						= {
									ProviderJson.Version2 : ProviderJson.RequestCurveSecp512r1,
									ProviderJson.Version3 : None,
								}

	_LimitOffset 				= 1000 # Number of items to return per page. Although higher numbers are possible in the query, the result JSON always say "perPage":"1000", so it seems 1000 is the limit.

	_CategoryVideo				= 'VIDEO'

	_CustomSpam					= 'spam'
	_CustomGroup				= 'group'
	_CustomDuplicates			= 'duplicates'
	_CustomDuration				= 'duration'
	_CustomStemmed				= 'stemmed'

	_ParameterSearchKeyword		= 'gps'
	_ParameterSearchSubject		= 'sbj'
	_ParameterSearchType		= 'st'
	_ParameterCategory			= 'fty[]'
	_ParameterOffsetPage		= 'pno'
	_ParameterSort1Value		= 's1'
	_ParameterSort1Order		= 's1d'
	_ParameterSort2Value		= 's2'
	_ParameterSort2Order		= 's2d'
	_ParameterSort3Value		= 's3'
	_ParameterSort3Order		= 's3d'
	_ParameterSortSize			= 'dsize'
	_ParameterSortTime			= 'dtime'
	_ParameterDuplicates		= 'u'
	_ParameterGroup				= 'gx'
	_ParameterSpam				= 'spamf'
	_ParameterStem				= 'nostem'

	_ParameterOffset			= {ProviderJson.Version2 : 'pby',		ProviderJson.Version3 : 'dni'}
	_ParameterRelevance			= {ProviderJson.Version2 : 'relevance',	ProviderJson.Version3 : 'rel'}
	_ParameterAdvanced			= {ProviderJson.Version2 : 'adv',		ProviderJson.Version3 : 'advanced'}
	_ParameterDescending		= {ProviderJson.Version2 : '-',			ProviderJson.Version3 : 'Dec'}

	_AttributeData				= 'data'
	_AttributeSid				= 'sid'
	_AttributeWidth				= 'width'
	_AttributeHeight			= 'height'
	_AttributePageNumber		= 'page'
	_AttributePageCount			= 'numPages'
	_AttributePassword			= 'passwd'
	_AttributeVirus				= 'virus'

	_AttributeSig				= {ProviderJson.Version2 : '0',			ProviderJson.Version3 : 'sig'}
	_AttributeHash				= {ProviderJson.Version2 : '19',		ProviderJson.Version3 : 'hash'}
	_AttributeFilename			= {ProviderJson.Version2 : '10',		ProviderJson.Version3 : 'fn'} # V3 changed 'filename' to 'fn'
	_AttributeExtension			= {ProviderJson.Version2 : '11',		ProviderJson.Version3 : 'extension'}
	_AttributeVideoCodec		= {ProviderJson.Version2 : '12',		ProviderJson.Version3 : 'vcodec'}
	_AttributeAudioCodec		= {ProviderJson.Version2 : '18',		ProviderJson.Version3 : 'acodec'}
	_AttributeAudioLanguage		= {ProviderJson.Version2 : 'alangs',	ProviderJson.Version3 : 'alang'}
	_AttributeSubtitleLanguage	= {ProviderJson.Version2 : 'slangs',	ProviderJson.Version3 : 'slang'}
	_AttributeSubject			= {ProviderJson.Version2 : '6',			ProviderJson.Version3 : 'subject'}
	_AttributeSize				= {ProviderJson.Version2 : 'rawSize',	ProviderJson.Version3 : 'size'} # V3 changed 'bytes' to 'size'
	_AttributePoster			= {ProviderJson.Version2 : '7',			ProviderJson.Version3 : 'poster'}
	_AttributeTime				= {ProviderJson.Version2 : 'ts',		ProviderJson.Version3 : 'timestamp'}
	_AttributeDuration			= {ProviderJson.Version2 : '14',		ProviderJson.Version3 : 'runtime'}

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		core = Core()

		version = self.customVersion(default = ProviderJson.VersionAutomatic)
		if version == ProviderJson.VersionAutomatic:
			version = core.accountVersion(detect = True) # Always redetect, since the user might have changed the version preferences.
			if version is None: version = ProviderJson.Version2
			version = str(int(version))

		self.mVersion = version
		self.mSid = None

		# Retrieve these values BEFORE calling ProviderPremium.initialize(...).
		# Otherwise the call to ProviderPremium.initialize(...) replaces the custom settings, and when calling these functions in ProviderJson.initialize(...), they return None.
		# Alternatively, also pass the "custom" list to ProviderPremium.initialize(...).
		customDuplicates = self.custom(id = Provider._CustomDuplicates)
		customGroup = self.custom(id = Provider._CustomGroup)
		customSpam = self.custom(id = Provider._CustomSpam)
		customStem = not self.custom(id = Provider._CustomStemmed)

		ProviderPremium.initialize(self, core = core)
		ProviderJson.initialize(self,
			description				= '{name} is a premium usenet service that has been around for a long time. The provider neither handles NZBs, nor interacts with the usenet, but instead directly streams unpacked videos from the {name} cache. {name} contains many English results, but is also a great source for other languages, especially European languages. {name} has two different website interfaces. Old accounts can only access the version 2.0 interface. New accounts can only access the version 3.0 interface. Automatic detection determines the version from your authenticated account.',
			rank					= 5,
			performance				= ProviderJson.PerformanceExcellent,

			link					= Provider._Link[version],

			certificateCurve		= Provider._Curve[version], # More info in cloudflare.py.

			accountOther			= ProviderJson.AccountInputCustom,
			accountAuthentication	= {
										ProviderJson.ProcessMode : ProviderJson.AccountModeScrape,
										ProviderJson.ProcessAuthorization : ProviderJson.AccountAuthorizationBasic,
									},

			custom					= [
										{
											ProviderJson.SettingsId				: Provider._CustomStemmed,
											ProviderJson.SettingsLabel			: 'Stemmed Keywords',
											ProviderJson.SettingsDefault		: True,
											ProviderJson.SettingsType			: ProviderJson.SettingsTypeBoolean,
											ProviderJson.SettingsDescription	: 'Use keyword stemming during search. Stemmed keywords are new keywords derived from given main keywords in order to find more results.',
										},
										{
											ProviderJson.SettingsId				: Provider._CustomSpam,
											ProviderJson.SettingsLabel			: 'Spam Filter',
											ProviderJson.SettingsDefault		: False,
											ProviderJson.SettingsType			: ProviderJson.SettingsTypeBoolean,
											ProviderJson.SettingsDescription	: 'Filter out results that are considered spam. Spam filters can be customized on {name}\' website.',
										},
										{
											ProviderJson.SettingsId				: Provider._CustomGroup,
											ProviderJson.SettingsLabel			: 'Group Filter',
											ProviderJson.SettingsDefault		: False,
											ProviderJson.SettingsType			: ProviderJson.SettingsTypeBoolean,
											ProviderJson.SettingsDescription	: 'Filter out certain usenet groups. Group filters can be customized on {name}\' website.',
										},
										{
											ProviderJson.SettingsId				: Provider._CustomDuplicates,
											ProviderJson.SettingsLabel			: 'Duplicate Filter',
											ProviderJson.SettingsDefault		: True,
											ProviderJson.SettingsType			: ProviderJson.SettingsTypeBoolean,
											ProviderJson.SettingsDescription	: 'Filter out duplicate results. Removing duplicates can reduce scraping time.',
										},
										{
											ProviderJson.SettingsId				: Provider._CustomDuration,
											ProviderJson.SettingsLabel			: 'Duration Filter',
											ProviderJson.SettingsDefault		: True,
											ProviderJson.SettingsType			: ProviderJson.SettingsTypeBoolean,
											ProviderJson.SettingsDescription	: 'Filter out results that have a considerable shorter runtime than expected. Shorter runtimes might indicate incorrect results or corrupted files.',
										},
									],
			customVersion		= [ProviderJson.VersionAutomatic, ProviderJson.Version2, ProviderJson.Version3],

			# EasyNews does not support movie collection or show/season packs.
			# EasyNews disassembles packs into individual files.
			# Hence, although there are packs, the search results return the individual files inside the pack as separate items.
			# It is also important to search both the keywords (gps=%s) and the subject (sbj=%s), because the full name might not appear in the keywords (file name).
			# Example:
			#	gps: The.Lord.Of.The.Rings.Trilogy.Theatrical.480p.BRRip.XviD.AC3-FLAWL3SS
			#	sbj: the.fellowship.of.the.ring-flawl3ss.avi
			# Still enable supportPack, because a few files are not found if the search does not contain specific pack keywords, since the gps and sbj do not contain the same keywords.
			supportMovie			= True,
			supportShow				= True,
			supportPack				= True,

			offsetStart				= 1,
			offsetIncrease			= 1,

			queryExtraEpisode		= [ # Some files only have the written-out format.
										'%s season %s episode %s' % (ProviderJson.TermTitleShow, ProviderJson.TermSeason, ProviderJson.TermEpisode),
										'%s season %s episode %s' % (ProviderJson.TermTitleShow, ProviderJson.TermSeasonZero, ProviderJson.TermEpisodeZero),
									],

			searchQuery				= {
										ProviderJson.RequestPath : Provider._Path[version],
										ProviderJson.RequestData : {
											Provider._ParameterSearchKeyword	: ProviderJson.TermQuery,							# Search by keywords
											Provider._ParameterSearchSubject	: ProviderJson.TermQuery,							# Search by subject
											Provider._ParameterCategory			: ProviderJson.TermCategory,						# Category
											Provider._ParameterOffsetPage		: ProviderJson.TermOffset,							# Page number
											Provider._ParameterOffset[version]	: Provider._LimitOffset,							# Results per page
											Provider._ParameterSearchType		: Provider._ParameterAdvanced[version],				# Advanced search
											Provider._ParameterSort1Value		: Provider._ParameterRelevance[version],			# First sort attribute: relevance
											Provider._ParameterSort1Order		: Provider._ParameterDescending[version],			# First sort order: descending
											Provider._ParameterSort2Value		: Provider._ParameterSortSize,						# Second sort attribute: size
											Provider._ParameterSort2Order		: Provider._ParameterDescending[version],			# Second sort order: descending
											Provider._ParameterSort3Value		: Provider._ParameterSortTime,						# Third sort attribute: time
											Provider._ParameterSort3Order		: Provider._ParameterDescending[version],			# Third sort order: descending
											Provider._ParameterDuplicates		: customDuplicates,									# Remove duplicates
											Provider._ParameterGroup			: customGroup,										# Group exclusion filters
											Provider._ParameterSpam				: customSpam,										# Spam exclusion filters
											Provider._ParameterStem				: customStem,										# Stemmed keyword searches.
										},
									},
			searchCategory			= Provider._CategoryVideo,

			extractList				= Provider._AttributeData,
			extractLink				= [[Provider._AttributeHash[version]], [Provider._AttributeFilename[version]], [Provider._AttributeExtension[version]], [Provider._AttributeSig[version]]],
			extractVideoWidth		= Provider._AttributeWidth,
			extractVideoHeight		= Provider._AttributeHeight,
			extractVideoCodec		= Provider._AttributeVideoCodec[version],
			extractAudioSystem		= Provider._AttributeAudioCodec[version], # Audio system and codec mixed in this attribute.
			extractAudioCodec		= Provider._AttributeAudioCodec[version], # Audio system and codec mixed in this attribute.
			extractAudioLanguage	= Provider._AttributeAudioLanguage[version],
			extractSubtitleLanguage	= Provider._AttributeSubtitleLanguage[version],
			extractFileName			= [[Provider._AttributeFilename[version]], [Provider._AttributeExtension[version]]], # File name and extension. Might only contaian the file name, without the parent archive name.
			extractFileExtra		= Provider._AttributeSubject[version], # Parent archive/container name. Extract and pass to stream to detect additional metadata (not used during title validation).
			extractFileSize			= Provider._AttributeSize[version],
			extractFileContainer	= Provider._AttributeExtension[version],
			extractReleaseUploader	= Provider._AttributePoster[version],
			extractSourceTime		= Provider._AttributeTime[version],
		)

	##############################################################################
	# ACCOUNT
	##############################################################################

	def accountUsername(self):
		return self.core().accountUsername()

	def accountPassword(self):
		return self.core().accountPassword()

	##############################################################################
	# PROCESS
	##############################################################################

	def processInitial(self):
		# Increase the number of queries when scraping episodes.
		# Episodes are often difficult to find, due to there being few files, and files using other naming conventions.
		# We therefore add additional "queryExtraEpisode" values to increase chances of finding files.
		# These additional queries could lead to the lower queries being removed due to the query limit.
		# Eg: For "Game of Thrones", the "GoT" alias title might not be used, since there are already too many queries.
		# Additional queries to the EasyNews API should not take much extra time.
		# Only use the increased limit if the user has not manually set a limit for the EasyNews provider.
		if self.parameterMediaShow() and not self.scrapeQuery(settings = True, default = False):
			limit = self.scrapeQuery(settings = False, default = True)
			if limit:
				value = min(16, max(6, limit * 2))
				if value > limit: self.scrapeQuerySet(value = value, settings = True)

	def processOffset(self, data, items):
		if data[Provider._AttributePageNumber] >= data[Provider._AttributePageCount]: return ProviderJson.Skip

	def processData(self, data):
		self.mSid = data[Provider._AttributeSid]
		return data

	def processBefore(self, item):
		# This is now done using the spam filter.
		'''
		# Ignore password protected files.
		try:
			if item[Provider._AttributePassword]: return ProviderJson.Skip
		except: pass

		# Ignore files that were flagged as virus.
		# Do not check this anymore. Even if the archive contains a virus, EasyNews only returns the raw video file in it, without any of the other files. So it should be safe.
		try:
			if item[Provider._AttributeVirus]: return ProviderJson.Skip
		except: pass
		'''

		# Ignore files with a duration less than 5 minutes.
		if self.custom(id = Provider._CustomDuration):
			try:
				durationReal = item[Provider._AttributeDuration[self.mVersion]]
				if Tools.isString(durationReal): durationReal = ConverterDuration(durationReal.replace(':', ' ')).value(ConverterDuration.UnitSecond) # Older version had the runtime as HH:SS:MM. New version gives it in seconds already.
				if durationReal:
					if durationReal < 300: return ProviderJson.Skip
					durationExpected = self.parameterDuration()
					# EasyNews marks some movie duration between 40 to 60 minutes. However, if those files are played, they are longer.
					# Do not exclude any files longer than 30 minutes (1800).
					if durationExpected and durationReal < min(1800, durationExpected / 2): return ProviderJson.Skip
			except: self.logError()

	def processLink(self, value, item, details = None, entry = None):
		if self.mVersion == ProviderJson.Version2: link = (value[3], value[2], value[1], value[2])
		else: link = (value[0], value[2], value[1], self.mSid, value[3])
		link = Networker.linkQuote(Provider._File[self.mVersion] % link)
		link = Provider._Download[self.mVersion] % (self.link(), link)
		link = Networker.linkHeaders(link = link, headers = self.accountAuthenticationHeaders())
		#try: link = link.encode('utf-8')# do not do this, otherwise it converts to bytes object instead of string.
		#except: pass
		return link

	def processReleaseUploader(self, value, item, details = None, entry = None):
		return Networker.htmlDecode(value) # Unescape HTML entities.

	def processFileName(self, value, item, details = None, entry = None):
		return value[0] + value[1] # Add extension to filename.

	def processFilePack(self, value, item, details = None, entry = None):
		return Stream.FilePackDisabled # All files on EasyNews are individual videos, even if the file name contains pack keywords.
