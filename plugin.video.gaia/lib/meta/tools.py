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

try: from xbmc import Actor, VideoStreamDetail, AudioStreamDetail, SubtitleStreamDetail # Kodi 20+
except: pass

from lib.meta.data import MetaData
from lib.meta.pack import MetaPack
from lib.meta.image import MetaImage
from lib.meta.company import MetaCompany

from lib.modules.tools import Media, Title, Language, Country, Tools, Converter, Regex, Logger, System, Settings, Audience, Time, Math, Matcher, File
from lib.modules.interface import Context, Directory, Icon, Format, Translation, Skin, Font, Detail
from lib.modules.convert import ConverterTime
from lib.modules.theme import Theme
from lib.modules.network import Networker
from lib.modules.shortcut import Shortcut
from lib.modules.cache import Cache, Memory
from lib.modules.concurrency import Pool, Lock
from lib.modules.video import Trailer, Recap, Review, Reaction, Bonus, Deleted, Production, Direction, Interview, Explanation, Alternation

class MetaTools(object):

	DetailEssential				= 'essential'
	DetailStandard				= 'standard'
	DetailExtended				= 'extended'
	Details						= [DetailEssential, DetailStandard, DetailExtended]

	ProviderImdb				= 'imdb'
	ProviderTmdb				= 'tmdb'
	ProviderTvdb				= 'tvdb'
	ProviderTvmaze				= 'tvmaze'
	ProviderTvrage				= 'tvrage'
	ProviderTrakt				= 'trakt'
	ProviderFanart				= 'fanart'
	ProviderImdx				= 'imdx' # Old IMDb ID that got replaced by a new IMDb ID.
	Providers					= [ProviderImdb, ProviderTmdb, ProviderTvdb, ProviderTvmaze, ProviderTvrage, ProviderTrakt, ProviderFanart]

	ExtendFull					= 'full' # Add extended info, release decoration, and use the show title + numbering instead of the episode title.
	ExtendBasic					= 'basic' # Do not add any extended info. Add release decoration and use the show title + numbering instead of the episode title.
	ExtendTitle					= 'title' # Do not add any extended info or release decoration. Only use the episode title instead of the show title + numbering.
	ExtendNone					= False # Do not add any extended info, release decoration, or episode title adaption.

	ContentNever				= 0
	ContentOccasional			= 1
	ContentRegular				= 2
	ContentFrequent				= 3

	ContentSearch				= 'search'		# Internal. Must be the same as the MetaMenu enum.
	ContentQuick				= 'quick'		# Internal. Must be the same as the MetaMenu enum.
	ContentProgress				= 'progress'	# Internal. Must be the same as the MetaMenu enum.
	ContentArrival				= 'arrival'		# Internal. Must be the same as the MetaMenu enum.

	StreamVideo					= 'video'
	StreamAudio					= 'audio'
	StreamSubtitle				= 'subtitle'
	StreamDuration				= 'duration'
	StreamCodec					= 'codec'
	StreamAspect				= 'aspect'
	StreamWidth					= 'width'
	StreamHeight				= 'height'
	StreamChannels				= 'channels'
	StreamLanguage				= 'language'

	# NB: If any genre enum value is changed, also change in meta/data.py.

	GenreNone					= 'none'				# IMDb (Unsupported)				Trakt (Movie+Show: none - "None")							TMDb (Unsupported)															TVDb (Unsupported)
	GenreAction					= 'action'				# IMDb (Movie+Show: "Action")		Trakt (Movie+Show: action - "Action")						TMDb (Movie: 28 - "Action" | Show: 10759 - "Action & Adventure")			TVDb (Movie+Show: 19 - action - "Action")
	GenreAdventure				= 'adventure'			# IMDb (Movie+Show: "Adventure")	Trakt (Movie+Show: adventure - "Adventure")					TMDb (Movie: 12 - "Adventure" | Show: 10759 - "Action & Adventure")			TVDb (Movie+Show: 18 - adventure - "Adventure")
	GenreAnimation				= 'animation'			# IMDb (Movie+Show: "Animation")	Trakt (Movie+Show: animation - "Animation")					TMDb (Movie+Show: 16 - "Animation")											TVDb (Movie+Show: 17 - animation - "Animation")
	GenreAnime					= 'anime'				# IMDb (Unsupported)				Trakt (Movie+Show: anime - "Anime")							TMDb (Unsupported)															TVDb (Movie+Show: 27 - anime - "Anime")
	GenreBiography				= 'biography'			# IMDb (Movie+Show: "Biography")	Trakt (Show: biography - "Biography")						TMDb (Unsupported)															TVDb (Unsupported)
	GenreChildren				= 'children'			# IMDb (Unsupported)				Trakt (Show: children - "Children")							TMDb (Show: 10762 - "Kids")													TVDb (Movie+Show: 16 - children - "Children")
	GenreComedy					= 'comedy'				# IMDb (Movie+Show: "Comedy")		Trakt (Movie+Show: comedy - "Comedy")						TMDb (Movie+Show: 35 - "Comedy")											TVDb (Movie+Show: 15 - comedy - "Comedy")
	GenreCrime					= 'crime'				# IMDb (Movie+Show: "Crime")		Trakt (Movie+Show: crime - "Crime")							TMDb (Movie+Show: 80 - "Crime")												TVDb (Movie+Show: 14 - crime - "Crime")
	GenreDocumentary			= 'documentary'			# IMDb (Movie+Show: "Documentary")	Trakt (Movie+Show: documentary - "Documentary")				TMDb (Movie+Show: 99 - "Documentary")										TVDb (Movie+Show: 13 - documentary - "Documentary")
	GenreDonghua				= 'donghua'				# IMDb (Unsupported)				Trakt (Movie+Show: donghua - "Donghua")						TMDb (Unsupported)															TVDb (Unsupported)
	GenreDrama					= 'drama'				# IMDb (Movie+Show: "Drama")		Trakt (Movie+Show: drama - "Drama")							TMDb (Movie+Show: 18 - "Drama")												TVDb (Movie+Show: 12 - drama - "Drama")
	GenreFamily					= 'family'				# IMDb (Movie+Show: "Family")		Trakt (Movie+Show: family - "Family")						TMDb (Movie+Show: 10751 - "Family")											TVDb (Movie+Show: 11 - family - "Family")
	GenreFantasy				= 'fantasy'				# IMDb (Movie+Show: "Fantasy")		Trakt (Movie+Show: fantasy - "Fantasy")						TMDb (Movie: 14 - "Fantasy" | Show: 10765 - "Sci-Fi & Fantasy")				TVDb (Movie+Show: 10 - fantasy - "Fantasy")
	GenreHistory				= 'history'				# IMDb (Movie+Show: "History")		Trakt (Movie+Show: history - "History")						TMDb (Movie: 36 - "History")												TVDb (Movie+Show: 33 - history - "History")
	GenreHorror					= 'horror'				# IMDb (Movie+Show: "Horror")		Trakt (Movie+Show: horror - "Horror")						TMDb (Movie: 27 - "Horror")													TVDb (Movie+Show: 6 - horror - "Horror")
	GenreMartial				= 'martial'				# IMDb (Unsupported)				Trakt (Unsupported)											TMDb (Unsupported)															TVDb (Movie+Show: 35 - martial-arts - "Martial Arts")
	GenreMusic					= 'music'				# IMDb (Movie+Show: "Music")		Trakt (Movie+Show: music - "Music")							TMDb (Movie: 10402 - "Music")												TVDb (Unsupported)
	GenreMusical				= 'musical'				# IMDb (Movie+Show: "Musical")		Trakt (Movie+Show: musical - "Musical")						TMDb (Unsupported)															TVDb (Movie+Show: 29 - musical - "Musical")
	GenreMystery				= 'mystery'				# IMDb (Movie+Show: "Mystery")		Trakt (Movie+Show: mystery - "Mystery")						TMDb (Movie+Show: 9648 - "Mystery")											TVDb (Movie+Show: 31 - mystery - "Mystery")
	GenreNoir					= 'noir'				# IMDb (Movie: "Film-Noir")			Trakt (Unsupported)											TMDb (Unsupported)															TVDb (Unsupported)
	GenrePolitics				= 'politics'			# IMDb (Unsupported)				Trakt (Unsupported)											TMDb (Show: 10768 - "War & Politics")										TVDb (Unsupported)
	GenreRomance				= 'romance'				# IMDb (Movie+Show: "Romance")		Trakt (Movie+Show: romance - "Romance")						TMDb (Movie: 10749 - "Romance")												TVDb (Movie+Show: 28 - romance - "Romance")
	GenreScifi					= 'scifi'				# IMDb (Movie+Show: "Sci-Fi")		Trakt (Movie+Show: science-fiction - "Science Fiction")		TMDb (Movie: 878 - "Science Fiction" | Show: 10765 - "Sci-Fi & Fantasy")	TVDb (Movie+Show: 2 - science-fiction - "Science Fiction")
	GenreSuperhero				= 'superhero'			# IMDb (Unsupported)				Trakt (Movie+Show: superhero - "Superhero")					TMDb (Unsupported)															TVDb (Unsupported)
	GenreSuspense				= 'suspense'			# IMDb (Unsupported)				Trakt (Movie+Show: suspense - "Suspense")					TMDb (Unsupported)															TVDb (Movie+Show: 22 - suspense - "Suspense")
	GenreThriller				= 'thriller'			# IMDb (Movie+Show: "Thriller")		Trakt (Movie+Show: thriller - "Thriller")					TMDb (Movie: 53 - "Thriller")												TVDb (Movie+Show: 24 - thriller - "Thriller")
	GenreWar					= 'war'					# IMDb (Movie+Show: "War")			Trakt (Movie+Show: war - "War")								TMDb (Movie: 10752 - "War" | Show: 10768 - "War & Politics")				TVDb (Movie+Show: 34 - war - "War")
	GenreWestern				= 'western'				# IMDb (Movie+Show: "Western")		Trakt (Movie+Show: western - "Western")						TMDb (Movie+Show: 37 - "Western")											TVDb (Movie+Show: 26 - western - "Western")
	GenreShort					= 'short'				# IMDb (Movie+Show: "Short")		Trakt (Movie+Show: short - "Short")							TMDb (Unsupported)															TVDb (Unsupported)
	GenreMini					= 'mini'				# IMDb (Unsupported)				Trakt (Show: mini-series - "Mini Series")					TMDb (Unsupported)															TVDb (Show: 5 - mini-series - "Mini-Series")
	GenreTelevision				= 'television'			# IMDb (Unsupported)				Trakt (Unsupported)											TMDb (Movie: 10770 - "TV Movie")											TVDb (Unsupported)
	GenreNews					= 'news'				# IMDb (Movie+Show: "News")			Trakt (Show: news - "News")									TMDb (Show: 10763 - "News")													TVDb (Movie+Show: 4 - news - "News")
	GenreSport					= 'sport'				# IMDb (Movie+Show: "Sport")		Trakt (Unsupported)											TMDb (Unsupported)															TVDb (Movie+Show: 21 - sport - "Sport")
	GenreSporting				= 'sporting'			# IMDb (Unsupported)				Trakt (Movie+Show: sporting-event - "Sporting Event")		TMDb (Unsupported)															TVDb (Unsupported)
	GenreTravel					= 'travel'				# IMDb (Unsupported)				Trakt (Unsupported)											TMDb (Unsupported)															TVDb (Movie+Show: 25 - travel - "Travel")
	GenreHoliday				= 'holiday'				# IMDb (Unsupported)				Trakt (Movie+Show: holiday - "Holiday")						TMDb (Unsupported)															TVDb (Unsupported)
	GenreHome					= 'home'				# IMDb (Unsupported)				Trakt (Show: home-and-garden - "Home And Garden")			TMDb (Unsupported)															TVDb (Movie+Show: 7 - home-and-garden - "Home and Garden")
	GenreFood					= 'food'				# IMDb (Unsupported)				Trakt (Unsupported)											TMDb (Unsupported)															TVDb (Movie+Show: 9 - food - "Food")
	GenreTalk					= 'talk'				# IMDb (Movie+Show: "Talk-Show")	Trakt (Show: talk-show - "Talk Show")						TMDb (Show: 10767 - "Talk")													TVDb (Movie+Show: 23 - talk-show - "Talk Show")
	GenreGame					= 'game'				# IMDb (Movie+Show: "Game-Show")	Trakt (Show: game-show - "Game Show")						TMDb (Unsupported)															TVDb (Movie+Show: 8 - game-show - "Game Show")
	GenreAward					= 'award'				# IMDb (Unsupported)				Trakt (Unsupported)											TMDb (Unsupported)															TVDb (Movie+Show: 36 - awards-show - "Awards Show")
	GenreReality				= 'reality'				# IMDb (Movie+Show: "Reality-TV")	Trakt (Show: reality - "Reality")							TMDb (Show: 10764 - "Reality")												TVDb (Movie+Show: 3 - reality - "Reality")
	GenreSoap					= 'soap'				# IMDb (Unsupported)				Trakt (Show: soap - "Soap")									TMDb (Show: 10766 - "Soap")													TVDb (Movie+Show: 1 - soap - "Soap")
	GenrePodcast				= 'podcast'				# IMDb (Unsupported)				Trakt (Unsupported)											TMDb (Unsupported)															TVDb (Movie+Show: 30 - podcast - "Podcast")
	GenreIndie					= 'indie'				# IMDb (Unsupported)				Trakt (Unsupported)											TMDb (Unsupported)															TVDb (Movie+Show: 32 - indie - "Indie")
	GenreSpecial				= 'special'				# IMDb (Unsupported)				Trakt (Show: special-interest - "Special Interest")			TMDb (Unsupported)															TVDb (Unsupported)

	Genres						= None

	Pleasures					= None

	StatusRumored				= 'rumored'				# IMDb (Unsupported)			 			Trakt (Movie: "rumored")				TMDb (Movie: "Rumored")							TVDb (Unsupported)
	StatusPlanned				= 'planned'				# IMDb (Movie+Show: "Announced")			Trakt (Movie+Show: "planned")			TMDb (Movie+Show: "Planned" | Show: 1)			TVDb (Movie: 1 - "Announced")
	StatusScripted				= 'scripted'			# IMDb (Movie+Show: "Script")				Trakt (Unsupported)						TMDb (Unsupported)								TVDb (Unsupported)
	StatusPreproduction			= 'preproduction'		# IMDb (Movie+Show: "Pre-production")		Trakt (Unsupported)						TMDb (Unsupported)								TVDb (Movie: 2 - "Pre-Production")
	StatusProduction			= 'production'			# IMDb (Movie+Show: "Filming")				Trakt (Movie+Show: "in production")		TMDb (Movie+Show: "In Production" | Show: 2)	TVDb (Movie: 3 - "Filming / Post-Production")
	StatusPostproduction		= 'postproduction'		# IMDb (Movie+Show: "Post-production")		Trakt (Movie: "post production")		TMDb (Movie: "Post Production")					TVDb (Movie: 3 - "Filming / Post-Production")
	StatusCompleted				= 'completed'			# IMDb (Movie+Show: "Completed")			Trakt (Unsupported)						TMDb (Unsupported)								TVDb (Movie: 4 - "Completed")
	StatusReleased				= 'released'			# IMDb (Movie+Show: "Released")				Trakt (Movie: "released")				TMDb (Movie: "Released")						TVDb (Movie: 5 - "Released")

	StatusUpcoming				= 'upcoming'			# IMDb (Unsupported)						Trakt (Show: "upcoming")				TMDb (Unsupported)								TVDb (Show: 3 - "Upcoming")
	StatusPiloted				= 'piloted'				# IMDb (Unsupported)						Trakt (Show: "pilot")					TMDb (Show: 5 - "Pilot")						TVDb (Unsupported)
	StatusContinuing			= 'continuing'			# IMDb (Unsupported)						Trakt (Show: "continuing")				TMDb (Unsupported)								TVDb (Show: 1 - "Continuing")
	StatusReturning				= 'returning'			# IMDb (Unsupported)						Trakt (Show: "returning series")		TMDb (Show: 0 - "Returning Series")				TVDb (Unsupported)
	StatusEnded					= 'ended'				# IMDb (Unsupported)						Trakt (Show: "ended")					TMDb (Show: 3 - "Ended")						TVDb (Show: 2 - "Ended")
	StatusCanceled				= 'canceled'			# IMDb (Unsupported)						Trakt (Movie+Show: "canceled")			TMDb (Movie+Show: "Canceled" | Show: 4)			TVDb (Unsupported)

	StatusesPast				= (StatusReleased, StatusEnded, StatusCanceled)
	StatusesPresent				= (StatusPiloted, StatusContinuing, StatusReturning) # Sometimes StatusReturning is used for currently running seasons (present), but sometimes it is also used to indicate a new upcoming season that has not started to air yet (future).
	StatusesFuture				= (StatusRumored, StatusPlanned, StatusScripted, StatusPreproduction, StatusProduction, StatusPostproduction, StatusCompleted, StatusUpcoming)
	StatusesDraft				= (StatusRumored, StatusPlanned, StatusScripted)
	StatusesBusy				= (StatusPreproduction, StatusProduction, StatusPostproduction)

	Status						= {
		StatusRumored			: {'order' : 1,		'label' : 'Rumored'},
		StatusPlanned			: {'order' : 2,		'label' : 'Planned'},
		StatusScripted			: {'order' : 3,		'label' : 'Scripted'},
		StatusPreproduction		: {'order' : 4,		'label' : 'Pre-Production'},
		StatusProduction		: {'order' : 5,		'label' : 'Production'},
		StatusPostproduction	: {'order' : 6,		'label' : 'Post-Production'},
		StatusCompleted			: {'order' : 8,		'label' : 'Completed'},
		StatusReleased			: {'order' : 9,		'label' : 'Released'},
		StatusUpcoming			: {'order' : 7,		'label' : 'Upcoming'},
		StatusPiloted			: {'order' : 10,	'label' : 'Piloted'},
		StatusContinuing		: {'order' : 11,	'label' : 'Continuing'},
		StatusReturning			: {'order' : 12,	'label' : 'Returning'},
		StatusEnded				: {'order' : 13,	'label' : 'Ended'},
		StatusCanceled			: {'order' : 14,	'label' : 'Canceled'},
	}

	AwardAcademyWinner			= 'academywinner'		# Titles + People.
	AwardAcademyNominee			= 'academynominee'		# Titles + People.
	AwardEmmyWinner				= 'emmywinner'			# Titles + People.
	AwardEmmyNominee			= 'emmynominee'			# Titles + People.
	AwardGlobeWinner			= 'globewinner'			# Titles + People.
	AwardGlobeNominee			= 'globenominee'		# Titles + People.
	AwardRazzieWinner			= 'razziewinner'		# Titles.
	AwardRazzieNominee			= 'razzienominee'		# Titles.
	AwardNationalWinner			= 'nationalwinner'		# Titles.

	AwardTop100					= 'top100'				# Titles.
	AwardTop250					= 'top250'				# Titles.
	AwardTop1000				= 'top1000'				# Titles.
	AwardBottom100				= 'bottom100'			# Titles.
	AwardBottom250				= 'bottom250'			# Titles.
	AwardBottom1000				= 'bottom1000'			# Titles.

	AwardPictureWinner			= 'picturewinner'		# Titles.
	AwardPictureNominee			= 'picturenominee'		# Titles.
	AwardDirectorWinner			= 'directorwinner'		# Titles + People
	AwardDirectorNominee		= 'directornominee'		# Titles + People.
	AwardActorWinner			= 'actorwinner'			# People.
	AwardActorNominee			= 'actornominee'		# People.
	AwardActressWinner			= 'actresswinner'		# People.
	AwardActressNominee			= 'actressnominee'		# People.
	AwardSupportorWinner		= 'supportorwinner'		# People.
	AwardSupportorNominee		= 'supportornominee'	# People.
	AwardSupportressWinner		= 'supportresswinner'	# People.
	AwardSupportressNominee		= 'supportressnominee'	# People.

	RatingImdb					= 'imdb'
	RatingTmdb					= 'tmdb'
	RatingTvdb					= 'tvdb'
	RatingTrakt					= 'trakt'
	RatingTvmaze				= 'tvmaze'
	RatingMetacritic			= 'metacritic'
	RatingAverage				= 'average'
	RatingAverageWeighted		= 'averageweighted'
	RatingAverageLimited		= 'averagelimited'
	RatingDefault				= RatingAverageWeighted
	RatingProviders				= [RatingImdb, RatingTmdb, RatingTvdb, RatingTrakt, RatingTvmaze, RatingMetacritic]
	RatingVotes					= 10 # Default vote count if there is a rating by no vote count (eg Metacritic or Tvmaze).

	ProgressAll					= 'all'
	ProgressStarted				= 'started'
	ProgressPartial				= 'partial'
	ProgressConclude			= 'conclude'
	ProgressUnfinished			= 'unfinished'
	ProgressFinished			= 'finished'
	ProgressRewatch				= 'rewatch'
	ProgressRewatching			= 'rewatching'
	ProgressRewatched			= 'rewatched'
	ProgressDefault				= 'default'

	HistoryStream				= 'stream'
	HistoryMovie				= Media.Movie
	HistorySet					= Media.Set
	HistoryShow					= Media.Show
	HistorySeason				= Media.Season
	HistoryEpisode				= Media.Episode

	SetDiscover					= 'discover'
	SetAlphabetic				= 'alphabetic'
	SetArrival					= 'arrival'
	SetPopular					= 'popular'
	SetRandom					= 'random'
	SetSearch					= 'search'

	ListRecommendation			= 'recommendation'
	ListCalendar				= 'calendar'
	ListWatchlist				= 'watchlist'
	ListFavorite				= 'favorite'
	ListRating					= 'rating'
	ListCollection				= 'collection'
	ListHistory					= 'history'
	ListProgress				= 'progress'
	ListHidden					= 'hidden'
	ListCheckin					= 'checkin'
	ListCustom					= 'custom'
	ListPersonal				= 'personal'
	ListLike					= 'like'
	ListComment					= 'comment'
	ListCollaboration			= 'collaboration'
	ListPopular					= 'popular'
	ListTrending				= 'trending'
	ListOfficial				= 'official'
	ListDiscover				= 'discover'
	ListArrival					= 'arrival'			# New arrivals.
	ListQuality					= 'quality'			# High quality.
	ListAward					= 'award'			# Award winners.
	ListReal					= 'real'			# True stories. Do not use "true", since it will be converted to a boolean parameter.
	ListBucket					= 'bucket'			# Bucket list.
	ListMind					= 'mind'			# Mind fucks.
	ListsFavorite				= [ListPersonal, ListLike, ListComment, ListCollaboration, ListRecommendation, ListCalendar, ListWatchlist, ListFavorite, ListCollection, ListRating, ListHistory, ListProgress, ListHidden, ListCustom, ListCheckin]

	PersonDiscover				= 'discover'
	PersonFamous				= 'famous'
	PersonAward					= 'award'
	PersonGender				= 'gender'
	PersonFilmmaker				= 'filmmaker'
	PersonCreator				= 'creator'
	PersonDirector				= 'director'
	PersonCinematographer		= 'cinematographer'
	PersonWriter				= 'writer'
	PersonProducer				= 'producer'
	PersonEditor				= 'editor'
	PersonComposer				= 'composer'
	PersonActor					= 'actor'
	PersonActress				= 'actress'

	GenderMale					= 'male'
	GenderFemale				= 'female'
	GenderNonbinary				= 'nonbinary'
	GenderOther					= 'other'

	ReleaseUnknown				= 'unknown'			# Other unknown release date.
	ReleasePremiere				= 'premiere'		# Premiere release date.
	ReleaseLimited				= 'limited'			# Limited theatrical release date.
	ReleaseTheatrical			= 'theatrical'		# Theatrical release date.
	ReleaseDigital				= 'digital'			# Digital release date.
	ReleasePhysical				= 'physical'		# Physical release date.
	ReleaseTelevision			= 'television'		# Television release date.

	TimeUnknown					= ReleaseUnknown	# Other unknown type release date.
	TimePremiere				= ReleasePremiere	# Premiere release date.
	TimeLimited					= ReleaseLimited	# Limited theatrical release date.
	TimeTheatrical				= ReleaseTheatrical	# Theatrical release date.
	TimeDigital					= ReleaseDigital	# Digital release date.
	TimePhysical				= ReleasePhysical	# Physical release date.
	TimeTelevision				= ReleaseTelevision	# Television release date.
	TimeRelease					= 'release'			# Earliest of any of the available times, preferring home release dates above cinema dates.
	TimeDebut					= 'debut'			# Earliest of any of the available times (the "premiered" Kodi attribute is typically NOT the premiere date, but rather the limited/theatrical date, or even the digital date if there was no theatrical release).
	TimeLaunch					= 'launch'			# Earliest of the limited/theatrical or digital/physical/television release dates (some smaller movies are sometimes released digitially first, and months later in theaters).
	TimeTheater					= 'theater'			# Earliest of the premiere/limited/theatrical.
	TimeCinema					= 'cinema'			# Earliest of the limited/theatrical.
	TimeHome					= 'home'			# Earliest of the digital/physical/television release dates.
	TimeAdded					= 'added'			# Trakt added date by the user.
	TimeUpdated					= 'updated'			# Trakt update date by the user.
	TimeWatched					= 'watched'			# Trakt watched date by the user.
	TimeRewatched				= 'rewatched'		# Trakt rewatched date by the user.
	TimePaused					= 'paused'			# Trakt scrobble paused date by the user.
	TimeExpired					= 'expired'			# Trakt scrobble expiration date by the user.
	TimeRated					= 'rated'			# Trakt rated date by the user.
	TimeCollected				= 'collected'		# Trakt collected date by the user.
	TimeUsed					= 'used'			# Latests of the watched/rewatched/paused/rated/collected user dates, or added/updated dates if none of the previous ones are available.
	TimeSerie					= 'serie'			# Deprecated - TimeSerie can be removed after 2025-09
	TimeEnded					= 'ended'			# The time of the last episode in a season.
	TimeCustom					= 'custom'			# Internal. Used to indicate a season or episode time within a show object. Or a more recent release time for movies/shows for barebone metadata before the detailed metadata is retrieved.
	TimesRelease				= [TimePhysical, TimeDigital, TimeTelevision, TimeTheatrical, TimeLimited, TimePremiere, TimeUnknown]
	TimesDebut					= [TimePremiere, TimeLimited, TimeTheatrical, TimeDigital, TimePhysical, TimeTelevision, TimeUnknown]
	TimesLaunch					= [TimeLimited, TimeTheatrical, TimeDigital, TimePhysical, TimeTelevision]
	TimesTheater				= [TimePremiere, TimeLimited, TimeTheatrical]
	TimesCinema					= [TimeLimited, TimeTheatrical]
	TimesHome					= [TimeDigital, TimePhysical, TimeTelevision]
	TimesTrakt					= [TimeAdded, TimeUpdated, TimeWatched, TimeRewatched, TimePaused, TimeExpired, TimeRated, TimeCollected]

	SortNone					= None
	SortInternal				= 'internal'		# Sort by a custom "sort" attribute. Should be numeric value.
	SortShuffle					= 'shuffle'			# Randomize items.

	SortGlobal					= 'global'			# Sort by global relevance, by combining the rating, votes, and release date.
	SortLocal					= 'local'			# Sort by local/user relevance, by combining the last watched activity and release date.
	SortRewatch					= 'rewatch'			# Sort by rewatch relevance, that is the rewatch potential when watched a long time ago with a high rating.

	SortBest					= 'best'			# Sort from best to worst rating.
	SortWorst					= 'worst'			# Sort from worst to best rating.
	SortPopular					= 'popular'			# Sort from most to least number of votes.
	SortUnpopular				= 'unpopular'		# Sort from least to most number of votes.
	SortNewest					= 'newest'			# Sort from newest to oldest launch date.
	SortOldest					= 'oldest'			# Sort from oldest to newest launch date.
	SortLatest					= 'latest'			# Sort from newest to oldest home date.
	SortEarliest				= 'earliest'		# Sort from oldest to newest home date.
	SortTitle					= 'title'			# Sort titles alphabetically from A to Z.

	SortArticle					= 'article'			# Sort by title including articles.
	SortArticleless				= 'articleless'		# Sort by title excluding articles.
	SortWeighted				= 'weighted'		# Weighted Bayes estimates for rating and votes.
	SortRating					= 'rating'			# Average rating cast.
	SortUser					= 'user'			# Rating cast by user.
	SortVotes					= 'votes'			# Number of votes cast.
	SortPremiere				= TimePremiere		# Premiere release date.
	SortLimited					= TimeLimited		# Limited theatrical release date.
	SortTheatrical				= TimeTheatrical	# Theatrical release date.
	SortDigital					= TimeDigital		# Digital release date.
	SortPhysical				= TimePhysical		# Physical release date.
	SortTelevision				= TimeTelevision	# Television release date.
	SortDebut					= TimeDebut			# Earliest of any of the available times.
	SortLaunch					= TimeLaunch		# Earliest of the limited/theatrical/digital/physical/television release dates.
	SortTheater					= TimeTheater		# Earliest of the premiere/limited/theatrical.
	SortCinema					= TimeCinema		# Earliest of the limited/theatrical.
	SortHome					= TimeHome			# Earliest of the digital/physical/television release dates.
	SortAdded					= TimeAdded			# Trakt added date by the user.
	SortUpdated					= TimeUpdated		# Trakt update date by the user.
	SortWatched					= TimeWatched		# Trakt watched date by the user.
	SortRewatched				= TimeRewatched		# Trakt rewatched date by the user.
	SortPaused					= TimePaused		# Trakt scrobble paused date by the user.
	SortExpired					= TimeExpired		# Trakt scrobble expiration date by the user.
	SortRated					= TimeRated			# Trakt rated date by the user.
	SortCollected				= TimeCollected		# Trakt collected date by the user.
	SortUsed					= TimeUsed			# Latests of the watched/rewatched/paused/rated/collected user dates, or added/updated dates if none of the previous ones are available..

	OrderNone					= None
	OrderAscending				= 'asc'
	OrderDescending				= 'desc'
	OrderDefault				= {
		SortInternal			: OrderDescending,
		SortShuffle				: OrderAscending,
		SortGlobal				: OrderDescending,
		SortLocal				: OrderDescending,
		SortRewatch				: OrderDescending,
		SortArticle				: OrderAscending,
		SortArticleless			: OrderAscending,
		SortWeighted			: OrderDescending,
		SortRating				: OrderDescending,
		SortUser				: OrderDescending,
		SortVotes				: OrderDescending,
		SortPremiere			: OrderDescending,
		SortLimited				: OrderDescending,
		SortTheatrical			: OrderDescending,
		SortDigital				: OrderDescending,
		SortPhysical			: OrderDescending,
		SortTelevision			: OrderDescending,
		SortDebut				: OrderDescending,
		SortLaunch				: OrderDescending,
		SortTheater				: OrderDescending,
		SortCinema				: OrderDescending,
		SortHome				: OrderDescending,
		SortAdded				: OrderDescending,
		SortUpdated				: OrderDescending,
		SortWatched				: OrderDescending,
		SortRewatched			: OrderDescending,
		SortPaused				: OrderDescending,
		SortExpired				: OrderDescending,
		SortRated				: OrderDescending,
		SortCollected			: OrderDescending,
		SortUsed				: OrderDescending,

		SortBest				: (OrderDescending,	SortRating),
		SortWorst				: (OrderAscending,	SortRating),
		SortPopular				: (OrderDescending,	SortVotes),
		SortUnpopular			: (OrderAscending,	SortVotes),
		SortNewest				: (OrderDescending,	SortLaunch),
		SortOldest				: (OrderAscending,	SortLaunch),
		SortLatest				: (OrderDescending,	SortHome),
		SortEarliest			: (OrderAscending,	SortHome),
		SortTitle				: (OrderAscending,	SortArticle),
	}

	FilterDuplicate				= 'duplicate'
	FilterNumber				= 'number'
	FilterProgress				= 'progress'
	FilterNiche					= 'niche'
	FilterCertificate			= 'certificate'
	FilterAudience				= 'audience'
	FilterKid					= 'kid'
	FilterTeen					= 'teen'
	FilterAdult					= 'adult'
	FilterEdition				= 'edition'
	FilterGenre					= 'genre'
	FilterLanguage				= 'language'
	FilterCountry				= 'country'
	FilterRating				= 'rating'
	FilterVotes					= 'votes'
	FilterQuality				= 'quality'
	FilterPopularity			= 'popularity'
	FilterTime					= 'time'
	FilterPartial				= 'partial'

	# The Oscars define a short film as 40 minutes or less. But some films that one might consider as short, seem to go up to 60 minutes.
	# IMDb API docs: Any theatrical film or made-for-video title with a running time of less than 45 minutes, i.e., 44 minutes or less, or any TV series or TV movie with a running time of less than 22 minutes, i.e. 21 minutes or less.
	ShortMinimum				= 60			# 1 minute. Minimum duration which is considered to be a short film.
	ShortAverage				= 1800 			# 30 minutes. Duration which is considered to be an average short film, but still allow longer shorts to be listed under the Movies section (eg: The Wonderful Story of Henry Sugar).
	ShortStandard				= 2400 			# 40 minutes. Duration which is considered to be a standard short film.
	ShortMaximum				= 3600 			# 60 minutes. Duration which is considered to be a short film, listed under the Shorts section.

	CustomLimit					= 'limit'
	CustomSort					= 'sort'
	CustomOrder					= 'order'

	DummyString					= 'zzzzzzzzzz'
	DummyNumber					= 9999999999
	DummyTime					= 1

	DiscrepancyDisabbled		= 0
	DiscrepancyLenient			= 1
	DiscrepancyStrict			= 2

	TimeNewMovie				= 21600 # 6 hours.
	TimeNewShow					= 82800 # 23 hours. Make this a bit higher, since often episodes leak a day before, or the timezone difference between the release country and the user's country.
	TimeFuture					= 86400 # 1 day.
	TimeOldest					= 1890 # First movie released in 1888. Oldest movie on IMDb is 1894.

	PropertySelect				= 'GaiaSelect'
	PropertyProgress			= 'GaiaProgress'

	SubmenuParameter			= 'submenu'
	SubmenuSerie				= 'serie'		# Submenu under the Series menu.
	SubmenuSequential			= 'sequential'	# Submenu under the Absolute menu.
	SubmenuAbsolute				= 'absolute'	# Currently not used, due to discrepancies. Use SubmenuSequential instead.
	SubmenuEpisode				= 'episode'		# Submenu under the Progress menu.

	Topics						= None
	Moods						= None
	Ages						= None
	Qualities					= None
	Regions						= None
	Instance					= None
	Lock						= Lock()

	###################################################################
	# CONSTRUCTOR
	###################################################################

	def __init__(self):
		self.mConcurrency = {}
		self.mDeveloper = System.developerVersion()
		self.mKodiNew = System.versionKodiMinimum(version = 20)

		self.mSettingsDetail = Settings.getString('metadata.general.detail').lower()
		self.mSettingsExternal = not Settings.getString('metadata.general.external') == Translation.string(32302) # Enable by default if user has a different language set.
		self.mSettingsLanguage = Language.settingsCustom('metadata.region.language')
		self.mSettingsCountry = Country.settings('metadata.region.country') # Important for timeGenerate() for this variable to be None if it is left on "Automatic".

		self.mMetaAllowed = ['genre', 'country', 'year', 'episode', 'season', 'sortepisode', 'sortseason', 'episodeguide', 'showlink', 'top250', 'setid', 'tracknumber', 'rating', 'userrating', 'watched', 'playcount', 'overlay', 'cast', 'castandrole', 'director', 'mpaa', 'plot', 'plotoutline', 'title', 'originaltitle', 'sorttitle', 'duration', 'studio', 'tagline', 'writer', 'tvshowtitle', 'premiered', 'status', 'set', 'setoverview', 'tag', 'imdbnumber', 'code', 'aired', 'credits', 'lastplayed', 'album', 'artist', 'votes', 'path', 'trailer', 'dateadded', 'mediatype', 'dbid']
		self.mMetaNonzero = ['genre', 'country', 'year', 'episodeguide', 'showlink', 'top250', 'cast', 'castandrole', 'director', 'mpaa', 'plot', 'plotoutline', 'title', 'originaltitle', 'sorttitle', 'duration', 'studio', 'tagline', 'writer', 'tvshowtitle', 'premiered', 'status', 'set', 'setoverview', 'tag', 'imdbnumber', 'aired', 'credits', 'path', 'trailer', 'dateadded', 'mediatype']
		self.mMetaExclude = ['userrating', 'watched', 'playcount', 'overlay', 'duration', 'title']
		self.mMetaFunctions = {
			'genre'			: 'setGenres',
			'country'		: 'setCountries',
			'year'			: 'setYear',
			'episode'		: 'setEpisode',
			'season'		: 'setSeason',
			'sortepisode'	: 'setSortEpisode',
			'sortseason'	: 'setSortSeason',
			'episodeguide'	: 'setEpisodeGuide',
			'showlink'		: 'setShowLinks',
			'top250'		: 'setTop250',
			'setid'			: 'setSetId',
			'tracknumber'	: 'setTrackNumber',
			'rating'		: 'setRating',
			'userrating'	: 'setUserRating',
			'watched'		: None,
			'playcount'		: 'setPlaycount',
			'overlay'		: None,
			'cast'			: None,
			'castandrole'	: None,
			'director'		: 'setDirectors',
			'mpaa'			: 'setMpaa',
			'plot'			: 'setPlot',
			'plotoutline'	: 'setPlotOutline',
			'title'			: 'setTitle',
			'originaltitle'	: 'setOriginalTitle',
			'sorttitle'		: 'setSortTitle',
			'duration'		: 'setDuration',
			'studio'		: 'setStudios',
			'tagline'		: 'setTagLine',
			'writer'		: 'setWriters',
			'tvshowtitle'	: 'setTvShowTitle',
			'premiered'		: 'setPremiered',
			'status'		: 'setTvShowStatus',
			'set'			: 'setSet',
			'setoverview'	: 'setSetOverview',
			'tag'			: 'setTags',
			'imdbnumber'	: 'setIMDBNumber',
			'code'			: 'setProductionCode',
			'aired'			: 'setFirstAired',
			'credits'		: None,
			'lastplayed'	: 'setLastPlayed',
			'album'			: 'setAlbum',
			'artist'		: 'setArtists',
			'votes'			: 'setVotes',
			'path'			: 'setPath',
			'trailer'		: 'setTrailer',
			'dateadded'		: 'setDateAdded',
			'mediatype'		: 'setMediaType',
			'dbid'			: 'setDbId',
		}

		self.mTimeCurrent = Time.timestamp()
		self.mTimeClock = None

		self.mOriginGaia = System.originGaia()
		self.mOriginAddon = System.originAddon()
		self.mOriginExternal = System.originExternal()

		self.mPlayback = None
		self.mPlayable = not self.mOriginAddon
		self.mContext = Context.enabled()

		self.mContentDocu = Settings.getInteger('general.content.docu')
		self.mContentShort = Settings.getInteger('general.content.short')
		self.mContentFamily = Settings.getInteger('general.content.family')
		self.mContentAnima = Settings.getInteger('general.content.anima')
		self.mContentAnime = Settings.getInteger('general.content.anime')
		self.mContentDonghua = Settings.getInteger('general.content.donghua')

		hide = Settings.getInteger('menu.general.watched')
		self.mHideRelease = hide == 1
		self.mHideAll = hide == 2

		self.mPageMovie = Settings.getInteger('menu.page.movie')
		self.mPageShow = Settings.getInteger('menu.page.show')
		self.mPageSerie = Settings.getInteger('menu.page.serie')
		self.mPageAbsolute = Settings.getInteger('menu.page.absolute')
		self.mPageEpisode = Settings.getInteger('menu.page.episode')
		self.mPageSubmenu = Settings.getInteger('menu.page.submenu')
		self.mPageSearch = Settings.getInteger('menu.page.search')
		self.mPageProgress = Settings.getInteger('menu.page.progress')
		self.mPageMixed = Settings.getInteger('menu.page.mixed')

		self.mSleepyEnabled = Settings.getBoolean('menu.general.sleepy')
		self.mSleepyLimit = min(self.mPageSubmenu - 1, Settings.getInteger('menu.general.sleepy.limit')) if self.mSleepyEnabled else 0
		self.mSleepyDuration = Settings.getCustom('menu.general.sleepy.duration') if self.mSleepyEnabled else 0

		self.mShowSubmenu = Settings.getBoolean('menu.show.submenu')
		self.mShowFlat = Settings.getBoolean('menu.show.flat')
		self.mShowSerie = 0 if self.mShowFlat else Settings.getInteger('menu.show.serie')
		self.mShowAbsolute = 0 if self.mShowFlat else Settings.getInteger('menu.show.absolute')

		self.mShowInterleave = Settings.getBoolean('menu.show.interleave')
		self.mShowInterleaveUnofficial = {
			None : Settings.getInteger('menu.show.interleave.unofficial'),
			True : {0 : None, 1 : True, 2 : True}, # Progress submenus (fewer specials).
			False : {0 : None, 1 : None, 2 : True}, # Series menus (more specials).
		}
		self.mShowInterleaveExtra = {
			None : Settings.getInteger('menu.show.interleave.extra'),
			True : {0 : None, 1 : False, 2 : False, 3 : True}, # Progress submenus (fewer specials).
			False : {0 : None, 1 : None, 2 : False, 3 : True}, # Series menus (more specials).
		}
		self.mShowInterleaveDuration = {
			None : Settings.getInteger('menu.show.interleave.duration'),  # Automatic: 0.0 for series menus, 0.5 for other interleaved submenus (eg Trakt progress list).
			True : {0 : 0.0, 1 : 0.5, 2 : 0.25, 3 : 0.5}, # Progress submenus (fewer specials).
			False : {0 : 0.0, 1 : 0.0, 2 : 0.25, 3 : 0.5}, # Series menus (more specials).
		}

		self.mShowSpecial = Settings.getInteger('menu.show.special')
		self.mShowSpecialSeason = Settings.getBoolean('menu.show.special.season') if self.mShowSpecial else False
		self.mShowSpecialEpisode = Settings.getBoolean('menu.show.special.episode') if self.mShowSpecial else False

		self.mShowFuture = Settings.getBoolean('menu.show.future')
		self.mShowFutureSeason = Settings.getBoolean('menu.show.future.season') if self.mShowFuture else False
		self.mShowFutureEpisode = Settings.getBoolean('menu.show.future.episode') if self.mShowFuture else False

		self.mShowBonus = Settings.getBoolean('menu.show.bonus')
		self.mShowBonusRecap = Settings.getBoolean('menu.show.bonus.recap') if self.mShowBonus else False
		self.mShowBonusExtra = Settings.getBoolean('menu.show.bonus.extra') if self.mShowBonus else False

		self.mShowCountEnabled = Settings.getBoolean('menu.show.count')
		self.mShowCountSpecial = Settings.getBoolean('menu.show.count.special')
		self.mShowCountUnwatched = Settings.getBoolean('menu.show.count.unwatched')
		self.mShowCountLimit = Settings.getBoolean('menu.show.count.limit')

		self.mShowDiscrepancy = Settings.getInteger('menu.show.discrepancy')

		self.mLabelStyle = Settings.getInteger('label.general.style')
		self.mLabelStyleRelease = self.mLabelStyle == 1 or self.mLabelStyle == 2
		self.mLabelStyleEpisode = self.mLabelStyle == 1 or self.mLabelStyle == 3
		self.mLabelStyleColor = Format.colorDisabled() if Settings.getBoolean('label.general.style.color') else None
		self.mLabelStyleColorLight = Format.colorMix(self.mLabelStyleColor, Format.colorWhite(), ratio = 0.7) if self.mLabelStyleColor else None
		self.mLabelStyleColorLighter = Format.colorMix(self.mLabelStyleColor, Format.colorWhite(), ratio = 0.4) if self.mLabelStyleColor else None

		self.mLabelForce = Settings.getInteger('label.general.force')
		if self.mLabelForce == 2: self.mLabelForce = not Skin.supportLabelCustom() # Do not use Skin.supportLabelCustom(default = True), since essentially all skins use the title instead of the label.
		else: self.mLabelForce = bool(self.mLabelForce)

		self.mLabelDetailEnabled = Settings.getBoolean('label.detail.enabled')

		self.mLabelMediaEnabled = self.mLabelDetailEnabled and Settings.getBoolean('label.detail.media')
		self.mLabelMediaMenu = Detail.settingsMediaMenu()
		self.mLabelMediaFormat = Detail.settingsMediaFormat(prepare = True)

		self.mLabelActivityEnabled = self.mLabelDetailEnabled and Settings.getBoolean('label.detail.activity')
		self.mLabelActivityMenu = Detail.settingsActivityMenu()
		self.mLabelActivityFormat = Detail.settingsActivityFormat(prepare = True)

		self.mLabelPlayEnabled = Settings.getBoolean('label.detail.activity.play')
		self.mLabelPlayMedia = Detail.settingsActivityPlay() if self.mLabelPlayEnabled else None
		self.mLabelPlayThreshold = Settings.getInteger('label.detail.activity.play.threshold')

		self.mLabelProgressEnabled = Settings.getBoolean('label.detail.activity.progress')
		self.mLabelProgressMedia = Detail.settingsActivityProgress() if self.mLabelProgressEnabled else None
		self.mLabelProgressFormat = Settings.getInteger('label.detail.activity.progress.format')

		self.mLabelRatingEnabled = Settings.getBoolean('label.detail.activity.rating')
		self.mLabelRatingMedia = Detail.settingsActivityRating() if self.mLabelRatingEnabled else None
		self.mLabelRatingFormat = Settings.getInteger('label.detail.activity.rating.format')

		self.mLabelAirEnabled = Settings.getBoolean('label.detail.activity.air')
		self.mLabelAirMedia = Detail.settingsActivityAir() if self.mLabelAirEnabled else None
		self.mLabelAirZone = Settings.getInteger('label.detail.activity.air.zone') if self.mLabelAirEnabled else None
		self.mLabelAirFormat = Settings.getInteger('label.detail.activity.air.format') if self.mLabelAirEnabled else None
		self.mLabelAirDay = Settings.getInteger('label.detail.activity.air.day') if self.mLabelAirEnabled else None
		self.mLabelAirTime = Settings.getInteger('label.detail.activity.air.time') if self.mLabelAirEnabled else None

		self.mIconEnabled = Settings.getBoolean('menu.icon.enabled')
		self.mIconPlay = self.mIconEnabled and Settings.getBoolean('menu.icon.play')
		self.mIconProgress = self.mIconEnabled and Settings.getBoolean('menu.icon.progress')
		self.mIconRating = self.mIconEnabled and Settings.getBoolean('menu.icon.rating')
		self.mIconCount = self.mIconEnabled and self.mShowCountEnabled and Settings.getBoolean('menu.icon.count')
		self.mIconDuration = self.mIconEnabled and Settings.getBoolean('menu.icon.duration')
		self.mIconDate = self.mIconEnabled and Settings.getBoolean('menu.icon.date')
		self.mIconCompany = MetaCompany.settingsMode()

		self.mIconExclude = []
		if not self.mIconPlay: self.mIconExclude.append('playcount')
		if not self.mIconRating: self.mIconExclude.append('rating')
		if not self.mIconDuration: self.mIconExclude.append('duration')
		if not self.mIconDate: self.mIconExclude.extend(['premiered', 'aired'])
		if self.mIconCompany == MetaCompany.ModeDisabled: self.mIconExclude.append('studio')

		self.mDirectory = Directory()

		self.mThemeFanart = Theme.fanart()
		self.mThemeBanner = Theme.banner()
		self.mThemePoster = Theme.poster()
		self.mThemeThumb = Theme.thumbnail()
		self.mThemeMoreBanner = Theme.moreBanner()
		self.mThemeMorePoster = Theme.morePoster()
		self.mThemeMoreThumb = Theme.moreThumbnail()

		ratingsUser = [False, None, True]
		ratingsMovie = [MetaTools.RatingImdb, MetaTools.RatingTmdb, MetaTools.RatingTrakt, MetaTools.RatingMetacritic, MetaTools.RatingAverage, MetaTools.RatingAverageWeighted, MetaTools.RatingAverageLimited]
		ratingsShow = [MetaTools.RatingImdb, MetaTools.RatingTmdb, MetaTools.RatingTrakt, MetaTools.RatingTvmaze, MetaTools.RatingAverage, MetaTools.RatingAverageWeighted, MetaTools.RatingAverageLimited]

		self.mRatingMovieMain = MetaTools.RatingDefault
		try: self.mRatingMovieMain = ratingsMovie[Settings.getInteger('metadata.rating.movie')]
		except: self.mRatingMovieMain = MetaTools.RatingDefault
		try: self.mRatingMovieFallback = ratingsMovie[Settings.getInteger('metadata.rating.movie.fallback')]
		except: self.mRatingMovieFallback = MetaTools.RatingDefault
		try: self.mRatingMovieUser = ratingsUser[Settings.getInteger('metadata.rating.movie.user')]
		except: self.mRatingMovieUser = None

		self.mRatingShowMain = MetaTools.RatingDefault
		try: self.mRatingShowMain = ratingsShow[Settings.getInteger('metadata.rating.show')]
		except: self.mRatingShowMain = MetaTools.RatingDefault
		try: self.mRatingShowFallback = ratingsShow[Settings.getInteger('metadata.rating.show.fallback')]
		except: self.mRatingShowFallback = MetaTools.RatingDefault
		try: self.mRatingShowUser = ratingsUser[Settings.getInteger('metadata.rating.show.user')]
		except: self.mRatingShowUser = None

	# Use a singleton, since it is more efficient to initialize the settings and other variables only once.
	# Especially if the functions are called multiple times in a loop.
	@classmethod
	def instance(self):
		if MetaTools.Instance is None:
			MetaTools.Lock.acquire()
			if MetaTools.Instance is None: MetaTools.Instance = MetaTools()
			MetaTools.Lock.release()
		return MetaTools.Instance

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True, full = True):
		# Reset values like self.mTimeCurrent and self.mOriginXXX.
		MetaTools.Instance = None

		if settings:
			MetaTools.Topics = None
			MetaTools.Moods = None
			MetaTools.Ages = None
			MetaTools.Regions = None

		if full:
			from lib.meta.cache import MetaCache
			from lib.meta.image import MetaImage
			from lib.meta.service import MetaService
			from lib.meta.services.tvdb import MetaTvdb as MetaTvdbService
			from lib.meta.providers.fanart import MetaFanart
			from lib.meta.providers.imdb import MetaImdb
			from lib.meta.providers.tmdb import MetaTmdb
			from lib.meta.providers.tvdb import MetaTvdb
			from lib.meta.providers.trakt import MetaTrakt

			MetaCache.reset(settings = settings)
			MetaImage.reset(settings = settings)
			MetaService.reset(settings = settings)
			MetaTvdbService.reset(settings = settings)
			MetaFanart.reset(settings = settings)
			MetaImdb.reset(settings = settings)
			MetaTmdb.reset(settings = settings)
			MetaTvdb.reset(settings = settings)
			MetaTrakt.reset(settings = settings)

	###################################################################
	# SETTINGS
	###################################################################

	@classmethod
	def settingsInitialize(self):
		self.settingsExternalInitialize()

	def settingsLanguage(self):
		return self.mSettingsLanguage

	def settingsCountry(self):
		return self.mSettingsCountry

	def settingsContentDocu(self, level = None):
		if level is None: return self.mContentDocu
		else: return self.mContentDocu >= level

	def settingsContentShort(self, level = None):
		if level is None: return self.mContentShort
		else: return self.mContentShort >= level

	def settingsContentFamily(self, level = None):
		if level is None: return self.mContentFamily
		else: return self.mContentFamily >= level

	def settingsContentAnima(self, level = None):
		if level is None: return self.mContentAnima
		else: return self.mContentAnima >= level

	def settingsContentAnime(self, level = None):
		if level is None: return self.mContentAnime
		else: return self.mContentAnime >= level

	def settingsContentDonghua(self, level = None):
		if level is None: return self.mContentDonghua
		else: return self.mContentDonghua >= level

	def settingsSleepy(self):
		return self.mSleepyEnabled

	def settingsSleepyLimit(self):
		return self.mSleepyLimit

	def settingsSleepyDuration(self):
		return self.mSleepyDuration

	def settingsPageMovie(self):
		return self.mPageMovie

	def settingsPageShow(self):
		return self.mPageShow

	def settingsPageSerie(self):
		return self.mPageSerie

	def settingsPageAbsolute(self):
		return self.mPageAbsolute

	def settingsPageEpisode(self):
		return self.mPageEpisode

	def settingsPageSubmenu(self):
		return self.mPageSubmenu

	def settingsPageSearch(self):
		return self.mPageSearch

	def settingsPageProgress(self):
		return self.mPageProgress

	def settingsPageMixed(self):
		return self.mPageMixed

	def settingsShowFlat(self):
		return self.mShowFlat

	def settingsShowSerie(self):
		return self.mShowSerie

	def settingsShowAbsolute(self):
		return self.mShowAbsolute

	def settingsShowInterleave(self):
		return self.mShowInterleave

	# If reduce (True/False), then returns: True = strict, None = disabled.
	def settingsShowInterleaveUnofficial(self, reduce = None):
		interleave = self.mShowInterleaveUnofficial[None]
		return self.mShowInterleaveUnofficial[reduce][interleave]

	# If reduce (True/False), then returns: True = strict, False = lenient, None = disabled.
	def settingsShowInterleaveExtra(self, reduce = None):
		interleave = self.mShowInterleaveExtra[None]
		return self.mShowInterleaveExtra[reduce][interleave]

	def settingsShowInterleaveDuration(self, reduce = None):
		interleave = self.mShowInterleaveDuration[None]
		return self.mShowInterleaveDuration[reduce][interleave]

	def settingsShowSpecial(self):
		return self.mShowSpecial

	def settingsShowSpecialSeason(self):
		return self.mShowSpecialSeason

	def settingsShowSpecialEpisode(self):
		return self.mShowSpecialEpisode

	def settingsShowDiscrepancy(self):
		return self.mShowDiscrepancy

	def settingsDetail(self, level = False, reload = False):
		if reload: self.mSettingsDetail = Settings.getString('metadata.general.detail').lower()
		if level:
			try: return MetaTools.Details.index(self.mSettingsDetail)
			except: return 1
		else:
			return self.mSettingsDetail

	@classmethod
	def settingsDetailSet(self, detail):
		Settings.set('metadata.general.detail', detail.capitalize())
		self.instance().settingsDetail(reload = True)

	@classmethod
	def settingsDetailShow(self, settings = False):
		from lib.modules.window import WindowMetaDetail
		WindowMetaDetail.show(wait = True)
		if settings: Settings.launch(id = 'metadata.general.detail')

	@classmethod
	def settingsPreloadShow(self, clean = False, settings = False):
		from lib.modules.window import WindowMetaPreload
		WindowMetaPreload.show(clean = clean, wait = True)
		if settings: Settings.launch(id = 'metadata.general.preload')

	def settingsExternal(self):
		return self.mSettingsExternal

	@classmethod
	def settingsExternalSet(self, enabled = True):
		Settings.set('metadata.general.external', Translation.string(32301 if enabled else 32302))

	@classmethod
	def settingsExternalInitialize(self):
		from lib.modules.tools import Extension
		if not Extension.installed(id = Extension.IdGaiaMetadata):
			Settings.set('metadata.general.external', Translation.string(35859))

	@classmethod
	def settingsExternalHas(self):
		return not Settings.defaultIs('metadata.general.external')

	@classmethod
	def settingsExternalShow(self, settings = False):
		from lib.modules.window import WindowMetaExternal
		WindowMetaExternal.show(wait = True)
		if settings: Settings.launch(id = 'metadata.general.external')

	###################################################################
	# CONCURRENCY
	##################################################################

	# Kodi can run out of threads if we load the Trakt show arrivals list the first time.
	# Too many sub-threads are created to retrieve shows, seasons, and episodes, all within the same execution.
	# hierarchical: retrieve a list of episodes from different shows, each of them retrieving their own season and show metadata.
	def concurrency(self, media = None, hierarchical = False):
		id = str(media) + '_' + str(hierarchical)
		if not id in self.mConcurrency:
			tasks = Pool.settingMetadata()
			if hierarchical:
				from lib.modules.tools import Hardware
				adjust = Math.scale(Hardware.performanceRating(), fromMinimum = 0, fromMaximum = 1, toMinimum = 0.6, toMaximum = 0.9)
				tasks = max(10, tasks * adjust)
			self.mConcurrency[id] = max(3, int(tasks))
		return self.mConcurrency[id]

	###################################################################
	# GENERAL
	##################################################################

	@classmethod
	def base(self, items, media = None):
		single = not Tools.isArray(items)
		if single: items = [items]

		attributesGeneral = ['niche', MetaTools.ProviderImdb, MetaTools.ProviderTmdb, MetaTools.ProviderTvdb, MetaTools.ProviderTrakt]
		attributesSeason = ['season', 'number']
		attributesEpisode = ['season', 'episode', 'number']

		result = []
		for item in items:
			mediad = media or item.get('media')
			base = {'media' : mediad}

			for i in attributesGeneral: base[i] = item.get(i)
			if Media.isSeason(mediad):
				for i in attributesSeason: base[i] = item.get(i)
			if Media.isEpisode(mediad):
				for i in attributesEpisode: base[i] = item.get(i)

			result.append(base)

		return result[0] if single else result

	def _playback(self):
		# NB: Only create the Playback instance here and not in the constructor.
		# Since Playback's constructor creates a MetaManager instance, which in turn creates a MetaTools instance in its constructor.
		# Hence, a circular instance creation, causing Kodi to freeze.
		# Update: a MetaManager instance is not created in Playback's constructor anymore, so technically not needed anymore. But still keep here, to avoid unnecessary Playback instance creation if it is not needed.
		if self.mPlayback is None:
			from lib.modules.playback import Playback
			self.mPlayback = Playback.instance()
		return self.mPlayback

	def _clock(self):
		# Do not initialize this in the constuctor, since it can take 20-30 ms, since it imports a module.
		# Only create if actually needed.
		if self.mTimeClock is None: self.mTimeClock = Time.format(timestamp = self.mTimeCurrent, format = Time.FormatTime, local = True)
		return self.mTimeClock

	###################################################################
	# NETWORK
	##################################################################

	# Create a "Accept-Language" HTTP header, to return metadata in a specifc language.
	# Eg: IMDb uses the public IP address (eg: VPN) if this header is not set, and might return some titles in another unwanted language.
	def headerLanguage(self, language = None, country = None, weighted = True, wildcard = True, structured = True):
		if language is None:
			language = []
			language.append(self.settingsLanguage())
			language.extend(Language.settingsCode())
		elif language and not Tools.isArray(language):
			language = [language]
		language = Tools.listUnique([i for i in language if i])

		if country is None:
			country = self.settingsCountry()
		elif country and not Tools.isArray(country):
			country = [country]

		return Networker.headersAcceptLanguage(language = language, country = country, weighted = weighted, wildcard = wildcard, structured = structured)

	###################################################################
	# MEDIA
	###################################################################

	def media(self, metadata, media = None, mixed = False):
		try:
			if media: return media # Avoid length code below.
			elif not metadata and not media: return Media.Unknown

			if Tools.isArray(metadata): metadata = metadata[0]

			if not media: media = metadata.get('media') or metadata.get('temp', {}).get('media')
			if media:
				if mixed and Media.isSerie(media): return Media.Show
				else: return media # Avoid length code below.

			if metadata.get('tvshowtitle') or not metadata.get('season') is None or not metadata.get('episode') is None:
				if mixed: return Media.Show
				elif not metadata.get('episode') is None: return Media.Episode
				elif not metadata.get('season') is None: return Media.Season
				else: return Media.Show
			elif metadata.get('title') and (metadata.get('mpaa') or '').lower().startswith('tv'):
				if mixed: return Media.Show
				elif not metadata.get('episode') is None: return Media.Episode
				elif not metadata.get('season') is None: return Media.Season
				else: return Media.Show
			elif metadata.get('title') and metadata.get('part') and not Media.isMovie(media):
				return Media.Set
			elif metadata.get('title') and not Media.isSet(media) and not Media.isList(media):
				return Media.Movie
			elif metadata.get('name'):
				if not Media.isCompany(media) and (metadata.get('profession') or metadata.get('gender') or metadata.get('birth') or metadata.get('image')): return Media.Person
				elif not Media.isPerson(media): return Media.Company
		except: Logger.error()
		return Media.Unknown

	@classmethod
	def slug(self, title, year = None, separator = '-', symbol = None, lower = True):
		try:
			slug = ''
			try:
				for char in title:
					if char == ' ': slug += separator
					elif char.isalnum(): slug += char.lower() if lower else char
					elif symbol: slug += symbol
			except: pass
			if slug:
				if year: slug += separator + str(year)
				if separator: slug = Regex.replace(data = slug, expression = '(\%s{2,})' % separator, replacement = separator, group = None, all = True).strip(separator)
				if symbol and not symbol == separator: slug = Regex.replace(data = slug, expression = '(\%s{2,})' % symbol, replacement = symbol, group = None, all = True).strip(symbol)
			if slug: return slug
		except: Logger.error()
		return None

	###################################################################
	# NICHE
	###################################################################

	def niche(self, metadata, media = None, niche = None, show = None, pack = None, seasons = None, episodes = None):
		try:
			if not metadata and not niche: return Media.Unknown
			if Tools.isArray(metadata): metadata = metadata[0]

			if not media: media = metadata.get('media') or metadata.get('temp', {}).get('media')
			if not niche:
				niche = metadata.get('niche') or metadata.get('temp', {}).get('niche')
				if not niche: niche = []
			if niche:
				niche = Media.stringFrom(niche)
				niche = Tools.copy(niche) # In case a list was passed in. Since we edit the list below.

			# Add niches from the show to seasons/episodes.
			# Sometimes the seasons/episodes do not have eg a specific genre, making the season/episode niche different to the show.
			# Eg: American Manhunt: O.J. Simpson (show has the "mini" genre, but the episodes do not).
			if show:
				nicheShow = show.get('niche')
				if Media.isMini(nicheShow): niche.append(Media.Mini)
				if Media.isMulti(nicheShow): niche.append(Media.Multi)
				if Media.isShort(nicheShow): niche.append(Media.Short)

			# Some shows start of as a Mini, but later get more seasons.
			# This makes sure the old "mini" niche is removed if the show becomes "multi".
			# Eg: tt14063678
			multi = Media.Multi in niche

			genre = metadata.get('genre')
			if not genre and show: genre = show.get('genre') # Genre might not be available for each episode.
			if genre: genre = [i.lower() for i in genre]

			# Serie
			if Media.isSerie(media):
				season = metadata.get('season')
				episode = metadata.get('episode')

				if not pack:
					if show: pack = show.get('pack')
					if not pack:
						pack = metadata.get('pack')
						if not pack: # Summarized pack data.
							if show: pack = show.get('packed')
							if not pack: pack = metadata.get('packed')
				if pack: pack = MetaPack.instance(pack = pack)

				status = metadata.get('status')
				if not status and pack: status = pack.status()
				if status: status = status.lower()

				ended = status == MetaTools.StatusEnded

				if pack:
					seasons = pack.countSeasonOfficial()
					episodes = pack.countEpisodeOfficial()
				if seasons: multi = seasons > 1 # Shows that are originally Mini, but later a new season is added (eg: tt14063678).

				if genre and MetaTools.GenreMini in genre: niche.append(Media.Mini)
				# Do not do for seasons (or episodes), since their status is "ended", but the show was canceled after S01 and has a status of "canceled". Do not see this as the "mini" niche and do not propagate to the episodes.
				# Only for a few episodes. Otherwise anime shows with a single season and 100+ episodes would also be marked.
				elif ended and Media.isShow(media) and seasons == 1 and episodes and episodes <= 20: niche.append(Media.Mini)
				elif not Media.isMini(niche) and seasons and seasons > 1: niche.append(Media.Multi)

				# This should not be necessary anymore.
				# The season/episode types are determined accurately in MetaManager and MetaPack.
				# Rather use those types, instead of calculating them here again.
				# NB: If this is enabled again, make sure to place Media.remove() below before this code.
				'''
				# Episode
				if not episode is None:
					if season == 0 or episode == 0:
						niche.append(Media.Exclusive)
					elif episode == 1:
						niche.append(Media.Premiere)
						if not Media.isOuter(niche) and not Media.isInner(niche) and not Media.isMiddle(niche):
							if season == 1 : niche.append(Media.Outer)
							elif season > 1: niche.append(Media.Inner)
					elif pack:
						if pack.status(season = season) == MetaTools.StatusEnded:
							if episode == pack.numberLastStandardEpisode(season = season) or episode == pack.numberLastSequentialEpisode(season = season):
								niche.append(Media.Finale)
						if Media.isFinale(niche):
							if not Media.isOuter(niche) and not Media.isInner(niche) and not Media.isMiddle(niche):
								if ended and season == seasons: niche.append(Media.Outer)
								else: niche.append(Media.Inner)
						else:
							niche.append(Media.Standard)

				# Season
				elif not season is None:
					if season == 0: niche.append(Media.Exclusive)
					elif season == 1: niche.append(Media.Premiere)
					elif pack:
						if ended and season == seasons: niche.append(Media.Finale)
						else: niche.append(Media.Standard)'''

				# Episode and season
				# Trakt and TVDb season/episode types.
				if not season is None:
					# Remove old types before adding new ones.
					# Sometimes TVDb/Trakt has the incorrect type.
					# Eg: An episode is marked as season finale, but is actually a midseason finale.
					# Eg: An episode is marked as series finale, but is actually a season finale.
					# In case those types change at a later time, do not use the old/incorrect type from the cached metadata.
					niche = Media.remove(niche, Media.Chapter)

					type = metadata.get('type')
					if type:
						if Tools.isArray(type):
							niche.extend([i for i in type if not i == Media.Special]) # Media.Special is reserved for movie specials. Media.Exclusive should also be in the list to refer to episode specials.
						elif Tools.isString(type):
							type = type.lower()
							if 'standard' in type:
								niche.append(Media.Standard)
							elif 'premiere' in type or 'finale' in type:
								if 'premiere' in type: niche.append(Media.Premiere)
								elif 'finale' in type: niche.append(Media.Finale)

								if 'show' in type or 'serie' in type: niche.extend([Media.Outer, Media.Inner])
								elif 'season' in type: niche.append(Media.Inner)
								elif 'mid' in type: niche.append(Media.Middle)

				# Add the release type, how frequently episodes are released.
				# Remove the old release, since it can change.
				# Eg: An unreleased future season might be "otherly", since no episodes are available yet, but when it airs and episodes are available, it might change to "weekly".
				release = (metadata.get('packed') or {}).get('interval')
				if release:
					niche = Media.remove(niche, Media.Interval)
					niche.append(release)

			# Movie
			elif Media.isMovie(media):
				duration = metadata.get('duration') or 0

				# 40 mins. The Oscars define a short film as 40 minutes or less.
				# Some home movies are eg 58m long. Do not use ShortMaximum
				short = duration and duration <= 2400

				if genre and MetaTools.GenreTelevision in genre:
					niche.append(Media.Television)
					if short: niche.append(Media.Short)
					else: niche.append(Media.Feature)

				if not Media.isFeature(niche) and not Media.isSpecial(niche):
					if genre and MetaTools.GenreShort in genre: niche.append(Media.Short)
					elif short:
						# Unreleased/future titles might have the wrong duration, leading to them being labelled incorrectly as shorts.
						# Eg: The Avatar Collection on Trakt also lists the unreleased Avatar (3, 4, 5) movies, but they have a duration of 60 seconds.
						exception = False
						if duration <= 60:
							premiered = metadata.get('time', {}).get(MetaTools.TimePremiere)
							if premiered:
								if premiered > Time.timestamp(): exception = True
							else:
								year = metadata.get('year')
								if year:
									if year > Time.year(): exception = True
								else:
									exception = True # No year or premiere date. Assume it has not been released yet.
						if not exception: niche.append(Media.Short)

				if not Media.isFeature(niche) and not Media.isShort(niche) and not Media.isSpecial(niche):
					if (metadata.get('title') or '').lower().endswith('special'): niche.append(Media.Special)

				if not Media.isShort(niche) and not Media.isSpecial(niche): niche.append(Media.Feature)

				if not Media.isCinema(niche) and not Media.isTelevision(niche):
					if Media.isShort(niche) or Media.isSpecial(niche): niche.append(Media.Television)
					else: niche.append(Media.Cinema)

			# Topic
			if genre:
				if MetaTools.GenreAnime in genre: niche.append(Media.Anime)
				if MetaTools.GenreDonghua in genre: niche.append(Media.Donghua)
				if MetaTools.GenreAnimation in genre: niche.append(Media.Anima)
				if MetaTools.GenreDocumentary in genre: niche.append(Media.Docu)
				if MetaTools.GenreFamily in genre or MetaTools.GenreChildren in genre: niche.append(Media.Family)
				if MetaTools.GenreMusic in genre or MetaTools.GenreMusical in genre: niche.append(Media.Music)
				if MetaTools.GenreSport in genre or MetaTools.GenreSporting in genre: niche.append(Media.Sport)
				if MetaTools.GenreTelevision in genre or MetaTools.GenreReality in genre or MetaTools.GenreTalk in genre or MetaTools.GenreAward in genre or MetaTools.GenreNews in genre or MetaTools.GenreTravel in genre or MetaTools.GenreFood in genre or MetaTools.GenreHome in genre: niche.append(Media.Telly)
				if MetaTools.GenreSoap in genre: niche.extend([Media.Telly, Media.Soap])

			# Age
			time = self.time(type = MetaTools.TimeLaunch, metadata = metadata)
			if time:
				# The niche might have been calculated before the detailed metadata is available.
				# With the detailed metadata, more accurate dates might bve available, replacing the previous ones.
				niche = Media.remove(media = niche, type = Media.Age)

				ages = self.nicheAge(format = False)
				for k, v in ages.items():
					if (v[0] is None or time >= v[0]) and (v[1] is None or time < v[1]):
						niche.append(k)
						break

			# Quality
			rating = self.voting(metadata = metadata)
			if rating:
				rating = rating.get('rating')
				if rating:
					# The niche might have been calculated before the detailed metadata is available.
					# It might have assigned "Good", but after the detailed metadata is retrieved, the rating might drop to "Fair".
					# Remove old values and recalculate.
					niche = Media.remove(media = niche, type = Media.Quality)

					qualities = self.nicheQuality(media = media)
					for k, v in qualities.items():
						if (v[0] is None or rating >= v[0]) and (v[1] is None or rating <= v[1]):
							niche.append(k)
							break

			# Audience
			certificate = metadata.get('mpaa')
			if Audience.allowedKid(certificate = certificate, invalid = False, select = Audience.SelectExclusive): niche.append(Media.Kid)
			elif Audience.allowedTeen(certificate = certificate, invalid = False, select = Audience.SelectExclusive): niche.append(Media.Teen)
			elif Audience.allowedAdult(certificate = certificate, invalid = False, select = Audience.SelectExclusive): niche.append(Media.Adult)

			# Region
			regions = self.nicheRegion()
			for k, v in regions.items():
				country = metadata.get('country')
				if country:
					countries = v.get('country')
					if countries and country[0] in countries: niche.append(k)
				language = metadata.get('language')
				if language:
					languages = v.get('language')
					if languages and language[0] in languages: niche.append(k)

			# Company
			companies = MetaCompany.company()
			for i in ['studio', 'network']:
				value = metadata.get(i)
				if value:
					if not Tools.isArray(value): value = [value]
					for j in value:
						for k, v in companies.items():
							if Regex.match(data = j, expression = v.get('expression'), cache = True):
								niche.append(k)
								break

			# Pleasure
			pleasures = self.pleasure()
			for i in ['plot', 'tagline', 'title', 'originaltitle']:
				value = metadata.get(i)
				if value:
					for k, v in pleasures.items():
						if Regex.match(data = value, expression = v.get('expression'), cache = True):
							niche.append(k)

			# Other
			# Always add certain attributes that might be useful.
			# This allows the niche to be added as a database column for quick search.
			extra = []

			year = None
			if Media.isSeason(media) or Media.isEpisode(media): # Do not use the show's year for seasons and episodes.
				date = metadata.get('aired') or metadata.get('premiered')
				if date:
					try: year = int(Regex.extract(data = date, expression = '(\d{4})', cache = True))
					except: pass
			if not year: year = metadata.get('year') or metadata.get('tvshowyear')
			if year: extra.append(str(year))

			country = metadata.get('country')
			if country: extra.append(country) # Country and language codes could possibly clash.
			language = metadata.get('language')
			if language: extra.append(language) # Country and language codes could possibly clash.
			genre = metadata.get('genre') # Some genres can clash. Special/Short are also media types. History can also be the History Channel company. A few clashes might not be a huge issue.
			if genre: extra.append(genre)
			for i in extra: niche.extend(i) if Tools.isArray(i) else niche.append(i)

			# Remove contradicting niches.
			# Do AFTER the genre was added.
			niche = self.nicheClean(niche = niche, genre = genre, multi = multi)

			if niche: niche = Tools.listUnique(niche)
			if not niche: niche = None
		except: Logger.error()
		return niche

	def nicheClean(self, niche, genre = None, multi = None):
		if niche:
			# Sometimes the show type changes. Remove old types.
			# On IMDb sometimes a mini-series is later changed to a multi-series.
			# Check Multi before Mini.
			# Eg: tt20234568 (mini-series type, but 2 seasons).
			# Eg: tt14063678.
			# Do not remove Mini if there is a mini-series genre.
			# Eg: tt35456246

			mini = (MetaTools.GenreMini in genre) if genre else False
			if Media.Multi in niche and (not mini or multi): niche = Media.remove(media = niche, type = Media.Mini)
			elif Media.Mini in niche: niche = Media.remove(media = niche, type = Media.Multi)

		return niche

	def nicheTopic(self, niche = None, strict = False):
		if MetaTools.Topics is None:
			# Place the most important genre first.
			# By default, without being strict, also add other genres.
			# For instance, on IMDb anime is only marked with the Animation genre, still allow this under anime.
			MetaTools.Topics = {
				True : {
					Media.Anima		: [MetaTools.GenreAnimation],
					Media.Anime		: [MetaTools.GenreAnime],
					Media.Donghua	: [MetaTools.GenreDonghua],
					Media.Docu		: [MetaTools.GenreDocumentary],
					Media.Family	: [MetaTools.GenreFamily, MetaTools.GenreChildren],
					Media.Music		: [MetaTools.GenreMusic, MetaTools.GenreMusical],
					Media.Sport		: [MetaTools.GenreSport, MetaTools.GenreSporting],
					Media.Telly		: [MetaTools.GenreTelevision, MetaTools.GenreReality, MetaTools.GenreNews, MetaTools.GenreTalk, MetaTools.GenreGame, MetaTools.GenreAward, MetaTools.GenreTravel, MetaTools.GenreFood, MetaTools.GenreHome],
					Media.Soap		: [MetaTools.GenreSoap],
				},
				False : {
					Media.Anima		: [MetaTools.GenreAnimation, MetaTools.GenreAnime, MetaTools.GenreDonghua],
					Media.Anime		: [MetaTools.GenreAnime, MetaTools.GenreAnimation],
					Media.Donghua	: [MetaTools.GenreDonghua, MetaTools.GenreAnimation],
					Media.Docu		: [MetaTools.GenreDocumentary, MetaTools.GenreBiography],
					Media.Family	: [MetaTools.GenreFamily, MetaTools.GenreChildren],
					Media.Music		: [MetaTools.GenreMusic, MetaTools.GenreMusical],
					Media.Sport		: [MetaTools.GenreSport, MetaTools.GenreSporting],
					Media.Telly		: [MetaTools.GenreTelevision, MetaTools.GenreReality, MetaTools.GenreNews, MetaTools.GenreTalk, MetaTools.GenreGame, MetaTools.GenreAward, MetaTools.GenreTravel, MetaTools.GenreFood, MetaTools.GenreHome],
					Media.Soap		: [MetaTools.GenreSoap],
				},
			}

		if strict is None: strict = False
		topics = MetaTools.Topics.get(strict)
		if topics:
			if niche:
				if Tools.isArray(niche):
					for key in niche:
						result = topics.get(key)
						if result: return result
				else: return topics.get(niche)
			else: return topics
		else: return None

	def nicheMood(self, niche = None):
		if MetaTools.Moods is None:
			# Place the most important genre first.
			# Some providers can only filter by one genre (eg IMDb, since they AND the genres instead of OR).
			MetaTools.Moods = {
				Media.Loved			: [MetaTools.GenreRomance],
				Media.Relaxed		: [MetaTools.GenreDrama, MetaTools.GenreFamily],
				Media.Cheerful		: [MetaTools.GenreComedy],
				Media.Imaginary		: [MetaTools.GenreFantasy, MetaTools.GenreScifi, MetaTools.GenreSuperhero],
				Media.Suspicious	: [MetaTools.GenreThriller, MetaTools.GenreMystery, MetaTools.GenreSuspense],
				Media.Adventurous	: [MetaTools.GenreAdventure, MetaTools.GenreAction],
				Media.Aggressive	: [MetaTools.GenreAction, MetaTools.GenreCrime, MetaTools.GenreWar, MetaTools.GenreMartial, MetaTools.GenreWestern],
				Media.Frightened	: [MetaTools.GenreHorror, MetaTools.GenreThriller],
				Media.Curious		: [MetaTools.GenreHistory, MetaTools.GenreDocumentary, MetaTools.GenreBiography, MetaTools.GenrePolitics],
				Media.Energetic		: [MetaTools.GenreSport, MetaTools.GenreSporting, MetaTools.GenreTravel, MetaTools.GenreHoliday, MetaTools.GenreMusic, MetaTools.GenreMusical],
				Media.Indifferent	: [MetaTools.GenreReality, MetaTools.GenreSoap, MetaTools.GenreTalk, MetaTools.GenreGame, MetaTools.GenreHome, MetaTools.GenreFood, MetaTools.GenreAward],
				Media.Experimental	: [MetaTools.GenreNoir, MetaTools.GenreShort, MetaTools.GenreIndie, MetaTools.GenreSpecial, MetaTools.GenreTelevision],
			}

		if niche:
			if Tools.isArray(niche):
				for key in niche:
					result = MetaTools.Moods.get(key)
					if result: return result
			else:
				return MetaTools.Moods.get(niche)
		else:
			return MetaTools.Moods

	def nicheAge(self, niche = None, format = False):
		if MetaTools.Ages is None:
			timestamp = Time.timestamp()
			future = timestamp + 604800 # 1 week.
			ages = {
				Media.Future	: [future, None], # Released in the future.
				Media.Recent	: [timestamp - 63115200, future - 1], # Released over the past 2 years.
				Media.Modern	: [1262304000, timestamp], # Released between 2010 and now.
				Media.Mature	: [631152000, 1262304000 - 1], # Released between 1990 and 2010.
				Media.Vintage	: [-315619200, 631152000 - 1], # Released between 1960 and 1990.
				Media.Ancient	: [None, -315619200 - 1], # Released before 1960.
			}
			MetaTools.Ages = {
				False : ages,
				True : {k : [v[0] if v[0] is None else Time.format(v[0], format = Time.FormatDate), v[1] if v[1] is None else Time.format(v[1], format = Time.FormatDate)] for k, v in ages.items()}
			}

		if niche:
			if Tools.isArray(niche):
				for key in niche:
					result = MetaTools.Ages[format].get(key)
					if result: return result
			else:
				return MetaTools.Ages[format].get(niche)
		else:
			return MetaTools.Ages[format]

	def nicheQuality(self, niche = None, media = None):
		if MetaTools.Qualities is None:
			MetaTools.Qualities = {
				Media.Movie : {
					Media.Great : [8.0, None],
					Media.Good : [7.0, 8.0],
					Media.Fair : [6.0, 7.0],
					Media.Poor : [4.0, 6.0],
					Media.Bad : [None, 4.0],
				},
				Media.Show : {
					Media.Great : [8.5, None],
					Media.Good : [7.5, 8.5],
					Media.Fair : [6.5, 7.5],
					Media.Poor : [4.5, 6.5],
					Media.Bad : [None, 4.5],
				},
				Media.Mixed : {
					Media.Great : [8.5, None],
					Media.Good : [7.5, 8.5],
					Media.Fair : [6.5, 7.5],
					Media.Poor : [4.5, 6.5],
					Media.Bad : [None, 4.5],
				},
			}

		if not Media.isMixed(media):
			if Media.isSerie(media): media = Media.Show
			else: media = Media.Movie

		if niche:
			if Tools.isArray(niche):
				for key in niche:
					result = MetaTools.Qualities[media].get(key)
					if result: return result
			else:
				return MetaTools.Qualities[media].get(niche)
		else:
			return MetaTools.Qualities[media]

	def nicheCertificate(self, age, media = None, unrated = None, format = False, select = Audience.SelectAll):
		certificate = Audience.certificate(type = age, media = media, unrated = unrated, select = select)
		if format: certificate = ['-'.join(i[j : j + 2] for j in range(0, len(i), 2)) for i in certificate]
		return certificate

	def nicheRegion(self, niche = None):
		if MetaTools.Regions is None:
			# 3-letter codes are used by IMDb, with some exceptions (eg: vls, zea)
			MetaTools.Regions = {
				Media.American		: {'country' : ['us', 'ca']},
				Media.Oceanic		: {'country' : ['au', 'nz']},
				Media.British		: {'country' : ['gb', 'uk', 'ie']},
				Media.French		: {'language' : ['fr']},
				Media.Germanic		: {'language' : ['de', 'gsw', 'nds']},
				Media.Spanish		: {'language' : ['es', 'ca']},
				Media.Portuguese	: {'language' : ['pt']},
				Media.Italian		: {'language' : ['it', 'sc']},
				Media.Russian		: {'language' : ['ru', 'be', 'tt', 'ce', 'ba', 'cv']},
				Media.Turkish		: {'language' : ['tr', 'ku']},
				Media.Benelux		: {'language' : ['nl', 'fy', 'li', 'lb', 'qbn', 'vls', 'zea']}, # Too many unrelated titles returned if using countries.
				Media.Nordic		: {'language' : ['no', 'sv', 'fi', 'da', 'is']},
				Media.Slavic		: {'country' : ['uk', 'pl', 'cz', 'sk', 'md']},
				Media.Balkan		: {'country' : ['ro', 'bg', 'gr', 'al', 'rs', 'si', 'hr', 'ba', 'me', 'mk', 'xk', 'ua']},
				Media.Baltic		: {'country' : ['ee', 'lv', 'lt']},
				Media.Mexican		: {'country' : ['mx']},
				Media.Latin			: {'country' : ['br', 'ar', 'pe', 'co', 'bo', 'vc', 'cl', 'ai', 'ag', 'aw', 'bs', 'bb', 'bz', 'bm', 'bq', 'bv', 'ca', 'ky', 'cr', 'cu', 'cw', 'dm', 'do', 'ec', 'sv', 'fk', 'gf', 'gl', 'gd', 'gp', 'gt', 'gy', 'ht', 'hn', 'jm', 'mq', 'mx', 'ms', 'ni', 'pa', 'py', 'pr', 'bl', 'kn', 'lc', 'pm', 'gs', 'sr', 'tt', 'tc', 'uy', 've']},
				Media.Indian		: {'language' : ['hi', 'bn', 'mr', 'te', 'ta', 'gu', 'ur', 'kn', 'or', 'ml', 'pa', 'as', 'mai', 'mni', 'sa', 'sat']},
				Media.Chinese		: {'language' : ['zh', 'zt', 'ze', 'ug', 'za', 'ban']},
				Media.Japanese		: {'language' : ['ja']}, # js, not jp.
				Media.Korean		: {'language' : ['ko']},
				Media.Eastern		: {'country' : ['bn', 'kh', 'id', 'la', 'my', 'mm', 'ph', 'sg', 'th', 'tl', 'vn']},
				Media.Arabian		: {'language' : ['ar']},
				Media.African		: {'country' : ['za', 'ng', 'eg', 'et', 'cd', 'tz', 'ke', 'ug', 'dz', 'ao', 'bj', 'bw', 'bf', 'bi', 'cm', 'cv', 'cf', 'td', 'km', 'dj', 'gq', 'er', 'ga', 'gm', 'gh', 'gn', 'gw', 'ci', 'ls', 'lr', 'ly', 'mg', 'mw', 'ml', 'mr', 'mu', 'yt', 'ma', 'mz', 'na', 'ne', 'cg', 're', 'rw', 'sh', 'st', 'sn', 'sc', 'sl', 'so', 'ss', 'sd', 'sz', 'tg', 'tn', 'eh', 'zm', 'zw']},
			}

			language = self.settingsLanguage()
			languages = Language.settingsCode()
			languages = [language] + languages

			country = self.settingsCountry()
			if country: # If the country is France, but the title was not produced in France, but is still in the French language, also include it when detecting the niche in media().
				language = Country.language(country, language = Country.LanguagePrimary)
				if language: languages.append(language)
				country = [country]
			elif not country and language == Language.EnglishCode:
				country = ['us', 'ca']

			languages = Tools.listUnique(languages)

			if country: MetaTools.Regions[Media.Local] = {'country' : country, 'language' : None} # Do not add the languages here.
			elif languages: MetaTools.Regions[Media.Local] = {'country' : None, 'language' : languages}
			else: MetaTools.Regions[Media.Local] = {'country' : None, 'language' : None}

		if niche:
			if Tools.isArray(niche):
				for key in niche:
					result = MetaTools.Regions.get(key)
					if result: return result
			else:
				return MetaTools.Regions.get(niche)
		else:
			return MetaTools.Regions

	###################################################################
	# STATUS
	###################################################################

	@classmethod
	def statusExtract(self, status):
		return MetaData.statusExtract(status)

	###################################################################
	# GENRE
	###################################################################

	@classmethod
	def genre(self, genre = None):
		if MetaTools.Genres is None:
			# For the "media" attribute: True = supported by genre, False = not supported at all, None = supported by non-genre (eg: keywords or language/country).
			MetaTools.Genres = {
				MetaTools.GenreNone : {
					'label'						: {
						'short'					: 'None',
						'full'					: 'None',
					},
					'support'					: {
						Media.Movie				: 1999,
						Media.Show				: 1999,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenreAction : {
					'label'						: {
						'short'					: 'Action',
						'full'					: 'Action',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenreAdventure : {
					'label'						: {
						'short'					: 'Adventure',
						'full'					: 'Adventure',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenreAnimation : {
					'label'						: {
						'short'					: 'Animation',
						'full'					: 'Animation',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenreAnime : {
					'label'						: {
						'short'					: 'Anime',
						'full'					: 'Anime',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : None,	Media.Show : None},
						MetaTools.ProviderTmdb	: {Media.Movie : None,	Media.Show : None},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenreBiography : {
					'label'						: {
						'short'					: 'Biography',
						'full'					: 'Biography',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTrakt	: {Media.Movie : False,	Media.Show : True},
					},
				},
				MetaTools.GenreChildren : {
					'label'						: {
						'short'					: 'Children',
						'full'					: 'Children',
					},
					'support'					: {
						Media.Movie				: False, # Only shows supported by Trakt for this genre.
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : True},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : False,	Media.Show : True},
					},
				},
				MetaTools.GenreComedy : {
					'label'						: {
						'short'					: 'Comedy',
						'full'					: 'Comedy',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenreCrime : {
					'label'						: {
						'short'					: 'Crime',
						'full'					: 'Crime',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenreDocumentary : {
					'label'						: {
						'short'					: 'Documentary',
						'full'					: 'Documentary',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenreDonghua : {
					'label'						: {
						'short'					: 'Donghua',
						'full'					: 'Donghua',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : None,	Media.Show : None},
						MetaTools.ProviderTmdb	: {Media.Movie : None,	Media.Show : None},
						MetaTools.ProviderTvdb	: {Media.Movie : None,	Media.Show : None},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenreDrama : {
					'label'						: {
						'short'					: 'Drama',
						'full'					: 'Drama',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenreFamily : {
					'label'						: {
						'short'					: 'Family',
						'full'					: 'Family',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenreFantasy : {
					'label'						: {
						'short'					: 'Fantasy',
						'full'					: 'Fantasy',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenreHistory : {
					'label'						: {
						'short'					: 'History',
						'full'					: 'History',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : True,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenreHorror : {
					'label'						: {
						'short'					: 'Horror',
						'full'					: 'Horror',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : True,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenreMartial : {
					'label'						: {
						'short'					: 'Martial',
						'full'					: 'Martial Arts',
					},
					'support'					: {
						Media.Movie				: False, # Not supported by Trakt or IMDb.
						Media.Show				: False, # Not supported by Trakt or IMDb.
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : False,	Media.Show : False},
					},
				},
				MetaTools.GenreMusic : {
					'label'						: {
						'short'					: 'Music',
						'full'					: 'Music',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : True,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenreMusical : {
					'label'						: {
						'short'					: 'Musical',
						'full'					: 'Musical',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenreMystery : {
					'label'						: {
						'short'					: 'Mystery',
						'full'					: 'Mystery',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenrePolitics : {
					'label'						: {
						'short'					: 'Politics',
						'full'					: 'Politics',
					},
					'support'					: {
						Media.Movie				: False, # Not supported by Trakt or IMDb.
						Media.Show				: False, # Not supported by Trakt or IMDb.
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : True},
						MetaTools.ProviderTvdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTrakt	: {Media.Movie : False,	Media.Show : False},
					},
				},
				MetaTools.GenreRomance : {
					'label'						: {
						'short'					: 'Romance',
						'full'					: 'Romance',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : True,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenreScifi : {
					'label'						: {
						'short'					: 'Scifi',
						'full'					: 'Science Fiction',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenreSport : {
					'label'						: {
						'short'					: 'Sport',
						'full'					: 'Sport',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : False,	Media.Show : False},
					},
				},
				MetaTools.GenreSuperhero : {
					'label'						: {
						'short'					: 'Superhero',
						'full'					: 'Superhero',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenreSuspense : {
					'label'						: {
						'short'					: 'Suspense',
						'full'					: 'Suspense',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenreThriller : {
					'label'						: {
						'short'					: 'Thriller',
						'full'					: 'Thriller',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : True,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenreWar : {
					'label'						: {
						'short'					: 'War',
						'full'					: 'War',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenreWestern : {
					'label'						: {
						'short'					: 'Western',
						'full'					: 'Western',
					},
					'support'					: {
						Media.Movie				: 1,
						Media.Show				: 1,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenreMini : {
					'label'						: {
						'short'					: 'Mini',
						'full'					: 'Miniseries',
					},
					'support'					: {
						Media.Movie				: False, # Only shows supported by Trakt for this genre.
						Media.Show				: 1001,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : False,	Media.Show : None},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : False,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : False,	Media.Show : None},
					},
				},
				MetaTools.GenreNoir : {
					'label'						: {
						'short'					: 'Noir',
						'full'					: 'Noir',
					},
					'support'					: {
						Media.Movie				: 1002,
						Media.Show				: False, # Only movies supported by Trakt for this genre.
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : False},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTrakt	: {Media.Movie : False,	Media.Show : False},
					},
				},
				MetaTools.GenreShort : {
					'label'						: {
						'short'					: 'Short',
						'full'					: 'Short',
					},
					'support'					: {
						Media.Movie				: 1003,
						Media.Show				: 1003,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : None},
					},
				},
				MetaTools.GenreSoap : {
					'label'						: {
						'short'					: 'Soap',
						'full'					: 'Soap',
					},
					'support'					: {
						Media.Movie				: False, # Only shows supported by Trakt for this genre.
						Media.Show				: 1004,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : True},
						MetaTools.ProviderTvdb	: {Media.Movie : False,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : False,	Media.Show : True},
					},
				},
				MetaTools.GenreNews : {
					'label'						: {
						'short'					: 'News',
						'full'					: 'News',
					},
					'support'					: {
						Media.Movie				: 1005,
						Media.Show				: 1005,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : True},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : False,	Media.Show : True},
					},
				},
				MetaTools.GenreTravel : {
					'label'						: {
						'short'					: 'Travel',
						'full'					: 'Travel',
					},
					'support'					: {
						Media.Movie				: False, # Not supported by Trakt or IMDb.
						Media.Show				: False, # Not supported by Trakt or IMDb.
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : False,	Media.Show : False},
					},
				},
				MetaTools.GenreHoliday : {
					'label'						: {
						'short'					: 'Holiday',
						'full'					: 'Holiday',
					},
					'support'					: {
						Media.Movie				: 1007,
						Media.Show				: 1007,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTrakt	: {Media.Movie : True,	Media.Show : True},
					},
				},
				MetaTools.GenreTelevision : {
					'label'						: {
						'short'					: 'Television',
						'full'					: 'Television',
					},
					'support'					: {
						Media.Movie				: False, # Not supported by Trakt or IMDb.
						Media.Show				: False, # Not supported by Trakt or IMDb.
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : None,	Media.Show : False},
						MetaTools.ProviderTmdb	: {Media.Movie : True,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTrakt	: {Media.Movie : False,	Media.Show : False},
					},
				},
				MetaTools.GenreTalk : {
					'label'						: {
						'short'					: 'Talk',
						'full'					: 'Talk Show',
					},
					'support'					: {
						Media.Movie				: 1009,
						Media.Show				: 1009,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : True},
						MetaTools.ProviderTvdb	: {Media.Movie : False,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : False,	Media.Show : True},
					},
				},
				MetaTools.GenreGame : {
					'label'						: {
						'short'					: 'Game',
						'full'					: 'Game Show',
					},
					'support'					: {
						Media.Movie				: 1010,
						Media.Show				: 1010,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : False,	Media.Show : True},
					},
				},
				MetaTools.GenreAward : {
					'label'						: {
						'short'					: 'Award',
						'full'					: 'Award Show',
					},
					'support'					: {
						Media.Movie				: False, # Not supported by Trakt or IMDb.
						Media.Show				: False, # Not supported by Trakt or IMDb.
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : False,	Media.Show : False},
					},
				},
				MetaTools.GenreReality : {
					'label'						: {
						'short'					: 'Reality',
						'full'					: 'Reality Show',
					},
					'support'					: {
						Media.Movie				: 1012,
						Media.Show				: 1012,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : True},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : False,	Media.Show : True},
					},
				},
				MetaTools.GenreHome : {
					'label'						: {
						'short'					: 'Home',
						'full'					: 'Home and Garden',
					},
					'support'					: {
						Media.Movie				: False, # Only shows supported by Trakt for this genre.
						Media.Show				: 1013,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : False,	Media.Show : True},
					},
				},
				MetaTools.GenreFood : {
					'label'						: {
						'short'					: 'Food',
						'full'					: 'Food and Cooking',
					},
					'support'					: {
						Media.Movie				: 1014,
						Media.Show				: 1014,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : False,	Media.Show : False},
					},
				},
				MetaTools.GenreSporting : {
					'label'						: {
						'short'					: 'Sporting',
						'full'					: 'Sporting Event',
					},
					'support'					: {
						Media.Movie				: 1015,
						Media.Show				: 1015,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTrakt	: {Media.Movie : False,	Media.Show : True},
					},
				},
				MetaTools.GenreSpecial : {
					'label'						: {
						'short'					: 'Interest',
						'full'					: 'Special Interest',
					},
					'support'					: {
						Media.Movie				: False, # Only shows supported by Trakt for this genre.
						Media.Show				: 1016,
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTrakt	: {Media.Movie : False,	Media.Show : True},
					},
				},
				MetaTools.GenreIndie : {
					'label'						: {
						'short'					: 'Indie',
						'full'					: 'Indie',
					},
					'support'					: {
						Media.Movie				: False, # Not supported by Trakt or IMDb.
						Media.Show				: False, # Not supported by Trakt or IMDb.
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : False,	Media.Show : False},
					},
				},
				MetaTools.GenrePodcast : {
					'label'						: {
						'short'					: 'Podcast',
						'full'					: 'Podcast',
					},
					'support'					: {
						Media.Movie				: False, # Not supported by Trakt or IMDb.
						Media.Show				: False, # Not supported by Trakt or IMDb.
					},
					'provider'					: {
						MetaTools.ProviderImdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTmdb	: {Media.Movie : False,	Media.Show : False},
						MetaTools.ProviderTvdb	: {Media.Movie : True,	Media.Show : True},
						MetaTools.ProviderTrakt	: {Media.Movie : False,	Media.Show : False},
					},
				},
			}

		return MetaTools.Genres if genre is None else MetaTools.Genres.get(genre)

	###################################################################
	# PLEASURE
	###################################################################

	@classmethod
	def pleasure(self, pleasure = None):
		if MetaTools.Pleasures is None:
			MetaTools.Pleasures = {
				Media.Drug : {
					'label'						: 36646,
					'expression'				: '(drugs?|weed|cannabis|mari[jh]uana|ganja|mary[\s\-]*jane|stone(?:rs?|d)|spliff|pot|psychedelics?|lsd|acid|shrooms?|magic[\s\-]*mushrooms?|psilocybin|psychoactives?|hallucinogens?|tripping|cocaine|coke)',
					'provider' : {
						MetaTools.ProviderImdb	: 'drugs',
						MetaTools.ProviderTrakt	: '("drugs" OR "weed")',
					},
				},
				Media.Cannabis : {
					'label'						: 36647,
					'expression'				: '(weed|cannabis|mari[jh]uana|ganja|mary[\s\-]*jane|stone(?:rs?|d)|spliff|pot)',
					'provider' : {
						MetaTools.ProviderImdb	: 'marijuana',
						MetaTools.ProviderTrakt	: '("weed" || "cannabis" || "marijuana" || "ganja" || "mary jane" || "stoner" || "stoned" || "spliff")',
					},
				},
				Media.Psychedelic : {
					'label'						: 36648,
					'expression'				: '(psychedelics?|lsd|acid|shrooms?|magic[\s\-]*mushrooms?|psilocybin|psychoactives?|hallucinogens?|tripping)',
					'provider' : {
						MetaTools.ProviderImdb	: 'psychedelic',
						MetaTools.ProviderTrakt	: '("psychedelic" || "lsd" || "shrooms" || "magic mushrooms" || "psilocybin" || "psychoactive" || "hallucinogen")',
					},
				},
				Media.Cocaine : {
					'label'						: 36649,
					'expression'				: '(cocaine|coke)',
					'provider' : {
						MetaTools.ProviderImdb	: 'cocaine',
						MetaTools.ProviderTrakt	: '("cocaine" || "coke")',
					},
				},
				Media.Alcohol : {
					'label'						: 36650,
					'expression'				: '(alcohol(?:ics?)?|drunk|beers?|wine|vodka|whiskey)',
					'provider' : {
						MetaTools.ProviderImdb	: 'alcohol',
						MetaTools.ProviderTrakt	: '("alcohol" || "drunk" || "beer" || "wine" || "vodka" || "whiskey")',
					},
				},
				Media.Pill : {
					'label'						: 36651,
					'expression'				: '(pills?|prescription[\s\-]*drugs?|pharmaceuticals?)',
					'provider' : {
						MetaTools.ProviderImdb	: 'pill',
						MetaTools.ProviderTrakt	: '("pill" || "prescription drug" || "pharmaceutical")',
					},
				},

				Media.Love : {
					'label'						: 36652,
					'expression'				: '(lov(?:e|ed|ing))',
					'provider' : {
						MetaTools.ProviderImdb	: 'love',
						MetaTools.ProviderTrakt	: '("love" || "loving")',
					},
				},
				Media.Romance : {
					'label'						: 36653,
					'expression'				: '(roman(?:ce|tic(?:ally)?))',
					'provider' : {
						MetaTools.ProviderImdb	: 'romantic relationship',
						MetaTools.ProviderTrakt	: '("romance" || "romantic")',
					},
				},
				Media.Kiss : {
					'label'						: 36654,
					'expression'				: '(kiss(?:es|ed|ing)?|frenching|smooch(?:es|ed|ing)?)',
					'provider' : {
						MetaTools.ProviderImdb	: 'kiss',
						MetaTools.ProviderTrakt	: '("kiss" || "kissing" || "frenching" || "smooch")',
					},
				},
				Media.Lgbtq : {
					'label'						: 36655,
					'expression'				: '(lgbtq?\+?|gays?|homosexual(?:s|ity)?|lesbi(?:ans?|c)|queers?|transgender|tranny)',
					'provider' : {
						MetaTools.ProviderImdb	: 'lgbt',
						MetaTools.ProviderTrakt	: '("lgbt" || "lgbtq" || "queer" || "transgender")',
					},
				},
				Media.Gay : {
					'label'						: 36656,
					'expression'				: '(gays?|homosexual(?:s|ity)?)',
					'provider' : {
						MetaTools.ProviderImdb	: 'gay',
						MetaTools.ProviderTrakt	: '("gay" || "homosexual")',
					},
				},
				Media.Lesbian : {
					'label'						: 36657,
					'expression'				: '(lesbi(?:ans?|c))',
					'provider' : {
						MetaTools.ProviderImdb	: 'lesbian',
						MetaTools.ProviderTrakt	: '("lesbian" || "lesbic")',
					},
				},

				Media.Sex : {
					'label'						: 36658,
					'expression'				: '(sex|fucking|intercourse|coitus|fornication|lovemaking|making[\s\-]*love)',
					'provider' : {
						MetaTools.ProviderImdb	: 'sex',
						MetaTools.ProviderTrakt	: '("sex" || "fucking" || "intercourse" || "coitus" || "fornication")',
					},
				},
				Media.Nudity : {
					'label'						: 36659,
					'expression'				: '(nud(?:es?|ity)|naked(?:ness)?|undress(?:ing|ed)?)',
					'provider' : {
						MetaTools.ProviderImdb	: 'nudity',
						MetaTools.ProviderTrakt	: '("nude" || "nudity" || "naked" || "undress")',
					},
				},
				Media.Erotica : {
					'label'						: 36660,
					'expression'				: '(erotic(?:a|ism)?)',
					'provider' : {
						MetaTools.ProviderImdb	: 'erotica',
						MetaTools.ProviderTrakt	: '("erotic" || "erotica" || "eroticism")',
					},
				},
				Media.Pornography : {
					'label'						: 36661,
					'expression'				: '(porn(?:os?|ography)?)',
					'provider' : {
						MetaTools.ProviderImdb	: 'pornography',
						MetaTools.ProviderTrakt	: '("porn" || "pornography")',
					},
				},
				Media.Prostitution : {
					'label'						: 36662,
					'expression'				: '(prostitut(?:es?|ion|ing)|hookers?|whores?|call[\s\-]*girls?)',
					'provider' : {
						MetaTools.ProviderImdb	: 'prostitute',
						MetaTools.ProviderTrakt	: '("prostitute" || "prostitution" || "hooker" || "whore" || "call girl")',
					},
				},
				Media.Orgy : {
					'label'						: 36663,
					'expression'				: '(org(?:y|ies)|swingers?|group[\s\-]*sex|gang[\s\-]*bangs?)',
					'provider' : {
						MetaTools.ProviderImdb	: 'orgy',
						MetaTools.ProviderTrakt	: '("orgy" || "orgies" || "swinger" || "group sex" || "gang bang")',
					},
				},

				Media.Violence : {
					'label'						: 36664,
					'expression'				: '(violen(?:t|ce)|fight(?:ing)?|agressi(?:ons?|ve)|brutalit(?:y|ies))',
					'provider' : {
						MetaTools.ProviderImdb	: 'violence',
						MetaTools.ProviderTrakt	: '("violent" || "violence" || "brutality")',
					},
				},
				Media.Robbery : {
					'label'						: 36665,
					'expression'				: '(robber(?:s|y|ies)?|theft|thieves?|(?:bank[\s\-]*)?heists?)',
					'provider' : {
						MetaTools.ProviderImdb	: 'robbery',
						MetaTools.ProviderTrakt	: '("robber" || "robbery" || "heist")',
					},
				},
				Media.Smuggle : {
					'label'						: 36666,
					'expression'				: '(smuggl(?:er?s?|ing))',
					'provider' : {
						MetaTools.ProviderImdb	: 'smuggling',
						MetaTools.ProviderTrakt	: '("smuggle" || "smuggling")',
					},
				},
				Media.Hostage : {
					'label'						: 36668,
					'expression'				: '(hostages?|kidnap(?:ers?|pp?ing)?|abduct(?:ions?|ings?|ors?))',
					'provider' : {
						MetaTools.ProviderImdb	: 'hostage',
						MetaTools.ProviderTrakt	: '("hostage" || "kidnap" || "abduction" || "abducting")',
					},
				},
				Media.Torture : {
					'label'						: 36674,
					'expression'				: '(tortur(?:e[sd]?|ing))',
					'provider' : {
						MetaTools.ProviderImdb	: 'torture',
						MetaTools.ProviderTrakt	: '("torture" || "torturing")',
					},
				},
				Media.Murder : {
					'label'						: 36669,
					'expression'				: '(murder(?:s|ers?|ings?|ed)?|kill(?:ers?|ings?|ed)?)',
					'provider' : {
						MetaTools.ProviderImdb	: 'murder',
						MetaTools.ProviderTrakt	: '("murder" || "kill")',
					},
				},

				Media.Religion : {
					'label'						: 36670,
					'expression'				: '(religio(?:ns?|ious(?:ly)?)|church|synagogue|mosque|temple|god)', # "god" also matches Dragon Ball Super (from the plot: "Beerus, the God of Destruction")
					'provider' : {
						MetaTools.ProviderImdb	: 'religion',
						MetaTools.ProviderTrakt	: '("religion" || "religious")',
					},
				},
				Media.Cult : {
					'label'						: 36671,
					'expression'				: '(cults?|sects?)',
					'provider' : {
						MetaTools.ProviderImdb	: 'cult',
						MetaTools.ProviderTrakt	: '("cult"  || "sect")',
					},
				},
				Media.Secret : {
					'label'						: 36672,
					'expression'				: '((?:secret|hidden)[\s\-]*societ(?:y|ies)|illuminati|free[\s\-]*mason(?:s|ry)?)',
					'provider' : {
						MetaTools.ProviderImdb	: 'secret society',
						MetaTools.ProviderTrakt	: '("secret society" || "secret societies" || "hidden society" || "illuminati" || "freemasonry" || "free mason")',
					},
				},
				Media.Terrorism : {
					'label'						: 36673,
					'expression'				: '(terroris(?:m|ts?))',
					'provider' : {
						MetaTools.ProviderImdb	: 'terrorism',
						MetaTools.ProviderTrakt	: '("terrorism" || "terrorist")',
					},
				},
				Media.Psycho : {
					'label'						: 36675,
					'expression'				: '((?:psycho|socio)(?:s|paths?)?)',
					'provider' : {
						MetaTools.ProviderImdb	: 'psychopath',
						MetaTools.ProviderTrakt	: '("psycho" || "psychopath" || "sociopath" || "sociopaths")',
					},
				},
				Media.Sadism : {
					'label'						: 36667,
					'expression'				: '(sadis(?:ts?|m|tic(?:al(?:lt)?)?))',
					'provider' : {
						MetaTools.ProviderImdb	: 'torture',
						MetaTools.ProviderTrakt	: '("sadism" || "sadist" || "sadistic")',
					},
				},

				Media.Profanity : {
					'label'						: 36640,
					'expression'				: '(f[\s\-]words?|profan(?:e|ity|ities)|swearing|cursing|cuss(?:ing)?|(?:swear|curse|cuss)[\s\-]*words?|(?:bad|foul)[\s\-]*languages?|obscen(?:e|ity))',
					'provider' : {
						MetaTools.ProviderImdb	: 'f word',
						MetaTools.ProviderTrakt	: '("f word" || "fuck" || "profanity" || "profane" || "swearing" || "swear word" || "cursing" || "curse word" || "cussing" || "cuss word")',
					},
				},
				Media.Blasphemy : {
					'label'						: 36641,
					'expression'				: '(blasphem(?:y|ous|ers?))',
					'provider' : {
						MetaTools.ProviderImdb	: 'blasphemy',
						MetaTools.ProviderTrakt	: '("blasphemy" || "blasphemous" || "blasphemer")',
					},
				},
				Media.Sarcasm : {
					'label'						: 36642,
					'expression'				: '(sarcas(?:m|tic))',
					'provider' : {
						MetaTools.ProviderImdb	: 'sarcasm',
						MetaTools.ProviderTrakt	: '("sarcasm" || "sarcastic")',
					},
				},
				Media.Parody : {
					'label'						: 36644,
					'expression'				: '(parod(?:y|ies)|mock(?:umentar(?:y|ies)|er(?:y|ies)|ings?)?)',
					'provider' : {
						MetaTools.ProviderImdb	: 'parody',
						MetaTools.ProviderTrakt	: '("parody" || "parodies" || "mockumentary" || "mockumentaries" || "mockery" || "mocking")',
					},
				},
				Media.Satire : {
					'label'						: 36643,
					'expression'				: '(satir(?:e|ical(?:ly)?))',
					'provider' : {
						MetaTools.ProviderImdb	: 'satire',
						MetaTools.ProviderTrakt	: '("satire" || "satirical")',
					},
				},
				Media.Humor : {
					'label'						: 36645,
					'expression'				: '(humor(?:ous)?|funny|laugh(?:s|ing|able)?|hilarious|amus(?:ed?|ing))',
					'provider' : {
						MetaTools.ProviderImdb	: 'humor',
						MetaTools.ProviderTrakt	: '("humor" || "humorous" || "funny" || "laugh" || "hilarious" || "amused" || "amusing")',
					},
				},
			}

			# Only check full words. Do not match substrings within other words.
			# Eg: when matching "sex", it should not match "sexy".
			for i in MetaTools.Pleasures.values():
				i['expression'] = '(?:^|[\s\-\,\.\!\?\(\[])' + i['expression'] + '(?:$|[\s\-\,\.\!\?\)\]])'

		return MetaTools.Pleasures if pleasure is None else MetaTools.Pleasures.get(pleasure)

	###################################################################
	# COMMAND
	###################################################################

	def command(self, metadata, media = None, niche = None, action = None, video = None, multiple = None, submenu = None, number = None):
		command, folder = self._command(metadata = metadata, media = media, niche = niche, action = action, video = video, multiple = multiple, submenu = submenu, number = number)
		return command

	def commandFolder(self, metadata, media = None, niche = None, action = None, video = None, multiple = None, submenu = None, number = None):
		return self._command(metadata = metadata, media = media, niche = niche, action = action, video = video, multiple = multiple, submenu = submenu, number = number)

	def _command(self, metadata, media = None, niche = None, action = None, video = None, multiple = None, submenu = None, number = None):
		from lib.meta.menu import MetaMenu

		parameters = {}
		folder = None

		if media == Media.List or media == Media.Person:
			action = MetaMenu.Action
			parameters[MetaMenu.ParameterMedia] = metadata.get('niche')
			parameters[MetaMenu.ParameterMenu] = MetaMenu.MenuMedia
			parameters[MetaMenu.ParameterContent] = MetaMenu.ContentList if media == Media.List else MetaMenu.ContentPerson

			user = (metadata.get('id') or {}).get('user')
			for attribute in ['imdb', 'tmdb', 'tvdb', 'trakt']:
				value = metadata.get(attribute)
				if value: parameters[attribute] = ','.join([user, value]) if user else value
		else:
			bonus = Media.isBonus(media) # For Recaps/Extras in the Series menus.
			force = False
			scrape = submenu and Tools.isString(submenu) and not bonus
			sequential = metadata.get('sequential')

			# For Quick and Progress show menus.
			# The media is set to Show in MetaMenu.buildMedia(), since the layout/view looks better for shows than for episodes.
			if media == Media.Show and not metadata.get('episode') is None: media = Media.Episode

			if media == Media.Season and sequential:
				media = Media.Show
				submenu = MetaTools.SubmenuSequential
			elif (media == Media.Season and not 'season' in metadata) or (not bonus and self.submenuIs(submenu = submenu, type = MetaTools.SubmenuSerie)): # Series menu.
				media = Media.Show
				force = True
				if Tools.isString(submenu): scrape = True
				else: submenu = MetaTools.SubmenuSerie
			serie = Media.isSerie(media)

			if submenu is None: submenu = self.submenu(media = media, multiple = multiple, force = force)
			if submenu is True: submenu = MetaTools.SubmenuSerie if self.submenuFlat(media = media, force = force) else MetaTools.SubmenuEpisode

			if not action:
				action = 'scrape'
				if not scrape:
					if not video is None:
						action = 'streamsVideo'
					elif media == Media.Extra:
						action = MetaMenu.Action
						parameters[MetaMenu.ParameterMenu] = MetaMenu.MenuExtra
					elif serie and submenu:
						media = Media.Episode
						action = MetaMenu.Action
						parameters[MetaMenu.ParameterMenu] = MetaMenu.MenuMedia
						parameters[MetaMenu.ParameterContent] = MetaMenu.ContentEpisode
					elif media == Media.Show:
						media = Media.Season
						action = MetaMenu.Action
						parameters[MetaMenu.ParameterMenu] = MetaMenu.MenuMedia
						parameters[MetaMenu.ParameterContent] = MetaMenu.ContentSeason
					elif media == Media.Season:
						media = Media.Episode
						action = MetaMenu.Action
						parameters[MetaMenu.ParameterMenu] = MetaMenu.MenuMedia
						parameters[MetaMenu.ParameterContent] = MetaMenu.ContentEpisode
					elif media == Media.Set:
						media = Media.Set
						action = MetaMenu.Action
						parameters[MetaMenu.ParameterMenu] = MetaMenu.MenuMedia
						parameters[MetaMenu.ParameterContent] = MetaMenu.ContentSet

			if action == 'scrape': add = ['imdb', 'tmdb', 'tvdb', 'trakt', 'title', 'tvshowtitle', 'year', 'tvshowyear', 'premiered', 'season', 'episode']
			else: add = ['imdb', 'tmdb', 'tvdb', 'trakt', 'title', 'year', 'season', 'episode']
			for attribute in add:
				try: parameters[attribute] = metadata[attribute]
				except: pass
			if not action == 'scrape':
				parameters['title'] = metadata.get('tvshowtitle') or metadata.get('title')
				parameters['year'] = metadata.get('tvshowyear') or metadata.get('year')

			# Season recaps and extras.
			if metadata and 'query' in metadata: parameters['title'] = parameters['tvshowtitle'] = metadata['query']
			if not video is None: parameters['video'] = video
			parameters['media'] = Media.Episode if media == Media.Recap or media == Media.Extra else media
			if niche: parameters['niche'] = Media.stringTo(niche)

			if not action == 'scrape':
				if serie and (submenu or force):
					# Series menu and Progress submenu.
					self.submenuNumber(media = media, submenu = submenu, multiple = multiple, metadata = metadata, parameters = parameters)
				if submenu:
					parameters[MetaTools.SubmenuParameter] = submenu
					# gaiasubmenu - Check MetaTools.submenuSpecial() for more info.
					if self.submenuSpecial(media = media, submenu = submenu, multiple = multiple, metadata = metadata): folder = False

			# Scrape using a specific number to retreive the detailed metadata in core.py.
			if action == 'scrape' and serie:
				value = None
				if number is None: number = submenu
				if self.submenuIsSequential(number): value = MetaPack.NumberSequential
				elif self.submenuIsAbsolute(number): value = MetaPack.NumberAbsolute
				elif not number: value = MetaPack.NumberStandard
				if value: parameters['number'] = value

		# Do not optimize anymore, since it makes it more reabable/editable and we do not pass large metadata objects or long URLs via commands anymore.
		command = System.command(action = action, parameters = parameters, optimize = False)

		return command, folder

	###################################################################
	# MULTIPLE
	###################################################################

	def multiple(self, metadata):
		if not Tools.isArray(metadata): metadata = [metadata]

		# Sometimes the seasons can have different foreign titles.
		# Eg: "A Fazenda" vs "The Color of Love"
		imdb = [i.get('imdb') for i in metadata]
		imdb = Tools.listUnique([i for i in imdb if i])
		trakt = [i.get('trakt') for i in metadata]
		trakt = Tools.listUnique([i for i in trakt if i])
		if len(imdb) == 1 and len(trakt) == 1: return False

		titles = [meta['tvshowtitle'] for meta in metadata if 'tvshowtitle' in meta and meta['tvshowtitle']]
		titles = [Tools.replaceNotAlphaNumeric(i).lower() for i in titles] # Sometimes the seasons use different symbols (eg apostrophes) for their titles. Eg: "Poppa's House" vs "Poppa’s House".
		titles = Tools.listUnique(titles)

		# Sometimes different episodes of the same season have different show titles.
		# Eg: 'Hollywood Medium with Tyler Henry' vs 'Hollywood Medium'
		result = []
		for title in titles:
			found = False
			for i in result:
				if title in i or i in title:
					found = True
					break
			if not found: result.append(title)

		return len(result) > 1

	###################################################################
	# SUBMENU
	###################################################################

	def submenu(self, media, multiple, force = False):
		return self.submenuFlat(media = media, force = force) or self.submenuProgress(media = media, multiple = multiple)

	def submenuSpecial(self, media, submenu, multiple, metadata, force = False):
		# UPDATE 1
		#	There is a problem with opening the context menu on an episode in the Progress/Quick submenu.
		#	For some reason Kodi executes the command of the item the context was opened on, and all its submenu items.
		#	This causes "episodesRetrieve" (and sometimes "seasonsRetrieve") to be called many times, causing the context menu to take very long to open.
		#	Especially if S00 or other extras are in the submenu, Kodi can take minutes to load the context, sometimes hanging so long that a restart is required.
		#	UPDATE: The problem is the "Next Page" menu entry in the submenus. If Kodi encounters the next item in a page, it loads that submenu.
		#	UPDATE: That submenu also has a next page. So Kodi continues to sequentially load all submenus from the next entry, one after the other, which can take a long time for shows with a lot of unwatched episodes.
		#	This only happens with episode submenus that have a folder underneath it.
		#	This does not happen with any other show/season/episode/movie/generic menus.
		#	Also, if the "Direct Scraping" setting is enabled, this also does not happen, since the Progress menu entries are not folders anymore, but initiate the scrape process directly.
		#	This is also not caused by the custom Gaia context menu. Even if no context menu is added at all, this problem persists.
		#	Only if the link/command attribute is removed from items passed to xbmcplugin.addDirectoryItems(), is this problem gone.
		#	This inidcates that this is a Kodi bug. Maybe if Kodi sees an episode folder menu, it scans all subitems to determine which labels to add to the context.
		#	There is no way to differentiate this endpoint being executed by Kodi when the context is opened, vs if the user just manually clicks on it to open the submenu (handle, plugin origin, etc is all the same).
		#	There also does not seem any way to prevent this from happening by calling functions on xbmcplugin, listitem, etc.
		#	So the only way is a dirty hack. We simply check if this endpoint is called with the same title within a few seconds of each other using global variables.
		#	Any subsequent "duplicate" requests are blocked, making the context load faster.
		#	There is still one minor problem: if the user manually opens the submenu within this time period, it might be detected as a "dupliacte" request and the menu is not loaded.
		#	The user will have to wait a few seconds and then reopen the submenu.
		#	Same happens if the user opens a submenu, quickly navigates back and tries to reopen the same menu.
		#	UPDATE: We changed the global property code and now detect the context menu using "Container.HasFiles". This will still call "episodesRetrieve" once, but not subsequent times.
		#	UPDATE: And the problem with quickly manually opening submenus is also gone with this alternative.
		# UPDATE 2
		#	Even with the solution above, opening the context menu of submenus on low-end devices is still very slow.
		#	We now use a better solution. Submenus are not marked as directories/folders anymore, but instead an action that calls the "episodesSubmenu" endpoint.
		#	"episodesSubmenu" then manually updates the container.
		#	If the "episodesSubmenu" endpoint is ever removed again, make sure to update the following:
		#		1. Uncomment the code above in this endpoint.
		#		2. In meta/tools.py, revert all statements marked as "gaiasubmenu".
		# UPDATE 3
		#	The above two sections are from Gaia 6. In Gaia 7+ we now use the new MetaMenu.
		#	Still make the episode submenu an action to prevent the sequentially scanning of items underneath it.
		#	But we do not have to create a special endpoint anymore, since MetaMenu will now automatically create a new Python process and call Container.Update(...) if the action to MetaMenu does not have a handle (aka called via RunPlugin(...)).
		#	Check this file for all "gaiasubmenu" comments added for this purpose.
		# UPDATE 4
		#	Not sure if this has been fixed in the latests Kodi 21? Seems so.
		#	But we now might need this in any case, since Kodi 20 does not show process icons for "folder" menu entries.
		#	Check the comments under _items().

		if submenu: return True if self.submenuIs(submenu = submenu, type = MetaTools.SubmenuEpisode) else False # Is this needed for the Series/Absolute menu as well? Currently assuming no.
		elif media == Media.Season and metadata and not 'season' in metadata: return True
		elif self.submenu(media = media, multiple = multiple, force = force): return True
		else: return False

	def submenuFlat(self, media, force = False):
		return media == Media.Show and (force or self.mShowFlat)

	def submenuProgress(self, media, multiple):
		return (media == Media.Episode or media == Media.Mixed) and multiple and self.mShowSubmenu

	def submenuHistory(self):
		return self.mSleepyLimit

	@classmethod
	def submenuIs(self, submenu, type):
		return Tools.isString(submenu) and submenu == type

	@classmethod
	def submenuIsSerie(self, submenu):
		return self.submenuIs(submenu = submenu, type = MetaTools.SubmenuSerie)

	@classmethod
	def submenuIsSequential(self, submenu):
		return self.submenuIs(submenu = submenu, type = MetaTools.SubmenuSequential)

	@classmethod
	def submenuIsAbsolute(self, submenu):
		return self.submenuIs(submenu = submenu, type = MetaTools.SubmenuAbsolute)

	@classmethod
	def submenuIsEpisode(self, submenu):
		return self.submenuIs(submenu = submenu, type = MetaTools.SubmenuEpisode)

	def submenuNumber(self, media, submenu, multiple, metadata, parameters):
		# First value is the page offset, that is, the number of previous pages that were filled purley with specials.
		# Second value is the episode number of the last special in the menu, used to filter out already-seen specials on the next page.

		# There are various issues with interleaving specials in Series and Progress submenus:
		#	1. If too many specials are available (eg: changing the settings to incldue ALL specials), some pages only contain specials and therefore no next page is added.
		#	2. Even if a next page is added, it still contains the parameters of the last season/episode from the previous "normal" page, and therefore the next page just reloads the same page with all the specials.
		#	3. Specials that are interleaved between the end of one season and the start of the next season, can appear on two subsequent pages, that is listed on the previous page after all the normal episodes, and on the next page before the next normal episode.
		# There are various ways we tried to solve this, like making certain parameters (eg season/episode/page) negative to indicate a sub-page, or adding an additional "offset" parameter to act as a sub-page increment for pages with all specials.
		# Each of these methods has their own problems and only solves part of the problem. We even tried to make the "offset" parameter an array holding multiple integers to hjandle different aspects of the paging, just bloating things.
		# A "hacky" way ends up being the cleanest solution, solving all the problems.
		# Just add the episode number of last shown special as an "offset" parameter.
		# On the next page, ALL specials are interleaved, even those that shouldn't. When we apply the limiting/paging, we simply cut away the "offset" special and any specials before it.
		# This solves the issue of paging with all-special-pages, and gets rid of certain specials showing up multiple times on subsequent pages.
		# Basically "season"/"episode" are usaed as offset for the normal episodes, and "offset" as the offset for specials.

		force = False
		specials = False

		season = None
		episode = None

		seasoned = parameters.get('season')
		episoded = parameters.get('episode')
		offset = parameters.get('offset')
		sequential = self.submenuIsSequential(submenu = submenu)
		absolute = self.submenuIsAbsolute(submenu = submenu)

		metadatas = None
		if Tools.isArray(metadata):
			metadatas = metadata
			for i in reversed(metadatas):
				if Media.isEpisode(i.get('media')) and i.get('season') == 0:
					offset = i.get('episode')
					break
			for i in reversed(metadatas):
				if Media.isEpisode(i.get('media')):
					if i.get('season') or i.get('season') == seasoned: # Ignore Recaps, Extras, and Specials.
						metadata = i
						break

		if sequential or absolute:
			media = Media.Show
			force = True
		elif (Media.isSeason(media) and not 'season' in metadata) or self.submenuIsSerie(submenu = submenu): # Series menu.
			media = Media.Show
			force = True
			if not Tools.isString(submenu): submenu = MetaTools.SubmenuSerie

		flat = self.submenuFlat(media = media, force = force)
		if submenu is None: submenu = self.submenu(media = media, multiple = multiple, force = force)
		if submenu is True: submenu = MetaTools.SubmenuSerie if flat else MetaTools.SubmenuEpisode

		# Season offset for "More" of flattened show menus.
		if Media.isSerie(media) and (submenu or force):
			progress = False
			page = parameters.get('page')
			first = not page or page == 1

			if metadata:
				season = metadata.get('season') or 1
				episode = metadata.get('episode') or 0
				if not first: episode += 1 # Only increment for More menu items, not for the original non-more entry (eg Progress menu or 1st page of Series menu).

				if metadata and 'episode' in metadata: # Submenus for multiple episode menus.
					progress = True

					# Include the last 3 watched episodes, in case the user wants to rewatch them (aka fell asleep yesterday while watching).
					# Only do this for the first submenu. Do not offset subsequent (More) pages with the watched history.
					if first and self.submenuIsEpisode(submenu = submenu): episode -= self.submenuHistory()

					# NB: Do not use the pack data here.
					# To make episode Progress menus load faster, the pack is not retrieved.
					# Allow negative numbers, which are correctly looked-up in MetaManager.metadataEpisode().
					# Eg: S02E-02 means the 2nd last episode from S02.
					# Now we only need to retrieve the pack if the submenu is actaully opened on an episode in the Progress menu.
					if episode <= 0:
						episode -= 1 # For the correct offset/index from the back of the season for the MetaPack lookup.
						if season > 1:
							season -= 1
						elif season <= 1: # Do not go negative for S01.
							season = 1
							episode = 1
			else:
				# Carry on the numbers from the previous page, for a page containing only specials.
				season = parameters.get('season') or 1
				episode = parameters.get('episode') or 0

			parameters['season'] = season if progress else max(0, season)
			parameters['episode'] = episode if progress else max(1, episode)
			if offset: parameters['offset'] = offset

		return season, episode

	###################################################################
	# LABEl
	###################################################################

	def label(self, metadata, media = None, label = None, future = None, multiple = False, mixed = False, extend = True, menu = None, submenu = None, decorate = None):
		if not media: media = self.media(metadata = metadata)
		if decorate is None: decorate = True

		if extend is True:
			# For external addons and widgets, do not add any extra info or decoration, since it looks ugly.
			# Useful for skins that use the label instead of the title of a ListItem (eg Eminence 2).
			if self.mOriginExternal: extend = MetaTools.ExtendNone
			else: extend = MetaTools.ExtendFull
		basic = multiple or extend == MetaTools.ExtendNone

		pack = None
		prefix = None
		suffix = None
		serie = Media.isSerie(media)
		season = metadata.get('season')
		episode = metadata.get('episode')
		special = media == Media.Season and season is None # Series and Absolute menus.

		try:
			futureKnown = future['known']
			futureUnknown = future['unknown']
			futureAge = future['age']
			futureTime = future['time']
		except:
			futureKnown = None
			futureUnknown = None
			futureAge = None
			futureTime = None

		# For Quick and Progress show menus.
		# The media is set to Show in MetaMenu.buildMedia(), since the layout/view looks better for shows than for episodes.
		if media == Media.Show and not episode is None: media = Media.Episode

		# Allow seasons and episodes for the Trakt watchlist.
		if media == Media.Show and self.menuTypeWatchlist(menu = menu):
			if not episode is None: media = Media.Episode
			elif not season is None: media = Media.Season

		# For episodes with a generic title, like "Episode 8".
		# Use the original title if available.
		title = None
		if media == Media.Episode:
			title = metadata.get('title')
			originaltitle = metadata.get('originaltitle')
			if title and originaltitle and MetaPack.titleGeneric(title = title) and not MetaPack.titleGeneric(title = originaltitle): title = originaltitle
		elif Media.isBonus(media):
			seasoned = 1 if season is None else season
			if media == Media.Recap: seasoned += 1
			label = Title.title(media = media, title = label, season = seasoned, episode = 0)

		if not label:
			if media == Media.List:
				return metadata.get('title')
			elif media == Media.Season and metadata.get('sequential'):
				label = Translation.string(36677)
			elif media == Media.Season or (media == Media.Episode and mixed): # Just use the season number of mixed menus.
				if not title: title = metadata.get('title')
				year = metadata.get('year') or metadata.get('tvshowyear')
				series = season is None and not 'season' in metadata
				if not mixed: label = Title.title(media = media, title = None if basic else title, year = year, season = season, series = series, special = True)
			elif media == Media.Episode:
				if not title: title = metadata.get('title')
				year = metadata.get('year') or metadata.get('tvshowyear')

				# Sequential/absolute menus with IMDb specials. Eg: Downton Abbey S02E09.
				if metadata.get('sequential'):
					season = 1
					episode = 0

				if extend == MetaTools.ExtendTitle:
					label = title # Use by Kodi Informer.
				elif basic:
					label = Title.title(media = media, year = year, season = season, episode = episode)
				elif not mixed:
					prefix = Title.title(media = media, year = year, season = season, episode = episode)
					label = title
			else:
				title = metadata.get('title') or metadata.get('originaltitle') or metadata.get('tvshowtitle')
				year = metadata.get('year') or metadata.get('tvshowyear')
				label = Title.title(media = media, title = title, year = year)
				if not label: label = title

		if (media == Media.Season or media == Media.Episode) and not extend == MetaTools.ExtendTitle and basic:
			title = metadata.get('tvshowtitle')

			# Always add the title.
			# Eg: The first episode's title of the show "1883" is also "1883".
			#if title and not title in label and not label in title: label = '%s - %s' % (title, label)
			#if title and label: suffix = label # Already set in itemDetails()
			label = title

		# Episodes without a title.
		# Otherwise "None" is shown in the menus.
		if not label and Media.isBase(media): label = Translation.string(36812)

		if extend:
			if (extend == MetaTools.ExtendFull or extend == MetaTools.ExtendBasic) and self.mLabelStyle and not special: # Do not do this for the Series/Absolute menus.
				fontBold = False
				fontItalic = False
				fontLight = False
				fontColor = None

				current = Time.timestamp()
				plays = metadata.get('playcount') or 0
				timeExact = self.time(type = MetaTools.TimePremiere if serie else MetaTools.TimeHome, metadata = metadata, estimate = False, fallback = False)
				time = self.time(type = MetaTools.TimePremiere if serie else MetaTools.TimeHome, metadata = metadata, estimate = True, fallback = True) or 0
				age = current - time

				# Mark "important" titles, namely unwatched titles that were recently released and have at certain rating and number of votes.
				if self.mLabelStyleRelease and not plays and ((media == Media.Movie and age > -MetaTools.TimeNewMovie) or (media == Media.Show and age > -MetaTools.TimeNewShow)): # Allow releases slightly into the future, especially for shows (early episode leaks or timezone differences).
					important = False
					progress = metadata.get('progress') or 0
					played = current - (self.time(type = MetaTools.TimePaused, metadata = metadata, estimate = False, fallback = False) or 0)

					if progress > 0.05 and progress < 0.8 and played < 2419200: # Unfinished titles played during past 4 weeks.
						important = True
					else:
						values = [
							{'age' : 604800,	'votes' : 500,		'rating' : 4.5},	# 1 week.
							{'age' : 1209600,	'votes' : 5000,		'rating' : 5.0},	# 2 weeks.
							{'age' : 1814400,	'votes' : 7500,		'rating' : 6.0},	# 3 weeks.
							{'age' : 2419200,	'votes' : 10000,	'rating' : 7.0},	# 4 weeks.
							{'age' : 3628800,	'votes' : 20000,	'rating' : 7.2},	# 6 weeks.
							{'age' : 4838400,	'votes' : 50000,	'rating' : 7.5},	# 8 weeks.
							{'age' : 7884000,	'votes' : 100000,	'rating' : 7.7},	# 3 months.
							{'age' : 15768000,	'votes' : 200000,	'rating' : 8.0},	# 6 months.
							{'age' : 23652000,	'votes' : 500000,	'rating' : 8.2},	# 9 months.
						]

						# Reduce the votes requirement if there is no IMDb rating.
						adjustVotes = 1.0
						try:
							# 3.5 - 5.7% for "Dune Part Two" and "Game of Thrones".
							if not metadata['voting']['votes'].get(MetaTools.ProviderImdb): adjustVotes = 0.06
						except: pass

						# Shows generally have a higher rating than movies. Increase the requirement.
						adjustRating = 0.0
						minimumRating = 0.0
						if media == Media.Show:
							# Increasing the rating by 0.3 marks too few titles with bold.
							# Also, new shows often have way fewer votes, since those only accumlate over time.
							#adjustRating = 0.3

							# Still increase the rating, since there are often too many titles in bold.
							# With too many bold labels, they lose their meaning/importance.
							if season and season > 1 and not episode: # Not for Progress menus.
								minimumRating = 6.5 if season <= 2 else 7.0 if season <= 3 else 7.2
								adjustRating = 0.5 if season <= 2 else 0.75 if season <= 3 else 1.0

							if adjustVotes >= 1:
								if season: adjustVotes = 0.3 if season <= 1 else 0.6 if season <= 2 else 0.9 if season <= 3 else 1.5
								else: adjustVotes = 0.4

						rating = metadata.get('rating') or 0
						votes = metadata.get('votes') or 0
						for i in values:
							if age <= i['age'] and votes >= (i['votes'] * adjustVotes) and rating >= (i['rating'] + adjustRating) and rating >= minimumRating:
								important = True
								break

					if important: fontBold = True

				if Media.isMovie(media):
					# Mark unreleased movies with italics.
					if not futureAge is None:
						if futureAge > 0 and futureAge <= MetaTools.TimeNewMovie: # Near future.
							fontItalic = True
							fontColor = self.mLabelStyleColor
						elif futureAge >= MetaTools.TimeFuture: # Far future.
							fontLight = True
							fontColor = self.mLabelStyleColor
					elif futureAge is None and not futureTime:
						# Eg: Untitled Avatar: The Last Airbender Film 2
						if 'untitle' in title.lower():
							fontLight = True
							fontColor = self.mLabelStyleColor

				elif serie:
					# NB: The pack is not added to the Progress menu top-level anymore. Use the smart pack.
					# Packs are only available for season and episode menus.
					pack = metadata.get('pack')
					if pack: pack = MetaPack.instance(pack = pack)

					# Mark "unofficial" seasons/episodes as light (typically seasons/episodes that are on TVDb or IMDb, but not on Trakt).
					# Eg: Dragon Ball Super S02+.
					if self.mLabelStyleEpisode and pack and (media == Media.Season or media == Media.Episode) and not submenu:
						if season: # For seasons, but exclude the S0 menu.
							if Media.isSeason(media):
								item = pack.seasonStandard(season = season)
								type = pack.type(item = item)
								if type:
									if type.get(MetaPack.NumberUnofficial) or type.get(Media.Alternate):
										# Eg: Dragon Ball Super S02+.
										fontLight = True
										fontColor = self.mLabelStyleColorLight

							elif Media.isEpisode(media):
								# Do not directly retrieve the type, since it can point to a sequential episode number.
								# Eg: Star Wars: Young Jedi Adventures S01E26-S01E50.
								#type = pack.type(season = season, episode = episode)
								item = pack.episodeStandard(season = season, episode = episode)
								type = pack.type(item = item)
								if type:
									numberSequential = pack.number(item = item, number = MetaPack.NumberSequential)
									numberTrakt = pack.number(item = item, provider = MetaPack.ProviderTrakt)
									numberTvdb = pack.number(item = item, provider = MetaPack.ProviderTvdb)

									if type.get(MetaPack.NumberUnofficial):
										# Eg: Star Wars: Young Jedi Adventures S01E26-S01E50.
										fontLight = True
										fontColor = self.mLabelStyleColorLight
									elif not numberTrakt[MetaPack.PartEpisode] is None and numberTvdb[MetaPack.PartEpisode] is None and age > 1209600: # 2 weeks.
										# Eg: Pokémon S25E47+.
										# Only do this if the episode is more than 3 days old. Otherwise new episodes that are already on Trakt/TMDb/IMDb, but not on TVDb yet, are made italics.
										# This also marks episodes that are not on TVDb, but do not really need to be formatted with fontLight.
										# Eg: QI S22E09 (not on TVDb).
										# Update (2025-11): 3 days is not enough. Increase to 2 weeks.
										# There are shows where Trakt does not have the TVDb IDs for the episodes yet, and TVDb does not have the IMDb IDs yet.
										# This makes all the Trakt episodes official, and all the TVDb episodes unofficial.
										# Eg: Unburied (tt33038523) did not have the TVDb IDs, even after 5 days of airing. All episodes are instantly released.
										# Update (2025-11): MetaPack was fixed to be able to match the episodes of this specific show by title, even with missing IDs. But keep a longer age for other shows that cannot be matched by title.
										fontLight = True
										fontColor = self.mLabelStyleColorLighter
									elif numberTrakt[MetaPack.PartEpisode] is None and not numberTvdb[MetaPack.PartEpisode] is None:
										fontLight = True
										fontColor = self.mLabelStyleColorLight
									elif type.get(MetaPack.NumberOfficial) and not type.get(MetaPack.NumberUniversal) and numberSequential[MetaPack.PartEpisode] == episode:
										# Eg: Dragon Ball Super S01E15. Check numberSequential for Pokémon S19+.
										# Update: Do not make these official episodes light/italics, since too many anime shows have too many episodes in italics and might confuse the user.
										# All official (Trakt/TMDb) episodes should be in normal font, even if they do not match TVDb.
										# Only mark unofficial (TVDb) episodes in italics.
										# Eg: One Piece S01.
										#fontLight = True
										#fontColor = self.mLabelStyleColorLighter
										pass
									elif not pack.number(season = season, episode = episode) == [season, episode]:
										# Eg: Star Wars: Young Jedi Adventures S01E26-S01E50.
										# Update: Not anymore. This is now done by the first if-statement.
										fontLight = True
										fontColor = self.mLabelStyleColorLight
								else:
									# Eg: Downtonw Abbey S02E09 (IMDb).
									# This can also happen if a new episode is on IMDb, but not on Trakt/TMDb/TVDb yet.
									# The IMDb bulk data might be outdated by a few days, so the new IMDb episode is also not in MetaPack yet.
									fontItalic = True

					# Do not decorate if it is from Releases (New Shows / New Seasons / New Episodes), since these are obviously all new.
					if self.mLabelStyleRelease and decorate:
						if not futureAge is None:
							if futureAge > 0 and futureAge <= MetaTools.TimeNewShow:
								fontItalic = True
								fontColor = self.mLabelStyleColor

							# Not if a season does not have a release date.
							# Or if a season does not have a release date, but the show is continuing (aka a future season that does not have a release date yet).
							if futureAge >= MetaTools.TimeFuture and (metadata.get('time') or (pack and pack.status() in MetaTools.StatusesFuture)):
								fontLight = True
								fontColor = self.mLabelStyleColor

						# If a season does not have a release date, but the show is continuing (aka a future season that does not have a release date yet).
						elif (media == Media.Season or media == Media.Episode) and futureAge is None:
							if futureKnown:
								fontItalic = True
								fontColor = self.mLabelStyleColor
							elif futureUnknown:
								fontLight = True
								fontColor = self.mLabelStyleColor
							elif pack and pack.status() in MetaTools.StatusesFuture:
								fontLight = True
								fontColor = self.mLabelStyleColor

					if self.mLabelStyleEpisode and decorate and media == Media.Episode and season == 0:
						if not 'special' in metadata or not metadata['special'] or not 'story' in metadata['special'] or not metadata['special']['story']:
							fontLight = True

					# Mark new episodes/seasons in multiple menus as bold.
					if self.mLabelStyleRelease and decorate and (media == Media.Season or media == Media.Episode or (media == Media.Show and not season is None)) and (not futureAge or futureAge < MetaTools.TimeNewShow):
						new = False

						# New and future episode.
						if not new and time and not plays:
							if age > -MetaTools.TimeNewShow:
								if multiple: # Arrivals and Progress menus.
									if episode is None: # Arrivals and other menus.
										if not season or season == 1:
											if age < 518400: new = True # 6 days.
										elif season:
											if season <= 2 and age < 432000: new = True # 5 days.
											elif season <= 3 and age < 345600: new = True # 4 days.
											elif season <= 4 and age < 259200: new = True # 3 days.
									else: # Progress menu.
										if age < 518400: new = True # 6 days (not 1 week, otherwise last week's episode might show as bold)

									# The above code is only for the CURRENT season/episode.
									# Also make the label bold in the Progress menu if a later episode is newly released.
									# The smart-pack data contains the episode release dates for the season that is closest to the current date.
									# Eg: The user is busy with S02E03 of a show. If a new episode S04E01 is released, the label in the Progress menu should be bold to indicate the show has a new episode.
									if not new and submenu:
										smart = Tools.get(metadata, 'smart', 'pack', 'time', 'episode')
										if smart:
											age2 = None
											for i in reversed(smart):
												if i <= current:
													age2 = current - i
													break
											if age2 and age2 > -MetaTools.TimeNewShow:
												if age2 < 518400:
													new = True # 6 days.

								# Season and Episode menus.
								# Do not make specials without an airing date bold (timeExact is None).
								# Eg: Vikings S00E27+.
								# Do not make future unreleased seasons bold.
								# Use a lower limit for daily shows, otherwise too many episodes are marked in bold.
								elif not season == 0 and timeExact:
									if episode is None: # Season menus.
										if age < 2419200: new = True # 28 days.
									else: # Episode menus.
										if age < (432000 if Media.isDaily(metadata.get('niche')) else 864000): new = True # 5/10 days.

						# New Season.
						if not new:
							date = 0
							seasoned = None

							# For season and episode menus where the pack is available.
							if pack:
								for i in pack.season(default = []):
									number = pack.numberStandard(item = i)
									if number: # Exclude specials.
										minimum = pack.timeMinimum(item = i)
										if minimum and minimum < current and minimum >= date:
											date = minimum
											seasoned = number

							# For Progress menus where only the smart pack is available.
							else:
								smart = Tools.get(metadata, 'smart', 'pack', 'time', 'season')
								if smart:
									for i in range(1, len(smart)): # Exclude specials.
										if smart[i]:
											minimum = smart[i][0]
											if minimum and minimum < current and minimum >= date:
												date = minimum
												seasoned = i

							# Only do this for the season that is newley released.
							# Otherwise a new season might cause all unwatched episodes in older seasons to also be marked in bold.
							# Or mark as bold if multiple, so that shows in the Arrivals menu are highlighted if a new season comes out, even if the user still watches an older season.
							if date and not seasoned is None and (season == seasoned or multiple):
								date = current - date
								if date > -MetaTools.TimeNewShow and date < (518400 if media == Media.Episode else 2419200): # 6 days or 4 weeks.
									playback = self._playback()
									# NB: Only do this if at least 1 episode in the show was previously watched.
									# Otherwise shows without any watched episodes also show in bold (Quick menu - recommendations/featured/trending/arrivals).
									history = playback.history(media = Media.Show, imdb = metadata.get('imdb'), tmdb = metadata.get('tmdb'), tvdb = metadata.get('tvdb'), trakt = metadata.get('trakt'), metadata = metadata, pack = pack, quick = True)
									if history and history['count']['total']:
										if media == Media.Episode:
											# Do not bolden already watched episodes.
											history = playback.history(media = Media.Episode, imdb = metadata.get('imdb'), tmdb = metadata.get('tmdb'), tvdb = metadata.get('tvdb'), trakt = metadata.get('trakt'), season = season, episode = episode, metadata = metadata, pack = pack, quick = True)
											if not history or not history['count']['total']:
												new = True
										elif metadata.get('count') and (media == Media.Show or media == Media.Season):
											# Only mark new shows/seasons with bold if they were not fully watched yet.
											# If a new show/season was fully watched, it should not show as bold anymore.
											unwatched = (metadata.get('count').get('episode') or {}).get('unwatched')
											if unwatched: new = True
										else:
											new = True

						if new: fontBold = True

				# Estaury font does not have "light", or at least not something one can notice.
				if fontLight and Skin.isEstuary():
					fontItalic = True
					fontLight = False

				if fontBold: label = Format.fontBold(label)
				if fontItalic: label = Format.fontItalic(label)
				if fontLight: label = Format.fontLight(label)
				if fontColor: label = Format.fontColor(label, color = fontColor)

			# Do this last, after Format.fontBold(label).
			# Otherwise the labelBefore/labelAfter, which might have its own bold formatting, is formatted a second time.
			# There could then be 2 nested bold tags, and then the title in the label is not actually bold and ends with "[/B]".
			# Make sure there is no nested formatting.
			if extend == MetaTools.ExtendFull:
				if metadata.get('labelBefore'): label = Detail.joinBefore(data = label, detail = metadata['labelBefore'])
				if metadata.get('labelAfter'): label = Detail.joinAfter(data = label, detail = metadata['labelAfter'])

			if prefix: label = prefix + ' - ' + label
			if suffix: label += ' - ' + Format.fontItalic(suffix)

		return label

	###################################################################
	# MENU
	###################################################################

	def menuContent(self, menu):
		try: return menu['content']
		except: return None

	def menuRelease(self, menu):
		try: return menu['release']
		except: return None

	def menuProgress(self, menu):
		try: return menu['progress']
		except: return None

	def menuParameters(self, menu):
		try: return menu['parameters']
		except: return None

	def menuNiche(self, menu):
		try: return menu['niche']
		except: return None

	def menuSeason(self, menu):
		try: return self.menuParameters(menu = menu)['season']
		except: return None

	def menuList(self, menu):
		try: return self.menuParameters(menu = menu)['list']
		except: return None

	def menuProvider(self, menu):
		try: return self.menuParameters(menu = menu)['provider']
		except: return None

	def menuTypeSmart(self, menu):
		return self.menuContent(menu = menu) in (MetaTools.ContentQuick, MetaTools.ContentProgress, MetaTools.ContentArrival)

	def menuTypeQuick(self, menu):
		return self.menuContent(menu = menu) == MetaTools.ContentQuick

	def menuTypeProgress(self, menu):
		return self.menuContent(menu = menu) == MetaTools.ContentProgress

	def menuTypeProgressDefault(self, menu):
		return self.menuProgress(menu = menu) == MetaTools.ProgressDefault

	def menuTypeProgressOther(self, menu):
		return self.menuTypeProgress(menu = menu) and not self.menuTypeProgressDefault(menu = menu)

	def menuTypeArrival(self, menu):
		return self.menuContent(menu = menu) == MetaTools.ContentArrival

	def menuTypeFavorite(self, menu):
		try: return self.menuContent(menu = menu) == 'list' and self.menuList(menu = menu) in MetaTools.ListsFavorite and self.menuProvider(menu = menu) in (MetaTools.ProviderTrakt, MetaTools.ProviderImdb)
		except: return None

	def menuTypeWatchlist(self, menu):
		try: return self.menuList(menu = menu) == MetaTools.ListWatchlist
		except: return False

	###################################################################
	# SELECT
	###################################################################

	def select(self, items, menu = None, submenu = None):
		try:
			if items:
				plays = []
				for i in range(len(items)):
					item = items[i]
					metadata = item.get('metadata')
					if metadata: # Ignore recaps and extras, which do not have metadata.
						play = {'time' : 0, 'count' : 0, 'progress' : 0, 'media' : metadata.get('media'), 'season' : metadata.get('season'), 'episode' : metadata.get('episode'), 'item' : item}
						time = metadata.get('lastplayed')
						if time: play['time'] = Time.integer(time)
						count = metadata.get('playcount')
						if count: play['count'] = count
						progress = items[i]['data'][1].getProperty(MetaTools.PropertyProgress)
						if progress: play['progress'] = float(progress)
						plays.append(play)

				if plays:
					# Ignore specials, except if we are in the specials menu.
					special = len(Tools.listUnique([i['season'] for i in plays])) == 1 and plays[0]['season'] == 0
					if not special: plays = [i for i in plays if i.get('season')]

					index = None

					# For episode, series, sequential, and absolute menus.
					# If all episodes were watched the exact same number of times, do not auto-select the last episode, but rather the first one.
					# This is because the user probably wants to rewatch the season.
					if self.menuContent(menu = menu) == Media.Episode and (not submenu or submenu == MetaTools.SubmenuSerie or submenu == MetaTools.SubmenuSequential or submenu == MetaTools.SubmenuAbsolute):
						count = plays[0].get('count')
						if count and all(i.get('count') == count and not i.get('progress') for i in plays): # Do not do if an episode has playback progress.
							first = min(plays, key = lambda i : i['episode'])
							if first: index = plays.index(first)

					if index is None:
						# Always get the episode with the LOWEST season-episode number if all the previous values are the same.
						# Hence, subtract to make sure the max() function selects the first episode at that point.
						# Important for menus where all episodes are unwatched, in which case it should select the first episode.
						def _inverse(value): return 999999999 - int(value)

						# First try to pick an in-progress item, in case all have the same count, but one was rewatched without being finished.
						# Do this first, because this one should not increment to the next episode.
						busy = max(plays, key = lambda i : (i['time'], i['count'], i['progress'], _inverse(i['season']), _inverse(i['episode'])))
						if busy and busy['progress']:
							index = plays.index(busy)
						else:
							# All episodes could have the same play count, and even the same play time, if all were batch-marked as watched in one go.
							# Hence, also incorporate the episode number.
							last = max(plays, key = lambda i : (i['time'], i['count'], i['progress'], _inverse(i['season']), _inverse(i['episode'])))
							if last:
								# Find the next unplayed or less-watched episode.
								# If no further episodes are availaible, stick to the last watched one.

								index = plays.index(last) # The last played episode.
								for i in range(index + 1, len(plays)):
									# Make sure this still selects the first episode if the all episodes in the menu are unwatched (the count needs to be less).
									if (special or plays[i].get('season')) and plays[i].get('count') < last.get('count'):
										index = i
										break

					if not index is None:
						item = plays[index]['item']
						item['data'][1].setProperty(MetaTools.PropertySelect, '1')
						return item
		except: Logger.error()
		return None

	def selectIndex(self, items, more = True, adjust = False):
		try:
			for i in range(len(items)):
				if items[i][1].getProperty(MetaTools.PropertySelect):
					return i
		except: Logger.error()
		return None

	###################################################################
	# STREAM
	###################################################################

	def stream(self, duration = None, videoCodec = None, videoAspect = None, videoWidth = None, videoHeight = None, audioCodec = None, audioChannels = None, audioLanguage = None, subtitleLanguage = None):
		# https://alwinesch.github.io/group__python__xbmcgui__listitem.html#ga99c7bf16729b18b6378ea7069ee5b138

		audioLanguage = [audioLanguage] if audioLanguage and not Tools.isArray(audioLanguage) else []
		subtitleLanguage = [subtitleLanguage] if subtitleLanguage and not Tools.isArray(subtitleLanguage) else []

		video = []
		audio = []
		subtitle = []

		# Video
		data = {}
		if duration: data[MetaTools.StreamDuration] = duration
		if videoCodec: data[MetaTools.StreamCodec] = videoCodec
		if videoAspect: data[MetaTools.StreamAspect] = videoAspect
		if videoWidth: data[MetaTools.StreamWidth] = videoWidth
		if videoHeight: data[MetaTools.StreamHeight] = videoHeight
		if data:
			if self.mKodiNew: data = VideoStreamDetail(**data) # Kodi 20+
			video.append(data)

		# Audio
		for i in audioLanguage:
			if i:
				data = {}
				if audioCodec: data[MetaTools.StreamCodec] = audioCodec
				if audioChannels: data[MetaTools.StreamChannels] = audioChannels
				data[MetaTools.StreamLanguage] = i
				if data:
					if self.mKodiNew: data = AudioStreamDetail(**data) # Kodi 20+
					audio.append(data)

		# Subtitle
		for i in subtitleLanguage:
			if i:
				data = {}
				data[MetaTools.StreamLanguage] = i
				if data:
					if self.mKodiNew: data = SubtitleStreamDetail(**data) # Kodi 20+
					subtitle.append(data)

		return {MetaTools.StreamVideo : video, MetaTools.StreamAudio : audio, MetaTools.StreamSubtitle : subtitle}

	###################################################################
	# ITEM
	###################################################################

	def items(self,
		metadatas,

		media = None,
		niche = None,

		item = None,
		stream = None,
		properties = None,
		playable = None,
		multiple = None,
		mixed = None,
		menu = None,
		submenu = None,
		more = None,
		recap = None,
		extra = None,
		progress = None,
		decorate = None,

		context = None,
		contextAdd = None,
		contextMode = None,
		contextLibrary = None,
		contextPlaylist = None,
		contextShortcut = None,

		hide = False,
		hideSearch = False,
		hideRelease = False,
		hideWatched = False,

		label = True,
		command = True,
		clean = True,
		images = True,
	):
		if media is None: media = self.media(metadata = metadatas)
		if multiple is None: multiple = self.multiple(metadata = metadatas) if (media == Media.Season or media == Media.Episode) else False
		if mixed is None: mixed = media == Media.Mixed

		if submenu is None:
			# Show + Mixed:
			#	Quick: Episode submenu (including the Arrivals/Random items which we might have wanted to open with a Season submenu).
			#	Progress: Episode submenu.
			#	Arrivals: Season submenu.
			# The media is set to Show in MetaMenu.buildMedia(), since the layout/view looks better for shows than for episodes.
			# Do not use "metadatas[0].get('season')", since we still want the show submenus for Arrivals.
			mediad = media
			if media == Media.Show and not metadatas[0].get('episode') is None:
				mediad = Media.Episode
			elif media == Media.Mixed:
				for metadata in metadatas:
					if Media.isSerie(metadata.get('media')):
						if metadata.get('episode') is None: mediad = None # Not for Mixed Arrivals menu.
						break
			submenu = self.submenu(media = mediad, multiple = multiple)

		items = []
		if not mixed and media == Media.Episode and sum(Tools.listUnique([i['season'] for i in metadatas if 'season' in i and not i['season'] == 0])) > 1:
			# NB: when there are submenus in the Progress menu that contain episodes from multiple seasons (eg: last episodes of S02 and first episodes of S03).
			# The season extras, recap, and the occasional special episodes between seasons, are all mixed up (eg: S03 recap is listed before S02 extras).
			# This is because adding the recap/extras item cannot deal with multiple seasons, always moving the recap before the extras while assuming it is the same season.
			# Instead, break the episodes into chuncks, one for each season.
			# Process each subset separately, each with their own recap/extras, and then combine them into one linear list.

			index = -1
			season = -1
			chunks = []
			for i in range(len(metadatas)):
				metadata = metadatas[i]

				number = metadata.get('season')
				if number is None: number = -1

				# Determine for special episodes between seasons, if they belong to the previous or next season (closest release date).
				if number == 0:
					timePrevious = 0
					for j in range(i, 0, -1):
						if metadatas[j]['season'] > 0:
							time = None
							try: time = item['aired']
							except: pass
							if not time:
								try: time = item['premiered']
								except: pass
							if time:
								timePrevious = Time.integer(time)
								break

					timeNext = 0
					for j in range(i, len(metadatas)):
						if metadatas[j]['season'] > 0:
							time = None
							try: time = item['aired']
							except: pass
							if not time:
								try: time = item['premiered']
								except: pass
							if time:
								timeNext = Time.integer(time)
								break

					if timeNext > timePrevious:
						chunks.append([])
						index += 1

				if index < 0 or (number > 0 and not number == season):
					chunks.append([])
					index += 1
					if number > 0: season = number
				if season < 0 or number > 0: season = number
				chunks[index].append(metadata)
		else:
			chunks = [metadatas]

		if menu:
			menu['media'] = media
			menu['mixed'] = mixed
			menu['multiple'] = multiple
			menu['submenu'] = submenu

		for chunk in chunks:
			items.append(self._items(
				metadatas = chunk,

				media = media,
				niche = niche,

				item = item,
				stream = stream,
				properties = properties,
				playable = playable,
				multiple = multiple,
				mixed = mixed,
				menu = menu,
				submenu = submenu,
				recap = recap,
				extra = extra,
				progress = progress,
				decorate = decorate,

				context = context,
				contextAdd = contextAdd,
				contextMode = contextMode,
				contextLibrary = contextLibrary,
				contextPlaylist = contextPlaylist,
				contextShortcut = contextShortcut,

				hide = hide,
				hideSearch = hideSearch,
				hideRelease = hideRelease,
				hideWatched = hideWatched,

				label = label,
				command = command,
				clean = clean,
				images = images,
			))
		items = Tools.listFlatten(data = items, recursive = False)

		# Make sure that special episodes are listed after the recap.
		# Check the series menu for Game of Thrones S02 and S03 which has specials before E01.
		# Only do this for series menus, otherwise the recap will be pulled above specials from the previous seaosn in Arrivals/Progress.
		if self.submenuIs(submenu = submenu, type = MetaTools.SubmenuSerie):
			try:
				for i in range(len(items)):
					if 'metadata' in items[i]:
						if not items[i]['metadata'].get('season') == 0: break
					else:
						items.insert(0, items.pop(i))
						break
			except: Logger.error()

		if more:
			itemMore = self.itemMore(metadata = metadatas, media = media, niche = niche, multiple = multiple, submenu = submenu, data = more)
			if itemMore:
				items.append({'data' : itemMore})

				# Do not display extras in episode menus where there is a next page. Only display on last page.
				if not submenu:
					for i in range(len(items)):
						if items[i].get('media') == Media.Extra:
							del items[i]
							break

		# Specify the last watched episode to auto-select from view.py.
		if Media.isEpisode(media): self.select(items = items, menu = menu, submenu = submenu)

		return [item['data'] for item in items]

	def _items(self,
		metadatas,

		media = None,
		niche = None,

		item = None,
		stream = None,
		properties = None,
		playable = None,
		multiple = None,
		mixed = None,
		menu = None,
		submenu = None,
		recap = None,
		extra = None,
		progress = None,
		decorate = None,

		context = None,
		contextAdd = None,
		contextMode = None,
		contextLibrary = None,
		contextPlaylist = None,
		contextShortcut = None,

		hide = False,
		hideSearch = False,
		hideRelease = False,
		hideWatched = False,

		label = True,
		command = True,
		clean = True,
		images = True,
	):
		# Important that lists (eg: Favorites -> Trakt -> Lists -> Personal Lists) are marked as folders.
		# Otherwise the lists cannot be used for skin widgets.
		folder = None if media == Media.Mixed else bool((submenu and not media == Media.Episode) or (media == Media.List or media == Media.Set or media == Media.Show or media == Media.Season))

		seasons = []
		items = []
		itemsRecap = []
		itemsExtra = []

		for metadata in metadatas:
			try:
				item = self.item(
					metadata = metadata,

					# Add "mixed = True" so that episodes in the main/mixed Progress/Quick are listed as shows, not just the show Progress/Quick menus.
					# This is also important for Playback.dialogWatch() to ask if the entire show/season should be marked, or only the single episode.
					media = self.media(metadata = metadata, mixed = True) if mixed else media,
					niche = self.niche(metadata = metadata) if mixed else niche,

					stream = stream,
					properties = properties,
					playable = playable,
					multiple = multiple,
					mixed = mixed,
					menu = menu,
					submenu = submenu,
					progress = progress,
					decorate = decorate,

					context = context,
					contextAdd = contextAdd,
					contextMode = contextMode,
					contextLibrary = contextLibrary,
					contextPlaylist = contextPlaylist,
					contextShortcut = contextShortcut,

					hide = hide,
					hideSearch = hideSearch,
					hideRelease = hideRelease,
					hideWatched = hideWatched,

					label = label,
					command = command,
					clean = clean,
					images = images
				)
				if item:
					itemMedia = self.media(metadata)

					if folder is None: itemFolder = bool((submenu and not media == Media.Episode) or (itemMedia == Media.Set or itemMedia == Media.Show or itemMedia == Media.Season))
					else: itemFolder = folder

					# gaiasubmenu - Check MetaTools.submenuSpecial() for more info.
					if item.get('folder') is False: itemFolder = False

					# When using "folder=True", Kodi 20+ does not add progress icons to show/season menu entries (some unwatched episodes remaining).
					# Not sure if doing this removes any functionality, since Kodi does not treat it like a folder anymore.
					# Update: Doing this treats show/season menu like a normal action. When opening them, MetaMenu.menu() will start a new process for this to update the container in, since there is no Kodi handle, and this obviously takes longer.
					# We might still need this due to the old bug that made Kodi recursivley scan subfolders when eg opening the context menu on a "folder" item. More in under submenuSpecial().
					# Update (2025-05): Also reset this for movies. Otherwise movies in mixed menus (eg: Quick Mixed) are marked as a folder, since "submenu" has a value due to episodes being in the menu, and then the movies do not get a progress icon.
					#gaiafuture - If this is ever fixed in Kodi, this line can be commented out to allow for faster show/season menu access.
					if itemMedia == Media.Movie or itemMedia == Media.Set or itemMedia == Media.Show or itemMedia == Media.Season: itemFolder = False

					if 'season' in metadata: seasons.append([metadata.get('season'), metadata.get('episode')])
					items.append({'metadata' : item['metadata'], 'data' : [item['command'], item['item'], bool(itemFolder)]})

					# Add here instead of after the loop, since recaps/extras have to be inserted between episodes for flattened menus.
					# Insert AFTER the episode item() above was created, since we want to use the cleaned metadata with the watched status.
					# There can be multiple recaps/extras for multiple submenus (if the number of episodes listed is less than the multiple page limit).
					if recap or extra:
						cleaned = Tools.update(self.copy(metadata), item['metadata'])
						if recap:
							item = self.itemRecap(metadata = cleaned, media = media, multiple = multiple, submenu = submenu)
							if item: itemsRecap.append({'index' : len(items) - 1, 'season' : cleaned['season'], 'item' : {'media' : Media.Recap, 'data' : item}})
						if extra:
							# If a season is still continuing (not ended yet) with a few unreleased/future episodes (without a date), the "Season Extras" item often gets added after the last aired episodes, but before the unreleased episodes.
							# Make sure it is only added after the last episode in the menu.
							# Eg: One Piece S22
							# This will then not show the season extras if the last episode was not aired yet.
							# Not sure if this removes season extras from some menus where it should actually be.
							last = None
							season = metadata.get('season')
							for episode in reversed(metadatas):
								if episode.get('season') == season:
									last = episode
									break
							if metadata == last:
								item = self.itemExtra(metadata = cleaned, media = media, multiple = multiple, submenu = submenu)
								if item: itemsExtra.append({'index' : len(items) - 1, 'season' : cleaned['season'], 'item' : {'media' : Media.Extra, 'data' : item}})
			except: Logger.error()

		offset = 0
		if itemsRecap:
			for itemMore in itemsRecap: # Iterate from front to back.
				index = 0
				itemIndex = itemMore['index']
				itemSeason = itemMore['season']
				for i in range(itemIndex, -1, -1): # If special episodes are interleaved, make sure the recap/extra is placed before/after all interleaved specials.
					if seasons[i][0] == 0 or seasons[i][1] == 0: index -= 1 # Place BEFORE SxxE00 (specials from IMDb).
					elif seasons[i][0] < itemSeason: break
				for i in range(itemIndex, len(seasons)):
					if seasons[i][0] > 0 and seasons[i][0] >= itemSeason:
						index += i
						break
				items.insert(index + offset, itemMore['item'])
				offset += 1

		if itemsExtra:
			found = {}
			for itemMore in reversed(itemsExtra): # Iterate from back to front.
				index = 0
				itemIndex = itemMore['index']
				itemSeason = itemMore['season']
				for i in range(itemIndex, len(seasons)): # If special episodes are interleaved, make sure the recap/extra is placed before/after all interleaved specials.
					if seasons[i][0] == 0: index += 1
					elif seasons[i][0] > itemSeason: break
				for i in range(itemIndex, -1, -1):
					if seasons[i][0] > 0 and seasons[i][0] <= itemSeason:
						index += i + 1
						break

				# Sometimes Trakt has more episodes in the season than TVDb.
				# The pack data will therefore have 1 less episode than the actual episode list.
				# Eg: Shark Tank India S01 has 35 episodes on TVDb and 36 episodes on Trakt (last episode is online special).
				# This will add 2 Season Extras menus, one after E35 and one after E36.
				# Start from the back and only add
				if not itemSeason in found:
					found[itemSeason] = True
					items.insert(index + offset, itemMore['item'])

		return items

	def itemsExtra(self,
		metadata,
		item = None,
		command = True,
		clean = True,
		images = True
	):
		media = Media.Episode
		query = metadata['tvshowtitle']

		for i in ['episode', 'premiered', 'genre', 'rating', 'userrating', 'votes', 'voting', 'duration']:
			try: del metadata[i]
			except: pass

		items = []
		videos = [Trailer, Recap, Review, Reaction, Bonus, Deleted, Production, Direction, Interview, Explanation, Alternation]
		for video in videos:
			try:
				if video.enabled():
					metadatad = Tools.copy(metadata) # Copy, otherwise the extra type in itemDetail() will add the prefix/suffix to the same dict shared by all the extras.
					metadatad['query'] = query
					metadatad['duration'] = video.Duration
					metadatad['title'] = metadatad['originaltitle'] = metadatad['tagline'] = Translation.string(video.Label)
					metadatad['plot'] = Translation.string(video.Description) % (str(metadatad['season']), query)

					item = self.item(
						metadata = metadatad,

						media = Media.Extra,

						contextMode = Context.ModeVideo,

						video = video.Id,
						label = metadatad['title'],
						command = command,
						clean = clean,
						images = images
					)
					if item: items.append([item['command'], item['item'], False])
			except: Logger.error()

		return items

	'''
		clean:
			True: Clean the metadata before adding it to the item.
			False: Do not clean the metadata before adding it to the item. This assumes that the "metadata" parameter wass already cleaned.
			Dictionary: An already cleaned metadata dictionary. Can be used to avoid cleaning and already cleaned dictionary.
		stream:
			dictionary created by stream().
		properties:
			dictionary with custom properties.
		multiple:
			Whether or not the seasons/episodes are from different shows.
		mixed:
			Whether or not the items are a mixture of movies and shows.
		extend:
			Add extra info to the label or plot.
			Should mostly be used with items in a menu, but not items in the player.
		images:
			True: Extract images from the metadata and add them to the item.
			False: Do not extract images from the metadata and do not add them to the item.
			Dictionary: Use already extracted images and add them to the item.
		context:
			True: Add a context menu to the item.
			False: Do not add a context menu to the item.
			None: Use the settings to determine wether or not to add a context menu to the item.
	'''
	def item(self,
		metadata,

		media = None,
		niche = None,

		item = None,
		stream = None,
		properties = None,
		playable = None,
		video = None,
		multiple = False,
		mixed = False,
		menu = None,
		submenu = False,
		progress = False,
		decorate = None,

		context = None, # If False, do not create a context menu.
		contextAdd = None, # Add the context to the list item. Otherwise the context menu iss just returned.
		contextMode = None, # The type of context menu to create.
		contextCommand = None, # The link/command for the context menu.
		contextLibrary = None, # The link/command to add to the library. If True, uses contextCommand.
		contextPlaylist = None, # Wether or not to allow the item to be queued to the playlist.
		contextSource = None, # The stream source dictionary for stream list items.
		contextOrion = None, # Orion identifiers for stream list items.
		contextShortcut = None, # The dictionary with shortcut details.
		contextMixed = None, # The context was added from a menu that has a mix of different movies/shows.

		hide = False,
		hideSearch = False,
		hideRelease = False,
		hideWatched = False,

		extend = True,
		extendLabel = True,
		extendTagline = True,
		extendPlot = True,

		label = True,
		detail = True,
		command = True,
		clean = True,
		images = True,
		content = True,

		cleanStudio = True,
		cleanExclude = False,
		cleanIcon = True,
	):
		mediaOriginal = media
		if not media: media = mediaOriginal = self.media(metadata = metadata)

		# Hide special seasons and episodes.
		if (media == Media.Season or media == Media.Episode) and not self.mShowSpecialSeason and metadata.get('season') == 0: return None
		elif media == Media.Episode and not self.mShowSpecialEpisode and not metadata.get('episode'): return None

		if not extend:
			extendLabel = extend
			extendTagline = extend
			extendPlot = extend

		future = None
		if content:
			# Hide future seasons and episodes.
			# Calculate the future value for all media types, so that future/unaired episodes in the Progress menu are made italics from label().
			# It should at least be done for shows, seasons, and episodes. Movies might not be necessary.
			#future = self.itemFuture(metadata = metadata, media = media) if (media == Media.Season or media == Media.Episode) else None
			future = self.itemFuture(media = media, metadata = metadata)
			if (media == Media.Season and not self.mShowFutureSeason) or (media == Media.Episode and not self.mShowFutureEpisode):
				futureAge = future.get('age')
				if futureAge is None: return None # No release date.
				elif futureAge > -MetaTools.TimeNewShow: return None # Released in the past 3 hours or sometime in the future.

		if not item: item = self.itemCreate()
		tag = self.itemTag(item = item)

		if content:
			# Add missing attributes.
			# Will be removed by clean(), but added to commands and context.
			self.itemShow(media = media, item = item, metadata = metadata)

			# Must be before clean() and setInfo().
			self.itemPlayback(media = media, item = item, tag = tag, metadata = metadata, mixed = mixed, progress = progress, menu = menu)

			# Must be before setInfo() and itemPlot().
			# Must be after itemPlayback().
			if detail: self.itemDetail(media = media, item = item, metadata = metadata, future = future, mixed = mixed, progress = progress, menu = menu, submenu = submenu)

			# Must be before setInfo().
			self.itemDate(media = media, item = item, metadata = metadata)

			# Must be before setInfo().
			# Must be before itemShow().
			self.itemTagline(media = media, item = item, metadata = metadata, extend = extendTagline)

			# Must be before setInfo().
			self.itemPlot(media = media, item = item, metadata = metadata, extend = extendPlot)

			if hide:
				if not hideSearch: # Always show watched items in the search menu.
					watched = None

					# For show Arrivals, hide title if the newly released season was fully watched.
					try: watched = metadata['count']['current']['watched'] and not metadata['count']['current']['rewatching']
					except: pass

					if watched is None:
						try: watched = (metadata.get('playcount') or 0) > 0
						except: watched = False

					if watched:
						if ((hideRelease and self.mHideRelease) or self.mHideAll) and (media == Media.Movie or media == Media.Show): return None # Only for movies/shows. Do not hide seasons/episodes in the submenus, even if self.mHideAll.
						if hideWatched and (not 'progress' in metadata or not metadata['progress']): return None # Skip episodes marked as watched for the unfinished list.

		# Must be done before the title/label is changed below.
		folder = None # gaiasubmenu - Check MetaTools.submenuSpecial() for more info.
		if command is True: command, folder = self.commandFolder(media = media, niche = niche, metadata = metadata, video = video, multiple = multiple, submenu = submenu)
		elif not command: command = None
		elif command: item.setPath(command)

		if clean is True: cleaned = self.clean(media = media, metadata = metadata, studio = cleanStudio, exclude = cleanExclude, icon = cleanIcon)
		elif Tools.isDictionary(clean): cleaned = clean
		else: cleaned = metadata

		# Adding Label or Label2 to the ListItem does not work.
		# Instead of the label, the title set in setInfo() is used.
		# This is most likley a skin bug (including the default Kodi skin), since skins seem to not check if there is a label, but only always just pick the title.
		# The only way to use a custom title seems to be to replace the title attribute.
		# Note that this will propagate to all places where the ListItem is used. Eg: The Kodi info dialog will show the custom label instead of the title and might eg have 2 years in the label.
		if label:
			if label is True:
				if media == Media.Person: label = metadata.get('label') or metadata.get('name') or metadata.get('title')
				else: label = self.label(metadata = metadata, media = mediaOriginal, future = future, multiple = multiple, mixed = mixed, extend = extendLabel, menu = menu, submenu = submenu, decorate = decorate)

			# Use original, since we can pass docu/short in.
			# Always force for seasons, since a few seasons have their own title and we do not want to have naming inconsistencies.
			# Eg: Breaking Bad's special season has an English title "Minisodes".
			# Update: not needed anymore, since the setting "metadata.title.layout" is now enabled by default.
			if self.mLabelForce: cleaned['title'] = label

			item.setLabel(label)

		# NB: call setInfo() first, before any of the other functions below.
		# Otherwise Kodi might replace values set by the other functions with the values from setInfo().
		# For instance, setInfo() will replace the values set by setCast(), and then actor thumbnails do not show in the Kodi info dialog.
		self.itemInfo(item = item, tag = tag, metadata = cleaned)

		self.itemId(item = item, tag = tag, metadata = metadata)
		self.itemVoting(item = item, tag = tag, metadata = metadata)
		self.itemCast(item = item, tag = tag, metadata = metadata)
		self.itemStream(item = item, tag = tag, metadata = metadata, stream = stream)
		self.itemProperty(item = item, properties = properties, playable = playable)

		images = self.itemImage(item = item, media = media, metadata = metadata, images = images, video = video, menu = menu, submenu = submenu, player = playable)

		if context is False:
			context = None
		else:
			if contextMode is None and not content: contextMode = Context.ModeStream

			# For episode submenus, make sure that the command passed to the context is the scrape command and not the episodesSubmenu command.
			# Eg: Open the Progress main menu -> open the context menu on an episode -> Scrape -> Rescrape -> this should launch the scrape process.
			if contextCommand is None and submenu: contextCommand = self.command(media = media, niche = niche, metadata = metadata, video = video, multiple = multiple, submenu = False, number = submenu)

			context = self.itemContext(item = item, context = context, add = contextAdd, mode = contextMode, media = mediaOriginal, niche = niche, video = video, command = contextCommand if contextCommand else command, library = contextLibrary, playlist = contextPlaylist, source = contextSource, metadata = metadata, orion = contextOrion, shortcut = contextShortcut, mixed = contextMixed)

		return {'item' : item, 'command' : command, 'context' : context, 'folder' : folder, 'metadata' : cleaned, 'images' : images}

	# ListItem passed to Kodi's player.
	def itemPlayer(self,
		metadata,

		media = None,
		niche = None,

		item = None,
		stream = None,
		properties = None,

		label = False,
		command = True,
		clean = True,
		images = True
	):
		return self.item(
			metadata = metadata,

			media = media,
			niche = niche,

			item = item,
			stream = stream,
			properties = properties,
			playable = True,
			multiple = False,

			context = False,

			hide = False,
			extend = False,

			label = label,
			command = command,
			clean = clean,
			images = images
		)

	def itemCreate(self):
		return self.mDirectory.item()

	def itemTag(self, item):
		if self.mKodiNew:
			try: return item.getVideoInfoTag() # Kodi 20+
			except: pass
		return False

	def itemShow(self, media, metadata, item):
		if metadata:
			# Replace missing/incorrect attributes for seasons/episodes that are displayed as shows.
			# Used for Quick and Progress menus.
			if media == Media.Show:
				try: serie = metadata['serie']['show']
				except: serie = None
				if serie:
					if not metadata.get('tagline'): metadata['tagline'] = serie.get('tagline')
					metadata['status'] = serie.get('status') # Replace episode status with show status.

			if media == Media.Show or media == Media.Season:
				if not metadata.get('tvshowtitle') and metadata.get('title'): metadata['tvshowtitle'] = metadata['title']
				if not metadata.get('tvshowyear') and metadata.get('year'): metadata['tvshowyear'] = metadata['year']

			# For Gaia Eminence.
			if media == Media.Episode:
				item.setProperty('GaiaShowNumber', Title.number(metadata = metadata))

				try: special = metadata['special']
				except: special = None

				specialType = None
				if special and 'type' in special: specialType = special['type']
				item.setProperty('GaiaShowSpecial', '-'.join(specialType) if specialType else '')

				specialStory = metadata['season'] > 0
				if not specialStory and special and 'story' in special: specialStory = special['story']
				item.setProperty('GaiaShowStory', str(int(False if specialStory is None else specialStory)))

				specialExtra = metadata['season'] == 0 or metadata['episode'] == 0
				if special and 'extra' in special: specialExtra = special['extra']
				item.setProperty('GaiaShowExtra', str(int(False if specialExtra is None else specialExtra)))

			elif media == Media.Extra or media == Media.Recap:
				item.setProperty('GaiaShowExtra', '1')

	def itemDetail(self, media, metadata, item = None, future = None, mixed = False, progress = False, menu = None, submenu = None):
		if metadata:
			activity = []
			label = []
			description = []

			season = metadata.get('season')
			episode = metadata.get('episode')

			serie = Media.isSerie(media)
			niche = metadata.get('niche')
			nicheMenu = self.menuNiche(menu = menu)

			try:
				futureKnown = future['known']
				futureUnknown = future['unknown']
				future = future['future']
			except:
				futureKnown = None
				futureUnknown = None
				future = None

			##############################
			# ACTIVITY DETAILS
			##############################

			if self.mLabelActivityEnabled:
				detailForce = False
				detailMedia = Media.Mixed if mixed else media
				detail = Detail.MenuGeneric
				if menu:
					if self.menuTypeQuick(menu = menu): detail = Detail.MenuQuick
					elif self.menuTypeArrival(menu = menu): detail = Detail.MenuArrival
					elif self.menuTypeProgressDefault(menu = menu): detail = Detail.MenuProgress
					elif self.menuTypeProgressOther(menu = menu):
						detailForce = True # Always enable for the other Progress menus in Favorites.
						detail = Detail.MenuProgress
				detail = self.mLabelActivityMenu[detail].get(Media.Mixed if mixed else Media.Extra if Media.isBonus(media) else media) or {}

				if detail:
					if self.mLabelPlayEnabled and self.mLabelPlayMedia.get(detailMedia) == Detail.ModeEnabled:
						playcount = metadata.get('playcount') or 0

						# Also show a playcount label if the titles is being rewatched.
						# Otherwise during rewatch, the watched checkmark icon is replaced with a progress icon, and the user cannot see that the show was fully watched already.
						rewatch = None
						if self.mLabelPlayThreshold >= 2 and playcount >= (self.mLabelPlayThreshold - 1):
							if serie:
								try: rewatch = metadata['count']['episode']['rewatched']
								except: pass
							if rewatch is None:
								progression = metadata.get('progress')
								if progression:
									playback = self._playback()
									if progression < (playback.ProgressEndShow if serie else playback.ProgressEndMovie): rewatch = True

						if playcount >= self.mLabelPlayThreshold or rewatch:
							activity.append({'label' : 32006, 'value' : str(playcount), 'icon' : Font.IconWatched, 'color' : Format.colorExcellent()})

					# For mixed menus, do not add the progress if it is <= 1% or >= 99%.
					# Still show the progress for unfinished lists.
					if self.mLabelProgressEnabled and self.mLabelProgressMedia.get(detailMedia) == Detail.ModeEnabled:
						if not metadata.get('busy') is False: # Set by itemPlayback() to not show progress labels in the lower 90% if the title was marked as watched recently.
							progression = None
							progressMinimum = 0.01
							progressMaximum = 0.99
							if Tools.isArray(progress): # Used from MetaMenu.buildMedia().
								if progress[0] is False: progressMinimum = -1.0
								elif Tools.isNumber(progress[0]): progressMinimum = progress[0]
								if progress[1] is False: progressMaximum = 2.0
								elif Tools.isNumber(progress[1]): progressMaximum = progress[1]
								progress = None

							# For shows and seasons, display the progress percentage as the number of episodes watched.
							if media == Media.Show or media == Media.Season:
								# Only use the rewatch rate if the user is currently rewatching the show.
								# Eg: Severance: watch all episodes of S01 twice. Watch the first half of episodes of S02 (last season).
								try: watched = metadata['count']['episode']['watched']
								except: watched = 0
								try: rewatched = metadata['count']['episode']['rewatched']
								except: rewatched = 0
								try: rewatching = metadata['count']['episode']['rewatching']
								except: rewatching = None
								if rewatching: watched = rewatched
								if watched:
									try:
										progression = watched / float(metadata['count']['episode']['total'])
										if progression == 1: progression = None
										progressMinimum = -1.0
										progressMaximum = 2.0
									except: pass
								else:
									# No episode fully watched. Only an episode in progress.
									try: progression = metadata.get('progress') / float(metadata['count']['episode']['total'])
									except: pass
							else:
								progression = metadata.get('progress')

							if not progression is None:
								if progress or (not mixed and not progress is None) or (progression > progressMinimum and progression < progressMaximum):
									if progression >= 0.0 and progression < 0.01: progression = 0.01 # If progress is eg 0.4%, show as 1%.
									elif progression >= 0.99:
										# If a show has more than 100 episodes and all but one was watched, the progress is eg 99.7%.
										# Do not round up to 100%, otherwise the 100% label looks like the show was finished, although an episode is still left.
										if media == Media.Show or media == Media.Season: progression = 0.99
										else: progression = 1.0 # For movies/episodes assume that 99% is fully watched.

									format = '%.0f%%' if self.mLabelProgressFormat == 0 else '%d'
									activity.append({'label' : 32037, 'value' : format % (progression * 100.0), 'icon' : Font.IconProgress, 'color' : Format.colorPoor()})

					if self.mLabelRatingEnabled and self.mLabelRatingMedia.get(detailMedia) == Detail.ModeEnabled and not metadata.get('userrating') is None:
						format = '%d' if self.mLabelRatingFormat == 0 else '%.1f'
						activity.append({'label' : 35187, 'value' : format % metadata['userrating'], 'icon' : Font.IconRating, 'color' : Format.colorMedium()})

					if serie and self.mLabelAirEnabled and self.mLabelAirMedia.get(detailMedia) == Detail.ModeEnabled and 'airs' in metadata:
						try: airTime = metadata['airs']['time']
						except: airTime = None
						try: airDay = metadata['airs']['day'][0]
						except: airDay = None
						try: airZone = metadata['airs']['zone']
						except: airZone = None

						if airTime and airDay:
							if airZone:
								if self.mLabelAirZone == 1: zoneTo = airZone
								elif self.mLabelAirZone == 2: zoneTo = Time.ZoneUtc
								else: zoneTo = Time.ZoneLocal

								if self.mLabelAirTime == 0: formatOutput = '%I:%M %p'
								elif self.mLabelAirTime == 1: formatOutput = '%H:%M'

								abbreviate = self.mLabelAirDay == 1
								airTime = Time.convert(stringTime = airTime, stringDay = airDay, zoneFrom = airZone, zoneTo = zoneTo, abbreviate = abbreviate, formatOutput = formatOutput)
								if airDay:
									airDay = airTime[1]
									airTime = airTime[0]

							air = []
							if airDay: air.append(airDay)
							if airTime: air.append(airTime)
							if air:
								if self.mLabelAirFormat == 0: air = airTime
								elif self.mLabelAirFormat == 1: air = airDay
								elif self.mLabelAirFormat == 2: air = air = ' '.join(air)
								activity.append({'label' : 35032, 'value' : air, 'icon' : Font.IconCalendar, 'color' : Format.colorSpecial()})

					if activity:
						for type in (Detail.TypeLabel, Detail.TypeTagline, Detail.TypePlot):
							if not detailForce and detail.get(type) == Detail.ModeDisabled: continue
							format = self.mLabelActivityFormat[type]
							if format:
								value = Tools.copy(activity)
								decoration = format[Detail.Decoration]
								color = format[Detail.Format][Detail.Color]
								if format[Detail.Color] == Detail.ColorPalette: color = None
								elif format[Detail.Color] == Detail.ColorNone: color = False

								# For DecorationAbbreviate, use 'X' for progress, since otherwise there are 2 activities with the same letter 'P' (Plays vs Progress).
								if decoration == Detail.DecorationNone: value = [Format.fontColor(i['value'], color = None if color is False else (color or i['color'])) for i in value]
								elif decoration == Detail.DecorationComplete: value = [Format.fontColor('%s: %s' % (Translation.string(i['label']), i['value']), color = None if color is False else (color or i['color'])) for i in value]
								elif decoration == Detail.DecorationAbbreviate: value = [Format.fontColor('%s: %s' % ('X' if i['label'] == 32006 else Translation.string(i['label'])[0], i['value']), color = None if color is False else (color or i['color'])) for i in value]
								elif decoration == Detail.DecorationIcon: value = ['%s %s' % (Format.fontColor(Font.icon(i['icon']), color = None if color is False else (color or i['color'])), i['value']) for i in value]

								value = Format.iconJoin(value, color = Detail.color(format = format))
								value = Detail.format(data = value, format = format, color = False)

								attribute = type + ('Before' if format[Detail.Placement] == Detail.PlacementPrepend else 'After')
								valueCurrent = metadata.get(attribute)
								if valueCurrent: valueCurrent.append((value, format))
								else: valueCurrent = [(value, format)]
								metadata[attribute] = valueCurrent

			##############################
			# MEDIA DETAILS
			##############################

			detail = Detail.MenuGeneric
			if menu:
				if self.menuTypeQuick(menu = menu): detail = Detail.MenuQuick
				elif self.menuTypeArrival(menu = menu) or self.menuRelease(menu = menu): detail = Detail.MenuArrival
				elif self.menuTypeProgressDefault(menu = menu): detail = Detail.MenuProgress
			detail = self.mLabelMediaMenu[detail].get(Media.Mixed if mixed else Media.Extra if Media.isBonus(media) else media) or {}

			# Never add the label to menus of the same media, since they are almost always the same and clutter the menu.
			# Only add outlying media, such as specials, shorts, TV movies, and mini-series.
			detailFull = mixed or detail.get(Detail.TypeLabel) == Detail.ModeEnabled
			detailForce = False

			if self.mLabelMediaEnabled:
				type = metadata.get('type') or []
				specialSeason = Media.Season in type
				specialEpisodes = (MetaData.SpecialEpisode, MetaData.SpecialPilot)
				specialIncludes = (MetaData.SpecialImportant, MetaData.SpecialEpisode, MetaData.SpecialPilot)
				specialExcludes = (MetaData.SpecialUnimportant, MetaData.SpecialMovie)
				specialExtras = list(MetaData.SpecialExtra.keys())

				# Episode type labels.
				if Media.isEpisode(media):
					if self.menuSeason(menu = menu) == 0: # S0 menu.
						special = metadata.get('special')
						try:
							specialType = special['type'] or []
							try: specialFirst = specialType[0]
							except: specialFirst = None
							specialInclude = any(x in specialIncludes for x in specialType)
							specialExclude = any(x in specialExcludes for x in specialType)
							specialMain = specialInclude and not specialExclude # Exclude: Downton Abbey S00E18-19.

							# Eg: Downton Abbey S00E18-19.
							if MetaData.SpecialMovie in specialType:
								label.append(35496)
								description.append(36822)
							# Eg: Money Heist S00E01 and S00E14.
							elif specialMain and Media.Premiere in type:
								label.append(36000)
								description.append(36815 if Media.Middle in type else 36813)
							# Eg: Money Heist S00E15 and S00E22.
							elif specialMain and Media.Finale in type:
								label.append(36005)
								description.append(36816 if Media.Middle in type else 36814)
							elif specialSeason and MetaData.SpecialEpisode in specialType:
								# Eg: Money Heist S0.
								label.append(36091)
								description.append(36832)
							elif specialFirst == MetaData.SpecialImportant:
								label.append(33111)
								description.append(36011)
							else:
								labeled = Translation.string(35149) if specialFirst == MetaData.SpecialUnimportant else specialFirst.capitalize()
								label.append(labeled)
								description.append(labeled + ' ' + Translation.string(33105))
						except: Logger.error()
					else:
						# Test this with:
						#	Dragon Ball Super S02+ (S02E01, S02E13, S03E01, S05E01, S5E55)
						#	The 100 S07 (S07E09/S07E10, S07E12/S07E13)
						#	Lost S06 (S06E17/S06E18)

						# Do not label unaired/future episodes as "Alternate Premiere", "Alternate Episode", etc.
						# The new season might only be on TVDb, but not on Trakt/TMDb yet, and will therefore be marked as an unofficial episode.
						time = self.time(type = MetaTools.TimePremiere, metadata = metadata, estimate = False, fallback = False)
						released = time and time < self.mTimeCurrent
						try: finished = metadata['serie']['season']['status'] in MetaTools.StatusesPast
						except: finished = False
						alternate = False
						if Media.Alternate in type and not future:
							if released: alternate = True
							elif not time:
								# For episodes only on IMDb.
								# Eg: The Tonight Show Starring Jimmy Fallon S08E206 (IMDb finale).
								# Eg: The Tonight Show Starring Jimmy Fallon S08E198+.
								try: ids = metadata['id']['episode']
								except: ids = None
								if ids and ids.get('imdb') and len([i for i in ids.values() if i and not Tools.isDictionary(i)]) == 1: alternate = True

						if futureUnknown and season:
							# Only future episodes without an air date.
							# Nopt for unaired episodes of a currently running season which has air dates.
							label.append(36601)
							description.append(35118)
						elif Media.Premiere in type and not Media.Special in type and not season == 0:
							label.append(36000)
							if Media.Outer in type: description.append(36827 if (specialSeason and alternate) else 36001)
							elif Media.Middle in type: description.append(36825 if (specialSeason and alternate) else 36003)
							elif Media.Inner in type: description.append(36829 if (specialSeason and alternate) else 36004 if alternate else 36002) # Money Heist S04E01 (only on IMDb).
							elif alternate: description.append(36004)
						elif Media.Finale in type and not Media.Special in type and not season == 0:
							label.append(36005)
							if Media.Outer in type: description.append(36826 if (specialSeason and alternate) else 36006)
							elif Media.Middle in type: description.append(36824 if (specialSeason and alternate) else 36008)
							elif Media.Inner in type: description.append(36828 if (specialSeason and alternate) else 36009 if alternate else 36007) # One Piece S01E60 (TVDb S04 finale).
							elif alternate: description.append(36009)
						elif Media.Special in type or Media.Exclusive in type:
							special = metadata.get('special') or {}
							specialType = special['type'] or []
							specialInclude = any(x in specialIncludes for x in specialType)
							specialExclude = any(x in specialExcludes for x in specialType)
							specialEpisode = any(x in specialEpisodes for x in specialType)
							specialExtra = any(x in specialExtras for x in specialType)
							specialMain = specialInclude and not specialExclude # Exclude: Downton Abbey S00E18-19.

							if season == 0:
								# Eg: Downton Abbey S00E18-19.
								if MetaData.SpecialMovie in specialType:
									label.append(35496)
									description.append(36817)
								# Eg: Money Heist S00E01 and S00E14.
								# Eg: Downton Abbey S02E09.
								elif specialMain and Media.Premiere in type:
									label.append(33105)
									if specialInclude: description.append(36820 if Media.Middle in type else 36818)
									else: description.append(36815 if Media.Middle in type else 36813)
								# Eg: Money Heist S00E15 and S00E22.
								# Eg: Downton Abbey S02E09 vs S00E02.
								elif specialMain and Media.Finale in type:
									label.append(33105)
									if specialInclude: description.append(36821 if Media.Middle in type else 36819)
									else: description.append(36816 if Media.Middle in type else 36814)
								# Eg: Downton Abbey Series menu at S02 (specials).
								elif special.get('story') and submenu:
									label.append(33105)
									if MetaPack.NumberUniversal in type: description.append(36011) # Heroes S00E01 + S01E00 in the Series menu.
									elif specialSeason and specialEpisode: description.append(36831) # Money Heist S00E01+ in the Series menu. Not for Heroes S00E23 in the Series menu.
									else: description.append(36011)
								# Eg: House S00E
								# Exclude unimportant specials that were incorrectly marked as finales on TVDb.
								# Eg: Heroes S00E56 in the Series menu.
								elif special.get('story') or (not specialExtra and (Media.Premiere in type or Media.Finale in type)):
									label.append(33111)
									if Media.Premiere in type:
										if Media.Outer in type: description.append(36001)
										elif Media.Middle in type: description.append(36003)
										elif alternate: description.append(36004)
										elif Media.Inner in type: description.append(36002)
									elif Media.Finale in type:
										if Media.Outer in type: description.append(36006)
										elif Media.Middle in type: description.append(36008)
										elif alternate: description.append(36009)
										elif Media.Inner in type: description.append(36007)
									else:
										description.append(36011)
								elif special.get('extra'):
									label.append(35653)
									try: description.append(special['type'][0].capitalize() + ' ' + Translation.string(33105))
									except: description.append(36012)
							else:
								# Mark IMDb specials as storyline specials.
								# Not sure if this is always the case.
								# Eg: LEGO Masters S03E00.
								label.append(33105)

								# Eg: Downton Abbey S02E09 should use a different description in S01 vs Series menu.
								# Eg: QI S21E17 and S22E16.
								storySpecial = (special.get('story') or episode == 0)
								storyOfficial = MetaPack.NumberOfficial in type
								if submenu and storySpecial and Media.Premiere in type: description.append(36818) # Eg: Downton Abbey
								elif submenu and storySpecial and Media.Finale in type: description.append(36819) # Eg: Downton Abbey
								elif storyOfficial and Media.Premiere in type: description.append(36835) # Eg: QI
								elif storyOfficial and Media.Finale in type: description.append(36836) # Eg: QI
								elif storySpecial or storyOfficial: description.append(36011)
								elif special.get('extra'): description.append(36012)
						elif type and MetaPack.NumberUnofficial in type and (released or finished):
							# Not for unreleased/future episodes.
							# Allow for unreleased/future episodes, if the season finished and the metadata is on TVDb, but not on Trakt yet, and TVDb maps to a different season.
							# Eg: LEGO Masters S05E05+ (TVDb) vs S06E05+ (Trakt).
							# This will change once S06E06 is on Trakt, which is currently not.
							# Can also be a finale.
							# Eg: Lost S01E25.
							if detailFull: label.append(33504)
							description.append(36830 if (specialSeason and Media.Standard in type) else 32535)
						elif not type or Media.Standard in type:
							if detailFull: label.append(36091)
							description.append(36830 if (specialSeason and alternate) else 36010)
						elif futureKnown:
							label.append(36601)
							description.append(35118)

				# Season Recap and Extras type labels.
				elif Media.isBonus(media):
					if detailFull: label.append(36758)
					description.append(metadata.get('originaltitle'))

				# Add media labels for:
				#	1. Top-level mixed menus.
				#	2. Progress/Arrivals menus.
				#	3. Release menus.
				#	4. Niche Arrivals menus.
				else:
					new = 15768000 * (2 if menu and menu.get('niche') else 1)
					time = self.time(type = MetaTools.TimeHome, metadata = metadata, estimate = False, fallback = [MetaTools.TimeLaunch, MetaTools.TimeDebut, MetaTools.TimePremiere])
					age = (self.mTimeCurrent - time) if time else 9999999999

					if Media.isMovie(media):
						if Media.isShort(niche):
							if detailFull or not Media.isShort(nicheMenu): label.append(35110)
							description.append(36015)
						elif Media.isSpecial(niche):
							if detailFull or not Media.isSpecial(nicheMenu): label.append(33105)
							description.append(36014)
						elif Media.isTelevision(niche): # After specials, since most specials are also TV movies.
							if detailFull or not Media.isTelevision(nicheMenu): label.append(36561)
							description.append(36013)
						else:
							if detailFull: label.append(35496)
							description.append(36461)
					elif Media.isSet(media):
						if detailFull: label.append(35534)
						description.append(36730)
					elif Media.isSeason(media):
						if season is None: # Series and Absolute season menus.
							if detailFull: label.append(32003)
							description.append(36756 if metadata.get('sequential') else 36755)
						elif season == 0: # Specials season.
							if detailFull: label.append(33105)
							description.append(36764)
						elif future: # Future/unaired seasons.
							if detailFull: label.append(36601)
							description.append(35117)
						elif Media.isMini(niche): # Miniseries season.
							if detailFull: label.append(35301)
							description.append(36760)
						elif Media.Alternate in type or MetaPack.NumberUnofficial in type: # TVDb/IMDb only seasons. Eg: Money Heist S04-05. Dragon Ball Super S02-05.
							if detailFull: label.append(33504)
							description.append(36823)
						elif season == 1 or Media.Premiere in type: # Premiere season.
							if detailFull: label.append(36000)
							description.append(36762)
						elif Media.Finale in type: # Finale season.
							if detailFull: label.append(36005)
							description.append(36763)
						elif season: # Other seasons.
							if detailFull: label.append(36091)
							description.append(36761)
					elif serie:
						if Media.isMini(niche) and (mixed or not self.menuTypeProgress(menu = menu)): # Do not add the "Mini" label to the show Progress menu, since the episode number should be shown.
							if detailFull or not Media.isMini(nicheMenu): label.append(35301)
							description.append(32007 if Media.isShort(niche) else 36493)
						elif season == 0:
							label.append(33105)
							description.append(35637)
						elif season:
							# Not for the show Progress menu.
							# Not for the Trakt/IMDb favorite lists.
							if mixed or (not self.menuTypeProgress(menu = menu) and not self.menuTypeFavorite(menu = menu)): label.append(Title.title(media = Media.Season, season = season))
							description.append(32007 if Media.isShort(niche) else 36493 if Media.isMini(niche) else 32003)
						else:
							if detailFull: label.append(35498)
							description.append(32007 if Media.isShort(niche) else 36493 if Media.isMini(niche) else 32003)

					if description and not Media.isSeason(media):
						type = None
						genre = None
						genres = metadata.get('genre')

						if Media.isDocu(niche) and (not genres or genres[0] == MetaTools.GenreDocumentary or (genres[0] == MetaTools.GenreMini and genres[1] == MetaTools.GenreDocumentary)): type = 35497 # Some standup comedy specials also have a Documentary genre.
						elif Media.isAnime(niche): genre = MetaTools.GenreAnime # Many have the Anime genre listed later.
						elif Media.isDonghua(niche): genre = MetaTools.GenreDonghua
						elif Media.isAnima(niche): genre = MetaTools.GenreAnimation # Some have the Animation genre listed later.
						elif genres:
							# Do not add the genre if the label already contains it as media type.
							if Media.isShort(niche): genres = [i for i in genres if not i == MetaTools.GenreShort]
							if Media.isMini(niche): genres = [i for i in genres if not i == MetaTools.GenreMini]

							if genres:
								genre = genres[0]

								# Pick genres that are substantially different and might help the user decide if they want to watch the title.
								# Eg: Daredevil: Born Again
								# Do not add GenreReality (eg: American Manhunt: O.J. Simpson).
								for i in ((MetaTools.GenreSuperhero, 3), (MetaTools.GenreSoap, 2)):
									try:
										if genres.index(i[0]) <= i[1]: genre = i[0]
									except: pass

								# Too many series are listed with Drama as first genre.
								# Sometimes this is caused by mergeGenre(), since Drama will occure mostly frequently among the providers.
								# The first Trakt genre could be picked:
								# Eg: Daredevil: Born Again (Trakt's first genre is Superhero)
								# But for many other shows Trakt has also listed Drama as first genre:
								# Eg: Gangs of London
								# Eg: The Cleaning Lady 2022
								# Eg: 1923
								# So pick the next genre, since Drama does not tell the user much.
								# Do this after short/mini, since there can be genres: Drama/Miniseries for which we want to use Drama.
								# Eg: Toxic Town
								if genre == MetaTools.GenreDrama and len(genres) > 1:
									# If there are only 2 genres and Drama is the first one, then the second genre might be less accurate or even almost completely wrong.
									# Only do this for certain genres, since other ones might be accurate (eg: Drama + Crime).
									# Eg: Succession (Drama + Comedy)
									# Eg: Downton Abbey (Drama + Romance)
									# Many (Drama + Family) titles are also more (darker) dramas rather than titles one would watch with the family/kids.
									# Many of these shows also only have the Family genre on TVDb, but not on Trakt/TMDb/IMDb.
									# Eg: tt31656537, tt28803868, tt18753124
									ignore = False
									if len(genres) == 2:
										if any(i == genres[1] for i in (MetaTools.GenreComedy, MetaTools.GenreFamily)): ignore = True

										# Only do this for shows, since for movies the second genre can be more relevant.
										# Eg: Downton Abbey
										if serie and any(i == genres[1] for i in (MetaTools.GenreRomance, )): ignore = True

									if not ignore: genre = genres[1]

						if genre:
							try: type = self.genre(genre = genre)['label']['short']
							except: Logger.error() # Should not happen.
						if type: description.insert(0, type)

					type = None
					if Media.isMovie(media) or Media.isSet(media):
						status = metadata.get('status')
						if status == MetaTools.StatusCanceled: # Eg: Mad Max: The Wasteland (current status as canceled).
							type = 32321
						elif status in MetaTools.StatusesDraft:
							type = 36800
						elif status in MetaTools.StatusesBusy:
							type = 36801
						elif age < -MetaTools.TimeNewMovie:
							# Metadata can be oudated or the metadata is new, but there are no digitial/physical release dates on Trakt yet.
							# But the digitial/physical date might be available from other sources in MetaManager.release().
							# Mark these titles as "New", instead of "Premiered", since there should be 4K sources available.
							custom = self.time(type = MetaTools.TimeCustom, metadata = metadata, estimate = False)
							if custom and custom < self.mTimeCurrent and (self.mTimeCurrent - custom) < new:
								type = 35447 # Newer than 6 or 12 months.
							else:
								premiere = self.time(type = MetaTools.TimeDebut, metadata = metadata, estimate = False)
								if premiere and premiere < self.mTimeCurrent: type = 36765 # Premiered, but no digital/physical release yet.
								else: type = 33001 # Future releases.
						elif age > 0 and age < new: # Newer than 6 or 12 months.
							type = 35447

					elif Media.isShow(media):
						if not season is None and not mixed and not Media.isEpisode(media):
							if not episode and Media.isMini(niche): label.append(35301)
							else: label.append(Title.title(media = Media.Season if episode is None else Media.Episode, season = season, episode = episode))

						if description:
							episoded = Media.isEpisode(metadata.get('media'))

							# Do not use "status", since it is the status of the episode, not that of the show or season.
							try: status = metadata['serie']['show']['status']
							except: status = None
							if Media.isSeason(media):
								try: statused = metadata['serie']['season']['status']
								except: statused = metadata['status']
								if statused: status = statused

							# Show releases.
							# Also do for show objects in the Quick menu.
							# Check the metadata media and not the media variable passed in, since the recommendations/random entries are show objects, while the progres/arrivals entries are episode objects.
							if not status and (season is None or Media.isShow(metadata.get('media')) or (episoded and metadata.get('smart'))): status = metadata.get('status')

							if not episoded and age < -MetaTools.TimeNewShow: type = 33001 # Future releases.
							elif (season == 1 or season is None) and not episoded and age > 0 and age < new: type = 35447 # Newer than 6 or 12 months.
							elif status == MetaTools.StatusEnded: type = 33437
							elif not Media.isMini(niche):
								if status == MetaTools.StatusCanceled: type = 32321
								else: type = 32039

					if type: description.insert(0, type)

			else: # Force certain labels, even if the setting was disabled.
				# Add number labels for seasons/episodes in the Trakt watchlist.
				if Media.isShow(media) and self.menuTypeFavorite(menu = menu):
					if not season is None:
						detailForce = True
						label.append(Title.title(media = Media.Season if episode is None else Media.Episode, season = season, episode = episode))

			result = None
			for i in ((Detail.TypeLabel, label), (Detail.TypeTagline, description), (Detail.TypePlot, description)):
				type = i[0]
				value = i[1]
				if value:
					if not detailForce and detail.get(type) == Detail.ModeDisabled: continue
					format = self.mLabelMediaFormat[type]
					if format:
						if type == Detail.TypeLabel: value = Translation.string(value[0])
						elif Tools.isArray(value): value = ' '.join([Translation.string(j) for j in value])
						result = value # Set before any formatting.
						value = Detail.format(data = value, format = format, color = True)

						attribute = type + ('Before' if format[Detail.Placement] == Detail.PlacementPrepend else 'After')
						valueCurrent = metadata.get(attribute)
						if valueCurrent: valueCurrent.append((value, format))
						else: valueCurrent = [(value, format)]
						metadata[attribute] = valueCurrent
			return result # Used by player.py.
		return None

	def itemDate(self, media, metadata, item):
		if metadata:
			# New Season and New Episodes menus that use the show metadata.
			if Media.isSerie(media):
				custom = self.time(type = MetaTools.TimeCustom, metadata = metadata, estimate = False, fallback = False)
				if not custom: custom = self.time(type = MetaTools.TimeSerie, metadata = metadata, estimate = False, fallback = False) # Deprecated - TimeSerie can be removed after 2025-09.
				if custom: metadata['premiered'] = metadata['aired'] = Time.format(custom, format = Time.FormatDate)

			# For Gaia Eminence.
			# These are needed to use sorting in the menus.
			# date/SORT_METHOD_DATE seems to be broken and does not return the correct order.
			# dateadded/SORT_METHOD_DATEADDED can correctly sort by date.
			if 'premiered' in metadata and metadata['premiered']: date = metadata['premiered']
			elif 'aired' in metadata and metadata['aired']: date = metadata['aired']
			else: date = None

			if date:
				# Needs to be set in a specific format.
				dated = ConverterTime(date, format = '%Y-%m-%d')
				metadata['date'] = dated.string(format = '%d.%m.%Y')
				metadata['dateadded'] = dated.string(format = '%Y-%m-%d %H:%M:%S')

				if media == Media.Season or media == Media.Episode:
					year = Regex.extract(data = date, expression = '(\d{4})', cache = True)
					if year: metadata['year'] = int(year)

	def itemTagline(self, media, metadata, item, extend = True):
		if metadata:
			if extend:
				if metadata.get('taglineBefore'): metadata['tagline'] = Detail.joinBefore(data = metadata.get('tagline'), detail = metadata.get('taglineBefore'))
				if metadata.get('taglineAfter'): metadata['tagline'] = Detail.joinAfter(data = metadata.get('tagline'), detail = metadata.get('taglineAfter'))

	def itemPlot(self, media, metadata, item, extend = True):
		if metadata:
			if media == Media.List:
				from lib.meta.provider import MetaProvider
				provider = None
				for i in [MetaTools.ProviderTrakt, MetaTools.ProviderImdb]:
					if i in metadata or i in (metadata.get('id') or {}):
						provider = i
						break
				if provider:
					description = []
					try: description.append([33406, MetaProvider.name(id = provider)])
					except: pass
					try: description.append([32303, metadata['temp'][provider]['list']['user']])
					except: pass
					try: description.append([33343, metadata['temp'][provider]['list']['type'].capitalize()])
					except: pass
					try: description.append([35841, metadata['temp'][provider]['list']['privacy'].capitalize()])
					except: pass
					try: description.append([32515, metadata['temp'][provider]['count']['item']])
					except: pass
					try: description.append([33444, metadata['temp'][provider]['count']['like']])
					except: pass
					try: description.append([33403, metadata['temp'][provider]['count']['comment']])
					except: pass
					try: description.append([33385, Time.format(metadata['temp'][provider]['time']['added'], format = Time.FormatDate)])
					except: pass
					try: description.append([33386, Time.format(metadata['temp'][provider]['time']['updated'], format = Time.FormatDate)])
					except: pass
					if description:
						description = [Format.fontBold(Translation.string(i[0]) + ': ') + str(i[1]) for i in description]
						description = Format.newline().join(description)
						plot = metadata.get('plot')
						if plot:
							plot = Regex.remove(data = plot, expression = '(?:updated|modified|created|added)\s*(?:at|on)?[\s\:\-]*[\d\-\:\s\/]+', cache = True)
							plot = Regex.remove(data = plot, expression = 'create\s*your\s*own\s*[\:\.\,]?\s*', cache = True)
							plot = Regex.replace(data = plot, expression = '\n+', replacement = '\n', cache = True).strip()
							plot = Regex.replace(data = plot, expression = '\s+', replacement = ' ', cache = True).strip()
							if plot: description = description + (Format.newline() * 2) + plot
						metadata['plot'] = description
			elif media == Media.Person:
				description = []

				try:
					base = metadata['profession']
					if Tools.isDictionary(base[0]): base = [i['department'] for i in base]
					profession = [i for i in base if not ' ' in i] # Filter out "Additional Crew", "Music Department", etc.
					if not profession: profession = base
					profession = [i.title() for i in profession]
					description.append([36697, ' / '.join(profession)])
				except: pass
				try:
					filmography = metadata['filmography'][0]
					year = filmography.get('year')
					filmography = filmography.get('title') + ((' (%d)' % year) if year else '')
					description.append([36696, filmography])
				except: pass
				try: description.append([36837, metadata['origin']])
				except: pass
				try: description.append([36698, metadata['birth']])
				except: pass
				try: description.append([35306, metadata['gender'].title()])
				except: pass

				biography = metadata.get('description')
				if description:
					description = [Format.fontBold(Translation.string(i[0]) + ': ') + str(i[1]) for i in description]
					description = Format.newline().join(description)
					if biography: description += (Format.newline() * 2) + biography
				else:
					description = biography
				metadata['plot'] = description
			elif extend:
				if metadata.get('plotBefore'): metadata['plot'] = Detail.joinBefore(data = metadata.get('plot'), detail = metadata['plotBefore'])
				if metadata.get('plotAfter'): metadata['plot'] = Detail.joinAfter(data = metadata.get('plot'), detail = metadata['plotAfter'])

	def itemId(self, metadata, item, tag = None):
		try:
			if metadata:
				if tag is None: tag = self.itemTag(item = item)
				ids = {}
				imdb = None
				for id in [MetaTools.RatingImdb, MetaTools.RatingTmdb, MetaTools.RatingTvdb, MetaTools.RatingTrakt if tag else None]:
					if id and id in metadata and metadata[id]:
						ids[id] = str(metadata[id])
						if id == MetaTools.RatingImdb: imdb = metadata[id]
				try: tag.setUniqueIDs(ids, 'imdb') # Kodi 20+
				except: item.setUniqueIDs(ids, 'imdb') # Kodi 19
				if imdb: metadata['imdbnumber'] = imdb
		except: Logger.error()

	def itemInfo(self, metadata, item, tag = None, type = None):
		if tag is None: tag = self.itemTag(item = item)
		if tag and metadata: # Kodi 20+
			for key, value in metadata.items():
				try:
					if not value is None:
						function = self.mMetaFunctions[key]
						if function: Tools.executeFunction(tag, function, value)
				except: Logger.error(key)
		else: # Kodi 19
			item.setInfo(type = type if type else 'video', infoLabels = metadata)

	def itemFuture(self, metadata, media = None):
		result = {'future' : None, 'known' : None, 'unknown' : None, 'time' : None, 'age' : None}
		try:
			if metadata:
				if media is None: media = metadata.get('media')
				if Media.isBonus(media): return result
				serie = Media.isSerie(media)

				status = metadata.get('status')
				finished = False
				if serie:
					try: finished = metadata['serie']['season']['status'] in MetaTools.StatusesPast
					except: pass

				age = None
				time = self.time(type = MetaTools.TimePremiere, metadata = metadata, estimate = False, fallback = False if serie else MetaTools.TimeDebut)
				if not time:
					date = metadata.get('aired') or metadata.get('premiered')
					if date: time = Time.timestamp(fixedTime = date + ' ' + self._clock(), format = Time.FormatDateTime, utc = True)

				if time:
					age = time - self.mTimeCurrent
				else:
					# Trakt sometimes returns new/unaired seasons that or not yet on TVDb, and also sometimes vice versa.
					# These seasons seem to not have a premiered/aired date, year, or even the number of episodes aired.
					# Make them italic to inidcate that they are unaired.
					# Update: Sometimes the year and airs attributes are available.
					if media == Media.Season:
						if not 'year' in metadata:
							try: episodes = metadata['count']['episode']['released']
							except: episodes = None
							if not episodes: age = MetaTools.TimeFuture
						if age is None and 'pack' in metadata:
							# Slow Horses has a year for S03, although not aired yet.
							season = metadata.get('season')
							if not season is None:
								found = MetaPack.instance(pack = metadata.get('pack')).season(season = season)
								if not found: age = MetaTools.TimeFuture
					if age is None and (media == Media.Season or media == Media.Episode):
						if metadata and (not 'rating' in metadata or not metadata['rating']) and (not 'votes' in metadata or not metadata['votes']):
							# If no rating, votes or images.
							images = False
							if MetaImage.Attribute in metadata and metadata[MetaImage.Attribute]:
								for k, v in metadata[MetaImage.Attribute].items():
									if not Tools.isDictionary(v) and v:
										images = True
										break
							if not images: age = MetaTools.TimeFuture

				known = time and time > self.mTimeCurrent
				unknown = not time and (status in MetaTools.StatusesFuture or (serie and not status and not finished))
				result['future'] = known or unknown
				result['known'] = known
				result['unknown'] = unknown
				result['time'] = time
				result['age'] = age
		except: Logger.error()
		return result

	def itemVoting(self, metadata, item, tag = None):
		try:
			if metadata and 'voting' in metadata:
				if tag is None: tag = self.itemTag(item = item)
				for i in [MetaTools.RatingImdb, MetaTools.RatingTmdb, MetaTools.RatingTvdb, MetaTools.RatingTrakt if tag else None]:
					if i:
						voting = metadata['voting']
						if i in voting.get('rating', {}):
							rating = metadata['voting']['rating'][i]
							if not rating is None and i in metadata['voting']['votes']:
								votes = metadata['voting']['votes'][i]
								if votes is None: votes = 0
								try: tag.setRating(rating, votes, i, False) # Kodi 20+
								except: item.setRating(i, rating, votes, False) # Kodi 19
						if i in voting.get('user', {}):
							rating = metadata['voting']['user'][i]
							if not rating is None:
								try: tag.setUserRating(rating) # Kodi 20+
								except: pass
		except: Logger.error()

	def itemImage(self, media, metadata, item, images = True, video = None, menu = None, submenu = None, player = None):
		if media == Media.List or media == Media.Person:
			if media == Media.List:
				if metadata.get('trakt'): image = 'liststrakt'
				elif metadata.get('imdb'): image = 'listsimdb'
				else: image = 'lists'
				icon, thumb, poster, banner = Icon.pathAll(icon = image, default = self.mThemeThumb)
			elif media == Media.Person:
				image = metadata.get('image')
				if Tools.isDictionary(image): # Trakt.
					try: image = image[MetaImage.TypePhoto][0]['link']
					except: image = None
				if image: icon = thumb = poster = banner = image
				else: icon, thumb, poster, banner = Icon.pathAll(icon = 'people', default = self.mThemeThumb)
			Directory.decorate(item = item, icon = image) # For Gaia Eminence.
			images = {
				MetaImage.TypePoster : poster,
				MetaImage.TypeThumb : thumb,
				MetaImage.TypeFanart : self.mThemeFanart,
				MetaImage.TypeLandscape : self.mThemeFanart,
				MetaImage.TypeBanner : banner,
				MetaImage.TypeClearlogo : icon,
				MetaImage.TypeClearart : icon,
				MetaImage.TypeDiscart : poster,
				MetaImage.TypeIcon : icon,
			}
			MetaImage.set(item = item, images = images)
		elif Tools.isDictionary(images):
			return MetaImage.set(item = item, images = images)
		elif images:
			# For Quick and Progress show menus.
			# The media is set to Show in MetaMenu.buildMedia(), since the layout/view looks better for shows than for episodes.
			if media == Media.Show and not metadata.get('season') is None: media = Media.Episode

			# Use the secondary images for the Absolute season menu, so that there is some variance from the Series menu.
			# Only do for some image types, since we want to keep a static background for all seasons.
			choice = None
			if media == Media.Season and metadata.get('sequential'): choice = {i : MetaImage.ChoiceSecondary for i in [MetaImage.TypePoster, MetaImage.TypeThumb, MetaImage.TypeKeyart]}

			if media == Media.Season and metadata and not 'season' in metadata: media = Media.Show # Series menu.

			if video is None:
				custom = None
				if player: custom = MetaImage.CustomPlayer
				elif self.menuTypeSmart(menu = menu) or self.menuTypeFavorite(menu = menu): custom = MetaImage.CustomSmart
				return MetaImage.setMedia(media = media, data = metadata, item = item, custom = custom, choice = choice)
			elif video == Recap.Id: return MetaImage.setRecap(data = metadata, item = item)
			else: return MetaImage.setExtra(data = metadata, item = item)
		return None

	def itemCast(self, metadata, item, tag = None):
		# There is a bug in Kodi when setting a ListItem in the Player.
		# When setting the cast, the name/role/order is added correctly, but for some unknown reason the thumbnail is removed.
		# This only happens in Kodi's player. The cast thumbnails are correct when creating a directory or showing the movie/show info dialog.
		# To replicate the problem, add this to player.py:
		#	self.item.setCast([{'name' : 'vvv', 'role' : 'uuu', 'thumbnail' : 'https://image.tmdb.org/t/p/w185/gwQ5MfY68BvvyIbef3kr2XPilTx.jpg'}])
		#	self.updateInfoTag(self.item)
		#	tools.Time.sleep(1)
		#	tools.System.executeJson(method = 'Player.GetItem', parameters = {'playerid' : interface.Player().id(), 'properties':['cast']})
		# The RPC returns:
		#	{"id":1,"jsonrpc":"2.0","result":{"item":{"cast":[{"name":"vvv","order":-1,"role":"uuu"}],"label":"The Shawshank Redemption","type":"movie"}}}
		# The name/role/order is returned, but the thumbnail is missing.
		# This is most likley also the reason why the cast thumbnails do not show up in Kodi Kore or Yatse, since both probably use the RPC.
		# Various attempts were made to solve the problem, but without any success:
		#	1. Removing the cast/castandrole attributes before setting item.setInfo() and only use item.setCast().
		#	2. Setting the thumbnail as a HTTP URL, local file path, special:// path, URL-encoded image:// path, or <thumb>https://...</thumb>.
		#	3. Inserting the actor and thumbnail into Kodi's local DB (MyVideosXXX.db), in case the RPC retrieves the thumbnail from there.
		#	4. Using differnt attributes (thumbnail/thumb/photo/image) in the dictionaries set with item.setCast().
		# Maybe this will be fixed in Kodi 20 with the new functions/classes:
		#	self.item.setCast([xbmc.Actor('vvv', 'role', order=1, thumbnail='https://image.tmdb.org/t/p/w185/gwQ5MfY68BvvyIbef3kr2XPilTx.jpg')])

		if metadata and 'cast' in metadata:
			cast = metadata['cast']
			if cast:
				if Tools.isDictionary(cast[0]):
					attributes = {'name' : True, 'role' : True, 'order' : True, 'thumbnail' : True}
					castDetail = [{k : v for k, v in i.items() if k in attributes} for i in cast]
				else:
					try: multi = Tools.isArray(cast[0]) and len(cast[0]) > 1
					except: multi = False
					if multi: castDetail = [{'name' : i[0], 'role' : i[1]} for i in cast]
					else: castDetail = [{'name' : i} for i in cast]

				# Sometimes there are still large integers in the "order" attribute, causing the following error:
				#	tag.setCast(): OverflowError: signed integer is greater than maximum
				# More info under mergeCast().
				# This should not happen anymore, since we copy the dicts.
				# But sometimes this still sporadically happens for shows (not even season/episodes where we do the copying).
				# Manually adjust them here.
				# This should NOT happen. The problem lies somewhere else that causes the large integers to remain (which they shouldn't from mergeCast()), and this has to be fixed at the root of the problem.
				# It probably is caused by some nested cast dict being used in multiple places without deep-copying it.
				maximum = 2000000000 # 2147483647
				for i in castDetail:
					if i['order'] > maximum:
						i['order'] -= maximum

				# There is a bug in Kodi that the thumbnails are not shown, even if they were set.
				if tag is None: tag = self.itemTag(item = item)
				try: tag.setCast([Actor(**i) for i in castDetail]) # Kodi 20+
				except: item.setCast(castDetail) # Kodi 19

	def itemStream(self, stream, item, tag = None, metadata = None):
		audio = False

		if stream:
			if tag is None: tag = self.itemTag(item = item)
			if tag: # Kodi 20+
				for type, datas in stream.items():
					if type == MetaTools.StreamVideo:
						for data in datas: tag.addVideoStream(data)
					elif type == MetaTools.StreamAudio:
						audio = bool(datas)
						for data in datas: tag.addAudioStream(data)
					elif type == MetaTools.StreamSubtitle:
						for data in datas: tag.addSubtitleStream(data)
			else: # Kodi 19
				for type, datas in stream.items():
					if type == MetaTools.StreamAudio: audio = bool(datas)
					for data in datas: item.addStreamInfo(type, data)

		if metadata and not audio:
			languages = metadata.get('language')
			if languages:
				audio = []
				for language in languages:
					if language:
						data = {MetaTools.StreamLanguage : Language.code(language, code = Language.CodeSecondary)}
						if self.mKodiNew: data = AudioStreamDetail(**data) # Kodi 20+
						audio.append(data)
				self.itemStream(stream = {MetaTools.StreamAudio : audio}, item = item, tag = tag, metadata = None)

	def itemProperty(self, properties, item, playable = None):
		if not properties: properties = {}
		if not 'IsPlayable' in properties:
			if playable is None: playable = self.mPlayable
			properties['IsPlayable'] = 'true' if playable else 'false'
		item.setProperties(properties)

	def itemPlayback(self, media, metadata, item, tag = None, mixed = False, progress = False, menu = None):
		# Do not do for sets, since it will try to retrieve the playback history/progress/rating for sets which does not exist.
		# Do not do for lists. Eg: Movies -> Favorites -> Trakt -> Lists -> Liked Lists.
		if metadata and not media == Media.Set and not media == Media.Person and not media == Media.List:
			if Media.isRecap(media):
				# Can be set from itemRecap().
				# Use the current, instead of the previous, season metadata for Playback.
				try: metadata = metadata['seasons']['recap']
				except: pass

			if tag is None: tag = self.itemTag(item = item)

			# Reuse the variable name for "progress" below.
			progression = None
			progressed = progress
			if Tools.isArray(progress):
				progression = progress
				progressed = True

			try: imdb = metadata['imdb']
			except: imdb = None
			try: tmdb = metadata['tmdb']
			except: tmdb = None
			try: tvdb = metadata['tvdb']
			except: tvdb = None
			try: trakt = metadata['trakt']
			except: trakt = None
			try: season = metadata['extra']['season']
			except:
				try: season = metadata['season']
				except: season = None
			try: episode = metadata['extra']['episode']
			except:
				try: episode = metadata['episode']
				except: episode = None
			if Media.isRecap(media) and episode is None: episode = 1

			# Series menu.
			if media == Media.Season and not 'season' in metadata: media = Media.Show
			special = media == Media.Show and not episode is None # Progress/Arrivals menu where episodes are listed as shows.

			busy = True
			count = None
			time = None
			progress = None
			rating = None
			playback = None
			playback2 = None
			playback3 = None
			playbacker = None

			# NB: Also do this for Recap/Extra, since they use the first/last episode for the playback indicators.
			#if not(media == Media.Recap or media == Media.Extra):
			if True:
				playbacker = self._playback()
				if not 'time' in metadata: metadata['time'] = {}

				adjust = playbacker.AdjustSettings
				if progression and progression[1] is True: adjust = True
				elif progressed or progressed is None: adjust = False
				elif media == Media.Episode: adjust = True

				# NB: Use "quick=True" to avoid pack retrieval for show menus, which can take very long, and is not needed here.
				# The pack data is used to convert/lookup standard numbers to Trakt numbers and vice versa.
				# For seasons and episodes, the pack data should already have been aggregated into each metadata object, and the Trakt number conversion should still fine, even with "quick=True".
				playback = playbacker.retrieve(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, metadata = metadata, adjust = adjust, quick = True)

				count = playback['history']['count']['total']

				time = playback['history']['time']['last']
				if time: metadata['time'][MetaTools.TimeWatched] = time

				progress = playback.get('progress')
				if progress:
					progressed = progress.get('time')
					if progressed: metadata['time'][MetaTools.TimePaused] = progressed
					progress = progress.get('value')

					# Do not add a progress icon for finished/watched movies in the main Progress menu if they have a progress of eg 99%.
					if not adjust and progression:
						if progress < progression[0] or progress > progression[1]: progress = None

				rating = playback.get('rating')
				if rating:
					rated = rating.get('time')
					if rated: metadata['time'][MetaTools.TimeRated] = rated
					rating = rating.get('value')

			# If the 1st episode is in-progress, already mark the recap as watched, and not also as in-progress.
			if progress:
				if media == Media.Recap:
					progress = None
					if not count: count = 1
				elif media == Media.Extra:
					progress = None

			# Do not use overlay/watched attribute, since Kodi (or maybe the Kodi skin) resets the playcount to 1, even if playcount is higher than 1.
			# https://github.com/xbmc/xbmc/blob/master/xbmc/guilib/GUIListItem.h
			#metadata['overlay'] = 5 if count else 4
			metadata['playcount'] = count

			if time: metadata['lastplayed'] = Time.format(time, format = Time.FormatDateTime)

			# Some shows have very long credits that already start at 92%-94%.
			# If an episodes was marked as watched, but playback was stopped (or binge continued) at eg 93%, the menu will show a progress icon, instead of a watched checkmark.
			# This can be confusing, as it looks like the episode was not finished yet.
			# Playback.ProgressEndShow was already reduced from 96% to 95%, which is still not enough for these special cases.
			# We could reduce Playback.ProgressEndShow, but this would then cause false-positives for episodes that were paused/stopped at these percentages, although playback was not finished.
			# Instead, do not add the progress icon, if the progress timestamp is AFTER (or close to) the watched timestamp.
			# Eg: If an episode progress is at 93%, but it was marked as watched 10 minutes before, assumed it was fully watched and do not add the progress.
			if media == Media.Movie or media == Media.Episode:
				if count and progress and progress > 0.85 and time and progressed and Tools.isInteger(progressed):
					if time > progressed or abs(time - progressed) < (3600 if media == Media.Movie else 1800): # 1 hour or 30 mins.
						busy = False
						metadata['busy'] = False # Used by itemDetail() ot also remove the progress from the label.

			# Resume/Progress
			# Do not set TotalTime, otherwise Kodi shows a resume popup dialog when clicking on the item, instead of going directly to scraping.
			# item.setProperty('TotalTime', str(metadata['duration']))
			# For some skins (eg: skin.eminence.2) the TotalTime has to be set for a different progress icon to show (25%, 50%, 75%).
			# Without TotalTime, the skins justs shows the default 25% icon.
			if progress:
				# Not listed under the Python docs, but listed under the infolabels docs.
				# Do not add, since Kodi throws a warning in the log: Unknown Video Info Key "percentplayed"
				#metadata['percentplayed'] = progress * 100

				if busy and self.mIconProgress and (special or (not media == Media.Show and not media == Media.Season)):
					duration = metadata.get('duration')
					if not duration: duration = 3600 if Media.isSerie(media) else 7200
					resume = progress * duration
					try:
						# Kodi 20+ now requires the total time, otherwise the progress icon is not shown in the menus.
						# However, when specifying the total time, Kodi adds a "resume" entry to the context menu.
						# When using a very small time (eg: 0.1), it seems Kodi adds the progress icon without adding an entry to the context menu.
						#tag.setResumePoint(int(resume))
						#tag.setResumePoint(int(resume), int(duration))
						tag.setResumePoint(0.1, 1)
					except: item.setProperty('ResumeTime', str(int(resume)))
					item.setProperty(MetaTools.PropertyProgress, str(progress)) # Used by select().

				# Used by the context menu to add a "Clear Progress" option.
				if special or (not media == Media.Show and not media == Media.Season): metadata['progress'] = progress
			else:
				# If the progress was adjusted (eg: ignore if above 95%), reset the value, otherwise the progress is still added to the label.
				metadata['progress'] = None

			if rating:
				try: tag.setUserRating(rating) # Kodi 20+
				except: pass
				metadata['userrating'] = rating

			if Media.isSerie(media):
				currentTotal = None
				currentWatched = 0
				currentUnwatched = 0
				currentRewatched = 0
				currentReunwatched = 0
				currentRewatching = 0

				seasonsTotal = None
				seasonsWatched = 0
				seasonsUnwatched = 0
				seasonsRewatched = 0
				seasonsReunwatched = 0
				seasonsRewatching = 0

				episodesTotal = None
				episodesWatched = None
				episodesUnwatched = None
				episodesRewatched = None
				episodesReunwatched = None
				episodesRewatching = None

				pack = metadata.get('pack')
				if pack: pack = MetaPack.instance(pack = pack)

				# Progress menu where episodes are listed as shows.
				# These do not load full pack data and also do not have the necessary values in the summarized "packed".
				if special:
					if pack: # This will probably never happen, since the full pack is never set.
						seasonsTotal = pack.countSeasonOfficial()
						episodesTotal = pack.countEpisodeOfficial()
						if self.mShowCountSpecial:
							seasonsTotal += pack.countSeasonSpecial()
							episodesTotal += pack.countEpisodeOfficial()
					else:
						smart = Tools.get(metadata, 'smart', 'pack', MetaPack.ValueCount)
						if smart:
							# Retrieve the show's playback to get episode watched/unwatched counts.
							playback2 = playbacker.retrieve(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, metadata = metadata, adjust = adjust, quick = True)

							total = smart.get(MetaPack.ValueTotal) or {}
							official = smart.get(MetaPack.NumberOfficial) or {}
							if self.mShowCountSpecial:
								seasonsTotal = total.get(MetaPack.ValueSeason) or 1
								episodesTotal = (official.get(MetaPack.ValueEpisode) or 1) + (official.get(MetaPack.ValueSpecial) or 0)
							else:
								seasonsTotal = official.get(MetaPack.ValueSeason) or 1
								episodesTotal = official.get(MetaPack.ValueEpisode) or 1
						else:
							seasonsTotal = 1
							episodesTotal = 1

				if seasonsTotal is None or episodesTotal is None:
					if not pack:
						pack = metadata.get('packed') # Either full pack, or reduced pack.
						if pack: pack = MetaPack.instance(pack = pack)

					if pack:
						if media == Media.Show or (season is None and episode is None): # Arrivals menu has items with season numbers, but they are shows.
							seasonsTotal = pack.countSeasonOfficial()
							episodesTotal = pack.countEpisodeOfficial()
							if self.mShowCountSpecial:
								seasonsTotal += pack.countSeasonSpecial()
								episodesTotal += pack.countEpisodeOfficial()
						elif episode is None:
							seasonsTotal = 1
							if season == 1 and pack.typeUnofficial(season = season + 1): episodesTotal = pack.countEpisodeOfficial(season = season) # If Trakt has a single absolute season, while TVDB has additional seasons (eg: Dragon Ball Super S02+).
							else: episodesTotal = pack.countEpisodeOfficial(season = season) or pack.countEpisodeUnofficial(season = season) # Use unoffical count for seasons not on Trakt (eg: Dragon Ball Super S02+).
						else:
							seasonsTotal = 1
							episodesTotal = 1

				playback3 = playback2 or playback

				# The current counts are used to hide fully watched seasons from the Arrivals menu.
				try:
					if pack and (media == Media.Show or media == Media.Season):
						currentTotal = 0
						if media == Media.Season: lookup = [Tools.update({'season' : season}, playback3['history'])]
						else: lookup = playback3['history'].get('seasons')
						if lookup:
							for i in lookup:
								try:
									subEpisodesTotal = pack.countEpisodeOfficial(season = i['season']) or pack.countEpisodeUnofficial(season = i['season'])
									if subEpisodesTotal:
										if i['count']['unique'] == subEpisodesTotal: seasonsWatched += 1
										if (i['count']['total'] or 0) > subEpisodesTotal:
											if subEpisodesTotal and (i['count']['total'] % subEpisodesTotal) == 0: seasonsRewatched += 1
											else: seasonsRewatching += 1

										if i['season'] == season and episode is None:
											currentTotal = 1
											if i['count']['unique'] == subEpisodesTotal: currentWatched = 1
											if (i['count']['total'] or 0) > subEpisodesTotal:
												if subEpisodesTotal and (i['count']['total'] % subEpisodesTotal) == 0: currentRewatched = int(i['count']['total'] / subEpisodesTotal)
												else: currentRewatching = 1
											currentUnwatched = 0 if currentWatched else 1
											currentReunwatched = 0 if currentRewatched else 1
								except: Logger.error()
							seasonsUnwatched = max(0, seasonsTotal - seasonsWatched)
							seasonsReunwatched = seasonsTotal - seasonsRewatched
				except: Logger.error()

				if 'main' in playback3['history']['count'] and not self.mShowCountSpecial:
					episodesWatched = playback3['history']['count']['main']['unique']
					episodesRewatched = playback3['history']['count']['main']['total']
				else:
					episodesWatched = playback3['history']['count']['unique']
					episodesRewatched = playback3['history']['count']['total']

				if not episodesWatched: episodesWatched = 0
				if not episodesUnwatched: episodesUnwatched = 0
				if not episodesRewatched: episodesRewatched = 0
				if not episodesReunwatched: episodesReunwatched = 0
				if episodesTotal:
					episodesUnwatched = max(0, episodesTotal - episodesWatched) # Can be negative. Eg: Dragon Ball Super S02+.

					# This does not work correctly if not all episodes were watched/rewatched the same number of times.
					# Eg: Severance: watch all episodes of S01 twice. Watch the first half of episodes of S02 (last season). The progress should be around 70%.
					# Add a new "rewatching" attribute which determines if the user is currently rewatching the show.
					# A show can be watched in the following ways:
					#	1. Watch all episodes once from start to finish.
					#	2. After having watched all episodes at least once, rewatch all episodes again from start to finish.
					#	3. The first N seasons where watched at least once. A new season comes out and the user decides to rewatch all previous seasons before watching the new season for the first time.
					# Determine if the last watched episods is a first watch or a rewatch, which is then used to determine the overall progress.

					#if episodesRewatched > episodesTotal:
					#	episodesRewatched = episodesRewatched % episodesTotal
					#	episodesReunwatched = episodesTotal - episodesRewatched
					#else:
					#	episodesRewatched = 0
					#	episodesReunwatched = 0

					try: episodeLast = playback3['history']['time']['last']
					except: episodeLast = None

					episodesRewatched = 0
					for i in (playback3['history'].get('seasons') or []):
						for j in (i.get('episodes') or []):
							watched = (j.get('count') or {}).get('total')
							if watched:
								if watched > 1: episodesRewatched += 1
								if episodeLast and episodeLast == (j.get('time') or {}).get('last'): episodesRewatching = watched > 1
					episodesReunwatched = episodesTotal - episodesRewatched

				# Set this to allow the context menu to add "Mark As Unwatched" for partially watched shows/seasons.
				if not 'count' in metadata: metadata['count'] = {}
				metadata['count'] = Tools.update(metadata['count'], {
					'season' : {'total' : seasonsTotal, 'watched' : seasonsWatched, 'unwatched' : seasonsUnwatched, 'rewatched' : seasonsRewatched, 'reunwatched' : seasonsReunwatched, 'rewatching' : seasonsRewatching},
					'episode' : {'total' : episodesTotal, 'watched' : episodesWatched, 'unwatched' : episodesUnwatched, 'rewatched' : episodesRewatched, 'reunwatched' : episodesReunwatched, 'rewatching' : episodesRewatching},
				})
				# Current season counts for hiding watched seasons from the Arrivals menu.
				if media == Media.Show and not currentTotal is None: metadata['count']['current'] = {'total' : currentTotal, 'watched' : currentWatched, 'unwatched' : currentUnwatched, 'rewatched' : currentRewatched, 'reunwatched' : currentReunwatched, 'rewatching' : currentRewatching}

				if self.mShowCountEnabled and self.mIconCount:
					if not seasonsTotal is None: item.setProperty('TotalSeasons', str(seasonsTotal))
					if not episodesTotal is None: item.setProperty('TotalEpisodes', str(episodesTotal))
					if not episodesWatched is None: item.setProperty('WatchedEpisodes', str(episodesWatched))
					if not episodesUnwatched is None and self.mShowCountUnwatched:
						if self.mShowCountLimit: episodesUnwatched = min(99, episodesUnwatched)
						item.setProperty('UnWatchedEpisodes', str(episodesUnwatched))

				# For shows and seasons, only mark as watched if all episodes were watched.
				# If some episodes are watched and some are unwatched, add a resume time to indicate there are still some unwatched episodes.
				# Do not do this for Progress menus that are episodes, but are listed as shows.
				# Update (2025-01): Now also do this for the Progress menus.
				#if (media == Media.Show or media == Media.Season) and not(media == Media.Show and not episode is None and progressed):
				if media == Media.Show or media == Media.Season:
					if episodesUnwatched and episodesUnwatched > 0:
						metadata['playcount'] = None
					else:
						# NB: Use "quick=True" to avoid pack retrieval for show menus, which can take very long, and is not needed here.
						count, remaining = playbacker.count(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, specials = True if season == 0 else self.mShowCountSpecial, metadata = metadata, history = playback3['history'], quick = True)
						metadata['playcount'] = count

					# Icons should be displayed as follows:
					#	1. Checkmark icon: if a show was fully watched, show the checkmark icon.
					#	   The show will still be listed in the Progress menu for a few days after being fully watched (to allow rewatching the last episode), until it will be moved down the list.
					#	   The checmark indicates to the user that the show was finished/watched.
					#	2. Progress icon: If at least one episode of the current season was watched, or one episode has progress without being finished, show a progress icon.
					#	   The icon indicates to the user that he is still busy watching the show, or rather the current season.
					#	3. Progress icon: If a show was fully watched, and at least one episode was rewatched, show a progress icon.
					#	   The icon indicates to the user that he is busy with a rewatch.
					#	   The icon indicates to the user that he is still busy watching the show, or rather the current season.
					#	4. No icon: If the show has no watched orbusy/progress episodes, do not show any icon.
					#	   Also do not show an icon if the user fully watched the previous season, but has not started to watch the next season. Eg: a new season is released.
					#	5. Progress icon: For all non-Progress menus, including Arrivals, always show a progress icon if at least one episode was started.
					if self.mIconProgress:
						allow = False
						if progress: allow = True # The current episode is still busy with playback progress.
						elif episodesWatched and episodesUnwatched: allow = True # The show is watched for the first time with some episodes watched and others unwatched.
						else:
							# The show is was fully watched and is now being rewatched.
							# Mod instead of just checking if total > unique, in case the show was fully watched twice.
							try: allow = playback3['history']['count']['main']['total'] % playback3['history']['count']['main']['unique'] > 0
							except:
								try: allow = playback3['history']['count']['total'] % playback3['history']['count']['unique'] > 0 # Season menus.
								except: pass

							# If a single episode of the show (eg S01E01) was watched twice, and later all the other episodes were watched.
							# A checkmark icon and not a progress icon should show, since the show was fully watched.
							# The one episode that was watched twice is just a discrepancy and should not be seen as a rewatch.
							# Only if the last watched episode was actually a rewatched, show the progress icon.
							if allow and episodesRewatched and not episodesRewatching: allow = False

						if allow:
							started = True

							# For the Arrivals and other menus besides Progress, always show the progress icon if at least one episode was started.
							# So that the user can quickly see in the Arrivals menu which shows he is watching, even if it is a newly released season that would not be marked with progress in the Progress menu.
							unspecial = not progressed and (episodesWatched or progress)

							# At least one episode in the current season was watched.
							# Do not check if there is playback progress for the current episode.
							if (media == Media.Show and not season is None) and not progress and not unspecial:
								started = False
								try:
									for i in playback3['history']['seasons']:
										if i['season'] == season:
											started = True
											break
								except: pass # "seasons" might not be available.

							if started:
								try:
									# Kodi 20+ now requires the total time, otherwise the progress icon is not shown in the menus.
									# However, when specifying the total time, Kodi adds a "resume" entry to the context menu.
									# When using a very small time (eg: 0.1), it seems Kodi adds the progress icon without adding an entry to the context menu.
									#tag.setResumePoint(1)
									#tag.setResumePoint(1, 100)
									tag.setResumePoint(0.1, 1)
								except: item.setProperty('ResumeTime', str(1))

	def itemContext(self,
		item,

		add = None,
		context = None,
		mode = None,

		media = None,
		niche = None,
		video = None,

		command = None,
		provider = None,
		library = None,
		playlist = None,

		source = None,
		metadata = None,
		orion = None,
		shortcut = None,
		mixed = None,
	):
		# NB: Do not pass the cleaned metadata, since we need to extract the raw YouTube trailer URL, not the already created Gaia plugin command.
		menu = self.context(context = context, mode = mode, media = media, niche = niche, video = video, command = command, provider = provider, library = library, playlist = playlist, source = source, metadata = metadata, orion = orion, shortcut = shortcut, mixed = mixed)
		if menu and (add or add is None): item.addContextMenuItems(menu.menu(full = True))
		return menu

	def itemMore(self, metadata = None, media = None, niche = None, multiple = False, submenu = None, link = None, parameters = None, data = None, item = None):
		try:
			if data:
				if Tools.isString(data): link = data
				elif Tools.isDictionary(data): parameters = data

				if not Tools.isArray(metadata): metadata = [metadata]

			if link or parameters:
				if not item: item = self.itemCreate()
				tag = self.itemTag(item = item)
				if not media: media = self.media(metadata = metadata[0])

				title = Format.fontItalic(33432)
				item.setLabel(title)

				self.itemInfo(item = item, tag = tag, metadata = {'title' : title, 'tagline' : Translation.string(35317), 'plot' : Translation.string(35318)})

				icon = Icon.pathIcon(icon = 'next.png', default = 'DefaultFolder.png')
				image = self.mThemeMoreThumb if media == Media.Episode and not multiple else self.mThemeMorePoster
				images = {
					MetaImage.TypePoster : image,
					MetaImage.TypeThumb : icon,
					MetaImage.TypeFanart : self.mThemeFanart,
					MetaImage.TypeLandscape : self.mThemeFanart,
					MetaImage.TypeBanner : self.mThemeMoreBanner,
					MetaImage.TypeClearlogo : icon,
					MetaImage.TypeClearart : icon,
					MetaImage.TypeDiscart : image,
					MetaImage.TypeIcon : icon,
				}
				MetaImage.set(item = item, images = images)

				if link and Tools.isString(link) and link.startswith(System.plugin()):
					command = link # Flattened show menus.
				else:
					if not parameters: parameters = {'link' : link}
					if not 'media' in parameters: parameters['media'] = media
					if not 'niche' in parameters and niche: parameters['niche'] = niche
					if 'niche' in parameters:
						niche = parameters['niche']
						if niche: parameters['niche'] = Media.stringTo(niche)
						else: del parameters['niche']

					submenu = submenu
					if submenu is True and parameters.get('submenu'): submenu = parameters.get('submenu')
					if submenu and not submenu is True: # Do not do this if "submenu=True", for the top-level More item of the show Progress menu.
						parameters[MetaTools.SubmenuParameter] = submenu
						self.submenuNumber(media = media, submenu = submenu, multiple = multiple, metadata = metadata, parameters = parameters)

					from lib.meta.menu import MetaMenu
					parameters = MetaMenu.commandCreateMore(media = media, parameters = parameters)

					# Do not optimize/encode the command parameters.
					# This makes it easier to read, so that users can add skin shortcuts and easily manipulate the URL.
					command = System.command(parameters = parameters, optimize = False)

				# gaiasubmenu - Check MetaTools.submenuSpecial() for more info.
				folder = not self.submenuSpecial(media = media, submenu = submenu, multiple = multiple, metadata = metadata)

				return [command, item, folder]
		except: Logger.error()
		return None

	def itemRecap(self, metadata, media = None, multiple = None, submenu = None):
		try:
			if media is None: media = self.media(metadata = metadata)
			if multiple is None: multiple = self.multiple(metadata = metadata) if (media == Media.Season or media == Media.Episode) else False

			if media == Media.Episode and not multiple:
				if self.mShowBonusRecap and Recap.enabled():
					if Tools.isArray(metadata): metadata = metadata[0]
					season = metadata['season'] - 1
					episode = metadata['episode'] - 1
					if season > 0 and episode == 0:
						# Ensures that the Recaps are automatically marked as watched if the first episode in the season was watched.
						metadataReuse = {i : metadata[i] for i in ['playcount', 'watched', 'overlay', 'lastplayed', 'date', 'dateadded'] if i in metadata}
						metadataReuse['extra'] = {'season' : metadata['season'], 'episode' : metadata['episode']}

						# Rather prefer the episode premiere date from the pack, instead of the current season's premiere (extracted from metadata2 below).
						# Sometimes there can be discrepancies between the premiere date of a season and the actual SxxE01 episode premier date, especially for future seasons.
						# This could be because there is some timezone discrepancy, causing the date to be off by a day, or simply that the metadata on a provider is outdated.
						# Eg: Foundation S03:
						#	Trakt:
						#		S03 premiere: None (not yet added)
						#		S03E01 premier: July 10, 2025 1:00 PM
						#	TVDb:
						#		S03 premiere: July 11, 2025
						#		S03E01 premier: July 11, 2025
						# This now causes the Season Recap to use 2025-07-11, while S03E01 uses 2025-07-10.
						# Hence, use the episode date from the pack (if available), to ensure the Season Recap and SxxE01 have the same date.
						premieredFirst = None
						pack = metadata.get('pack')
						if pack:
							try:
								premieredFirst = MetaPack.instance(pack = pack).time(season = metadata['season'], episode = 1)
								if premieredFirst: premieredFirst = Time.format(premieredFirst, format = Time.FormatDate)
							except: Logger.error()

						pack = metadata.get('pack')
						metadata = metadata.get('seasons')
						metadata2 = None
						if metadata:
							metadataPrevious = metadata.get('previous')
							metadataCurrent = metadata.get('current')
							metadataNext = metadata.get('next')
							metadata = self.copy(metadataPrevious or metadataCurrent or metadataNext)
							if metadataCurrent: metadata2 = self.copy(metadataCurrent or metadataPrevious or metadataNext)
							if not premieredFirst: premieredFirst = metadata2.get('premiered') or metadata2.get('aired')
						if not metadata: return None

						# Copy images, otherwise if there is an Extras from the previous season and a Recap from the next seasons (eg: Trakt progress submenu), the image dictionary is changed, causing exceptions.
						if metadataCurrent and MetaImage.Attribute in metadataCurrent:
							MetaImage.update(media = MetaImage.MediaSeason, images = metadataCurrent[MetaImage.Attribute], data = metadata, copy = True)
							MetaImage.update(media = MetaImage.MediaSeason, images = metadataCurrent[MetaImage.Attribute], data = metadata, category = MetaImage.MediaSeason, copy = True)

							# This is the thumb of the current season and not the previous season. Force remove to pick a fallback in MetaImage.
							# Eg: True Detective S03 (recap for S02)
							try: metadata[MetaImage.Attribute][MetaImage.TypeThumb] = []
							except: pass
						if metadataCurrent and MetaImage.Attribute in metadataCurrent and MetaImage.MediaShow in metadataCurrent[MetaImage.Attribute]: MetaImage.update(media = MetaImage.MediaSeason, images = metadataCurrent[MetaImage.Attribute][MetaImage.MediaShow], data = metadata, category = MetaImage.MediaShow, copy = True)
						if metadataPrevious and MetaImage.Attribute in metadataPrevious: MetaImage.update(media = MetaImage.MediaSeason, images = metadataPrevious[MetaImage.Attribute], data = metadata, category = MetaImage.IndexPrevious, copy = True)
						if metadataNext and MetaImage.Attribute in metadataNext: MetaImage.update(media = MetaImage.MediaSeason, images = metadataNext[MetaImage.Attribute], data = metadata, category = MetaImage.IndexNext, copy = True)

						title = metadata['tvshowtitle'] if 'tvshowtitle' in metadata else metadata['title']
						label2 = Regex.replace(data = Translation.string(35362) % '', expression = '\s+', replacement = ' ', all = True)
						if submenu: label = Translation.string(35362) % str(metadata['season'])
						else: label = label2

						self.itemDetail(media = Media.Recap, metadata = metadata, submenu = submenu)
						label = self.label(media = Media.Recap, metadata = metadata, label = label, multiple = multiple, submenu = submenu)

						for i in ['episode', 'premiered', 'aired', 'genre', 'duration', 'airs', 'voting', 'rating', 'votes', 'userrating', 'labelBefore', 'labelAfter', 'taglineBefore', 'taglineAfter', 'plotBefore', 'plotAfter']:
							try: del metadata[i]
							except: pass
						metadata.update(metadataReuse)
						metadata['pack'] = pack # For itemPlayback().

						metadata['query'] = title
						metadata['title'] = label
						metadata['originaltitle'] = label2
						metadata['tagline'] = Translation.string(35362) % str(metadata['season'])
						metadata['plot'] = Translation.string(35657) % (str(metadata['season']), title)
						metadata['duration'] = Recap.Duration
						if premieredFirst: metadata['premiered'] = metadata['aired'] = premieredFirst # Looks beter in skins that show the date.

						# The current season metadata is needed to correctly marked the Recap menu entry as watch in itemPlayback() for seasons that do not exist on Trakt.
						# Eg: The Office UK S03 (IMDb).
						if metadata2: metadata['seasons'] = {'recap' : metadata2}

						item = self.item(
							metadata = metadata,

							media = Media.Recap,
							submenu = submenu,

							contextMode = Context.ModeVideo,

							video = Recap.Id,
							label = label,
						)
						return [item['command'], item['item'], False]
		except: Logger.error()
		return None

	def itemExtra(self, metadata, media = None, multiple = None, submenu = None):
		try:
			if media is None: media = self.media(metadata = metadata)
			if multiple is None: multiple = self.multiple(metadata = metadata) if (media == Media.Season or media == Media.Episode) else False

			if media == Media.Episode and not multiple:
				if self.mShowBonusExtra and Bonus.enabled():
					if Tools.isArray(metadata): metadata = metadata[-1]
					season = metadata['season']
					if season > 0:
						ended = True
						try: status = metadata['serie']['show']['status']
						except: status = None

						# If the current last episode has not been aired yet, do not show extras.
						# Only do this if the last episode in the menu is not the finale.
						# That is, the last episode might not have been aired yet, but still show the extra if it is the finale and we know there is no episode after it.
						if ended:
							type = metadata.get('type')
							if not type or not(Media.Finale in type and not Media.Middle in type):
								premiered = self.time(type = MetaTools.TimePremiere, metadata = metadata, estimate = False, fallback = False) # Do not estimate for future seasons with only one episode currently listed.
								if premiered and premiered > self.mTimeCurrent: ended = False
								elif not premiered and metadata.get('episode') == 1: ended = False # Only a single new unaired episode without a release date.

						# If the current last episode is lower than the available episodes in the season, do not show extras.
						premieredLast = None
						if ended:
							found = False
							pack = metadata.get('pack')
							if pack:
								pack = MetaPack.instance(pack = pack)

								# Important to check the official number before the standard number, if there are discrepancies between Trakt and TVDb numbering.
								# Eg: One Piece - Progress submenu starting from S01E20. Navigate to the next page until the end of S02. Make sure there is a "Season 2 Extras" after S02E16.
								last = pack.numberLastOfficialEpisode(season = metadata['season'])
								if not last: last = pack.numberLastStandardEpisode(season = metadata['season'])

								if not last is None:
									premieredLast = pack.time(season = metadata['season'], episode = last)

									found = True
									if metadata['episode'] < last: ended = False

								# Sometimes the new unaired season does not form part of the pack data.
								if not found:
									# If the show has ended, but the episode could not be found, it might be because it is not in the pack.
									# The season might only be available on IMDb, but on no other providers.
									# Eg: Money Heist S04 + S05.
									if not status in MetaTools.StatusesPast:
										values = [i['number'][MetaData.NumberStandard] for i in pack.season(default = [])]
										if values and season > max(values): ended = False

						if ended:
							# Ensures that the Extras are automatically marked as watched if the last episode in the season was watched.
							metadataReuse = {i : metadata[i] for i in ['playcount', 'watched', 'overlay', 'lastplayed', 'date', 'dateadded'] if i in metadata}
							metadataReuse['extra'] = {'season' : metadata['season'], 'episode' : metadata['episode']}

							pack = metadata.get('pack')
							metadata = metadata.get('seasons')
							if metadata:
								metadataPrevious = metadata.get('previous')
								metadataCurrent = metadata.get('current')
								metadataNext = metadata.get('next')
								metadata = self.copy(metadataCurrent or metadataNext or metadataPrevious)
							if not metadata: return None

							# Copy images, otherwise if there is an Extras from the previous season and a Recap from the next seasons (eg: Trakt progress submenu), the image dictionary is changed, causing exceptions.
							if metadataCurrent and MetaImage.Attribute in metadataCurrent:
								MetaImage.update(media = MetaImage.MediaSeason, images = metadataCurrent[MetaImage.Attribute], data = metadata, copy = True)
								MetaImage.update(media = MetaImage.MediaSeason, images = metadataCurrent[MetaImage.Attribute], data = metadata, category = MetaImage.MediaSeason, copy = True)
							if metadataCurrent and MetaImage.Attribute in metadataCurrent and MetaImage.MediaShow in metadataCurrent[MetaImage.Attribute]: MetaImage.update(media = MetaImage.MediaSeason, images = metadataCurrent[MetaImage.Attribute][MetaImage.MediaShow], data = metadata, category = MetaImage.MediaShow, copy = True)
							if metadataPrevious and MetaImage.Attribute in metadataPrevious: MetaImage.update(media = MetaImage.MediaSeason, images = metadataPrevious[MetaImage.Attribute], data = metadata, category = MetaImage.IndexPrevious, copy = True)
							if metadataNext and MetaImage.Attribute in metadataNext: MetaImage.update(media = MetaImage.MediaSeason, images = metadataNext[MetaImage.Attribute], data = metadata, category = MetaImage.IndexNext, copy = True)

							title = metadata['tvshowtitle'] if 'tvshowtitle' in metadata else metadata['title']

							label2 = Regex.replace(data = Translation.string(35791) % '', expression = '\s+', replacement = ' ', all = True)
							if submenu: label = Translation.string(35791) % str(metadata['season'])
							else: label = label2

							self.itemDetail(media = Media.Extra, metadata = metadata, submenu = submenu)
							label = self.label(media = Media.Extra, metadata = metadata, label = label, multiple = multiple, submenu = submenu)

							for i in ['episode', 'premiered', 'aired', 'genre', 'duration', 'airs', 'voting', 'rating', 'votes', 'userrating', 'labelBefore', 'labelAfter', 'taglineBefore', 'taglineAfter', 'plotBefore', 'plotAfter']:
								try: del metadata[i]
								except: pass
							metadata.update(metadataReuse)
							metadata['pack'] = pack # For itemPlayback().

							metadata['title'] = label
							metadata['originaltitle'] = label2
							metadata['tagline'] = Translation.string(35791) % str(metadata['season'])
							metadata['plot'] = Translation.string(35649) % (str(metadata['season']), title)
							metadata['duration'] = Recap.Duration # Add a duration, otherwise when scrolling it looks bad if suddenly the duration disappears in the skin.
							if premieredLast: metadata['premiered'] = metadata['aired'] = Time.format(premieredLast, format = Time.FormatDate) # Also looks beter in skins that show the date.

							item = self.item(
								metadata = metadata,

								media = Media.Extra,
								submenu = submenu,

								label = label,
							)
							return [item['command'], item['item'], True]
		except: Logger.error()
		return None

	###################################################################
	# DIRECTORY
	###################################################################

	def directories(self, metadatas, media = None, niche = None, person = None, more = True, folder = True):
		items = []

		for metadata in metadatas:
			try:
				item = self.directory(media = media, niche = niche, metadata = metadata, person = person)
				if item:
					foldered = metadata.get('folder')
					if foldered is None: foldered = folder
					items.append([item['command'], item['item'], foldered])
			except: Logger.error()

		if more:
			itemMore = self.itemMore(metadata = metadatas, media = media, niche = niche, data = more)
			if itemMore: items.append(itemMore)

		return items

	def directory(self, metadata = None, media = None, niche = None, person = None, item = None, context = None):
		try:
			if not item: item = self.itemCreate()

			try: parameters = metadata['parameters']
			except: parameters = {}

			contextual = metadata.get('context') or {}
			media = metadata.get('media') or media
			niche = metadata.get('niche') or niche
			name = label = Translation.string(metadata.get('name') or metadata.get('label'))
			action = metadata.get('action')

			if metadata:
				data = {}

				if person: data['title'] = name
				if parameters.get('more'): label = Format.fontItalic(label)

				if 'plot' in metadata and metadata['plot']: data['plot'] = metadata['plot']
				elif 'description' in metadata and metadata['description']: data['plot'] = metadata['description']
				else: data['plot'] = System.navigationDescription(name = name)

				if data: self.itemInfo(item = item, metadata = data)

			item.setLabel(label)

			if metadata['image'].startswith('http'):
				icon = thumb = poster = banner = metadata['image']
			else:
				icon, thumb, poster, banner = Icon.pathAll(icon = metadata['image'], default = self.mThemeThumb)
				Directory.decorate(item = item, icon = metadata['image']) # For Gaia Eminence.

			images = {
				MetaImage.TypePoster : poster,
				MetaImage.TypeThumb : thumb,
				MetaImage.TypeFanart : self.mThemeFanart,
				MetaImage.TypeLandscape : self.mThemeFanart,
				MetaImage.TypeBanner : banner,
				MetaImage.TypeClearlogo : icon,
				MetaImage.TypeClearart : icon,
				MetaImage.TypeDiscart : poster,
				MetaImage.TypeIcon : icon,
			}
			MetaImage.set(item = item, images = images)

			if not 'media' in parameters: parameters['media'] = media
			if not 'niche' in parameters: parameters['niche'] = niche
			if 'niche' in parameters:
				niche = parameters['niche']
				if niche: parameters['niche'] = Media.stringTo(niche)
				else: del parameters['niche']

			# Add additional context options for explore and search menus.
			provider = contextual.get('provider')

			# Do this before addtional parameters are added.
			library = None
			if provider: # Only add muti-library links for directories that contain titles underneath them, not for higher-up directories.
				library = metadata.get('library')
				if library is None or library is True: library = Networker.linkCreate(parameters = parameters)

			parameters[System.NavigationParameter] = System.navigation(name = name)

			# Do not optimize/encode the command parameters.
			# This makes it easier to read, so that users can add skin shortcuts and easily manipulate the URL.
			optimize = metadata.get('optimize', False)
			command = System.command(action = action, parameters = parameters, optimize = optimize)

			shortcut = parameters.get(Shortcut.Parameter)
			if shortcut: shortcut = Shortcut.item(id = shortcut, label = name, create = False, delete = True) # The context menu from a shortcut item itself.
			else: shortcut = Shortcut.item(label = name, folder = True, create = True, delete = False)

			context = self.itemContext(item = item, context = context, mode = Context.ModeGeneric, media = media, niche = niche, command = command, provider = provider, library = library, shortcut = shortcut)

			return {'item' : item, 'command' : command, 'context' : context, 'images' : images}
		except: Logger.error()
		return None

	###################################################################
	# CONTEXT
	###################################################################

	def context(self,
		context = None,
		mode = None,

		media = None,
		niche = None,
		video = None,

		command = None,
		provider = None,
		library = None,
		playlist = None,

		source = None,
		metadata = None,
		orion = None,
		shortcut = None,
		mixed = None,
	):
		if context is None: context = self.mContext
		if context:
			if metadata:
				if not mode: mode = Context.ModeItem
				if not media: media = self.media(metadata = metadata)
				if not command: command = self.command(metadata = metadata, media = media, niche = niche)
			else:
				if not mode: mode = Context.ModeGeneric

			return Context(
				mode = mode,
				media = media,
				niche = niche,
				video = video,

				link = command,
				provider = provider,
				library = library,
				playlist = playlist,

				source = source,
				metadata = metadata,
				orion = orion,
				shortcut = shortcut,
				mixed = mixed,
			)
		return None

	###################################################################
	# COPY
	###################################################################

	@classmethod
	def copy(self, metadata):
		# Do not make a deep copy of the pack and season data.
		# For shows with a lot of seasons/episodes, the pack dictionary can be very large.
		# Just copying the pack already takes a long time.
		# And there should not be a reason to copy the pack, because it is static and not edited/cleaned like the rest of the metadata.
		# Eg: Coronation Street - S01 has only 7 episodes, but loads 4-5 secs without the code below, or 2.5 secs with the code.

		if metadata and 'pack' in metadata:
			temp = {}
			attributes = ['pack', 'seasons']

			for i in attributes:
				try:
					temp[i] = metadata[i]
					del metadata[i]
				except: pass

			result = Tools.copy(metadata)

			for key, value in temp.items():
				metadata[key] = value
				result[key] = value

			return result
		else:
			return Tools.copy(metadata)

	# copy = False: Delete the exclusions directly from the original dictionary.
	# copy = None: Create a shallow copy of the original dictionary without the exclusions. Inner dicts/lists are still references that are not copied.
	# copy = True: Create a deep copy of the original dictionary without the exclusions. Inner dicts/lists are also deep copied.
	@classmethod
	def reduce(self, metadata, pack = False, seasons = False, exclude = None, copy = None):
		if metadata is None: return metadata

		excludes = {}
		if pack: excludes['pack'] = True
		if seasons: excludes['seasons'] = True
		if exclude:
			if Tools.isDictionary(exclude): excludes.update(exclude)
			elif Tools.isArray(exclude): excludes.update({i : True for i in exclude})
			elif Tools.isString(exclude): excludes[exclude] = True

		if copy is False:
			for i in excludes.keys():
				try: del metadata[i]
				except: pass
		else:
			metadata = {k : v for k, v in metadata.items() if not k in excludes}
			if copy is True: metadata = Tools.copy(metadata)

		return metadata

	###################################################################
	# CLEAN
	###################################################################

	'''
		exclude:
			True: Attributes that should be removed even if they are officially supported by Kodi. Uses the default exclude attributes. This is useful if the skin should be forced (eg: streams directory - do not show the movie title, but use the custom createrd label instead).
			List: Attributes that should be removed even if they are officially supported by Kodi.
		studio:
			True: If no studio is specified in the metadata, add an empty string as the studio. This prevents some skins (eg: Aeon Nox) from showing thumbnails instead of of the studio logo for certain views. Also reduces it down to a single studio, since the studio icon addon does not display anything if multiple studios are specified.
			False: If no studio is specified in the metadata, leave it as is and do not add an empty string. Also allows multiple studios.
	'''
	def clean(self, metadata, media = None, exclude = False, studio = True, icon = True):
		if not metadata: return None
		if Tools.isString(metadata): metadata = Converter.jsonFrom(metadata)
		else: metadata = self.copy(metadata) # Create a copy, since we do not want to edit the outside dictionary passed to this function.
		if media is None: media = self.media(metadata = metadata)

		# Do not replace if already set (eg: video.py -> playing trailers in cinematic mode).
		# This is shown in the Kodi info dialog under "Type: ..." with lower case letters.
		# We can change these to title case (eg: "Movie") and it shows correctly/aesthetically in the Kodi info dialog.
		# However, other Kodi features (eg player, skins, etc) might specifically compare stings with lower case, so leave them for now.
		if not 'mediatype' in metadata or not metadata['mediatype']:
			if media == Media.Movie: metadata['mediatype'] = 'movie'
			elif media == Media.Show: metadata['mediatype'] = 'tvshow'
			elif media == Media.Season: metadata['mediatype'] = 'season'
			elif media == Media.Episode: metadata['mediatype'] = 'episode'
			elif media == Media.Recap: metadata['mediatype'] = 'episode'
			elif media == Media.Extra: metadata['mediatype'] = 'episode'

		# Remove the season number, otherwise some skins (eg Estuary) display the number in the info dialog prepended to the title.
		if media == Media.Recap or media == Media.Extra:
			try: del metadata['season']
			except: pass
			try: del metadata['episode']
			except: pass

		try: metadata['duration'] = int(metadata['duration'])
		except: pass
		try: metadata['tvshowyear'] = int(metadata['tvshowyear'])
		except: pass
		try: metadata['year'] = int(metadata['year'])
		except: pass

		# Do before cleaning the metadata, since we need the IDs.
		self.cleanTrailer(metadata = metadata, media = media)

		# Do before cleaning the metadata, since we need the 'voting'.
		self.cleanVoting(metadata = metadata)

		# Do this before data is saved to the MetaCache.
		# Otherwise a bunch of regular expressions are called every time the menu is loaded.
		#self.cleanDescription(metadata = metadata)

		self.cleanStatus(metadata = metadata, media = media)
		self.cleanGenre(metadata = metadata)
		self.cleanCountry(metadata = metadata)
		self.cleanCertificate(metadata = metadata)
		self.cleanCast(metadata = metadata)
		self.cleanCrew(metadata = metadata)
		self.cleanStudio(metadata = metadata, media = media, empty = studio, reduce = studio)

		# Filter out non-existing/custom keys.
		# Otherise there are tons of errors in Kodi 18 log.
		# Do this last, since some attributes might be required in the function calls above (eg: network).
		allowed = self.mMetaAllowed
		if exclude:
			if not Tools.isArray(exclude): exclude = self.mMetaExclude
			allowed = [i for i in allowed if not i in exclude]

		# Icons and labels disabled in the settings.
		remove = self.mIconExclude if icon else []

		metadata = {k : v for k, v in metadata.items() if k in allowed and not k in remove}

		return metadata

	@classmethod
	def cleanId(self, metadata = None, id = None):
		# Sometimes IMDb IDs show up as "ttt..." (tripple t).
		# Not sure where it comes from.
		# Maybe some APIs have mistakes in their IDs.
		# Eg: ttt4154796
		# Update: this was caused by:
		#	'tt' + Regex.remove(data = str(imdb), expression = '[^0-9]', all = True)
		# That was called without "all = True", therefore only replacing the first t.
		# This has been fixed now.
		if metadata:
			try:
				if metadata['imdb'].startswith('ttt'): metadata['imdb'] = 'tt' + metadata['imdb'].replace('t', '')
			except: pass
			for i in ['show', 'season', 'episode']:
				try:
					if metadata['id'][i]['imdb'].startswith('ttt'): metadata['id'][i]['imdb'] = 'tt' + metadata['id'][i]['imdb'].replace('t', '')
				except: pass
			return metadata
		elif id:
			if id.startswith('ttt'): id = 'tt' + id.replace('t', '')
			return id
		else:
			return None

	@classmethod
	def cleanTitle(self, title, media = None, parts = None):
		if not title: return None
		if Media.isSet(media):
			# Remove the "Collection" part at the end, for both Trakt and TMDb.
			# TMDb typically also has collections starting with "The ...".
			# Sometimes "The" is essential, like "The Hobbit", but sometimes it is not, like "The Hannibal" or "The Bourne".
			# Test this with:
			#	Avatar Collection (87096)
			#	The Lord of the Rings Collection (119)
			#	The Making of The Lord of the Rings Collection (1173608)
			#	The Hobbit Collection (121938)
			#	The Bourne Collection (31562)
			#	The Hannibal Lecter Collection (9743)
			#	The Terminator Collection (528)
			#	The Fast and the Furious Collection (9485)
			#	Spider-Man (TV) Collection (225941)
			#	Spider-Man Collection (556)
			#	The Amazing Spider-Man Collection (125574)

			# Remove the trailing keyword.
			title = Regex.remove(data = title, expression = '(?:\s*-\s*)?(?:\s*movie\s*)?(?:\s*[\[\(\{])?\s*((?:d(?:i|uo|ou)|tr[iy]|(?:quadr[iao]|tetr[ao])|penta|hex[ao]|hept[ao]|oct[ao]|enn?e[ao]|dec[ao]|antho)log(?:(?:i|í)[ae]?|y)s?|coll?ecti(?:on|e)s?|colecci(?:o|ó)n|cole(?:c|ç)(?:a|ã)o|collezione|kollektion(?:en)?|kolekcja|kolekce|koleksiyonu|sagas?|set|seri|sammlung|(?:film)?reihe|komplett|verzameling|samling|filmene|трилогия|коллекция|полный)(?:\s*[\]\)\}])?$', all = True, cache = True)

			# Determine if the leading "The" should be removed.
			if title.startswith('The ') and not title.startswith('The Making'):
				the = True
				total = 0
				exact = 0
				prefix = 0
				starts = 0

				if parts:
					total = len(parts)
					expression = '^' + Regex.escape(title) + '\s*[\:\-]\s+'
					for i in parts:
						i = i.get('title')
						if i:
							if i == title: exact += 1
							if Regex.match(data = i, expression = expression): prefix += 1
							if i.startswith(title): starts += 1

				# The set contains at least one movie with the exact title as the collection.
				#	Eg: The Terminator Collection
				# Or a movie in the set starts with the collection title prefix (contains : or -).
				#	Eg: The Lord of the Rings Collection
				#	Eg: The Hobbit Collection
				# Or a movie starts with the collection title (excluding : or -), but there is more than one word.
				#	Eg (exclude): The Bourne Collection (assuming the last movie was never there and all movies start with "The Bourne ...").
				if total and (exact or prefix or (starts and (title.count(' ') + title.count('-')) > 1)): the = False

				if the: title = Regex.remove(data = title, expression = '^the\s+', cache = True)
		else:
			title = title.lower()
			title = Regex.remove(data = title, expression = '&#(\d+);', cache = True)
			title = Regex.replace(data = title, expression = '(&#\d+)([^;\d]+)', replacement = r'\1;\2', cache = True)
			title = title.replace('&quot;', '\"').replace('&amp;', '&')
			title = Regex.remove(data = title, expression = '\n|(\[.+?\])|(\(.+?\))|\s(vs|v\.)\s|[\.,_\-\?\!:;"\']', cache = True)
		return title.strip()

	def cleanDescription(self, metadata):
		try:
			for i in ('plot', 'tagline'):
				description = metadata.get(i)
				if description:
					# Some have no plot, just showing "Add a Plot<a ...".
					if Regex.match(data = description, expression = '(add\s*a\s*(?:plot|tag))'): description = None

					if description:
						# Some plots end with a URL.
						description = Regex.remove(data = description, expression = '.{10,}\.(\s*(?:[a-z\d\s\-\,\;\:\\\']*)(?:https?:\/\/|www\.).*?$)', group = 1)

						# Some plots end with "see full summary".
						description = Regex.remove(data = description, expression = '.{10,}(see\s*full\s*summary.*$)', group = 1).strip()

						# Some plots start with "Short synopsis (50 words)".
						# https://www.imdb.com/title/tt20158938/
						description = Regex.remove(data = description, expression = '(short\s*synopsis\s*(?:[\[\(]\d+\s*words?[\]\)]\s*)?(?:docu(?:mentary)?|short|movie|film|(?:tv\s*)?show|series?)?,?\s*)', group = 1)

						# Symbols without spacing, which prevents line breaks.
						# Eg (Mad Max 2 tagline): When all that's left is one last chance, pray that he's still out there...somewhere!
						try:
							symbols = Regex.extract(data = description, expression = '(?:[a-z\d\s]([\.\,\-\+]{2,})[a-z\d]|[a-z\d]([\.\,\-\+]{2,})[a-z\d\s])', group = None, all = True)
							if symbols:
								for s1 in symbols:
									if s1 and Tools.isArray(s1):
										for s2 in s1:
											if s2: description = description.replace(s2, ' ' + s2 + ' ')
						except: Logger.error()

						# Some plots are cut off and do not end with a full stop.
						if Regex.match(data = description, expression = '[a-z\d]$'): description += ' ...'

						# Remove duplicate spaces.
						description = Tools.stringRemoveSpace(description).strip()

					metadata[i] = description
		except: Logger.error()

	@classmethod
	def cleanGenre(self, metadata = None, full = True):
		try:
			# Still allow non-convetional genre slugs.
			# This allows old metadata to still be displayed (although some other features like filtering might ignore it).
			# Also allows providers to add new genres and still display them in Kodi.
			genre = metadata.get('genre')
			if genre:
				# Move miniseries to the front, since it is not really a genre, and looks better if placed at the front or back.
				try:
					genre.remove(MetaTools.GenreMini)
					genre.insert(0, MetaTools.GenreMini)
				except: pass

				genres = self.genre()
				result = []
				for i in genre:
					if i and not i == MetaTools.GenreNone:
						j = genres.get(i)
						if j: result.append(j.get('label').get('full' if full else 'short'))
						else: result.append(i.title())

				metadata['genre'] = result
		except: Logger.error()

	def cleanStatus(self, metadata = None, media = None):
		try:
			status = metadata.get('status')

			# Check the episode air date and update the status according to the current date.
			if Media.isEpisode(media):
				try: premiered = metadata['time'][MetaTools.TimePremiere]
				except: premiered = None
				if premiered: status = MetaTools.StatusEnded if premiered < self.mTimeCurrent else MetaTools.StatusUpcoming
				else: status = MetaTools.StatusUpcoming # Future seasons often do not have premiere dates for their episodes yet.

			if status: metadata['status'] = MetaTools.Status.get(status, {}).get('label') or status.title()
		except: Logger.error()

	def cleanCountry(self, metadata):
		try:
			# Change country codes to names.
			country = metadata.get('country')
			if country: metadata['country'] = [Country.name(i) if len(i) <= 3 else i for i in country]
		except: Logger.error()

	def cleanCertificate(self, metadata):
		try:
			certificate = metadata.get('mpaa')
			if certificate:
				certificate = Audience.format(certificate)
				if certificate: metadata['mpaa'] = certificate
		except: Logger.error()

	def cleanVoting(self, metadata, round = False):
		'''
			The rating is calculated twice:
				1. Once the metadata is retrieved the first time and before it is saved to the MetaCache.
				   This ensures there is always a rating/votes if the metadata dictionary is used/passed elsewhere where is does not get cleaned first.
				2. Every time the metadata gets cleaned, that is every time a menu is loaded.
				   This has the advantage of not having to re-retrieve metadata (invalidating the metadata in MetaCache due to the 'settings' property) if the user changes the rating settings.
				   Another advantage is that we can later add code to retrieve the user's ratings from Trakt and overlaying it (similar to the playcount, watched, progress).
				   Then if the user casts a new vote, the rating can be dynamically added and recalculated once the menu is loaded, without having to re-retrieve metadata before saving it to MetaCache.
		'''
		voting = self.voting(metadata = metadata)
		if voting:
			for i in ['rating', 'userrating']:
				if i in voting and not voting[i] is None:
					rating = voting[i]
					if rating and rating > 0 and rating < 0.1: rating = 0.1 # Some skins (eg: Estaury) show a 0.0 rating for low ratings like 0.004 (eg: Jeopardy! S38).
					metadata[i] = Math.round(rating, places = 3) if round else rating # Has many decimal places, which just takes up unnecessary space in the MetaCache.
			for i in ['votes']:
				if i in voting and not voting[i] is None: metadata[i] = voting[i]

		if round:
			data = metadata.get('voting')
			if data:
				data = data.get('rating')
				if data:
					for k, v in data.items():
						if not v is None: data[k] = Math.round(v, places = 3)

	def cleanCast(self, metadata):
		try:
			for i in ['cast', 'castandrole']:
				if i in metadata:
					cast = metadata[i]
					if not cast: del metadata[i]
					elif cast and Tools.isDictionary(cast[0]): metadata[i] = [(j.get('name'), j.get('role')) for j in cast]
		except: Logger.error()

	def cleanCrew(self, metadata):
		try:
			for i in ['director', 'writer']:
				if i in metadata:
					crew = metadata[i]
					if crew:
						if Tools.isDictionary(crew[0]): metadata[i] = [j['name'] for j in crew]
						elif Tools.isArray(crew[0]): metadata[i] = [j[0] for j in crew]
					else: del metadata[i]
		except: Logger.error()

	def cleanStudio(self, metadata, media = None, studio = True, network = True, empty = True, reduce = True):
		try:
			# Some studio names are not detected and no logos are shown in the menus (eg: Aeon Nox).

			studios = None
			if studio:
				studios = metadata.get('studio')
				if studios and not Tools.isArray(studios): studios = [studios]
			if not studios: studios = []

			networks = None
			if network:
				networks = metadata.get('network')
				if networks and not Tools.isArray(networks): networks = [networks]
			if not networks: networks = []

			# More icons for show networks in the icon pack than for show studios.
			values = (networks + studios) if (Media.isSerie(media) or Media.isBonus(media)) else (studios + networks)

			# This entire section takes 20-50ms for 50 items.
			# Around 20ms is used just for initializing MetaCompany.helper().
			if values and reduce:
				# Kodi documentation states that the studio attribute can be a string or a list.
				# However, studio icons does not work with multiple studios and needs a single studio.
				# Eg:  DoWork - Direct texture file loading failed for resource://resource.images.studios.white/Columbia Pictures / Relativity Media / Pariah.png

				addon = MetaCompany.helperAddon()
				if addon['enabled'] and not addon['mode'] in (MetaCompany.ModeDisabled, MetaCompany.ModeSingle, MetaCompany.ModeMultiple):
					include = MetaCompany.helperInclude() # Icons that are available in the studio icon addon.
					partial = MetaCompany.helperPartial()
					replacement = MetaCompany.helperReplacement()
					preference = MetaCompany.helperPreference().get(Media.Show if Media.isSerie(media) else None)

					# Prefer "HBO Max" or "Max" over "HBO".
					if preference:
						for value in preference:
							try:
								values.insert(0, values.pop(values.index(value)))
								break
							except: pass

					for value in values:
						for k, v in partial.items():
							v = Regex.replace(data = value, expression = k, replacement = v, group = 1, cache = True)
							if not v == value:
								value = v
								break

						# Replace BEFORE looking up the includes, since it will cahnge the lookup value.
						for k, v in replacement.items():
							if Regex.match(data = value, expression = k, cache = True):
								if v: value = v # Value can be None. Stop scanning and keep current value.
								break

						if include and value.lower() in include:
							values = [value]
							break

				# Always use a single company, even when not found in include.
				# Some skins, like Aeon Nox Silvo, display a label if no icon can be found, and the label should be brief.
				if (addon['enabled'] and not addon['mode'] == MetaCompany.ModeMultiple) or addon['mode'] == MetaCompany.ModeSingle: values = [values[0]]

			# Some skins, like Aeon Nox (List View), show the poster in the menu when there is no studio.
			# This looks ugly, so set an empty studio.
			# Do not use space or empty string, since it will be ignored by the skin.
			# Do not use a string that contains visible characters (eg: '0'), since some view types (eg: Aeon Nox - Icons) will show the studio as text if no icon is availble.
			if empty and not values and not media == Media.Set and Skin.isAeon(): values = ['\u200c']

			if not values: metadata['studio'] = None
			elif self.mKodiNew: metadata['studio'] = values
			else: metadata['studio'] = values[0]

		except: Logger.error()

	def cleanTrailer(self, metadata, media = None):
		if metadata:
			trailer = {}
			if media is None: media = self.media(metadata = metadata)

			trailer['video'] = 'trailer'
			trailer['media'] = media
			try:
				if metadata['imdb']: trailer['imdb'] = metadata['imdb']
			except: pass
			try:
				if metadata['tmdb']: trailer['tmdb'] = metadata['tmdb']
			except: pass
			try:
				if metadata['tvdb']: trailer['tvdb'] = metadata['tvdb']
			except: pass
			try: trailer['title'] = metadata['tvshowtitle']
			except:
				try: trailer['title'] = metadata['title']
				except: pass
			try: trailer['year'] = metadata.get('tvshowyear') or metadata['year']
			except: pass
			try: trailer['season'] = metadata['season']
			except: pass
			try: trailer['link'] = metadata['trailer']
			except: pass

			metadata['trailer'] = System.command(action = 'streamsVideo', parameters = trailer)

	###################################################################
	# MERGE
	###################################################################

	# Merge multiple lists of values from different providers.
	# frequency: The degree of matching to determine which values are the same and which ones should be placed first, based on their frequency of occurance.
	#	frequency=0: No matching, just interleave the vales and remove duplicates.
	#	frequency=1: Matching of the raw values. For values that are consistent, like enums. Eg: genres, languages.
	#	frequency=2: Matching of words within the values. For values that are not consistent. Eg: studios, networks.
	# order: Use the order to determine the final rank items are sorted by. The order can consist of two parts: the provider order (eg prefer Trakt values over TMDb values) and the internal order (eg the order in which each of the providers returns the values).
	#	order=None: Do not use the order at all. Simply use the number of occurrences, irrespective of the provider or internal order. Eg: items that occur frequently are moved to the front.
	#	order=False: Ignore the provider order and sort based on the combined/average internal order. Eg: items that are closer to the front across all providers are moved to the front.
	#	order=True: Use the provider and internal order, which more emphasis on the provider order. Eg: items that occur first in the preferred provider(s) are moved to the front.
	def merge(self, values, reverse = True, frequency = None, lookup = None, ignore = None, last = None, order = None):
		if values:
			values = [i for i in values if i]
			if values:
				if reverse: values = values[::-1] # MetaManager adds the most important providers to the end of the list.

				if Tools.isList(values[0]):
					# Get the original index before interleaving.
					# Give the 1st entry a higher weight (eg: TVDb perfered network).
					# Give a heavier weight to the most preferred network (-1).
					# NB: Sometimes a value can be None, causing j.lower() to fail. Always check the value.
					values = [[{'id' : Tools.replaceNotAlphaNumeric(j.lower()), 'value' : j, 'index' : y, 'order' : (x if x else -1) if order else 0} for y, j in enumerate(i) if j] for x, i in enumerate(values) if i]
					values = Tools.listInterleave(*values)
				else:
					values = [{'id' : Tools.replaceNotAlphaNumeric(i.lower()), 'value' : i, 'index' : x} for x, i in enumerate(values) if i]

				if len(values) > 1: # Save some time by not doing this for single-item lists (eg: languages.)
					ranks = {}
					base = 999999

					if frequency:
						if frequency is True or frequency == 1:
							counts = {}
							for item in values:
								id = item['id']
								try: counts[id] += 1
								except: counts[id] = 1
							values = Tools.listSort(data = values, key = lambda i : counts.get(i['id']) or 0, reverse = True)

						elif frequency == 2:
							# Test this with:
							#	Harry Potter (Warner Bros. should be listed before 1492 and Heyday).
							#		[['Warner Bros.', 'Heyday Films', '1492 Pictures'], ['Warner Bros. Pictures', 'Heyday Films', '1492 Pictures'], ['Warner Bros. Pictures', '1492 Pictures', 'Heyday Films']]
							#		[['Warner Bros.', 'Heyday Films', '1492 Pictures'], ['Warner Bros. Pictures', 'Heyday Films', '1492 Pictures'], ['1492 Pictures', 'Heyday Films', 'Warner Bros. Pictures']]
							#	The Hobbit: An Unexpected Journey (IMDb lists them as follows: MGM, New Line Cinema, WingNut Films)
							#		[['Metro-Goldwyn-Mayer (MGM)', 'New Line Cinema', 'WingNut Films'], ['New Line Cinema', 'Metro-Goldwyn-Mayer', 'WingNut Films', 'Warner Bros. Pictures', 'Warner Bros. Entertainment'], ['WingNut Films', 'New Line Cinema', 'Metro-Goldwyn-Mayer', 'Warner Bros. Pictures', 'Warner Bros. Entertainment']]
							# 	Vikings (tt2306299) (check seasons networks)
							#		[['Prime Video', 'History'], ['Amazon'], ['History Canada']]
							#	Snowpiercer (tt6156584)
							#		[['TNT', 'AMC'], ['AMC'], ['TNT (US)', 'AMC']]
							#	Community (tt1439629)
							#		[['NBC', 'Yahoo! Screen'], ['Yahoo! Screen'], ['NBC', 'Yahoo! Screen', 'YouTube']]
							#	The Boys (tt1190634)
							#		[['Prime Video'], ['Amazon'], ['Prime Video', 'YouTube']]
							#	Star Trek (1966) (tt0060028)
							#		[['NBC'], ['Syndication']]
							#		[['NBC'], ['Spike TV']]
							#	Brooklyn Nine-Nine (tt2467372)
							#		[['NBC', 'FOX'], ['FOX'], ['FOX', 'NBC', 'YouTube']]

							# Move "Syndication" to the back.
							# Eg: Star Trek (1966)
							if last:
								temp1 = []
								temp2 = []
								for i in values:
									if i['value'] in last:
										i['order'] = (i.get('order') or 0) + base
										temp2.append(i)
									else:
										temp1.append(i)
								values = temp1 + temp2

							for i, item in enumerate(values):
								# Important for the 2nd loop, using the test case above.
								# Every entry should be counted separately, even if they have the exact same value.
								item['unique'] = item['id'] + str(i)

								words = Tools.replaceNotAlphaNumeric(item['value'], replace = ' ').split(' ')
								if lookup:
									value = lookup.get(item['value'])
									if value: words.extend(Tools.replaceNotAlpha(value, replace = ' ').split(' '))

								# Allow "20th" (20th Studios), but also add "BBC" for "BBC2".
								for j in words:
									word = Tools.replaceNotAlpha(j)
									if not word == j: words.append(word)

								words = [j.lower() for j in words if len(j) > 3 or (len(j) > 1 and j.isupper())]
								if ignore: words = [j for j in words if not j in ignore]

								item['words'] = words if words else [item['value'].lower()] # Eg: Fox.

							for item1 in values:
								id1 = item1['unique']
								words1 = item1['words']
								index1 = item1['index']
								order1 = item1['order']
								for item2 in values:
									if not item1 == item2:
										words2 = item2['words']
										if any(w in words2 for w in words1):
											id2 = item2['unique']
											index2 = item2['index']
											order2 = item2['order']
											if order:
												# Firstly, prefer the earlier providers ("order").
												# Eg: If a studio is listed 1st by TMDb and IMDb, but 2nd by Trakt, still list it 1st, even if Trakt is considered the "best" provider.
												# Secondly, prefer the order within the provider.
												rank = min(order1 + (index1 / 10000.0), order2 + (index2 / 10000.0)) + 1
												try: ranks[id1] -= rank
												except: ranks[id1] = base - rank
											elif order is False:
												try: ranks[id1].extend([index1, index2])
												except: ranks[id1] = [index1, index2]
												try: ranks[id2].extend([index1, index2])
												except: ranks[id2] = [index1, index2]
											else:
												try: ranks[id1] += 1
												except: ranks[id1] = 1

							if order is False:
								for k, v in ranks.items(): ranks[k] = base - ((sum(v) / float(len(v))) if v else base)
							values = Tools.listSort(data = values, key = lambda i : ranks.get(i['unique']) or 0, reverse = True)

					values = Tools.listUnique(values, attribute = 'id')

				if values: return [i['value'] for i in values]
		return None

	def mergeNiche(self, values, reverse = True):
		if values: values = Tools.listFlatten(values)
		return self.merge(values = values, reverse = reverse, frequency = 1)

	def mergeGenre(self, values, parent = None, reverse = True):
		genres = self.merge(values = values, reverse = reverse, frequency = 1)

		# Use the genre order of the show/season for the season/episode.
		# Eg: American Manhunt: O.J. Simpson
		# Both the show and the episodes had: ['reality', 'documentary', 'crime']
		# Later the providers changed the show to: ['documentary', 'crime', 'reality']
		# But the episodes still have the old/unchanged order.
		# Reorder according to the parent order.
		if parent and genres:
			# Add important genres that are in the show/season, but not in the season/episode.
			for i in (MetaTools.GenreMini, MetaTools.GenreShort):
				if i in parent and not i in genres: genres.append(i)

			try:
				missing = [i for i in genres if not i in parent] # A genre is not in the "parent" list.
				if missing: parent = parent + missing # Creates a new list and does not edit the list passed in.

				genres = Tools.listSort(data = genres, order = parent)
			except: Logger.error() # A genre is not in the "parent" list. Although this is now fixed with "missing".

		return genres

	def _mergeCompany(self, values, country = None):
		if values:
			# Split companies that contain multiple names.
			# Eg: Agat Films & Cie / Ex Nihilo
			temp = []
			for value in values:
				if ' / ' in value and len(value) > 15: temp.extend([i.strip() for i in value.split('/')])
				else: temp.append(value)
			values = temp

			replacements = []

			if country:
				# For Anime, certain companies have the same abbreviation as US companies.
				if 'jp' in country:
					replacements.extend([
						{'expression' : '^(tbs)', 'replacement' : 'Tokyo Broadcasting System', 'group' : 1},
						{'expression' : '^(cbc)', 'replacement' : 'Chubu-Nippon Broadcasting Company', 'group' : 1},
					])

				# Different TV2 stations across the world.
				if 'hu' in country:
					replacements.extend([
						{'expression' : '^(tv2)(?:.*?hungary)?', 'replacement' : 'TV2 (HU)'},
					])

				if 'ru' in country:
					replacements.extend([
						{'expression' : '^(premier)(?:$|\s)(?:.*?russia)?', 'replacement' : 'Premier (RU)'},
					])

			replacements.extend([
				# TMDb sometimes returns "5" for "Channel 5".
				# Eg: The Madame Blanc Mysteries
				{'expression' : '^4$', 'replacement' : 'Channel 4'},
				{'expression' : '^5$', 'replacement' : 'Channel 5'},
			])

			if replacements:
				for i in range(len(values)):
					value = values[i]
					for j in replacements:
						temp = Regex.replace(data = value, expression = j.get('expression'), replacement = j.get('replacement'), group = j.get('group'), cache = True)
						if not temp == value:
							values[i] = temp
							break

			for i in range(len(values)):
				value = values[i]

				# Remove alternative names with numbers, typically coming from IMDb.
				# Eg: "Liberty Films" vs "Liberty Films (II)"
				if '(' in value: value = Regex.remove(data = value, expression = '(\s*\([iv]+\))', group = 1, cache = True)

				values[i] = value

			# Move certain companies to the back.
			temp1 = []
			temp2 = []
			for value in values:
				# Probably not a studio/network, but indicates the original creators.
				# Eg: Anime OAV
				if Regex.match(data = value, expression = '[\s\-]oav($|[\s\-])', cache = True): temp2.append(value)
				else: temp1.append(value)
			values = temp1 + temp2

			# There are often studios/networks coming from different providers that have similar names.
			#	Eg: Film4 vs Film4 Productions
			#	Eg: Dare Pictures vs Dare Pictures (GB)
			# Filter out these "duplicates".
			base = {}
			ignore = MetaCompany.helperIgnore()
			numbers = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen']

			for i in values:
				value = Regex.remove(data = i.lower(), expression = '[\.\,\-\_\+\!\?\(\)\[\]\&]', all = True, cache = True)

				# Remove common words. Full words only.
				for j in ignore: value = Regex.remove(data = value, expression = '(?:^|\s)(' + j + ')(?:$|\s)', group = 1, cache = True)

				# Replace number words. Full words or ending words only.
				# Eg: Film4 vs Film 4 vs FilmFour vs Film Four
				for j, k in enumerate(numbers): value = Regex.replace(data = value, expression = '(' + k + ')(?:$|[\s\-])', replacement = str(j + 1), group = 1, cache = True)

				base[i] = value

			result = []
			founds = {}
			for k1, v1 in base.items():
				if k1 in founds: continue # Already added from previous iteration.

				found = [k1]
				for k2, v2 in base.items():
					if not k1 == k2:
						if Matcher.levenshtein(v1, v2, ignoreCase = True, ignoreSpace = True, ignoreSymbol = True, ignoreNumeric = False) > 0.5:
							found.append(k2)
							# Do not break, in case there are 3 or more similar companies.

				add = None

				# Prefer "+" services. Eg: "Lionsgate+" over "Lionsgate".
				if not add:
					for i in found:
						if '+' in i:
							add = i
							break

				# Prefer country. Eg: "History (CA)" over "History".
				if not add:
					for i in found:
						if '(' in i:
							add = i
							break

				# Else prefer the shorter one, which is more likley to have a studio icon. Eg: "TBS" over "Turner Broadcasting System".
				# Update: This would prefer "Warner Bros." over "Warner Bros. Pictures", which does not look good for sets (eg Harry Potter which has both of them).
				# Instead, prefer acronyms instead of just the shortest one.
				#if not add: add = min(found, key = len)
				if not add: add = min(found, key = lambda x : 0 if x.isupper() else len(x) if len(x) <= 5 else 99999)

				result.append(add)
				for i in found: founds[i] = True

			values = result

		return values

	# order=True: give more weight to more important providers, aka those listed last (or first if reverse=False).
	def mergeNetwork(self, values, reverse = True, order = None, country = None):
		result = self.merge(values = values, reverse = reverse, frequency = 2, lookup = MetaCompany.helperAlias(), ignore = MetaCompany.helperIgnore(), last = MetaCompany.helperSyndication(), order = order)
		return self._mergeCompany(values = result, country = country)

	# other: List of networks that should be moved to the end of the studio list, because they are probably networks and not production companies. Eg: IMDb lists HBO as production company for GoT, while others do not.
	def mergeStudio(self, values, reverse = True, order = None, other = None, country = None):
		result = self.merge(values = values, reverse = reverse, frequency = 2, lookup = MetaCompany.helperAlias(), ignore = MetaCompany.helperIgnore(), last = MetaCompany.helperSyndication(), order = order)
		if other and result:
			temp1 = []
			temp2 = []
			for i in result:
				if any(j in i for j in other): temp2.append(i)
				else: temp1.append(i)
			result = Tools.listUnique(temp1 + temp2)
		return self._mergeCompany(values = result, country = country)

	def mergeLanguage(self, values, reverse = True):
		result = self.merge(values = values, reverse = reverse, frequency = 1)

		# If anyone has listed English first, move English to the start.
		# Sometimes Trakt has English listed later one, although it is the primary language.
		# Eg: Dracula 1992.
		if result and not result[0] == Language.EnglishCode:
			for i in values:
				if i and i[0] == Language.EnglishCode:
					try: result.remove(Language.EnglishCode)
					except: pass
					result.insert(0, Language.EnglishCode)
					break

		return result

	def mergeCountry(self, values, reverse = True):
		return self.merge(values = values, reverse = reverse, frequency = 1)

	def mergeCertificate(self, values, media = None):
		if Tools.isArray(values):
			# TVDb sometimes does not have the MPAA certificate, but a certificate from some other country (eg: AU).
			# https://api4.thetvdb.com/v4/series/418712/extended
			converted = [Audience.convert(certificate = i, media = media) for i in values]

			# If there is an MPAA latrer in the list (eg from Trakt), move it to the front, since the conversion is not always perfect.
			temp1 = []
			temp2 = []
			for i in converted:
				if i in values: temp1.append(i)
				else: temp2.append(i)
			values = temp1 + temp2

			value = Tools.listCommon([i for i in values if i and not i == Audience.CertificateNr], count = 1)
			if value: return value
			return Tools.listCommon(values, count = 1)
		else:
			return Audience.convert(certificate = values, media = media)

	# season: the current season number.
	# episode: the current episode number.
	# seasonReleased: the season number of the last fully released season.
	# time: premiere timestamp of the season or episode.
	# timeFirst: premiere timestamp of the first episode in the season.
	# timeLast: premiere timestamp of the last episode in the current season.
	# timeSeasonNext: premiere timestamp of the first episode of the next season.
	# timeSeasonLast: premiere timestamp of the last episode of the last season.
	# timeEpisode: a list of premiere timestamp of all episodes in the season.
	# type: the season or episode type.
	# typeEpisode: a list of types of all episodes in the season.
	# status: the current status of the show.
	# statusLast: the current status of the last episode in the season.
	def mergeStatus(self, values = None, media = None, season = None, episode = None, seasonReleased = None, time = None, timeFirst = None, timeLast = None, timeSeasonNext = None, timeSeasonLast = None, timeEpisode = None, type = None, typeEpisode = None, status = None, statusLast = None):
		try:
			# Combine values from different providers.
			if values:
				if Tools.isList(values) and Tools.isList(values[0]): values = Tools.listFlatten(values)

				result = None
				order = None
				for value in values:
					current = MetaTools.Status.get(value, {}).get('order', 0)
					if order is None or current > order:
						order = current
						result = value

				if season == 0 and MetaTools.StatusContinuing in values: result = MetaTools.StatusContinuing # Sometimes Trakt does not have newer specials that are on TVDb and S00 is then marked as ended.
				elif result == MetaTools.StatusContinuing and time and time > self.mTimeCurrent: result = MetaTools.StatusUpcoming # Future seasons not released yet.

				# Pick the most common occurring status if available.
				if not season == 0:
					common = Tools.listCommon(values, count = 1)
					if common and values.count(common) > (len(values) / 2.0): return common

				return result

			# Seasons
			elif not season is None and episode is None:
				finished = status in (MetaTools.StatusEnded, MetaTools.StatusCanceled)

				if timeFirst and timeFirst > self.mTimeCurrent: return MetaTools.StatusUpcoming # The first episode in the season has not aired yet.
				elif time and time > self.mTimeCurrent: return MetaTools.StatusUpcoming # The season premiere is in the future. Should be the same as timeFirst above.
				elif timeLast and timeLast > self.mTimeCurrent: return MetaTools.StatusContinuing # The last episode in the seasons is still unaired.

				if season == 0:
					if finished:
						# There is no clear point where S0 can be marked as "ended", since sometimes new specials are released months/years after the show ended.
						# Assume that if the show ended and the last special is older than 6 months, that S0 ended.
						if not timeFirst and not timeLast and not timeSeasonLast: return MetaTools.StatusEnded # There are no episodes in S0.
						elif (timeEpisode or not timeEpisode is None) and timeSeasonLast and timeSeasonLast < (self.mTimeCurrent - 63115200) and all(abs(self.mTimeCurrent - j) > 63115200 for j in timeEpisode):
							# Specials can be released months or years after the show has ended.
							# If the show has ended and the last episode was released more than 2 years ago, mark S00 as ended, else as continuing.
							# If there are relativley new specials, also mark it as continuing, even if the show has ended a long time ago.
							# Also do this if "timeEpisode == []" if there are not specials on a provider (eg: Money Heist S0 on TVDb has no episodes).
							return MetaTools.StatusEnded
						elif not timeEpisode and timeLast and timeLast < (self.mTimeCurrent - 15768000): return MetaTools.StatusEnded # The last episode in S0 is older than 6 months.
						else: return MetaTools.StatusContinuing
					elif status:
						if (not timeEpisode is None and not timeEpisode) or (timeEpisode and not any(timeEpisode)): return MetaTools.StatusUpcoming # If S01+ has not been released yet.
						elif seasonReleased: return MetaTools.StatusContinuing
				elif season >= 1:
					if finished or (Media.isFinale(type) and Media.isOuter(type)):
						# The shows has ended or was canceled, or the last episode in the season was marked as series finale.
						# If the last episode has not aired yet, mark the season as "continuing", since season metadata might not be refreshed by MetaCache as often if they are marked as "ended".,
						if timeLast and timeLast > self.mTimeCurrent: return MetaTools.StatusContinuing

						# TVDb sometimes (incorrectly) marks the last episode of S01 of a new show as "series finale", although probably is (or will be) a multi-season show according to Trakt/IMDb.
						# TVDb might only have airing dates for the first few episodes in the season, but not for the rest which are future episodes.
						# If the last episode does not have a date and the season is marked as a series finale, do not mark the season as a finale.

						# This does seem to work for the test cases.
						# But rather check for "timeLast is False", which specifically indicates these outlier cases and is only set from MetaTvdb.metadataSeason().
						#elif timeLast or not Media.isFinale(type): return MetaTools.StatusEnded
						elif not timeLast is False: return MetaTools.StatusEnded

					elif seasonReleased and season <= seasonReleased:
						# Any season before the last season which episodes have already aired.
						return MetaTools.StatusEnded
					elif season > 0 and timeSeasonNext and timeSeasonNext < self.mTimeCurrent: return MetaTools.StatusEnded
					elif timeEpisode and timeEpisode[-1] > 0 and max(timeEpisode) < self.mTimeCurrent and (finished or (typeEpisode and (Media.isFinale(typeEpisode[-1]) and (Media.isOuter(typeEpisode[-1]) or Media.isInner(typeEpisode[-1]))))): return MetaTools.StatusEnded
					elif (not timeEpisode is None and not timeEpisode) or (timeEpisode and min(timeEpisode) > self.mTimeCurrent): return MetaTools.StatusUpcoming
					elif timeEpisode and any(timeEpisode): return MetaTools.StatusContinuing

				if status:
					if status in (MetaTools.StatusRumored, MetaTools.StatusPlanned): return status
					elif status in (MetaTools.StatusPreproduction, MetaTools.StatusProduction, MetaTools.StatusPostproduction, MetaTools.StatusCompleted, MetaTools.StatusUpcoming): return MetaTools.StatusUpcoming
					elif status in (MetaTools.StatusReleased, MetaTools.StatusPiloted, MetaTools.StatusContinuing, MetaTools.StatusReturning):
						if not time and not timeFirst and season >= 1: return MetaTools.StatusUpcoming # Unreleased seasons sometimes do not have a permiere date yet.
						else: return MetaTools.StatusContinuing

				if not status and statusLast: return statusLast

			# Episodes, shows, and movies.
			else:
				if time:
					if time < self.mTimeCurrent: return MetaTools.StatusEnded if Media.isSerie(media) else MetaTools.StatusReleased
					else: return MetaTools.StatusUpcoming if Media.isSerie(media) else MetaTools.StatusProduction
		except: Logger.error()
		return None

	# season: season number.
	# episode: episode number.
	# seasonLastStandard: season number of the last standard season.
	# seasonLastOfficial: season number of the last official season.
	# seasonLastRelease: season number of the last fully released season.
	# episodeLastStandard: episode number of the last standard episode in the season.
	# episodeLastOfficial: episode number of the last official episode in the season.
	# episodePrevious: episode number of the previous episode in the season.
	# type: the type dictionary of the current episode from MetaPack.
	# typePrevious: the type array of the previous episode before this one.
	# typeNext: the type array of the next episode after this one.
	# typeLast: the type array of the last episode in this season.
	# typeProvider: a dictionary where the key is the provider ID and the value the type array.
	# typeProviderNext: a dictionary where the key is the provider ID and the value the type array, foe the next episode.
	# map: a dictionary or list with provider IDs that use a different episode number to the official number for the current episode.
	# mapNext: a dictionary or list with provider IDs that use a different episode number to the official number for the next episode.
	# remap: a dictionary or list with provider IDs that matched any episode in the season to a different season number. Eg: the official episode is S02E01, but TVDb has that episode as S03E04 (different season).
	# unmap: a dictionary or list with provider IDs that could not match their episode number to an official number.
	# timeEpisode: the timestamp of the episode premiere.
	# timeLast: the timestamp of the last episode in the season.
	# timePack: the timestamp when the pack was generated. Outdated pack data might have missing/incorrect details for new and future episodes.
	# statusShow: the current status of the show.
	# statusSeason: the current status of the current season.
	# specialSeason: S0 contains a full season of storyline episode specials that should have been a separate season. Instead of where normally S0 contains a loose collection of specials for various seasons.
	# specialPremiere: within a S0 that is a "specialSeason", is S00E01 most likley a full episode premiere.
	# specialEpisode: the episode is most likley a special, such as extra episodes at the end of a season on IMDb.
	# fix: fix the type if incorrectly set, such as TVDb marking an episode as series finale instead of season finale.
	def mergeType(self, values = None, season = None, episode = None, seasonLastStandard = None, seasonLastOfficial = None, seasonLastRelease = None, episodeLastStandard = None, episodeLastOfficial = None, episodePrevious = None, type = None, typePrevious = None, typeNext = None, typeLast = None, typeProvider = None, typeProviderNext = None, map = None, mapNext = None, remap = None, unmap = None, timeEpisode = None, timeLast = None, timePack = None, statusShow = None, statusSeason = None, specialSeason = None, specialPremiere = None, specialEpisode = None, fix = False):
		try:
			if values:
				values = [i for i in values if i]
				if Tools.isArray(values[0]): values = Tools.listFlatten(values)
			else:
				values = []

			finishedShow = statusShow == MetaTools.StatusEnded or statusShow == MetaTools.StatusCanceled
			finishedSeason = statusSeason == MetaTools.StatusEnded or statusSeason == MetaTools.StatusCanceled
			try: outdated = timeEpisode > timePack
			except: outdated = False

			def variantTvdb(typed):
				return typed and len(typed.keys()) == 1 and typed.get(MetaTools.ProviderTvdb) == [Media.Standard]

			variant = False
			try:
				if abs(episode - episodePrevious) > 1: variant = True
			except: pass
			try:
				if type:
					if type.get(MetaPack.NumberCustom): variant = True

					# Star Wars: Young Jedi Adventures: S01E26 + S01E39
					if type.get(MetaPack.NumberUnofficial) and not type.get(Media.Alternate) and (not typePrevious or (not Media.Middle in typePrevious and not Media.Alternate in typePrevious)): variant = True
			except: pass

			# Add the pack types, such as "unofficial", so that the episode type can be used later on without having to first retrieve the pack.
			if type:
				# Do not add these types from the pack, if the pack was generated before the episode was released.
				# Otherwise newly-released or future episodes that have missing IDs and numbers (eg: not on Trakt yet), will be marked as unofficial episodes.
				# This will then show in the menus as "Nonstandard Episode", simply because metadata is missing.
				# Only add the unofficial type if the pack was generated after the episode aired.
				# Update: Still add NumberUnofficial if TVDb has the episode in a different season to Trakt/official.
				# Eg: LEGO Masters S05E06 (TVDb) vs S06E06 (Trakt), while the episode metadata is on TVDb, but not on Trakt yet, and the episode has not aired yet.
				if outdated and not(remap and len(remap) == 1 and MetaTools.ProviderTvdb in remap): types = (MetaPack.NumberSpecial, MetaPack.NumberOfficial, MetaPack.NumberUniversal)
				else: types = (MetaPack.NumberSpecial, MetaPack.NumberOfficial, MetaPack.NumberUnofficial, MetaPack.NumberUniversal)
				values.extend([i for i in types if type.get(i)])

				# Add the types from the pack to the episode metadata.
				# Since packs have all episodes and can determine the type more accurately that the episode metadata from a single season.
				# Eg: Dragon Ball Super S01E131.
				types = (Media.Premiere, Media.Finale, Media.Outer, Media.Inner, Media.Middle, Media.Alternate, Media.Season)
				values.extend([i for i in types if type.get(i)])

			if season == 0:
				# "special" is technically  reserved for movie specials.
				# Add "exclusive" used to generate the niche ion MetaTools.niche().
				values.extend([Media.Special, Media.Exclusive])

				# Sometimes S0 can contain a full season of sequential episodes.
				# Eg: Money Heist S0
				if specialSeason:
					# So we know that S00 is a full season.
					# Eg: Money Heist S0 (do not add S00E23 from TVDb).
					if MetaPack.NumberOfficial in values: values.append(Media.Season)

					# The first episode is a full premiere, but was not labeled as one.
					# Eg: Money Heist S00E01.
					if specialPremiere and episode == 1:
						values.append(Media.Premiere)
						if not Media.Outer in values and not Media.Middle in values: values.append(Media.Inner)

					# Add midseason premieres.
					# Eg: Money Heist S0 (S00E13 -> S00E14).
					if typePrevious and Media.Finale in typePrevious and Media.Middle in typePrevious and not Media.Finale in values:
						if not variant:
							values = Tools.listRemove(data = values, value = (Media.Inner, Media.Outer, Media.Finale), all = True)
							values.append(Media.Premiere)
							values.append(Media.Middle)
							if Media.Alternate in typePrevious: values.append(Media.Alternate)

			elif season and season > 0:
				# Seasons
				if episode is None:
					# This should already be set by default.
					# But explicitly indicate the first season as outer premiere.
					if season == 1: values.extend([Media.Premiere, Media.Outer])

					# If the show ended, or the last episode in the season is a series finale, mark the last season as finale.
					# Eg (seasonLastStandard): Dragon Ball Super S05 (TVDb).
					# Eg (seasonLastOfficial): Money Heist S03 (official last season), while IMDb has S04 + S05.
					if season == seasonLastStandard or season == seasonLastOfficial:
						done = finishedShow
						if not done and typeLast and Media.Finale in typeLast and Media.Outer in typeLast: done = True
						if done: values.extend([Media.Finale, Media.Outer])

					# Eg: Dragon Ball Super S02-05.
					if MetaPack.NumberUnofficial in values:
						values.append(Media.Alternate)

				# Episodes
				else:
					# Many premieres are not marked anywhere.
					# Eg: One Piece S22E01.
					if episode == 1:
						values.append(Media.Premiere)
						values.append(Media.Outer if season == 1 else Media.Inner)

					# Sometimes the same finale is marked as season and series finale by different providers.
					# Eg: Dragon Ball Super S01E131 - season finale (Trakt), series finale (TVDb).
					if Media.Finale in values and Media.Outer in values and Media.Inner in values:
						values = Tools.listRemove(data = values, value = Media.Inner, all = True)

					# If the pack type is added tot he episode type, an episode might be marked as both inner and middle.
					# Eg: Dragon Ball Super S02E04.
					if Media.Inner in values and Media.Middle in values:
						values = Tools.listRemove(data = values, value = Media.Inner, all = True)

					# IMDb specials.
					# Eg: Downton Abbey S02E09.
					if MetaPack.NumberUnofficial in values and MetaPack.NumberSpecial in values and season:
						values.append(Media.Alternate)

					# Finales not marked as a finale on Trakt.
					# Eg: QI S21E17
					# Only do this if the season has ended.
					if not Media.Finale in values and episodeLastOfficial and episode == episodeLastOfficial and statusSeason in MetaTools.StatusesPast:
						values.append(Media.Finale)
						if not Media.Inner in values and not Media.Outer in values:
							if seasonLastOfficial and season == seasonLastOfficial and statusShow in MetaTools.StatusesPast: values.append(Media.Outer)
							else: values.append(Media.Inner)

					# IMDb specials.
					# Eg: Family Guy S23E19 + S23E20.
					# Only do this if it is likely that the episode is a special (specialEpisode).
					# Ignore this if the episode is probably not a special and just has episode number discrepancies.
					# Eg: The Tonight Show Starring Jimmy Fallon S08E198+ (IMDb), while Trakt only goes up to S08E197.
					# Also note that sometimes Trakt/TMDb/TVDb only have a few episodes listed for a new season (eg: 5 of 20), while IMDb has all episodes listed (eg: 20 of 20).
					# Do not mark these as specials.
					if specialEpisode:
						if MetaPack.NumberUnofficial in values and Media.Alternate in values and not Media.Special in values and season:
							if episodeLastOfficial and episode > episodeLastOfficial:
								values.append(Media.Special)

					# IMDb specials in S01+ for which the exclusive type was not added yet.
					# Eg: Downton Abbey S02E09.
					if MetaPack.NumberSpecial in values:
						values.append(Media.Exclusive)

					# Middle premieres/finales indicated by TVDb but not by Trakt.
					# Use Alternate to distinguish these from official middle premieres/finales.
					# Eg: One Piece S01E08, S18E02, S18E31, S21E194, S21E197
					# Eg: Dragon Ball Super S01E14
					# Eg: Vikings S06E10
					if typeProvider:
						typeTrakt = typeProvider.get(MetaTools.ProviderTrakt)
						typeTmdb = typeProvider.get(MetaTools.ProviderTmdb)
						typeTvdb = typeProvider.get(MetaTools.ProviderTvdb)

						# If the episode is marked as both premiere and finale.
						# Eg: One Piece S01E61 (Trakt - finale) vs S05E01 (TVDb - premiere).
						if Media.Premiere in values and Media.Finale in values:
							if (typeTrakt and Media.Finale in typeTrakt) and (typeTvdb and Media.Premiere in typeTvdb):
								values = Tools.listRemove(data = values, value = Media.Premiere, all = True)

						# Episodes that are mistmatched between Trakt and TVDb, where the values contain premiere/finale, but all typeProvider values are standard.
						# Eg: Star Wars: Young Jedi Adventures S02E22 (TVDb midseason finale).
						# Still allow other alternate finales.
						# Eg: One Piece S01E06 (S04E13 finale on TVDb)
						if typeProvider and (Media.Premiere in values or Media.Finale in values) and not Media.Alternate in values:
							if not any(Media.Premiere in i or Media.Finale in i for i in typeProvider.values()):
								# Ignore specials finales.
								# Eg: QI S21E17 (Trakt) is a special on TVDb and it should keep the finale type.
								if not Media.Special in values:
									values = Tools.listRemove(data = values, value = [Media.Premiere, Media.Finale, Media.Inner, Media.Outer, Media.Middle], all = True)

						# Not for One Piece S02E01 which is not marked as a premiere on Trakt.
						# Still do it for Dragon Ball Super S02E01 which is only on TVDb.
						if not typeTrakt or (Media.Standard in typeTrakt and (not episode == 1 or not typeTvdb or not Media.Standard in typeTvdb)):
							# (typeTvdb and not typeTrakt): if the episode is only on TVDb, but not on Trakt/TMDb.
							# Eg: Dragon Ball Super S02E13
							# Only add for "typeTvdb and not typeTrakt" if the episode number exceeds the last number.
							# For future episodes that are on TVDb, but not on Trakt yet.
							# Check typePrevious to not add alternate to mid-season finales that are on Trakt but not on TVDb.
							# Eg: House S01E08.
							if (
								(Media.Inner in values or Media.Outer in values or Media.Middle in values)
								and (
									(not episodeLastStandard is None and episode < episodeLastStandard and (not Media.Middle in values or not typeTrakt or not Media.Middle in typeTrakt))
									or (typeTvdb and not typeTrakt and (episodeLastStandard is None or episode >= episodeLastStandard))
								)
								and (not typePrevious or not Media.Middle in typePrevious)

								# Not if the TVDb episode maps to a different season.
								# Eg: One Piece S03E01.
								# Eg: One Piece S06E01.
								and (typeTvdb or not remap or not(not typeTvdb and remap and MetaTools.ProviderTvdb in remap))

								# Episodes marked by Trakt as standard, although they are premieres.
								# Eg: One Piece S20E01.
								and not(episode == 1 and Media.Premiere in values)
							):
								# Do not remove these, since both types should be kept.
								# Eg: Dragon Ball Super S02E01 should not only be marked as an alternate permiere, but also as inner permiere.
								# values = Tools.listRemove(data = values, value = (Media.Inner, Media.Outer), all = True)
								values.append(Media.Alternate)

							# Eg: One Piece S18E02
							elif Media.Middle in values and map and MetaTools.ProviderTvdb in map:
								values.append(Media.Alternate)

							# Eg: Lost S06E18 (on Trakt a single combined finale S06E17, on TVDb a split finale).
							# Eg: Dragon Ball Super S02E13.
							elif MetaPack.NumberUnofficial in values and (Media.Premiere in values or Media.Finale in values):
								values.append(Media.Alternate)

							# Sometimes TMDb has future/unreleased episodes, while Trakt and TVDb have not.
							# Trakt has probably not scraped TMDb for the new values.
							# Eg: Foundation S03 (Trakt has no episodes, TVDb has the first episode, TMDb has all episodes with S03E10 marked as "finale")
							elif (Media.Premiere in values or Media.Finale in values) and len(values) == 1:
								values.append(Media.Inner) # Could be "outer", but that will only be known once the metadata is updated.
								values.append(Media.Alternate)

						# Sometimes TMDb has future/unreleased episodes, while Trakt and TVDb have not.
						# Trakt has probably not scraped TMDb for the new values.
						# Eg: Foundation S03 (Trakt has no episodes, TVDb has the first episode, TMDb has all episodes with S03E10 marked as "finale")
						# Assume the alternate premiere/finale is actually the normal premiere/finale.
						if Media.Alternate in values and typeTmdb and not typeTrakt and (not typeTvdb or Media.Premiere in typeTvdb or Media.Finale in typeTvdb):
							values = Tools.listRemove(data = values, value = Media.Alternate, all = True)

						# If the season finale is not marked on Trakt/TMDb, but marked on TVDb AND TVDb contains additional episodes after the season finale.
						# Eg: Jimmy Fallon has S12E1301 - S12E1305 after the season finale S12E162, which are the absolute numbers for the new S13 episodes. TVDb will probably fix this at some point.
						if Media.Finale in values and Media.Middle in values and not typeNext and not typeProviderNext:
							if typeTrakt and not Media.Finale in typeTrakt and not Media.Alternate in typeTrakt:
								values = Tools.listRemove(data = values, value = [Media.Middle, Media.Alternate], all = True)
								if finishedShow and season == seasonLastStandard: values.append(Media.Outer)
								elif seasonLastStandard and season < seasonLastStandard: values.append(Media.Inner)

					# Eg: Star Wars: Young Jedi Adventures S01E49
					elif MetaPack.NumberUnofficial in values and (Media.Premiere in values or Media.Finale in values) and map and MetaTools.ProviderTvdb in map:
						values.append(Media.Alternate)

					# Some middle episodes are marked incorrectly as inner/outer.
					# Eg: Vikings S06E10 is marked as season finale on TVDb, although it should be an middle finale.
					if Media.Finale in values and (Media.Inner in values or Media.Outer in values) and not episode is None and not episodeLastOfficial is None and episode < episodeLastOfficial:
						# Do not assume this if there is a double finale.
						# Eg: House S06E21 and S06E22.
						# Do not do this if the next episode is only available on IMDb, which is probably a special.
						# Eg: Downton Abbey S02E09.
						if (not typeNext or not Media.Finale in typeNext) and (not mapNext or any(i in mapNext for i in (MetaTools.ProviderTrakt, MetaTools.ProviderTvdb, MetaTools.ProviderTmdb))):
							# Do not do this if the next episode is a special.
							# Eg: Downton Abbey S03E08 -> S03E09.
							if not typeNext or not Media.Special in typeNext:
								# Do not do this if there is a discrepancy between TVDb and Trakt.
								# Eg: One Piece S18E31 (on TVDb it is S18E33, a season finale).
								# Eg: One Piece S18E194 (on TVDb it is S18E194, a season finale).
								if (not mapNext and not Media.Inner in values) or (not mapNext and typeNext and not Media.Inner in typeNext and not Media.Outer in typeNext) or (mapNext and not(mapNext and len(mapNext) == 1 and mapNext[0] == MetaTools.ProviderTvdb)):
									# Do not do this if the next episode is a TVDb variant/special episode.
									# Eg: Dragon Ball Super S05E55/S05E56.
									if not variantTvdb(typeProviderNext):
										# If the TVDb finale is just 1-2 episodes before the Trakt finale, do not mark it as midseason finale, but as an alternate finale.
										# Eg: QI S22E14 (finale on TVDb) vs S22E16 (finale on Trakt).
										lastDifference = (episodeLastOfficial - episode) if episodeLastOfficial else -1
										if lastDifference and lastDifference > 0 and lastDifference < 3:
											values.append(Media.Alternate)
										else:
											values = Tools.listRemove(data = values, value = (Media.Inner, Media.Outer), all = True)
											values.append(Media.Middle)

					# If providers mark middle episodes, it is only the middle finale, not the middle premiere.
					# Mark as middle premiere if the previous episode was a middle finale.
					# Do not do this if the episode is marked as a finale, since there can sometimes be two finales at the end of a season.
					# Eg: House S06E21 and S06E22.
					if typePrevious and Media.Finale in typePrevious and Media.Middle in typePrevious and not Media.Finale in values:
						# Do not do this if the gap between the episodes is greater than 1.
						# Eg: Star Wars: Young Jedi Adventures: S01E38 + S01E40
						if not variant:
							values = Tools.listRemove(data = values, value = (Media.Inner, Media.Outer, Media.Finale), all = True)
							values.append(Media.Premiere)
							values.append(Media.Middle)
							if Media.Alternate in typePrevious: values.append(Media.Alternate) # Vikings S06E11, since S06E10 is not marked as a middle finale on Trakt.

					# Sometimes the season finale is marked incorrectly as middle finale.
					# Eg: One Piece S21E194 is marked as middle finale on Trakt.
					if Media.Finale in values and Media.Middle in values and episode == episodeLastOfficial:
						values = Tools.listRemove(data = values, value = Media.Middle, all = True)
						if finishedShow and season == seasonLastStandard: values.append(Media.Outer)
						elif seasonLastStandard and season < seasonLastStandard: values.append(Media.Inner)

					# Incorrectly marked inner/outer premieres/finales that should be middle.
					# This will probably not be triggered, since the code above would set these already.
					if not episode is None and not Media.Alternate in values and not Media.Middle in values and (Media.Outer in values or Media.Inner in values):
						# Allow double finales.
						# Eg: House S06E21 and S06E22.
						if (Media.Premiere in values and episode > 1) or (Media.Finale in values and not episodeLastOfficial is None and episode < (episodeLastOfficial - 2)):
							values = Tools.listRemove(data = values, value = (Media.Inner, Media.Outer), all = True)
							values.append(Media.Middle)

					# For episodes only available on IMDb.
					# Eg: Downton Abbey S02E09.
					if not Media.Premiere in values and not Media.Finale in values:
						if map and MetaTools.ProviderImdb in map and not any(i in map for i in (MetaTools.ProviderTrakt, MetaTools.ProviderTvdb, MetaTools.ProviderTmdb)):
							# Exclude standard episodes.
							# Eg: The Tonight Show Starring Jimmy Fallon S04E21.
							if not typeProvider or not any(i in typeProvider for i in (MetaTools.ProviderTrakt, MetaTools.ProviderTvdb, MetaTools.ProviderTmdb)):
								values.extend([Media.Special, Media.Exclusive, Media.Alternate])

					# If the previous episode is an alternative finale (from TVDb), mark the next one as an alternative premiere.
					# Eg: One Piece S18E31/32, S21E194/195
					if typePrevious and Media.Finale in typePrevious:
						if not Media.Premiere in values and not Media.Finale in values and not Media.Special in values:
							# Do not do this for unofficial episodes.
							# Eg: Star Wars: Young Jedi Adventures: S01E28+
							if not variant:
								# IMDb specials.
								# Eg: Lost S01E25 (only on IMDb).
								if typeNext is None and typeProvider is None and typeProviderNext is None and map is None and remap is None and unmap is None:
									# Not for IMDb episodes that are not specials or finales.
									# Eg: The Tonight Show Starring Jimmy Fallon S08E198+.
									if not type or not MetaPack.NumberStandard in type:
										values.append(Media.Finale)
										for i in (Media.Outer, Media.Inner, Media.Middle, Media.Alternate):
											if i in typePrevious: values.append(i)
										values.append(Media.Alternate)
										values.append(MetaPack.NumberUnofficial)
								else:
									# Only mark the next episode after a finale as a premiere, if it is not close to the end of the season.
									# If TVDb has an alternate finale 1-2 episodes before the Trakt finale, do not mark it as a premiere.
									# Eg: QI S22E15.
									lastDifference = (episodeLastOfficial - episode) if episodeLastOfficial else -1
									if lastDifference and lastDifference > 0 and lastDifference > 3:
										values.append(Media.Premiere)
										for i in (Media.Outer, Media.Inner, Media.Middle, Media.Alternate):
											if i in typePrevious: values.append(i)

					# Shows that get canceled often have the last episode as season finale, instead of series finale.
					# If the show was canceled or ended, mark the last season as finale.
					# Also do this for the last official episode.
					# Eg: Dragon Ball Super S01E131.
					# Do not do this if the next episode is a TVDb variant/special episode.
					# Eg: Dragon Ball Super S05E55/S05E56.
					if ((seasonLastStandard and season == seasonLastStandard) or (seasonLastOfficial and season == seasonLastOfficial)) and episode == episodeLastOfficial and not variantTvdb(typeProvider):
						done = finishedShow
						if not done and typeLast and Media.Finale in typeLast and Media.Outer in typeLast: done = True
						if done: values.extend([Media.Finale, Media.Outer])

					# For specials on TVDb that are added after the finale and are not on other providers.
					# Eg: Dragon Ball Super S01E15, S02E14, S05E56.
					# Update: TVDb seems to have removed these specials now.
					if season > 0 and not episode is None and episode == episodeLastStandard and variantTvdb(typeProvider):
						# Do not do this if there are extra TVDb episodes, simply because TVDb has a different season numbering.
						# Eg: LEGO Masters S05E06+ (TVDb) should not be marked as a special (S06E06 on Trakt).
						if not remap or not(remap and len(remap) == 1 and MetaTools.ProviderTvdb in remap):
							# Do not mark them as special if their release date is in the future.
							# Since episodes might already be on TVDb, but not on Trakt/TMDb yet, causing "remap" to be None.
							# Eg: LEGO Masters S05E09 (TVDb) at 2025-07-05.
							if not timeEpisode or timeEpisode < self.mTimeCurrent:
								# Do not do if the episode is a TVDb outlier.
								# Eg: Star Wars: Young Jedi Adventures S02E43 (TVDb).
								# Eg: LEGO Masters S04E15.
								if not((typePrevious and MetaPack.NumberUnofficial in typePrevious) and (not typeNext or not MetaPack.NumberUnofficial in typeNext)):
									values = Tools.listRemove(data = values, value = Media.Standard, all = True)
									values.extend([Media.Special, Media.Exclusive, Media.Alternate])

			# Fill in missing types.
			if not season is None or not episode is None:
				if not Media.Special in values and (season == 0 or episode == 0):
					values.extend([Media.Special, Media.Exclusive])
				elif not Media.Premiere in values and not Media.Finale in values and not Media.Special in values:
					if season == 1 and episode == 1:
						values.extend([Media.Premiere, Media.Outer])
					elif season > 1 and episode == 1:
						values.extend([Media.Premiere, Media.Inner])
					elif (finishedShow or finishedSeason) and season == seasonLastStandard and not episode is None and episode == episodeLastOfficial:
						# Do not assume the finale if there are still future/unaired episodes.
						values.extend([Media.Finale, Media.Outer])
					elif (finishedShow or finishedSeason) and season > 0 and not episode is None and episode == episodeLastOfficial:
						# Do not assume the finale if there are still future/unaired episodes.
						values.extend([Media.Finale, Media.Inner])
					else:
						values.append(Media.Standard)

			# Eg: Vikings S06E11.
			if Media.Premiere in values or Media.Finale in values or Media.Special in values or Media.Exclusive in values:
				# all = True: "standard" can be in the values mutiple times if coming from MetaManager. Remove all.
				values = Tools.listRemove(data = values, value = Media.Standard, all = True)

			# Mark standard seasons as standard-inner.
			if not season is None and episode is None and Media.Standard in values: values.append(Media.Inner)

			if fix and not season is None:
				if episode is None: # Seasons
					# Sometimes an episode is marked as a series finale on TVDb, instead of a season finale.
					# Eg: South Park S26E06 is a "series finale" on TVDb, although there is a new/upcoming S27.
					# If no season type is available, services/tvdb.py will mark the season as series finale if the last episode in the season is also marked as series finale.
					# Hence, remove the finale if the show has not ended.
					if Media.Finale in values and Media.Outer in values:
						# Do not use the show status to determine if the show has ended.
						# Shows that have technically finished, but the last few episodes have not been aired yet, will have the show status as "Continuing".
						# Hence, the show status will only work if all episodes were already aired.
						# Instead determine if there is a new season after this one.
						#if statusShow in (MetaTools.StatusEnded, MetaTools.StatusCanceled):

						unfinished = False

						if seasonLastStandard and season < seasonLastStandard: unfinished = True # A later season is available.
						elif not statusShow in (MetaTools.StatusEnded, MetaTools.StatusCanceled) and not((timeLast and timeLast < self.mTimeCurrent) or season == seasonLastStandard): unfinished = True # The last episode has not aired yet.

						if unfinished: values = Tools.listRemove(data = values, value = (Media.Finale, Media.Outer), all = True)

					# Shows that get canceled often have the last episode as season finale, instead of series finale.
					# If the show was canceled or ended, mark the last season as finale.
					if season >= 1 and season == seasonLastRelease and statusShow in (MetaTools.StatusEnded, MetaTools.StatusCanceled):
						values = Tools.listRemove(data = values, value = (Media.Standard, Media.Outer), all = True)
						values.extend([Media.Finale, Media.Outer])

				else: # Episodes
					# Sometimes middle finales are listed as season finales.
					# Eg: Vikings S06E10
					# Do not do this for specials.
					# Eg: Downton Abbey S00E02 (season finale, do not make it a midseason finale).
					if season:
						if episode > 1 and (Media.Premiere in values and (Media.Outer in values or Media.Inner in values)):
							values = Tools.listRemove(data = values, value = (Media.Outer, Media.Inner), all = True)
							values.append(Media.Middle)
						elif episodeLastStandard and episode < episodeLastStandard and (Media.Finale in values and (Media.Outer in values or Media.Inner in values)):
							# Do not do this for specials placed after the finale on TVDb.
							# Eg: Dragon Ball Super S01E15, S02E14, S05E56.
							if episode < (episodeLastStandard - 2):
								values = Tools.listRemove(data = values, value = (Media.Outer, Media.Inner), all = True)
								values.append(Media.Middle)

			values = Tools.listUnique(values)
			if values:
				# Sort to make it more human readable.
				order = {Media.Standard : 0, Media.Premiere : 1, Media.Finale : 2, Media.Outer : 3, Media.Inner : 4, Media.Middle : 5, Media.Special : 6, Media.Exclusive : 7, Media.Alternate : 8, MetaPack.NumberOfficial : 9, MetaPack.NumberUnofficial : 10, MetaPack.NumberUniversal : 11, Media.Season : 12}
				values = Tools.listSort(data = values, key = lambda i : order.get(i, 99))

				return values

		except: Logger.error()
		return None

	def mergeTime(self, values, providers = None, metadata = None):
		try:
			# If a show is only available on IMDb, there will be no time values from other providers, only a premiered date from IMDb (eg: tt31566242, tt30346074).
			if (not values or not any(i.get(MetaTools.TimePremiere) for i in values)) and metadata:
				value = metadata.get('aired') or metadata.get('premiered')
				if value:
					value = Time.timestamp(fixedTime = value, format = Time.FormatDate, utc = True)
					if value:
						if values is None: values = []
						values.append({MetaTools.TimePremiere : value})
		except: Logger.error()

		if values:
			# Prefer Trakt times if available, since Trakt has the date+time, whereas TMDb/TVDb only have the date.
			# Only important for shows. Less so for movies, since Trakt movies also mostly have the date without the time.
			preference = {}
			if providers:
				value = providers.get(MetaTools.ProviderTrakt)
				if value:
					for k, v in value.items():
						if Tools.isDictionary(v):
							if not k in preference: preference[k] = {}
							for k2, v2 in v.items():
								preference[k][k2] = v2
						else:
							preference[k] = v

			result = {}
			for value in values:
				for k, v in value.items():
					if Tools.isDictionary(v):
						if not k in result: result[k] = {}
						for k2, v2 in v.items():
							try:
								prefer = preference[k][k2]
								if prefer: v2 = prefer
							except: pass
							if result.get(k, {}).get(k2) is None: result[k][k2] = v2
							elif v2: result[k][k2] = min(result[k][k2], v2)
					else:
						try:
							prefer = preference[k]
							if prefer: v = prefer
						except: pass
						if result.get(k) is None: result[k] = v
						elif v: result[k] = min(result[k], v)

			# Remove estimates if we have the exact time. Saves some disk space.
			estimate = result.get('estimate')
			if estimate:
				estimate = {k : v for k, v in estimate.items() if not result.get(k)}
				if estimate: result['estimate'] = estimate
				else: del result['estimate']

			return result
		return None

	def mergeDuration(self, values, short = False):
		try:
			if values:
				# Prefer Trakt for consistency.
				result = values[-1]

				# Trakt sometimes has the wrong duration.
				# Eg: The Librarians 2014 runtime listed as 1min.
				if not result or (result <= 60 and not short):
					temp = max(values)
					if abs(temp - result) > 600: result = temp

				# Trakt sometimes has the wrong duration for short shows.
				# Eg: Star Wars: Tales of the Underworld (Trakt has 42min, while TVDb and the average time is 15min).
				elif short:
					temp = min(values)
					if temp > 60: result = temp

				if result: return result
		except: Logger.error()
		return None

	def mergeCast(self, values, season = None, show = None, reverse = True):
		# Some episodes only have a few cast members listed.
		# Either no one has added the cast to the APIs, or it only lists the guest stars for that episode.
		# In such a case, add the season/show cast as well.
		# At the same time, we might not always want to use the show cast, especially for anthology series where each seasons/episode has different actors.
		# Having a proper cast list is important for the Kodi Kore app when playing an episode.
		#	Trakt: has main cast members and guest stars (with extended info) under each episode. No thumbnails and the cast is only retrieved with DetailsExtended.
		#	TMDb: only has guest stars under each episode. Has thumbnails, although some thumbnails might be missing.
		#	TVDb: only has guest stars under each episode. Has thumbnails, although some thumbnails and roles might be missing.
		#		It seems TVDb lists all the stars of the show as cast members of the show.
		#		Occasional guest stars on the other hand are listed as cast members of the individual episodes.
		#		Guest stars also seem to be less likley to have a thumbnail and/or character name. List them last.
		result = {}

		def _id(item):
			id = item.get('name')
			if id: id = 'name_' + id
			else: id = 'role_' + str(item.get('role'))
			return id

		def _add(item, condition = True, rank = 0, copy = False):
			id = _id(item)
			found = result.get(id)
			if found:
				if copy: item = Tools.copy(item)
				for i in ['name', 'role', 'job', 'thumbnail']:
					if not found.get(i): found[i] = item.get(i)
				found['order'].append(item.get('order') or 0)
			elif condition:
				if copy: item = Tools.copy(item)
				order = item.get('order')
				if order is None: item['order'] = []
				else: item['order'] = [order]
				item['rank'] = rank
				result[id] = item

		if values:
			if reverse: values = values[::-1] # MetaManager adds the most important providers to the end of the list.
			for i in values:
				for j in i: _add(j)
		initial = len(list(result.values()))

		# Most episode casts do not have a thumbnail, but season/show cast does.
		# Do not add season/show cast if the episode cast is large enough. Otherwise we add too many guest and other irrelevant actors.
		# Eg: Law & Order S01.
		# Still add all of them here, since we want to aggregate the thumbnails. They are later filtered out.
		# NB NB: Make sure to COPY the items in _add().
		# Otherwise if we just retrieved new episodes and merge it with the season/show cast, there can be discrepancies in the "order" attribute (very large integers used below), since we edit the item order/rank in _add().
		# This causes an exception with "order" in tag.setCast(): OverflowError: signed integer is greater than maximum
		# This only happens for certain shows. And only if we open an episode menus and the episodes are retrieved for the first time. If we go back and open the menu again with cached episode metadata, the exception does not happen.
		if season:
			# Do not make this too high, otherwise season guest stars that appear in other episodes are added here (That 70's Show S05E01 - Tommy Chong).
			few = len(result.keys()) <= (7 if len(season) <= 15 else 10)
			for i in season: _add(i, condition = few, rank = 1, copy = True)
		if show:
			few = len(result.keys()) <= (5 if len(show) <= 15 else 7)
			for i in show: _add(i, condition = few, rank = 2, copy = True)

		# Calculate the summed order and then sort.
		result = list(result.values())
		for i in result:
			order = 9999999999
			try: order -= sum(i.get('order'))
			except: Logger.error(str(i.get('order'))) # Once happened that there was a list inside the list to be summed.

			rank = i.get('rank')
			if not rank: order += 30000000
			elif rank == 1: order += 20000000
			elif rank == 2: order += 10000000

			job = i.get('job')
			if job:
				if 'star' in job: order += 5000000
				elif 'guest' in job: order += 3000000
				elif 'actor' in job: order += 4000000
				else: order += 2000000
			else:
				order += 1000000
				i['job'] = ['actor'] # Might be empty if they come from TMDb/TVDb and are listed on Trakt.

			if i.get('role'): order += 20
			if i.get('thumbnail'): order += 10

			i['order'] = order
		result = Tools.listSort(data = result, key = lambda i : i['order'], reverse = True)

		# Do not add season/show cast if the episode cast is large enough. Otherwise we add too many guest and other irrelevant actors.
		# Eg: Law & Order S01 (show has 7000 total actors, 470 season actors, and 20-40 episode actors).
		# Either get rid of the season/show cast if there are already enough episode cast, or if there are few episode cast, and enough season/show cast was already added.
		# NB: Keep these values low, for shows with few actors. Otherwise too many guest/new actors from later seasons are added.
		# Eg: Two and a half Men S01.
		if season or show:
			temp = []
			exclude = initial >= 7
			for i in result:
				allow = True
				rank = i['rank']
				if exclude:
					allow = rank <= 0
				else:
					count = len(temp)
					if count > 10:
						if count > 30: allow = rank <= (0 if season else 1)
						elif count > 20: allow = rank <= (1 if season else 2)
						elif count > 10: allow = rank <= 2
				if allow: temp.append(i)
			result = temp

		# Move people without a thumbnail to the end.
		temp1 = []
		temp2 = []
		temp3 = []
		temp4 = []
		for i in result:
			job = i.get('job')
			thumbnail = i.get('thumbnail')
			if job and 'guest' in job:
				if thumbnail: temp3.append(i)
				else: temp4.append(i)
			else:
				if thumbnail: temp1.append(i)
				else: temp2.append(i)
		result = temp1 + temp2 + temp3 + temp4

		# Limit the number of cast.
		# Eg: Law & Order has almost 7000 total cast for its show (over all season/episodes).
		# No need to add them all here. So many cannot be used anywhere. And it increases the database size drastically.
		result = result[:500]

		# Create a new order.
		# NB: Do not make the order value to big of a number, otherwise when setting the cast in Kodi, it overflows a signed integer in tag.setCast().
		for i in range(len(result)):
			result[i]['order'] = i
			try: del result[i]['rank'] # Otherwise itemCast() fails it there is an unknown attribute in the dict.
			except: pass

			job = result[i].get('job')
			if job: result[i]['job'] = Tools.listUnique(job)

		return result

	def mergeCrew(self, values, reverse = True):
		if values:
			values = [[j.get('name') if Tools.isDictionary(j) else j for j in i if j] for i in values if i]
			return self.merge(values = values, reverse = reverse, frequency = 2)
		return None

	def mergeCount(self, values):
		if values:
			def _mergeCount(result, values):
				for k, v in values.items():
					if Tools.isDictionary(v):
						if not k in result: result[k] = {}
						_mergeCount(result = result[k], values = v)
					else:
						if k in result: result[k] = max(result[k] or 0, v or 0)
						else: result[k] = v

			result = {}
			for value in values.values():
				_mergeCount(result = result, values = value)
			if result: return result
		return None

	###################################################################
	# VOTING
	###################################################################

	def voting(self, metadata):
		if not metadata: return None
		voting = self.votingExtract(metadata = metadata)
		if not voting: return None

		settingMain = None
		settingFallback = None
		settingUser = None
		if Media.isSerie(self.media(metadata = metadata)):
			settingMain = self.mRatingShowMain
			settingFallback = self.mRatingShowFallback
			settingUser = self.mRatingShowUser
		else:
			settingMain = self.mRatingMovieMain
			settingFallback = self.mRatingMovieFallback
			settingUser = self.mRatingMovieUser

		result = self.votingCalculate(setting = settingMain, voting = voting)
		if not result:
			result = self.votingCalculate(setting = settingFallback, voting = voting)
			if not result:
				result = self.votingCalculate(setting = MetaTools.RatingDefault, voting = voting)

		if not settingUser is False:
			rating = self.votingUser(voting = voting, metadata = metadata)
			if rating:
				if not result: result = {}
				result['userrating'] = rating
				if settingUser: result['rating'] = rating

		return result

	def votingUser(self, voting, metadata = None):
		if 'user' in voting:
			voting = voting['user']
			for provider in MetaTools.RatingProviders:
				if provider in voting:
					rating = voting[provider]
					if rating: return rating
		if metadata: return metadata.get('userrating')
		return None

	def votingCalculate(self, setting, voting):
		if setting in MetaTools.RatingProviders: return self.votingProvider(voting = voting, provider = setting)
		elif setting == MetaTools.RatingAverage: return self.votingAverage(voting = voting)
		elif setting == MetaTools.RatingAverageWeighted: return self.votingAverageWeighted(voting = voting)
		elif setting == MetaTools.RatingAverageLimited: return self.votingAverageLimited(voting = voting)
		else: return None

	def votingExtract(self, metadata):
		rating = {}
		votes = {}

		voting = metadata.get('voting')
		if voting:
			votingRating = voting.get('rating')
			if votingRating:
				votingVotes = voting.get('votes', {})
				for provider in MetaTools.RatingProviders:
					rated = votingRating.get(provider)
					if rated:
						rating[provider] = rated
						votes[provider] = votingVotes.get(provider) or MetaTools.RatingVotes

		if not rating:
			temp = metadata.get('temp')
			if temp:
				for provider in MetaTools.RatingProviders:
					tempProvider = temp.get(provider)
					if tempProvider:
						rated = tempProvider.get('voting', {}).get('rating')
						if rated:
							rating[provider] = rated
							votes[provider] = tempProvider.get('voting', {}).get('votes') or MetaTools.RatingVotes

		# If only the aggregated rating is available.
		# Eg: Arrivals smart menu.
		if not rating:
			value = metadata.get('rating')
			if not value is None: rating[None] = value
			value = metadata.get('votes')
			if not value is None: votes[None] = value

		return {'rating' : rating, 'votes' : votes}

	def votingCollect(self, voting = None, metadata = None):
		result = {'rating' : [], 'votes' : []}

		if voting is None and Tools.isArray(metadata): # Averaging the episode ratings to get a season rating.
			for item in metadata:
				rating = item.get('rating')
				if rating:
					votes = item.get('votes')
					if votes:
						result['rating'].append(rating)
						result['votes'].append(votes)
		else:
			if voting is None: voting = self.votingExtract(metadata = metadata)

			for provider in MetaTools.RatingProviders + [None]: # None: for the already aggregated rating from votingExtract().
				if provider in voting['rating']:
					rating = voting['rating'][provider]
					if rating:
						votes = 0
						if provider in voting['votes']: votes = voting['votes'][provider]
						if Tools.isArray(rating): result['rating'].extend(rating)
						else: result['rating'].append(rating)
						if Tools.isArray(votes): result['votes'].extend(votes)
						else: result['votes'].append(votes if votes else MetaTools.RatingVotes)

		return result

	def votingProvider(self, voting, provider):
		if provider in voting['rating'] and voting['rating'][provider]: return {'rating' : voting['rating'][provider], 'votes' : voting['votes'][provider]}
		else: return None

	def votingAverage(self, voting = None, metadata = None, round = None):
		result = self.votingCollect(voting = voting, metadata = metadata)
		if not result['rating']: return None
		rating = sum(result['rating']) / len(result['rating'])
		if not round is None: rating = Math.round(rating, places = 1 if round is True else round)
		result['rating'] = rating
		result['votes'] = sum(result['votes'])
		return result

	# maximum=False: return the total vote count from all items.
	# maximum=True: return the maximum vote count from all items.
	def votingAverageWeighted(self, voting = None, metadata = None, maximum = False, round = None):
		result = self.votingCollect(voting = voting, metadata = metadata)
		if not result['rating']: return None

		votes = sum(result['votes'])
		rating = 0
		for i in range(len(result['rating'])):
			rating += result['rating'][i] * result['votes'][i]
		if votes: rating /= float(votes)
		if not round is None: rating = Math.round(rating, places = 1 if round is True else round)

		result['rating'] = rating
		result['votes'] = max(result['votes']) if maximum else votes
		return result

	def votingAverageLimited(self, voting = None, metadata = None, round = None):
		result = self.votingCollect(voting = voting, metadata = metadata)
		if not result['rating']: return None

		# If the highest votes are more than 1000, limit it to twice the 2nd highest.
		# Example:
		#	Before: IMDb=100200 | TMDb=5000 | Trakt=100
		#	After: IMDb=10000 | TMDb=5000 | Trakt=100
		votesHighest = max(result['votes'])
		try: votesLimit = sorted(result['votes'])[-2]
		except: votesLimit = votesHighest
		votesLimit = (votesLimit * 2) if (votesHighest > 1000 and votesLimit > 500) else votesHighest

		votes = 0
		rating = 0
		for i in range(len(result['rating'])):
			vote = min(result['votes'][i], votesLimit)
			rating += result['rating'][i] * vote
			votes += vote
		rating /= float(votes)
		if not round is None: rating = Math.round(rating, places = 1 if round is True else round)

		result['rating'] = rating
		result['votes'] = sum(result['votes'])
		return result

	def votingBayesian(self, voting = None, metadata = None, rating = None, votes = None, round = None):
		# https://en.wikipedia.org/wiki/Bayes_estimator#Practical_example_of_Bayes_estimators
		if not rating: rating = 7.0
		if not votes: votes = 2000 # Minimum number of votes considered to be an acceptable number, deemed necessary for average rating to approach statistical validity.
		if voting is None:
			voting = self.voting(metadata = metadata)
			if not voting: return 0.0
		rating = ((voting['rating'] * voting['votes']) + (rating * votes)) / float(voting['votes'] + votes)
		if not round is None: rating = Math.round(rating, places = 1 if round is True else round)
		return rating

	###################################################################
	# TIME
	###################################################################

	def time(self, type, metadata, default = None, estimate = True, fallback = True, alternative = None, custom = None):
		try:
			times = metadata.get('time')

			media = metadata.get('media')
			serie = Media.isSerie(media)
			movie = not serie

			# Firstly, try to pick the exact time as requested.
			if times:
				# For New season/episode release menus from S02+. The show object contains a more accurate season or episode date stored in TimeCustom, compared to TimePremiere which is the show's premiere and might be years ago.
				# Important, otherwise new seasons S02+ from Arrivals will be sorted to the back, since the premiere date is the show's premiere (S01E01), instead of the premiere of a later season that was just released (SxxE01).
				# Only do this for shows and not movies by default (custom=None) BEFORE trying to retrieve the actual requested "type" time below, since the show's custom date is preferred over the premiere/launch date.
				if custom is True or (serie and (custom is None and (type == MetaTools.TimeHome or type == MetaTools.TimeLaunch or type == MetaTools.TimePremiere))):
					value = times.get(MetaTools.TimeCustom)
					if not value and serie: value = times.get(MetaTools.TimeSerie) # Deprecated - TimeSerie can be removed after 2025-09.
					if not value is None: return value

				value = times.get(type)
				if not value is None: return value

				# Sometimes the "type" passed in is not actually a concrete time, but rather one that has multiple time types.
				# This for instance is the case when calls are made from _sortXYZ().
				# Lookup the concrete times first before doing an estimation.
				# Otherwise if TimeHome is requested, this concrete time is not in the dict, and if "estimate=True", it will now estimate the home date, instead of retrieving the available TimeDigital/TimePhysical.
				# These concrete times might sometimes be in the detailed metadata, since they are calculated and added to the "time" dict (eg: TimeLaunch).
				# But other metadata, such as smart-loaded data, might not have these times and only have the base/normal times (eg: TimeDigital).
				lookup = None
				if type == MetaTools.TimeHome: lookup = MetaTools.TimesHome
				elif type == MetaTools.TimeLaunch: lookup = MetaTools.TimesLaunch
				elif type == MetaTools.TimeDebut: lookup = MetaTools.TimesDebut
				elif type == MetaTools.TimeRelease: lookup = MetaTools.TimesRelease
				elif type == MetaTools.TimeTheater: lookup = MetaTools.TimesTheater
				elif type == MetaTools.TimeCinema: lookup = MetaTools.TimesCinema
				if lookup:
					for i in lookup:
						value = times.get(i)
						if not value is None: return value

				# By default (custom=None) only do this for movies AFTER trying to retrieve the actual requested "type" time above.
				# For movies the custom time is inaccurate. It can be the digital/physical/television or even some other inaccurate date from external sources (eg scene releases).
				# Only use this custom date if the accurate/exact date is not available.
				# This allows us to sort the movie Arrivals more precisely when new digital/physical releases come out, using the dates from MetaManager.release(), even if the exact digital/physical dates are not available from Trakt/TMDb yet or were not smart-loaded yet.
				if custom is None and movie and (type == MetaTools.TimeHome or type == MetaTools.TimeLaunch):
					value = times.get(MetaTools.TimeCustom)
					if not value is None: return value

			# Secondly, estimate the date from other dates.
			if estimate:
				estimate = (times or {}).get('estimate') # Precalculated estimates
				if estimate:
					value = estimate.get(type)
					if not value is None: return value
				elif Media.isMovie(media): # Only do this for movies. Dates for shows are typically the same (eg: no difference between premiere and home release).
					value = self.timeEstimate(type = type, metadata = metadata, default = default)
					if not value is None: return value

			if fallback:
				# Thirdly, try to pick any one of the other times according to a specifc preference order.
				if times:
					# Only use the other alternative fallback methods below if "fallback=True" and not if a specific fallback type was requested.
					# Eg: if "fallback=MetaTools.TimeCustom", do not use the premiere or year attributes if no custom time is available.
					if fallback is True:
						fallback = [MetaTools.TimeLaunch, MetaTools.TimeTheatrical, MetaTools.TimeLimited, MetaTools.TimeDigital, MetaTools.TimePhysical, MetaTools.TimeTelevision, MetaTools.TimePremiere, MetaTools.TimeUnknown]
					elif Tools.isString(fallback):
						fallback = [fallback]
						if alternative is None: alternative = False # Do not use generic fallback options below.
					elif Tools.isArray(fallback):
						if alternative is None: alternative = False # Do not use generic fallback options below.

					for i in fallback:
						value = times.get(i)
						if not value is None: return value

				if alternative or alternative is None:
					# Fourthly, try to pick the fixed set Kodi attribute.
					value = metadata.get('aired') or metadata.get('premiered')
					if not value is None:
						value = Time.timestamp(fixedTime = value, format = Time.FormatDate, utc = True)
						if not value is None: return value

					# Fithly, try to pick any of the available times.
					if times:
						value = next(i for i in times.values() if not i is None)
						if not value is None: return value

					# Sixthly, try to estimate the date from the year.
					value = metadata.get('year') or metadata.get('tvshowyear')
					if value:
						value = Time.timestamp(fixedTime = '%d-01-01' % value, format = Time.FormatDate, utc = True)
						if not value is None: return value
		except: Logger.error()
		return None

	# release: list of dictionaries: {'type' : <release type>, 'time' : <timestamp>}
	# metadata: metadata item if available.
	# local: if the user's local metadata country setting should be used.
	# origin: if the title's country of origin should be used.
	# estimate: fill in the missing dates by estimating them from other available dates.
	def timeGenerate(self, release, metadata = None, local = True, origin = True, estimate = True):
		try:
			# On most APIs, the normal release date stored in the "premiered" Kodi attribute is often not TimePremiere, but rather TimeLimited or TimeTheatrical, or even TimeDigital.
			# APIs also seem to use TimeLimited over TimeTheatrical for the normal "premiered" date if available, at least on Trakt.
			# Some movies also do not have a TimeLimited/TimeTheatrical, but just TimeDigital, and some do not even have a TimePremiere.
			# For these movies, the TimeDigital/TimePhysical becomes the normal "premiered" date.
			# Therefore always use all the time types, and only use TimePremiere if no other time is available.
			# Eg: https://trakt.tv/movies/bank-of-dave-2023/releases			https://www.themoviedb.org/movie/937220-bank-of-dave/releases
			# Eg: https://trakt.tv/movies/brightwood-2022/releases				https://www.themoviedb.org/movie/1012706-brightwood/releases
			# Eg: https://trakt.tv/movies/fremont-2023/releases					https://www.themoviedb.org/movie/1048522-fremont/releases
			# Eg: https://trakt.tv/movies/the-girls-are-alright-2023/releases	https://www.themoviedb.org/movie/1002711-las-chicas-estan-bien/releases
			# Sometimes the digital release can be months before the theatrical release.
			# Eg: "Bank of Dave" first had a Netflix release. 6-12 months later the first theatrical releases came out,

			if release and not Tools.isArray(release): release = [release]

			if local is True or local is None: local = self.mSettingsCountry
			if local and not Tools.isArray(local): local = [local]

			if origin is True or origin is None: origin = metadata.get('country') if metadata else None
			if origin and not Tools.isArray(origin): origin = [origin]

			groups = ['origin', 'primary', 'secondary', 'local', 'global', 'fallback']
			primary = ['us', 'gb', 'uk', 'ca', 'au', 'de', 'fr', 'jp']
			secondary = ['ru', 'es', 'pt', 'it', 'pl', 'ua' 'nl', 'no', 'se', 'fi', 'mx', 'br', 'nz', 'cn', 'in']

			extra = {
				MetaTools.TimeDebut		: None,
				MetaTools.TimeLaunch	: MetaTools.TimesLaunch,
				MetaTools.TimeTheater	: MetaTools.TimesTheater,
				MetaTools.TimeCinema	: MetaTools.TimesCinema,
				MetaTools.TimeHome		: MetaTools.TimesHome,
			}

			# Order groups according to preference.
			types = {
				# The premiere date is not really used anywhere.
				# The country of origin seems to be the better option for the premiere date.
				# Sometimes there is a premiere in a foreign country a few days earlier than the origin premiere, typically some film festival.
				MetaTools.TimePremiere		: ['origin', 'global', 'fallback'],

				# The limited/theatrical date are displayed in Kodi menus.
				# The country of origin probably has one of the earliest theatrical dates.
				# However, there are sometimes smaller countries (eg: island nations) who have an earlier release to the oriogin and other countries.
				# Prefer the user settings, since this will only be used if the user has explicitly set the setting and did not leave it on "Automatic".
				MetaTools.TimeLimited		: ['local', 'origin', 'global', 'fallback'],
				MetaTools.TimeTheatrical	: ['local', 'origin', 'global', 'fallback'],

				# The digital/physical dates are used for Home Releases menus.
				# Sometimes smaller countries (eg: island nations) have a digital release days/weeks/months before other countries, but there are typically not 4K rips available from these countries.
				# Prefer the larger/primary countries, since there is a way higher chance that 4K rips will be available from these countries.
				# We do not care too much about the origin/local countries, since digital/BluRay releases typically have multiple audio/subtitle languages. Hence, a French movie might get released on US Netflix earlier.
				MetaTools.TimeDigital		: ['primary', 'secondary', 'global', 'fallback'],
				MetaTools.TimePhysical		: ['primary', 'secondary', 'global', 'fallback'],
				MetaTools.TimeTelevision	: ['primary', 'secondary', 'global', 'fallback'],

				MetaTools.TimeUnknown		: ['global', 'fallback'],
			}

			result = {}
			for i in types.keys(): result[i] = None
			for i in extra.keys(): result[i] = None

			data = {i : {j : [] for j in types.keys()} for i in groups}
			for i in release:
				type = i.get('type') or MetaTools.TimeUnknown
				time = i.get('time')
				country = i.get('country')
				group = types.get(type, [])

				if 'global' in group: data['global'][type].append(time)
				if 'origin' in group and origin and country in origin: data['origin'][type].append(time)
				if 'primary' in group and country in primary: data['primary'][type].append(time)
				if 'secondary' in group and country in secondary: data['secondary'][type].append(time)
				if 'local' in group and local and country in local: data['local'][type].append(time)

			# Add the "premiered" date attribute in case no other dates are available.
			# These dates can differ between providers (IMDb, TMDb, and Trakt), since it mostly is NOT the "premiere" date, but rather any of the limited/theatrical/digital/physical dates.
			if metadata:
				premiered = metadata.get('aired') or metadata.get('premiered')
				if premiered: data['fallback'][MetaTools.TimeUnknown].append(Time.timestamp(fixedTime = premiered, format = Time.FormatDate, utc = True))

			# Find the minimum for each type and group.
			for k1, v1 in data.items():
				for k2, v2 in v1.items():
					v2 = [i for i in v2 if i]
					data[k1][k2] = min(v2) if v2 else None

			# Sometimes old releases get a new physical/digital release date.
			# Eg: https://trakt.tv/movies/the-twilight-saga-new-moon-2009/releases got a "15th Anniversary Steelbook" release in 2023.
			# Eg: https://trakt.tv/movies/aliens-1986/releases  got remastered physical/digital releases in 2023/2024.
			# If a digital/pysical/television release date from one country is more than 3 years older than the dates from other countries, ignore it.
			all = {MetaTools.TimeDigital : [], MetaTools.TimePhysical : [], MetaTools.TimeTelevision : []}
			for k1, v1 in data.items():
				for k2 in [MetaTools.TimeDigital, MetaTools.TimePhysical, MetaTools.TimeTelevision]:
					v2 = data[k1][k2]
					if v2: all[k2].append(v2)
			for k1, v1 in all.items():
				all[k1] = min(v1) if v1 else None
			for k1, v1 in data.items():
				for k2 in [MetaTools.TimeDigital, MetaTools.TimePhysical, MetaTools.TimeTelevision]:
					v2 = data[k1][k2]
					if v2 and all[k2] and (v2 - all[k2]) > 94672800: data[k1][k2] = None

			# Pick the value of the best available group.
			for i in types.keys():
				for j in groups:
					value = data[j][i]
					if not value is None:
						result[i] = value
						break

			# Summarize the extra dates with the other dates.
			for i, j in extra.items():
				try: result[i] = min(v for k, v in result.items() if not v is None and (not j or k in j))
				except: pass

			# Estimate missing dates from other dates.
			if estimate:
				estimate = {}
				for i in types.keys():
					estimate[i] = self.timeEstimate(type = i, times = result, metadata = metadata)
				for i, j in extra.items(): # Calculate again with the new estimates.
					try: estimate[i] = min(v for k, v in estimate.items() if not v is None and (not j or k in j))
					except: pass
				result['estimate'] = estimate

			return result
		except: Logger.error()
		return None

	def timeEstimate(self, type, times = None, metadata = None, default = None):
		try:
			# Examples:
			# 	Avatar: The Way of Water (2023)
			#		    Premiere:	2022-12-06
			#		    Limited:	None
			#		    Theatrical:	2022-12-14
			#		    Digital:	2023-03-28
			#		    Physical:	2023-06-20
			#		    Television:	2023-06-10
			# 	John Wick: Chapter 4 (2023)
			#		    Premiere:	2023-03-06
			#		    Limited:	None
			#		    Theatrical:	2023-03-22
			#		    Digital:	2023-05-23
			#		    Physical:	2023-06-13
			#		    Television:	None
			# 	The Covenant (2023)
			#		    Premiere:	2023-04-19
			#		    Limited:	None
			#		    Theatrical:	2023-04-21
			#		    Digital:	2023-05-09
			#		    Physical:	None
			#		    Television:	None

			earlier = None
			later = None
			time = None

			if not times: times = (metadata.get('time') or {}) if metadata else {}
			if default is None: default = self.timeDefault(times = times, metadata = metadata)

			if type == MetaTools.TimeDebut: type = MetaTools.TimePremiere
			elif type == MetaTools.TimeLaunch: type = MetaTools.TimeLimited
			elif type == MetaTools.TimeTheater: type = MetaTools.TimePremiere
			elif type == MetaTools.TimeCinema: type = MetaTools.TimeLimited
			elif type == MetaTools.TimeHome: type = MetaTools.TimeDigital

			if type == MetaTools.TimePremiere:
				time = times.get(MetaTools.TimePremiere)
				if time is None:
					previous = None
					next = times.get(MetaTools.TimeLimited)
					earlier = previous
					later = next

					if later is None:
						later = times.get(MetaTools.TimeTheatrical)
						if later is None:
							later = times.get(MetaTools.TimeDigital)
							if later is None:
								later = times.get(MetaTools.TimePhysical)
								if later is None:
									later = times.get(MetaTools.TimeTelevision)

					if not next is None: time = next - 604800 # 1 week.
					elif not default is None: time = default - 2419200 # 2 weeks.
			elif type == MetaTools.TimeLimited:
				time = times.get(MetaTools.TimeLimited)
				if time is None:
					previous = times.get(MetaTools.TimePremiere)
					next = times.get(MetaTools.TimeTheatrical)
					earlier = previous
					later = next

					if later is None:
						later = times.get(MetaTools.TimeDigital)
						if later is None:
							later = times.get(MetaTools.TimePhysical)
							if later is None:
								later = times.get(MetaTools.TimeTelevision)

					if not next is None: time = next - 604800 # 1 week.
					elif not default is None: time = default - 604800 # 1 week.
			elif type == MetaTools.TimeTheatrical:
				time = times.get(MetaTools.TimeTheatrical) or default
				if time is None:
					previous = times.get(MetaTools.TimeLimited)
					next = times.get(MetaTools.TimeDigital)
					earlier = previous
					later = next

					if earlier is None:
						earlier = times.get(MetaTools.TimePremiere)

					if later is None:
						later = times.get(MetaTools.TimePhysical)
						if later is None:
							later = times.get(MetaTools.TimeTelevision)

					if not previous is None: time = previous + 604800 # 1 week.
			elif type == MetaTools.TimeDigital:
				time = times.get(MetaTools.TimeDigital)
				if time is None:
					previous = times.get(MetaTools.TimeTheatrical)
					next = times.get(MetaTools.TimePhysical)
					earlier = previous
					later = next

					if earlier is None:
						earlier = times.get(MetaTools.TimeLimited)
						if earlier is None:
							earlier = times.get(MetaTools.TimePremiere)

					if later is None:
						later = times.get(MetaTools.TimeTelevision)

					if not next is None: time = next - 2419200 # 4 weeks.
					elif not previous is None: time = previous + 7257600 # 12 weeks.
					elif not default is None: time = default + 7257600 # 12 weeks.
			elif type == MetaTools.TimePhysical:
				time = times.get(MetaTools.TimePhysical)
				if time is None:
					previous = times.get(MetaTools.TimeDigital)
					next = times.get(MetaTools.TimeTelevision)
					later = next
					earlier = previous

					if earlier is None:
						earlier = times.get(MetaTools.TimeTheatrical)
						if earlier is None:
							earlier = times.get(MetaTools.TimeLimited)
							if earlier is None:
								earlier = times.get(MetaTools.TimePremiere)

					if not previous is None: time = previous + 2419200 # 4 weeks.
					elif not next is None: time = next - 2419200 # 2 weeks.
					elif not default is None: time = default + 9676800 # 16 weeks.
			elif type == MetaTools.TimeTelevision:
				time = times.get(MetaTools.TimeTelevision)
				if time is None:
					previous = times.get(MetaTools.TimePhysical)
					next = None
					earlier = previous
					later = next

					if earlier is None:
						earlier = times.get(MetaTools.TimeDigital)
						if earlier is None:
							earlier = times.get(MetaTools.TimeTheatrical)
							if earlier is None:
								earlier = times.get(MetaTools.TimeLimited)
								if earlier is None:
									earlier = times.get(MetaTools.TimePremiere)

					if not previous is None: time = previous + 1209600 # 2 weeks.
					elif not default is None: time = default + 10886400 # 18 weeks.
			else:
				time = times.get(type)
				if time is None and metadata:
					temp = metadata.get('temp')
					if temp:
						for provider in [MetaTools.ProviderImdb, MetaTools.ProviderTrakt, MetaTools.ProviderTmdb, MetaTools.ProviderTvdb]:
							time = temp.get(provider, {}).get('time', {}).get(type)
							if not time is None: break

			if not time is None:
				if not default is None: time = min(default, time) if type == MetaTools.TimePremiere or type == MetaTools.TimeLimited else max(default, time)
				if not earlier is None: time = max(earlier, time)
				if not later is None: time = min(later, time)
				return time
		except: Logger.error()
		return default if Tools.isInteger(default) else None

	def timeDefault(self, times = None, metadata = None):
		default = None
		try:
			if not times: times = (metadata.get('time') or {}) if metadata else {}

			if default is None and times:
				default = times.get(MetaTools.TimeTheatrical)
				if default is None:
					default = times.get(MetaTools.TimeLaunch)

			if default is None and metadata:
				default = metadata.get('aired') or metadata.get('premiered')
				if default is None and times:
					default = times.get(MetaTools.TimePremiere)
					if not default is None: default += 2419200 # 2 weeks to estimate the theatrical date.
				if default is None:
					year = metadata.get('year') or metadata.get('tvshowyear')
					if year: default = '%d-01-01' % year

			if not default is None and Tools.isString(default): default = Time.timestamp(fixedTime = default, format = Time.FormatDate, utc = True)
		except: Logger.error()
		return default

	# Given a list of times, pick the one that is closest to a specific or the current time.
	# time: base timestamp to compare against. If None, the current timestamp is used.
	# future: True (allow dates in the future), False (only allow past dates), Integer (maximum number of seconds into the future allowed).
	# past: Integer (if the past date is more than this number of seconds ago, also allow future dates).
	# fallback: True (return excluded dates if no other past date is available).
	def timeClosest(self, times, time = None, future = True, past = None, fallback = False, default = None):
		try:
			if time is None: time = self.mTimeCurrent
			values = []
			extra1 = []
			extra2 = []
			for i in times:
				if not i is None:
					difference = (time - i)
					if difference >= 0:
						values.append((difference, i))
					elif future:
						difference2 = abs(difference)
						if difference < 0 and (future is True or difference2 <= future): extra1.append((difference2, i)) # Only future dates withitn the "future" limit.
						extra2.append((difference2, i)) # All future dates, including those outside the "future" limit. Plus past dates.
						if future is True or difference2 <= future: values.append((difference2, i))

			result = None

			# First try to get the closest past date.
			if values: result = min(values, key = lambda i : i[0])

			# If the closest past date is older than the specified amount, also allow future dates to be used.
			# NB: On 2025-12-19 "Tron: Ares" had a digital date "18 days ago" while the physical date was "17 days into the future."
			# Hence, future=1week + past=2weeks does not work, since it will prefer the physical date.
			# Therefore use extra1 instead of extra2, which ONLY includes future dates that are within the limit of "future".
			if past and result and result[0] > past and extra1: result = min(extra1 + [result], key = lambda i : i[0])

			# Else pick the closest future date.
			elif fallback and extra2 and not result: result = min(extra2, key = lambda i : i[0])


			return result[1] if result else default
		except: Logger.error()
		return default

	###################################################################
	# FILTER
	###################################################################

	def filter(self, items, filter, unknown = None, **parameters):
		if Tools.isString(filter):
			data = dict(**parameters)
			data['unknown'] = unknown
			filter = {filter : data}

		before = len(items)
		total = before
		count = {}

		for key, value in filter.items():
			try:
				function = None

				if not value is None and not value is False:
					if key == MetaTools.FilterDuplicate: function = self.filterDuplicate
					elif key == MetaTools.FilterNumber: function = self.filterNumber
					elif key == MetaTools.FilterProgress: function = self.filterProgress
					elif key == MetaTools.FilterNiche: function = self.filterNiche
					elif key == MetaTools.FilterCertificate: function = self.filterCertificate
					elif key == MetaTools.FilterAudience: function = self.filterAudience
					elif key == MetaTools.FilterKid: function = self.filterKid
					elif key == MetaTools.FilterTeen: function = self.filterTeen
					elif key == MetaTools.FilterAdult: function = self.filterAdult
					elif key == MetaTools.FilterEdition: function = self.filterEdition
					elif key == MetaTools.FilterGenre: function = self.filterGenre
					elif key == MetaTools.FilterLanguage: function = self.filterLanguage
					elif key == MetaTools.FilterRating: function = self.filterRating
					elif key == MetaTools.FilterVotes: function = self.filterVotes
					elif key == MetaTools.FilterQuality: function = self.filterQuality
					elif key == MetaTools.FilterPopularity: function = self.filterPopularity
					elif key == MetaTools.FilterTime: function = self.filterTime
					elif key == MetaTools.FilterPartial: function = self.filterPartial

				if function:
					if Tools.isDictionary(value): items = function(items = items, **value)
					elif key == MetaTools.FilterDuplicate or key == MetaTools.FilterNumber: items = function(items = items)
					elif key == MetaTools.FilterCertificate: items = function(items = items, certificate = value, include = True, unknown = unknown)
					elif key == MetaTools.FilterAudience and Tools.isString(value): items = function(items = items, age = value, include = True, unknown = unknown)
					elif key == MetaTools.FilterEdition and Tools.isString(value): items = function(items = items, condition = value, unknown = unknown)
					elif key == MetaTools.FilterTime and value: items = function(items = items, include = True, time = value, unknown = unknown)
					elif key == MetaTools.FilterPartial and value: items = function(items = items)
					else: items = function(items = items, include = value, unknown = unknown)

					current = len(items)
					count[key] = before - current
					before = current
			except: Logger.error()

		if self.mDeveloper:
			after = len(items)
			values = ['%d %s' % (v, k.title()) for k, v in count.items() if v]
			values = ['%d Before' % total, '%d After' % after, ('%d Removed' % (total - after)) + ((' (%s)' % ', '.join(values)) if values else '')]
			Logger.log('FILTERING: ' + ', '.join(values))

		return items

	# Pass in a dictionary as "helper" to more efficiently filter if this function is called multiple times with the same items.
	# Do not pass in a helper if this function is only called once, since it is more efficient without it.
	# key: try to extract the season/episode number from a nested dictionary, before trying the numbers from the root dictionary.
	# number='extended': also use sequential and Trakt alternative numbers.
	# serie=True: treat shows/seasons/episodes as the same media. Otherwise they are seen as separate media, hence a show with the same ID as an episode would be seen as different items.
	def filterContains(self, items, item, number = False, result = False, key = None, serie = False, helper = None):
		try:
			def _number(item, type, key):
				value = None
				if key:
					try: value = item[key][type]
					except: pass
				if value is None:
					try: value = item[type]
					except: pass
				return 'z' if value is None else str(value)

			def _numbers(item, id, key, extended = False):
				mediad = item.get('media')
				if serie and Media.isSerie(mediad): mediad = Media.Show

				# Add the media type, since movies and episodes can have the same TMDb ID.
				#	https://www.themoviedb.org/movie/1891
				#	https://www.themoviedb.org/tv/1891
				if extended:
					numbers = [[_number(item, 'season', key), _number(item, 'episode', key)]]
					values = item.get('number')
					if values:
						numbers.append(values.get(MetaPack.NumberStandard))
						numbers.append(values.get(MetaPack.NumberSequential))
						trakt = values.get(MetaPack.ProviderTrakt)
						if trakt:
							numbers.append(trakt.get(MetaPack.NumberStandard))
							numbers.append(trakt.get(MetaPack.NumberSequential))
					base = str(mediad) + '_' + str(id) + '_%s_%s'
					return Tools.listUnique([base % (str(i[0]), str(i[1])) for i in numbers if i])
				else:
					return '%s_%s_%s_%s' % (str(mediad), str(id), _number(item, 'season', key), _number(item, 'episode', key))

			extended = number == 'extended'

			if helper is None:
				helper = {'imdb' : {}, 'tmdb' : {}, 'tvdb' : {}, 'trakt' : {}}
				keys = list(helper.keys())
				keys.append('imdx') # Alternative/outdated IMDb ID not updated on Trakt/TMDb/TVDb yet. Check MetaManager._metadataSmartLoad() for more info.

				for id in keys:
					i = item.get(id)
					if i:
						lookup = 'imdb' if id == 'imdx' else id
						if number: i = _numbers(item, i, key, extended = extended)
						if Tools.isArray(i):
							for j in i: helper[lookup][j] = True
						else:
							helper[lookup][i] = True

				# Outer and inner loops like this, not the other way around.
				# More efficient, because we first scan one ID over all items before moving on to the next ID.
				for id in keys:
					if id == 'imdx':
						imdx = True
						lookup = 'imdb'
					else:
						imdx = False
						lookup = id

					if helper.get(lookup):
						for value in items:
							i = value.get(id)
							if i:
								# Check this, otherwise an item might be filtered out if its "imdb" is equal to "imdx".
								if imdx and i == value.get('imdb'): continue

								if number: i = _numbers(value, i, key, extended = extended)
								if Tools.isArray(i):
									for j in i:
										if helper[lookup].get(j): return value if result else True
								else:
									if helper[lookup].get(i): return value if result else True
			else:
				keys = []
				if not helper:
					helper.update({'imdb' : {}, 'tmdb' : {}, 'tvdb' : {}, 'trakt' : {}}) # Update, not assign, since it is passed by reference.
					keys = list(helper.keys())
					keys.append('imdx') # Alternative/outdated IMDb ID not updated on Trakt/TMDb/TVDb yet. Check MetaManager._metadataSmartLoad() for more info.

					for value in items:
						for id in keys:
							i = value.get(id)
							if i:
								lookup = 'imdb' if id == 'imdx' else id
								if number: i = _numbers(value, i, key, extended = extended)
								if Tools.isArray(i):
									for j in i: helper[lookup][j] = value
								else:
									helper[lookup][i] = value

				else:
					keys = list(helper.keys())
					keys.append('imdx') # Alternative/outdated IMDb ID not updated on Trakt/TMDb/TVDb yet. Check MetaManager._metadataSmartLoad() for more info.

				for id in keys:
					if id == 'imdx':
						imdx = True
						lookup = 'imdb'
					else:
						imdx = False
						lookup = id

					i = item.get(id)
					if i:
						# Check this, otherwise an item might be filtered out if its "imdb" is equal to "imdx".
						if imdx and i == item.get('imdb'): continue

						if number: i = _numbers(item, i, key, extended = extended)
						if Tools.isArray(i):
							for j in i:
								value = helper[lookup].get(j)
								if value: break
						else:
							value = helper[lookup].get(i)
						if value: return value if result else True

			return None if result else False
		except: Logger.error()
		return None

	# merge=True: merge duplicate items. Later items will replace earlier items.
	# merge="number": merge duplicate items. Items with a higher season/episode number will replace items with a lower number.
	# merge="id": merge duplicate items. Items with more provider IDs will replace those with fewer IDs.
	# merge="idless": merge duplicate items. Items with fewer provider IDs will replace those with more IDs.
	# merge="idimdb": merge duplicate items. Items with fewer provider IDs will replace those with more IDs, and the "imdb" and "imdx" IDs are changed accordingly.
	# serie=True: treat shows/seasons/episodes as the same media. Otherwise they are seen as separate media, hence a show with the same ID as an episode would be seen as different items.
	def filterDuplicate(self, items, id = True, title = False, number = False, key = None, last = False, serie = False, merge = False):
		try:
			if last: items = reversed(items)
			custom = Tools.isString(number)

			mergeNumber = False
			mergeId = False
			mergeIdless = False
			mergeIdimdb = False
			mergeVote = False
			if merge:
				if not Tools.isArray(merge): merge = [merge]
				mergeNumber = 'number' in merge
				mergeId = 'id' in merge
				mergeIdless = 'idless' in merge
				mergeIdimdb = 'idimdb' in merge or 'imdb' in merge
				mergeVotes = 'votes' in merge

			if id:
				result = []
				duplicates = {'imdb' : {}, 'tmdb' : {}, 'tvdb' : {}, 'trakt' : {}}
				keys = list(duplicates.keys())
				keys.append('imdx') # Alternative/outdated IMDb ID not updated on Trakt/TMDb/TVDb yet. Check MetaManager._metadataSmartLoad() for more info.

				for item in items:
					found = False
					entry = item[key] if key else item
					for i in keys:
						value = entry.get(i)
						if value:
							if i == 'imdx':
								# Check this, otherwise an item might be filtered out if its "imdb" is equal to "imdx".
								if value == entry.get('imdb'): continue
								lookup = 'imdb'
							else:
								lookup = i

							# Add the media type, since movies and episodes can have the same TMDb ID.
							#	https://www.themoviedb.org/movie/1891
							#	https://www.themoviedb.org/tv/1891
							mediad = entry.get('media')
							if serie and Media.isSerie(mediad): mediad = Media.Show
							j = '%s_%s' % (str(mediad), entry[i])

							if number:
								if custom:
									try:
										numberSeason = entry['season']
										if numberSeason == 0: season = numberSeason # Specials have all the same sequential numbers.
										else: season = entry['number'][number][MetaPack.PartSeason]
									except:
										try: season = entry['season']
										except: season = 'z'
									try:
										numberSeason = entry['season']
										if numberSeason == 0: episode = str(numberSeason) + '-' + str(entry['episode'])
										else: episode = entry['number'][number][MetaPack.PartEpisode]
									except:
										try: episode = str(entry['season']) + '-' + str(entry['episode']) # Do not confuse the season-episode number with the sequential episode number.
										except: episode = 'z'
								else:
									try: season = entry['season']
									except: season = 'z'
									try: episode = entry['episode']
									except: episode = 'z'
								try: sequential = entry['sequential']
								except: sequential = 'z'
								j = '%s_%s_%s_%s' % (j, str(season), str(episode), str(sequential))

							found = duplicates[lookup].get(j)
							if found: break
							else: duplicates[lookup][j] = item

					if not found:
						result.append(item)
					elif found and merge:
						swap = False

						# Pick the one with the highest number.
						if mergeNumber:
							number1 = ((found.get('season') or 0) * 10000000) + (found.get('episode') or 0)
							number2 = ((item.get('season') or 0) * 10000000) + (item.get('episode') or 0)
							if number1 > number2: swap = True

						# Pick the one with the most number of IDs.
						imdbNew = None
						imdbOld = None
						if mergeId or mergeIdless or mergeIdimdb:
							ids1 = [k for k, v in (found.get('id') or {}).items() if v]
							ids2 = [k for k, v in (item.get('id') or {}).items() if v]
							number1 = len(ids1)
							number2 = len(ids2)
							if mergeIdimdb:
								# Set the newest IMDb ID, if there is a difference between the IMDb ID from different lists.
								# Trakt/TMDb can sometimes have an old/oudated IMDb ID, which on IMDb now redirects to a new ID.
								# If only a imdb/imdx ID is available, assume it comes from an IMDb list and therefore has the newest ID.
								# Otherwise it comes from Trakt/TMDb and its ID is probably the one outdated.
								if 'imdb' in ids1 and (number1 == 1 or (number1 == 2 and 'imdx' in ids1)):
									try: imdbNew = found['id']['imdb']
									except: pass
									try: imdbOld = item['id']['imdb']
									except: pass
								elif 'imdb' in ids2 and (number2 == 1 or (number2 == 2 and 'imdx' in ids2)):
									try: imdbNew = item['id']['imdb']
									except: pass
									try: imdbOld = found['id']['imdb']
									except: pass
							if mergeIdless or mergeIdimdb:
								if number1 > number2: swap = True
							else:
								if number1 < number2: swap = True

						# Prefer the one with the higher number of votes, which is typically the more recent metadata (eg: Arrivals).
						if not swap and mergeVotes:
							number1 = found.get('votes') or 0
							number2 = item.get('votes') or 0
							if number1 > number2: swap = True

						if swap:
							swap = found
							found = item
							item = swap

						Tools.update(found, item, none = False, lists = True, unique = True) # Do not append, the "found" var is a reference to the dict already in result.

						if imdbNew or imdbOld:
							if not found.get('id'): found['id'] = {}
							if imdbNew: found['id']['imdb'] = found['imdb'] = imdbNew
							if imdbOld: found['id']['imdx'] = found['imdx'] = imdbOld

				items = result

			if title:
				result = []
				duplicates = {}
				keys = ['title', 'originaltitle']
				for item in items:
					found = False
					entry = item[key] if key else item
					values = {}
					for i in keys:
						if entry.get(i):
							# Add the media type, in case a movie and show/episode have the same name.
							# Important to use lower case, since sometimes the titles between IMDb and TMDb do not use the sasme case.
							# Eg: "Operation Fortune: Ruse de guerre" vs Operation Fortune: Ruse de Guerre
							mediad = entry.get('media')
							if serie and Media.isSerie(mediad): mediad = Media.Show
							j = '%s_%s' % (str(mediad), Regex.remove(data = entry[i].lower(), expression = Regex.Symbol, all = True, cache = True).replace('  ', ' '))

							if number:
								if custom:
									try:
										numberSeason = entry['season']
										if numberSeason == 0: season = numberSeason # Specials have all the same sequential numbers.
										else: season = entry['number'][number][MetaPack.PartSeason]
									except:
										try: season = entry['season']
										except: season = 'z'
									try:
										numberSeason = entry['season']
										if numberSeason == 0: episode = str(numberSeason) + '-' + str(entry['episode'])
										else: episode = entry['number'][number][MetaPack.PartEpisode]
									except:
										try: episode = str(entry['season']) + '-' + str(entry['episode']) # Do not confuse the season-episode number with the sequential episode number.
										except: episode = 'z'
								else:
									try: season = entry['season']
									except: season = 'z'
									try: episode = entry['episode']
									except: episode = 'z'

								j = '%s_%s_%s' % (j, str(season), str(episode))
							found = duplicates.get(j)
							if found: break
							else: values[j] = item

					duplicates.update(values)
					if not found:
						result.append(item)
					elif found and merge:
						swap = False

						# Pick the one with the highest number.
						if mergeNumber:
							number1 = ((found.get('season') or 0) * 10000000) + (found.get('episode') or 0)
							number2 = ((item.get('season') or 0) * 10000000) + (item.get('episode') or 0)
							if number1 > number2: swap = True

						# Pick the one with the most number of IDs.
						imdbNew = None
						imdbOld = None
						if mergeId or mergeIdless or mergeIdimdb:
							ids1 = [k for k, v in (found.get('id') or {}).items() if v]
							ids2 = [k for k, v in (item.get('id') or {}).items() if v]
							number1 = len(ids1)
							number2 = len(ids2)
							if mergeIdimdb:
								# Set the newest IMDb ID, if there is a difference between the IMDb ID from different lists.
								# Trakt/TMDb can sometimes have an old/oudated IMDb ID, which on IMDb now redirects to a new ID.
								# If only a imdb/imdx ID is available, assume it comes from an IMDb list and therefore has the newest ID.
								# Otherwise it comes from Trakt/TMDb and its ID is probably the one outdated.
								if 'imdb' in ids1 and (number1 == 1 or (number1 == 2 and 'imdx' in ids1)):
									try: imdbNew = found['id']['imdb']
									except: pass
									try: imdbOld = item['id']['imdb']
									except: pass
								elif 'imdb' in ids2 and (number2 == 1 or (number2 == 2 and 'imdx' in ids2)):
									try: imdbNew = item['id']['imdb']
									except: pass
									try: imdbOld = found['id']['imdb']
									except: pass
							if mergeIdless or mergeIdimdb:
								if number1 > number2: swap = True
							else:
								if number1 < number2: swap = True

						# Prefer the one with the higher number of votes, which is typically the more recent metadata (eg: Arrivals).
						if not swap and mergeVotes:
							number1 = found.get('votes') or 0
							number2 = item.get('votes') or 0
							if number1 > number2: swap = True

						if swap:
							swap = found
							found = item
							item = swap

						Tools.update(found, item, none = False, lists = True, unique = True) # Do not append, the "found" var is a reference to the dict already in result.

						if imdbNew or imdbOld:
							if not found.get('id'): found['id'] = {}
							if imdbNew: found['id']['imdb'] = found['imdb'] = imdbNew
							if imdbOld: found['id']['imdx'] = found['imdx'] = imdbOld

				items = result

			if last: items = list(reversed(items))
		except: Logger.error()
		return items

	# single: Media.Season = only return a single season. Media.Episode = only return a single episode.
	def filterNumber(self, items, season = None, episode = None, single = None, special = None):
		try:
			if Tools.isArray(items) and not season is None and not episode is None:
				season = abs(season)
				episode = abs(episode)

				# Allow IMDb specials.
				# Eg: GoT S01E00
				# If the episode is SxxE01, also check for SxxE00.
				#number = [x for x, y in enumerate(items) if y['season'] == season and y['episode'] == episode]
				number = [x for x, y in enumerate(items) if y['season'] == season and (y['episode'] == episode or (episode == 1 and y['episode'] == 0))]

				if not number: number = [x for x, y in enumerate(items) if y['season'] == season + 1 and (y['episode'] == 0 or y['episode'] == 1)]

				if number:
					# Update (2025-07):
					# Not sure why the last number was used here?
					# But this does not add IMDb specials SxxE00.
					# For those specials, both SxxE00 and SxxE01 are in "number".
					# Pick the first one SxxE00, for interleaved series/progress submenus.
					# Eg: LEGO Masters S03E00 + S03E01.
					#number = number[-1]
					number = number[0]

					if self.mShowInterleave if special is None else special:
						if single == Media.Episode: items = [y for x, y in enumerate(items) if x == number or y['season'] == 0]
						elif single == Media.Season: items = [y for x, y in enumerate(items) if (x >= number and y['season'] == season) or y['season'] == 0]
						else: items = [y for x, y in enumerate(items) if x >= number or y['season'] == 0]
					else:
						if single == Media.Episode: items = [y for x, y in enumerate(items) if x == number]
						elif single == Media.Season: items = [y for x, y in enumerate(items) if x >= number and y['season'] == season]
						else: items = [y for x, y in enumerate(items) if x >= number]
		except: Logger.error()
		return items

	# include(bool): include specific progress types.
	# exclude(bool): exclude specific progress types.
	# unknown(None/bool): True = include items without a progress or colunt. False = exclude items without a progress or colunt. None = include items without a progress or colunt.
	def filterProgress(self, items, include = None, exclude = None, unknown = None):
		if include or exclude:
			def _value(value, rewatch, base = None, media = None):
				if Tools.isDictionary(value): value = value[media]
				if base: value += base
				return (value % 1) if rewatch else value

			def _valid(item, lt = None, gt = None, le = None, ge = None, unknown = None, rewatch = None, base = None):
				play = Tools.get(item, 'smart', 'play')
				if not play and not unknown: return False

				play = _value(play, rewatch)
				media = Media.Show if Media.isSerie(item.get('media')) else Media.Movie

				if not lt is None and play >= _value(lt, rewatch, base, media): return False
				if not gt is None and play <= _value(gt, rewatch, base, media): return False
				if not le is None and play > _value(le, rewatch, base, media): return False
				if not ge is None and play < _value(ge, rewatch, base, media): return False

				return True

			if unknown is None: unknown = True
			if include and not Tools.isArray(include): include = [include]
			if exclude and not Tools.isArray(exclude): exclude = [exclude]

			from lib.modules.playback import Playback
			start = {}
			end = {}
			conclude = {}
			for i in [Media.Movie, Media.Show]: # Add both, so we can also filter mixed lists.
				start[i] = Playback.percentStart(media = i)
				end[i] = Playback.percentEnd(media = i)
				conclude[i] = Playback.percentConclude(media = i)
			end[Media.Show] = 0.999 # Movies can have a earlier end, due to credits. But shows are only done if the last episode was watched.

			for i in include:
				if not i or i == MetaTools.ProgressDefault or i == MetaTools.ProgressAll: continue # Not filtered, only sorted.
				elif i == MetaTools.ProgressStarted: function = lambda x: _valid(x, gt = 0, le = start, unknown = unknown, rewatch = True) # Also allow if rewatching.
				elif i == MetaTools.ProgressPartial: function = lambda x: _valid(x, gt = start, le = end, unknown = unknown, rewatch = True) # Also allow if rewatching.
				elif i == MetaTools.ProgressConclude: function = lambda x: _valid(x, ge = conclude, le = end, unknown = unknown, rewatch = True) # Also allow if rewatching.
				elif i == MetaTools.ProgressUnfinished: function = lambda x: _valid(x, le = end, unknown = unknown)
				elif i == MetaTools.ProgressFinished: function = lambda x: _valid(x, gt = end, unknown = unknown)
				elif i == MetaTools.ProgressRewatch: function = lambda x: _valid(x, gt = end, unknown = unknown)
				elif i == MetaTools.ProgressRewatching: function = lambda x: _valid(x, gt = 1, unknown = unknown)
				elif i == MetaTools.ProgressRewatched: function = lambda x: _valid(x, gt = end, unknown = unknown, base = 1) # Using "base" is the same as "gt = 1 + end".

				if function: items = [item for item in items if function(item)]

			return items

	# include(bool): include specific niches.
	# exclude(bool): exclude specific niches.
	# unknown(None/bool): True = include items without a niche. False = exclude items without a niche. None = False for include and True for exclude.
	def filterNiche(self, items, include = None, exclude = None, unknown = None):
		if include or exclude:
			if unknown is None: unknown = False if include else True
			if include and not Tools.isArray(include): include = Media.stringFrom(include)
			if exclude and not Tools.isArray(exclude): exclude = Media.stringFrom(exclude)

			temp = []
			for item in items:
				value = item.get('niche')
				if value:
					if not Tools.isArray(value): value = Media.stringFrom(value)
					if include and all(i in value for i in include): temp.append(item)
					elif exclude and not any(i in value for i in exclude): temp.append(item)
				elif unknown:
					temp.append(item)

			items = temp
		return items

	# include(bool): include certified content.
	# exclude(bool): exclude certified content.
	# unknown(None/bool): True = include items without a certificate. False = exclude items without a certificate. None = False for include and True for exclude.
	def filterCertificate(self, items, certificate, include = None, exclude = None, unknown = None, select = Audience.SelectAll):
		if include or exclude:
			if unknown is None: unknown = False if include else True
			if not Tools.isArray(certificate): certificate = [certificate]

			temp = []
			for item in items:
				mpaa = item.get('mpaa')
				if mpaa:
					contains = Audience.allowed(certificate = mpaa, certificates = certificate, unrated = unknown, select = select)
					if include and contains: temp.append(item)
					elif exclude and not contains: temp.append(item)
				elif unknown:
					temp.append(item)

			items = temp
		return items

	# include(bool): include generational content and exlude non-generational content.
	# exclude(bool): exclude generational content and include non-generational content.
	# unknown(None/bool): True = include items without a certificate. False = exclude items without a certificate. None = False for include and True for exclude.
	def filterAudience(self, items, age, include = None, exclude = None, unknown = None, select = Audience.SelectAll):
		if include or exclude:
			if unknown is None: unknown = False if include else True

			temp = []
			for item in items:
				mpaa = item.get('mpaa')
				if mpaa:
					contains = Audience.allowed(certificate = mpaa, type = age, unrated = unknown, select = select)
					if include and contains: temp.append(item)
					elif exclude and not contains: temp.append(item)
				elif unknown:
					temp.append(item)

			items = temp
		return items

	# include(bool): include kids content and exlude non-kids content.
	# exclude(bool): exclude kids content and include non-kids content.
	# unknown(None/bool): True = include items without a certificate. False = exclude items without a certificate. None = False for include and True for exclude.
	def filterKid(self, items, include = None, exclude = None, unknown = None, select = Audience.SelectExclusive):
		return self.filterAudience(items = items, age = Audience.TypeKid, include = include, exclude = exclude, unknown = unknown, select = select)

	# include(bool): include teens content and exlude non-teens content.
	# exclude(bool): exclude teens content and include non-teens content.
	# unknown(None/bool): True = include items without a certificate. False = exclude items without a certificate. None = False for include and True for exclude.
	def filterTeen(self, items, include = None, exclude = None, unknown = None, select = Audience.SelectExclusive):
		return self.filterAudience(items = items, age = Audience.TypeTeen, include = include, exclude = exclude, unknown = unknown, select = select)

	# include(bool): include adults content and exlude non-adults content.
	# exclude(bool): exclude adults content and include non-adults content.
	# unknown(None/bool): True = include items without a certificate. False = exclude items without a certificate. None = False for include and True for exclude.
	def filterAdult(self, items, include = None, exclude = None, unknown = None, select = Audience.SelectExclusive):
		if unknown is None and include: unknown = True # Allow unrated items for adults.
		return self.filterAudience(items = items, age = Audience.TypeAdult, include = include, exclude = exclude, unknown = unknown, select = select)

	# unknown: True = include items without a title. False = exclude items without a title.
	# full: check the release date and duration and exclude any item without one of them.
	# condition: link or query string that has to be matched before filtering.
	def filterEdition(self, items, include = None, exclude = None, unknown = None, full = True, condition = None):
		# Hide extended editions, since otherwise some users might scrape that one instead of the normal edition and then find fewer/no links.
		try:
			if condition is None or not Regex.match(data = condition, expression = '(extend|special|edition|version)'):
				if unknown is None: unknown = True
				if include is None and exclude is None: exclude = True
				result = []
				for item in items:
					title = item.get('title')
					if title:
						normal = False
						if not Regex.match(data = title, expression = '[\(\[].*?edition.*[\)\]]$', cache = True):
							if full:
								if item.get('year') or item.get('tvshowyear') or item.get('premiered') or (item.get('time') or {}).get(MetaTools.TimePremiere) or item.get('duration'):
									normal = True
							else:
								normal = True
						if exclude:
							if normal: result.append(item)
						elif include:
							if not normal: result.append(item)
					elif unknown:
						result.append(item)
				items = result
		except: Logger.error()
		return items

	# Either provide 'include' or 'exclude', not both.
	# include(None/string/list/tuple): genres to include.
	# exclude(None/string/list/tuple): genres to exclude.
	# unknown: True = include items without a genre. False = exclude items without a genre.
	# limit: True = only evaluate the main/primary genre of the title. False/None = evaluate all genres of the title. Integer = evaluate the first N genres of the title.
	def filterGenre(self, items, include = None, exclude = None, unknown = None, limit = None):
		try:
			if unknown is None: unknown = True

			genres = None
			if not include is None:
				matched = 1
				unmatched = -1
				if Tools.isArray(include): genres = include
				else: genres = [include]
			elif not exclude is None:
				matched = -1
				unmatched = 1
				if Tools.isArray(exclude): genres = exclude
				else: genres = [exclude]
			else:
				return items

			result = []
			for item in items:
				value = item.get('genre')
				if value:
					match = unmatched
					for i in range(len(value)):
						if limit and i == limit:
							break # Only check the 1st genre.
						elif value[i] in genres:
							match = matched
							break
				else: match = 0
				result.append({'match' : match, 'item' : item})

			if unknown: result = [i['item'] for i in result if i['match'] >= 0]
			else: result = [i['item'] for i in result if i['match'] == 1]

			return result
		except: Logger.error()
		return items

	# Either provide 'include' or 'exclude', not both. Languages must be 2-digit ISO codes (ISO-639-1).
	# include(None/string/list/tuple): languages to include.
	# exclude(None/string/list/tuple): languages to exclude.
	# unknown: True = include items without a language. False = exclude items without a language.
	# limit: True = only evaluate the main/primary language of the title. False/None = evaluate all languages of the title. Integer = evaluate the first N languages of the title.
	def filterLanguage(self, items, include = None, exclude = None, unknown = None, limit = None):
		try:
			languages = None
			if not include is None:
				matched = 1
				unmatched = -1
				if Tools.isArray(include): languages = {i : True for i in include}
				else: languages = {include : True}
			elif not exclude is None:
				matched = -1
				unmatched = 1
				if Tools.isArray(exclude): languages = {i : True for i in exclude}
				else: languages = {exclude : True}
			else:
				return items

			if unknown is None: unknown = True
			if limit is True: limit = 1

			result = []
			for item in items:
				value = item.get('language')
				if value:
					match = unmatched
					for i in range(len(value)):
						if limit and i == limit:
							break # Only check the 1st language.
						elif value[i] in languages:
							match = matched
							break
				else: match = 0
				result.append({'match' : match, 'item' : item})

			if unknown: result = [i['item'] for i in result if i['match'] >= 0]
			else: result = [i['item'] for i in result if i['match'] == 1]

			return result
		except: Logger.error()
		return items

	# Either provide 'include' or 'exclude', not both. Countries must be 2-digit ISO codes (ISO Alpha-2).
	# include(None/string/list/tuple): countries to include.
	# exclude(None/string/list/tuple): countries to exclude.
	# unknown: True = include items without a language. False = exclude items without a language.
	# limit: True = only evaluate the main/primary language of the title. False/None = evaluate all countries of the title. Integer = evaluate the first N countries of the title.
	def filterCountry(self, items, include = None, exclude = None, unknown = None, limit = None):
		try:
			countries = None
			if not include is None:
				matched = 1
				unmatched = -1
				if Tools.isArray(include): countries = {i : True for i in include}
				else: countries = {include : True}
			elif not exclude is None:
				matched = -1
				unmatched = 1
				if Tools.isArray(exclude): countries = {i : True for i in exclude}
				else: countries = {exclude : True}
			else:
				return items

			if unknown is None: unknown = True
			if limit is True: limit = 1

			result = []
			for item in items:
				value = item.get('country')
				if value:
					match = unmatched
					for i in range(len(value)):
						if limit and i == limit:
							break # Only check the 1st language.
						elif value[i] in countries:
							match = matched
							break
				else: match = 0
				result.append({'match' : match, 'item' : item})

			if unknown: result = [i['item'] for i in result if i['match'] >= 0]
			else: result = [i['item'] for i in result if i['match'] == 1]

			return result
		except: Logger.error()
		return items

	# Either provide 'include' or 'exclude', not both.
	# include(None/int/float/list/tuple): minimum or [minimum,maximum] rating to include.
	# exclude(None/int/float/list/tuple): maximum or [minimum,maximum] rating to exclude.
	# unknown: True = include items without a rating. False = exclude items without a rating.
	# deviation: percentage [0.0, 1.0] the rating can be outside the required range to accommodate rating averages from multiple providers. True = 0.5 rating deviation. Float = specific percetange. List = Upper and lower percetange deviation.
	def filterRating(self, items, include = None, exclude = None, unknown = None, deviation = None):
		try:
			minimum = 0
			maximum = 10

			if not include is None:
				matched = 1
				unmatched = -1
				if Tools.isArray(include):
					if not include[0] is None: minimum = include[0]
					if not include[1] is None: maximum = include[1]
				else:
					minimum = include
			elif not exclude is None:
				matched = -1
				unmatched = 1
				if Tools.isArray(exclude):
					if not exclude[0] is None: minimum = exclude[0]
					if not exclude[1] is None: maximum = exclude[1]
				else:
					maximum = exclude
			else:
				return items

			if unknown is None: unknown = True

			if deviation:
				fixed = 0.5
				if not Tools.isArray(deviation): deviation = [deviation, deviation]
				if deviation[0] is True: minimum -= fixed
				else: minimum -= minimum * deviation[0]
				if deviation[1] is True: maximum += fixed
				else: maximum += maximum * deviation[1]

			result = []
			for item in items:
				value = item.get('userrating') or item.get('rating')
				if not value: match = 0
				elif value >= minimum and value <= maximum: match = matched
				else: match = unmatched
				result.append({'match' : match, 'item' : item})

			if unknown: result = [i['item'] for i in result if i['match'] >= 0]
			else: result = [i['item'] for i in result if i['match'] == 1]

			return result
		except: Logger.error()
		return items

	# Either provide 'include' or 'exclude', not both.
	# include(None/int/float/list/tuple): minimum or [minimum,maximum] number of votes to include.
	# exclude(None/int/float/list/tuple): maximum or [minimum,maximum] number of votes to exclude.
	# unknown: True = include items without votes. False = exclude items without votes.
	def filterVotes(self, items, include = None, exclude = None, unknown = None):
		try:
			minimum = 0
			maximum = 9999999999

			if not include is None:
				matched = 1
				unmatched = -1
				if Tools.isArray(include):
					if not include[0] is None: minimum = include[0]
					if not include[1] is None: maximum = include[1]
				else:
					minimum = include
			elif not exclude is None:
				matched = -1
				unmatched = 1
				if Tools.isArray(exclude):
					if not exclude[0] is None: minimum = exclude[0]
					if not exclude[1] is None: maximum = exclude[1]
				else:
					maximum = exclude
			else:
				return items

			if unknown is None: unknown = True

			result = []
			for item in items:
				value = item.get('votes')
				if not value: match = 0
				elif value >= minimum and value <= maximum: match = matched
				else: match = unmatched
				result.append({'match' : match, 'item' : item})

			if unknown: result = [i['item'] for i in result if i['match'] >= 0]
			else: result = [i['item'] for i in result if i['match'] == 1]

			return result
		except: Logger.error()
		return items

	# Either provide 'include' or 'exclude', not both.
	# include(None/bool/int/float/list/tuple): True or minimum or [minimum,maximum] rating to include.
	# exclude(None/bool/int/float/list/tuple): True or maximum or [minimum,maximum] rating to exclude.
	# unknown: True = include items without a rating. False = exclude items without a rating.
	def filterQuality(self, items, include = None, exclude = None, unknown = None):
		try:
			minimum = 0
			maximum = 10
			default = 6.5

			if not include is None:
				if include is True: include = default
				matched = 1
				unmatched = -1
				if Tools.isArray(include):
					if not include[0] is None: minimum = include[0]
					if not include[1] is None: maximum = include[1]
				else:
					minimum = include
			elif not exclude is None:
				if exclude is True: exclude = default
				matched = -1
				unmatched = 1
				if Tools.isArray(exclude):
					if not exclude[0] is None: minimum = exclude[0]
					if not exclude[1] is None: maximum = exclude[1]
				else:
					maximum = exclude
			else:
				return items

			if unknown is None: unknown = True

			result = []
			for item in items:
				value = self.voting(metadata = item)
				if value: value = value['rating']
				if not value: match = 0
				elif value >= minimum and value <= maximum: match = matched
				else: match = unmatched
				result.append({'match' : match, 'item' : item})

			if unknown: result = [i['item'] for i in result if i['match'] >= 0]
			else: result = [i['item'] for i in result if i['match'] == 1]

			return result
		except: Logger.error()
		return items

	# Either provide 'include' or 'exclude', not both.
	# include(None/bool/int/float/list/tuple): True or minimum or [minimum,maximum] rating to include.
	# exclude(None/bool/int/float/list/tuple): True or maximum or [minimum,maximum] rating to exclude.
	# unknown: True = include items without a rating. False = exclude items without a rating.
	def filterPopularity(self, items, include = None, exclude = None, unknown = None):
		try:
			minimum = 0
			maximum = 100000000
			default = 20000

			if not include is None:
				if include is True: include = default
				matched = 1
				unmatched = -1
				if Tools.isArray(include):
					if not include[0] is None: minimum = include[0]
					if not include[1] is None: maximum = include[1]
				else:
					minimum = include
			elif not exclude is None:
				if exclude is True: exclude = default
				matched = -1
				unmatched = 1
				if Tools.isArray(exclude):
					if not exclude[0] is None: minimum = exclude[0]
					if not exclude[1] is None: maximum = exclude[1]
				else:
					maximum = exclude
			else:
				return items

			if unknown is None: unknown = True

			result = []
			for item in items:
				value = self.voting(metadata = item)
				if value: value = value['votes']
				if not value: match = 0
				elif value >= minimum and value <= maximum: match = matched
				else: match = unmatched
				result.append({'match' : match, 'item' : item})

			if unknown: result = [i['item'] for i in result if i['match'] >= 0]
			else: result = [i['item'] for i in result if i['match'] == 1]

			return result
		except: Logger.error()
		return items

	# Either provide 'include' or 'exclude', not both. Values can be number of seconds or date format.
	# include(None/int/float/list/tuple): maximum or [minimum,maximum] age to include.
	# exclude(None/int/float/list/tuple): minimum or [minimum,maximum] age to exclude.
	# unknown: True = include items without an age. False = exclude items without an age.
	# time: TimeLaunch/TimeHome or list of times to check against. None = All available times.
	# deviation: percentage [0.0, 1.0] the time can be outside the required range to accommodate slightly older/newer titles. True = the time range (eg range of 1 month allows up to a month older/newer). Float = specific percetange. List = specific percentage for older and newer titles.
	def filterTime(self, items, include = None, exclude = None, unknown = None, time = None, deviation = None):
		try:
			default = 9999999999
			minimum = default
			maximum = -default # Negative, to make the Time.past() calculate a time far into the future.
			matched = 1
			unmatched = -1

			if not include is None:
				if Tools.isArray(include):
					if not include[0] is None: minimum = include[0]
					if not include[1] is None: maximum = include[1]
				else:
					maximum = include
			elif not exclude is None:

				if Tools.isArray(exclude):
					if not exclude[0] is None: minimum = exclude[0]
					if not exclude[1] is None: maximum = exclude[1]
				else:
					minimum = exclude
			else:
				return items

			if unknown is None: unknown = True

			release = {
				Media.Movie		: 86400, # 1 day.
				Media.Show		: 10800, # 3 hours.
				Media.Unknown	: 86400, # 1 day.
			}

			minimum = {k :
				0 if minimum is False else
				Time.timestamp(fixedTime = minimum, format = Time.FormatDate, utc = True) if Tools.isString(minimum) else
				Time.past(seconds = v if minimum is True else minimum, format = Time.FormatTimestamp)
			for k, v in release.items()}

			maximum = {k :
				0 if maximum is False else
				Time.timestamp(fixedTime = maximum, format = Time.FormatDate, utc = True) if Tools.isString(maximum) else
				Time.past(seconds = v if maximum is True else maximum, format = Time.FormatTimestamp)
			for k, v in release.items()}

			if deviation:
				year = 31556952
				if not Tools.isArray(deviation): deviation = [deviation, deviation]
				for i in release.keys():
					# If deviation == True, allow a maximum of 1 year deviation.
					# For filtering the century/decade menus, titles should not be out by more than a year.
					range = abs(maximum.get(i) - minimum.get(i))
					if deviation[0] is True: minimum[i] -= min(year, range)
					else: minimum[i] -= range * deviation[0]
					if deviation[1] is True: maximum[i] += min(year, range)
					else: maximum[i] += range * deviation[1]

			result = []
			for item in items:
				value = self.time(type = time, metadata = item, estimate = False)
				media = item.get('media')
				if Media.isSerie(media): media = Media.Show
				elif not Media.isMovie(media): media = Media.Unknown

				if not value: match = 0
				elif value >= minimum.get(media, 0) and value <= maximum.get(media, default): match = matched
				else: match = unmatched
				result.append({'match' : match, 'item' : item})

			if unknown: result = [i['item'] for i in result if i['match'] >= 0]
			else: result = [i['item'] for i in result if i['match'] == 1]

			return result
		except: Logger.error()
		return items

	# Remove items with partial/incomplete metadata.
	# plot: remove items without a plot.
	# poster: remove items without a poster.
	def filterPartial(self, items, plot = True, poster = True):
		try:
			result = []
			for item in items:
				if plot and not item.get('plot'): continue
				if poster and not (item.get(MetaImage.Attribute) or {}).get('poster'): continue
				result.append(item)
			return result
		except: Logger.error()
		return items

	###################################################################
	# SORT
	###################################################################

	# inplace: Sort/reverse list of items in place, otherwise return a shallow copy of the list that is sorted/reversed.
	def sort(self, items, sort = SortNone, order = OrderNone, inplace = False):
		try:
			if items:
				summary = None
				function = None
				ordered = order # Allow the default order to be overwritten by a custom parameter passed in by the user.
				sort, order = self.sortDefault(sort = sort, order = order)
				if not ordered: ordered = order

				if sort == MetaTools.SortShuffle:		return Tools.listShuffle(items)
				elif sort == MetaTools.SortInternal:	function = self._sortInternal
				elif sort == MetaTools.SortGlobal:		function = self._sortGlobal;		summary = True
				elif sort == MetaTools.SortLocal:		function = self._sortLocal;			summary = True
				elif sort == MetaTools.SortRewatch:		function = self._sortRewatch;		summary = True
				elif sort == MetaTools.SortArticle:		function = self._sortArticle
				elif sort == MetaTools.SortArticleless:	function = self._sortArticleless;	summary = True
				elif sort == MetaTools.SortWeighted:	function = self._sortWeighted;		summary = True
				elif sort == MetaTools.SortRating:		function = self._sortRating
				elif sort == MetaTools.SortUser:		function = self._sortUser
				elif sort == MetaTools.SortVotes:		function = self._sortVotes

				elif sort == MetaTools.SortPremiere:	function = self._sortPremiere
				elif sort == MetaTools.SortLimited:		function = self._sortLimited
				elif sort == MetaTools.SortTheatrical:	function = self._sortTheatrical
				elif sort == MetaTools.SortDigital:		function = self._sortDigital
				elif sort == MetaTools.SortPhysical:	function = self._sortPhysical
				elif sort == MetaTools.SortTelevision:	function = self._sortTelevision
				elif sort == MetaTools.SortDebut:		function = self._sortDebut
				elif sort == MetaTools.SortLaunch:		function = self._sortLaunch
				elif sort == MetaTools.SortTheater:		function = self._sortTheater
				elif sort == MetaTools.SortCinema:		function = self._sortCinema
				elif sort == MetaTools.SortHome:		function = self._sortHome
				elif sort == MetaTools.SortAdded:		function = self._sortAdded
				elif sort == MetaTools.SortUpdated:		function = self._sortUpdated
				elif sort == MetaTools.SortWatched:		function = self._sortWatched
				elif sort == MetaTools.SortRewatched:	function = self._sortRewatched
				elif sort == MetaTools.SortPaused:		function = self._sortPaused
				elif sort == MetaTools.SortExpired:		function = self._sortExpired
				elif sort == MetaTools.SortRated:		function = self._sortRated
				elif sort == MetaTools.SortCollected:	function = self._sortCollected
				elif sort == MetaTools.SortUsed:		function = self._sortUsed

				reverse = ordered == MetaTools.OrderDescending
				if function:
					if summary:
						summary = function(metadatas = items)
						items = Tools.listSort(data = items, key = lambda i : function(metadata = i, summary = summary), inplace = inplace, reverse = reverse)
					else:
						items = Tools.listSort(data = items, key = function, inplace = inplace, reverse = reverse)
				elif reverse:
					items = Tools.listReverse(data = items, inplace = inplace)
		except: Logger.error()
		return items

	def sortDefault(self, sort, order = OrderNone, media = None, menu = None):
		default = MetaTools.OrderDefault.get(sort)
		if not default:
			if sort and order: return sort, order
			else: return None, None
		elif Tools.isTuple(default):
			if order: return default[1], MetaTools.OrderAscending if default[0] == MetaTools.OrderDescending else MetaTools.OrderDescending # Take the inverse, eg: allow SortBest + OrderDescending.
			return default[1], (order or default[0])
		else:
			return sort, default

	def _sortInternal(self, metadata = None):
		try:
			value = metadata.get('sort')
			if value is None: value = 0
			elif Tools.isArray(value): value = max(value)
			return value
		except: Logger.error()
		return 0

	def _sortGlobal(self, metadata = None, metadatas = None, summary = None):
		week = 604800
		if metadata:
			try:
				special = 1.0
				media = metadata.get('media')
				movie = Media.isMovie(media)
				serie = Media.isSerie(media)
				rating = self._sortRating(metadata = metadata)
				votes = self._sortVotes(metadata = metadata)
				smart = (metadata.get('smart') or {})
				smartTime = smart.get('time')

				if serie: time = self._sortPremiere(metadata = metadata)
				else: time = self._sortHome(metadata = metadata)

				# If there is only an Unknown time, it means the title is only available on IMDb, but not on other providers (eg: tt31566242, tt30346074).
				# The Unknown time is set based on the REQUEST parameters and will therefore be very inaccurate.
				# Subtract some time in this case, otherwise these (typically uncommon) shows are listed to far at the top, because they are seen as recent releases.
				times = metadata.get('time')
				if times and len(times.keys()) == 1 and MetaTools.TimeUnknown in times: time[0] -= 1814400 # 3 weeks.

				current = summary['time']['current']
				seconds = current - time[0]

				# Boost the votes of new releases, since they had a lot less time to accumlate votes.
				# The smart data is mostly also outdated, still having a low vote count, while the detailed metadata has the new higher vote count.
				# And it might take some time until the smart metadata is updated.
				# Otherwise new releases are pushed down the list too far, simply because they have a low vote count.
				# This then causes the mixed Arrivals menu to have shows far down the list (even page 2+) that are at the top of page 1 of the shows Arrivals menu.
				if not 'trakt' in ((metadata.get('voting') or {}).get('votes') or {}) or seconds < 172800: # NB: Only do this for the basic smart data, but not if we sort detailed metadata. Or for very recent releases
					if seconds > -86400 and seconds < 1209600: # Released in the past 2 weeks or the next 24 hours (for early episode releases or timezone differences).
						# Dune Prophecy had 600 votes (mostly IMDb) the day of premiere, before it actually aired.
						mutiplier = 0
						if votes < 100: mutiplier = 10
						elif votes < 500: mutiplier = 7
						elif votes < 1000: mutiplier = 5
						if mutiplier:
							if seconds > 604800: mutiplier *= 0.5 # 1-2 weeks.
							if serie: mutiplier *= 1.5
							votes = int(mutiplier * votes)

				# There are quite a number of Indian movies listed in Arrivals.
				# Most of these Indian movies have a very high rating (8.0+) and a lot of votes.
				# However, these are not relevant for most non-Hindi-etc speakers and they would probably also rate these titles lower.
				# Reduce the weight of Indian titles and move them further down the list.

				specialCountry = []
				specialLanguage = []
				specialGenre = []
				specialGenreInclude = []
				specialGenreBoost = []
				specialNiche = []
				specialNicheInclude = []
				specialNicheBoost = []

				country = metadata.get('country')
				if country:
					for i in summary['special']['country']:
						try: specialCountry.append(country.index(i))
						except: pass

				language = metadata.get('language')
				if language:
					for i in summary['special']['language']:
						try: specialLanguage.append(language.index(i))
						except: pass

				genre = metadata.get('genre')
				if genre:
					for i in summary['special']['genre']['exclude']:
						try: specialGenre.append(genre.index(i))
						except: pass
					for i in summary['special']['genre']['include']:
						try: specialGenreInclude.append(genre.index(i))
						except: pass
					for i in summary['special']['genre']['boost']:
						try: specialGenreBoost.append(genre.index(i))
						except: pass

				niche = metadata.get('niche')
				if niche:
					for i in summary['special']['niche']['exclude']:
						try: specialNiche.append(niche.index(i))
						except: pass
					for i in summary['special']['niche']['include']:
						try: specialNicheInclude.append(niche.index(i))
						except: pass
					for i in summary['special']['niche']['boost']:
						try: specialNicheBoost.append(niche.index(i))
						except: pass

				if specialCountry:
					specialMinimum = min(specialCountry)
					if specialMinimum == 0: special -= 0.1
					elif specialMinimum == 1: special -= 0.05 if specialLanguage else 0.02
					elif specialLanguage: special -= 0.01
				if specialLanguage:
					specialMinimum = min(specialLanguage)
					if specialMinimum == 0: special -= 0.3
					elif specialMinimum == 1: special -= 0.15
					else: special -= 0.05
					special -= len(specialLanguage) * 0.02
				if specialGenre:
					specialMinimum = min(specialGenre)
					if specialMinimum == 0: special -= 0.15
					elif specialMinimum == 1: special -= 0.02
					else: special -= 0.01
					special -= len(specialGenre) * 0.02
				if specialGenreInclude:
					specialMinimum = min(specialGenreInclude)
					if specialMinimum == 0: special += 0.03
					elif specialMinimum == 1: special += 0.01
					else: special += 0.005
					special += len(specialGenreInclude) * 0.005
				if specialGenreBoost:
					specialMinimum = min(specialGenreBoost)
					if specialMinimum == 0: special += 0.05
					elif specialMinimum == 1: special += 0.02
					else: special += 0.01
					special += len(specialGenreBoost) * 0.01
				if specialNiche: # Do not use the order for niches.
					special -= len(specialNiche) * 0.05
				if specialNicheInclude:
					special += len(specialNiche) * 0.03
				if specialNicheBoost:
					special += len(specialNicheBoost) * 0.05

				# Titles with only a few votes. Typically less-known foreign releases.
				if serie:
					if votes < 10: special -= 0.50
					elif votes < 30: special -= 0.25
					elif votes < 50: special -= 0.15
				else:
					if votes < 20: special -= 0.50
					elif votes < 50: special -= 0.25
					elif votes < 80: special -= 0.15


				# There are many new releases that are only available on IMDb.
				# Often IMDb does not have any episodes listed, or only a single episode somewhere in the first season (eg: S01E49).
				# Trakt/TMDb/TVDb typically do not have these listed at all, or need some time until they pull this in from IMDb. TVDb sometimes has the show listed, but no seasons/episodes.
				#	Eg: tt31566242, tt30346074
				# These shows are typically cheaply produced mini series, with 100-300 votes, Mostly in English and from the US, but there are a few from South Korea, and a bunch in English, but produced by ReelShort and other Chinese outlets.
				# There is no good way of detecting these. But one thing they all seem to have in common, is that they are only listed on IMDb and do not have a duration.
				if serie and not metadata.get('duration') and votes < 1000 and not metadata.get('trakt') and not metadata.get('tmdb') and not metadata.get('tvdb'):
					special -= 0.25

				# Titles in other languages than the user might understand.
				# Only do this if there are few votes, since we might want to keep foreign movies that are very popular (eg: Parasite 2019).
				if language and not language[0] in summary['language']:
					adjust1 = 0.0
					if votes <= 20000 and language[0] in ['ja', 'ko', 'fr', 'es']: adjust1 = 0.02 # Subtract less for languages that are common or make good films. Also allow Japanese anime.
					elif votes < 1000: adjust1 = 0.25
					elif votes < 5000: adjust1 = 0.20
					elif votes < 10000: adjust1 = 0.15
					elif votes < 15000: adjust1 = 0.10
					elif votes < 20000: adjust1 = 0.05

					# Reduce the impact if the show has less seasons.
					# There would obviously be less votes for a show that just aired S01, compared to a show which is already at S05.
					adjust2 = 1.0
					if serie:
						season = metadata.get('season')
						if season == 1: adjust2 = 0.7
						elif season == 2: adjust2 = 0.8
						elif season == 3: adjust2 = 0.9
					else:
						# Recent movies have less votes.
						if seconds > 0:
							if seconds > 2419200: adjust2 = 0.8 # 4 weeks ago.
							elif seconds > 1209600: adjust2 = 0.6 # 2 weeks ago.
							elif seconds > 604800: adjust2 = 0.4 # 1 week ago.
					special -= adjust1 * adjust2

				# Some series have very few votes when released, causing them not to show up on the first page of Arrivals, although they are good shows that should be listed at the top.
				# Eg: Netflix's "American Primeval" had less than 20 votes in the first 2 days. Since it was smart-loaded early on, the updated metadata with a higher vote count was not retrieved over the next few days.
				# If it is a new release published by one of the major networks, increase the rank to force those titles to be moved higher up.
				if niche and seconds < 604800:
					if serie:
						primary = summary['special']['network'][0]
						secondary = summary['special']['network'][1]
						if any(i in primary for i in niche):
							special += 0.2 if seconds < 345600 else 0.1
						elif any(i in secondary for i in niche):
							special += 0.1 if seconds < 345600 else 0.05
					else:
						special += 0.15 if seconds < 345600 else 0.08

				# For new S02+ releases, move them slightly to the back, since they are less important than new S01 releases.
				# Especially long-running shows with eg S32 is irrelevant for the Arrivals menu.
				# S02 and S03, even up to S05, might still be of interest for the Arrivals menu.
				if serie:
					season = metadata.get('season')
					if season:
						if season >= 30: special -= 0.9
						elif season >= 20: special -= 0.7
						elif season >= 10: special -= 0.4
						elif season > 5: special -= 0.2
						elif season > 3: special -= 0.05

				# Titles with no plot or no poster.
				# The value is only available if the item was already smart-loaded.
				if 'complete' in smart and smart['complete'] is False: # Can be None if the premiere date is in the future and might therefore not have all metadata yet.
					adjust1 = 0.0
					adjust2 = 1.0

					# Adjust if the smart-loaded time is long ago, probably indicating that the smart-loaded data is outdated, and that the detailed metadata will have these values.
					if smartTime:
						smartTime = current - smartTime
						if smartTime > 4838400: adjust2 = 0.1 # 8 weeks.
						elif smartTime > 3628800: adjust2 = 0.2 # 6 weeks.
						elif smartTime > 2419200: adjust2 = 0.3 # 4 weeks.
						elif smartTime > 1814400: adjust2 = 0.4 # 3 weeks.
						elif smartTime > 1209600: adjust2 = 0.6 # 2 weeks.
						elif smartTime > 604800: adjust2 = 0.8 # 1 weeks.
					else:
						adjust2 = 0.01

					# Only do this if there are not many votes.
					# Since if there are a lot of votes, but no plot/poster, it probably means that the smart-loaded data is outdated, and that the detailed metadata will have these values.
					if not votes or votes < 10: adjust1 = 4.0
					elif votes < 50: adjust1 = 3.5
					elif votes < 100: adjust1 = 3.0
					elif votes < 200: adjust1 = 2.5
					elif votes < 500: adjust1 = 2.0
					elif votes < 1000: adjust1 = 1.5
					elif votes < 2000: adjust1 = 1.0

					special -= adjust1 * adjust2

				# TV Movies sometimes do not have images.
				# Move it to the back, since this looks ugly, and the movie can't be that important if it does not have any images.
				# NB: Do not just use "if not metadata.get('image'):", since smart-reduced items do not have the "image" attribute. Only do this if the image attribute is available, but all image types are empty.
				# Update: Is not that important anymore, since smart['complete'] is checked above.
				elif 'image' in metadata and (not metadata['image'] or not any(i for i in metadata['image'].values())): special -= 3.0

				# Sometimes there are low-budget movies that only have a premiere date, but never get a home date in the future.
				# Since self._sortHome() above also returns estimated dates, a movie might get listed 3 months after its premiere, although it does not have a home release and is now kind of old.
				# This happens often with Hindi, US low-budget, and TV movies.
				# Reduce their weight, so that they are sorted to the back of the list.
				# Not sure how well this actually works in practice. Might need to be adjusted later on.
				if movie:
					home = self.time(type = MetaTools.TimeHome, metadata = metadata, estimate = False, fallback = MetaTools.TimeCustom, alternative = False, custom = None) # Allow custom dates from MetaManager.release().
					if not home:
						# Prefer the theatrical date, since sometimes the premiere date is 6+ months before the actual theatrical release.
						premiere = self.time(type = MetaTools.TimeTheatrical, metadata = metadata, estimate = False, fallback = [MetaTools.TimeLimited, MetaTools.TimePremiere], alternative = False, custom = False)
						if not premiere: # No date at all.
							if smartTime: special -= 0.2
							else: special -= 0.05 # Not smart-loaded yet and will therefore probably not have a home date yet.
						elif not Media.isTelevision(niche) and not Media.isSpecial(niche) and not Media.isShort(niche): # Many TV movies only have a premiere date.
							if smartTime:
								if smartTime < premiere: # Smart-loaded before the premiere and might therefore not have a home date yet.
									special -= 0.15
								else:
									agePremiere = current - premiere
									if agePremiere > 47336400: special -= 0.9 # Premiered 1.5+ year ago.
									elif agePremiere > 31536000: special -= 0.7 # Premiered 1+ year ago.
									elif agePremiere > 23652000: special -= 0.5 # Premiered 9+ months ago.
									elif agePremiere > 15768000: special -= 0.3 # Premiered 6+ months ago.
									elif agePremiere > 7884000: special -= 0.1 # Premiered 3+ months ago.
							else: # Not smart-loaded yet.
								if language and Language.EnglishCode in language: special -= 0.05
								else: special -= 0.1

				# Increase the rank of titles that appear on a Trakt calendar.
				# For instance, during the Christmas time, there are a LOT of low-budget Christmas cinema and TV movies, most of them listed on IMDb.
				# There are also a lot of crappy Hindi movies, although these are already deranked by country/language above.
				# These movies often have a high rating (6.0 - 8.0), even if they have a low vote count.
				# These movies now clutter the Arrivals menu because they were released very recently, while big blockbusters just a few days older might be far down the list.
				# If the movie is on the Trakt streaming/DVD calendar, assign a higher rank to push them to the top.
				# Trakt has most Hindi and Christmas movies not in the streaming/DVD calendars.
				# Even if Trakt has the digital release date, it might still not appear in the streaming calendar (eg: tt15868638).
				# Not sure what criteria Trakt uses to add titles to the calendars. Maybe vote count, language, etc?
				smartOrigin = smart.get('origin')
				if smartOrigin:
					smartOriginRelease = smartOrigin.get('release') # Only Trakt streaming and DVD calendar.
					smartOriginArrival = smartOrigin.get('arrival') # Trakt new-premiere, streaming, and DVD calendar.
					if movie:
						# Add much, since these are guaranteed to have a home release dates.
						# This value could potentially be increased even further (eg 0.75) if big blockbusters are still too far down the list.
						if smartOriginRelease and MetaTools.ProviderTrakt in smartOriginRelease: special += 0.50

						# Do not add too much, since they include premieres, but could still be more important than the clutter returned by IMDb.
						elif smartOriginArrival and MetaTools.ProviderTrakt in smartOriginArrival: special += 0.05
					else:
						# Do not add too much, since these already appear in the user's Progress menu.
						# The releases only contain new episodes of shows from the user's progress, not any other arrivals the user is not watching.
						# Still increase the rank, to push the user-watched titles up in the Arrivals menu, since those are the ones the user might be more interested in.
						# But do not add too much, since the user will rather use the Progress menu for shows being watched, and probably use the Arrivals menu to discover new unwatched shows.
						if smartOriginRelease and MetaTools.ProviderTrakt in smartOriginRelease: special += 0.15

						# Not too much, since the show calendars form Trakt/TMDb/IMDb are all based on the premiere date, and the Trakt origin does not mean much.
						elif smartOriginArrival and MetaTools.ProviderTrakt in smartOriginArrival: special += 0.05

				# Reduce the votes requirement if there is no IMDb rating.
				# NB: Items not smart-loaded yet, do not have a "voting" dict.
				adjust = 1.0
				try:
					# 3.5 - 5.7% for "Dune Part Two" and "Game of Thrones".
					if not metadata['voting']['votes'].get(MetaTools.ProviderImdb): adjust = 0.06
				except: pass

				voting = self._sortWeighted(metadata = metadata, summary = summary['rating'])
				popularity = min(10, Math.scale(value = votes, fromMinimum = 0, fromMaximum = (50000 * adjust), toMinimum = 0, toMaximum = 10)) # Average popular.

				# Give a big boost to very popular titles.
				# Most titles with this many votes are slightly older releases, since they needed time to accumulate the votes.
				# Keep these more popular titles higher up in the list.
				boost = min(25, Math.scale(value = votes, fromMinimum = 0, fromMaximum = (250000 * adjust), toMinimum = 0, toMaximum = 10)) # Allow more than 10, to give a higher boost than the weight assigned to it below.
				if boost < 7: boost = 0  # Only if they have at least a minimum number of votes.

				# Give a lower weight to titles with few votes.
				# Otherwise a title with a 9.0+ rating, but only a few votes will be ranked too high.
				if voting: voting *= min(1.0, max(0.05, Math.scale(value = votes, fromMinimum = 0, fromMaximum = (2000 * adjust), toMinimum = 0, toMaximum = 1)))

				# Calculate the number of weeks since the title was released.
				# Do this in blocks of weeks, instead of calculating the absolute age in seconds, since it should not matter if one title was released 2 days ago and another 4 days ago.
				age = Math.roundDown(seconds / week)

				# Future releases.
				if age < 0:
					second = abs(seconds)

					# Allow titles that are released within the next 24 hours. Especially shows are sometimes leaked a day before permiere. Plus we want to list shows coming out today, even if the timezone difference places the release in the future by a few hours.
					if second < (86400 if serie else 43200): age = 0.00000001

					# If the title is in the future, reduce the special.
					# Otherwise future items are listed too early on page 2+.
					# Future titles should only appear in the movie Arrivals.
					elif second > 2628000: special = min(0.2, special) # 1+ month.
					elif second > 604800: special = min(0.5, special) # 1 week.
					elif second > 259200: special = min(0.8, special) # 3 days.
					elif second > 86400: special = min(1.0, special) # 1 day.

				if age < 0: age = 0 # Estimated not-yet-released future date.
				else: age = Math.scale(value = age, fromMinimum = summary['time']['minimum'], fromMaximum = summary['time']['maximum'], toMinimum = 0, toMaximum = 10) # Past 10 weeks.

				# This lists newer items too far down: 50% release date + 40% weighted voting + 5% rating + 5% votes.
				# This lists quality items too far down: 80% release date + 14% weighted voting + 3% rating + 3% votes.
				rank = (0.60 * age) + (0.25 * voting) + (0.03 * rating) + (0.08 * popularity) + (0.04 * boost)
				rank *= max(0, special) # Applies this to the total rank, not just the voting part.

				time[0] = rank # Still keep the show title/season/episode at the end of the list.

				return time
			except: Logger.error()
			return [0, MetaTools.DummyString, MetaTools.DummyNumber, MetaTools.DummyNumber]
		else:
			try:
				languages = [self.settingsLanguage()] + Language.settingsCode()
				country = self.settingsCountry()
				if country:
					language = Country.language(country)
					if language: languages.extend(language)
				languages = Tools.listUnique(languages)

				rating = self._sortWeighted(metadatas = metadatas)

				current = Time.timestamp()
				time = []
				for metadata in metadatas:
					# Deprecated - TimeSerie can be removed after 2025-09.
					if Media.isSerie(metadata.get('media')): time.append(self._sortTime(metadata = metadata, type = [MetaTools.TimeCustom, MetaTools.TimeSerie, MetaTools.TimePremiere])[0]) # Use the season date, instead of the show date, if available.
					else: time.append(self._sortHome(metadata = metadata)[0])
				time = [i for i in time if i]

				# Remove outliers from the list, since large outliers cause the deviation other titles' ages to be very small.
				# Eg: Some titles that were released decades ago, might only recently have gotten a digital/physical release.
				# Bloodsport (1988): {'premiere': 572832000, 'limited': None, 'theatrical': 572832000, 'digital': None, 'physical': 1681430400, 'television': None}
				time = Math.outliers(time, threshold = 3)
				if time:
					# Limit to 1 year, since there can be very old releases in the list with a recent BluRay re-release, which skew the scaling making the difference between 1-week and 2-months old releases very small.
					year = current - 31557600
					try: timeMinimum = min([i for i in time if i > year])
					except: timeMinimum = year # Sometimes all are older than a year. Eg: when only a subset of titles are sorted during smart loading.
					try: timeMaximum = max([i for i in time if i < current]) # There can be future releases in the list.
					except: timeMaximum = 0 # Today.
				else:
					timeMinimum = 0
					timeMaximum = 0

				country = []
				language = []
				genreBoost = []
				genreInclude = []
				genreExclude = []
				nicheBoost = []
				nicheInclude = []
				nicheExclude = []

				# Many Indian/Hindi titles on IMDb.
				if not any(i in Language.CodeIndian for i in languages):
					india = Country.code('in')
					indias = Tools.copy(Country.language(india)) # Copy, since we remove English below.
					indias.remove(Language.EnglishCode)
					country.append(india)
					language.extend(indias)

				niches = {
					Media.Docu		: self.settingsContentDocu(),
					Media.Short		: self.settingsContentShort(),
					Media.Family	: self.settingsContentFamily(),
					Media.Anima		: self.settingsContentAnima(),
					Media.Anime		: self.settingsContentAnime(),
					Media.Donghua	: self.settingsContentDonghua(),
				}
				for k, v in niches.items():
					if v >= MetaTools.ContentFrequent: nicheBoost.append(k)
					elif v >= MetaTools.ContentRegular: nicheInclude.append(k)
					elif v <= MetaTools.ContentNever: nicheExclude.append(k)

				# Do not use niche for docus, since we want to allow titles with Documentary as secondary genre.
				if Media.Docu in nicheExclude:
					nicheExclude.remove(Media.Docu)
					genreExclude.append(MetaTools.GenreDocumentary)

				if niches[Media.Anime] >= MetaTools.ContentRegular: languages.extend(['ja'])
				if niches[Media.Donghua] >= MetaTools.ContentRegular: languages.extend(['zh', 'ug', 'za', 'chi', 'zho', 'zt', 'zht', 'zht', 'ze', 'zhe', 'zhe'])

				genreExclude.append(MetaTools.GenreNews)
				nicheExclude.append(Media.Soap)

				network = [
					[MetaCompany.CompanyAmazon, MetaCompany.CompanyApple, MetaCompany.CompanyDisney, MetaCompany.CompanyFox, MetaCompany.CompanyFx, MetaCompany.CompanyHbo, MetaCompany.CompanyHulu, MetaCompany.CompanyNetflix, MetaCompany.CompanyParamount, MetaCompany.CompanyPeacock],
					[MetaCompany.CompanyAbc, MetaCompany.CompanyAe, MetaCompany.CompanyAmc, MetaCompany.CompanyBbc, MetaCompany.CompanyCbs, MetaCompany.CompanyChannel4, MetaCompany.CompanyCw, MetaCompany.CompanyDiscovery, MetaCompany.CompanyHistory, MetaCompany.CompanyItv, MetaCompany.CompanyMgm, MetaCompany.CompanyNbc, MetaCompany.CompanyShowtime, MetaCompany.CompanySky, MetaCompany.CompanySony, MetaCompany.CompanyStarz, MetaCompany.CompanySyfy, MetaCompany.CompanyTbs, MetaCompany.CompanyTnt, MetaCompany.CompanyUsa],
				]

				return {
					'language' : languages,
					'rating' : rating,
					'time' : {
						'current' : current,
						'minimum' : Math.roundUp((current - timeMinimum) / week),
						'maximum' : Math.roundDown((current - timeMaximum) / week),
					},
					'special' : {
						'country' : country,
						'language' : language,
						'network' : network,
						'genre' : {
							'boost' : genreBoost,
							'include' : genreInclude,
							'exclude' : genreExclude,
						},
						'niche' : {
							'boost' : nicheBoost,
							'include' : nicheInclude,
							'exclude' : nicheExclude,
						},
					},
				}
			except: Logger.error()
			return None

	def _sortLocal(self, metadata = None, metadatas = None, summary = None):
		if metadata:
			try:
				default = 315569520
				value = [default, default, default]
				current = summary['time']
				time = self._sortLaunch(metadata = metadata)

				progress = metadata.get('progress')
				launch = self.time(metadata = metadata, type = MetaTools.TimeLaunch)

				# Also allow scrobble progress time for unfinished titles.
				age = default
				aged = 0.99999999
				used = None
				used1 = self.time(metadata = metadata, estimate = False, fallback = False, type = MetaTools.SortWatched)
				used2 = self.time(metadata = metadata, estimate = False, fallback = False, type = MetaTools.SortPaused)
				if used1 and used2: used = max(used1, used2)
				else: used = used1 or used2
				if not used:
					for i in [MetaTools.SortRewatched, MetaTools.SortRated, MetaTools.SortCollected]:
						used = self.time(metadata = metadata, estimate = False, fallback = False, type = i)
						if used: break

				if used:
					age = current - used
					aged = age / float(1000000000.0) # Devide by large enough number that long ages (eg 10 years) can be accomodated.

					if age < self.mSleepyDuration: value[0] = age # Always place titles that were watched in the past 3 days right at the top.
					elif age < (self.mSleepyDuration * 2.5): value[0] -= ((self.mSleepyDuration * 2.5) - age) # Place titles that were watched in the past week closer to the top, but not too much. Useful if the user want to rewatch episodes.
					elif age < (self.mSleepyDuration * 10): value[1] = age # Place titles that were watched in the past month closer to the top, but not too much.

					value[2] = age

				if Media.isSerie(metadata.get('media')):
					smart = (metadata.get('smart') or {})
					next = smart.get('next') if smart else None
					nextTime = next.get('time') if next else None

					# Place shows with a recent release of a new season close to the top.
					release = Tools.get(smart, 'pack', 'time', 'season')
					if release:
						past = True
						released = []
						unreleased = []
						for i in release:
							if i and i[0]:
								seconds = current - i[0]
								if seconds >= 0: released.append(seconds)
								else: unreleased.append(seconds)

						# Also add the next episodes time, but only if SxxE01.
						# Should be the same as the one from the pack, but this one can be newer if the pack metadata is outdated.
						if nextTime and metadata.get('episode') == 1:
							seconds = current - nextTime
							if seconds >= 0: released.append(seconds)
							else: unreleased.append(seconds)

						released = min(released) if released else None
						unreleased = abs(min(unreleased)) if unreleased else None

						# Already released season closest to today.
						if released:
							if released < 259200: value[0] = min(value[0], int(released / 5.0)) # Place new seasons released the past 3 days way at the top.
							elif released < 604800: value[0] = min(value[0], int(released / 2.0)) # Place new seasons released the past 7 days at the top, maybe even before the recentley watched.
							elif released < 1209600: value[0] = min(value[0], released) # Place new seasons released the past 2 weeks closer to the top.
							elif released < 2629800: value[1] -= (2629800 - released) # Place new seasons released the past 4 weeks closer to the top.
							elif released < 7889400: value[2] = min(value[2], released) # Move new seasons released the past 3 months closer to the top.
							else: past = False
						else: past = False

						# Soon to be released season closest to today.
						# Only do this if there is no recently released season, since a show can have both a recently released season and a future season.
						if not past and unreleased:
							if unreleased < 86400: value[1] = min(value[1], unreleased) # Place seasons to be released in the next day closer to the top.
							elif unreleased < 259200: value[2] = min(value[2], unreleased) # Place seasons to be released in the next 3 days closer to the top.
							elif unreleased > 1209600: value[1] += unreleased # Move unreleased seasons far down the list.

					# Move episodes that are released far into the future down the list.
					# Only do this if the previous episode was watched a long time ago, which assumes the user does not want to rewatch any of the old episodes.
					# If all episodes of a show were watched, leave it at the top for longer, since the user might want to rewatch some episodes.
					# First try to use the next episodes time if available. This is during the initial sorting PRIOR to the paging, where the detailed metadata is still from the previous (last watched) episode, and not the incremented one.
					launched = nextTime or launch
					if launched and (launched - current) > 604800:
						if age < 86400: value[0] += age
						elif age < 259200: value[0] += (age * 2)
						else: value[0] = MetaTools.DummyNumber

					# Fully watched shows are not removed from the list anymore.
					# Otherwise niche Progress menus might have very few items.
					# Instead, move those episodes to the end.
					# Do this after all the other values were set.
					if next is False:
						# Only increase a little for recently finished shows, in case the user wants to rewatch an episode.
						if age < 86400: value[0] += age
						elif age < 259200: value[0] += (age * 2)
						else: value[0] += MetaTools.DummyNumber

				else:
					# Place "Partial" items first, followed by "Started", followed by "Finished", followed by others without progress.
					# Use weird numbers to allow sorting movies and shows together.
					if progress is None: value[1] = MetaTools.DummyNumber
					elif progress >= summary['end']: value[2] -= max(1, 2678400 - age)
					elif progress <= summary['start']: value[1] -= max(1, 1209600 - age)
					else: value[1] = age

					# "aged" is calculated with either the watched or scrobble date.
					# Boost the ones with a scrobble date (unfinished) over those with a watched date (finished).
					# Check progress, since finished titles can have a value for used2.
					if used2 and progress and progress <= summary['end']: aged /= 15

				# aged:
				#	At the same level, if the value is the same, prefer the one with a more recent used time.
				#	This only adds a decimal fraction to each value, and will not change the order for the integer part.
				# DummyNumber:
				#	Make sure that descending sorting will list the latests ones first.
				#	Since "Global Relevance" and other sorting methods are by default Descending, and we do not want to confuse the user by making "Local Relevance" Ascending.
				value = [MetaTools.DummyNumber - (i + aged) for i in value]
				return value + time
			except: Logger.error()
			return value + [MetaTools.DummyTime, MetaTools.DummyString, MetaTools.DummyNumber, MetaTools.DummyNumber]
		else:
			try:
				from lib.modules.playback import Playback
				return {'time' : Time.timestamp(), 'start' : Playback.percentStart(), 'end' : Playback.percentEnd()}
			except: Logger.error()
			return None

	def _sortRewatch(self, metadata = None, metadatas = None, summary = None):
		if metadata:
			try:
				rating = self._sortUser(metadata = metadata)
				if not rating:
					rating = self._sortRating(metadata = metadata) # In case the user did not rate the title.
					if rating: rating *= 0.8
					else: rating = 5.0

				# Do not use fallback times (eg: theatrical) if the rewatched/watched time is not available.
				time = self._sortRewatched(metadata = metadata, fallback = False)
				if time and time[0] > MetaTools.DummyTime:
					time = time[0]
				else:
					time = self._sortWatched(metadata = metadata, fallback = False)
					if time and time[0] > MetaTools.DummyTime:
						time = time[0]
					else:
						time = self._sortUpdated(metadata = metadata, fallback = False)
						if time and time[0] > MetaTools.DummyTime:
							time = time[0]
						else:
							time = summary['time']
				age = summary['time'] - time
				if age < 0: age = 0
				else: age = Math.scale(value = age, fromMinimum = 0, fromMaximum = 315569520, toMinimum = 0, toMaximum = 10)

				relevance = (rating * 0.25) + (age * 0.75)

				if rating < 5.0: relevance *= 0.2
				elif rating < 7.0: relevance *= 0.5
				elif rating >= 10.0: relevance *= 1.3
				elif rating >= 9.0: relevance *= 1.1

				if age < 1.0: relevance *= 0.2 # 1 year.
				elif age < 2.0: relevance *= 0.5 # 2 years.
				elif age >= 10.0: relevance *= 1.3 # 10 years.
				elif age >= 8.0: relevance *= 1.2 # 8 years.
				elif age >= 5.0: relevance *= 1.1 # 5 years.

				return relevance
			except: Logger.error()
			return 0
		else:
			try: return {'time' : Time.timestamp()}
			except: Logger.error()
			return None

	def _sortArticle(self, metadata = None):
		try:
			title = metadata.get('tvshowtitle') or metadata.get('title') or metadata.get('originaltitle') or metadata.get('sorttitle')
			if title: return title.lower().strip()
		except: Logger.error()
		return MetaTools.DummyString

	def _sortArticleless(self, metadata = None, metadatas = None, summary = None):
		if metadata:
			try:
				title = metadata.get('tvshowtitle') or metadata.get('title') or metadata.get('originaltitle') or metadata.get('sorttitle')
				if title:
					title = title.lower().strip()
					if summary: title = Regex.remove(data = title, expression = summary, group = 1)
					return title
			except: Logger.error()
			return MetaTools.DummyString
		else:
			try:
				if self.mSettingsLanguage == 'de': return '^((?:de[nmrs]|die|das|ein(?:e[nmrs])?|dies(?:e[nmrs])?)\s)'
				elif self.mSettingsLanguage == 'fr': return '^((?:l[ae]|les|une?|d[eu](?:\sl[ae])?|des|)\s|(?:l[\'\’\‘]|d[eu](?:\sl[\'\’\‘])))'
				elif self.mSettingsLanguage == 'nl': return '^((?:de|het|een)\s)'
				elif self.mSettingsLanguage == 'es': return '^((?:l[ao]s?|el|un[ao]?s?)\s)'
				elif self.mSettingsLanguage == 'pt': return '^((?:[ao]s?|uma?s?|uns)\s)'
				elif self.mSettingsLanguage == 'it': return '^((?:il?|gil|l[aeo]|un[ao]?)\s|l[\'\’\‘])'
				else: return '^((?:the|an?)\s)'
			except: Logger.error()
			return None

	def _sortWeighted(self, metadata = None, metadatas = None, summary = None):
		if metadata:
			try: return self.votingBayesian(metadata = metadata, rating = summary)
			except: Logger.error()
			return 0.0
		else:
			try:
				voting = [self.voting(metadata = metadata) for metadata in metadatas]
				voting = [i['rating'] for i in voting if i]
				if voting: return Tools.listMean(voting)
			except: Logger.error()
			return 7.0

	def _sortRating(self, metadata = None):
		try:
			result = metadata.get('rating')
			if not result:
				voting = self.voting(metadata = metadata)
				if voting: return voting['rating']
			return result or 0.0
		except: Logger.error()
		return 0.0

	def _sortVotes(self, metadata = None):
		try:
			result = metadata.get('votes')
			if not result:
				voting = self.voting(metadata = metadata)
				if voting: return voting['votes']
			return result or 0
		except: Logger.error()
		return 0

	def _sortUser(self, metadata = None):
		try:
			result = metadata.get('userrating')

			if not result:
				rating = []

				voting = metadata.get('voting')
				if voting:
					user = voting.get('user')
					if user:
						for provider in MetaTools.RatingProviders:
							rated = user.get(provider)
							if rated: rating.append(rated)

				if not rating:
					temp = metadata.get('temp')
					if temp:
						for provider in MetaTools.RatingProviders:
							tempProvider = temp.get(provider)
							if tempProvider:
								rated = tempProvider.get('voting', {}).get('user')
								if rated: rating.append(rated)

				if rating: result = sum(rating) / float(len(rating))

			return result or 0.0
		except: Logger.error()
		return 0.0

	def _sortTime(self, metadata = None, type = None, estimate = True, fallback = True):
		try:
			default = self.timeDefault(metadata = metadata) if fallback else None
			if type and Tools.isArray(type):
				time = None
				if not Tools.isArray(type[0]): type = [type]
				for i in type:
					# Do not use estimate or fallback here, since it will use launch dates when Trakt dates are requested from _sortUsed().
					# Do this at the end of the loop.
					times = [self.time(type = j, metadata = metadata, default = default, estimate = False, fallback = False) for j in i]
					if times:
						times = [j for j in times if not j is None]
						if times:
							time = max(times)
							break
				if not time and fallback: time = self.time(type = None, metadata = metadata, default = default, estimate = estimate, fallback = fallback)
			else:
				time = self.time(type = type, metadata = metadata, default = default, estimate = estimate, fallback = fallback)

			if time is None: time = MetaTools.DummyTime

			# Add the season and episode numbers.
			# This is especially important for "premiered" sorting of Trakt calendars.
			# All episodes of a show might be released on the same day and then they are listed in random order.
			# Adding the season/episode numbers first sorts by date, and then makes sure episodes from the same show are listed sequentially.
			# Always add these, even for movies, in case we have a mixed movie-show list.
			return [time, metadata.get('tvshowtitle') or MetaTools.DummyString, metadata.get('season') or MetaTools.DummyNumber, metadata.get('episode') or MetaTools.DummyNumber]
		except: Logger.error()
		return [MetaTools.DummyTime, MetaTools.DummyString, MetaTools.DummyNumber, MetaTools.DummyNumber]

	def _sortPremiere(self, metadata = None, estimate = True, fallback = True):
		return self._sortTime(metadata = metadata, estimate = estimate, fallback = fallback, type = MetaTools.SortPremiere)

	def _sortLimited(self, metadata = None, estimate = True, fallback = True):
		return self._sortTime(metadata = metadata, estimate = estimate, fallback = fallback, type = MetaTools.SortLimited)

	def _sortTheatrical(self, metadata = None, estimate = True, fallback = True):
		return self._sortTime(metadata = metadata, estimate = estimate, fallback = fallback, type = MetaTools.SortTheatrical)

	def _sortDigital(self, metadata = None, estimate = True, fallback = True):
		return self._sortTime(metadata = metadata, estimate = estimate, fallback = fallback, type = MetaTools.SortDigital)

	def _sortPhysical(self, metadata = None, estimate = True, fallback = True):
		return self._sortTime(metadata = metadata, estimate = estimate, fallback = fallback, type = MetaTools.SortPhysical)

	def _sortTelevision(self, metadata = None, estimate = True, fallback = True):
		return self._sortTime(metadata = metadata, estimate = estimate, fallback = fallback, type = MetaTools.SortTelevision)

	def _sortDebut(self, metadata = None, estimate = True, fallback = True):
		return self._sortTime(metadata = metadata, estimate = estimate, fallback = fallback, type = MetaTools.SortDebut)

	def _sortTheater(self, metadata = None, estimate = True, fallback = True):
		return self._sortTime(metadata = metadata, estimate = estimate, fallback = fallback, type = MetaTools.SortTheater)

	def _sortCinema(self, metadata = None, estimate = True, fallback = True):
		return self._sortTime(metadata = metadata, estimate = estimate, fallback = fallback, type = MetaTools.SortCinema)

	def _sortLaunch(self, metadata = None, estimate = True, fallback = True):
		return self._sortTime(metadata = metadata, estimate = estimate, fallback = fallback, type = MetaTools.SortLaunch)

	def _sortHome(self, metadata = None, estimate = True, fallback = True):
		return self._sortTime(metadata = metadata, estimate = estimate, fallback = fallback, type = MetaTools.SortHome)

	def _sortAdded(self, metadata = None, estimate = True, fallback = True):
		return self._sortTime(metadata = metadata, estimate = estimate, fallback = fallback, type = MetaTools.SortAdded)

	def _sortUpdated(self, metadata = None, estimate = True, fallback = True):
		return self._sortTime(metadata = metadata, estimate = estimate, fallback = fallback, type = MetaTools.SortUpdated)

	def _sortWatched(self, metadata = None, estimate = True, fallback = True):
		return self._sortTime(metadata = metadata, estimate = estimate, fallback = fallback, type = MetaTools.SortWatched)

	def _sortRewatched(self, metadata = None, estimate = True, fallback = True):
		return self._sortTime(metadata = metadata, estimate = estimate, fallback = fallback, type = MetaTools.SortRewatched)

	def _sortPaused(self, metadata = None, estimate = True, fallback = True):
		return self._sortTime(metadata = metadata, estimate = estimate, fallback = fallback, type = MetaTools.SortPaused)

	def _sortExpired(self, metadata = None, estimate = True, fallback = True):
		return self._sortTime(metadata = metadata, estimate = estimate, fallback = fallback, type = MetaTools.SortExpired)

	def _sortRated(self, metadata = None, estimate = True, fallback = True):
		return self._sortTime(metadata = metadata, estimate = estimate, fallback = fallback, type = MetaTools.SortRated)

	def _sortCollected(self, metadata = None, estimate = True, fallback = True):
		return self._sortTime(metadata = metadata, estimate = estimate, fallback = fallback, type = MetaTools.SortCollected)

	def _sortUsed(self, metadata = None, estimate = True, fallback = True):
		# First try the dates that are directly linked to the user activity.
		# Only if none of those dates are found, use added/updated, since these dates might be for something else, like list added/updated dates.
		type = [
			[MetaTools.SortWatched, MetaTools.SortRewatched, MetaTools.SortPaused, MetaTools.SortRated, MetaTools.SortCollected],
			[MetaTools.SortAdded, MetaTools.SortUpdated],
		]
		return self._sortTime(metadata = metadata, estimate = estimate, fallback = fallback, type = type)

	###################################################################
	# INDEX
	###################################################################

	def index(self, items, item, number = False, default = None):
		try:
			ids = self.indexId(item = item, number = number)
			for i in range(len(items)):
				id = self.indexId(item = items[i], number = number)
				if any(j in ids for j in id.keys()): return i
		except: Logger.error()
		return default

	def indexId(self, item, number = False):
		ids = {}
		if Tools.isList(item): item = item[0] # From MetaManager.metadata() if a season/episode is retrieved, a list of season/episodes is returned, instead of a single item.
		for i in [MetaTools.ProviderImdb, MetaTools.ProviderTmdb, MetaTools.ProviderTvdb, MetaTools.ProviderTrakt]:
			id = (item.get('id') or {}).get(i)
			if id:
				if number:
					try: season = str(item['season'])
					except: season = 'z'
					try: episode = str(item['episode'])
					except: episode = 'z'
					id = '%s_%s_%s_%s' % (str(item.get('media')), id, season, episode)
				ids[id] = True
		return ids

	###################################################################
	# ID
	###################################################################

	@classmethod
	def _idCache(self, function, **kwargs):
		# Do not cache this call for very long (eg: 1 week).
		# The ID lookup might not return any results (eg: new released movie not on Trakt yet), and we do not want to wait that long before retrying the lookup (hoping Trakt has added it by then).
		# Shorter cache times should not be a massive performance issue, since this should mainly be called when downloading detailed metadata from MetaManager.
		# Do not cache long and then delete the cache entry on failed lookups, since this would redo the lookup multiple times a day, even though it always returns the same incomplete/failed results.
		return Cache.instance().cache(None, Cache.TimeoutDay1, None, function, **kwargs)

	@classmethod
	def _idCacheRetrieve(self, function, **kwargs):
		return Cache.instance().cacheRetrieve(function, **kwargs)

	@classmethod
	def _idValidate(self, result, imdb = None, tmdb = None, tvdb = None, trakt = None):
		# There can sometimes be an incorrect ID lookup.
		# Especially the IMDb IDs for new releases can be wrong, for one of these reasons:
		#	1. The title is added to IMDb twice, and one later gets removed. Trakt/TMDb might still point to the old ID for a while.
		#	2. The title on IMDb gets moved at a later point, getting a new IMDb ID. Trakt/TMDb might need some time until they detect it.
		#	3. The wrong IMDb ID might be on Trakt/TMDb and it might need some time until they fix it.
		#	4. If the IDs cannot be looked-up at all, it will fall back to title+year lookup, which might also return the incorrect value, since Trakt/TMDb returns the "best" result, not neccessarily the correct result.
		# Then in MetaManager._metadataMovieUpdate() when _metadataMovieId() is called, one IMDb ID is passed in for the lookup, but the function returns a different IMDb ID as result.
		# This can cause two titles with the same IMDb (but different other IDs) to be added to MetaCache.
		# If we then retrieve the metadata from MetaCache using the IMDb ID for the query, it might return the incorrect title.
		# This then causes the metadata to be retrieved in the foreground every time the New Releases menu is opened (although the menu should already be cached), because saving the metadata to MetaCache overwrites some of the IDs, invalidating the next lookup.
		# Not a huge issue, since eventually the metadata will be refreshed, hopefully pulling in the new/correct IDs.
		# This is very difficult to debug, since if we detect this a few days later, it might be impossible to replicate the problem, since by that time Trakt/TMDb/IMDb probably already fixed the issue.
		# But to avoid this, we always compare the IDs passed into this function with the looked-up IDs. If they are different we assume it is an incorrect lookup and we do not use the results.

		if result:
			if imdb:
				lookup = result.get('imdb')
				if lookup and not lookup == imdb: return None
			if tmdb:
				lookup = result.get('tmdb')
				if lookup and not lookup == tmdb: return None
			if tvdb:
				lookup = result.get('tvdb')
				if lookup and not lookup == tvdb: return None
			if trakt:
				lookup = result.get('trakt')
				if lookup and not lookup == trakt: return None

		return result

	@classmethod
	def id(self, media, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, deviation = True, cache = True, extra = False, extended = False, quick = None):
		if media == Media.Set: return self.idSet(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, deviation = deviation, cache = cache, extra = extra, extended = extended)
		elif Media.isSerie(media): return self.idShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, deviation = deviation, cache = cache, extra = extra, quick = quick)
		else: return self.idMovie(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, deviation = deviation, cache = cache, extra = extra, quick = quick)

	@classmethod
	def idMovie(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, deviation = True, cache = True, extra = False, validate = True, quick = None):
		if cache:
			result = None

			# Try without the "quick" parameter to retrieve whatever is in the cache.
			if quick:
				if not result and imdb: result = self._idCacheRetrieve(function = self.idMovie, imdb = imdb, extra = extra, validate = validate, quick = None, cache = False)
				if not result and tmdb: result = self._idCacheRetrieve(function = self.idMovie, tmdb = tmdb, extra = extra, validate = validate, quick = None, cache = False)
				if not result and trakt: result = self._idCacheRetrieve(function = self.idMovie, trakt = trakt, extra = extra, validate = validate, quick = None, cache = False)
				if not result and tvdb: result = self._idCacheRetrieve(function = self.idMovie, tvdb = tvdb, extra = extra, validate = validate, quick = None, cache = False)

			# Do these separately, otherwise if this function is called with different ID-combination, it will not use the cached result.
			# Eg: the function is called 1st with only an IMDb ID, and a 2nd time with an IMDb and TMDb ID.
			if not result and imdb: result = self._idCache(function = self.idMovie, imdb = imdb, extra = extra, validate = validate, quick = quick, cache = False)
			if not result and tmdb: result = self._idCache(function = self.idMovie, tmdb = tmdb, extra = extra, validate = validate, quick = quick, cache = False)
			if not result and trakt: result = self._idCache(function = self.idMovie, trakt = trakt, extra = extra, validate = validate, quick = quick, cache = False)
			if not result and tvdb: result = self._idCache(function = self.idMovie, tvdb = tvdb, extra = extra, validate = validate, quick = quick, cache = False)

			# Only do this if no IDs are available.
			# If there are IDs, but Trakt and TMDb did not return any results for them, it means this is probably a new release that is not on Trakt/TMDb.
			# In this case, looking up by title will unnecessarily prolong the call, and will probably return the incorrect results in any case, since it is not on Trakt/TMDb and they will return the "best" match they can find.
			if not result and title and not imdb and not tmdb and not tvdb and not trakt: result = self._idCache(function = self.idMovie, title = title, year = year, deviation = deviation, extra = extra, validate = validate, quick = quick, cache = False)

			# Validate here, not at the end of the function.
			# Because the cached function calls only get one ID passed in at a time, and a proper validation is therefore not possible within the cached call.
			if validate: result = self._idValidate(result = result, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt)

			return result

		result = {}
		lookup = False

		# TMDb ID lookups are twice as fast as Trakt ID lookups.
		if quick:
			if quick is True: quick = {'tmdb' : True}
			elif Tools.isString(quick): quick = {quick : True}
		else:
			quick = {'trakt' : True, 'tmdb' : True}

		# Search Trakt by ID.
		try:
			if quick.get('trakt'):
				if not result or not 'imdb' in result or not result['imdb']:
					if imdb or tmdb or tvdb or trakt:
						from lib.modules import trakt as Trakt
						lookup = True
						data = Trakt.SearchMovie(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, single = True, full = extra, cache = False)
						if data and 'movie' in data:
							ids = data['movie'].get('ids')
							if ids:
								ids = {k : str(v) for k, v in ids.items() if v}
								if ids:
									Tools.update(result, ids, none = False)
									if extra: Tools.update(result, {'title' : data['movie'].get('title'), 'year' : data['movie'].get('year'), 'score' : data.get('score'), 'rating' : data['movie'].get('rating'), 'votes' : data['movie'].get('votes'), 'comments' : data['movie'].get('comment_count')}, none = False)
		except: Logger.error()

		# Search TMDb by ID.
		# Do this after Trakt, since it only returns the IMDb/TMDb ID.
		try:
			if quick.get('tmdb'):
				if not result or not 'imdb' in result or not result['imdb']:
					if imdb or tmdb:
						from lib.modules.account import Tmdb
						key = Tmdb.instance().key()
						lookup = True
						if tmdb:
							link = 'https://api.themoviedb.org/3/movie/%s/external_ids' % tmdb
							data = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key})
							if data:
								id = data.get('imdb_id')
								if id:
									Tools.update(result, {'imdb' : id}, none = False)
									if extra: Tools.update(result, {'score' : data.get('popularity'), 'rating' : data.get('vote_average'), 'votes' : data.get('vote_count')}, none = False)
						elif imdb:
							link = 'https://api.themoviedb.org/3/find/%s' % imdb
							data = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key, 'external_source' : 'imdb_id'})
							if data and 'movie_results' in data and data['movie_results']:
								id = data['movie_results'][0].get('id')
								if id:
									Tools.update(result, {'tmdb' : id}, none = False)
									if extra:
										data2 = data['movie_results'][0]
										release = None
										if 'release_date' in data2:
											release = Regex.extract(data = data2['release_date'], expression = '(\d{4})-', group = 1)
											release = int(release) if release else None
										Tools.update(result, {'title' : data2.get('title'), 'year' : release, 'score' : data2.get('popularity'), 'rating' : data2.get('vote_average'), 'votes' : data2.get('vote_count')}, none = False)
		except: Logger.error()

		if not lookup and title:

			# Search Trakt by title.
			try:
				if quick.get('trakt'):
					if not result or not 'imdb' in result or not result['imdb']:
						from lib.modules import trakt as Trakt
						data = Trakt.SearchMovie(title = title, year = year, single = True, full = extra, cache = False)
						if not(data and 'movie' in data and data['movie']) and deviation and year: data = Trakt.SearchMovie(title = title, year = [int(year) - 1, int(year) + 1], single = True, full = extra, cache = False)
						if data and 'movie' in data:
							ids = data['movie'].get('ids')
							if ids:
								result = {}
								ids = {k : str(v) for k, v in ids.items() if v}
								if ids:
									Tools.update(result, ids, none = False)
									if extra: Tools.update(result, {'title' : data.get('title'), 'year' : data.get('year'), 'score' : data.get('score'), 'rating' : data['movie'].get('rating'), 'votes' : data['movie'].get('votes'), 'comments' : data['movie'].get('comment_count')}, none = False)
			except: Logger.error()

			# Search TMDb by title.
			# Do this after Trakt, since it only returns the IMDb ID.
			try:
				if quick.get('tmdb'):
					if not result or not 'imdb' in result or not result['imdb']:
						from lib.modules.account import Tmdb
						key = Tmdb.instance().key()
						query = self.cleanTitle(title)
						yearDeviated = year
						link = 'https://api.themoviedb.org/3/search/movie'

						data = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key, 'query' : query, 'year' : year})
						if not(data and 'results' in data and data['results']) and deviation and year:
							yearDeviated = int(year) + 1
							data = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key, 'query' : query, 'year' : yearDeviated})
							if not(data and 'results' in data and data['results']) and deviation and year:
								yearDeviated = int(year) - 1
								data = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key, 'query' : query, 'year' : yearDeviated})

						if data and 'results' in data:
							data = data['results']
							for i in data:
								if (query == self.cleanTitle(i['title']) or query == self.cleanTitle(i['original_title'])):
									release = None
									if 'release_date' in i:
										release = Regex.extract(data = i['release_date'], expression = '(\d{4})-', group = 1)
										release = int(release) if release else None
									if not year or yearDeviated == release:
										link = 'https://api.themoviedb.org/3/movie/%s/external_ids' % str(i['id'])
										data2 = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key})
										if data2:
											id = data2.get('imdb_id')
											if id:
												Tools.update(result, {'imdb' : id, 'tmdb' : str(data2.get('id'))}, none = False)
												if extra: Tools.update(result, {'title' : i.get('title'), 'year' : release, 'score' : i.get('popularity'), 'rating' : i.get('vote_average'), 'votes' : i.get('vote_count')}, none = False)
										break
			except: Logger.error()

		# This only works for non-cached calls.
		if validate and not cache: result = self._idValidate(result = result, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt)

		return result if result else None

	@classmethod
	def idSet(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, deviation = True, cache = True, extra = False, extended = False, validate = True):
		if cache:
			result = None
			if not result and title: result = self._idCache(function = self.idSet, title = title, year = year, deviation = deviation, extra = extra, extended = extended, validate = validate, cache = False)
			if validate: result = self._idValidate(result = result, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt)
			return result

		result = {}
		lookup = False
		prefix = 'the '
		suffix = ' collection'
		if not lookup and title:

			# Search TMDb by title.
			try:
				if not result or not 'tmdb' in result or not result['tmdb']:
					from lib.modules.account import Tmdb
					key = Tmdb.instance().key()
					query = self.cleanTitle(title)

					link = 'https://api.themoviedb.org/3/search/collection'
					data = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key, 'query' : query})

					# Searching "The Harry Potter Collection" does not return anything, but "Harry Potter Collection" does return.
					if data and 'results' in data and not data['results'] and query.startswith(prefix):
						data = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key, 'query' : Tools.stringRemovePrefix(data = query, remove = prefix)})

					if data and 'results' in data:
						data = data['results']
						query = Tools.stringRemoveAffix(data = query, prefix = prefix, suffix = suffix)

						# Find exact match.
						for i in data:
							if query == Tools.stringRemoveAffix(data = self.cleanTitle(i['name']), prefix = prefix, suffix = suffix):
								id = i.get('id')
								if id:
									Tools.update(result, {'tmdb' : str(id)}, none = False)
									if extra: Tools.update(result, {'title' : i.get('name'), 'score' : i.get('popularity'), 'rating' : i.get('vote_average'), 'votes' : i.get('vote_count')}, none = False)
									break

						# Find closest match.
						if not result:
							from lib.modules.tools import Matcher
							matches = []
							for i in data:
								if i.get('id'):
									match = Matcher.levenshtein(title, i['name'], ignoreCase = True, ignoreSpace = True, ignoreNumeric = False, ignoreSymbol = True)
									matches.append((match, i))
							if matches:
								matches = Tools.listSort(matches, key = lambda x : x[0])
								i = matches[-1][1]
								if i:
									Tools.update(result, {'tmdb' : str(i.get('id'))}, none = False)
									if extra: Tools.update(result, {'title' : i.get('name'), 'score' : i.get('popularity'), 'rating' : i.get('vote_average'), 'votes' : i.get('vote_count')}, none = False)
			except: Logger.error()

		# Search for the movie title that is part of the collection, instead of searching the collection name.
		if not result and extended and title:
			try:
				if not result or not 'imdb' in result or not result['imdb']:
					from lib.modules.account import Tmdb
					key = Tmdb.instance().key()
					query = self.cleanTitle(title)
					yearDeviated = year
					link = 'https://api.themoviedb.org/3/search/movie'

					data = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key, 'query' : query, 'year' : year})
					if not(data and 'results' in data and data['results']) and deviation and year:
						yearDeviated = int(year) + 1
						data = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key, 'query' : query, 'year' : yearDeviated})
						if not(data and 'results' in data and data['results']) and deviation and year:
							yearDeviated = int(year) - 1
							data = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key, 'query' : query, 'year' : yearDeviated})

					if data and 'results' in data:
						data = data['results']
						for i in data:
							if (query == self.cleanTitle(i['title']) or query == self.cleanTitle(i['original_title'])):
								id = i['id']
								if id:
									link = 'https://api.themoviedb.org/3/movie/%s' % id
									data2 = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key})
									if data2 and 'belongs_to_collection' in data2 and data2['belongs_to_collection']:
										id = data2['belongs_to_collection']['id']
										if id:
											link = 'https://api.themoviedb.org/3/collection/%s' % id
											data3 = Networker().requestJson(method = Networker.MethodGet, link = link, data = {'api_key' : key})
											if data3:
												Tools.update(result, {'tmdb' : str(data3.get('id'))}, none = False)
												if extra: Tools.update(result, {'title' : data3.get('name'), 'score' : data3.get('popularity'), 'rating' : data3.get('vote_average'), 'votes' : data3.get('vote_count')}, none = False)
											break
			except: Logger.error()

		# This only works for non-cached calls.
		if validate and not cache: result = self._idValidate(result = result, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt)

		return result if result else None

	@classmethod
	def idShow(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, deviation = True, cache = True, extra = False, validate = True, quick = None):
		if cache:
			result = None

			# Try without the "quick" parameter to retrieve whatever is in the cache.
			if quick:
				if not result and imdb: result = self._idCacheRetrieve(function = self.idShow, imdb = imdb, extra = extra, validate = validate, quick = None, cache = False)
				if not result and tvdb: result = self._idCacheRetrieve(function = self.idShow, tvdb = tvdb, extra = extra, validate = validate, quick = None, cache = False)
				if not result and trakt: result = self._idCacheRetrieve(function = self.idShow, trakt = trakt, extra = extra, validate = validate, quick = None, cache = False)
				if not result and tmdb: result = self._idCacheRetrieve(function = self.idShow, tmdb = tmdb, extra = extra, validate = validate, quick = None, cache = False)

			# Do these separately, otherwise if this function is called with different ID-combination, it will not use the cached result.
			# Eg: the function is called 1st with only an IMDb ID, and a 2nd time with an IMDb and TVDb ID.
			if not result and imdb: result = self._idCache(function = self.idShow, imdb = imdb, extra = extra, validate = validate, quick = quick, cache = False)
			if not result and tvdb: result = self._idCache(function = self.idShow, tvdb = tvdb, extra = extra, validate = validate, quick = quick, cache = False)
			if not result and trakt: result = self._idCache(function = self.idShow, trakt = trakt, extra = extra, validate = validate, quick = quick, cache = False)
			if not result and tmdb: result = self._idCache(function = self.idShow, tmdb = tmdb, extra = extra, validate = validate, quick = quick, cache = False)

			# Only do this if no IDs are available.
			# If there are IDs, but Trakt and TMDb did not return any results for them, it means this is probably a new release that is not on Trakt/TMDb.
			# In this case, looking up by title will unnecessarily prolong the call, and will probably return the incorrect results in any case, since it is not on Trakt/TMDb and they will return the "best" match they can find.
			if not result and title and not imdb and not tmdb and not tvdb and not trakt: result = self._idCache(function = self.idShow, title = title, year = year, deviation = deviation, extra = extra, validate = validate, quick = quick, cache = False)

			# Validate here, not at the end of the function.
			# Because the cached function calls only get one ID passed in at a time, and a proper validation is therefore not possible within the cached call.
			if validate: result = self._idValidate(result = result, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt)

			return result

		result = {}
		multiple = None
		manager = None
		lookup = False

		# TMDb ID lookups are twice as fast as Trakt ID lookups.
		if quick:
			if quick is True: quick = {'tvdb' : True}
			elif Tools.isString(quick): quick = {quick : True}
		else:
			quick = {'trakt' : True, 'tvdb' : True}

		# Search TVDb by ID.
		# Search TVDb before Trakt, since Trakt sometimes returns multiple shows.
		def _idShowTvdbId():
			try:
				nonlocal imdb
				nonlocal tmdb
				nonlocal tvdb
				nonlocal trakt
				nonlocal title
				nonlocal year
				nonlocal result
				nonlocal manager
				nonlocal lookup
				nonlocal extra
				nonlocal deviation

				if not result or not 'tvdb' in result or not result['tvdb']:
					if imdb or tvdb or tmdb: # TVDb does not have the Trakt ID.
						if manager is None:
							from lib.meta.core import MetaCore
							manager = MetaCore(provider = MetaCore.ProviderTvdb, threaded = MetaCore.ThreadedDisable)
						lookup = True
						data = manager.search(idImdb = imdb, idTmdb = tmdb, idTvdb = tvdb, idTrakt = trakt, media = MetaData.MediaShow, limit = 1, cache = False)
						if data:
							result = {}
							ids = data.id()
							if ids:
								Tools.update(result, ids, none = False)
								if extra: Tools.update(result, {'title' : data.title(), 'year' : data.year(), 'rating' : data.voteRating(), 'votes' : data.voteCount()}, none = False)
			except: Logger.error()

		# Search Trakt by ID.
		# Trakt can sometimes return multiple shows for the same IMDb ID.
		# Eg: For "TVF Pitchers" Trakt returns
		#	{"trakt":100814,"slug":"tvf-pitchers-2015","tvdb":298807,"imdb":"tt4742876","tmdb":63180}
		#	{"trakt":185757,"slug":"tvf-pitchers-2015-185757","tvdb":298868,"imdb":"tt4742876","tmdb":63180}
		# Update: It seems that the 2nd TVF Pitchers has been removed.
		def _idShowTraktId():
			try:
				nonlocal imdb
				nonlocal tmdb
				nonlocal tvdb
				nonlocal trakt
				nonlocal title
				nonlocal year
				nonlocal result
				nonlocal multiple
				nonlocal manager
				nonlocal lookup
				nonlocal extra
				nonlocal deviation

				if not result or not 'tvdb' in result or not result['tvdb']:
					if imdb or tvdb or trakt:
						from lib.modules import trakt as Trakt
						lookup = True
						data = Trakt.SearchTVShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, single = True, full = extra, cache = False)
						if data and 'show' in data:
							ids = data['show'].get('ids')
							if ids:
								result = {}
								ids = {k : str(v) for k, v in ids.items() if v}
								if ids:
									Tools.update(result, ids, none = False)
									if extra: Tools.update(result, {'title' : data['show'].get('title'), 'year' : data['show'].get('year'), 'score' : data.get('score'), 'rating' : data['show'].get('rating'), 'votes' : data['show'].get('votes'), 'comments' : data['show'].get('comment_count')}, none = False)
			except: Logger.error()

		# Search TVDb by title.
		def _idShowTvdbTitle():
			try:
				nonlocal imdb
				nonlocal tmdb
				nonlocal tvdb
				nonlocal trakt
				nonlocal title
				nonlocal year
				nonlocal result
				nonlocal manager
				nonlocal lookup
				nonlocal extra
				nonlocal deviation

				if not result or not 'tvdb' in result or not result['tvdb']:
					if manager is None:
						from lib.meta.core import MetaCore
						manager = MetaCore(provider = MetaCore.ProviderTvdb, threaded = MetaCore.ThreadedDisable)
					query = self.cleanTitle(title)

					if year:
						year = int(year)
						if deviation: years = [year, year + 1, year - 1]
						else: years = [year]
					else:
						years = [None]

					found = False
					for i in years:
						data = manager.search(query = query, year = i, media = MetaData.MediaShow, cache = False)
						if data:
							for j in data:
								if query == self.cleanTitle(j.titleOriginal(selection = MetaData.SelectionSingle)) and (not year or j.year() in years):
									result = {}
									ids = j.id()
									if ids:
										Tools.update(result, ids, none = False)
										if extra: Tools.update(result, {'title' : j.title(), 'year' : j.year(), 'rating' : j.voteRating(), 'votes' : j.voteCount()}, none = False)
										found = True
										break
							if found: break
			except: Logger.error()

		# Search Trakt by title.
		def _idShowTraktTitle():
			try:
				nonlocal imdb
				nonlocal tmdb
				nonlocal tvdb
				nonlocal trakt
				nonlocal title
				nonlocal year
				nonlocal result
				nonlocal manager
				nonlocal lookup
				nonlocal extra
				nonlocal deviation

				if not result or not 'tvdb' in result or not result['tvdb']:
					from lib.modules import trakt as Trakt
					data = Trakt.SearchTVShow(title = title, year = year, single = True, full = extra, cache = False)
					if not(data and 'show' in data and data['show']) and deviation and year: data = Trakt.SearchTVShow(title = title, year = [int(year) - 1, int(year) + 1], single = True, full = extra, cache = False)
					if data and 'show' in data:
						ids = data['show'].get('ids')
						if ids:
							result = {}
							ids = {k : str(v) for k, v in ids.items() if v}
							if ids:
								Tools.update(result, ids, none = False)
								if extra: Tools.update(result, {'title' : data['show'].get('title'), 'year' : data['show'].get('year'), 'score' : data.get('score'), 'rating' : data['show'].get('rating'), 'votes' : data['show'].get('votes'), 'comments' : data['show'].get('comment_count')}, none = False)
			except: Logger.error()

		# TVDb does not have rating/votes in the search endpoint.
		# Utilize Trakt first. Used by Oracle to determine if a title is a movie or show based on these values.
		'''if extra:
			_idShowTraktId()
			_idShowTvdbId()
			if not lookup and title:
				_idShowTraktTitle()
				_idShowTvdbTitle()
		else:
			_idShowTvdbId()
			_idShowTraktId()
			if not lookup and title:
				_idShowTvdbTitle()
				_idShowTraktTitle()'''

		# Previously we retrieved the ID from TVDb before trying Trakt (if "extra == False"), since Trakt can sometimes return multiple IDs.
		# However, this causes this function to not return the Trakt ID, since TVDb does not have the Trakt ID (unlike Trakt, which has all 4 IDs for IMDb/TMdb/TVDb/Trakt).
		# Try Trakt before TVDb to get as many IDs as possible, especially if we need the Trakt ID for scrobbeling, ratings, etc.
		# The "TVF Pitchers" duplicates have now been removed from Trakt, so not an issue anymore.
		# Even if Trakt returns multiple results, we just pick the first one (with the highest search rank), which is probably the correct one.
		# Even in the case that is the wrong one, this should be a very rare exception.
		if quick.get('trakt'): _idShowTraktId()
		if quick.get('tvdb'): _idShowTvdbId()
		if not lookup and title:
			if quick.get('trakt'): _idShowTraktTitle()
			if quick.get('tvdb'): _idShowTvdbTitle()

		# This only works for non-cached calls.
		if validate and not cache: result = self._idValidate(result = result, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt)

		return result if result else None
