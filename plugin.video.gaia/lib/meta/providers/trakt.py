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

'''
	SUPPORTED MEDIA

	SET
		Limited support.
		Retrieves official Trakt lists together with the "collection" keyword.
			Trakt does not have separate API endpoints for sets.
			Instead, Trakt uses normal lists, officially maintained by Trakt admins, to simulate sets.
			Eg: On top of the page it states "Pirates of the Caribbean Collection":
				https://trakt.tv/movies/pirates-of-the-caribbean-dead-men-tell-no-tales-2017
				https://trakt.tv/lists/official/pirates-of-the-caribbean-collection?sort=rank,asc

	MINI
		No support.
		Trakt has a "mini-series" genre, but no show is labeled with this genre.

	--------------------------------------------------------------------------------------------------------------

	SUPPORTED RESULTS

		LEVEL-0
			The request is nativley supported by Trakt.
			The number of results returned is the same as the limit requested.
			No additional request parameters are set (keywords, genre, duration).
			Eg: MovieFeatureTheater
		LEVEL-1
			The request is somewhat nativley supported by Trakt.
			The number of results returned is moslty the same as the limit requested, but not always.
			These requests typically add a genre and/or duration.
			Sometimes includes titles that are not exactly what was requested (eg returns short TV movies/specials for short films).
			Eg: MovieShortTheater
		LEVEL-2
			The request is not nativley supported by Trakt.
			The number of results returned is mostly not the same as the limit requested.
			These requests typically add keywords to the query and locally filter the returned results by genre and duration.
			Eg: MovieSpecialTelevision
		LEVEL-3
			The request is not nativley or otherwise supported by Trakt, typically because the API endpoint does not support filtering.
			The number of results returned is mostly not the same as the limit requested, and can even return no results.
			These requests retrieve all available results and only do local post-request filtering.
		LEVEL-4
			The request currently does not work at all.
			The API docs list specific features/attributes that do not seem to be supported in the live API.
			The code is still left here, since this feature might start working in the future.
			Eg: The docs state that episodes can be of type "mid_season_premiere", but not episode seems to be labeled as such (although "mid_season_finale" works).

'''

from lib.modules.tools import Media, Logger, Tools, Media, Audience, Regex, Time, Converter, Math, Country, Language, System
from lib.modules.network import Networker
from lib.modules.cache import Cache, Memory
from lib.modules.concurrency import Pool
from lib.modules import trakt as Core
from lib.meta.provider import MetaProvider
from lib.meta.tools import MetaTools
from lib.meta.image import MetaImage

class MetaTrakt(MetaProvider):

	# TYPE

	TypeMovie				= 'movie'
	TypeShow				= 'show'
	TypeSeason				= 'season'
	TypeEpisode				= 'episode'
	TypePerson				= 'person'
	TypeStudio				= 'studio'
	TypeList				= 'list'

	# Not part of the official Trakt types.
	TypeSummary				= 'summary'
	TypeRelease				= 'release'
	TypeTranslation			= 'translation'
	TypeAlias				= 'alias'
	TypeRating				= 'rating'

	# CATEGORY

	CategoryAll				= 'all'
	CategoryUser			= 'my'
	CategoryMovie			= 'movies'
	CategoryShow			= 'shows'
	CategorySeason			= 'seasons'
	CategoryEpisode			= 'episodes'
	CategoryPerson			= 'people'
	CategoryStudio			= 'studios'
	CategoryList			= 'lists'

	# LINK

	LinkWeb					= 'https://trakt.tv'
	LinkApi					= 'https://api.trakt.tv'

	LinkDiscover			= '{category}/{sort}/{period}'
	LinkRecommendation		= 'recommendations/{category}'

	LinkSearch				= 'search'
	LinkSearchQuery			= LinkSearch + '/{type}'
	LinkSearchId			= LinkSearch + '/{provider}/{id}'

	LinkPerson				= 'people/{id}'
	LinkPersonFilmography	= LinkPerson + '/{category}'

	LinkDetailSummary		= '{category}/{id}'
	LinkDetailPerson		= LinkDetailSummary + '/people'
	LinkDetailStudio		= LinkDetailSummary + '/studios'
	LinkDetailTranslation	= LinkDetailSummary + '/translations/{language}'
	LinkDetailAlias			= LinkDetailSummary + '/aliases'
	LinkDetailList			= LinkDetailSummary + '/lists/{list}/{sort}'
	LinkDetailRelease		= LinkDetailSummary + '/releases/{country}'
	LinkDetailRating		= LinkDetailSummary + '/ratings'

	LinkMovieSummary		= LinkDetailSummary
	LinkMoviePerson			= LinkDetailPerson
	LinkMovieStudio			= LinkDetailStudio
	LinkMovieTranslation	= LinkDetailTranslation
	LinkMovieAlias			= LinkDetailAlias
	LinkMovieList			= LinkDetailList
	LinkMovieRelease		= LinkDetailRelease
	LinkMovieRating			= LinkDetailRating

	LinkShowSummary			= LinkDetailSummary
	LinkShowPerson			= LinkDetailPerson
	LinkShowStudio			= LinkDetailStudio
	LinkShowTranslation		= LinkDetailTranslation
	LinkShowAlias			= LinkDetailAlias
	LinkShowList			= LinkDetailList
	LinkShowRating			= LinkDetailRating

	LinkSeasonSummary		= 'shows/{id}/seasons/{season}'
	LinkSeasonPerson		= LinkSeasonSummary + '/people'
	LinkSeasonTranslation	= LinkSeasonSummary + '/translations/{language}'
	LinkSeasonRating		= LinkSeasonSummary + '/ratings'

	LinkEpisodeSummary		= LinkSeasonSummary + '/episodes/{episode}'
	LinkEpisodePerson		= LinkEpisodeSummary + '/people'
	LinkEpisodeTranslation	= LinkEpisodeSummary + '/translations/{language}'
	LinkEpisodeRating		= LinkEpisodeSummary + '/ratings'

	LinkRelease				= 'calendars/{mode}'
	LinkReleaseMain			= LinkRelease + '/{calendar}/{date}/{days}'
	LinkReleaseGroup		= LinkRelease + '/{category}/{calendar}/{date}/{days}'

	LinkUser				= 'users/{user}'
	LinkUserLists			= LinkUser + '/lists'
	LinkUserListsLike		= LinkUser + '/likes/lists'
	LinkUserListsComment	= LinkUser + '/comments/all/lists'
	LinkUserListsCollaboration	= LinkUserLists + '/collaborations'
	LinkUserList			= LinkUserLists + '/{id}'
	LinkUserListItem		= LinkUserList + '/items/{type}'
	LinkUserHistory			= LinkUser + '/history/{category}'
	LinkUserWatched			= LinkUser + '/watched/{category}'
	LinkUserCollection		= LinkUser + '/collection/{category}'
	LinkUserRating			= LinkUser + '/ratings/{category}/{rating}'
	LinkUserFavorite		= LinkUser + '/favorites/{category}/{sort}'
	LinkUserWatchlist		= LinkUser + '/watchlist/{category}/{sort}'
	LinkUserHidden			= 'users/hidden/{section}?type={type}'
	LinkUserProgress		= 'sync/playback/{category}'

	LinkList				= 'lists/{id}'
	LinkListItem			= LinkList + '/items/{type}'
	LinkListPopular			= 'lists/popular'
	LinkListTrending		= 'lists/trending'

	LinkWebMovie			= 'movies/{id}'
	LinkWebShow				= 'shows/{id}'
	LinkWebSeason			= LinkWebShow + '/seasons/{season}'
	LinkWebEpisode			= LinkWebSeason + '/episodes/{episode}'
	LinkWebPerson			= 'people/{id}'
	LinkWebList				= 'lists/{list}/{id}'

	LinkWebSearch			= 'search?query={query}'
	LinkWebSearchMovie		= 'search/movies?query={query}'
	LinkWebSearchShow		= 'search/shows?query={query}'
	LinkWebSearchEpisode	= 'search/episodes?query={query}'
	LinkWebSearchPerson		= 'search/people?query={query}'
	LinkWebSearchList		= 'search/lists?query={query}'
	LinkWebSearchUser		= 'search/users?query={query}'

	LinkWebUser				= 'users/{user}'
	LinkWebUserList			= LinkWebUser + '/lists/{id}'
	LinkWebUserHistory		= LinkWebUser + '/history'
	LinkWebUserProgress		= LinkWebUser + '/progress'
	LinkWebUserCollection	= LinkWebUser + '/collection'
	LinkWebUserRating		= LinkWebUser + '/ratings'
	LinkWebUserFavorite		= LinkWebUser + '/favorites'
	LinkWebUserWatchlist	= LinkWebUser + '/watchlist'

	# GENRE
	# https://api.trakt.tv/genres/movies
	# https://api.trakt.tv/genres/shows

	GenreNone				= 'none'				# Movies, Shows
	GenreAction				= 'action'				# Movies, Shows
	GenreAdventure			= 'adventure'			# Movies, Shows
	GenreAnimation			= 'animation'			# Movies, Shows
	GenreAnime				= 'anime'				# Movies, Shows
	GenreBiography			= 'biography'			# Shows
	GenreChildren			= 'children'			# Shows
	GenreComedy				= 'comedy'				# Movies, Shows
	GenreCrime				= 'crime'				# Movies, Shows
	GenreDocumentary		= 'documentary'			# Movies, Shows
	GenreDonghua			= 'donghua'				# Movies, Shows
	GenreDrama				= 'drama'				# Movies, Shows
	GenreFamily				= 'family'				# Movies, Shows
	GenreFantasy			= 'fantasy'				# Movies, Shows
	GenreGame				= 'game-show'			# Shows
	GenreHistory			= 'history'				# Movies, Shows
	GenreHoliday			= 'holiday'				# Movies, Shows
	GenreHome				= 'home-and-garden'		# Shows
	GenreHorror				= 'horror'				# Movies, Shows
	GenreMini				= 'mini-series'			# Shows (listed by Trakt as a show genre, but no shows actually labelled as such)
	GenreMusic				= 'music'				# Movies, Shows
	GenreMusical			= 'musical'				# Movies, Shows
	GenreMystery			= 'mystery'				# Movies, Shows
	GenreNews				= 'news'				# Shows
	GenreReality			= 'reality'				# Shows
	GenreRomance			= 'romance'				# Movies, Shows
	GenreScifi				= 'science-fiction'		# Movies, Shows
	GenreShort				= 'short'				# Movies, Shows (many short films are not labelled with the short genre, filter by duration instead)
	GenreSoap				= 'soap'				# Shows
	GenreSpecial			= 'special-interest'	# Shows
	GenreSporting			= 'sporting-event'		# Movies, Shows
	GenreSport				= 'sports'				# Not returned by the API genre endpoint, but listed in the API docs examples. A few titles are still listed under this genre.
	GenreSuperhero			= 'superhero'			# Movies, Shows
	GenreSuspense			= 'suspense'			# Movies, Shows
	GenreTalk				= 'talk-show'			# Shows
	GenreThriller			= 'thriller'			# Movies, Shows
	GenreWar				= 'war'					# Movies, Shows
	GenreWestern			= 'western'				# Movies, Shows

	Genres 					= {
								MetaTools.GenreNone			: GenreNone,
								MetaTools.GenreAction		: GenreAction,
								MetaTools.GenreAdventure	: GenreAdventure,
								MetaTools.GenreAnimation	: GenreAnimation,
								MetaTools.GenreAnime		: GenreAnime,
								MetaTools.GenreBiography	: GenreBiography,
								MetaTools.GenreChildren		: GenreChildren,
								MetaTools.GenreComedy		: GenreComedy,
								MetaTools.GenreCrime		: GenreCrime,
								MetaTools.GenreDocumentary	: GenreDocumentary,
								MetaTools.GenreDonghua		: GenreDonghua,
								MetaTools.GenreDrama		: GenreDrama,
								MetaTools.GenreFamily		: GenreFamily,
								MetaTools.GenreFantasy		: GenreFantasy,
								MetaTools.GenreHistory		: GenreHistory,
								MetaTools.GenreHorror		: GenreHorror,
								MetaTools.GenreMusic		: GenreMusic,
								MetaTools.GenreMusical		: GenreMusical,
								MetaTools.GenreMystery		: GenreMystery,
								MetaTools.GenreRomance		: GenreRomance,
								MetaTools.GenreScifi		: GenreScifi,
								MetaTools.GenreSuperhero	: GenreSuperhero,
								MetaTools.GenreSuspense		: GenreSuspense,
								MetaTools.GenreThriller		: GenreThriller,
								MetaTools.GenreWar			: GenreWar,
								MetaTools.GenreWestern		: GenreWestern,
								MetaTools.GenreNews			: GenreNews,
								MetaTools.GenreSport		: GenreSport,
								MetaTools.GenreSporting		: GenreSporting,
								MetaTools.GenreHoliday		: GenreHoliday,
								MetaTools.GenreHome			: GenreHome,
								MetaTools.GenreTalk			: GenreTalk,
								MetaTools.GenreGame			: GenreGame,
								MetaTools.GenreReality		: GenreReality,
								MetaTools.GenreSoap			: GenreSoap,
								MetaTools.GenreShort		: GenreShort,
								MetaTools.GenreMini			: GenreMini,
								MetaTools.GenreSpecial		: GenreSpecial,
							}

	# COMPANY

	Companies				= None

	# PERIOD

	PeriodAll				= 'all'
	PeriodYearly			= 'yearly'
	PeriodMonthly			= 'monthly'
	PeriodWeekly			= 'weekly'
	PeriodDaily				= 'daily'
	PeriodDefault			= PeriodAll

	# STATUS
	# According to the API docs, seem to contain spaces.

	StatusRumored			= 'rumored'				# Movies
	StatusPlanned			= 'planned'				# Movies, Shows
	StatusProduction		= 'in production'		# Movies, Shows
	StatusPostproduction	= 'post production'		# Movies
	StatusReleased			= 'released'			# Movies
	StatusUpcoming			= 'upcoming'			# Shows
	StatusPilot				= 'pilot'				# Shows
	StatusContinuing		= 'continuing'			# Shows
	StatusReturning			= 'returning series'	# Shows
	StatusEnded				= 'ended'				# Shows
	StatusCanceled			= 'canceled'			# Movies, Shows
	StatusAvailable			= [StatusReleased, StatusPilot, StatusContinuing, StatusReturning, StatusEnded, StatusCanceled]
	StatusUnavailable		= [StatusRumored, StatusPlanned, StatusProduction, StatusPostproduction, StatusUpcoming]

	Status 					= {
								MetaTools.StatusRumored			: StatusRumored,
								MetaTools.StatusPlanned			: StatusPlanned,
								MetaTools.StatusProduction		: StatusProduction,
								MetaTools.StatusPostproduction	: StatusPostproduction,
								MetaTools.StatusReleased		: StatusReleased,
								MetaTools.StatusUpcoming		: StatusUpcoming,
								MetaTools.StatusPiloted			: StatusPilot,
								MetaTools.StatusContinuing		: StatusContinuing,
								MetaTools.StatusReturning		: StatusReturning,
								MetaTools.StatusEnded			: StatusEnded,
								MetaTools.StatusCanceled		: StatusCanceled,
							}

	# IMAGE

	ImagePoster				= 'poster'		# Movie, Show, Season
	ImageFanart				= 'fanart'		# Movie, Show, Person (not documented, but often returned)
	ImageBanner				= 'banner'		# Movie, Show, Season
	ImageLogo				= 'logo'		# Movie, Show
	ImageClearart			= 'clearart'	# Movie, Show
	ImageThumb				= 'thumb'		# Movie, Show, Season
	ImageScreenshot			= 'screenshot'	# Episode
	ImageHeadshot			= 'headshot'	# Person
	ImageCharacter			= 'character'	# Person

	Images 					= {
								ImagePoster		: MetaImage.TypePoster,
								ImageFanart		: MetaImage.TypeFanart,
								ImageBanner		: MetaImage.TypeBanner,
								ImageLogo		: MetaImage.TypeClearlogo,
								ImageClearart	: MetaImage.TypeClearart,
								ImageThumb		: MetaImage.TypeThumb,
								ImageScreenshot	: MetaImage.TypeThumb,
								ImageHeadshot	: MetaImage.TypePhoto,
								ImageCharacter	: MetaImage.TypePhoto,
							}

	# RELEASE

	ReleasePremiere			= 'premiere'
	ReleaseLimited			= 'limited'
	ReleaseTheatrical		= 'theatrical'
	ReleaseDigital			= 'digital'
	ReleasePhysical			= 'physical'
	ReleaseTelevision		= 'tv'
	ReleaseUnknown			= 'unknown'

	# CALENDAR

	CalendarNew				= 'new'					# New shows airing (EpisodePremiereShow).
	CalendarPremiere		= 'premieres'			# New seasons airing (EpisodePremiereShow/EpisodePremiereSeason/EpisodePremiereMiddle).
	CalendarShow			= 'shows'				# All shows with and episode airing.
	CalendarFinale			= 'finales'				# Show finales airing (EpisodeFinaleShow/EpisodeFinaleSeason/EpisodeFinaleMiddle).
	CalendarMovie			= 'movies'				# All movies released.
	CalendarDvd				= 'dvd'					# All movies with a home release Trakt states "DVD" releases, but this probably also includes digital releases, since the movies/id/releases endpoint states all release dates come from TMDb.
	CalendarStreaming		= 'streaming'			# All movies with a digitial release. This seems to be a new API endpoint (2025-09).

	# EPISODE
	# Many shows are not labeled at all with mid season premieres/finales: https://trakt.tv/shows/vikings/seasons/5
	# Other shows only have the mid season finale labled, but not the next episode as the new mid season premiere: https://trakt.tv/shows/family-guy/seasons/22
	# It seems that there are no mid season premieres at all over a long time period, so it is probably not supported or not used yet.

	EpisodeStandard			= 'standard'			# Any episode not part of the any of the types below.
	EpisodePremiereShow		= 'series_premiere'		# New shows with the first episode of the show aired.
	EpisodePremiereSeason	= 'season_premiere'		# New seasons with the first episode of the season aired.
	EpisodePremiereMiddle	= 'mid_season_premiere'	# New episode in the middle of a split season aired (eg: Vikings S05 | S05E10 24-01-2018 | S05E11 28-11-2018).
	EpisodeFinaleShow		= 'series_finale'		# Last episode of an ended show aired.
	EpisodeFinaleSeason		= 'season_finale'		# Last episode of an ended season aired.
	EpisodeFinaleMiddle		= 'mid_season_finale'	# Last episode in the middle of a split season aired (eg: Vikings S05 | S05E10 24-01-2018 | S05E11 28-11-2018).

	# GENDER

	GenderMale				= 'male'
	GenderFemale			= 'female'
	GenderNonbinary			= 'non_binary'

	# DIVISION

	DivisionCast			= 'cast'
	DivisionCrew			= 'crew'
	DivisionGuest			= 'guest_stars'		# When retrieving guest stars in detail(). Is converted to DivisionCast.

	# DEPARTMENT

	DepartmentActing		= 'acting'			# Not official department.
	DepartmentCrew			= 'crew'			# Other type of crew member.
	DepartmentCreating		= 'created by'		# Only for shows.
	DepartmentDirecting		= 'directing'
	DepartmentWriting		= 'writing'
	DepartmentEditing		= 'editing'
	DepartmentProducing		= 'production'
	DepartmentCamera		= 'camera'
	DepartmentSound			= 'sound'
	DepartmentVisual		= 'visual effects'
	DepartmentLighting		= 'lighting'
	DepartmentArt			= 'art'
	DepartmentCostume		= 'costume & make-up'

	# JOB
	# Many more possible values. Not explicitly stated in the Trakt docs.

	JobActor				= 'actor'
	JobCreator				= 'creator'

	# Trakt (sometimes) orders directors according to importance, in the order given below.
	JobDirector				= 'director'
	JobDirectorUnit			= 'second unit director'
	JobDirectorAssistant	= 'assistant director'
	JobDirectorAssistant1	= 'first assistant director'
	JobDirectorAssistant2	= 'second assistant director'
	JobDirectorAssistant3	= 'third assistant director'
	JobDirectorAdditional	= 'additional assistant director'
	JobDirectorAdditional1	= 'additional first assistant director'
	JobDirectorAdditional2	= 'additional second assistant director'
	JobDirectorAdditional3	= 'additional third assistant director'
	JobDirectorScript		= 'script supervisor'
	JobDirectorContinuity	= 'continuity'

	# Trakt (sometimes) orders writers according to importance, in the order given below.
	JobWriterNovel			= 'novel'				# Novel writer.
	JobWriter				= 'writer'				# General writer.
	JobWriterScreenplay		= 'screenplay'			# Screenplay writer.
	JobWriterStory			= 'story'				# Story writer.
	JobWriterCharacter		= 'characters'			# Character writer.

	# ROLE

	RoleStar				= 'star'				# Star actor.
	RoleGuest				= 'guest'				# Guest actor.

	# WATCH
	# Not officially documented in the API docs.
	# But these parameters exist on the website Movie Calendar.
	# Individual streaming service slugs can also be used.

	WatchAny				= 'any'			# Any streaming services.
	WatchFree				= 'free'		# Free streaming services.
	WatchDvd				= 'dvd'			# DVD release.

	# LIST

	ListAll					= 'all'					# All lists.
	ListOfficial			= 'official'			# Official list maintained by Trakt.
	ListPersonal			= 'personal'			# Custom list maintained by a user.
	ListWatchlists			= 'watchlists'			# Custom watchlist maintained by a user.
	ListFavorites			= 'favorites'			# Custom favorites maintained by a user.

	# Not part of Trakt API parameters. Used to generate web links.
	ListHistory				= 'history'
	ListProgress			= 'progress'
	ListCollection			= 'collection'
	ListRating				= 'ratings'
	ListFavorite			= 'favorites'
	ListWatchlist			= 'watchlist'

	# Not part of Trakt API parameters. Used to retrieve lists of lists.
	ListPopular				= MetaTools.ListPopular
	ListTrending			= MetaTools.ListTrending
	ListLike				= MetaTools.ListLike
	ListComment				= MetaTools.ListComment
	ListCollaboration		= MetaTools.ListCollaboration

	# SECTION

	SectionCalendar			= 'calendar'
	SectionProgress			= 'progress_watched'
	SectionReset			= 'progress_watched_reset'
	SectionCollection		= 'progress_collected'
	SectionRecommendations	= 'recommendations'
	SectionComments			= 'comments'

	# PRIVACY
	# List privacy.

	PrivacyPublic			= 'public'				# Anyone can see the list.
	PrivacyPrivate			= 'private'				# Only the creator can see the list.
	PrivacyFriends			= 'friends'				# Only the creator's friends can see the list.
	PrivacyLink				= 'link'				# Anyone with the share_link can see the list.

	# FIELD

	FieldTitle				= 'title'				# Movies, Shows, Episodes
	FieldTagline			= 'tagline'				# Movies
	FieldOverview			= 'overview'			# Movies, Shows, Episodes
	FieldPeople				= 'people'				# Movies, Shows
	FieldTranslations		= 'translations'		# Movies, Shows
	FieldAliases			= 'aliases'				# Movies, Shows
	FieldName				= 'name'				# People, Lists
	FieldBiography			= 'biography'			# People
	FieldDescription		= 'description'			# Lists
	FieldsSearch			= [FieldTitle, FieldTranslations, FieldAliases, FieldName] # Which fields to use for searching.
	FieldsKeyword			= [FieldTitle, FieldTagline, FieldOverview, FieldDescription, FieldName] # Which fields to emulate keywords (similar to IMDb).

	# SORT

	# Only for Discover. Not actual sort methods, but specific API endpoints that have fixed sorting method/order.
	SortTrending			= 'trending'	# Highest number of users currently watching.
	SortPopular				= 'popular'		# Highest rating and votes cast.
	SortFavorited			= 'favorited'	# Highest number of user favorites.
	SortPlayed				= 'played'		# Highest number of plays (multiple plays per user).
	SortWatched				= 'watched'		# Highest number of plays (single play per user).
	SortCollected			= 'collected'	# Highest number of users collected (single collection per user).
	SortAnticipated			= 'anticipated'	# Highest number of list appearances.
	SortShuffle				= 'shuffle'		# Internal. Randomize list. Make sure this is the same as in MetaTools.

	# Sort method for user Watchtlists and Favorites API endpoints.
	SortRank				= 'rank'
	SortAdded				= 'added'
	SortReleased			= 'released'
	SortTitle				= 'title'

	# SELECT

	SelectIncludeAny		= '+'			# Include any match. Eg: filter by "+documentary" will allow ["Documentary", "History"] and ["History", "Documentary"], but remove ["History"].
	SelectExcludeAny		= '-'			# Exclude any match. Eg: filter by "-documentary" will allow ["History"], but remove ["Documentary", "History"] and ["History", "Documentary"].
	SelectIncludeMain		= '#'			# Include first/primary match. Eg: filter by "#documentary" will allow ["Documentary", "History"], but remove ["History", "Documentary"] and ["History"].
	SelectExcludeMain		= '~'			# Exclude first/primary match. Eg: filter by "~documentary" will allow ["History", "Documentary"] and ["History"], but remove ["Documentary", "History"].

	# DUPLICATE

	DuplicateAll			= 'all'			# Keep all duplicates.
	DuplicateFirst			= 'first'		# Remove duplicates and only keep the first item (eg: first episode of a show/season, depends on th elist order).
	DuplicateLast			= 'last'		# Remove duplicates and only keep the last item (eg: last episode of a show/season, depends on th elist order).
	DuplicateMerge			= 'merge'		# Merge duplicates into one (eg: discovering by person might return duplicates if a person was actor and director in a movie).

	# EXTENDED

	ExtendedFull			= 'full'		# Retrieve full extended metadata.
	ExtendedMeta			= 'metadata'	# Retrieve additional video and audio info for collections only.
	ExtendedEpisode			= 'episodes'	# Retrieve all episodes of a season. NB: This can return a lot of data.
	ExtendedGuest			= 'guest_stars'	# Retrieve guest stars of the last episode in the show/season. NB: This can return a lot of data.
	ExtendedImages			= 'images'		# Retrieve images.

	ExtendedBasic			= 'basic'		# Not an official value.

	# STRUCTURE

	StructureShow			= 'show'
	StructureSeason			= 'season'
	StructureEpisode		= 'episode'

	# ACTION

	ActionScrobble			= 'scrobble'
	ActionCheckin			= 'checkin'
	ActionWatch				= 'watch'

	# LIMIT

	LimitFixed				= 10				# Trakt page limit if no limit parameter was added.
	LimitDefault			= 50				# Default limit to use instead.
	LimitSearch				= 50				# Maximum limit for the search endpoint. New (unofficial) limit added by Trakt around 2025-12.
	LimitGeneral			= 250				# Maximum limit for the popular/etc endpoints. New (unofficial) limit added by Trakt around 2025-12.
	LimitRecommendation		= 100				# Maximum limit for the recommendation endpoint.
	LimitHome				= 30				# How many days into the past a title is considered to have a home/digital release.
	LimitFuture				= 1					# How many days into the future a title is considered to be a future release.

	# There is a problem with pagination+sorting for lists.
	# Trakt always applies its own sorting, which is typically "rank", or for a few "added" (eg: watchlist).
	# Even for own lists, on Trakt's website the list settings can be edited (little green pen icon), but Trakt still returns the list in a fixed order through the API.
	# However, the list's sort setting is returned in the headers (x-sort-how), which can be used to sort locally.
	# But if we page, only eg 50 items are returned per page (in default order, NOT sorted by Trakt's API according to the user's settings), and sorting can only be applied to a single page, instead of across the entire list.
	# Currently the only option to do proper sorting seems to be to retrieve the entire list. The options are:
	#	1. Either retrieve one page at a time from the list: Way faster loading, not overloading Trakt's server, proper way of doing things, sub-par sorting or for smaller pages close to no sorting at all.
	#	2. Or retrieve the entire list in one go: Way slower loading, overloading Trakt, improper way of doing things, proper sorting (at least for the 1st LimitList items).
	# Trakt currently has the following limits:
	#	https://forums.trakt.tv/t/personal-list-updates/10170
	#	1. VIP Members: 10,000 custom lists, 10,000 watchlist
	#	2. Old Members: 1,000 custom lists, 2,000 watchlist
	#	3. New Members: 500 custom lists, 1,000 watchlist
	# Retrieve up to 2000 items to allow proper sorting. This will not retrieve the possible last 8,000 items for VIP members.
	LimitList				= 2000

	# USAGE
	# https://trakt.docs.apiary.io/#introduction/rate-limiting
	# Trakt has reduced its API calls to 1000 requests per 5 minutes.
	# It seems that these limits are not strictly adhered to all the time, maybe because Trakt needs some time to update the rate limit, or because the limits are not applied strictly.
	# There are two different limits:
	#	1. Authenticated API calls: when the user is involved, eg retrieving user lists and ratings.
	#	2. Unauthenticated API calls: when authentication is not required, like discover, search, and metadata.
	# Authentication can be added to unauthenticated API calls can, so technically we have 1000+1000 = 2000 requests per 5 minutes.
	# Update (2025-12): The combined total of 2000 p/5m for auth/unauth calls might not work anymore. Check _request() -> _waitUpdate() for more details.
	UsageAuthenticatedRequest		= 1000
	UsageAuthenticatedDuration		= 300
	UsageUnauthenticatedRequest		= 1000
	UsageUnauthenticatedDuration	= 300

	# Global properties.
	PropertyLookup					= 'GaiaTraktLookup'

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		MetaProvider.__init__(self, account = Core.getTraktAccount())

	##############################################################################
	# REQUEST
	##############################################################################

	def _retrieve(self, link, extract = True, lock = True, cache = None, failsafe = True, detail = None, **parameters):
		try:
			data = parameters
			if not data: data = {}

			sort = data.get('sort')
			if sort is True: data['sort'] = '' # Remove eg "sort=True" for the Watchlist.

			user = bool(data.get('user'))
			data = self._parameterDefault(**data)
			data = self._parameterConvert(**data)
			link = self._linkApi(link = link, **data)
			data = self._parameterInitialize(**data)

			result = None
			try:
				if lock: self._lock(limit = lock)
				if cache is None:
					result = self._request(link = link, user = user, sort = sort, data = data)
				else:
					result = self._cache(timeout = cache, function = self._request, link = link, user = user, sort = sort, data = data)
					# Clear cache for failed requests, eg temporary Trakt server problems.
					if failsafe and result and (result.get('error') or {}).get('type') in Networker.ErrorNetwork: self._cacheDelete(function = self._request, link = link, user = user, sort = sort, data = data)
			except:
				self._logError()
			finally:
				if lock: self._unlock(limit = lock)

			items = self._extract(data = result, extract = extract, **parameters)
			if detail: return items, result.get('sort'), result.get('error')
			else: return items
		except: self._logError()
		return None

	def _request(self, link, user = None, sort = None, data = None):
		try:
			# Use authenticated API requests if required (eg: retrieve user-specific lists).
			# Or use authenticated API requests if the unauthenticated API calls are used up, so we can get an additional 1000 requests.
			# Update (2025-12): This might not work anymore. Check _waitUpdate() below.
			direct = True
			if user: direct = False
			elif self.usage(authenticated = False) > 0.95 and self.usage(authenticated = True) < 0.9: direct = False
			self._usageUpdate(authenticated = not direct)

			# UPDATE (2025-11-15)
			# When the link does not end with a slash, the search/trending/etc endpoints now ingores the parameters.
			# All filters (genre/years/studio_ids/etc) are ignored without a slash. The only parameter that still seems to work is "limit".
			# When adding the slash at the end, the filter parameters work again.
			# Pretty sure that when a slash was added before, a HTTP error was returned.
			# Maybe this is a "bug" on Trakt's side when they made recent API changes. Might change in the future back to the old way.
			# UPDATE (2025-12-15)
			# Now adding the slash for the search endpoint also does not work. Most parameters (years, etc) are ignored, including the limit and page parameter.
			# It seems the limit parameter is still applied to the search endpoint, but only if it is a value below 50. Any value above 50 is reduced to 50. And the page parameter is still ingored.
			# More info under search().
			if not link.endswith('/'): link += '/'

			data, headers, error = Core.getTrakt(method = Networker.MethodGet, url = link, post = data, direct = direct, extended = True)
			data = Converter.jsonFrom(data)

			if not data and error:
				if error.get('trakt'): self._errorUpdate() # Rate limit reached, or temporary server problems.
				if error.get('code') == 429:
					# Update (2025-12):
					# Add the wait timestamp as well. This is important for MetaManager.generate() and MetaManager.reload() to not reach the Trakt API limit.
					# Trakt does not seem to always return the X-Ratelimit header, only the Retry-After header. Maybe this is new, since they possibly changed the way the limits work?
					# The usage counters calculated locally with _usageUpdate() also do not seem to work anymore.
					# 	Either Trakt has changed their API rate limits/durations from the "1000 calls every 5 minutes" stated in the docs.
					# 	Or Trakt now handles auth/unauth requests differently, not allowing a combined total of 2000 anymore.
					# 	Or Trakt now counts auth/unauth requests together? Or counts all non-user-endpoint calls made with authentication towards "unauth" and not as previously towards "auth".
					# It is probably the last one. Check the limits in MetaManager._batchStart() for more info.
					#	If the requests are only stopped after 50% (even just above 50-55%), then the Trakt limits are hit all the time.
					#	If the requests are already stopped after 45-50%, then the Trakt limits are not hit.
					# 	This would indicate that the combined auth/unauth total of 2000 does not apply anymore, but rather just below 1000.
					#	So either Trakt now uses the same limit for both auth/unauth, or counts all authed non-user calls towards the unauth limit.
					self._waitUpdate(Core.limitWait())

					if System.developer(): Logger.log('TRAKT RATE LIMIT REACHED: %s Request' % ('Unauthenticated' if direct else 'Authenticated'))

			# Always sort if headers are available.
			if not sort is False:
				sort = Core.sortHas(headers)
				data = Core.sortList(data = data, headers = headers) # Default user lists (eg: a user's rating list) do not have sort parameters.

			return {'data' : data, 'headers' : headers, 'error' : error, 'sort' : sort}
		except: self._logError()
		return None

	##############################################################################
	# EXECUTE
	##############################################################################

	def _execute(self, iterator, function = None, interleave = True, sort = True, order = None, concurrency = None, lock = True, detail = None, exit = None, **parameters):
		internal = parameters.get('internal')
		try:
			iterator = [i for i in iterator if i]
			separate = True if (iterator and 'result' in iterator) or function is None else False

			if concurrency is None: concurrency = True
			if concurrency is True and len(iterator) == 1: concurrency = False

			items = {} if separate else []
			errors = {} if separate else []
			count = {}
			threads = []

			for i in iterator:
				kwargs = {'function' : function or self._retrieve, 'items' : items, 'errors' : errors, 'count' : count, 'result' : i.get('link'), 'lock' : lock, 'detail' : detail, 'sort' : sort, 'order' : order}
				kwargs.update(Tools.copy(dict(**parameters)))
				kwargs.update(i)
				if concurrency:
					threads.append(Pool.thread(target = self._executeIteration, kwargs = kwargs, start = True))
				else:
					self._executeIteration(**kwargs)
					# Exit and do not continue with the other requests if the request was successful.
					if exit:
						if separate and items.get(kwargs.get('result')): break
						elif not separate and items[-1]: break
			[thread.join() for thread in threads]

			if not separate and items:
				if interleave: items = Tools.listInterleave(*items) # Interleave movies and shows, in case the rank sorting below does not work.
				else: items = Tools.listFlatten(*items)

				if sort:
					if sort is True: items = Tools.listSort(items, key = lambda i : self._temp(item = i, key = ['list', 'rank'], default = 0), reverse = order == MetaTools.OrderDescending)
					elif Tools.isArray(sort): items = Tools.listSort(items, key = lambda i : Tools.dictionaryGet(i, sort), reverse = order == MetaTools.OrderDescending)
					else: items = self.mMetatools.sort(items = items, sort = sort, order = order, inplace = True)

			return self._internal(items = items, errors = errors, detail = detail, internal = internal, **count)
		except: self._logError()
		return self._internal(internal = internal, detail = detail)

	def _executeIteration(self, function, items, errors, count = None, result = None, lock = None, **parameters):
		try:
			if lock: self._lock(limit = lock)
			error = None
			if function == self._retrieve and parameters.get('detail'):
				parameters['detail'] = True
				data, _, error = function(**parameters)
			else:
				data = function(**parameters)

			if parameters.get('internal'):
				if data:
					if not count is None:
						for k, v in data.items():
							if not k == 'items':
								if k in count: count[k] += v
								else: count[k] = v
					data = data.get('items')

			if data:
				if Tools.isArray(result): self._dataSet(item = items, key = result, value = data)
				elif result: items[result] = data
				else: items.append(data)
			else: # Allow metadata() to determine if the request was completed.
				if Tools.isArray(result): self._dataSet(item = items, key = result, value = data)
				elif result: items[result] = data

			# Add errors, such as HTTP 404.
			if Tools.isArray(result): self._dataSet(item = errors, key = result, value = error)
			elif result: errors[result] = error
			else: errors.append(error)
		except:
			self._logError()
		finally:
			if lock: self._unlock(limit = lock)

	##############################################################################
	# LINK
	##############################################################################

	@classmethod
	def link(self, media = None, id = None, slug = None, season = None, episode = None, title = None, year = None, user = None, list = None, metadata = None, search = False, test = False):
		if metadata:
			if media is None: media = metadata.get('media')
			if id is None: id = metadata.get('id', {}).get(self.id()) or metadata.get(self.id()) or metadata.get('id', {}).get('imdb') or metadata.get('imdb')
			if slug is None: slug = metadata.get('slug')
			if season is None: season = metadata.get('season')
			if episode is None: episode = metadata.get('episode')
			if title is None: title = metadata.get('tvshowtitle') or metadata.get('title') or metadata.get('name')
			if year is None: year = metadata.get('year')

		if user is True or (not user is False and list): user = self.accountUser()
		if list is None and Media.isSet(media): list = MetaTrakt.ListOfficial
		if Media.isSet(media) and title and not title.lower().endswith(' collection'): title += ' Collection'

		data = {
			'media' : media,
			'id' : slug or id, # Prefer slug, since it is easier to read.
			'season' : season,
			'episode' : episode,
			'user' : user,
			'list' : list,
		}
		instance = self.instance()
		data = instance._parameterDefault(**data)
		data = instance._parameterConvert(**data)

		base = None
		if Media.isMovie(media): base = MetaTrakt.LinkWebMovie
		elif Media.isShow(media): base = MetaTrakt.LinkWebShow
		elif Media.isSeason(media): base = MetaTrakt.LinkWebSeason
		elif Media.isEpisode(media): base = MetaTrakt.LinkWebEpisode
		elif Media.isSet(media) or list: base = MetaTrakt.LinkWebList
		elif Media.isPerson(media): base = MetaTrakt.LinkWebPerson

		link = None
		if user:
			if id:
				list = MetaTrakt.LinkWebUserList
			elif list:
				if list == MetaTrakt.ListHistory: list = MetaTrakt.LinkWebUserHistory
				elif list == MetaTrakt.ListProgress: list = MetaTrakt.LinkWebUserProgress
				elif list == MetaTrakt.ListCollection: list = MetaTrakt.LinkWebUserCollection
				elif list == MetaTrakt.ListRating: list = MetaTrakt.LinkWebUserRating
				elif list == MetaTrakt.ListFavorite: list = MetaTrakt.LinkWebUserFavorite
				elif list == MetaTrakt.ListWatchlist: list = MetaTrakt.LinkWebUserWatchlist
			else:
				link = MetaTrakt.LinkWebUser
		else:
			slug = None
			if not data.get('id') and title:
				if test:
					# Trakt slugs seem to always have a year for movies, but only occasional for shows (with duplicate names).
					tester = Tools.copy(data)
					slug = tester['id'] = MetaTools.slug(title = title, year = year, separator = '-', symbol = '-', lower = True)
					if not Networker().requestSuccess(link = self._linkWeb(link = base, **tester)):
						slug = tester['id'] = MetaTools.slug(title = title, year = None, separator = '-', symbol = '-', lower = True)
						if not year: slug = None # Same as the previous request.
						elif not Networker().requestSuccess(link = self._linkWeb(link = base, **tester)): slug = None
				else:
					slug = MetaTools.slug(title = title, year = None if Media.isSerie(media) else year, separator = '-', symbol = '-', lower = True)

			if slug:
				data['id'] = slug
			elif search and not data['id'] and title:
				query = None

				if Media.isMovie(media):
					link = MetaTrakt.LinkWebSearchMovie
					query = title + ((' ' + str(year)) if year else '')
				elif Media.isShow(media):
					link = MetaTrakt.LinkWebSearchShow
					query = title
				elif Media.isEpisode(media):
					link = MetaTrakt.LinkWebSearchEpisode
					query = title
				elif Media.isSerie(media):
					link = MetaTrakt.LinkWebSearchShow
					query = title
				elif Media.isSet(media):
					link = MetaTrakt.LinkWebSearchList
					query = title
				elif Media.isPerson(media):
					link = MetaTrakt.LinkWebSearchPerson
					query = title
				elif list:
					link = MetaTrakt.LinkWebSearchList
					query = list
				elif user:
					link = MetaTrakt.LinkWebSearchUser
					query = user
				elif title:
					link = MetaTrakt.LinkWebSearch
					query = title

				if query: data['query'] = Networker.linkQuote(data = query, plus = False)

			if not link and data['id'] and base: link = base

		if link: link = self._linkWeb(link = link, **data)
		return link

	@classmethod
	def _linkFormat(self, base, link, **data):
		if not link.startswith(base): link = Networker.linkJoin(base, link)
		link = link.format(**data)
		link = link.rstrip('/') # If we format with an empty string to remove the last part of the path.
		return link

	@classmethod
	def _linkApi(self, link, **data):
		return self._linkFormat(base = MetaTrakt.LinkApi, link = link, **data)

	@classmethod
	def _linkWeb(self, link, **data):
		return self._linkFormat(base = MetaTrakt.LinkWeb, link = link, **data)

	##############################################################################
	# PARAMETER
	##############################################################################

	def _parameterDefault(self, **data):
		result = Tools.copy(data)

		medias = result.get('medias') or result.get('media')
		if not medias: result['medias'] = [Media.Movie, Media.Show] # Multiple types possible for certain endpoints (eg: search).

		page = result.get('page')
		if page is None: result['page'] = 1

		limit = result.get('limit')
		if limit is None: result['limit'] = MetaTrakt.LimitDefault

		extended = result.get('extended')
		if extended is None: result['extended'] = True

		period = result.get('period')
		if period is None: result['period'] = MetaTrakt.PeriodAll

		provider = result.get('provider')
		if provider is None: result['provider'] = self.id()

		return result

	def _parameterConvert(self, **data):
		type = typeBase = data.get('type')
		if type: type = None
		else: type = []

		category = categoryBase = data.get('category')
		if category: category = None
		else: category = []

		medias = data.get('medias') or data.get('media')
		if not Tools.isArray(medias): medias = [medias]

		for media in medias:
			if Media.isSet(media) or Media.isList(media):
				if not type is None: type.append(MetaTrakt.TypeList)
				if not category is None: category.append(MetaTrakt.CategoryList)
			elif Media.isMovie(media):
				if not type is None: type.append(MetaTrakt.TypeMovie)
				if not category is None: category.append(MetaTrakt.CategoryMovie)
			elif Media.isShow(media):
				if not type is None: type.append(MetaTrakt.TypeShow)
				if not category is None: category.append(MetaTrakt.CategoryShow)
			elif Media.isSeason(media):
				if not type is None: type.append(MetaTrakt.TypeSeason)
				if not category is None: category.append(MetaTrakt.CategorySeason)
			elif Media.isEpisode(media):
				if not type is None: type.append(MetaTrakt.TypeEpisode)
				if not category is None: category.append(MetaTrakt.CategoryEpisode)
			elif Media.isPerson(media):
				if not type is None: type.append(MetaTrakt.TypePerson)
				if not category is None: category.append(MetaTrakt.CategoryPerson)

		if not type is None: data['type'] = typeBase if typeBase == '' else ','.join(type)
		if not category is None: data['category'] = categoryBase if categoryBase == '' else ','.join(category)

		if data.get('language') is True: data['language'] = self.language(exclude = True)

		return data

	def _parameterInitialize(self,
		media = None,
		niche = None,

		query = None,				# String: query

		date = None,				# Integer: minimum history timestamp | String: minimum history date | List: history date range
		year = None,				# Integer: single year | List: year range
		duration = None,			# List: duration range, seconds

		genre = None,				# String: single Trakt genre, genre slug | List: multiple genres, ORed
		language = None,			# String: single language, 2-digit code | List: multiple languages, ORed
		country = None,				# String: single country, 2-digit code | List: multiple countries, ORed
		certificate = None,			# String: single certificate, US MPAA | List: multiple certificates, ORed

		status = None,				# String: single status, Trakt status slug only for shows | List: multiple statuses, ORed
		watch = None,				# String: single watch status | List: multiple watch statuses, ORed
		episode = None,				# String: single episode type, Trakt episode slug only for episodes | List: multiple episode types, ORed

		studio = None,				# String: single studio, Trakt studio ID | List: multiple studios, ORed
		network = None,				# String: single network, Trakt network ID only for shows and episodes | List: multiple networks, ORed

		rating = None,				# Float: minimum Trakt rating, 0.0 - 10.0 | List: rating range
		votes = None,				# Integer: minimum Trakt votes, 0 - 100000 | List: vote range
		imdbRating = None,			# Float: minimum IMDb rating, 0.0 - 10.0 | List: rating range
		imdbVotes = None,			# Integer: minimum IMDb votes, 0 - 3000000 | List: vote range
		tmdbRating = None,			# Float: minimum TMDb rating, 0.0 - 10.0 | List: rating range
		tmdbVotes = None,			# Integer: minimum TMDb votes, 0 - 100000 | List: vote range
		rtRating = None,			# Float: minimum Rotten Tomatoes audience score rating, 0.0 - 10.0 only for movies | List: rating range
		rtMeter = None,				# Float: minimum Rotten Tomatoes tomatometer rating, 0.0 - 10.0 only for movies | List: rating range
		mcRating = None,			# Float: minimum Metacritic rating, 0.0 - 10.0 only for movies | List: rating range

		page = None,				# Integer: page number
		limit = None,				# Integer: page limit
		sort = None,				# Boolean: sort according to the headers
		extended = None,			# Boolean: extended details | String: type of extended details | List: multiple extended details (eg: extended=full,episodes)
		field = None,				# Boolean: all applicable search fields | String: single search field | List: multiple search field
		list = None,				# String: the type of lists to retrieve
		search = None,				# String: the types to retrieve for ID lookups
		translation = None,			# String: the episode translations to retrieve. Country code or "all".

		collection = None,			# Boolean: include user collected items
		watchlist = None,			# Boolean: include user watchlist items

		**data
	):
		# NB: Although not mentioned in the Trakt docs, it seems that the filter parameters can be negated.
		# Eg: "genres=-anime,-documentary" will return all titles that are not anime or documentaries.

		result = {}

		if not query is None: # Allow empty string.1
			if Tools.isArray(query): query = ' '.join(query)
			result['query'] = query.strip()

		if date:
			if not Tools.isArray(date): date = [date, None]
			for i in range(len(date)):
				value = date[i]
				if value is None or value is True or value is False: value = Time.timestamp()
				elif Tools.isString(value) and not 'T' in value: value = Time.timestamp(fixedTime = value, format = Time.FormatDate, utc = True)
				if Tools.isInteger(value): date[i] = Core.timeFormat(value)
			result['start_at'] = date[0]
			result['end_at'] = date[1]

		if year: result['years'] = self._parameterRange(values = year, none = [0, 9999])

		if duration: # Trakt uses minutes.
			if Tools.isNumber(duration): duration = str(int(duration / 60.0))
			elif Tools.isArray(duration): duration = self._parameterRange(values = [99999999 if i is None else int(i / 60.0) for i in duration])
			result['runtimes'] = duration

		if genre: result['genres'] = self._parameterList(values = self._convertGenre(genre = genre))
		if language: result['languages'] = self._parameterList(values = language)
		if country: result['countries'] = self._parameterList(values = country)
		if certificate: result['certifications'] = self._parameterList(values = self._convertCertificate(certificate = certificate)).lower() # Must be lower case.

		if status:
			if status is True: status = MetaTrakt.StatusAvailable
			elif status is False: status = MetaTrakt.StatusUnavailable
			else: status = self._convertStatus(status = status)
			result['status'] = self._parameterList(values = status)
		if watch:
			if watch is True: status = MetaTrakt.WatchAny
			elif watch is False: status = MetaTrakt.WatchFree
			result['watchnow'] = self._parameterList(values = watch)
		if episode and not Tools.isInteger(episode): result['episode_types'] = self._parameterList(values = episode) # Do not add episode numbers to the episode types.

		if studio: result['studio_ids'] = self._parameterList(values = studio)
		if network: result['network_ids'] = self._parameterList(values = network)

		if rating: result['ratings'] = self._parameterRatingInteger(rating = rating)
		if votes: result['votes'] = self._parameterVotesCount(votes = votes, media = media, niche = niche)
		if imdbRating: result['imdb_ratings'] = self._parameterRatingDecimal(rating = imdbRating)
		if imdbVotes: result['imdb_votes'] = self._parameterVotesCount(votes = imdbVotes, media = media, niche = niche)
		if tmdbRating: result['tmdb_ratings'] = self._parameterRatingDecimal(rating = tmdbRating)
		if tmdbVotes: result['tmdb_votes'] = self._parameterVotesCount(votes = tmdbVotes, media = media, niche = niche)
		if rtRating: result['rt_user_meters'] = self._parameterRatingInteger(rating = rtRating)
		if rtMeter: result['rt_meters'] = self._parameterRatingInteger(rating = rtMeter)
		if mcRating: result['metascores'] = self._parameterRatingDecimal(rating = mcRating)

		if page: result['page'] = str(page)
		if limit: result['limit'] = str(limit)

		if extended:
			if Tools.isArray(extended): # Although not documented, multiple extended infos can be passed. Eg: extended=full,episodes.
				extended = [i for i in extended if i and not i == MetaTrakt.ExtendedBasic]
				if extended: result['extended'] = ','.join(extended)
			elif Tools.isString(extended):
				if not extended == MetaTrakt.ExtendedBasic: result['extended'] = extended
			else:
				result['extended'] = MetaTrakt.ExtendedFull

		if field: result['fields'] = ','.join([i for i in field if i]) if Tools.isArray(field) else ','.join(MetaTrakt.FieldsSearch) if field is True else field
		if list: result['types'] = self._parameterList(values = list)
		if search: result['type'] = self._parameterList(values = search)
		if translation: result['translations'] = MetaTrakt.CategoryAll if translation is True else self._parameterList(values = translation)

		# Note the values of these parameters are switched.
		if not collection is None: result['ignore_collected'] = 'false' if collection else 'true'
		if not watchlist is None: result['ignore_watchlisted'] = 'false' if watchlist else 'true'

		return result

	def _parameterRange(self, values, none = True):
		if Tools.isArray(values):
			if none is True: values = '-'.join([str(i) for i in values])
			elif none is False: values = '-'.join(['' if i is None else str(i) for i in values])
			elif Tools.isArray(none): values = '-'.join([str(none[0 if i == 0 else -1]) if values[i] is None else str(values[i]) for i in range(len(values))])
			else: values = '-'.join([str(none) if i is None else str(i) for i in values])
		return str(values)

	def _parameterList(self, values):
		if Tools.isArray(values): values = ','.join([str(i) for i in values])
		return str(values)

	def _parameterRating(self, rating):
		if rating is True or Tools.isNumber(rating) or Tools.isString(rating): rating = [rating, None]
		if Tools.isArray(rating):
			for i in range(len(rating)):
				value = rating[i]
				if value is None:
					value = 0.0 if i == 0 else 10.0
				elif Tools.isString(value): # Do not apply to fixed rating ranges.
					if value == MetaProvider.VotingMinimal: value = 0.0
					elif value == MetaProvider.VotingLenient: value = 1.0
					elif value == MetaProvider.VotingNormal: value = 3.0
					elif value == MetaProvider.VotingModerate: value = 5.0
					elif value == MetaProvider.VotingStrict: value = 7.5
					elif value == MetaProvider.VotingExtreme: value = 8.0
				rating[i] = value
		return rating

	def _parameterRatingInteger(self, rating):
		rating = self._parameterRating(rating = rating)
		if Tools.isArray(rating): rating = self._parameterRange([int(max(0, min(100, float(rating[0] if rating[0] else 0) * 10))), int(max(0, min(100, float(rating[1] if rating[1] else 10) * 10)))])
		return rating

	def _parameterRatingDecimal(self, rating):
		rating = self._parameterRating(rating = rating)
		if Tools.isArray(rating): rating = self._parameterRange(['%.1f' % float(max(0, min(10, float(rating[0] if rating[0] else 0)))), '%.1f' % float(max(0, min(10, float(rating[1] if rating[1] else 10))))])
		return rating

	def _parameterVotes(self, votes, media = None, niche = None):
		if votes is True or Tools.isNumber(votes) or Tools.isString(votes): votes = [votes, None]
		if Tools.isArray(votes):
			for i in range(len(votes)):
				value = votes[i]
				if value is None:
					value = 0 if i == 0 else 999999999
				elif Tools.isString(value): # Do not apply to fixed vote ranges.
					# NB: The vote brackets should correspond with the estimates in release().
					if value == MetaProvider.VotingMinimal: value = 1
					elif value == MetaProvider.VotingLenient: value = 20
					elif value == MetaProvider.VotingNormal: value = 200
					elif value == MetaProvider.VotingModerate: value = 1000
					elif value == MetaProvider.VotingStrict: value = 5000
					elif value == MetaProvider.VotingExtreme: value = 20000

					if Media.isSerie(media):
						value = value / 2.0
						if Media.isEpisode(media): value = value / 10.0
						elif Media.isSeason(media): value = value / 20.0
					elif Media.isSet(media) or Media.isList(media):
						value = value / 20.0

					if Media.isTelevision(niche): value = value / 10.0

					if Media.isShort(niche): value = value / 20.0
					elif Media.isSpecial(niche): value = value / 25.0
					elif Media.isDocu(niche): value = value / 10.0
					elif Media.isAnime(niche): value = value / 10.0
					elif Media.isDonghua(niche): value = value / 20.0
					elif Media.isTopic(niche): value = value / 10.0
					elif Media.isRegion(niche): value = value / 3.0

					if (Media.isKid(niche) or Media.isTeen(niche)) and value: value = int(value * 0.75) # Reduce votes for kids.
					value = Math.roundUp(value)

				# There are separate vote limits listed in the Trakt API docs. Not sure if they are absolutely required.
				if i == 0: value = max(0, int(value if value else 0))
				elif i == 1: value = max(0, int(value if value else 99999999))

				votes[i] = value
		return votes

	def _parameterVotesCount(self, votes, media = None, niche = None):
		votes = self._parameterVotes(votes = votes, media = media, niche = niche)
		return self._parameterRange(votes)

	def _parameterNiche(self, niche = None, extension = None, copy = False):
		if extension:
			if niche:
				if not Tools.isArray(niche): niche = [niche]
				elif copy: niche = Tools.copy(niche)
			else: niche = []

			if Tools.isArray(extension): niche.extend(extension)
			else: niche.append(extension)

		return niche

	def _parameterFilter(self, media, niche = None, query = None, keyword = None, release = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, award = None, sort = None, order = None, filter = None, field = None, list = None, strucuture = False):
		# Keep the original parameters, in case this function is called twice.
		# Eg: In discover() and release() the function can call search() or iteself internally.
		original = {
			'media'			: media,
			'niche'			: niche,
			'query'			: query,
			'keyword'		: keyword,
			'date'			: date,
			'year'			: year,
			'duration'		: duration,
			'genre'			: genre,
			'language'		: language,
			'country'		: country,
			'certificate'	: certificate,
			'status'		: status,
			'episode'		: episode,
			'company'		: company,
			'studio'		: studio,
			'network'		: network,
			'rating'		: rating,
			'votes'			: votes,
			'sort'			: sort,
			'order'			: order,
			'field'			: field,
			'filter'		: filter,
		}

		support = True
		medias = None
		extra = None

		filter = self._filterDefault(filter = filter, niche = niche)

		# Convert, in case MetaTrakt instead of MetaTools genres were passed in.
		genreInclude = self._convertGenre(genre = genre, inverse = True, default = True) or []
		genreExclude = []

		# Should match with code in filter().
		if media is True:
			media = Media.Unknown
			medias = [Media.Movie, Media.Show, Media.Season, Media.Episode, Media.Person, Media.List]
		elif media is None or media is False or Media.isMixed(media):
			media = Media.Unknown
			medias = [Media.Movie, Media.Show]
		else:
			if Tools.isArray(media):
				if len(media) == 1:
					medias = media
					media = media[0]
				else:
					medias = media
					media = Media.Unknown
			else:
				medias = [media]

			if Media.isMovie(media):
				if Media.isShort(niche):
					# Some titles are listed with "short" as genre:
					#	https://trakt.tv/movies/zero-2010
					# However, many shorts do not have "short" as genre, although IMDb lists them as shorts.
					#	https://trakt.tv/movies/piper-2016
					#	https://trakt.tv/movies/the-wonderful-story-of-henry-sugar-2023
					#	https://trakt.tv/movies/kung-fury-2015
					# It is therefore better to filteratingr by runtime.
					# For the discover() endpoints that have filters, using the "short" genre works, but it obviously does not return those without "short" set as genre.
					# Do not set the maximum duration too high (eg 60 minutes), since there are shorter TV movies and TV specials.
					#	https://trakt.tv/movies/werewolf-by-night-2022
					#	https://trakt.tv/movies/the-guardians-of-the-galaxy-holiday-special-2022
					# However, there are also TV movies in the shorter duration range (eg +- 30 minutes).
					#	https://trakt.tv/movies/a-charlie-brown-christmas-1965
					if filter >= MetaProvider.FilterLenient:
						if filter >= MetaProvider.FilterStrict:
							genreInclude.append(MetaTools.GenreShort)
							if Media.isCinema(niche): '!("tv" || "television")'
							elif Media.isTelevision(niche): '("tv" || "television")'
						else:
							minimum = MetaTools.ShortMinimum
							maximum = MetaTools.ShortStandard # ShortMaximum is too long.
							if Tools.isInteger(duration): duration = [minimum, min(maximum, duration)]
							elif Tools.isArray(duration) and len(duration) >= 2: duration = [max(minimum, duration[0]), min(maximum, duration[1])]
							else: duration = [minimum, maximum]
							if Media.isCinema(niche): extra = '!("tv" || "television" || "special" || "christmas" || "holiday")'
							elif Media.isTelevision(niche): extra = '("tv?short*" || "television?short*" || "short?tv*" || "short?television*" || "for tv*" || "for television*")'
				elif Media.isSpecial(niche):
					# Many Holiday Specials are categoriesed under the Holiday genre.
					#	https://trakt.tv/movies/lego-star-wars-holiday-special-2020
					#	https://trakt.tv/movies/the-star-wars-holiday-special-1978
					# But some are specials, but are not categoriesed under the Holiday genre.
					#	https://trakt.tv/movies/minions-holiday-special-2020
					# There are also some under the Holiday genre that are not specials, but feature movies.
					#	https://trakt.tv/movies/silent-night-2023-12-01
					# Best is to use a combination of the Holiday genre and "special" keyword.
					# Not perfect, since the query also searches the tagline and plot for the "special" keyword, so add duration as well.
					genreInclude.append(MetaTools.GenreHoliday)
					duration = [60, 4500] # 1 hour 15 minutes.
					if Media.isCinema(niche): extra = '"special" && !("tv" || "television")'
					elif Media.isTelevision(niche): extra = '"special" && ("tv" || "television")'
				else:
					if filter >= MetaProvider.FilterLenient:
						if filter >= MetaProvider.FilterStrict: duration = [int(MetaTools.ShortAverage / 1.5) if Media.isTelevision(niche) else MetaTools.ShortStandard, None]
						else: duration = [int(MetaTools.ShortAverage / 2) if Media.isTelevision(niche) else MetaTools.ShortAverage, None]
						if filter >= MetaProvider.FilterStrict and not MetaTools.GenreShort in genreInclude: genreExclude.append(MetaTools.GenreShort)
						if filter >= MetaProvider.FilterStrict or not query:
							if Media.isCinema(niche): extra = '!("tv?movie*" || "television?movie*" || "tv?film*" || "television?film*" || "tv?special*" || "television?special*" || "christmas?special*" || "christmas?special*" || "holiday?special*" || "holiday?special*")'
							elif Media.isTelevision(niche): extra = '("tv?movie*" || "tv?film*" || "television?movie*" || "television?film*")'
			elif Media.isSerie(media):
				if Media.isMini(niche):
					# Nothing is listed under the mini-series genre on Trakt.
					# Use keywords to find at least some series where the "mini series" keywords appear in the title, plot, or in the title of a list that added the series.
					# Trakt uses Solr for the query. Adjust it to make sure both keywords appear in that order. Otherwise any title with the "mini" keyword OR "series" keyword is returned.
					# https://solr.apache.org/guide/7_3/the-standard-query-parser.html
					#genreInclude.append(MetaTrakt.GenreMini)
					extra = '("mini?serie*" || "miniserie*" || "mini?show*" || "minishow*" || "tv?mini*" || "mini?tv*")'
				if Media.isShort(niche):
					genreInclude.append(MetaTools.GenreShort) # Only has 3 shows listed under the "Short" genre.

				if Media.isPremiere(niche):
					if Media.isSeason(media): episode = MetaTrakt.EpisodePremiereShow
					elif Media.isOuter(niche): episode = MetaTrakt.EpisodePremiereShow
					elif Media.isInner(niche): episode = MetaTrakt.EpisodePremiereSeason
					elif Media.isMiddle(niche): episode = MetaTrakt.EpisodePremiereMiddle
				elif Media.isFinale(niche):
					if Media.isSeason(media): episode = MetaTrakt.EpisodeFinaleShow
					elif Media.isOuter(niche): episode = MetaTrakt.EpisodeFinaleShow
					elif Media.isInner(niche): episode = MetaTrakt.EpisodeFinaleSeason
					elif Media.isMiddle(niche): episode = MetaTrakt.EpisodeFinaleMiddle
			elif Media.isSet(media):
				# Trakt does not officially support sets.
				# However, they implement sets as normal lists, officially maintained by Trakt admins.
				# Eg: On top of the page it states "Pirates of the Caribbean Collection":
				#	https://trakt.tv/movies/pirates-of-the-caribbean-dead-men-tell-no-tales-2017
				#	https://trakt.tv/lists/official/pirates-of-the-caribbean-collection?sort=rank,asc
				# The API docs do not seem to allow searching between "official" and "personal" lists.
				# However, it seems that Trakt did add this to their API, just not to the API docs.
				#	https://www.reddit.com/r/trakt/comments/11ddyyq/is_there_any_way_to_findfilter_all_the_official/
				# Hence, we search for "official" types and the "collection" keyword to simulate sets.
				extra = '"collection"'
				list = MetaTrakt.ListOfficial
			elif media and not Media.isList(media) and not Media.isPerson(media) and not Media.isCompany(media): # Eg: MediaAnime()
				medias = [Media.Movie, Media.Show]

		if Media.isTopic(niche):
			topic = self.mMetatools.nicheTopic(niche = niche, strict = True)
			if topic: self._parameterGenre(genres = topic, result = genreInclude, ignore = genreExclude)
		if filter >= MetaProvider.FilterStrict:
			for i in [Media.Docu, Media.Telly, Media.Soap, Media.Anime, Media.Donghua]:
				if not Media.isMedia(media = niche, type = i):
					topic = self.mMetatools.nicheTopic(niche = i, strict = True)
					if topic: self._parameterGenre(genres = topic, result = genreExclude, ignore = genreInclude)

		if Media.isMood(niche):
			mood = self.mMetatools.nicheMood(niche = niche)
			if mood: self._parameterGenre(genres = mood, result = genreInclude, ignore = genreExclude)

		if Media.isAge(niche):
			# Can only filter by year, so always pick the next year, not the current year.
			if Media.isFuture(niche):
				date = None
				year = [Time.year() + 1, None]
			else:
				age = self.mMetatools.nicheAge(niche = niche, format = True)
				if age: date = age

		if Media.isQuality(niche):
			quality = self.mMetatools.nicheQuality(niche = niche, media = media)
			if quality:
				rating = quality
				if not votes and not Media.isPoor(niche) and not Media.isBad(niche):
					if Media.isSerie(niche): votes = 250
					elif Media.isShort(niche) or Media.isSpecial(niche): votes = 100
					elif Media.isTopic(niche): votes = 100
					else: votes = 500
					votes = [votes, None]

		if Media.isRegion(niche):
			region = self.mMetatools.nicheRegion(niche = niche)
			if region:
				if 'country' in region:
					if not country: country = []
					country.extend(region['country'])
					country = Tools.listUnique(country)
				if 'language' in region:
					if not language: language = []
					language.extend(region['language'])
					language = Tools.listUnique(language)

		if Media.isAudience(niche):
			age = Audience.TypeKid if Media.isKid(niche) else Audience.TypeTeen if Media.isTeen(niche) else Audience.TypeAdult
			certificates = self.mMetatools.nicheCertificate(age = age, media = media, unrated = False, format = True)
			if certificates:
				if not certificate: certificate = []
				certificate.extend(certificates)
				certificate = Tools.listUnique(self._convertCertificate(certificate = certificate, inverse = True))

		# NB: Although not mentioned in the Trakt docs, it seems that the filter parameters can be negated.
		# Eg: "genres=-anime,-documentary" will return all titles that are not anime or documentaries.
		genre = genreInclude

		# Do not exclude genres here.
		# Trakt filters any of the genres, not just the first/primary genre.
		# This then filters out titles that we might want to include.
		# Eg (anime listed as 3rd genre, still include in feature movies): https://trakt.tv/movies/howl-s-moving-castle-2004
		# Eg (documentary listed as 3rd genre, still include in feature movies, on IMDb is is listed as biography): https://trakt.tv/movies/american-animals-2018
		# Filter these post-request in filter().
		#if genreExclude: genre.extend([self._parameterSelect(value = i, select = '-') for i in genreExclude])

		# Pleasure
		if Media.isPleasure(niche):
			pleasure = self._convertPleasure(pleasure = niche)
			if pleasure:
				if not keyword: keyword = []
				elif not Tools.isArray(keyword): keyword = [keyword]
				keyword.extend(pleasure)

		if keyword:
			if not field: field = MetaTrakt.FieldsKeyword
			extra = [extra] if extra else []
			if Tools.isArray(keyword): extra.extend(keyword)
			else: extra.append(keyword)
		if extra: query = self._parameterQuery(query = query, extra = extra)

		yeared = year[0] if (year and Tools.isArray(year)) else year
		past = not date and yeared and yeared <= Time.year() # Check before date is changed below.
		if date or year:
			currentDate = Time.timestamp()
			currentYear = Time.year()

			if Tools.isInteger(year):
				if year > 1800: year = [year, year]
				else: year = [currentYear - year, currentYear] if year >= 0 else [currentYear, currentYear - year]

			if date is True or date == MetaTrakt.ReleaseNew:
				date = [None, currentDate]
			elif date is False or date == MetaTrakt.ReleaseFuture:
				date = [Time.future(day = MetaTrakt.LimitFuture), None]
			elif date == MetaTrakt.ReleaseHome or date == MetaTrakt.ReleaseDigital or date == MetaTrakt.ReleasePhysical:
				date = [None, currentDate if Media.isSerie(media) else Time.past(day = MetaTrakt.LimitHome)]
			elif Tools.isString(date):
				date = [None, Time.timestamp(fixedTime = date, format = Time.FormatDate, utc = True)]
			elif Tools.isInteger(date):
				if date > 10000: date = [None, date]
				elif date < -10000: date = [-1 * date, None]
				else: date = [Time.past(days = date), currentDate] if date >= 0 else [currentDate, Time.future(days = -1 * date)]
			elif not date and year:
				date = [None if year[0] is None else Time.timestamp(fixedTime = '%s-01-01' % str(year[0]), format = Time.FormatDate, utc = True), None if year[-1] is None else Time.timestamp(fixedTime = '%s-12-31' % str(year[-1]), format = Time.FormatDate, utc = True)]
			date = [Time.timestamp(fixedTime = i, format = Time.FormatDate, utc = True) if Tools.isString(i) else i for i in date]
			if not year: year = [None if date[0] is None else Time.year(date[0]), None if date[-1] is None else Time.year(date[-1])]

		status = self._convertStatus(status = status, inverse = True, default = True)

		# Award
		if award:
			if award in [MetaTools.AwardTop100, MetaTools.AwardTop250, MetaTools.AwardTop1000]:
				if rating is None: rating = MetaTrakt.VotingStrict if niche else MetaTrakt.VotingExtreme
				if votes is None: votes = MetaTrakt.VotingStrict if niche else MetaTrakt.VotingExtreme
				niche.append(Media.Best)
			elif award in [MetaTools.AwardBottom100, MetaTools.AwardBottom250, MetaTools.AwardBottom1000]:
				niche.append(Media.Worst)

		# Company
		studio, network = self._convertCompanies(media = media, niche = niche, company = company, studio = studio, network = network)
		if (company or Media.isEnterprise(niche)) and not studio and not network: support = False # Eg: network not supported for movies. Or Originals not available for a company, since there are no studios.

		# Explore
		rating, votes = self._voting(media = media, niche = niche, release = release, year = year, date = date, past = past, genre = genre, language = language, country = country, certificate = certificate, company = studio or network, status = status, rating = rating, votes = votes, active = False) # active=False: not that many votes compared to other platforms like IMDb.
		if Media.isAll(niche):
			# Search endpoint, which seems to be the same the the Popularity endpoint.
			# Sorted by popularity, so low ratings/votes should in any case not appear.
			pass
		elif Media.isNew(niche):
			# Calendar endpoint.
			if rating is None: rating = MetaProvider.VotingLenient
			if votes is None or Tools.isString(votes): votes = MetaProvider.VotingLenient # Otherwise too few are returned, for both main and niche Explore menus, since new releases often have few votes.
		elif Media.isHome(niche):
			# Calendar endpoint.
			# Do not apply rating/votes filtering, not even VotingLenient, otherwise very few titles are returned for the past few months.
			# It seems that a lot of digital/physical release dates are only added after a few months.
			if Tools.isString(votes): votes = None # Reset from _voting().
		elif Media.isBest(niche):
			# Popularity endpoint.
			# Still contains low rated (5.0-7.5) titles, since the vote count contributes a lot to the popularity.
			if sort is None: sort = MetaTrakt.SortPopular
		elif Media.isWorst(niche):
			# Can't sort by lowest rating.
			# Just filter by low ratings.
			if rating is None: rating = [0.0, 4.0]
			if Tools.isString(votes): votes = 100 # Otherwise few titles are returned.
		elif Media.isPrestige(niche):
			# Popularity endpoint.
			# Still contains low rated (5.0-7.5) titles, since the vote count contributes a lot to the popularity.
			if sort is None: sort = MetaTrakt.SortPopular
		elif Media.isPopular(niche):
			# Popularity endpoint.
			if sort is None: sort = MetaTrakt.SortPopular
		elif Media.isUnpopular(niche):
			# Can't sort by lowest votes.
			# Just filter by low votes.
			if votes is None: votes = [0, 50]
		elif Media.isViewed(niche):
			# Played endpoint.
			if sort is None: sort = MetaTrakt.SortPlayed
		elif Media.isGross(niche):
			support = False
		elif Media.isAward(niche):
			support = False
		elif Media.isTrend(niche):
			if sort is None: sort = MetaTrakt.SortTrending

		if niche and not Tools.isArray(niche): niche = [niche]
		if strucuture:
			return {
				'support'		: support,
				'media'			: media,
				'medias'		: medias,
				'niche'			: niche,
				'query'			: query,
				'date'			: date,
				'year'			: year,
				'duration'		: duration,
				'genre'			: genre,
				'language'		: language,
				'country'		: country,
				'certificate'	: certificate,
				'status'		: status,
				'episode'		: episode,
				'studio'		: studio,
				'network'		: network,
				'rating'		: rating,
				'votes'			: votes,
				'sort'			: sort,
				'order'			: order,
				'filter'		: filter,
				'field'			: field,
				'list'			: list,
				'original'		: original,
			}
		else:
			return support, media, medias, niche, query, date, year, duration, genre, language, country, certificate, status, episode, studio, network, rating, votes, sort, order, filter, field, list, original

	def _parameterGenre(self, genres, result, ignore = None):
		for genre in genres:
			if (not ignore or not genre in ignore) and not genre in result:
				result.append(genre)
		return result

	def _parameterQuery(self, query = None, extra = None):
		result = None
		if query or extra:
			# Trakt uses Solr for the query. Escape special characters.
			# https://trakt.docs.apiary.io/#reference/search/text-query/get-text-query-results
			# https://solr.apache.org/guide/6_6/the-standard-query-parser.html
			if query: query = Regex.replace(data = query, expression = '([\+\-\!\(\)\{\}\[\]\^\"\~\*\?\:\/]|[\&\|]{2})', replacement = r'\\\1', group = None, all = True)

			# Although Trakt states in the docs that && and || are reserved Solr characters, often using them does not work and returns few results.
			# Use the Solr AND and OR instead, which seems to work better.
			# Update: This is probably not true, and/or Trakt has updated their API.
			# When we search with "AND" instead of "&&" we indeed get more results, but those are probably incorrect, probably because "AND" is seen as a search word, not an operator.
			# If this is ever changed back, test this:
			#	("tv" AND "movie") vs ("tv" && "movie") vs ("tv"&&"movie")
			# Besides AND/&& and OR/||, there are also other issues:
			#	1. Adding spaces before/after the operator vs no spaces returns different results, although these are only a few titles difference.
			#	2. Wrapping the keyword in quotes returns way more links (30x more) than without quotes. Not sure which one is correct.
			#	3. Not using brackets around the expression returns why less results, probably because it is seen as a normal search query.

			if extra:
				if not Tools.isArray(extra): extra = [extra]
				#extra = [('%s' if i.startswith('(') else '(%s)') % i.replace(' && ', ' AND ').replace(' || ', ' OR ') for i in extra]
				#extra = ' AND '.join(extra)
				extra = [('%s' if i.startswith('(') else '(%s)') % i for i in extra]
				extra = ' && '.join(extra)

			if not query: result = extra
			elif not extra: result = query
			#else: result = '%s AND %s' % (query, ('%s' if extra.startswith('(') else '(%s)') % extra)
			else: result = '%s && %s' % (query, ('%s' if extra.startswith('(') else '(%s)') % extra)
		return result

	def _parameterUser(self, user = None, id = None):
		if user is None and not Tools.isNumeric(str(id)): user = self.accountUser()
		elif user == MetaTrakt.ListOfficial: user = False
		elif user and user.lower() == self.id(): user = False # Official lists have "Trakt" as user.
		return user, id

	def _parameterSelect(self, value, select = None):
		if not select: select = ''
		if Tools.isArray(value): return [select + str(i) for i in value]
		else: return select + str(value)

	##############################################################################
	# COMPANY
	##############################################################################

	@classmethod
	def _companies(self):
		# This structure is too large to add as a global enum.
		# Otherwise importing this class has an initialization overhead.
		# Only create on demand.
		if MetaTrakt.Companies is None:
			from lib.meta.company import MetaCompany

			MetaTrakt.Companies = {
				MetaCompany.Company20thcentury : {
					MetaProvider.CompanyStudio	: ['50', '42', '95', '25519', '5039', '3965', '95378', '68257', '13260', '5168', '103387', '6254', '39950', '39532', '150785', '67348', '126816'],
					MetaProvider.CompanyNetwork	: [],
					MetaProvider.CompanyVendor	: ['1569'],
				},
				MetaCompany.CompanyAbc : {
					MetaProvider.CompanyStudio	: ['125476', '29', '3328', '457', '128742', '1178', '361', '3500', '36654', '496', '5647', '67160', '53385', '30451', '94804', '973', '38090', '177437', '162298', '1154'],
					MetaProvider.CompanyNetwork	: ['16', '9', '425', '1561', '986', '1754', '2931'],
					MetaProvider.CompanyVendor	: ['2260', '808'],
				},
				MetaCompany.CompanyAe : {
					MetaProvider.CompanyStudio	: ['1072', '7913', '20259', '38080', '100570', '182433', '129828'],
					MetaProvider.CompanyNetwork	: ['44', '1752', '2547', '2226', '2742', '2495', '3624', '3216'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyAcorn : {
					MetaProvider.CompanyStudio	: ['2341', '161589', '136323'],
					MetaProvider.CompanyNetwork	: ['557', '2316', '2288'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyAdultswim : {
					MetaProvider.CompanyStudio	: ['259', '12260', '89195'],
					MetaProvider.CompanyNetwork	: ['104', '3571', '2334', '3020'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyAmazon : {
					MetaProvider.CompanyStudio	: ['179', '158509'],
					MetaProvider.CompanyNetwork	: ['47', '2501', '2392', '2256', '3205', '3596', '2385', '2385', '2214'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyAmc : {
					MetaProvider.CompanyStudio	: ['289', '3789', '2808', '18519', '11389', '11703', '10257', '159017', '12295', '65890'],
					MetaProvider.CompanyNetwork	: ['107', '194', '467', '173', '153', '546', '1955', '1858', '2768', '151', '3647', '1761'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyApple : {
					MetaProvider.CompanyStudio	: ['142848'],
					MetaProvider.CompanyNetwork	: ['256'],
					MetaProvider.CompanyVendor	: ['685', '638'],
				},
				MetaCompany.CompanyArd : {
					MetaProvider.CompanyStudio	: ['1629', '1187', '2919', '2916', '2918', '1587', '10128', '1371', '269', '5018', '26657', '9198', '7954', '3373', '2292', '14182', '22344', '6988', '69625', '15170', '30132', '22294', '97309', '12989', '89260', '153470'],
					MetaProvider.CompanyNetwork	: ['265', '268', '270', '568', '492', '271', '106', '345', '654', '346', '76638', '871', '269', '428', '2325', '3417', '2507', '2070', '2995', '1804', '2595', '1703', '1594', '3143', '2814', '3843', '2071', '3635', '3195', '2883'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyAubc : {
					MetaProvider.CompanyStudio	: ['401', '426', '166275', '108530'],
					MetaProvider.CompanyNetwork	: ['60', '138', '135', '193', '2057', '1327', '141', '1228'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyBbc : {
					MetaProvider.CompanyStudio	: ['1149', '3510', '1012', '1200', '3383', '2080', '2080', '13491', '120', '114813', '2032', '27566', '11055', '57894', '13992', '2807', '1442', '91307', '2808', '2873', '1895', '2253', '50067', '76598', '108941', '88204', '38914', '108532', '30777', '20472', '30777', '85965', '33592', '104679', '2748', '219', '1763', '41817', '32272', '17351', '81883', '70448', '70448', '18003', '73598', '165545', '162938', '72707', '70416', '171670', '138224', '104679', '84100', '47824', '170766', '167937', '10236', '61433', '33006', '165372', '146600', '109660', '95633', '66174', '56143', '126759', '126758'],
					MetaProvider.CompanyNetwork	: ['77', '33', '121', '278', '137', '486', '616', '909', '279', '173', '618', '455', '736', '2689', '2607', '3001', '1118', '3172', '1127', '460', '2179', '3242', '2857', '2625', '2402', '838', '3709', '3688', '3592', '3568', '3071', '3048', '2319', '2191', '900', '899', '3718', '3717', '246', '2448', '2186', '1992', '1692', '1598', '1217', '1076'],
					MetaProvider.CompanyVendor	: ['3501', '1661'],
				},
				MetaCompany.CompanyBoomerang : {
					MetaProvider.CompanyStudio	: [],
					MetaProvider.CompanyNetwork	: ['254', '2257', '3600', '3066'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyBravo : {
					MetaProvider.CompanyStudio	: ['38665', '1920', '157883', '43510'],
					MetaProvider.CompanyNetwork	: ['84', '117'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyBritbox : {
					MetaProvider.CompanyStudio	: [],
					MetaProvider.CompanyNetwork	: ['553'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyCartoonnet : {
					MetaProvider.CompanyStudio	: ['1321', '129704', '1329', '40089', '96727'],
					MetaProvider.CompanyNetwork	: ['120', '1061', '234', '1945', '2979', '1151', '1209', '3204', '3788', '3191', '3164', '3008', '2665', '2582', '1388', '1386', '989', '2518', '1961', '1882'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyCbc : {
					MetaProvider.CompanyStudio	: ['900', '106097'],
					MetaProvider.CompanyNetwork	: ['97', '163', '1686', '1747', '3881'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyCbs : {
					MetaProvider.CompanyStudio	: ['733', '203', '738', '33269', '77016', '4493', '40809', '168927', '75125', '24674', '1744', '173345', '3159', '121407', '19212', '139167', '100902'],
					MetaProvider.CompanyNetwork	: ['22', '149', '818', '2477', '1725', '4001', '839', '3736', '2511', '1226'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyChannel4 : {
					MetaProvider.CompanyStudio	: ['1328', '5512', '3661', '4500', '129465', '52611'],
					MetaProvider.CompanyNetwork	: ['150', '294', '124', '718', '3285', '2889'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyChannel5 : {
					MetaProvider.CompanyStudio	: ['2995', '66981'],
					MetaProvider.CompanyNetwork	: ['409', '511', '2205', '3593', '916', '3939', '2005', '3326', '2676', '2165', '1999'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyCineflix : {
					MetaProvider.CompanyStudio	: ['1654'],
					MetaProvider.CompanyNetwork	: [],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyCinemax : {
					MetaProvider.CompanyStudio	: ['3190', '41495', '34297'],
					MetaProvider.CompanyNetwork	: ['52'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyColumbia : {
					MetaProvider.CompanyStudio	: ['865', '69', '443', '10649', '9766', '21614', '13897', '13366', '14283', '45819', '26163', '28419', '30269', '21402', '115848'],
					MetaProvider.CompanyNetwork	: [],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyComedycen : {
					MetaProvider.CompanyStudio	: ['1663', '5444'],
					MetaProvider.CompanyNetwork	: ['45', '649', '903', '841', '604', '1528', '1117', '2626', '2096', '2065', '1313', '1573', '950', '3981', '2492', '1728', '2757'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyConstantin : {
					MetaProvider.CompanyStudio	: ['1829', '1579', '44700', '151477'],
					MetaProvider.CompanyNetwork	: [],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyCrave : {
					MetaProvider.CompanyStudio	: ['4785', '106096'],
					MetaProvider.CompanyNetwork	: ['401', '935', '3652'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyCrunchyroll : {
					MetaProvider.CompanyStudio	: ['15770', '147379', '155485'],
					MetaProvider.CompanyNetwork	: ['502'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyCw : {
					MetaProvider.CompanyStudio	: [],
					MetaProvider.CompanyNetwork	: ['18', '640', '843', '1762', '3970', '3377'],
					MetaProvider.CompanyVendor	: ['945'],
				},
				MetaCompany.CompanyDarkhorse : {
					MetaProvider.CompanyStudio	: ['696', '61823'],
					MetaProvider.CompanyNetwork	: [],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyDccomics : {
					MetaProvider.CompanyStudio	: ['167', '60', '134194', '26741', '121146'],
					MetaProvider.CompanyNetwork	: [],
					MetaProvider.CompanyVendor	: ['36'],
				},
				MetaCompany.CompanyDimension : {
					MetaProvider.CompanyStudio	: ['2247', '1503'],
					MetaProvider.CompanyNetwork	: [],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyDiscovery : {
					MetaProvider.CompanyStudio	: ['2069', '3313', '20112', '17469', '1786', '7638', '43448', '1061', '72759', '67423'],
					MetaProvider.CompanyNetwork	: ['108', '248', '1662', '725', '314', '1937', '352', '1993', '1807', '1695', '601', '1971', '628', '728', '1541', '1826', '2219', '762', '733', '2200', '228', '2042', '315', '2025', '2668', '2599', '2283', '2884', '1968', '1165', '3038', '1749', '952', '2916', '2589', '1733', '1321', '3316', '3151', '3138', '2604', '2516', '2483', '2398', '2309', '1967', '3041', '2386', '2308', '1392', '1343', '1279'],
					MetaProvider.CompanyVendor	: ['2087'],
				},
				MetaCompany.CompanyDisney : {
					MetaProvider.CompanyStudio	: ['897', '3542', '244', '145', '4156', '9882', '6809', '114864', '76390', '120781', '5677', '12814', '33725', '80365', '113755', '9951', '9951', '23614', '74559', '128651', '11001', '90039', '116243', '17991', '15644', '126396', '74242', '173936', '151455', '134465', '117047', '93807', '74241', '162834', '127553'],
					MetaProvider.CompanyNetwork	: ['41', '93', '105', '48', '133', '760', '2026', '1536', '176', '798', '2567', '1368', '1265', '1530', '2566', '1951', '853', '1189', '606', '1744', '1603', '3331', '2766', '2478', '2286', '2077', '1948', '3744', '3622', '3119', '2845', '2835', '2692', '2418', '2107', '171', '1519', '3710', '2716', '2597', '2519', '2282', '2018', '1845', '1837', '1433', '1316'],
					MetaProvider.CompanyVendor	: ['2357'],
				},
				MetaCompany.CompanyDreamworks : {
					MetaProvider.CompanyStudio	: ['249', '335', '252', '56', '12040'],
					MetaProvider.CompanyNetwork	: [],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyFacebook : {
					MetaProvider.CompanyStudio	: [],
					MetaProvider.CompanyNetwork	: ['434', '1002', '1738'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyFox : {
					MetaProvider.CompanyStudio	: ['50', '42', '4413', '5039', '3965', '6068', '16', '1570', '1570', '68257', '107', '17', '9574', '106306', '20983', '5168', '112608', '144304', '110', '7', '1780', '2998', '4213', '7531', '593', '155752', '6254', '155810', '137334', '155817', '155821', '155809', '11610', '84751', '68794', '150785', '109665', '155826', '155818', '136447', '131257'],
					MetaProvider.CompanyNetwork	: ['5', '29', '7', '1045', '2109', '11', '10', '326', '25', '1315', '764', '35', '28', '2743', '13', '1175', '484', '26', '2569', '24', '2413', '574', '32', '2805', '2164', '1958', '1902', '1181', '1174', '1079', '734', '388', '3199', '2526', '23', '2259', '2108', '1981', '1936', '12', '829', '2263', '1901'],
					MetaProvider.CompanyVendor	: ['1653'],
				},
				MetaCompany.CompanyFreevee : {
					MetaProvider.CompanyStudio	: [],
					MetaProvider.CompanyNetwork	: ['2392', '1628', '3205', '923', '3596', '2230', '1517'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyFx : {
					MetaProvider.CompanyStudio	: ['4'],
					MetaProvider.CompanyNetwork	: ['2', '4', '1885', '2409', '1642'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyGaumont : {
					MetaProvider.CompanyStudio	: ['1995', '4871', '2805', '78921', '5310', '1941', '4745', '22722', '630', '159271', '1945', '154611', '69335', '8267', '15543', '22325', '40478', '88654', '91022', '33189', '150081'],
					MetaProvider.CompanyNetwork	: [],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyGoogle : {
					MetaProvider.CompanyStudio	: ['49108'],
					MetaProvider.CompanyNetwork	: ['1446'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyHayu : {
					MetaProvider.CompanyStudio	: [],
					MetaProvider.CompanyNetwork	: [],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyHbo : {
					MetaProvider.CompanyStudio	: ['1030', '2764', '2531', '6471', '2866', '1357', '1357', '88810', '81327', '32065', '2205', '83538', '721'],
					MetaProvider.CompanyNetwork	: ['1', '514', '2934', '2224', '487', '1355', '212', '2227', '340', '3563', '1364', '83', '3897', '2228', '1585', '244', '3826', '2346', '2358', '3757', '2351', '3551', '2844', '2394', '2360', '1780', '1098', '3564'],
					MetaProvider.CompanyVendor	: ['487', '1355', '212', '340', '1364', '83', '244', '2360', '1780'],
				},
				MetaCompany.CompanyHistory : {
					MetaProvider.CompanyStudio	: ['13860'],
					MetaProvider.CompanyNetwork	: ['198', '1000', '1334', '293', '1715', '1018', '3673', '2711', '2664', '2455', '1400', '1373'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyHulu : {
					MetaProvider.CompanyStudio	: [],
					MetaProvider.CompanyNetwork	: ['87', '635', '3710'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyItv : {
					MetaProvider.CompanyStudio	: ['2394', '1332', '22623', '194', '14352', '19698', '71', '2367', '2365', '2365', '12737', '489', '2236', '116493', '69163', '82190', '16749', '56999', '43445', '2366', '112075', '102835'],
					MetaProvider.CompanyNetwork	: ['68', '207', '167', '2502', '1138', '318', '605', '3579', '1001', '329', '113', '3435', '3877', '3590', '2369'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyLionsgate : {
					MetaProvider.CompanyStudio	: ['538', '12', '4867', '19564', '102047', '173996', '173852'],
					MetaProvider.CompanyNetwork	: ['2229', '2701', '3632', '3166', '2638'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyLucasfilm : {
					MetaProvider.CompanyStudio	: ['174', '186'],
					MetaProvider.CompanyNetwork	: [],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyMarvel : {
					MetaProvider.CompanyStudio	: ['181', '183', '46', '974', '146', '7159', '45', '109306', '3225', '2483'],
					MetaProvider.CompanyNetwork	: [],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyMgm : {
					MetaProvider.CompanyStudio	: ['123', '236', '158509', '9864', '21264', '81503', '2269', '83', '29551', '1463', '140095', '89259', '72762', '64428', '160118', '26288', '21495'],
					MetaProvider.CompanyNetwork	: ['334', '2639', '3159', '1991'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyMiramax : {
					MetaProvider.CompanyStudio	: ['332'],
					MetaProvider.CompanyNetwork	: [],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyMtv : {
					MetaProvider.CompanyStudio	: ['3537', '10908', '2363', '3520', '97024', '1456', '23361', '2364', '23548', '23318', '27021', '2491', '1457', '78156', '171314', '61353', '131403'],
					MetaProvider.CompanyNetwork	: ['94', '390', '459', '488', '1233', '1004', '1112', '1013', '1048', '958', '912', '1073', '646', '2564', '1157', '3002', '2517', '1776', '1689', '3299', '2720', '2719', '2718'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyNationalgeo : {
					MetaProvider.CompanyStudio	: ['1392', '2321', '138750', '138750', '127133'],
					MetaProvider.CompanyNetwork	: ['80', '185', '567', '1880', '1755', '446', '1985', '3315', '1557', '2914', '2403', '3726', '3247', '3137', '3024', '1756', '2382'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyNbc : {
					MetaProvider.CompanyStudio	: ['8037', '1311', '313', '1071', '304', '2443', '7862', '111102', '44641', '1896', '2756', '155816', '70892', '75288', '41837', '138024'],
					MetaProvider.CompanyNetwork	: ['21'],
					MetaProvider.CompanyVendor	: ['209', '469', '201', '3414', '2602', '1671'],
				},
				MetaCompany.CompanyNetflix : {
					MetaProvider.CompanyStudio	: ['127791', '120480'],
					MetaProvider.CompanyNetwork	: ['53', '1465'],
					MetaProvider.CompanyVendor	: ['53', '1465'],
				},
				MetaCompany.CompanyNewline : {
					MetaProvider.CompanyStudio	: ['1227', '5610', '2191'],
					MetaProvider.CompanyNetwork	: [],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyNickelodeon : {
					MetaProvider.CompanyStudio	: ['1119', '1533', '4568', '84694', '151752', '24136', '70634'],
					MetaProvider.CompanyNetwork	: ['230', '330', '403', '761', '612', '999', '845', '2755', '1036', '3559', '281', '231', '1135', '877', '2823', '1439', '1121', '3903', '3782', '3697', '1719', '1711', '2922', '1438', '1026'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyParamount : {
					MetaProvider.CompanyStudio	: ['455', '352', '7085', '5793', '4071', '41123', '44425', '168927', '4569', '150364', '3130', '22388', '12500', '13240', '163403', '151215', '151548', '45935', '91489', '137858'],
					MetaProvider.CompanyNetwork	: ['34', '1623', '2579', '118', '2232', '2269', '2239', '2790', '2876', '1778', '2631', '440', '3097', '1324', '614', '2605', '2005', '2970', '2444'],
					MetaProvider.CompanyVendor	: ['1111', '3354', '2192', '1989'],
				},
				MetaCompany.CompanyPeacock : {
					MetaProvider.CompanyStudio	: ['19161'],
					MetaProvider.CompanyNetwork	: ['550', '3027'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyPhilo : {
					MetaProvider.CompanyStudio	: [],
					MetaProvider.CompanyNetwork	: [],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyPixar : {
					MetaProvider.CompanyStudio	: ['1690'],
					MetaProvider.CompanyNetwork	: [],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyPluto : {
					MetaProvider.CompanyStudio	: [],
					MetaProvider.CompanyNetwork	: ['744', '3133'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyRegency : {
					MetaProvider.CompanyStudio	: ['4659', '4662', '2589', '5947', '13896', '15831'],
					MetaProvider.CompanyNetwork	: [],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyRko : {
					MetaProvider.CompanyStudio	: ['3490', '17058', '7103', '17698', '117985'],
					MetaProvider.CompanyNetwork	: [],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyRoku : {
					MetaProvider.CompanyStudio	: [],
					MetaProvider.CompanyNetwork	: ['3853', '1867'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyScreengems : {
					MetaProvider.CompanyStudio	: ['391', '376', '59039', '51582'],
					MetaProvider.CompanyNetwork	: [],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyShowtime : {
					MetaProvider.CompanyStudio	: ['191', '43380', '125949', '25867', '12808', '36301', '69830'],
					MetaProvider.CompanyNetwork	: ['50', '2737', '326', '2876', '1834', '42814'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanySky : {
					MetaProvider.CompanyStudio	: ['1208', '78934', '75014', '136528', '12080', '3192', '9581', '7006', '2779', '32502', '2276', '74838', '8184', '46389', '1874', '162046', '65407', '16105', '65406', '166142', '115008'],
					MetaProvider.CompanyNetwork	: ['187', '695', '284', '1022', '2082', '617', '1601', '750', '1682', '1071', '583', '496', '1046', '2737', '678', '2347', '2237', '2050', '1424', '1996', '3346', '2496', '1159', '802', '545', '891', '3179', '2421', '3823', '3817', '3685', '3597', '3070', '2953', '2464', '2100', '1116', '3550', '2905', '2521', '2372', '2292', '2241'],
					MetaProvider.CompanyVendor	: ['2680', '3914', '3813', '949'],
				},
				MetaCompany.CompanySony : {
					MetaProvider.CompanyStudio	: ['8', '11799', '1968', '3342', '2305', '10723', '10753', '6617', '2392', '48497', '105856', '20585', '27372', '2457', '1929', '75899', '41016', '168161', '36601', '144379', '11918', '173773', '80195'],
					MetaProvider.CompanyNetwork	: ['309', '1322', '1051', '3025', '2379', '3797', '3755', '3501', '3378', '3335', '3213'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyStarz : {
					MetaProvider.CompanyStudio	: ['19655'],
					MetaProvider.CompanyNetwork	: ['272', '2700', '1053', '3323', '2270', '2298'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanySyfy : {
					MetaProvider.CompanyStudio	: ['253', '1871', '17816'],
					MetaProvider.CompanyNetwork	: ['17', '2167', '1219'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyTbs : {
					MetaProvider.CompanyStudio	: ['38744', '53929', '110634', '45876'],
					MetaProvider.CompanyNetwork	: ['161', '3572', '2514', '3899', '3682', '2909', '1953', '1892'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyTnt : {
					MetaProvider.CompanyStudio	: ['2027', '5006', '15890'],
					MetaProvider.CompanyNetwork	: ['382', '320', '1356', '1110', '497', '910', '3117'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyTouchstone : {
					MetaProvider.CompanyStudio	: ['3800', '32'],
					MetaProvider.CompanyNetwork	: [],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyTristar : {
					MetaProvider.CompanyStudio	: ['3595', '443', '188', '21614', '14283', '82509', '21402', '140649'],
					MetaProvider.CompanyNetwork	: [],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyTrutv : {
					MetaProvider.CompanyStudio	: [],
					MetaProvider.CompanyNetwork	: ['69', '1522'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyTubi : {
					MetaProvider.CompanyStudio	: [],
					MetaProvider.CompanyNetwork	: ['2166'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyTurner : {
					MetaProvider.CompanyStudio	: ['2027', '8665', '1523', '2762', '66219', '31337', '69727', '69654', '58702', '54310'],
					MetaProvider.CompanyNetwork	: [],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyUniversal : {
					MetaProvider.CompanyStudio	: ['937', '64', '3565', '21822', '189', '4492', '28448', '7331', '23680', '1071', '34467', '839', '67776', '1361', '293', '2443', '1896', '30650', '11852', '155816', '70892', '31159', '35010', '98984', '98983', '75288', '69970', '40271', '29867', '145816', '31546', '79732', '134886', '13486', '114586'],
					MetaProvider.CompanyNetwork	: ['145', '1458', '859', '3613', '1449', '1192'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyUsa : {
					MetaProvider.CompanyStudio	: ['312', '57011', '6648', '18350', '8505', '67775', '0016587'],
					MetaProvider.CompanyNetwork	: ['51'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyWarner : {
					MetaProvider.CompanyStudio	: ['113', '51', '76', '4615', '3062', '4841', '512', '5342', '9955', '7241', '15782', '21788', '7835', '4757', '998', '59370', '51994', '14866', '2297', '131941', '6863', '28691', '555', '37897', '83538', '75435', '2461', '147701', '113193', '63462', '61428', '137523', '48347', '131813', '161686', '139432'],
					MetaProvider.CompanyNetwork	: ['27', '2570', '2343', '2218', '3178', '2993', '2982', '2549', '1588'],
					MetaProvider.CompanyVendor	: ['2097', '1549'],
				},
				MetaCompany.CompanyWeinstein : {
					MetaProvider.CompanyStudio	: ['613'],
					MetaProvider.CompanyNetwork	: [],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyYoutube : {
					MetaProvider.CompanyStudio	: ['10650', '93922', '3067'],
					MetaProvider.CompanyNetwork	: ['49', '240', '1205', '2908', '2907', '2248', '2149'],
					MetaProvider.CompanyVendor	: [],
				},
				MetaCompany.CompanyZdf : {
					MetaProvider.CompanyStudio	: ['1628', '5028', '12725', '175124', '175071', '136686'],
					MetaProvider.CompanyNetwork	: ['139', '268', '178', '482', '2325', '1201', '3861', '2704'],
					MetaProvider.CompanyVendor	: [],
				},
			}
		return MetaTrakt.Companies

	##############################################################################
	# CONVERT
	##############################################################################

	@classmethod
	def _convertCompanies(self, media = None, niche = None, company = None, studio = None, network = None, inverse = False, default = None):
		company = self.company(niche = niche, company = company, studio = studio, network = network)
		if not company: return None, None

		typeStudio = {
			MetaProvider.CompanyStudio : True,
			MetaProvider.CompanyProducer : True,
			MetaProvider.CompanyDistributor : True,
			MetaProvider.CompanyBroadcaster : True,
			MetaProvider.CompanyOriginal : True,
		}
		typeNetwork = {
			MetaProvider.CompanyNetwork : True,
			MetaProvider.CompanyVendor : True,
			MetaProvider.CompanyDistributor : True,
			MetaProvider.CompanyBroadcaster : True,
		}
		typeBase = {
			MetaProvider.CompanyStudio : MetaProvider.CompanyStudio,
			MetaProvider.CompanyNetwork : MetaProvider.CompanyNetwork,
			MetaProvider.CompanyVendor : MetaProvider.CompanyVendor,
			MetaProvider.CompanyProducer : MetaProvider.CompanyStudio,
			MetaProvider.CompanyBroadcaster : MetaProvider.CompanyNetwork,
			MetaProvider.CompanyDistributor : MetaProvider.CompanyNetwork,
			MetaProvider.CompanyOriginal : MetaProvider.CompanyStudio,
		}

		types = {MetaProvider.CompanyStudio : 0, MetaProvider.CompanyNetwork : 0}
		companies = {MetaProvider.CompanyStudio : [], MetaProvider.CompanyNetwork : []}

		for k, v in company.items():
			for i in v:
				type = []
				if not i:
					type.append(MetaProvider.CompanyStudio)
				else:
					if i in typeStudio:
						types[typeBase[i]] += 1
						type.append(MetaProvider.CompanyStudio)
					if i in typeNetwork and (media is None or Media.isSerie(media)): # Only Shows/episodes support the network_ids parameter. For movies, the parameter is ignore and all movies are returned.
						types[typeBase[i]] += 1
						type.append(MetaProvider.CompanyNetwork)

				for j in type:
					value = self._convertCompany(company = [k, j])
					if value: companies[j].extend(value)
					elif Tools.isNumeric(k): companies[j].append(k)

		# Trakt uses different parameters for the studio and network.
		# Only pass in one type, otherwise too few results are returned if both are passed.
		if not companies[MetaProvider.CompanyStudio] and not companies[MetaProvider.CompanyNetwork]: return None, None
		elif types[MetaProvider.CompanyStudio] > types[MetaProvider.CompanyNetwork]: return companies[MetaProvider.CompanyStudio], None
		elif types[MetaProvider.CompanyNetwork] > types[MetaProvider.CompanyStudio]: return None, companies[MetaProvider.CompanyNetwork]
		elif len(companies[MetaProvider.CompanyStudio]) >= len(companies[MetaProvider.CompanyNetwork]): return companies[MetaProvider.CompanyStudio], None
		else: return None, companies[MetaProvider.CompanyNetwork]

	##############################################################################
	# EXTRACT
	##############################################################################

	def _extract(self, data, media, niche = None, extract = True, **parameters):
		values = data.get('data')
		if values:
			if extract:
				if Tools.isDictionary(values) and ('ids' in values or 'distribution' in values):
					return self._extractSingle(data = data, media = media, niche = niche, **parameters)
				else:
					return self._extractMulti(data = data, media = media, niche = niche, **parameters)
			else:
				return values
		return None

	def _extractType(self, data):
		if Tools.isDictionary(data) and 'data' in data: data = data['data']
		item = data[0] if Tools.isArray(data) else data
		type = item.get('type')

		if type:
			if 'privacy' in item: type = MetaTrakt.TypeList
		else:
			if 'title' in item:
				if not 'ids' in item:
					if 'language' in item:
						type = MetaTrakt.TypeTranslation
					elif 'country' in item:
						type = MetaTrakt.TypeAlias
			else:
				if MetaTrakt.TypePerson in item or MetaTrakt.DivisionCast in item or MetaTrakt.DivisionCrew in item:
					type = MetaTrakt.TypePerson
				elif MetaTrakt.TypeList in item:
					type = MetaTrakt.TypeList
				elif 'name' in item:
					if 'biography' in item or 'gender' in item: type = MetaTrakt.TypePerson
					elif 'privacy' in item: type = MetaTrakt.TypeList
					elif 'country' in item: type = MetaTrakt.TypeStudio
					else: type = MetaTrakt.TypePerson
				elif 'release_type' in item:
					type = MetaTrakt.TypeRelease
				elif 'distribution' in item:
					type = MetaTrakt.TypeRating

		return type

	def _extractItem(self, data, media, niche, **parameters):
		type = self._extractType(data = data)

		if type == MetaTrakt.TypePerson: result = self._extractPerson(data = data, media = media, **parameters)
		elif type == MetaTrakt.TypeStudio: result = self._extractStudio(data = data, media = media, **parameters)
		elif type == MetaTrakt.TypeRelease: result = self._extractRelease(data = data)
		elif type == MetaTrakt.TypeTranslation: result = self._extractTranslation(data = data)
		elif type == MetaTrakt.TypeAlias: result = self._extractAlias(data = data)
		elif type == MetaTrakt.TypeRating: result = self._extractRating(data = data)
		elif type == MetaTrakt.TypeList: result = self._extractList(data = data, media = media, **parameters)
		else: result = self._extractTitle(data = data, media = media, niche = niche, **parameters)

		# If we retrieve all episodes of a show, it uses a season endpoint, but the extracted items are episodes.
		# Only change after extraction, since we also want to extract the season IDs for packs().
		if Media.isSeason(media) and parameters:
			extended = parameters.get('extended')
			if extended and MetaTrakt.ExtendedEpisode in extended: media = Media.Episode

		# Update (2025-12):
		# Trakt now returns images with some list endpoints, like "popular", even though the images were not requested.
		# This causes the list returned to the menus to contain image dictionaries which then cause various errors because they cannot be merged and Tools.listUnique().
		# Remove these images from list entries and only allow if a specific movie/show/season/episode/person is requested.
		try:
			try: image = MetaTrakt.ExtendedImages in parameters['extended']
			except: image = False
			if not image:
				for i in result if Tools.isArray(result) else [result]:
					try: del i[MetaImage.Attribute]
					except: pass
		except: Logger.error()

		# Aggregate metadata.
		if result and not type in [MetaTrakt.TypeRelease, MetaTrakt.TypeTranslation, MetaTrakt.TypeAlias, MetaTrakt.TypeRating]:
			for i in result if Tools.isArray(result) else [result]:
				entity = type in [MetaTrakt.TypePerson, MetaTrakt.TypeStudio]
				if entity:
					self._dataSet(item = i, key = 'media', value = self.mMetatools.media(metadata = i, media = Media.Person if type == MetaTrakt.TypePerson else Media.Company if type == MetaTrakt.TypeStudio else media))
				else:
					self._dataSet(item = i, key = 'media', value = self.mMetatools.media(metadata = i, media = media))
					self._dataSet(item = i, key = 'niche', value = self.mMetatools.niche(metadata = i, media = media, niche = niche))
				self._dataSet(item = i, value = {k : v for k, v in i.get('id', {}).items() if not Tools.isDictionary(v)})
				if not entity:
					self._dataSet(item = i, key = 'time', value = self._temp(item = i, key = 'time', default = {}))
					if not type == MetaTrakt.TypeList:
						rating = self._temp(item = i, key = ['voting', 'rating'])
						if not rating is None: self._dataSet(item = i, key = 'rating', value = rating)
						votes = self._temp(item = i, key = ['voting', 'votes'])
						if not votes is None: self._dataSet(item = i, key = 'votes', value = votes)

		return result

	def _extractSingle(self, data, media, niche, **parameters):
		return self._extractItem(data = data['data'], media = media, niche = niche, **parameters)

	def _extractMulti(self, data, media, niche, **parameters):
		type = self._extractType(data = data['data'])
		if type == MetaTrakt.TypePerson and Tools.isDictionary(data['data']):
			# Discover by person ID or title details for people.
			# The "cast" object has titles listed directly under it.
			# The "crew" object has further subcategory objects under it (eg: production, writing, etc).
			result = []
			for division, v1 in data['data'].items():
				if Tools.isArray(v1):
					for i in range(len(v1)):
						v1[i].update({
							'division' : division,
							'order' : i,
						})
					result.extend(v1)
				elif Tools.isDictionary(v1):
					for department, v2 in v1.items():
						for i in range(len(v2)):
							v2[i].update({
								'division' : division,
								'department' : department,
								'order' : i,
							})
						result.extend(v2)
			items = result
		else: items = data['data']

		results = []
		if items:
			for item in items:
				try:
					result = self._extractItem(data = item, media = media, niche = niche, **parameters)
					if result:
						if Tools.isArray(result): results.extend(result)
						else: results.append(result)
				except: self._logError()

		return self._extractMeta(items = results, headers = data['headers'])

	def _extractBase(self, data):
		try:
			# Important to remove the time dictionary.
			# Otherwise if some future episodes in the season do not have a date yet, it will use the season's premiere date for the episodes' dates instead.
			# This incorrect date will cause issues in MetaPack, such as making the release interval "daily", which should rather use the dates from TVDb if they are available there.
			item = Tools.copy(data)
			for k in ['title', 'originaltitle', 'year', 'tagline', 'plot', 'status', 'duration', 'rating', 'userrating', 'votes', 'trailer', 'homepage', 'premiered', 'aired', 'time']:
				try: del item[k]
				except: pass
			return item
		except: self._logError()
		return None

	def _extractId(self, data = None, **parameters):
		result = {}
		types = ('imdb', 'tmdb', 'tvdb', 'trakt', 'tvrage', 'slug')

		if data:
			ids = data.get('ids')
			if ids:
				for i in types:
					id = ids.get(i)
					if id: result[i] = str(id)

			# Sets (official Trakt lists) often contain the TMDb collection link in the description.
			if not result.get('tmdb'):
				description = (data.get(data.get('type')) or data).get('description')
				if description:
					id = Regex.extract(data = description, expression = 'themoviedb\.org\/collection\/(\d+)')
					if id: result['tmdb'] = str(id)

		# If IDs are missing, add them from the request parameters.
		# This is useful of Trakt does not have an IMDb/TVDb ID yet, and a title lookup is done.
		if parameters:
			for i in types:
				if not result.get(i) and parameters.get(i): result[i] = str(parameters.get(i))

		return result

	def _extractDescription(self, data):
		if data:
			# Might look like a space, but is a different UTF character (U+00A0 or U+200B).
			# Eg: The biography of Jeff Devlin (Trakt ID: 2828485).
			data = data.replace(' ', ' ').replace('​', ' ')

			# Sets (official Trakt lists) often contain the TMDb collection link in the description. Remove it.
			# Eg: The Transformers series follows the continuing battle between the Autobots and the Decepticons and ultimately, the triumph of good over evil. This collection includes theatrically released films of the Transformers saga only.https://themoviedb.org/collection/8650
			data = Regex.remove(data = data, expression = 'http\S+', all = True, flags = Regex.FlagCaseInsensitive | Regex.FlagAllLines)

			data = data.strip()
		return data

	def _extractLink(self, data):
		# Trakt has now removed the https:// protocol for trailer and homepage URLs.
		if data and not data.startswith('http'): data = 'https://' + data
		return data

	def _extractProfession(self, data):
		base = {}

		person = data.get('person')
		cast = bool(data.get('characters') or data.get('character'))
		crew = bool(data.get('jobs') or data.get('job'))

		episodes = data.get('episode_count', 0) # How many episodes of the show were directed or acted in by a person.
		order = (episodes * 100000) + (10000 - data.get('order', 0))

		role = None
		division = data.get('division')
		if division == MetaTrakt.DivisionGuest:
			role = MetaTrakt.RoleGuest
			division = MetaTrakt.DivisionCast
		elif not division:
			if cast: division = MetaTrakt.DivisionCast
			elif crew: division = MetaTrakt.DivisionCrew
		if division:
			if not role and division == MetaTrakt.DivisionCast: role = MetaTrakt.RoleStar
			base['division'] = division.strip().lower()

		if role == MetaTrakt.RoleStar: order += 2000000
		elif role == MetaTrakt.RoleGuest: order += 1000000

		department = data.get('department')
		if not department:
			department = data.get('known_for_department')
			if not department and person: department = person.get('known_for_department')
		if not department and cast: department = MetaTrakt.DepartmentActing
		if department: base['department'] = department.strip().lower()

		job = data.get('jobs')
		if not job:
			job = data.get('job')
			job = [job] if job else None
		if not job:
			if cast: job = [MetaTrakt.JobActor]
		if job: job = [i.strip().lower() for i in job]

		character = data.get('characters')
		if not character:
			character = data.get('character')
			character = [character] if character else None
		if character: character = [i.strip().title() for i in character]

		count = 0
		if job: count = max(count, len(job))
		if character: count = max(count, len(character))
		if not count and base: count = 1 # Only contains known_for_department.

		result = []
		for i in range(count):
			entry = Tools.copy(base)
			if job: entry['job'] = job[min(len(job) - 1, i)]
			if role: entry['role'] = role
			if character: entry['character'] = character[min(len(character) - 1, i)]
			entry['order'] = order
			result.append(entry)

		return result or None

	def _extractTime(self, data):
		try:
			result = {}
			times = {
				MetaTools.TimeAdded		: ['created_at', 'listed_at', 'collected_at'], # Time added to list. Not documented.
				MetaTools.TimeUpdated	: ['updated_at', 'listed_at', 'collected_at'],
				MetaTools.TimeWatched	: ['watched_at'],
				MetaTools.TimeRewatched	: ['reset_at'], # It seems that reset_at is always null.
				MetaTools.TimePaused	: ['paused_at'],
				MetaTools.TimeExpired	: ['expires_at'],
				MetaTools.TimeRated		: ['rated_at'],
				MetaTools.TimeCollected	: ['collected_at'],
			}
			for k, v in times.items():
				for i in v:
					try: time = Time.timestamp(fixedTime = data['last_' + i], iso = True) # Eg: last_updated_at
					except:
						try: time = Time.timestamp(fixedTime = data[i], iso = True)
						except: time = None
					if time: break
				if time: result[k] = time
			if result: return result
		except: self._logError()
		return None

	def _extractMeta(self, items, headers):
		try:
			if items:
				meta = {}

				private = headers.get('x-private-user')
				if private: meta['private'] = Converter.boolean(private)

				count = headers.get('x-pagination-item-count')
				if count: meta['items'] = int(count)

				pages = headers.get('x-pagination-page-count')
				if pages: meta['pages'] = int(pages)

				page = headers.get('x-pagination-page')
				if page: meta['page'] = int(page)

				limit = headers.get('x-pagination-limit')
				if limit: meta['limit'] = int(limit)

				sort = headers.get('x-sort-by') # Default sort method specified by the user in the list settings.
				if sort: meta['sort'] = sort

				order = headers.get('x-sort-how') # Default sort order specified by the user in the list settings.
				if order: meta['order'] = order

				sorted = headers.get('x-applied-sort-by') # Actual sort method applied by the API.
				if sorted: meta['sorted'] = sorted

				ordered = headers.get('x-applied-sort-how') # Actual sort order applied by the API.
				if ordered: meta['ordered'] = ordered

				if meta:
					for item in items: self._tempSet(item = item, key = 'list', value = meta, copy = True)
		except: self._logError()
		return items

	def _extractTitle(self, data, media = None, niche = None, type = None, calendar = None, **parameters):
		try:
			result = {}
			resultTrakt = {}
			resultList = {}
			resultTemp = {}

			resultShow = None
			resultSeason = None
			resultEpisode = None

			# Single title details.
			if type is None and media and 'ids' in data:
				if Media.isMovie(media): type = MetaTrakt.TypeMovie
				elif Media.isShow(media): type = MetaTrakt.TypeShow
				elif Media.isSeason(media): type = MetaTrakt.TypeSeason
				elif Media.isEpisode(media): type = MetaTrakt.TypeEpisode

			if type is None:
				# For listCollection(), objects are returned as follows:
				#	{"show" : {...}, "seasons" : [{"episodes" : []}, ...]}
				# Multiple seasons or episodes can be returned. Return the entire list here.
				if data.get('seasons'):
					if Media.isEpisode(media): return self._extractTitle(data = data, media = media, niche = niche, type = MetaTrakt.TypeEpisode)
					elif Media.isSeason(media): return self._extractTitle(data = data, media = media, niche = niche, type = MetaTrakt.TypeSeason)
					elif Media.isShow(media): return self._extractTitle(data = data, media = media, niche = niche, type = MetaTrakt.TypeShow)
				elif data.get('episodes'): # Retrieving all episodes from a show in detail(). Individual episodes are extracted at the end of this function.
					return self._extractTitle(data = data, media = media, niche = niche, type = MetaTrakt.TypeSeason)

				type = data.get('type')
				for i in [MetaTrakt.TypeMovie, MetaTrakt.TypeShow, MetaTrakt.TypeSeason, MetaTrakt.TypeEpisode]:
					if i in data:
						if not type: type = i # Discover by person ID and show calendars/releases.
						if i == MetaTrakt.TypeShow: # For show calendars/releases that have a "show" and "episode" object. And for other user lists (eg: user ratings).
							resultShow = self._extractTitle(data = data, media = media, niche = niche, type = MetaTrakt.TypeShow)
							resultShow['media'] = Media.Show
							if MetaTrakt.TypeSeason in data: resultSeason = self._extractTitle(data = data, media = media, niche = niche, type = MetaTrakt.TypeSeason)
							if MetaTrakt.TypeEpisode in data: resultEpisode = self._extractTitle(data = data, media = media, niche = niche, type = MetaTrakt.TypeEpisode)
							if not resultSeason and resultEpisode and resultShow:
								# Create a custom season object (useful for new season releases).
								# NB: Copy the values, in case it is a list/dict (eg: genre). Otherwise calling structure() will cause lists/dicts to use references, causing recursion errors when eg casting to JSON.
								resultSeason = {}
								resultSeason['media'] = Media.Season
								for j in ['group', 'id', 'imdb', 'tmdb', 'tvdb', 'trakt', 'tvrage', 'slug', 'tvshowtitle', 'mpaa', 'duration', 'studio', 'country', 'language', 'genre', 'time', self._tempKey()]:
									value = resultShow.get(j)
									if value: resultSeason[j] = Tools.copy(value)
								for j in ['season', 'mpaa', 'duration', 'studio', 'country', 'language', 'genre', self._tempKey()]:
									value = resultEpisode.get(j)
									if value and not j in resultSeason: resultSeason[j] = Tools.copy(value)
								if resultEpisode.get('episode') == 1:
									value = resultEpisode.get('premiered') or resultEpisode.get('aired')
									if value:
										resultSeason['premiered'] = resultSeason['aired'] = value

										# Important when retrieving new seasons beyond S01 (S02+) from release().
										# Otherwise the show premiere (aka S01E01 premiere) is used for the season (copied by the above for-lop), instead of the date for the later season.
										# Without this, S02+ releases in the Arrivals menu get quickly smart-removed, since the release date of S01 is very old.
										value = resultEpisode.get('time')
										if value:
											if resultSeason.get('time'): resultSeason['time'].update(value)
											else: resultSeason['time'] = Tools.copy(value)

								self._tempSet(item = resultSeason)
							break

			# Trakt calendars always return both an episode and a show object.
			# Other users lists, like the user's ratings, can also return multiple objects.
			# Filters are always applied to the episode, never to the show/season, even if we specifically retrieve new shows/seasons.
			# Always return the episode object. It will be converted as necessary in release().
			if resultShow and (resultSeason or resultEpisode):
				detailShow = True
				detailSeason = True
				detailEpisode = True

				# The first three if-else parts are for "New Shows" menu.
				if media == MetaTrakt.TypeShow and resultShow:
					result = resultShow
					detailShow = False
				elif media == MetaTrakt.TypeSeason and resultSeason:
					result = resultSeason
					detailSeason = False
				elif media == MetaTrakt.TypeEpisode and resultEpisode:
					result = resultEpisode
					detailEpisode = False
				else:
					if resultEpisode:
						result = resultEpisode
						detailEpisode = False
					elif resultSeason:
						result = resultSeason
						detailSeason = False
					else:
						result = resultShow
						detailShow = False

				resultDetail = {}
				if resultShow and detailShow:
					resultShow['media'] = Media.Show
					resultShow['niche'] = self.mMetatools.niche(metadata = resultShow, media = Media.Show, niche = niche)
					resultDetail[Media.Show] = resultShow
				if resultSeason and detailSeason:
					resultSeason['media'] = Media.Season
					resultSeason['niche'] = self.mMetatools.niche(metadata = resultSeason, media = Media.Season, niche = niche)
					resultDetail[Media.Season] = resultSeason
				if resultEpisode and detailEpisode:
					resultEpisode['media'] = Media.Episode
					resultEpisode['niche'] = self.mMetatools.niche(metadata = resultEpisode, media = Media.Episode, niche = niche)
					resultDetail[Media.Episode] = resultEpisode

				# If the show does not have a time, use the season/episode date.
				# Eg: for release() when retrieving show objects.
				if resultSeason:
					try: premiere = resultSeason['time'][MetaTools.TimePremiere]
					except: premiere = None
					if not premiere:
						if resultEpisode and resultEpisode.get('season') == resultSeason.get('season') and resultEpisode.get('episode') == 1:
							resultSeason['premiered'] = resultEpisode.get('premiered')
							resultSeason['aired'] = resultEpisode.get('aired')
							resultSeason['time'] = Tools.copy(resultEpisode.get('time'))
				if resultShow:
					try: premiere = resultShow['time'][MetaTools.TimePremiere]
					except: premiere = None
					if not premiere:
						if resultSeason and resultSeason.get('season') == 1:
							resultShow['premiered'] = resultSeason.get('premiered')
							resultShow['aired'] = resultSeason.get('aired')
							resultShow['time'] = Tools.copy(resultSeason.get('time'))
						elif resultEpisode and resultEpisode.get('season') == 1 and resultEpisode.get('episode') == 1:
							resultShow['premiered'] = resultEpisode.get('premiered')
							resultShow['aired'] = resultEpisode.get('aired')
							resultShow['time'] = Tools.copy(resultEpisode.get('time'))

				# Store this in temp, since it will later be deleted by the indexer.
				# Otherwise, if it is stored directly in the object, it will not be deleted and gets saved in the local cache, unnecessarily increasing the database size.
				if resultDetail: self._tempSet(item = result, key = 'detail', value = resultDetail)

				return result
			else:
				current = Time.timestamp()

				# For certain endpoints that have a fixed movie or show media (eg: movies/trending), Trakt does not wrap the object in a type-subobject.
				# Use the media that was used for the request instead.
				if not type: type = parameters.get('type')

				if type and not media:
					if type == MetaTrakt.TypeMovie: media = Media.Movie
					elif type == MetaTrakt.TypeShow: media = Media.Show
					elif type == MetaTrakt.TypeSeason: media = Media.Season
					elif type == MetaTrakt.TypeEpisode: media = Media.Episode
				resultTemp['media'] = media
				resultTemp['niche'] = Tools.copy(niche)

				dataItem = data.get(type) or data
				dataShow = data.get(MetaTrakt.TypeShow)


				season = None
				episode = None
				if Media.isSerie(media) or type == MetaTrakt.TypeShow or type == MetaTrakt.TypeSeason or type == MetaTrakt.TypeEpisode:
					if dataShow: resultTemp['id'] = self._extractId(data = dataShow, **parameters)
					elif type == MetaTrakt.TypeSeason or type == MetaTrakt.TypeEpisode: resultTemp['id'] = self._extractId(**parameters)
					if (type == MetaTrakt.TypeShow and not dataShow) or type == MetaTrakt.TypeSeason or type == MetaTrakt.TypeEpisode:
						if type == MetaTrakt.TypeShow: id = self._extractId(data = dataItem, **parameters)
						else: id = self._extractId(data = dataItem)
						if id:
							if not 'id' in resultTemp: resultTemp['id'] = {}
							if type == MetaTrakt.TypeShow: resultTemp['id'] = id
							else: resultTemp['id'][type] = id

					season = dataItem.get('season')
					if season is None: season = dataItem.get('number')
					if not season is None: result['season'] = season

					episode = dataItem.get('episode')
					if episode is None and not type == MetaTrakt.TypeSeason: episode = dataItem.get('number')
					if not episode is None: result['episode'] = episode

					absolute = dataItem.get('number_abs') # Absolute episode number. Useful for anime.
					if not absolute is None: result['absolute'] = absolute

					if dataShow:
						title = dataShow.get('title')
						if title: result['tvshowtitle'] = title
					elif not type == MetaTrakt.TypeSeason and not type == MetaTrakt.TypeEpisode:
						# Recommendations does not have an outer object.
						# Do not set the tvshowtitle for season/episode objects in detail().
						title = data.get('title')
						if title: result['tvshowtitle'] = title
				else:
					resultTemp['id'] = self._extractId(data = dataItem, **parameters)

				resultTemp.update({k : v for k, v in resultTemp.get('id', {}).items() if not Tools.isDictionary(v)})
				resultTemp.update(result)
				result = resultTemp

				title = dataItem.get('title')
				if title: result['title'] = result['originaltitle'] = title

				year = dataItem.get('year')
				if year: result['year'] = year

				tagline = dataItem.get('tagline')
				if tagline: result['tagline'] = self._extractDescription(tagline)

				plot = dataItem.get('overview')
				if plot: result['plot'] = self._extractDescription(plot)

				# NB: Trakt returns the dates as an ISO date string with a timezone.
				# Do not just extract the date and convert to a timestamp.
				# This can cause the date to be off by 1 day, if the episode was released close to UTC midnight, and it is closer than the local timezone offset which seems to be used in Time.timestamp().
				# Eg: One Piece: 2001-03-21T00:30:00Z (check that the date is the same in the Series menu between S01E61 and "Reason Extras").
				# Movies have a normal date without a timezone.
				#	premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
				#	time = Time.timestamp(fixedTime = premiered, format = Time.FormatDate)
				# All dates from Trakt are returned as GMT/UTC.
				#	https://trakt.docs.apiary.io/#introduction/dates

				premiered = dataItem.get('released')
				if premiered:
					time = None
					if 'T' in premiered: time = Time.timestamp(fixedTime = premiered, iso = True)
					if time:
						premiered = Time.format(time, format = Time.FormatDate)
					else:
						premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1, cache = True)
						time = Time.timestamp(fixedTime = premiered, format = Time.FormatDate, utc = True)
					if premiered:
						result['premiered'] = premiered
						self._dataSet(item = result, key = ['time', MetaTools.ReleasePremiere], value = time)
						premiered = time # Used later on.

				aired = dataItem.get('first_aired')
				if aired:
					time = None
					if 'T' in aired: time = Time.timestamp(fixedTime = aired, iso = True)
					if time:
						aired = Time.format(time, format = Time.FormatDate)
					else:
						aired = Regex.extract(data = aired, expression = '(\d{4}-\d{2}-\d{2})', group = 1, cache = True)
						time = Time.timestamp(fixedTime = aired, format = Time.FormatDate, utc = True)
					if aired:
						result['premiered'] = result['aired'] = aired
						self._dataSet(item = result, key = ['time', MetaTools.ReleasePremiere], value = time)
						premiered = time # Used later on.

				# The disc release date for calendars/all/dvd.
				# Do not do this for other calendars, since their release date is the premiere.
				if calendar == MetaTrakt.CalendarDvd or calendar == MetaTrakt.CalendarStreaming:
					released = data.get('released')
					if released:
						time = None
						if 'T' in released: time = Time.timestamp(fixedTime = released, iso = True)
						if not time:
							released = Regex.extract(data = released, expression = '(\d{4}-\d{2}-\d{2})', group = 1, cache = True)
							time = Time.timestamp(fixedTime = released, format = Time.FormatDate, utc = True)
						if time: self._dataSet(item = result, key = ['time', MetaTools.ReleaseDigital if calendar == MetaTrakt.CalendarStreaming else MetaTools.ReleasePhysical], value = time)

				airs = dataItem.get('airs')
				if airs:
					result['airs'] = {}

					airsDay = airs.get('day') # Trakt only has a single air day, although some shows are aired daily (eg: The Bold and the Beautiful).
					if airsDay: result['airs']['day'] = [airsDay]

					airsTime = airs.get('time')
					if airsTime: result['airs']['time'] = airsTime

					airsZone = airs.get('timezone')
					if airsZone: result['airs']['zone'] = airsZone

					# Check MetaManager._metadataShowUpdate() for more info.
					resultTrakt['offset'] = True
					if airsTime and not ':00' in airsTime:
						airing = dataItem.get('first_aired') or dataItem.get('released')
						if airing and ':00:00.000Z' in airing: resultTrakt['offset'] = False

				mpaa = dataItem.get('certification')
				if mpaa: result['mpaa'] = self._convertCertificate(mpaa, inverse = True)

				rating = dataItem.get('rating')
				if rating:
					if not 'voting' in resultTrakt: resultTrakt['voting'] = {}
					resultTrakt['voting']['rating'] = result['rating'] = Math.round(rating, places = 3) # Often has many decimal places, which just takes up unnecessary space in the MetaCache.

				votes = dataItem.get('votes')
				if votes:
					if not 'voting' in resultTrakt: resultTrakt['voting'] = {}
					resultTrakt['voting']['votes'] = result['votes'] = votes

				if not data == dataItem: # Only for eg user rating list.
					rating = data.get('rating')
					if rating:
						if not 'voting' in resultTrakt: resultTrakt['voting'] = {}
						resultTrakt['voting']['user'] = result['userrating'] = rating

				# For unrated titles (eg: future releases), the Trakt API returns rating=1.0 and votes=1, although they do not display this on their website.
				# Remove these fake ratings if it is a new/future release. Otherwise, for older titles, assume it is actually a 1.0 rating.
				voting = resultTrakt.get('voting')
				if voting and voting.get('rating') == 1 and voting.get('votes') == 1:
					if premiered and premiered > (Time.timestamp() - 604800):
						voting['rating'] = result['rating'] = None
						voting['votes'] = result['votes'] = None

				duration = dataItem.get('runtime')
				if duration:
					duration = duration * 60 # Used below.
					result['duration'] = duration

				finished = False
				status = dataItem.get('status')
				if status: status = self._convertStatus(status = status, inverse = True)
				else: status = self.mMetatools.mergeStatus(media = media, season = season, episode = episode, time = premiered, status = dataShow.get('status') if dataShow else None)
				if status:
					if status == MetaTrakt.StatusEnded or status == MetaTrakt.StatusCanceled: finished = True
					result['status'] = status

				network = dataItem.get('network')
				if network:
					if not 'network' in result: result['network'] = []
					if Tools.isArray(network): result['network'].extend(network)
					else: result['network'].append(network)

				studio = dataItem.get('studio')
				if studio:
					if not 'studio' in result: result['studio'] = []
					if Tools.isArray(studio): result['studio'].extend(studio)
					else: result['studio'].append(studio)

				country = dataItem.get('country')
				if country: result['country'] = Country.codes([country.lower()])

				language = dataItem.get('languages')
				if language: result['language'] = Language.codes([i.lower() for i in language] if Tools.isArray(language) else [language.lower()])

				genre = dataItem.get('genres')
				if genre: result['genre'] = self._convertGenre(genre = genre, inverse = True, default = True)

				trailer = dataItem.get('trailer')
				if trailer: result['trailer'] = self._extractLink(trailer)

				homepage = dataItem.get('homepage')
				if homepage: result['homepage'] = self._extractLink(homepage)

				serietype = None
				if type == MetaTrakt.TypeEpisode:
					serietype = dataItem.get('episode_type')
					if serietype:
						if serietype == MetaTrakt.EpisodeStandard: serietype = [Media.Standard]
						elif serietype == MetaTrakt.EpisodePremiereShow: serietype = [Media.Premiere, Media.Outer]
						elif serietype == MetaTrakt.EpisodePremiereSeason: serietype = [Media.Premiere, Media.Inner]
						elif serietype == MetaTrakt.EpisodePremiereMiddle: serietype = [Media.Premiere, Media.Middle]
						elif serietype == MetaTrakt.EpisodeFinaleShow: serietype = [Media.Finale, Media.Outer]
						elif serietype == MetaTrakt.EpisodeFinaleSeason: serietype = [Media.Finale, Media.Inner]
						elif serietype == MetaTrakt.EpisodeFinaleMiddle: serietype = [Media.Finale, Media.Middle]
						else: serietype = None
					else: serietype = None
				if serietype:
					serietype = self.mMetatools.mergeType(values = serietype, season = season, episode = episode)
					if serietype:result['type'] = serietype

				count = dataItem.get('episode_count')
				if not count is None:
					if not 'count' in result: result['count'] = {}
					if not 'episode' in result['count']: result['count']['episode'] = {}
					result['count']['episode']['total'] = count

				count = dataItem.get('aired_episodes')
				if not count is None:
					if not 'count' in result: result['count'] = {}
					if not 'episode' in result['count']: result['count']['episode'] = {}
					result['count']['episode']['released'] = count

				if finished and result.get('count') and result.get('count').get('episode'):
					if result['count']['episode'].get('total') is None: result['count']['episode']['total'] = result['count']['episode'].get('released')
					if result['count']['episode'].get('released') is None: result['count']['episode']['released'] = result['count']['episode'].get('total')
					try: result['count']['episode']['unreleased'] = result['count']['episode'].get('total') - result['count']['episode'].get('released')
					except: result['count']['episode']['unreleased'] = None

				progress = dataItem.get('progress')
				if progress:
					try: resultTrakt['progress'] = max(0, min(1, int(progress) / 100.0))
					except: pass

				time = self._extractTime(data = data)
				if time:
					resultTrakt['time'] = time
					time = time.get(MetaTools.TimeRated)
					if time: resultTrakt['voting']['time'] = time

				# Additional attributes when discover titles for a person.
				profession = self._extractProfession(data = data)
				if profession: resultTrakt['profession'] = profession

				comments = dataItem.get('comment_count')
				if not comments is None:
					if not 'count' in resultTrakt: resultTrakt['count'] = {}
					resultTrakt['count']['comment'] = comments

				# Additional attributes for recommendations.
				favorited = dataItem.get('favorited_by')
				if not favorited is None:
					if not 'count' in resultTrakt: resultTrakt['count'] = {}
					resultTrakt['count']['favorite'] = len(favorited)

				# Additional attributes for recommendations.
				recommended = dataItem.get('recommended_by')
				if not recommended is None:
					if not 'count' in resultTrakt: resultTrakt['count'] = {}
					resultTrakt['count']['recommend'] = len(recommended)

				# Additional attributes for history.
				action = data.get('action')
				if not action is None: resultTrakt['action'] = action

				id = data.get('id')
				if id: resultList['id'] = id

				rank = data.get('rank')
				if rank is None and 'score' in data:
					# For search, but highest values are first.
					# Sometimes with query searches, Trakt returns very large scores.
					# Eg: 1736172819517538427
					score = data.get('score')
					if not score: rank = 1
					elif score <= 1000: rank = 1001 - score
					else: rank = 10000000000000000001 - score
				if rank: resultList['rank'] = rank

				time = data.get('listed_at')
				if time:
					time = Time.timestamp(fixedTime = time, iso = True)
					if time: resultList['time'] = time

				description = data.get('notes')
				if description: resultList['description'] = description

				# Images
				self._extractImage(media = media, data = data, result = result)

				if result:
					self._tempSet(item = result, value = resultTrakt)
					if resultList: self._tempSet(item = result, key = 'list', value = resultList)

					if Media.isSerie(media): niche = self.mMetatools.niche(metadata = result, media = media, niche = niche) # Extract niche to update the details below.

					# Additional translations that are retrieved with the same API call.
					# Used by the /seasons/ endpoint.
					translations = data.get('translations')
					if translations:
						for translation in translations: translation['plot'] = translation.pop('overview')
						self._tempSet(item = result, key = 'translation', value = translations, copy = True)

					# User Collection and Watched. Episodes are listed under "show".
					seasons = data.get('seasons')
					if seasons:
						results = [result] if result['media'] == type else []
						for i in seasons:
							season = i.get('number')
							item = self._extractBase(data = result)
							item['media'] = Media.Season
							item['niche'] = Tools.copy(niche)
							item['season'] = season
							time = self._extractTime(data = i)
							if time: self._tempSet(item = item, key = 'time', value = time)
							self._tempSet(item = item, key = ['detail', 'show'], value = result, copy = True)
							self._tempSet(item = item, key = ['detail', 'show', 'media'], value = Media.Show)
							self._tempSet(item = item, key = ['detail', 'show', 'niche'], value = niche, copy = True)
							itemSeason = Tools.copy(item)
							if type == MetaTrakt.TypeSeason: results.append(item)
							for j in i.get('episodes', []):
								item = self._extractBase(data = result)
								item['media'] = Media.Episode
								item['niche'] = Tools.copy(niche)
								item['season'] = season
								item['episode'] = j.get('number')
								time = self._extractTime(data = j)
								if time: self._tempSet(item = item, key = 'time', value = time)
								self._tempSet(item = item, key = ['detail', 'show'], value = result, copy = True)
								self._tempSet(item = item, key = ['detail', 'show', 'media'], value = Media.Show)
								self._tempSet(item = item, key = ['detail', 'show', 'niche'], value = niche, copy = True)
								self._tempSet(item = item, key = ['detail', 'season'], value = itemSeason, copy = True)
								self._tempSet(item = item, key = ['detail', 'season', 'media'], value = Media.Season)
								self._tempSet(item = item, key = ['detail', 'season', 'niche'], value = niche, copy = True)
								if type == MetaTrakt.TypeEpisode: results.append(item)
						result = results
					else: # Retrieving all episodes from a show in detail().
						episodes = data.get('episodes')
						if episodes:
							results = []
							for i in episodes:
								item = self._extractBase(data = result)
								item = Tools.update(item, self._extractTitle(data = i, type = MetaTrakt.TypeEpisode))
								self._tempSet(item = item, key = ['detail', 'season'], value = result, copy = True)
								self._tempSet(item = item, key = ['detail', 'season', 'media'], value = Media.Season)
								self._tempSet(item = item, key = ['detail', 'season', 'niche'], value = niche, copy = True)
								results.append(item)
							result = results
				return result
		except: self._logError()
		return None

	def _extractPerson(self, data, media, **parameters):
		try:
			result = {}
			resultTrakt = {}
			resultList = {}

			dataItem = data.get(data.get('type') or MetaTrakt.TypePerson) or data

			result['id'] = self._extractId(data = dataItem)

			name = dataItem.get('name')
			if name: result['name'] = name

			description = dataItem.get('biography')
			if description: result['description'] = self._extractDescription(description)

			gender = dataItem.get('gender')
			if gender:
				# Sometimes the gender is returned as an integer (eg: Foundation).
				if Tools.isInteger(gender): gender = MetaTrakt.GenderFemale if gender == 1 else MetaTrakt.GenderMale if gender == 2 else MetaTrakt.GenderNonbinary
				result['gender'] = gender.replace('_', '-').title()

			birth = dataItem.get('birthday')
			if birth: result['birth'] = birth

			death = dataItem.get('death')
			if death: result['death'] = death

			origin = dataItem.get('birthplace')
			if origin: result['origin'] = origin.strip() # Sometimes ends in a space.

			profession = self._extractProfession(data = data)
			if profession: result['profession'] = profession

			homepage = dataItem.get('homepage')
			if homepage: result['homepage'] = self._extractLink(homepage)

			social = dataItem.get('social_ids')
			if social:
				social = {k : v for k, v in social.items() if v}
				if social: result['social'] = social

			rank = data.get('rank')
			if rank is None and 'score' in data: rank = 1001 - data.get('score', 1000) # For search, but highest values are first.
			if rank: resultList['rank'] = rank

			self._extractImage(media = Media.Person, data = dataItem, result = result)

			if result:
				self._tempSet(item = result, value = resultTrakt)
				if resultList: self._tempSet(item = result, key = 'list', value = resultList)
				return result
		except: self._logError()
		return None

	def _extractStudio(self, data, media, **parameters):
		try:
			result = {}

			dataItem = data.get(data.get('type') or MetaTrakt.TypeStudio) or data

			result['id'] = self._extractId(data = dataItem)

			name = dataItem.get('name')
			if name: result['name'] = name

			country = dataItem.get('country')
			if country: result['country'] = Country.codes(country)

			if result: return result
		except: self._logError()
		return None

	def _extractRelease(self, data):
		try:
			result = {}

			releases = {
				MetaTrakt.ReleasePremiere	: MetaTools.ReleasePremiere,
				MetaTrakt.ReleaseLimited	: MetaTools.ReleaseLimited,
				MetaTrakt.ReleaseTheatrical	: MetaTools.ReleaseTheatrical,
				MetaTrakt.ReleaseDigital	: MetaTools.ReleaseDigital,
				MetaTrakt.ReleasePhysical	: MetaTools.ReleasePhysical,
				MetaTrakt.ReleaseTelevision	: MetaTools.ReleaseTelevision,
				MetaTrakt.ReleaseUnknown	: MetaTools.ReleaseUnknown,
			}

			result['type'] = releases.get(data.get('release_type'), MetaTrakt.ReleaseUnknown)
			result['time'] = Time.timestamp(fixedTime = data.get('release_date'), format = Time.FormatDate, utc = True)
			result['country'] = Country.codes(data.get('country')) if data.get('country') else None
			result['certificate'] = data.get('certification')
			result['description'] = data.get('note')

			return result
		except: self._logError()
		return None

	def _extractTranslation(self, data):
		try:
			result = {}

			title = data.get('title')
			if title: result['title'] = title

			tagline = data.get('tagline')
			if tagline: result['tagline'] = self._extractDescription(tagline)

			plot = data.get('overview')
			if plot: result['plot'] = self._extractDescription(plot)

			language = data.get('language')
			if language: result['language'] = Language.codes(language)

			country = data.get('country')
			if country: result['country'] = Country.codes(country)

			return result
		except: self._logError()
		return None

	def _extractAlias(self, data):
		try:
			result = {}

			title = data.get('title')
			if title: result['title'] = title

			country = data.get('country')
			if country: result['country'] = Country.codes(country)

			return result
		except: self._logError()
		return None

	def _extractRating(self, data):
		try:
			result = {}

			rating = data.get('rating')
			if not rating is None: result['rating'] = rating

			votes = data.get('votes')
			if not votes is None: result['votes'] = votes

			# Note that the dict keys are strings, not integers.
			# Do not convert to integers, since encoding to JSON will make them strings.
			# Convert to a list, so that integers can be used as indexes.
			distribution = data.get('distribution')
			if distribution:
				values = [0] * 11 # Include a rating 0 which is not from Trakt.
				for k, v in distribution.items():
					values[int(k)] = v
				result['distribution'] = values

			return result
		except: self._logError()
		return None

	def _extractList(self, data, media, **parameters):
		try:
			result = {}
			resultTrakt = {}
			resultList = {}

			dataItem = data.get(data.get('type') or MetaTrakt.TypeList) or data

			result['media'] = media

			result['id'] = self._extractId(data = dataItem)

			title = dataItem.get('name')
			if title: result['title'] = result['originaltitle'] = title # Keep the original title, since Set names are edited below.

			plot = dataItem.get('description')
			if plot: result['plot'] = self._extractDescription(plot)

			time = self._extractTime(data = dataItem)
			if time: resultTrakt['time'] = time

			items = dataItem.get('item_count')
			if not items is None:
				if not 'count' in resultTrakt: resultTrakt['count'] = {}
				resultTrakt['count']['item'] = items

				 # For sets. The "released" attribute is set in detail().
				if not 'count' in result: result['count'] = {}
				if not 'movie' in result['count']: result['count']['movie'] = {}
				result['count']['movie']['total'] = items

			comments = dataItem.get('comment_count')
			if not comments is None:
				if not 'count' in resultTrakt: resultTrakt['count'] = {}
				resultTrakt['count']['comment'] = comments

			likes = dataItem.get('likes')
			if not likes is None:
				if not 'count' in resultTrakt: resultTrakt['count'] = {}
				resultTrakt['count']['like'] = likes

			user = dataItem.get('user')
			if user:
				user = user.get('username') or user.get('name')
				if user: resultList['user'] = result['id']['user'] = user

			type = dataItem.get('type')
			if type: resultList['type'] = type

			privacy = dataItem.get('privacy')
			if privacy: resultList['privacy'] = privacy

			link = dataItem.get('share_link')
			if link: resultList['link'] = link

			rank = dataItem.get('rank')
			if rank is None: rank = 1001 - data.get('score', 1000) # For search, but highest values are first.
			if rank: resultList['rank'] = rank

			time = dataItem.get('created_at')
			if time:
				time = Time.timestamp(fixedTime = time, iso = True)
				if time: resultList['time'] = time

			sort = dataItem.get('sort_by')
			if sort: resultList['sort'] = sort

			order = dataItem.get('sort_how')
			if order: resultList['order'] = order

			number = dataItem.get('display_numbers')
			if not number is None:
				if not 'support' in resultList: resultList['support'] = {}
				resultList['support']['number'] = number

			comment = dataItem.get('allow_comments')
			if not comment is None:
				if not 'support' in resultList: resultList['support'] = {}
				resultList['support']['comment'] = comment

			if not Media.isList(media) and type == MetaTrakt.ListOfficial: result['media'] = Media.Set
			elif not Media.isSet(media): result['media'] = Media.List

			if result.get('title') and Media.isSet(media):
				# When searching "avatar" sets, there are a bunch of official lists returned named "Avatar Collection copy".
				# Most of these lists return 404 (probably deleted), and one redirects to a personal user list.
				# Maybe these lists are users who copy the official list and create their own personal list, but Trakt foregets to update the "type" attribute from the original "offical" to the new "personal".
				# Remove any copied list from the results.
				#	https://trakt.tv/lists/25075602
				#	https://trakt.tv/lists/25629401
				#	https://trakt.tv/lists/26068972
				if Regex.match(data = result['title'], expression = 'collection(\s*[\:\-]+\s*)*\s*copy$'): return None

			if result:
				self._tempSet(item = result, value = resultTrakt)
				if resultList: self._tempSet(item = result, key = 'list', value = resultList)
				return result
		except: self._logError()
		return None

	def _extractImage(self, media, data, result = None):
		# Trakt now supports images in their API.
		# All images are returned in WEBP format. This seems to be supported in Kodi.
		# No rating, language, or other grouping or sorting attribute is provided with the image data.

		# Sometimes some images return a 404 error.
		# Eg: Avatar (clearart): https://media.trakt.tv/images/movies/000/012/269/cleararts/medium/9e6bb0d8d0.png.webp

		# Retrieving images from Trakt can be useful.
		# Firstly, it does not require a separate API call, since it is returned with "extended" metadata.
		# Secondly, if the user has only Standard-detailed metadata, episodes only retrieve images from TVDb, but not from TMDb/IMDb. And Fanart does not have episode thumbs.
		# If there are no images on TVDb, or there is a season-number mismatch on Trakt, some episodes might end up without a thumb.
		# Eg: One Piece S21E197 (1088 on Trakt) is S22E03 (TVDb). Due to the episode being in a different season, with Standard-detailed metadata and without Trakt images, this episode would not have a thumb.

		images = {}
		if data:
			photos1 = []
			photos2 = []
			imageData = data.get('images')
			if imageData:
				for typed, links in imageData.items():
					if links:
						type = MetaTrakt.Images.get(typed)
						if type:
							for link in links:
								if link:
									image = MetaImage.create(link = 'https://' + link, provider = MetaImage.ProviderTrakt)
									if image:
										if not type in images: images[type] = []
										if typed == MetaTrakt.ImageHeadshot: photos1.append(image)
										elif typed == MetaTrakt.ImageCharacter: photos2.append(image)
										else: images[type].append(image)

				if images:
					# Prefer the actor photo over the character photo.
					if photos1 or photos2: images[MetaImage.TypePhoto] = photos1 + photos2

					if result: result[MetaImage.Attribute] = images
		return images or None

	##############################################################################
	# PROCESS
	##############################################################################

	def _processSelect(self, media, items, result):
		# For sets, season, and episodes, the sub-metadsata (people, translations, ratings, etc) have to be retrieved separately for each part/season/episode.
		# In such a case, the items are a nested dictionary with the keys being the set IDs or the season/episode numbers.
		# Select the correct part/season/episode to apply the sub-metadsata to.
		selection = None
		if Tools.isDictionary(items):
			selection = []
			if not result: # If no summary is retrieved and result is None.
				keys = list(items.keys())
				if len(keys) == 1: selection.append({'item' : items[keys[0]], 'result' : result})
			elif Media.isSet(media):
				for s, v in items.items():
					item = None
					for i in result.get('part', []):
						if i.get('id', {}).get(self.id()) == str(s): # The key is an integer.
							item = i
							break
					if item: selection.append({'item' : v, 'result' : item})
			else:
				if not Tools.isArray(result): result = [result] # Also allow a single season or a single episode.
				if Media.isSeason(media):
					for s, v in items.items():
						item = None
						for i in result:
							if i.get('season') == s:
								item = i
								break
						if item: selection.append({'item' : v, 'result' : item})
				elif Media.isEpisode(media):
					for s, u in items.items():
						for e, v in u.items():
							item = None
							for i in result:
								if i.get('season') == s and i.get('episode') == e:
									item = i
									break
							if item: selection.append({'item' : v, 'result' : item})
		return selection

	def _processSummary(self, media, items, result = None, id = None, season = None):
		try:
			if items:
				multi = Tools.isArray(items)

				# Retrieve a specific season.
				if Tools.isInteger(season) and Media.isSeason(media) and multi:
					for item in items:
						if item.get('season', -1) == season:
							items = item
							multi = False
							break

				if Media.isSeason(media) or Media.isEpisode(media):
					# Season and episode objects do not return the ID for the show.
					# Add it from the param,eters passed into this function.
					if id:
						id = str(id)
						if Tools.isNumeric(id): idType = 'trakt'
						elif Tools.isNumeric(id[2:]): idType = 'imdb'
						else: idType = 'slug'
						for item in items if multi else [items]:
							if not 'id' in item: item['id'] = {}
							item['id'][idType] = id
							item[idType] = id

				# In case the set summary was retrieved using the ID lookup search endpoint, returning a list of results.
				if Media.isSet(media) and multi:
					items = items[0]

				if result is None: result = items
				elif multi: result.extend(items)
				else: result.update(items)
		except: self._logError()
		return result

	def _processPerson(self, media, items, result = None, temp = True):
		try:
			# Trakt does not always list the cast, director, and writers in the correct order.
			# Sometimes the main director is listed in the middle or the end of the director's list.
			# Use other means to determine the importance and order the people.
			if items:
				selection = self._processSelect(media = media, items = items, result = result)
				if selection:
					for i in selection:
						self._processPerson(media = i['result'].get('media'), items = i['item'], result = i['result'], temp = not Media.isSet(media))

					if Media.isSet(media):
						people = {
							'creator' : [],
							'director' : [],
							'writer' : [],
							'cast' : [],
						}

						for i in selection:
							for j in people.keys():
								value = i['result'].get(j)
								if value: people[j].append(value)

						for k, v in people.items():
							all = original = Tools.listFlatten(v)
							if k == 'cast': all = [i.get('name') for i in all]
							occurance = Tools.listUnique(all)
							occurance = [[i, Tools.listCount(data = all, value = i)] for i in occurance]
							occurance = Tools.listSort(occurance, key = lambda x : x[1], reverse = True)
							occurance = [i[0] for i in occurance]
							if k == 'cast':
								cast = []
								for i in range(len(occurance)):
									name = occurance[i]
									role = [j['role'] for j in original if j['name'] == name if j['role']]
									if role:
										role = [[i, Tools.listCount(data = role, value = i)] for i in Tools.listUnique(role)]
										role = Tools.listSort(role, key = lambda x : x[1], reverse = True)
										role = [i[0] for i in role]
									cast.append({
										'name' : name,
										'role' : ' / '.join(role) if role else None,
										'order' : i,
									})
								occurance = cast
							if occurance: result[k] = occurance
				else:
					items = self._filter(items = items, duplicate = MetaTrakt.DuplicateMerge)
					if items:
						people = {
							'creator' : {
								'count' : 0,
								'person' : [],
							},
							'director' : {
								'count' : 0,
								'person' : [[], []],
							},
							'writer' : {
								'count' : 0,
								'person' : [[], [], []],
							},
							'cast' : {
								'count' : 0,
								'person' : [],
							},
						}

						for i in items:
							profession = i.get('profession')
							if profession:
								creator = []
								director = [[], []]
								writer = [[], [], []]
								character = []
								jobs = []

								for j in profession:
									order = j.get('order')
									division = j.get('division')
									department = j.get('department')
									job = j.get('job')
									role = j.get('role')

									if job: jobs.append(job)
									if role: jobs.append(role)

									# Creators
									if department == MetaTrakt.DepartmentCreating:
										order += 90000000
										creator.append(order)

									# Directors
									elif department == MetaTrakt.DepartmentDirecting:
										if job == MetaTrakt.JobDirector:
											key = 0
											order += 90000000
										elif job:
											key = 1
											if 'unit' in job: order += 80000000
											elif 'additional' in job: order += 60000000 # Check this before 'assistant', since both contain the 'assistant' keyword.
											elif 'assistant' in job: order += 70000000
											elif 'supervisor' in job: order += 50000000
											else: order += 40000000
										else:
											key = 1
											order += 30000000
										director[key].append(order)

									# Writers
									elif department == MetaTrakt.DepartmentWriting:
										if job == MetaTrakt.JobWriterNovel:
											key = 0
											order += 90000000
										elif job == MetaTrakt.JobWriter:
											key = 0
											order += 80000000
										elif job == MetaTrakt.JobWriterScreenplay:
											key = 0
											order += 70000000
										elif job == MetaTrakt.JobWriterStory:
											key = 1
											order += 60000000
										else:
											key = 2
											order += 50000000
										writer[key].append(order)

									# Cast
									elif j.get('division') == MetaTrakt.DivisionCast:
										character.append(j.get('character', None)) # The role is often not known.

								# Images
								try: thumbnail = i[MetaImage.Attribute][MetaImage.TypePhoto][0]['link']
								except: thumbnail = None

								# Creators
								if creator:
									order = (100000000 - (people['creator']['count'] * 1000)) + len(creator) + (len(profession) / 100.0)
									entry = {'name' : i['name'], 'order' : order, 'job' : jobs}
									if thumbnail: entry['thumbnail'] = thumbnail
									people['creator']['count'] += 1
									people['creator']['person'].append(entry)

								# Directors
								if director[0] or director[1]:
									people['director']['count'] += 1
									for k in [0, 1]:
										if director[k]:
											director[k] = Tools.listSort(director[k])
											entry = {'name' : i['name'], 'order' : director[k][-1] + (1.0 - (people['director']['count'] / 10000.0)) + (len(profession) / 100000.0), 'job' : jobs}
											if thumbnail: entry['thumbnail'] = thumbnail
											people['director']['person'][k].append(entry)

								# Writers
								if writer[0] or writer[1] or writer[2]:
									people['writer']['count'] += 1
									for k in [0, 1, 2]:
										if writer[k]:
											writer[k] = Tools.listSort(writer[k])
											entry = {'name' : i['name'], 'order' : writer[k][-1] + (1.0 - (people['writer']['count'] / 10000.0)) + (len(profession) / 100000.0), 'job' : jobs}
											if thumbnail: entry['thumbnail'] = thumbnail
											people['writer']['person'][k].append(entry)

								# Cast
								if character:
									character = [k for k in character if k] # Filter out those without a role.
									order = (100000000 - (people['cast']['count'] * 1000)) + len(character) + (len(profession) / 100.0)
									if character and any('uncredit' in k for k in character): order -= 100 # Uncredited characters.
									entry = {'name' : i['name'], 'role' : ' / '.join(character) if character else None, 'order' : order, 'job' : jobs}
									if thumbnail: entry['thumbnail'] = thumbnail
									people['cast']['count'] += 1
									people['cast']['person'].append(entry)

						# Creators
						if people['creator']['count']:
							creator = people['creator']['person']
							if creator:
								creator = Tools.listSort(creator, key = lambda x : x['order'], reverse = True)
								result['creator'] = Tools.listUnique([k['name'] for k in creator])

						# Directors
						if people['director']['count']:
							director = people['director']['person'][0]
							if not director: director = people['director']['person'][1]
							if director:
								director = Tools.listSort(director, key = lambda x : x['order'], reverse = True)
								result['director'] = Tools.listUnique([k['name'] for k in director])

						# Writers
						if people['writer']['count']:
							writer = people['writer']['person'][0]
							if len(writer) < 3: # Add story writers, if there a few other writers.
								writer.extend(people['writer']['person'][1])
								if len(writer) < 1: writer.extend(people['writer']['person'][2])
							if writer:
								writer = Tools.listSort(writer, key = lambda x : x['order'], reverse = True)
								result['writer'] = Tools.listUnique([k['name'] for k in writer])

						# Cast
						if people['cast']['count']:
							cast = people['cast']['person']
							if cast:
								cast = Tools.listSort(cast, key = lambda x : x['order'], reverse = True)
								for k in range(len(cast)): cast[k]['order'] = k
								result['cast'] = cast

						if temp: self._tempSet(item = result, key = 'person', value = items, clean = True)
		except: self._logError()
		return result

	def _processStudio(self, media, items, result = None, temp = True):
		try:
			if items:
				selection = self._processSelect(media = media, items = items, result = result)
				if selection:
					for i in selection:
						self._processStudio(media = i['result'].get('media'), items = i['item'], result = i['result'], temp = not Media.isSet(media))

					if Media.isSet(media):
						studios = []

						for i in selection:
							value = i['result'].get('studio')
							if value: studios.extend(value)

						occurance = Tools.listUnique(studios)
						occurance = [[i, Tools.listCount(data = studios, value = i)] for i in occurance]
						occurance = Tools.listSort(occurance, key = lambda x : x[1], reverse = True)
						occurance = [i[0] for i in occurance]
						if occurance: result['studio'] = occurance
				else:
					studio = []
					for item in items:
						name = item.get('name')
						if name: studio.append(name)

					if studio: result['studio'] = studio
					if temp: self._tempSet(item = result, key = 'studio', value = items, clean = True)
		except: self._logError()
		return result

	def _processTranslation(self, media, items, result = None, language = None, country = None, temp = True):
		try:
			# Do not store all translations, since the size can be large (50-100KB uncompressed and 10-30KB compressed).
			# We only need the titles (for scraping and filtering), but the tagline and plot is the largest and not used anywhere else.
			# The meta cache will in any case re-retrieve the metadata if the user's language or country settings were changed.
			if items:
				selection = self._processSelect(media = media, items = items, result = result)
				if selection:
					for i in selection:
						self._processTranslation(media = i['result'].get('media'), items = i['item'], result = i['result'], language = language, country = country, temp = not Media.isSet(media))

					# Copy over the translated tagline.
					if Media.isSet(media):
						for i in result.get('part', []):
							tagline = i.get('tagline')
							if tagline:
								result['tagline'] = tagline
								break
				else:
					language = self.language(language = language, exclude = False, default = False)
					country = self.country(country = country, exclude = False, default = False)

					title = {}
					translation = {}
					match = {'both' : {}, 'language' : {}, 'country' : {}}
					values = ['title', 'tagline', 'plot']

					for item in items:
						itemLanguage = item.get('language')
						itemCountry = item.get('country')

						isLanguage = language and language == itemLanguage
						isCountry = country and country == itemCountry

						# Update the dicts, since there can be multiple entries for the same language/country, each with only partial values.
						# Eg: [{"title":"أفاتار: طريق المياه","overview":" لينهيا م...","tagline":null,"language":"ar","country":"ae"},{"title":"أفاتار: طريق المياه","overview":" لينهيا م...","tagline":"العودة إلى باندورا","language":"ar","country":"sa"},{"title":"Avatar 2","overview":"","tagline":"","language":"de","country":null},{"title":null,"overview":"Mehr als zehn Jahre ...","tagline":"Rückkehr nach Pandora","language":"de","country":"de"}]
						if isLanguage and isCountry: match['both'].update(item)
						elif isLanguage: match['language'].update(item)
						elif isCountry: match['country'].update(item)

						entry = translation
						if not itemLanguage in entry: entry[itemLanguage] = {}
						entry = entry[itemLanguage]
						if not itemCountry in entry: entry[itemCountry] = {}
						entry = entry[itemCountry]
						for j in values:
							value = item.get(j)
							if value or not entry.get(j): entry[j] = value

						value = item.get('title')
						if value:
							if not itemLanguage in title: title[itemLanguage] = []
							title[itemLanguage].append(value)

					for i in ['country', 'language', 'both']:
						entry = match[i]
						for j in values:
							value = entry.get(j)
							if value: result[j] = value

					for k, v in title.items(): title[k] = Tools.listUnique(v)
					self._dataSet(item = result, key = 'alias', value = title)
					if temp: self._tempSet(item = result, key = 'translation', value = items)
		except: self._logError()
		return result

	def _processAlias(self, media, items, result = None, temp = True):
		try:
			if items:
				selection = self._processSelect(media = media, items = items, result = result)
				if selection:
					for i in selection:
						self._processAlias(media = i['result'].get('media'), items = i['item'], result = i['result'], temp = not Media.isSet(media))
				else:
					title = {}
					for item in items:
						value = item.get('title')
						if value:
							country = item.get('country')
							if not country in title: title[country] = []
							title[country].append(value)

					for k, v in title.items(): title[k] = Tools.listUnique(v)
					self._dataSet(item = result, key = ['alias', 'country'], value = title)
					if temp: self._tempSet(item = result, key = 'alias', value = items)
		except: self._logError()
		return result

	def _processRating(self, media, items, result = None, temp = True):
		try:
			# It seems that the ratings/votes in the summary can sometimes be outdated a little bit.
			# Trakt probably recalculates the averages once a day or so, and might therefore not have the latests values in the summary.
			# The Ratings endpoint seems to always return the current stats. Replace the sumamry values with these ones.
			if items:
				selection = None
				if Tools.isDictionary(items) and not 'distribution' in items:
					selection = self._processSelect(media = media, items = items, result = result)

				if selection:
					for i in selection:
						self._processRating(media = i['result'].get('media'), items = i['item'], result = i['result'], temp = not Media.isSet(media))

					if Media.isSet(media):
						distributions = []
						for i in selection:
							value = i['result'].get('distribution')
							if value: distributions.append(value)

						if distributions:
							distributions = [sum(i) for i in zip(*distributions)]
							self._dataSet(item = result, key = 'distribution', value = distributions)
							if temp: self._tempSet(item = result, key = ['voting', 'distribution'], value = distributions)
				else:
					rating = items.get('rating')
					if not rating is None:
						self._dataSet(item = result, key = 'rating', value = rating)
						if temp: self._tempSet(item = result, key = ['voting', 'rating'], value = rating)

					votes = items.get('votes')
					if not votes is None:
						self._dataSet(item = result, key = 'votes', value = votes)
						if temp: self._tempSet(item = result, key = ['voting', 'votes'], value = votes)

					distribution = items.get('distribution')
					if distribution: self._dataSet(item = result, key = 'distribution', value = distribution)

					if temp: self._tempSet(item = result, key = ['voting', 'distribution'], value = items.get('distribution'))
		except: self._logError()
		return result

	def _processRelease(self, media, items, result, local = None, origin = None, temp = True):
		try:
			# Firstly, try to pick the origin country of release.
			# Secondly, try to pick one of the common countries.
			# Thirdly, try to pick the country as specified in the user settings.
			# Lastly, pick any country that is available.
			if items:
				selection = self._processSelect(media = media, items = items, result = result)
				if selection:
					for i in selection:
						self._processRelease(media = i['result'].get('media'), items = i['item'], result = i['result'], local = local, origin = origin, temp = not Media.isSet(media))

					if Media.isSet(media):
						times = []
						for i in selection:
							value = i['result'].get('time')
							if value: times.append(value)

						first = {}
						for i in times:
							if i:
								for k, v, in i.items():
									if not k in first: first[k] = []
									if v: first[k].append(v)
						first = {k : min(v) for k, v in first.items() if v}
						result['time'] = first
				else:
					time = self.mMetatools.timeGenerate(release = items, metadata = result, local = local, origin = origin)
					self._dataSet(item = result, key = 'time', value = time) # Some values might have already been set from extractTitle(), eg: premiere date.
					if temp: self._tempSet(item = result, key = 'release', value = items)
		except: self._logError()
		return result

	def _processSet(self, media, items = None, parts = None, result = None, temp = True):
		try:
			if items or parts:
				if items:
					setBase = None
					setMatch = None
					for item in items:
						if Media.isSet(item['media']):
							if not setBase: setBase = item
							if item.get('originaltitle', '').lower().endswith('collection') or item.get('title', '').lower().endswith('collection'):
								setMatch = item
								break

					set = setMatch or setBase
					if set:
						result['set'] = set.get('title')
						result['setoverview'] = set.get('plot')

						titles = [set.get('title'), set.get('originaltitle')]
						titles = Tools.listUnique([i for i in titles if i])
						if titles: self._dataSet(item = result, key = ['alias', 'set', Language.CodeEnglish], value = titles)

						value = Tools.copy(set)
						self._tempClean(item = value)
						self._dataSet(item = result, key = 'collection', value = value)

				if parts:
					# Parts can be retrieved as standalone details of a set, or as the set details retrieved as subpart of a movie.
					parent = ['collection'] if result.get('collection') else []

					pack = {}
					niche = []
					year = []
					premiered = []
					time = []
					duration = []
					rating = []
					votes = []
					mpaa = []
					genre = []
					language = []
					country = []
					tagline = None
					trailer = None
					homepage = None
					released = 0

					parts = Tools.listSort(parts, key = lambda i : i.get('premiered', '99999999'))
					for part in parts:
						self._tempClean(item = part)

						niche.append(part.get('niche'))
						year.append(part.get('year'))
						premiered.append(part.get('premiered'))
						time.append(Time.timestamp(fixedTime = part.get('premiered'), format = Time.FormatDate, utc = True))
						duration.append(part.get('duration'))
						rating.append(part.get('rating'))
						votes.append(part.get('votes'))
						mpaa.append(part.get('mpaa'))

						value = part.get('genre')
						if value: genre.extend(value)

						value = part.get('language')
						if value: language.extend(Language.codes(value))

						value = part.get('country')
						if value: country.extend(Country.codes(value))

						value = part.get('mpaa')
						if value: mpaa.append(value)

						if not tagline: tagline = part.get('tagline')
						if not trailer: trailer = self._extractLink(part.get('trailer'))
						if not homepage: homepage = self._extractLink(part.get('homepage'))

						status = part.get('status')
						if status and status.lower() == MetaTrakt.StatusReleased: released += 1

					total = len(parts)
					pack['count'] = {'movie' : {'total' : total, 'released' : released, 'unreleased' : total - released}}
					self._dataSet(item = result, value = pack, copy = True) # Add the counts to the main dict, similar to episode counts.

					year = [i for i in year if i]
					pack['year'] = {'minimum' : None, 'maximum' : None, 'range' : None}
					try: pack['year']['minimum'] = min(year)
					except: pass
					try: pack['year']['maximum'] = max(year)
					except: pass
					try: pack['year']['range'] = year
					except: pass

					time = [i for i in time if i]
					pack['time'] = {'minimum' : None, 'maximum' : None, 'range' : None}
					try: pack['time']['minimum'] = min(time)
					except: pass
					try: pack['time']['maximum'] = max(time)
					except: pass
					try: pack['time']['range'] = time
					except: pass

					duration = [i for i in duration if i]
					pack['duration'] = {'total' : None, 'mean' : None, 'minimum' : None, 'maximum' : None, 'range' : None}
					try: pack['duration']['range'] = duration
					except: pass
					# For unreleased movies (eg Avatar [9720,11520,60,60,60]), the duration is sometimes 60 (1 min).
					# Do not use Math.outliers(), since the mean and std might be too much affected by outliers, and therefore remove too much or too little.
					if duration:
						maximum = max(duration)
						duration = [i for i in duration if (i / maximum) > 0.05]
						try: pack['duration']['total'] = sum(duration) if len(duration) == len(parts) else sum(duration + ([int(sum(duration) / float(len(duration)))] * (len(parts) - len(duration)))) # Estimate the total duration if outliers were removed.
						except: pass
						try: pack['duration']['mean'] = int(sum(duration) / float(len(duration)))
						except: pass
						try: pack['duration']['minimum'] = min(duration)
						except: pass
						try: pack['duration']['maximum'] = max(duration)
						except: pass

					niche = Tools.listUnique([i for i in Tools.listFlatten(niche) if i])
					if niche: self._dataSet(item = result, key = 'niche', value = niche)

					year = pack.get('year', {}).get('minimum')
					if year: self._dataSet(item = result, key = parent + ['year'], value = year)

					if premiered:
						premiered = [i for i in premiered if i]
						if premiered:
							premiered = Tools.listSort(premiered)
							if premiered: self._dataSet(item = result, key = parent + ['premiered'], value = premiered[0])

					duration = pack.get('duration', {}).get('mean')
					if duration: self._dataSet(item = result, key = parent + ['duration'], value = duration)

					voting = 0
					for i in range(len(rating)):
						r = rating[i]
						v = votes[i]
						if r and v: voting += r * v
					try: votes = sum([i for i in votes if not i is None])
					except: votes = 0
					rating = voting / float(votes) if votes else None
					if rating:
						self._dataSet(item = result, key = parent + ['rating'], value = rating)
						if temp and not parent: self._tempSet(item = result, key = ['voting', 'rating'], value = rating)
					if votes:
						self._dataSet(item = result, key = parent + ['votes'], value = votes)
						if temp and not parent: self._tempSet(item = result, key = ['voting', 'votes'], value = votes)

					if genre:
						genre = Tools.listUnique(genre)
						if genre: self._dataSet(item = result, key = parent + ['genre'], value = genre)

					if language:
						language = Tools.listUnique(language)
						if language: self._dataSet(item = result, key = parent + ['language'], value = language)

					if country:
						country = Tools.listUnique(country)
						if country: self._dataSet(item = result, key = parent + ['country'], value = country)

					if mpaa:
						mpaa = Tools.listCommon(mpaa)
						if mpaa: self._dataSet(item = result, key = parent + ['mpaa'], value = mpaa)

					if tagline: self._dataSet(item = result, key = parent + ['tagline'], value = tagline)
					if trailer: self._dataSet(item = result, key = parent + ['trailer'], value = trailer)
					if homepage: self._dataSet(item = result, key = parent + ['homepage'], value = homepage)

					self._dataSet(item = result, key = parent + ['part'], value = parts)
					self._dataSet(item = result, key = parent + ['pack'], value = pack)

		except: self._logError()
		return result

	##############################################################################
	# FILTER
	##############################################################################

	def _filter(self, items, media = None, niche = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, episode = None, studio = None, network = None, rating = None, votes = None, action = None, page = None, limit = None, sort = None, order = None, filter = False, duplicate = None, extended = None, unknown = None):
		if items:
			filter = self._filterDefault(filter = filter, niche = niche)
			if extended is None: extended = True
			if not filter == MetaProvider.FilterNone:
				if not genre: genre = []
				elif not Tools.isArray(genre): genre = [genre]

				durationRange = None
				genreIncludeAny = []
				genreIncludeMain = []
				genreIncludeFilter = (genreIncludeMain if filter >= MetaProvider.FilterStrict else genreIncludeAny)
				genreExcludeAny = []
				genreExcludeMain = []
				genreExcludeFilter = (genreExcludeAny if filter >= MetaProvider.FilterStrict else genreExcludeMain)

				if media:
					# Should match with code in parameterFilter().
					if not Media.isSet(media) and not Media.isList(media) and not Media.isPerson(media) and not Media.isCompany(media):
						if Media.isMovie(media):
							if Media.isFeature(niche):
								if filter >= MetaProvider.FilterLenient:
									if filter >= MetaProvider.FilterStrict: durationRange = [int(MetaTools.ShortAverage / 1.5) if Media.isTelevision(niche) else MetaTools.ShortStandard, None]
									else: durationRange = [int(MetaTools.ShortAverage / 2) if Media.isTelevision(niche) else MetaTools.ShortAverage, None]
									genreExcludeFilter.append(MetaTools.GenreShort)
							elif Media.isShort(niche):
								if filter >= MetaProvider.FilterLenient:
									if not MetaTools.GenreDocumentary in genre: genreExcludeMain.append(MetaTools.GenreDocumentary)
									if filter >= MetaProvider.FilterLenient: # Do this for FilterLenient, not just FilterStrict, since we check both the duration and genre for shorts below.
										genreIncludeAny.append(MetaTools.GenreShort)
										durationRange = [MetaTools.ShortMinimum, MetaTools.ShortMaximum]
							elif Media.isSpecial(niche):
								genreIncludeAny.append(MetaTools.GenreHoliday)
								durationRange = [60, 4500] # 1 hour 15 minutes.

					if Media.isAge(niche):
						age = self.mMetatools.nicheAge(niche = niche, format = False)
						if age:
							# Do not filter by date, since Trakt can only filter by year, causing many items to be removed if the date is not exactly in the range.
							#if Media.isFuture(niche): date = None # Many future releases do not have a premier date yet, and would otherwise be filtered out.
							#else: date = age
							date = None

					if Media.isQuality(niche):
						quality = self.mMetatools.nicheQuality(niche = niche, media = media)
						if quality: rating = quality

					if Media.isRegion(niche):
						region = self.mMetatools.nicheRegion(niche = niche)
						if region:
							if 'country' in region:
								if not country: country = []
								country.extend(region['country'])
								country = Tools.listUnique(country)
							if 'language' in region:
								if not language: language = []
								language.extend(region['language'])
								language = Tools.listUnique(language)

					if Media.isAudience(niche):
						age = Audience.TypeKid if Media.isKid(niche) else Audience.TypeTeen if Media.isTeen(niche) else Audience.TypeAdult
						certificates = self.mMetatools.nicheCertificate(age = age, media = media, unrated = False, format = True)
						if certificates:
							if not certificate: certificate = []
							certificate.extend(certificates)
							certificate = Tools.listUnique(certificate)

					# Note that genres should be filtered post-request, so that we can accomodate main genre vs sub-genres.
					# Check parameterFilter() for more details.
					if Media.isTopic(niche):
						topic = self.mMetatools.nicheTopic(niche = niche, strict = True)
						if topic: self._parameterGenre(genres = topic, result = genreIncludeFilter, ignore = genreExcludeFilter)
					if filter >= MetaProvider.FilterStrict:
						for i in [Media.Docu, Media.Telly, Media.Soap, Media.Anime, Media.Donghua]:
							if not Media.isMedia(media = niche, type = i):
								topic = self.mMetatools.nicheTopic(niche = i, strict = True)
								if topic: self._parameterGenre(genres = topic, result = genreExcludeMain, ignore = genreIncludeFilter)

					if Media.isMood(niche):
						mood = self.mMetatools.nicheMood(niche = niche)
						if mood: self._parameterGenre(genres = mood, result = genreIncludeAny, ignore = genreExcludeFilter)

				if durationRange and not duration: duration = durationRange

				genreAll = []
				for i in genreIncludeAny:
					genreAll.append(self._parameterSelect(i, select = MetaTrakt.SelectIncludeAny))
				for i in genreIncludeMain:
					genreAll.append(self._parameterSelect(i, select = MetaTrakt.SelectIncludeMain))
				for i in genreExcludeAny:
					if not genre or not i in genre: genreAll.append(self._parameterSelect(i, select = MetaTrakt.SelectExcludeAny))
				for i in genreExcludeMain:
					if not genre or not i in genre: genreAll.append(self._parameterSelect(i, select = MetaTrakt.SelectExcludeMain))
				genre = genreAll

			if media:
				if Tools.isArray(media):
					result = []
					for i in media:
						subitems = self._filter(items = items, filter = filter, media = i, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, episode = episode, studio = studio, network = network, rating = rating, votes = votes, unknown = unknown)
						if subitems: result.extend(subitems)
					items = Tools.listUnique(result)
				elif not media == MetaTrakt.CategoryAll:
					items = self._filterMedia(items = items, media = media, niche = niche, unknown = unknown)

			if duplicate is True: duplicate = MetaTrakt.DuplicateAll
			elif duplicate is False: duplicate = MetaTrakt.DuplicateFirst
			if duplicate and not duplicate == MetaTrakt.DuplicateAll:
				items = self.mMetatools.filterDuplicate(items = items, id = True, title = False, number = False, last = duplicate == MetaTrakt.DuplicateLast, merge = 'number' if duplicate == MetaTrakt.DuplicateMerge else False)

			# Move more important jobs to the front.
			# Some people might have multiple professions for the same title (eg: actor and director).
			if items and items[0].get('profession'):
				departments = [MetaTrakt.DepartmentActing, MetaTrakt.DepartmentCreating, MetaTrakt.DepartmentDirecting, MetaTrakt.DepartmentWriting, MetaTrakt.DepartmentEditing, MetaTrakt.DepartmentProducing, MetaTrakt.DepartmentCamera, MetaTrakt.DepartmentVisual, MetaTrakt.DepartmentSound, MetaTrakt.DepartmentCostume, MetaTrakt.DepartmentLighting, MetaTrakt.DepartmentArt, MetaTrakt.DepartmentCrew]
				departments = [i.title() for i in departments]
				for item in items:
					if 'profession' in item:
						item['profession'] = Tools.listSort(item['profession'], key = lambda i : Tools.listIndex(data = departments, value = i.get('department')))

			if date and extended: items = self._filterRange(items = items, attribute = ['time', MetaTools.ReleasePremiere], filter = date, range = None, unknown = unknown) # Non-extended data does not have a date.
			elif year: items = self._filterRange(items = items, attribute = 'year', filter = year, range = None, unknown = unknown)

			if language: items = self._filterList(items = items, attribute = 'language', filter = language, unknown = unknown)
			if country: items = self._filterList(items = items, attribute = 'country', filter = country, unknown = unknown)
			if certificate: items = self._filterValue(items = items, attribute = 'mpaa', filter = certificate, unknown = unknown)
			if status: items = self._filterValue(items = items, attribute = 'status', filter = status, unknown = unknown)
			if episode: items = self._filterValue(items = items, attribute = 'type', filter = episode, unknown = unknown)
			if rating: items = self._filterRange(items = items, attribute = [self._tempKey(), self.id(), 'voting', 'rating'], filter = self._parameterRating(rating = rating), range = True, unknown = unknown)
			if votes: items = self._filterRange(items = items, attribute = [self._tempKey(), self.id(), 'voting', 'votes'], filter = self._parameterVotes(votes = votes, media = media, niche = niche), range = True, unknown = unknown)
			if action: items = self._filterValue(items = items, attribute = [self._tempKey(), self.id(), 'action'], filter = action, unknown = unknown)

			# Do not filter anymore, since the studio/network values are now converted to a list of Trakt studios IDs, and the metadata attributes returned by the API are names/strings.
			#if studio: items = self._filterValue(items = items, attribute = 'studio', filter = studio, unknown = unknown)
			#if network: items = self._filterValue(items = items, attribute = 'studio', filter = network, unknown = unknown) # Network is added to the "studio" attribute.

			# Some TV movies and specials have no genre and/or duration. Still include them.
			unknown = True if unknown is None else unknown

			if Media.isShort(niche):
				# Only some shorts have "short" listed as their genre on Trakt.
				# Allow both, those with genre, and those with a short duration.
				items1 = self._filterRange(items = items, attribute = 'duration', filter = duration, range = False, unknown = unknown) if duration else []
				items2 = self._filterList(items = items, attribute = 'genre', filter = genre, unknown = unknown) if genre else []
				items = Tools.listUnique(items1 + items2)
			else:
				if duration: items = self._filterRange(items = items, attribute = 'duration', filter = duration, range = True, unknown = unknown)
				if genre: items = self._filterList(items = items, attribute = 'genre', filter = genre, unknown = unknown)

			if sort:
				items = self.mMetatools.sort(items = items, sort = sort, order = order, inplace = True)

			if limit:
				if page is None: page = 1
				items = items[(page - 1) * limit : page * limit]

		return items

	def _filterDefault(self, filter, niche = None):
		# Only filter if a specific niche is being retrieved.
		# If we only retrieve general movies without specific niche (feature/short/special), include everything.
		# Otherwise listHistoryMovie() will filter out shorts/specials.
		if filter is None: filter = MetaProvider.FilterLenient if niche else MetaProvider.FilterNone
		return filter

	def _filterNested(self, item, attribute):
		if Tools.isArray(attribute):
			value = item
			for i in attribute:
				value = value.get(i)
				if value is None: break
		else: value = item.get(attribute)
		return value

	def _filterMedia(self, items, media, niche, unknown = False):
		try:
			if media:
				result = []
				mini = Media.isMini(niche)
				for item in items:
					valueMedia = self._filterNested(item = item, attribute = 'media')
					if valueMedia:
						if valueMedia == media:
							valueNiche = self._filterNested(item = item, attribute = 'niche')
							if not niche or Media.isMedia(media = valueNiche, type = niche):
								# Retrieving by "mini-series" genre does not work, so we retrieve using a query keyword "mini series".
								# This does retreive mini-series, but also returns normal series (eg: that have the keywrod "mini" in their title/plot).
								# Filter these out by number of episodes. Anything above 25 episodes is considered multiple seasons.
								# This is not perfect, since some series (eg: tt0361243) have 25 episodes over multiple seasons.
								if mini:
									status = item.get('status')
									if status:
										status = status.lower()
										if 'return' in status or 'continue' in status: continue

									count = item.get('count')
									if count:
										count = count.get('episode')
										if count:
											count = count.get('total') or count.get('released')
											if not count is None and count > 25: continue

								result.append(item)
					elif unknown: result.append(item)
				items = result
		except: self._logError()
		return items

	def _filterRange(self, items, attribute, filter, range = None, unknown = False):
		try:
			if not filter is None:
				if not filter is None and not Tools.isArray(filter):
					if range is True: filter = [filter, None]
					elif range is False: filter = [None, filter]
					else: filter = [filter, filter]
				minimum = filter[0]
				maximum = filter[1]

				result = []
				for item in items:
					value = self._filterNested(item = item, attribute = attribute)
					if value or not minimum: # Also check minimum, in case the minimum is 0/None.
						if (value is None or minimum is None or value >= minimum) and (value is None or maximum is None or value <= maximum):
							result.append(item)
					elif unknown:
						result.append(item)
				items = result
		except: self._logError()
		return items

	def _filterList(self, items, attribute, filter, unknown = False):
		try:
			if filter:
				result = []
				includeAny = []
				excludeAny = []
				includeMain = []
				excludeMain = []

				if not Tools.isArray(filter): filter = [filter]
				for i in filter:
					value = i.lower().replace(MetaTrakt.SelectIncludeAny, '').replace(MetaTrakt.SelectExcludeAny, '').replace(MetaTrakt.SelectIncludeMain, '').replace(MetaTrakt.SelectExcludeMain, '')
					value = value.replace('-', '').replace('_', '').replace(' ', '').strip()
					if i.startswith(MetaTrakt.SelectExcludeAny): excludeAny.append(value)
					elif i.startswith(MetaTrakt.SelectIncludeMain): includeMain.append(value)
					elif i.startswith(MetaTrakt.SelectExcludeMain): excludeMain.append(value)
					else: includeAny.append(value)

				for item in items:
					value = self._filterNested(item = item, attribute = attribute)

					# Many endpoints return both a show and an episode object.
					# The show object might have more metadata than the episode (eg: genre).
					# During post-request filtering, the filters might be applied to the episode, which does not have the metadata.
					# Also scan the other objects.
					# Eg: listRating() to return anime.
					if not value and Media.isSerie(item['media']):
						for i in [MetaTrakt.TypeShow, MetaTrakt.TypeEpisode, MetaTrakt.TypeSeason]:
							i = self._temp(item = item, key = ['detail', i])
							if i:
								value = self._filterNested(item = i, attribute = attribute)
								if value: break

					if value:
						if not Tools.isArray(value): value = [value]
						for i in range(len(value)):
							val = value[i].lower().replace('-', '').replace('_', '').replace(' ', '').strip()
							if i == 0:
								if excludeMain and val in excludeMain:
									break
								elif includeMain:
									if val in includeMain: result.append(item)
									break
							if excludeAny and val in excludeAny:
								break
							elif not includeAny or val in includeAny:
								result.append(item)
								break
					elif unknown: result.append(item)
				items = result
		except: self._logError()
		return items

	def _filterValue(self, items, attribute, filter, unknown = False):
		try:
			if filter:
				result = []
				if not Tools.isArray(filter): filter = [filter]
				filter = [i.lower().replace('-', '').replace('_', '').replace(' ', '').strip() for i in filter]
				for item in items:
					value = self._filterNested(item = item, attribute = attribute)
					if value:
						if value.lower().replace('-', '').replace('_', '').replace(' ', '').strip() in filter:
							result.append(item)
					elif unknown: result.append(item)
				items = result
		except: self._logError()
		return items

	##############################################################################
	# INTERNAL
	##############################################################################

	def _internal(self, items = None, errors = None, initial = None, filter = None, structure = None, final = None, limit = None, more = None, detail = None, internal = True):
		if internal:
			if final is None: final = self._internalCount(items = items)

			if limit is None:
				try: limit = self._temp(item = items[0], key = ['list', 'limit'])
				except: limit = None

			if more is None:
				try: more = self._temp(item = items[0], key = ['list', 'pages']) > self._temp(item = items[0], key = ['list', 'page'])
				except: more = False

			return {
				'items' : items,
				'errors' : errors,
				'more'	: bool(more),
				'count' : {
					'limit'		: limit,
					'initial'	: initial or final,
					'filter'	: filter or final,
					'structure'	: structure or final,
					'final'		: final,
				},
			}
		else:
			if detail: return items, errors
			else: return items

	def _internalCount(self, items = None):
		try: return len(items)
		except: return 0

	##############################################################################
	# STRUCTURE
	##############################################################################

	def _structure(self, items, structure = None, media = None):
		# For certain endpoints (eg: calendars, user ratings, etc), Trakt returns both an episode/season object and a show object for each title.
		# By default the requested media type is returned. Eg: retrieving season ratings will by default return season objects.
		# The other objects are still accessible from the nested ['temp']['detail'] attribute.
		# It might be useful to sometimes return a different object. Eg: list all shows which are airing an episode today (Trakt calendar returns episodes).
		try:
			if structure is None or structure is True: structure = media
			if items and not structure is False:
				if Media.isSerie(structure):
					if Media.isShow(structure): structure = Media.Show
					elif Media.isSeason(structure): structure = Media.Season
					elif Media.isEpisode(structure): structure = Media.Episode
					medias = [Media.Show, Media.Season, Media.Episode]

					for i in range(len(items)):
						item = items[i]
						media = item.get('media')
						detail = self._temp(item = item, key = 'detail')

						if detail:
							values = {}
							for j in medias:
								value = detail.get(j)
								if not value and media == j: value = item
								if value: values[j] = value
							for j in medias:
								self._tempRemove(item = values.get(j), key = 'detail')

							item = values.get(structure)
							if item:
								try: del values[structure]
								except: pass
								if values: self._tempSet(item = item, key = 'detail', value = values)
								items[i] = item
		except: self._logError()
		return items

	##############################################################################
	# LOOKUP
	##############################################################################

	# Efficiently lookup by ID or title.
	# deviation: also search one year before and after the specified year.
	# match: do an additional local string match when doing a title lookup, in case Trakt returns partial (incorrect) matches. Note that this will eliminate alias/translation matches, since they are not returned with the metadata.
	def lookup(self, media, trakt = None, imdb = None, tmdb = None, tvdb = None, title = None, year = None, deviation = None, match = True, extended = None, concurrency = False, cache = True, memory = True, detail = False):
		if memory and not detail: # Only summarized data is stored in memory.
			result = self._lookupGet(media = media, trakt = trakt, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year)
			if result: return result

		# cache=False: returns the current cached data and does a refresh in the background. There is no real usecase for this, so always refresh in the foreground (cache=None).
		if cache is False: cache = None
		elif cache is True: cache = Cache.TimeoutDay3 # This is the default timeout, but explicitly set it here to ensure it is cached for more than a day.

		iterator = []

		# Lookup by ID first.
		ids = (('trakt', trakt), ('imdb', imdb), ('tmdb', tmdb), ('tvdb', tvdb))
		for i in ids: # Order by likelihood of finding by this ID.
			if i[1]: iterator.append({'link' : MetaTrakt.LinkSearchId, 'type' : media, 'search' : media, 'provider' : i[0], 'id' : i[1], 'result' : i[0]}) # Important to add "search", which is added as the "type" parameter.

		# Lookup by title if the IDs were not found.
		if title:
			lookup = {'link' : MetaTrakt.LinkSearchQuery, 'type' : media, 'query' : title, 'result' : 'title'}
			if year: lookup['year'] = [year - 1, year + 1] if deviation else [year, year]
			iterator.append(lookup)

		# concurrency=False and exit=True: execute sequentially until the a result is found.
		data = self._execute(iterator = iterator, media = media, extended = extended, cache = cache, concurrency = concurrency, exit = True)

		result = None
		if data:
			for i in ids:
				result = data.get(i[0])
				if result: break

			if not result:
				if match:
					from lib.modules.tools import Matcher
					def matcher(metadata, strict = True):
						if title:
							threshold = 0.9 if strict else 0.8
							for i in ('title', 'originaltitle', 'tvshowtitle'):
								title2 = metadata.get(i)
								if title2:
									# Also match Jaro, since Levenshtein is sometimes too strict.
									# Eg: "Plur1bus" vs "Pluribus".
									if Matcher.levenshtein(title, title2, ignoreCase = True, ignoreSpace = False, ignoreNumeric = False, ignoreSymbol = True) >= threshold: return True
									elif Matcher.jaro(title, title2, ignoreCase = True, ignoreSpace = False, ignoreNumeric = False, ignoreSymbol = True) >= threshold: return True
						return False

				results = data.get('title')
				if results:
					# Prefer the first one with the exact year.
					if deviation and year:
						# First do a strict match.
						if not result:
							for i in results:
								if i.get('year') == year:
									if not match or matcher(i, strict = True):
										result = i
										break

						# Then do a lenient match.
						if not result and match:
							for i in results:
								if i.get('year') == year:
									if not match or matcher(i, strict = False):
										result = i
										break

					# Otherwise pick the first item.
					if not result and (not match or matcher(results[0], strict = True)): result = results[0]

					# Otherwise pick the first item with lenient matching
					if not result and match and matcher(results[0], strict = False): result = results[0]

		if result:
			result = result[0] if Tools.isArray(result) else result

			if memory:
				data = self._lookupSet(media = media, data = result, trakt = trakt, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year)
				if not detail: return data

			if detail: return result
			else: return self._lookupData(media = media, data = result, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year)
		return None

	def lookupMovie(self, trakt = None, imdb = None, tmdb = None, tvdb = None, title = None, year = None, deviation = None, match = True, extended = None, concurrency = False, cache = True):
		return self.lookup(media = Media.Movie, trakt = trakt, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year, deviation = deviation, match = match, extended = extended, concurrency = concurrency, cache = cache)

	def lookupShow(self, trakt = None, imdb = None, tmdb = None, tvdb = None, title = None, year = None, deviation = None, match = True, extended = None, concurrency = False, cache = True):
		return self.lookup(media = Media.Show, trakt = trakt, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year, deviation = deviation, match = match, extended = extended, concurrency = concurrency, cache = cache)

	def lookupEpisode(self, trakt = None, imdb = None, tmdb = None, tvdb = None, title = None, year = None, deviation = None, match = True, extended = None, concurrency = False, cache = True):
		return self.lookup(media = Media.Episode, trakt = trakt, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year, deviation = deviation, match = match, extended = extended, concurrency = concurrency, cache = cache)

	def _lookupData(self, data, media = None, trakt = None, imdb = None, tmdb = None, tvdb = None, title = None, year = None):
		try:
			result = {'media' : media}
			try: result['media'] = data['media']
			except: pass
			try: result.update(data['id'])
			except: pass

			# Add known IDs if not on Trakt.
			# Especially since lookups are done specifically if Trakt does not have the IMDb yet.
			if trakt and not result.get('trakt'): result['trakt'] = trakt
			if tmdb and not result.get('tmdb'): result['tmdb'] = tmdb
			if tvdb and not result.get('tvdb'): result['tvdb'] = tvdb

			# If the IMDb changed.
			# The lookup ID is still the old one, while Trakt has a new ID.
			if imdb:
				if not result.get('imdb'): result['imdb'] = imdb
				elif not imdb == result.get('imdb'): result['imdx'] = imdb

			# Prefer the searched title/year, since Trakt can return a different title or deviated year.
			result['title'] = title or data.get('title')
			result['year'] = year or data.get('year')

			return result
		except: Logger.error()

	def _lookupGet(self, media, trakt = None, imdb = None, tmdb = None, tvdb = None, title = None, year = None):
		try:
			lookup = Memory.get(fixed = MetaTrakt.PropertyLookup, local = True, kodi = True)
			if lookup:
				lookup = lookup.get(media)
				if lookup:
					for i in (('trakt', trakt), ('imdb', imdb), ('tmdb', tmdb), ('tvdb', tvdb)):
						if i[1]:
							try: return lookup[i[0]][i[1]]
							except: pass
					if title:
						try: return lookup['title'][title + '_' + str(year)]
						except: pass
		except: Logger.error()
		return None

	def _lookupSet(self, media, data, trakt = None, imdb = None, tmdb = None, tvdb = None, title = None, year = None):
		try:
			lookup = Memory.get(fixed = MetaTrakt.PropertyLookup, local = True, kodi = True)
			if lookup is None: lookup = {}
			if not media in lookup: lookup[media] = {}
			lookuped = lookup.get(media)

			data = self._lookupData(media = media, data = data, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year)

			for i in ('trakt', 'imdb', 'imdx', 'tmdb', 'tvdb'):
				id = data.get(i)
				if id:
					if i == 'imdx': i = 'imdb'
					if not i in lookuped: lookuped[i] = {}
					lookuped[i][id] = data

			if data.get('title'):
				if not 'title' in lookuped: lookuped['title'] = {}
				lookuped['title'][data.get('title') + '_' + str(data.get('year'))] = data

			Memory.set(fixed = MetaTrakt.PropertyLookup, value = lookup, local = True, kodi = True)
			return data
		except: Logger.error()
		return None

	##############################################################################
	# SEARCH
	##############################################################################

	'''
		SEARCH BY QUERY

		NOTES:
			Not all parameters are always used, depending on the media.
				For instance, the genre is ignored for docus, since docus can only be found using a fixed genre.
				Check the individual functions below to see which parameters are allowed for which media.
			This API endpoint does not always strictly adhere to the page limit.
				There can be anywhere from [limit, limit * 2] results returned.
				If multiple medias are specified, close to "limit * 2" results are returned.
				But even with a single media, sometimes a few more than "limit" results are returned.
				Not sure if this is a temporary Trakt bug, or this is part of the permanent logic.
				The pagination headers returned by Trakt indicate that the correct page/limit parameters where used during execution.

		MEDIA:
			None:		Movie + Show
			True:		Movie + Show + Episode + Person + List
			False:		Movie + Show + Person
			String:		Single media from the list below.
			List:		Multiple medias from the list below. Certain combinations of medias, especially Level-1 and Level-2, might not work correctly (eg [Movie + Set] or [Short + Mini]).

			MOVIE
				FeatureTheater:		Level-0 support.
				FeatureTelevision:	Level-2 support.
				ShortTheater:		Level-1 support.
				ShortTelevision:	Level-2 support.
				SpecialTheater:		Level-2 support.
				SpecialTelevision:	Level-2 support.
			SERIE
				Multi:				Level-0 support.
				Mini:				Level-2 support.
				Episode:			Level-0 support.
			GROUP
				Set:				Level-1 support.
				List:				Level-0 support.
			ENTITY
				Person:				Level-0 support.
			TOPIC
				Anima:				Level-0 support.
				Anime:				Level-0 support.
				Donghua:			Level-0 support.
				Docu:				Level-0 support.
				Family:				Level-0 support.
				Music:				Level-0 support.
				Sport:				Level-0 support.
				Telly:				Level-0 support.
				Soap:				Level-0 support.
				Intrest:			Level-0 support.

		PARAMETERS:
			date:				Not supported by the Trakt API. Dates are converted to years for pre-request filtering. The accurate dates are only filtered post-request.
				True:			Same as ReleaseNew.
				False:			Same as ReleaseFuture.
				ReleaseNew:		Cinema released today or before.
				ReleaseHome:	Digital or TV release. Note this is just an estimation and does not neccessarily mean there is a home release available yet.
				ReleaseFuture:	Future releases after today.
				Integer:		Small positive values are number of days into the past from today. Small negative values are number of days into the future from today. Large positive values are ending timestamps. Large negative values are starting timestamps.
				String:			Formatted date string as the ending date.
				List:			Date range. Can be timestamps or date strings.
			sort:				Sorting is only applied post-request to a single page.
	'''
	def search(self, media = None, niche = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, watch = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, award = None, list = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, field = None, structure = None, cache = None, internal = None, concurrency = None, split = None, **parameters): # parameters: since "detail" is added in _execute().
		try:
			#gaiaremove
			# UPDATE (2025-12):
			# NB: The search endpoint has changed and does not work as it previously did.
			#	1. The limit is now capped at 50.
			#	2. Paging is not possible anymore.
			#	3. If the limit is above 50, the request is now split (see below MetaTrakt.LimitSearch). However, since paging does not work anymore, every page returns the same results.
			#	4. Trakt seems to now only use the "query" and "limit" parameters. Everything else is ignored.
			# Check this in regular intervals to see if Trakt has fixed this.
			# 	Eg: Make a call with a limit of 100 and check if 100 items are returned.
			# 	Eg: Make a call with a year and check if the returned items are within that year.
			# If this is fixed, also revert the code in MetaManager._search().

			# Update (2025-12):
			# Trakt has now introduced a hard upper limit of 50.
			# If more items are requested, it caps the results at 50.
			# Split the query over multiple requests and add paging.
			if limit and limit > MetaTrakt.LimitSearch and split is None:
				pages = Math.roundUp(limit / MetaTrakt.LimitSearch)
				limitOriginal = limit
				limit = MetaTrakt.LimitSearch

				items = self._execute(function = self.search, iterator = [{'page' : i + 1} for i in range(pages)], split = False, structure = None, media = media, niche = niche, query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, watch = watch, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, award = award, limit = limit, sort = sort, order = order, extended = extended, filter = filter, field = field, cache = cache, internal = internal, concurrency = concurrency)
				countInitial = self._internalCount(items = items)

				items = self._filter(
					items = items,
					sort = sort, order = order,
					limit = limitOriginal,
				)
				countFilter = self._internalCount(items = items)

				# Change the returned structure for shows/seasons/episodes.
				items = self._structure(items, structure = structure, media = media)
				countStructure = self._internalCount(items = items)

				return self._internal(items = items, initial = countInitial, filter = countFilter, structure = countStructure, internal = internal)

			# When doing a global search over multiple medias, only include certain types.
			# Do not include the following media (in addition to Movie/Show/Person):
			#	Episode:
			#		When searching "kevin costner", close to all results returned are episodes.
			#		No Movie/Show/Person are returned. In this case we might specifically want a Person, probably somewhere in the top of the results.
			#	Set:
			#		Adding a "collection" keyword to the query is not possible, since it would also apply to Movie/Show/Person.
			#		Adding "types=official" makes the search return only sets, but no Movie/Show/Person.
			#		Only adding the "list" type without a query or "types=official", returns a ton of "personal" lists, but no "official" lists (sets), just spamming the results.
			if media is None: media = [Media.Movie, Media.Show]
			elif media is True: media = [Media.Movie, Media.Show, Media.Episode, Media.Person, Media.List]
			elif media is False: media = [Media.Movie, Media.Show, Media.Person]

			support, media, medias, niche, query, date, year, duration, genre, language, country, certificate, status, episode, studio, network, rating, votes, sort, order, filter, field, list, original = self._parameterFilter(media = media, niche = niche, query = query, keyword = keyword, list = list, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, episode = episode, company = company, studio = studio, network = network, rating = rating, award = award, votes = votes, sort = sort, order = order, filter = filter, field = field)
			if not support: return self._internal(internal = internal)

			items = self._retrieve(
				link = MetaTrakt.LinkSearchQuery, cache = cache,
				media = media, medias = medias, niche = niche, query = query or '', list = list, # query = '', otherwise Trakt returns HTTP 400.
				year = year, duration = duration,
				genre = genre, language = language, country = country, certificate = certificate,
				status = status, watch = watch, episode = episode,
				studio = studio, network = network,
				rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating,
				page = page, limit = limit, extended = extended, field = field,
			)
			countInitial = self._internalCount(items = items)

			# In case multiple medias are specified that cannot be filtered through the API.
			items = self._filter(
				media = media, niche = niche, items = items,
				sort = sort, order = order, filter = filter,
				date = date, year = year, duration = duration,
				genre = genre, language = language, country = country, certificate = certificate,
				status = status, episode = episode, studio = studio, network = network,
				rating = rating, votes = votes,
				extended = extended,
			)
			countFilter = self._internalCount(items = items)

			# Change the returned structure for shows/seasons/episodes.
			items = self._structure(items, structure = structure, media = media)
			countStructure = self._internalCount(items = items)

			return self._internal(items = items, initial = countInitial, filter = countFilter, structure = countStructure, internal = internal)
		except: self._logError()
		return self._internal(internal = internal)

	# Feature, short, and special movies.
	def searchMovie(self, niche = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, watch = None, company = None, studio = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, award = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, field = None, cache = None, internal = None):
		return self.search(media = Media.Movie, niche = niche, query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, watch = watch, company = company, studio = studio, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, award = award, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, field = field, cache = cache, internal = internal)

	# Theater and television feature movies.
	def searchFeature(self, niche = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, watch = None, company = None, studio = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, award = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, field = None, cache = None, internal = None):
		return self.searchMovie(niche = self._parameterNiche(niche = niche, extension = Media.Feature), query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, watch = watch, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, award = award, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, field = field, cache = cache, internal = internal)

	# Theater and television short films.
	def searchShort(self, niche = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, watch = None, company = None, studio = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, award = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, field = None, cache = None, internal = None):
		return self.searchMovie(niche = self._parameterNiche(niche = niche, extension = Media.Short), query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, watch = watch, company = company, studio = studio, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, award = award, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, field = field, cache = cache, internal = internal)

	# Theater and television specials.
	def searchSpecial(self, niche = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, watch = None, company = None, studio = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, award = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, field = None, cache = None, internal = None):
		return self.searchMovie(niche = self._parameterNiche(niche = niche, extension = Media.Special), query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, watch = watch, company = company, studio = studio, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, award = award, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, field = field, cache = cache, internal = internal)

	# Movie sets.
	def searchSet(self, niche = None, query = None, keyword = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, field = None, cache = None, internal = None):
		return self.search(media = Media.Set, niche = niche, query = query, keyword = keyword, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, field = field, cache = cache, internal = internal)

	# Multi-season shows and single-season mini-series.
	def searchShow(self, niche = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, watch = None, company = None, studio = None, network = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, award = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, field = None, structure = None, cache = None, internal = None):
		return self.search(media = Media.Show, niche = niche, query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, watch = watch, company = company, studio = studio, network = network, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, award = award, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, field = field, structure = structure, cache = cache, internal = internal)

	# Multi-season shows (will most likely include mini-series).
	def searchMulti(self, niche = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, watch = None, company = None, studio = None, network = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, award = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, field = None, structure = None, cache = None, internal = None):
		return self.searchShow(niche = self._parameterNiche(niche = niche, extension = Media.Multi), query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, watch = watch, company = company, studio = studio, network = network, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, award = award, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, field = field, structure = structure, cache = cache, internal = internal)

	# Single-season mini-series (does not work well).
	def searchMini(self, niche = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, watch = None, company = None, studio = None, network = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, award = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, field = None, structure = None, cache = None, internal = None):
		return self.searchShow(niche = self._parameterNiche(niche = niche, extension = Media.Mini), query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, watch = watch, company = company, studio = studio, network = network, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, award = award, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, field = field, structure = structure, cache = cache, internal = internal)

	# Show episodes.
	def searchEpisode(self, niche = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, watch = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, award = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, field = None, structure = None, cache = None, internal = None):
		return self.search(media = Media.Episode, niche = niche, query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, watch = watch, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, award = award, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, field = field, structure = structure, cache = cache, internal = internal)

	# People.
	def searchPerson(self, query = None, keyword = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, field = None, cache = None, internal = None):
		return self.search(media = Media.Person, query = query, keyword = keyword, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, field = field, cache = cache, internal = internal)

	##############################################################################
	# DISCOVER
	##############################################################################

	'''
		DISCOVER BY FILTERS

		NOTES:
			Not all parameters are always used, depending on the media.
				For instance, the genre is ignored for docus, since docus can only be found using a fixed genre.
				Check the individual functions below to see which parameters are allowed for which media.
			Trakt does neither support a proper discover endpoint, nor sorting.
				Use different endpoints to simulate discovery.
				All endpoints support filtering and paging, but are returned in different predefined orders.
			Multiple medias can be provided, but this will fall back to the search endpoint.
				In this case, the sort and period parameters will be ignored.
			This API endpoint does not always strictly adhere to the page limit.
				If the search endpoint fallback is used, more items might be returned. More info in the search() comment.
 				If certain sort methods are used (eg trending), less items might be returned, depending on the filters.

			Different API endpoints are used, depending on the parameters passed.
				1. sort:		/{movies|shows}/{trending|popular|favorited|played|watched|collected|anticipated}
				2. all else:	/search/{movie|show|episode|person|list}

		MEDIA:
			None:		Movie + Show
			True:		Movie + Show
			False:		Movie + Show
			String:		Single media from the list below.
			List:		Multiple medias from the list below. Does not support sorting. Certain combinations of medias, especially Level-1 and Level-2, might not work correctly (eg [Movie + Set] or [Short + Mini]).

			MOVIE
				FeatureTheater:		Level-0 support with sorting.
				FeatureTelevision:	Level-2 support with sorting.
				ShortTheater:		Level-1 support with sorting.
				ShortTelevision:	Level-2 support with sorting.
				SpecialTheater:		Level-2 support with sorting.
				SpecialTelevision:	Level-2 support with sorting.
			SERIE
				Multi:				Level-0 support with sorting.
				Mini:				Level-2 support with sorting.
				Episode:			Level-0 support without sorting via search().
			GROUP
				Set:				Level-1 support without sorting via search().
				List:				Level-0 support without sorting via search().
			ENTITY
				Person:				Level-0 support without sorting via search().
			TOPIC
				Anima:				Level-0 support.
				Anime:				Level-0 support.
				Donghua:			Level-0 support.
				Docu:				Level-0 support.
				Family:				Level-0 support.
				Music:				Level-0 support.
				Sport:				Level-0 support.
				Telly:				Level-0 support.
				Soap:				Level-0 support.
				Intrest:			Level-0 support.

		PARAMETERS:
			date:				Not supported by the Trakt API. Dates are converted to years for pre-request filtering. The accurate dates are only filtered post-request. If release or the New/Home niches are specified, the date is forwarded to release().
				True:			Same as ReleaseNew.
				False:			Same as ReleaseFuture.
				ReleaseNew:		Cinema released today or before.
				ReleaseHome:	Digital or TV release. Note this is just an estimation and does not neccessarily mean there is a home release available yet.
				ReleaseFuture:	Future releases after today.
				Integer:		Small positive values are number of days into the past from today. Small negative values are number of days into the future from today. Large positive values are ending timestamps. Large negative values are starting timestamps.
				String:			Formatted date string as the ending date.
				List:			Date range. Can be timestamps or date strings.
			sort:				SortTrending/SortPopular/SortAnticipated/SortFavorited/SortPlayed/SortWatched/SortCollected is done pre-request. Other sorting options are only applied post-request to a single page.
	'''

	def discover(self, media = None, niche = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, watch = None, episode = None, company = None, studio = None, network = None, release = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, award = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, field = None, period = None, structure = None, cache = None, internal = None, concurrency = None, split = None, **parameters): # parameters: since "detail" is added in _execute().
		try:
			# Do not call release() if a year was specified (eg: New/Home Releases menu for the Years/Decades menus).
			if release or date or ((Media.isNew(niche) or Media.isHome(niche)) and not year):
				if release is None:
					if Media.isNew(niche): release = MetaTrakt.ReleaseNew
					elif Media.isHome(niche): release = MetaTrakt.ReleaseHome
					else: release = MetaTrakt.ReleaseNew
				return self.release(media = media, niche = niche, release = release, query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, watch = watch, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, structure = structure, cache = cache, internal = internal, concurrency = concurrency)

			# Update (2025-12):
			# Trakt has now introduced a hard upper limit of 250.
			# If more items are requested, it caps the results at 250.
			# Split the query over multiple requests and add paging.
			if limit and limit > MetaTrakt.LimitGeneral and split is None:
				pages = Math.roundUp(limit / MetaTrakt.LimitGeneral)
				limitOriginal = limit
				limit = MetaTrakt.LimitGeneral

				items = self._execute(function = self.discover, iterator = [{'page' : i + 1} for i in range(pages)], split = False, structure = None, media = media, niche = niche, query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, watch = watch, episode = episode, company = company, studio = studio, network = network, release = release, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, award = award, limit = limit, sort = sort, order = order, extended = extended, filter = filter, field = field, period = period, cache = cache, internal = internal, concurrency = concurrency)
				countInitial = self._internalCount(items = items)

				items = self._filter(
					items = items,
					sort = sort, order = order,
					limit = limitOriginal,
				)
				countFilter = self._internalCount(items = items)

				# Change the returned structure for shows/seasons/episodes.
				items = self._structure(items, structure = structure, media = media)
				countStructure = self._internalCount(items = items)

				return self._internal(items = items, initial = countInitial, filter = countFilter, structure = countStructure, internal = internal)

			if sort is None:
				if Media.isBest(niche) or Media.isPrestige(niche) or Media.isPopular(niche): sort = MetaTrakt.SortPopular
				elif Media.isViewed(niche): sort = MetaTrakt.SortPlayed
				elif Media.isTrend(niche): sort = MetaTrakt.SortTrending

			link = None
			sorting = None
			support, media, medias, niche, query, date, year, duration, genre, language, country, certificate, status, episode, studio, network, rating, votes, sort, order, filter, field, list, original = self._parameterFilter(media = media, niche = niche, query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, award = award, sort = sort, order = order, filter = filter, field = field)
			if not support: return self._internal(internal = internal)

			if not Tools.isArray(media) and (not Tools.isArray(medias) or len(medias) == 1):
				if Media.isMovie(media) or Media.isShow(media):
					sortBasic = sort in [MetaTrakt.SortTrending, MetaTrakt.SortPopular, MetaTrakt.SortAnticipated]
					sortPeriod = sort in [MetaTrakt.SortFavorited, MetaTrakt.SortPlayed, MetaTrakt.SortWatched, MetaTrakt.SortCollected]
					if sortBasic or sortPeriod:
						link = MetaTrakt.LinkDiscover
						if sortBasic: period = ''
						sorting = sort
						sort = None
						order = None

			#gaiaremove
			# UPDATE (2025-12):
			# The search endpoint now ignores all parameters and is essentially useless for discovering.
			# More info under search().
			# The next best option is to use the popular endpoint.
			# This endpoint seems to still allow higher limits, paging, and includes all the added parameters (eg year/genre/etc).
			# The only disadvantage is that this always returns the most popular items, instead of random discovery.
			# For now, redirect all discovery calls top the popular endpoint.
			# Check this in regular intervals to see if the search endpoint is fixed by Trakt.
			# If so, this code can be removed again (or just commented out, since this issues might return in the future).
			if link is None:
				if not Tools.isArray(media) and (not Tools.isArray(medias) or len(medias) == 1):
					if Media.isMovie(media) or Media.isShow(media):
						link = MetaTrakt.LinkDiscover
						sorting = MetaTrakt.SortPopular
						sort = MetaTrakt.SortShuffle # At least create some kind of randomness, since the popular endpoint are ordered by rating/votes.
						order = None
						period = ''

			# It seems the search endpoint returns the titles in the same order as SortPopular.
			if link is None:
				return self.search(imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, award = award, page = page, limit = limit, extended = extended, cache = cache, internal = internal, **original)

			items = self._retrieve(
				link = link, cache = cache,
				media = media, medias = medias, niche = niche, query = query, list = list,
				year = year, duration = duration,
				genre = genre, language = language, country = country, certificate = certificate,
				status = status, watch = watch, episode = episode,
				studio = studio, network = network,
				rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating,
				page = page, limit = limit, extended = extended, field = field, period = period, sort = sorting,
			)
			countInitial = self._internalCount(items = items)

			# In case multiple medias are specified that cannot be filtered through the API.
			items = self._filter(
				media = media, niche = niche, items = items,
				sort = sort, order = order, filter = filter,
				date = date, year = year, duration = duration,
				genre = genre, language = language, country = country, certificate = certificate,
				status = status, episode = episode, studio = studio, network = network,
				rating = rating, votes = votes,
				extended = extended,
			)
			countFilter = self._internalCount(items = items)

			# Change the returned structure for shows/seasons/episodes.
			items = self._structure(items, structure = structure, media = media)
			countStructure = self._internalCount(items = items)

			return self._internal(items = items, initial = countInitial, filter = countFilter, structure = countStructure, internal = internal)
		except: self._logError()
		return self._internal(internal = internal)

	# Feature, short, and special movies.
	def discoverMovie(self, niche = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, watch = None, company = None, studio = None, release = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, award = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, field = None, cache = None, internal = None, concurrency = None):
		return self.discover(media = Media.Movie, niche = niche, query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, watch = watch, company = company, studio = studio, release = release, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, award = award, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, field = field, cache = cache, internal = internal, concurrency = concurrency)

	# Theater and television feature movies.
	def discoverFeature(self, niche = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, watch = None, company = None, studio = None, release = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, award = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, field = None, cache = None, internal = None, concurrency = None):
		return self.discoverMovie(niche = self._parameterNiche(niche = niche, extension = Media.Feature), query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, watch = watch, company = company, studio = studio, release = release, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, award = award, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, field = field, cache = cache, internal = internal, concurrency = concurrency)

	# Theater and television short films.
	def discoverShort(self, niche = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, watch = None, company = None, studio = None, release = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, award = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, field = None, cache = None, internal = None, concurrency = None):
		return self.discoverMovie(niche = self._parameterNiche(niche = niche, extension = Media.Short), query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, watch = watch, company = company, studio = studio, release = release, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, award = award, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, field = field, cache = cache, internal = internal, concurrency = concurrency)

	# Theater and television specials.
	def discoverSpecial(self, niche = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, watch = None, company = None, studio = None, release = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, award = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, field = None, cache = None, internal = None, concurrency = None):
		return self.discoverMovie(niche = self._parameterNiche(niche = niche, extension = Media.Special), query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, watch = watch, company = company, studio = studio, release = release, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, award = award, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, field = field, cache = cache, internal = internal, concurrency = concurrency)

	# Movie sets.
	def discoverSet(self, niche = None, query = None, keyword = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, field = None, cache = None, internal = None):
		return self.discover(media = Media.Set, niche = niche, query = query, keyword = keyword, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, field = field, cache = cache, internal = internal)

	# Multi-season shows and single-season mini-series.
	def discoverShow(self, niche = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, watch = None, company = None, studio = None, network = None, release = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, award = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, field = None, structure = None, cache = None, internal = None, concurrency = None):
		return self.discover(media = Media.Show, niche = niche, query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, watch = watch, company = company, studio = studio, network = network, release = release, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, award = award, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, field = field, structure = structure, cache = cache, internal = internal, concurrency = concurrency)

	# Multi-season shows (will most likely include mini-series).
	def discoverMulti(self, niche = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, watch = None, company = None, studio = None, network = None, release = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, award = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, field = None, structure = None, cache = None, internal = None, concurrency = None):
		return self.discoverShow(niche = self._parameterNiche(niche = niche, extension = Media.Multi), query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, watch = watch, company = company, studio = studio, network = network, release = release, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, award = award, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, field = field, structure = structure, cache = cache, internal = internal, concurrency = concurrency)

	# Single-season mini-series (does not work well).
	def discoverMini(self, niche = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, watch = None, company = None, studio = None, network = None, release = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, award = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, field = None, structure = None, cache = None, internal = None, concurrency = None):
		return self.discoverShow(niche = self._parameterNiche(niche = niche, extension = Media.Mini), query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, watch = watch, company = company, studio = studio, network = network, release = release, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, award = award, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, field = field, structure = structure, cache = cache, internal = internal, concurrency = concurrency)

	# Show episodes.
	def discoverEpisode(self, niche = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, watch = None, episode = None, company = None, studio = None, network = None, release = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, award = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, field = None, structure = None, cache = None, internal = None, concurrency = None):
		return self.discover(media = Media.Episode, niche = niche, query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, watch = watch, episode = episode, company = company, studio = studio, network = network, release = release, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, award = award, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, field = field, structure = structure, cache = cache, internal = internal, concurrency = concurrency)

	# People.
	def discoverPerson(self, query = None, keyword = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, field = None, cache = None, internal = None):
		return self.discover(media = Media.Person, query = query, keyword = keyword, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, field = field, cache = cache, internal = internal)

	##############################################################################
	# PERSON
	##############################################################################

	'''
		DISCOVER BY PERSON

		NOTES:
			This function is used in different ways, depending on the parameters used:
				1. id: Search all movies or shows someone was cast/crew in, using a person's ID. Returns a list of movies or shows. Filtering only supported post-request. No paging supported, all titles are returned at once.
				2. query: Search using a person's name. Returns a list of people. Filtering and paging supported.
				3. no query or id: Basically "discovering" people. Returns a list of random people. Filtering and paging supported.

		MEDIA:
			None:		Movie + Show (2 separate requests)
			True:		Movie + Show (2 separate requests)
			False:		Movie + Show (2 separate requests)
			String:		Single media from the list below.
			List:		Multiple medias from the list below.

			MOVIE
				FeatureTheater:		Level-0 support.
				FeatureTelevision:	Level-2 support.
				ShortTheater:		Level-1 support.
				ShortTelevision:	Level-2 support.
				SpecialTheater:		Level-2 support.
				SpecialTelevision:	Level-2 support.
			SERIE
				Multi:				Level-0 support.
				Mini:				Level-2 support.
			ENTITY
				Person:			Level-0 support.
			TOPIC
				Anima:				Level-0 support.
				Anime:				Level-0 support.
				Donghua:			Level-0 support.
				Docu:				Level-0 support.
				Family:				Level-0 support.
				Music:				Level-0 support.
				Sport:				Level-0 support.
				Telly:				Level-0 support.
				Soap:				Level-0 support.
				Intrest:			Level-0 support.

		PARAMETERS:
			query:		Search by person name. Returns a list of people.
			id:			Search by person ID (IMDb ID, Trakt ID, or Trakt slug). Returns a list of titles.
			page:		Paging is supported by the API when searching by name. When retrieving by person ID, all titles are returned as one. Paging is applied post-request in this case.
			sort:		Sorting is only applied post-request to a single page.
	'''

	def person(self, media = None, niche = None, query = None, id = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, duplicate = None, filter = None, field = None, cache = None, internal = None, concurrency = None):
		try:
			if id:
				support, media, medias, niche, query, date, year, duration, genre, language, country, certificate, status, episode, studio, network, rating, votes, sort, order, filter, field, list, original = self._parameterFilter(media = media, niche = niche, query = query, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, sort = sort, order = order, filter = filter, field = field)
				if not support: return self._internal(internal = internal)

				if len(medias) > 1: # Request movies and shows together.
					if sort is None: sort = MetaTools.SortNewest
					items = self._execute(function = self.person, iterator = [{'media' : i} for i in medias], niche = niche, id = id, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, field = field, cache = cache, concurrency = concurrency)
					countInitial = self._internalCount(items = items)

					items = self._filter(
						items = items,
						sort = sort, order = order,
						page = page, limit = limit,
					)
					countFilter = self._internalCount(items = items)
				else:
					if duplicate is None: duplicate = MetaTrakt.DuplicateMerge

					# Copy the media to allow eg: movie-docu used by filter() below.
					if Media.isSerie(media): media = Media.Show
					else: media = Media.Movie

					items = self._retrieve(
						link = MetaTrakt.LinkPersonFilmography, cache = cache,
						media = media, medias = medias, niche = niche, id = id,
						page = False, limit = False, extended = extended,
					)
					countInitial = self._internalCount(items = items)

					# The person endpoint does not have filters.
					items = self._filter(
						media = media, niche = niche, items = items,
						sort = sort, order = order,
						duplicate = duplicate, filter = filter,
						page = page, limit = limit,
						date = date, year = year, duration = duration,
						genre = genre, language = language, country = country, certificate = certificate,
						status = status, studio = studio, network = network,
						rating = rating, votes = votes,
					)
					countFilter = self._internalCount(items = items)

				return self._internal(items = items, initial = countInitial, filter = countFilter, internal = internal)
			else:
				return self.searchPerson(query = query, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, field = field, cache = cache, internal = internal)
		except: self._logError()
		return self._internal(internal = internal)

	# Feature, short, and special movies.
	def personMovie(self, niche = None, id = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, duplicate = None, filter = None, field = None, cache = None, internal = None):
		return self.person(media = Media.Movie, niche = niche, id = id, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, duplicate = duplicate, filter = filter, field = field, cache = cache, internal = internal)

	# Theater and television feature movies.
	def personFeature(self, niche = None, id = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, duplicate = None, filter = None, field = None, cache = None, internal = None):
		return self.personMovie(niche = self._parameterNiche(niche = niche, extension = Media.Feature), id = id, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, duplicate = duplicate, filter = filter, field = field, cache = cache, internal = internal)

	# Theater and television short films.
	def personShort(self, niche = None, id = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, duplicate = None, filter = None, field = None, cache = None, internal = None):
		return self.personMovie(niche = self._parameterNiche(niche = niche, extension = Media.Short), id = id, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, duplicate = duplicate, filter = filter, field = field, cache = cache, internal = internal)

	# Theater and television specials (currently does not work at all).
	def personSpecial(self, niche = None, id = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, duplicate = None, filter = None, field = None, cache = None, internal = None):
		return self.personMovie(niche = self._parameterNiche(niche = niche, extension = Media.Special), id = id, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, duplicate = duplicate, filter = filter, field = field, cache = cache, internal = internal)

	# Multi-season shows and single-season mini-series.
	def personShow(self, niche = None, id = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, duplicate = None, filter = None, field = None, cache = None, internal = None):
		return self.person(media = Media.Show, niche = niche, id = id, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, duplicate = duplicate, filter = filter, field = field, cache = cache, internal = internal)

	# Multi-season shows (will most likely include mini-series).
	def personMulti(self, niche = None, id = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, duplicate = None, filter = None, field = None, cache = None, internal = None):
		return self.personShow(niche = self._parameterNiche(niche = niche, extension = Media.Multi), id = id, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, duplicate = duplicate, filter = filter, field = field, cache = cache, internal = internal)

	# Single-season mini-series (currently does not work at all).
	def personMini(self, niche = None, id = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, duplicate = None, filter = None, field = None, cache = None, internal = None):
		return self.personShow(niche = self._parameterNiche(niche = niche, extension = Media.Mini), id = id, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, duplicate = duplicate, filter = filter, field = field, cache = cache, internal = internal)

	##############################################################################
	# RELEASE
	##############################################################################

	'''
		FIND BY RELEASE DATE

		NOTES:
			Trakt calendars return both a show and an episode object for each title. Gaia generates a corresponding season object as well.
				Note that if shows/seasons/episodes are retrieved, the filters are applied to the episode object, not the show object.
				For instance, if new shows are retrieved using a vote range, the votes are for the episode, not for the show or season.
				Although the filters are only applied to the episode, the structure returned by this function is still the requested show/season/episode object.
			Paging is not officially support, but instead paging is simulated by retrieving titles for a limited time period.
				This period can be a few days or a few weeks, depending on the media, or up to the maximum Trakt calendar period of 33 days.
				Based on the media, release type, and number of votes, the number of days will be adjusted to return about 50 titles per "page".
				The actual number of titles returned might vary between requests and whatever is currently released.
				Try to keep the number low, especially for episodes, otherwise opening a menu page might require 100s of detailed show/season/episode metadata to be retrieved.
			Pre-request filtering is supported.

		MEDIA:
			None:		Movie + Show (2 separate requests).
			True:		Movie + Show (2 separate requests).
			False:		Movie + Show (2 separate requests).
			String:		Single media from the list below.
			List:		Multiple medias from the list below (multiple separate requests).

			MOVIE
				FeatureTheater:			Level-0 support.
				FeatureTelevision:		Level-2 support.
				ShortTheater:			Level-1 support.
				ShortTelevision:		Level-2 support.
				SpecialTheater:			Level-2 support.
				SpecialTelevision:		Level-3 support (mostly returns nothing).
			SERIE
				Multi:					Level-0 support.
				Mini:					Level-2 support.
				Season:					Level-0 support.
				SeasonPremiere:			Level-0 support.
				SeasonFinale:			Level-3 support.
				Episode:				Level-0 support.
				EpisodePremiereOuter:	Level-3 support.
				EpisodePremiereInner:	Level-3 support.
				EpisodePremiereMiddle:	Level-4 support (no episodes labeled as "mid_season_premiere").
				EpisodeFinaleOuter:		Level-3 support.
				EpisodeFinaleInner:		Level-3 support.
				EpisodeFinaleMiddle:	Level-3 support.
			TOPIC
				Anima:					Level-0 support.
				Anime:					Level-0 support.
				Donghua:				Level-0 support.
				Docu:					Level-0 support.
				Family:					Level-0 support.
				Music:					Level-0 support.
				Sport:					Level-0 support.
				Telly:					Level-0 support.
				Soap:					Level-0 support.
				Intrest:				Level-0 support.

		PARAMETERS:
			date:			The date range to retrieve releases for. If the date range is greater than one month, it will be split up into multiple requests.
				Integer:	Start date (or end date for future releases). Timestamp, or number of days into the past from now.
				String:		Start date (or end date for future releases) formatted as YYYY-MM-DD.
				List:		Date range. Either None (current date), timestamp, number of days, date string.
			user:			If only titles related to the user should be returned. Eg: titles watched, collected, or watchlisted.
				None:		All titles.
				False:		All titles.
				True:		Only user-specific titles.
			duplicate:		Remove duplicate episodes from the same show. If all episodes of a season are released on the same day, they will appear in the same list, although we might only want to display a single episode for the show.
				None:		Remove duplicates and only keep the first episode.
				False:		Remove duplicates and only keep the first episode.
				True:		Keep all duplicates.
				String:		DuplicateAll/DuplicateFirst/DuplicateLast.
			structure:		Return show, season, or episode objects. By default the requested media structure is returned, and all other objects are nested in the ['temp']['detail'] object.
				None:		Convert to the specified media structure. Show=StructureShow, Season=StructureSeason, Episode/ReleaseFinale=StructureEpisode.
				True:		Convert to the specified media structure. Show=StructureShow, Season=StructureSeason, Episode/ReleaseFinale=StructureEpisode.
				False:		Do not convert and return all as the default structure (episode if available, or season otherwise, or show otherwise).
				String:		Convert to a specific structure: StructureShow/StructureSeason/StructureEpisode.
	'''

	def release(self, media = None, niche = None, release = None, future = None, user = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, watch = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, page = None, offset = None, limit = None, sort = None, order = None, extended = None, duplicate = None, filter = None, structure = None, cache = None, internal = None, concurrency = None):
		items = None
		try:
			day = 86400 # Number of seconds in a day.
			full = 33 # Maximum number of days that can be returned for calendars.
			month = 31
			interval = month * day
			more = bool(page or limit)

			# Rating and Votes are adjusted later in the function.
			support, media, medias, niche, query, date, _, duration, genre, language, country, certificate, status, episode, studio, network, rating, votes, sort, order, filter, _, _, original = self._parameterFilter(media = media, niche = niche, query = query, keyword = keyword, release = release, date = date, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, sort = sort, order = order, filter = filter)
			if not support: return self._internal(internal = internal)

			if not release: release = MetaTrakt.ReleaseNew
			futured = release == MetaTrakt.ReleaseFuture
			if not sort: sort = MetaTools.SortHome if (Media.isMovie(media) and (release == MetaTrakt.ReleaseHome or release == MetaTrakt.ReleaseDigital or release == MetaTrakt.ReleasePhysical)) else MetaTools.SortLaunch
			if not order: order = MetaTools.OrderAscending if futured else None

			if date is None:
				date = month # By default Trakt returns 7 days. Set the default to a full month.

				# Increase the duration for niches, otherwise no or very few items are returned.
				# Do not do for Documentaries, since enough are returned by month.
				# Eg: Anime -> Discover -> Explore -> New Releases.
				if Media.isAnime(niche) or Media.isDonghua(niche): date *= 4
				elif Media.isMood(niche) or Media.isAudience(niche) or Media.isRegion(niche): date *= 2

			if not Tools.isArray(date): date = [None, date] if futured else [date, None]
			elif len(date) == 1: date.append(None)
			for i in range(len(date)):
				value = date[i]
				if value is None: value = Time.future(days = 1) if futured else Time.timestamp()
				elif Tools.isInteger(value) and value < 10000: value = Time.future(days = value) if futured else Time.past(days = value)
				elif Tools.isString(value): value = Time.timestamp(fixedTime = value, format = Time.FormatDate, utc = True)
				date[i] = value

			if date[0] > date[1]: date = [date[1], date[0]] # If the date order is incorrect.

			# Split over multiple requests. Trakt can only retrieve up to 33 days at once from calendars.
			multiple = abs(date[1] - date[0]) > interval
			if multiple or (Tools.isList(medias) and len(medias) > 1):
				if multiple:
					dates = []
					start = None
					end = None
					if futured:
						start = date[0]
						while True:
							end = Time.timestamp(fixedTime = Time.format(timestamp = start, format = Time.FormatDate), format = Time.FormatDate) + interval # Convert to date, to reduce to a full day (aka ignore hours/minutes/seconds).
							if end > date[1]: end = date[1]
							dates.append([start, end])
							if end >= date[1]: break
							start = end + day
					else:
						end = date[1]
						while True:
							start = end - interval
							end = Time.timestamp(fixedTime = Time.format(timestamp = start, format = Time.FormatDate), format = Time.FormatDate) + interval # Convert to date, to reduce to a full day (aka ignore hours/minutes/seconds).
							if start < date[0]: start = date[0]
							dates.append([start, end])
							end = start - day
							if end < date[0]: break
					date = dates
				else:
					date = [date[0]]

				iterator = []
				for i in medias:
					offset = len(date)
					for j in date:
						iterator.append({'media' : i, 'date' : j, 'offset' : offset})

				items = self._execute(function = self.release, iterator = iterator, lock = 12, structure = False, niche = niche, release = release, user = user, query = original['query'], keyword = original['keyword'], year = year, duration = original['duration'], genre = original['genre'], language = language, country = country, certificate = certificate, status = status, episode = original['episode'], company = original['company'], studio = original['studio'], network = original['network'], rating = original['rating'], votes = original['votes'], imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, extended = extended, page = page, limit = limit, duplicate = duplicate, filter = original['filter'], cache = cache, concurrency = concurrency)
				countInitial = self._internalCount(items = items)

				items = self._filter(
					media = media,
					items = items,
					sort = sort, order = order, filter = filter, # Sort again, since the threads might not finish in the order of the date ranges.
					page = page, limit = limit,
					duplicate = MetaTrakt.DuplicateFirst, # Always filter out duplicates, since we have overlapping periods.
				)
				countFilter = self._internalCount(items = items)

				# Change the returned structure for shows/seasons/episodes.
				items = self._structure(items, structure = structure, media = media)
				countStructure = self._internalCount(items = items)

				return self._internal(items = items, initial = countInitial, filter = countFilter, structure = countStructure, internal = internal, more = more)
			else:
				if futured: release = MetaTrakt.ReleaseNew

				if media is None:
					if release == MetaTrakt.ReleaseFinale: media = Media.Episode
					else: media = Media.Movie

				# Some movies are only released decades later on DVD.
				# This might result in very old titles (eg 70s) to be included in the list.
				# Filter by year, to avoid these realy old titles.
				if filter >= MetaProvider.FilterLenient and Media.isMovie(media) and year is None and date:
					year = [Time.year(date[0]) - 5, Time.year(date[-1]) + 1]

				# Update (2025-09): Trakt has added a new streaming movie calendar API endpoint.
				# This endpoint now returns the digital release dates and also returns more titles than the DVD calendar.
				# Hence, use the streaming calendar for ReleaseHome.
				calendar = None
				if release == MetaTrakt.ReleaseDigital:
					# The DVD Calendar only returns physical releases, but not digital releases.
					# There is no Digital Calendar.
					# But we can use the normal premiere/new Calendar and filter by the "watchnow" parameter (which is not in the API docs, but available on the website under the Movie Calendar).

					# Changes due to the new streaming calendar.
					#release = MetaTrakt.ReleaseNew
					#if not watch: watch = MetaTrakt.WatchAny
					release = MetaTrakt.ReleaseHome
				elif release == MetaTrakt.ReleasePhysical:
					# Changes due to the new streaming calendar.
					#release = MetaTrakt.ReleaseHome
					release = MetaTrakt.ReleasePhysical
				elif release == MetaTrakt.ReleaseHome and Media.isSerie(media):
					release = MetaTrakt.ReleaseNew
				if Media.isEpisode(media):
					# It seems the "episode_types" parameter is ignored by the calendar endpoints, maybe because it is seen as a "show" endpoint, not an "episode" endpoint, that does not support this parameter.
					if release == MetaTrakt.ReleaseNew or release == MetaTrakt.ReleaseHome or release == MetaTrakt.ReleaseDigital or release == MetaTrakt.ReleasePhysical:
						if Media.isPremiere(niche):
							if Media.isOuter(niche): calendar = MetaTrakt.CalendarNew # Do not use CalendarPremiere, since it also returns season premieres.
							elif Media.isInner(niche): calendar = MetaTrakt.CalendarPremiere
							elif Media.isMiddle(niche): calendar = MetaTrakt.CalendarPremiere
							else: calendar = MetaTrakt.CalendarNew
						elif Media.isFinale(niche): calendar = MetaTrakt.CalendarFinale
						else: calendar = MetaTrakt.CalendarShow
					elif release == MetaTrakt.ReleaseFinale: calendar = MetaTrakt.CalendarFinale
					else: calendar = MetaTrakt.CalendarShow
				elif Media.isSeason(media):
					if Media.isPremiere(niche): calendar = MetaTrakt.CalendarNew
					elif Media.isFinale(niche) or release == MetaTrakt.ReleaseFinale: calendar = MetaTrakt.CalendarFinale
					elif release == MetaTrakt.ReleaseNew or release == MetaTrakt.ReleaseHome or release == MetaTrakt.ReleaseDigital or release == MetaTrakt.ReleasePhysical: calendar = MetaTrakt.CalendarPremiere
					else: calendar = MetaTrakt.CalendarPremiere
				elif Media.isSerie(media):
					if release == MetaTrakt.ReleaseNew or release == MetaTrakt.ReleaseHome or release == MetaTrakt.ReleaseDigital or release == MetaTrakt.ReleasePhysical: calendar = MetaTrakt.CalendarNew
					elif release == MetaTrakt.ReleaseFinale: calendar = MetaTrakt.CalendarFinale
					else: calendar = MetaTrakt.CalendarNew
				else:
					if release == MetaTrakt.ReleaseNew: calendar = MetaTrakt.CalendarMovie

					# Changes due to the new streaming calendar.
					#elif release == MetaTrakt.ReleaseHome: calendar = MetaTrakt.CalendarDvd
					elif release == MetaTrakt.ReleaseHome: calendar = MetaTrakt.CalendarStreaming
					elif release == MetaTrakt.ReleaseDigital: calendar = MetaTrakt.CalendarStreaming
					elif release == MetaTrakt.ReleasePhysical: calendar = MetaTrakt.CalendarDvd

					else: calendar = MetaTrakt.CalendarMovie
				if not calendar: return self._internal(internal = internal)

				if calendar in [MetaTrakt.CalendarNew, MetaTrakt.CalendarPremiere, MetaTrakt.CalendarFinale]: link = MetaTrakt.LinkReleaseGroup
				else: link = MetaTrakt.LinkReleaseMain

				mode = MetaTrakt.CategoryUser if user else MetaTrakt.CategoryAll
				if duplicate is None: duplicate = MetaTrakt.DuplicateFirst

				days = None
				if page or limit:
					if not page: page = 1
					if not offset: offset = 0

					day1 = 1
					day3 = 3
					week1 = 7
					week2 = 14
					week3 = 21
					estimates = {i : full for i in [5000, 2000, 1000, 500, 200, 100, 50, 20, 10, 1, 0]}

					# Estimates that return +- 50 titles per request.
					# Also test across niches such as anime and docus.
					if Media.isMovie(media):
						if release == MetaTrakt.ReleaseNew:
							if Media.isShort(niche) or Media.isSpecial(niche) or Media.isDocu(niche): estimates.update({10 : week3, 1 : week3, 0 : day3})
							elif not Media.isNiche(niche): estimates.update({20 : week3, 10 : week2, 1 : day3, 0 : day3}) # "10 : week3" returned 100-170 items for general New Releases menu.
					elif Media.isSerie(media):
						if Media.isShow(media):
							if not Media.isNiche(niche): estimates.update({10 : week2, 1 : week1, 0 : week1})
						elif Media.isSeason(media):
							if Media.isNiche(niche): estimates.update({1 : week2, 0 : week1})
							else: estimates.update({20 : week3, 10 : week2, 1 : week1, 0 : day3})
						elif Media.isEpisode(media):
							if release == MetaTrakt.ReleaseFinale or Media.isFinale(niche):
								if not Media.isNiche(niche): estimates.update({1 : week2, 0 : week1})
							else:
								if Media.isNiche(niche): estimates.update({10 : week3, 1 : week1, 0 : day3})
								else: estimates.update({50 : week2, 20 : week1, 10 : day3, 1 : day1, 0 : day1})

					if Media.isEpisode(media) and (votes is None or votes == MetaProvider.VotingLenient): votes = 3 # Otherwise too many episodes are returned.

					if Tools.isString(votes): voting = self._parameterVotes(votes = votes, media = media, niche = niche)[0]
					elif Tools.isArray(votes): voting = votes[0]
					else: voting = votes

					if not voting is None:
						for i, j in estimates.items():
							if voting >= i:
								days = j
								break

					if not days: days = estimates[0]

					# If other parameters were set, increase the number of days, since fewer titles will be returned with more parameters specified.
					# If other parameters were set, increase the number of days, since fewer titles will be returned with more parameters specified.
					increase = False
					if language or country or certificate or status or episode or studio or network: increase = True
					elif not Media.isNiche(niche) and genre: increase = True
					elif not Media.isAll(niche) and (rating or imdbRating or imdbVotes or tmdbRating or tmdbVotes or rtRating or rtMeter or mcRating): increase = True
					if increase: days = max(1, min(full, int(Math.roundUp(days * 2))))

					if offset:
						if futured:
							months = ((page - 1) * offset) # Also incorporate the offset, since sometimes (eg Anime) we retrieve multiple months in one go. Otherwise the offset for page 2+ is wrong.
							date = date[0] + (days * day * months)
							if days == full: date -= day * (((page - 1) * offset) + Math.roundUp(months / 2.0)) # (+ day), because Trakt sees the last date as exclusive. (months / 2.0) since only every 2nd month has 31 days.
						else:
							months = ((page - 1) * offset) + 1 # Also incorporate the offset, since sometimes (eg Anime) we retrieve multiple months in one go. Otherwise the offset for page 2+ is wrong.
							date = date[1] - (days * day * months)
							if days == full: date += day * (page + Math.roundUp(months / 2.0)) # (+ day), because Trakt sees the last date as exclusive. (months / 2.0) since only every 2nd month has 31 days.
							else: date += day
						if int(Time.format(date, format = '%m')) == 3: date -= 2 * day # February has less days. Add additional days if we the previous month is January. Assume non-leap year.
					else:
						if futured: date = date[0] + (days * day * (page - 1))
						else: date = date[1] - (days * day * page) + day # (+ day), because Trakt sees the last date as exclusive.
				else:
					# Trakt is able to retrieve up to 33 days.
					# Add another day, since Trakt seems to exclude the end date: [start,start+days).
					days = Math.roundUp(abs(date[1] - date[0]) / day) + 1 # Round up, if both dates do not have the same time.

					# Add one more day to avoid a day-gap between months when retrieving in intervals/threads.
					# Do not do this, othewrwise a date range ['2023-12-01', '2023-12-31'] will return titles from 2024-01-01.
					#if days >= month: days += 1

					date = date[0]

				# In case the 33 days include future days.
				if not future and not futured:
					current = Time.timestamp(fixedTime = Time.format(format = Time.FormatDate) + ' 23:59:59', format = Time.FormatDateTime)
					while days > 0 and (date + ((days - 1) * day)) > current: days -= 1 # (days - 1), because Trakt sees the last date as exclusive.
					if days <= 0: return self._internal(internal = internal)

				# Adjust the rating/votes with the calculated dates.
				# If we use eg VotingNormal/VotingStrict, etc on newer releases, they might not have many votes yet, resulting in few items returned.
				# Reduce the minimum rating/votes for newer releases.
				_, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, rating, votes, _, _, _, _, _, _ = self._parameterFilter(media = media, niche = niche, release = release, date = date, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, rating = rating, votes = votes)

				date = Time.format(timestamp = date, format = Time.FormatDate)

				items = self._retrieve(
					link = link, cache = cache,
					media = media, medias = medias, niche = niche,
					category = MetaTrakt.CategoryShow if Media.isSerie(media) else None,
					user = user,
					mode = mode, calendar = calendar, date = date, days = days, query = query,
					year = year, duration = duration,
					genre = genre, language = language, country = country, certificate = certificate,
					status = status, watch = watch, episode = episode,
					studio = studio, network = network,
					rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating,
					extended = extended,
				)
				countInitial = self._internalCount(items = items)

				# NB: Trakt applies filters to the episode object, not the show object.
				# Always filter by the episode attributes.
				# The structure is converted below.
				items = self._filter(
					media = media,
					niche = niche,
					items = items,

					# Trakt returns the result in ascending date order.
					# Makes more sense to return them from most recent to least recent release date.
					# NB: Sort before we change the structure below.
					sort = sort, order = order, filter = filter,

					# When all episodes of a season are released at once, they will all show up on the same day.
					# By default, filter out duplicates and just keep the first episode.
					duplicate = duplicate,

					# Filter by genre to exclude eg docus from feature movies.
					# This is only done posrt-request. Check parameterFilter() for more info.
					duration = duration, genre = genre,

					# The episode type for pre-request filtering is ignored.
					# Maybe Trakt ignores the parameter, since it is intended for episode endpoints, and this is seen as a show endpoint.
					episode = episode,
				)
				countFilter = self._internalCount(items = items)

				# Change the returned structure for shows/seasons/episodes.
				items = self._structure(items, structure = structure, media = media)
				countStructure = self._internalCount(items = items)

				return self._internal(items = items, initial = countInitial, filter = countFilter, structure = countStructure, internal = internal, more = more)
		except: self._logError()
		return self._internal(items = items, internal = internal)

	# Feature, short, and special movies.
	def releaseMovie(self, niche = None, release = None, future = None, user = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, watch = None, company = None, studio = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, page = None, limit = None, sort = None, order = None, extended = None, duplicate = None, filter = None, cache = None, concurrency = None):
		return self.release(media = Media.Movie, niche = niche, release = release, future = future, user = user, query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, watch = watch, company = company, studio = studio, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, page = page, limit = limit, sort = sort, order = order, extended = extended, duplicate = duplicate, filter = filter, cache = cache, concurrency = concurrency)

	# Theater and television feature movies.
	def releaseFeature(self, niche = None, release = None, future = None, user = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, watch = None, company = None, studio = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, page = None, limit = None, sort = None, order = None, extended = None, duplicate = None, filter = None, cache = None, concurrency = None):
		return self.releaseMovie(niche = self._parameterNiche(niche = niche, extension = Media.Feature), release = release, future = future, user = user, query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, watch = watch, company = company, studio = studio, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, page = page, limit = limit, sort = sort, order = order, extended = extended, duplicate = duplicate, filter = filter, cache = cache, concurrency = concurrency)

	# Theater and television short films.
	def releaseShort(self, niche = None, release = None, future = None, user = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, watch = None, company = None, studio = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, page = None, limit = None, sort = None, order = None, extended = None, duplicate = None, filter = None, cache = None, concurrency = None):
		return self.releaseMovie(niche = self._parameterNiche(niche = niche, extension = Media.Short), release = release, future = future, user = user, query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, watch = watch, company = company, studio = studio, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, page = page, limit = limit, sort = sort, order = order, extended = extended, duplicate = duplicate, filter = filter, cache = cache, concurrency = concurrency)

	# Theater and television specials.
	def releaseSpecial(self, niche = None, release = None, future = None, user = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, watch = None, company = None, studio = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, page = None, limit = None, sort = None, order = None, extended = None, duplicate = None, filter = None, cache = None, concurrency = None):
		return self.releaseMovie(niche = self._parameterNiche(niche = niche, extension = Media.Special), release = release, future = future, user = user, query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, watch = watch, company = company, studio = studio, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, page = page, limit = limit, sort = sort, order = order, extended = extended, duplicate = duplicate, filter = filter, cache = cache, concurrency = concurrency)

	# Multi-season shows and single-season mini-series.
	def releaseShow(self, niche = None, release = None, future = None, user = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, watch = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, page = None, limit = None, sort = None, order = None, extended = None, duplicate = None, filter = None, structure = None, cache = None, concurrency = None):
		return self.release(media = Media.Show, release = release, future = future, user = user, query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, watch = watch, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, page = page, limit = limit, sort = sort, order = order, extended = extended, duplicate = duplicate, filter = filter, structure = structure, cache = cache, concurrency = concurrency)

	# Multi-season shows (will most likely include mini-series).
	def releaseMulti(self, niche = None, release = None, future = None, user = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, watch = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, page = None, limit = None, sort = None, order = None, extended = None, duplicate = None, filter = None, structure = None, cache = None, concurrency = None):
		return self.releaseShow(niche = self._parameterNiche(niche = niche, extension = Media.Multi), release = release, future = future, user = user, query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, watch = watch, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, page = page, limit = limit, sort = sort, order = order, extended = extended, duplicate = duplicate, filter = filter, structure = structure, cache = cache, concurrency = concurrency)

	# Single-season mini-series (does not work well).
	def releaseMini(self, niche = None, release = None, future = None, user = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, watch = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, page = None, limit = None, sort = None, order = None, extended = None, duplicate = None, filter = None, structure = None, cache = None, concurrency = None):
		return self.releaseShow(niche = self._parameterNiche(niche = niche, extension = Media.Mini), release = release, future = future, user = user, query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, watch = watch, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, page = page, limit = limit, sort = sort, order = order, extended = extended, duplicate = duplicate, filter = filter, structure = structure, cache = cache, concurrency = concurrency)

	# Show seasons.
	def releaseSeason(self, niche = None, release = None, future = None, user = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, watch = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, page = None, limit = None, sort = None, order = None, extended = None, duplicate = None, filter = None, structure = None, cache = None, concurrency = None):
		return self.release(media = Media.Season, niche = niche, release = release, future = future, user = user, query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, watch = watch, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, page = page, limit = limit, sort = sort, order = order, extended = extended, duplicate = duplicate, filter = filter, structure = structure, cache = cache, concurrency = concurrency)

	# Show episodes.
	def releaseEpisode(self, niche = None, release = None, future = None, user = None, query = None, keyword = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, watch = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, imdbRating = None, imdbVotes = None, tmdbRating = None, tmdbVotes = None, rtRating = None, rtMeter = None, mcRating = None, page = None, limit = None, sort = None, order = None, extended = None, duplicate = None, filter = None, structure = None, cache = None, concurrency = None):
		return self.release(media = Media.Episode, niche = niche, release = release, future = future, user = user, query = query, keyword = keyword, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, watch = watch, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, imdbRating = imdbRating, imdbVotes = imdbVotes, tmdbRating = tmdbRating, tmdbVotes = tmdbVotes, rtRating = rtRating, rtMeter = rtMeter, mcRating = mcRating, page = page, limit = limit, sort = sort, order = order, extended = extended, duplicate = duplicate, filter = filter, structure = structure, cache = cache, concurrency = concurrency)

	##############################################################################
	# RECOMMENDATION
	##############################################################################

	'''
		RECOMMENDATIONS BASED ON USER'S HISTORY

		NOTES:
			All filtering is done post-request.
				It migth therefore not be a good idea to use filters, otherwise few, or even no, results might be returend.
			No paging available.
				The maximum limit is 100.

		MEDIA:
			None:		Movie + Show (2 separate requests).
			True:		Movie + Show (2 separate requests).
			False:		Movie + Show (2 separate requests).
			String:		Single media from the list below.
			List:		Multiple medias from the list below (multiple separate requests).

			MOVIE
				FeatureTheater:		Level-0 support.
				FeatureTelevision:	Level-3 support.
				ShortTheater:		Level-3 support.
				ShortTelevision:	Level-3 support.
				SpecialTheater:		Level-3 support.
				SpecialTelevision:	Level-3 support.
			SERIE
				MediaMulti:			Level-0 support.
				MediaMini:			Level-3 support.
			TOPIC
				Anima:				Level-3 support.
				Anime:				Level-3 support.
				Donghua:			Level-3 support.
				Docu:				Level-3 support.
				Family:				Level-3 support.
				Music:				Level-3 support.
				Sport:				Level-3 support.
				Telly:				Level-3 support.
				Soap:				Level-3 support.
				Intrest:			Level-3 support.

		PARAMETERS:
			collection:		Included titles already collected by the user.
			watchlist:		Included titles already added to the watchlist by the user.
	'''

	def recommendation(self, media = None, niche = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, limit = None, sort = None, order = None, extended = None, filter = None, collection = None, watchlist = None, cache = None, internal = None, concurrency = None):
		try:
			support, media, medias, niche, _, _, year, duration, genre, language, country, certificate, status, _, studio, network, rating, votes, sort, order, filter, _, _, original = self._parameterFilter(media = media, niche = niche, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, sort = sort, order = order, filter = filter)
			if not support: return self._internal(internal = internal)

			if len(medias) > 1: # Request movies and shows together.
				items = self._execute(function = self.recommendation, iterator = [{'media' : i} for i in medias], niche = niche, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, studio = studio, network = network, rating = rating, votes = votes, limit = limit, sort = sort, order = order, extended = extended, filter = filter, cache = cache, concurrency = concurrency)
				countInitial = self._internalCount(items = items)

				items = self._filter(
					items = items,
					sort = sort, order = order,
					limit = limit,
				)
				countFilter = self._internalCount(items = items)
			else:
				if limit is None: limit = MetaTrakt.LimitRecommendation
				elif limit: limit = min(MetaTrakt.LimitRecommendation, limit)

				if collection is None: collection = False # Titles collected are probably ones that were already watched.
				if watchlist is None: watchlist = True # Titles on the watchlist are probably ones that were not watched yet.

				# Requires user authentication.
				user, id = self._parameterUser()

				items = self._retrieve(
					link = MetaTrakt.LinkRecommendation, cache = cache,
					media = media, medias = medias, niche = niche, user = user,
					page = False, limit = limit, extended = extended,
					collection = collection, watchlist = watchlist,
				)
				countInitial = self._internalCount(items = items)

				items = self._filter(
					media = media, niche = niche, items = items,
					sort = sort, order = order, filter = filter,
					year = year, duration = duration,
					genre = genre, language = language, country = country, certificate = certificate,
					status = status, studio = studio, network = network,
					rating = rating, votes = votes,
				)
				countFilter = self._internalCount(items = items)

			return self._internal(items = items, initial = countInitial, filter = countFilter, internal = internal)
		except: self._logError()
		return self._internal(internal = internal)

	# Feature, short, and special movies.
	def recommendationMovie(self, niche = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, limit = None, sort = None, order = None, extended = None, filter = None, collection = None, watchlist = None, cache = None, internal = None):
		return self.recommendation(media = Media.Movie, niche = niche, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, limit = limit, sort = sort, order = order, extended = extended, filter = filter, collection = collection, watchlist = watchlist, cache = cache, internal = internal)

	# Theater and television feature movies.
	def recommendationFeature(self, niche = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, limit = None, sort = None, order = None, extended = None, filter = None, collection = None, watchlist = None, cache = None, internal = None):
		return self.recommendationMovie(niche = self._parameterNiche(niche = niche, extension = Media.Feature), year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, limit = limit, sort = sort, order = order, extended = extended, filter = filter, collection = collection, watchlist = watchlist, cache = cache, internal = internal)

	# Theater and television short films (mostly returns nothing).
	def recommendationShort(self, niche = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, limit = None, sort = None, order = None, extended = None, filter = None, collection = None, watchlist = None, cache = None, internal = None):
		return self.recommendationMovie(niche = self._parameterNiche(niche = niche, extension = Media.Short), year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, limit = limit, sort = sort, order = order, extended = extended, filter = filter, collection = collection, watchlist = watchlist, cache = cache, internal = internal)

	# Theater and television specials (mostly returns nothing).
	def recommendationSpecial(self, niche = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, limit = None, sort = None, order = None, extended = None, filter = None, collection = None, watchlist = None, cache = None, internal = None):
		return self.recommendationMovie(niche = self._parameterNiche(niche = niche, extension = Media.Special), year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, limit = limit, sort = sort, order = order, extended = extended, filter = filter, collection = collection, watchlist = watchlist, cache = cache, internal = internal)

	# Multi-season shows and single-season mini-series.
	def recommendationShow(self, niche = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, limit = None, sort = None, order = None, extended = None, filter = None, collection = None, watchlist = None, cache = None, internal = None):
		return self.recommendation(media = Media.Show, niche = niche, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, limit = limit, sort = sort, order = order, extended = extended, filter = filter, collection = collection, watchlist = watchlist, cache = cache, internal = internal)

	# Multi-season shows (will most likely include mini-series).
	def recommendationMulti(self, niche = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, limit = None, sort = None, order = None, extended = None, filter = None, collection = None, watchlist = None, cache = None, internal = None):
		return self.recommendationShow(niche = self._parameterNiche(niche = niche, extension = Media.Multi), year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, limit = limit, sort = sort, order = order, extended = extended, filter = filter, collection = collection, watchlist = watchlist, cache = cache, internal = internal)

	# Single-season mini-series (does not work well).
	def recommendationMini(self, niche = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, limit = None, sort = None, order = None, extended = None, filter = None, collection = None, watchlist = None, cache = None, internal = None):
		return self.recommendationShow(niche = self._parameterNiche(niche = niche, extension = Media.Mini), year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, limit = limit, sort = sort, order = order, extended = extended, filter = filter, collection = collection, watchlist = watchlist, cache = cache, internal = internal)

	##############################################################################
	# LISTS
	##############################################################################

	'''
		LISTS OF LISTS
	'''

	def lists(self, list = None, user = None, id = None, page = None, limit = None, cache = None):
		try:
			link = None
			if list == MetaTrakt.ListPopular:
				link = MetaTrakt.LinkListPopular
			elif list == MetaTrakt.ListTrending:
				link = MetaTrakt.LinkListTrending
			else:
				if list == MetaTrakt.ListLike: link = MetaTrakt.LinkUserListsLike
				elif list == MetaTrakt.ListComment: link = MetaTrakt.LinkUserListsComment
				elif list == MetaTrakt.ListCollaboration: link = MetaTrakt.LinkUserListsCollaboration
				else: link = MetaTrakt.LinkUserLists
				user, id = self._parameterUser(user = user, id = id)

			if link:
				items = self._retrieve(
					link = link, media = Media.List, cache = cache,
					user = user, id = id,
					page = page, limit = limit,
				)
				return items
		except: self._logError()
		return None

	##############################################################################
	# LIST
	##############################################################################

	'''
		CUSTOM LISTS

		NOTES:
			Lists can be retrieved in one of three ways:
				1. Specify the user slug and the list slug/ID. https://api.trakt.tv/users/plexmetamanager/lists/netflix-movies/items/movie
				2. Specify the list slug. The authenticated Trakt account will be added as the user to 1. above.
				3. Specify the numerical list ID. The ID can found by opening the list on Trakt's website and then click the "Copy Link" button. https://trakt.tv/lists/23368695
			Lists do not support filtering through the API.
				All filtering is done post-request and the number of items returned might be less than the given limit.
				Paging is still possible.

		MEDIA:
			None:		Movie + Show
			True:		Movie + Show + Season + Episode + Person
			False:		Movie + Show + Season + Person
			String:		Single media from the list below.
			List:		Multiple medias from the list below.

			MOVIE
				FeatureTheater:		Level-0 support.
				FeatureTelevision:	Level-3 support.
				ShortTheater:		Level-3 support.
				ShortTelevision:	Level-3 support.
				SpecialTheater:		Level-3 support.
				SpecialTelevision:	Level-3 support.
			SERIE
				Multi:				Level-0 support.
				Mini:				Level-4 support.
				Season:				Level-0 support.
				Episode:			Level-0 support.
			ENTITY
				Person:				Level-0 support.
			TOPIC
				Anima:				Level-3 support.
				Anime:				Level-3 support.
				Donghua:			Level-3 support.
				Docu:				Level-3 support.
				Family:				Level-3 support.
				Music:				Level-3 support.
				Sport:				Level-3 support.
				Telly:				Level-3 support.
				Soap:				Level-3 support.
				Intrest:			Level-3 support.

		PARAMETERS:
			sort:			Sorting is only applied post-request to a single page.
				True:		Sort the list according to the headers sent by Trakt (the sorting options set by the user in the list's settings on Trakt's website).
				String:		Sort by a specific attribute.
	'''

	def list(self, media = None, niche = None, user = None, id = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		try:
			if media is None: media = [Media.Movie, Media.Show]
			elif media is True: media = [Media.Movie, Media.Show, Media.Season, Media.Episode, Media.Person]
			elif media is False: media = [Media.Movie, Media.Show, Media.Season, Media.Episode]

			if filter is None: filter = False
			support, media, medias, niche, query, _, year, duration, genre, language, country, certificate, status, episode, studio, network, rating, votes, sort, order, filter, _, _, original = self._parameterFilter(media = media, niche = niche, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, sort = sort, order = order, filter = filter)
			if not support: return self._internal(internal = internal)
			user, id = self._parameterUser(user = user, id = id)

			if sort is None: sort = True # Trigger sorting using the Trakt headers.

			items, sorted, _ = self._retrieve(
				link = MetaTrakt.LinkUserListItem if user else MetaTrakt.LinkListItem, cache = cache,
				media = media, medias = medias, niche = niche,
				user = user, id = id,
				page = page, limit = limit, extended = extended,
				sort = sort, detail = True,
			)
			countInitial = self._internalCount(items = items)
			if sorted:  # Already sorted according to Trakt headers. Do not sort again with default sort options.
				sort = False
				order = False

			# In case multiple medias are specified that cannot be filtered through the API.
			items = self._filter(
				media = media, niche = niche, items = items,
				sort = None if sort is True else sort, order = order, filter = filter,
				year = year, duration = duration,
				genre = genre, language = language, country = country, certificate = certificate,
				status = status, episode = episode, studio = studio, network = network,
				rating = rating, votes = votes,
				duplicate = duplicate,
			)
			countFilter = self._internalCount(items = items)

			# Change the returned structure for shows/seasons/episodes.
			items = self._structure(items, structure = structure, media = media)
			countStructure = self._internalCount(items = items)

			return self._internal(items = items, initial = countInitial, filter = countFilter, structure = countStructure, internal = internal)
		except: self._logError()
		return self._internal(internal = internal)

	# Feature, short, and special movies.
	def listMovie(self, niche = None, user = None, id = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.list(media = Media.Movie, niche = niche, user = user, id = id, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television feature movies.
	def listFeature(self, niche = None, user = None, id = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listMovie(niche = self._parameterNiche(niche = niche, extension = Media.Feature), user = user, id = id, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television short films (mostly returns nothing).
	def listShort(self, niche = None, user = None, id = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listMovie(niche = self._parameterNiche(niche = niche, extension = Media.Short), user = user, id = id, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television specials (mostly returns nothing).
	def listSpecial(self, niche = None, user = None, id = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listMovie(niche = self._parameterNiche(niche = niche, extension = Media.Special), user = user, id = id, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Multi-season shows and single-season mini-series.
	def listShow(self, niche = None, user = None, id = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		return self.list(media = Media.Show, niche = niche, user = user, id = id, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)

	# Multi-season shows (will most likely include mini-series).
	def listMulti(self, niche = None, user = None, id = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		return self.listShow(niche = self._parameterNiche(niche = niche, extension = Media.Multi), user = user, id = id, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)

	# Single-season mini-series (does not work well).
	def listMini(self, niche = None, user = None, id = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		return self.listShow(niche = self._parameterNiche(niche = niche, extension = Media.Mini), user = user, id = id, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)

	# Show seasons.
	def listSeason(self, niche = None, user = None, id = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		return self.list(media = Media.Season, niche = niche, user = user, id = id, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)

	# Show episodes.
	def listEpisode(self, niche = None, user = None, id = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		return self.list(media = Media.Episode, niche = niche, user = user, id = id, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)

	# People.
	def listPerson(self, user = None, id = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		return self.list(media = Media.Person, user = user, id = id, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)

	##############################################################################
	# LIST - USER
	##############################################################################

	'''
		USER LISTS

		NOTES:
			This function should not be called directly.
				Use one of the other functions below instead.
			Lists do not support filtering through the API.
				All filtering is done post-request and the number of items returned might be less than the given limit.
				Paging is still possible.

		MEDIA:
			None:		Movie + Show.
			True:		Movie + Show + Season + Episode + Person.
			False:		Movie + Show + Season + Episode.
			String:		Single media from the list below.
			List:		Multiple medias from the list below.

			MOVIE
				FeatureTheater:		Level-0 support.
				FeatureTelevision:	Level-3 support.
				ShortTheater:		Level-3 support.
				ShortTelevision:	Level-3 support.
				SpecialTheater:		Level-3 support.
				SpecialTelevision:	Level-3 support.
			SERIE
				Multi:				Level-0 support.
				Mini:				Level-4 support.
				Season:				Level-0 support.
				Episode:			Level-0 support.
			ENTITY
				Person:				Level-0 support.
			TOPIC
				Anima:				Level-3 support.
				Anime:				Level-3 support.
				Donghua:			Level-3 support.
				Docu:				Level-3 support.
				Family:				Level-3 support.
				Music:				Level-3 support.
				Sport:				Level-3 support.
				Telly:				Level-3 support.
				Soap:				Level-3 support.
				Intrest:			Level-3 support.

		PARAMETERS:
			sort:			Sorting is only applied post-request to a single page.
				True:		Sort the list according to the headers sent by Trakt (the sorting options set by the user in the list's settings on Trakt's website).
				String:		Sort by a specific attribute.
	'''

	def listUser(self, link, media = None, niche = None, support = None, category = None, user = None, action = None, section = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		try:
			if media is None: media = [Media.Movie, Media.Show]
			elif media is True: media = [Media.Movie, Media.Show, Media.Season, Media.Episode, Media.Person]
			elif media is False: media = [Media.Movie, Media.Show, Media.Season, Media.Episode]

			if filter is None: filter = False
			supported, media, medias, niche, query, _, year, duration, genre, language, country, certificate, status, episode, studio, network, rating, votes, sort, order, filter, _, _, original = self._parameterFilter(media = media, niche = niche, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, sort = sort, order = order, filter = filter)
			if not supported: return self._internal(internal = internal)
			user, _ = self._parameterUser(user = user)

			if support:
				if Tools.isArray(medias):
					for i in medias:
						if not i in support: return self._internal(internal = internal)
				elif not media == '': # Allow empty media string from history.
					found = False
					if not media in support: return self._internal(internal = internal)

			if media is None: media = '' # If no category is added, all media is returned.
			if media is None or not sort: sort = '' # Sort only works if the media/category was provided.

			items, sorted, _ = self._retrieve(
				link = link, cache = cache,
				media = media, medias = medias, niche = niche, category = category,
				user = user, section = section, date = date,
				rating = rating,
				page = page, limit = limit, extended = extended,
				sort = sort, detail = True,
			)
			countInitial = self._internalCount(items = items)
			if sorted:  # Already sorted according to Trakt headers. Do not sort again with default sort options.
				sort = False
				order = False

			# Do not filter if the rating is in the link (eg: LinkUserRating).
			if '{rating}' in link: rating = None

			# In case multiple medias are specified that cannot be filtered through the API.
			items = self._filter(
				media = media, niche = niche, items = items,
				sort = None if sort is True else sort, order = order, filter = filter,
				year = year, duration = duration,
				genre = genre, language = language, country = country, certificate = certificate,
				status = status, episode = episode, studio = studio, network = network,
				rating = rating, votes = votes,
				action = action, duplicate = duplicate,
			)
			countFilter = self._internalCount(items = items)

			# Change the returned structure for shows/seasons/episodes.
			items = self._structure(items, structure = structure, media = media)
			countStructure = self._internalCount(items = items)

			return self._internal(items = items, initial = countInitial, filter = countFilter, structure = countStructure, internal = internal)
		except: self._logError()
		return self._internal(internal = internal)

	##############################################################################
	# LIST - WATCH
	##############################################################################

	'''
		USER WATCHLIST

		NOTES:
			Pre-request filtering through the API is not supported.
				All filtering is done post-request and the number of items returned might be less than the given limit.
				Paging is still possible.

		MEDIA:
			None:		Movie + Show.
			True:		Movie + Show + Season + Episode.
			False:		Movie + Show + Season.
			String:		Single media from the list below.
			List:		Multiple medias from the list below.

			MOVIE
				FeatureTheater:		Level-0 support.
				FeatureTelevision:	Level-3 support.
				ShortTheater:		Level-3 support.
				ShortTelevision:	Level-3 support.
				SpecialTheater:		Level-3 support.
				SpecialTelevision:	Level-3 support.
			SERIE
				Multi:				Level-0 support.
				Mini:				Level-4 support.
				Season:				Level-0 support.
				Episode:			Level-0 support.
			ENTITY
				Person:				Level-0 support.
			TOPIC
				Anima:				Level-3 support.
				Anime:				Level-3 support.
				Donghua:			Level-3 support.
				Docu:				Level-3 support.
				Family:				Level-3 support.
				Music:				Level-3 support.
				Sport:				Level-3 support.
				Telly:				Level-3 support.
				Soap:				Level-3 support.
				Intrest:			Level-3 support.

		PARAMETERS:
			sort:
				True:		Sort the list post-request according to the headers sent by Trakt (the sorting options set by the user in the list's settings on Trakt's website).
				String:		SortRank/SortAdded/SortReleased/SortTitle for pre-request sorting. Otherwise post-request sorting according to a specific attribute.
	'''

	def listWatch(self, media = None, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		support = [Media.Movie, Media.Show, Media.Season, Media.Episode]

		if media is None: media = [Media.Movie, Media.Show]
		elif media is True: media = [Media.Movie, Media.Show, Media.Season, Media.Episode]
		elif media is False: media = [Media.Movie, Media.Show, Media.Season]

		# This list is already sorted from most recently rated to last rated.
		if not sort:
			sort = MetaTools.SortAdded
			if not order: order = MetaTools.OrderDescending

		return self.listUser(link = MetaTrakt.LinkUserWatchlist, support = support, media = media, niche = niche, user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)

	# Feature, short, and special movies.
	def listWatchMovie(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listWatch(media = Media.Movie, niche = niche, user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television feature movies.
	def listWatchFeature(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listWatchMovie(niche = self._parameterNiche(niche = niche, extension = Media.Feature), user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television short films (mostly returns nothing).
	def listWatchShort(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listWatchMovie(niche = self._parameterNiche(niche = niche, extension = Media.Short), user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television specials (mostly returns nothing).
	def listWatchSpecial(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listWatchMovie(niche = self._parameterNiche(niche = niche, extension = Media.Special), user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Multi-season shows and single-season mini-series.
	def listWatchShow(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		return self.listWatch(media = Media.Show, niche = niche, user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)

	# Multi-season shows (will most likely include mini-series).
	def listWatchMulti(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		return self.listWatchShow(niche = self._parameterNiche(niche = niche, extension = Media.Multi), user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)

	# Single-season mini-series (does not work well).
	def listWatchMini(self, niche = None, user = None, id = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		return self.listWatchShow(niche = self._parameterNiche(niche = niche, extension = Media.Mini), user = user, id = id, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)

	# Show seasons.
	def listWatchSeason(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		return self.listWatch(media = Media.Season, niche = niche, user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)

	# Show episodes.
	def listWatchEpisode(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		return self.listWatch(media = Media.Episode, niche = niche, user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)

	##############################################################################
	# LIST - FAVORITE
	##############################################################################

	'''
		USER FAVORITES

		NOTES:
			Pre-request filtering through the API is not supported.
				All filtering is done post-request and the number of items returned might be less than the given limit.
				Paging is still possible.

		MEDIA:
			None:		Movie + Show.
			True:		Movie + Show.
			False:		Movie + Show.
			String:		Single media from the list below.
			List:		Multiple medias from the list below.

			MOVIE
				FeatureTheater:		Level-0 support.
				FeatureTelevision:	Level-3 support.
				ShortTheater:		Level-3 support.
				ShortTelevision:	Level-3 support.
				SpecialTheater:		Level-3 support.
				SpecialTelevision:	Level-3 support.
			SERIE
				Multi:				Level-0 support.
				Mini:				Level-4 support.
			TOPIC
				Anima:				Level-3 support.
				Anime:				Level-3 support.
				Donghua:			Level-3 support.
				Docu:				Level-3 support.
				Family:				Level-3 support.
				Music:				Level-3 support.
				Sport:				Level-3 support.
				Telly:				Level-3 support.
				Soap:				Level-3 support.
				Intrest:			Level-3 support.

		PARAMETERS:
			sort:
				True:		Sort the list post-request according to the headers sent by Trakt (the sorting options set by the user in the list's settings on Trakt's website).
				String:		SortRank/SortAdded/SortReleased/SortTitle for pre-request sorting. Otherwise post-request sorting according to a specific attribute.
	'''

	def listFavorite(self, media = None, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		support = [Media.Movie, Media.Show]

		if not media or media is True: media = [Media.Movie, Media.Show]

		# This list is already sorted from most recently rated to last rated.
		if not sort:
			sort = MetaTools.SortAdded
			if not order: order = MetaTools.OrderDescending

		return self.listUser(link = MetaTrakt.LinkUserFavorite, support = support, media = media, niche = niche, user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Feature, short, and special movies.
	def listFavoriteMovie(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listFavorite(media = Media.Movie, niche = niche, user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television feature movies.
	def listFavoriteFeature(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listFavoriteMovie(niche = self._parameterNiche(niche = niche, extension = Media.Feature), user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television short films (mostly returns nothing).
	def listFavoriteShort(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listFavoriteMovie(niche = self._parameterNiche(niche = niche, extension = Media.Short), user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television specials (mostly returns nothing).
	def listFavoriteSpecial(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listFavoriteMovie(niche = self._parameterNiche(niche = niche, extension = Media.Special), user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Multi-season shows and single-season mini-series.
	def listFavoriteShow(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listFavorite(media = Media.Show, niche = niche, user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Multi-season shows (will most likely include mini-series).
	def listFavoriteMulti(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listFavoriteShow(niche = self._parameterNiche(niche = niche, extension = Media.Multi), user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Single-season mini-series (does not work well).
	def listFavoriteMini(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listFavoriteShow(niche = self._parameterNiche(niche = niche, extension = Media.Mini), user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	##############################################################################
	# LIST - RATING
	##############################################################################

	'''
		USER RATINGS

		NOTES:
			Pre-request filtering through the API is not supported.
				All filtering is done post-request and the number of items returned might be less than the given limit.
				Paging is still possible.

		MEDIA:
			None:		Movie + Show + Season + Episode.
			True:		Movie + Show.
			False:		Movie + Show.
			String:		Single media from the list below.
			List:		Multiple medias from the list below.

			MOVIE
				FeatureTheater:		Level-0 support.
				FeatureTelevision:	Level-3 support.
				ShortTheater:		Level-3 support.
				ShortTelevision:	Level-3 support.
				SpecialTheater:		Level-3 support.
				SpecialTelevision:	Level-3 support.
			SERIE
				Multi:				Level-0 support.
				Mini:				Level-4 support.
				Season:				Level-0 support.
				Episode:			Level-0 support.
			TOPIC
				Anima:				Level-3 support.
				Anime:				Level-3 support.
				Donghua:			Level-3 support.
				Docu:				Level-3 support.
				Family:				Level-3 support.
				Music:				Level-3 support.
				Sport:				Level-3 support.
				Telly:				Level-3 support.
				Soap:				Level-3 support.
				Intrest:			Level-3 support.

		PARAMETERS:
			rating:
				Integer:	Titles with the exact rating.
				List:		All titles are retrieved and then filtered post-request.
	'''

	def listRating(self, media = None, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		try:
			support = [Media.Movie, Media.Show, Media.Season, Media.Episode]

			category = None
			if not media or media is True:
				media = None
				category = MetaTrakt.CategoryAll
			elif Tools.isArray(media):
				if len(media) == 1:
					media = media[0]
				else:
					media = None
					category = MetaTrakt.CategoryAll

			if Tools.isNumber(rating) and int(rating) == rating: rating = int(rating)
			else: rating = ''

			# This list is already sorted from most recently rated to last rated.
			if not sort:
				sort = MetaTools.SortRated
				if not order: order = MetaTools.OrderDescending

			return self.listUser(link = MetaTrakt.LinkUserRating, support = support, media = media, niche = niche, category = category, user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)
		except: self._logError()
		return self._internal(internal = internal)

	# Feature, short, and special movies.
	def listRatingMovie(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listRating(media = Media.Movie, niche = niche, user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television feature movies.
	def listRatingFeature(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listRatingMovie(niche = self._parameterNiche(niche = niche, extension = Media.Feature), user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television short films (mostly returns nothing).
	def listRatingShort(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listRatingMovie(niche = self._parameterNiche(niche = niche, extension = Media.Short), user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television specials (mostly returns nothing).
	def listRatingSpecial(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listRatingMovie(niche = self._parameterNiche(niche = niche, extension = Media.Special), user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Multi-season shows and single-season mini-series.
	def listRatingShow(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listRating(media = Media.Show, niche = niche, user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Multi-season shows (will most likely include mini-series).
	def listRatingMulti(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listRatingShow(niche = self._parameterNiche(niche = niche, extension = Media.Multi), user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Single-season mini-series (does not work well).
	def listRatingMini(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listRatingShow(niche = self._parameterNiche(niche = niche, extension = Media.Mini), user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Shows seasons.
	def listRatingSeason(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		return self.listRating(media = Media.Season, niche = niche, user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)

	# Shows episodes.
	def listRatingEpisode(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		return self.listRating(media = Media.Episode, niche = niche, user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)

	##############################################################################
	# LIST - COLLECTION
	##############################################################################

	'''
		USER COLLECTION

		NOTES:
			Collected items work similar to the watched history.
				Only movies and episodes are collected.
				If a show or season is collected, it actually collects the individual episodes.
			Pre-request filtering through the API is not supported.
				All filtering is done post-request and the number of items returned might be less than the given limit.
			Paging and limiting is not supported.
				All titles are returned at once.

		MEDIA:
			None:		Movie + Show.
			True:		Movie + Show + Season + Episode.
			False:		Movie + Show.
			String:		Single media from the list below.
			List:		Multiple medias from the list below.

			MOVIE
				FeatureTheater:		Level-0 support.
				FeatureTelevision:	Level-3 support.
				ShortTheater:		Level-3 support.
				ShortTelevision:	Level-3 support.
				SpecialTheater:		Level-3 support.
				SpecialTelevision:	Level-3 support.
			SERIE
				Multi:				Level-0 support.
				Mini:				Level-4 support.
				Season:				Level-1 support.
				Episode:			Level-1 support.
			TOPIC
				Anima:				Level-3 support.
				Anime:				Level-3 support.
				Donghua:			Level-3 support.
				Docu:				Level-3 support.
				Family:				Level-3 support.
				Music:				Level-3 support.
				Sport:				Level-3 support.
				Telly:				Level-3 support.
				Soap:				Level-3 support.
				Intrest:			Level-3 support.

		PARAMETERS:
			rating:
				Integer:	Titles with the exact rating.
				List:		All titles are retrieved and then filtered post-request.
	'''

	def listCollection(self, media = None, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None, concurrency = None):
		try:
			support = [Media.Movie, Media.Show, Media.Season, Media.Episode]

			if not media: media = [Media.Movie, Media.Show]
			elif media is True: media = [Media.Movie, Media.Show, Media.Season, Media.Episode]

			# The items are returned from earliest to latest watched.
			# Reverse it to list recently watched items first.
			if not sort:
				sort = MetaTools.SortCollected
				if not order: order = MetaTools.OrderDescending

			if Tools.isArray(media):
				# Technically we can retrieve shows/seasons/episodes in one request, since seasons and episodes are nested objects in the show.
				# But this would complicate the code logic too much (making a single request and processing it in differnt ways).
				# So just make multiple requests if we want to retrieve shows/seasons/episodes in one request.
				return self._execute(function = self.listCollection, iterator = [{'media' : i} for i in media], niche = niche, user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal, concurrency = concurrency)
			else:
				# Manually specify the category, since we still need the media for extracting and filtering.
				# Eg: For episodes, the media is Episode, but the category is CategoryShow.
				category = None
				if media:
					if Media.isMovie(media): category = MetaTrakt.CategoryMovie
					elif Media.isSerie(media): category = MetaTrakt.CategoryShow

				return self.listUser(link = MetaTrakt.LinkUserCollection, support = support, media = media, niche = niche, category = category, user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)
		except: self._logError()
		return self._internal(internal = internal)

	# Feature, short, and special movies.
	def listCollectionMovie(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listCollection(media = Media.Movie, niche = niche, user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television feature movies.
	def listCollectionFeature(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listCollectionMovie(niche = self._parameterNiche(niche = niche, extension = Media.Feature), user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television short films (mostly returns nothing).
	def listCollectionShort(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listCollectionMovie(niche = self._parameterNiche(niche = niche, extension = Media.Short), user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television specials (mostly returns nothing).
	def listCollectionSpecial(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listCollectionMovie(niche = self._parameterNiche(niche = niche, extension = Media.Special), user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Multi-season shows and single-season mini-series.
	def listCollectionShow(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listCollection(media = Media.Show, niche = niche, user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Multi-season shows (will most likely include mini-series).
	def listCollectionMulti(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listCollectionShow(niche = self._parameterNiche(niche = niche, extension = Media.Multi), user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Single-season mini-series (does not work well).
	def listCollectionMini(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listCollectionShow(niche = self._parameterNiche(niche = niche, extension = Media.Mini), user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Shows seasons.
	def listCollectionSeason(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		return self.listCollection(media = Media.Season, niche = niche, user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)

	# Shows episodes.
	def listCollectionEpisode(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		return self.listCollection(media = Media.Episode, niche = niche, user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)

	##############################################################################
	# LIST - WATCHED
	##############################################################################

	'''
		USER WATCHED

		NOTES:
			Pre-request filtering through the API is not supported.
				All filtering is done post-request and the number of items returned might be less than the given limit.
			Paging and limiting is not supported.
				All titles are returned at once.

		MEDIA:
			None:		Movie + Show.
			True:		Movie + Show + Season + Episode.
			False:		Movie + Show.
			String:		Single media from the list below.
			List:		Multiple medias from the list below.

			MOVIE
				FeatureTheater:		Level-0 support.
				FeatureTelevision:	Level-3 support.
				ShortTheater:		Level-3 support.
				ShortTelevision:	Level-3 support.
				SpecialTheater:		Level-3 support.
				SpecialTelevision:	Level-3 support.
			SERIE
				Multi:				Level-0 support.
				Mini:				Level-4 support.
				Season:				Level-1 support.
				Episode:			Level-1 support.
			TOPIC
				Anima:				Level-3 support.
				Anime:				Level-3 support.
				Donghua:			Level-3 support.
				Docu:				Level-3 support.
				Family:				Level-3 support.
				Music:				Level-3 support.
				Sport:				Level-3 support.
				Telly:				Level-3 support.
				Soap:				Level-3 support.
				Intrest:			Level-3 support.
	'''

	def listWatched(self, media = None, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None, concurrency = None):
		try:
			support = [Media.Movie, Media.Show, Media.Season, Media.Episode]

			if not media: media = [Media.Movie, Media.Show]
			elif media is True: media = [Media.Movie, Media.Show, Media.Season, Media.Episode]

			# The items are returned from earliest to latest watched.
			# Reverse it to list recently watched items first.
			if not sort:
				sort = MetaTools.SortWatched
				if not order: order = MetaTools.OrderDescending

			if Tools.isArray(media):
				# Technically we can retrieve shows/seasons/episodes in one request, since seasons and episodes are nested objects in the show.
				# But this would complicate the code logic too much (making a single request and processing it in differnt ways).
				# So just make multiple requests if we want to retrieve shows/seasons/episodes in one request.
				return self._execute(function = self.listWatched, iterator = [{'media' : i} for i in media], niche = niche, user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal, concurrency = concurrency)
			else:
				# Manually specify the category, since we still need the media for extracting and filtering.
				# Eg: For episodes, the media is MediaEpisode, but the category is CategoryShow.
				category = None
				if media:
					if Media.isMovie(media): category = MetaTrakt.CategoryMovie
					elif Media.isSerie(media): category = MetaTrakt.CategoryShow

				return self.listUser(link = MetaTrakt.LinkUserWatched, support = support, media = media, niche = niche, category = category, user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)
		except: self._logError()
		return self._internal(internal = internal)

	# Feature, short, and special movies.
	def listWatchedMovie(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listWatched(media = Media.Movie, niche = niche, ser = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television feature movies.
	def listWatchedFeature(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listWatchedMovie(niche = self._parameterNiche(niche = niche, extension = Media.Feature), user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television short films (mostly returns nothing).
	def listWatchedShort(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listWatchedMovie(niche = self._parameterNiche(niche = niche, extension = Media.Short), user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television specials (mostly returns nothing).
	def listWatchedSpecial(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listWatchedMovie(niche = self._parameterNiche(niche = niche, extension = Media.Special), user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Multi-season shows and single-season mini-series.
	def listWatchedShow(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listWatched(media = Media.Show, niche = niche, user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Multi-season shows (will most likely include mini-series).
	def listWatchedMulti(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listWatchedShow(niche = self._parameterNiche(niche = niche, extension = Media.Multi), user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Single-season mini-series (does not work well).
	def listWatchedMini(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listWatchedShow(niche = self._parameterNiche(niche = niche, extension = Media.Mini), user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Shows seasons.
	def listWatchedSeason(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		return self.listWatched(media = Media.Season, niche = niche, user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)

	# Shows episodes.
	def listWatchedEpisode(self, niche = None, user = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		return self.listWatched(media = Media.Episode, niche = niche, user = user, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)

	##############################################################################
	# LIST - HISTORY
	##############################################################################

	'''
		USER HISTORY

		NOTES:
			This endpoint is similar to the Watched endpoint. However, the following differs:
				1. This endpoint supports paging.
				2. This endpoints support retrieving seasons and episodes, not only movies and shows.
				3. This endpoint allows for a date range.
				4. This endpoint not only contains watched titles, but also checkins and scrobbles.
			Pre-request filtering through the API is not supported.
				All filtering is done post-request and the number of items returned might be less than the given limit.
			Although shows and seasons are mentioned in the docs, it seems only episodes can be returned.

		MEDIA:
			None:		Movie + Show.
			True:		Movie + Show + Season + Episode.
			False:		Movie + Show.
			String:		Single media from the list below.
			List:		Multiple medias from the list below.

			MOVIE
				FeatureTheater:		Level-0 support.
				FeatureTelevision:	Level-3 support.
				ShortTheater:		Level-3 support.
				ShortTelevision:	Level-3 support.
				SpecialTheater:		Level-3 support.
				SpecialTelevision:	Level-3 support.
			SERIE
				Multi:				Level-1 support.
				Mini:				Level-4 support.
				Season:				Level-1 support.
				Episode:			Level-0 support.
			TOPIC
				Anima:				Level-3 support.
				Anime:				Level-3 support.
				Donghua:			Level-3 support.
				Docu:				Level-3 support.
				Family:				Level-3 support.
				Music:				Level-3 support.
				Sport:				Level-3 support.
				Telly:				Level-3 support.
				Soap:				Level-3 support.
				Intrest:			Level-3 support.

		PARAMETERS:
			action:			The action that made the title end up in the user's history.
				None:		All actions.
				String:		Single action. ActionScrobble/ActionCheckin/ActionWatch.
				List:		Multiple actions.
			date:			The date range to retrieve the history for.
				None:		Retrieve the full history.
				List:		A date or timestamp range to only retrieve a subset of the user's history.
	'''

	def listHistory(self, media = None, niche = None, user = None, action = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		try:
			support = [Media.Movie, Media.Show, Media.Season, Media.Episode]

			if not media: media = [Media.Movie, Media.Show]
			elif media is True: media = [Media.Movie, Media.Show, Media.Season, Media.Episode]

			category = None
			if media is None or Tools.isArray(media):
				media = None
				category = '' # If no category is added, all media is returned.
			elif media:
				if Media.isMovie(media):
					category = MetaTrakt.CategoryMovie
				elif Media.isSerie(media):
					# Although shows and seasons are mentioned in the docs, it seems only episodes can be returned.
					if not structure: structure = media
					category = MetaTrakt.CategoryShow
					media = Media.Episode

			# This list is already sorted from most recently watched to last watched.
			if not sort:
				sort = MetaTools.SortWatched
				if not order: order = MetaTools.OrderDescending

			return self.listUser(link = MetaTrakt.LinkUserHistory, support = support, media = media, niche = niche, category = category, user = user, action = action, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)
		except: self._logError()
		return self._internal(internal = internal)

	# Feature, short, and special movies.
	def listHistoryMovie(self, niche = None, user = None, action = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listHistory(media = Media.Movie, niche = niche, user = user, action = action, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television feature movies.
	def listHistoryFeature(self, niche = None, user = None, action = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listHistoryMovie(niche = self._parameterNiche(niche = niche, extension = Media.Feature), user = user, action = action, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television short films (mostly returns nothing).
	def listHistoryShort(self, niche = None, user = None, action = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listHistoryMovie(niche = self._parameterNiche(niche = niche, extension = Media.Short), user = user, action = action, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television specials (mostly returns nothing).
	def listHistorySpecial(self, niche = None, user = None, action = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listHistoryMovie(niche = self._parameterNiche(niche = niche, extension = Media.Special), user = user, action = action, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Multi-season shows and single-season mini-series.
	def listHistoryShow(self, niche = None, user = None, action = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listHistory(media = Media.Show, niche = niche, user = user, action = action, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Multi-season shows (will most likely include mini-series).
	def listHistoryMulti(self, niche = None, user = None, action = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listHistoryShow(niche = self._parameterNiche(niche = niche, extension = Media.Multi), user = user, action = action, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Single-season mini-series (does not work well).
	def listHistoryMini(self, niche = None, user = None, action = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listHistoryShow(niche = self._parameterNiche(niche = niche, extension = Media.Mini), user = user, action = action, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Shows seasons.
	def listHistorySeason(self, niche = None, user = None, action = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		return self.listHistory(media = Media.Season, niche = niche, user = user, action = action, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)

	# Shows episodes.
	def listHistoryEpisode(self, niche = None, user = None, action = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		return self.listHistory(media = Media.Episode, niche = niche, user = user, action = action, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)

	##############################################################################
	# LIST - PROGRESS
	##############################################################################

	'''
		USER PROGRESS

		NOTES:
			Pre-request filtering through the API is not supported.
				All filtering is done post-request and the number of items returned might be less than the given limit.
				Paging is still possible.

		MEDIA:
			None:		Movie + Episode.
			True:		Movie + Episode.
			False:		Movie + Episode.
			String:		Single media from the list below.
			List:		Multiple medias from the list below.

			MOVIE
				FeatureTheater:		Level-0 support.
				FeatureTelevision:	Level-3 support.
				ShortTheater:		Level-3 support.
				ShortTelevision:	Level-3 support.
				SpecialTheater:		Level-3 support.
				SpecialTelevision:	Level-3 support.
			SERIE
				Multi:				Level-4 support.
				Mini:				Level-4 support.
				Season:				Level-4 support.
				Episode:			Level-0 support.
			TOPIC
				Anima:				Level-3 support.
				Anime:				Level-3 support.
				Donghua:			Level-3 support.
				Docu:				Level-3 support.
				Family:				Level-3 support.
				Music:				Level-3 support.
				Sport:				Level-3 support.
				Telly:				Level-3 support.
				Soap:				Level-3 support.
				Intrest:			Level-3 support.

		PARAMETERS:
			date:			The date range to retrieve the progress for.
				None:		Retrieve the full progress.
				List:		A date or timestamp range to only retrieve a subset of the user's progress.

	'''

	def listProgress(self, media = None, niche = None, user = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		try:
			support = [Media.Movie, Media.Episode]

			if not media: media = [Media.Movie, Media.Episode]
			elif media is True: media = [Media.Movie, Media.Episode]

			category = None
			if media is None or Tools.isArray(media):
				media = None
				category = '' # If no category is added, all media is returned.
			elif media:
				if Media.isMovie(media):
					category = MetaTrakt.CategoryMovie
				elif Media.isSerie(media):
					if not structure: structure = media
					category = MetaTrakt.CategoryEpisode
					media = Media.Episode

			return self.listUser(link = MetaTrakt.LinkUserProgress, support = support, media = media, niche = niche, category = category, user = user, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)
		except: self._logError()
		return self._internal(internal = internal)

	# Feature, short, and special movies.
	def listProgressMovie(self, niche = None, user = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listProgress(media = Media.Movie, niche = niche, user = user, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television feature movies.
	def listProgressFeature(self, niche = None, user = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listProgressMovie(niche = self._parameterNiche(niche = niche, extension = Media.Feature), user = user, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television short films (mostly returns nothing).
	def listProgressShort(self, niche = None, user = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listProgressMovie(niche = self._parameterNiche(niche = niche, extension = Media.Short), user = user, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television specials (mostly returns nothing).
	def listProgressSpecial(self, niche = None, user = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listProgressMovie(niche = self._parameterNiche(niche = niche, extension = Media.Special), user = user, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Multi-season shows and single-season mini-series.
	def listProgressShow(self, niche = None, user = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listProgress(media = Media.Show, niche = niche, user = user, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Multi-season shows (will most likely include mini-series).
	def listProgressMulti(self, niche = None, user = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listProgressShow(niche = self._parameterNiche(niche = niche, extension = Media.Multi), user = user, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Single-season mini-series (does not work well).
	def listProgressMini(self, niche = None, user = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listProgressShow(niche = self._parameterNiche(niche = niche, extension = Media.Mini), user = user, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Shows seasons.
	def listProgressSeason(self, niche = None, user = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		return self.listProgress(media = Media.Season, niche = niche, user = user, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)

	# Shows episodes.
	def listProgressEpisode(self, niche = None, user = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		return self.listProgress(media = Media.Episode, niche = niche, user = user, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)

	##############################################################################
	# LIST - HIDDEN
	##############################################################################

	'''
		USER HIDDEN

		NOTES:
			Pre-request filtering through the API is not supported.
				All filtering is done post-request and the number of items returned might be less than the given limit.
				Paging is still possible.

		MEDIA:
			None:		Movie + Show + Episode.
			True:		Movie + Show + Episode.
			False:		Movie + Show.
			String:		Single media from the list below.
			List:		Multiple medias from the list below.

			MOVIE
				FeatureTheater:		Level-0 support.
				FeatureTelevision:	Level-3 support.
				ShortTheater:		Level-3 support.
				ShortTelevision:	Level-3 support.
				SpecialTheater:		Level-3 support.
				SpecialTelevision:	Level-3 support.
			SERIE
				Multi:				Level-0 support.
				Mini:				Level-4 support.
				Season:				Level-4 support.
				Episode:			Level-0 support.
			TOPIC
				Anima:				Level-3 support.
				Anime:				Level-3 support.
				Donghua:			Level-3 support.
				Docu:				Level-3 support.
				Family:				Level-3 support.
				Music:				Level-3 support.
				Sport:				Level-3 support.
				Telly:				Level-3 support.
				Soap:				Level-3 support.
				Intrest:			Level-3 support.

		PARAMETERS:
			section:			The section the hidden items were added for.

	'''

	def listHidden(self, media = None, niche = None, section = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		try:
			support = [Media.Movie, Media.Show, Media.Season]

			if not media: media = [Media.Movie, Media.Show]
			elif media is True: media = [Media.Movie, Media.Show, Media.Season]

			if section is None: section = MetaTrakt.SectionProgress if Media.isSerie(media) else MetaTrakt.SectionCalendar

			category = None
			if media is None or Tools.isArray(media):
				media = None
				category = '' # If no category is added, all media is returned.
			elif media:
				if Media.isMovie(media):
					category = MetaTrakt.CategoryMovie
				elif Media.isSerie(media):
					if not structure: structure = media
					if media == Media.Show:
						category = MetaTrakt.CategoryShow
					elif media == Media.Season:
						category = MetaTrakt.CategorySeason
					if media == Media.Episode: media = Media.Show

			return self.listUser(link = MetaTrakt.LinkUserHidden, support = support, media = media, niche = niche, section = section, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)
		except: self._logError()
		return self._internal(internal = internal)

	# Feature, short, and special movies.
	def listHiddenMovie(self, niche = None, section = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listHidden(media = Media.Movie, niche = niche, section = section, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television feature movies.
	def listHiddenFeature(self, niche = None, section = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listHiddenMovie(niche = self._parameterNiche(niche = niche, extension = Media.Feature), section = section, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television short films (mostly returns nothing).
	def listHiddenShort(self, niche = None, section = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listHiddenMovie(niche = self._parameterNiche(niche = niche, extension = Media.Short), section = section, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Theater and television specials (mostly returns nothing).
	def listHiddenSpecial(self, niche = None, section = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listHiddenMovie(niche = self._parameterNiche(niche = niche, extension = Media.Special), section = section, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Multi-season shows and single-season mini-series.
	def listHiddenShow(self, niche = None, section = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listHidden(media = Media.Show, niche = niche, section = section, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Multi-season shows (will most likely include mini-series).
	def listHiddenMulti(self, niche = None, section = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listHiddenShow(niche = self._parameterNiche(niche = niche, extension = Media.Multi), section = section, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Single-season mini-series (does not work well).
	def listHiddenMini(self, niche = None, section = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, cache = None, internal = None):
		return self.listHiddenShow(niche = self._parameterNiche(niche = niche, extension = Media.Mini), section = section, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, cache = cache, internal = internal)

	# Shows seasons.
	def listHiddenSeason(self, niche = None, section = None, date = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, status = None, episode = None, company = None, studio = None, network = None, rating = None, votes = None, page = None, limit = None, sort = None, order = None, extended = None, filter = None, duplicate = None, structure = None, cache = None, internal = None):
		return self.listHidden(media = Media.Season, niche = niche, section = section, date = date, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, status = status, episode = episode, company = company, studio = studio, network = network, rating = rating, votes = votes, page = page, limit = limit, sort = sort, order = order, extended = extended, filter = filter, duplicate = duplicate, structure = structure, cache = cache, internal = internal)

	##############################################################################
	# METADATA
	##############################################################################

	'''
		TITLE DETAILS

		NOTES:
			Many of the parameters below require additional requests, hence use sparingly.
				During extended metadata retrieval for menus, only retrieve what is absolutely necessary and actually used in the menus.
				For instance, do not retrieve the translations, aliases, and set, for menus.
				Only retrieve them during scraping when additional titles are needed.

		MEDIA:
			String:		Single media from the list below.

			MOVIE
				Movie:		Level-0 support.
			SERIE
				Show:		Level-0 support.
				Season:		Level-0 support. Retrieve a single season, or all seasons of a show.
				Episode:	Level-0 support. Retrieve a single episode, all episodes of a season, or all episodes of a show.
			GROUP
				Set:		Level-0 support.
			ENTITY
				Person:		Level-0 support.

		PARAMETERS:
			id:						Trakt ID, Trakt slug, or IMDB ID.
			season:					Retrieve a specifc season.
				None:				Retrieve all seasons of the show.
				True:				Retrieve all seasons of the show.
				False:				Retrieve all seasons of the show.
				Integer:			Retrieve a specific season by number.
			episode:				Retrieve a specifc episode. If both season and episode is True, retrieve all episodes from the entire show, instead of just a single season. This can return a lot of data for some shows.
				None:				Retrieve all episodes of the season.
				True:				Retrieve all episodes of the season.
				False:				Retrieve all episodes of the season.
				Integer:			Retrieve a specific episode by number.
			summary:				Retrieve the summarized metadata. Requires an additional request.
				None:				Retrieve the summary.
				True:				Retrieve the summary.
				False:				Do not retrieve the summary.
				ExtendedBasic:		Only retrieve a basic info of the summary.
				ExtendedFull:		Retrieve an extended summary. This info necessary for Kodi menus/dialogs.
				ExtendedEpisode:	For episodes, return all episodes of the show, instead of just the episodes of a single season. Can return a lot of data, so use sparingly. Equivalent to "season = True, episode = True".
				List:				A combination of the extended info strings above. Eg: [ExtendedFull, ExtendedEpisode].
			person:					Retrieve the directors, writers, and cast. Requires an additional request. Retrieving for seasons/episodes requires one additional request per season/episode, so use sparingly.
				None:				Do not retrieve the people.
				True:				Retrieve the people.
				False:				Do not retrieve the people.
				ExtendedBasic:		Only retrieve a basic info of the people.
				ExtendedFull:		Retrieve extended info of the people. This info is unnecessary for Kodi menus/dialogs and returns a lot of data.
				ExtendedGuest:		Retrieve guest stars of the last episode. For shows, seasons, and episodes. This info is unnecessary for Kodi menus/dialogs and returns a lot of data.
				List:				A combination of the extended info strings above. Eg: [ExtendedFull, ExtendedGuest].
			studio:					Retrieve the studios. Requires an additional request.
				None:				Do not retrieve the studios.
				True:				Retrieve the studios.
				False:				Do not retrieve the studios.
			translation:			Retrieve the title, tagline, and plot in another language. Requires an additional request.
				None:				Retrieve the translations if the user's metadata language setting is non-English.
				True:				Retrieve the translations, irrespective of the user settings.
				False:				Do not retrieve the translations.
			alias:					Retrieve the alias titles from other countries. Requires an additional request.
				None:				Do not retrieve the aliases.
				True:				Retrieve the aliases.
				False:				Do not retrieve the aliases.
			rating:					Retrieve the rating distributions as the number of votes for each rating (integer in [1,10]). The average rating is already returned in the summary. Requires an additional request.
				None:				Do not retrieve the ratings.
				True:				Retrieve the ratings.
				False:				Do not retrieve the ratings.
			set:					Retrieve the set details if a movie belongs to a set. Requires one or two additional requests.
				None:				Do not retrieve the set.
				True:				Retrieve the set summary, without the individual parts/movies. Requires an additional request.
				False:				Do not retrieve the set.
				ExtendedFull:		Retrieve the set summary and the individual parts/movies. Requires two additional sequential requests.
			release:				Retrieve various release dates for a movie. Requires an additional request.
				None:				Do not retrieve the releases.
				True:				Retrieve the releases.
				False:				Do not retrieve the releases.
			language:				The language to use for translations.
				None:				Use the user's metadata language setting.
				True:				Use the user's metadata language setting.
				False:				Do not use any specifc language.
				String:				A two-letter ISO code of the language to use.
			country:				The country to use for translations and releases.
				None:				Use the user's metadata country setting.
				True:				Use the user's metadata country setting.
				False:				Do not use any specifc country.
				String:				A two-letter ISO code of the country to use.
			detail:					Return a detailed dictionary, indicating whether or not all data was retrieved successfully.
				None:				Do not return details, only the metadata.
				True:				Return the details.
				False:				Do not return details, only the metadata.
			concurrency:			If multiple requests should be run concurrently in threads.
				None:				Use concurrency if needed.
				True:				Use concurrency if needed.
				False:				Do not use concurrency.
	'''

	def metadata(self, media, id = None, trakt = None, imdb = None, tmdb = None, tvdb = None, title = None, year = None, season = None, episode = None, summary = None, person = None, studio = None, translation = None, alias = None, rating = None, set = None, release = None, language = None, country = None, extended = None, cache = None, detail = None, concurrency = None):
		result = None
		complete = True

		try:
			if not id: id = trakt or imdb

			# More info in the comments below at self.lookup().
			# Use a previous lookup to avoid trying to retrieve with the (non-existing) IMDb ID that will in any case fail.
			if not trakt and (not id or id.startswith('tt')):
				if Media.isMovie(media) or Media.isSerie(media):
					if id:
						if not imdb and id.startswith('tt'): imdb = id
						elif not trakt and not id.startswith('tt'): trakt = id
					lookup = self._lookupGet(media = Media.Show if Media.isSerie(media) else media, trakt = trakt, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year)
					if lookup and lookup.get('trakt'):
						id = trakt = lookup.get('trakt')
						imdb = lookup.get('imdb') or imdb
						tmdb = lookup.get('tmdb') or tmdb
						tvdb = lookup.get('tvdb') or tvdb

			if media == Media.Season:
				if season is None: season = True
			elif media == Media.Episode:
				if season is None: season = True
				if episode is None: episode = True

			# Allow Media.Show to be passed in with a season or episode number.
			if episode is True or Tools.isInteger(episode): media = Media.Episode
			elif season is True or Tools.isInteger(season): media = Media.Season

			# Retrieving all seasons/episodes requires the summary, in order to know how many seasons/episodes there are.
			late = (Media.isSeason(media) and not Tools.isInteger(season)) or (Media.isEpisode(media) and not Tools.isInteger(episode))
			early = Media.isMovie(media) or Media.isShow(media) or ((Media.isSeason(media) or Media.isEpisode(media)) and not late)
			if summary is False and late: summary = True

			# Only translate if explicitly stated (translation=True), otherwise only translate if it is non-English (translation=None).
			if translation is None: translation = bool(summary and self.language(language = language, exclude = True, default = False))

			# We can retrieve the episode translations with the summary API call.
			# This saves a lot of time for translation  retrievals, especially when creating pack data.
			# Although the translations added to the summary only contain the language code, but not the country code, although that should not cause any issues.
			translate = translation and Media.isEpisode(media)

			extra = person or studio or translation or alias or rating or release

			# DETAILS
			# Sometimes, for some titles, if "extended=full" is added, Trakt returns HTTP 500
			#	Eg: 300 (2007) - _metadataRelease()
			# Disable this parameter for all calls that do not have ExtendedInfo in the Trakt docs, in case they might occasionally have similar problems.
			iterator = []
			iterator.append(self._metadataSummary(media = media, summary = summary, season = season, episode = episode, extended = extended, translation = translate))
			iterator.append(self._metadataSet(media = media, set = set, extra = extra, extended = extended))
			iterator.append(self._metadataStudio(media = media, studio = studio, extended = False))
			iterator.append(self._metadataAlias(media = media, alias = alias, id = id, extended = False))
			iterator.append(self._metadataRelease(media = media, release = release, id = id, extended = False)) # Sometimes returns HTTP 500 if "extended=full" is passed in. Eg: 300 (2007).
			if early:
				iterator.append(self._metadataPerson(media = media, person = person, season = season, episode = episode, extended = extended)) # People for sets, multiple seasons, and multiple episodes are retrieved later, since the summary is needed for it.
				if not translate: iterator.append(self._metadataTranslation(media = media, translation = translation, summary = summary, id = id, season = season, episode = episode, language = language, extended = False))
				iterator.append(self._metadataRating(media = media, rating = rating, id = id, season = season, episode = episode, extended = False))

			data, errors = self._execute(iterator = iterator, media = media, id = id, trakt = trakt, imdb = imdb, tmdb = tmdb, tvdb = tvdb, extended = extended, cache = cache, concurrency = concurrency, page = False, limit = False, detail = True)

			if MetaTrakt.TypeSummary in data:
				items = data[MetaTrakt.TypeSummary]
				if items: result = self._processSummary(media = media, items = items, result = result, id = id, season = season)
				elif items is None: complete = False
			if result is None: result = {}

			# Trakt quite often does not have the IMDb ID of relatively new titles (yet), typically for less popular titles.
			# When retrieving the detailed metadata using the IMDb ID, a HTTP 404 error is returned.
			# It is important to have the Trakt metadata, especially for the (Standard/Essential)-detail metadata level that mostly relies on Trakt metadata, and even for the Extended-detail metadata level, in order to mark-as-watched and rate titles on Trakt.
			# Sometimes even weeks after the premiere, there is still no IMDb ID, and the IMDb button on Trakt's website just redirects to a title-search on IMDb. This happens even if Trakt says the metadata was refreshed today.
			# In very rare cases, this can also mean that Trakt does not have a movie at all that is already on IMDb. But this does not happen often. Typically Trakt has the title, but just has not linked it to IMDb.
			# It seems that the TMDb ID is typically available in these cases, since the Trakt data comes from TMDb.
			# In such a case, do a lookup with the TMDb/TVDb ID (if available), or the title/year, and try to retrieve again with the Trakt ID.
			if not complete and errors and id and id.startswith('tt'):
				if Media.isMovie(media) or Media.isSerie(media):
					# Only do this if there is no Trakt ID.
					# Otherwise the retry call below with self.metadata() might get called recursively if the title does not exist or Trakt returns a 404 error because of some other reason.
					if not trakt and (tmdb or tvdb or title):
						try: error = errors[MetaTrakt.TypeSummary]['code']
						except: error = None
						if error == 404:
							# Do not search by IMDb ID, because it already did not return results above.
							lookup = self.lookup(media = Media.Show if Media.isSerie(media) else media, trakt = None, imdb = None, tmdb = tmdb, tvdb = tvdb, title = title, year = year)
							if lookup and lookup.get('trakt'):
								trakt = lookup.get('trakt')
								imdb = lookup.get('imdb') or imdb
								tmdb = lookup.get('tmdb') or tmdb
								tvdb = lookup.get('tvdb') or tvdb
								return self.metadata(media = media, trakt = trakt, imdb = imdb, tmdb = tmdb, tvdb = tvdb, season = season, episode = episode, summary = summary, person = person, studio = studio, translation = translation, alias = alias, rating = rating, set = set, release = release, language = language, country = country, extended = extended, cache = cache, detail = detail, concurrency = concurrency)

			# LATE - SEASON + EPISODE
			# People and translations for seasons/episodes can only be retrieved with separate requests per season/episode.
			# This requires the number of seasons/episodes from the summary.
			# Update: There is an additional "translations" parameter for the seasons endpoint that retrieves all episodes which allows to get translations with the same call.
			if late:
				iterator = []
				if result and Tools.isArray(result):
					if Media.isSeason(media):
						for i in result:
							iterator.append(self._metadataPerson(media = media, person = person, season = i.get('season'), extended = extended))
							iterator.append(self._metadataTranslation(media = media, translation = translation, summary = summary, season = i.get('season'), language = language, extended = False))
							iterator.append(self._metadataRating(media = media, rating = rating, season = i.get('season'), extended = False))
					elif Media.isEpisode(media):
						for i in result:
							iterator.append(self._metadataPerson(media = media, person = person, season = season, episode = i.get('episode'), extended = extended))
							if not translate: iterator.append(self._metadataTranslation(media = media, translation = translation, summary = summary, season = i.get('season'), episode = i.get('episode'), language = language, extended = False)) # This should not execute anymore, since we now retrieve the episode translations with the summary above.
							iterator.append(self._metadataRating(media = media, rating = rating, season = i.get('season'), episode = i.get('episode'), extended = False))

				if iterator: data.update(self._execute(iterator = iterator, media = media, id = id, extended = extended, cache = cache, concurrency = concurrency, page = False, limit = False))

			# LATE - SET
			if MetaTrakt.TypeList in data:
				items = data[MetaTrakt.TypeList]
				if items is None:
					complete = False
				elif items:
					if Media.isSet(media):
						result = self._processSet(media = media, result = result, parts = items)
					else:
						result = self._processSet(media = media, result = result, items = items)
						if set == MetaTrakt.ExtendedFull:
							idSet = result.get('collection', {}).get('id', {}).get('trakt')
							if idSet:
								parts = self.list(media = Media.Movie, user = False, id = idSet, extended = extended, cache = cache, page = False, limit = False)
								if parts: result = self._processSet(media = media, result = result, parts = parts)
								else: complete = False

				iterator = []
				if result:
					part = result.get('part')
					if part:
						for i in part:
							partMedia = i.get('media')
							partId = id = i.get('id', {}).get(self.id())
							iterator.append(self._metadataPerson(media = partMedia, id = partId, person = person, set = True, extended = extended))
							iterator.append(self._metadataStudio(media = partMedia, id = partId, studio = studio, set = True, extended = False))
							iterator.append(self._metadataTranslation(media = partMedia, id = partId, translation = translation, summary = summary, language = language, set = True, extended = False))
							iterator.append(self._metadataAlias(media = partMedia, id = partId, alias = alias, set = True, extended = False))
							iterator.append(self._metadataRating(media = partMedia, id = partId, rating = rating, set = True, extended = False))
							iterator.append(self._metadataRelease(media = partMedia, id = partId, release = release, set = True, extended = False))
				if iterator: data.update(self._execute(iterator = iterator, extended = extended, cache = cache, concurrency = concurrency, page = False, limit = False))

			# Copy over the translations from the summary, and process like the data of a separate translation call.
			if translate:
				items = data[MetaTrakt.TypeSummary]
				if items:
					translations = {}
					for item in items if Tools.isArray(items) else [items]:
						numberSeason = item.get('season')
						numberEpisode = item.get('episode')
						if not numberSeason in translations: translations[numberSeason] = {}
						translations[numberSeason][numberEpisode] = self._temp(item = item, key = 'translation')
					data[MetaTrakt.TypeTranslation] = translations

			# PROCESS
			processes = [
				{'type' : MetaTrakt.TypePerson,			'function' : self._processPerson,		'parameters' : {}},
				{'type' : MetaTrakt.TypeStudio,			'function' : self._processStudio,		'parameters' : {}},
				{'type' : MetaTrakt.TypeTranslation,	'function' : self._processTranslation,	'parameters' : {'language' : language, 'country' : country}},
				{'type' : MetaTrakt.TypeAlias,			'function' : self._processAlias,		'parameters' : {}},
				{'type' : MetaTrakt.TypeRating,			'function' : self._processRating,		'parameters' : {}},
				{'type' : MetaTrakt.TypeRelease,		'function' : self._processRelease,		'parameters' : {'local' : country}},
			]
			for process in processes:
				type = process['type']
				if type in data:
					items = data[type]

					# Check if requests failed.
					# Sets, multiple seasons and episodes can have nested dictionaries with an integer key being the set ID, or season/episode numbers.
					if items is None:
						complete = False
					elif Tools.isDictionary(items) and Tools.isInteger(list(items.keys())[0]):
						for i in items.values():
							if i is None:
								complete = False
								break
							elif Tools.isDictionary(i) and Tools.isInteger(list(i.keys())[0]):
								for j in i.values():
									if j is None:
										complete = False
										break

					if items:
						parameters = {'media' : media, 'items' : items, 'result' : result}
						parameters.update(process['parameters'])
						result = process['function'](**parameters)
		except: self._logError()
		return {'provider' : self.id(), 'complete' : complete, 'data' : result} if detail else result

	def metadataMovie(self, id = None, trakt = None, imdb = None, tmdb = None, tvdb = None, title = None, year = None, summary = None, person = None, studio = None, translation = None, alias = None, rating = None, set = None, release = None, language = None, country = None, extended = None, cache = None, detail = None, concurrency = None):
		return self.metadata(media = Media.Movie, id = id, trakt = trakt, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year, summary = summary, person = person, studio = studio, translation = translation, alias = alias, rating = rating, set = set, release = release, language = language, country = country, extended = extended, cache = cache, detail = detail, concurrency = concurrency)

	def metadataSet(self, id = None, trakt = None, imdb = None, tmdb = None, tvdb = None, title = None, year = None, summary = None, person = None, studio = None, translation = None, alias = None, rating = None, set = None, release = None, language = None, country = None, extended = None, cache = None, detail = None, concurrency = None):
		return self.metadata(media = Media.Set, id = id, trakt = trakt, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year, summary = summary, person = person, studio = studio, translation = translation, alias = alias, rating = rating, set = set, release = release, language = language, country = country, extended = extended, cache = cache, detail = detail, concurrency = concurrency)

	def metadataShow(self, id = None, trakt = None, imdb = None, tmdb = None, tvdb = None, title = None, year = None, summary = None, person = None, studio = None, translation = None, alias = None, rating = None, language = None, country = None, extended = None, cache = None, detail = None, concurrency = None):
		return self.metadata(media = Media.Show, id = id, trakt = trakt, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year, summary = summary, person = person, studio = studio, translation = translation, alias = alias, rating = rating, language = language, country = country, extended = extended, cache = cache, detail = detail, concurrency = concurrency)

	def metadataSeason(self, id = None, trakt = None, imdb = None, tmdb = None, tvdb = None, title = None, year = None, season = None, summary = None, person = None, translation = None, rating = None, language = None, country = None, extended = None, cache = None, detail = None, concurrency = None):
		return self.metadata(media = Media.Season, id = id, trakt = trakt, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year, season = season, summary = summary, person = person, translation = translation, rating = rating, language = language, country = country, extended = extended, cache = cache, detail = detail, concurrency = concurrency)

	def metadataEpisode(self, id = None, trakt = None, imdb = None, tmdb = None, tvdb = None, title = None, year = None, season = None, episode = None, summary = None, person = None, translation = None, rating = None, language = None, country = None, extended = None, cache = None, detail = None, concurrency = None):
		return self.metadata(media = Media.Episode, id = id, trakt = trakt, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year, season = season, episode = episode, summary = summary, person = person, translation = translation, rating = rating, language = language, country = country, extended = extended, cache = cache, detail = detail, concurrency = concurrency)

	def metadataPerson(self, id = None, trakt = None, imdb = None, tmdb = None, tvdb = None, summary = None, extended = None, cache = None, detail = None, concurrency = None):
		return self.metadata(media = Media.Person, id = id, strakt = trakt, imdb = imdb, tmdb = tmdb, tvdb = tvdb, summary = summary, extended = extended, cache = cache, detail = detail, concurrency = concurrency)

	def metadataSummary(self, media, id, season = None, episode = None, summary = True, language = None, country = None, extended = None, cache = None, detail = None, concurrency = None):
		return self.metadata(media = media, id = id, season = season, episode = episode, summary = summary, language = language, country = country, extended = extended, cache = cache, detail = detail, concurrency = concurrency)

	def metadataPeople(self, media, id, season = None, episode = None, person = True, extended = None, cache = None, detail = None, concurrency = None):
		return self._metadataSection(detail = detail, temp = 'person', data = {'director' : True, 'writer' : True, 'cast' : True}, metadata = self.metadata(media = media, id = id, season = season, episode = episode, person = person, extended = extended, cache = cache, detail = detail, concurrency = concurrency))

	def metadataStudio(self, media, id, studio = True, extended = None, cache = None, detail = None, concurrency = None):
		return self._metadataSection(detail = detail, temp = 'studio', data = 'studio', metadata = self.metadata(media = media, id = id, studio = studio, extended = extended, cache = cache, detail = detail, concurrency = concurrency))

	def metadataTranslation(self, media, id, season = None, episode = None, translation = True, language = None, country = None, extended = None, cache = None, detail = None, concurrency = None):
		return self._metadataSection(detail = detail, temp = 'translation', data = ['alias', 'language'], metadata = self.metadata(media = media, id = id, season = season, episode = episode, translation = translation, language = language, country = country, extended = extended, cache = cache, detail = detail, concurrency = concurrency))

	def metadataAlias(self, media, id, alias = True, language = None, country = None, extended = None, cache = None, detail = None, concurrency = None):
		return self._metadataSection(detail = detail, temp = 'alias', data = ['alias', 'country'], metadata = self.metadata(media = media, id = id, alias = alias, language = language, country = country, extended = extended, cache = cache, detail = detail, concurrency = concurrency))

	def metadataRating(self, media, id, season = None, episode = None, rating = True, extended = None, cache = None, detail = None, concurrency = None):
		return self._metadataSection(detail = detail, temp = 'voting', data = {'rating' : True, 'votes' : True, 'distribution' : True}, metadata = self.metadata(media = media, id = id, season = season, episode = episode, rating = rating, extended = extended, cache = cache, detail = detail, concurrency = concurrency))

	def metadataPart(self, media, id, set = True, language = None, country = None, extended = None, cache = None, detail = None, concurrency = None):
		return self._metadataSection(detail = detail, data = 'collection' if Media.isMovie(media) else 'part', metadata = self.metadata(media = media, id = id, set = set, language = language, country = country, extended = extended, cache = cache, detail = detail, concurrency = concurrency))

	def metadataRelease(self, media, id, release = True, country = None, extended = None, cache = None, detail = None, concurrency = None):
		return self._metadataSection(detail = detail, temp = 'release', data = 'time', metadata = self.metadata(media = media, id = id, release = release, country = country, extended = extended, cache = cache, detail = detail, concurrency = concurrency))

	def _metadataSection(self, metadata, detail, temp = None, data = None):
		if detail is None:
			if temp:
				if Tools.isDictionary(temp): return {k : metadata.get(k) for k in temp.keys()}
				else: return self._temp(key = temp, item = metadata)
			elif data:
				return self._metadataSection(metadata = metadata, detail = False, data = data)
		elif detail is False:
			if data:
				if Tools.isDictionary(data): return {k : metadata.get(k) for k in data.keys()}
				else: return self._data(key = data, item = metadata)
			elif temp:
				return self._metadataSection(metadata = metadata, detail = None, temp = temp)
		return metadata

	def _metadataExtended(self, value, extended = None, image = None, none = True):
		result = False
		episodes = Tools.isArray(value) and MetaTrakt.ExtendedEpisode in value

		if (not extended is False or episodes) and not extended == MetaTrakt.ExtendedBasic and not value == MetaTrakt.ExtendedBasic:
			result = []

			# Trakt allows to add multiple "extended" values (eg: "extended=full,episodes").
			if not value is False:
				if extended is True or (none and extended is None): result.append(MetaTrakt.ExtendedFull)
				elif Tools.isString(extended): result.append(extended)
				elif Tools.isArray(extended): result.extend(extended)

			if Tools.isString(value): result.append(value)
			elif Tools.isArray(value): result.extend(value)

			if image: result.append(MetaTrakt.ExtendedImages)

			result = Tools.listUnique(result)

		return result

	def _metadataSummary(self, media = None, summary = None, id = None, season = None, episode = None, extended = None, translation = None):
		data = None

		if summary or summary is None:
			if Media.isPerson(media):
				data = {'link' : MetaTrakt.LinkPerson}
			elif Media.isSet(media):
				# For some reason Trakt returns a HTTP 500 error when retrieving the list summary with MetaTrakt.LinkList.
				# This previously worked fine. Either Trakt changed something, or this is just a temporary problem.
				# Trying to retrieve sets as user lists (with the user: Trakt/trakt/official) does not work and returns HTTP 404.
				# For now, use the search endpoint to retrieve the list. This seems to be a bit slower than directly retrieving the list.
				# Eg: https://api.trakt.tv/lists/884 (Name: Avatar Collection | ID: 884 | Slug: avatar-collection)
				# Update: LinkList has started to work again. Use it for now, and if it causes issues, revert back to LinkSearchId.
				data = {'link' : MetaTrakt.LinkList}
				#data = {'link' : MetaTrakt.LinkSearchId, 'search' : MetaTrakt.TypeList, 'list' : MetaTrakt.ListOfficial}
			elif Media.isMovie(media):
				data = {'link' : MetaTrakt.LinkMovieSummary}
			elif Media.isShow(media):
				data = {'link' : MetaTrakt.LinkShowSummary}
			elif Media.isSeason(media):
				data = {'link' : MetaTrakt.LinkSeasonSummary, 'season' : ''}
			elif Media.isEpisode(media):
				if season is True:
					summary = summary if Tools.isArray(summary) else [summary] if Tools.isString(summary) else []
					summary.append(MetaTrakt.ExtendedEpisode)
					data = {'link' : MetaTrakt.LinkSeasonSummary, 'media' : Media.Season, 'season' : ''}
				elif episode is True or episode is None:
					data = {'link' : MetaTrakt.LinkSeasonSummary, 'season' : season}
				else:
					data = {'link' : MetaTrakt.LinkEpisodeSummary, 'season' : season, 'episode' : '' if (episode is None or episode is True or episode is False) else episode}

			if data:
				if id: data['id'] = id
				if not 'extended' in data: data['extended'] = self._metadataExtended(value = summary, extended = extended, image = True, none = True)
				if translation: data['translation'] = translation
				data['result'] = MetaTrakt.TypeSummary

		return data

	def _metadataSet(self, media = None, set = None, extra = None, extended = None):
		data = None

		extendedSet = not extended is False and Media.isSet(media) and extra
		if set or extended or extendedSet:
			if Media.isSet(media):
				data = {'function' : self.list, 'media' : Media.Movie, 'user' : False, 'extended' : extendedSet, 'page' : False, 'limit' : False}
			elif Media.isMovie(media) and set:
				data = {'link' : MetaTrakt.LinkDetailList, 'category' : MetaTrakt.CategoryMovie, 'media' : Media.Set, 'list' : MetaTrakt.ListOfficial, 'sort' : MetaTrakt.SortPopular, 'limit' : 300}

			if data:
				if not 'extended' in data: data['extended'] = self._metadataExtended(value = set, extended = extended, none = True)
				data['result'] = MetaTrakt.TypeList

		return data

	def _metadataPerson(self, media = None, person = None, id = None, season = None, episode = None, set = None, extended = None):
		data = None

		if person:
			if Media.isMovie(media):
				data = {'link' : MetaTrakt.LinkMoviePerson}
			elif Media.isShow(media):
				data = {'link' : MetaTrakt.LinkShowPerson}
			elif Media.isSeason(media):
				data = {'link' : MetaTrakt.LinkSeasonPerson, 'season' : season}
			elif Media.isEpisode(media):
				if season is True:
					data = {'link' : MetaTrakt.LinkSeasonPerson, 'media' : Media.Season, 'season' : ''}
				elif episode is True:
					data = {'link' : MetaTrakt.LinkSeasonPerson, 'season' : season}
				else:
					data = {'link' : MetaTrakt.LinkEpisodePerson, 'season' : season, 'episode' : '' if (episode is None or episode is True or episode is False) else episode}

			if data:
				if media: data['media'] = media
				if id: data['id'] = id
				if not 'extended' in data:
					if extended is True and Media.isSerie(media): extended = [MetaTrakt.ExtendedFull, MetaTrakt.ExtendedGuest] # Also retrieve guest stars.
					data['extended'] = self._metadataExtended(value = person, extended = extended, image = True, none = False) # none = False: all the extra info is unnecessary for Kodi menus/dialogs.

				result = [MetaTrakt.TypePerson]
				if Media.isSeason(media) or Media.isEpisode(media): result.append(season)
				if Media.isEpisode(media): result.append(episode)
				if set: result.append(int(id)) # Add the ID as integer, since we check if the request was successful, by iterating over nested dictionary keys that are numeric.
				data['result'] = result

		return data

	def _metadataStudio(self, media = None, studio = None, id = None, set = None, extended = None):
		data = None

		if studio:
			if Media.isMovie(media):
				data = {'link' : MetaTrakt.LinkMovieStudio}
			elif Media.isShow(media):
				data = {'link' : MetaTrakt.LinkShowStudio}

			if data:
				if media: data['media'] = media
				if id: data['id'] = id
				if not 'extended' in data: data['extended'] = self._metadataExtended(value = studio, extended = extended, none = True)

				result = [MetaTrakt.TypeStudio]
				if set: result.append(int(id)) # Add the ID as integer, since we check if the request was successful, by iterating over nested dictionary keys that are numeric.
				data['result'] = result

		return data

	def _metadataTranslation(self, media = None, translation = None, summary = None, id = None, season = None, episode = None, language = None, set = None, extended = None):
		data = None

		if translation:
			if Media.isMovie(media):
				data = {'link' : MetaTrakt.LinkMovieTranslation}
			elif Media.isShow(media):
				data = {'link' : MetaTrakt.LinkShowTranslation}
			elif Media.isSeason(media):
				data = {'link' : MetaTrakt.LinkSeasonTranslation, 'season' : season}
			elif Media.isEpisode(media):
				data = {'link' : MetaTrakt.LinkEpisodeTranslation, 'season' : season, 'episode' : '' if episode is True else episode}

			if data:
				if media: data['media'] = media
				if id: data['id'] = id
				if not 'extended' in data: data['extended'] = self._metadataExtended(value = translation, extended = extended, none = True)
				data['language'] = '' # Language is filtered in processTranslation().

				result = [MetaTrakt.TypeTranslation]
				if Media.isSeason(media) or Media.isEpisode(media): result.append(season)
				if Media.isEpisode(media): result.append(episode)
				if set: result.append(int(id)) # Add the ID as integer, since we check if the request was successful, by iterating over nested dictionary keys that are numeric.
				data['result'] = result

		return data

	def _metadataAlias(self, media = None, alias = None, id = None, set = None, extended = None):
		data = None

		if alias:
			if Media.isMovie(media):
				data = {'link' : MetaTrakt.LinkMovieAlias}
			elif Media.isShow(media):
				data = {'link' : MetaTrakt.LinkShowAlias}

			if data:
				if media: data['media'] = media
				if id: data['id'] = id
				if not 'extended' in data: data['extended'] = self._metadataExtended(value = alias, extended = extended, none = True)

				result = [MetaTrakt.TypeAlias]
				if set: result.append(int(id)) # Add the ID as integer, since we check if the request was successful, by iterating over nested dictionary keys that are numeric.
				data['result'] = result

		return data

	def _metadataRating(self, media = None, rating = None, id = None, season = None, episode = None, set = None, extended = None):
		data = None

		if rating:
			if Media.isMovie(media):
				data = {'link' : MetaTrakt.LinkMovieRating}
			elif Media.isShow(media):
				data = {'link' : MetaTrakt.LinkShowRating}
			elif Media.isSeason(media):
				data = {'link' : MetaTrakt.LinkSeasonRating, 'season' : season}
			elif Media.isEpisode(media):
				data = {'link' : MetaTrakt.LinkEpisodeRating, 'season' : season, 'episode' : '' if episode is True else episode}

			if data:
				if media: data['media'] = media
				if id: data['id'] = id
				if not 'extended' in data: data['extended'] = self._metadataExtended(value = rating, extended = extended, none = True)

				result = [MetaTrakt.TypeRating]
				if Media.isSeason(media) or Media.isEpisode(media): result.append(season)
				if Media.isEpisode(media): result.append(episode)
				if set: result.append(int(id)) # Add the ID as integer, since we check if the request was successful, by iterating over nested dictionary keys that are numeric.
				data['result'] = result

		return data

	def _metadataRelease(self, media = None, release = None, id = None, set = None, extended = None):
		data = None

		if release:
			if Media.isMovie(media):
				data = {'link' : MetaTrakt.LinkMovieRelease}

			if data:
				if media: data['media'] = media
				if id: data['id'] = id
				if not 'extended' in data: data['extended'] = self._metadataExtended(value = release, extended = extended, none = True)
				data['country'] = '' # Country is filtered in processRelease().

				result = [MetaTrakt.TypeRelease]
				if set: result.append(int(id)) # Add the ID as integer, since we check if the request was successful, by iterating over nested dictionary keys that are numeric.
				data['result'] = result

		return data

	##############################################################################
	# PACK
	##############################################################################

	# Enable translations by default. This only requires one additional request for the show metadata, and NO additional requests for the episode metadata, since the translations are appended to the same request.
	# Retrieve the translations with Trakt, since TVDb can only do this by making a separate request for each individual episode in the show, which takes way too long.
	# Plus if the show metadata is refreshed once a month, recreating the pack will require too many request.
	# Currently the alias titles are not absolutely necessary for any current pack feature.
	# However, it can make the pack more accurate, when Trakt and TVDb pack data is combined, and both have different episode numbering.
	# In such a case the episode titles are matched to determine which episode number from Trakt belongs to which episode number of TVDb.
	# Eg: Dragon Ball Super. Has different numbering on Trakt and TVDb. Plus the default titles on TVDb are in Japanese, whereas the default Trakt title is English.
	def metadataPack(self, id = None, trakt = None, imdb = None, tmdb = None, tvdb = None, title = None, year = None, dataShow = None, dataEpisode = None, translation = True, threaded = None, cache = None, detail = None):
		complete = True
		result = None
		try:
			if not id: id = trakt or imdb
			if id or (dataShow and dataEpisode):
				from lib.meta.pack import MetaPack

				def _packNumber(season, episode):
					return int(('%06d' % season) + ('%06d' % episode))

				if dataShow is None: dataShow = self.metadataShow(id = id, trakt = trakt, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year, cache = cache) # No translations needed for this.
				if dataShow:
					current = Time.timestamp()
					seasons = []

					# In case they were retrieved by lookup in metadataShow()
					if not trakt:
						try: trakt = dataShow['id']['trakt']
						except: pass
					if not imdb:
						try: imdb = dataShow['id']['imdb']
						except: pass
					if not tmdb:
						try: tmdb = dataShow['id']['tmdb']
						except: pass
					if not tvdb:
						try: tvdb = dataShow['id']['tvdb']
						except: pass
					id = trakt or imdb

					try: country = dataShow['country']
					except: country = None
					try: zone = dataShow['airs']['zone']
					except: zone = None
					if not country and not zone: zone = 'UTC' # Trakt returns dates in GMT/UTC timezone.

					if dataEpisode is None:
						dataEpisode = self.metadataEpisode(id = id, trakt = trakt, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year, cache = cache, translation = translation, extended = True) # Extended for the time and duration.
					if dataEpisode:
						order = []
						dataSeason = {} # Dict for avoiding duplicates.
						for episode in dataEpisode:
							season = self._temp(item = episode, key = ['detail', 'season'])
							if season:
								season = Tools.copy(season) # Copy, otherwise the is a circular reference when adding the episodes below.
								number = season.get('season')
								if not number in dataSeason:
									season['episodes'] = []
									dataSeason[number] = season
								dataSeason[number]['episodes'].append(episode)
								if number > 0: order.append(_packNumber(season = number, episode = episode.get('episode')))

						# Determine the abolsute episode number.
						order = Tools.listSort(order)
						order = {order[i] : i + 1 for i in range(len(order))}

						dataSeason = Tools.listSort(list(dataSeason.values()), key = lambda i : i.get('season'))
						for i in range(len(dataSeason)):
							season = dataSeason[i]
							numberSeason = season.get('season')
							numbersSeason = {MetaPack.NumberStandard : numberSeason}
							if not MetaPack.NumberAbsolute in numbersSeason: numbersSeason[MetaPack.NumberAbsolute] = 1 if numberSeason > 0 else 0
							if not MetaPack.NumberSequential in numbersSeason: numbersSeason[MetaPack.NumberSequential] = 1 if numberSeason > 0 else 0

							# Sometimes Trakt has clearly incorrect absolute numbers.
							# Eg: My Name is Earl S03E01+ has absolute number 1+.
							# This is probably the absolute number within S03 instead of the entire show, since TVDb has a bunch of extra split/double episodes.
							absolute = True
							if numberSeason and numberSeason > 1:
								# Still allow it if the first episode does not start at E01, for absolute-episode numbers.
								# Eg: One Piece S02+.
								try: first = season['episodes'][0]
								except: first = None
								if first and first.get('absolute') == first.get('episode') and first.get('episode') == 1: absolute = False

							episodes = []
							aliases = []
							times = []
							types = []
							durations = []
							counter = 0
							previous = 0

							for episode in season['episodes']:
								numberEpisode = episode.get('episode')
								numberAbsolute = episode.get('absolute')

								if not absolute: numberAbsolute = None
								numbersEpisode = {MetaPack.NumberStandard : [numberSeason, numberEpisode], MetaPack.NumberAbsolute : [1, numberAbsolute or 0]}

								if numberSeason > 0:
									counter += 1

									# Sometimes Trakt has a missing episode.
									# Increase the counter, so that the custom episode still matches with the standard episode number.
									# Eg: The Tonight Show Starring Jimmy Fallon S01E174 (missing on both Trakt and TMDb).
									# Only do this up to 3 missing episodes, since Trakt/TMDb can sometimes have entire blocks of episodes missing.
									if previous:
										difference = abs(previous - numberEpisode)
										if difference > 1 and difference <= 3: counter += (difference - 1)

									# Add this for shows where Trakt uses season-numbering for seasons, but within each season, episodes are numbered absolutely.
									# Eg: One Piece first episode of S02 is S02E62, not S02E01.
									# Do not do for specials, since Trakt might have specials missing.
									# Eg: GoT S00E08
									numbersEpisode[MetaPack.NumberCustom] = [numberSeason, counter]

									previous = numberEpisode

								if not MetaPack.NumberSequential in numbersEpisode:
									if numberSeason == 0:
										numbersEpisode[MetaPack.NumberSequential] = [1, 0]
									else:
										try: numbersEpisode[MetaPack.NumberSequential] = [1, order[_packNumber(season = numberSeason, episode = numberEpisode)]]
										except: pass

								id = episode.get('id', {}).get('episode') or {}

								title = episode.get('title')
								if title and not Tools.isArray(title): title = [title]

								time = episode.get('time', {}).get('premiere')
								times.append(time if time else 0)

								date = Time.format(timestamp = time, format = Time.FormatDate, zone = zone, country = country) if time else None

								status = episode.get('status')
								if not status: status = self.mMetatools.mergeStatus(media = Media.Episode, season = numberSeason, episode = numberEpisode, time = time)

								type = episode.get('type')

								# Trakt sometimes marks premieres as standard episodes.
								# Eg: One Piece: many SxxE01
								# Probably because Trakt looks for SxxE01 as premieres, but if abolsute episode numbers are used, the premiere has a different number.
								# Eg: One Piece S04E01 (S04E92 on Trakt).
								# Also use "counter" instead of "numberEpisode", because of exactly this reason.
								if not type or (numberSeason and counter == 1 and not Media.Premiere in type): type = [Media.Premiere, Media.Outer if numberSeason == 1 else Media.Inner]
								types.append(type)

								duration = episode.get('duration')
								if duration: durations.append(duration)

								# This is an absolute horrible solution, but not sure if there is a better option.
								# Trakt sometimes has the incorrect alias for an episode, so that two different episodes have the same alias title.
								# Eg: Dragon Ball Super S01E109 vs S01E110 - same Japanese alias.
								# Before those two episodes had the correct aliases. But then Trakt updated the metadata of that show (2025-05-09) and suddenly those two episodes had the same title.
								# This causes matching problems in MetaPack so that S01E110 is seen as an unofficial episode using Trakt's number S01E109 (instead of S01E110), since it matches S01E109's title as well.
								# Maybe this was caused by Trakt scraping TVDb and TVDb having added specials to the standard seasons, causing an incorrect episode offset on Trakt. More info at MetaTvdb.metadataEpisode(pack = ...).
								# Hacky solution: if we see an alias appear twice for different episodes in the same season, just ignore the subsequent aliases.
								# Maybe this is something that will be fixed on Trakt in the future.
								alias = episode.get('alias')
								if alias:
									alias = {k : [x for x in v if x and not x in aliases] for k, v in alias.items() if v}
									for x in alias.values(): aliases.extend(x)

								episodes.append({
									'id' : {
										'imdb'	: id.get('imdb'),
										'tmdb'	: id.get('tmdb'),
										'tvdb'	: id.get('tvdb'),
										'trakt'	: id.get('trakt'),
										'slug'	: id.get('slug'),
									},
									'title'		: title,
									'alias'		: alias,
									'number'	: numbersEpisode,
									'year'		: Time.year(timestamp = time) if time else episode.get('year'),
									'date'		: date,
									'time'		: time,
									'status'	: status,
									'serie'		: type,
									'duration'	: duration,
								})

							id = season.get('id', {}).get('season') or {}

							title = season.get('title')
							if title and not Tools.isArray(title): title = [title]

							type = season.get('type')

							time = season.get('time', {}).get('premiere')
							if not time and times: time = min(times)
							date = Time.format(timestamp = time, format = Time.FormatDate, zone = zone, country = country) if time else None

							# Trakt only has a status for shows, but not for seasons. Calculate the status based on the episode release dates.
							status = season.get('status')
							if not status:
								# Do not mark the season as ended purley on time.
								# Since the season might still continue, although the last episode has already been aired, but there are new unaired episodes that were not scraped by Trakt yet.
								try: timeNext = dataSeason[i + 1]['episodes'][0]['time']['premiere']
								except: timeNext = None
								try: timeLast = dataSeason[-1]['episodes'][-1]['time']['premiere']
								except: timeLast = None
								status = self.mMetatools.mergeStatus(media = Media.Season, season = numberSeason, time = time, timeSeasonLast = timeLast, timeSeasonNext = timeNext, timeEpisode = times, type = type, typeEpisode = types, status = dataShow.get('status'))

							duration = season.get('duration')
							if not duration and durations: duration = int(sum(durations) / float(len(durations)))

							seasons.append({
								'id' : {
									'imdb'	: id.get('imdb'),
									'tmdb'	: id.get('tmdb'),
									'tvdb'	: id.get('tvdb'),
									'trakt'	: id.get('trakt'),
									'slug'	: id.get('slug'),
								},
								'title'		: title,
								'alias'		: season.get('alias'),
								'number'	: numbersSeason,
								'year'		: Time.year(timestamp = time) if time else season.get('year'),
								'date'		: date,
								'time'		: time,
								'status'	: status,
								'serie'		: type,
								'duration'	: duration,
								'episodes'	: episodes,
							})
					else: complete = False

					id = dataShow.get('id') or {}

					title = dataShow.get('title')
					if title and not Tools.isArray(title): title = [title]

					time = None
					date = dataShow.get('premiered')
					if date: time = Time.timestamp(fixedTime = date, format = Time.FormatDate, utc = True)

					result = {
						'id' : {
							'imdb'	: id.get('imdb') or imdb, # If Trakt does not have the IMDb yet.
							'tmdb'	: id.get('tmdb') or tmdb,
							'tvdb'	: id.get('tvdb') or tvdb,
							'trakt'	: id.get('trakt'),
							'slug'	: id.get('slug'),
						},
						'title'		: title,
						'alias'		: dataShow.get('alias'),
						'year'		: dataShow.get('year'),
						'date'		: date,
						'time'		: time,
						'status'	: dataShow.get('status'),
						'duration'	: dataShow.get('duration'),
						'language'	: dataShow.get('language'),
						'country'	: dataShow.get('country'),
						'seasons'	: seasons,
					}
				else: complete = False
		except: Logger.error()
		return {'provider' : self.id(), 'complete' : complete, 'data' : result} if detail else result
