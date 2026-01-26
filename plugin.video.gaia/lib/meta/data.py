# -*- coding: utf-8 -*-

'''
	Gaia Add-on
	Copyright (C) 2016 Gaia

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from lib.meta.image import MetaImage

from lib.modules.serializer import Serializer
from lib.modules.convert import ConverterTime
from lib.modules.tools import Regex, Tools, Time, Converter, Settings, Language, Country, Media, Title, Logger

class MetaData(Serializer):

	# Default

	Default	= None

	# Selection

	SelectionSingle				= False
	SelectionList				= True
	SelectionDefault			= Default

	# Fallback
	FallbackNone				= 0	# If not found, do not fall back, but return None.
	FallbackPrimary				= 1	# If not found, fall back to the next best option.
	FallbackSecondary			= 2	# If not found, fall back to the next best option. If not found, fall back to the next-next best option.
	FallbackTertiary			= 3
	FallbackQuaternary			= 4
	FallbackDefault				= Default

	# Media

	MediaMovie					= 'movie'
	MediaShow					= 'show'
	MediaSeason					= 'season'
	MediaEpisode				= 'episode'
	MediaCollection				= 'collection'
	MediaPerson					= 'person'
	MediaCharacter				= 'character'
	MediaCompany				= 'company'
	MediaDefault				= Default
	MediaAll					= [MediaMovie, MediaShow, MediaSeason, MediaEpisode, MediaCollection, MediaPerson, MediaCharacter, MediaCompany]
	MediaContent				= [MediaMovie, MediaShow, MediaSeason, MediaEpisode, MediaCollection]
	MediaFilm					= [MediaMovie, MediaCollection]
	MediaTelevision				= [MediaShow, MediaSeason, MediaEpisode]
	MediaEntity					= [MediaPerson, MediaCharacter, MediaCompany]
	MediaIndividual				= [MediaPerson, MediaCharacter]

	# Number

	NumberStandard				= 'standard'		# Officialy aired order with episodes divided into seasons.
	NumberAbsolute				= 'absolute'		# Absolute order without seasons where episodes are numbered sequentially.
	NumberDisc					= 'disc'			# Order as released on DVD or BluRay.
	NumberYear					= 'year'			# The year is used as season number. Sometimes used by TVDb for daytime shows.
	NumberRegional				= 'regional'		# TVDb.
	NumberAlternative			= 'alternative'		# TVDb.
	NumberAlternativeDisc		= 'alternativedisc'	# TVDb.
	NumberDefault				= NumberStandard
	Numbers						= [NumberStandard, NumberAbsolute, NumberDisc, NumberYear, NumberRegional, NumberAlternative, NumberAlternativeDisc]

	# Character

	CharacterTypeActor			= 'actor'
	CharacterTypeDirector		= 'director'
	CharacterTypeWriter			= 'writer'
	CharacterTypeEditor			= 'editor'
	CharacterTypeCreator		= 'creator'
	CharacterTypeHost			= 'host'
	CharacterTypeCrew			= 'crew'
	CharacterTypeProducer		= 'producer'
	CharacterTypeGuest			= 'guest'
	CharacterTypeDefault		= Default

	# Role

	CharacterRoleRunner			= 'runner'		# Showrunner
	CharacterRoleExecutive		= 'executive'	# Executive Producer
	CharacterRoleAssociate		= 'associate'	# Associate Producer
	CharacterRoleCo				= 'co'			# Co-Producer
	CharacterRoleLine			= 'line'		# Line Producer
	CharacterRoleCoordinate		= 'coordinate'	# Coordinate Producer
	CharacterRoleSupervise		= 'supervise'	# Supervise Producer
	CharacterRoleConsult		= 'consult'		# Consult Producer
	CharacterRoleSegment		= 'segment'		# Segment Producer
	CharacterRoleField			= 'field'		# Field Producer
	CharacterRoleStar			= 'star'		# Guest Star
	CharacterRoleMusical		= 'musical'		# Musical Guest
	CharacterRoleDefault		= Default

	# Company

	CompanyTypeNetwork			= 'network'
	CompanyTypeStudio			= 'studio'
	CompanyTypeProducer			= 'producer'
	CompanyTypeDistributor		= 'distributor'
	CompanyTypeEffects			= 'effects'
	CompanyTypeDefault			= Default

	# Provider

	ProviderOrion				= 'orion'
	ProviderImdb				= 'imdb'
	ProviderTmdb				= 'tmdb'
	ProviderTvdb				= 'tvdb'
	ProviderTrakt				= 'trakt'
	ProviderDefault				= Default
	Providers					= [ProviderOrion, ProviderImdb, ProviderTmdb, ProviderTvdb, ProviderTrakt]

	# Language

	LanguageOriginal			= 'original'
	LanguageAudio				= 'audio'
	LanguageSubtitle			= 'subtitle'
	LanguageSettings			= 'settings'
	LanguageUniversal			= Language.CodeUniversal
	LanguageEnglish				= Language.CodeEnglish
	LanguageUnknown				= Language.CodeUnknown	# Do not use None/True/False as values, since it is used as a dictionary key that gets (un)serialized.
	LanguageDefault				= Language.CodeNone		# Do not use None/True/False as values, since it is used as a dictionary key that gets (un)serialized.
	LanguageCommon				= [LanguageUniversal, LanguageEnglish, LanguageUnknown]
	LanguageUncommon			= [LanguageUniversal, LanguageUnknown, LanguageEnglish]
	LanguageSpecific			= [LanguageSettings, LanguageUniversal, LanguageEnglish, LanguageUnknown]
	LanguageUnspecific			= [LanguageSettings, LanguageUniversal, LanguageUnknown, LanguageEnglish]

	# Country

	CountryOriginal				= 'original'
	CountrySettings				= 'settings'
	CountryUniversal			= Country.UniversalCode
	CountryUnitedStates			= Country.CodeUnitedStates
	CountryDefault				= Default

	# Image

	# https://kodi.wiki/view/Artwork_types
	#	actor: ImageTypePhoto + ImageOpacitySolid + ImageDecorPlain
	#	characterart: ImageTypePhoto + ImageOpacityClear + ImageDecorPlain
	#	clearart: ImageTypeArtwork + ImageOpacityClear + ImageDecorEmbell
	#	clearlogo: ImageTypeIcon + ImageOpacityClear + ImageDecorEmbell
	#	icon: ImageTypeIcon + ImageOpacitySolid + ImageDecorEmbell
	#	discart: ImageTypeDisc + ImageOpacitySolid + ImageDecorEmbell
	#	thumb: ImageTypeThumbnail + ImageOpacitySolid + ImageDecorPlain
	#	banner: ImageTypeBanner + ImageOpacitySolid + ImageDecorEmbell
	#	poster: ImageTypePoster + ImageOpacitySolid + ImageDecorEmbell
	#	fanart: ImageTypeBackground + ImageOpacitySolid + ImageDecorPlain
	#	keyart (poster): ImageTypePoster + ImageOpacitySolid + ImageDecorPlain
	#	landscape (fanart): ImageTypeBackground + ImageOpacitySolid + ImageDecorEmbell

	ImageTypeIcon				= 'icon'
	ImageTypePoster				= 'poster'
	ImageTypeDisc				= 'disc'
	ImageTypePhoto				= 'photo'
	ImageTypeBanner				= 'banner'
	ImageTypeBackground			= 'background'
	ImageTypeArtwork			= 'artwork'
	ImageTypeThumbnail			= 'thumbnail'
	ImageTypeCinemagraph		= 'cinemagraph'
	ImageTypeDefault			= Default

	ImageQualityHigh			= 'high'
	ImageQualityLow				= 'low'
	ImageQualityDefault			= Default

	ImageResolutionDefault		= Default

	ImageOpacitySolid			= 'solid'
	ImageOpacityClear			= 'clear'
	ImageOpacityDefault			= Default

	ImageDecorPlain				= 'plain'	# Images without text, logo, or other decorations.
	ImageDecorEmbell			= 'embell'	# Images with text, logo, or other decorations.
	ImageDecorDefault			= Default
	ImageDecorTypes				= {
									ImageTypeIcon			: ImageDecorEmbell,
									ImageTypePoster			: ImageDecorEmbell,
									ImageTypeDisc			: ImageDecorEmbell,
									ImageTypePhoto			: ImageDecorPlain,
									ImageTypeBanner			: ImageDecorEmbell,
									ImageTypeBackground		: ImageDecorPlain,
									ImageTypeArtwork		: ImageDecorEmbell,
									ImageTypeThumbnail		: ImageDecorPlain,
									ImageTypeCinemagraph	: ImageDecorPlain,
								}

	# Genre

	GenreAction					= 'action'
	GenreScifi					= 'scifi'
	GenreFantasy				= 'fantasy'
	GenreAdventure				= 'adventure'
	GenreHorror					= 'horror'
	GenreMystery				= 'mystery'
	GenreSuspense				= 'suspense'
	GenreThriller				= 'thriller'
	GenreCrime					= 'crime'
	GenreMartial				= 'martial'
	GenreWestern				= 'western'
	GenreWar					= 'war'
	GenrePolitics				= 'politics'
	GenreHistory				= 'history'
	GenreComedy					= 'comedy'
	GenreRomance				= 'romance'
	GenreDrama					= 'drama'

	GenreFamily					= 'family'
	GenreChildren				= 'children'
	GenreAnimation				= 'animation'
	GenreAnime					= 'anime'
	GenreMusic					= 'music'
	GenreMusical				= 'musical'

	GenreDocumentary			= 'documentary'
	GenreBiography				= 'biography'
	GenreSport					= 'sport'
	GenreSporting				= 'sporting'
	GenreTravel					= 'travel'
	GenreHoliday				= 'holiday'
	GenreHome					= 'home'
	GenreFood					= 'food'

	GenreSoap					= 'soap'
	GenreReality				= 'reality'
	GenreNews					= 'news'
	GenreTalk					= 'talk'
	GenreGame					= 'game'
	GenreAward					= 'award'
	GenreMini					= 'mini'
	GenrePodcast				= 'podcast'
	GenreTelevision				= 'television'

	GenreShort					= 'short'
	GenreIndie					= 'indie'
	GenreNoir					= 'noir'

	GenreDefault				= Default

	# Vote

	VoteAbsolute				= 'absolute'		# Absolute score [0,inf]
	VoteRating					= 'rating'			# Cast rating [0,10]
	VotePercent					= 'percent'			# Cast rating as a percentage [0,1]
	VoteCount					= 'count'			# Number of votes cast [0,inf]

	# Sort

	SortNone					= None
	SortSettings				= 'settings'
	SortIndex					= 'index'			# Sort by the original order of the array as returned by the API.
	SortId						= 'id'				# Sort by ID.
	SortVote					= 'vote'			# Sort by votes/rating.
	SortVoteIndex				= 'voteindex'		# Sort by vote and then by index.
	SortVoteId					= 'voteid'			# Sort by vote and then by ID.
	SortVoteOrigin				= 'voteorigin'		# Sort by vote and then by origin.
	SortVoteOriginIndex			= 'voteoriginindex'	# Sort by vote, then by origin, and then by index.
	SortVoteOriginId			= 'voteoriginid'	# Sort by vote, then by origin, and then by ID.
	SortOrigin					= 'origin'			# Sort by origin/uploader (eg: some images might be the official ones uploaded by the admin, whereas other might be fanmade uploaded by normal users).
	SortOriginIndex				= 'originindex'		# Sort by origin and then by index.
	SortOriginId				= 'originid'		# Sort by origin and then by ID.
	SortOriginVote				= 'originvote'		# Sort by origin and then by vote.
	SortOriginVoteIndex			= 'originvoteindex'	# Sort by origin, then by vote, and then by index.
	SortOriginVoteId			= 'originvoteid'	# Sort by origin, then by vote, and then by ID.
	SortDefault					= SortNone

	# Order
	# For images, this  should not be seen as ascending/descending, but rather original/reversed order.

	OrderAscending				= 'ascending'
	OrderDescending				= 'descending'
	OrderDefault				= OrderDescending

	# Status

	StatusRumored				= 'rumored'			# Rumored, but not officially announced.
	StatusPlanned				= 'planned'			# Planned or announced, but production has not started.
	StatusPreproduction			= 'preproduction'	# Busy with initial production phase.
	StatusProduction			= 'production'		# Busy filming.
	StatusPostproduction		= 'postproduction'	# Busy with post production phase.
	StatusCompleted				= 'completed'		# Completed with production, but not yet released.
	StatusReleased				= 'released'		# Released and in theaters. For movies.
	StatusPiloted				= 'piloted'			# First pilot episode released. For shows.
	StatusUpcoming				= 'upcoming'		# Upcoming release. For shows.
	StatusContinuing			= 'continuing'		# Continuing show on returning for a next season. For shows.
	StatusEnded					= 'ended'			# Ended with last episode. For shows.
	StatusCanceled				= 'canceled'		# Canceled without ending properley. For shows.
	StatusReturning				= 'returning'		# Internal. Not avilable on TVDb, but used by Trakt/TMDb.
	StatusFinished				= 'finished'		# Internal. Reserved for specials (S0) where it is assumed the season has ended (eg: since the show has ended), but there can be new specials added to S0 years after the show ended.
	StatusDefault				= Default

	# Serie Type

	SerieTypeStandard			= 'standard'		# A standard season or episode.
	SerieTypeSpecial			= 'special'			# A special season or episode.
	SerieTypePremiereShow		= 'premiereshow'	# A first season or episode of a show.
	SerieTypePremiereSeason		= 'premiereseason'	# A first episode of a season.
	SerieTypePremiereMiddle		= 'premieremiddle'	# A first episode in the middle of a season that is split into multiple parts.
	SerieTypePremiereFinale		= 'premierefinale'	# A first season of a show which is also the last season.
	SerieTypeFinaleShow			= 'finaleshow'		# A last season or episode of a show.
	SerieTypeFinaleSeason		= 'finaleseason'	# A last episode of a season.
	SerieTypeFinaleMiddle		= 'finalemiddle'	# A last episode in the middle of a season that is split into multiple parts.

	# Special
	# https://thetvdb.com/taxonomy

	SpecialImportant			= 'important'	# The special is important to the main story line (TVDb: 277).
	SpecialUnimportant			= 'unimportant'	# The special is not important to the main story line (TVDb: 278).
	SpecialProduction			= 'production'	# The special is a behind the scenes (TVDb: 4447).
	SpecialBlooper				= 'blooper'		# The special is bloopers (TVDb: 4448).
	SpecialInterview			= 'interview'	# The special is a cast interview (TVDb: 4449).
	SpecialCrossover			= 'crossover'	# The special is a crossover episode (TVDb: 4450). Update (2025-07): This category seems to have been removed
	SpecialDeleted				= 'deleted'		# The special is a deleted scenes (TVDb: 4458).
	SpecialMovie				= 'movie'		# The special is a full movie (TVDb: 4455).
	SpecialEpisode				= 'episode'		# The special is a full length episode not aired as part of a normal season (TVDb: 4460).
	SpecialExtended				= 'extended'	# The special is a extended scenes (TVDb: 4459).
	SpecialMaking				= 'making'		# The special is a making of (TVDb: 4451). Update (2025-07): This category seems to have been removed. Now merged with 4447 into "Behind the Scenes/ Makings Of".
	SpecialOriginal				= 'original'	# The special is not aired, but situational to the show. Original video animation (OVA) used mainly by anime (TVDb: 4452).
	SpecialPilot				= 'pilot'		# The special is a pilot episode (TVDb: 4453).
	SpecialRecap				= 'recap'		# The special is a season recap (TVDb: 4454).
	SpecialShort				= 'short'		# The special is a webisode or short (TVDb: 4456).
	SpecialPodcast				= 'podcast'		# The special is a podcast. Not an official special type, but some shows have a lot of podcasts (eg Last of Us S01).
	SpecialDefault				= Default

	SpecialStory				= {				# Part of the main storyline.
		SpecialImportant		: True,
		SpecialCrossover		: True,
		SpecialMovie			: True,
		SpecialEpisode			: True,
		SpecialOriginal			: True,
		SpecialPilot			: True,
	}
	SpecialExtra				= {				# Not part of the main storyline.
		SpecialUnimportant		: True,
		SpecialProduction		: True,
		SpecialBlooper			: True,
		SpecialInterview		: True,
		SpecialDeleted			: True,
		SpecialExtended			: True,
		SpecialMaking			: True,
		SpecialRecap			: True,
		SpecialShort			: True,
		SpecialPodcast			: True,
	}

	# Duration

	DurationSeconds				= 'seconds'
	DurationMinutes				= 'minutes'
	DurationHours				= 'hours'
	DurationDefault				= DurationSeconds

	# Day

	DayMonday					= 'monday'
	DayTuesday					= 'tuesday'
	DayWednesday				= 'wednesday'
	DayThursday					= 'thursday'
	DayFriday					= 'friday'
	DaySaturday					= 'saturday'
	DaySunday					= 'sunday'
	DayDefault					= Default

	# Zone

	ZoneOriginal				= 'original'
	ZoneLocal					= 'local'
	ZoneUtc						= 'utc'
	ZoneDefault					= Default

	# Format

	FormatDate					= ConverterTime.FormatDate
	FormatDateTime				= ConverterTime.FormatDateTimeShort
	FormatTime					= ConverterTime.FormatTimeShort
	FormatTimestamp				= ConverterTime.FormatTimestamp
	FormatComma					= ', '
	FormatSlash					= ' / '
	FormatBar					= ' | '
	FormatUniversal				= 'universal'
	FormatDefault				= True
	FormatNone					= Default

	# Data

	DataMedia					= {}
	DataProvider				= {}
	DataCharacterType			= {}
	DataCharacterRole			= {}
	DataCompany					= {}
	DataImageType				= {}
	DataImageQuality			= {}
	DataImageOpacity			= {}
	DataImageDecor				= {}
	DataGenre					= {}
	DataCountry					= {}
	DataDay						= {}
	DataStatus					= {}

	###################################################################
	# CONSTRUCTOR
	###################################################################

	def __init__(self, media = None, data = None):
		Serializer.__init__(self)

		self.mMedia = None
		self.mData = {}

		if not media and data and Tools.isDictionary(data): media = data.get('media')
		self.mediaSet(value = media)
		self.dataUpdate(data = data)

	###################################################################
	# DATA
	###################################################################

	def dataRetrieve(self, type = None, attribute = None, unique = False, sort = None, order = OrderDefault, extract = None, media = MediaDefault, flatten = SelectionSingle, selection = SelectionDefault, metadata = None):
		result = metadata or self.mData

		media = self.mediaDefault(media = media)
		if not media is False and not media is None and not media == self.media():
			try: result = result[media]
			except: return None

		# Match according to keys.
		if not type is None:
			if Tools.isArray(result):
				temp = []
				result = Tools.copy(result, deep = False) # Since the list is changed below.
				for i in range(len(result)):
					if Tools.isArray(type):
						found = True
						for j in type:
							try: result[i] = result[i][j]
							except:
								found = False
								break
						if not found: continue
						temp.append(result[i])
					else:
						try: temp.append(result[i][type])
						except: continue
				result = temp
			else:
				if Tools.isArray(type):
					for i in type:
						try: result = result[i]
						except: return None
				else:
					try: result = result[type]
					except: return None

		selection = self.selectionDefault(selection = selection)

		# Flatten nested dictionary containing lists at the lowest level. Eg: images.
		if Tools.isDictionary(result):
			# Finding a single item faster.
			if not attribute is None and selection is MetaData.SelectionSingle and not sort:
				result = self._dataRetrieveExtract(data = result, attribute = attribute)
			elif flatten is MetaData.SelectionList:
				temp = []
				self._dataRetrieveFlatten(data = result, result = temp)
				result = temp

		if Tools.isArray(result):
			# Match according to attributes.
			if not attribute is None:
				temp = []
				if selection is MetaData.SelectionSingle and not sort:
					for i in result:
						if self._dataRetrieveMatch(data = i, attribute = attribute):
							temp.append(i)
							break
				else:
					for i in result:
						if self._dataRetrieveMatch(data = i, attribute = attribute):
							temp.append(i)
				result = temp

			# Flatten list-of-lists.
			if flatten is MetaData.SelectionSingle or flatten is MetaData.SelectionList:
				if len(result) > 0 and Tools.isArray(result[0]):
					if MetaData.SelectionSingle: result = [i[0] for i in result if len(i) > 0]
					else: result = Tools.listFlatten(result)

			# Remove duplicate values.
			if unique: result = Tools.listUnique(result)

			# Sort according to attribute.
			if sort:
				keys = None
				if Tools.isArray(sort) and len(sort) > 0 and Tools.isArray(sort[0]):
					# Alternative sorting keys. Pick the first one available in the results.
					for i in sort:
						try:
							temp = result[0]
							for j in i: temp = temp[j]
							keys = i
							break
						except: pass
				else:
					keys = sort

				def _dataSortSingle(data, keys, order):
					return self._dataRetrieveValue(data = data, keys = keys)

				def _dataSortMulti(data, keys, order):
					values = []
					value = self._dataRetrieveValue(data = data, keys = keys)
					values.extend([-i for i in value[0]])
					if order == MetaData.OrderDescending: values.extend([-i for i in value[1]]) # Reversed
					else: values.extend(value[1])
					return values

				sortReverse = order == MetaData.OrderDescending
				sortFunction = _dataSortSingle

				if result:
					values = self._dataRetrieveValue(data = result[0], keys = keys)
					if Tools.isArray(values) and len(values) > 0 and Tools.isArray(values[0]):
						sortReverse = False # We do the ordering inside  the sort function.
						sortFunction = _dataSortMulti

					result.sort(key = lambda i : sortFunction(data = i, keys = keys, order = order), reverse = sortReverse)

			# Extract a specific attribute.
			if extract: result = [i[extract] for i in result]

		return self.dataSelect(data = result, selection = selection)

	@classmethod
	def _dataRetrieveMatch(self, data, attribute):
		if data is None: return False

		match = True
		for k, v in attribute.items():
			if k in data:
				if v is None:
					if not data[k] is v:
						match = False
						break
				elif Tools.isDictionary(v):
					if not self._dataRetrieveMatch(data = data[k], attribute = v):
						match = False
						break
				elif Tools.isList(v):
					if not data[k] in v:
						match = False
						break
				else:
					if not data[k] == v:
						match = False
						break
			else:
				match = False
				break
		return match

	@classmethod
	def _dataRetrieveExtract(self, data, attribute):
		for k, v in data.items():
			if Tools.isArray(v):
				for i in v:
					if self._dataRetrieveMatch(data = i, attribute = attribute):
						return i
			else:
				result = self._dataRetrieveExtract(data = v, attribute = attribute)
				if not result is None: return result
		return None

	@classmethod
	def _dataRetrieveFlatten(self, data, result):
		if Tools.isDictionary(data):
			for i in data.values():
				self._dataRetrieveFlatten(data = i, result = result)
		elif Tools.isArray(data):
			result.extend(data)

	@classmethod
	def _dataRetrieveValue(self, data, keys):
		try:
			value = Tools.dictionaryGet(dictionary = data, keys = keys)
			if value is None: return 0
			else: return value
		except: return 0

	def dataUpdate(self, data, media = False, unique = True, metadata = None):
		if data:
			if not media is False: data = self.mediaWrap(media = media, data = data)
			Tools.update(metadata if metadata else self.mData, data, none = False, lists = True, unique = unique)

	def dataSelect(self, data, selection = SelectionDefault):
		if Tools.isArray(data):
			if selection is MetaData.SelectionSingle:
				try: return data[0]
				except: return None
			elif Tools.isInteger(selection):
				try: return data[selection]
				except: return None
			elif Tools.isArray(selection):
				try: return data[selection[0] : selection[1]]
				except: return None
		return data

	def dataList(self, data):
		if not data is None and not Tools.isArray(data): data = [data]
		return data

	@classmethod
	def dataFix(self, media, data):
		# Sometimes there are exceptions thrown:
		#	data.py", line 920, in personKodi\n    characterName = i.name()\n', "AttributeError: 'dict' object has no attribute 'name'\n"
		# This happens with person, character, company, and possibly others.
		# Not sure why this happens.
		# Maybe when old metadata from the cache is used that has a different old/legacy structure?
		# Or maybe when the metadata object is serialized, and later unserialized, that only the parent dictionary is converted back to a Metadata object and not its internal child dictionaries (person, character, company).
		# In any case, we have a dirty fix here. Just convert to a MetaData object if a dictionary is detected.
		# NB: Use MetaData() and not self.dataCreate(), since the latter throws other errors.
		try:
			if not data: return data
			if Tools.isArray(data): data = [MetaData(media = media, data = i) if Tools.isDictionary(i) else i for i in data]
			elif Tools.isDictionary(data): data = MetaData(media = media, data = data)
		except: Logger.error()
		return data

	@classmethod
	def dataClean(self, data, newline = True, space = True):
		# TVDb character names sometimes contain space characters (eg: "Self \n  \n  \n  (archive footage)").
		if Tools.isDictionary(data):
			for key, value in data.items():
				for i in range(len(value)):
					value[i] = self.dataClean(data = value[i], newline = newline, space = space)
		else:
			# Use faster Python replacements.
			'''if newline:
				data = Regex.remove(data = data, expression = r'[\r\n]', all = True, cache = True)
			if space:
				data = Regex.remove(data = data, expression = r'\t', all = True, cache = True)
				data = Regex.replace(data = data, expression = r'\s{2,}', replacement = ' ', all = True, cache = True)'''
			if newline: data = data.replace('\r', '').replace('\n', '')
			if space: data = ' '.join(data.split())
		return data

	@classmethod
	def dataCreate(self, media, data):
		metadata = MetaData(media = media)
		metadata.dataImport(data = data)
		return metadata

	def dataExportBefore(self):
		items = {}
		for media in MetaData.MediaAll:
			try:
				item = self.mData[media]
				if item:
					items[media] = item
					if Tools.isArray(item): self.mData[media] = [i.dataExport() for i in item]
					else: self.mData[media] = item.dataExport()
			except: pass
		return items

	def dataExportAfter(self, data):
		for media, item in data.items():
			self.mData[media] = item

	def dataImportBefore(self, data = None):
		try:
			for media in MetaData.MediaAll:
				try:
					if media in data:
						item = data[media]
						if item:
							if Tools.isArray(item): data[media] = [self.dataCreate(media = media, data = i) for i in item]
							else: data[media] = self.dataCreate(media = media, data = item)
				except: Logger.error()
		except: Logger.error()
		return data

	def dataImportAfter(self, data = None):
		try: self.mediaSet(data['media'])
		except: pass

	###################################################################
	# SORT
	###################################################################

	@classmethod
	def sort(self, sort, media, type, decor):
		sort, order = self.sortSettings(sort = sort, media = media, type = type, decor = decor)
		if sort is MetaData.SortNone: return MetaData.Default, MetaData.Default
		return [['sort', sort]], order

	@classmethod
	def sortSettings(self, sort, media, type, decor):
		order = MetaData.OrderDefault
		if sort == MetaData.SortSettings:
			sort = MetaData.SortDefault
			if media in MetaData.MediaContent:
				type = self.imageTypeConvert(media = media, type = type, decor = decor)
				if type:
					sort = MetaImage.settingsStyleSort(media = media, type = type, default = True)
					if not sort: sort = MetaData.SortDefault
					order = MetaImage.settingsStyleOrder(media = media, type = type, default = True)
					if not order: order = MetaData.OrderDefault
		return sort, order

	@classmethod
	def sortDefault(self, value):
		return value if value else 0

	###################################################################
	# SELECTION
	###################################################################

	@classmethod
	def selectionDefault(self, selection, default = SelectionList):
		if selection is MetaData.SelectionDefault: selection = default
		return selection

	###################################################################
	# FALLBACK
	###################################################################

	@classmethod
	def fallbackDefault(self, fallback, default = FallbackDefault):
		if fallback is MetaData.FallbackDefault: fallback = MetaData.FallbackQuaternary if default is MetaData.FallbackDefault else default
		return fallback

	###################################################################
	# FORMAT
	###################################################################

	@classmethod
	def format(self, value, format = FormatDefault):
		if Tools.isArray(value) and format: value = format.join(value)
		return value

	###################################################################
	# PROVIDER
	###################################################################

	@classmethod
	def providerExtract(self, data):
		try: return MetaData.DataProvider[data]
		except: pass

		provider = MetaData.ProviderDefault
		if Regex.match(data = data, expression = r'(?:the[\s\-\_\.]*)?i(?:nternet[\s\-\_\.]*)?m(?:ovie[\s\-\_\.]*)?d(?:ata[\s\-\_\.]*)?b(?:ase)?', cache = True): provider = MetaData.ProviderImdb
		elif Regex.match(data = data, expression = r'(?:the[\s\-\_\.]*)?m(?:ovie[\s\-\_\.]*)?d(?:ata[\s\-\_\.]*)?b(?:ase)?', cache = True): provider = MetaData.ProviderTmdb
		elif Regex.match(data = data, expression = r'(?:the[\s\-\_\.]*)?tv[\s\-\_\.]*d(?:ata[\s\-\_\.]*)?b(?:ase)?', cache = True): provider = MetaData.ProviderTvdb
		elif Regex.match(data = data, expression = r'trakt', cache = True): provider = MetaData.ProviderTrakt
		elif Regex.match(data = data, expression = r'orion(?:[\s\-\_\.]*oid)?', cache = True): provider = MetaData.ProviderOrion

		MetaData.DataProvider[data] = provider
		return provider

	###################################################################
	# PERSON
	###################################################################

	def person(self, type = CharacterTypeDefault, role = CharacterRoleDefault, selection = SelectionDefault, detailed = False):
		result = self.dataRetrieve(type = 'person', selection = selection)
		if result is None:
			character = self.character(type = type, role = role, selection = selection)
			if character:
				character = self.dataFix(media = MetaData.MediaCharacter, data = character)
				if Tools.isArray(character):
					result = [i.person(selection = self.selectionDefault(selection = selection, default = MetaData.SelectionSingle)) for i in character]

					# Some actors play multiple roles (eg: Family Guy).
					# Filter out duplicate entries.
					characters = {}
					names = []
					temp = []
					if detailed:
						# The standard structure is that a character is the root object containing a person sub-object.
						# With "detailed", extract the person, and add all the characters as sub-objects.
						for i in range(len(result)):
							name = result[i].name()
							if not name in names:
								char = Tools.copy(character[i])
								try: del char.mData['person'] # Otherwise we have an infinite loop when exporting to JSON.
								except: pass
								characters[name] = [char]
								result[i].mData['character'] = characters[name]

								names.append(name)
								temp.append(result[i])
							else:
								char = Tools.copy(character[i])
								try: del char.mData['person']
								except: pass
								characters[name].append(char)
					else:
						for i in range(len(result)):
							name = result[i].name()
							if not name in names:
								names.append(name)
								temp.append(result[i])
					result = temp
				else:
					result = character.person(selection = self.selectionDefault(selection = selection, default = MetaData.SelectionSingle))
		return result

	def personActor(self, role = CharacterRoleDefault, selection = SelectionDefault, detailed = False):
		return self.person(type = MetaData.CharacterTypeActor, role = role, selection = selection, detailed = detailed)

	def personDirector(self, role = CharacterRoleDefault, selection = SelectionDefault, detailed = False):
		return self.person(type = MetaData.CharacterTypeDirector, role = role, selection = selection, detailed = detailed)

	def personWriter(self, role = CharacterRoleDefault, selection = SelectionDefault, detailed = False):
		return self.person(type = MetaData.CharacterTypeWriter, role = role, selection = selection, detailed = detailed)

	def personEditor(self, role = CharacterRoleDefault, selection = SelectionDefault, detailed = False):
		return self.person(type = MetaData.CharacterTypeEditor, role = role, selection = selection, detailed = detailed)

	def personCreator(self, role = CharacterRoleDefault, selection = SelectionDefault, detailed = False):
		return self.person(type = MetaData.CharacterTypeCreator, role = role, selection = selection, detailed = detailed)

	def personHost(self, role = CharacterRoleDefault, selection = SelectionDefault, detailed = False):
		return self.person(type = MetaData.CharacterTypeHost, role = role, selection = selection, detailed = detailed)

	def personCrew(self, role = CharacterRoleDefault, selection = SelectionDefault, detailed = False):
		return self.person(type = MetaData.CharacterTypeCrew, role = role, selection = selection, detailed = detailed)

	def personProducer(self, role = CharacterRoleDefault, selection = SelectionDefault, detailed = False):
		return self.person(type = MetaData.CharacterTypeProducer, role = role, selection = selection, detailed = detailed)

	def personGuest(self, role = CharacterRoleDefault, selection = SelectionDefault, detailed = False):
		return self.person(type = MetaData.CharacterTypeGuest, role = role, selection = selection, detailed = detailed)

	def personName(self, type = CharacterTypeDefault, role = CharacterRoleDefault, language = LanguageDefault, format = FormatNone, selection = SelectionDefault, fallback = FallbackDefault):
		person = self.person(type = type, role = role, selection = selection)
		if person:
			person = self.dataFix(media = MetaData.MediaPerson, data = person)
			if Tools.isArray(person):
				person = [i.name(language = language, selection = MetaData.SelectionSingle, fallback = fallback) for i in person]
				person = [i for i in person if i]
				return self.format(value = person, format = format)
			else:
				return person.name(language = language, selection = MetaData.SelectionSingle, fallback = fallback)
		return None

	def personNameActor(self, role = CharacterRoleDefault, language = LanguageDefault, format = FormatNone, selection = SelectionDefault, fallback = FallbackDefault):
		return self.personName(type = MetaData.CharacterTypeActor, role = role, language = language, format = format, selection = selection, fallback = fallback)

	def personNameDirector(self, role = CharacterRoleDefault, language = LanguageDefault, format = FormatNone, selection = SelectionDefault, fallback = FallbackDefault):
		return self.personName(type = MetaData.CharacterTypeDirector, role = role, language = language, format = format, selection = selection, fallback = fallback)

	def personNameWriter(self, role = CharacterRoleDefault, language = LanguageDefault, format = FormatNone, selection = SelectionDefault, fallback = FallbackDefault):
		return self.personName(type = MetaData.CharacterTypeWriter, role = role, language = language, format = format, selection = selection, fallback = fallback)

	def personNameEditor(self, role = CharacterRoleDefault, language = LanguageDefault, format = FormatNone, selection = SelectionDefault, fallback = FallbackDefault):
		return self.personName(type = MetaData.CharacterTypeEditor, role = role, language = language, format = format, selection = selection, fallback = fallback)

	def personNameCreator(self, role = CharacterRoleDefault, language = LanguageDefault, format = FormatNone, selection = SelectionDefault, fallback = FallbackDefault):
		return self.personName(type = MetaData.CharacterTypeCreator, role = role, language = language, format = format, selection = selection, fallback = fallback)

	def personNameHost(self, role = CharacterRoleDefault, language = LanguageDefault, format = FormatNone, selection = SelectionDefault, fallback = FallbackDefault):
		return self.personName(type = MetaData.CharacterTypeHost, role = role, language = language, format = format, selection = selection, fallback = fallback)

	def personNameCrew(self, role = CharacterRoleDefault, language = LanguageDefault, format = FormatNone, selection = SelectionDefault, fallback = FallbackDefault):
		return self.personName(type = MetaData.CharacterTypeCrew, role = role, language = language, format = format, selection = selection, fallback = fallback)

	def personNameProducer(self, role = CharacterRoleDefault, language = LanguageDefault, format = FormatNone, selection = SelectionDefault, fallback = FallbackDefault):
		return self.personName(type = MetaData.CharacterTypeProducer, role = role, language = language, format = format, selection = selection, fallback = fallback)

	def personNameGuest(self, role = CharacterRoleDefault, language = LanguageDefault, format = FormatNone, selection = SelectionDefault, fallback = FallbackDefault):
		return self.personName(type = MetaData.CharacterTypeGuest, role = role, language = language, format = format, selection = selection, fallback = fallback)

	def personKodi(self, type = CharacterTypeDefault, role = CharacterRoleDefault, selection = SelectionDefault, multiple = True):
		character = self.character(type = type, role = role, selection = selection)
		if character:
			character = self.dataFix(media = MetaData.MediaCharacter, data = character)

			multi = Tools.isArray(character)
			if not multi: character = [character]
			result = []

			for i in character:
				characterName = i.name()
				characterPhoto = i.image(type = MetaData.ImageTypePhoto, selection = MetaData.SelectionSingle)

				person = i.person()
				person = self.dataFix(media = MetaData.MediaPerson, data = person)
				if not person: continue
				personName = person.name()
				personPhoto = person.image(type = MetaData.ImageTypePhoto, selection = MetaData.SelectionSingle)

				# The same person can play by multiple roles.
				found = False
				for j in result:
					if personName and personName in j['person']['name']:
						found = True
						if characterName and not characterName in j['character']['name']: j['character']['name'].append(characterName)
						if characterPhoto and not characterPhoto in j['character']['photo']: j['character']['photo'].append(characterPhoto)
						if personName and not personName in j['person']['name']: j['person']['name'].append(personName)
						if personPhoto and not personPhoto in j['person']['photo']: j['person']['photo'].append(personPhoto)

				if not found:
					result.append({
						'character' : {'name' : [characterName] if characterName else [], 'photo' : [characterPhoto] if characterPhoto else []},
						'person' : {'name' : [personName] if personName else [], 'photo' : [personPhoto] if personPhoto else []},
					})

			kodi = []
			order = 0
			for i in result:
				name = i['person']['name'][0] if i['person']['name'] else None
				role = None if not i['character']['name'] else (' / ' .join(i['character']['name'])) if multiple else i['character']['name'][0]
				try: thumbnail = i['person']['photo'][0]
				except:
					try: thumbnail = i['character']['photo'][0]
					except: thumbnail = None
				kodi.append({'name' : name, 'role' : role, 'order' : order, 'thumbnail' : thumbnail})
				order += 1

			if multi: character = kodi
			else: character = kodi[0]
		return character

	# Includes actors and guest stars.
	def personKodiCast(self, selection = SelectionDefault, multiple = True):
		return self.personKodi(type = [MetaData.CharacterTypeActor, MetaData.CharacterTypeGuest], selection = selection, multiple = multiple)

	def personKodiActor(self, role = CharacterRoleDefault, selection = SelectionDefault, multiple = True):
		return self.personKodi(type = MetaData.CharacterTypeActor, role = role, selection = selection, multiple = multiple)

	def personKodiDirector(self, role = CharacterRoleDefault, selection = SelectionDefault, multiple = True):
		return self.personKodi(type = MetaData.CharacterTypeDirector, role = role, selection = selection, multiple = multiple)

	def personKodiWriter(self, role = CharacterRoleDefault, selection = SelectionDefault, multiple = True):
		return self.personKodi(type = MetaData.CharacterTypeWriter, role = role, selection = selection, multiple = multiple)

	def personKodiEditor(self, role = CharacterRoleDefault, selection = SelectionDefault, multiple = True):
		return self.personKodi(type = MetaData.CharacterTypeEditor, role = role, selection = selection, multiple = multiple)

	def personKodiCreator(self, role = CharacterRoleDefault, selection = SelectionDefault, multiple = True):
		return self.personKodi(type = MetaData.CharacterTypeCreator, role = role, selection = selection, multiple = multiple)

	def personKodiHost(self, role = CharacterRoleDefault, selection = SelectionDefault, multiple = True):
		return self.personKodi(type = MetaData.CharacterTypeHost, role = role, selection = selection, multiple = multiple)

	def personKodiCrew(self, role = CharacterRoleDefault, selection = SelectionDefault, multiple = True):
		return self.personKodi(type = MetaData.CharacterTypeCrew, role = role, selection = selection, multiple = multiple)

	def personKodiProducer(self, role = CharacterRoleDefault, selection = SelectionDefault, multiple = True):
		return self.personKodi(type = MetaData.CharacterTypeProducer, role = role, selection = selection, multiple = multiple)

	def personKodiGuest(self, role = CharacterRoleDefault, selection = SelectionDefault, multiple = True):
		return self.personKodi(type = MetaData.CharacterTypeGuest, role = role, selection = selection, multiple = multiple)

	def personSet(self, value):
		if value: self.dataUpdate(data = {'person' : value})

	###################################################################
	# CHARACTER
	###################################################################

	def character(self, type = CharacterTypeDefault, role = CharacterRoleDefault, selection = SelectionDefault):
		attribute = {}
		if type: attribute['type'] = type
		if role: attribute['role'] = role
		return self.dataRetrieve(type = 'character', attribute = attribute, sort = [['vote', MetaData.VotePercent], ['vote', MetaData.VoteAbsolute]], selection = selection)

	def characterActor(self, role = CharacterRoleDefault, selection = SelectionDefault):
		return self.character(type = MetaData.CharacterTypeActor, role = role, selection = selection)

	def characterDirector(self, role = CharacterRoleDefault, selection = SelectionDefault):
		return self.character(type = MetaData.CharacterTypeDirector, role = role, selection = selection)

	def characterWriter(self, role = CharacterRoleDefault, selection = SelectionDefault):
		return self.character(type = MetaData.CharacterTypeWriter, role = role, selection = selection)

	def characterEditor(self, role = CharacterRoleDefault, selection = SelectionDefault):
		return self.character(type = MetaData.CharacterTypeEditor, role = role, selection = selection)

	def characterCreator(self, role = CharacterRoleDefault, selection = SelectionDefault):
		return self.character(type = MetaData.CharacterTypeCreator, role = role, selection = selection)

	def characterHost(self, role = CharacterRoleDefault, selection = SelectionDefault):
		return self.character(type = MetaData.CharacterTypeHost, role = role, selection = selection)

	def characterCrew(self, role = CharacterRoleDefault, selection = SelectionDefault):
		return self.character(type = MetaData.CharacterTypeCrew, role = role, selection = selection)

	def characterProducer(self, role = CharacterRoleDefault, selection = SelectionDefault):
		return self.character(type = MetaData.CharacterTypeProducer, role = role, selection = selection)

	def characterGuest(self, role = CharacterRoleDefault, selection = SelectionDefault):
		return self.character(type = MetaData.CharacterTypeGuest, role = role, selection = selection)

	# This might not be the function you want, since it returns the character' photos.
	# For Kodi's ListItem.setCast(), the actor photo might be more suitable.
	# Have a look at personKodi().
	def characterKodi(self, type = CharacterTypeDefault, role = CharacterRoleDefault, selection = SelectionDefault, multiple = True):
		character = self.character(type = type, role = role, selection = selection)
		if character:
			character = self.dataFix(media = MetaData.MediaCharacter, data = character)

			multi = Tools.isArray(character)
			if not multi: character = [character]
			result = []

			for i in character:
				characterName = i.name()
				if not characterName: continue
				characterPhoto = i.image(type = MetaData.ImageTypePhoto, selection = MetaData.SelectionSingle)

				person = i.person()
				person = self.dataFix(media = MetaData.MediaPerson, data = person)
				personName = None
				personPhoto = None
				if person:
					personName = person.name()
					personPhoto = person.image(type = MetaData.ImageTypePhoto, selection = MetaData.SelectionSingle)

				# The same character can be played by multiple people (eg: old and young character).
				found = False
				for j in result:
					if characterName and characterName in j['character']['name']:
						found = True
						if characterName and not characterName in j['character']['name']: j['character']['name'].append(characterName)
						if characterPhoto and not characterPhoto in j['character']['photo']: j['character']['photo'].append(characterPhoto)
						if personName and not personName in j['person']['name']: j['person']['name'].append(personName)
						if personPhoto and not personPhoto in j['person']['photo']: j['person']['photo'].append(personPhoto)

				if not found:
					result.append({
						'character' : {'name' : [characterName] if characterName else [], 'photo' : [characterPhoto] if characterPhoto else []},
						'person' : {'name' : [personName] if personName else [], 'photo' : [personPhoto] if personPhoto else []},
					})

			kodi = []
			for i in result:
				name = None if not i['person']['name'] else (' / ' .join(i['person']['name'])) if multiple else i['person']['name'][0]
				role = i['character']['name'][0]
				try: thumbnail = i['character']['photo'][0]
				except:
					try: thumbnail = i['person']['photo'][0]
					except: thumbnail = None
				kodi.append({'name' : name, 'role' : role, 'thumbnail' : thumbnail})

			if multi: character = kodi
			else: character = kodi[0]
		return character

	# Includes actors and guest stars.
	def characterKodiCast(self, selection = SelectionDefault, multiple = True):
		return self.characterKodi(type = [MetaData.CharacterTypeActor, MetaData.CharacterTypeGuest], selection = selection, multiple = multiple)

	def characterKodiActor(self, role = CharacterRoleDefault, selection = SelectionDefault, multiple = True):
		return self.characterKodi(type = MetaData.CharacterTypeActor, role = role, selection = selection, multiple = multiple)

	def characterKodiDirector(self, role = CharacterRoleDefault, selection = SelectionDefault, multiple = True):
		return self.characterKodi(type = MetaData.CharacterTypeDirector, role = role, selection = selection, multiple = multiple)

	def characterKodiWriter(self, role = CharacterRoleDefault, selection = SelectionDefault, multiple = True):
		return self.characterKodi(type = MetaData.CharacterTypeWriter, role = role, selection = selection, multiple = multiple)

	def characterKodiEditor(self, role = CharacterRoleDefault, selection = SelectionDefault, multiple = True):
		return self.characterKodi(type = MetaData.CharacterTypeEditor, role = role, selection = selection, multiple = multiple)

	def characterKodiCreator(self, role = CharacterRoleDefault, selection = SelectionDefault, multiple = True):
		return self.characterKodi(type = MetaData.CharacterTypeCreator, role = role, selection = selection, multiple = multiple)

	def characterKodiHost(self, role = CharacterRoleDefault, selection = SelectionDefault, multiple = True):
		return self.characterKodi(type = MetaData.CharacterTypeHost, role = role, selection = selection, multiple = multiple)

	def characterKodiCrew(self, role = CharacterRoleDefault, selection = SelectionDefault, multiple = True):
		return self.characterKodi(type = MetaData.CharacterTypeCrew, role = role, selection = selection, multiple = multiple)

	def characterKodiProducer(self, role = CharacterRoleDefault, selection = SelectionDefault, multiple = True):
		return self.characterKodi(type = MetaData.CharacterTypeProducer, role = role, selection = selection, multiple = multiple)

	def characterKodiGuest(self, role = CharacterRoleDefault, selection = SelectionDefault, multiple = True):
		return self.characterKodi(type = MetaData.CharacterTypeGuest, role = role, selection = selection, multiple = multiple)

	def characterSet(self, value):
		if value:
			if self.mediaCharacter(): self.dataUpdate(data = value)
			else: self.dataUpdate(data = {'character' : self.dataList(value)})

	@classmethod
	def characterExtract(self, data):
		type = self.characterTypeExtract(data)
		if not type: return None
		return {
			'type' : type,
			'role' : self.characterRoleExtract(data),
		}

	@classmethod
	def characterTypeExtract(self, data):
		try: return MetaData.DataCharacterType[data]
		except: pass

		character = MetaData.CharacterTypeDefault
		if Regex.match(data = data, expression = r'(?:actor)', cache = True): character = MetaData.CharacterTypeActor
		elif Regex.match(data = data, expression = r'(?:director)', cache = True): character = MetaData.CharacterTypeDirector
		elif Regex.match(data = data, expression = r'(?:writer)', cache = True): character = MetaData.CharacterTypeWriter
		elif Regex.match(data = data, expression = r'(?:editor)', cache = True): character = MetaData.CharacterTypeEditor
		elif Regex.match(data = data, expression = r'(?:creator)', cache = True): character = MetaData.CharacterTypeCreator
		elif Regex.match(data = data, expression = r'(?:host)', cache = True): character = MetaData.CharacterTypeHost
		elif Regex.match(data = data, expression = r'(?:crew)', cache = True): character = MetaData.CharacterTypeCrew
		elif Regex.match(data = data, expression = r'(?:producer|show.*runner)', cache = True): character = MetaData.CharacterTypeProducer
		elif Regex.match(data = data, expression = r'(?:guest)', cache = True): character = MetaData.CharacterTypeGuest

		MetaData.DataCharacterType[data] = character
		return character

	@classmethod
	def characterRoleExtract(self, data):
		try: return MetaData.DataCharacterRole[data]
		except: pass

		character = MetaData.CharacterTypeDefault
		if Regex.match(data = data, expression = r'(?:show.*runner)', cache = True): character = MetaData.CharacterRoleRunner
		elif Regex.match(data = data, expression = r'(?:executive)', cache = True): character = MetaData.CharacterRoleExecutive
		elif Regex.match(data = data, expression = r'(?:associat(?:e|ive))', cache = True): character = MetaData.CharacterRoleAssociate
		elif Regex.match(data = data, expression = r'(?:co[\s\-]*producer)', cache = True): character = MetaData.CharacterRoleCo
		elif Regex.match(data = data, expression = r'(?:line)', cache = True): character = MetaData.CharacterRoleLine
		elif Regex.match(data = data, expression = r'(?:coordinate)', cache = True): character = MetaData.CharacterRoleCoordinate
		elif Regex.match(data = data, expression = r'(?:supervise)', cache = True): character = MetaData.CharacterRoleSupervise
		elif Regex.match(data = data, expression = r'(?:consult)', cache = True): character = MetaData.CharacterRoleConsult
		elif Regex.match(data = data, expression = r'(?:segment)', cache = True): character = MetaData.CharacterRoleSegment
		elif Regex.match(data = data, expression = r'(?:field)', cache = True): character = MetaData.CharacterRoleField
		elif Regex.match(data = data, expression = r'(?:star)', cache = True): character = MetaData.CharacterRoleStar
		elif Regex.match(data = data, expression = r'(?:music)', cache = True): character = MetaData.CharacterRoleMusical

		MetaData.DataCharacterRole[data] = character
		return character

	###################################################################
	# COMPANY
	###################################################################

	def company(self, type = CompanyTypeDefault, selection = SelectionDefault):
		attribute = {}
		if type: attribute['type'] = type
		return self.dataRetrieve(type = 'company', attribute = attribute, selection = selection)

	def companyNetwork(self, selection = SelectionDefault):
		return self.company(type = MetaData.CompanyTypeNetwork, selection = selection)

	def companyStudio(self, selection = SelectionDefault):
		return self.company(type = MetaData.CompanyTypeStudio, selection = selection)

	def companyProducer(self, selection = SelectionDefault):
		return self.company(type = MetaData.CompanyTypeProducer, selection = selection)

	def companyDistributor(self, selection = SelectionDefault):
		return self.company(type = MetaData.CompanyTypeDistributor, selection = selection)

	def companyEffects(self, selection = SelectionDefault):
		return self.company(type = MetaData.CompanyTypeEffects, selection = selection)

	def companyName(self, type = CompanyTypeDefault, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		company = self.company(type = type, selection = selection)
		if company:
			company = self.dataFix(media = MetaData.MediaCompany, data = company)
			if Tools.isArray(company):
				company = [i.name(language = language, selection = MetaData.SelectionSingle, fallback = fallback) for i in company]
				return [i for i in company if i]
			else:
				return company.name(language = language, selection = MetaData.SelectionSingle, fallback = fallback)
		return None

	def companyNameNetwork(self, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.companyName(type = MetaData.CompanyTypeNetwork, language = language, selection = selection, fallback = fallback)

	def companyNameStudio(self, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.companyName(type = MetaData.CompanyTypeStudio, language = language, selection = selection, fallback = fallback)

	def companyNameProducer(self, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.companyName(type = MetaData.CompanyTypeProducer, language = language, selection = selection, fallback = fallback)

	def companyNameDistributor(self, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.companyName(type = MetaData.CompanyTypeDistributor, language = language, selection = selection, fallback = fallback)

	def companyNameEffects(self, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.companyName(type = MetaData.CompanyTypeEffects, language = language, selection = selection, fallback = fallback)

	def companySet(self, value):
		if value: self.dataUpdate(data = {'company' : self.dataList(value)})

	@classmethod
	def companyExtract(self, data):
		try: return MetaData.DataCompany[data]
		except: pass

		company = MetaData.CompanyTypeDefault
		if Regex.match(data = data, expression = r'(?:network)', cache = True): company = MetaData.CompanyTypeNetwork
		elif Regex.match(data = data, expression = r'(?:studio)', cache = True): company = MetaData.CompanyTypeStudio
		elif Regex.match(data = data, expression = r'(?:produc(?:tion|er))', cache = True): company = MetaData.CompanyTypeProducer
		elif Regex.match(data = data, expression = r'(?:distribut(?:tion|or))', cache = True): company = MetaData.CompanyTypeDistributor
		elif Regex.match(data = data, expression = r'(?:effect)', cache = True): company = MetaData.CompanyTypeEffects

		MetaData.DataCompany[data] = company
		return company

	###################################################################
	# GENERAL
	###################################################################

	def item(self, media, attribute = Default, sort = Default, selection = SelectionDefault):
		return self.dataRetrieve(type = media, attribute = attribute, sort = ['number', MetaData.NumberStandard] if sort is True else sort, order = MetaData.OrderAscending, selection = selection)

	def movie(self, attribute = Default, selection = SelectionDefault):
		return self.item(media = MetaData.MediaMovie, attribute = attribute, selection = selection)

	def collection(self, attribute = Default, selection = SelectionDefault):
		return self.item(media = MetaData.MediaCollection, attribute = attribute, selection = selection)

	def show(self, attribute = Default, selection = SelectionDefault):
		return self.item(media = MetaData.MediaShow, attribute = attribute, selection = selection)

	def season(self, number = Default, numberSeason = Default, exclude = Default, excludeSeason = Default, attribute = Default, sort = Default, selection = SelectionDefault):
		if excludeSeason is MetaData.Default: excludeSeason = exclude
		if not excludeSeason is MetaData.Default and not Tools.isArray(excludeSeason): excludeSeason = [excludeSeason]

		if numberSeason is MetaData.Default: numberSeason = number
		if not numberSeason is MetaData.Default and not Tools.isArray(numberSeason): numberSeason = [numberSeason]

		if selection is MetaData.SelectionDefault and numberSeason and len(numberSeason) == 1: selection = MetaData.SelectionSingle

		result = self.item(media = MetaData.MediaSeason, attribute = attribute, sort = sort)

		if result:
			if not numberSeason is MetaData.Default: result = [i for i in result if i.numberSeason() in numberSeason]
			if not excludeSeason is MetaData.Default: result = [i for i in result if not i.numberSeason() in excludeSeason]

		return self.dataSelect(data = result, selection = selection)

	def episode(self, number = Default, numberSeason = Default, numberEpisode = Default, exclude = Default, excludeSeason = Default, excludeEpisode = Default, attribute = Default, sort = Default, selection = SelectionDefault):
		if excludeSeason is MetaData.Default: excludeSeason = exclude
		if excludeEpisode is MetaData.Default: excludeEpisode = exclude
		if not excludeSeason is MetaData.Default and not Tools.isArray(excludeSeason): excludeSeason = [excludeSeason]
		if not excludeEpisode is MetaData.Default and not Tools.isArray(excludeEpisode): excludeEpisode = [excludeEpisode]

		if numberEpisode is MetaData.Default: numberEpisode = number
		if not numberSeason is MetaData.Default and not Tools.isArray(numberSeason): numberSeason = [numberSeason]
		if not numberEpisode is MetaData.Default and not Tools.isArray(numberEpisode): numberEpisode = [numberEpisode]

		if selection is MetaData.SelectionDefault and numberSeason and len(numberSeason) == 1 and numberEpisode and len(numberEpisode) == 1: selection = MetaData.SelectionSingle

		if self.mediaShow():
			season = self.season(number = numberSeason, excludeSeason = excludeSeason, attribute = attribute, sort = sort, selection = MetaData.SelectionList)
			if season:
				if season and not Tools.isList(season): season = [season] # If an individual season is set to the show when retrieving from episodes.py.
				result = []
				for i in season:
					if i: # Sometimes None.
						episode = i.episode(number = numberEpisode, excludeEpisode = excludeEpisode, attribute = attribute, sort = sort)
						if episode: result.extend(episode)
				return self.dataSelect(data = result, selection = selection)
			else: return None

		result = self.item(media = MetaData.MediaEpisode, attribute = attribute, sort = sort)

		if result:
			if not numberSeason is MetaData.Default: result = [i for i in result if i.numberSeason() in numberSeason]
			if not numberEpisode is MetaData.Default: result = [i for i in result if i.numberEpisode() in numberEpisode]

			if not excludeSeason is MetaData.Default: result = [i for i in result if not i.numberSeason() in excludeSeason]
			if not excludeEpisode is MetaData.Default: result = [i for i in result if not i.numberEpisode() in excludeEpisode]

		return self.dataSelect(data = result, selection = selection)

	def itemSet(self, value, unique = Default, media = MediaDefault):
		if value:
			if media is MetaData.MediaDefault:
				try: media = value.media()
				except:
					try: media = value[0].media()
					except: pass
			if media:
				if unique and unique in MetaData.Providers: unique = ['id', unique]
				self.dataUpdate(data = {media : value}, unique = unique)

	def movieSet(self, value, unique = Default):
		self.itemSet(value = value, unique = unique, media = MetaData.MediaMovie)

	def collectionSet(self, value, unique = Default):
		self.itemSet(value = value, unique = unique, media = MetaData.MediaCollection)

	def showSet(self, value, unique = Default):
		self.itemSet(value = value, unique = unique, media = MetaData.MediaShow)

	def seasonSet(self, value, unique = Default):
		self.itemSet(value = value, unique = unique, media = MetaData.MediaSeason)

	def episodeSet(self, value, unique = Default):
		if self.mediaShow():
			if not Tools.isArray(value): value = [value]
			for i in value:
				found = False
				number = i.numberSeason()
				if not number is None:
					season = self.season(number = number, selection = MetaData.SelectionSingle)
					if not season:
						season = i.season(selection = MetaData.SelectionSingle)
						if season: self.seasonSet(season)
					if season:
						found = True
						season.episodeSet(value = self.dataList(i), unique = unique)
				if not found: Logger.log('MetaData: Season not found')
		else:
			self.itemSet(value = value, unique = unique, media = MetaData.MediaEpisode)

	###################################################################
	# MEDIA
	###################################################################

	def media(self):
		# This function is called very often, including from every dataRetrieve() call.
		# Use a separate variable to improve access speed.
		#return self.dataRetrieve(type = 'media', media = False)
		return self.mMedia

	def mediaContent(self, media = MediaDefault):
		return self.mediaDefault(media = media) in MetaData.MediaContent

	def mediaFilm(self, media = MediaDefault):
		return self.mediaDefault(media = media) in MetaData.MediaFilm

	def mediaTelevision(self, media = MediaDefault):
		return self.mediaDefault(media = media) in MetaData.MediaTelevision

	def mediaEntity(self, media = MediaDefault):
		return self.mediaDefault(media = media) in MetaData.MediaEntity

	def mediaIndividual(self, media = MediaDefault):
		return self.mediaDefault(media = media) in MetaData.MediaIndividual

	def mediaMovie(self):
		return self.media() == MetaData.MediaMovie

	def mediaCollection(self):
		return self.media() == MetaData.MediaCollection

	def mediaShow(self):
		return self.media() == MetaData.MediaShow

	def mediaSeason(self):
		return self.media() == MetaData.MediaSeason

	def mediaEpisode(self):
		return self.media() == MetaData.MediaEpisode

	def mediaPerson(self):
		return self.media() == MetaData.MediaPerson

	def mediaCharacter(self):
		return self.media() == MetaData.MediaCharacter

	def mediaCompany(self):
		return self.media() == MetaData.MediaCompany

	def mediaSet(self, value):
		self.mMedia = value
		self.mData['media'] = value

	def mediaDefault(self, media):
		if media is MetaData.MediaDefault: media = self.media()
		return media

	def mediaWrap(self, media, data):
		media = self.mediaDefault(media = media)
		if not media == self.media(): data = {media : data}
		return data

	@classmethod
	def mediaExtract(self, data):
		if not Tools.isString(data): return None

		try: return MetaData.DataMedia[data]
		except: pass

		media = MetaData.MediaDefault
		if Regex.match(data = data, expression = r'(?:movie|film)', cache = True): media = MetaData.MediaMovie
		elif Regex.match(data = data, expression = r'(?:season)', cache = True): media = MetaData.MediaSeason
		elif Regex.match(data = data, expression = r'(?:ep(?:isode)?|part)', cache = True): media = MetaData.MediaEpisode
		elif Regex.match(data = data, expression = r'(?:show|serie)', cache = True): media = MetaData.MediaShow
		elif Regex.match(data = data, expression = r'(?:collection|box|set)', cache = True): media = MetaData.MediaCollection
		elif Regex.match(data = data, expression = r'(?:person|people)', cache = True): media = MetaData.MediaPerson
		elif Regex.match(data = data, expression = r'(?:character|actor|director|writer|producer|creator|crew|star|host|guest|showrunner)', cache = True): media = MetaData.MediaCharacter
		elif Regex.match(data = data, expression = r'(?:company|network|studio|distribut(?:or|ion)|production|special.*effects)', cache = True): media = MetaData.MediaCompany

		MetaData.DataMedia[data] = media
		return media

	###################################################################
	# ID
	###################################################################

	def id(self, provider = ProviderDefault, media = MediaDefault):
		type = ['id']
		if provider: type.append(provider)
		return self.dataRetrieve(type = type, media = media)

	def idOrion(self, media = MediaDefault):
		return self.id(provider = MetaData.ProviderOrion, media = media)

	def idImdb(self, media = MediaDefault):
		return self.id(provider = MetaData.ProviderImdb, media = media)

	def idTmdb(self, media = MediaDefault):
		return self.id(provider = MetaData.ProviderTmdb, media = media)

	def idTvdb(self, media = MediaDefault):
		return self.id(provider = MetaData.ProviderTvdb, media = media)

	def idTrakt(self, media = MediaDefault):
		return self.id(provider = MetaData.ProviderTrakt, media = media)

	def idSet(self, value, provider = ProviderDefault, media = MediaDefault):
		if value:
			if Tools.isDictionary(value): value = {k : str(v) for k, v in value.items()}
			else: value = {provider : str(value)}
			self.dataUpdate(data = {'id' : value}, media = media)

	def idOrionSet(self, value, media = MediaDefault):
		self.idSet(value = value, provider = MetaData.ProviderOrion, media = media)

	def idImdbSet(self, value, media = MediaDefault):
		self.idSet(value = value, provider = MetaData.ProviderImdb, media = media)

	def idTmdbSet(self, value, media = MediaDefault):
		self.idSet(value = value, provider = MetaData.ProviderTmdb, media = media)

	def idTvdbSet(self, value, media = MediaDefault):
		self.idSet(value = value, provider = MetaData.ProviderTvdb, media = media)

	def idTraktSet(self, value, media = MediaDefault):
		self.idSet(value = value, provider = MetaData.ProviderTrakt, media = media)

	###################################################################
	# ID - MOVIE
	###################################################################

	def idMovie(self, provider):
		return self.id(provider = provider, media = MetaData.MediaMovie)

	def idMovieOrion(self):
		return self.idMovie(provider = MetaData.ProviderOrion)

	def idMovieImdb(self):
		return self.idMovie(provider = MetaData.ProviderImdb)

	def idMovieTmdb(self):
		return self.idMovie(provider = MetaData.ProviderTmdb)

	def idMovieTvdb(self):
		return self.idMovie(provider = MetaData.ProviderTvdb)

	def idMovieTrakt(self):
		return self.idMovie(provider = MetaData.ProviderTrakt)

	def idMovieSet(self, value, provider):
		self.idSet(value = value, provider = provider, media = MetaData.MediaMovie)

	def idMovieOrionSet(self, value):
		self.idMovieSet(value = value, provider = MetaData.ProviderOrion)

	def idMovieImdbSet(self, value):
		self.idMovieSet(value = value, provider = MetaData.ProviderImdb)

	def idMovieTmdbSet(self, value):
		self.idMovieSet(value = value, provider = MetaData.ProviderTmdb)

	def idMovieTvdbSet(self, value):
		self.idMovieSet(value = value, provider = MetaData.ProviderTvdb)

	def idMovieTraktSet(self, value):
		self.idMovieSet(value = value, provider = MetaData.ProviderTrakt)

	###################################################################
	# ID - COLLECTION
	###################################################################

	def idCollection(self, provider):
		return self.id(provider = provider, media = MetaData.MediaCollection)

	def idCollectionOrion(self):
		return self.idCollection(provider = MetaData.ProviderOrion)

	def idCollectionImdb(self):
		return self.idCollection(provider = MetaData.ProviderImdb)

	def idCollectionTmdb(self):
		return self.idCollection(provider = MetaData.ProviderTmdb)

	def idCollectionTvdb(self):
		return self.idCollection(provider = MetaData.ProviderTvdb)

	def idCollectionTrakt(self):
		return self.idCollection(provider = MetaData.ProviderTrakt)

	def idCollectionSet(self, value, provider):
		self.idSet(value = value, provider = provider, media = MetaData.MediaCollection)

	def idCollectionOrionSet(self, value):
		self.idCollectionSet(value = value, provider = MetaData.ProviderOrion)

	def idCollectionImdbSet(self, value):
		self.idCollectionSet(value = value, provider = MetaData.ProviderImdb)

	def idCollectionTmdbSet(self, value):
		self.idCollectionSet(value = value, provider = MetaData.ProviderTmdb)

	def idCollectionTvdbSet(self, value):
		self.idCollectionSet(value = value, provider = MetaData.ProviderTvdb)

	def idCollectionTraktSet(self, value):
		self.idCollectionSet(value = value, provider = MetaData.ProviderTrakt)

	###################################################################
	# ID - SHOW
	###################################################################

	def idShow(self, provider):
		return self.id(provider = provider, media = MetaData.MediaShow)

	def idShowOrion(self):
		return self.idShow(provider = MetaData.ProviderOrion)

	def idShowImdb(self):
		return self.idShow(provider = MetaData.ProviderImdb)

	def idShowTmdb(self):
		return self.idShow(provider = MetaData.ProviderTmdb)

	def idShowTvdb(self):
		return self.idShow(provider = MetaData.ProviderTvdb)

	def idShowTrakt(self):
		return self.idShow(provider = MetaData.ProviderTrakt)

	def idShowSet(self, value, provider):
		self.idSet(value = value, provider = provider, media = MetaData.MediaShow)

	def idShowOrionSet(self, value):
		self.idShowSet(value = value, provider = MetaData.ProviderOrion)

	def idShowImdbSet(self, value):
		self.idShowSet(value = value, provider = MetaData.ProviderImdb)

	def idShowTmdbSet(self, value):
		self.idShowSet(value = value, provider = MetaData.ProviderTmdb)

	def idShowTvdbSet(self, value):
		self.idShowSet(value = value, provider = MetaData.ProviderTvdb)

	def idShowTraktSet(self, value):
		self.idShowSet(value = value, provider = MetaData.ProviderTrakt)

	###################################################################
	# ID - SEASON
	###################################################################

	def idSeason(self, provider):
		return self.id(provider = provider, media = MetaData.MediaSeason)

	def idSeasonOrion(self):
		return self.idSeason(provider = MetaData.ProviderOrion)

	def idSeasonImdb(self):
		return self.idSeason(provider = MetaData.ProviderImdb)

	def idSeasonTmdb(self):
		return self.idSeason(provider = MetaData.ProviderTmdb)

	def idSeasonTvdb(self):
		return self.idSeason(provider = MetaData.ProviderTvdb)

	def idSeasonTrakt(self):
		return self.idSeason(provider = MetaData.ProviderTrakt)

	def idSeasonSet(self, value, provider):
		self.idSet(value = value, provider = provider, media = MetaData.MediaSeason)

	def idSeasonOrionSet(self, value):
		self.idSeasonSet(value = value, provider = MetaData.ProviderOrion)

	def idSeasonImdbSet(self, value):
		self.idSeasonSet(value = value, provider = MetaData.ProviderImdb)

	def idSeasonTmdbSet(self, value):
		self.idSeasonSet(value = value, provider = MetaData.ProviderTmdb)

	def idSeasonTvdbSet(self, value):
		self.idSeasonSet(value = value, provider = MetaData.ProviderTvdb)

	def idSeasonTraktSet(self, value):
		self.idSeasonSet(value = value, provider = MetaData.ProviderTrakt)

	###################################################################
	# ID - EPISODE
	###################################################################

	def idEpisode(self, provider):
		return self.id(provider = provider, media = MetaData.MediaEpisode)

	def idEpisodeOrion(self):
		return self.idEpisode(provider = MetaData.ProviderOrion)

	def idEpisodeImdb(self):
		return self.idEpisode(provider = MetaData.ProviderImdb)

	def idEpisodeTmdb(self):
		return self.idEpisode(provider = MetaData.ProviderTmdb)

	def idEpisodeTvdb(self):
		return self.idEpisode(provider = MetaData.ProviderTvdb)

	def idEpisodeTrakt(self):
		return self.idEpisode(provider = MetaData.ProviderTrakt)

	def idEpisodeSet(self, value, provider):
		self.idSet(value = value, provider = provider, media = MetaData.MediaEpisode)

	def idEpisodeOrionSet(self, value):
		self.idEpisodeSet(value = value, provider = MetaData.ProviderOrion)

	def idEpisodeImdbSet(self, value):
		self.idEpisodeSet(value = value, provider = MetaData.ProviderImdb)

	def idEpisodeTmdbSet(self, value):
		self.idEpisodeSet(value = value, provider = MetaData.ProviderTmdb)

	def idEpisodeTvdbSet(self, value):
		self.idEpisodeSet(value = value, provider = MetaData.ProviderTvdb)

	def idEpisodeTraktSet(self, value):
		self.idEpisodeSet(value = value, provider = MetaData.ProviderTrakt)

	###################################################################
	# ID - PERSON
	###################################################################

	def idPerson(self, provider):
		return self.id(provider = provider, media = MetaData.MediaPerson)

	def idPersonOrion(self):
		return self.idPerson(provider = MetaData.ProviderOrion)

	def idPersonImdb(self):
		return self.idPerson(provider = MetaData.ProviderImdb)

	def idPersonTmdb(self):
		return self.idPerson(provider = MetaData.ProviderTmdb)

	def idPersonTvdb(self):
		return self.idPerson(provider = MetaData.ProviderTvdb)

	def idPersonTrakt(self):
		return self.idPerson(provider = MetaData.ProviderTrakt)

	def idPersonSet(self, value, provider):
		self.idSet(value = value, provider = provider, media = MetaData.MediaPerson)

	def idPersonOrionSet(self, value):
		self.idPersonSet(value = value, provider = MetaData.ProviderOrion)

	def idPersonImdbSet(self, value):
		self.idPersonSet(value = value, provider = MetaData.ProviderImdb)

	def idPersonTmdbSet(self, value):
		self.idPersonSet(value = value, provider = MetaData.ProviderTmdb)

	def idPersonTvdbSet(self, value):
		self.idPersonSet(value = value, provider = MetaData.ProviderTvdb)

	def idPersonTraktSet(self, value):
		self.idPersonSet(value = value, provider = MetaData.ProviderTrakt)

	###################################################################
	# ID - CHARACTER
	###################################################################

	def idCharacter(self, provider):
		return self.id(provider = provider, media = MetaData.MediaCharacter)

	def idCharacterOrion(self):
		return self.idCharacter(provider = MetaData.ProviderOrion)

	def idCharacterImdb(self):
		return self.idCharacter(provider = MetaData.ProviderImdb)

	def idCharacterTmdb(self):
		return self.idCharacter(provider = MetaData.ProviderTmdb)

	def idCharacterTvdb(self):
		return self.idCharacter(provider = MetaData.ProviderTvdb)

	def idCharacterTrakt(self):
		return self.idCharacter(provider = MetaData.ProviderTrakt)

	def idCharacterSet(self, value, provider):
		self.idSet(value = value, provider = provider, media = MetaData.MediaCharacter)

	def idCharacterOrionSet(self, value):
		self.idCharacterSet(value = value, provider = MetaData.ProviderOrion)

	def idCharacterImdbSet(self, value):
		self.idCharacterSet(value = value, provider = MetaData.ProviderImdb)

	def idCharacterTmdbSet(self, value):
		self.idCharacterSet(value = value, provider = MetaData.ProviderTmdb)

	def idCharacterTvdbSet(self, value):
		self.idCharacterSet(value = value, provider = MetaData.ProviderTvdb)

	def idCharacterTraktSet(self, value):
		self.idCharacterSet(value = value, provider = MetaData.ProviderTrakt)

	###################################################################
	# ID - COMPANY
	###################################################################

	def idCompany(self, provider):
		return self.id(provider = provider, media = MetaData.MediaCompany)

	def idCompanyOrion(self):
		return self.idCompany(provider = MetaData.ProviderOrion)

	def idCompanyImdb(self):
		return self.idCompany(provider = MetaData.ProviderImdb)

	def idCompanyTmdb(self):
		return self.idCompany(provider = MetaData.ProviderTmdb)

	def idCompanyTvdb(self):
		return self.idCompany(provider = MetaData.ProviderTvdb)

	def idCompanyTrakt(self):
		return self.idCompany(provider = MetaData.ProviderTrakt)

	def idCompanySet(self, value, provider):
		self.idSet(value = value, provider = provider, media = MetaData.MediaCompany)

	def idCompanyOrionSet(self, value):
		self.idCompanySet(value = value, provider = MetaData.ProviderOrion)

	def idCompanyImdbSet(self, value):
		self.idCompanySet(value = value, provider = MetaData.ProviderImdb)

	def idCompanyTmdbSet(self, value):
		self.idCompanySet(value = value, provider = MetaData.ProviderTmdb)

	def idCompanyTvdbSet(self, value):
		self.idCompanySet(value = value, provider = MetaData.ProviderTvdb)

	def idCompanyTraktSet(self, value):
		self.idCompanySet(value = value, provider = MetaData.ProviderTrakt)

	###################################################################
	# TYPE
	###################################################################

	def type(self, media = MediaDefault, selection = SelectionDefault):
		return self.dataRetrieve(type = 'type', media = media, unique = True, selection = selection)

	def typeCharacter(self, selection = SelectionDefault):
		return self.type(media = MetaData.MediaCharacter if self.mediaPerson() else MetaData.MediaDefault, selection = selection)

	def typeCompany(self, selection = SelectionDefault):
		return self.type(media = MetaData.MediaCompany, selection = selection)

	def typeSeason(self, selection = SelectionDefault):
		return self.type(media = MetaData.MediaSeason, selection = selection)

	def typeEpisode(self, selection = SelectionDefault):
		return self.type(media = MetaData.MediaEpisode, selection = selection)

	def typeSet(self, value, media = MediaDefault):
		if value: self.dataUpdate(data = {'type' : value}, media = media)

	###################################################################
	# ROLE
	###################################################################

	def role(self, media = MediaDefault, selection = SelectionDefault):
		return self.dataRetrieve(type = 'role', media = media, unique = True, selection = selection)

	def roleCharacter(self, selection = SelectionDefault):
		return self.role(media = MetaData.MediaCharacter if self.mediaPerson() else MetaData.MediaDefault, selection = selection)

	def roleSet(self, value, media = MediaDefault):
		if value: self.dataUpdate(data = {'role' : value}, media = media)

	###################################################################
	# SLUG
	###################################################################

	def slug(self, media = MediaDefault):
		return self.dataRetrieve(type = 'slug', media = media)

	def slugMovie(self):
		return self.slug(media = MetaData.MediaMovie)

	def slugCollection(self):
		return self.slug(media = MetaData.MediaCollection)

	def slugShow(self):
		return self.slug( media = MetaData.MediaShow)

	def slugSeason(self):
		return self.slug(media = MetaData.MediaSeason)

	def slugEpisode(self):
		return self.slug(media = MetaData.MediaEpisode)

	def slugSet(self, value, media = MediaDefault):
		if value: self.dataUpdate(data = {'slug' : value}, media = media)

	def slugMovieSet(self, value):
		self.slugSet(value = value, media = MetaData.MediaMovie)

	def slugCollectionSet(self, value):
		self.slugSet(value = value, media = MetaData.MediaCollection)

	def slugShowSet(self, value):
		self.slugSet(value = value, media = MetaData.MediaShow)

	def slugSeasonSet(self, value):
		self.slugSet(value = value, media = MetaData.MediaSeason)

	def slugEpisodeSet(self, value):
		self.slugSet(value = value, media = MetaData.MediaEpisode)

	###################################################################
	# NUMBER
	###################################################################

	def number(self, number = NumberDefault, format = Default, media = MediaDefault):
		if format and media is MetaData.MediaDefault and self.mediaEpisode():
			numberSeason = self.numberSeason()
			numberEpisode = self.numberEpisode()
			try:
				if format == MetaData.FormatUniversal: return Title.numberUniversal(season = numberSeason, episode = numberEpisode)
				else: return format % (numberSeason, numberEpisode)
			except:
				result = Title.number(season = numberSeason, episode = numberEpisode)
				if not result: result = Title.numberUniversal(season = numberSeason, episode = numberEpisode) # Format selected that requires the title.
				return result
		elif number is MetaData.Default:
			return self.dataRetrieve(type = ['number'], media = media)
		else:
			result = self.dataRetrieve(type = ['number', number], media = media)
			if not result is None and format:
				if format is True: result = '%01d' % result
				else: result = format % result
			return result

	def numberSeason(self, number = NumberDefault, format = Default):
		return self.number(number = number, format = format, media = MetaData.MediaSeason)

	def numberEpisode(self, number = NumberDefault, format = Default):
		return self.number(number = number, format = format, media = MetaData.MediaEpisode)

	def numbers(self, media = MediaDefault):
		return self.number(number = MetaData.Default, media = media)

	def numbersSeason(self):
		return self.numbers(media = MetaData.MediaSeason)

	def numbersEpisode(self):
		return self.numbers(media = MetaData.MediaEpisode)

	def numberSet(self, value, number = NumberDefault, media = MediaDefault):
		if not value is None: self.dataUpdate(data = {'number' : {number : value}}, media = media)

	def numberSeasonSet(self, value, number = NumberDefault):
		self.numberSet(value = value, number = number, media = MetaData.MediaSeason)

	def numberEpisodeSet(self, value, number = NumberDefault):
		self.numberSet(value = value, number = number, media = MetaData.MediaEpisode)

	def numberAdjust(self):
		try:
			# TVDb uses the year as season number for some daytime shows.
			# Eg: Coronation Street - https://thetvdb.com/series/coronation-street
			# Trakt/TMDb use the default abolsute numbering starting from 0, 1, 2, etc.
			# IMDb also uses the year.
			# Convert years to abolsute season numbers.
			# This function also calculates the absolute order number.
			# UPDATE: Now TVDb updated Coronation Street. The first half of the seasons still use the year as number, the last half of the episodes use the official number.
			# UPDATE 2: Now TVDb has updated all seasons of Coronation Street to reflect the official number.
			if self.mediaShow():
				seasons = self.season(sort = True)
				if seasons:
					minimum = 1900

					if seasons and not Tools.isList(seasons): seasons = [seasons] # If an individual season is set to the show when retrieving from episodes.py.
					numbers = [season.numberSeason() for season in seasons if season] # Sometimes None.
					try: numbers.remove(0)
					except: pass

					if numbers and any(i >= minimum for i in numbers) and len(numbers) < minimum:
						# Only some season numbers are years.
						# Eg: Coronation Street
						# Sort by the first episodes air date, since seasons do not have a release date on TVDb.
						if not len([i for i in numbers if i >= minimum]) == len(numbers):
							releases = []
							for season in seasons:
								if season.numberSeason() > 0:
									try: release = season.episode(sort = True)[0].releaseDateFirst(format = MetaData.FormatTimestamp)
									except: release = None # No episodes.
									if not release: return False # Missing release dates. Cannot sort. Give up.
									releases.append((release, season))
							if not releases: return False
							releases = Tools.listSort(data = releases, key = lambda i : i[0])
							numbers = [season[1].numberSeason() for season in releases]
							try: numbers.remove(0)
							except: pass

						temp = {}
						counter = 0
						for number in numbers:
							counter += 1
							temp[number] = counter
						numbers = temp

						for season in seasons:
							try:
								if season:
									numberYear = season.numberSeason()
									if numberYear >= minimum:
										numberStandard = numbers[numberYear]
										season.numberSeasonSet(value = numberYear, number = MetaData.NumberYear)
										season.numberSeasonSet(value = numberStandard, number = MetaData.NumberStandard)
										episodes = season.episode()
										if episodes:
											for episode in episodes:
												if episode:
													episode.numberSeasonSet(value = numberYear, number = MetaData.NumberYear)
													episode.numberSeasonSet(value = numberStandard, number = MetaData.NumberStandard)
							except: pass
					else:
						# The parent season might have already gone through numberAdjust() and now has the correct season number.
						# However, the child episodes might still have the year as season number, extracted from their own individual TVDb request.
						# Without this, TVDb detailed episodes will have the year as season number, and if episode menus are loaded, it will show both 1x02 (Trakt/IMDb) and 1960x02 (TVDb), eg (Coronation Street S01).
						for season in seasons:
							if season:
								numberStandard = season.numberSeason()
								episodes = season.episode()
								if episodes:
									for episode in episodes:
										if episode: episode.numberSeasonSet(value = numberStandard, number = MetaData.NumberStandard)

				# Calculating the absolute episode order here does not always work.
				# When retrieving detailed episode metadata from episodes.py, only a single season and its episodes are retrieved.
				# That means we cannot calculate the absolute number, since episodes from other seasons are not available.
				# We now use the numbers from the pack to set the abolsute episode number in episodes.py.
				'''episodes = self.episode(sort = True)
				if episodes:
					episodes = [episode for episode in episodes if episode.numberSeason() > 0]
					counter = 0
					for episode in episodes:
						counter += 1
						if not episode.numberSeason(number = MetaData.NumberAbsolute): episode.numberSeasonSet(value = 1, number = MetaData.NumberAbsolute)
						episode.numberEpisodeSet(value = counter, number = MetaData.NumberAbsolute)'''
		except: Logger.error()

	###################################################################
	# LANGUAGE
	###################################################################

	def language(self, language, media = MediaDefault, selection = SelectionDefault):
		return self.dataRetrieve(type = ['language', language], media = media, selection = selection)

	def languageOriginal(self, media = MediaDefault, selection = SelectionDefault):
		return self.language(language = MetaData.LanguageOriginal, media = media, selection = selection)

	def languageAudio(self, media = MediaDefault, selection = SelectionDefault):
		return self.language(language = MetaData.LanguageAudio, media = media, selection = selection)

	def languageSubtitle(self, media = MediaDefault, selection = SelectionDefault):
		return self.language(language = MetaData.LanguageSubtitle, media = media, selection = selection)

	def languageSet(self, value, language, media = MediaDefault):
		if value: self.dataUpdate(data = {'language' : {language : self.dataList(value)}}, media = media)

	def languageOriginalSet(self, value, media = MediaDefault):
		self.languageSet(value = value, language = MetaData.LanguageOriginal, media = media)

	def languageAudioSet(self, value, media = MediaDefault):
		self.languageSet(value = value, language = MetaData.LanguageAudio, media = media)

	def languageSubtitleSet(self, value, media = MediaDefault):
		self.languageSet(value = value, language = MetaData.LanguageSubtitle, media = media)

	def languageSettings(self, media = None, type = None, decor = None):
		if media: return MetaImage.settingsLanguage(media = media, type = self.imageTypeConvert(media = media, type = type, decor = decor))
		else: return Language.settingsCustom('metadata.region.language')

	def languageDefault(self, language, universal = True, media = None, type = None, decor = None):
		if language == MetaData.LanguageUnknown: language = MetaData.LanguageDefault
		elif language == MetaData.LanguageDefault: language = MetaData.LanguageOriginal
		elif language == MetaData.LanguageSettings: language = self.languageSettings(media = media, type = type, decor = decor)
		if universal and language == MetaData.LanguageOriginal: language = MetaData.LanguageUniversal
		return language

	###################################################################
	# COUNTRY
	###################################################################

	def countryDefault(self, country, universal = True):
		if country is MetaData.CountryDefault: country = MetaData.CountryOriginal
		elif country == MetaData.CountrySettings: country = Country.settings('metadata.region.country')
		if country == Country.Automatic: country = MetaData.CountryOriginal
		if universal and country == MetaData.CountryOriginal: country = MetaData.CountryUniversal
		return country

	###################################################################
	# NAME
	###################################################################

	def name(self, language = LanguageDefault, media = MediaDefault, selection = SelectionDefault, fallback = FallbackDefault):
		if selection is MetaData.SelectionDefault:
			media = self.mediaDefault(media)
			if media in [self.media(), MetaData.MediaPerson]: selection = MetaData.SelectionSingle

		result = None
		subdata = self.dataRetrieve(type = 'name', media = media)

		if subdata:
			language = self.languageDefault(language = language)
			result = self.dataRetrieve(type = [language], selection = selection, media = False, metadata = subdata) # Pass language as a list, since it can be None and would otherwise be ignored.
			if not result:
				fallback = self.fallbackDefault(fallback = fallback)
				if fallback:
					if fallback >= MetaData.FallbackSecondary:
						# Prefer English over Original titles, since otherwise original titles using other alphabets might not show up (or show rectangles) if the skin's font does not support the alphabet.
						if not result and fallback >= MetaData.FallbackPrimary and not language == MetaData.LanguageEnglish: result = self.dataRetrieve(type = [self.languageDefault(language = MetaData.LanguageEnglish)], selection = selection, media = False, metadata = subdata)
						if not result and fallback >= MetaData.FallbackSecondary and not language == MetaData.LanguageOriginal: result = self.dataRetrieve(type = [self.languageDefault(language = MetaData.LanguageOriginal)], selection = selection, media = False, metadata = subdata)
					else:
						if not result and fallback >= MetaData.FallbackPrimary and not language == MetaData.LanguageOriginal: result = self.dataRetrieve(type = [self.languageDefault(language = MetaData.LanguageOriginal)], selection = selection, media = False, metadata = subdata)
						if not result and fallback >= MetaData.FallbackPrimary and not language == MetaData.LanguageEnglish: result = self.dataRetrieve(type = [self.languageDefault(language = MetaData.LanguageEnglish)], selection = selection, media = False, metadata = subdata)

		return result

	def nameOriginal(self, media = MediaDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.name(language = MetaData.LanguageOriginal, media = media, selection = selection, fallback = fallback)

	def nameEnglish(self, media = MediaDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.name(language = MetaData.LanguageEnglish, media = media, selection = selection, fallback = fallback)

	def nameSettings(self, media = MediaDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.name(language = MetaData.LanguageSettings, media = media, selection = selection, fallback = fallback)

	def nameSet(self, value, language = LanguageDefault, media = MediaDefault):
		if value:
			if not Tools.isDictionary(value): value = {self.languageDefault(language = language) : self.dataList(value)}
			value = self.dataClean(data = value, newline = True, space = True)
			media = self.mediaDefault(media)
			if media == self.media(): self.dataUpdate(data = {'name' : value}, media = media)
			else:
				person = MetaData(media = MetaData.MediaPerson)
				person.nameSet(value = value, language = language)
				self.personSet(person)

	def nameOriginalSet(self, value, media = MediaDefault):
		self.nameSet(value = value, language = MetaData.LanguageOriginal, media = media)

	def nameEnglishSet(self, value, media = MediaDefault):
		self.nameSet(value = value, language = MetaData.LanguageEnglish, media = media)

	def nameSettingsSet(self, value, media = MediaDefault):
		self.nameSet(value = value, language = MetaData.LanguageSettings, media = media)

	###################################################################
	# NAME - PERSON
	###################################################################

	def namePerson(self, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		person = self.person(selection = selection)
		person = self.dataFix(media = MetaData.MediaPerson, data = person)
		if Tools.isArray(person):
			result = [i.name(language = language, selection = selection, fallback = fallback) for i in person]
			result = Tools.listUnique([i for i in result if i])
			return result
		else: return person.name(language = language, selection = selection, fallback = fallback)

	def namePersonOriginal(self, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.namePerson(language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def namePersonEnglish(self, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.namePerson(language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def namePersonSettings(self, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.namePerson(language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	###################################################################
	# NAME - CHARACTER
	###################################################################

	def nameCharacter(self, type = CharacterTypeDefault, role = CharacterRoleDefault, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		character = self.character(type = type, role = role, selection = selection)
		character = self.dataFix(media = MetaData.MediaCharacter, data = character)
		if Tools.isArray(character):
			result = [i.name(language = language, selection = selection, fallback = fallback) for i in character]
			result = Tools.listUnique([i for i in result if i])
			return result
		else: return character.name(language = language, selection = selection, fallback = fallback)

	def nameCharacterOriginal(self, type = CharacterTypeDefault, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacter(type = type, role = role, language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def nameCharacterEnglish(self, type = CharacterTypeDefault, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacter(type = type, role = role, language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def nameCharacterSettings(self, type = CharacterTypeDefault, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacter(type = type, role = role, language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	def nameCharacterActor(self, role = CharacterRoleDefault, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacter(type = MetaData.CharacterTypeActor, role = role, language = language, selection = selection, fallback = fallback)

	def nameCharacterActorOriginal(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterActor(role = role, language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def nameCharacterActorEnglish(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterActor(role = role, language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def nameCharacterActorSettings(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterActor(role = role, language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	def nameCharacterDirector(self, role = CharacterRoleDefault, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacter(type = MetaData.CharacterTypeDirector, role = role, language = language, selection = selection, fallback = fallback)

	def nameCharacterDirectorOriginal(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterDirector(role = role, language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def nameCharacterDirectorEnglish(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterDirector(role = role, language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def nameCharacterDirectorSettings(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterDirector(role = role, language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	def nameCharacterWriter(self, role = CharacterRoleDefault, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacter(type = MetaData.CharacterTypeWriter, role = role, language = language, selection = selection, fallback = fallback)

	def nameCharacterWriterOriginal(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterWriter(role = role, language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def nameCharacterWriterEnglish(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterWriter(role = role, language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def nameCharacterWriterSettings(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterWriter(role = role, language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	def nameCharacterEditor(self, role = CharacterRoleDefault, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacter(type = MetaData.CharacterTypeEditor, role = role, language = language, selection = selection, fallback = fallback)

	def nameCharacterEditorOriginal(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterEditor(role = role, language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def nameCharacterEditorEnglish(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterEditor(role = role, language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def nameCharacterEditorSettings(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterEditor(role = role, language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	def nameCharacterCreator(self, role = CharacterRoleDefault, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacter(type = MetaData.CharacterTypeCreator, role = role, language = language, selection = selection, fallback = fallback)

	def nameCharacterCreatorOriginal(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterCreator(role = role, language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def nameCharacterCreatorEnglish(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterCreator(role = role, language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def nameCharacterCreatorSettings(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterCreator(role = role, language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	def nameCharacterHost(self, role = CharacterRoleDefault, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacter(type = MetaData.CharacterTypeHost, role = role, language = language, selection = selection, fallback = fallback)

	def nameCharacterHostOriginal(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterHost(role = role, language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def nameCharacterHostEnglish(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterHost(role = role, language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def nameCharacterHostSettings(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterHost(role = role, language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	def nameCharacterCrew(self, role = CharacterRoleDefault, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacter(type = MetaData.CharacterTypeCrew, role = role, language = language, selection = selection, fallback = fallback)

	def nameCharacterCrewOriginal(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterCrew(role = role, language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def nameCharacterCrewEnglish(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterCrew(role = role, language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def nameCharacterCrewSettings(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterCrew(role = role, language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	def nameCharacterProducer(self, role = CharacterRoleDefault, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacter(type = MetaData.CharacterTypeProducer, role = role, language = language, selection = selection, fallback = fallback)

	def nameCharacterProducerOriginal(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterProducer(role = role, language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def nameCharacterProducerEnglish(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterProducer(role = role, language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def nameCharacterProducerSettings(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterProducer(role = role, language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	def nameCharacterGuest(self, role = CharacterRoleDefault, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacter(type = MetaData.CharacterTypeGuest, role = role, language = language, selection = selection, fallback = fallback)

	def nameCharacterGuestOriginal(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterGuest(role = role, language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def nameCharacterGuestEnglish(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterGuest(role = role, language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def nameCharacterGuestSettings(self, role = CharacterRoleDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCharacterGuest(role = role, language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	###################################################################
	# NAME - COMPANY
	###################################################################

	def nameCompany(self, type = CompanyTypeDefault, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		company = self.company(type = type, selection = selection)
		company = self.dataFix(media = MetaData.MediaCompany, data = company)
		if Tools.isArray(company):
			result = [i.name(language = language, selection = selection, fallback = fallback) for i in company]
			result = Tools.listUnique([i for i in result if i])
			return result
		else: return company.name(language = language, selection = selection, fallback = fallback)

	def nameCompanyOriginal(self, company = CompanyTypeDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCompany(company = company, language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def nameCompanyEnglish(self, company = CompanyTypeDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCompany(company = company, language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def nameCompanySettings(self, company = CompanyTypeDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCompany(company = company, language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	def nameCompanyNetwork(self, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCompany(company = MetaData.CompanyTypeNetwork, language = language, selection = selection, fallback = fallback)

	def nameCompanyNetworkOriginal(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCompanyNetwork(language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def nameCompanyNetworkEnglish(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCompanyNetwork(language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def nameCompanyNetworkSettings(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCompanyNetwork(language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	def nameCompanyStudio(self, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCompany(company = MetaData.CompanyTypeStudio, language = language, selection = selection, fallback = fallback)

	def nameCompanyStudioOriginal(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCompanyStudio(language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def nameCompanyStudioEnglish(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCompanyStudio(language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def nameCompanyStudioSettings(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCompanyStudio(language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	def nameCompanyProducer(self, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCompany(company = MetaData.CompanyTypeProducer, language = language, selection = selection, fallback = fallback)

	def nameCompanyProducerOriginal(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCompanyProducer(language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def nameCompanyProducerEnglish(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCompanyProducer(language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def nameCompanyProducerSettings(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCompanyProducer(language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	def nameCompanyDistributor(self, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCompany(company = MetaData.CompanyTypeDistributor, language = language, selection = selection, fallback = fallback)

	def nameCompanyDistributorOriginal(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCompanyDistributor(language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def nameCompanyDistributorEnglish(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCompanyDistributor(language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def nameCompanyDistributorSettings(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCompanyDistributor(language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	def nameCompanyEffects(self, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCompany(company = MetaData.CompanyTypeEffects, language = language, selection = selection, fallback = fallback)

	def nameCompanyEffectsOriginal(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCompanyEffects(language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def nameCompanyEffectsEnglish(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCompanyEffects(language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def nameCompanyEffectsSettings(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.nameCompanyEffects(language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	###################################################################
	# TITLE
	###################################################################

	def title(self, language = LanguageDefault, media = MediaDefault, selection = SelectionDefault, fallback = FallbackDefault):
		if language is True: return self.dataRetrieve(type = 'title', media = media, selection = selection) # Retrieve dictionary of all translations.

		result = None
		subdata = self.dataRetrieve(type = 'title', media = media)

		if subdata:
			language = self.languageDefault(language = language)
			result = self.dataRetrieve(type = [language], selection = selection, media = False, metadata = subdata) # Pass language as a list, since it can be None and would otherwise be ignored.
			if not result:
				fallback = self.fallbackDefault(fallback = fallback)
				if fallback:
					if fallback >= MetaData.FallbackSecondary:
						# Prefer English over Original titles, since otherwise original titles using other alphabets might not show up (or show rectangles) if the skin's font does not support the alphabet.
						if not result and fallback >= MetaData.FallbackPrimary and not language == MetaData.LanguageEnglish: result = self.dataRetrieve(type = [self.languageDefault(language = MetaData.LanguageEnglish)], selection = selection, media = False, metadata = subdata)
						if not result and fallback >= MetaData.FallbackSecondary and not language == MetaData.LanguageOriginal: result = self.dataRetrieve(type = [self.languageDefault(language = MetaData.LanguageOriginal)], selection = selection, media = False, metadata = subdata)
					else:
						if not result and fallback >= MetaData.FallbackPrimary and not language == MetaData.LanguageOriginal: result = self.dataRetrieve(type = [self.languageDefault(language = MetaData.LanguageOriginal)], selection = selection, media = False, metadata = subdata)
						if not result and fallback >= MetaData.FallbackPrimary and not language == MetaData.LanguageEnglish: result = self.dataRetrieve(type = [self.languageDefault(language = MetaData.LanguageEnglish)], selection = selection, media = False, metadata = subdata)

		return result

	def titleOriginal(self, media = MediaDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.title(language = MetaData.LanguageOriginal, media = media, selection = selection, fallback = fallback)

	def titleEnglish(self, media = MediaDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.title(language = MetaData.LanguageEnglish, media = media, selection = selection, fallback = fallback)

	def titleSettings(self, media = MediaDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.title(language = MetaData.LanguageSettings, media = media, selection = selection, fallback = fallback)

	def titleSet(self, value, language = LanguageDefault, media = MediaDefault):
		if value:
			if not Tools.isDictionary(value): value = {self.languageDefault(language = language) : self.dataList(value)}

			# Some titles returned by TVDb contain the year in the title, probably because there are different shows with the same name, but different release years.
			#	Cosmos (2014)
			#	Aspirants (2021)
			#	Hunter x Hunter (2011)
			# This makes show menus look bad if some titles have the year and others not. Remove it to make it aesthetically more appealing.
			# The user can still check the year or premiered date in the GUI to determine the release.
			# There are also some shows containing the country:
			#	The Office (US)
			#	The Heroes (IR)
			# Also remove this, since the user will be able to identify the correct show based on the poster/fanart.
			# And even without that, the release country is still available in the info dialog.
			for k, v in value.items():
				value[k] = Tools.listUnique([Regex.remove(data = i, expression = r'\s+[\(\[](?:(?:19|2[01])\d{2}|[A-Z]{2})[\)\]]$', all = True, flags = Regex.FlagNone) for i in v] if v else v)

			value = self.dataClean(data = value, newline = True, space = True)
			self.dataUpdate(data = {'title' : value}, media = media)

	def titleOriginalSet(self, value, media = MediaDefault):
		self.titleSet(value = value, language = MetaData.LanguageOriginal, media = media)

	def titleEnglishSet(self, value, media = MediaDefault):
		self.titleSet(value = value, language = MetaData.LanguageEnglish, media = media)

	def titleSettingsSet(self, value, media = MediaDefault):
		self.titleSet(value = value, language = MetaData.LanguageSettings, media = media)

	###################################################################
	# TITLE - MOVIE
	###################################################################

	def titleMovie(self, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.title(language = language, media = MetaData.MediaMovie, selection = selection, fallback = fallback)

	def titleMovieOriginal(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.titleMovie(language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def titleMovieEnglish(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.titleMovie(language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def titleMovieSettings(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.titleMovie(language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	def titleMovieSet(self, value, language = LanguageDefault):
		self.titleSet(value = value, language = language, media = MetaData.MediaMovie)

	def titleMovieOriginalSet(self, value):
		self.titleMovieSet(value = value, language = MetaData.LanguageOriginal)

	def titleMovieEnglishSet(self, value):
		self.titleMovieSet(value = value, language = MetaData.LanguageEnglish)

	def titleMovieSettingsSet(self, value):
		self.titleMovieSet(value = value, language = MetaData.LanguageSettings)

	###################################################################
	# TITLE - COLLECTION
	###################################################################

	def titleCollection(self, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.title(language = language, media = MetaData.MediaCollection, selection = selection, fallback = fallback)

	def titleCollectionOriginal(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.titleCollection(language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def titleCollectionEnglish(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.titleCollection(language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def titleCollectionSettings(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.titleCollection(language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	def titleCollectionSet(self, value, language = LanguageDefault):
		self.titleSet(value = value, language = language, media = MetaData.MediaCollection)

	def titleCollectionOriginalSet(self, value):
		self.titleCollectionSet(value = value, language = MetaData.LanguageOriginal)

	def titleCollectionEnglishSet(self, value):
		self.titleCollectionSet(value = value, language = MetaData.LanguageEnglish)

	def titleCollectionSettingsSet(self, value):
		self.titleCollectionSet(value = value, language = MetaData.LanguageSettings)

	###################################################################
	# TITLE - SHOW
	###################################################################

	def titleShow(self, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.title(language = language, media = MetaData.MediaShow, selection = selection, fallback = fallback)

	def titleShowOriginal(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.titleShow(language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def titleShowEnglish(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.titleShow(language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def titleShowSettings(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.titleShow(language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	def titleShowSet(self, value, language = LanguageDefault):
		self.titleSet(value = value, language = language, media = MetaData.MediaShow)

	def titleShowOriginalSet(self, value):
		self.titleShowSet(value = value, language = MetaData.LanguageOriginal)

	def titleShowEnglishSet(self, value):
		self.titleShowSet(value = value, language = MetaData.LanguageEnglish)

	def titleShowSettingsSet(self, value):
		self.titleShowSet(value = value, language = MetaData.LanguageSettings)

	###################################################################
	# TITLE - SEASON
	###################################################################

	def titleSeason(self, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.title(language = language, media = MetaData.MediaSeason, selection = selection, fallback = fallback)

	def titleSeasonOriginal(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.titleSeason(language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def titleSeasonEnglish(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.titleSeason(language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def titleSeasonSettings(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.titleSeason(language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	def titleSeasonSet(self, value, language = LanguageDefault):
		self.titleSet(value = value, language = language, media = MetaData.MediaSeason)

	def titleSeasonOriginalSet(self, title):
		self.titleSeasonSet(value = value, language = MetaData.LanguageOriginal)

	def titleSeasonEnglishSet(self, title):
		self.titleSeasonSet(value = value, language = MetaData.LanguageEnglish)

	def titleSeasonSettingsSet(self, title):
		self.titleSeasonSet(value = value, language = MetaData.LanguageSettings)

	###################################################################
	# TITLE - EPISODE
	###################################################################

	def titleEpisode(self, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.title(language = language, media = MetaData.MediaEpisode, selection = selection, fallback = fallback)

	def titleEpisodeOriginal(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.titleEpisode(language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def titleEpisodeEnglish(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.titleEpisode(language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def titleEpisodeSettings(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.titleEpisode(language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	def titleEpisodeSet(self, value, language = LanguageDefault):
		self.titleSet(value = value, language = language, media = MetaData.MediaEpisode)

	def titleEpisodeOriginalSet(self, title):
		self.titleEpisodeSet(value = value, language = MetaData.LanguageOriginal)

	def titleEpisodeEnglishSet(self, title):
		self.titleEpisodeSet(value = value, language = MetaData.LanguageEnglish)

	def titleEpisodeSettingsSet(self, title):
		self.titleEpisodeSet(value = value, language = MetaData.LanguageSettings)

	###################################################################
	# OVERVIEW
	###################################################################

	def overview(self, language = LanguageDefault, media = MediaDefault, selection = SelectionDefault, fallback = FallbackDefault):
		if language is True: return self.dataRetrieve(type = 'overview', media = media, selection = selection) # Retrieve dictionary of all translations.

		result = None
		subdata = self.dataRetrieve(type = 'overview', media = media)

		if subdata:
			language = self.languageDefault(language = language)
			result = self.dataRetrieve(type = [language], selection = selection, media = False, metadata = subdata) # Pass language as a list, since it can be None and would otherwise be ignored.
			if not result:
				fallback = self.fallbackDefault(fallback = fallback)
				if fallback >= MetaData.FallbackSecondary:
					# Prefer English over Original overviews, since otherwise original overviews using other alphabets might not show up (or show rectangles) if the skin's font does not support the alphabet.
					if not result and fallback >= MetaData.FallbackPrimary and not language == MetaData.LanguageEnglish: result = self.dataRetrieve(type = [self.languageDefault(language = MetaData.LanguageEnglish)], selection = selection, media = False, metadata = subdata)
					if not result and fallback >= MetaData.FallbackSecondary and not language == MetaData.LanguageOriginal: result = self.dataRetrieve(type = [self.languageDefault(language = MetaData.LanguageOriginal)], selection = selection, media = False, metadata = subdata)
				else:
					if not result and fallback >= MetaData.FallbackPrimary and not language == MetaData.LanguageOriginal: result = self.dataRetrieve(type = [self.languageDefault(language = MetaData.LanguageOriginal)], selection = selection, media = False, metadata = subdata)
					if not result and fallback >= MetaData.FallbackPrimary and not language == MetaData.LanguageEnglish: result = self.dataRetrieve(type = [self.languageDefault(language = MetaData.LanguageEnglish)], selection = selection, media = False, metadata = subdata)

		return result

	def overviewOriginal(self, media = MediaDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.overview(language = MetaData.LanguageOriginal, media = media, selection = selection, fallback = fallback)

	def overviewEnglish(self, media = MediaDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.overview(language = MetaData.LanguageEnglish, media = media, selection = selection, fallback = fallback)

	def overviewSettings(self, media = MediaDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.overview(language = MetaData.LanguageSettings, media = media, selection = selection, fallback = fallback)

	def overviewSet(self, value, language = LanguageDefault, media = MediaDefault):
		if value:
			if not Tools.isDictionary(value): value = {self.languageDefault(language = language) : self.dataList(value)}
			value = self.dataClean(data = value, newline = False, space = True)
			self.dataUpdate(data = {'overview' : value}, media = media)

	def overviewOriginalSet(self, value, media = MediaDefault):
		self.overviewSet(value = value, language = MetaData.LanguageOriginal, media = media)

	def overviewEnglishSet(self, value, media = MediaDefault):
		self.overviewSet(value = value, language = MetaData.LanguageEnglish, media = media)

	def overviewSettingsSet(self, value, media = MediaDefault):
		self.overviewSet(value = value, language = MetaData.LanguageSettings, media = media)

	###################################################################
	# OVERVIEW - MOVIE
	###################################################################

	def overviewMovie(self, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.overview(language = language, media = MetaData.MediaMovie, selection = selection, fallback = fallback)

	def overviewMovieOriginal(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.overviewMovie(language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def overviewMovieEnglish(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.overviewMovie(language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def overviewMovieSettings(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.overviewMovie(language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	def overviewMovieSet(self, value, language = LanguageDefault):
		self.overviewSet(value = value, language = language, media = MetaData.MediaMovie)

	def overviewMovieOriginalSet(self, value):
		self.overviewMovieSet(value = overview, language = MetaData.LanguageOriginal)

	def overviewMovieEnglishSet(self, value):
		self.overviewMovieSet(value = value, language = MetaData.LanguageEnglish)

	def overviewMovieSettingsSet(self, value):
		self.overviewMovieSet(value = value, language = MetaData.LanguageSettings)

	###################################################################
	# OVERVIEW - COLLECTION
	###################################################################

	def overviewCollection(self, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.overview(language = language, media = MetaData.MediaCollection, selection = selection, fallback = fallback)

	def overviewCollectionOriginal(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.overviewCollection(language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def overviewCollectionEnglish(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.overviewCollection(language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def overviewCollectionSettings(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.overviewCollection(language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	def overviewCollectionSet(self, value, language = LanguageDefault):
		self.overviewSet(value = value, language = language, media = MetaData.MediaCollection)

	def overviewCollectionOriginalSet(self, value):
		self.overviewCollectionSet(value = value, language = MetaData.LanguageOriginal)

	def overviewCollectionEnglishSet(self, value):
		self.overviewCollectionSet(value = value, language = MetaData.LanguageEnglish)

	def overviewCollectionSettingsSet(self, value):
		self.overviewCollectionSet(value = value, language = MetaData.LanguageSettings)

	###################################################################
	# OVERVIEW - SHOW
	###################################################################

	def overviewShow(self, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.overview(language = language, media = MetaData.MediaShow, selection = selection, fallback = fallback)

	def overviewShowOriginal(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.overviewShow(language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def overviewShowEnglish(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.overviewShow(language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def overviewShowSettings(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.overviewShow(language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	def overviewShowSet(self, value, language = LanguageDefault):
		self.overviewSet(value = value, language = language, media = MetaData.MediaShow)

	def overviewShowOriginalSet(self, value):
		self.overviewShowSet(value = value, language = MetaData.LanguageOriginal)

	def overviewShowEnglishSet(self, value):
		self.overviewShowSet(value = value, language = MetaData.LanguageEnglish)

	def overviewShowSettingsSet(self, value):
		self.overviewShowSet(value = value, language = MetaData.LanguageSettings)

	###################################################################
	# OVERVIEW - SEASON
	###################################################################

	def overviewSeason(self, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.overview(language = language, media = MetaData.MediaSeason, selection = selection, fallback = fallback)

	def overviewSeasonOriginal(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.overviewSeason(language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def overviewSeasonEnglish(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.overviewSeason(language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def overviewSeasonSettings(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.overviewSeason(language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	def overviewSeasonSet(self, value, language = LanguageDefault):
		self.overviewSet(value = value, language = language, media = MetaData.MediaSeason)

	def overviewSeasonOriginalSet(self, value):
		self.overviewSeasonSet(value = value, language = MetaData.LanguageOriginal)

	def overviewSeasonEnglishSet(self, value):
		self.overviewSeasonSet(value = value, language = MetaData.LanguageEnglish)

	def overviewSeasonSettingsSet(self, value):
		self.overviewSeasonSet(value = value, language = MetaData.LanguageSettings)

	###################################################################
	# OVERVIEW - EPISODE
	###################################################################

	def overviewEpisode(self, language = LanguageDefault, selection = SelectionDefault, fallback = FallbackDefault):
		return self.overview(language = language, media = MetaData.MediaEpisode, selection = selection, fallback = fallback)

	def overviewEpisodeOriginal(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.overviewEpisode(language = MetaData.LanguageOriginal, selection = selection, fallback = fallback)

	def overviewEpisodeEnglish(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.overviewEpisode(language = MetaData.LanguageEnglish, selection = selection, fallback = fallback)

	def overviewEpisodeSettings(self, selection = SelectionDefault, fallback = FallbackDefault):
		return self.overviewEpisode(language = MetaData.LanguageSettings, selection = selection, fallback = fallback)

	def overviewEpisodeSet(self, value, language = LanguageDefault):
		self.overviewSet(value = value, language = language, media = MetaData.MediaEpisode)

	def overviewEpisodeOriginalSet(self, value):
		self.overviewEpisodeSet(value = value, language = MetaData.LanguageOriginal)

	def overviewEpisodeEnglishSet(self, value):
		self.overviewEpisodeSet(value = value, language = MetaData.LanguageEnglish)

	def overviewEpisodeSettingsSet(self, value):
		self.overviewEpisodeSet(value = value, language = MetaData.LanguageSettings)

	###################################################################
	# YEAR
	###################################################################

	def year(self, media = MediaDefault):
		return self.dataRetrieve(type = 'year', media = media)

	def yearSet(self, value, media = MediaDefault):
		if value: self.dataUpdate(data = {'year' : int(value)}, media = media)

	@classmethod
	def yearExtract(self, data):
		if data:
			year = Regex.extract(data = data, expression = r'((?:19|2\d)\d{2})', cache = True)
			if year: return int(year)
		return None

	###################################################################
	# IMAGE
	###################################################################

	def image(self, type = ImageTypeDefault, quality = ImageQualityDefault, opacity = ImageOpacityDefault, decor = ImageDecorDefault, language = LanguageDefault, media = MediaDefault, selection = SelectionDefault, fallback = FallbackDefault, sort = SortDefault, internal = False, extract = None):
		# Things that are done to improve lookup time:
		#	1. Store images in a nested dictionary instead of a linear list. Lookup by keys is a lot faster than iterating over the list and matching the attributes.
		#	2. Extract subdata and pass it to fallback dataRetrieve(), instead of calling dataRetrieve() with a full list of the type parameters each time. This especially improves speed if the item does not contain any images.
		# Note that languages should always be passed as a list for subdata, eg: dataRetrieve(type = [language]), since the language can be None and would otherwise be ignored.

		subdata = self.dataRetrieve(media = media, type = 'image')
		if not subdata: return None # Reduces lookup times if there are no photos at all.
		mediaCurrent = self.media()

		if extract is None: extract = 'link'
		elif extract is False: extract = None

		type = self.imageTypeDefault(type = type)
		quality = self.imageQualityDefault(quality = quality)
		opacity = self.imageOpacityDefault(opacity = opacity)
		decor = self.imageDecorDefault(decor = decor)

		if not Tools.isArray(language): language = [language]
		language = [self.languageDefault(language = i, media = mediaCurrent, type = type, decor = decor) for i in language]
		language = Tools.listUnique(language)

		sort, order = self.sort(sort = sort, media = mediaCurrent, type = type, decor = decor)

		result = []

		subdata0 = images = self.dataRetrieve(type = type, media = False, metadata = subdata)
		subdata1 = None
		if subdata0:
			subdata1 = images = self.dataRetrieve(type = [quality, opacity, decor], media = False, metadata = subdata0)
			if subdata1:
				for i in language:
					images = self.dataRetrieve(type = [i], sort = sort, order = order, extract = extract, selection = selection, media = False, metadata = subdata1)
					if images:
						if Tools.isArray(images): result.extend(images)
						else: result.append(images)

		fallback = self.fallbackDefault(fallback = fallback, default = MetaData.FallbackSecondary if (opacity == MetaData.ImageOpacityClear or decor == MetaData.ImageDecorEmbell) else MetaData.FallbackPrimary) # Do not fall back to solid for clear images. Otherwise solid images are displayed in the GUI where opacity is required.
		if fallback and not result:
			# Put False (unknown language) last, since TVDb has images with an unknow language.
			# Some of these unknown languages are indeed the universal (or common English) images, but some contain writing from other languages (eg: Avatar).
			# Try to avoid these images by preferring English images.

			languageExtra = []
			if fallback >= MetaData.FallbackPrimary:
				languageExtra = [MetaData.LanguageUniversal, MetaData.LanguageEnglish, MetaData.LanguageUnknown]
				languageExtra = [self.languageDefault(language = i, media = mediaCurrent, type = type, decor = decor) for i in languageExtra]
				language.extend(languageExtra)
				language = Tools.listUnique(language)

			# Prefer the same type/quality/opacity/decor over language.
			if subdata1 and languageExtra:
				for i in languageExtra:
					result = self.dataRetrieve(type = [i], sort = sort, order = order, extract = extract, selection = selection, media = False, metadata = subdata1)
					if result: break

			if not result:
				ordered = []

				if fallback >= MetaData.FallbackPrimary:
					if decor == MetaData.ImageDecorEmbell: ordered.append([quality, opacity, MetaData.ImageDecorPlain])
					elif decor == MetaData.ImageDecorPlain: ordered.append([quality, opacity, MetaData.ImageDecorEmbell])

					if quality == MetaData.ImageQualityHigh: ordered.append([MetaData.ImageQualityLow, opacity, decor])
					elif quality == MetaData.ImageQualityLow: ordered.append([MetaData.ImageQualityHigh, opacity, decor])

					if decor == MetaData.ImageDecorEmbell:
						if quality == MetaData.ImageQualityHigh: ordered.append([MetaData.ImageQualityLow, opacity, MetaData.ImageDecorPlain])
						elif quality == MetaData.ImageQualityLow: ordered.append([MetaData.ImageQualityHigh, opacity, MetaData.ImageDecorPlain])
					elif decor == MetaData.ImageDecorPlain:
						if quality == MetaData.ImageQualityHigh: ordered.append([MetaData.ImageQualityLow, opacity, MetaData.ImageDecorEmbell])
						elif quality == MetaData.ImageQualityLow: ordered.append([MetaData.ImageQualityHigh, opacity, MetaData.ImageDecorEmbell])

				if fallback >= MetaData.FallbackTertiary:
					if opacity == MetaData.ImageOpacityClear: ordered.append([quality, MetaData.ImageOpacitySolid, decor])
					elif opacity == MetaData.ImageOpacitySolid: ordered.append([quality, MetaData.ImageOpacityClear, decor])

					if decor == MetaData.ImageDecorEmbell:
						if opacity == MetaData.ImageOpacityClear: ordered.append([quality, MetaData.ImageOpacitySolid, MetaData.ImageDecorPlain])
						elif opacity == MetaData.ImageOpacitySolid: ordered.append([quality, MetaData.ImageOpacityClear, MetaData.ImageDecorPlain])
					elif decor == MetaData.ImageDecorPlain:
						if opacity == MetaData.ImageOpacityClear: ordered.append([quality, MetaData.ImageOpacitySolid, MetaData.ImageDecorEmbell])
						elif opacity == MetaData.ImageOpacitySolid: ordered.append([quality, MetaData.ImageOpacityClear, MetaData.ImageDecorEmbell])

					if quality == MetaData.ImageQualityHigh:
						if opacity == MetaData.ImageOpacityClear: ordered.append([MetaData.ImageQualityLow, MetaData.ImageOpacitySolid, decor])
						elif opacity == MetaData.ImageOpacitySolid: ordered.append([MetaData.ImageQualityLow, MetaData.ImageOpacityClear, decor])
					elif quality == MetaData.ImageQualityLow:
						if opacity == MetaData.ImageOpacityClear: ordered.append([MetaData.ImageQualityHigh, MetaData.ImageOpacitySolid, decor])
						elif opacity == MetaData.ImageOpacitySolid: ordered.append([MetaData.ImageQualityHigh, MetaData.ImageOpacityClear, decor])

					if decor == MetaData.ImageDecorEmbell:
						if quality == MetaData.ImageQualityHigh:
							if opacity == MetaData.ImageOpacityClear: ordered.append([MetaData.ImageQualityLow, MetaData.ImageOpacitySolid, MetaData.ImageDecorPlain])
							elif opacity == MetaData.ImageOpacitySolid: ordered.append([MetaData.ImageQualityLow, MetaData.ImageOpacityClear, MetaData.ImageDecorPlain])
						elif quality == MetaData.ImageQualityLow:
							if opacity == MetaData.ImageOpacityClear: ordered.append([MetaData.ImageQualityHigh, MetaData.ImageOpacitySolid, MetaData.ImageDecorPlain])
							elif opacity == MetaData.ImageOpacitySolid: ordered.append([MetaData.ImageQualityHigh, MetaData.ImageOpacityClear, MetaData.ImageDecorPlain])
					elif decor == MetaData.ImageDecorPlain:
						if quality == MetaData.ImageQualityHigh:
							if opacity == MetaData.ImageOpacityClear: ordered.append([MetaData.ImageQualityLow, MetaData.ImageOpacitySolid, MetaData.ImageDecorEmbell])
							elif opacity == MetaData.ImageOpacitySolid: ordered.append([MetaData.ImageQualityLow, MetaData.ImageOpacityClear, MetaData.ImageDecorEmbell])
						elif quality == MetaData.ImageQualityLow:
							if opacity == MetaData.ImageOpacityClear: ordered.append([MetaData.ImageQualityHigh, MetaData.ImageOpacitySolid, MetaData.ImageDecorEmbell])
							elif opacity == MetaData.ImageOpacitySolid: ordered.append([MetaData.ImageQualityHigh, MetaData.ImageOpacityClear, MetaData.ImageDecorEmbell])

				# Select a similar quality/opacity/decor.
				if subdata0:
					for j in range(len(ordered)):
						ordered[j] = self.dataRetrieve(type = [ordered[j][0], ordered[j][1], ordered[j][2]], media = False, metadata = subdata0)
						if ordered[j]:
							for i in language:
								result = self.dataRetrieve(type = [i], sort = sort, order = order, extract = extract, selection = selection, media = False, metadata = ordered[j])
								if result: break
							if result: break

					# Select any available language.
					if not result and fallback >= MetaData.FallbackSecondary:
						for j in ordered:
							if j:
								result = self.dataRetrieve(sort = sort, order = order, extract = extract, selection = selection, flatten = MetaData.SelectionList, media = False, metadata = j)
								if result: break

				# Select alterntives.
				if not result and fallback >= MetaData.FallbackTertiary and not internal:
					alternatives = {
						MetaData.ImageTypePoster : MetaData.ImageTypeThumbnail,
						MetaData.ImageTypeDisc : MetaData.ImageTypePoster,
						MetaData.ImageTypeThumbnail : MetaData.ImageTypePoster,

						MetaData.ImageTypeBackground : MetaData.ImageTypeArtwork,
						MetaData.ImageTypeArtwork : MetaData.ImageTypeBackground,
					}
					if type in alternatives:
						for i in language:
							result = self.image(type = alternatives[type], quality = quality, opacity = opacity, decor = decor, language = i, media = media, selection = selection, fallback = fallback, internal = True)
							if result: break

				# Select any available.
				if not result and subdata and fallback >= MetaData.FallbackQuaternary:
					result = self.dataRetrieve(sort = sort, order = order, extract = extract, selection = selection, flatten = MetaData.SelectionList, media = False, metadata = subdata)

		result = self.dataSelect(data = result, selection = selection)
		if Tools.isArray(result): result = Tools.listUnique(result)
		return result

	def imageIcon(self, quality = ImageQualityDefault, opacity = ImageOpacityDefault, decor = ImageDecorDefault, language = LanguageDefault, media = MediaDefault, selection = SelectionSingle, fallback = FallbackDefault, sort = SortDefault, extract = None):
		return self.image(type = MetaData.ImageTypeIcon, quality = quality, opacity = opacity, decor = decor, language = language, media = media, selection = selection, fallback = fallback, sort = sort, extract = extract)

	def imageIconClear(self, quality = ImageQualityDefault, decor = ImageDecorDefault, language = LanguageDefault, media = MediaDefault, selection = SelectionSingle, fallback = FallbackDefault, sort = SortDefault, extract = None):
		return self.imageIcon(quality = quality, opacity = MetaData.ImageOpacityClear, decor = decor, language = language, media = media, selection = selection, fallback = fallback, sort = sort, extract = extract)

	def imagePoster(self, quality = ImageQualityDefault, opacity = ImageOpacityDefault, decor = ImageDecorDefault, language = LanguageDefault, media = MediaDefault, selection = SelectionSingle, fallback = FallbackDefault, sort = SortDefault, extract = None):
		return self.image(type = MetaData.ImageTypePoster, quality = quality, opacity = opacity, decor = decor, language = language, media = media, selection = selection, fallback = fallback, sort = sort, extract = extract)

	def imageDisc(self, quality = ImageQualityDefault, opacity = ImageOpacityDefault, decor = ImageDecorDefault, language = LanguageDefault, media = MediaDefault, selection = SelectionSingle, fallback = FallbackDefault, sort = SortDefault, extract = None):
		return self.image(type = MetaData.ImageTypeDisc, quality = quality, opacity = opacity, decor = decor, language = language, media = media, selection = selection, fallback = fallback, sort = sort, extract = extract)

	def imagePhoto(self, quality = ImageQualityDefault, opacity = ImageOpacityDefault, decor = ImageDecorDefault, language = LanguageDefault, media = MediaDefault, selection = SelectionSingle, fallback = FallbackDefault, sort = SortDefault, extract = None):
		return self.image(type = MetaData.ImageTypePhoto, quality = quality, opacity = opacity, decor = decor, language = language, media = media, selection = selection, fallback = fallback, sort = sort, extract = extract)

	def imageBanner(self, quality = ImageQualityDefault, opacity = ImageOpacityDefault, decor = ImageDecorDefault, language = LanguageDefault, media = MediaDefault, selection = SelectionSingle, fallback = FallbackDefault, sort = SortDefault, extract = None):
		return self.image(type = MetaData.ImageTypeBanner, quality = quality, opacity = opacity, decor = decor, language = language, media = media, selection = selection, fallback = fallback, sort = sort, extract = extract)

	def imageBackground(self, quality = ImageQualityDefault, opacity = ImageOpacityDefault, decor = ImageDecorDefault, language = LanguageDefault, media = MediaDefault, selection = SelectionSingle, fallback = FallbackDefault, sort = SortDefault, extract = None):
		return self.image(type = MetaData.ImageTypeBackground, quality = quality, opacity = opacity, decor = decor, language = language, media = media, selection = selection, fallback = fallback, sort = sort, extract = extract)

	def imageArtwork(self, quality = ImageQualityDefault, opacity = ImageOpacityDefault, decor = ImageDecorDefault, language = LanguageDefault, media = MediaDefault, selection = SelectionSingle, fallback = FallbackDefault, sort = SortDefault, extract = None):
		return self.image(type = MetaData.ImageTypeArtwork, quality = quality, opacity = opacity, decor = decor, language = language, media = media, selection = selection, fallback = fallback, sort = sort, extract = extract)

	def imageArtworkClear(self, quality = ImageQualityDefault, decor = ImageDecorDefault, language = LanguageDefault, media = MediaDefault, selection = SelectionSingle, fallback = FallbackDefault, sort = SortDefault, extract = None):
		return self.imageArtwork(quality = quality, opacity = MetaData.ImageOpacityClear, decor = decor, language = language, media = media, selection = selection, fallback = fallback, sort = sort, extract = extract)

	def imageThumbnail(self, quality = ImageQualityDefault, opacity = ImageOpacityDefault, decor = ImageDecorDefault, language = LanguageDefault, media = MediaDefault, selection = SelectionSingle, fallback = FallbackDefault, sort = SortDefault, extract = None):
		return self.image(type = MetaData.ImageTypeThumbnail, quality = quality, opacity = opacity, decor = decor, language = language, media = media, selection = selection, fallback = fallback, sort = sort, extract = extract)

	def imageCinemagraph(self, quality = ImageQualityDefault, opacity = ImageOpacityDefault, decor = ImageDecorDefault, language = LanguageDefault, media = MediaDefault, selection = SelectionSingle, fallback = FallbackDefault, sort = SortDefault, extract = None):
		return self.image(type = MetaData.ImageTypeCinemagraph, quality = quality, opacity = opacity, decor = decor, language = language, media = media, selection = selection, fallback = fallback, sort = sort, extract = extract)

	def imageKodiActor(self, quality = ImageQualityDefault, opacity = ImageOpacitySolid, decor = ImageDecorPlain, language = LanguageDefault, media = MediaDefault, selection = SelectionSingle, fallback = FallbackDefault, sort = SortDefault, extract = None):
		return self.imagePhoto(quality = quality, opacity = opacity, decor = decor, language = language, media = media, selection = selection, fallback = fallback, sort = sort, extract = extract)

	def imageKodiCharacterart(self, quality = ImageQualityDefault, opacity = ImageOpacityClear, decor = ImageDecorPlain, language = LanguageDefault, media = MediaDefault, selection = SelectionSingle, fallback = FallbackDefault, sort = SortDefault, extract = None):
		return self.imagePhoto(quality = quality, opacity = opacity, decor = decor, language = language, media = media, selection = selection, fallback = fallback, sort = sort, extract = extract)

	def imageKodiClearart(self, quality = ImageQualityDefault, opacity = ImageOpacityClear, decor = ImageDecorEmbell, language = LanguageDefault, media = MediaDefault, selection = SelectionSingle, fallback = FallbackDefault, sort = SortDefault, extract = None):
		return self.imageArtwork(quality = quality, opacity = opacity, decor = decor, language = language, media = media, selection = selection, fallback = fallback, sort = sort, extract = extract)

	def imageKodiClearlogo(self, quality = ImageQualityDefault, opacity = ImageOpacityClear, decor = ImageDecorEmbell, language = LanguageDefault, media = MediaDefault, selection = SelectionSingle, fallback = FallbackDefault, sort = SortDefault, extract = None):
		return self.imageIcon(quality = quality, opacity = opacity, decor = decor, language = language, media = media, selection = selection, fallback = fallback, sort = sort, extract = extract)

	def imageKodiIcon(self, quality = ImageQualityDefault, opacity = ImageOpacitySolid, decor = ImageDecorEmbell, language = LanguageDefault, media = MediaDefault, selection = SelectionSingle, fallback = FallbackDefault, sort = SortDefault, extract = None):
		return self.imageIcon(quality = quality, opacity = opacity, decor = decor, language = language, media = media, selection = selection, fallback = fallback, sort = sort, extract = extract)

	def imageKodiDiscart(self, quality = ImageQualityDefault, opacity = ImageOpacitySolid, decor = ImageDecorEmbell, language = LanguageDefault, media = MediaDefault, selection = SelectionSingle, fallback = FallbackDefault, sort = SortDefault, extract = None):
		return self.imageDisc(quality = quality, opacity = opacity, decor = decor, language = language, media = media, selection = selection, fallback = fallback, sort = sort, extract = extract)

	def imageKodiThumb(self, quality = ImageQualityDefault, opacity = ImageOpacitySolid, decor = ImageDecorPlain, language = LanguageDefault, media = MediaDefault, selection = SelectionSingle, fallback = FallbackDefault, sort = SortDefault, extract = None):
		return self.imageThumbnail(quality = quality, opacity = opacity, decor = decor, language = language, media = media, selection = selection, fallback = fallback, sort = sort, extract = extract)

	def imageKodiBanner(self, quality = ImageQualityDefault, opacity = ImageOpacitySolid, decor = ImageDecorEmbell, language = LanguageDefault, media = MediaDefault, selection = SelectionSingle, fallback = FallbackDefault, sort = SortDefault, extract = None):
		return self.imageBanner(quality = quality, opacity = opacity, decor = decor, language = language, media = media, selection = selection, fallback = fallback, sort = sort, extract = extract)

	def imageKodiPoster(self, quality = ImageQualityDefault, opacity = ImageOpacitySolid, decor = ImageDecorEmbell, language = LanguageDefault, media = MediaDefault, selection = SelectionSingle, fallback = FallbackDefault, sort = SortDefault, extract = None):
		return self.imagePoster(quality = quality, opacity = opacity, decor = decor, language = language, media = media, selection = selection, fallback = fallback, sort = sort, extract = extract)

	def imageKodiFanart(self, quality = ImageQualityDefault, opacity = ImageOpacitySolid, decor = ImageDecorPlain, language = LanguageDefault, media = MediaDefault, selection = SelectionSingle, fallback = FallbackDefault, sort = SortDefault, extract = None):
		return self.imageBackground(quality = quality, opacity = opacity, decor = decor, language = language, media = media, selection = selection, fallback = fallback, sort = sort, extract = extract)

	def imageKodiKeyart(self, quality = ImageQualityDefault, opacity = ImageOpacitySolid, decor = ImageDecorPlain, language = LanguageDefault, media = MediaDefault, selection = SelectionSingle, fallback = FallbackDefault, sort = SortDefault, extract = None):
		return self.imagePoster(quality = quality, opacity = opacity, decor = decor, language = language, media = media, selection = selection, fallback = fallback, sort = sort, extract = extract)

	def imageKodiLandscape(self, quality = ImageQualityDefault, opacity = ImageOpacitySolid, decor = ImageDecorEmbell, language = LanguageDefault, media = MediaDefault, selection = SelectionSingle, fallback = FallbackDefault, sort = SortDefault, extract = None):
		return self.imageBackground(quality = quality, opacity = opacity, decor = decor, language = language, media = media, selection = selection, fallback = fallback, sort = sort, extract = extract)

	def imageSet(self, value, id = None, provider = ProviderDefault, type = ImageTypeDefault, quality = ImageQualityDefault, resolution = ImageResolutionDefault, opacity = ImageOpacityDefault, decor = ImageDecorDefault, language = LanguageDefault, vote = 0, sort = 0, media = MediaDefault):
		# Set images as a list, so that a list of images can be passed to imageSet().
		# This reduces the time of dataUpdate() compared to setting images individually.
		if value:
			if not Tools.isArray(value): value = [value]
			for i in range(len(value)):
				item = value[i]

				if not media:
					try: media = item['media']
					except: pass

				if not Tools.isStructure(item):
					item = {
						'type' : type,
						'quality' : quality,
						'resolution' : resolution,
						'opacity' : opacity,
						'decor' : decor,
						'language' : language,
						'vote' : vote,
						'sort' : sort,
						'link' : item,
					}
				itemDefault = {
					'type' : self.imageTypeDefault(type = item['type']),
					'quality' : self.imageQualityDefault(quality = item['quality']),
					'resolution' : self.imageResolutionDefault(resolution = item['resolution']),
					'opacity' : self.imageOpacityDefault(opacity = item['opacity']),
					'decor' : self.imageDecorDefault(decor = item['decor']),
					'language' : self.languageDefault(language = item['language']),
					'vote' : self.voteDefault(item['vote']),
					'sort' : self.sortDefault(item['sort']),
					'link' : item['link'],
				}

				media = self.mediaDefault(media = media)

				# TVDb returns artwork in the main structure (eg: show) that belongs to substructures (eg: season or episode).
				# Eg: S.W.A.T.
				ignore = False
				if self.mediaContent():
					if id is None:
						try: id = item['id']
						except: pass
					if id:
						item = self.item(media = media, attribute = {'id' : {provider : str(id)}}, selection = MetaData.SelectionSingle)

						# TVDb has character images but they have the person ID.
						if not item and media == MetaData.MediaCharacter: item = self.item(media = media, attribute = {'person' : {'id' : {provider : str(id)}}}, selection = MetaData.SelectionSingle)

						if item: item.imageSet(value = itemDefault, media = media)

						# Update (2025-04)
						# If season images are returned for the show, ignore them.
						# Eg: S.W.A.T. - S05 poster is returned for the show.
						# Not sure if this breaks anything?
						mediaReal = self.media()
						if (mediaReal == MetaData.MediaShow and media in (MetaData.MediaSeason, MetaData.MediaEpisode)) or (mediaReal == MetaData.MediaSeason and media == MetaData.MediaEpisode):
							# Image already added to the season object. Do not add it to the show object.
							ignore = True

				# Character photos should be added to the main "image" list and not the "character" list.
				if self.mediaContent() and (self.mediaEntity(media = media) or id): media = MetaData.MediaDefault

				# If the image is overwritten multiple times (eg: TVDb might have the image in "artwork" and "season"), use the best values between them.
				# This is especially important for the vote. Always use the highest vote instead of overwritting it with the last value.

				result = self.dataRetrieve(type = 'image', attribute = {'link' : itemDefault['link']}, media = media, selection = MetaData.SelectionSingle, flatten = MetaData.SelectionList)
				if result:
					for k, v in result.items():
						if item[k] is None:
							if not v is None: item[k] = v
					try: item['vote'] = max(item['vote'], result['vote'])
					except: pass
					try: item['sort'] = max(item['sort'], result['sort'])
					except: pass
				else:
					item = itemDefault

				if ignore: value[i] = None
				else: value[i] = item

			# Always add character photos to the content/main image list as well, even if already added to the subcontent.
			# Allows the character photos to be part of the movie/show images.
			images = {}
			for image in value:
				if image:
					data = images

					type = image['type']
					try:
						data = data[type]
					except:
						data[type] = {}
						data = data[type]

					quality = image['quality']
					try:
						data = data[quality]
					except:
						data[quality] = {}
						data = data[quality]

					opacity = image['opacity']
					try:
						data = data[opacity]
					except:
						data[opacity] = {}
						data = data[opacity]

					decor = image['decor']
					try:
						data = data[decor]
					except:
						data[decor] = {}
						data = data[decor]

					language = image['language']
					try:
						data = data[language]
					except:
						data[language] = []
						data = data[language]

					data.append(image)

			self.dataUpdate(data = {'image' : images}, media = media)

	@classmethod
	def imageTypeConvert(self, media, type, decor):
		if media in MetaData.MediaContent:
			if type == MetaData.ImageTypePoster:
				if decor == MetaData.ImageDecorPlain: return MetaImage.TypeKeyart
				else: return MetaImage.TypePoster
			elif type == MetaData.ImageTypeBackground:
				if decor == MetaData.ImageDecorEmbell: return MetaImage.TypeLandscape
				else: return MetaImage.TypeFanart
			elif type == MetaData.ImageTypeThumbnail: return MetaImage.TypeThumb
			elif type == MetaData.ImageTypeBanner: return MetaImage.TypeBanner
			elif type == MetaData.ImageTypeIcon: return MetaImage.TypeClearlogo
			elif type == MetaData.ImageTypeArtwork: return MetaImage.TypeClearart
			elif type == MetaData.ImageTypeDisc: return MetaImage.TypeDiscart
		return None

	@classmethod
	def imageTypeExtract(self, data):
		try: return MetaData.DataImageType[data]
		except: pass

		image = MetaData.ImageTypeDefault
		if Regex.match(data = data, expression = r'(?:icon|logo)', cache = True): image = MetaData.ImageTypeIcon
		elif Regex.match(data = data, expression = r'poster', cache = True): image = MetaData.ImageTypePoster
		elif Regex.match(data = data, expression = r'(?:dis[ck]|dvd|blu.?ray|box|cover)', cache = True): image = MetaData.ImageTypeDisc
		elif Regex.match(data = data, expression = r'(?:ph|f)oto', cache = True): image = MetaData.ImageTypePhoto
		elif Regex.match(data = data, expression = r'banner', cache = True): image = MetaData.ImageTypeBanner
		elif Regex.match(data = data, expression = r'(?:background|landscape)', cache = True): image = MetaData.ImageTypeBackground
		elif Regex.match(data = data, expression = r'(?:fan[\s\-\_\.]*)?art(?:[\s\-\_\.]*work)?', cache = True): image = MetaData.ImageTypeArtwork
		elif Regex.match(data = data, expression = r'(?:thumb(?:[\s\-\_\.]*nail)?|screens?(?:[\s\-\_\.]*caps?)?)', cache = True): image = MetaData.ImageTypeThumbnail
		elif Regex.match(data = data, expression = r'cinema(?:[\s\-\_\.]*graph)?', cache = True): image = MetaData.ImageTypeCinemagraph
		elif Regex.match(data = data, expression = r'(?:person|people|character|actor|director|producer)', cache = True): image = MetaData.ImageTypePhoto # Eg: https://artworks.thetvdb.com/banners/person/xxx/primary.jpg

		MetaData.DataImageType[data] = image
		return image

	def imageTypeDefault(self, type):
		if type is MetaData.ImageTypeDefault:
			if self.mediaEntity(): type = MetaData.ImageTypePhoto
			else: type = MetaData.ImageTypePoster
		return type

	@classmethod
	def imageQualityExtract(self, data, width = None, height = None):
		id = str(data) + '_' + str(width) + '_' + str(height) # Include the width/height, since this function is sometimes called with the same data, but sometimes with ans sometimes without width/height.
		try: return MetaData.DataImageQuality[id]
		except: pass

		quality = MetaData.ImageQualityDefault
		if width: quality = MetaData.ImageQualityLow if width < 500 else MetaData.ImageQualityHigh # Eg: https://thetvdb.com/artwork/60802233
		elif height: quality = MetaData.ImageQualityLow if height < 600 else MetaData.ImageQualityHigh
		elif Regex.match(data = data, expression = r'(?:high|[^a-z0-9]*h[qd][^a-z0-9]*|16\s*:\s*\d)', cache = True): quality = MetaData.ImageQualityHigh
		elif Regex.match(data = data, expression = r'(?:low|[^a-z0-9]*[sl][qd][^a-z0-9]*|4\s*:\s*3)', cache = True): quality = MetaData.ImageQualityLow

		MetaData.DataImageQuality[id] = quality
		return quality

	@classmethod
	def imageQualityDefault(self, quality):
		if quality is MetaData.ImageQualityDefault: quality = MetaData.ImageQualityHigh
		return quality

	@classmethod
	def imageResolutionDefault(self, resolution = None, quality = None, width = None, height = None):
		if not resolution: resolution = {'quality' : quality, 'width' : width, 'height' : height}
		return resolution

	@classmethod
	def imageOpacityExtract(self, data):
		try: return MetaData.DataImageOpacity[data]
		except: pass

		opacity = MetaData.ImageOpacityDefault
		if Regex.match(data = data, expression = r'(?:clear|transparent)', cache = True): opacity = MetaData.ImageOpacityClear
		elif Regex.match(data = data, expression = r'(?:opaque|solid)', cache = True): opacity = MetaData.ImageOpacitySolid

		MetaData.DataImageOpacity[data] = opacity
		return opacity

	@classmethod
	def imageOpacityDefault(self, opacity):
		if opacity is MetaData.ImageOpacityDefault: opacity = MetaData.ImageOpacitySolid
		return opacity

	@classmethod
	def imageDecorExtract(self, data = None, type = None, text = None, language = None):
		id = str(data) + '_' + str(type) # Include the type, since TVDb sometimes has a poster also listed as a background.
		try: return MetaData.DataImageDecor[id]
		except: pass

		decor = MetaData.ImageDecorDefault
		if text: decor = MetaData.ImageDecorEmbell
		elif language and not language == MetaData.LanguageUnknown: decor = MetaData.ImageDecorEmbell
		elif data and Regex.match(data = data, expression = r'(?:landscape|logo|icon|clear[\s\-\_\.]?art)', cache = True): decor = MetaData.ImageDecorEmbell
		elif data and Regex.match(data = data, expression = r'(?:actor|character|photo|thumb|(?:fan|key)[\s\-\_\.]?art)', cache = True): decor = MetaData.ImageDecorPlain
		else:
			try: decor = MetaData.ImageDecorTypes[type if type else self.imageTypeExtract(data = data)]
			except: pass

		MetaData.DataImageDecor[id] = decor
		return decor

	@classmethod
	def imageDecorDefault(self, decor):
		if decor is MetaData.ImageDecorDefault: decor = MetaData.ImageDecorEmbell
		return decor

	###################################################################
	# GENRE
	###################################################################

	def genre(self, media = MediaDefault, selection = SelectionDefault):
		result = self.dataRetrieve(type = 'genre', media = media, selection = selection)
		return result

	def genreSet(self, value, media = MediaDefault):
		if value: self.dataUpdate(data = {'genre' : self.dataList(value)}, media = media)

	@classmethod
	def genreExtract(self, data):
		try: return MetaData.DataGenre[genre]
		except: pass

		provider = MetaData.GenreDefault
		if Regex.match(data = data, expression = r'(?:action)', cache = True): genre = MetaData.GenreAction
		elif Regex.match(data = data, expression = r'(?:sci(?:ence)?[\s\-]*fi(?:ction)?)', cache = True): genre = MetaData.GenreScifi
		elif Regex.match(data = data, expression = r'(?:fantasy)', cache = True): genre = MetaData.GenreFantasy
		elif Regex.match(data = data, expression = r'(?:adventure)', cache = True): genre = MetaData.GenreAdventure
		elif Regex.match(data = data, expression = r'(?:horror)', cache = True): genre = MetaData.GenreHorror
		elif Regex.match(data = data, expression = r'(?:mystery)', cache = True): genre = MetaData.GenreMystery
		elif Regex.match(data = data, expression = r'(?:suspense)', cache = True): genre = MetaData.GenreSuspense
		elif Regex.match(data = data, expression = r'(?:thriller)', cache = True): genre = MetaData.GenreThriller
		elif Regex.match(data = data, expression = r'(?:crime)'): genre = MetaData.GenreCrime
		elif Regex.match(data = data, expression = r'(?:martial|karate|kong[\s\-]*fu)', cache = True): genre = MetaData.GenreMartial
		elif Regex.match(data = data, expression = r'(?:west)', cache = True): genre = MetaData.GenreWestern
		elif Regex.match(data = data, expression = r'(?:war)', cache = True): genre = MetaData.GenreWar
		elif Regex.match(data = data, expression = r'(?:politics)', cache = True): genre = MetaData.GenrePolitics
		elif Regex.match(data = data, expression = r'(?:histor(?:y|ical))', cache = True): genre = MetaData.GenreHistory
		elif Regex.match(data = data, expression = r'(?:comedy)', cache = True): genre = MetaData.GenreComedy
		elif Regex.match(data = data, expression = r'(?:romance|love)', cache = True): genre = MetaData.GenreRomance
		elif Regex.match(data = data, expression = r'(?:drama)', cache = True): genre = MetaData.GenreDrama

		elif Regex.match(data = data, expression = r'(?:family)', cache = True): genre = MetaData.GenreFamily
		elif Regex.match(data = data, expression = r'(?:child)', cache = True): genre = MetaData.GenreChildren
		elif Regex.match(data = data, expression = r'(?:animat(?:ion|ed))', cache = True): genre = MetaData.GenreAnimation
		elif Regex.match(data = data, expression = r'(?:anime)', cache = True): genre = MetaData.GenreAnime
		elif Regex.match(data = data, expression = r'(?:musical)', cache = True): genre = MetaData.GenreMusical
		elif Regex.match(data = data, expression = r'(?:music)', cache = True): genre = MetaData.GenreMusic

		elif Regex.match(data = data, expression = r'(?:docu)', cache = True): genre = MetaData.GenreDocumentary
		elif Regex.match(data = data, expression = r'(?:bio)', cache = True): genre = MetaData.GenreBiography
		elif Regex.match(data = data, expression = r'(?:sporting)', cache = True): genre = MetaData.GenreSporting
		elif Regex.match(data = data, expression = r'(?:sport)', cache = True): genre = MetaData.GenreSport
		elif Regex.match(data = data, expression = r'(?:travel|road|trip)', cache = True): genre = MetaData.GenreTravel
		elif Regex.match(data = data, expression = r'(?:holiday|vacation)', cache = True): genre = MetaData.GenreHoliday
		elif Regex.match(data = data, expression = r'(?:home|garde|living)', cache = True): genre = MetaData.GenreHome
		elif Regex.match(data = data, expression = r'(?:food|cook)', cache = True): genre = MetaData.GenreFood

		elif Regex.match(data = data, expression = r'(?:soap)', cache = True): genre = MetaData.GenreSoap
		elif Regex.match(data = data, expression = r'(?:reality)', cache = True): genre = MetaData.GenreReality
		elif Regex.match(data = data, expression = r'(?:news)', cache = True): genre = MetaData.GenreNews
		elif Regex.match(data = data, expression = r'(?:talk)', cache = True): genre = MetaData.GenreTalk
		elif Regex.match(data = data, expression = r'(?:game)', cache = True): genre = MetaData.GenreGame
		elif Regex.match(data = data, expression = r'(?:award)', cache = True): genre = MetaData.GenreAward
		elif Regex.match(data = data, expression = r'(?:mini)', cache = True): genre = MetaData.GenreMini
		elif Regex.match(data = data, expression = r'(?:pod[\s\-]*cast)', cache = True): genre = MetaData.GenrePodcast
		elif Regex.match(data = data, expression = r'(?:tv|television)', cache = True): genre = MetaData.GenreTelevision

		elif Regex.match(data = data, expression = r'(?:short)', cache = True): genre = MetaData.GenreShort
		elif Regex.match(data = data, expression = r'(?:ind(?:ie|ependent))', cache = True): genre = MetaData.GenreIndie
		elif Regex.match(data = data, expression = r'(?:noir)', cache = True): genre = MetaData.GenreNoir

		MetaData.DataGenre[data] = genre
		return genre

	###################################################################
	# VOTE
	###################################################################

	def vote(self, type, media = MediaDefault):
		result = self.dataRetrieve(type = ['vote', MetaData.VotePercent if type == MetaData.VoteRating else type], media = media)
		if result and type == MetaData.VoteRating: result = result * 10.0
		return result

	def voteAbsolute(self, media = MediaDefault):
		return self.vote(type = MetaData.VoteAbsolute, media = media)

	def voteRating(self, media = MediaDefault):
		return self.vote(type = MetaData.VoteRating, media = media)

	def votePercent(self, media = MediaDefault):
		return self.vote(type = MetaData.VotePercent, media = media)

	def voteCount(self, media = MediaDefault):
		return self.vote(type = MetaData.VoteCount, media = media)

	def voteSet(self, value, type, media = MediaDefault):
		if not value is None:
			if type == MetaData.VoteRating:
				type = MetaData.VotePercent
				value = value / 10.0
			self.dataUpdate(data = {'vote' : {type : value}}, media = media)

	def voteAbsoluteSet(self, value, media = MediaDefault):
		self.voteSet(value = value, type = MetaData.VoteAbsolute, media = media)

	def voteRatingSet(self, value, media = MediaDefault):
		self.voteSet(value = value, type = MetaData.VoteRating, media = media)

	def votePercentSet(self, value, media = MediaDefault):
		self.voteSet(value = value, type = MetaData.VotePercent, media = media)

	def voteCountSet(self, value, media = MediaDefault):
		self.voteSet(value = value, type = MetaData.VoteCount, media = media)

	@classmethod
	def voteDefault(self, value):
		return value if value else 0

	###################################################################
	# STATUS
	###################################################################

	def status(self, media = MediaDefault):
		return self.dataRetrieve(type = 'status', media = media)

	def statusRumored(self, media = MediaDefault):
		return self.status() == MetaData.StatusRumored

	def statusPlanned(self, media = MediaDefault):
		return self.status() == MetaData.StatusPlanned

	def statusPreproduction(self, media = MediaDefault):
		return self.status() == MetaData.StatusPreproduction

	def statusProduction(self, media = MediaDefault):
		return self.status() == MetaData.StatusProduction

	def statusPostproduction(self, media = MediaDefault):
		return self.status() == MetaData.StatusPostproduction

	def statusCompleted(self, media = MediaDefault):
		return self.status() == MetaData.StatusCompleted

	def statusReleased(self, media = MediaDefault):
		return self.status() == MetaData.StatusReleased

	def statusPiloted(self, media = MediaDefault):
		return self.status() == MetaData.StatusPiloted

	def statusUpcoming(self, media = MediaDefault):
		return self.status() == MetaData.StatusUpcoming

	def statusContinuing(self, media = MediaDefault):
		return self.status() == MetaData.StatusContinuing

	def statusEnded(self, media = MediaDefault):
		return self.status() == MetaData.StatusEnded

	def statusCanceled(self, media = MediaDefault):
		return self.status() == MetaData.StatusCanceled

	def statusSet(self, value, media = MediaDefault):
		if value: self.dataUpdate(data = {'status' : value}, media = media)

	@classmethod
	def statusExtract(self, data):
		try: return MetaData.DataStatus[data]
		except: pass

		# TMDb:
		#	Movies: Canceled, In Production, Planned, Post Production, Released, Rumored
		#	Shows: Returning Series, Planned, In Production, Ended, Canceled, Pilot
		# TVDb:
		#	Movies: Announced, Pre-Production, Filming / Post-Production, Completed, Released
		#	Shows: Continuing, Ended, Upcoming
		# Trakt:
		#	Movies: released, in production, post production, planned, rumored, or canceled
		#	Shows: returning series, in production, planned, canceled, ended

		status = MetaData.StatusDefault
		if Regex.match(data = data, expression = r'(?:rumou?r)', cache = True): status = MetaData.StatusRumored
		elif Regex.match(data = data, expression = r'(?:plan)', cache = True): status = MetaData.StatusPlanned
		elif Regex.match(data = data, expression = r'(?:pre.?product)', cache = True): status = MetaData.StatusPreproduction
		elif Regex.match(data = data, expression = r'(?:post.?product)', cache = True): status = MetaData.StatusPostproduction
		elif Regex.match(data = data, expression = r'(?:product|film)', cache = True): status = MetaData.StatusProduction
		elif Regex.match(data = data, expression = r'(?:complet)', cache = True): status = MetaData.StatusCompleted
		elif Regex.match(data = data, expression = r'(?:release)', cache = True): status = MetaData.StatusReleased
		elif Regex.match(data = data, expression = r'(?:pilot|test)', cache = True): status = MetaData.StatusPiloted
		elif Regex.match(data = data, expression = r'(?:upcoming)', cache = True): status = MetaData.StatusUpcoming
		elif Regex.match(data = data, expression = r'(?:contin|busy|running)', cache = True): status = MetaData.StatusContinuing
		elif Regex.match(data = data, expression = r'(?:return)', cache = True): status = MetaData.StatusReturning
		elif Regex.match(data = data, expression = r'(?:end|finish)', cache = True): status = MetaData.StatusEnded
		elif Regex.match(data = data, expression = r'(?:cancel)', cache = True): status = MetaData.StatusCanceled

		MetaData.DataStatus[data] = status
		return status

	###################################################################
	# SPECIAL
	###################################################################

	def special(self, type = None, media = MediaDefault, selection = SelectionDefault):
		return self.dataRetrieve(type = ['special', type] if type else 'special', media = media, selection = selection)

	def specialType(self, media = MediaDefault, selection = SelectionDefault):
		return self.special(type = 'type', media = media, selection = selection)

	def specialStory(self, special = None, media = MediaDefault):
		if special is None: special = self.specialType(media = media, selection = MetaData.SelectionList)
		elif not Tools.isArray(special): special = [special]
		if special: return any(i in MetaData.SpecialStory for i in special)
		return None

	def specialExtra(self, special = None, media = MediaDefault):
		if special is None: special = self.specialType(media = media, selection = MetaData.SelectionList)
		elif not Tools.isArray(special): special = [special]
		if special: return any(i in MetaData.SpecialExtra for i in special)
		return None

	def specialBefore(self, media = MediaDefault, selection = SelectionDefault):
		return self.special(type = 'before', media = media, selection = selection)

	def specialAfter(self, media = MediaDefault, selection = SelectionDefault):
		return self.special(type = 'after', media = media, selection = selection)

	@classmethod
	def specialExtraLegacy(self, special = None, title = None, exclude = None):
		if not special: special = []
		if title:
			extracted = self.specialExtract(data = title, exclude = exclude)
			if extracted: special.extend(extracted)
			special = Tools.listUnique(special)
		if special: return any(i in MetaData.SpecialExtra for i in special)
		return None

	def specialSet(self, value, media = MediaDefault):
		if value: self.dataUpdate(data = {'special' : value}, media = media)

	@classmethod
	def specialExtract(self, data, exclude = None):
		if data:
			special = []
			if exclude and not Tools.isArray(exclude): exclude = [exclude]

			# Eg: The Cost of Genius: Inside The Queen's Gambit
			# Eg: Creating the Queen's Gambit
			if exclude: title = r'(?:%s)' % r'|'.join([Regex.escape(i) for i in exclude])
			else: title = 'xxxxxxxxxxxx'

			expression = (
				(MetaData.SpecialProduction,	(r'((?:inside|creat(?:e|ings?))(?:\s*(?:the|of))*\s%s)' % title, False)),									# Eg: The Queen's Gambit S00E01, S00E02.

				(MetaData.SpecialProduction,	r'(behind[\s\-]*the[\s\-]*(?:scenes?|casts?|shows?|series?|seasons?|drama)|^(?:inside|creat(?:e|ings?)))'),	# Eg: Downton Abbey S00E01. The Queen's Gambit S00E02.
				(MetaData.SpecialBlooper,		r'(bloopers?)'),
				(MetaData.SpecialInterview,		r'(interview(?:s|ed|ing)?|conversation|up[\s\-]close[\s\-]with)'),											# Eg: True Detective S00E03.
				(MetaData.SpecialCrossover,		r'(cross-?over(?:s|ed|ing)?)'),
				(MetaData.SpecialDeleted,		r'(deleted[\s\-]*scenes?)'),
				(MetaData.SpecialMovie,			r'((?:tv[\s\-]*)?movie)'),
				(MetaData.SpecialExtended,		r'(extended[\s\-]*scenes?)'),

				# Update (2025-07): This category has been removed by TVDb and merged with 4447 into "Behind the Scenes/ Makings Of".
				# Use SpecialProduction instead, to ensure consistency with specials marked with the taxonomy ID, which are not extracted by title.
				# Eg: The Witcher S00E01 (Behind ID) vs S00E02-09 (No ID, but titles include "a look inside").
				#(MetaData.SpecialMaking,		r'(making[\s\-](?:of|the|an?)|^making|look[\s\-]inside)'),													# Eg: True Detective S00E01, S00E04, S00E05.
				(MetaData.SpecialProduction,	r'(making[\s\-](?:of|the|an?)|^making|look[\s\-]inside)'),													# Eg: The Witcher S00E01 vs S00E02-09.

				(MetaData.SpecialOriginal,		r'(ova|original[\s\-]*video[\s\-]*animations?)'),
				(MetaData.SpecialPilot,			r'((?:un)?(?:aired|released)[\s\-]*pilot|pilot(?:[\s\-]*episode)?)'),										# Eg: Sherlock S00E01.
				(MetaData.SpecialRecap,			r'((?:(?:show|series|season)[\s\-]*)?recap|story[\s\-]so[\s\-]far|^(?:a|the)?\s*count\-?down)'),				# Eg: Heroes S00E56.
				(MetaData.SpecialShort,			r'(short(?:[\s\-]*episode)?|webisode|webinar)'),
				(MetaData.SpecialPodcast,		r'((?:pod|vod|mob|god|web)cast(?:ed|ing)?|vlog)'), 															# Eg: Last of Us S00E02, S00E06, S00E07, etc.
				(MetaData.SpecialUnimportant,	r'(best[\s\-]*of|rewind|concert|pre[\s\-]*show|comic[\s\-]*relief|awards?|celebrates?|batfa)'),				# Eg: Doctor Who S00E37, S00E40, S00E41, S00E50, S00E76, S00E128. Downton Abbey S00E16, S00E17.

				# Do this after Unimportant. Eg: "Best of the Christmas Specials"
				(MetaData.SpecialEpisode,		r'((?:christmas|holiday)[\s\-]*specials?|episode)'),															# Eg: The Office UK S00E01, S00E02.

				(MetaData.SpecialEpisode,		r'^\s*(?:(?:(?:e|é|e\?)pis(?:o|ó|o\?)(?:des?|d?ios?)|part|folge|teil|aflevering|deel)[\s\-\_\.]*(?:(?:\d{2}[\-\_\.]){2}\d{4}|\d{4}(?:[\-\_\.]\d{2}){2}|(?:\#\s?)?\d+(?:\.\d+)?(?:$|[^\d])|[ivxlcd]+(?:$|[^\da-z]))|(?:(?:\d{2}[\-\_\.]){2}\d{4}|\d{4}(?:[\-\_\.]\d{2}){2}))[\s\:\-]*'),																						# Eg: Money Heist (entire S00 is a season with full episodes).
			)

			for key, value in expression:
				excluded = True
				if Tools.isArray(value):
					excluded = value[1]
					value = value[0]

				value += r'(?:$|[\s\,\.\!\?\:\-])'
				if Regex.match(data = data, expression = value):
					ignore = False
					if excluded and exclude:
						for j in exclude:
							if Regex.match(data = j, expression = value):
								ignore = True
								break
					if key in MetaData.SpecialStory and any(i in MetaData.SpecialExtra for i in special): ignore = True # Eg: "Best of the Christmas Specials" (containing both "Best of" and "Christmas Specials")
					if not ignore: special.append(key)

			if special: return Tools.listUnique(special)
		return MetaData.SpecialDefault

	###################################################################
	# DURATION
	###################################################################

	def duration(self, type = DurationDefault, media = MediaDefault):
		result = self.dataRetrieve(type = 'duration', media = media)
		if result:
			if type == MetaData.DurationMinutes: result = result / 60.0
			elif type == MetaData.DurationHours: result = result / 3600.0
		return result

	def durationSeconds(self, media = MediaDefault):
		return self.duration(type = MetaData.DurationSeconds, media = media)

	def durationMinutes(self, media = MediaDefault):
		return self.duration(type = MetaData.DurationMinutes, media = media)

	def durationHours(self, media = MediaDefault):
		return self.duration(type = MetaData.DurationHours, media = media)

	def durationSet(self, value, type = DurationDefault, media = MediaDefault):
		if not value is None:
			if type == MetaData.DurationMinutes: value = value * 60.0
			elif type == MetaData.DurationHours: value = value * 3600.0
			value = int(value)
			self.dataUpdate(data = {'duration' : value}, media = media)

	def durationSecondsSet(self, value, type = DurationDefault, media = MediaDefault):
		self.durationSet(value = value, type = MetaData.DurationSeconds, media = media)

	def durationMinutesSet(self, value, type = DurationDefault, media = MediaDefault):
		self.durationSet(value = value, type = MetaData.DurationMinutes, media = media)

	def durationHoursSet(self, value, type = DurationDefault, media = MediaDefault):
		self.durationSet(value = value, type = MetaData.DurationHours, media = media)

	###################################################################
	# RELEASE - DATE
	###################################################################

	def releaseDate(self, type = None, zone = ZoneDefault, format = FormatDefault, media = MediaDefault):
		types = ['release', 'date']
		if type: types.append(type)
		result = self.dataRetrieve(type = types, media = media)
		if result and (zone or format):
			offset = self.releaseZoneOffsetDefault(zone = zone)
			if format is MetaData.FormatDefault: format = MetaData.FormatDate
			converter = ConverterTime(result, offset = MetaData.ZoneUtc)
			if format and not format == MetaData.FormatTimestamp: result = converter.string(format = format, offset = offset)
			else: result = converter.timestamp(offset = offset)
		return result

	def releaseDateFirst(self, zone = ZoneDefault, format = FormatDefault, media = MediaDefault):
		return self.releaseDate(type = 'first', zone = zone, format = format, media = media)

	def releaseDateLast(self, zone = ZoneDefault, format = FormatDefault, media = MediaDefault):
		return self.releaseDate(type = 'last', zone = zone, format = format, media = media)

	def releaseDateNext(self, zone = ZoneDefault, format = FormatDefault, media = MediaDefault):
		return self.releaseDate(type = 'next', zone = zone, format = format, media = media)

	def releaseDateSet(self, value, type = None, zone = ZoneDefault, media = MediaDefault):
		if value:
			if not Tools.isInteger(value):
				if '-00' in value:
					value = None
				else:
					offset = self.releaseZoneOffsetDefault(zone = zone)
					if not ':' in value:
						time = self.releaseTime(zone = zone, format = MetaData.FormatTime)
						if time: value += ' ' + time
					value = ConverterTime(value, offset = offset).timestamp(offset = MetaData.ZoneUtc)
			if value:
				if type: value = {type : value}
				self.dataUpdate(data = {'release' : {'date' : value}}, media = media)

	def releaseDateFirstSet(self, value, zone = ZoneDefault, media = MediaDefault):
		self.releaseDateSet(value = value, type = 'first', zone = zone, media = media)

	def releaseDateLastSet(self, value, zone = ZoneDefault, media = MediaDefault):
		self.releaseDateSet(value = value, type = 'last', zone = zone, media = media)

	def releaseDateNextSet(self, value, zone = ZoneDefault, media = MediaDefault):
		self.releaseDateSet(value = value, type = 'next', zone = zone, media = media)

	###################################################################
	# RELEASE - TIME
	###################################################################

	def releaseTime(self, zone = ZoneDefault, format = FormatDefault, media = MediaDefault):
		result = self.dataRetrieve(type = ['release', 'time'], media = media)
		if result and (zone or format):
			offset = self.releaseZoneOffsetDefault(zone = zone)
			if format is MetaData.FormatDefault: format = MetaData.FormatTime
			base = ConverterTime('2020-05-15 00:00:00', offset = MetaData.ZoneUtc).timestamp()
			converter = ConverterTime(result + base, offset = MetaData.ZoneUtc)
			if format and not format == MetaData.FormatTimestamp: result = converter.string(format = format, offset = offset)
			else: result = converter.timestamp(offset = offset) - base
		return result

	def releaseTimeSet(self, value, zone = ZoneDefault, media = MediaDefault):
		if value:
			if not Tools.isInteger(value):
				value = value.replace('24:', '00:') # Sometimes TVDb has a time like 24:30.
				date = '2020-05-15 '
				offset = self.releaseZoneOffsetDefault(zone = zone)
				try:
					value = ConverterTime(date + value, offset = offset).timestamp() - ConverterTime(date + '00:00').timestamp()
				except:
					Logger.error(message = '%s (%s : %s)' % (str(value), str(zone), str(offset)))
					return
			self.dataUpdate(data = {'release' : {'time' : value}}, media = media)

	###################################################################
	# RELEASE - DAY
	###################################################################

	def releaseDay(self, media = MediaDefault, selection = SelectionDefault):
		return self.dataRetrieve(type = ['release', 'day'], media = media, selection = selection)

	def releaseDaySet(self, value, media = MediaDefault):
		if value: self.dataUpdate(data = {'release' : {'day' : self.dataList(value)}}, media = media)

	@classmethod
	def releaseDayExtract(self, data):
		try: return MetaData.DataDay[data]
		except: pass

		day = MetaData.DayDefault
		if Regex.match(data = data, expression = r'mon', cache = True): day = MetaData.DayMonday
		elif Regex.match(data = data, expression = r'tue', cache = True): day = MetaData.DayTuesday
		elif Regex.match(data = data, expression = r'wed', cache = True): day = MetaData.DayWednesday
		elif Regex.match(data = data, expression = r'thu', cache = True): day = MetaData.DayThursday
		elif Regex.match(data = data, expression = r'fri', cache = True): day = MetaData.DayFriday
		elif Regex.match(data = data, expression = r'sat', cache = True): day = MetaData.DaySaturday
		elif Regex.match(data = data, expression = r'sun', cache = True): day = MetaData.DaySunday

		MetaData.DataDay[data] = day
		return day

	###################################################################
	# RELEASE - COUNTRY
	###################################################################

	def releaseCountry(self, media = MediaDefault):
		return self.dataRetrieve(type = ['release', 'country'], media = media)

	def releaseCountrySet(self, value, media = MediaDefault):
		if value: self.dataUpdate(data = {'release' : {'country' : value}}, media = media)

	@classmethod
	def releaseCountryExtract(self, data):
		try: return MetaData.DataCountry[data]
		except: pass
		country = Country.code(data)
		MetaData.DataCountry[data] = country
		return country

	###################################################################
	# RELEASE - ZONE
	###################################################################

	def releaseZoneName(self, media = MediaDefault, fallback = FallbackDefault):
		result = self.dataRetrieve(type = ['release', 'zone'], media = media)
		if not result and fallback:
			country = self.country(media = media)
			if country: result = Country.zone(country)
		return result

	def releaseZoneOffset(self, media = MediaDefault, fallback = FallbackDefault):
		return Time.offset(zone = self.releaseZoneName())

	def releaseZoneSeconds(self, media = MediaDefault, fallback = FallbackDefault):
		return ConverterTime.offset(self.releaseZoneOffset(media = media, fallback = fallback))

	def releaseZoneSet(self, value, media = MediaDefault):
		if value: self.dataUpdate(data = {'release' : {'zone' : value}}, media = media)

	def releaseZoneOffsetDefault(self, zone, default = FallbackDefault):
		offset = None
		if not zone: zone = self.releaseZoneName()

		if zone == MetaData.ZoneOriginal: offset = self.releaseZoneOffset()
		elif zone == MetaData.ZoneLocal: offset = Time.offset()
		elif zone: offset = Time.offset(zone)

		return offset

	###################################################################
	# MONEY
	###################################################################

	def moneyBudget(self, media = MediaDefault):
		return self.dataRetrieve(type = ['money', 'budget'], media = media)

	def moneyIncome(self, media = MediaDefault):
		return self.dataRetrieve(type = ['money', 'income'], media = media)

	def moneyProfit(self, media = MediaDefault):
		try: return self.moneyIncome(media = media) - self.moneyBudget(media = media)
		except: return None

	def moneyBudgetSet(self, value, media = MediaDefault):
		if value: self.dataUpdate(data = {'money' : {'budget' : value}}, media = media)

	def moneyIncomeSet(self, value, media = MediaDefault):
		if value: self.dataUpdate(data = {'money' : {'income' : value}}, media = media)

	###################################################################
	# CERTIFICATE
	###################################################################

	def certificate(self, country = CountryDefault, media = MediaDefault, selection = SelectionDefault, fallback = FallbackDefault):
		country = self.countryDefault(country = country)

		result = None
		subdata = self.dataRetrieve(type = 'certificate', media = media)
		if subdata:
			result = self.dataRetrieve(attribute = {'country' : country}, selection = selection, media = False, metadata = subdata)
			if not result:
				fallback = self.fallbackDefault(fallback = fallback)
				if fallback: result = self.dataRetrieve(selection = selection, media = False, metadata = subdata)

		return result

	def certificateCode(self, country = CountryDefault, media = MediaDefault, selection = SelectionDefault, fallback = FallbackDefault):
		result = self.certificate(country = country, media = media, selection = selection, fallback = fallback)
		if result:
			if Tools.isDictionary(result): return result['code']
			else: return [i['code'] for i in result]
		return None

	def certificateSet(self, value, name = Default, description = Default, country = CountryDefault, media = MediaDefault):
		if value:
			if not Tools.isStructure(value):
				value = {
					'code' : value,
					'name' : name,
					'description' : description,
					'media' : self.mediaDefault(media = media),
					'country' : self.countryDefault(country = country),
				}
			self.dataUpdate(data = {'certificate' : self.dataList(value)}, media = media)


class MetaWrap(MetaData):

	###################################################################
	# CONSTRUCTOR
	###################################################################

	def __init__(self):
		MetaData.__init__(self)
		self.mData = {}
		self.mProviders = []

	###################################################################
	# DATA
	###################################################################

	def dataRetrieve(self, type = None, attribute = None, unique = False, sort = None, order = MetaData.OrderDefault, extract = None, media = MetaData.MediaDefault, flatten = MetaData.SelectionSingle, selection = MetaData.SelectionDefault, metadata = None):
		for provider in self.providers():
			if metadata is None: metadata = self.metadata(provider = provider)
			if not metadata is None:
				result = MetaData.dataRetrieve(self, type = type, attribute = attribute, unique = unique, sort = sort, order = order, extract = extract, media = media, flatten = flatten, selection = selection, metadata = metadata)
				if not result is None: return result
		return None

	def dataUpdate(self, data, media = False, unique = True, structure = None):
		MetaData.dataUpdate(self, data = data, media = media, unique = unique, metadata = self.metadata())

	@classmethod
	def dataCreate(self, media, data):
		metawrap = MetaWrap()
		metawrap.dataImport(data = data)
		return metawrap

	def dataExportBefore(self):
		items = {}
		for provider, metadata in self.mData.items():
			items[provider] = metadata
			self.mData[provider] = metadata.dataExport()
		return items

	def dataExportAfter(self, data):
		for provider, metadata in data.items():
			self.mData[provider] = metadata

	def dataImportBefore(self, data = None):
		try:
			for provider, metadata in data.items():
				data[provider] = metadata.dataImport(data = metadata)
		except: pass
		return data

	def dataImportAfter(self, data = None):
		MetaData.dataImportAfter(self, data = data)
		self.providersUpdate()

	###################################################################
	# PROVIDER
	###################################################################

	def providers(self):
		return self.mProviders

	def providerDefault(self, provider):
		if provider is MetaData.ProviderDefault:
			try: return self.providers()[0]
			except: pass
		return provider

	def providersUpdate(self):
		self.mProviders = list(self.mData.keys())

	###################################################################
	# METADATA
	###################################################################

	def metadata(self, provider = MetaData.ProviderDefault):
		try: return self.mData[self.providerDefault(provider = provider)]
		except: return None

	def metadataSet(self, value, provider = MetaData.ProviderDefault):
		if not value is None:
			provider = self.providerDefault(provider = provider)
			if provider:
				self.mData[provider] = value
				self.providersUpdate()

	###################################################################
	# MEDIA
	###################################################################

	# Because there is a separate media variable.
	def media(self):
		return self.metadata().media()
